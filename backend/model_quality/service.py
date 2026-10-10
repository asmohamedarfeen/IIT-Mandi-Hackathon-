"""Read-only, bounded snapshot cache. No models are loaded or predictions run."""
import copy
import hashlib
from importlib.metadata import PackageNotFoundError, version as library_version
import json
from pathlib import Path
from threading import RLock

from backend.model_quality.schemas import OOF, Pointer, Summary


class ArtifactMissing(Exception):
    pass


class ArtifactCorrupt(Exception):
    pass


def version(path):
    stat = path.stat()
    return (stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns)


def read_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('Duplicate JSON key')
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=pairs)


class QualityService:
    def __init__(self, artifact_dir, model_path, dataset_path=None, source_root=None):
        self.artifact_dir = Path(artifact_dir)
        self.model_path = Path(model_path)
        self.dataset_path = Path(dataset_path) if dataset_path else None
        self.source_root = Path(source_root) if source_root else Path(__file__).resolve().parents[2]
        self._lock = RLock()
        self._key = self._snapshot = self._model_key = self._model_hash = None
        self._hash_cache = {}

    def _load(self):
        try:
            pointer_path = self.artifact_dir / 'current.json'
            pointer_version = version(pointer_path)
            pointer = Pointer.model_validate(read_json(pointer_path.read_bytes()))
            runs_dir = self.artifact_dir / 'runs'
            run_dir = runs_dir / pointer.run_id
            paths = [run_dir / 'summary.json', run_dir / 'oof.json']
            if runs_dir.is_symlink() or run_dir.is_symlink() or any(p.is_symlink() for p in paths) or pointer_path.is_symlink():
                raise ValueError('Symlink artifact is not allowed')
            key = (pointer_version, *(version(p) for p in paths))
            if key != self._key:
                raw = [p.read_bytes() for p in paths]
                if [hashlib.sha256(r).hexdigest() for r in raw] != [pointer.summary_sha256, pointer.oof_sha256]:
                    raise ValueError('Artifact integrity mismatch')
                summary = Summary.model_validate(read_json(raw[0]))
                oof = OOF.model_validate(read_json(raw[1]))
                if summary.run_id != pointer.run_id:
                    raise ValueError('Pointer identity mismatch')
                oof.validate_against(summary)
                # A concurrent replacement must not produce a mixed snapshot.
                if key != (version(pointer_path), *(version(p) for p in paths)):
                    raise ValueError('Artifact changed while reading')
                self._snapshot = (summary.model_dump(), oof.model_dump())
                self._key = key
            return self._snapshot
        except FileNotFoundError as exc:
            raise ArtifactMissing from exc
        except Exception as exc:
            raise ArtifactCorrupt from exc

    def _stale(self, summary):
        def matches(path, expected):
            try:
                key = version(path)
                cached = self._hash_cache.get(path)
                if cached and cached[0] == key:
                    return cached[1] == expected
                digest = hashlib.sha256()
                with path.open('rb') as stream:
                    for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                        digest.update(chunk)
                if version(path) != key:
                    return False
                self._hash_cache[path] = (key, digest.hexdigest())
                return digest.hexdigest() == expected
            except OSError:
                return False
        provenance = summary['provenance']
        for package, expected in provenance.get('library_versions', {}).items():
            try:
                if library_version(package) != expected:
                    return True
            except PackageNotFoundError:
                return True
        expected_files = {self.model_path: provenance['model_sha256']}
        if self.dataset_path:
            expected_files[self.dataset_path] = provenance['dataset_sha256']
        for relative, digest in provenance['source_hashes'].items():
            source = (self.source_root / relative).resolve()
            if not source.is_relative_to(self.source_root.resolve()):
                return True
            expected_files[source] = digest
        self._hash_cache = {path: value for path, value in self._hash_cache.items() if path in expected_files}
        return not all(matches(path, digest) for path, digest in expected_files.items())

    def overview(self):
        return self.capture()[0]

    def capture(self):
        """One detached summary/private audit pair for an entire request."""
        with self._lock:
            summary, oof = self._load()
            stale = self._stale(summary)
            return ({**copy.deepcopy(summary), 'status': 'stale' if stale else 'ready', 'stale': stale}, copy.deepcopy(oof))

    def confusion(self, target, model, threshold):
        summary, oof = self.capture()
        return self.confusion_from_snapshot(summary, oof, target, model, threshold)

    @staticmethod
    def confusion_from_snapshot(summary, oof, target, model, threshold):
        from backend.model_quality.metrics import binary_metrics
        if model not in summary['targets'][target]['models']:
            raise KeyError(model)
        rows = oof['targets'][target]
        values = binary_metrics(rows['labels'], rows['probabilities'][model], threshold)
        return {'run_id': summary['run_id'], 'target': target, 'model': model, **values}

"""Regression coverage for immutable evaluation inputs and offline imports."""
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import sys

import numpy as np
import pytest

from backend.model_quality import evaluation
from testing.backend.api.test_model_quality import evidence


@pytest.fixture
def inputs(tmp_path, monkeypatch):
    source = tmp_path / 'source.py'
    source.write_bytes(b'original evaluation source')
    dataset = tmp_path / 'cohort with spaces.xlsx'
    dataset.write_bytes(b'original dataset')
    bundle = tmp_path / 'model.joblib'
    bundle.write_bytes(b'original model')
    subprocess.run(['git', 'init', '-q', str(tmp_path)], check=True)
    subprocess.run(['git', 'add', 'source.py'], cwd=tmp_path, check=True)
    subprocess.run(['git', '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '-qm', 'test source'], cwd=tmp_path, check=True)
    monkeypatch.setattr(evaluation, 'ROOT', tmp_path)
    monkeypatch.setattr(evaluation, 'SOURCE_FILES', ['source.py'])
    monkeypatch.setattr(evaluation, 'IMPORTED_SOURCE_HASHES', {}, raising=False)
    return source, dataset, bundle


@pytest.mark.parametrize('changed', ['source', 'dataset', 'bundle'])
def test_input_or_source_drift_is_rejected_before_publication(inputs, changed):
    source, dataset, bundle = inputs
    frozen = evaluation.freeze_provenance(dataset, bundle)
    {'source': source, 'dataset': dataset, 'bundle': bundle}[changed].write_bytes(b'changed during fit')
    with pytest.raises(RuntimeError, match='changed'):
        evaluation.assert_unchanged(frozen)


def test_source_modified_since_import_cannot_be_attributed_to_loaded_code(inputs, monkeypatch):
    _, dataset, bundle = inputs
    monkeypatch.setattr(evaluation, 'IMPORTED_SOURCE_HASHES', {'source.py': 'a' * 64})
    with pytest.raises(RuntimeError, match='loaded|import'):
        evaluation.freeze_provenance(dataset, bundle)


def test_publication_archives_frozen_source_bytes(inputs, tmp_path):
    source, dataset, bundle = inputs
    frozen = evaluation.freeze_provenance(dataset, bundle)
    source.write_bytes(b'changed after snapshot')
    run = evaluation.publish_run(tmp_path / 'model_quality', {'run_id': 'b' * 32}, {}, frozen['source_bytes'])
    assert (run / 'source/source.py').read_bytes() == b'original evaluation source'


def test_reproduction_and_audit_commands_are_separate_and_shell_safe(tmp_path):
    dataset = tmp_path / 'cohort $(unsafe).xlsx'
    bundle = tmp_path / 'saved model.joblib'
    output = tmp_path / 'model_quality'
    rerun, verify = evaluation.reproduction_commands(dataset, bundle, output, 17, 4, 3)
    args = shlex.split(rerun)
    assert '--verify' not in args
    assert args[args.index('--dataset') + 1] == str(dataset)
    assert args[args.index('--bundle') + 1] == str(bundle)
    assert args[args.index('--output') + 1] == str(output)
    assert args[args.index('--seed') + 1] == '17'
    assert args[args.index('--outer-folds') + 1] == '4'
    assert args[args.index('--inner-folds') + 1] == '3'
    assert shlex.split(verify)[-3:] == ['--output', str(output), '--verify']


def test_offline_evaluation_import_does_not_load_production_prediction_service():
    code = "import sys; import backend.model_quality.evaluation; assert 'backend.cardio.service.prediction_service' not in sys.modules"
    result = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_legacy_metric_adapter_preserves_unavailable_metrics():
    from scripts.train_pipeline import calculate_metrics
    result = calculate_metrics(np.array([0, 0, 1, 1]), np.array([0, 0, 0, 0]), np.array([.1, .2, .3, .4]))
    assert result['accuracy'] == .5
    assert result['precision'] is None
    assert result['mcc'] is None


def test_audit_command_rejects_changed_archived_source(evidence):
    _, _, summary, _, _, folder, publish = evidence
    source = folder / 'source/source.py'
    source.parent.mkdir()
    source.write_bytes(b'evaluated source')
    summary['provenance']['source_hashes'] = {'source.py': hashlib.sha256(b'evaluated source').hexdigest()}
    publish()
    assert evaluation.verify_run(folder.parent.parent)['run_id'] == summary['run_id']
    source.write_bytes(b'different source')
    with pytest.raises(ValueError, match='source integrity'):
        evaluation.verify_run(folder.parent.parent)


def test_audit_command_uses_strict_fold_and_diagnostic_recomputation(evidence):
    _, _, summary, _, _, folder, publish = evidence
    summary['targets']['CAD']['models']['CalibratedVoting']['fold_metrics'][0]['accuracy'] = .123
    publish()
    with pytest.raises(ValueError, match='fold metric'):
        evaluation.verify_run(folder.parent.parent)


def test_nested_calibration_fits_imputation_only_on_inner_training_rows(monkeypatch):
    import pandas as pd
    from sklearn.calibration import CalibratedClassifierCV
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import StratifiedKFold
    from sklearn.pipeline import Pipeline
    from backend.cardio.service.feature_service import ClinicalPreprocessor

    raw = pd.DataFrame({'Age': [float(i) if i % 3 else None for i in range(40)]})
    labels = np.arange(40) % 2
    splits = list(StratifiedKFold(2, shuffle=True, random_state=42).split(raw, labels))
    recorded = []
    original = ClinicalPreprocessor.fit

    def capture_fit(self, frame, y=None):
        result = original(self, frame, y)
        recorded.append((set(frame.index), self.medians_['Age']))
        return result

    monkeypatch.setattr(ClinicalPreprocessor, 'fit', capture_fit)
    pipeline = Pipeline([('preprocess', ClinicalPreprocessor(['Age'])), ('model', LogisticRegression(random_state=42))])
    calibrated = CalibratedClassifierCV(pipeline, method='sigmoid', cv=5, n_jobs=1)
    evaluation.evaluate_estimator(calibrated, raw, labels, splits)
    assert len(recorded) == 10
    for outer, (train, test) in enumerate(splits):
        inner = recorded[outer * 5:(outer + 1) * 5]
        for rows, median in inner:
            assert len(rows) == 16
            assert rows <= set(train)
            assert not rows & set(test)
            assert median == raw.loc[sorted(rows), 'Age'].median()
        assert set.union(*(rows for rows, _ in inner)) == set(train)

import json

import pytest

from backend.model_quality.service import ArtifactCorrupt, ArtifactMissing, QualityService


def test_missing_artifact_is_explicit(tmp_path):
    with pytest.raises(ArtifactMissing):
        QualityService(tmp_path, tmp_path / 'model.joblib').overview()


@pytest.mark.parametrize('run_id', ['../escape', '/tmp/run', 'bad id', ''])
def test_pointer_never_accepts_paths(tmp_path, run_id):
    (tmp_path / 'current.json').write_text(json.dumps({'run_id': run_id, 'summary_sha256': 'a'*64, 'oof_sha256': 'b'*64}))
    with pytest.raises(ArtifactCorrupt):
        QualityService(tmp_path, tmp_path / 'model.joblib').overview()

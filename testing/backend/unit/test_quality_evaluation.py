import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold

from backend.model_quality.evaluation import evaluate_estimator, publish_run


def test_out_of_fold_evaluation_scores_each_row_once_and_keeps_estimator_unfitted():
    raw = pd.DataFrame({'x': [-4, -3, -2, -1, 1, 2, 3, 4]})
    y = np.array([0, 0, 0, 0, 1, 1, 1, 1])
    estimator = LogisticRegression(random_state=42)
    splits = list(StratifiedKFold(2, shuffle=True, random_state=42).split(raw, y))
    result, audit = evaluate_estimator(estimator, raw, y, splits)
    assert not hasattr(estimator, 'coef_')
    assert len(audit['probabilities']) == len(y)
    assert set(audit['fold_ids']) == {1, 2}
    assert result['metrics']['roc_auc'] == 1
    assert len(result['fold_metrics']) == 2
    assert len(result['fold_model_hashes']) == 2
    again, _ = evaluate_estimator(estimator, raw, y, splits)
    assert result['metrics'] == again['metrics']


def test_fold_overlap_or_incomplete_scoring_is_rejected():
    with pytest.raises(ValueError, match='partition|overlap'):
        evaluate_estimator(LogisticRegression(), pd.DataFrame({'x': [0, 1, 2, 3]}), [0, 1, 0, 1], [(np.array([0, 1]), np.array([1, 2]))])


def test_publication_is_atomic_and_refuses_deployed_artifact_paths(tmp_path):
    summary = {'run_id': 'a' * 32, 'schema_version': 1}
    audit = {'run_id': 'a' * 32}
    publish_run(tmp_path / 'model_quality', summary, audit)
    assert (tmp_path / 'model_quality' / 'current.json').exists()
    with pytest.raises(ValueError, match='protected|model_quality'):
        publish_run(tmp_path / 'artifacts', summary, audit)

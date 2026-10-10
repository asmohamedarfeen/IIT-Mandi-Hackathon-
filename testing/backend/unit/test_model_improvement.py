"""Checks for selection leakage, threshold behavior and conservative promotion."""
import numpy as np
import pytest
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.linear_model import LogisticRegression


def test_threshold_search_preserves_recall_and_does_not_modify_probability():
    from backend.model_quality.improvement import choose_threshold
    y = np.array([0, 0, 0, 1, 1, 1])
    p = np.array([.1, .2, .48, .42, .65, .8])
    original = p.copy()
    threshold, metrics = choose_threshold(y, p, recall_floor=1.0)
    assert threshold == pytest.approx(.4)
    assert metrics['recall'] == 1.0
    assert metrics['accuracy'] == pytest.approx(5 / 6)
    np.testing.assert_array_equal(p, original)


def test_promotion_rejects_accuracy_gain_that_loses_detection_or_calibration():
    from backend.model_quality.improvement import promotion_allowed
    baseline = dict(accuracy=.70, recall=.60, roc_auc=.76, brier_score=.19)
    candidate = dict(accuracy=.74, recall=.61, roc_auc=.77, brier_score=.18)
    assert promotion_allowed(baseline, candidate)
    assert not promotion_allowed(baseline, {**candidate, 'recall': .56})
    assert not promotion_allowed(baseline, {**candidate, 'brier_score': .22})
    assert not promotion_allowed(baseline, {**candidate, 'accuracy': .70})


class RecordingClassifier(ClassifierMixin, BaseEstimator):
    seen = []

    def __init__(self, C=1.0):
        self.C = C

    def fit(self, X, y):
        type(self).seen.append(set(np.asarray(X)[:, 0].astype(int)))
        self.model_ = LogisticRegression(C=self.C).fit(X, y)
        self.classes_ = self.model_.classes_
        return self

    def predict_proba(self, X):
        return self.model_.predict_proba(X)

    def predict(self, X):
        return self.model_.predict(X)


def test_nested_selection_never_fits_outer_test_rows():
    from backend.model_quality.improvement import evaluate_nested
    RecordingClassifier.seen = []
    X = np.column_stack([np.arange(48), np.arange(48) % 3])
    y = np.arange(48) % 2
    configurations = {'Baseline': RecordingClassifier(), 'Candidate': RecordingClassifier(C=.1)}
    result = evaluate_nested(X, y, configurations, outer_folds=2, inner_folds=2)
    assert len(result['probabilities']) == 48
    assert sorted(np.unique(result['fold_ids']).tolist()) == [1, 2]
    assert np.isfinite(result['probabilities']).all()
    outer_training_sets = [set(fold['train_indices']) for fold in result['folds']]
    for fit_rows in RecordingClassifier.seen:
        assert any(fit_rows <= train for train in outer_training_sets)
    for fold in result['folds']:
        assert fold['threshold'] in [.35, .4, .45, .5, .55, .6, .65]


def test_baseline_evaluation_preserves_its_deployed_threshold():
    from backend.model_quality.improvement import evaluate_nested
    from backend.model_quality.metrics import binary_metrics
    X = np.column_stack([np.arange(48), np.arange(48) % 3])
    y = np.arange(48) % 2
    result = evaluate_nested(X, y, {'Baseline': LogisticRegression()}, outer_folds=2, inner_folds=2, baseline_threshold=.65)
    expected = binary_metrics(y, result['baseline_probabilities'], threshold=.65)
    assert result['baseline_metrics'] == expected


def test_recorded_feature_ablation_excludes_derived_blood_count_indices():
    from backend.model_quality.improvement import candidate_configurations, validate_trial_budget
    names = ['Age', 'Neut', 'Lymph', 'PLT', 'NLR', 'PLR', 'SII', 'Age_EF_Ratio']
    configurations = candidate_configurations(LogisticRegression(), names)
    selected = configurations['CatBoost-d3-raw'].estimator.named_steps['select'].transformers[0][2]
    assert selected == [0, 1, 2, 3]
    rca = candidate_configurations(LogisticRegression(), names, target='RCA')
    assert len(rca) == 3
    validate_trial_budget(rca)


def test_trial_cap_rejects_broad_search_before_any_estimator_fit():
    from backend.model_quality.improvement import evaluate_nested, select_configuration
    RecordingClassifier.seen = []
    X = np.column_stack([np.arange(48), np.arange(48) % 3])
    y = np.arange(48) % 2
    configurations = {name: RecordingClassifier() for name in ('Baseline', 'A', 'B', 'C')}
    for evaluate in (evaluate_nested, select_configuration):
        with pytest.raises(ValueError, match='at most 3'):
            evaluate(X, y, configurations)
        assert RecordingClassifier.seen == []


def test_release_runner_rejects_broad_search_before_creating_release_or_reading_cohort(tmp_path, monkeypatch):
    import scripts.improve_models as runner
    from backend.cardio.constants import TARGET_NAMES
    dataset, bundle = tmp_path / 'cohort.xlsx', tmp_path / 'bundle.joblib'
    for path in (dataset, bundle, tmp_path / 'benchmark_summary.json'):
        path.write_bytes(b'preflight placeholder')
    monkeypatch.setattr(runner.joblib, 'load', lambda path: {'feature_names': ['Age'], 'calibrated_models': {t: RecordingClassifier() for t in TARGET_NAMES}})
    monkeypatch.setattr(runner, 'candidate_configurations', lambda *args: {name: RecordingClassifier() for name in ('Baseline', 'A', 'B', 'C')})
    with pytest.raises(ValueError, match='at most 3'):
        runner.run(dataset, bundle)
    assert not (tmp_path / 'model_releases').exists()

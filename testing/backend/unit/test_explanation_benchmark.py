import numpy as np
import pytest


class InteractingPredictor:
    def predict_proba(self, X):
        X = np.asarray(X)
        p = X[:, 0] / 200 + X[:, 1] / 1000 + X[:, 0] * X[:, 1] / 100000
        return np.column_stack([1 - p, p])


def test_benchmark_compares_real_prediction_reference_and_perturbation():
    from scripts.benchmark_explanations import benchmark
    bundle = {'feature_names': ['Age', 'BP'], 'calibrated_models': {'CAD': InteractingPredictor()}}
    result = benchmark(bundle, repeats=2)
    assert result['timing']['calls'] == 6
    assert result['timing']['p95_seconds'] >= result['timing']['p50_seconds'] > 0
    for case in result['cases']:
        target = case['targets']['CAD']
        assert target['prediction_error'] < 1e-9
        assert target['reconstruction_error'] < 1e-9
        assert target['repeat_max_contribution_difference'] == 0
        assert target['alternate_reference']['allocation_l1_difference'] > 0
        assert target['age_plus_one']['probability_difference'] > 0
    assert result['alternate_reference_inputs']['Age'] == 45
    with pytest.raises(ValueError, match='repeats'):
        benchmark(bundle, repeats=0)

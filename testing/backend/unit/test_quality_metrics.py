import numpy as np
import pytest
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss

from backend.model_quality.metrics import binary_metrics, diagnostics, stability_summary


def test_metrics_and_confusion_are_computed_from_probabilities():
    y = np.array([0, 0, 1, 1])
    p = np.array([.1, .6, .4, .9])
    result = binary_metrics(y, p)
    assert [result[k] for k in ('tn', 'fp', 'fn', 'tp')] == [1, 1, 1, 1]
    assert result['accuracy'] == result['sensitivity'] == result['specificity'] == .5
    assert result['average_precision'] == average_precision_score(y, p)
    assert result['brier_score'] == brier_score_loss(y, p)
    assert result['log_loss'] == log_loss(y, p)
    assert binary_metrics(y, p, .9)['tp'] == 1


def test_empty_bins_and_undefined_metrics_are_not_fabricated():
    result = diagnostics([0, 0], [.1, .2])
    assert result['calibration'][-1]['count'] == 0
    assert result['calibration'][-1]['fraction_positive'] is None
    assert result['roc']['fpr'] == []
    assert result['undefined_metrics']['roc_auc']
    assert binary_metrics([0, 1], [0, 0])['precision'] is None


def test_probability_one_is_included_and_threshold_zero_predicts_all_positive():
    result = diagnostics([0, 1], [0, 1])
    assert sum(row['count'] for row in result['calibration']) == 2
    assert result['calibration'][-1]['count'] == 1
    assert result['thresholds'][0]['tp'] == result['thresholds'][0]['fp'] == 1
    assert result['thresholds'][-1]['tp'] == 1


@pytest.mark.parametrize('y,p', [([0, 2], [.1, .2]), ([0, 1], [.1, float('nan')]), ([0], [.1, .2]), ([0, 1], [-.1, .2])])
def test_invalid_diagnostic_inputs_fail(y, p):
    with pytest.raises(ValueError):
        diagnostics(y, p)


def test_stability_preserves_all_fold_values_and_top_k_frequency():
    result = stability_summary([[1, 0], [0, 2]], ['a', 'b'], 'method', top_k=1)
    assert result['features'][0]['fold_values'] == [0, 2]
    assert result['features'][0]['top_k_frequency'] == .5
    assert result['mean_top_k_jaccard'] == 0

import copy
import pytest

from testing.backend.api.test_model_quality import evidence
from backend.model_quality.schemas import OOF, Summary
from backend.model_quality.metrics import stability_summary
import numpy as np
import pandas as pd
from backend.cardio.service.feature_service import normalize_dataset, extract_targets


@pytest.mark.parametrize('kind', ['calibration', 'roc', 'threshold', 'fold', 'split'])
def test_private_oof_rejects_inconsistent_saved_evidence(evidence, kind):
    _, _, original, original_oof, *_ = evidence
    summary, audit = copy.deepcopy(original), copy.deepcopy(original_oof)
    model = summary['targets']['CAD']['models']['CalibratedVoting']
    if kind == 'calibration':
        model['diagnostics']['calibration'][0]['fraction_positive'] = .123
    elif kind == 'roc':
        model['diagnostics']['roc']['fpr'][0] = .123
    elif kind == 'threshold':
        model['diagnostics']['thresholds'][50].update(tn=0, fp=0, fn=0, tp=30, sensitivity=2)
    elif kind == 'fold':
        model['fold_metrics'][0]['accuracy'] = .123
    else:
        audit['targets']['CAD']['splits'] = [{'fold': 1, 'train_indices': [0], 'test_indices': [0]}]
    with pytest.raises(ValueError):
        OOF.model_validate(audit).validate_against(Summary.model_validate(summary))


def test_shap_and_feature_stability_are_recomputed_from_private_audit(evidence):
    _, _, summary, audit, *_ = evidence
    summary = copy.deepcopy(summary)
    audit = copy.deepcopy(audit)
    names = ['measurement_a', 'measurement_b']
    summary['provenance']['feature_names'] = names
    for target in summary['targets']:
        local = audit['targets'][target]
        folds = np.asarray(local['fold_ids'])
        shap = np.arange(len(folds) * 2, dtype=float).reshape(-1, 2) / 100
        permutation = [[.1, .2], [.2, .1], [.3, .2]]
        local['splits'] = [{'fold': i, 'train_indices': np.flatnonzero(folds != i).tolist(), 'test_indices': np.flatnonzero(folds == i).tolist()} for i in (1, 2, 3)]
        local['explanation_audit'] = {'shap_values': shap.tolist(), 'permutation_fold_importance': permutation}
        expected = summary['targets'][target]
        expected['models']['CalibratedVoting']['fold_model_hashes'] = ['a' * 64] * 3
        expected['shap_stability'] = stability_summary([abs(shap[folds == i]).mean(axis=0) for i in (1, 2, 3)], names, 'test audit')
        expected['feature_stability'] = stability_summary(permutation, names, 'test audit')
    OOF.model_validate(audit).validate_against(Summary.model_validate(summary))
    audit['targets']['CAD']['explanation_audit']['shap_values'][0][0] += 1
    with pytest.raises(ValueError, match='stability mismatch'):
        OOF.model_validate(audit).validate_against(Summary.model_validate(summary))


@pytest.mark.parametrize('prepare', [normalize_dataset, extract_targets])
def test_whitespace_aliases_cannot_duplicate_dataset_columns(prepare):
    with pytest.raises(ValueError, match='Duplicate normalized'):
        prepare(pd.DataFrame([[1, 2]], columns=['Age', ' Age ']))

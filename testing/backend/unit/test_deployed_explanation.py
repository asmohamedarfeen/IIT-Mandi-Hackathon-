"""Actual probability explanations, independently checked with an interacting predictor."""
import numpy as np
import pytest

from backend.cardio.schemas.patient_schema import PatientInputSchema


class InteractingPredictor:
    def predict_proba(self, X):
        X = np.asarray(X)
        age, pressure = X[:, 0], X[:, 1]
        probability = age / 200 + pressure / 1000 + age * pressure / 100000
        return np.column_stack([1 - probability, probability])


def test_exact_domain_allocation_includes_interaction_and_reconstructs_actual_probability():
    from backend.cardio.service.deployed_explanation import explain_predictions
    bundle = {'feature_names': ['Age', 'BP'], 'calibrated_models': {'CAD': InteractingPredictor()}}
    explanation = explain_predictions(PatientInputSchema(Age=67, BP=140), bundle)['CAD']
    groups = {g['id']: g for g in explanation['groups']}
    assert groups['profile']['contribution'] == pytest.approx(.0756)
    assert groups['vitals']['contribution'] == pytest.approx(.0322)
    assert explanation['baseline_probability'] == pytest.approx(.461)
    assert explanation['predicted_probability'] == pytest.approx(.5688)
    assert explanation['baseline_probability'] + sum(g['contribution'] for g in groups.values()) == pytest.approx(.5688)
    assert explanation['reconstruction_error'] < 1e-12
    assert all(abs(g['contribution']) < 1e-12 for k, g in groups.items() if k not in ('profile', 'vitals'))
    assert groups['profile']['source_measurements'][0]['recorded_value'] == 67
    assert explanation['reference_type'] == 'synthetic_default_profile'


def test_default_reference_has_zero_contributions():
    from backend.cardio.service.deployed_explanation import explain_predictions
    bundle = {'feature_names': ['Age', 'BP'], 'calibrated_models': {'CAD': InteractingPredictor()}}
    explanation = explain_predictions(PatientInputSchema(), bundle)['CAD']
    assert all(abs(g['contribution']) < 1e-12 for g in explanation['groups'])
    assert explanation['unique_model_vectors'] == 1


def test_named_alternate_reference_changes_allocation_but_preserves_prediction():
    from backend.cardio.service.deployed_explanation import explain_predictions
    bundle = {'feature_names': ['Age', 'BP'], 'calibrated_models': {'CAD': InteractingPredictor()}}
    actual = PatientInputSchema(Age=67, BP=140)
    default = explain_predictions(actual, bundle)['CAD']
    alternate = explain_predictions(actual, bundle, reference_patient=PatientInputSchema(Age=45, BP=110))['CAD']
    assert alternate['reference_type'] == 'explicit_synthetic_profile'
    assert alternate['reference_inputs']['Age'] == 45
    assert alternate['baseline_probability'] != default['baseline_probability']
    assert alternate['predicted_probability'] == default['predicted_probability']
    assert alternate['reconstruction_error'] < 1e-9


def test_actual_release_explanation_is_bound_to_unrounded_predictor_output():
    from backend.cardio.service.prediction_service import prediction_service_instance
    response = prediction_service_instance.predict(PatientInputSchema(Age=67, **{'St Depression': 1}))
    for target, explanation in response.prediction_explanations.items():
        assert explanation.reconstruction_error < 1e-9
        rebuilt = explanation.baseline_probability + sum(g.contribution for g in explanation.groups)
        assert rebuilt == pytest.approx(explanation.predicted_probability, abs=1e-9)
        risk = response.overall_cad if target == 'CAD' else response.vessels[target]
        assert round(rebuilt, 4) == risk.probability
    assert set(response.prediction_explanations) == {'CAD', 'LAD', 'LCX', 'RCA'}

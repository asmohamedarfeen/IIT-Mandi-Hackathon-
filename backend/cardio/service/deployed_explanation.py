"""Exact seven-domain Shapley allocation of the deployed calibrated probability.

The reference is an explicit synthetic schema-default profile, not a healthy patient
or a population expectation. Raw measurement groups are swapped and derived features
recomputed. The finite group game is exact; it is not individual-feature SHAP,
conditional/population attribution, a clinical counterfactual, or causal evidence.
"""
from math import factorial

import numpy as np
import pandas as pd

from backend.cardio.schemas.patient_schema import PatientInputSchema
from backend.cardio.service.feature_service import prepare_features

METADATA_FIELDS = {'patient_id', 'assessment_mode', 'confirmed_measurements', 'input_sources'}
DOMAIN_GROUPS = [
    ('profile', 'Patient profile', ['Age', 'Sex', 'Weight', 'Length', 'BMI']),
    ('history', 'History and risk factors', ['DM', 'HTN', 'Current Smoker', 'EX-Smoker', 'FH', 'Obesity', 'CRF', 'CVA', 'Airway disease', 'Thyroid Disease', 'CHF', 'DLP']),
    ('vitals', 'Vitals and examination', ['BP', 'PR', 'Edema', 'Weak Peripheral Pulse', 'Lung rales', 'Systolic Murmur', 'Diastolic Murmur']),
    ('symptoms', 'Symptoms', ['Typical Chest Pain', 'Dyspnea', 'Function Class', 'Atypical', 'Nonanginal', 'LowTH Ang']),
    ('ecg', 'ECG findings', ['Q Wave', 'St Elevation', 'St Depression', 'Tinversion', 'LVH', 'Poor R Progression', 'BBB']),
    ('laboratory', 'Laboratory measurements', ['FBS', 'CR', 'TG', 'LDL', 'HDL', 'BUN', 'ESR', 'HB', 'K', 'Na', 'WBC', 'Lymph', 'Neut', 'PLT']),
    ('echo', 'Echocardiography', ['EF-TTE', 'Region RWMA', 'VHD']),
]


def explain_predictions(patient, bundle, *, reference_patient=None):
    actual = patient.model_dump(by_alias=True, exclude=METADATA_FIELDS)
    reference = (reference_patient if reference_patient is not None else PatientInputSchema()).model_dump(by_alias=True, exclude=METADATA_FIELDS)
    grouped = [key for _, _, keys in DOMAIN_GROUPS for key in keys]
    if len(grouped) != len(set(grouped)) or set(actual) - {'Exertional CP'} != set(grouped):
        raise ValueError('Explanation domains do not cover the raw measurement contract')
    n = len(DOMAIN_GROUPS)
    rows = []
    for mask in range(1 << n):
        row = dict(reference)
        for i, (_, _, keys) in enumerate(DOMAIN_GROUPS):
            if mask & (1 << i):
                row.update({key: actual[key] for key in keys})
        rows.append(row)
    matrix = prepare_features(pd.DataFrame(rows), bundle['feature_names']).to_numpy(dtype=np.float32)
    # Unchanged domains create repeated vectors; score each distinct vector once.
    unique, inverse = np.unique(matrix, axis=0, return_inverse=True)
    result = {}
    for target, model in bundle['calibrated_models'].items():
        probabilities = np.asarray(model.predict_proba(unique), dtype=np.float64)[:, 1][inverse]
        if not np.isfinite(probabilities).all() or ((probabilities < 0) | (probabilities > 1)).any():
            raise ValueError('Invalid probability in deployed explanation')
        groups = []
        for i, (key, label, fields) in enumerate(DOMAIN_GROUPS):
            contribution = 0.0
            for mask in range(1 << n):
                if mask & (1 << i):
                    continue
                size = mask.bit_count()
                weight = factorial(size) * factorial(n - size - 1) / factorial(n)
                contribution += weight * (probabilities[mask | (1 << i)] - probabilities[mask])
            groups.append({'id': key, 'label': label, 'contribution': float(contribution),
                           'source_measurements': [{'input_key': field, 'recorded_value': actual[field]} for field in fields]})
        baseline, prediction = float(probabilities[0]), float(probabilities[-1])
        error = abs(baseline + sum(g['contribution'] for g in groups) - prediction)
        if error > 1e-9:
            raise ValueError('Deployed explanation does not reconstruct probability')
        result[target] = {
            'method': 'Exact seven-domain Shapley allocation of deployed predict_proba',
            'output_space': 'probability', 'reference_type': 'synthetic_default_profile' if reference_patient is None else 'explicit_synthetic_profile',
            'reference_inputs': reference, 'baseline_probability': baseline,
            'predicted_probability': prediction, 'reconstruction_error': error,
            'evaluated_coalitions': 1 << n, 'unique_model_vectors': len(unique), 'groups': groups,
            'limitations': 'Relative to the explicit synthetic reference profile, not population-normal or healthy reference. Domain grouping and reference choice affect attribution; mixed profiles may be implausible. Not individual-feature SHAP, a causal effect or treatment advice.',
        }
    return result

"""Offline synthetic deployed-probability explanation validation; never trains or deploys."""
import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import platform
import sys
from time import perf_counter
import warnings

import joblib
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE_FILES = ['scripts/benchmark_explanations.py', 'backend/cardio/service/deployed_explanation.py',
                'backend/cardio/service/feature_service.py', 'backend/cardio/schemas/patient_schema.py']
sys.path.insert(0, str(ROOT))
from backend.cardio.schemas.patient_schema import PatientInputSchema
from backend.cardio.service.deployed_explanation import explain_predictions, METADATA_FIELDS
from backend.cardio.service.feature_service import prepare_features


def contributions(explanation):
    return np.array([group['contribution'] for group in explanation['groups']])


def benchmark(bundle, repeats=5):
    if repeats < 2:
        raise ValueError('repeats must be at least 2 for deterministic repeat validation')
    profiles = [('schema_defaults', PatientInputSchema()),
                ('synthetic_older_higher_pressure', PatientInputSchema(Age=67, BP=140)),
                ('synthetic_ecg_history', PatientInputSchema(Age=60, DM=1, **{'St Depression': 1}))]
    alternate = PatientInputSchema(Age=45, BP=110)
    rows, durations = [], []
    for name, patient in profiles:
        repeated = []
        for _ in range(repeats):
            started = perf_counter()
            repeated.append(explain_predictions(patient, bundle))
            durations.append(perf_counter() - started)
        base = repeated[0]
        changed_reference = explain_predictions(patient, bundle, reference_patient=alternate)
        perturbed = explain_predictions(patient.model_copy(update={'Age': patient.Age + 1}), bundle)
        inputs = patient.model_dump(by_alias=True, exclude=METADATA_FIELDS)
        vector = prepare_features(pd.DataFrame([inputs]), bundle['feature_names']).to_numpy(dtype=np.float32)
        targets = {}
        for target, explanation in base.items():
            actual = float(bundle['calibrated_models'][target].predict_proba(vector)[0, 1])
            prediction_error = abs(actual - explanation['predicted_probability'])
            repeat_difference = max(float(np.max(np.abs(contributions(run[target]) - contributions(explanation)))) for run in repeated)
            if prediction_error > 1e-9 or repeat_difference > 1e-9:
                raise ValueError('Explanation fidelity or deterministic repeat validation failed')
            comparison = {}
            for key, other in [('alternate_reference', changed_reference[target]), ('age_plus_one', perturbed[target])]:
                comparison[key] = {'probability_difference': other['predicted_probability'] - explanation['predicted_probability'],
                                   'baseline_difference': other['baseline_probability'] - explanation['baseline_probability'],
                                   'allocation_l1_difference': float(np.abs(contributions(other) - contributions(explanation)).sum()),
                                   'largest_domain_before': explanation['groups'][int(np.argmax(np.abs(contributions(explanation))))]['id'],
                                   'largest_domain_after': other['groups'][int(np.argmax(np.abs(contributions(other))))]['id']}
            targets[target] = {'prediction_error': prediction_error, 'reconstruction_error': explanation['reconstruction_error'],
                               'repeat_max_contribution_difference': repeat_difference,
                               'predicted_probability': actual, 'unique_model_vectors': explanation['unique_model_vectors'], **comparison}
        rows.append({'name': name, 'synthetic_inputs': inputs, 'targets': targets})
    return {'measured_at': datetime.now(timezone.utc).isoformat(),
            'method': 'Synthetic profiles; exact seven-domain allocation of loaded calibrated predict_proba. Timings cover all targets and all coalition evaluations; include first invocation, exclude model loading and direct fidelity checks.',
            'timing': {'calls': len(durations), 'repeats_per_profile': repeats, 'p50_seconds': float(np.percentile(durations, 50)),
                       'p95_seconds': float(np.percentile(durations, 95)), 'max_seconds': max(durations)},
            'alternate_reference_inputs': alternate.model_dump(by_alias=True, exclude=METADATA_FIELDS), 'cases': rows,
            'limitations': ['Synthetic local smoke benchmark, not hardware/load SLO or patient-level confidence interval.',
                           'One named alternate synthetic reference and one-year age perturbation are descriptive sensitivity checks, not a comprehensive stability study.',
                           'Reference choice and domain grouping affect allocation; mixed profiles may be implausible; no causal or treatment interpretation.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path, default=ROOT / 'artifacts/cardiovision_ensemble.joblib')
    parser.add_argument('--repeats', type=int, default=5)
    parser.add_argument('--output', type=Path, default=ROOT / 'artifacts/explanation_validation.json')
    args = parser.parse_args()
    source_hashes = {name: sha256((ROOT / name).read_bytes()).hexdigest() for name in SOURCE_FILES}
    bundle_hash = sha256(args.bundle.read_bytes()).hexdigest()
    started = perf_counter()
    bundle = joblib.load(args.bundle)  # Operator-trusted local serving artifact only.
    load_seconds = perf_counter() - started
    with warnings.catch_warnings():
        # The saved LightGBM pipeline accepts numeric vectors; preserve other warnings.
        warnings.filterwarnings('ignore', message='X does not have valid feature names, but LGBMClassifier was fitted with feature names', category=UserWarning)
        result = benchmark(bundle, args.repeats)
    if bundle_hash != sha256(args.bundle.read_bytes()).hexdigest() or source_hashes != {name: sha256((ROOT / name).read_bytes()).hexdigest() for name in SOURCE_FILES}:
        raise RuntimeError('Evaluated source or bundle changed during explanation validation; rerun')
    result.update({'model_load_seconds': load_seconds, 'bundle_sha256': bundle_hash,
                   'release_id': bundle.get('model_release', {}).get('run_id'),
                   'runtime': {'python': platform.python_version(), 'platform': platform.platform()}, 'source_hashes': source_hashes})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(f'Explanation validation written to {args.output}; p50={result["timing"]["p50_seconds"]:.4f}s p95={result["timing"]["p95_seconds"]:.4f}s load={load_seconds:.4f}s')


if __name__ == '__main__':
    main()

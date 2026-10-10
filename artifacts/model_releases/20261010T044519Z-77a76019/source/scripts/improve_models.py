#!/usr/bin/env python3
"""Reproducible nested comparison; --deploy publishes only guarded improvements."""
import argparse
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
from importlib.metadata import version
import json
import os
from pathlib import Path
import shutil
import sys
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from threadpoolctl import threadpool_limits

from backend.cardio.constants import LEAKAGE_COLUMNS, TARGET_NAMES
from backend.cardio.service.feature_service import extract_targets, prepare_features
from backend.model_quality.evaluation import estimator_parameters, file_hash
from backend.model_quality.improvement import candidate_configurations, evaluate_nested, promotion_allowed, select_configuration
from backend.model_quality.metrics import METRIC_KEYS, binary_metrics

SOURCE_FILES = ['scripts/improve_models.py', 'backend/model_quality/improvement.py',
                'backend/model_quality/models.py', 'backend/model_quality/metrics.py',
                'backend/cardio/service/feature_service.py', 'backend/cardio/constants.py',
                'backend/requirements.lock.txt']


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n')


def run(dataset, bundle_path, outer_folds=10, inner_folds=3, seed=42, deploy=False, tune_targets=TARGET_NAMES):
    dataset, bundle_path = Path(dataset).resolve(), Path(bundle_path).resolve()
    benchmark_path = bundle_path.parent / 'benchmark_summary.json'
    protected = {p: file_hash(p) for p in (dataset, bundle_path, benchmark_path)}
    source_bytes = {p: (ROOT / p).read_bytes() for p in SOURCE_FILES}
    bundle = joblib.load(bundle_path)  # Trusted local operator artifact only.
    names = bundle['feature_names']
    if len(names) != len(set(names)) or set(names) & set(LEAKAGE_COLUMNS):
        raise ValueError('Invalid feature contract')
    raw = pd.read_excel(dataset)
    # This run preserves deterministic legacy encoding; learned imputation is in estimators.
    # Reject missing source inputs so the compatibility wrapper cannot learn global medians.
    if raw.isna().any().any() or raw.duplicated().any():
        raise ValueError('This compatibility run requires complete, unique source records')
    targets = extract_targets(raw)
    X = prepare_features(raw, names).to_numpy(dtype=np.float32)
    reference = np.asarray(bundle['reference_background'])
    if not np.array_equal(X[:len(reference)], reference):
        raise ValueError('Feature definitions differ from saved reference vectors')
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ-') + uuid4().hex[:8]
    folder = bundle_path.parent / 'model_releases' / run_id
    folder.mkdir(parents=True, exist_ok=False)
    backup = folder / 'baseline'
    backup.mkdir()
    shutil.copy2(bundle_path, backup / bundle_path.name)
    shutil.copy2(benchmark_path, backup / benchmark_path.name)
    for relative, content in source_bytes.items():
        destination = folder / 'source' / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
    report = {
        'run_id': run_id, 'generated_at': datetime.now(timezone.utc).isoformat(),
        'record_count': len(raw), 'feature_count': len(names), 'random_seed': seed,
        'outer_folds': outer_folds, 'inner_folds': inner_folds, 'candidate_calibration_folds': 3,
        'tuned_targets': list(tune_targets),
        'dataset_sha256': protected[dataset], 'baseline_model_sha256': protected[bundle_path],
        'source_hashes': {p: sha256(data).hexdigest() for p, data in source_bytes.items()},
        'library_versions': {p: version(p) for p in ['numpy', 'pandas', 'scikit-learn', 'xgboost', 'lightgbm', 'catboost', 'joblib']},
        'method': f'Paired stratified {outer_folds}-fold outer evaluation; {inner_folds}-fold inner model/threshold selection for {", ".join(tune_targets)}; sigmoid calibration within each estimator fit. Other targets retain their current configuration and threshold.',
        'promotion_rule': 'Accuracy must increase; recall and ROC-AUC may fall by at most 0.02; Brier score may increase by at most 0.01. These tolerances are engineering release rules, not clinical boundaries.',
        'limitations': [
            'Internal single-cohort evaluation, not external clinical validation.',
            'Earlier configurations were developed on this cohort; historical selection bias remains.',
            'Outer metrics evaluate the selection procedure, not the final full-cohort fitted weights.',
            'Promotion is chosen after seeing outer metrics; release-level selection adds optimism. Gains are descriptive and not evidence of statistical significance.',
            'Final configuration and threshold are selected on full-cohort inner OOF data, not on outer-test predictions.',
            'Independent XGBoost SHAP explanations remain surrogate attributions, not exact explanations of the calibrated predictor.',
            'Clinical proxies and RWMA territory assumptions are preserved for compatibility. Recorded-feature ablations are available in the broad search; the RCA shortlist uses full features.',
            'The RCA shortlist follows an unsuccessful broader tuning trial on this same cohort. This additional experiment increases historical selection bias.',
            'Classification thresholds are separate from the 35%/65% artery display bands.',
        ], 'targets': {},
    }
    updated = dict(bundle)
    updated['calibrated_models'] = dict(bundle['calibrated_models'])
    updated['decision_thresholds'] = {t: bundle.get('decision_thresholds', {}).get(t, .5) for t in TARGET_NAMES}
    updated['prediction_model_names'] = {t: bundle.get('prediction_model_names', {}).get(t, 'Existing sigmoid-calibrated voting ensemble') for t in TARGET_NAMES}
    audit = {'run_id': run_id, 'targets': {}}
    with threadpool_limits(limits=1):
        for target in TARGET_NAMES:
            y = targets[target].to_numpy(dtype=int)
            baseline_threshold = updated['decision_thresholds'][target]
            configurations = candidate_configurations(bundle['calibrated_models'][target], names, seed, target)
            if target not in tune_targets:
                configurations = {'Baseline': configurations['Baseline']}
            print(f'{target}: {len(configurations)} configurations; nested evaluation', flush=True)
            outcome = evaluate_nested(X, y, configurations, outer_folds, inner_folds, seed, baseline_threshold)
            promoted = promotion_allowed(outcome['baseline_metrics'], outcome['candidate_metrics'])
            final = select_configuration(X, y, configurations, inner_folds, seed, baseline_threshold) if promoted else {'model': 'Baseline', 'threshold': baseline_threshold}
            if promoted:
                updated['calibrated_models'][target] = clone(configurations[final['model']]).fit(X, y)
                updated['decision_thresholds'][target] = final['threshold']
                updated['prediction_model_names'][target] = f'Sigmoid-calibrated {final["model"]}'
            chosen_metrics = outcome['candidate_metrics'] if promoted else outcome['baseline_metrics']
            report['targets'][target] = {
                'class_distribution': {'positive': int(y.sum()), 'negative': int(len(y) - y.sum())},
                'baseline_metrics': outcome['baseline_metrics'], 'candidate_metrics': outcome['candidate_metrics'],
                'baseline_threshold': baseline_threshold,
                'release_procedure_metrics': chosen_metrics, 'promoted': promoted,
                'final_selection': final, 'model_name': updated['prediction_model_names'][target],
                'outer_selected_models': dict(Counter(f['model'] for f in outcome['folds'])),
                'fold_selections': [{k: v for k, v in f.items() if k not in ('train_indices', 'test_indices')} for f in outcome['folds']],
                'configuration_parameters': {name: estimator_parameters(model) for name, model in configurations.items()},
            }
            audit['targets'][target] = {'labels': y.tolist(), **outcome}
            write_json(folder / 'summary.json', report)
            write_json(folder / 'oof.json', audit)
            (folder / 'oof.json').chmod(0o600)
            print(f'{target}: accuracy {outcome["baseline_metrics"]["accuracy"]:.4f} -> {outcome["candidate_metrics"]["accuracy"]:.4f}; promoted={promoted}', flush=True)
    for path, digest in protected.items():
        if file_hash(path) != digest:
            raise RuntimeError(f'Input changed during evaluation: {path.name}')
    for relative, content in source_bytes.items():
        if (ROOT / relative).read_bytes() != content:
            raise RuntimeError(f'Source changed during evaluation: {relative}')
    updated['model_release'] = {'run_id': run_id, 'summary': report,
                               'validation_summary': {
                                   'record_count': len(raw), 'method': report['method'],
                                   'source': f'model_releases/{run_id}/summary.json; paired outer-held-out predictions',
                                   'ensemble_metrics': {t: report['targets'][t]['release_procedure_metrics'] for t in TARGET_NAMES},
                                   'limitations': ' '.join(report['limitations'][:5])}}
    staged = folder / bundle_path.name
    joblib.dump(updated, staged)
    # Reopen and execute actual serialized pipelines before deployment.
    reopened = joblib.load(staged)
    for target in TARGET_NAMES:
        probability = reopened['calibrated_models'][target].predict_proba(X[:3])[:, 1]
        if not np.isfinite(probability).all() or ((probability < 0) | (probability > 1)).any():
            raise ValueError('Serialized model smoke check failed')
    report['release_model_sha256'] = file_hash(staged)
    report['deployed'] = bool(deploy and any(t['promoted'] for t in report['targets'].values()))
    write_json(folder / 'summary.json', report)
    benchmark = json.loads(benchmark_path.read_text())
    benchmark['targets'] = {
        t: {'Previous calibrated configuration': {k: report['targets'][t]['baseline_metrics'][k] for k in METRIC_KEYS},
            ('Promoted nested selection strategy' if report['targets'][t]['promoted'] else 'Retained calibrated configuration'): {k: report['targets'][t]['release_procedure_metrics'][k] for k in METRIC_KEYS}}
        for t in TARGET_NAMES}
    benchmark['evaluation'] = {k: report[k] for k in ('run_id', 'method', 'record_count', 'limitations')}
    benchmark['model_release'] = report
    write_json(folder / benchmark_path.name, benchmark)
    if report['deployed']:
        # Serving reads validation from the bundle, so the bundle is the coherent release boundary.
        temporary = bundle_path.with_suffix('.joblib.tmp')
        shutil.copy2(staged, temporary)
        os.replace(temporary, bundle_path)
        temporary = benchmark_path.with_suffix('.json.tmp')
        shutil.copy2(folder / benchmark_path.name, temporary)
        os.replace(temporary, benchmark_path)
    print(f'Release report: {folder / "summary.json"}; deployed={report["deployed"]}', flush=True)
    return folder


def verify(folder):
    folder = Path(folder)
    report = json.loads((folder / 'summary.json').read_text())
    audit = json.loads((folder / 'oof.json').read_text())
    if audit['run_id'] != report['run_id']:
        raise ValueError('Run identity mismatch')
    for relative, digest in report['source_hashes'].items():
        if file_hash(folder / 'source' / relative) != digest:
            raise ValueError('Archived source hash mismatch')
    if file_hash(folder / 'cardiovision_ensemble.joblib') != report['release_model_sha256']:
        raise ValueError('Release model hash mismatch')
    for target in TARGET_NAMES:
        rows, saved = audit['targets'][target], report['targets'][target]
        metrics = binary_metrics(rows['labels'], rows['probabilities'], y_pred=rows['predictions'])
        baseline = binary_metrics(rows['labels'], rows['baseline_probabilities'], saved.get('baseline_threshold', .5))
        for key in METRIC_KEYS:
            for actual, expected in ((metrics[key], saved['candidate_metrics'][key]), (baseline[key], saved['baseline_metrics'][key])):
                if actual != expected and not (actual is not None and expected is not None and abs(actual - expected) < 1e-12):
                    raise ValueError(f'{target}: metric mismatch: {key}')
        if promotion_allowed(baseline, metrics) != saved['promoted']:
            raise ValueError('Promotion rule mismatch')
        all_indices, scored = set(range(len(rows['labels']))), []
        for fold in rows['folds']:
            train, test = set(fold['train_indices']), set(fold['test_indices'])
            if train & test or train | test != all_indices:
                raise ValueError('Outer partition mismatch')
            for i in test:
                if rows['fold_ids'][i] != fold['fold'] or rows['predictions'][i] != int(rows['probabilities'][i] >= fold['threshold']):
                    raise ValueError('Fold or threshold mismatch')
            scored.extend(test)
        if sorted(scored) != list(range(len(rows['labels']))):
            raise ValueError('Outer coverage mismatch')
    print(f'Verified release hashes, paired OOF metrics, fold coverage, thresholds and promotion: {report["run_id"]}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', type=Path, default=ROOT / 'extention of Z-Alizadeh sani dataset.xlsx')
    parser.add_argument('--bundle', type=Path, default=ROOT / 'artifacts/cardiovision_ensemble.joblib')
    parser.add_argument('--outer-folds', type=int, default=10)
    parser.add_argument('--inner-folds', type=int, default=3)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--deploy', action='store_true')
    parser.add_argument('--targets', nargs='+', choices=TARGET_NAMES, default=TARGET_NAMES,
                        help='Targets to tune; other targets are evaluated and preserved unchanged')
    parser.add_argument('--verify', type=Path)
    args = parser.parse_args()
    if args.verify:
        verify(args.verify)
    else:
        folder = run(args.dataset, args.bundle, args.outer_folds, args.inner_folds, args.seed, args.deploy, args.targets)
        verify(folder)


if __name__ == '__main__':
    main()

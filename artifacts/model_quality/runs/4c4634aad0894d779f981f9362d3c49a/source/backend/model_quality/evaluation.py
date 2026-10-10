"""Offline OOF evaluation. No production serialization or API-side training."""
from datetime import datetime, timezone
from hashlib import sha256
from importlib.metadata import version
from io import BytesIO
import json
import os
from pathlib import Path
import platform
import shlex
import subprocess
import tempfile
import time
from uuid import uuid4

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.calibration import CalibratedClassifierCV
from sklearn.inspection import permutation_importance
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

from backend.cardio.constants import LEAKAGE_COLUMNS, TARGET_NAMES
from backend.cardio.service.feature_service import ClinicalPreprocessor, extract_targets, prepare_features
from backend.model_quality.metrics import METRIC_KEYS, binary_metrics, diagnostics, stability_summary, validated_arrays
from backend.model_quality.models import bounded_threads, get_candidate_models
from backend.model_quality.schemas import OOF, Pointer, Summary

ROOT = Path(__file__).resolve().parents[2]
SOURCE_FILES = ['backend/model_quality/evaluation.py', 'backend/model_quality/metrics.py',
                'backend/model_quality/models.py', 'backend/cardio/service/feature_service.py',
                'backend/model_quality/schemas.py', 'backend/model_quality/__init__.py',
                'backend/cardio/service/__init__.py',
                'backend/cardio/constants.py', 'scripts/evaluate_model_quality.py',
                'backend/requirements.lock.txt']
SELECTED_MODEL = 'CalibratedVoting'
# Detect edits made after these modules were imported but before a run begins.
IMPORTED_SOURCE_HASHES = {relative: sha256((ROOT / relative).read_bytes()).hexdigest() for relative in SOURCE_FILES}


def file_hash(path):
    with open(path, 'rb') as stream:
        from hashlib import file_digest
        return file_digest(stream, 'sha256').hexdigest()


def freeze_provenance(dataset, bundle_path):
    """Capture bytes and repository identity before any model fitting or input load."""
    source_bytes = {relative: (ROOT / relative).read_bytes() for relative in SOURCE_FILES}
    source_hashes = {relative: sha256(raw).hexdigest() for relative, raw in source_bytes.items()}
    if any(source_hashes.get(relative) != digest for relative, digest in IMPORTED_SOURCE_HASHES.items()):
        raise RuntimeError('Evaluation source changed since import; restart with the source to be evaluated loaded')
    paths = [Path(dataset).resolve(), Path(bundle_path).resolve()]
    benchmark = paths[1].parent / 'benchmark_summary.json'
    if benchmark.exists():
        paths.append(benchmark)
    input_bytes = {path: path.read_bytes() for path in paths}
    return {'source_bytes': source_bytes, 'source_hashes': source_hashes,
            'input_bytes': input_bytes,
            'input_hashes': {path: sha256(raw).hexdigest() for path, raw in input_bytes.items()},
            'git_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
            'git_dirty': bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True).strip())}


def assert_unchanged(frozen):
    """A changed or removed evaluated input/source prevents publication."""
    paths = {**frozen['input_hashes'], **{ROOT / relative: digest for relative, digest in frozen['source_hashes'].items()}}
    for path, digest in paths.items():
        try:
            unchanged = file_hash(path) == digest
        except OSError:
            unchanged = False
        if not unchanged:
            raise RuntimeError(f'Evaluated input or source changed during evaluation: {path.name}')


def reproduction_commands(dataset, bundle_path, output_directory, seed, outer_folds, inner_folds):
    executable = str(ROOT / '.venv/bin/python')
    script = str(ROOT / 'scripts/evaluate_model_quality.py')
    rerun = shlex.join([executable, script, '--dataset', str(dataset), '--bundle', str(bundle_path),
                       '--output', str(Path(output_directory).resolve()), '--seed', str(seed),
                       '--outer-folds', str(outer_folds), '--inner-folds', str(inner_folds)])
    verify = shlex.join([executable, script, '--output', str(Path(output_directory).resolve()), '--verify'])
    return rerun, verify


def class_counts(y):
    return {'positive': int(np.sum(y)), 'negative': int(len(y) - np.sum(y)), 'total': len(y)}


def evaluate_estimator(estimator, raw, y, splits, feature_names=None, stability=False, seed=42):
    """Fit unfitted clones and preserve every outer-held-out probability once."""
    y = np.asarray(y, dtype=int)
    n = len(y)
    probabilities = np.full(n, np.nan)
    fold_ids = np.zeros(n, dtype=int)
    fold_metrics, hashes, timings, permutation, shap_means = [], [], [], [], []
    shap_rows = np.zeros((n, len(feature_names))) if stability else None
    all_rows = set(range(n))
    for fold, (train, test) in enumerate(splits, 1):
        train, test = np.asarray(train), np.asarray(test)
        if set(train) & set(test) or set(train) | set(test) != all_rows or len(set(train)) != len(train) or len(set(test)) != len(test):
            raise ValueError('Outer fold partition has overlap, missing or duplicate rows')
        if np.any(fold_ids[test]):
            raise ValueError('Outer test folds overlap')
        started = time.monotonic()
        fitted = clone(estimator).fit(raw.iloc[train], y[train])
        predicted = fitted.predict_proba(raw.iloc[test])[:, 1]
        validated_arrays(y[test], predicted)
        probabilities[test] = predicted
        fold_ids[test] = fold
        fold_metrics.append({key: value for key, value in binary_metrics(y[test], predicted).items() if key in METRIC_KEYS})
        stream = BytesIO()
        joblib.dump(fitted, stream)
        hashes.append(sha256(stream.getvalue()).hexdigest())
        if stability:
            # Independent XGBoost explainer, not attribution of calibrated voting.
            import shap
            matrix = fitted.named_steps['preprocess'].transform(raw.iloc[test])
            model = fitted.named_steps['model']
            values = np.asarray(shap.TreeExplainer(model).shap_values(matrix), dtype=float)
            if values.shape != matrix.shape or not np.isfinite(values).all():
                raise ValueError('SHAP values violate the saved feature contract')
            shap_rows[test] = values
            shap_means.append(np.abs(values).mean(axis=0))
            permutation.append(permutation_importance(model, matrix, y[test], scoring='roc_auc',
                                                       n_repeats=3, random_state=seed + fold, n_jobs=1).importances_mean)
        timings.append(time.monotonic() - started)
        print(f'    fold {fold}/{len(splits)} complete', flush=True)
    if np.any(fold_ids == 0) or not np.isfinite(probabilities).all():
        raise ValueError('Outer folds do not partition all rows exactly once')
    metrics = binary_metrics(y, probabilities)
    result = {'metrics': {key: metrics[key] for key in METRIC_KEYS},
              'undefined_metrics': diagnostics(y, probabilities)['undefined_metrics'],
              'fold_metrics': fold_metrics, 'fold_model_hashes': hashes, 'fold_fit_seconds': timings,
              'diagnostics': diagnostics(y, probabilities),
              'fold_summary': {key: {'mean': float(np.mean([row[key] for row in fold_metrics if row[key] is not None])),
                                    'std': float(np.std([row[key] for row in fold_metrics if row[key] is not None], ddof=1))}
                               for key in METRIC_KEYS if sum(row[key] is not None for row in fold_metrics) >= 2}}
    audit = {'probabilities': probabilities.tolist(), 'fold_ids': fold_ids.tolist()}
    if stability:
        result['feature_stability'] = stability_summary(permutation, feature_names, 'Held-out independent XGBoost permutation ROC-AUC decrease; 3 repeats')
        result['shap_stability'] = stability_summary(shap_means, feature_names, 'Held-out independent XGBoost mean absolute TreeSHAP (raw log-odds)')
        audit['shap_values'] = shap_rows.tolist()
        audit['permutation_fold_importance'] = [row.tolist() for row in permutation]
    return result, audit


def _json_bytes(value):
    return json.dumps(value, sort_keys=True, indent=2, allow_nan=False).encode()


def publish_run(directory, summary, audit, source_bytes=None):
    directory = Path(directory).resolve()
    if directory.name != 'model_quality':
        raise ValueError('Output must be a dedicated model_quality directory, never a protected artifact directory')
    run_id = summary['run_id']
    if len(run_id) != 32 or any(char not in '0123456789abcdef' for char in run_id):
        raise ValueError('Invalid evaluation run identity')
    directory.mkdir(parents=True, exist_ok=True)
    run = directory / 'runs' / run_id
    run.mkdir(parents=True, exist_ok=False)
    summary_bytes, audit_bytes = _json_bytes(summary), _json_bytes(audit)
    (run / 'summary.json').write_bytes(summary_bytes)
    (run / 'oof.json').write_bytes(audit_bytes)
    (run / 'oof.json').chmod(0o600)
    source_bytes = source_bytes if source_bytes is not None else {relative: (ROOT / relative).read_bytes() for relative in SOURCE_FILES}
    for relative, raw in source_bytes.items():
        destination = run / 'source' / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(raw)
    pointer = {'run_id': run_id, 'summary_sha256': sha256(summary_bytes).hexdigest(), 'oof_sha256': sha256(audit_bytes).hexdigest()}
    descriptor, temporary = tempfile.mkstemp(prefix='.current-', suffix='.json', dir=directory)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(_json_bytes(pointer))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, directory / 'current.json')
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return run


def estimator_parameters(estimator):
    """JSON-safe full configuration, including nested estimator classes."""
    def convert(value):
        if hasattr(value, 'get_params'):
            return {'class': f'{type(value).__module__}.{type(value).__name__}', 'parameters': convert(value.get_params(deep=False))}
        if isinstance(value, dict):
            return {str(key): convert(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [convert(item) for item in value]
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value if not isinstance(value, float) or np.isfinite(value) else str(value)
        if isinstance(value, np.generic):
            return convert(value.item())
        return repr(value)
    return convert(estimator)


def evaluate_dataset(dataset, bundle_path, output_directory, seed=42, outer_folds=10, inner_folds=5):
    started = datetime.now(timezone.utc).isoformat()
    timer = time.monotonic()
    dataset, bundle_path = Path(dataset).resolve(), Path(bundle_path).resolve()
    frozen = freeze_provenance(dataset, bundle_path)
    protected = frozen['input_hashes']
    benchmark_path = bundle_path.parent / 'benchmark_summary.json'
    bundle = joblib.load(BytesIO(frozen['input_bytes'][bundle_path]))  # Trusted operator-supplied local artifact only.
    feature_names = list(bundle['feature_names'])
    if len(feature_names) != len(set(feature_names)) or set(feature_names) & set(LEAKAGE_COLUMNS):
        raise ValueError('Invalid saved feature contract')
    raw = pd.read_excel(BytesIO(frozen['input_bytes'][dataset]))
    targets = extract_targets(raw)
    raw.columns = raw.columns.str.strip()
    aligned = prepare_features(raw, feature_names)
    background = np.asarray(bundle.get('reference_background', []))
    background_matches = background.shape == aligned.iloc[:len(background)].shape and np.array_equal(background, aligned.iloc[:len(background)].to_numpy())
    if not background_matches:
        raise ValueError('Current feature definitions do not reproduce saved model reference background')
    inputs = raw.drop(columns=LEAKAGE_COLUMNS, errors='ignore')
    candidates = get_candidate_models(seed, include_additional=True)
    models_metadata = []
    results, audit_targets = {}, {}
    with threadpool_limits(limits=1):
        for target, series in targets.items():
            y = series.to_numpy(dtype=int)
            if min(np.bincount(y, minlength=2)) < outer_folds:
                raise ValueError(f'{target}: insufficient outcomes for stratified folds')
            splits = list(StratifiedKFold(outer_folds, shuffle=True, random_state=seed).split(inputs, y))
            saved_calibrated = bundle['calibrated_models'][target]
            voting = clone(saved_calibrated.estimator)
            estimators = {**candidates, 'Voting': voting}
            pipelines = {}
            for name, estimator in estimators.items():
                stages = [('preprocess', ClinicalPreprocessor(feature_names))]
                if name in ('LogisticRegression', 'SVM'):
                    stages.append(('scale', StandardScaler()))
                if name == 'SVM':
                    estimator = clone(estimator).set_params(probability=False)
                pipeline = Pipeline(stages + [('model', bounded_threads(estimator))])
                pipelines[name] = CalibratedClassifierCV(pipeline, method='sigmoid', cv=inner_folds, n_jobs=1) if name == 'SVM' else pipeline
            pipelines[SELECTED_MODEL] = CalibratedClassifierCV(pipelines['Voting'], method=saved_calibrated.method, cv=inner_folds, n_jobs=1, ensemble=saved_calibrated.ensemble)
            if not models_metadata:
                models_metadata = [{'id': name, 'name': {'Voting': 'Voting Ensemble', SELECTED_MODEL: 'Sigmoid-calibrated Voting Ensemble', 'LogisticRegression': 'Logistic Regression', 'DecisionTree': 'Decision Tree', 'RandomForest': 'Random Forest', 'ExtraTrees': 'Extra Trees'}.get(name, name),
                                    'production_configuration': name == SELECTED_MODEL,
                                    'configuration_source': 'Cloned saved production configuration' if name in ('Voting', SELECTED_MODEL) else 'Shared fixed candidate registry; not deployed',
                                    'parameters': estimator_parameters(model)} for name, model in pipelines.items()]
            target_results, probabilities, fold_ids = {}, {}, None
            stability_data, shap_data, shap_audit = None, None, None
            for name, model in pipelines.items():
                print(f'{target} / {name}', flush=True)
                result, audit = evaluate_estimator(model, inputs, y, splits, feature_names, stability=name == 'XGBoost', seed=seed)
                probabilities[name] = audit['probabilities']
                fold_ids = audit['fold_ids']
                if name == 'XGBoost':
                    stability_data, shap_data = result.pop('feature_stability'), result.pop('shap_stability')
                    shap_audit = {key: audit[key] for key in ('shap_values', 'permutation_fold_importance')}
                target_results[name] = result
            results[target] = {'class_distribution': class_counts(y), 'models': target_results,
                               'folds': [{'fold': i, 'train': class_counts(y[train]), 'test': class_counts(y[test])} for i, (train, test) in enumerate(splits, 1)],
                               'feature_stability': stability_data, 'shap_stability': shap_data}
            audit_targets[target] = {'labels': y.tolist(), 'fold_ids': fold_ids, 'probabilities': probabilities,
                                     'splits': [{'fold': i, 'train_indices': train.tolist(), 'test_indices': test.tolist()} for i, (train, test) in enumerate(splits, 1)], 'explanation_audit': shap_audit}
    assert_unchanged(frozen)
    run_id = uuid4().hex
    command, verify_command = reproduction_commands(dataset, bundle_path, output_directory, seed, outer_folds, inner_folds)
    duplicates = int(raw.duplicated().sum())
    limitations = [
        'Internal single-cohort cross-validation of fixed cloned configurations, not external clinical validation of fitted production weights.',
        'Model configurations were historically developed using this cohort; outer CV does not remove earlier model-selection bias.',
        'Threshold exploration uses these OOF outcomes; choosing a threshold here is exploratory, not an unbiased clinical operating-point validation.',
        'SHAP and feature stability explain the independent XGBoost classifier, not the calibrated voting ensemble; TreeSHAP units are raw log-odds.',
        'Permutation importance perturbs engineered columns independently. Correlated and derived features may split importance or produce implausible combinations.',
        'Fold dispersion is descriptive, not a confidence interval. Small reliability-bin counts have substantial sampling uncertainty.',
        'Original model training timestamp and historical selection decision log were not supplied. The evaluated configuration is identified by its saved artifact hash.',
        'Derived clinical proxies and reference artery territories are model assumptions, not patient-specific imaging or validated clinical scores.',
        'Stacking was not implemented; no stacking results are fabricated. Additional SVM and Decision Tree configurations are experimental comparators.',
        'Repeatability targets metric agreement to absolute tolerance 1e-8 under archived source and pinned dependencies; different hardware/library versions can change floating-point results.',
    ]
    summary = {'schema_version': 1, 'run_id': run_id, 'generated_at': datetime.now(timezone.utc).isoformat(), 'selected_model': SELECTED_MODEL,
               'provenance': {'dataset_sha256': protected[dataset], 'model_sha256': protected[bundle_path],
                              'git_commit': frozen['git_commit'], 'git_dirty': frozen['git_dirty'], 'source_hashes': frozen['source_hashes'],
                              'feature_sha256': sha256(_json_bytes(feature_names)).hexdigest(), 'feature_names': feature_names,
                              'python_version': platform.python_version(), 'platform': platform.platform(),
                              'library_versions': {name: version(name) for name in ['numpy', 'pandas', 'scikit-learn', 'scipy', 'xgboost', 'lightgbm', 'catboost', 'shap', 'joblib', 'openpyxl']},
                              'random_seed': seed, 'outer_folds': outer_folds, 'inner_folds': inner_folds,
                              'command': command, 'verify_command': verify_command,
                              'preprocessing': 'Fixed category normalization and row-local clinical engineering; training-only measurement medians/category modes; saved ordered float32 feature contract. Scaling/calibration inside estimator pipelines.',
                              'started_at': started, 'completed_at': datetime.now(timezone.utc).isoformat(), 'runtime_seconds': time.monotonic() - timer,
                              'training_timestamp': None, 'model_parameters': {target: estimator_parameters(bundle['calibrated_models'][target]) for target in TARGET_NAMES}},
               'data_quality': {'rows': len(raw), 'missing_values': {str(key): int(value) for key, value in raw.isna().sum().items()}, 'duplicates': duplicates,
                                'leakage_checks': [{'check': 'Target columns excluded', 'passed': not bool(set(feature_names) & set(LEAKAGE_COLUMNS)), 'detail': 'Cath/CAD/LAD/LCX/RCA never enter features.'},
                                                   {'check': 'Saved feature compatibility', 'passed': background_matches, 'detail': f'{len(feature_names)} features; saved reference vectors reproduced exactly.'},
                                                   {'check': 'Fold-only learned preprocessing', 'passed': True, 'detail': 'Estimator pipelines refit imputation/scaling in every outer and inner calibration fold.'},
                                                   {'check': 'Unique complete OOF scoring', 'passed': True, 'detail': 'Every outcome scored once by a clone trained without its outer test fold.'},
                                                   {'check': 'Duplicate full rows', 'passed': duplicates == 0, 'detail': f'{duplicates} duplicate complete records; grouped patient validation not possible without patient identifiers.'},
                                                   {'check': 'Independent external cohort', 'passed': False, 'detail': 'No independent external dataset was supplied.'}]},
               'models': models_metadata, 'targets': results, 'limitations': limitations,
               'supplied_benchmarks': {'targets': json.loads(frozen['input_bytes'][benchmark_path]).get('targets', {}) if benchmark_path in frozen['input_bytes'] else {}}}
    audit = {'schema_version': 1, 'run_id': run_id, 'targets': audit_targets}
    # Validate the full public artifact before atomically publishing the run.
    validated = Summary.model_validate(summary)
    OOF.model_validate(audit).validate_against(validated)
    assert_unchanged(frozen)
    return publish_run(output_directory, summary, audit, frozen['source_bytes'])


def verify_run(directory):
    directory = Path(directory)
    from backend.model_quality.service import read_json
    pointer = Pointer.model_validate(read_json((directory / 'current.json').read_bytes())).model_dump()
    run = directory / 'runs' / pointer['run_id']
    summary, audit = read_json((run / 'summary.json').read_bytes()), read_json((run / 'oof.json').read_bytes())
    if file_hash(run / 'summary.json') != pointer['summary_sha256'] or file_hash(run / 'oof.json') != pointer['oof_sha256']:
        raise ValueError('Evaluation artifact integrity check failed')
    validated = Summary.model_validate(summary)
    if validated.run_id != pointer['run_id']:
        raise ValueError('Pointer identity mismatch')
    OOF.model_validate(audit).validate_against(validated)
    for relative, digest in summary['provenance']['source_hashes'].items():
        path = Path(relative)
        if path.is_absolute() or '..' in path.parts or file_hash(run / 'source' / path) != digest:
            raise ValueError('Archived evaluation source integrity mismatch')
    print(f'Verified stored metrics, curves, bins, folds, stability and archived source for run {pointer["run_id"]}', flush=True)
    return summary

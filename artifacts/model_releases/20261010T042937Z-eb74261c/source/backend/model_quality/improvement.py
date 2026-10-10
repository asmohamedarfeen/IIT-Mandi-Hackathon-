"""Offline nested model/threshold selection; never imported by the serving API."""
import numpy as np
from sklearn.base import clone
from sklearn.calibration import CalibratedClassifierCV
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import Pipeline

from backend.model_quality.metrics import binary_metrics
from backend.model_quality.models import bounded_threads, get_candidate_models

THRESHOLDS = (.35, .4, .45, .5, .55, .6, .65)


def choose_threshold(y, probabilities, recall_floor):
    """Choose using inner-held-out labels only; keep probability scores intact."""
    rows = [(t, binary_metrics(y, probabilities, t)) for t in THRESHOLDS]
    eligible = [(t, m) for t, m in rows if m['recall'] is not None and m['recall'] >= recall_floor]
    if not eligible:
        return .5, binary_metrics(y, probabilities)
    return max(eligible, key=lambda row: (row[1]['accuracy'], -abs(row[0] - .5)))


def promotion_allowed(baseline, candidate):
    """A descriptive release gate, not a significance or clinical-validity claim."""
    return (candidate['accuracy'] > baseline['accuracy'] + 1e-12
            and candidate['recall'] >= baseline['recall'] - .02
            and candidate['roc_auc'] >= baseline['roc_auc'] - .02
            and candidate['brier_score'] <= baseline['brier_score'] + .01)


def candidate_configurations(saved, feature_names, seed=42):
    """Small fixed search space. Every learned transform stays inside calibration."""
    registry = get_candidate_models(seed)
    variants = {
        'CatBoost-d3': clone(registry['CatBoost']).set_params(depth=3, iterations=220, learning_rate=.05, l2_leaf_reg=6),
        'CatBoost-d4': clone(registry['CatBoost']).set_params(depth=4, iterations=220, learning_rate=.05, l2_leaf_reg=6),
        'LightGBM-d3': clone(registry['LightGBM']).set_params(max_depth=3, num_leaves=7, n_estimators=160, learning_rate=.04, min_child_samples=15, reg_lambda=4),
        'LightGBM-balanced': clone(registry['LightGBM']).set_params(max_depth=3, num_leaves=7, n_estimators=160, learning_rate=.04, min_child_samples=15, reg_lambda=4, class_weight='balanced'),
        'XGBoost-d2': clone(registry['XGBoost']).set_params(max_depth=2, n_estimators=160, learning_rate=.05, min_child_weight=5, reg_lambda=5),
        'RandomForest-d6': clone(registry['RandomForest']).set_params(n_estimators=160, max_depth=6, min_samples_leaf=3, class_weight=None),
        'ExtraTrees-leaf5': clone(registry['ExtraTrees']).set_params(n_estimators=160, max_depth=None, min_samples_leaf=5, class_weight=None),
    }
    # Ablate proxy/duplicate-derived features while retaining the deployed input order.
    raw_indices = [i for i, name in enumerate(feature_names) if '_' not in name]
    configurations = {'Baseline': bounded_threads(saved)}
    for name, model in variants.items():
        stages = [('impute', SimpleImputer(strategy='median')), ('model', bounded_threads(model))]
        pipeline = Pipeline(stages)
        configurations[name] = CalibratedClassifierCV(pipeline, method='sigmoid', cv=3, n_jobs=1)
        if name in ('CatBoost-d3', 'LightGBM-d3'):
            selected = ColumnTransformer([('raw', SimpleImputer(strategy='median'), raw_indices)])
            configurations[name + '-raw'] = CalibratedClassifierCV(
                Pipeline([('select', selected), ('model', bounded_threads(model))]),
                method='sigmoid', cv=3, n_jobs=1)
    return configurations


def select_configuration(X, y, configurations, inner_folds=3, seed=42):
    """Select model and threshold without consulting any outer test observation."""
    splits = list(StratifiedKFold(inner_folds, shuffle=True, random_state=seed).split(X, y))
    probabilities = {}
    for name, model in configurations.items():
        probabilities[name] = cross_val_predict(clone(model), X, y, cv=splits,
                                               method='predict_proba', n_jobs=1)[:, 1]
    reference = binary_metrics(y, probabilities['Baseline'])
    choices = [('Baseline', .5, reference)]
    for name, probability in probabilities.items():
        threshold, metrics = choose_threshold(y, probability, max(0, reference['recall'] - .02))
        if (metrics['recall'] >= reference['recall'] - .02
                and metrics['roc_auc'] >= reference['roc_auc'] - .02
                and metrics['brier_score'] <= reference['brier_score'] + .01):
            choices.append((name, threshold, metrics))
    name, threshold, metrics = max(choices, key=lambda row: (
        row[2]['accuracy'], -row[2]['brier_score'], -abs(row[1] - .5)))
    return {'model': name, 'threshold': threshold, 'inner_metrics': metrics,
            'inner_baseline_metrics': reference}


def evaluate_nested(X, y, configurations, outer_folds=10, inner_folds=3, seed=42):
    """Compare a selected strategy with a cloned baseline on identical outer folds."""
    X, y = np.asarray(X), np.asarray(y, dtype=int)
    probabilities = np.full(len(y), np.nan)
    baseline = np.full(len(y), np.nan)
    predictions = np.zeros(len(y), dtype=int)
    fold_ids = np.zeros(len(y), dtype=int)
    folds = []
    splits = StratifiedKFold(outer_folds, shuffle=True, random_state=seed).split(X, y)
    for fold, (train, test) in enumerate(splits, 1):
        selected = select_configuration(X[train], y[train], configurations, inner_folds, seed + fold)
        baseline_fit = clone(configurations['Baseline']).fit(X[train], y[train])
        baseline[test] = baseline_fit.predict_proba(X[test])[:, 1]
        fitted = baseline_fit if selected['model'] == 'Baseline' else clone(configurations[selected['model']]).fit(X[train], y[train])
        probabilities[test] = fitted.predict_proba(X[test])[:, 1]
        predictions[test] = probabilities[test] >= selected['threshold']
        fold_ids[test] = fold
        folds.append({'fold': fold, 'train_indices': train.tolist(), 'test_indices': test.tolist(), **selected})
        print(f'  outer fold {fold}/{outer_folds}: {selected["model"]}, threshold={selected["threshold"]}', flush=True)
    if not np.isfinite(probabilities).all() or not np.isfinite(baseline).all() or np.any(fold_ids == 0):
        raise ValueError('Incomplete outer-held-out predictions')
    return {'probabilities': probabilities.tolist(), 'baseline_probabilities': baseline.tolist(),
            'predictions': predictions.tolist(), 'fold_ids': fold_ids.tolist(), 'folds': folds,
            'baseline_metrics': binary_metrics(y, baseline),
            'candidate_metrics': binary_metrics(y, probabilities, y_pred=predictions)}

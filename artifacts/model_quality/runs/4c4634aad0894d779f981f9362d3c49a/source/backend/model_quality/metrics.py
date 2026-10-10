"""One full-precision metric/curve implementation for training, OOF and APIs."""
from itertools import combinations

import numpy as np
from scipy.stats import rankdata, spearmanr
from sklearn.metrics import (accuracy_score, average_precision_score, balanced_accuracy_score,
                            brier_score_loss, cohen_kappa_score, log_loss,
                            matthews_corrcoef, precision_recall_curve, roc_auc_score, roc_curve)

METRIC_KEYS = ('accuracy', 'precision', 'recall', 'sensitivity', 'specificity', 'f1',
               'roc_auc', 'pr_auc', 'average_precision', 'mcc', 'cohen_kappa',
               'balanced_accuracy', 'log_loss', 'brier_score', 'ece')


def validated_arrays(y, probability):
    y, p = np.asarray(y), np.asarray(probability, dtype=float)
    if y.ndim != 1 or p.ndim != 1 or len(y) != len(p) or len(y) == 0:
        raise ValueError('Labels and probabilities must be nonempty matching vectors')
    if not np.isin(y, [0, 1]).all() or not np.isfinite(p).all() or ((p < 0) | (p > 1)).any():
        raise ValueError('Expected binary labels and finite probabilities in [0, 1]')
    return y.astype(int), p


def reliability(y, probability, bins=10):
    y, p = validated_arrays(y, probability)
    assignments = np.minimum((p * bins).astype(int), bins - 1)
    rows = []
    for i in range(bins):
        mask = assignments == i
        rows.append({'lower': i / bins, 'upper': (i + 1) / bins, 'count': int(mask.sum()),
                     'mean_probability': float(p[mask].mean()) if mask.any() else None,
                     'fraction_positive': float(y[mask].mean()) if mask.any() else None})
    return rows


def threshold_metrics(y, probability, threshold=.5):
    y, p = validated_arrays(y, probability)
    if not np.isfinite(threshold) or not 0 <= threshold <= 1:
        raise ValueError('Threshold must be in [0, 1]')
    predicted = p >= threshold
    tn = int(((y == 0) & ~predicted).sum())
    fp = int(((y == 0) & predicted).sum())
    fn = int(((y == 1) & ~predicted).sum())
    tp = int(((y == 1) & predicted).sum())
    ratio = lambda numerator, denominator: numerator / denominator if denominator else None
    return {'threshold': float(threshold), 'tn': tn, 'fp': fp, 'fn': fn, 'tp': tp,
            'precision': ratio(tp, tp + fp), 'recall': ratio(tp, tp + fn),
            'sensitivity': ratio(tp, tp + fn), 'specificity': ratio(tn, tn + fp),
            'f1': ratio(2 * tp, 2 * tp + fp + fn)}


def binary_metrics(y, probability, threshold=.5, y_pred=None):
    y, p = validated_arrays(y, probability)
    counts = threshold_metrics(y, p, threshold)
    predicted = (p >= threshold).astype(int)
    if y_pred is not None:
        supplied, _ = validated_arrays(y_pred, p)
        if len(supplied) != len(y):
            raise ValueError('Prediction length differs from labels')
        predicted = supplied
        counts = {**threshold_metrics(y, predicted.astype(float), .5), 'threshold': float(threshold)}
    both_classes = len(np.unique(y)) == 2
    precision, recall, _ = precision_recall_curve(y, p) if y.sum() else ([], [], [])
    mcc_denominator = (counts['tp'] + counts['fp']) * (counts['tp'] + counts['fn']) * (counts['tn'] + counts['fp']) * (counts['tn'] + counts['fn'])
    kappa = float(cohen_kappa_score(y, predicted)) if both_classes or len(np.unique(predicted)) == 2 else None
    bins = reliability(y, p)
    return {**counts,
            'accuracy': float(accuracy_score(y, predicted)),
            'roc_auc': float(roc_auc_score(y, p)) if both_classes else None,
            'pr_auc': float(np.trapezoid(precision[::-1], recall[::-1])) if y.sum() else None,
            'average_precision': float(average_precision_score(y, p)) if y.sum() else None,
            'mcc': float(matthews_corrcoef(y, predicted)) if mcc_denominator else None,
            'cohen_kappa': kappa if kappa is not None and np.isfinite(kappa) else None,
            'balanced_accuracy': float(balanced_accuracy_score(y, predicted)) if both_classes else None,
            'log_loss': float(log_loss(y, p, labels=[0, 1])),
            'brier_score': float(brier_score_loss(y, p)),
            'ece': sum(row['count'] / len(y) * abs(row['mean_probability'] - row['fraction_positive']) for row in bins if row['count'])}


def diagnostics(y, probability):
    y, p = validated_arrays(y, probability)
    metrics = binary_metrics(y, p)
    if len(np.unique(y)) == 2:
        fpr, tpr, thresholds = roc_curve(y, p, drop_intermediate=False)
        roc = {'fpr': fpr.tolist(), 'tpr': tpr.tolist(), 'thresholds': [float(t) if np.isfinite(t) else None for t in thresholds]}
    else:
        roc = {'fpr': [], 'tpr': [], 'thresholds': []}
    if y.sum():
        precision, recall, thresholds = precision_recall_curve(y, p)
        pr = {'precision': precision.tolist(), 'recall': recall.tolist(), 'thresholds': thresholds.tolist()}
    else:
        pr = {'precision': [], 'recall': [], 'thresholds': []}
    bins = reliability(y, p)
    return {'confusion_matrix': {key: metrics[key] for key in ('tn', 'fp', 'fn', 'tp', 'threshold')},
            'calibration': bins, 'probability_histogram': [{'lower': r['lower'], 'upper': r['upper'], 'count': r['count']} for r in bins],
            'roc': roc, 'pr': pr,
            'thresholds': [threshold_metrics(y, p, i / 100) for i in range(101)],
            'undefined_metrics': {key: 'Undefined for the observed class/prediction distribution or zero denominator.' for key in METRIC_KEYS if metrics[key] is None}}


def stability_summary(values, feature_names, method, top_k=10):
    values = np.asarray(values, dtype=float)
    if values.ndim != 2 or values.shape[1] != len(feature_names) or len(values) < 2 or not np.isfinite(values).all():
        raise ValueError('Stability requires finite fold-by-feature values')
    ranks = np.asarray([rankdata(-row, method='average') for row in values])
    tops = [set(np.argsort(-row, kind='stable')[:min(top_k, len(row))]) for row in values]
    overlap, correlation = [], []
    for i, j in combinations(range(len(values)), 2):
        overlap.append(len(tops[i] & tops[j]) / len(tops[i] | tops[j]))
        if np.ptp(ranks[i]) and np.ptp(ranks[j]):
            correlation.append(float(spearmanr(ranks[i], ranks[j]).statistic))
    features = [{'feature': name, 'mean': float(values[:, i].mean()), 'std': float(values[:, i].std(ddof=1)),
                 'fold_values': values[:, i].tolist(), 'rank_mean': float(ranks[:, i].mean()),
                 'rank_std': float(ranks[:, i].std(ddof=1)), 'top_k_frequency': sum(i in top for top in tops) / len(tops)} for i, name in enumerate(feature_names)]
    return {'model': 'XGBoost', 'method': method, 'features': sorted(features, key=lambda row: -row['mean']),
            'mean_rank_correlation': float(np.mean(correlation)) if correlation else None,
            'mean_top_k_jaccard': float(np.mean(overlap)), 'top_k': min(top_k, len(feature_names))}

"""Validation at the boundary between offline evaluation and public API."""
import math
import re
import numpy as np
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

TARGETS = {'CAD', 'LAD', 'LCX', 'RCA'}


class Pointer(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    run_id: str = Field(pattern=r'^[a-f0-9]{8,64}$')
    summary_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    oof_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')


def finite_tree(value):
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError('Non-finite artifact number')
    if isinstance(value, dict):
        for item in value.values():
            finite_tree(item)
    elif isinstance(value, list):
        for item in value:
            finite_tree(item)


def count(value):
    if type(value) is not int or value < 0:
        raise ValueError('Invalid count')
    return value


def distribution(value):
    if count(value['positive']) + count(value['negative']) != count(value['total']):
        raise ValueError('Class distribution does not sum to cohort')


def probability(value, nullable=False):
    if nullable and value is None:
        return
    if type(value) not in (int, float) or not 0 <= value <= 1:
        raise ValueError('Probability outside [0,1]')


def evidence_equal(expected, actual):
    """Compare rederived values across pinned-library patch/platform rounding."""
    if isinstance(expected, dict) and isinstance(actual, dict):
        return expected.keys() == actual.keys() and all(evidence_equal(expected[key], actual[key]) for key in expected)
    if isinstance(expected, list) and isinstance(actual, list):
        return len(expected) == len(actual) and all(evidence_equal(a, b) for a, b in zip(expected, actual))
    if isinstance(expected, (int, float)) and not isinstance(expected, bool) and isinstance(actual, (int, float)) and not isinstance(actual, bool):
        return math.isclose(expected, actual, rel_tol=1e-9, abs_tol=1e-12)
    return expected == actual


class Summary(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    schema_version: Literal[1]
    run_id: str = Field(pattern=r'^[a-f0-9]{8,64}$')
    generated_at: str
    selected_model: str
    provenance: dict[str, Any]
    data_quality: dict[str, Any]
    models: list[dict[str, Any]]
    targets: dict[str, Any]
    limitations: list[str]
    supplied_benchmarks: dict[str, Any]

    @model_validator(mode='after')
    def validate_contents(self):
        finite_tree(self.model_dump())
        ids = [m['id'] for m in self.models]
        if not ids or len(set(ids)) != len(ids) or self.selected_model not in ids:
            raise ValueError('Invalid model coverage')
        if any(not isinstance(identifier, str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]{0,63}', identifier) for identifier in ids):
            raise ValueError('Invalid model identifier')
        datetime.fromisoformat(self.generated_at.replace('Z', '+00:00'))
        for model in self.models:
            for key in ('name', 'production_configuration', 'configuration_source', 'parameters'):
                if key not in model:
                    raise ValueError('Incomplete model configuration')
        for key in ('dataset_sha256', 'model_sha256', 'feature_sha256'):
            if not re.fullmatch('[a-f0-9]{64}', self.provenance[key]):
                raise ValueError('Invalid provenance hash')
        for key in ('git_commit', 'git_dirty', 'source_hashes', 'python_version', 'library_versions', 'random_seed', 'outer_folds', 'inner_folds', 'command', 'preprocessing', 'model_parameters'):
            if key not in self.provenance:
                raise ValueError('Incomplete provenance')
        if type(self.provenance['git_dirty']) is not bool or type(self.provenance['inner_folds']) is not int or self.provenance['inner_folds'] < 2:
            raise ValueError('Invalid provenance configuration')
        for source_hash in self.provenance['source_hashes'].values():
            if not isinstance(source_hash, str) or not re.fullmatch('[a-f0-9]{64}', source_hash):
                raise ValueError('Invalid source hash')
        rows = count(self.data_quality['rows'])
        if rows == 0 or type(self.provenance['outer_folds']) is not int or self.provenance['outer_folds'] < 2:
            raise ValueError('Evaluation requires nonempty outer folds')
        if count(self.data_quality['duplicates']) > rows:
            raise ValueError('Duplicate count exceeds cohort')
        for missing in self.data_quality['missing_values'].values():
            if count(missing) > rows:
                raise ValueError('Missing count exceeds cohort')
        for check in self.data_quality['leakage_checks']:
            if type(check['passed']) is not bool or not isinstance(check['check'], str) or not isinstance(check['detail'], str):
                raise ValueError('Invalid leakage check')
        if set(self.targets) != TARGETS:
            raise ValueError('Incomplete targets')
        for target in self.targets.values():
            distribution(target['class_distribution'])
            if target['class_distribution']['total'] != rows:
                raise ValueError('Inconsistent target cohort')
            folds = target['folds']
            if len(folds) != self.provenance['outer_folds'] or len({f['fold'] for f in folds}) != len(folds):
                raise ValueError('Invalid fold coverage')
            if sum(f['test']['total'] for f in folds) != rows:
                raise ValueError('Test folds do not cover cohort')
            for fold in folds:
                distribution(fold['train']); distribution(fold['test'])
                if fold['train']['total'] + fold['test']['total'] != rows:
                    raise ValueError('Invalid fold cohort')
            if set(target['models']) != set(ids):
                raise ValueError('Incomplete target model coverage')
            for model in target['models'].values():
                if len(model['fold_metrics']) != len(folds):
                    raise ValueError('Incomplete fold metrics')
                for metric in model['metrics'].values():
                    if metric is not None and type(metric) not in (float, int):
                        raise ValueError('Invalid metric')
                for key, metric in model['metrics'].items():
                    if metric is None:
                        if key not in model['undefined_metrics']:
                            raise ValueError('Undefined metric has no explanation')
                    elif key in ('mcc', 'cohen_kappa'):
                        if not -1 <= metric <= 1:
                            raise ValueError('Correlation metric outside [-1,1]')
                    elif key != 'log_loss':
                        probability(metric)
                    elif metric < 0:
                        raise ValueError('Negative log loss')
                diagnostics = model['diagnostics']
                for cm in [diagnostics['confusion_matrix'], *diagnostics['thresholds']]:
                    probability(cm['threshold'])
                    if sum(count(cm[k]) for k in ('tn', 'fp', 'fn', 'tp')) != rows:
                        raise ValueError('Invalid confusion cohort')
                calibration = diagnostics['calibration']
                if sum(count(b['count']) for b in calibration) != rows:
                    raise ValueError('Invalid calibration cohort')
                for b in calibration:
                    for k in ('lower', 'upper', 'mean_probability', 'fraction_positive'):
                        probability(b[k], nullable=k in ('mean_probability', 'fraction_positive'))
                    if b['lower'] > b['upper']:
                        raise ValueError('Invalid calibration bounds')
                for curve, keys in [('roc', ('fpr', 'tpr')), ('pr', ('precision', 'recall'))]:
                    data = diagnostics[curve]
                    if len(data[keys[0]]) != len(data[keys[1]]):
                        raise ValueError('Invalid curve lengths')
                    expected = max(0, len(data[keys[0]]) - (curve == 'pr'))
                    if len(data['thresholds']) != expected:
                        raise ValueError('Invalid curve thresholds')
                    for key in (*keys, 'thresholds'):
                        for value in data[key]:
                            probability(value, nullable=key == 'thresholds')
            for key in ('feature_stability', 'shap_stability'):
                stability = target[key]
                for feature in stability['features']:
                    if len(feature['fold_values']) != len(folds):
                        raise ValueError('Invalid stability fold coverage')
                    probability(feature['top_k_frequency'])
                    if feature['std'] < 0 or feature['rank_std'] < 0 or feature['rank_mean'] < 1:
                        raise ValueError('Invalid stability dispersion/rank')
        return self


class OOF(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    schema_version: Literal[1]
    run_id: str = Field(pattern=r'^[a-f0-9]{8,64}$')
    targets: dict[str, Any]

    def validate_against(self, summary: Summary):
        finite_tree(self.model_dump())
        if self.run_id != summary.run_id or set(self.targets) != TARGETS:
            raise ValueError('OOF identity mismatch')
        for name, target in self.targets.items():
            labels, folds = target['labels'], target['fold_ids']
            expected = summary.targets[name]
            if len(labels) != expected['class_distribution']['total'] or any(type(y) is not int or y not in (0, 1) for y in labels):
                raise ValueError('Invalid OOF labels')
            if sum(labels) != expected['class_distribution']['positive'] or len(folds) != len(labels):
                raise ValueError('OOF cohort mismatch')
            for fold in expected['folds']:
                selected = [y for y, f in zip(labels, folds) if f == fold['fold']]
                if len(selected) != fold['test']['total'] or sum(selected) != fold['test']['positive']:
                    raise ValueError('OOF fold cohort mismatch')
            if set(folds) != {f['fold'] for f in expected['folds']} or set(target['probabilities']) != set(expected['models']):
                raise ValueError('OOF fold/model coverage mismatch')
            for values in target['probabilities'].values():
                if len(values) != len(labels):
                    raise ValueError('Invalid OOF probability length')
                for value in values:
                    probability(value)
            # Aggregate evidence and the private audit must describe the same OOF result.
            from backend.model_quality.metrics import METRIC_KEYS, binary_metrics, diagnostics, stability_summary
            labels_array, folds_array = np.asarray(labels), np.asarray(folds)
            if summary.provenance.get('feature_names') and 'splits' not in target:
                raise ValueError('Missing audited splits')
            if 'splits' in target:
                splits = target['splits']
                if len(splits) != len(expected['folds']) or {s['fold'] for s in splits} != set(folds):
                    raise ValueError('Incomplete audited splits')
                universe = set(range(len(labels)))
                for split in splits:
                    train, test = split['train_indices'], split['test_indices']
                    if any(type(i) is not int for i in train + test) or len(set(train)) != len(train) or len(set(test)) != len(test) or set(train) & set(test) or set(train) | set(test) != universe:
                        raise ValueError('Invalid audited partition')
                    if set(test) != set(np.flatnonzero(folds_array == split['fold']).tolist()):
                        raise ValueError('Audited split does not match OOF fold')
            for fold in expected['folds']:
                training = labels_array[folds_array != fold['fold']]
                if len(training) != fold['train']['total'] or int(training.sum()) != fold['train']['positive']:
                    raise ValueError('Training class count mismatch')
            for identifier, values in target['probabilities'].items():
                entry = expected['models'][identifier]
                if summary.provenance.get('feature_names') and (len(entry.get('fold_model_hashes', [])) != len(expected['folds']) or any(not re.fullmatch('[a-f0-9]{64}', value) for value in entry['fold_model_hashes'])):
                    raise ValueError('Missing fitted fold model fingerprints')
                threshold = entry['diagnostics']['confusion_matrix']['threshold']
                computed = binary_metrics(labels, values, threshold)
                if set(entry['metrics']) != set(METRIC_KEYS):
                    raise ValueError('Incomplete metric coverage')
                for key, actual in entry['metrics'].items():
                    calculated = computed[key]
                    if actual is None or calculated is None:
                        if actual is not calculated:
                            raise ValueError('OOF metric mismatch')
                    elif not math.isclose(actual, calculated, rel_tol=1e-9, abs_tol=1e-12):
                        raise ValueError('OOF metric mismatch')
                if any(entry['diagnostics']['confusion_matrix'][key] != computed[key] for key in ('tn', 'fp', 'fn', 'tp')):
                    raise ValueError('OOF confusion mismatch')
                if not evidence_equal(entry['diagnostics'], diagnostics(labels, values)):
                    raise ValueError('OOF diagnostic mismatch')
                probabilities_array = np.asarray(values)
                recomputed_folds = []
                for fold, recorded in zip(expected['folds'], entry['fold_metrics']):
                    mask = folds_array == fold['fold']
                    metrics = binary_metrics(labels_array[mask], probabilities_array[mask])
                    metrics = {key: metrics[key] for key in METRIC_KEYS}
                    if not evidence_equal({key: recorded.get(key) for key in METRIC_KEYS}, metrics):
                        raise ValueError('OOF fold metric mismatch')
                    recomputed_folds.append(metrics)
                if 'fold_summary' in entry:
                    dispersion = {key: {'mean': float(np.mean([row[key] for row in recomputed_folds if row[key] is not None])),
                                        'std': float(np.std([row[key] for row in recomputed_folds if row[key] is not None], ddof=1))}
                                  for key in METRIC_KEYS if sum(row[key] is not None for row in recomputed_folds) >= 2}
                    if not evidence_equal(entry['fold_summary'], dispersion):
                        raise ValueError('OOF fold dispersion mismatch')
            names = summary.provenance.get('feature_names', [])
            if any(expected[key]['features'] for key in ('feature_stability', 'shap_stability')):
                explanation = target.get('explanation_audit', {})
                shap = np.asarray(explanation.get('shap_values', []), dtype=float)
                if shap.shape != (len(labels), len(names)) or not np.isfinite(shap).all():
                    raise ValueError('Invalid held-out SHAP audit')
                means = [np.abs(shap[folds_array == fold['fold']]).mean(axis=0) for fold in expected['folds']]
                for key, values in [('shap_stability', means), ('feature_stability', explanation.get('permutation_fold_importance', []))]:
                    recorded = expected[key]
                    if not evidence_equal(stability_summary(values, names, recorded['method'], recorded['top_k']), recorded):
                        raise ValueError('OOF stability mismatch')

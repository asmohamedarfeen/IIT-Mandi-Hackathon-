"""Export aggregate release-procedure error counts; never exports patient rows or identifiers."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.cardio.service.feature_service import extract_targets
from backend.model_quality.metrics import binary_metrics, validated_arrays


def group_metrics(labels, probabilities, predictions, mask):
    y, p, predicted = labels[mask], probabilities[mask], predictions[mask]
    if not len(y):
        return {'n': 0, 'positive': 0, 'negative': 0, 'metrics': None, 'warning': 'Empty subgroup'}
    values = binary_metrics(y, p, y_pred=predicted)
    return {'n': len(y), 'positive': int(y.sum()), 'negative': int(len(y)-y.sum()),
            'metrics': {key: values[key] for key in ('tn','fp','fn','tp','accuracy','recall','specificity','roc_auc','brier_score')},
            'warning': 'Small subgroup; descriptive unstable estimates' if len(y)<30 or min(y.sum(),len(y)-y.sum())<10 else 'Internal descriptive subgroup; not external fairness validation'}


def error_patterns(raw, labels, predictions):
    """Descriptive measurement summaries by outcome, with no individual records."""
    groups = {}
    for name, actual, predicted in [('false_negative', 1, 0), ('false_positive', 0, 1),
                                    ('true_positive', 1, 1), ('true_negative', 0, 0)]:
        selected = raw.loc[(labels == actual) & (predictions == predicted)]
        measurements = {}
        # Recorded measurements only: no outcome, identifiers or engineered proxies.
        for field in ('Age', 'BP', 'FBS', 'CR', 'TG', 'LDL', 'HDL', 'EF-TTE'):
            if field not in raw:
                continue
            values = pd.to_numeric(selected[field], errors='coerce').replace([np.inf, -np.inf], np.nan).dropna()
            quartiles = values.quantile([.25, .5, .75]).tolist() if len(values) >= 10 else [None] * 3
            measurements[field] = {'available': len(values), 'missing': len(selected) - len(values),
                                   'median': quartiles[1], 'q1': quartiles[0], 'q3': quartiles[2]}
        groups[name] = {'n': len(selected), 'measurements': measurements}
    return {'groups': groups, 'limitations': 'Exploratory post-development comparisons; not causal effects or independent validation. Quartiles suppressed when fewer than 10 measurements are available. Counts are descriptive; no patient rows or measurement ranges are exported.'}


def analyze(release, dataset, logistic_baseline=False):
    summary_path, oof_path = release/'summary.json', release/'oof.json'
    summary, oof = json.loads(summary_path.read_text()), json.loads(oof_path.read_text())
    if sha256(dataset.read_bytes()).hexdigest() != summary['dataset_sha256'] or oof['run_id'] != summary['run_id']:
        raise ValueError('Dataset or release identity mismatch')
    raw = pd.read_excel(dataset)
    targets = extract_targets(raw)
    result = {'release_id': summary['run_id'], 'deployed': summary['deployed'], 'dataset_sha256': summary['dataset_sha256'],
              'summary_sha256': sha256(summary_path.read_bytes()).hexdigest(), 'oof_sha256': sha256(oof_path.read_bytes()).hexdigest(),
              'method': 'Reaggregation of archived outer-OOF release-selection procedure, using each outer-fold selected threshold; retained targets use baseline threshold. Does not score final fitted weights.',
              'limitations': ['No new validation or improvement experiment is performed.', 'Release selected after inspecting outer outcomes; prior tuning and cohort reuse add selection bias.', 'Subgroups were chosen after model development and are exploratory; no confidence or fairness claims.', 'Small groups have unstable estimates; denominators are explicitly reported.', 'No patient rows, identifiers, individual predictions or probabilities are exported.'], 'targets': {}}
    masks = {'all': np.ones(len(raw),dtype=bool), 'sex_female': raw['Sex'].astype(str).str.lower().isin(['female','fmale','0']).to_numpy(),
             'sex_male': raw['Sex'].astype(str).str.lower().isin(['male','1']).to_numpy(), 'age_below_55': (raw['Age']<55).to_numpy(),
             'age_55_or_more': (raw['Age']>=55).to_numpy(), 'DM_present': (raw['DM']==1).to_numpy(), 'DM_absent': (raw['DM']==0).to_numpy(),
             'HTN_present': (raw['HTN']==1).to_numpy(), 'HTN_absent': (raw['HTN']==0).to_numpy()}
    for target, series in targets.items():
        archived = oof['targets'][target]
        y = series.to_numpy(dtype=int)
        if not np.array_equal(y, archived['labels']):
            raise ValueError('Outcome row alignment mismatch')
        promoted = summary['targets'][target]['promoted']
        p = np.asarray(archived['probabilities'] if promoted else archived['baseline_probabilities'])
        predicted = np.asarray(archived['predictions']) if promoted else (p >= summary['targets'][target].get('baseline_threshold',.5)).astype(int)
        validated_arrays(y,p); validated_arrays(predicted,p)
        baseline_p = np.asarray(archived['baseline_probabilities'])
        baseline_pred = baseline_p >= summary['targets'][target].get('baseline_threshold',.5)
        before_correct, after_correct = baseline_pred==y, predicted==y
        folds = np.asarray(archived['fold_ids'])
        paired = {'newly_correct': int((~before_correct & after_correct).sum()), 'newly_wrong': int((before_correct & ~after_correct).sum()),
                  'net_correct_change': int(after_correct.sum()-before_correct.sum()),
                  'accuracy_difference': float(after_correct.mean()-before_correct.mean()),
                  'fold_accuracy_differences': [{'fold':int(fold),'n':int((folds==fold).sum()),'difference':float(after_correct[folds==fold].mean()-before_correct[folds==fold].mean())} for fold in sorted(set(folds))],
                  'uncertainty_note': 'Fold differences are descriptive. Overlapping training sets, post hoc release selection and earlier cohort reuse prevent treating folds/rows as independent untouched experiments. No significance claim or inferential confidence interval.'}
        majority = int(y.sum() >= len(y)/2)
        result['targets'][target] = {'promoted': promoted, 'selected_prediction_source': 'Nested selection OOF fold-specific decisions' if promoted else 'Retained baseline OOF decisions',
                                    'error_patterns': error_patterns(raw, y, predicted),
                                    'paired_baseline_comparison': paired, 'feature_availability': {'missing_recorded_values': int(raw.isna().sum().sum()), 'note':'Recorded workbook complete; application defaulted inputs need separate prospective evaluation'},
                                    'majority_baseline': {'prediction': majority, 'n': len(y), 'correct': int((y==majority).sum()), 'accuracy': float((y==majority).mean())},
                                    'subgroups': {name: group_metrics(y,p,predicted,mask) for name,mask in masks.items()}}
    if logistic_baseline:
        from sklearn.linear_model import LogisticRegression
        from sklearn.model_selection import StratifiedKFold
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import StandardScaler
        from backend.cardio.constants import LEAKAGE_COLUMNS
        from backend.cardio.service.feature_service import ClinicalPreprocessor
        from backend.model_quality.evaluation import evaluate_estimator
        import joblib
        bundle=joblib.load(release/'cardiovision_ensemble.joblib')
        inputs=raw.drop(columns=LEAKAGE_COLUMNS,errors='ignore')
        for target, series in targets.items():
            estimator=Pipeline([('preprocess',ClinicalPreprocessor(bundle['feature_names'])),('scale',StandardScaler()),('model',LogisticRegression(C=1,max_iter=2000,random_state=42))])
            splits=list(StratifiedKFold(10,shuffle=True,random_state=42).split(inputs,series))
            evaluated,_=evaluate_estimator(estimator,inputs,series.to_numpy(),splits)
            result['targets'][target]['logistic_baseline']={'method':'New fixed untuned logistic comparator OOF, 10 stratified folds seed42; training-only preprocessing/scaling; C1, max_iter2000, threshold0.5. Same historically reused cohort; no external validation.', 'metrics':evaluated['metrics'], 'confusion':evaluated['diagnostics']['confusion_matrix']}
        result['baseline_source_hashes']={name:sha256((ROOT/name).read_bytes()).hexdigest() for name in ['scripts/analyze_release_errors.py','backend/model_quality/evaluation.py','backend/cardio/service/feature_service.py','backend/model_quality/metrics.py']}
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release',type=Path,required=True)
    parser.add_argument('--dataset',type=Path,default=ROOT/'extention of Z-Alizadeh sani dataset.xlsx')
    parser.add_argument('--logistic-baseline',action='store_true',help='Fit a fixed untuned logistic comparator with fold-only preprocessing; does not deploy')
    parser.add_argument('--output',type=Path,default=ROOT/'artifacts/release_error_analysis.json')
    args=parser.parse_args()
    result=analyze(args.release,args.dataset,args.logistic_baseline)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(f'Aggregate error analysis written to {args.output}')


if __name__=='__main__':
    main()

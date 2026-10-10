import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd
from scripts.analyze_release_errors import analyze, group_metrics, ROOT


def test_error_counts_keep_subgroup_denominators_and_undefined_auc():
    values=group_metrics(np.array([1,1]),np.array([.2,.8]),np.array([0,1]),np.array([True,True]))
    assert values['n']==2 and values['positive']==2 and values['negative']==0
    assert values['metrics']['fn']==1 and values['metrics']['tp']==1
    assert values['metrics']['roc_auc'] is None
    assert 'Small subgroup' in values['warning']


def test_release_analysis_contains_no_individual_rows_and_matches_release_counts():
    release=ROOT/'artifacts/model_releases/20261010T044519Z-77a76019'
    result=analyze(release,ROOT/'extention of Z-Alizadeh sani dataset.xlsx')
    original=json.loads((release/'summary.json').read_text())
    for target, values in result['targets'].items():
        assert values['subgroups']['all']['n']==303
        assert values['subgroups']['all']['metrics']['recall']==original['targets'][target]['release_procedure_metrics']['recall']
    encoded=json.dumps(result)
    assert 'patient_id' not in encoded and 'train_indices' not in encoded
    assert 'labels' not in result and 'probabilities' not in result
    for target in ('LCX', 'RCA'):
        groups = result['targets'][target]['error_patterns']['groups']
        assert groups['false_negative']['n'] == original['targets'][target]['release_procedure_metrics']['fn']
        assert groups['false_positive']['n'] == original['targets'][target]['release_procedure_metrics']['fp']
        assert groups['false_negative']['measurements']['Age']['available'] == groups['false_negative']['n']


def test_error_patterns_report_missing_values_and_suppress_small_groups():
    from scripts.analyze_release_errors import error_patterns
    raw = pd.DataFrame({'Age': [50.] * 10 + [float('nan')] + [80.]})
    patterns = error_patterns(raw, np.ones(12, dtype=int), np.array([0] * 11 + [1]))
    missed = patterns['groups']['false_negative']
    assert missed['n'] == 11
    assert missed['measurements']['Age'] == {'available': 10, 'missing': 1, 'median': 50., 'q1': 50., 'q3': 50.}
    assert patterns['groups']['true_positive']['measurements']['Age']['median'] is None
    assert patterns['groups']['false_positive']['n'] == 0


def test_legacy_training_cli_refuses_without_optin():
    process=subprocess.run([sys.executable,str(ROOT/'scripts/train_pipeline.py')],capture_output=True,text=True)
    assert process.returncode != 0
    assert 'Retired legacy training entry point' in process.stderr

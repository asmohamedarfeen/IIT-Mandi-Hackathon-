"""Real, tiny fitted OOF evaluation; runtime never synthesizes evidence."""
import copy
import hashlib
import json

import numpy as np
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold

from backend.model_quality.metrics import METRIC_KEYS, binary_metrics, diagnostics
from backend.model_quality.routes import get_quality_service, router
from backend.model_quality.service import QualityService


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


@pytest.fixture
def evidence(tmp_path):
    x, y = make_classification(n_samples=30, n_features=4, n_informative=3, n_redundant=0, random_state=9)
    fold_ids = np.zeros(len(y), dtype=int)
    probabilities = np.zeros(len(y))
    folds, fold_metrics = [], []
    distribution = lambda labels: {'positive': int(sum(labels)), 'negative': int(len(labels) - sum(labels)), 'total': len(labels)}
    for fold, (train, test) in enumerate(StratifiedKFold(3, shuffle=True, random_state=7).split(x, y), 1):
        fitted = LogisticRegression(random_state=7).fit(x[train], y[train])
        probabilities[test] = fitted.predict_proba(x[test])[:, 1]
        fold_ids[test] = fold
        folds.append({'fold': fold, 'train': distribution(y[train]), 'test': distribution(y[test])})
        fold_metrics.append({'fold': fold, **{k: binary_metrics(y[test], probabilities[test])[k] for k in METRIC_KEYS}})
    run_id = 'a' * 16
    model_path = tmp_path / 'production.joblib'
    model_path.write_bytes(b'production-model-fixture')
    diag = diagnostics(y, probabilities)
    target = {'class_distribution': distribution(y), 'folds': folds, 'models': {'CalibratedVoting': {'metrics': {k: binary_metrics(y, probabilities)[k] for k in METRIC_KEYS}, 'undefined_metrics': diag['undefined_metrics'], 'fold_metrics': fold_metrics, 'diagnostics': diag}}, 'feature_stability': {'model': 'XGBoost', 'method': 'test fitted folds', 'features': [], 'mean_rank_correlation': None, 'mean_top_k_jaccard': None}, 'shap_stability': {'model': 'XGBoost', 'method': 'test fitted folds', 'features': [], 'mean_rank_correlation': None, 'mean_top_k_jaccard': None}}
    summary = {'schema_version': 1, 'run_id': run_id, 'generated_at': '2026-10-09T00:00:00Z', 'selected_model': 'CalibratedVoting', 'provenance': {'dataset_sha256': digest(x.tobytes()), 'model_sha256': digest(model_path.read_bytes()), 'feature_sha256': digest(b'four features'), 'git_commit': 'test', 'git_dirty': False, 'source_hashes': {}, 'python_version': '3.11', 'library_versions': {}, 'random_seed': 7, 'outer_folds': 3, 'inner_folds': 2, 'command': 'pytest real logistic OOF fixture', 'preprocessing': {}, 'model_parameters': {}}, 'data_quality': {'rows': len(y), 'missing_values': {}, 'duplicates': 0, 'leakage_checks': []}, 'models': [{'id': 'CalibratedVoting', 'name': 'Test fitted comparator', 'production_configuration': False, 'configuration_source': 'test only', 'parameters': {}}], 'targets': {name: copy.deepcopy(target) for name in ('CAD', 'LAD', 'LCX', 'RCA')}, 'limitations': ['Tiny fitted test cohort only.'], 'supplied_benchmarks': {'targets': {}}}
    oof = {'schema_version': 1, 'run_id': run_id, 'targets': {name: {'labels': y.tolist(), 'fold_ids': fold_ids.tolist(), 'probabilities': {'CalibratedVoting': probabilities.tolist()}} for name in summary['targets']}}
    folder = tmp_path / 'runs' / run_id
    folder.mkdir(parents=True)
    def publish():
        raw_summary, raw_oof = (json.dumps(v, allow_nan=False).encode() for v in (summary, oof))
        (folder / 'summary.json').write_bytes(raw_summary); (folder / 'oof.json').write_bytes(raw_oof)
        (tmp_path / 'current.json').write_text(json.dumps({'run_id': run_id, 'summary_sha256': digest(raw_summary), 'oof_sha256': digest(raw_oof)}))
    publish()
    service = QualityService(tmp_path, model_path)
    app = FastAPI()
    app.include_router(router, prefix='/api/v1')
    app.dependency_overrides[get_quality_service] = lambda: service
    return TestClient(app), service, summary, oof, model_path, folder, publish


def test_all_aggregate_endpoints_and_exact_threshold(evidence):
    client, service, summary, oof, *_ = evidence
    overview = client.get('/api/v1/model-quality/overview')
    assert overview.status_code == 200
    assert overview.json()['status'] == 'ready'
    for path in ('models', 'reproducibility', 'cad', 'lad', 'lcx', 'rca', 'calibration', 'roc', 'pr', 'shap', 'feature-stability', 'class-distribution'):
        response = client.get('/api/v1/model-quality/' + path)
        assert response.status_code == 200, response.text
        assert 'labels' not in response.json() and 'probabilities' not in response.json()
    threshold = .437812345
    response = client.get('/api/v1/model-quality/confusion-matrix', params={'target': 'CAD', 'threshold': threshold})
    expected = binary_metrics(oof['targets']['CAD']['labels'], oof['targets']['CAD']['probabilities']['CalibratedVoting'], threshold)
    assert response.status_code == 200
    assert all(response.json()[key] == value for key, value in expected.items())
    first = service.overview(); first['targets']['CAD']['models'].clear()
    assert service.overview()['targets']['CAD']['models']


def test_staleness_and_cache_invalidation(evidence):
    client, _, summary, _, model_path, _, publish = evidence
    model_path.write_bytes(b'different production weights')
    assert client.get('/api/v1/model-quality/overview').json()['stale'] is True
    summary['limitations'].append('Republished artifact')
    publish()
    assert client.get('/api/v1/model-quality/overview').json()['limitations'][-1] == 'Republished artifact'


@pytest.mark.parametrize('params', [{'threshold': -1}, {'threshold': 'nan'}, {'threshold': 'inf'}, {'target': 'bad'}, {'model': 'missing'}])
def test_query_validation(evidence, params):
    assert evidence[0].get('/api/v1/model-quality/confusion-matrix', params=params).status_code == 422


def test_integrity_and_schema_reject_corruption(evidence):
    client, _, summary, _, _, folder, publish = evidence
    (folder / 'summary.json').write_text('{}')
    assert client.get('/api/v1/model-quality/overview').status_code == 503
    summary['targets']['CAD']['class_distribution']['total'] += 1
    publish()
    assert client.get('/api/v1/model-quality/overview').status_code == 503


def test_exports_filter_aggregate_evidence(evidence):
    client = evidence[0]
    params = {'format': 'json', 'section': 'confusion-matrices', 'target': 'LAD', 'model': 'CalibratedVoting', 'threshold': .4321}
    response = client.get('/api/v1/model-quality/report', params=params)
    assert response.status_code == 200
    assert set(response.json()['targets']) == {'LAD'}
    assert response.json()['selection']['threshold'] == .4321
    assert 'labels' not in response.text and 'probabilities' not in response.text
    for section in ('metrics', 'calibration', 'roc', 'pr', 'shap', 'feature-stability', 'results'):
        for fmt in ('json', 'csv'):
            response = client.get('/api/v1/model-quality/report', params={'format': fmt, 'section': section})
            assert response.status_code == 200
            assert 'attachment;' in response.headers['content-disposition']
    assert client.get('/api/v1/model-quality/report?format=invalid').status_code == 422


def test_pdf_contains_aggregate_report_without_private_rows(evidence):
    from io import BytesIO
    from pypdf import PdfReader
    response = evidence[0].get('/api/v1/model-quality/report', params={'format': 'pdf', 'section': 'results'})
    assert response.status_code == 200 and response.content.startswith(b'%PDF-')
    reader = PdfReader(BytesIO(response.content))
    assert 'aggregate-evidence.json' in reader.attachments
    appendix = json.loads(reader.attachments['aggregate-evidence.json'][0])
    exported = evidence[0].get('/api/v1/model-quality/report', params={'format': 'json', 'section': 'results'}).json()
    assert appendix == exported
    assert not any(key in json.dumps(appendix) for key in ('"labels"', '"fold_ids"', '"probabilities"', '"explanation_audit"'))
    assert appendix['targets']['CAD']['models']['CalibratedVoting']['fold_metrics']
    assert appendix['data_quality']['rows'] == evidence[2]['data_quality']['rows']
    text = '\n'.join(page.extract_text() for page in reader.pages)
    for expected in ('CAD', 'LAD', 'LCX', 'RCA', 'roc_auc', 'Calibration', 'Reproducibility', 'Limitations'):
        assert expected in text
    assert 'labels' not in text and 'fold_ids' not in text


@pytest.mark.parametrize('corruption', ['metric', 'oof', 'curve', 'nonfinite', 'fold', 'model', 'null'])
def test_schema_trust_boundary(evidence, corruption):
    client, _, summary, oof, _, _, publish = evidence
    target = summary['targets']['CAD']
    model = target['models']['CalibratedVoting']
    if corruption == 'metric':
        model['metrics']['accuracy'] = .123
    elif corruption == 'oof':
        oof['targets']['CAD']['probabilities']['CalibratedVoting'].pop()
    elif corruption == 'curve':
        model['diagnostics']['roc']['fpr'].append(.5)
    elif corruption == 'nonfinite':
        model['metrics']['accuracy'] = 'NaN'
    elif corruption == 'fold':
        target['folds'][0]['test']['total'] += 1
    elif corruption == 'model':
        target['models']['UnlistedModel'] = copy.deepcopy(model)
    else:
        target['models'] = None
    publish()
    assert client.get('/api/v1/model-quality/overview').status_code == 503


def test_missing_has_safe_404_without_database_or_inference(tmp_path):
    app = FastAPI(); app.include_router(router, prefix='/api/v1')
    app.dependency_overrides[get_quality_service] = lambda: QualityService(tmp_path, tmp_path / 'model')
    response = TestClient(app).get('/api/v1/model-quality/overview')
    assert response.status_code == 404
    assert str(tmp_path) not in response.text


def test_report_rejects_changed_run_and_captures_once(evidence, monkeypatch):
    client, service, summary, *_ = evidence
    mismatch = client.get('/api/v1/model-quality/report', params={'format': 'json', 'expected_run_id': 'b'*16})
    assert mismatch.status_code == 409
    monkeypatch.setattr(service, 'confusion', lambda *args: pytest.fail('Report re-read current pointer'))
    original = service._load
    loads = []
    def load_once():
        loads.append(1)
        return original()
    monkeypatch.setattr(service, '_load', load_once)
    response = client.get('/api/v1/model-quality/report', params={'format': 'json', 'section': 'confusion-matrices', 'threshold': .4567, 'expected_run_id': summary['run_id']})
    assert response.status_code == 200
    assert response.json()['selection']['threshold'] == .4567
    assert len(loads) == 1


@pytest.mark.parametrize('section', ['thresholds', 'histogram', 'class-distribution', 'reproducibility'])
def test_additional_export_sections(evidence, section):
    for fmt in ('json', 'csv', 'pdf'):
        response = evidence[0].get('/api/v1/model-quality/report', params={'format': fmt, 'section': section})
        assert response.status_code == 200, response.text[:200]


def test_csv_preserves_signed_numbers_and_escapes_only_strings():
    import csv
    from io import StringIO
    from backend.model_quality.exports import csv_export
    rows = list(csv.reader(StringIO(csv_export({'run_id': 'a'*16, 'section': 'metrics', 'numeric': -.25, 'text': '=2+2'}).decode())))
    values = {row[2]: row[3] for row in rows[1:]}
    assert values['numeric'] == '-0.25'
    assert values['text'] == "'=2+2"


def test_dataset_and_source_staleness(evidence, tmp_path):
    _, _, summary, _, model_path, folder, publish = evidence
    dataset = tmp_path / 'cohort.xlsx'; dataset.write_bytes(b'evaluated cohort')
    source = tmp_path / 'pipeline.py'; source.write_text('original code')
    summary['provenance']['dataset_sha256'] = digest(dataset.read_bytes())
    summary['provenance']['source_hashes'] = {'pipeline.py': digest(source.read_bytes())}
    publish()
    service = QualityService(folder.parent.parent, model_path, dataset_path=dataset, source_root=tmp_path)
    assert service.overview()['stale'] is False
    dataset.write_bytes(b'changed cohort')
    assert service.overview()['stale'] is True
    dataset.write_bytes(b'evaluated cohort'); source.write_text('changed code')
    assert service.overview()['stale'] is True

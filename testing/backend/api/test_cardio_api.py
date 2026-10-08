"""
API tests for CardioVision FastAPI endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_health_check_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "CardioVision" in data["service"]


def test_benchmarks_endpoint(client):
    response = client.get("/api/v1/benchmarks")
    assert response.status_code == 200
    data = response.json()
    assert "targets" in data
    assert "CAD" in data["targets"]
    assert "LAD" in data["targets"]
    assert "LCX" in data["targets"]
    assert "RCA" in data["targets"]

    # Check ensemble metrics
    cad_models = data["targets"]["CAD"]
    assert "Ensemble (Soft-Voting)" in cad_models
    assert cad_models["Ensemble (Soft-Voting)"]["roc_auc"] > 0.85


def test_sample_patients_endpoint(client):
    response = client.get("/api/v1/sample-patients")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3
    assert "features" in data[0]
    assert "ground_truth" in data[0]


def test_prediction_endpoint(client):
    sample_payload = {
        "patient_id": "TEST-PT-99",
        "Age": 62,
        "Sex": "Male",
        "Weight": 78,
        "Length": 174,
        "BP": 135,
        "PR": 80,
        "DM": 1,
        "HTN": 1,
        "Typical Chest Pain": 1,
        "St Elevation": 0,
        "St Depression": 1,
        "Tinversion": 1,
        "EF-TTE": 45,
        "Region RWMA": 2
    }
    response = client.post("/api/v1/predict", json=sample_payload)
    assert response.status_code == 200
    body = response.json()

    assert body["patient_id"] == "TEST-PT-99"
    assert "overall_cad" in body
    assert "vessels" in body
    assert "vessel_colors_3d" in body
    assert "shap_explanations" in body
    assert body["vessel_colors_3d"]["lad"].startswith("#")


def test_3d_anatomy_endpoint(client):
    response = client.get("/api/v1/3d-anatomy")
    assert response.status_code == 200
    body = response.json()
    assert "structures" in body
    assert "lad" in body["structures"]
    assert "lcx" in body["structures"]
    assert "rca" in body["structures"]
    assert "myocardium" in body["structures"]
    assert len(body["structures"]["lad"]["positions"]) > 0


def test_sample_round_trips_and_history(client):
    import math
    from backend.cardio.constants import RAW_BINARY_TEXT_FEATURES
    for sample in client.get('/api/v1/sample-patients').json():
        payload = {**sample['features'], 'patient_id': sample['patient_id']}
        numeric = client.post('/api/v1/predict', json=payload)
        assert numeric.status_code == 200
        text = dict(payload)
        for name in RAW_BINARY_TEXT_FEATURES:
            if name in text:
                text[name] = 'Y' if text[name] == 1 else 'N'
        text['Sex'] = 'Male' if text['Sex'] == 1 else 'Female'
        text['BBB'] = ['N', 'LBBB', 'RBBB'][int(text['BBB'])]
        text['VHD'] = ['N', 'mild', 'Moderate', 'Severe'][int(text['VHD'])]
        categorical = client.post('/api/v1/predict', json=text)
        assert categorical.status_code == 200
        a, b = numeric.json(), categorical.json()
        assert a == b
        for risk in [a['overall_cad'], *a['vessels'].values()]:
            assert math.isfinite(risk['probability']) and 0 <= risk['probability'] <= 1
        assert all(a['shap_explanations'][target] for target in ['CAD', 'LAD', 'LCX', 'RCA'])
    history = client.get('/api/v1/history').json()
    assert all(any(record['patient_identifier'] == sample['patient_id'] for record in history)
               for sample in client.get('/api/v1/sample-patients').json())


def test_anatomy_api_matches_static_asset(client):
    import json
    from pathlib import Path
    root = Path(__file__).resolve().parents[3]
    assert client.get('/api/v1/3d-anatomy').json() == json.loads(
        (root / 'frontend/public/heart_model_anatomy.json').read_text())


def test_health_reports_missing_models(client, monkeypatch):
    from backend.cardio.service.prediction_service import prediction_service_instance
    monkeypatch.setattr(prediction_service_instance, 'bundle', None)
    response = client.get('/api/v1/health')
    assert response.status_code == 503
    assert response.json()['status'] == 'unavailable'
    assert response.json()['models_ready'] is False


def test_schema_rejects_invalid_category(client):
    assert client.post('/api/v1/predict', json={'Sex': 'invalid'}).status_code == 422
    assert client.post('/api/v1/predict', json={'DM': 2}).status_code == 422


def test_failed_persistence_rolls_back_without_exposing_inputs(client, caplog):
    from unittest.mock import Mock
    from backend.cardio.dependencies import get_cardio_repository
    repo = Mock()
    repo.create_assessment.side_effect = RuntimeError('private patient values')
    app.dependency_overrides[get_cardio_repository] = lambda: repo
    try:
        with caplog.at_level('ERROR'):
            response = client.post('/api/v1/predict', json={})
        assert response.status_code == 200
        repo.db.rollback.assert_called_once()
        assert 'Assessment persistence failed (RuntimeError)' in caplog.text
        assert 'private patient values' not in caplog.text
    finally:
        app.dependency_overrides.pop(get_cardio_repository)

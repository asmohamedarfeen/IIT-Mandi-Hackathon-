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

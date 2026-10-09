from io import BytesIO

from fastapi.testclient import TestClient
from pypdf import PdfReader

from backend.main import app
from backend.cardio.service.prediction_service import prediction_service_instance


def test_report_download_uses_saved_prediction_without_new_inference_or_history(monkeypatch):
    client = TestClient(app)
    prediction = client.post("/api/v1/predict", json={"patient_id": "REPORT-CASE", "Age": 67, "St Depression": 1}).json()
    assert prediction["evidence"]["report_available"] is True
    assert len(prediction["evidence"]["model_artifact_sha256"]) == 64
    history_count = len(client.get("/api/v1/history?limit=1000").json())
    monkeypatch.setattr(prediction_service_instance, "predict", lambda *_: (_ for _ in ()).throw(AssertionError("report must not rerun inference")))
    response = client.get(f'/api/v1/assessments/{prediction["evidence"]["assessment_id"]}/report')
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment" in response.headers["content-disposition"]
    assert response.headers["cache-control"] == "no-store"
    text = "\n".join(page.extract_text() for page in PdfReader(BytesIO(response.content)).pages)
    assert "REPORT-CASE" in text
    assert prediction["evidence"]["assessment_id"] in text
    assert prediction["evidence"]["model_artifact_sha256"] in text.replace("\n", "")
    assert "ST Depression" in text
    assert "303" in text and "uncalibrated" in text
    for target in ("CAD", "LAD", "LCX", "RCA"):
        risk = prediction["overall_cad"] if target == "CAD" else prediction["vessels"][target]
        assert f'{risk["probability_percent"]:.1f}%' in text
        for factor in prediction["shap_explanations"][target]:
            assert factor["display_name"] in text
            assert f'{factor["contribution"]:+.4f} log-odds' in text
    assert "Patient Age: 67" in text
    assert "ECG ST Depression: Yes (code 1)" in text
    assert "Platelet Count (1000/uL)" in text
    assert "White Blood Cell Count (/uL)" in text
    assert "Erythrocyte Sedimentation Rate (mm/h)" in text
    assert len(client.get("/api/v1/history?limit=1000").json()) == history_count


def test_unknown_report_does_not_fabricate_a_result():
    client = TestClient(app)
    assert client.get("/api/v1/assessments/00000000-0000-0000-0000-000000000000/report").status_code == 404
    assert client.get("/api/v1/assessments/not-a-uuid/report").status_code == 422


def test_report_generation_failure_is_safe_and_retryable(monkeypatch):
    from backend.cardio.service import report_service
    client = TestClient(app)
    prediction = client.post("/api/v1/predict", json={"patient_id": "REPORT-RETRY"}).json()
    def fail(*_):
        raise RuntimeError("private report contents")
    monkeypatch.setattr(report_service, "generate_evidence_report", fail)
    response = client.get(f'/api/v1/assessments/{prediction["evidence"]["assessment_id"]}/report')
    assert response.status_code == 503
    assert "private report contents" not in response.text


def test_legacy_assessment_without_snapshot_has_no_report():
    from types import SimpleNamespace
    from backend.cardio.dependencies import get_cardio_repository
    repository = SimpleNamespace(get_assessment_by_uuid=lambda _: SimpleNamespace(prediction_snapshot=None))
    app.dependency_overrides[get_cardio_repository] = lambda: repository
    try:
        assert TestClient(app).get("/api/v1/assessments/00000000-0000-0000-0000-000000000000/report").status_code == 404
    finally:
        app.dependency_overrides.pop(get_cardio_repository)

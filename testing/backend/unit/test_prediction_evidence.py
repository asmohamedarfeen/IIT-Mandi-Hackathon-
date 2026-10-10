from datetime import datetime
from uuid import UUID

import pytest

from backend.cardio.schemas.patient_schema import PatientInputSchema
from backend.cardio.service.prediction_service import prediction_service_instance


def test_evidence_binds_validated_measurements_to_unique_prediction():
    patient = PatientInputSchema(Age=67, Weight=80, Length=175, **{"EF-TTE": 45})
    first = prediction_service_instance.predict(patient)
    second = prediction_service_instance.predict(patient)
    evidence = first.evidence
    assert UUID(evidence.assessment_id)
    assert evidence.assessment_id != second.evidence.assessment_id
    assert datetime.fromisoformat(evidence.generated_at).utcoffset().total_seconds() == 0
    assert evidence.clinical_inputs["Age"] == 67
    assert evidence.clinical_inputs["EF-TTE"] == 45
    assert evidence.clinical_inputs["BMI"] == pytest.approx(80 / 1.75**2)
    assert "patient_id" not in evidence.clinical_inputs
    patient.Age = 40
    assert evidence.clinical_inputs["Age"] == 67
    assert evidence.confidence_interval is None
    assert evidence.limitations
    for key in ("LAD", "LCX", "RCA"):
        assert first.vessels[key].color_hex == first.vessel_colors_3d[key.lower()]


def test_release_metadata_and_decision_thresholds_follow_loaded_weights():
    from backend.cardio.service.prediction_service import PredictionService
    service = PredictionService()
    service.bundle['decision_thresholds'] = {'CAD': 1.0, 'LAD': 0.0, 'LCX': .5, 'RCA': .5}
    validation = {'record_count': 303, 'method': 'Nested outer-held-out evaluation', 'source': 'release-test'}
    service.bundle['model_release'] = {'run_id': 'release-test', 'validation_summary': validation}
    service.bundle['prediction_model_names'] = {'CAD': 'Calibrated candidate', 'LAD': 'Retained ensemble', 'LCX': 'Retained ensemble', 'RCA': 'Calibrated candidate'}
    result = service.predict(PatientInputSchema())
    assert result.overall_cad.predicted_status == 'Normal'
    assert result.overall_cad.decision_threshold == 1.0
    assert result.vessels['LAD'].predicted_status == 'Stenotic'
    assert result.vessels['LAD'].decision_threshold == 0.0
    assert result.evidence.validation_summary == validation
    assert 'CAD: Calibrated candidate' in result.evidence.prediction_model
    # Changing the classification threshold must not change the probability/color mapping.
    reference = prediction_service_instance.predict(PatientInputSchema())
    assert result.overall_cad.probability == reference.overall_cad.probability
    assert result.vessel_colors_3d == reference.vessel_colors_3d
    from io import BytesIO
    from pypdf import PdfReader
    from backend.cardio.service.report_service import generate_evidence_report
    text = '\n'.join(page.extract_text() for page in PdfReader(BytesIO(generate_evidence_report(result))).pages)
    assert 'Predicted status: Normal' in text
    assert 'Classification threshold: 100.0%' in text

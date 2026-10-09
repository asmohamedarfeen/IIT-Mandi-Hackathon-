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

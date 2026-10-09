"""Generate a synthetic report for PDF layout inspection (no database writes)."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.cardio.schemas.patient_schema import PatientInputSchema
from backend.cardio.service.prediction_service import prediction_service_instance
from backend.cardio.service.report_service import generate_evidence_report


if __name__ == "__main__":
    prediction = prediction_service_instance.predict(
        PatientInputSchema.model_validate({"patient_id": "SYNTHETIC-REPORT-DEMO", "Age": 67, "St Depression": 1})
    )
    destination = Path("output/pdf/cardiovision-evidence-sample.pdf")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(generate_evidence_report(prediction))
    print(destination)

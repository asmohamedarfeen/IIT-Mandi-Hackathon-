"""
Database repository for CardioVision AI assessments and audit logs.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from backend.cardio.models.patient_model import PatientAssessment, InferenceAudit


class CardioRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_assessment(self, data: Dict[str, Any]) -> PatientAssessment:
        record = PatientAssessment(
            patient_identifier=data.get("patient_identifier"),
            cad_probability=data["cad_probability"],
            cad_classification=data["cad_classification"],
            lad_probability=data["lad_probability"],
            lad_classification=data["lad_classification"],
            lcx_probability=data["lcx_probability"],
            lcx_classification=data["lcx_classification"],
            rca_probability=data["rca_probability"],
            rca_classification=data["rca_classification"],
            clinical_inputs=data["clinical_inputs"],
            explanation_summary=data.get("explanation_summary"),
            notes=data.get("notes"),
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def get_assessment(self, assessment_id: int) -> Optional[PatientAssessment]:
        return self.db.query(PatientAssessment).filter(PatientAssessment.id == assessment_id).first()

    def list_assessments(self, limit: int = 50) -> List[PatientAssessment]:
        return (
            self.db.query(PatientAssessment)
            .order_by(PatientAssessment.created_at.desc())
            .limit(limit)
            .all()
        )

    def log_audit(self, endpoint: str, execution_time_ms: float, status_code: int = 200) -> InferenceAudit:
        audit = InferenceAudit(
            endpoint=endpoint,
            execution_time_ms=execution_time_ms,
            status_code=status_code,
        )
        self.db.add(audit)
        self.db.commit()
        return audit

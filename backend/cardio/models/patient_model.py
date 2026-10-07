"""
SQLAlchemy ORM models for clinical patient records and inference audits.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, DateTime, JSON, Text
from backend.core.database import Base


class PatientAssessment(Base):
    """
    Persisted patient clinical assessment and multi-vessel prediction record.
    """
    __tablename__ = "patient_assessments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    patient_identifier = Column(String(64), index=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Core predictions
    cad_probability = Column(Float, nullable=False)
    cad_classification = Column(String(32), nullable=False)

    lad_probability = Column(Float, nullable=False)
    lad_classification = Column(String(32), nullable=False)

    lcx_probability = Column(Float, nullable=False)
    lcx_classification = Column(String(32), nullable=False)

    rca_probability = Column(Float, nullable=False)
    rca_classification = Column(String(32), nullable=False)

    # Input payload and explanation snapshot
    clinical_inputs = Column(JSON, nullable=False)
    explanation_summary = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)


class InferenceAudit(Base):
    """
    Audit log tracking system latency, requests, and pipeline events.
    """
    __tablename__ = "inference_audits"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    endpoint = Column(String(128), nullable=False)
    execution_time_ms = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    status_code = Column(Integer, default=200, nullable=False)

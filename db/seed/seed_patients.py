#!/usr/bin/env python3
"""
Seed script to populate initial patient assessments into the database.
"""

import os
import sys
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from backend.core.database import SessionLocal, Base, engine
from backend.cardio.models.patient_model import PatientAssessment
from backend.cardio.service.prediction_service import prediction_service_instance
from backend.cardio.schemas.patient_schema import PatientInputSchema

def seed_database():
    print("Creating tables if not exists...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    existing_count = db.query(PatientAssessment).count()
    print(f"Existing assessments in database: {existing_count}")

    samples = prediction_service_instance.get_sample_patients()
    for s in samples:
        exists = db.query(PatientAssessment).filter(PatientAssessment.patient_identifier == s["patient_id"]).first()
        if not exists:
            patient_schema = PatientInputSchema(
                patient_id=s["patient_id"],
                **s["features"]
            )
            prediction = prediction_service_instance.predict(patient_schema)
            record = PatientAssessment(
                patient_identifier=s["patient_id"],
                cad_probability=prediction.overall_cad.probability,
                cad_classification=prediction.overall_cad.risk_level,
                lad_probability=prediction.vessels["LAD"].probability,
                lad_classification=prediction.vessels["LAD"].risk_level,
                lcx_probability=prediction.vessels["LCX"].probability,
                lcx_classification=prediction.vessels["LCX"].risk_level,
                rca_probability=prediction.vessels["RCA"].probability,
                rca_classification=prediction.vessels["RCA"].risk_level,
                clinical_inputs=s["features"],
                notes=f"Ground truth Cath: {s['ground_truth'].get('CAD')}, LAD: {s['ground_truth'].get('LAD')}, LCX: {s['ground_truth'].get('LCX')}, RCA: {s['ground_truth'].get('RCA')}",
            )
            db.add(record)
    db.commit()
    print("Database seeding completed.")
    db.close()

if __name__ == "__main__":
    seed_database()

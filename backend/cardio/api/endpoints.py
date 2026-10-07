"""
FastAPI route handlers for CardioVision AI inference, explanations, benchmarks, and 3D anatomy.
Adheres strictly to AGENT.md: All business logic is delegated to service layer.
"""

import time
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.cardio.dependencies import (
    get_prediction_service,
    get_cardio_repository,
)
from backend.cardio.service.prediction_service import PredictionService
from backend.cardio.repository.cardio_repository import CardioRepository
from backend.cardio.schemas.patient_schema import PatientInputSchema, SamplePatientItem
from backend.cardio.schemas.prediction_schema import (
    PredictionResponse,
    ThreeDAnatomyResponse,
)

router = APIRouter(prefix="", tags=["CardioVision Predictions"])


@router.post(
    "/predict",
    response_model=PredictionResponse,
    summary="Predict multi-vessel CAD risk with calibrated probabilities and SHAP explanations",
)
def predict_cardiac_risk(
    patient: PatientInputSchema,
    service: PredictionService = Depends(get_prediction_service),
    repo: CardioRepository = Depends(get_cardio_repository),
) -> PredictionResponse:
    start_time = time.time()
    try:
        response = service.predict(patient)

        # Persist assessment record to database
        try:
            repo.create_assessment({
                "patient_identifier": patient.patient_id,
                "cad_probability": response.overall_cad.probability,
                "cad_classification": response.overall_cad.risk_level,
                "lad_probability": response.vessels["LAD"].probability,
                "lad_classification": response.vessels["LAD"].risk_level,
                "lcx_probability": response.vessels["LCX"].probability,
                "lcx_classification": response.vessels["LCX"].risk_level,
                "rca_probability": response.vessels["RCA"].probability,
                "rca_classification": response.vessels["RCA"].risk_level,
                "clinical_inputs": patient.model_dump(by_alias=True),
                "explanation_summary": {
                    v: [item.model_dump() for item in impacts]
                    for v, impacts in response.shap_explanations.items()
                },
            })
            duration_ms = (time.time() - start_time) * 1000.0
            repo.log_audit("/predict", duration_ms, 200)
        except Exception as db_err:
            # Failure to write to DB should not block clinical inference response
            pass

        return response
    except Exception as exc:
        duration_ms = (time.time() - start_time) * 1000.0
        try:
            repo.log_audit("/predict", duration_ms, 500)
        except Exception:
            pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference error: {str(exc)}",
        )


@router.get(
    "/benchmarks",
    summary="Retrieve 10-fold cross-validation performance metrics across all models",
)
def get_model_benchmarks(
    service: PredictionService = Depends(get_prediction_service),
) -> Dict[str, Any]:
    try:
        return service.get_benchmarks()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Benchmark results unavailable: {str(exc)}",
        )


@router.get(
    "/sample-patients",
    response_model=List[SamplePatientItem],
    summary="Get representative patient profiles (Healthy, LAD Stenosis, Multivessel CAD)",
)
def get_sample_cohort(
    service: PredictionService = Depends(get_prediction_service),
) -> List[SamplePatientItem]:
    patients = service.get_sample_patients()
    return [SamplePatientItem(**p) for p in patients]


@router.get(
    "/3d-anatomy",
    summary="Get normalized 3D heart anatomical structures (LAD, LCX, RCA, Myocardium) for Three.js",
)
def get_heart_anatomy_3d(
    service: PredictionService = Depends(get_prediction_service),
) -> Dict[str, Any]:
    try:
        return service.get_3d_anatomy()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"3D anatomical asset not found: {str(exc)}",
        )


@router.get("/history", summary="Get recent patient assessments from the database")
def get_assessment_history(
    limit: int = 20,
    repo: CardioRepository = Depends(get_cardio_repository),
) -> List[Dict[str, Any]]:
    records = repo.list_assessments(limit=limit)
    return [
        {
            "id": r.id,
            "patient_identifier": r.patient_identifier,
            "created_at": r.created_at.isoformat(),
            "cad_probability": r.cad_probability,
            "cad_classification": r.cad_classification,
            "lad_probability": r.lad_probability,
            "lcx_probability": r.lcx_probability,
            "rca_probability": r.rca_probability,
        }
        for r in records
    ]

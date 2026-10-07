"""
FastAPI dependency injection providers for CardioVision services and repositories.
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.cardio.service.prediction_service import (
    PredictionService,
    prediction_service_instance
)
from backend.cardio.repository.cardio_repository import CardioRepository


def get_prediction_service() -> PredictionService:
    """Dependency provider for singleton prediction service."""
    return prediction_service_instance


def get_cardio_repository(db: Session = Depends(get_db)) -> CardioRepository:
    """Dependency provider for cardio repository with active DB session."""
    return CardioRepository(db)

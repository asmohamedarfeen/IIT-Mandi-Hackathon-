"""
Router registration for the Cardio module.
"""

from fastapi import APIRouter
from backend.cardio.api.endpoints import router as cardio_endpoints

cardio_router = APIRouter()
cardio_router.include_router(cardio_endpoints)

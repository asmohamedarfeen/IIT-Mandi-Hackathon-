"""
Core application settings and environment configuration.
"""

import os
from typing import List
from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "CardioVision AI"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    # Optional coarse deployment guard. This is not user identity or record ACLs.
    API_TOKEN: str = ""
    AUTO_CREATE_TABLES: bool = True  # Docker runs Alembic and disables this fallback.
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        f"sqlite:///{os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'db', 'cardiovision.db'))}"
    )
    
    # Artifact paths
    ARTIFACTS_DIR: str = os.getenv(
        "ARTIFACTS_DIR",
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "artifacts"))
    )
    MODEL_BUNDLE_PATH: str = os.path.join(ARTIFACTS_DIR, "cardiovision_ensemble.joblib")
    ANATOMY_3D_PATH: str = os.path.join(ARTIFACTS_DIR, "heart_model_anatomy.json")
    BENCHMARK_PATH: str = os.path.join(ARTIFACTS_DIR, "benchmark_summary.json")
    MODEL_QUALITY_DIR: str = os.path.join(ARTIFACTS_DIR, "model_quality")

    # CORS settings
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000"
    ]

    @field_validator("ALLOWED_ORIGINS")
    @classmethod
    def explicit_origins(cls, origins):
        if any(origin == "*" for origin in origins):
            raise ValueError("ALLOWED_ORIGINS must list explicit origins; wildcard access is disabled.")
        return origins

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

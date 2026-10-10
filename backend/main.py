"""
CardioVision AI - Main FastAPI Application
Modular architecture following AGENT.md guidelines.
"""

import os
import sys
from pathlib import Path

# Ensure project root is in sys.path so 'backend' is always resolvable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI, Request, Depends, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import secrets

from backend.core.config import settings
from backend.core.logging import setup_logging, logger
from backend.core.database import engine, Base
from backend.cardio.routes import cardio_router
from backend.model_quality.routes import router as model_quality_router
from backend.cardio.constants import CLINICAL_SAFETY_DISCLAIMER
from backend.cardio.dependencies import get_prediction_service

# Initialize logging
setup_logging()

# Ensure database tables exist
if settings.AUTO_CREATE_TABLES:
    Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="CardioVision AI: Multi-task, clinically interpretable machine learning system for CAD and coronary artery stenosis prediction.",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.middleware("http")
async def protect_api(request: Request, call_next):
    # Preflight and readiness carry no records. Never put this token in a web bundle.
    protected = request.url.path.startswith(settings.API_V1_PREFIX + "/")
    public = request.url.path in {"/health", settings.API_V1_PREFIX + "/health"}
    if settings.API_TOKEN and protected and not public and request.method != "OPTIONS":
        supplied = request.headers.get("Authorization", "")
        if not secrets.compare_digest(supplied, "Bearer " + settings.API_TOKEN):
            return JSONResponse(status_code=401, content={"detail": "Authentication required."}, headers={"WWW-Authenticate": "Bearer"})
    return await call_next(request)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception as exc:
        # Starlette's outer error handler re-raises after sending its response,
        # which makes uvicorn log the sensitive traceback. Handle it here first.
        response = await global_exception_handler(request, exc)
    process_time = (time.perf_counter() - start_time) * 1000.0
    response.headers["X-Process-Time-Ms"] = f"{process_time:.2f}"
    if request.url.path.startswith(settings.API_V1_PREFIX + "/"):
        response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Exception strings/tracebacks and URL paths can contain clinical data or IDs.
    logger.error("Unhandled request failure (%s)", type(exc).__name__)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred while processing the clinical request."},
    )


# Mount Cardio feature module routes
app.include_router(cardio_router, prefix=settings.API_V1_PREFIX)
app.include_router(model_quality_router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["Health"])
@app.get(f"{settings.API_V1_PREFIX}/health", tags=["Health"])
def health_check(response: Response, service=Depends(get_prediction_service)):
    ready = service.models_ready
    response.status_code = 200 if ready else 503
    return {
        "status": "healthy" if ready else "unavailable",
        "models_ready": ready,
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "disclaimer": CLINICAL_SAFETY_DISCLAIMER,
    }


# Optional: Mount static frontend when SERVE_FRONTEND is enabled (for single-container cloud hosting)
SERVE_FRONTEND = os.getenv("SERVE_FRONTEND", "false").lower() in {"1", "true", "yes"}
STATIC_DIR = os.getenv("STATIC_DIR", str(PROJECT_ROOT / "frontend" / "dist"))
if SERVE_FRONTEND and os.path.isdir(STATIC_DIR):
    from fastapi.staticfiles import StaticFiles
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True, app_dir=str(PROJECT_ROOT), access_log=False)

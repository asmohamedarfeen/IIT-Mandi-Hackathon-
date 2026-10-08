# IIT-Mandi-Hackathon - CardioVision AI
### 3D Cardiovascular Risk & Coronary Artery Stenosis Visualization

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![React 18](https://img.shields.io/badge/React-18.3-61DAFB.svg)](https://reactjs.org/)
[![Three.js](https://img.shields.io/badge/Three.js-WebGL-black.svg)](https://threejs.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

CardioVision AI is an experimental machine learning and 3D visualization tool. Its supplied models estimate **CAD**, **LAD**, **LCX**, and **RCA** scores from an extended 303-record Z-Alizadeh Sani dataset. The display uses supplied BodyParts3D anatomy, not patient-specific imaging. See [the model and anatomy audit](docs/MODEL_AND_ANATOMY_AUDIT.md) for verified runtime versions, feature compatibility, source provenance and evidence limits.

---

## Key Highlights

- **Leak-Free Multi-Task Prediction:** Strictly excludes catheterization outcome variables (`Cath`, `CAD`, `LAD`, `LCX`, `RCA`) from the predictor space while evaluating four independent targets.
- **Ensemble ML Architecture:** Supplied ten-fold metrics cover six candidates and an uncalibrated voting ensemble. The saved CAD ensemble ROC-AUC is 94.66%; those metrics do not measure the deployed calibrated models.
- **Model Scores:** The saved models apply sigmoid calibration through five-fold cross-validation. Clinical calibration and external validation have not been established.
- **TreeSHAP:** Contributions come from independently fitted XGBoost models. They do not exactly explain the calibrated voting ensembles.
- **Interactive 3D Heart Viewer:** WebGL Three.js canvas dynamically color-codes coronary arteries (**Green <35%**, **Amber 35–65%**, **Red $\ge$ 65%**) with orbit controls, anatomical territory focus, and cardiac pulsation animation.
- **Application Architecture:** Modular FastAPI backend adhering to `AGENT.md`, React 18 + TypeScript + Tailwind CSS frontend, SQLAlchemy persistence, and Docker multi-stage deployments.

---

## Stratified 10-Fold Cross-Validation Performance

The saved benchmark reports ten stratified folds on 303 records. The training source evaluates uncalibrated candidates and voting ensembles; calibrated models are fitted afterward. These supplied metrics were not rerun or independently validated during the redesign.

| Target | Model Candidate | ROC-AUC | F1 Score | Accuracy | Precision | Recall |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **CAD (Cath)** | **Soft-Voting Ensemble** | **94.7%** | **92.5%** | **89.1%** | 91.9% | 93.5% |
| CAD (Cath) | CatBoost | 94.8% | 92.9% | 89.8% | 91.4% | 94.8% |
| CAD (Cath) | Extra Trees | 94.5% | 91.9% | 88.8% | 94.0% | 90.2% |
| **LAD Stenosis** | **Soft-Voting Ensemble** | **87.4%** | **83.8%** | **80.2%** | 80.5% | 87.6% |
| LAD Stenosis | Random Forest | 86.5% | 83.9% | 80.6% | 81.3% | 87.0% |
| LAD Stenosis | CatBoost | 86.6% | 82.7% | 78.9% | 79.5% | 86.4% |
| **LCX Stenosis** | **Soft-Voting Ensemble** | **75.8%** | **60.3%** | **70.7%** | 65.2% | 57.3% |
| LCX Stenosis | CatBoost | 77.0% | 58.2% | 70.0% | 65.9% | 53.0% |
| LCX Stenosis | Random Forest | 76.2% | 62.6% | 71.0% | 63.8% | 62.4% |
| **RCA Stenosis** | **Soft-Voting Ensemble** | **74.3%** | **54.2%** | **68.3%** | 61.8% | 49.8% |
| RCA Stenosis | LightGBM | 74.8% | 56.1% | 70.9% | 68.2% | 49.8% |
| RCA Stenosis | Random Forest | 72.4% | 56.1% | 68.6% | 61.2% | 53.4% |

---

## Project Structure

```
.
├── backend/                  # FastAPI Application (Modular per AGENT.md)
│   ├── cardio/
│   │   ├── api/             # API endpoints (predict, explain, benchmarks, 3d-anatomy)
│   │   ├── service/         # Business logic, feature engineering, TreeSHAP
│   │   ├── repository/      # SQLAlchemy CRUD
│   │   ├── models/          # ORM models (PatientAssessment, InferenceAudit)
│   │   ├── schemas/         # Pydantic input/output schemas
│   │   ├── routes.py        # Route registration
│   │   ├── dependencies.py  # Dependency injection
│   │   └── constants.py     # Medical & visual constants
│   ├── core/                # Config, database, logging
│   └── main.py              # Application entrypoint
├── frontend/                 # React + Vite + TypeScript + Tailwind CSS
│   ├── src/
│   │   ├── components/      # HeartViewer3D, PatientForm, RiskSummaryCards, SHAPChart
│   │   ├── services/        # api.ts
│   │   ├── layouts/         # MainLayout
│   │   ├── pages/           # DashboardPage
│   │   └── utils/           # TypeScript interfaces
│   └── public/              # heart_model_anatomy.json (Three.js asset)
├── db/                       # Database migrations & seeds
│   ├── migrations/          # Alembic migrations
│   └── seed/                # Sample patient cohort seed
├── deploy/                   # Deployment configurations
│   ├── docker/              # Dockerfile.backend, Dockerfile.frontend, docker-compose.yml
│   ├── nginx/               # nginx.conf
│   └── scripts/             # start.sh
├── testing/                  # Pytest automated test suite
│   ├── backend/unit/        # Feature engineering, prediction, SHAP tests
│   └── backend/api/         # API integration tests
├── scripts/                  # Machine learning training & 3D asset scripts
│   ├── train_pipeline.py    # 10-fold CV, model training, Optuna, calibration, SHAP
│   └── process_3d_heart.py  # BodyParts3D OBJ extraction and normalization
└── docs/                     # System architecture & clinical validation documentation
```

---

## Quickstart Guide

### 1. Prerequisites
- Python 3.11+
- Node.js 18+ & npm

### 2. Run Locally

```bash
# Clone the repository
git clone <repo-url>
cd iit-ma

# Start full-stack application (Backend on :8000, Frontend on :5173)
./deploy/scripts/start.sh
```

Or run services individually:

#### Backend:
```bash
# On macOS, XGBoost and LightGBM require OpenMP
brew install libomp

# Create the verified Python runtime and install pinned dependencies
uv venv --python python3.11 .venv
uv pip install --python .venv/bin/python -r backend/requirements.txt

# Run migrations
.venv/bin/alembic upgrade head

# Launch FastAPI server
.venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
Interactive Swagger documentation will be available at: [http://localhost:8000/docs](http://localhost:8000/docs)

#### Frontend:
```bash
cd frontend
npm install
npm run dev
```
Dashboard will be available at: [http://localhost:5173](http://localhost:5173)

---

### 3. Run with Docker Compose

```bash
cd deploy/docker
docker-compose up --build
```
- Web Application: [http://localhost](http://localhost)
- Backend API: [http://localhost:8000](http://localhost:8000)

---

## Running the Automated Test Suite

```bash
# Run all backend unit and API integration tests
.venv/bin/python -m pytest testing/backend -q
```

Tests create a temporary isolated SQLite database before importing the application.
The suite verifies input encoding, omitted BMI, saved feature definitions, all three
example round trips, readiness, persistence rollback and deterministic geometry.

---

## Retraining the Model Pipeline

Retraining replaces the supplied weights. The current engineer emits 86 columns, while the preserved bundle binds to 84; retraining is a separate validation task. To run the training script deliberately:

```bash
python3 scripts/train_pipeline.py
```

To regenerate the 3D heart anatomical meshes from the raw BodyParts3D archive:

```bash
.venv/bin/python scripts/process_3d_heart.py
```

---

## Clinical Safety Disclaimer

CardioVision AI is an experimental decision-support and 3D visualization research tool. Model predictions and 3D perfusion maps do not constitute diagnostic medical advice or replace formal coronary catheterization.

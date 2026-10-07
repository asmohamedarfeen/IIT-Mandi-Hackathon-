# CardioVision AI - 3D Cardiovascular Risk & Stenosis Visualization

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![React 18](https://img.shields.io/badge/React-18.3-61DAFB.svg)](https://reactjs.org/)
[![Three.js](https://img.shields.io/badge/Three.js-WebGL-black.svg)](https://threejs.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

CardioVision AI is a production-grade, clinically interpretable multi-task machine learning and 3D visualization platform for cardiovascular risk assessment. Using an extended cohort of the Z-Alizadeh Sani clinical dataset (303 patients), the system predicts overall **Coronary Artery Disease (CAD)** and vessel-specific stenosis in the three major epicardial arteries (**LAD**, **LCX**, and **RCA**) without target leakage, mapping calibrated probability estimates onto an interactive, anatomically registered 3D heart model.

---

## Key Highlights

- **Leak-Free Multi-Task Prediction:** Strictly excludes catheterization outcome variables (`Cath`, `CAD`, `LAD`, `LCX`, `RCA`) from the predictor space while evaluating four independent targets.
- **Ensemble ML Architecture:** Benchmarked CatBoost, XGBoost, LightGBM, Random Forest, Extra Trees, and Logistic Regression with Stratified 10-Fold Cross-Validation, deployed as a calibrated soft-voting ensemble achieving **>93% ROC-AUC** for CAD.
- **Calibrated Probabilities:** Platt/Sigmoid calibration yields true risk percentages (0–100%) rather than uncalibrated classification scores.
- **Explainable AI (TreeSHAP):** Patient-specific marginal feature contributions explain why an individual patient is predicted to have stenosis in each arterial territory.
- **Interactive 3D Heart Viewer:** WebGL Three.js canvas dynamically color-codes coronary arteries (**Green <35%**, **Amber 35–65%**, **Red $\ge$ 65%**) with orbit controls, anatomical territory focus, and cardiac pulsation animation.
- **Production Architecture:** Modular FastAPI backend adhering to `AGENT.md`, React 18 + TypeScript + Tailwind CSS frontend, SQLAlchemy persistence, and Docker multi-stage deployments.

---

## Stratified 10-Fold Cross-Validation Performance

All models were evaluated across 10 stratified folds on the full 303-patient dataset:

| Target | Model Candidate | ROC-AUC | F1 Score | Accuracy | Precision | Recall |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **CAD (Cath)** | **Soft-Voting Ensemble** | **93.2%** | **91.1%** | **87.1%** | 89.4% | 93.1% |
| CAD (Cath) | Extra Trees | 93.5% | 91.2% | 87.8% | 90.1% | 92.6% |
| CAD (Cath) | CatBoost | 93.0% | 91.3% | 87.4% | 89.2% | 93.5% |
| **LAD Stenosis** | **Extra Trees** | **85.3%** | **84.6%** | **81.2%** | 81.3% | 88.7% |
| LAD Stenosis | **Soft-Voting Ensemble** | **84.8%** | **81.9%** | **77.9%** | 79.4% | 85.3% |
| LAD Stenosis | CatBoost | 85.1% | 81.6% | 77.3% | 78.8% | 85.3% |
| **LCX Stenosis** | **Soft-Voting Ensemble** | **74.2%** | **59.0%** | **70.3%** | 64.9% | 55.4% |
| LCX Stenosis | XGBoost | 73.2% | 55.6% | 68.7% | 63.8% | 51.1% |
| **RCA Stenosis** | **Extra Trees** | **71.7%** | **53.4%** | **63.0%** | 51.1% | 57.0% |
| RCA Stenosis | **Soft-Voting Ensemble** | **71.3%** | **49.9%** | **66.3%** | 57.0% | 45.4% |

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
# Install backend dependencies
pip install -r backend/requirements.txt

# Run migrations
alembic upgrade head

# Launch FastAPI server
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
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
python3 -m pytest testing/
```

Output:
```
testing/backend/api/test_cardio_api.py::test_health_check_endpoint PASSED
testing/backend/api/test_cardio_api.py::test_benchmarks_endpoint PASSED
testing/backend/api/test_cardio_api.py::test_sample_patients_endpoint PASSED
testing/backend/api/test_cardio_api.py::test_prediction_endpoint PASSED
testing/backend/api/test_cardio_api.py::test_3d_anatomy_endpoint PASSED
testing/backend/unit/test_feature_engineering.py::test_leakage_columns_definition PASSED
testing/backend/unit/test_feature_engineering.py::test_clinical_feature_engineer_calculations PASSED
testing/backend/unit/test_feature_engineering.py::test_prepare_training_data_leakage_exclusion PASSED
testing/backend/unit/test_prediction_service.py::test_prediction_service_initialization PASSED
testing/backend/unit/test_prediction_service.py::test_prediction_output_structure_and_calibration PASSED

======================== 10 passed in 5.30s ========================
```

---

## Retraining the Model Pipeline

To execute the complete 10-fold Stratified Cross-Validation benchmark, calibrate probability estimators, compute TreeSHAP summaries, and serialize artifacts:

```bash
python3 scripts/train_pipeline.py
```

To regenerate the 3D heart anatomical meshes from the raw BodyParts3D archive:

```bash
python3 scripts/process_3d_heart.py
```

---

## Clinical Safety Disclaimer

CardioVision AI is an experimental decision-support and 3D visualization research tool. Model predictions and 3D perfusion maps do not constitute diagnostic medical advice or replace formal coronary catheterization.

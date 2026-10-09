# IIT-Mandi-Hackathon - CardioVision AI
### 3D Cardiovascular Risk & Coronary Artery Stenosis Visualization

[![Python 3.11](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![React 18](https://img.shields.io/badge/React-18.3-61DAFB.svg)](https://reactjs.org/)
[![Three.js](https://img.shields.io/badge/Three.js-WebGL-black.svg)](https://threejs.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

CardioVision AI is an experimental machine learning and 3D visualization tool. Its supplied models estimate **CAD**, **LAD**, **LCX**, and **RCA** scores from an extended 303-record Z-Alizadeh Sani dataset. The display uses supplied BodyParts3D anatomy, not patient-specific imaging. See [the model and anatomy audit](docs/MODEL_AND_ANATOMY_AUDIT.md) for verified runtime versions, feature compatibility, source provenance and evidence limits.

---

## Key Highlights

- **What Drives This Prediction?:** Expand a ranked patient-specific factor to inspect its signed XGBoost SHAP contribution, assessed value and model encoding. Calculated factors explain their derivation and list their original measurements. Source links open and focus the matching patient input without editing it; changing an input hides stale details until reassessment completes.
- **Coronary Evidence-to-Anatomy:** Select LAD, LCX or RCA using the 3D surface, vessel controls, result cards or evidence tabs. The linked evidence panel shows its probability, assessed clinical inputs, signed SHAP factors, model limitations and exact mesh color source. Each inference includes a unique assessment ID and UTC timestamp. Confidence intervals are unavailable in the supplied bundle.
- **Automatic Reassessment:** After the first assessment, valid input edits rerun inference after a 700 ms pause. Superseded requests are cancelled, late responses ignored, and stale evidence hidden until all views can update together. Assessment inputs and outputs continue to be saved by the existing prediction endpoint.
- **Leak-Free Multi-Task Prediction:** Strictly excludes catheterization outcome variables (`Cath`, `CAD`, `LAD`, `LCX`, `RCA`) from the predictor space while evaluating four independent targets.
- **Ensemble ML Architecture:** Supplied ten-fold metrics cover six candidates and an uncalibrated voting ensemble. The saved CAD ensemble ROC-AUC is 94.66%; those metrics do not measure the deployed calibrated models.
- **Model Scores:** The saved models apply sigmoid calibration through five-fold cross-validation. Clinical calibration and external validation have not been established.
- **TreeSHAP:** Contributions come from independently fitted XGBoost models. They do not exactly explain the calibrated voting ensembles.
- **Interactive 3D Heart Viewer:** WebGL Three.js canvas dynamically color-codes coronary arteries (**Green <35%**, **Amber 35–<65%**, **Red $\ge$ 65%**) with orbit controls, anatomical territory focus, and illustrative uniform pulse animation.
- **Application Architecture:** Modular FastAPI backend, React 18 + TypeScript + Tailwind CSS frontend, SQLAlchemy persistence, and Docker multi-stage deployments.

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
- Python 3.11
- Node.js 24+ & npm (native TypeScript test support; verified on 24.7.0)
- [uv](https://docs.astral.sh/uv/) for the project `.venv`
- On macOS: `brew install libomp` for XGBoost/LightGBM

### 2. Run Locally

```bash
# From this repository root; defaults to backend :8000 and frontend :5173
./deploy/scripts/start.sh

# Choose free ports and an isolated database when another checkout is running
DATABASE_URL=sqlite:////tmp/cardiovision-preview.db \
  BACKEND_PORT=8001 FRONTEND_PORT=5174 ./deploy/scripts/start.sh
```

The script creates or checks a Python 3.11 `.venv`, installs exact backend versions
with transitive constraints and frontend dependencies with `npm ci`, then migrates
the selected database. It binds both services to `127.0.0.1`, sets the matching
`VITE_API_BASE_URL`, rejects occupied ports without stopping existing servers, and
stops both owned processes on Ctrl+C/termination or if either service exits.
Models take several seconds to load; use **Recheck model service**, **Retry cases**,
or **Retry evidence** if you open the app during backend startup. The default DB is
`db/cardiovision.db`; use `DATABASE_URL` above for disposable verification data.

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
npm ci
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1 npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
```
Dashboard will be available at: [http://localhost:5173](http://localhost:5173)

---

### 3. Run with Docker Compose

```bash
cd deploy/docker
docker compose up --build
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

```bash
# Node.js 24+; patient normalization, fullscreen recovery, and real mesh lifecycle
npm --prefix frontend test
npm --prefix frontend run build

# Live API smoke; explicitly writes six assessments from supplied examples
# Run against an isolated database, using the API URL from your local startup
.venv/bin/python scripts/verify_api.py --base-url http://127.0.0.1:8001/api/v1
```

See [verification evidence and screenshots](docs/verification.md) for the checked
API scores, desktop/mobile interactions, recovery paths, and runtime limitations.
The production Three.js/GSAP chunk remains around 785 kB minified (225 kB gzip);
lazy loading remains a future performance improvement. Docker build/runtime was
not verified in this environment because its daemon was unavailable.

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

CardioVision AI is an experimental decision-support and 3D visualization research tool. Model predictions and whole-vessel risk colors do not constitute diagnostic medical advice or replace formal coronary catheterization.

## Model Quality Lab

Select **Model Quality Lab** in the application header. The assessment workspace stays
mounted so switching back preserves patient inputs and the heart view. The Lab reads
saved evaluation artifacts only; neither opening it nor downloading reports trains models.

Generate real evidence offline:

```bash
.venv/bin/python scripts/evaluate_model_quality.py
.venv/bin/python scripts/evaluate_model_quality.py --verify
```

The evaluator uses the supplied workbook, the deployed bundle's exact 84-feature
contract, ten stratified outer folds and five inner calibration folds. All learned
preprocessing stays inside each fit. It compares eight fixed individual classifiers,
voting and sigmoid-calibrated voting across CAD, LAD, LCX and RCA. Stacking is not
implemented and is not shown as an evaluated model. Temporary fitted clones are
fingerprinted and discarded; deployed weights and historical benchmarks are protected.

Runs are immutable directories under `artifacts/model_quality/runs/`; publication
atomically updates `current.json`. Public summaries contain aggregate evidence. Private
`oof.json` files contain row-level labels/probabilities and held-out explanation audit
data; do not publish the artifact directory as static assets. The API checks fingerprints,
recomputes evidence against OOF records on cache fill, and caches validated snapshots.
Downloads bind to the visible run and reject a changed run with HTTP 409.

APIs live under `/api/v1/model-quality`: overview, models, cad/lad/lcx/rca,
confusion-matrix, calibration, roc, pr, shap, feature-stability, class-distribution,
reproducibility and report. The download center exports PDF, aggregate JSON and CSV
evidence. Arbitrary threshold confusion counts are computed from stored OOF probabilities,
not interpolated. Undefined metrics and empty calibration bins remain explicitly unavailable.

Provenance records dataset/model/source hashes, archived source, git state, dependency
versions, parameters, seeds and fold partitions. Historical training timestamps were not
supplied and are not invented. SHAP and permutation stability explain an independent
held-out XGBoost classifier, **not the voting ensemble**. Cross-validation is internal
cohort evidence with historical model-selection bias, not external clinical validation.
The retained legacy production-training script still needs a separate validation review
before retraining; the Lab does not reuse its pre-CV imputation behavior.

See [architecture audit](docs/model-quality-architecture-audit.md) and
[implementation plan](docs/superpowers/plans/2026-10-09-model-quality-lab.md).

## One-click evidence reports

After a saved assessment completes, choose **Download evidence report** on the dashboard.
The PDF includes assessed measurements, all four predictions, vessel territory/color
sources, ranked signed factors with their original measurements, application version,
model artifact SHA-256, supplied validation metrics and limitations. It uses the stored
assessment snapshot: downloading does not rerun inference or use later form edits.
Stale, pending or unsaved assessments cannot be downloaded. Older history entries
without snapshots require a new assessment; reports are not retroactively fabricated.

For an existing installation, install backend requirements and run
`.venv/bin/alembic upgrade head` before restarting the backend. The migration adds
nullable snapshot columns and preserves existing records.

The download endpoint is `GET /api/v1/assessments/{assessment_id}/report`.
Reports contain confidential inputs. The current prototype has no authentication;
do not expose it publicly with real patient data. The supplied cross-validation
benchmarks concern uncalibrated models and are explicitly not validation of the
deployed calibrated ensemble.

To generate a synthetic PDF for layout checks without database writes:

```bash
.venv/bin/python scripts/verify_evidence_report.py
```

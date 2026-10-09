# Coronary Evidence-to-Anatomy Implementation Plan

**Goal:** Clicking LAD, LCX or RCA reveals its prediction, assessed measurements, contributing factors, confidence limitations and exact 3D color source. Editing valid inputs after an assessment reruns inference and updates all views together.

**Architecture:** Extend the existing FastAPI prediction response with evidence provenance. Dashboard owns the selected artery; the Three.js viewer, evidence panel and contributor chart share it. A debounced assessment runner cancels superseded requests and rejects late responses.

**Tech stack:** Existing FastAPI/Pydantic, React/TypeScript, Three.js and Node/Pytest tests; no new production dependencies.

## Constraints and design

- Preserve existing uncommitted component changes and work on the current `v1` branch.
- Use the existing calibrated models and color map without retraining or changing thresholds.
- Show confidence intervals as unavailable; never infer confidence from probability or historic ROC-AUC.
- Explain that SHAP values describe independent XGBoost log-odds, not exact ensemble probability contributions.
- Measurements come from the server's validated input snapshot, never a subsequently edited form.
- Use accessible vessel buttons as well as mesh picking. Orbit drags must not select an artery.
- Hide current evidence and risk colors immediately on edits; preserve selection through reassessment.
- First assessment is explicit. Later edits debounce for 700 ms; invalid forms wait for correction, errors permit manual retry, automatic updates do not scroll.

## Tasks

### 1. Prediction provenance

- [x] Add a failing backend test for unique assessment IDs, UTC timestamps, validated raw inputs including derived BMI, unavailable confidence intervals and color equality.
- [x] Extend `backend/cardio/schemas/prediction_schema.py` with `PredictionEvidence`; populate `evidence` in `prediction_service.py`.
- [x] Run backend tests; expected all pass.

### 2. Linked artery evidence

- [x] Add failing frontend tests for vessel-specific score/color/factors, absolute contribution ranking, stale suppression and patient measurements.
- [x] Add `utils/evidence.ts`, response types and `CoronaryEvidencePanel.tsx`.
- [x] Lift selection into `DashboardPage.tsx`; share it with `HeartViewer3D`, risk-card buttons and the controlled SHAP chart.
- [x] Add pointer raycasting with drag threshold, selecting visible coronary meshes only.
- [x] Style responsive evidence content using the existing visual system.

### 3. Automatic reassessment and verification

- [x] Add failing async tests for debounce, invalid input gating, superseded responses, cancellation, errors and manual retry.
- [x] Implement `utils/assessment.ts`; integrate with dashboard and optional API AbortSignal.
- [x] Run `npm --prefix frontend test`, `npm --prefix frontend run build`, and `.venv/bin/python -m pytest testing/backend -q`.
- [ ] Inspect desktop/mobile UI and selection/reassessment interactions in a local preview with an isolated database.
- [x] Review the final diff and record results below.

## Review focus

Rapid edits; invalid or empty numeric inputs; old responses arriving last; selection while inference runs; WebGL failure; reset and anatomy mode; absent evidence from an older backend; low scores with negative contributors; narrow mobile layouts.

## Execution record

User explicitly requested planning and execution in this turn. Implement inline, preserve user work, and leave changes uncommitted for review.

- Backend: 35 tests passed. Existing dependency deprecation and LightGBM feature-name warnings remain.
- Frontend: 29 tests passed, including real TSX component rendering, visible artery picking, per-vessel selection, stale hiding, provenance, debounce, abort, late responses and failure/retry.
- Production build passed. Vite reports the existing large-bundle warning (about 680 kB minified).
- Diff whitespace check passed. Review preserved the overall CAD explanation and fixed duplicate chart heading IDs and repeated reset behavior.
- Preview services started at `http://127.0.0.1:5175` and backend port 8002 with `/tmp/cardiovision-evidence-preview-20261009.db`.
- Browser inspection was blocked: Chrome security policy reported that the user declined access to the preview URL. No alternate browser access was attempted. Desktop/mobile visual and real browser interaction QA remain unverified; component rendering, Three.js raycasting and request lifecycle tests passed.

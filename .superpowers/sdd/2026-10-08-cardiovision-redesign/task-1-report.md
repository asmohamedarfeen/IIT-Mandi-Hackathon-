# Task 1 report — completed

Worktree: `/Users/asmohamedarfeen/.codex/worktrees/cardiovision-redesign/iit-ma`
Branch: `codex/cardiovision-redesign`. Base: `f54bbc362913ef0ca36c15d0effe01d014d67c21`.

## Changes

- Centralized category label/numeric decoding for dataset cleaning and API validation. Unknown, fractional/out-of-range categories and non-finite numeric values are rejected. Sex 0/1, binary Y/N or 0/1, BBB 0–2, VHD 0–3 and Function Class/RWMA 0–4 are consistent.
- Omitted/null BMI is derived per record and kept as a raw model feature. Explicit BMI remains unchanged. Frontend must omit/recompute BMI after editing weight/height.
- Preserved exact 84-feature bundle order, removed silent missing-column substitution and rejected non-finite model input.
- Preserved deployed ECG composite semantics as required by the amended brief. LVH and Poor R Progression stay raw predictors but are not newly added to the trained composite. The change would otherwise affect 29/303 dataset records.
- Found and corrected a second compatibility bug: newer source added HDL to Metabolic_Risk_Score, contradicting 35/50 saved reference vectors and 2/3 bundled samples. Restored the trained definition without HDL. All 50×84 saved background values now match, alongside all sample vectors.
- Model initialization now executes all four calibrated predictors and independent XGBoost explanations. Missing/invalid bundles leave the API running with truthful unavailable health. Health returns 200/healthy/models_ready:true only after successful initialization; failure returns 503/unavailable/models_ready:false.
- Persistence errors rollback and log safe exception types instead of swallowing failures or logging patient SQL parameters. Valid inference responses can survive persistence failure. Assessment/audit commits remain independent, as before.
- Rebuilt deterministic anatomy from every relevant supplied external-heart OBJ piece. Added the supplied left coronary stem as neutral `left_main`, retained all 38 myocardial wall/auricle/septum pieces, and documented all omitted names. Both artifact/static copies are byte-identical.
- Pinned verified dependencies and their full installed constraints. Added temporary isolated database setup to the backend suite. Corrected README/API descriptions and documented evidence/provenance in `docs/MODEL_AND_ANATOMY_AUDIT.md`.

## Runtime, bundle and dataset evidence

Created project `.venv` using `uv venv --python python3.11 .venv`, running CPython **3.11.14** on macOS arm64. Embedded bundle metadata identifies scikit-learn **1.7.1**, XGBoost **3.2.0**, CatBoost **1.2.10** and LightGBM format v4. Installed these exact first three versions plus LightGBM **4.6.0**. Verified NumPy **2.4.6**, pandas **3.0.6**, SHAP **0.51.0**, joblib **1.6.0**, SciPy **1.17.1**, FastAPI **0.142.4**, Pydantic **2.13.5**, SQLAlchemy **2.1.4**, pytest **9.1.1** and uvicorn **0.54.0**. Every installed package is recorded in `backend/requirements.lock.txt` and constrained from `backend/requirements.txt`.

The first import failed because macOS OpenMP was missing. `HOMEBREW_NO_AUTO_UPDATE=1 brew install libomp` installed **23.1.1** successfully. An attempted broad `DYLD_LIBRARY_PATH=/opt/anaconda3/lib` conflicted with NumPy's Accelerate symbols; it is not used. The normal `.venv/bin/python` works without environment/library-path overrides after libomp installation.

Preserved bundle SHA-256: `ee7b9d32a9b45b2b291c81ea93244a8188fa24ad77913732bc916b737f929e16`, 38,577,362 bytes. No training or bundle overwrite occurred.

Models: four `CalibratedClassifierCV` instances, sigmoid calibration, five calibrated soft-voting ensembles per target, each using CatBoost/XGBoost/LightGBM/Random Forest/Extra Trees. Four independent XGBClassifier models provide explanations. Saved feature count is **84**, while current engineering source emits **86** because two extra ratio aliases duplicate existing Castelli features. Inference uses the bundle's binding order.

Workbook: 303×59, zero missing cells. Engineered source: 303×86, zero NaNs. Positives/negatives: CAD 216/87, LAD 177/126, LCX 119/184, RCA 114/189. Saved benchmark metrics equal the bundle's metrics. Saved uncalibrated voting ROC-AUC: CAD 0.9466, LAD 0.8739, LCX 0.7583, RCA 0.7431. Calibration is applied after benchmarking; clinical calibrated-model performance is not established. Explanations are independent XGBoost log-odds contributions, not exact calibrated-ensemble attribution.

Synthetic baseline with schema defaults and explicit BMI 25 had CAD/LAD/LCX/RCA probabilities **0.0626/0.0845/0.1322/0.1258** before and after the fixes. No patient rows were logged during investigation. Regression mismatch summaries were used to inspect compatibility.

## UI/API handoff

Use this exact runtime path:

`/Users/asmohamedarfeen/.codex/worktrees/cardiovision-redesign/iit-ma/.venv/bin/python`

From the worktree root, start an isolated preview backend:

```sh
DATABASE_URL=sqlite:////tmp/cardiovision-redesign-preview.db .venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8001
```

Existing user servers on 8000/5173 were not stopped. This task did not leave any new lasting server running. UI preview should use its own free port and route to 8001.

Healthy response from `/api/v1/health` (HTTP 200):

```json
{
  "status": "healthy",
  "models_ready": true,
  "service": "CardioVision AI",
  "version": "1.0.0",
  "disclaimer": "CardioVision AI is an experimental decision-support and visualization research tool. Predictions and 3D maps do not constitute diagnostic medical advice or replace formal coronary angiography."
}
```

Unavailable health uses HTTP 503, `status: "unavailable"`, `models_ready: false`, with the same remaining fields. The UI must handle the unsuccessful HTTP status and show recovery/unknown readiness. Prediction/sample response keys remain unchanged. Schema-normalized persistence now records computed BMI and numeric categories.

**Sample-label warning:** all three supplied examples are CAD/multivessel cases. Their labels, in supplied order, are LAD+LCX+RCA; LAD+RCA; LAD+LCX. There is no healthy or isolated LAD example. Render labels from the actual `ground_truth` object. They are examples from the training data, not validation evidence.

Anatomy response continues `{metadata, structures}` and flat `positions`, `indices`, `vertex_count`, `face_count`. Contract:

| Key | Files | Vertices | Triangles | UI meaning |
|---|---:|---:|---:|---|
| lad |9|7,914|13,574|LAD trunk and supplied branches; prediction color|
| lcx |4|10,140|19,160|LCX and left marginal; prediction color|
| rca |10|8,215|13,764|RCA and right marginal; prediction color|
| myocardium |38|68,724|124,188|All supplied chamber/auricle walls and septa; tissue color|
| left_main |1|370|500|Left coronary stem; neutral color, no target score|

Total: **62 included pieces / 95,363 vertices / 171,186 triangles** from a 123-file ZIP. Metadata records 61 omitted names, per-key source filenames, ZIP provenance/hash, selection rules and one shared transformation. Omitted internal valves, papillary/trabecular/pectinate structures, conduction tissue, fibrous supports and veins are unnecessary for this external-surface view. Distinct pieces sharing FMA labels are all retained; none is skipped by index or mesh size.

Coordinates are uniformly centered/scaled from global source bounds and rotated `[x,z,-y]`. Longest extent is 3.5; no per-group normalization. Positions round to six decimal places. Output size **5,573,082 bytes**, SHA-256 `59139a900e2a13164ee4b0d38ed0391385899363693f64abb15d93570a8cc456`. ZIP SHA-256 `4b9707e49a4c2948abb8e0d9b3411a3fa16e09a3f40ff0f9e7faf1afa799e3d5`.

The old supplied asset already used identical coronary counts and placed its actual right marginal filename in RCA. New explicit naming precedence removes ambiguous generic marginal categorization. Myocardium grows **74,162→124,188 triangles**, plus the left-main piece. API JSON and static JSON are exactly equal; artifact/static files are byte-identical.

## Actual verification commands and results

1. Initial focused regression before feature/schema fixes:
   `DATABASE_URL=sqlite:////tmp/cardiovision-task1-baseline.db .venv/bin/python -m pytest testing/backend/unit/test_input_contract.py -q --tb=line`
   → **11 failed, 1 passed, 5 warnings in 6.03s** after runtime repair. Failures showed 22/84 category mismatches, missing BMI NaN, 7/84 sample-vector mismatches, and invalid category/BMI acceptance. Preserved ECG composite regression passed.
2. First fixed full suite:
   `DATABASE_URL=sqlite:////tmp/cardiovision-task1-fixed.db .venv/bin/python -m pytest testing/backend -q --tb=short`
   → **24 passed, 1 failed in 7.68s**. The remaining failure exposed the saved metabolic-score mismatch; not papered over in the test.
3. After restoring metabolic parity and adding API/readiness/persistence isolation checks:
   `.venv/bin/python -m pytest testing/backend -q --tb=short`
   → **34 passed, 205 warnings in 6.09s**.
4. Final suite after shared-transform, malformed-bundle guard and documentation changes:
   `.venv/bin/python -m pytest testing/backend -q --tb=short`
   → **34 passed, 205 warnings in 6.58s**. The suite's conftest creates a temporary SQLite DB before importing the app, regardless of ambient DB settings. Covers all sample API predictions and numeric/text equality, history, finite scores, nonempty explanations, healthy/unavailable health, load failure, safe rollback, background parity, BMI and deterministic full-source geometry/API/static equality.
5. `.venv/bin/python scripts/process_3d_heart.py`
   → successful deterministic generation, LAD 9 / LCX 4 / RCA 10 / myocardium 38 / left_main 1 files with the counts above. The asset regression regenerates independently in a temporary directory and checks exact bytes, finite coordinates, triangle ranges, group transforms and no myocardial subsampling.
6. `uv pip check --python .venv/bin/python`
   → **Checked 62 packages; all installed packages are compatible**.
   `uv pip install --python .venv/bin/python -r backend/requirements.txt`
   → **Audited 20 direct packages**, no changes required; relative constraints resolved successfully.

Warnings are non-blocking: LightGBM fitted-feature-name metadata warnings when using the binding numeric matrix, plus Starlette/SHAP/Pydantic settings deprecations. No scikit-learn serialization-version mismatch warning occurs. No external performance/calibration evaluation, browser visual QA or frontend build belongs to this task.

## Remaining concerns

- Current training source has 86 columns; preserve 84-feature saved weights unless explicitly retraining and reevaluating. ECG composite omissions remain intentionally compatible; source/evidence limitations are documented.
- Clinical calibration, generalization and exact ensemble explanations are unverified. Source geometry licensing has not been independently verified; no new claim was invented.
- Complete anatomy needs subsequent browser/performance evaluation; the viewer must support neutral `left_main` and avoid invented motion/patient-specific claims.
- A persistence failure is logged/rolled back but does not add a new response field because prediction response compatibility is preserved. Separate assessment/audit transactions can leave an assessment without an audit after an audit-write failure.
- Runtime was verified on macOS arm64 only. Native OpenMP is required on macOS; pinned wheel availability on other architectures was not tested.

## Review fix round 1 — Docker constraints layout

Reviewer identified that Docker copied only requirements.txt into `/app` before pip installation, leaving its sibling constraints file unavailable. Fixed the single COPY instruction to `COPY backend/requirements.txt backend/requirements.lock.txt /app/`. Both files are now present before the existing RUN installation step. No runtime/model/geometry behavior changed.

Verification:

- `docker version` → client 28.4.0 / darwin arm64 available, exit 1: cannot connect to Docker daemon at the user's desktop-linux socket. An actual Docker image build was not run; the daemon was not started or altered.
- `.venv/bin/python` static-layout check → asserted the two-file COPY precedes pip installation, copied both files into a temporary `app` directory and resolved the literal `-c requirements.lock.txt` sibling from that directory. Output: **PASS: both requirement files copied to /app before pip install; sibling constraints resolve**.
- Within that temporary container-style layout: `uv pip install --dry-run --python /Users/asmohamedarfeen/.codex/worktrees/cardiovision-redesign/iit-ma/.venv/bin/python -r requirements.txt` → **Audited 20 packages; would make no changes**. This verifies requirements/constraints path resolution and the installed local dependency set; it does not verify Linux wheels or the full container build.
- `uv pip check --python .venv/bin/python` → **Checked 62 packages; all installed packages are compatible**.
- `git diff --check` → passed.

The existing **205 warnings** remain recorded above. They were not broadly suppressed or expanded into unrelated dependency/model changes. Full container-build verification remains unavailable until a Docker daemon is running.

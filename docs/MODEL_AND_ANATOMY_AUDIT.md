# Model and anatomy audit

Verified locally on 2026-10-08 using the supplied files. No training, medical literature research or external validation was performed.

## Preserved model and inference contract

`artifacts/cardiovision_ensemble.joblib` is unchanged (38,577,362 bytes; SHA-256 `ee7b9d32a9b45b2b291c81ea93244a8188fa24ad77913732bc916b737f929e16`). It contains four `CalibratedClassifierCV` models, one each for CAD/LAD/LCX/RCA, with sigmoid calibration and five calibrated classifiers each. Each classifier wraps a soft-voting ensemble of CatBoost, XGBoost, LightGBM, Random Forest and Extra Trees. All bind to **84 features** in the bundle's `feature_names` order. Four separate `XGBClassifier` models supply TreeSHAP explanations.

The workbook contains 303 records and 59 columns, with no missing cells. Target positives/negatives are CAD 216/87, LAD 177/126, LCX 119/184 and RCA 114/189. Target columns Cath/CAD/LAD/LCX/RCA and constant Exertional CP are excluded from model inputs. The current feature-engineering source emits **86 columns**: LDL_HDL_Ratio and Total_Cholesterol_Ratio duplicate existing Castelli ratios and are absent from the saved bundle. Inference selects exactly the saved 84 columns and rejects missing/non-finite features; no zero-valued substitute columns are created.

The saved 50×84 reference background provides a compatibility check, not a validation cohort. Before correction, the current source's HDL addition changed Metabolic_Risk_Score in 35/50 reference records and 2/3 supplied samples. The fitted definition is `DM + HTN + (TG > 150) + (FBS > 100)`; that definition has been restored. After correction, all 50 background vectors and all three sample vectors match saved values within float32 tolerance. No trained parameters were changed.

The trained ECG_Abnormality_Score includes ST Elevation, ST Depression, Tinversion and Q Wave, while its encoded LVH/Poor R Progression values were omitted by the original text comparisons. Their raw binary features still enter the model. Broadening the composite would affect 29/303 workbook records (20 LVH, 9 Poor R Progression); it is deliberately deferred until retraining and evaluation. Numeric and textual inputs now follow the same cleaning path, preserving this fitted composite definition.

Binary categories accept integer-valued 0/1; the text-coded fields also accept Y/N. Sex accepts Male/Female/Fmale or 1/0; BBB accepts N/LBBB/RBBB or 0/1/2; VHD accepts N/mild/Moderate/Severe or 0/1/2/3. Matching is case-insensitive and trims surrounding whitespace. Function Class and Region RWMA accept integer categories 0–4. Unknown labels, fractional/out-of-range categories and non-finite numeric values are rejected at the API boundary. Omitted/null BMI derives from `Weight / (Length/100)^2` and remains in the feature vector. Supplied BMI is retained; callers editing weight/height must omit stale BMI.

The three bundled examples are **all CAD with multivessel disease**: LAD/LCX/RCA positive; LAD/RCA positive; LAD/LCX positive. None is a healthy or isolated LAD example. Example labels must come from `ground_truth`, never from positional assumptions. They belong to the supplied training data and are demonstrations, not held-out evaluation cases.

## Evidence limits

The saved benchmark JSON matches the bundle's benchmark_metrics. It reports uncalibrated ten-fold candidate/voting results; `scripts/train_pipeline.py` fits calibrated models afterward. Saved voting ROC-AUC values are CAD 0.9466, LAD 0.8739, LCX 0.7583 and RCA 0.7431. No out-of-fold predictions, calibration curves, Brier scores or external cohort validation are supplied to establish calibrated-model performance. The percentages are model scores, not verified clinical risk estimates. The 35%/65% display bands are application thresholds, not demonstrated clinical decision boundaries.

TreeSHAP explains independently fitted XGBoost classifiers trained on labels, rather than a model distilled from ensemble predictions. Contributions describe XGBoost log-odds and need not reproduce the voting score or its sigmoid calibration. They must not be described as exact explanations of the deployed ensemble. This redesign restores input consistency without establishing new clinical performance.

## Verified runtime and readiness

Runtime: Python **3.11.14**, macOS arm64, project `.venv/bin/python`. Embedded serialization identifies scikit-learn **1.7.1**, XGBoost **3.2.0**, CatBoost **1.2.10**; LightGBM stores format `v4`. Those three exact model versions and LightGBM **4.6.0** deserialize and execute successfully. Also verified: NumPy **2.4.6**, pandas **3.0.6**, SHAP **0.51.0**, joblib **1.6.0**, SciPy **1.17.1**, FastAPI **0.142.4**, Pydantic **2.13.5**, SQLAlchemy **2.1.4**, pytest **9.1.1**, uvicorn **0.54.0**. Direct dependencies are pinned in `backend/requirements.txt`; every installed version is constrained by `backend/requirements.lock.txt`.

macOS required Homebrew libomp **23.1.1** (`/opt/homebrew/opt/libomp/lib/libomp.dylib`). A broad DYLD_LIBRARY_PATH pointing at Anaconda caused an unrelated Accelerate/NumPy symbol failure and is unnecessary with libomp installed. Install with `brew install libomp` on macOS, then `uv venv --python python3.11 .venv` and `uv pip install --python .venv/bin/python -r backend/requirements.txt`. The package compatibility check passes. Other OS/architecture combinations were not exercised.

At initialization the service executes all four predictors and explanations using a synthetic default schema without persistence. Health returns HTTP 200 and `status: "healthy", models_ready: true` when this succeeds, or HTTP 503 and `status: "unavailable", models_ready: false` for missing/broken models. A broken bundle leaves the API available for health/recovery. Prediction persistence failures rollback and log exception types without patient parameter strings; inference can still return its valid result. Assessment and audit writes remain separate commits, so an audit failure can follow a successfully saved assessment.

Start an isolated local verification service from the worktree root without disturbing other servers:

```sh
DATABASE_URL=sqlite:////tmp/cardiovision-redesign-preview.db .venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8001
```

## Supplied anatomy contract and provenance

Source is the tracked `BP51939_FMA3_2_1_inference_partof_FMA7088_Heart.zip`, SHA-256 `4b9707e49a4c2948abb8e0d9b3411a3fa16e09a3f40ff0f9e7faf1afa799e3d5`. Its naming identifies BodyParts3D FMA 3.2.1. No independent licensing verification was performed; repository code licensing should not be assumed to establish geometry licensing.

All 123 supplied OBJ filenames are inspected. Selection uses anatomical labels, sorted deterministically, preserving every distinct named mesh piece without size limits, every-other-file selection or duplicate-FMA removal. **62 pieces** are included; **61** omitted names are recorded in metadata. Internal valves, papillary/trabecular and pectinate structures, conduction tissue, fibrous support and cardiac veins are omitted from this external-heart display. All supplied chamber/auricle walls and septa are retained, including membranous septum. The coronary trees are not a patient-specific reconstruction.

| Key | Supplied pieces | Vertices | Triangles | Display contract |
|---|---:|---:|---:|---|
| `lad` | 9 | 7,914 | 13,574 | Anterior interventricular trunk, diagonal/anterior/septal branches |
| `lcx` | 4 | 10,140 | 19,160 | Circumflex trunk/branches and left marginal artery |
| `rca` | 10 | 8,215 | 13,764 | Right coronary trunk/branches, including right marginal branch |
| `myocardium` | 38 | 68,724 | 124,188 | All supplied chamber/auricle walls and septa |
| `left_main` | 1 | 370 | 500 | Neutral left coronary stem; no separate model target |

The older supplied asset already had the same coronary counts. The corrected classifier explicitly prioritizes right-coronary labels, so the right marginal branch remains RCA; generic marginal matching is removed. Myocardium increases from 74,162 to 124,188 triangles. The left-main surface joins the supplied coronary anatomy without assigning it an unsupported patient risk target. Total is 95,363 vertices and 171,186 triangles, with no generated replacement geometry.

Structures keep `positions` (flat xyz), `indices` (flat triangle indices), `vertex_count`, `face_count`. Metadata version 2.0 retains source, units, scale and center, adding archive/hash, the exact transform, per-key full source filenames, omissions and `patient_specific: false`. All groups share one source-space bounding-box center and uniform scale:

`[x,y,z] = scale × [source_x-center_x, source_z-center_z, -(source_y-center_y)]`

The longest normalized extent is 3.5; source z maps to displayed y, with a proper shared rotation preserving registration/winding. Positions are rounded to six decimals. All coordinates are finite; triangle indices are in range. OBJ polygons use triangle fans; negative OBJ indices are supported. `left_main` should use neutral tissue/arterial color, never a fabricated prediction. The existing four risk-color keys remain unchanged.

The deterministic compact JSON is 5,573,082 bytes; SHA-256 `59139a900e2a13164ee4b0d38ed0391385899363693f64abb15d93570a8cc456`. `artifacts/heart_model_anatomy.json` and `frontend/public/heart_model_anatomy.json` are byte-identical, and the anatomy API returns the same payload. Regenerate both together using `.venv/bin/python scripts/process_3d_heart.py`. Rendering fidelity and low-end browser performance remain UI/integration verification tasks.

## Verification

Focused pre-fix command: `DATABASE_URL=sqlite:////tmp/cardiovision-task1-baseline.db .venv/bin/python -m pytest testing/backend/unit/test_input_contract.py -q --tb=line` → **11 failed, 1 passed in 6.03s**. Failures demonstrated category-vector inequality, missing BMI NaN, sample round-trip corruption and acceptance of invalid categories/non-finite BMI. The preserved ECG composite test already passed.

Post-fix suite: `.venv/bin/python -m pytest testing/backend -q --tb=short`. The suite creates a temporary SQLite database before importing the app. It covers numeric/text equality, BMI derivation, exact bundle feature order, 50 saved background vectors, three sample API round trips, finite scores/nonempty explanations, history, health success/failure, model-load failure, safe persistence rollback, deterministic full-source geometry, shared transform and API/static equality. Non-blocking warnings concern existing LightGBM feature-name metadata and library deprecations; no incompatible-version deserialization warning occurred. See the task report for the final exact count/time.

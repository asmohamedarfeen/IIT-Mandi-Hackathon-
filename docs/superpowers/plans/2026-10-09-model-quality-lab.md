# Model Quality Lab Implementation Plan

> **For agentic workers:** Use executing-plans and test-driven-development. Tasks use real evaluation artifacts, never demo payloads.

**Goal:** Complete the expanded Model Quality Lab with real, reproducible OOF evidence and all requested explorers and downloads.

**Architecture:** Shared ML preparation/model/metric primitives feed an offline
evaluator. Validated cached artifacts feed a read-only FastAPI module and a
lazy-loaded React Lab; the clinical workspace remains mounted.

**Tech Stack:** Existing sklearn, XGBoost, LightGBM, CatBoost, SHAP, NumPy,
pandas, FastAPI/Pydantic, ReportLab, React/TypeScript and accessible SVG.

**Spec:** `docs/superpowers/specs/2026-10-09-model-quality-lab-design.md`, expanded
by the user's Phase 1–5 implementation request. Architecture audit:
`docs/model-quality-architecture-audit.md`.

## Global constraints

Seed 42; 10 stratified outer folds; 5 inner calibration folds. Never overwrite
deployed models, benchmarks or patient reports. Fit learned preprocessing inside
folds. Include all requested metrics/curves, threshold analysis, stability,
missingness, leakage diagnostics, provenance and exports. No training from APIs.
No fabricated scores or historical model-selection claims. Preserve prior edits.

## Review focus

- Unknown targets or duplicate features must fail rather than silently encode.
- Inner and outer validation rows must not fit preprocessing or calibration.
- New/partial/corrupt/stale artifacts must not be mistaken for current evidence.
- Undefined rates and empty reliability bins must remain unavailable, not zero.
- Switching sections and fast requests must not reset clinical state or publish stale results.

## Tasks

### 1. Shared ML primitives

Files: `feature_service.py`, new `backend/model_quality/models.py`, shared
`metrics.py`; refactor training and experimental scripts; unit tests.
Interfaces: `extract_targets(df)`, `prepare_features(df, feature_names)`,
`ClinicalPreprocessor(feature_names)`, `get_candidate_models(seed)`,
`binary_metrics(y, probability, threshold)`, `diagnostics(y, probability)`.
- [x] Write and observe failing tests for strict labels, saved feature alignment,
  fold-only medians and metric/curve/empty-bin boundaries.
- [x] Refactor shared implementations; preserve production inference regression scores.
- [x] Run shared tests and full backend suite.

### 2. Offline evaluator and publication

Files: `backend/model_quality/evaluation.py`, `scripts/evaluate_model_quality.py`.
Interface: versioned aggregate JSON with provenance, targets, models, folds,
diagnostics and stability; local OOF audit records; atomic current-run pointer.
- [x] Test fold isolation, cloned model configuration, deterministic membership,
  recomputation, protected paths and complete-run publication.
- [x] Implement all metrics/curves, model comparisons, held-out permutation and
  XGBoost SHAP stability, leakage/missingness checks, source/config snapshots.
- [x] Execute full real dataset evaluation; verify all outputs and protected hashes.

### 3. Read-only Lab API and downloads

Files: `backend/model_quality/{schemas,service,routes,exports}.py`, router mount.
Interfaces: `/api/v1/model-quality/{overview,models,cad,lad,lcx,rca,calibration,
confusion-matrix,shap,class-distribution,reproducibility,report}` plus metrics,
ROC/PR/stability diagnostics and format/section exports.
- [x] Test missing/corrupt/stale runs, threshold boundaries, all endpoint results,
  export formats, cache reuse and no inference/database writes.
- [x] Implement typed validation, cache invalidation, aggregate-only exports,
  sanitised errors and PDF/CSV/JSON downloads.
- [x] Run API tests; render and inspect evaluation PDF pages.

### 4. Frontend Lab

Files: new typed `modelQuality` API/hooks/page/chart files, MainLayout/Header
integration and scoped stylesheet; component tests.
- [x] Test real API-contract rendering, selectors, sort/threshold changes,
  missing/stale/retry states, downloads and workspace preservation.
- [x] Implement all 12 requested sections with real saved data, lazy SVG graphs,
  reusable request hooks/charts, dark mode and mobile/accessibility support.
- [x] Run all frontend tests and build; inspect lazy chunks.

### 5. Review and handoff

- [x] Document reproduction commands, run outputs, model selection trade-offs and
  remaining deployment/clinical constraints.
- [x] Independent ML/clinical and engineering reviews; fix major findings with
  regression tests. Re-run full suites and integrity verification.
- [x] Record completed tasks/results here. Leave prior unrelated changes intact.

## Completion evidence

- Fresh real run: `4c4634aad0894d779f981f9362d3c49a`; 303 cohort records, 4 outcomes,
  10 evaluated configurations, 10 stratified outer folds and 5 inner calibration folds.
- Full rerun against the prior run produced identical fold memberships, OOF
  probabilities and aggregate metrics (maximum absolute difference `0.0`). Dataset
  and deployed model hashes also matched. Transient CatBoost pickle fingerprints can
  vary across identical prediction runs; they identify exact temporary artifacts,
  while the deployed bundle hash is stable.
- The run passed OOF recomputation, archived-source verification and the live API
  returned real summaries, threshold counts, selected curve overlays and PDF exports.
- The existing port 8000 server uses a different Anaconda ML environment; the API
  serves the evidence as stale until it is restarted with the project's pinned `.venv`.

## Execution decision

The user's latest instruction explicitly says implement completely after the
audit, without another planning approval. Execute this plan now, with separate
bounded agents only where interfaces are fixed. Work in the current `v1` feature
checkout to preserve the prior uncommitted application features on which this Lab
depends; a clean worktree would omit them. Do not stage or commit prior edits.

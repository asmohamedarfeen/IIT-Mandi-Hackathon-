# CardioVision roadmap remediation report

Date: 10 October 2026. Scope: [TEAM_EXCELLENCE_ROADMAP.md](TEAM_EXCELLENCE_ROADMAP.md), current working tree and release `20261010T044519Z-77a76019`.

## Outcome and scope

Three agents reviewed model evidence, input/UI behavior and deployment/security in parallel. The coordinating agent reconciled documentation, regenerated and visually inspected the six-page submission PDF, reviewed changes and ran integrated checks. The working tree already contained substantial remediation when this task began; those changes were preserved and validated rather than attributed entirely to this run. No serving weights, classification thresholds, source workbook or historical release archives were changed by this remediation session.

The largest software credibility gaps now have implementations: release-specific Lab evaluation; actual-predictor domain explanations; reviewed input provenance; saved provenance exports; weak-vessel aggregate error analysis; CI/browser checks; minimal Docker configuration; privacy-safe failure handling and an accessible anatomy fallback. This does not mean every roadmap item is complete. Clinical validation, full identity/record authorization, physical-device performance, licensing review and a published demo remain open.

## Concrete fixes added in this session

- **Saved measurement assumptions:** assessment PDFs now include demonstration/reviewed mode and each measurement's source and confirmation from the immutable snapshot. Source/confirmation is also visible in the coronary evidence view; edits cannot rewrite saved provenance.
- **Unknown input handling:** an explicit null/unknown measurement remains unknown rather than becoming a supplied healthy value. Reviewed-case submissions require explicitly supplied and confirmed modeled inputs; demo defaults remain visible assumptions.
- **Accessible anatomy failure:** failed anatomy/WebGL loading provides a local vessel table with probability, status and native keyboard selection buttons. Stale scores stay hidden. A WebGL context loss stops rendering and exposes the fallback.
- **Sample honesty:** the bundled examples are explicitly disclosed as recorded multivessel training examples. No normal/single-vessel truth labels were fabricated.
- **Error analysis:** FN/FP/TP/TN groups now include recorded-measurement availability, medians and quartiles. Quartiles/medians are suppressed below ten available records. Aggregates retain the majority/logistic comparators and avoid exposing row-level records.
- **Experiment guard:** future searches exceeding three configurations are rejected before fitting or writing a release. Existing RCA shortlist is preserved; archived broad sources are unchanged.
- **Explanation integration:** primary deployed-model domain contributions now appear in CAD/vessel explanations and saved PDFs, including baseline, reconstruction, exact inspectable reference measurements and reference limits. Historical XGBoost factors are explicitly separate; older snapshots show unavailable primary attribution rather than fabricating it.
- **Explanation verification:** an offline benchmark checks direct deployed probability fidelity, additive reconstruction, repeat determinism, named alternate-reference sensitivity and an age perturbation. The serving reference remains unchanged.
- **Deployment/privacy:** nginx suppresses access logs and adds response headers; API responses prohibit caching; timing uses a monotonic clock. Unexpected request exceptions are caught before Starlette can re-raise them into a server traceback. Docker projects no longer require fixed global container names; smoke checks use fresh isolated volumes and ports.
- **Executable clean deployment check:** added a Docker smoke command and CI job covering migrations, readiness, frontend proxy, synthetic assessment/PDF, private-file exclusions and persistence across restart. Local execution is blocked by the unavailable Docker daemon.
- **Documentation:** corrected stale README explanations, calibration folds, training commands and Lab status. Updated the submission report's explanation/input/Lab contracts and retained the original roadmap as a dated review.

## Verification

Fresh integrated verification results: Targeted agent runs are supporting evidence, not a substitute for the final integrated run.

| Check | Result |
|---|---|
| Full backend suite | 147 passed (26.93 seconds); scientific-library/deprecation warnings remain |
| Full frontend suite | 77 passed, zero failures |
| Production frontend build | Passed (TypeScript + Vite); 697.08 kB main chunk / 189.62 kB gzip; size warning remains |
| Chromium critical path | 4/4 passed in 23.8 seconds in coordinating-agent run: saved assessment/edit/PDF, unavailable API, keyboard WebGL fallback and context-loss retry |
| Current Lab archive audit | Passed: `c3b99b409b5d440ebc3d6365513264a6`; recomputed metrics, curves, bins, folds, stability and archived source |
| Release archive audit | Passed: hashes, paired OOF metrics, fold coverage, thresholds and promotion |
| Dependency consistency | `uv pip check`: 65 packages checked, no incompatibilities |
| Submission PDF | Generated, exactly six pages, all six rendered and visually inspected |
| Docker build/runtime | **Unverified:** CLI exists, daemon unavailable; smoke attempt blocked before build |

### Explanation benchmark

[Machine-readable benchmark](../artifacts/explanation_validation.json): 15 calls (five repeats of three **synthetic** profiles) across all four loaded predictors. Each call computes the complete seven-domain allocation. Median 125.2 ms, p95 137.2 ms, maximum 158.5 ms; model loading approximately 980 ms on local macOS/Python 3.11.14. Direct prediction difference was zero, largest reconstruction error `2.78e-17`, and repeated contributions were identical. The report includes named reference sensitivity and age+1 effects.

This measures local explanation computation, not whole HTTP request/report latency under load. Three synthetic profiles do not establish population stability, plausible clinical counterfactuals or individual confidence intervals. Reference choice affects attribution and the mixed-domain profiles can be implausible.

## Every roadmap item

**Implemented** means the repository contains the stated software/documentation capability with checks. **Partial** means a concrete component exists but the original acceptance condition remains incomplete. **External** requires evidence, reviewers, credentials or real-world work not supplied by code changes.

| ID | Status | Evidence and remaining acceptance condition |
|---|---|---|
| I01 Documentation reconciliation | Implemented | README, model card, clinical boundary and six-page PDF now distinguish current release, historical benchmarks, deployed domain allocations and independent TreeSHAP. Historical audits are dated. |
| I02 Release-aware Lab | Implemented | Exact cloned per-target recipe, target-specific name/calibration folds and saved thresholds; current archive hash matches bundle. Fixed-configuration OOF remains distinct from nested selection evaluation. |
| I03 Confirmed-input provenance | Implemented | Demo/reviewed modes, sources/confirmation, reviewed completeness guard, unknown handling and immutable PDF/UI provenance. Acquisition timestamps/authenticated assessor identity remain future clinical work. |
| I04 Submission package | Partial | Six-page PDF, setup/release documentation and sample workflow available. Verified 3-10 minute YouTube URL, clean Docker run and geometry redistribution review remain open. |
| I05 Docker/migrations | Partial | Node24/npm ci, pinned backend, minimal image files, Alembic, readiness/proxy configuration and runnable smoke check. No local clean image build/start evidence because daemon unavailable. |
| I06 CI/browser regression | Implemented | CI backend/frontend/build/Chromium plus Docker smoke job; local critical path and fallback regression. Remote CI has not been executed in this session. |
| I07 Deployed predictor explanations | Partial | Exact domain allocations reconstruct deployed probability and carry reference/units/limits; deterministic/fidelity/reference sensitivity benchmark added. Broader plausible-perturbation stability and latency under load remain open. |
| I08 LCX/RCA error analysis | Implemented for offline analysis | Aggregate confusion, subgroup denominators, FN/FP recorded-measurement patterns and majority/logistic baselines. Clinical review/new independent evaluation remain open. No model gain claimed. |
| I09 Frozen protocol | Partial | Protocol and failed-trial registry preserved; internal cohort is explicitly reused. Runner enforces a maximum of three configurations including Baseline before cohort loading, fitting or release-directory creation. Existing RCA shortlist is preserved; broad searches fail with actionable errors. Untouched data and prospectively registered study still external. |
| I10 Defensible feature ablations | Partial | Existing historical candidate ablations/failed search retained; proxy assumptions disclosed. No new predeclared domain-group ablation study or externally justified feature retirement. Serving 84-feature contract unchanged. |
| I11 Anatomy validation | External | Source hashes/transform/pieces retained; no anatomist sign-off or independent geometry licensing evidence supplied. Reference anatomy cannot localize patient lesions. |
| I12 3D performance | Open | Existing pause/disposal remain; context loss now stops rendering. No integrated-GPU FPS/heap/load budget, LOD or measured compression improvement. Existing build warns about a large chunk. |
| I13 Accessible fallback | Implemented with limits | Vessel text/table selection survives WebGL failure, native keyboard buttons and non-color status; existing reduced motion maintained. Physical touch, broader screen-reader/contrast and cross-browser audit remain open. |
| I14 Input ergonomics | Implemented | Units/ranges, source labels, completion/attestation, linked field errors and reviewed-mode block; no inferred unit conversion or validated missing-input imputation. |
| I15 Diverse cases | Partial | Recorded samples clearly labeled and their all-multivessel limitation disclosed. Verified normal/single-vessel examples remain absent. Synthetic benchmark profiles are not labeled outcome examples. |
| I16 Uncertainty presentation | Implemented for available cohort evidence | Reliability counts/Brier/log loss/threshold tradeoffs in Lab. No invented patient interval, clinically validated abstention or external calibration claim. |
| I17 Integration budgets | Partial | Existing response duration/audit plus monotonic timing and local explanation/model-load benchmark. Whole-request/report p50/p95 under load, timeouts and durable idempotency remain open. |
| I18 Legacy training path | Implemented | Legacy CLI refuses ordinary execution; versioned runner designated, historic sources/backups preserved. Explicit legacy opt-in is not a new validation path. |
| I19 External cohorts | External | Needs partner/data permissions, compatible feature/label definitions and frozen independent evaluation. Repeated tuning cannot supply this evidence. |
| I20 Workflow research | External | Needs intended-user recruitment, clinician observation, task/usability outcomes and approved prospective silent evaluation. |
| I21 Deployment access | Partial | Explicit CORS, loopback defaults, optional coarse bearer guard, no-store and safe error logging. Full identity/record ACL/TLS/rate-limit/export controls remain open; shared real-data readiness not claimed. |
| I22 Data lifecycle | Open | Distribution excludes private audit/local DB; durable protected retention/deletion/encryption/access audit/restore/revocation policies still need implementation and verification. |
| I23 Release/drift governance | Partial | Versioned hashes, compatibility checks, backups and audit archives retained. Signed trust, drift monitoring, documented approval and rollback drill remain open. |
| I24 Clinical integration | External/design pending | No FHIR adapter added without verified measurement units/timing/identity/provenance mapping and intended clinical workflow. |
| I25 Intended use/regulatory | External | Current research/educational boundary explicit; qualified clinical/regulatory review needed for any intended clinical product. No compliance claim. |

## Evidence limits and handoff

The release's selection-procedure LCX recall is 55.46% (53 false negatives); RCA recall is 55.26% (51 false negatives). These remain material weaknesses. Fixed-recipe Lab numbers use a different evaluation method and cannot be substituted to claim a release improvement. More features, explanation precision or software test counts do not remedy clinical generalization.

Next engineering acceptance checks: enable Docker and execute `python3 deploy/scripts/smoke_docker.py`; measure full-request/report and physical integrated-GPU performance; implement authenticated identity/record access and lifecycle controls before shared real-data deployment; add independently verified case diversity. Next external deliverables: record/publish/check demo URL, confirm geometry rights and clinician anatomy review, obtain independent cohort and conduct prespecified clinical/workflow studies.

No changes were committed, pushed, published or deployed during this session. Generated PDFs are in ignored `output/pdf/`; source scripts and Markdown report preserve reproducibility. Existing uncommitted work was retained.

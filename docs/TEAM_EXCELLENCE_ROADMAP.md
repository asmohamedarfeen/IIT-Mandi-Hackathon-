# CardioVision: improvement roadmap and scenario catalogue

**Dated review:** The observations below describe the review snapshot. Subsequent
implementation and fresh verification are tracked in
[TEAM_EXCELLENCE_REMEDIATION_REPORT.md](TEAM_EXCELLENCE_REMEDIATION_REPORT.md).
Preserve this backlog and its acceptance criteria as historical context.

Reviewed: 10 October 2026. Scope: Track A problem statement, current repository,
deployed release `20261010T044519Z-77a76019`, and prior verification records.
This is a review and proposed backlog; recommendations below are not implemented
by creating this file. No ranking against other teams is possible without their
submissions. These priorities aim to maximize demonstrable quality against the
published rubric, followed by a credible route toward clinical-sector work.

## 1. What will make this team stand out

The best next investment is trustworthy evidence linked to an excellent interactive
demonstration. Another algorithm or decorative animation alone is unlikely to resolve
the most important gaps. Show what the model predicts, what evidence explains it,
which inputs were actually supplied, how the arteries correspond to outputs, and
what happens when the system cannot produce a reliable assessment.

The judging weights in [Track A](../Track%20A.pdf), page 3, are:

| Area | Weight | Strongest next contribution |
|---|---:|---|
| Predictive performance | 30% | Honest vessel-level validation, error analysis, calibration, fixed experiment protocol |
| 3D visualization | 25% | Anatomically verified vessel mapping, fast low-end rendering, clear selection and accessible fallback |
| Clinical interpretability | 20% | Explanations of the actual deployed predictor, source measurements, stable and clearly bounded attribution |
| System integration | 15% | Same assessment identity across predictions, anatomy colors, explanations and saved reports; dependable recovery |
| Technical implementation | 10% | Reproducible releases, continuous checks, verified deployment and complete submission |

These weights are the problem statement's criteria, not an estimated score for this repo.
For sector leadership, clinician collaboration, external/prospective validation,
workflow evidence and responsible data handling matter beyond the hackathon rubric.

## 2. Current strengths and honest limits

Keep the four-target API, strict outcome exclusion, source-linked explanations,
anatomical provenance, synchronized vessel selection, stale-result handling,
immutable saved assessment reports, nested release evaluation, source hashes and
rollback backups. These are useful foundations, not features to rebuild.

The latest release's paired outer-held-out strategy results are:

| Target | Accuracy | Precision | Recall | F1 | ROC-AUC | False negatives / positives |
|---|---:|---:|---:|---:|---:|---:|
| CAD | 88.78% | 90.63% | 93.98% | 92.27% | 0.9456 | 13 / 21 |
| LAD | 80.53% | 80.73% | 87.57% | 84.01% | 0.8684 | 22 / 37 |
| LCX | 71.29% | 66.00% | 55.46% | 60.27% | 0.7607 | 53 / 34 |
| RCA | 68.32% | 58.33% | 55.26% | 56.76% | 0.7438 | 51 / 45 |

Source: [release summary](../artifacts/model_releases/20261010T044519Z-77a76019/summary.json).
These evaluate the selection procedure on 303 records, not an independent test of
the final full-cohort weights. RCA accuracy increased by two correct classifications,
from 205 to 207; detected positive cases increased from 52 to 63. This is descriptive
evidence, without an established significant improvement. Prior cohort reuse,
the failed broad search and selecting the release after outer evaluation add optimism.

Important observed gaps:

1. Independent XGBoost SHAP does not explain the actual calibrated voting/LightGBM
   predictors exactly. The UI discloses this; older documentation does not consistently do so.
2. Prefilled frontend and backend schema defaults can stand in for unmeasured values.
   A general prefill warning exists, but per-measurement confirmation/provenance does not.
3. LCX and RCA still miss roughly 45% of their positive cases in this internal evaluation.
   High overall CAD accuracy cannot stand in for strong vessel detection.
4. The historical Model Quality Lab is stale after release. Its evaluator also uses
   shared voting labels, global calibration-fold settings and default metric thresholds;
   merely rerunning it does not establish exact release-specific RCA evaluation.
5. Earlier audit and clinical documentation describe preserved weights, old benchmark
   assumptions and attribution claims that are no longer a complete description of the release.
6. No demonstration-video link was found in the inspected repository documentation.
   This is an unverified deliverable, not evidence that no video exists elsewhere.
7. No `.github` CI directory or browser E2E runner was found. Existing browser verification
   is useful but largely manual and historical.
8. Docker frontend uses Node 20 while `frontend/package.json` requires Node >=24;
   it uses `npm install` rather than `npm ci`. Docker startup remains unverified.
9. Backend Docker copies all `artifacts/` and `db/`. That can package private OOF data
   and a local database. It does not copy the workbook needed for full Lab provenance checks.
10. API history/report access has no authentication/authorization; CORS includes `*`;
    the global exception logger includes exception text. These need deliberate handling
    before a shared deployment with real patient information.

Prior completed verification: 122 backend tests, 64 frontend tests, successful production
build, active bundle hash check and live synthetic assessment/PDF download. This audit
did not rerun those tests or perform fresh cross-browser/load/security testing.

## 3. Track A requirement coverage

| Requirement | Current evidence | Remaining improvement |
|---|---|---|
| CAD and LAD/LCX/RCA classification | Four predictors; explicit statuses and stored thresholds | Improve weak vessel recall; validate operating points |
| Use supplied clinical feature domains | Form, schema and 84-feature contract | Distinguish measured, calculated, unknown and defaulted values |
| Exclude vessel/Cath outcomes | Leakage constants, feature checks and evaluation code | Keep regression guard when adding data/features |
| Accuracy, precision, recall, F1, ROC-AUC | Release summary and evidence views | Confidence/uncertainty reporting and release-aware Lab |
| Interactive heart/torso | Existing heart mesh and Three.js viewer | Low-end hardware and anatomical expert checks; torso is optional |
| Probability-dependent artery colors | LAD/LCX/RCA mapping and shared response | Threshold boundary tests using raw probabilities; color-independent labels |
| Rotate, zoom and select regions | Viewer controls and prior browser evidence | Physical touch, keyboard, context loss and cross-browser tests |
| Status and scores beside viewer | Dashboard cards and vessel detail | Data completeness and uncertainty context |
| Explain why a prediction was made | Independent XGBoost SHAP with caveat | Attribution for actual deployed probability or measured surrogate fidelity |
| Measurements and contributions | Source lineage and input navigation | Complete factor accounting, stability and correlated-feature grouping |
| Anatomical resources | Source mesh archive, transform and selected-piece metadata | Verify redistribution terms and include attribution |
| Visible educational disclaimer | UI, API and report disclaimer | Retain visibility in all layouts and exports |
| Working integrated prototype | Local live verification and saved reports | Verified clean-machine/container startup |
| Trained pipeline and clean code | Release runner, pinned Python runtime and saved weights | Retire ambiguous legacy training path; exact evaluator metadata |
| Documentation <=6 pages | Six-page project PDF | Regenerate after changes; keep this detailed roadmap separate |
| YouTube demonstration 3-10 minutes | Not verified in repo | Record, publish and add checked URL to submission checklist |
| Responsive on standard hardware | Hidden-view pause, disposal, prior desktop/mobile checks | Measured FPS, latency and resource budgets on integrated graphics |
| Extensible architecture | Existing service/schema/renderer modules | Version feature/model/anatomy contracts; avoid unnecessary abstractions |

## 4. Prioritized implementation backlog

P0 = submission credibility/reliability first. P1 = strongest next differentiation.
P2 = clinical-sector readiness. Effort S/M/L is a relative estimate, not a delivery promise.
Security items become P0 before shared use with real data.

| ID | Priority / effort | Add, improve or remove | Why and acceptance condition | Main evidence / owner |
|---|---|---|---|---|
| I01 | P0 / S | Reconcile current documentation | Correct exact-SHAP/governance claims; date historical audits; one release identity and honest limits throughout | `docs/CLINICAL_VALIDATION.md`, `docs/MODEL_AND_ANATOMY_AUDIT.md`, `README.md`; technical lead |
| I02 | P0 / M | Make Lab target/release aware | Use actual target model name, calibration configuration and stored class threshold; no RCA LightGBM called voting; distinguish fixed-configuration evaluation from nested selection evaluation | `backend/model_quality/evaluation.py`, service and UI; ML/backend |
| I03 | P0 / M | Add confirmed-input provenance | Each field records supplied/confirmed/defaulted/calculated/unknown status. Demo mode can prefill; real-case mode must not turn unknown into healthy automatically. Snapshot/export shows assumptions | Patient schema, form, normalization and snapshots; frontend/backend |
| I04 | P0 / M | Complete submission package | Verified video URL, clean setup, six-page PDF, model/source manifest, license/attribution and sample workflow; judge can reproduce without author's machine | README, output PDF, deployment; team lead |
| I05 | P0 / M | Verify Docker and migrations | Match Node >=24, use locked install, run database migration explicitly, exclude private files, test frontend/API proxy and readiness from clean volumes | `deploy/docker/`, nginx; platform |
| I06 | P0 / M | Add CI and browser critical-path tests | Backend tests, frontend tests/build, feature contract and E2E assessment/edit/vessel/report checks pass on clean checkout | New CI workflow/browser tests; QA |
| I07 | P1 / L | Explain the deployed predictor | For RCA, evaluate attribution of calibrated LightGBM ensemble; for voting, model-agnostic probability explanation is an option. Validate reconstruction/fidelity and latency. If retaining surrogate, disclose disagreement and never claim exactness | Prediction/explanation services; ML |
| I08 | P1 / M | Analyze LCX/RCA failures | Separate false-negative/false-positive patterns, subgroup counts, feature availability and uncertainty. Show majority/logistic baselines; predeclare next experiment objective | Release OOF, metrics; ML + clinical reviewer |
| I09 | P1 / M | Freeze evaluation protocol | Cap trials, record failed searches, choose metrics/threshold policy before tests. Report uncertainty for paired differences with appropriate dependency caveats; obtain untouched/external data | Improvement runner and protocol; ML |
| I10 | P1 / M | Add defensible feature ablations | Recorded-only vs engineered vs domain groups; remove unvalidated BP/PTP/RWMA proxies only through retraining and revalidation, not by changing loaded 84-feature vectors | Feature service, constants; ML + domain expert |
| I11 | P1 / M | Validate reference anatomy | Anatomist/clinician reviews LAD/LCX/RCA pieces, orientation and territories. Show orientation cues and source provenance; left main remains neutral | Anatomy processing/viewer; 3D + clinical reviewer |
| I12 | P1 / M | Measure and optimize 3D performance | Measure integrated-GPU FPS/load/heap first; lazy-load heavy code, compress/cache mesh and add LOD if needed. Verify branch coverage and preserve source mapping | Viewer, anatomy assets, Vite; frontend/3D |
| I13 | P1 / M | Add accessible fallback | Text/table/SVG vessel detail works when WebGL fails; keyboard selection, non-color status, contrast, reduced motion and screen reader checks | Viewer, modal, cards; frontend/QA |
| I14 | P1 / M | Improve input ergonomics | Units, missing-value policy, completion summary, field-level errors and explicit demo mode; treat out-of-supported-range values transparently | Form/schema/API errors; frontend/backend |
| I15 | P1 / M | Add release-consistent case diversity | Include normal, single-vessel and multi-vessel examples if available. Distinguish recorded cohort examples from synthetic scenarios; neither is held-out proof | Sample endpoint and demo assets; ML/frontend |
| I16 | P1 / M | Show uncertainty responsibly | Reliability diagrams with counts, Brier/log loss and threshold tradeoffs. Model disagreement/abstention only after validation; no invented patient-level confidence interval | Model Evidence/Lab; ML/frontend |
| I17 | P1 / M | Add monitored integration budgets | Measure p50/p95 inference/explanation/report time, model load and request failures; handle timeout/retry/idempotency without duplicate assessments | API, request coordinator, repository; backend |
| I18 | P1 / S | Retire ambiguous legacy training instructions | Clearly designate the release runner; archive or guard legacy `train_pipeline.py`, whose normalization can impute before CV. Preserve historical sources and backups | README and scripts; ML lead |
| I19 | P2 / L | Acquire externally validated cohorts | Confirm labels, timing, patient overlap, feature definitions and lawful access. Freeze model first; evaluate transportability/calibration and subgroup uncertainty | Data partnership; clinical/ML |
| I20 | P2 / L | Conduct workflow and usability research | Define intended users and decision point, observe clinicians, measure task completion and understanding, then run approved prospective silent evaluation | Clinical/product team |
| I21 | P2 / L | Add deployment access controls | Identity, record-level authorization, TLS, allowed origins, rate limits and secure export handling; deny unauthorized history/report access | API/config/proxy; security/backend |
| I22 | P2 / M | Define data lifecycle | Data minimization, retention/deletion, encryption/backups, access audit and privacy-safe telemetry; validate restores and access revocation | Database/deployment; security/platform |
| I23 | P2 / L | Add release/drift governance | Signed/trusted artifact manifest, compatibility checks, monitored drift, rollback drills and approval records. No automatic retraining from unreviewed patient feedback | Release lifecycle; ML/platform |
| I24 | P2 / L | Add standards-based clinical integration | FHIR/structured measurement import only with units, timestamps, identity mapping and provenance; validate mappings before replacing manual inputs | Future adapter; clinical/backend |
| I25 | P2 / L | Establish intended-use and regulatory strategy | With qualified domain/regulatory counsel, determine intended use, evidence, human oversight and applicable jurisdiction. No compliance claim based solely on SHAP/disclaimer | Clinical/product leadership |

Dependencies: I01-I06 before submission polish; I03 and I14 before treating unknown
measurements as supported inputs; I08-I10 before another broad tuning round;
I07 requires explicit output units and I17 latency measurement; I21-I22 before shared
real-data deployment; I19-I20 before clinical-benefit claims.

## 5. What to remove, simplify or avoid

| Item | Action | Keep instead |
|---|---|---|
| Exact explanation/compliance claims in old clinical guide | Correct or remove; do not imply SHAP proves clinical governance | Actual explainer identity, units, fidelity limits and evidence |
| Old audits presented as current | Mark historical; cross-link current release rather than deleting provenance | Dated historical snapshots and one current model card |
| Generic voting name for RCA | Replace in release-aware evaluation/UI | Per-target actual configuration and threshold |
| Low/Moderate/High described as measured blockage or validated severity | Remove such interpretation wherever found | Probability display bands with explicit limits |
| Defaults treated as recorded measurements | Remove that assumption in real-case mode | Confirmed measurements and visible default/missing provenance |
| Constant Exertional CP affecting prediction expectations | Mark currently excluded/non-predictive or hide in model-focused view | Preserve original clinical record if needed, without attributing model effect |
| Duplicate lipid-ratio aliases | Consolidate in a future versioned feature contract | Preserve loaded 84-feature compatibility until validated replacement |
| Unsupported PTP/BP/RWMA clinical interpretations | Remove clinical authority claims; ablate feature formulas before retirement | Recorded measurements and documented research assumptions |
| Repeated unbounded model searches on the same 303 records | Stop leaderboard chasing | Predeclared small experiments and independent evaluation |
| Decorative physiological claims from pulse animation | Keep pulse optional and illustrative; remove if distracting or costly | Anatomical focus, labels and usable orbit controls |
| New chatbot, treatment generator, diagnosis narrative or lesion coordinates | Defer; unsupported by supplied targets and raises evaluation burden | Bounded educational explanation of existing measurements |
| Raw OOF, local DB and scratch artifacts inside public/container packages | Exclude from distribution after provenance backup | Minimal serving weights, aggregate evidence, public anatomy and protected audit storage |
| Wildcard CORS and unauthenticated shared real-data access | Remove before real-data deployment | Explicit origins, authentication and record-level authorization |
| Duplicate training paths without clear authority | Guard/archive obsolete entry points | One reviewed release command and documented rollback |
| Early microservices/Kubernetes/large model stack | Defer until measured operational need | Existing modular app with clear contracts and reliable deployment |

Do not delete immutable release evidence, original source data, user work or historical
reports to make the repository look smaller. Cleanup should be reviewable and reversible.

## 6. Scenario catalogue and acceptance checks

This is the complete set of material scenarios identified by this scoped review,
not a claim that every possible software or clinical failure has been enumerated.
Existing guards should be preserved. Proposed checks need implementation and execution.

### A. Dataset, preprocessing and evaluation

| ID | Scenario | Expected behavior / improvement | Related item |
|---|---|---|---|
| S01 | Cath/LAD/LCX/RCA or identifier accidentally enters predictors | Training fails before fit; output excludes all target columns for every target | I06, I09 |
| S02 | Empty or wrong worksheet selected | Validate populated sheet, row count, named columns and dataset hash; do not train on empty headers | I06 |
| S03 | Missing/unknown outcome label | Reject with count and field context; never silently map to negative | I06 |
| S04 | New cohort contains missing measurements | Existing improvement command rejects; future supported pipeline fits imputation on training rows only | I03, I10 |
| S05 | Repeated patient records across folds/sites/time | Audit patient identifiers where available; group splits and prevent cross-cohort overlap | I09, I19 |
| S06 | Raw category is textual/numeric, unknown or fractional | Accepted encodings give identical vectors; invalid values get actionable 422 | I06, I14 |
| S07 | Feature order/derived formula changes with old weights | Fail compatibility validation; require a versioned retrained/revalidated release | I10, I23 |
| S08 | BMI is supplied while weight/height changes | Recompute in UI or explicitly confirm supplied BMI provenance; keep saved assessment unchanged | I03, I14 |
| S09 | Weak-vessel accuracy looks good because of imbalance | Display majority baseline, precision/recall/F1/AUC and confusion counts, not accuracy alone | I08 |
| S10 | More models/thresholds are tried after outer results | Record experiment history and selection optimism; no claim of untouched test performance | I09 |
| S11 | Gain is only two correct classifications | Show counts, paired uncertainty and selection caveats; no statistical-significance claim without suitable analysis | I09 |
| S12 | Accuracy increases while recall/calibration worsens | Apply declared release rule; preserve prior release on failure; clinical tradeoff requires expert-defined evidence | I08, I16 |
| S13 | Subgroup has few positives or one class | Report support and unavailable/unstable metrics, not reassuring zeroes; avoid subgroup-specific thresholds without evidence | I08, I19 |
| S14 | Incoming population differs from cohort | Display supported-population limits; evaluate shift and external calibration before reuse | I19, I23 |
| S15 | Derived blood-pressure/PTP/RWMA proxies dominate | Show estimated status and source; run grouped/raw-only ablations; no lesion-location inference | I07, I10 |

### B. Patient input and prediction meaning

| ID | Scenario | Expected behavior / improvement | Related item |
|---|---|---|---|
| S16 | User submits an untouched default form | Clearly identify synthetic/default mode; real-case mode requires reviewed inputs/completeness | I03 |
| S17 | Laboratory result is unknown | Unknown remains unknown; apply only a validated missing-input policy or decline assessment | I03, I14 |
| S18 | mg/dL versus mmol/L, cm versus m or platelet units confused | Explicit units and validated conversion; do not infer units from plausible numbers | I14, I24 |
| S19 | Empty, NaN, infinite or unsupported-range value | Explain field failure and focus input; no new prediction/colored anatomy | I06, I14 |
| S20 | Valid but unusual/inconsistent input combination | Flag unsupported distribution or inconsistency where validated; never silently diagnose or overcorrect | I14, I16 |
| S21 | Value exists but was measured at wrong time | Capture timestamp/source; require alignment with declared prediction time point | I03, I19, I24 |
| S22 | RCA probability lies between 0.40 and 0.65 | Class may be Stenotic while display band is Moderate; show saved class threshold and band definitions | I01, I06 |
| S23 | Probability is almost 0.35/0.65 or rounds across a boundary | Test raw-value class/color decisions and displayed rounding together; do not imply blockage percentage | I06 |
| S24 | CAD and vessel classes disagree | Explain independently trained outputs and dataset definitions; do not silently force labels/probabilities to agree | I08, I16 |
| S25 | Low score occurs in a known positive case | Keep 'does not rule out disease' context; include false-negative examples in error analysis | I08, I15 |
| S26 | Symptoms/user asks for diagnosis or treatment | Maintain intended educational role; no automatic treatment or clearance recommendation | I25 |

### C. Attribution and explainability

| ID | Scenario | Expected behavior / improvement | Related item |
|---|---|---|---|
| S27 | Independent XGBoost disagrees with serving predictor | Show both identities/fidelity limits; prioritize actual-model explanations | I07 |
| S28 | User thinks SHAP log-odds are probability points | Show output units/base value and conversion limits; no misleading additive probability explanation | I01, I07 |
| S29 | Top eight factors do not reconstruct output | Label truncated factors; show omitted contribution/base value where supported; validate complete reconstruction separately | I07 |
| S30 | Correlated raw and derived inputs split attribution | Group by original measurements, explain dependency and avoid double counting/causal interpretations | I07, I10 |
| S31 | Small plausible input change radically reorders factors | Measure explanation stability; disclose instability and use grouped presentation if appropriate | I07, I16 |
| S32 | Source measurement navigation points to edited values | Show assessed snapshot and edited input distinction; never rewrite historical explanation values | I03, I06 |
| S33 | Explanation fails while predictor succeeds | Show explicit partial/unavailable state or fail by declared contract; no fabricated factors | I07, I17 |
| S34 | Counterfactual changes sex/age or dependent biomarkers unrealistically | Defer or constrain to validated plausible scenarios; never label as treatment guidance | I07, I25 |

### D. Anatomy, interaction and accessibility

| ID | Scenario | Expected behavior / improvement | Related item |
|---|---|---|---|
| S35 | Right marginal branch/left main mapped incorrectly | Verify source anatomy labels; RCA branch stays RCA; left main neutral; expert review | I11 |
| S36 | User interprets red segment as patient lesion location | State reference anatomy/whole-vessel probability; no fabricated narrowing or lesion coordinates | I11 |
| S37 | Mesh is obscured by tissue | Accessible tissue opacity/hide and vessel focus; label what is selected | I11, I13 |
| S38 | WebGL unsupported or context lost | Visible retry and usable table/SVG alternative; no blank-only dashboard | I13 |
| S39 | Integrated GPU, slow network or mobile device | Measure load/FPS, compress/cache, adapt quality without dropping required vessel coverage | I12 |
| S40 | Keyboard-only/color-vision/screen-reader user | Buttons/table provide equivalent vessel selection and risk text; contrast and focus verified | I13 |
| S41 | Reduced motion, fullscreen denial or touch pinch | Respect preference; recover visibly from denial; test real devices and browser policies | I13 |
| S42 | Repeated tab switching, route mount/unmount or long session | No extra canvases/listeners or growing GPU resources; hidden rendering pauses | I06, I12 |
| S43 | Static anatomy differs from API asset | Verify anatomy version/hash/schema, surface mismatch and preserve output-to-structure contract | I11, I23 |

### E. Integration, persistence and release operations

| ID | Scenario | Expected behavior / improvement | Related item |
|---|---|---|---|
| S44 | Rapid edits produce out-of-order responses | Latest request owns cards/colors/explanations; older evidence remains stale and hidden | I06 |
| S45 | Double submit/retry after response loss | Define idempotent assessment request key; avoid unintended duplicate saved assessments | I17 |
| S46 | API unavailable, timeout or startup model not ready | Clear status/retry; neutral unassessed anatomy; do not replace with fake or default scores | I06, I17 |
| S47 | Database/audit write fails after valid inference | Clearly distinguish computed versus saved result; rollback appropriate transaction; report download disabled unless snapshot exists | I17 |
| S48 | Download after inputs change | Use immutable assessment ID/snapshot, not current form or new inference | I06 |
| S49 | Old snapshot lacks new class/threshold fields | Compatible historical display; absent fields remain unknown; no fabricated old classifications | I06, I23 |
| S50 | Model file replaced while worker retains old weights | Restart/reload coherently; active worker hash identifies its actual model; verify readiness for every worker | I05, I23 |
| S51 | Model and benchmark publication interrupted | Serve release-consistent evidence from one manifest/bundle; staged validation and recoverable atomic publication | I23 |
| S52 | Lab stale or target model/calibration changed | Keep archive visibly historical; evaluate exact per-target configuration/threshold and clearly identify method | I02 |
| S53 | Clean Docker build or empty/existing DB volume | Compatible Node/Python, pinned installs, explicit migrations, working proxy and readiness; no private artifact copying | I05 |
| S54 | Corrupt/untrusted joblib or incompatible runtime | Trusted artifacts only; hash/signature and dependency checks; readiness unavailable and prior release recoverable | I23 |
| S55 | Rollback after a failed release | Restore coherent weights/evidence, restart, verify hash; historical assessments retain original provenance | I23 |
| S56 | Concurrent users generate inference/report load | Measure p95 latency/resource use, bound heavy work and maintain response/assessment isolation | I17 |

### F. Sharing, submission and future clinical work

| ID | Scenario | Expected behavior / improvement | Related item |
|---|---|---|---|
| S57 | Unauthorized caller enumerates history/report UUIDs | Authenticate and authorize access to each record; UUID alone is not an access control | I21 |
| S58 | Exception/log/export exposes clinical values | Privacy-safe structured logs, authorized exports, no sensitive browser/analytics payloads | I21, I22 |
| S59 | Public image/repo contains DB or private OOF | Packaging excludes them; inspect image/files and maintain protected provenance separately | I05, I22 |
| S60 | Backups, deletion request or staff access revocation | Defined retention, tested restore/delete and access audit; no indefinite accidental copies | I22 |
| S61 | Dataset/anatomical license is unclear | Verify original terms/attribution and allowed redistribution; source naming does not prove permission | I04, I11 |
| S62 | Demo examples all have multivessel CAD | Add verified diverse examples or explicitly disclose limitation; do not invent recorded labels | I15 |
| S63 | Judge uses fresh laptop/no dedicated GPU | Clean install/container, loopback demo, fallback and measured hardware results | I04, I05, I12 |
| S64 | Video/docs contradict current model | Check release ID, threshold, metrics, six-page cap and 3-10 minute video together | I01, I04 |
| S65 | Clinician interprets score as future event risk | State outcome/time point: cohort CAD/stenosis classification, not validated future-event forecast | I19, I25 |
| S66 | Product expands to clinical decision support | Define intended use, qualified oversight, external and prospective evaluation plus applicable review | I19-I25 |
| S67 | Performance shifts after deployment | Monitor label quality, feature/score shift and delayed outcomes; investigate before retraining | I23 |
| S68 | EHR/ECG/image/longitudinal modalities added | Validate new data definitions and model separately; current structured ECG flags are not raw multimodal imaging | I19, I24 |

## 7. Execution sequence and team roles

### Before the next submission

1. Technical lead and ML engineer reconcile I01/I02, publish a current model card,
   and agree on one evaluation story. Keep internal results and limits visible.
2. Frontend/backend pair implement confirmed-input provenance and usable field errors
   (I03/I14), preserving the API/snapshot migration path.
3. Platform/QA verify clean deployment, artifact packaging and critical E2E tests
   (I05/I06). Local prototype remains synthetic/de-identified.
4. 3D/frontend pair plus domain reviewer validate artery mapping and low-end interaction
   (I11-I13). Record measurements instead of making untested performance claims.
5. ML/domain pair work on actual-predictor attribution and weak-vessel error analysis
   (I07-I10/I16). Avoid another unrestricted search without independent evidence.
6. Team lead records the final demonstration, checks the six-page report and video URL
   and rehearses the judge workflow (I04/I15).

A small team can combine roles. Every item needs one accountable owner and someone
else checking its acceptance criteria; role names are not a staffing requirement.

### Suggested 6-8 minute demonstration

| Segment | Demonstrate |
|---|---|
| 0:00-0:45 | Problem, four outputs, reference-anatomy and educational limits |
| 0:45-2:00 | Explicit sample/demo mode, measurement units, completeness and assessment |
| 2:00-3:15 | CAD/vessel statuses, probability bands, rotate/zoom/select linked anatomy |
| 3:15-4:30 | Original measurements, derived features and honest explanation identity |
| 4:30-5:30 | Input edit, stale-result protection, reassessment and saved PDF snapshot |
| 5:30-6:30 | Validation metrics, weak-vessel failures, current release and selection limits |
| 6:30-7:30 | Error/fallback behavior, reproducible setup, next clinical-validation steps |

The schedule fits the statement's 3-10 minute requirement. Do not publish patient
identifiers or private OOF files in the recording. Video recording/publication is
a separate action; this roadmap does not publish anything.

### Beyond the hackathon

First secure clinical/data partnerships and a precisely bounded intended use.
Then freeze an evaluation protocol, collect externally comparable data and test
workflow usefulness. Add operational/privacy controls before handling real patient
information in shared environments. Future imaging, longitudinal data or FHIR
integration should address a demonstrated user need and undergo separate validation.
There is no justified promise that this 303-record prototype is clinically deployable
or that implementing this backlog guarantees competition victory.

## 8. Completion scorecard

| Goal | Evidence required to call it done |
|---|---|
| Scientific credibility | Exact model/threshold names, leakage guards, baseline comparisons, recorded experiments and clearly qualified metrics |
| Explanation fidelity | Actual-model reconstruction/fidelity checks, output units, source lineage and measured performance |
| Usable assessment | Confirmed/unknown/defaulted inputs, units, task completion and comprehension checks |
| Anatomical quality | Expert-reviewed vessel mapping, public provenance and verified licensing |
| Reliable interaction | Browser E2E plus real device/accessibility/failure scenarios and measured low-end performance |
| Reproducibility | Clean-machine build/start, lockfiles, migrations, release manifest and tested rollback |
| Submission completeness | Working repo, weights, current <=6-page PDF and checked 3-10 minute YouTube URL |
| Clinical-sector progress | Independent validation, intended-use documentation, oversight and measured workflow benefit |

## 9. Sources and review boundaries

Repository evidence: [data pipeline](DATA_PIPELINE.md), [release summary](../artifacts/model_releases/20261010T044519Z-77a76019/summary.json),
[historical verification](verification.md), [historical anatomy/model audit](MODEL_AND_ANATOMY_AUDIT.md),
`backend/cardio/service/prediction_service.py`, `backend/cardio/service/explanation_service.py`,
`backend/cardio/schemas/patient_schema.py`, `backend/model_quality/evaluation.py`,
`backend/core/config.py`, `backend/main.py`, `scripts/train_pipeline.py`,
`frontend/src/utils/patient.ts`, `frontend/src/components/HeartViewer3D.tsx`,
`frontend/src/services/api.ts`, `frontend/package.json` and `deploy/`.
Historical documents are evidence of prior behavior and verification, not proof of
every current runtime behavior. Static findings are identified above; absence claims
are scoped to inspected repository paths. No competitor analysis or independent
medical, security or regulatory certification was performed.

Primary-source guidance and links are recorded in [research notes](roadmap-primary-sources.md).
Recommendations and effort estimates are this review's engineering judgment; they
are not additional requirements imposed by Track A.

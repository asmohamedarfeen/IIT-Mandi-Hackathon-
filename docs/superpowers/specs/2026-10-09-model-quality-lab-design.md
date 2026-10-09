# Model Quality Lab

## Purpose and approved scope

Give judges a dedicated, evidence-backed view of how the models compare and why
the prototype uses its current ensemble. Success means they can inspect class
balance, performance, confusion matrices and calibration for CAD, LAD, LCX and
RCA, then download a summary and reproduce the evaluation.

The user approved the proposed Lab and running a reproducible evaluation on the
supplied dataset. This document specifies that design for review before an
implementation plan is written.

## Existing evidence and constraints

- The existing Model evidence modal shows supplied average 10-fold CV metrics.
  Its benchmark JSON does not preserve out-of-fold predictions, confusion
  matrices or calibration bins. Those details cannot be inferred from averages.
- The deployed artifact uses sigmoid-calibrated ensembles with a saved feature
  contract. Earlier inspection found 84 saved features while the current feature
  engineer emits 86. The evaluator must use the saved ordered contract, not
  silently change deployed feature definitions or retrain production weights.
- Existing training code imputes missing numerical values before splitting.
  The new evaluator must fit learned preprocessing only on training folds.
- The supplied cohort is also the training cohort. New cross-validation is
  internal evaluation of fixed model configurations, not external validation of
  the already-fitted production weights or an independent model-selection study.
- Supplied scores do not always favor the ensemble over individual candidates.
  The Lab must not manufacture a historical selection rationale or winner.
- Preserve existing patient workflows, report snapshots, databases and artifacts.
  Browser access was previously denied; do not retry without renewed permission.

## Architecture

Keep training offline and the web application read-only with respect to evaluation.

1. An explicit command-line evaluator reads the supplied dataset and saved model
   configuration, trains temporary model copies, and writes a separate versioned
   evaluation artifact. It never calls the production training script or writes
   the model bundle, benchmark summary, assessment database or patient reports.
2. A backend service validates and reads the evaluation artifact. A dedicated
   endpoint returns aggregate results and provenance; a download endpoint returns
   the same reproducible summary as an attachment. Neither endpoint trains models.
3. A dedicated Model Quality Lab view reads those endpoints. Main navigation
   switches between the assessment workspace and Lab without destroying current
   form values, selected vessel or prediction state.
4. Preserve the existing benchmark endpoint and supplied results. The Lab exposes
   them as a separately labelled evidence source rather than merging them with
   new results. The existing Model evidence entry point links to the Lab.

No new database tables, background job system, external service or plotting
dependency is required. Reuse existing React, TypeScript, Python and ML libraries.

## Evaluation protocol

### Data preparation

- Read the supplied workbook and explicitly validate target labels. Do not turn
  unknown or missing labels into negative outcomes.
- Exclude Cath, CAD, LAD, LCX and RCA from all model inputs. Use the bundle's
  saved feature names in their exact order. Reject missing, duplicated, unexpected
  non-finite or incompatible features with actionable diagnostics; do not pad
  missing saved features with zero.
- Normalize categories and calculate row-local features using the existing
  definitions. Imputation and any scaling must be learned inside training folds.
  Preserve the deployed feature-definition compatibility fixes already in place.
- Save per-target positive and negative counts, sample count and label definition.
  No clinical identifiers or original measurement rows enter the public summary.

### Models and splits

- Use stratified 10-fold outer cross-validation with shuffle and seed 42.
  Persist each row's fold assignment and out-of-fold predicted probability in a
  local audit artifact. Each row is scored once by a model not fitted on that row.
- Compare Logistic Regression, Random Forest, Extra Trees, XGBoost, LightGBM,
  CatBoost, the uncalibrated soft-voting ensemble and its sigmoid-calibrated variant.
- Clone the saved ensemble configuration for temporary ensemble evaluation and
  document every configuration. Candidate configurations not recoverable from
  the saved bundle use the existing candidate factory, explicitly labelled as
  current-script configurations rather than historically verified settings.
- Fit calibration only within each outer training fold, using five inner folds.
  The outer validation fold must not fit preprocessing, models or calibrators.
  Put learned preprocessing inside each fitted estimator pipeline so inner
  calibration validation rows also cannot influence imputation or scaling.
- Limit estimator threads for predictable local execution and record those
  settings. A deficient class count or failed fit stops publication of a complete
  run; partial results cannot masquerade as a completed evaluation.
- Keep fixed configurations. Do not tune hyperparameters or automatically select
  and deploy a winner based on the same folds used to report performance.

### Outputs and interpretation

- Save pooled out-of-fold ROC-AUC, accuracy, precision, recall, F1, specificity,
  MCC and Brier score for each target/model. Where undefined, report null with a
  reason, never a fabricated score.
- Save per-fold metrics and their mean/standard deviation. Distinguish pooled
  metrics from supplied fold averages. Fold variation is not a confidence interval.
- Confusion matrices contain integer TN, FP, FN and TP at an explicit probability
  threshold of 0.50. Label rows as recorded outcome and columns as prediction.
  This evaluation threshold is not the dashboard's 35%/65% display bands and is
  not presented as a clinically validated decision boundary.
- Save reliability bins using ten fixed equal-width probability intervals,
  including bin bounds, count, mean predicted probability and observed positive
  fraction. Empty bins have no observation and are not plotted as zero incidence.
  Display the identity line and Brier score, not a claim of clinical calibration.
- Record dataset, model bundle, evaluation source and feature-contract hashes;
  schema version, UTC generation time, seed, folds, model parameters, package
  versions, preprocessing protocol and exact reproduction command.
- Export aggregate JSON and a readable evaluation summary. Local row-indexed OOF
  records support independent recomputation but are not served through the web API.
  An atomic publication step replaces the summary only after all targets finish.

## Lab experience

Use the application's existing visual language, with readable tables and direct
labels rather than a dashboard full of decorative metric cards.

- Header: Model Quality Lab, evidence source, generation time, short artifact
  identity and a Download evaluation summary action.
- Target selector: CAD, LAD, LCX and RCA. Model selector controls confusion matrix
  and calibration details; initially show the calibrated ensemble when available.
- Cohort balance: positive/negative counts and percentages with an accessible
  labelled proportion bar. Explicitly identify the internal training cohort.
- Model comparison: sortable metric table with metric direction indicated,
  selected/deployed-configuration marker and a separately labelled supplied-CV
  comparison. Performance rank is not a deployment recommendation.
- Confusion matrix: four clearly labelled integer counts, selected threshold,
  recorded/predicted axes and an equivalent accessible table.
- Calibration: SVG reliability plot with predicted versus observed axes, ideal
  line, bin counts, calibrated/uncalibrated ensemble comparison and a numerical
  table so the chart is not the only means of reading the evidence.
- Selection explanation: describe the actual fixed voting composition and
  sigmoid calibration configuration, show measured comparisons and trade-offs,
  and distinguish documented configuration from an unrecorded historical
  selection decision. Do not claim the ensemble won every target/metric.
- Reproducibility: protocol, versions, hashes, command, limitations and download.
  Truncate long hashes visually only if the complete value remains accessible.

Support keyboard interaction, meaningful focus states, contrast, mobile wrapping
and horizontally scrollable tables. Preserve workspace state when returning from
the Lab. No live training button is included in this prototype.

## Failure states and provenance

Missing evaluation data shows an explicit Not evaluated state with the reproduction
command, while still allowing inspection of supplied benchmarks. It never shows
synthetic matrices or calibration curves. Network failures offer Retry.

Invalid or incompatible artifacts are rejected by the backend. A different current
model hash is surfaced as stale evaluation; historical results remain labelled
with the evaluated hash and are not presented as matching the current deployment.
API errors expose safe messages, not clinical rows or exception payloads.

The downloadable summary is built from saved evaluation results, with no model
execution and no patient data or row-indexed predictions. Keep research-only,
single-cohort, small-sample, fixed-configuration and no-external-validation
limitations visible. Existing lack of authentication remains a documented
prototype limitation; this task does not authorize public clinical deployment.

## Acceptance and verification

1. Every requested Lab section is functional for all four targets and supported
   by actual saved evaluation results.
2. Independent recomputation from local OOF records matches aggregate metrics,
   confusion counts, calibration bins and sample/class counts within specified
   numerical tolerances. Matrices total the evaluated cohort size.
3. Tests establish outer-fold isolation, calibration fit isolation, deterministic
   splitting, saved feature order, target exclusion, strict labels and proper
   empty-bin/undefined-metric behavior.
4. API tests cover valid, missing, corrupt and stale artifacts, sanitized failures
   and summary download. No web request triggers training or a database write.
5. Frontend tests cover navigation/workspace preservation, selectors, sorting,
   all requested sections, retry/unavailable/stale states and download behavior.
6. Run the full backend/frontend suites and production build. Run the complete
   evaluator once on the supplied dataset and verify that protected production
   artifact hashes are unchanged.
7. Record measured runtime and the reproduction command. If dependency/platform
   differences prevent bitwise reproduction, state numerical tolerances and
   report the difference rather than hiding it.
8. Visual browser verification remains pending renewed authorization. Do not
   imply live browser QA from component tests alone.

## Non-goals

No production model replacement, new hyperparameter search, external-cohort
claims, medical recommendations, patient upload flow, automatic model deployment
or changes to existing assessment/report interpretation. This is one integrated
offline-evidence and read-only Lab feature, not a general experiment platform.

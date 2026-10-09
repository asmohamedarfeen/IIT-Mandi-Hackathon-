# Model Quality Lab: architecture audit

## System map

`scripts/train_pipeline.py` loads the workbook via `feature_service`, builds six
candidate models and a fixed five-member soft vote, evaluates uncalibrated
10-fold CV, fits a five-fold sigmoid-calibrated vote and separate XGBoost
explainers, then writes `cardiovision_ensemble.joblib` and `benchmark_summary.json`.
The existing benchmark reduces fold predictions to seven averaged metrics;
confusion counts are computed but discarded. Global SHAP uses the full training
matrix. There are no stored OOF probabilities or calibration diagnostics.

`PredictionService` loads the trusted local bundle, hashes it, aligns inputs to
its saved feature names, scores all four targets, and uses independent XGBoost
TreeSHAP to produce ranked contributions with original measurement lineage.
Readiness executes one inference. FastAPI dependency providers reuse this service;
repositories persist assessments and immutable report snapshots. Report download
reads a snapshot and does not rerun prediction. These paths must remain unchanged.

React App loads benchmark metadata. MainLayout owns modal state; DashboardPage
owns clinical inputs, assessment cancellation/debounce, prediction, selected
vessel and cases. Conditional unmounting loses that state. Preserve the workspace
mounted when switching to a lazy-loaded Lab. Existing API client, native dialogs,
buttons, table scrolling, typed utilities and React renderer tests are reusable.
Three.js is isolated to the heart viewer; Lab charts need no Three.js or new chart
package. Existing CSS has a light theme only, so Lab dark theme needs scoped tokens.

## Findings and implementation rulings

1. **Leakage-sensitive preprocessing:** numerical medians are computed on the
   complete dataset before CV. Separate deterministic normalization from learned
   imputation and use a shared sklearn transformer inside every evaluation fit,
   including inner calibration folds. Keep inference compatibility and test it.
2. **Feature contract drift:** engineer emits 86 columns, deployed bundle expects
   84; the two additional lipid ratios duplicate Castelli I/II. Share feature
   alignment, use saved order and fail on missing/non-finite saved columns. Do
   not modify fitted formula quirks or weights in this task.
3. **Duplicated estimators/metrics:** candidate definitions, vote members and
   XGBoost configuration repeat in training; experiments repeat feature formulas
   and metric code. Extract a shared model registry and metrics module; make
   training/experimental entry points delegate to shared implementations.
4. **Optimistic experimental selection:** experiment weights and thresholds are
   optimized on the same OOF labels used for reporting. Retire that entry point
   in favor of the fixed-configuration evaluator. Threshold exploration is
   descriptive and must not claim unbiased performance of a selected threshold.
5. **Target encoding:** unknown target labels currently become negative outcomes.
   Centralize strict label extraction, rejecting missing/unknown outcomes.
6. **Missing provenance:** benchmarks lack seeds/fold records/source hashes and
   archived OOF results. Publish versioned evaluation runs atomically with
   source snapshots, dependency versions, configurations, fold membership and
   local audit records. No request may train or modify production artifacts.
7. **Selection rationale:** vote membership is fixed, not automatically selected
   by a documented winning search. Explain recorded composition, calibration and
   measured trade-offs; do not invent historical reasons or declare accuracy
   alone decisive. SVM and Decision Tree will be additional fixed comparators;
   stacking is not implemented and will not have fabricated results.
8. **Clinical bounds:** this is internal, single-cohort CV of cloned configured
   models, not independent validation of already-fitted weights. Calibration and
   thresholds are not clinical decision recommendations. Correlated engineered
   features limit permutation/SHAP ranking interpretation. Fold variability is
   descriptive, not a confidence interval. No real patient rows in public exports.
9. **Operational debt outside this feature:** broad CORS, no authentication,
   database create-all at import, mutable full-data retraining script and Docker
   database-volume/migration coupling remain deployment limitations. Document
   these without unrelated rewrites or a claim of clinical production readiness.

## Approved implementation boundary

Refactor shared ML primitives first, run real ten-fold OOF evaluation of candidate
models and saved ensemble configurations with nested calibration, serve validated
cached aggregate artifacts, and build all requested Lab explorers and exports.
Protect production hashes before and after evaluation; retain existing regression
tests. No browser automation without renewed authorization.

## Method references

Inner calibration accepts estimator pipelines:
https://scikit-learn.org/1.7/modules/generated/sklearn.calibration.CalibratedClassifierCV.html

Average precision is reported separately from trapezoidal PR area:
https://scikit-learn.org/1.7/modules/generated/sklearn.metrics.average_precision_score.html

Independent XGBoost TreeSHAP raw outputs are log-odds:
https://shap.readthedocs.io/en/latest/generated/shap.TreeExplainer.html

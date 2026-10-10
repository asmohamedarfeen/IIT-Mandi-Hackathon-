# Evaluation protocol and experiment ledger

This protocol freezes future work as of 10 October 2026. It is not retrospective preregistration of the two completed searches. `artifacts/experiment_registry.json` links both archived experiments and their outcomes. The broader trial was unsuccessful and retained; the RCA-only second trial reused the same cohort and promoted a two-record accuracy gain. Original archived sources and reports are unchanged.

## Evidence distinctions

1. The release runner evaluates a model/threshold **selection procedure** with outer 10-fold, inner 3-fold selection and calibration inside estimator fit. Fold decisions may have different thresholds. It chooses promotion after observing outer results, which adds selection optimism.
2. Model Quality Lab evaluates **fixed cloned deployed recipes** at their saved thresholds. CAD/LAD/LCX calibrate sigmoid CV5; RCA LightGBM calibrates sigmoid CV3 and classifies at 0.4. It preserves each exact recipe and learns raw preprocessing within calibration training folds. No weight or threshold changes are deployed by evaluation. These scores can differ from the release-procedure scores and must be labeled separately.
3. `analyze_release_errors.py` reaggregates archived release-procedure errors. It neither retrains nor validates final fitted weights. Majority-class accuracy, class support, FN/FP, subgroup denominators and paired fold differences are descriptive checks. Fold differences are not confidence intervals: overlapping training sets and repeated development invalidate simple independent-fold significance claims.

## Before the next experiment

- Freeze dataset/source hashes, exact ordered features, target definitions and saved thresholds. Keep identifiers and all outcomes out of every predictor. Complete duplicate/participant/site/time overlap checks; no participant identifiers were supplied, so patient grouping remains unavailable.
- Obtain an independent untouched cohort or a prospectively locked temporal/site holdout. Keep it closed until one final model is selected. The present 303 records have been reused and cannot become an untouched test set by changing seeds.
- Record a timestamped experiment specification before fitting: objective (for example vessel recall with a clinically agreed specificity floor), at most **three candidate configurations and one threshold policy**, tuning budget, split plan and declared metric ordering. Do not expand after seeing outer outcomes. The runner rejects more than three configurations (including Baseline) before fitting or creating release files; broad historical shortlists remain archived and require an explicit new bounded design before execution.
- Report logistic regression and majority baselines, all four outcomes, accuracy, sensitivity/specificity, precision/F1, AUROC/PR metrics, Brier/log loss and calibration support. Report all failures, unavailable subgroup metrics and numerical differences, including discordant classifications. Never select on accuracy alone.
- The current automatic gate requires strict accuracy gain, recall/AUC drop at most 0.02 and Brier increase at most 0.01. These are engineering bounds, not clinical requirements. A clinician must predefine intended-use tradeoffs and study acceptance criteria before use beyond research.
- For a prospective untouched cohort, predeclare paired uncertainty estimates and clustered/site-aware resampling where appropriate. Multiple endpoints and repeated trials require declared multiplicity handling; consult a statistician for sample-size/power and study design. No statistical-significance claim is justified by the current two-record gain.
- Archive fixed inputs, source, parameters, decisions and failed runs. Stop when the trial cap is reached. New proposals require new evidence or a documented rationale, not another unbounded sweep on the same cohort.

## Commands

```sh
.venv/bin/python scripts/evaluate_model_quality.py --production-only
.venv/bin/python scripts/evaluate_model_quality.py --verify
.venv/bin/python scripts/analyze_release_errors.py --release artifacts/model_releases/20261010T044519Z-77a76019 --logistic-baseline
# Versioned release runner; applies gate and preserves backups
.venv/bin/python scripts/improve_models.py --targets RCA --deploy
```

The last command is a reproduction command for the existing RCA protocol, not a recommendation to repeat selection and claim another independent gain. `scripts/train_pipeline.py` refuses CLI execution without explicit `--legacy-retrain`, which acknowledges that historical direct overwriting and pre-CV normalization are unsuitable for new evidence.

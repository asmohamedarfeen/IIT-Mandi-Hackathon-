# CardioVision model card

Current release: `20261010T044519Z-77a76019`, generated 10 October 2026. Active model SHA-256: `0138162c96a87500b8d8abf0132f831b938b89b5f62e4277f022d0482a3de544`. This is a research demonstration, not an externally validated clinical product.

## Dataset and inputs

303 unique complete workbook records, 59 columns, one local cohort. CAD 216/87, LAD 177/126, LCX 119/184 and RCA 114/189 positive/negative. No patient/site/time identifiers were supplied for grouped validation. All outcome columns Cath/CAD/LAD/LCX/RCA and constant Exertional CP are excluded; inference uses exactly 84 saved engineered features. Deterministic clinical proxies preserve fitted definitions and are not independently validated clinical scores. No target leakage is permitted between vessel tasks.

## Deployed configurations and release evidence

The following metrics describe the archived **outer-fold release-selection procedure**, not held-out evaluation of final full-cohort weights. Fixed cloned deployed-configuration metrics are separately available in Model Quality Lab. Threshold selection in the release procedure occurs inside training folds; the final deployed RCA threshold is 0.4. Sigmoid calibration uses five folds for retained voting targets and three folds for RCA LightGBM.

| Target | Deployed recipe | Calibration folds | Final threshold | Release-procedure accuracy | Recall | FN / FP | Majority accuracy |
|---|---|---:|---:|---:|---:|---:|---:|
| CAD | Existing sigmoid-calibrated voting ensemble | 5 | 0.5 | 0.8878 | 0.9398 | 13 / 21 | 0.7129 |
| LAD | Existing sigmoid-calibrated voting ensemble | 5 | 0.5 | 0.8053 | 0.8757 | 22 / 37 | 0.5842 |
| LCX | Existing sigmoid-calibrated voting ensemble | 5 | 0.5 | 0.7129 | 0.5546 | 53 / 34 | 0.6073 |
| RCA | Sigmoid-calibrated LightGBM-d3 | 3 | 0.4 | 0.6832 | 0.5526 | 51 / 45 | 0.6238 |

The broad first search improved no targets. The narrower RCA second search reused the same cohort; accuracy increased by 2/303 records (67.66% to 68.32%) and recall from 45.61% to 55.26%. This is descriptive internal evidence with historical and release-selection optimism, not statistical significance or proven generalization. CAD/LAD/LCX retained their previous fitted models. LCX/RCA false negatives remain material. [Aggregate error analysis](../artifacts/release_error_analysis.json) reports all subgroup denominators and paired discordant classifications without individual records. [Experiment registry](../artifacts/experiment_registry.json) preserves both trials.

## Fixed-configuration and baseline comparison

The current Lab run `c3b99b409b5d440ebc3d6365513264a6` is ready and matches the active model hash. Fixed deployed RCA recipe OOF accuracy is 70.63% and recall 67.54%; these are **a different method** from the 68.32%/55.26% nested selection-procedure release scores. No new weights were trained for deployment and no additional gain is claimed. Both methods reuse the development cohort.

Untuned logistic comparator accuracy (same stratified 10-fold seed42, training-only preprocessing/scaling, C=1, threshold0.5) is CAD 85.81%, LAD 75.58%, LCX 66.34%, RCA 63.70%. Full metric/confusion support is in the aggregate error-analysis artifact. These baselines contextualize class imbalance and complexity; they are not external validation.

## Runtime and explanation contract

Validated inputs pass through category normalization, fitted-compatible row-local engineering, ordered feature alignment, exact per-target calibrated prediction and a saved class threshold. Independent target outputs are preserved even if they disagree. Display bands 35%/65% are separate from binary classification thresholds. Saved assessment snapshots retain model identity and prediction evidence for later PDF/history retrieval.

Primary grouped-domain Shapley attributions query the deployed calibrated predictor in probability units against a named synthetic reference. They reconstruct its probability relative to that reference and are not causal or individual-feature clinical effects. Separate historical independent XGBoost TreeSHAP has log-odds units and is not an exact explanation of the deployed model. Model Quality Lab comparator stability (when evaluated) is separate evidence; production-only runs explicitly omit it.

## Limits and exclusions

No independent clinical cohort, prospective study, external calibration, clinical threshold validation, patient-specific coronary imaging, lesion localization, or compliance certification is supplied. Assumed inputs can alter outputs; incomplete-input robustness needs separate validation. Aggregate RWMA and reference anatomy do not locate individual stenosis. Low scores do not rule out disease. Small subgroup estimates cannot establish fairness or equivalent sensitivity.

## Operations and audit

Use [DATA_PIPELINE.md](DATA_PIPELINE.md) for data boundaries, current release paths, reproduction and rollback. Use [EVALUATION_PROTOCOL.md](EVALUATION_PROTOCOL.md) before another experiment. The release runner stages artifacts and retains backups; the Lab evaluator never deploys weights. Legacy `train_pipeline.py` CLI is retired and requires explicit historical opt-in. Archived reports and sources remain immutable; historical docs are labeled accordingly. Private OOF records remain offline and are excluded from public endpoints/exports.

See [CLINICAL_VALIDATION.md](CLINICAL_VALIDATION.md) for required external evidence before clinical-sector use.

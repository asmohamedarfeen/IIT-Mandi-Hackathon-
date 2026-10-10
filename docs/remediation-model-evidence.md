# Model evidence remediation report

10 October 2026. Scope: roadmap I02, I08, I09, I15 support and I18, plus current clinical/model documentation. Existing dirty work and historical evaluation/release archives were preserved. No production weights or classification thresholds were changed in this remediation.

| Item | Status | Concrete work | Remaining boundary |
|---|---|---|---|
| I02 | Implemented and verified | Exact per-target saved calibration recipe cloned; raw preprocessing fits inside calibration folds; RCA LightGBM sigmoid CV3 and threshold0.4 preserved, voting targets CV5/0.5. Generic deployed/un-calibrated IDs, per-target names/parameters, default saved operating point, corrected calibration UI and benchmark selection-bias wording. New ready Lab run `c3b99b409b5d440ebc3d6365513264a6` replaces pointer while preserving archives. | Fixed recipe OOF differs from nested release-strategy evaluation; both remain internal. |
| I08 | Implemented analysis and baselines | Offline aggregate FN/FP, majority baseline, fixed untuned logistic OOF baseline, sex/age/DM/HTN denominators, missing-value note, paired discordant counts and per-fold differences in `artifacts/release_error_analysis.json`. | Clinical feature-review and independent weak-vessel validation need qualified reviewers/data; no accuracy improvement claimed by aggregation. |
| I09 | Protocol and registry implemented | `EVALUATION_PROTOCOL.md` caps future candidates, predeclares objective/threshold tradeoffs, freezes inputs and prohibits treating reused cohort as untouched test data. `experiment_registry.json` retains failed broad trial and second RCA trial with hashes. | Prospective preregistration and independent cohort require external work. No inferential confidence interval fabricated from dependent/postselected folds. |
| I15 | Model-side support | Current model card records original all-multivessel samples as demonstrations; team integrates verified record-based normal/single/multivessel diversity separately. | Root implementation owns selection/UI; examples cannot become held-out proof. |
| I18 | Implemented | Legacy training CLI fails before imports/fitting without explicit `--legacy-retrain`; directs operator to versioned release runner and evaluation-only mode. Archived historical source is untouched. | Explicit historical opt-in can overwrite artifacts and must not supply new validation evidence. |

## Results and limits

Archived nested release-procedure RCA errors are FN51/FP45; paired changes are 13 newly correct and 11 newly wrong, a net two records. Current fixed saved RCA recipe OOF accuracy70.63%/recall67.54% has a different evaluation method from nested selection accuracy68.32%/recall55.26%. Other deployed recipes are unchanged. No new clinical validity or statistical significance is established.

Current `MODEL_CARD.md` and rewritten `CLINICAL_VALIDATION.md` replace unqualified historical log-odds/protection and anatomical claims. `MODEL_AND_ANATOMY_AUDIT.md` and `verification.md` are labeled historical while preserving their original measurements.

## Reproduce

```sh
.venv/bin/python scripts/evaluate_model_quality.py --production-only
.venv/bin/python scripts/evaluate_model_quality.py --verify
.venv/bin/python scripts/analyze_release_errors.py --release artifacts/model_releases/20261010T044519Z-77a76019 --logistic-baseline
.venv/bin/python -m pytest testing/backend/unit/test_quality_evaluation.py testing/backend/unit/test_quality_integrity.py testing/backend/unit/test_quality_artifacts.py testing/backend/unit/test_release_error_analysis.py testing/backend/unit/test_quality_evidence_validation.py testing/backend/api/test_model_quality.py -q
npm --prefix frontend test
npm --prefix frontend run build
```

Validation: new threshold/recipe regression tests first failed, then passed. 58 focused backend tests passed; frontend test/build outcomes are reported in the overall remediation report because other team members are adding checks concurrently. The new RCA Lab regression verifies actual target name, calibration CV3 and saved40% slider. Archived OOF/source verification passed; `QualityService` reports ready for the new run. Private OOF records are retained offline; aggregate outputs never expose patient labels, vectors or identifiers.

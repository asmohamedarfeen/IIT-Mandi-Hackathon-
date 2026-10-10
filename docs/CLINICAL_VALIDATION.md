# Clinical validation boundary

CardioVision is a research demonstration using the supplied 303-record extended Z-Alizadeh Sani workbook. It has no independent external or prospective clinical validation. Current configuration, dataset, release identity and limitations are recorded in [MODEL_CARD.md](MODEL_CARD.md). The executable evaluation protocol is described in [EVALUATION_PROTOCOL.md](EVALUATION_PROTOCOL.md).

## Intended use and outcomes

The application demonstrates separate CAD, LAD, LCX and RCA predictions from recorded demographic, examination, ECG, laboratory and echo variables. The workbook's Cath and vessel labels define retrospective outcomes; they do not supply patient-specific lesion coordinates. All five possible outcome column names (Cath/CAD/LAD/LCX/RCA) are excluded from every predictor. Independent outputs may disagree; the application must not silently reconcile them.

An estimated model probability is not a validated clinical risk estimate, diagnosis, treatment recommendation or rule-out result. A low score can occur in a known positive case. The 35%/65% visualization bands and the per-target class thresholds are application choices, not clinically established operating points. Defaults and synthetic example inputs are assumptions, not measured observations.

## Anatomy and explanation boundaries

The 3D heart is a reference anatomy model. Vessel colors represent model probabilities; territory highlighting is an illustrative aggregate RWMA assumption. There is no patient-specific coronary imaging or validated plaque/lesion localization. Individual anatomical supply varies, so territory coloring must not be interpreted as an anatomical diagnosis.

Primary domain attributions evaluate the actual deployed calibrated predictor in probability space against an explicit synthetic reference. They attribute grouped domains (rather than independent individual features), reconstruct the prediction relative to that reference, and are descriptive model behavior. They do not demonstrate causality, clinical protection, conditional-population SHAP or patient-specific counterfactual treatment benefit. Separate legacy XGBoost TreeSHAP values, where exposed, describe that independent classifier's log-odds; they need not reproduce the deployed calibrated probability. Neither explanation establishes clinical validity or safety.

## Evidence already present

- Versioned nested-selection release reports, failed-trial archive, private outer-fold audit and exact source hashes.
- Fixed deployed-configuration OOF Lab evaluation, including per-target calibration folds and saved thresholds; clearly separated from nested procedure scores.
- Aggregate FN/FP analysis, majority baseline, class support and exploratory sex/age/DM/HTN subgroup denominators. Small subgroup estimates are unstable and are not fairness validation.
- Contract, leakage, persistence, explanation and deployment tests. Software tests establish behavior, not patient benefit.

## Evidence still required for clinical-sector use

1. Clinician-defined intended use, population, workflow, target definition and acceptable false-negative/false-positive tradeoff.
2. Representative independent data with patient/site/time separation and appropriate permissions; missing-input and prevalence shift studies.
3. Prespecified external/prospective evaluation, calibration, uncertainty and adequately powered subgroup analysis; comparison against appropriate clinical baselines.
4. Human factors/workflow evaluation with clinician oversight, monitoring and incident response; security and privacy assessment appropriate to deployment.
5. Jurisdiction-specific governance and regulatory review where the intended use requires it. No compliance or certification is claimed by this repository.

The supplied dataset cannot resolve these external dependencies by more repeated tuning. Existing probability and anatomy limitations must remain visible in demonstrations and exports.

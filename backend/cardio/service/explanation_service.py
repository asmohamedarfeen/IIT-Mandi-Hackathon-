"""Measurement lineage for the saved feature contract, without recalculating it."""

from typing import Any

from backend.cardio.schemas.patient_schema import PatientInputSchema
from backend.cardio.schemas.prediction_schema import FeatureLineage, SourceMeasurement

RECORDED_KEYS = {field.alias or name for name, field in PatientInputSchema.model_fields.items()} - {"patient_id"}
ECG_KEYS = ["St Elevation", "St Depression", "Tinversion", "Q Wave"]
DERIVED_FEATURES: dict[str, tuple[list[str], str]] = {
    "Pulse_Pressure": (["BP"], "Systolic pressure minus estimated diastolic pressure (0.65 × systolic pressure). Diastolic pressure was not measured."),
    "Mean_Arterial_Pressure": (["BP"], "(Systolic pressure + 2 × estimated diastolic pressure) / 3. Diastolic pressure is estimated as 0.65 × systolic pressure."),
    "Shock_Index": (["PR", "BP"], "Pulse rate / systolic pressure."),
    "LDL_HDL_Ratio": (["LDL", "HDL"], "LDL / HDL; HDL is bounded below at 10 in preprocessing."),
    "Castelli_Risk_Index_II": (["LDL", "HDL"], "LDL / HDL; HDL is bounded below at 10 in preprocessing."),
    "Total_Cholesterol_Ratio": (["LDL", "HDL", "TG"], "Estimated total cholesterol (LDL + HDL + TG / 5) / HDL; HDL and TG are bounded below at 10. Total cholesterol is estimated, not recorded."),
    "Castelli_Risk_Index_I": (["LDL", "HDL", "TG"], "Estimated total cholesterol (LDL + HDL + TG / 5) / HDL; HDL and TG are bounded below at 10. Total cholesterol is estimated, not recorded."),
    "Atherogenic_Index_Plasma": (["TG", "HDL"], "log10(TG / HDL); TG and HDL are bounded below at 10."),
    "TyG_Index": (["FBS", "TG"], "Natural logarithm of FBS × TG / 2; FBS is bounded below at 20 and TG at 10."),
    "Non_HDL_Cholesterol": (["LDL", "TG"], "Estimated total cholesterol minus HDL simplifies to LDL + TG / 5. TG is bounded below at 10; total cholesterol is estimated, not recorded."),
    "NLR": (["Neut", "Lymph"], "Neutrophils / lymphocytes; lymphocytes are bounded below at 1."),
    "PLR": (["PLT", "Lymph"], "Platelets / lymphocytes; lymphocytes are bounded below at 1."),
    "SII": (["PLT", "Neut", "Lymph"], "Platelets × neutrophils / lymphocytes; lymphocytes are bounded below at 1."),
    "BUN_CR_Ratio": (["BUN", "CR"], "Blood urea nitrogen / creatinine; creatinine is bounded below at 0.2."),
    "Age_EF_Ratio": (["Age", "EF-TTE"], "Age / ejection fraction; ejection fraction is bounded below at 10."),
    "BMI_Category_Overweight": (["BMI"], "1 when assessed BMI is at least 25 and below 30; otherwise 0. Assessed BMI may be supplied or calculated from height and weight."),
    "BMI_Category_Obese": (["BMI"], "1 when assessed BMI is at least 30; otherwise 0. Assessed BMI may be supplied or calculated from height and weight."),
    "ECG_Abnormality_Score": (ECG_KEYS, "Sum of the four encoded ECG findings. The fitted composite omits encoded LVH and poor R progression."),
    "Ischemic_ECG": (ECG_KEYS, "1 when the sum of these four encoded ECG findings is positive; otherwise 0."),
    "Has_RWMA": (["Region RWMA"], "1 when the assessed regional wall motion score is greater than 0; otherwise 0."),
    "RWMA_LAD_Territory": (["Region RWMA"], "1 when the regional wall motion score is 1 or 4; otherwise 0. This is a fitted feature rule, not patient-specific imaging."),
    "RWMA_RCA_Territory": (["Region RWMA"], "1 when the regional wall motion score is 2 or 4; otherwise 0. This is a fitted feature rule, not patient-specific imaging."),
    "RWMA_LCX_Territory": (["Region RWMA"], "1 when the regional wall motion score is 3 or 4; otherwise 0. This is a fitted feature rule, not patient-specific imaging."),
    "Pretest_PTP_Score": (["Age", "Sex", "Typical Chest Pain", "Atypical", "DM", "HTN", "Current Smoker", "FH"], "Fitted proxy: age ≥60 adds 2, age 50–59 adds 1; male sex adds 2, typical chest pain adds 3; atypical pain, diabetes, hypertension, smoking and family history each add their encoded value. Not a validated clinical probability."),
    "Metabolic_Risk_Score": (["DM", "HTN", "TG", "FBS"], "Diabetes + hypertension + 1 if TG >150 + 1 if FBS >100. The fitted composite does not include HDL."),
    "Lifestyle_Risk_Index": (["Current Smoker", "EX-Smoker", "FH", "HTN"], "Current smoking + 0.5 × former smoking + family history + hypertension, using encoded categories."),
}
for lab in ("TG", "CR", "ESR", "WBC", "FBS", "BUN"):
    DERIVED_FEATURES[f"Log_{lab}"] = ([lab], f"Natural logarithm of 1 + {lab}; negative values are clipped to 0 before transformation.")


def build_feature_lineage(feature: str, clinical_inputs: dict[str, Any], model_input_value: float) -> FeatureLineage:
    if feature in RECORDED_KEYS:
        kind, sources, derivation = "recorded", [feature], None
    elif feature in DERIVED_FEATURES:
        sources, derivation = DERIVED_FEATURES[feature]
        kind = "derived"
    else:
        kind, sources, derivation = "unmapped", [], None
    return FeatureLineage(
        feature_kind=kind,
        model_input_value=model_input_value,
        source_measurements=[SourceMeasurement(input_key=key, recorded_value=clinical_inputs[key]) for key in sources if key in clinical_inputs],
        derivation=derivation,
    )

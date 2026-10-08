"""
Constants for CardioVision AI machine learning and clinical inference pipeline.
"""

from typing import Final, Dict, List

# Target names and leakage definitions
TARGET_NAMES: Final[List[str]] = ["CAD", "LAD", "LCX", "RCA"]
RAW_TARGET_COLUMNS: Final[List[str]] = ["Cath", "LAD", "LCX", "RCA"]
LEAKAGE_COLUMNS: Final[List[str]] = ["Cath", "CAD", "LAD", "LCX", "RCA"]

# Target clinical descriptions
TARGET_DESCRIPTIONS: Final[Dict[str, str]] = {
    "CAD": "Overall Coronary Artery Disease (>=50% luminal stenosis in >=1 major vessel)",
    "LAD": "Left Anterior Descending Coronary Artery Stenosis (Anterior myocardial perfusion)",
    "LCX": "Left Circumflex Coronary Artery Stenosis (Lateral & posterior myocardial perfusion)",
    "RCA": "Right Coronary Artery Stenosis (Inferior myocardium & AV node conduction)",
}

# 3D anatomical visualization risk thresholds & hex color mapping
RISK_THRESHOLD_LOW: Final[float] = 0.35
RISK_THRESHOLD_HIGH: Final[float] = 0.65

COLOR_LOW_RISK: Final[str] = "#10B981"       # Emerald green
COLOR_MODERATE_RISK: Final[str] = "#F59E0B"  # Amber
COLOR_HIGH_RISK: Final[str] = "#EF4444"      # Crimson red

# Feature types in Z-Alizadeh Sani dataset
RAW_NUMERIC_FEATURES: Final[List[str]] = [
    "Age", "Weight", "Length", "BMI", "BP", "PR", "FBS", "CR", "TG",
    "LDL", "HDL", "BUN", "ESR", "HB", "K", "Na", "WBC", "Lymph",
    "Neut", "PLT", "EF-TTE", "Region RWMA", "Function Class"
]

RAW_BINARY_NUMERIC_FEATURES: Final[List[str]] = [
    "DM", "HTN", "Current Smoker", "EX-Smoker", "FH", "Edema",
    "Typical Chest Pain", "Q Wave", "St Elevation", "St Depression",
    "Tinversion"
]

RAW_BINARY_TEXT_FEATURES: Final[List[str]] = [
    "Obesity", "CRF", "CVA", "Airway disease", "Thyroid Disease",
    "CHF", "DLP", "Weak Peripheral Pulse", "Lung rales",
    "Systolic Murmur", "Diastolic Murmur", "Dyspnea", "Atypical",
    "Nonanginal", "Exertional CP", "LowTH Ang", "LVH", "Poor R Progression"
]

RAW_MULTICLASS_FEATURES: Final[List[str]] = [
    "Sex", "BBB", "VHD"
]

# Zero-variance columns to prune during preprocessing
ZERO_VARIANCE_COLUMNS: Final[List[str]] = ["Exertional CP"]

# Optimal classification decision thresholds tuned per target via 10-fold CV
OPTIMAL_VESSEL_THRESHOLDS: Final[Dict[str, float]] = {
    "CAD": 0.46,
    "LAD": 0.38,
    "LCX": 0.36,
    "RCA": 0.34,
}

# Engineered clinical feature names
ENGINEERED_FEATURES: Final[List[str]] = [
    "Pulse_Pressure",
    "Mean_Arterial_Pressure",
    "Shock_Index",
    "Castelli_Risk_Index_I",
    "Castelli_Risk_Index_II",
    "Atherogenic_Index_Plasma",
    "TyG_Index",
    "Non_HDL_Cholesterol",
    "NLR",
    "PLR",
    "SII",
    "BUN_CR_Ratio",
    "Age_EF_Ratio",
    "ECG_Abnormality_Score",
    "Ischemic_ECG",
    "Has_RWMA",
    "RWMA_LAD_Territory",
    "RWMA_LCX_Territory",
    "RWMA_RCA_Territory",
    "Pretest_PTP_Score",
    "Metabolic_Risk_Score",
    "Lifestyle_Risk_Index",
    "BMI_Category_Overweight",
    "BMI_Category_Obese",
    "Log_TG",
    "Log_CR",
    "Log_ESR",
    "Log_WBC",
    "Log_FBS",
    "Log_BUN",
]

# Clinical safety disclaimer mandated by medical ML guidelines
CLINICAL_SAFETY_DISCLAIMER: Final[str] = (
    "CardioVision AI is an experimental decision-support and visualization research tool. "
    "Predictions and 3D maps do not constitute diagnostic medical advice or replace formal "
    "coronary angiography."
)


# One category contract shared by dataset cleaning and the API boundary.
CATEGORY_CODES = {
    **{name: {"n": 0, "y": 1} for name in RAW_BINARY_TEXT_FEATURES},
    **{name: {} for name in RAW_BINARY_NUMERIC_FEATURES},
    "Sex": {"male": 1, "fmale": 0, "female": 0},
    "BBB": {"n": 0, "lbbb": 1, "rbbb": 2},
    "VHD": {"n": 0, "mild": 1, "moderate": 2, "severe": 3},
    "Function Class": {}, "Region RWMA": {},
}
CATEGORY_MAXIMUM = {"BBB": 2, "VHD": 3, "Function Class": 4, "Region RWMA": 4}


def encode_category(value, name):
    """Accept declared labels and integer-valued numeric codes; reject unknowns."""
    text = str(value).strip().lower()
    if text in CATEGORY_CODES[name]:
        return CATEGORY_CODES[name][text]
    try:
        number = float(text)
    except (ValueError, TypeError):
        raise ValueError(f"Unsupported category for {name}") from None
    maximum = CATEGORY_MAXIMUM.get(name, 1)
    if not 0 <= number <= maximum or not number.is_integer():
        raise ValueError(f"{name} must be an integer category from 0 to {maximum}")
    return int(number)

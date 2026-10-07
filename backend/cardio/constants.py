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

# Engineered clinical feature names
ENGINEERED_FEATURES: Final[List[str]] = [
    "Pulse_Pressure",
    "Mean_Arterial_Pressure",
    "LDL_HDL_Ratio",
    "Total_Cholesterol_Ratio",
    "ECG_Abnormality_Score",
    "Metabolic_Risk_Score",
    "Lifestyle_Risk_Index",
    "BMI_Category_Overweight",
    "BMI_Category_Obese"
]

# Clinical safety disclaimer mandated by medical ML guidelines
CLINICAL_SAFETY_DISCLAIMER: Final[str] = (
    "CardioVision AI is an experimental decision-support and visualization research tool. "
    "Predictions and 3D maps do not constitute diagnostic medical advice or replace formal "
    "coronary angiography."
)

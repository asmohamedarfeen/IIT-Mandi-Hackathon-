"""
Feature processing and clinical feature engineering pipeline for CardioVision AI.
"""

from typing import Tuple, List, Dict, Any
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

from backend.cardio.constants import (
    RAW_NUMERIC_FEATURES,
    RAW_BINARY_NUMERIC_FEATURES,
    RAW_BINARY_TEXT_FEATURES,
    RAW_MULTICLASS_FEATURES,
    LEAKAGE_COLUMNS,
    TARGET_NAMES,
    ZERO_VARIANCE_COLUMNS,
)


def _safe_series(df: pd.DataFrame, col: str, default_val: float) -> pd.Series:
    """Safely extracts a numeric Series from df or generates a constant Series if missing."""
    if col in df.columns:
        return pd.to_numeric(df[col], errors="coerce").fillna(default_val)
    return pd.Series(default_val, index=df.index, dtype=float)


class ClinicalFeatureEngineer(BaseEstimator, TransformerMixin):
    """
    Scikit-learn compatible transformer that calculates evidence-based
    cardiovascular risk features from raw patient records without data leakage.
    """

    def __init__(self):
        pass

    def fit(self, X: pd.DataFrame, y=None):
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        df = X.copy()

        # 1. Hemodynamic / Blood Pressure metrics
        sbp = _safe_series(df, "BP", 120.0)
        # Diastolic BP estimation based on standard clinical cardiovascular ratio
        estimated_dbp = sbp * 0.65
        df["Pulse_Pressure"] = sbp - estimated_dbp
        df["Mean_Arterial_Pressure"] = (sbp + 2.0 * estimated_dbp) / 3.0

        pr = _safe_series(df, "PR", 75.0)
        df["Shock_Index"] = pr / sbp

        # 2. Lipid / Cholesterol ratios & Atherogenic Indices
        ldl = _safe_series(df, "LDL", 100.0)
        hdl = _safe_series(df, "HDL", 40.0).clip(lower=10.0)
        tg = _safe_series(df, "TG", 150.0).clip(lower=10.0)
        fbs = _safe_series(df, "FBS", 100.0).clip(lower=20.0)

        estimated_total_chol = ldl + hdl + (tg / 5.0)
        df["LDL_HDL_Ratio"] = ldl / hdl
        df["Total_Cholesterol_Ratio"] = estimated_total_chol / hdl
        df["Castelli_Risk_Index_I"] = df["Total_Cholesterol_Ratio"]
        df["Castelli_Risk_Index_II"] = df["LDL_HDL_Ratio"]
        df["Atherogenic_Index_Plasma"] = np.log10(tg / hdl)
        df["TyG_Index"] = np.log(fbs * tg / 2.0)
        df["Non_HDL_Cholesterol"] = estimated_total_chol - hdl

        # 3. Inflammatory & Hematologic Biomarkers
        neut = _safe_series(df, "Neut", 60.0)
        lymph = _safe_series(df, "Lymph", 30.0).clip(lower=1.0)
        plt = _safe_series(df, "PLT", 220.0)

        df["NLR"] = neut / lymph
        df["PLR"] = plt / lymph
        df["SII"] = (plt * neut) / lymph

        # 4. Cardiorenal & Organ Interaction Markers
        cr = _safe_series(df, "CR", 1.0).clip(lower=0.2)
        bun = _safe_series(df, "BUN", 15.0)
        df["BUN_CR_Ratio"] = bun / cr

        age = _safe_series(df, "Age", 55.0)
        ef = _safe_series(df, "EF-TTE", 55.0).clip(lower=10.0)
        df["Age_EF_Ratio"] = age / ef

        # 5. Obesity categorization
        if "BMI" in df.columns and not df["BMI"].isna().all():
            bmi = pd.to_numeric(df["BMI"], errors="coerce")
        else:
            weight = _safe_series(df, "Weight", 70.0)
            length = _safe_series(df, "Length", 170.0) / 100.0
            bmi = weight / (length ** 2)
        bmi = bmi.fillna(25.0)

        df["BMI_Category_Overweight"] = ((bmi >= 25.0) & (bmi < 30.0)).astype(int)
        df["BMI_Category_Obese"] = (bmi >= 30.0).astype(int)

        # 6. Composite ECG Abnormality & Ischemia Scores
        ecg_components = []
        for col in ["St Elevation", "St Depression", "Tinversion", "Q Wave"]:
            if col in df.columns:
                ecg_components.append(pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int))

        if "LVH" in df.columns:
            ecg_components.append(df["LVH"].astype(str).str.upper().eq("Y").astype(int))
        if "Poor R Progression" in df.columns:
            ecg_components.append(df["Poor R Progression"].astype(str).str.upper().eq("Y").astype(int))

        df["ECG_Abnormality_Score"] = sum(ecg_components) if ecg_components else 0
        df["Ischemic_ECG"] = (sum(ecg_components[:4]) > 0).astype(int) if len(ecg_components) >= 4 else 0

        # 7. Echocardiographic RWMA territory flags
        rwma = _safe_series(df, "Region RWMA", 0.0).astype(int)
        df["Has_RWMA"] = (rwma > 0).astype(int)
        df["RWMA_LAD_Territory"] = ((rwma == 1) | (rwma == 4)).astype(int)
        df["RWMA_RCA_Territory"] = ((rwma == 2) | (rwma == 4)).astype(int)
        df["RWMA_LCX_Territory"] = ((rwma == 3) | (rwma == 4)).astype(int)

        # 8. Clinical Pretest Probability (Duke/Diamond-Forrester index proxy)
        sex_col = df["Sex"] if "Sex" in df.columns else pd.Series("Male", index=df.index)
        is_male = sex_col.astype(str).str.lower().str.startswith("m") | sex_col.astype(str).eq("1")
        male = is_male.astype(int)

        typical_cp = _safe_series(df, "Typical Chest Pain", 0.0).astype(int)
        atypical_cp = _safe_series(df, "Atypical", 0.0).astype(int)
        dm = _safe_series(df, "DM", 0.0).astype(int)
        htn = _safe_series(df, "HTN", 0.0).astype(int)
        smoker = _safe_series(df, "Current Smoker", 0.0).astype(int)
        ex_smoker = _safe_series(df, "EX-Smoker", 0.0).astype(int)
        fh = _safe_series(df, "FH", 0.0).astype(int)

        df["Pretest_PTP_Score"] = (
            (age >= 60).astype(int) * 2 + ((age >= 50) & (age < 60)).astype(int) * 1 +
            male * 2 + typical_cp * 3 + atypical_cp * 1 + dm + htn + smoker + fh
        )

        # 9. Composite Metabolic Risk & Lifestyle Scores
        is_female = sex_col.astype(str).str.lower().str.startswith("f") | sex_col.astype(str).eq("0")
        hdl_risk = np.where(is_female, (hdl < 50.0).astype(int), (hdl < 40.0).astype(int))
        tg_risk = (tg > 150.0).astype(int)
        fbs_risk = (fbs > 100.0).astype(int)
        df["Metabolic_Risk_Score"] = dm + htn + hdl_risk + tg_risk + fbs_risk
        df["Lifestyle_Risk_Index"] = (smoker * 1.0) + (ex_smoker * 0.5) + (fh * 1.0) + (htn * 1.0)

        # 10. Skewed clinical lab log-transforms
        for col in ["TG", "CR", "ESR", "WBC", "FBS", "BUN"]:
            if col in df.columns:
                df[f"Log_{col}"] = np.log1p(pd.to_numeric(df[col], errors="coerce").fillna(0).clip(lower=0))

        return df


def clean_and_encode_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans raw dataset, normalizes text variations, and standardizes binary and categorical fields.
    """
    df = df.copy()

    # Normalize column names (strip whitespace)
    df.columns = [col.strip() for col in df.columns]

    # Standardize binary text features ('Y'/'N' -> 1/0)
    for col in RAW_BINARY_TEXT_FEATURES:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.upper().map(
                lambda val: 1 if val == "Y" else (0 if val == "N" else 0)
            )

    # Standardize Sex ('Male' -> 1, 'Fmale'/'Female' -> 0)
    if "Sex" in df.columns:
        df["Sex"] = df["Sex"].astype(str).str.strip().str.lower().map(
            lambda val: 1 if val == "male" else 0
        )

    # Standardize BBB ('N' -> 0, 'LBBB' -> 1, 'RBBB' -> 2)
    if "BBB" in df.columns:
        df["BBB"] = df["BBB"].astype(str).str.strip().str.upper().map(
            lambda val: 1 if "LBBB" in val else (2 if "RBBB" in val else 0)
        )

    # Standardize VHD ('N' -> 0, 'mild' -> 1, 'Moderate' -> 2, 'Severe' -> 3)
    if "VHD" in df.columns:
        df["VHD"] = df["VHD"].astype(str).str.strip().str.lower().map(
            lambda val: 1 if "mild" in val else (2 if "moderate" in val else (3 if "severe" in val else 0))
        )

    # Clean numeric columns
    for col in RAW_NUMERIC_FEATURES + RAW_BINARY_NUMERIC_FEATURES:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            # Impute missing with median
            if df[col].isna().sum() > 0:
                df[col] = df[col].fillna(df[col].median())

    return df


def prepare_training_data(
    excel_path: str
) -> Tuple[pd.DataFrame, Dict[str, pd.Series], List[str]]:
    """
    Loads raw Excel dataset, extracts and encodes target labels, drops target leakage columns,
    applies feature engineering, and returns (X_features, y_targets_dict, feature_column_names).
    """
    raw_df = pd.read_excel(excel_path)
    cleaned_df = clean_and_encode_dataset(raw_df)

    # Extract target series
    targets: Dict[str, pd.Series] = {}

    # 1. Overall CAD (Cath)
    if "Cath" in cleaned_df.columns:
        targets["CAD"] = cleaned_df["Cath"].astype(str).str.strip().eq("CAD").astype(int)
    elif "CAD" in cleaned_df.columns:
        targets["CAD"] = cleaned_df["CAD"].astype(int)
    else:
        raise ValueError("Neither 'Cath' nor 'CAD' target column found in dataset")

    # 2. LAD Stenosis
    targets["LAD"] = cleaned_df["LAD"].astype(str).str.strip().str.lower().eq("stenotic").astype(int)

    # 3. LCX Stenosis
    targets["LCX"] = cleaned_df["LCX"].astype(str).str.strip().str.lower().eq("stenotic").astype(int)

    # 4. RCA Stenosis
    targets["RCA"] = cleaned_df["RCA"].astype(str).str.strip().str.lower().eq("stenotic").astype(int)

    # Drop all target leakage columns and zero-variance constant columns from feature matrix X
    drop_cols = [col for col in (LEAKAGE_COLUMNS + ZERO_VARIANCE_COLUMNS) if col in cleaned_df.columns]
    feature_df = cleaned_df.drop(columns=drop_cols)

    # Apply clinical feature engineering
    engineer = ClinicalFeatureEngineer()
    engineered_df = engineer.transform(feature_df)

    feature_names = list(engineered_df.columns)

    return engineered_df, targets, feature_names

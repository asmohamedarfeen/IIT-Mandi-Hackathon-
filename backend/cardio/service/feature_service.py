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
    TARGET_NAMES
)


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
        sbp = pd.to_numeric(df.get("BP", 120), errors="coerce").fillna(120.0)
        # Clinical estimation of diastolic BP based on systolic BP where DBP is not isolated
        estimated_dbp = sbp * 0.65
        df["Pulse_Pressure"] = sbp - estimated_dbp
        df["Mean_Arterial_Pressure"] = (sbp + 2.0 * estimated_dbp) / 3.0

        # 2. Lipid / Cholesterol ratios (Friedewald lipid assessment)
        ldl = pd.to_numeric(df.get("LDL", 100), errors="coerce").fillna(100.0)
        hdl = pd.to_numeric(df.get("HDL", 40), errors="coerce").fillna(40.0).clip(lower=10.0)
        tg = pd.to_numeric(df.get("TG", 150), errors="coerce").fillna(150.0)

        df["LDL_HDL_Ratio"] = ldl / hdl
        estimated_total_chol = ldl + hdl + (tg / 5.0)
        df["Total_Cholesterol_Ratio"] = estimated_total_chol / hdl

        # 3. Obesity categorization
        if "BMI" in df.columns:
            bmi = pd.to_numeric(df["BMI"], errors="coerce")
        else:
            weight = pd.to_numeric(df.get("Weight", 70), errors="coerce").fillna(70.0)
            length = pd.to_numeric(df.get("Length", 170), errors="coerce").fillna(170.0) / 100.0
            bmi = weight / (length ** 2)
        bmi = bmi.fillna(25.0)

        df["BMI_Category_Overweight"] = ((bmi >= 25.0) & (bmi < 30.0)).astype(int)
        df["BMI_Category_Obese"] = (bmi >= 30.0).astype(int)

        # 4. Composite ECG Abnormality Score
        ecg_components = []
        for col in ["St Elevation", "St Depression", "Tinversion", "Q Wave"]:
            if col in df.columns:
                ecg_components.append(pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int))

        if "LVH" in df.columns:
            ecg_components.append(df["LVH"].astype(str).str.upper().eq("Y").astype(int))
        if "Poor R Progression" in df.columns:
            ecg_components.append(df["Poor R Progression"].astype(str).str.upper().eq("Y").astype(int))

        df["ECG_Abnormality_Score"] = sum(ecg_components) if ecg_components else 0

        # 5. Composite Metabolic Risk Score
        dm = pd.to_numeric(df.get("DM", 0), errors="coerce").fillna(0).astype(int)
        htn = pd.to_numeric(df.get("HTN", 0), errors="coerce").fillna(0).astype(int)
        fbs = pd.to_numeric(df.get("FBS", 100), errors="coerce").fillna(100.0)
        sex = df.get("Sex", "Male").astype(str)

        hdl_risk = np.where(sex.str.lower().str.startswith("f"), (hdl < 50).astype(int), (hdl < 40).astype(int))
        tg_risk = (tg > 150.0).astype(int)
        fbs_risk = (fbs > 100.0).astype(int)

        df["Metabolic_Risk_Score"] = dm + htn + hdl_risk + tg_risk + fbs_risk

        # 6. Lifestyle Risk Index
        smoker = pd.to_numeric(df.get("Current Smoker", 0), errors="coerce").fillna(0).astype(int)
        ex_smoker = pd.to_numeric(df.get("EX-Smoker", 0), errors="coerce").fillna(0).astype(int)
        fh = pd.to_numeric(df.get("FH", 0), errors="coerce").fillna(0).astype(int)

        df["Lifestyle_Risk_Index"] = (smoker * 1.0) + (ex_smoker * 0.5) + (fh * 1.0) + (htn * 1.0)

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

    # Drop all target leakage columns from feature matrix X
    drop_cols = [col for col in LEAKAGE_COLUMNS if col in cleaned_df.columns]
    feature_df = cleaned_df.drop(columns=drop_cols)

    # Apply clinical feature engineering
    engineer = ClinicalFeatureEngineer()
    engineered_df = engineer.transform(feature_df)

    feature_names = list(engineered_df.columns)

    return engineered_df, targets, feature_names

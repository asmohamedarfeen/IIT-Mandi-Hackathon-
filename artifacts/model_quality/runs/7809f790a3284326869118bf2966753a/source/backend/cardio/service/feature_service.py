"""
Feature processing and clinical feature engineering pipeline for CardioVision AI.
"""

from typing import Tuple, List, Dict, Any
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.utils.validation import check_is_fitted

from backend.cardio.constants import (
    RAW_NUMERIC_FEATURES,
    RAW_BINARY_NUMERIC_FEATURES,
    RAW_BINARY_TEXT_FEATURES,
    RAW_MULTICLASS_FEATURES,
    LEAKAGE_COLUMNS,
    TARGET_NAMES,
    ZERO_VARIANCE_COLUMNS,
    CATEGORY_CODES,
    encode_category,
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

        # Saved weights were trained after encoding: these text comparisons omitted
        # encoded LVH/Poor R Progression. Preserve that composite until retraining.
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
        # The saved bundle background/sample vectors exclude HDL from this score.
        # Keep the fitted definition; adding HDL requires retraining and validation.
        tg_risk = (tg > 150.0).astype(int)
        fbs_risk = (fbs > 100.0).astype(int)
        df["Metabolic_Risk_Score"] = dm + htn + tg_risk + fbs_risk
        df["Lifestyle_Risk_Index"] = (smoker * 1.0) + (ex_smoker * 0.5) + (fh * 1.0) + (htn * 1.0)

        # 10. Skewed clinical lab log-transforms
        for col in ["TG", "CR", "ESR", "WBC", "FBS", "BUN"]:
            if col in df.columns:
                df[f"Log_{col}"] = np.log1p(pd.to_numeric(df[col], errors="coerce").fillna(0).clip(lower=0))

        return df


def normalize_dataset(df: pd.DataFrame, impute: bool = False) -> pd.DataFrame:
    """
    Cleans raw dataset, normalizes text variations, and standardizes binary and categorical fields.
    """
    df = df.copy()

    # Normalize column names (strip whitespace)
    df.columns = [col.strip() for col in df.columns]

    for col in CATEGORY_CODES:
        if col in df.columns:
            df[col] = df[col].map(lambda value: np.nan if pd.isna(value) else encode_category(value, col))

    # Fill missing BMI per row before numeric imputation, retaining it as a feature.
    if "Weight" in df.columns and "Length" in df.columns:
        computed_bmi = pd.to_numeric(df["Weight"], errors="coerce") / (
            pd.to_numeric(df["Length"], errors="coerce") / 100.0
        ) ** 2
        if "BMI" in df.columns:
            df["BMI"] = pd.to_numeric(df["BMI"], errors="coerce").fillna(computed_bmi)
        else:
            df["BMI"] = computed_bmi

    # Clean numeric columns
    for col in RAW_NUMERIC_FEATURES + RAW_BINARY_NUMERIC_FEATURES:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            # Impute missing with median
            if impute and df[col].isna().sum() > 0:
                df[col] = df[col].fillna(df[col].median())

    return df


def clean_and_encode_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Compatibility wrapper retaining legacy full-frame numeric imputation."""
    return normalize_dataset(df, impute=True)


def extract_targets(df: pd.DataFrame) -> Dict[str, pd.Series]:
    """Encode declared outcomes, rejecting absent, missing, or unknown labels."""
    df = df.rename(columns=lambda name: name.strip())
    targets = {}
    for target in TARGET_NAMES:
        column = "Cath" if target == "CAD" and "Cath" in df else target
        if column not in df:
            raise ValueError(f"Missing target column: {column}")
        values = df[column]
        if column == "CAD":
            encoded = pd.to_numeric(values, errors="coerce")
            valid = encoded.isin([0, 1]) & values.notna()
        else:
            labels = values.astype("string").str.strip().str.lower()
            positive = "cad" if target == "CAD" else "stenotic"
            valid = labels.isin(["normal", positive]) & values.notna()
            encoded = labels.eq(positive)
        if not valid.all():
            raise ValueError(f"Invalid or missing target labels in {column}")
        targets[target] = encoded.astype(int)
    return targets


def _engineer_and_align(df: pd.DataFrame, feature_names=None) -> pd.DataFrame:
    excluded = LEAKAGE_COLUMNS + ZERO_VARIANCE_COLUMNS + ["patient_id"]
    engineered = ClinicalFeatureEngineer().transform(df.drop(columns=excluded, errors="ignore"))
    if feature_names is not None:
        if set(feature_names) & set(LEAKAGE_COLUMNS):
            raise ValueError("Feature contract cannot contain target outcomes")
        missing = set(feature_names) - set(engineered.columns)
        if missing:
            raise ValueError(f"Missing required features: {sorted(missing)}")
        engineered = engineered.loc[:, list(feature_names)]
    try:
        engineered = engineered.astype(np.float32)
    except (ValueError, TypeError) as exc:
        raise ValueError("Model features must be numeric") from exc
    if not np.isfinite(engineered.to_numpy()).all():
        raise ValueError("Model features must contain only finite values")
    return engineered


def prepare_features(df: pd.DataFrame, feature_names=None) -> pd.DataFrame:
    """Apply the shared inference definition, optionally selecting a saved contract."""
    return _engineer_and_align(clean_and_encode_dataset(df), feature_names)


class ClinicalPreprocessor(BaseEstimator, TransformerMixin):
    """Fit imputation on training rows before deterministic clinical engineering."""

    def __init__(self, feature_names=None):
        self.feature_names = feature_names

    def fit(self, X: pd.DataFrame, y=None):
        normalized = normalize_dataset(X, impute=False).drop(
            columns=LEAKAGE_COLUMNS + ZERO_VARIANCE_COLUMNS + ["patient_id"], errors="ignore"
        )
        self.medians_ = {}
        for column in normalized:
            values = pd.to_numeric(normalized[column], errors="raise")
            if not np.isfinite(values.dropna().to_numpy()).all():
                raise ValueError(f"Training feature {column} must contain finite values")
            if values.isna().all():
                raise ValueError(f"Training feature {column} has no observed values")
            # Modes preserve valid integer category codes; medians cover measurements.
            self.medians_[column] = float(values.mode().iloc[0] if column in CATEGORY_CODES else values.median())
        self.input_columns_ = list(normalized.columns)
        fitted = _engineer_and_align(normalized.fillna(self.medians_), self.feature_names)
        self.feature_names_out_ = np.asarray(fitted.columns, dtype=object)
        self.n_features_in_ = X.shape[1]
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        check_is_fitted(self, "feature_names_out_")
        normalized = normalize_dataset(X, impute=False)
        missing = set(self.input_columns_) - set(normalized.columns)
        if missing:
            raise ValueError(f"Missing required input columns: {sorted(missing)}")
        normalized = normalized.loc[:, self.input_columns_].fillna(self.medians_)
        return _engineer_and_align(normalized, self.feature_names_out_)

    def get_feature_names_out(self, input_features=None):
        check_is_fitted(self, "feature_names_out_")
        return self.feature_names_out_.copy()


def prepare_training_data(
    excel_path: str
) -> Tuple[pd.DataFrame, Dict[str, pd.Series], List[str]]:
    """
    Loads raw Excel dataset, extracts and encodes target labels, drops target leakage columns,
    applies feature engineering, and returns (X_features, y_targets_dict, feature_column_names).
    """
    raw_df = pd.read_excel(excel_path)
    targets = extract_targets(raw_df)
    engineered_df = prepare_features(raw_df)
    feature_names = list(engineered_df.columns)

    return engineered_df, targets, feature_names

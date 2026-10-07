"""Clinical data processing, cleaning, encoding, and target leakage prevention pipeline."""

import logging
import os

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler

logger = logging.getLogger(__name__)

TARGET_COLUMNS: list[str] = ["Cath", "LAD", "LCX", "RCA"]


def load_and_clean_dataset(filepath: str) -> pd.DataFrame:
    """Loads and sanitizes the Z-Alizadeh Sani extension dataset.

    Performs column whitespace trimming, typo correction in categorical
    fields (e.g. 'Fmale' -> 'Female' in Sex), string value trimming, and
    removal of zero-variance non-target feature columns.

    Args:
        filepath: Path to the Excel dataset file.

    Returns:
        pd.DataFrame: Sanitized clinical dataset.

    Raises:
        FileNotFoundError: If the specified file does not exist.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Dataset file not found at: {filepath}")

    logger.info("Loading dataset from: %s", filepath)
    df = pd.read_excel(filepath, sheet_name=0)

    # 1. Clean column strings
    df.columns = [str(c).strip() for c in df.columns]

    # 2. Fix typos in categorical values
    if "Sex" in df.columns:
        df["Sex"] = df["Sex"].replace({"Fmale": "Female"})

    # 3. Strip whitespace in string columns
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].astype(str).str.strip()

    # 4. Drop zero-variance columns (e.g. Exertional CP where all values are 'N')
    zero_var_cols = [
        c for c in df.columns if df[c].nunique() <= 1 and c not in TARGET_COLUMNS
    ]
    if zero_var_cols:
        logger.info("Dropping zero-variance feature columns: %s", zero_var_cols)
        df = df.drop(columns=zero_var_cols)

    logger.info("Dataset loaded successfully with shape: %s", df.shape)
    return df


def prepare_features_and_targets(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, pd.Series], list[str], list[str]]:
    """Extracts leakage-free feature matrix X and encoded binary target series.

    Strictly removes all target columns ('Cath', 'LAD', 'LCX', 'RCA') from the
    feature matrix X to prevent target leakage into machine learning models.
    Encodes targets into binary values:
        Cath: Normal -> 0, CAD -> 1
        LAD/LCX/RCA: Normal -> 0, Stenotic -> 1

    Args:
        df: Cleaned clinical DataFrame.

    Returns:
        Tuple containing:
            - X (pd.DataFrame): Feature matrix free of all target columns.
            - targets (Dict[str, pd.Series]): Dictionary mapping target name to binary 0/1 Series.
            - numeric_cols (List[str]): List of column names with numeric types.
            - categorical_cols (List[str]): List of column names with categorical/object types.
    """
    df_clean = df.copy()

    # Encode targets: Normal -> 0, CAD/Stenotic -> 1
    target_mapping = {
        "Cath": {"Normal": 0, "CAD": 1},
        "LAD": {"Normal": 0, "Stenotic": 1},
        "LCX": {"Normal": 0, "Stenotic": 1},
        "RCA": {"Normal": 0, "Stenotic": 1},
    }

    targets: dict[str, pd.Series] = {}
    for col, mapping in target_mapping.items():
        if col in df_clean.columns:
            targets[col] = df_clean[col].map(mapping).astype(int)

    # STRICT LEAKAGE PREVENTION: Drop all target columns from X
    targets_to_drop = [c for c in TARGET_COLUMNS if c in df_clean.columns]
    X = df_clean.drop(columns=targets_to_drop)

    # Identify numeric and categorical columns
    numeric_cols = X.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = X.select_dtypes(include=["object"]).columns.tolist()

    logger.info(
        "Prepared feature matrix X shape: %s with %d numeric and %d categorical features.",
        X.shape,
        len(numeric_cols),
        len(categorical_cols),
    )
    return X, targets, numeric_cols, categorical_cols


def build_preprocessor(
    numeric_features: list[str], categorical_features: list[str]
) -> ColumnTransformer:
    """Builds a scikit-learn ColumnTransformer for standard scaling and one-hot encoding.

    Applies StandardScaler to numeric features and OneHotEncoder (with drop='first'
    and handle_unknown='ignore') to categorical features.

    Args:
        numeric_features: List of column names for numeric features.
        categorical_features: List of column names for categorical features.

    Returns:
        ColumnTransformer: Configured preprocessor pipeline.
    """
    return ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), numeric_features),
            (
                "cat",
                OneHotEncoder(
                    drop="first", handle_unknown="ignore", sparse_output=False
                ),
                categorical_features,
            ),
        ],
        remainder="passthrough",
    )

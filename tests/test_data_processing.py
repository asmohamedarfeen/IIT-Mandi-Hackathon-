"""Unit tests for clinical data processing and leakage prevention pipeline."""

import os

import numpy as np
import pytest

from src.data_processing import (
    TARGET_COLUMNS,
    build_preprocessor,
    load_and_clean_dataset,
    prepare_features_and_targets,
)

DATA_PATH = "extention of Z-Alizadeh sani dataset.xlsx"


def test_load_and_clean_dataset() -> None:
    """Verifies that dataset loads, cleans typos, and drops zero-variance columns."""
    assert os.path.exists(DATA_PATH)
    df = load_and_clean_dataset(DATA_PATH)
    assert len(df) == 303
    # Check typo harmonization
    assert "Fmale" not in df["Sex"].unique()
    assert "Female" in df["Sex"].unique()
    # Check zero-variance column removed
    assert "Exertional CP" not in df.columns


def test_load_and_clean_dataset_nonexistent_file() -> None:
    """Verifies that attempting to load a non-existent file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_and_clean_dataset("non_existent_file.xlsx")


def test_prepare_features_and_targets_leakage_prevention() -> None:
    """Verifies strict target leakage prevention and valid target encoding."""
    df = load_and_clean_dataset(DATA_PATH)
    X, targets, num_cols, cat_cols = prepare_features_and_targets(df)

    # Verify strict target leakage prevention: target columns must not appear in X
    for target in TARGET_COLUMNS:
        assert target not in X.columns
        assert target in targets
        assert len(targets[target]) == 303
        # Binary encoded 0 or 1
        assert set(targets[target].unique()).issubset({0, 1})

    # Verify features are split properly
    assert len(num_cols) > 0
    assert len(cat_cols) > 0
    assert len(num_cols) + len(cat_cols) == len(X.columns)


def test_build_preprocessor() -> None:
    """Verifies scikit-learn ColumnTransformer creation and transformation pipeline."""
    df = load_and_clean_dataset(DATA_PATH)
    X, _, num_cols, cat_cols = prepare_features_and_targets(df)

    preprocessor = build_preprocessor(num_cols, cat_cols)
    transformed = preprocessor.fit_transform(X)

    assert isinstance(transformed, np.ndarray)
    assert transformed.shape[0] == len(X)
    assert not np.isnan(transformed).any()

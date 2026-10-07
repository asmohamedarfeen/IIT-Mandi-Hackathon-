"""
Unit tests for CardioVision clinical feature engineering and leakage prevention.
"""

import pytest
import pandas as pd
import numpy as np

from backend.cardio.constants import LEAKAGE_COLUMNS
from backend.cardio.service.feature_service import (
    ClinicalFeatureEngineer,
    clean_and_encode_dataset,
    prepare_training_data,
)


def test_leakage_columns_definition():
    """Verify strictly defined target leakage columns."""
    assert "Cath" in LEAKAGE_COLUMNS
    assert "CAD" in LEAKAGE_COLUMNS
    assert "LAD" in LEAKAGE_COLUMNS
    assert "LCX" in LEAKAGE_COLUMNS
    assert "RCA" in LEAKAGE_COLUMNS


def test_clinical_feature_engineer_calculations():
    """Verify mathematical and physiological correctness of engineered features."""
    raw_sample = pd.DataFrame([{
        "BP": 140,
        "LDL": 160,
        "HDL": 40,
        "TG": 200,
        "Weight": 90,
        "Length": 175,
        "BMI": 29.4,
        "DM": 1,
        "HTN": 1,
        "FBS": 120,
        "Sex": "Male",
        "Current Smoker": 1,
        "EX-Smoker": 0,
        "FH": 1,
        "St Elevation": 1,
        "St Depression": 0,
        "Tinversion": 1,
        "Q Wave": 0,
        "LVH": "Y",
        "Poor R Progression": "N"
    }])

    engineer = ClinicalFeatureEngineer()
    transformed = engineer.transform(raw_sample)

    # 1. Pulse Pressure & MAP
    assert transformed["Pulse_Pressure"].iloc[0] > 0
    assert transformed["Mean_Arterial_Pressure"].iloc[0] > 0

    # 2. Lipid ratios
    assert np.isclose(transformed["LDL_HDL_Ratio"].iloc[0], 160.0 / 40.0)
    # Total cholesterol = 160 + 40 + 200/5 = 240; ratio = 240 / 40 = 6.0
    assert np.isclose(transformed["Total_Cholesterol_Ratio"].iloc[0], 6.0)

    # 3. Obesity categorization
    assert transformed["BMI_Category_Overweight"].iloc[0] == 1
    assert transformed["BMI_Category_Obese"].iloc[0] == 0

    # 4. ECG Abnormality score: ST Elevation(1) + Tinversion(1) + LVH(1) = 3
    assert transformed["ECG_Abnormality_Score"].iloc[0] == 3

    # 5. Metabolic Risk Score: DM(1) + HTN(1) + HDL<40(0, since HDL=40) + TG>150(1) + FBS>100(1) = 4
    assert transformed["Metabolic_Risk_Score"].iloc[0] == 4

    # 6. Lifestyle Risk: Smoker(1) + FH(1) + HTN(1) = 3.0
    assert transformed["Lifestyle_Risk_Index"].iloc[0] == 3.0


def test_prepare_training_data_leakage_exclusion():
    """Verify that feature matrix X excludes all target leakage columns."""
    dataset_path = "extention of Z-Alizadeh sani dataset.xlsx"
    X_df, targets, feature_names = prepare_training_data(dataset_path)

    # Ensure no leakage columns are present in features
    for leak_col in LEAKAGE_COLUMNS:
        assert leak_col not in X_df.columns
        assert leak_col not in feature_names

    # Ensure all 4 targets are cleanly extracted
    assert set(targets.keys()) == {"CAD", "LAD", "LCX", "RCA"}
    for t_name, series in targets.items():
        assert len(series) == len(X_df)
        assert set(series.unique()).issubset({0, 1})

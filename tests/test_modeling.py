"""Unit tests for multi-target predictive modeling, cross-validation, and 3D payload generation."""

import json

from src.data_processing import load_and_clean_dataset, prepare_features_and_targets
from src.modeling import (
    assign_risk_color,
    evaluate_multitarget_models,
    generate_3d_payload,
    get_candidate_models,
    train_final_models,
)

DATA_PATH = "extention of Z-Alizadeh sani dataset.xlsx"


def test_risk_color_assignment():
    """Tests risk tier and hex color categorization based on probability thresholds."""
    # Low risk (< 0.35)
    low_res = assign_risk_color(0.20)
    assert low_res["risk_level"] == "Low"
    assert low_res["color_hex"] == "#10B981"
    assert low_res["recommendation"] == "Normal / Routine monitoring"

    low_boundary = assign_risk_color(0.349)
    assert low_boundary["risk_level"] == "Low"

    # Moderate risk (0.35 <= p < 0.65)
    mod_res = assign_risk_color(0.50)
    assert mod_res["risk_level"] == "Moderate"
    assert mod_res["color_hex"] == "#F59E0B"
    assert mod_res["recommendation"] == "Borderline / Non-invasive follow-up"

    mod_boundary = assign_risk_color(0.35)
    assert mod_boundary["risk_level"] == "Moderate"

    # High risk (>= 0.65)
    high_res = assign_risk_color(0.85)
    assert high_res["risk_level"] == "High"
    assert high_res["color_hex"] == "#EF4444"
    assert (
        high_res["recommendation"]
        == "Significant stenosis (>=50%) / Urgent clinical review"
    )

    high_boundary = assign_risk_color(0.65)
    assert high_boundary["risk_level"] == "High"


def test_get_candidate_models():
    """Tests candidate classification model dictionary instantiation."""
    models = get_candidate_models()
    assert set(models.keys()) == {"RandomForest", "XGBoost", "LogisticRegression"}
    for clf in models.values():
        assert hasattr(clf, "fit")
        assert hasattr(clf, "predict_proba")


def test_evaluate_multitarget_models():
    """Tests 5-fold cross-validation multi-target model evaluation."""
    df = load_and_clean_dataset(DATA_PATH)
    X, targets, num_cols, cat_cols = prepare_features_and_targets(df)

    # Evaluate on a subset of targets (Cath and LAD) to verify evaluation pipeline and metrics
    eval_targets = {"Cath": targets["Cath"], "LAD": targets["LAD"]}
    results_df = evaluate_multitarget_models(X, eval_targets, num_cols, cat_cols)

    expected_columns = {
        "Target",
        "Model",
        "Accuracy",
        "Precision",
        "Recall",
        "F1_Score",
        "ROC_AUC",
    }
    assert expected_columns.issubset(set(results_df.columns))

    # 2 targets * 3 models = 6 rows
    assert len(results_df) == 6
    assert set(results_df["Target"].unique()) == {"Cath", "LAD"}
    assert set(results_df["Model"].unique()) == {
        "RandomForest",
        "XGBoost",
        "LogisticRegression",
    }

    for _, row in results_df.iterrows():
        assert 0.0 <= row["Accuracy"] <= 1.0
        assert 0.0 <= row["Precision"] <= 1.0
        assert 0.0 <= row["Recall"] <= 1.0
        assert 0.0 <= row["F1_Score"] <= 1.0
        assert 0.0 <= row["ROC_AUC"] <= 1.0


def test_model_training_and_payload_generation():
    """Tests final pipeline training across all targets and 3D visualization payload generation."""
    df = load_and_clean_dataset(DATA_PATH)
    X, targets, num_cols, cat_cols = prepare_features_and_targets(df)

    # Train production models
    models = train_final_models(X, targets, num_cols, cat_cols)
    assert set(models.keys()) == {"Cath", "LAD", "LCX", "RCA"}

    # Generate 3D payload for sample patient
    sample_patient = X.iloc[0].to_dict()
    payload = generate_3d_payload(
        sample_patient, models, X.columns.tolist(), patient_id="PT-TEST-001"
    )

    assert payload["patient_id"] == "PT-TEST-001"
    assert "overall_cad" in payload
    assert "vessel_predictions" in payload
    assert "key_physiological_measurements" in payload
    assert "clinical_safety_disclaimer" in payload

    # Verify overall CAD structure
    overall = payload["overall_cad"]
    assert 0.0 <= overall["probability"] <= 1.0
    assert isinstance(overall["cad_predicted"], bool)
    assert overall["risk_level"] in ["Low", "Moderate", "High"]
    assert overall["color_hex"] in ["#10B981", "#F59E0B", "#EF4444"]

    # Verify vessel predictions
    assert set(payload["vessel_predictions"].keys()) == {"LAD", "LCX", "RCA"}
    for data in payload["vessel_predictions"].values():
        assert 0.0 <= data["probability"] <= 1.0
        assert isinstance(data["stenosis_predicted"], bool)
        assert data["risk_level"] in ["Low", "Moderate", "High"]
        assert data["color_hex"] in ["#10B981", "#F59E0B", "#EF4444"]
        assert isinstance(data["recommendation"], str)

    # Verify disclaimer text
    assert (
        "FOR DECISION SUPPORT & RESEARCH PURPOSES ONLY"
        in payload["clinical_safety_disclaimer"]
    )

    # Verify JSON serializability
    json_str = json.dumps(payload)
    assert isinstance(json_str, str)

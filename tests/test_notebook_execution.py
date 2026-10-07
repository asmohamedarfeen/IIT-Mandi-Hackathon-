"""Integration test for end-to-end execution of the master cardiovascular risk analysis notebook."""

import os
import joblib
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor

from src.data_processing import TARGET_COLUMNS, load_and_clean_dataset


def test_notebook_executes_successfully():
    """Executes cardiovascular_risk_analysis.ipynb end-to-end and validates generated artifacts."""
    notebook_path = "cardiovascular_risk_analysis.ipynb"
    assert os.path.exists(notebook_path), "Notebook file must exist"

    with open(notebook_path, "r", encoding="utf-8") as f:
        nb = nbformat.read(f, as_version=4)

    ep = ExecutePreprocessor(timeout=600, kernel_name="python3")
    ep.preprocess(nb, {"metadata": {"path": "./"}})

    # Save the executed notebook back to disk
    with open(notebook_path, "w", encoding="utf-8") as f:
        nbformat.write(nb, f)

    # 1. Verify downstream artifact files were generated
    payload_path = "artifacts/sample_patient_3d_payload.json"
    scored_csv_path = "artifacts/scored_patient_cohort.csv"
    weights_path = "artifacts/model_pipeline_weights.joblib"

    assert os.path.exists(payload_path), "3D payload JSON must exist"
    assert os.path.exists(scored_csv_path), "Scored cohort CSV must exist"
    assert os.path.exists(weights_path), "Model weights joblib must exist"

    # 2. Verify schema and inference on saved model weights
    models = joblib.load(weights_path)
    assert set(models.keys()) == set(TARGET_COLUMNS), "All 4 target models must be serialized"

    clean_df = load_and_clean_dataset("extention of Z-Alizadeh sani dataset.xlsx").drop(
        columns=TARGET_COLUMNS
    )
    assert clean_df.shape[1] == 54, f"Clean feature space must have exactly 54 columns, found {clean_df.shape[1]}"
    assert "Vessel_Tier" not in clean_df.columns, "Target composite 'Vessel_Tier' must not be in clean feature space"

    sample_patient = clean_df.iloc[[0]]

    for target_name, pipeline in models.items():
        # Verify no target-derived column like Vessel_Tier is expected
        if hasattr(pipeline, "feature_names_in_"):
            assert (
                "Vessel_Tier" not in pipeline.feature_names_in_
            ), f"Target composite 'Vessel_Tier' found in {target_name} feature_names_in_"
        # Test predict_proba execution on raw clean patient record
        prob = pipeline.predict_proba(sample_patient)
        assert prob.shape == (1, 2), f"Prediction output must be shape (1, 2) for {target_name}"
        assert 0.0 <= prob[0, 1] <= 1.0, f"Predicted probability out of range for {target_name}"

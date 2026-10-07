"""Integration test for end-to-end execution of the master cardiovascular risk analysis notebook."""

import os
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor


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

    # Verify downstream artifacts were generated
    assert os.path.exists("artifacts/sample_patient_3d_payload.json"), "3D payload JSON must exist"
    assert os.path.exists("artifacts/scored_patient_cohort.csv"), "Scored cohort CSV must exist"
    assert os.path.exists("artifacts/model_pipeline_weights.joblib"), "Model weights joblib must exist"

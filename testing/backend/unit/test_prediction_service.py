"""
Unit tests for CardioVision PredictionService inference, calibration, and SHAP.
"""

import pytest
import numpy as np

from backend.cardio.service.prediction_service import prediction_service_instance
from backend.cardio.schemas.patient_schema import PatientInputSchema
from backend.cardio.constants import COLOR_LOW_RISK, COLOR_MODERATE_RISK, COLOR_HIGH_RISK


def test_prediction_service_initialization():
    """Verify singleton instance has loaded model bundle and feature names."""
    service = prediction_service_instance
    assert service.bundle is not None
    assert "CAD" in service.bundle["calibrated_models"]
    assert "LAD" in service.bundle["calibrated_models"]
    assert "LCX" in service.bundle["calibrated_models"]
    assert "RCA" in service.bundle["calibrated_models"]
    assert len(service.bundle["feature_names"]) > 50


def test_prediction_output_structure_and_calibration():
    """Verify calibrated probability percentage and risk classification."""
    service = prediction_service_instance
    patient = PatientInputSchema(
        Age=65,
        Sex="Male",
        Weight=80,
        Length=172,
        BP=150,
        DM=1,
        HTN=1,
        Typical_Chest_Pain=1,
        St_Elevation=1
    )

    pred = service.predict(patient)

    # CAD Target
    assert 0.0 <= pred.overall_cad.probability <= 1.0
    assert 0.0 <= pred.overall_cad.probability_percent <= 100.0
    assert pred.overall_cad.color_hex in [COLOR_LOW_RISK, COLOR_MODERATE_RISK, COLOR_HIGH_RISK]

    # Vessel Targets
    for vessel_name in ["LAD", "LCX", "RCA"]:
        assert vessel_name in pred.vessels
        v_info = pred.vessels[vessel_name]
        assert 0.0 <= v_info.probability <= 1.0
        assert v_info.risk_level in ["Low Risk", "Intermediate Risk", "High Stenosis Risk"]

    # 3D Colors mapping
    assert "lad" in pred.vessel_colors_3d
    assert "lcx" in pred.vessel_colors_3d
    assert "rca" in pred.vessel_colors_3d

    # SHAP Explanations
    assert "CAD" in pred.shap_explanations
    assert len(pred.shap_explanations["CAD"]) > 0
    top_shap = pred.shap_explanations["CAD"][0]
    assert hasattr(top_shap, "display_name")
    assert hasattr(top_shap, "contribution")
    assert top_shap.impact_direction in ["increases_risk", "decreases_risk"]

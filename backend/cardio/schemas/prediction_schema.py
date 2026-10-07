"""
Pydantic schemas for multi-target risk predictions, calibrated probabilities, and SHAP explanations.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class VesselRiskInfo(BaseModel):
    vessel: str = Field(..., description="Vessel or target code: CAD, LAD, LCX, RCA")
    probability: float = Field(..., description="Calibrated risk probability (0.0 - 1.0)")
    probability_percent: float = Field(..., description="Percentage risk (0.0% - 100.0%)")
    risk_level: str = Field(..., description="'Low Risk', 'Intermediate Risk', or 'High Stenosis Risk'")
    color_hex: str = Field(..., description="Hex color for 3D visualization: Green, Amber, or Red")
    anatomical_description: str = Field(..., description="Clinical description of vascular territory")


class SHAPFeatureImpact(BaseModel):
    feature: str = Field(..., description="Feature column name")
    display_name: str = Field(..., description="User-friendly clinical label")
    contribution: float = Field(..., description="SHAP value impact on log-odds / risk probability")
    patient_value: Any = Field(..., description="The patient's recorded value")
    impact_direction: str = Field(..., description="'increases_risk' or 'decreases_risk'")


class PredictionResponse(BaseModel):
    patient_id: str
    overall_cad: VesselRiskInfo
    vessels: Dict[str, VesselRiskInfo] = Field(..., description="Target artery risks: LAD, LCX, RCA")
    vessel_colors_3d: Dict[str, str] = Field(..., description="Direct 3D mesh hex map: {lad, lcx, rca, myocardium}")
    shap_explanations: Dict[str, List[SHAPFeatureImpact]] = Field(
        ..., description="Top contributing clinical features for CAD and each coronary vessel"
    )
    disclaimer: str = Field(..., description="Clinical safety statement")


class ModelMetrics(BaseModel):
    accuracy: float
    precision: float
    recall: float
    f1: float
    roc_auc: float
    specificity: float
    mcc: float


class TargetBenchmarkResponse(BaseModel):
    targets: Dict[str, Dict[str, ModelMetrics]]
    global_importances: Dict[str, List[Dict[str, Any]]]


class ThreeDAnatomyResponse(BaseModel):
    metadata: Dict[str, Any]
    structures: Dict[str, Dict[str, Any]]

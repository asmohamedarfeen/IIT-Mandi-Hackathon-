"""
Pydantic schemas for multi-target risk predictions, calibrated probabilities, and SHAP explanations.
"""

from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field


class VesselRiskInfo(BaseModel):
    vessel: str = Field(..., description="Vessel or target code: CAD, LAD, LCX, RCA")
    probability: float = Field(..., description="Sigmoid-calibrated model score (0.0 - 1.0); clinical calibration is unverified")
    probability_percent: float = Field(..., description="Percentage risk (0.0% - 100.0%)")
    risk_level: str = Field(..., description="'Low Risk', 'Intermediate Risk', or 'High Stenosis Risk'")
    color_hex: str = Field(..., description="Hex color for 3D visualization: Green, Amber, or Red")
    anatomical_description: str = Field(..., description="Clinical description of vascular territory")
    predicted_status: Optional[Literal['CAD', 'Stenotic', 'Normal']] = Field(None, description="Binary model classification, separate from probability display bands")
    decision_threshold: float = Field(.5, ge=0, le=1, description="Research classification threshold selected on training-only folds")


class SourceMeasurement(BaseModel):
    input_key: str
    recorded_value: Any


class FeatureLineage(BaseModel):
    feature_kind: Literal["recorded", "derived", "unmapped"]
    model_input_value: float
    source_measurements: List[SourceMeasurement]
    derivation: Optional[str] = None


class SHAPFeatureImpact(FeatureLineage):
    feature: str = Field(..., description="Feature column name")
    display_name: str = Field(..., description="User-friendly clinical label")
    contribution: float = Field(..., description="Independent XGBoost SHAP contribution in log-odds; not an ensemble probability contribution")
    patient_value: Any = Field(..., description="Rounded aligned feature value; calculated features are not raw measurements")
    impact_direction: str = Field(..., description="'increases_risk' or 'decreases_risk'")


class PredictionEvidence(BaseModel):
    assessment_id: str
    generated_at: str = Field(..., description="UTC timestamp for this inference")
    clinical_inputs: Dict[str, Any] = Field(..., description="Validated raw input snapshot used for this inference")
    prediction_model: str
    explanation_model: str
    confidence_interval: Optional[List[float]] = Field(None, description="Unavailable for the supplied model bundle")
    limitations: List[str]
    application_version: str = "Unavailable"
    model_artifact_sha256: Optional[str] = None
    validation_summary: Dict[str, Any] = Field(default_factory=dict)
    report_available: bool = False
    input_provenance: Dict[str, Any] = Field(default_factory=dict)


class DomainContribution(BaseModel):
    id: str
    label: str
    contribution: float = Field(..., description='Additive probability contribution; multiply by 100 for percentage points')
    source_measurements: List[SourceMeasurement]


class DeployedPredictionExplanation(BaseModel):
    method: str
    output_space: Literal['probability']
    reference_type: Literal['synthetic_default_profile']
    reference_inputs: Dict[str, Any]
    baseline_probability: float
    predicted_probability: float
    reconstruction_error: float
    evaluated_coalitions: int
    unique_model_vectors: int
    groups: List[DomainContribution]
    limitations: str


class PredictionResponse(BaseModel):
    patient_id: str
    overall_cad: VesselRiskInfo
    vessels: Dict[str, VesselRiskInfo] = Field(..., description="Target artery risks: LAD, LCX, RCA")
    vessel_colors_3d: Dict[str, str] = Field(..., description="Direct 3D mesh hex map: {lad, lcx, rca, myocardium}")
    shap_explanations: Dict[str, List[SHAPFeatureImpact]] = Field(
        ..., description="Top contributing clinical features for CAD and each coronary vessel"
    )
    disclaimer: str = Field(..., description="Clinical safety statement")
    evidence: PredictionEvidence
    prediction_explanations: Dict[str, DeployedPredictionExplanation] = Field(default_factory=dict)


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

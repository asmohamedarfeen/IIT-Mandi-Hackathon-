"""
CardioVision AI Prediction & Explainability Service.
Handles model loading, feature preparation, multi-target inference,
calibrated probability estimation, 3D anatomical risk coloring, and independent XGBoost TreeSHAP explanations.
"""

import os
import json
import logging
import hashlib
import warnings
from datetime import datetime, timezone
from uuid import uuid4
from typing import Dict, Any, List, Optional, Tuple
import joblib
import numpy as np
import pandas as pd
import shap

# Suppress sklearn/LightGBM feature name validation warning when passing ndarray/clean feature vectors
warnings.filterwarnings(
    "ignore",
    message=".*X does not have valid feature names, but LGBMClassifier was fitted with feature names.*",
    category=UserWarning,
)
warnings.filterwarnings(
    "ignore",
    message=".*X has feature names, but.*was fitted without feature names.*",
    category=UserWarning,
)

from backend.core.config import settings
from backend.cardio.constants import (
    TARGET_NAMES,
    TARGET_DESCRIPTIONS,
    COLOR_LOW_RISK,
    COLOR_MODERATE_RISK,
    COLOR_HIGH_RISK,
    RISK_THRESHOLD_LOW,
    RISK_THRESHOLD_HIGH,
    CLINICAL_SAFETY_DISCLAIMER,
    RAW_BINARY_TEXT_FEATURES,
    RAW_NUMERIC_FEATURES,
    RAW_BINARY_NUMERIC_FEATURES,
)
from backend.cardio.service.feature_service import (
    prepare_features,
)
from backend.cardio.schemas.patient_schema import PatientInputSchema
from backend.cardio.service.explanation_service import build_feature_lineage
from backend.cardio.schemas.prediction_schema import (
    VesselRiskInfo,
    SHAPFeatureImpact,
    PredictionResponse,
    PredictionEvidence,
    TargetBenchmarkResponse,
    ThreeDAnatomyResponse,
)

logger = logging.getLogger("CardioVision.PredictionService")

FEATURE_DISPLAY_NAMES = {
    "Age": "Patient Age",
    "Weight": "Weight (kg)",
    "Length": "Height (cm)",
    "BMI": "Body Mass Index",
    "BP": "Systolic Blood Pressure (mmHg)",
    "PR": "Pulse Rate (bpm)",
    "FBS": "Fasting Blood Sugar (mg/dL)",
    "CR": "Serum Creatinine (mg/dL)",
    "TG": "Triglycerides (mg/dL)",
    "LDL": "LDL Cholesterol (mg/dL)",
    "HDL": "HDL Cholesterol (mg/dL)",
    "BUN": "Blood Urea Nitrogen (mg/dL)",
    "ESR": "Erythrocyte Sedimentation Rate",
    "HB": "Hemoglobin (g/dL)",
    "K": "Serum Potassium (mEq/L)",
    "Na": "Serum Sodium (mEq/L)",
    "WBC": "White Blood Cell Count",
    "Lymph": "Lymphocyte (%)",
    "Neut": "Neutrophil (%)",
    "PLT": "Platelet Count",
    "EF-TTE": "Echo Ejection Fraction (%)",
    "Region RWMA": "Regional Wall Motion Abnormality",
    "Function Class": "NYHA Functional Class",
    "DM": "Diabetes Mellitus",
    "HTN": "Hypertension",
    "Current Smoker": "Active Smoking Status",
    "EX-Smoker": "Former Smoker History",
    "FH": "Family History of CAD",
    "Edema": "Peripheral Edema",
    "Typical Chest Pain": "Typical Anginal Chest Pain",
    "Q Wave": "Pathologic Q-Wave",
    "St Elevation": "ECG ST Elevation",
    "St Depression": "ECG ST Depression",
    "Tinversion": "ECG T-Wave Inversion",
    "Sex": "Sex (Male/Female)",
    "BBB": "Bundle Branch Block",
    "VHD": "Valvular Heart Disease",
    "Obesity": "Clinical Obesity",
    "CRF": "Chronic Renal Failure",
    "CVA": "Cerebrovascular Accident",
    "Airway disease": "Airway Disease",
    "Thyroid Disease": "Thyroid Disease",
    "CHF": "Congestive Heart Failure",
    "DLP": "Dyslipidemia",
    "Weak Peripheral Pulse": "Weak Peripheral Pulse",
    "Lung rales": "Pulmonary Rales",
    "Systolic Murmur": "Systolic Heart Murmur",
    "Diastolic Murmur": "Diastolic Heart Murmur",
    "Dyspnea": "Dyspnea on Exertion",
    "Atypical": "Atypical Angina",
    "Nonanginal": "Non-anginal Discomfort",
    "Exertional CP": "Exertional Chest Pain",
    "LowTH Ang": "Low Threshold Angina",
    "LVH": "Left Ventricular Hypertrophy",
    "Poor R Progression": "Poor R-Wave Progression",
    "Pulse_Pressure": "Calculated Pulse Pressure",
    "Mean_Arterial_Pressure": "Mean Arterial Pressure (MAP)",
    "Shock_Index": "Shock Index (PR/SBP)",
    "Castelli_Risk_Index_I": "Castelli Risk Index I (TC/HDL)",
    "Castelli_Risk_Index_II": "Castelli Risk Index II (LDL/HDL)",
    "Atherogenic_Index_Plasma": "Atherogenic Index of Plasma (AIP)",
    "TyG_Index": "Triglyceride-Glucose Index (TyG)",
    "Non_HDL_Cholesterol": "Non-HDL Cholesterol (mg/dL)",
    "NLR": "Neutrophil-to-Lymphocyte Ratio (NLR)",
    "PLR": "Platelet-to-Lymphocyte Ratio (PLR)",
    "SII": "Systemic Immune-Inflammation Index (SII)",
    "BUN_CR_Ratio": "BUN / Creatinine Ratio",
    "Age_EF_Ratio": "Age / Ejection Fraction Ratio",
    "ECG_Abnormality_Score": "ECG Composite Abnormality Score",
    "Ischemic_ECG": "Ischemic ECG Findings",
    "Has_RWMA": "Echocardiographic RWMA Present",
    "RWMA_LAD_Territory": "RWMA: Anterior/Apical (LAD Territory)",
    "RWMA_LCX_Territory": "RWMA: Lateral/Postero-lateral (LCX Territory)",
    "RWMA_RCA_Territory": "RWMA: Inferior/Posterior (RCA Territory)",
    "Pretest_PTP_Score": "Pretest CAD Probability (Duke/DF Score)",
    "Metabolic_Risk_Score": "Metabolic Syndrome Score",
    "Lifestyle_Risk_Index": "Lifestyle Risk Index",
    "BMI_Category_Overweight": "BMI Category: Overweight",
    "BMI_Category_Obese": "BMI Category: Obese",
    "Log_TG": "Log-Transformed Triglycerides",
    "Log_CR": "Log-Transformed Creatinine",
    "Log_ESR": "Log-Transformed ESR",
    "Log_WBC": "Log-Transformed WBC",
    "Log_FBS": "Log-Transformed Fasting Glucose",
    "Log_BUN": "Log-Transformed BUN",
}


class PredictionService:
    """
    Singleton service managing model evaluation, inference, and SHAP explanations.
    """
    _instance = None

    def __init__(self):
        self.ready = False
        self.bundle: Optional[Dict[str, Any]] = None
        self.tree_explainers: Dict[str, Any] = {}
        self.anatomy_cache: Optional[Dict[str, Any]] = None
        self.benchmark_cache: Optional[Dict[str, Any]] = None
        self.model_artifact_sha256: Optional[str] = None
        self._load_artifacts()

    def _load_artifacts(self):
        if not os.path.exists(settings.MODEL_BUNDLE_PATH):
            logger.warning(f"Model bundle not found at {settings.MODEL_BUNDLE_PATH}. Need to run pipeline first.")
            return

        try:
            logger.info(f"Loading model bundle from {settings.MODEL_BUNDLE_PATH}...")
            self.bundle = joblib.load(settings.MODEL_BUNDLE_PATH)
            with open(settings.MODEL_BUNDLE_PATH, "rb") as artifact:
                self.model_artifact_sha256 = hashlib.file_digest(artifact, "sha256").hexdigest()
            if not isinstance(self.bundle, dict) or not self.bundle.get("feature_names"):
                raise ValueError("Model bundle has no feature contract")

            # Initialize TreeSHAP explainers for fast patient-level explanation
            for target in TARGET_NAMES:
                if "tree_surrogates" in self.bundle and target in self.bundle["tree_surrogates"]:
                    surrogate = self.bundle["tree_surrogates"][target]
                    self.tree_explainers[target] = shap.TreeExplainer(surrogate)
                else:
                    calibrated = self.bundle["calibrated_models"][target]
                    # Retrieve base estimator from calibrated classifier
                    cal_clf = calibrated.calibrated_classifiers_[0]
                    voting_clf = getattr(cal_clf, "estimator", getattr(cal_clf, "base_estimator", None))
                    xgb_est = [est for name, est in voting_clf.named_estimators_.items() if name == "xgboost"][0]
                    self.tree_explainers[target] = shap.TreeExplainer(xgb_est)

            # Load benchmark summary if present
            if os.path.exists(settings.BENCHMARK_PATH):
                with open(settings.BENCHMARK_PATH, "r") as f:
                    self.benchmark_cache = json.load(f)

            # Readiness means all four predictors and explanations executed successfully.
            prediction = self.predict(PatientInputSchema())
            probabilities = [prediction.overall_cad.probability] + [risk.probability for risk in prediction.vessels.values()]
            if not all(np.isfinite(value) and 0 <= value <= 1 for value in probabilities):
                raise ValueError("Model readiness check returned invalid probabilities")
            self.ready = True
            logger.info("CardioVision PredictionService successfully initialized.")
        except Exception:
            self.bundle = None
            self.tree_explainers.clear()
            self.ready = False
            logger.exception("Model initialization failed; prediction service is unavailable")

    @property
    def models_ready(self):
        return self.ready and self.bundle is not None

    def _prepare_patient_feature_vector(self, patient_data: PatientInputSchema) -> Tuple[np.ndarray, pd.DataFrame]:
        """Convert Pydantic patient schema into clean engineered feature vector in saved bundle order."""
        # Convert schema to dict with alias support
        raw_dict = patient_data.model_dump(by_alias=True, exclude={"patient_id", "assessment_mode", "confirmed_measurements", "input_sources"})

        df = pd.DataFrame([raw_dict])
        aligned_df = prepare_features(df, feature_names=self.bundle["feature_names"])
        vector = aligned_df.values.astype(np.float32)
        if not np.isfinite(vector).all():
            raise ValueError("Model input contains non-finite feature values")
        return vector, aligned_df

    def _determine_risk_level(self, proba: float) -> Tuple[str, str]:
        """Determine clinical risk category and corresponding 3D visualization color."""
        if proba < RISK_THRESHOLD_LOW:
            return "Low Risk", COLOR_LOW_RISK
        elif proba < RISK_THRESHOLD_HIGH:
            return "Intermediate Risk", COLOR_MODERATE_RISK
        else:
            return "High Stenosis Risk", COLOR_HIGH_RISK

    def predict(self, patient_data: PatientInputSchema) -> PredictionResponse:
        """
        Executes multi-target calibrated prediction and generates independent XGBoost TreeSHAP explanations.
        """
        if self.bundle is None:
            self._load_artifacts()
            if self.bundle is None:
                raise RuntimeError("Model pipeline weights not loaded. Run train_pipeline.py first.")

        vector, aligned_df = self._prepare_patient_feature_vector(patient_data)
        clinical_inputs = patient_data.model_dump(by_alias=True, exclude={"patient_id", "assessment_mode", "confirmed_measurements", "input_sources"})
        from backend.cardio.service.deployed_explanation import explain_predictions
        prediction_explanations = explain_predictions(patient_data, self.bundle)

        target_risks: Dict[str, VesselRiskInfo] = {}
        shap_explanations: Dict[str, List[SHAPFeatureImpact]] = {}

        for target in TARGET_NAMES:
            model = self.bundle["calibrated_models"][target]
            proba = float(model.predict_proba(vector)[0, 1])
            threshold = float(self.bundle.get('decision_thresholds', {}).get(target, .5))
            if not np.isfinite(proba) or not 0 <= proba <= 1 or not np.isfinite(threshold) or not 0 <= threshold <= 1:
                raise ValueError('Invalid model probability or classification threshold')
            predicted_status = ('CAD' if target == 'CAD' else 'Stenotic') if proba >= threshold else 'Normal'
            risk_level, color_hex = self._determine_risk_level(proba)
            proba = round(proba, 4)
            proba_pct = round(proba * 100.0, 1)

            target_risks[target] = VesselRiskInfo(
                vessel=target,
                probability=proba,
                probability_percent=proba_pct,
                risk_level=risk_level,
                color_hex=color_hex,
                anatomical_description=TARGET_DESCRIPTIONS[target],
                predicted_status=predicted_status,
                decision_threshold=threshold,
            )

            # Compute TreeSHAP local values for this patient
            explainer = self.tree_explainers[target]
            shap_values = explainer.shap_values(vector)
            if isinstance(shap_values, list) and len(shap_values) == 2:
                shap_row = shap_values[1][0]
            elif isinstance(shap_values, np.ndarray) and len(shap_values.shape) > 1:
                shap_row = shap_values[0]
            else:
                shap_row = shap_values

            # Sort features by absolute impact
            abs_indices = np.argsort(np.abs(shap_row))[::-1]
            top_impacts: List[SHAPFeatureImpact] = []

            for idx in abs_indices[:8]:
                feat_name = self.bundle["feature_names"][idx]
                contrib = round(float(shap_row[idx]), 4)
                if abs(contrib) < 0.001:
                    continue

                patient_val = aligned_df.iloc[0][feat_name]
                if isinstance(patient_val, (int, float, np.number)):
                    patient_val = round(float(patient_val), 2)
                else:
                    patient_val = str(patient_val)

                impact_dir = "increases_risk" if contrib > 0 else "decreases_risk"

                top_impacts.append(
                    SHAPFeatureImpact(
                        **build_feature_lineage(feat_name, clinical_inputs, float(vector[0, idx])).model_dump(),
                        feature=feat_name,
                        display_name=FEATURE_DISPLAY_NAMES.get(feat_name, feat_name),
                        contribution=contrib,
                        patient_value=patient_val,
                        impact_direction=impact_dir,
                    )
                )

            shap_explanations[target] = top_impacts

        # Build 3D mesh coloring mapping
        vessel_colors_3d = {
            "lad": target_risks["LAD"].color_hex,
            "lcx": target_risks["LCX"].color_hex,
            "rca": target_risks["RCA"].color_hex,
            "myocardium": "#64748B",  # Neutral anatomical slate/cardiac tone
        }

        return PredictionResponse(
            patient_id=patient_data.patient_id or "PATIENT-001",
            overall_cad=target_risks["CAD"],
            vessels={
                "LAD": target_risks["LAD"],
                "LCX": target_risks["LCX"],
                "RCA": target_risks["RCA"],
            },
            vessel_colors_3d=vessel_colors_3d,
            shap_explanations=shap_explanations,
            prediction_explanations=prediction_explanations,
            disclaimer=CLINICAL_SAFETY_DISCLAIMER,
            evidence=PredictionEvidence(
                assessment_id=str(uuid4()),
                generated_at=datetime.now(timezone.utc).isoformat(),
                clinical_inputs=clinical_inputs,
                prediction_model='; '.join(f'{target}: {name}' for target, name in self.bundle['prediction_model_names'].items()) if self.bundle.get('prediction_model_names') else "Sigmoid-calibrated voting ensemble",
                explanation_model="Deployed calibrated predictor: exact domain Shapley (probability); separate independent XGBoost TreeSHAP (log-odds)",
                input_provenance=patient_data.input_provenance(),
                application_version=settings.VERSION,
                model_artifact_sha256=self.model_artifact_sha256,
                validation_summary=self.bundle.get('model_release', {}).get('validation_summary') or {
                    "record_count": 303,
                    "method": "Supplied stratified 10-fold cross-validation of uncalibrated candidates and soft-voting ensembles",
                    "source": "Supplied benchmark_summary.json; not independently rerun",
                    "ensemble_metrics": {
                        target: dict(models["Ensemble (Soft-Voting)"])
                        for target, models in (self.benchmark_cache or {}).get("targets", {}).items()
                        if "Ensemble (Soft-Voting)" in models
                    },
                    "limitations": "These benchmarks do not measure the deployed sigmoid-calibrated models. No external validation, calibration curves or confidence intervals are supplied.",
                },
                limitations=[
                    "Confidence intervals are not available for this model release.",
                    "Clinical calibration and external validation have not been established. Training used 303 records.",
                    "SHAP describes an independent XGBoost model; contributions do not exactly explain the calibrated prediction probability.",
                    "Primary domain attributions reconstruct the deployed probability relative to an explicit synthetic reference. They are not causal, population-conditional or individual-feature explanations.",
                    "Classification thresholds are research operating points, distinct from artery display bands and not validated clinical decision boundaries.",
                    "35% and 65% are display thresholds, not validated clinical decision boundaries.",
                    "Whole-vessel scores do not locate lesions or measure percentage blockage. Anatomy is a reference model, not patient-specific imaging.",
                ],
            ),
        )

    def get_benchmarks(self) -> Dict[str, Any]:
        """Returns 10-fold cross-validation metrics across all candidate models."""
        if self.benchmark_cache:
            return self.benchmark_cache
        if os.path.exists(settings.BENCHMARK_PATH):
            with open(settings.BENCHMARK_PATH, "r") as f:
                self.benchmark_cache = json.load(f)
                return self.benchmark_cache
        raise FileNotFoundError("Benchmark metrics not generated.")

    def get_sample_patients(self) -> List[Dict[str, Any]]:
        """Returns the three supplied clinical examples with their recorded outcome labels."""
        if self.bundle and "sample_patients" in self.bundle:
            return self.bundle["sample_patients"]
        if self.benchmark_cache and "sample_patients" in self.benchmark_cache:
            return self.benchmark_cache["sample_patients"]
        return []

    def get_3d_anatomy(self) -> Dict[str, Any]:
        """Loads and returns 3D heart anatomical structures for Three.js rendering."""
        if self.anatomy_cache:
            return self.anatomy_cache
        if not os.path.exists(settings.ANATOMY_3D_PATH):
            raise FileNotFoundError(f"3D anatomy asset missing at {settings.ANATOMY_3D_PATH}")

        with open(settings.ANATOMY_3D_PATH, "r") as f:
            self.anatomy_cache = json.load(f)
        return self.anatomy_cache


# Global singleton instance
prediction_service_instance = PredictionService()

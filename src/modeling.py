"""Multi-target predictive modeling, cross-validation evaluation, and 3D viewer payload generation."""

import logging
import warnings
from typing import Any

import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from xgboost import XGBClassifier

from src.data_processing import build_preprocessor

logger = logging.getLogger(__name__)


def assign_risk_color(probability: float) -> dict[str, str]:
    """Maps predicted stenosis probability to clinical risk tier, hex color, and recommendation.

    Thresholds:
        - Low Risk (< 0.35): Green (#10B981) - Normal / Routine monitoring
        - Moderate Risk (0.35 <= p < 0.65): Amber (#F59E0B) - Borderline / Non-invasive follow-up
        - High Risk (>= 0.65): Red (#EF4444) - Significant stenosis (>=50%) / Urgent clinical review

    Args:
        probability: Predicted probability between 0.0 and 1.0.

    Returns:
        dict containing 'risk_level', 'color_hex', and 'recommendation'.
    """
    if probability < 0.35:
        return {
            "risk_level": "Low",
            "color_hex": "#10B981",
            "recommendation": "Normal / Routine monitoring",
        }
    elif probability < 0.65:
        return {
            "risk_level": "Moderate",
            "color_hex": "#F59E0B",
            "recommendation": "Borderline / Non-invasive follow-up",
        }
    else:
        return {
            "risk_level": "High",
            "color_hex": "#EF4444",
            "recommendation": "Significant stenosis (>=50%) / Urgent clinical review",
        }


def get_candidate_models() -> dict[str, Any]:
    """Returns candidate classification algorithms for benchmark evaluation.

    Returns:
        dict: Mapping of model names ('RandomForest', 'XGBoost', 'LogisticRegression')
            to estimator instances configured with fixed random states.
    """
    return {
        "RandomForest": RandomForestClassifier(
            n_estimators=100, max_depth=6, random_state=42
        ),
        "XGBoost": XGBClassifier(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.05,
            eval_metric="logloss",
            random_state=42,
        ),
        "LogisticRegression": LogisticRegression(
            max_iter=1000, penalty="l2", C=1.0, random_state=42
        ),
    }


def evaluate_multitarget_models(
    X: pd.DataFrame,
    targets: dict[str, pd.Series],
    num_cols: list[str],
    cat_cols: list[str],
) -> pd.DataFrame:
    """Performs 5-fold Stratified Cross-Validation for each clinical target across candidate models.

    For each target and candidate classifier, constructs an isolated preprocessing
    and classification pipeline to eliminate data leakage. Aggregates out-of-fold
    predictions to compute Accuracy, Precision, Recall, F1 Score, and ROC-AUC.

    Args:
        X: Feature matrix free of all target columns.
        targets: Dictionary mapping clinical target names (e.g. 'Cath', 'LAD') to binary Series.
        num_cols: List of numeric feature column names.
        cat_cols: List of categorical feature column names.

    Returns:
        pd.DataFrame: Evaluation table with columns 'Target', 'Model', 'Accuracy',
            'Precision', 'Recall', 'F1_Score', 'ROC_AUC'.
    """
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    candidate_models = get_candidate_models()
    results: list[dict[str, Any]] = []

    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        warnings.filterwarnings("ignore", category=UserWarning)

        for target_name, y in targets.items():
            logger.info("Evaluating models for target: %s", target_name)
            for model_name, clf in candidate_models.items():
                y_true_all: list[int] = []
                y_pred_all: list[int] = []
                y_prob_all: list[float] = []

                for train_idx, test_idx in skf.split(X, y):
                    X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
                    y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

                    pipeline = Pipeline(
                        [
                            ("preprocessor", build_preprocessor(num_cols, cat_cols)),
                            ("classifier", clone(clf)),
                        ]
                    )
                    pipeline.fit(X_train, y_train)

                    preds = pipeline.predict(X_test)
                    probs = pipeline.predict_proba(X_test)[:, 1]

                    y_true_all.extend(y_test)
                    y_pred_all.extend(preds)
                    y_prob_all.extend(probs)

                results.append(
                    {
                        "Target": target_name,
                        "Model": model_name,
                        "Accuracy": float(accuracy_score(y_true_all, y_pred_all)),
                        "Precision": float(
                            precision_score(y_true_all, y_pred_all, zero_division=0)
                        ),
                        "Recall": float(
                            recall_score(y_true_all, y_pred_all, zero_division=0)
                        ),
                        "F1_Score": float(
                            f1_score(y_true_all, y_pred_all, zero_division=0)
                        ),
                        "ROC_AUC": float(roc_auc_score(y_true_all, y_prob_all)),
                    }
                )

    return pd.DataFrame(results)


def train_final_models(
    X: pd.DataFrame,
    targets: dict[str, pd.Series],
    num_cols: list[str],
    cat_cols: list[str],
) -> dict[str, Pipeline]:
    """Trains final production pipelines using XGBoost classifiers for each target.

    Args:
        X: Feature matrix free of all target columns.
        targets: Dictionary mapping clinical target names to binary Series.
        num_cols: List of numeric feature column names.
        cat_cols: List of categorical feature column names.

    Returns:
        dict: Mapping of target names to fitted scikit-learn Pipeline objects.
    """
    trained_models: dict[str, Pipeline] = {}
    for target_name, y in targets.items():
        logger.info("Training production model for target: %s", target_name)
        pipeline = Pipeline(
            [
                ("preprocessor", build_preprocessor(num_cols, cat_cols)),
                (
                    "classifier",
                    XGBClassifier(
                        n_estimators=100,
                        max_depth=4,
                        learning_rate=0.05,
                        eval_metric="logloss",
                        random_state=42,
                    ),
                ),
            ]
        )
        pipeline.fit(X, y)
        trained_models[target_name] = pipeline
    return trained_models


def _sanitize_measurement(val: Any) -> Any:
    """Safely converts numpy scalars to standard Python primitives for JSON compatibility."""
    if hasattr(val, "item"):
        return val.item()
    return val


def generate_3d_payload(
    patient_record: dict[str, Any],
    trained_models: dict[str, Pipeline],
    feature_cols: list[str],
    patient_id: str = "PT-SAMPLE-01",
) -> dict[str, Any]:
    """Generates standardized 3D heart viewer payload from patient data and trained models.

    Args:
        patient_record: Dictionary containing single patient features.
        trained_models: Dictionary containing fitted pipelines for 'Cath', 'LAD', 'LCX', 'RCA'.
        feature_cols: List of feature names expected by the model preprocessor.
        patient_id: Identifier for the patient record. Defaults to 'PT-SAMPLE-01'.

    Returns:
        dict: Hierarchical JSON-serializable clinical risk payload with overall CAD assessment,
            individual vessel stenosis probabilities, hex color encodings, physiological
            measurements, and medical safety disclaimer.
    """
    df_single = pd.DataFrame([patient_record])[feature_cols]

    vessel_preds: dict[str, dict[str, Any]] = {}
    for vessel in ["LAD", "LCX", "RCA"]:
        prob = float(trained_models[vessel].predict_proba(df_single)[0, 1])
        color_info = assign_risk_color(prob)
        vessel_preds[vessel] = {
            "probability": round(prob, 4),
            "stenosis_predicted": bool(prob >= 0.5),
            "risk_level": color_info["risk_level"],
            "color_hex": color_info["color_hex"],
            "recommendation": color_info["recommendation"],
        }

    cad_prob = float(trained_models["Cath"].predict_proba(df_single)[0, 1])
    cad_color_info = assign_risk_color(cad_prob)

    measurement_keys = [
        "Age",
        "BP",
        "PR",
        "FBS",
        "TG",
        "LDL",
        "HDL",
        "EF-TTE",
        "Region RWMA",
    ]
    key_measurements = {
        k: _sanitize_measurement(patient_record[k])
        for k in measurement_keys
        if k in patient_record
    }

    return {
        "patient_id": patient_id,
        "overall_cad": {
            "probability": round(cad_prob, 4),
            "cad_predicted": bool(cad_prob >= 0.5),
            "risk_level": cad_color_info["risk_level"],
            "color_hex": cad_color_info["color_hex"],
        },
        "vessel_predictions": vessel_preds,
        "key_physiological_measurements": key_measurements,
        "clinical_safety_disclaimer": (
            "FOR DECISION SUPPORT & RESEARCH PURPOSES ONLY. "
            "Not a substitute for formal diagnostic angiography."
        ),
    }

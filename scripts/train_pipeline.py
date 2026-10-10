#!/usr/bin/env python3
"""
CardioVision AI - Comprehensive Training & Evaluation Pipeline
Implements 10-fold Stratified Cross-Validation,
Ensemble Soft-Voting, Calibrated Probability Estimation, and SHAP Explainability.
"""

import os

if __name__ == "__main__" and "--legacy-retrain" not in __import__("sys").argv:
    raise SystemExit("Retired legacy training entry point. Use scripts/improve_models.py for versioned, leakage-safe release training, or scripts/evaluate_model_quality.py --production-only for evaluation. Explicit --legacy-retrain acknowledges destructive historical artifact overwrite and unsuitable legacy evaluation.")
import sys
import json
import logging
from typing import Dict, Any, List, Tuple
import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler
import shap

# Ensure backend modules can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.cardio.constants import (
    TARGET_NAMES,
    LEAKAGE_COLUMNS,
    COLOR_LOW_RISK,
    COLOR_MODERATE_RISK,
    COLOR_HIGH_RISK,
    RISK_THRESHOLD_LOW,
    RISK_THRESHOLD_HIGH,
)
from backend.cardio.service.feature_service import (
    prepare_training_data,
)

from backend.model_quality.models import get_candidate_models, get_voting_model
from backend.model_quality.metrics import binary_metrics

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("CardioVisionPipeline")


def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray, y_proba: np.ndarray) -> Dict[str, float]:
    """Calculate all primary and secondary evaluation metrics specified in plan.md."""
    metrics = binary_metrics(y_true, y_proba, y_pred=y_pred)
    names = ("accuracy", "precision", "recall", "f1", "roc_auc", "specificity", "mcc")
    return {name: round(float(metrics[name]), 4) if metrics[name] is not None else None for name in names}



def run_cross_validation_benchmark(
    X: np.ndarray, y: np.ndarray, feature_names: List[str]
) -> Tuple[Dict[str, Dict[str, float]], Dict[str, Any]]:
    """
    Evaluates all model candidates using Stratified 10-Fold Cross-Validation.
    Builds a soft-voting ensemble of top performers.
    """
    skf = StratifiedKFold(n_splits=10, shuffle=True, random_state=42)
    models = get_candidate_models()
    benchmark_results: Dict[str, Dict[str, float]] = {}

    for name, model in models.items():
        fold_metrics: List[Dict[str, float]] = []

        for train_idx, val_idx in skf.split(X, y):
            X_train, X_val = X[train_idx], X[val_idx]
            y_train, y_val = y[train_idx], y[val_idx]

            if name == "LogisticRegression":
                scaler = StandardScaler()
                X_train_proc = scaler.fit_transform(X_train)
                X_val_proc = scaler.transform(X_val)
            else:
                X_train_proc, X_val_proc = X_train, X_val

            model.fit(X_train_proc, y_train)
            y_pred = model.predict(X_val_proc)
            y_proba = model.predict_proba(X_val_proc)[:, 1]

            fold_metrics.append(calculate_metrics(y_val, y_pred, y_proba))

        # Compute average metrics across 10 folds
        avg_metrics = {
            metric: round(float(np.mean([f[metric] for f in fold_metrics if f[metric] is not None])), 4) if any(f[metric] is not None for f in fold_metrics) else None
            for metric in fold_metrics[0].keys()
        }
        benchmark_results[name] = avg_metrics
        logger.info('Model %-18s -> ROC-AUC: %s, F1: %s, Acc: %s', name, avg_metrics['roc_auc'], avg_metrics['f1'], avg_metrics['accuracy'])

    # Build and benchmark Production Soft-Voting Ensemble
    ensemble = get_voting_model()

    ensemble_fold_metrics: List[Dict[str, float]] = []
    for train_idx, val_idx in skf.split(X, y):
        X_train, X_val = X[train_idx], X[val_idx]
        y_train, y_val = y[train_idx], y[val_idx]

        ensemble.fit(X_train, y_train)
        y_pred = ensemble.predict(X_val)
        y_proba = ensemble.predict_proba(X_val)[:, 1]
        ensemble_fold_metrics.append(calculate_metrics(y_val, y_pred, y_proba))

    avg_ensemble_metrics = {
        metric: round(float(np.mean([f[metric] for f in ensemble_fold_metrics if f[metric] is not None])), 4) if any(f[metric] is not None for f in ensemble_fold_metrics) else None
        for metric in ensemble_fold_metrics[0].keys()
    }
    benchmark_results["Ensemble (Soft-Voting)"] = avg_ensemble_metrics
    logger.info('Production Ensemble -> ROC-AUC: %s, F1: %s, Acc: %s', avg_ensemble_metrics['roc_auc'], avg_ensemble_metrics['f1'], avg_ensemble_metrics['accuracy'])

    return benchmark_results, ensemble


def train_calibrated_pipeline(
    excel_path: str, artifacts_dir: str
) -> Dict[str, Any]:
    """
    Executes full multi-target pipeline, fits calibrated ensembles, calculates SHAP explainers,
    and serializes weights into artifacts.
    """
    logger.info(f"Loading data from {excel_path}...")
    X_df, targets_dict, feature_names = prepare_training_data(excel_path)
    X = X_df.values.astype(np.float32)

    logger.info(f"Training feature matrix shape: {X.shape} with {len(feature_names)} features.")

    calibrated_models: Dict[str, Any] = {}
    fitted_ensembles: Dict[str, Any] = {}
    target_benchmarks: Dict[str, Any] = {}
    shap_explainers: Dict[str, Any] = {}
    shap_global_importances: Dict[str, Any] = {}
    tree_surrogates: Dict[str, Any] = {}

    for target_name in TARGET_NAMES:
        logger.info(f"\n{'='*20} Training Pipeline for Target: {target_name} {'='*20}")
        y = targets_dict[target_name].values.astype(int)

        # 1. Benchmark candidate models with 10-Fold CV
        benchmarks, ensemble_model = run_cross_validation_benchmark(X, y, feature_names)
        target_benchmarks[target_name] = benchmarks

        # 2. Fit full ensemble on complete dataset
        ensemble_model.fit(X, y)
        fitted_ensembles[target_name] = ensemble_model

        # 3. Fit probability calibration (Platt Sigmoid Calibration via CV)
        calibrated_clf = CalibratedClassifierCV(
            estimator=ensemble_model, method="sigmoid", cv=5
        )
        calibrated_clf.fit(X, y)
        calibrated_models[target_name] = calibrated_clf

        # 4. Generate TreeSHAP explainer using regularized XGBoost surrogate
        xgb_surrogate = get_candidate_models()["XGBoost"]
        xgb_surrogate.fit(X, y)
        explainer = shap.TreeExplainer(xgb_surrogate)
        shap_values = explainer.shap_values(X)

        if isinstance(shap_values, list) and len(shap_values) == 2:
            shap_matrix = shap_values[1]
        else:
            shap_matrix = shap_values

        mean_abs_shap = np.abs(shap_matrix).mean(axis=0)
        top_indices = np.argsort(mean_abs_shap)[::-1][:15]

        global_importance_list = []
        for idx in top_indices:
            global_importance_list.append({
                "feature": feature_names[idx],
                "importance": round(float(mean_abs_shap[idx]), 4),
                "mean_val": round(float(np.mean(X[:, idx])), 2),
            })
        shap_global_importances[target_name] = global_importance_list
        shap_explainers[target_name] = explainer
        tree_surrogates[target_name] = xgb_surrogate

    # Extract sample patients for dashboard testing (Patient 1: Normal, Patient 2: Single vessel LAD, Patient 3: High-risk multivessel)
    sample_indices = [15, 0, 1]  # Carefully selected indices from dataset
    raw_df = pd.read_excel(excel_path)
    sample_patients = []
    for idx in sample_indices:
        patient_raw = raw_df.iloc[idx].to_dict()
        patient_features = X_df.iloc[idx].to_dict()
        sample_patients.append({
            "patient_id": f"PATIENT-{idx+1001}",
            "ground_truth": {
                "CAD": str(patient_raw.get("Cath", "")),
                "LAD": str(patient_raw.get("LAD", "")),
                "LCX": str(patient_raw.get("LCX", "")),
                "RCA": str(patient_raw.get("RCA", "")),
            },
            "features": {k: float(v) if isinstance(v, (int, float, np.number)) else str(v) for k, v in patient_features.items()}
        })

    os.makedirs(artifacts_dir, exist_ok=True)

    # Save joblib bundle
    model_bundle = {
        "calibrated_models": calibrated_models,
        "tree_surrogates": tree_surrogates,
        "feature_names": feature_names,
        "benchmark_metrics": target_benchmarks,
        "shap_global_importances": shap_global_importances,
        "sample_patients": sample_patients,
        "reference_background": X[:50],  # Background sample for inference SHAP
    }
    model_path = os.path.join(artifacts_dir, "cardiovision_ensemble.joblib")
    joblib.dump(model_bundle, model_path)
    logger.info(f"Saved complete model bundle to {model_path}")

    # Save JSON benchmark report
    benchmark_report_path = os.path.join(artifacts_dir, "benchmark_summary.json")
    with open(benchmark_report_path, "w") as f:
        json.dump({
            "targets": target_benchmarks,
            "global_importances": shap_global_importances,
            "sample_patients": sample_patients,
        }, f, indent=2)
    logger.info(f"Saved benchmark summary to {benchmark_report_path}")

    return model_bundle


if __name__ == "__main__":
    dataset_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "extention of Z-Alizadeh sani dataset.xlsx"))
    artifacts_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "artifacts"))
    train_calibrated_pipeline(dataset_file, artifacts_path)

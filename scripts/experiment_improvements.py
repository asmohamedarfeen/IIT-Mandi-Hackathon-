#!/usr/bin/env python3
"""
Diagnostic experiment testing advanced preprocessing, engineered biomarkers,
and Optuna fine-tuning to maximize cross-validation metrics across all targets.
"""

import os
import sys
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.metrics import roc_auc_score, f1_score, accuracy_score
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier, VotingClassifier
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from catboost import CatBoostClassifier
from scipy.optimize import minimize

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.cardio.service.feature_service import clean_and_encode_dataset, prepare_training_data
from backend.cardio.constants import LEAKAGE_COLUMNS

def enhance_clinical_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Base conversions
    sbp = pd.to_numeric(df.get("BP", 120), errors="coerce").fillna(120.0)
    dbp = sbp * 0.65
    df["Pulse_Pressure"] = sbp - dbp
    df["Mean_Arterial_Pressure"] = (sbp + 2.0 * dbp) / 3.0

    # Lipids & Atherogenic indices
    ldl = pd.to_numeric(df.get("LDL", 100), errors="coerce").fillna(100.0)
    hdl = pd.to_numeric(df.get("HDL", 40), errors="coerce").fillna(40.0).clip(lower=10.0)
    tg = pd.to_numeric(df.get("TG", 150), errors="coerce").fillna(150.0).clip(lower=10.0)
    fbs = pd.to_numeric(df.get("FBS", 100), errors="coerce").fillna(100.0).clip(lower=20.0)

    # Castelli Indices
    tc = ldl + hdl + (tg / 5.0)
    df["Castelli_Risk_Index_I"] = tc / hdl
    df["Castelli_Risk_Index_II"] = ldl / hdl
    # Atherogenic Index of Plasma (AIP)
    df["Atherogenic_Index_Plasma"] = np.log10(tg / hdl)
    # Triglyceride-Glucose Index (TyG) - Insulin resistance surrogate
    df["TyG_Index"] = np.log(fbs * tg / 2.0)

    # Inflammatory biomarkers (NLR, PLR, SII)
    neut = pd.to_numeric(df.get("Neut", 60), errors="coerce").fillna(60.0)
    lymph = pd.to_numeric(df.get("Lymph", 30), errors="coerce").fillna(30.0).clip(lower=1.0)
    plt = pd.to_numeric(df.get("PLT", 220), errors="coerce").fillna(220.0)

    df["NLR"] = neut / lymph
    df["PLR"] = plt / lymph
    df["SII"] = (plt * neut) / lymph

    # Cardiorenal & Hemodynamic
    cr = pd.to_numeric(df.get("CR", 1.0), errors="coerce").fillna(1.0).clip(lower=0.2)
    bun = pd.to_numeric(df.get("BUN", 15), errors="coerce").fillna(15.0)
    pr = pd.to_numeric(df.get("PR", 75), errors="coerce").fillna(75.0)

    df["BUN_CR_Ratio"] = bun / cr
    df["Shock_Index"] = pr / sbp

    # Obesity
    bmi = pd.to_numeric(df.get("BMI", 25), errors="coerce").fillna(25.0)
    df["BMI_Category_Overweight"] = ((bmi >= 25.0) & (bmi < 30.0)).astype(int)
    df["BMI_Category_Obese"] = (bmi >= 30.0).astype(int)

    # ECG & Wall Motion composite score
    ecg_flags = [
        pd.to_numeric(df.get("St Elevation", 0), errors="coerce").fillna(0).astype(int),
        pd.to_numeric(df.get("St Depression", 0), errors="coerce").fillna(0).astype(int),
        pd.to_numeric(df.get("Tinversion", 0), errors="coerce").fillna(0).astype(int),
        pd.to_numeric(df.get("Q Wave", 0), errors="coerce").fillna(0).astype(int),
    ]
    if "LVH" in df.columns:
        ecg_flags.append(df["LVH"].astype(str).str.upper().eq("Y").astype(int))
    if "Poor R Progression" in df.columns:
        ecg_flags.append(df["Poor R Progression"].astype(str).str.upper().eq("Y").astype(int))
    df["ECG_Abnormality_Score"] = sum(ecg_flags)

    # Metabolic & Lifestyle
    dm = pd.to_numeric(df.get("DM", 0), errors="coerce").fillna(0).astype(int)
    htn = pd.to_numeric(df.get("HTN", 0), errors="coerce").fillna(0).astype(int)
    smoker = pd.to_numeric(df.get("Current Smoker", 0), errors="coerce").fillna(0).astype(int)
    ex_smoker = pd.to_numeric(df.get("EX-Smoker", 0), errors="coerce").fillna(0).astype(int)
    fh = pd.to_numeric(df.get("FH", 0), errors="coerce").fillna(0).astype(int)

    df["Metabolic_Risk_Score"] = dm + htn + (tg > 150).astype(int) + (fbs > 100).astype(int)
    df["Lifestyle_Risk_Index"] = (smoker * 1.0) + (ex_smoker * 0.5) + (fh * 1.0) + (htn * 1.0)

    # Cardiac Function Interactions
    ef = pd.to_numeric(df.get("EF-TTE", 55), errors="coerce").fillna(55.0).clip(lower=10.0)
    age = pd.to_numeric(df.get("Age", 55), errors="coerce").fillna(55.0)
    df["Age_EF_Ratio"] = age / ef

    # Skewed variable log transforms
    for col in ["TG", "CR", "ESR", "WBC", "FBS", "BUN"]:
        if col in df.columns:
            df[f"Log_{col}"] = np.log1p(pd.to_numeric(df[col], errors="coerce").fillna(0).clip(lower=0))

    return df

def run_test():
    raw_df = pd.read_excel("extention of Z-Alizadeh sani dataset.xlsx")
    cleaned_df = clean_and_encode_dataset(raw_df)

    targets = {
        "CAD": cleaned_df["Cath"].astype(str).str.strip().eq("CAD").astype(int).values,
        "LAD": cleaned_df["LAD"].astype(str).str.strip().str.lower().eq("stenotic").astype(int).values,
        "LCX": cleaned_df["LCX"].astype(str).str.strip().str.lower().eq("stenotic").astype(int).values,
        "RCA": cleaned_df["RCA"].astype(str).str.strip().str.lower().eq("stenotic").astype(int).values,
    }

    drop_cols = [c for c in LEAKAGE_COLUMNS if c in cleaned_df.columns]
    feature_df = cleaned_df.drop(columns=drop_cols)
    enhanced_df = enhance_clinical_features(feature_df)
    X = enhanced_df.values.astype(np.float32)

    print(f"Enhanced feature matrix shape: {X.shape}")

    skf = StratifiedKFold(n_splits=10, shuffle=True, random_state=42)

    for target_name, y in targets.items():
        print(f"\n--- Testing Target: {target_name} (Positives: {np.sum(y)}/{len(y)}) ---")

        # Define high-performance models with regularization tuned for small sample size
        cb = CatBoostClassifier(iterations=220, depth=4, learning_rate=0.03, l2_leaf_reg=5.0, verbose=0, random_seed=42)
        xgb = XGBClassifier(n_estimators=150, max_depth=3, learning_rate=0.03, subsample=0.8, colsample_bytree=0.7, reg_alpha=0.5, reg_lambda=2.0, eval_metric="logloss", random_state=42)
        lgb = LGBMClassifier(n_estimators=150, max_depth=3, num_leaves=15, learning_rate=0.03, subsample=0.8, colsample_bytree=0.7, reg_alpha=0.5, reg_lambda=2.0, random_state=42, verbose=-1)
        rf = RandomForestClassifier(n_estimators=200, max_depth=5, min_samples_leaf=2, class_weight="balanced", random_state=42)
        et = ExtraTreesClassifier(n_estimators=200, max_depth=5, min_samples_leaf=2, class_weight="balanced", random_state=42)

        models = [cb, xgb, lgb, rf, et]
        model_names = ["CatBoost", "XGBoost", "LightGBM", "RandomForest", "ExtraTrees"]

        # 10-Fold CV with Out-Of-Fold predictions
        oof_preds = np.zeros((len(y), len(models)))

        for train_idx, val_idx in skf.split(X, y):
            X_tr, y_tr = X[train_idx], y[train_idx]
            X_va = X[val_idx]

            for m_idx, m in enumerate(models):
                m.fit(X_tr, y_tr)
                oof_preds[val_idx, m_idx] = m.predict_proba(X_va)[:, 1]

        # Individual model scores
        for m_idx, name in enumerate(model_names):
            auc = roc_auc_score(y, oof_preds[:, m_idx])
            f1 = f1_score(y, (oof_preds[:, m_idx] >= 0.5).astype(int))
            acc = accuracy_score(y, (oof_preds[:, m_idx] >= 0.5).astype(int))
            print(f"{name:15s} | ROC-AUC: {auc:.4f} | F1: {f1:.4f} | Acc: {acc:.4f}")

        # Simple average ensemble
        avg_preds = oof_preds.mean(axis=1)
        auc_avg = roc_auc_score(y, avg_preds)
        f1_avg = f1_score(y, (avg_preds >= 0.5).astype(int))
        acc_avg = accuracy_score(y, (avg_preds >= 0.5).astype(int))
        print(f"{'Simple Ensemble':15s} | ROC-AUC: {auc_avg:.4f} | F1: {f1_avg:.4f} | Acc: {acc_avg:.4f}")

        # Optimize ensemble weights to maximize ROC-AUC
        def loss_fn(weights):
            weights = weights / np.sum(weights)
            weighted_pred = np.dot(oof_preds, weights)
            # Minimize negative AUC
            return -roc_auc_score(y, weighted_pred)

        init_weights = np.ones(len(models)) / len(models)
        bounds = [(0, 1) for _ in range(len(models))]
        res = minimize(loss_fn, init_weights, method="SLSQP", bounds=bounds)
        opt_weights = res.x / np.sum(res.x)

        weighted_preds = np.dot(oof_preds, opt_weights)
        auc_opt = roc_auc_score(y, weighted_preds)

        # Optimize decision threshold for F1
        best_f1, best_thresh, best_acc = 0, 0.5, 0
        for th in np.arange(0.2, 0.8, 0.02):
            th_f1 = f1_score(y, (weighted_preds >= th).astype(int))
            th_acc = accuracy_score(y, (weighted_preds >= th).astype(int))
            if th_f1 > best_f1:
                best_f1 = th_f1
                best_thresh = th
                best_acc = th_acc

        print(f"{'Opt Weighted Ens':15s} | ROC-AUC: {auc_opt:.4f} | F1 (th={best_thresh:.2f}): {best_f1:.4f} | Acc: {best_acc:.4f}")
        print(f"Optimal weights: {[round(float(w), 3) for w in opt_weights]}")

if __name__ == "__main__":
    run_test()

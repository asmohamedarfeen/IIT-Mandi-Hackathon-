# Cardiovascular Risk Analysis Notebook Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a comprehensive, publication-quality Jupyter notebook (`cardiovascular_risk_analysis.ipynb`) and supporting clinical ML pipeline for Track A of the Multimodal AI Hackathon 2026, analyzing the Z-Alizadeh Sani dataset, producing advanced statistical & interactive visualizations, training leak-free multi-target models (CAD, LAD, LCX, RCA), generating SHAP explanations, and exporting 3D heart mapping payloads.

**Architecture:** Build a modular python core (`src/data_processing.py` and `src/modeling.py`) with full unit test coverage to ensure data hygiene, target leakage prevention, and model stability. Assemble and execute the master Jupyter notebook (`cardiovascular_risk_analysis.ipynb`) uniting narrative medical analysis, publication-grade Seaborn figures, interactive Plotly charts, TreeSHAP interpretations, and downstream 3D JSON/CSV payloads.

**Tech Stack:** Python 3, Pandas, NumPy, Scikit-Learn, XGBoost, Matplotlib, Seaborn, Plotly, SHAP, Nbformat, Nbconvert, Pytest.

**Spec:** [`docs/superpowers/specs/2026-10-07-cardiovascular-risk-analysis-design.md`](file:///Users/asmohamedarfeen/Desktop/project/iit-ma/docs/superpowers/specs/2026-10-07-cardiovascular-risk-analysis-design.md)

## Global Constraints

- Dataset source file: `extention of Z-Alizadeh sani dataset.xlsx` (303 rows, 59 columns).
- Target leakage prevention is non-negotiable: `['Cath', 'LAD', 'LCX', 'RCA']` must be strictly excluded from input feature space $X$.
- Targets to predict: `Cath` (Overall CAD), `LAD` (Left Anterior Descending stenosis), `LCX` (Left Circumflex stenosis), `RCA` (Right Coronary Artery stenosis).
- Evaluation metrics must include: Accuracy, Precision, Recall, F1-Score, and ROC-AUC.
- Downstream 3D risk color mapping rules: Green (`#10B981`) for $p < 0.35$, Amber (`#F59E0B`) for $0.35 \le p < 0.65$, Red (`#EF4444`) for $p \ge 0.65$.
- Clinical Safety Disclaimer must be prominently included in notebook outputs and exported metadata.

---

### Task 1: Clinical Data Processing & Leakage Prevention Pipeline

**Files:**
- Create: `src/__init__.py`
- Create: `src/data_processing.py`
- Create: `tests/__init__.py`
- Create: `tests/test_data_processing.py`

**Interfaces:**
- Consumes: `extention of Z-Alizadeh sani dataset.xlsx`
- Produces:
  - `load_and_clean_dataset(filepath: str) -> pd.DataFrame`
  - `prepare_features_and_targets(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, pd.Series], list[str], list[str]]`
  - `build_preprocessor(numeric_features: list[str], categorical_features: list[str]) -> ColumnTransformer`

- [ ] **Step 1: Write failing tests for data processing and leakage prevention**

```python
# tests/test_data_processing.py
import os
import pytest
import pandas as pd
from src.data_processing import (
    load_and_clean_dataset,
    prepare_features_and_targets,
    TARGET_COLUMNS
)

DATA_PATH = "extention of Z-Alizadeh sani dataset.xlsx"

def test_load_and_clean_dataset():
    assert os.path.exists(DATA_PATH)
    df = load_and_clean_dataset(DATA_PATH)
    assert len(df) == 303
    # Check typo harmonization
    assert "Fmale" not in df["Sex"].unique()
    assert "Female" in df["Sex"].unique()
    # Check zero-variance column removed
    assert "Exertional CP" not in df.columns

def test_prepare_features_and_targets_leakage_prevention():
    df = load_and_clean_dataset(DATA_PATH)
    X, targets, num_cols, cat_cols = prepare_features_and_targets(df)
    
    # Verify strict target leakage prevention
    for target in TARGET_COLUMNS:
        assert target not in X.columns
        assert target in targets
        assert len(targets[target]) == 303
        # Binary encoded 0 or 1
        assert set(targets[target].unique()).issubset({0, 1})
    
    # Verify features are split properly
    assert len(num_cols) > 0
    assert len(cat_cols) > 0
    assert len(num_cols) + len(cat_cols) == len(X.columns)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_data_processing.py -v`  
Expected: FAIL with `ModuleNotFoundError: No module named 'src'`

- [ ] **Step 3: Implement data processing module**

```python
# src/data_processing.py
import pandas as pd
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder

TARGET_COLUMNS = ["Cath", "LAD", "LCX", "RCA"]

def load_and_clean_dataset(filepath: str) -> pd.DataFrame:
    """Loads and sanitizes the Z-Alizadeh Sani extension dataset."""
    df = pd.read_excel(filepath, sheet_name=0)
    
    # 1. Clean column strings
    df.columns = [c.strip() for c in df.columns]
    
    # 2. Fix typos in categorical values
    if "Sex" in df.columns:
        df["Sex"] = df["Sex"].replace({"Fmale": "Female"})
        
    # 3. Strip whitespace in string columns
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].astype(str).str.strip()
        
    # 4. Drop zero-variance columns (e.g. Exertional CP where all values are 'N')
    zero_var_cols = [c for c in df.columns if df[c].nunique() <= 1 and c not in TARGET_COLUMNS]
    if zero_var_cols:
        df = df.drop(columns=zero_var_cols)
        
    return df

def prepare_features_and_targets(df: pd.DataFrame) -> tuple:
    """Extracts leakage-free feature matrix X and encoded binary target series."""
    df_clean = df.copy()
    
    # Encode targets: Normal -> 0, CAD/Stenotic -> 1
    target_mapping = {
        "Cath": {"Normal": 0, "CAD": 1},
        "LAD": {"Normal": 0, "Stenotic": 1},
        "LCX": {"Normal": 0, "Stenotic": 1},
        "RCA": {"Normal": 0, "Stenotic": 1}
    }
    
    targets = {}
    for col, mapping in target_mapping.items():
        if col in df_clean.columns:
            targets[col] = df_clean[col].map(mapping).astype(int)
            
    # STRICT LEAKAGE PREVENTION: Drop all targets from X
    X = df_clean.drop(columns=[c for c in TARGET_COLUMNS if c in df_clean.columns])
    
    # Identify numeric and categorical columns
    numeric_cols = X.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = X.select_dtypes(include=["object"]).columns.tolist()
    
    return X, targets, numeric_cols, categorical_cols

def build_preprocessor(numeric_features: list, categorical_features: list) -> ColumnTransformer:
    """Builds a scikit-learn ColumnTransformer for scaling and encoding."""
    return ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), numeric_features),
            ("cat", OneHotEncoder(drop="first", handle_unknown="ignore", sparse_output=False), categorical_features)
        ],
        remainder="passthrough"
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_data_processing.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/ tests/
git commit -m "feat(data): implement clinical dataset cleaning and target leakage prevention"
```

---

### Task 2: Multi-Target Predictive Modeling, Evaluation & Payload Generation

**Files:**
- Create: `src/modeling.py`
- Create: `tests/test_modeling.py`

**Interfaces:**
- Consumes: `src/data_processing.py`
- Produces:
  - `evaluate_multitarget_models(X, targets, numeric_cols, categorical_cols) -> dict`
  - `train_final_models(X, targets, numeric_cols, categorical_cols) -> dict`
  - `generate_3d_payload(patient_record: dict, trained_models: dict, feature_cols: list) -> dict`

- [ ] **Step 1: Write failing tests for modeling and payload generator**

```python
# tests/test_modeling.py
import pytest
from src.data_processing import load_and_clean_dataset, prepare_features_and_targets
from src.modeling import (
    evaluate_multitarget_models,
    train_final_models,
    generate_3d_payload,
    assign_risk_color
)

DATA_PATH = "extention of Z-Alizadeh sani dataset.xlsx"

def test_risk_color_assignment():
    assert assign_risk_color(0.20)["risk_level"] == "Low"
    assert assign_risk_color(0.20)["color_hex"] == "#10B981"
    assert assign_risk_color(0.50)["risk_level"] == "Moderate"
    assert assign_risk_color(0.50)["color_hex"] == "#F59E0B"
    assert assign_risk_color(0.85)["risk_level"] == "High"
    assert assign_risk_color(0.85)["color_hex"] == "#EF4444"

def test_model_training_and_payload_generation():
    df = load_and_clean_dataset(DATA_PATH)
    X, targets, num_cols, cat_cols = prepare_features_and_targets(df)
    
    # Train models
    models = train_final_models(X, targets, num_cols, cat_cols)
    assert set(models.keys()) == {"Cath", "LAD", "LCX", "RCA"}
    
    # Test 3D payload generation for sample patient
    sample_patient = X.iloc[0].to_dict()
    payload = generate_3d_payload(sample_patient, models, X.columns.tolist())
    
    assert "patient_id" in payload
    assert "vessel_predictions" in payload
    assert set(payload["vessel_predictions"].keys()) == {"LAD", "LCX", "RCA"}
    assert "overall_cad" in payload
    assert "clinical_safety_disclaimer" in payload
    
    for vessel, data in payload["vessel_predictions"].items():
        assert 0.0 <= data["probability"] <= 1.0
        assert data["color_hex"] in ["#10B981", "#F59E0B", "#EF4444"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_modeling.py -v`  
Expected: FAIL with `ModuleNotFoundError: No module named 'src.modeling'`

- [ ] **Step 3: Implement modeling and payload generation module**

```python
# src/modeling.py
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from src.data_processing import build_preprocessor

def assign_risk_color(probability: float) -> dict:
    """Maps predicted stenosis probability to clinical risk tier and hex color."""
    if probability < 0.35:
        return {"risk_level": "Low", "color_hex": "#10B981", "recommendation": "Normal / Routine monitoring"}
    elif probability < 0.65:
        return {"risk_level": "Moderate", "color_hex": "#F59E0B", "recommendation": "Borderline / Non-invasive follow-up"}
    else:
        return {"risk_level": "High", "color_hex": "#EF4444", "recommendation": "Significant stenosis (>=50%) / Urgent clinical review"}

def get_candidate_models():
    """Returns candidate classification algorithms."""
    return {
        "RandomForest": RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42),
        "XGBoost": XGBClassifier(n_estimators=100, max_depth=4, learning_rate=0.05, eval_metric="logloss", random_state=42),
        "LogisticRegression": LogisticRegression(max_iter=1000, penalty="l2", C=1.0, random_state=42)
    }

def evaluate_multitarget_models(X: pd.DataFrame, targets: dict, num_cols: list, cat_cols: list) -> pd.DataFrame:
    """Performs 5-fold Stratified CV for each target and computes all required metrics."""
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    results = []
    
    for target_name, y in targets.items():
        for model_name, clf in get_candidate_models().items():
            pipeline = Pipeline([
                ("preprocessor", build_preprocessor(num_cols, cat_cols)),
                ("classifier", clf)
            ])
            
            y_true_all, y_pred_all, y_prob_all = [], [], []
            for train_idx, test_idx in skf.split(X, y):
                X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
                y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
                
                pipeline.fit(X_train, y_train)
                preds = pipeline.predict(X_test)
                probs = pipeline.predict_proba(X_test)[:, 1]
                
                y_true_all.extend(y_test)
                y_pred_all.extend(preds)
                y_prob_all.extend(probs)
                
            results.append({
                "Target": target_name,
                "Model": model_name,
                "Accuracy": accuracy_score(y_true_all, y_pred_all),
                "Precision": precision_score(y_true_all, y_pred_all, zero_division=0),
                "Recall": recall_score(y_true_all, y_pred_all, zero_division=0),
                "F1_Score": f1_score(y_true_all, y_pred_all, zero_division=0),
                "ROC_AUC": roc_auc_score(y_true_all, y_prob_all)
            })
            
    return pd.DataFrame(results)

def train_final_models(X: pd.DataFrame, targets: dict, num_cols: list, cat_cols: list) -> dict:
    """Trains final production pipelines (XGBoost) for all targets."""
    trained_models = {}
    for target_name, y in targets.items():
        pipeline = Pipeline([
            ("preprocessor", build_preprocessor(num_cols, cat_cols)),
            ("classifier", XGBClassifier(n_estimators=100, max_depth=4, learning_rate=0.05, eval_metric="logloss", random_state=42))
        ])
        pipeline.fit(X, y)
        trained_models[target_name] = pipeline
    return trained_models

def generate_3d_payload(patient_record: dict, trained_models: dict, feature_cols: list, patient_id: str = "PT-SAMPLE-01") -> dict:
    """Generates standardized 3D heart viewer payload from patient data."""
    df_single = pd.DataFrame([patient_record])[feature_cols]
    
    vessel_preds = {}
    for vessel in ["LAD", "LCX", "RCA"]:
        prob = float(trained_models[vessel].predict_proba(df_single)[0, 1])
        color_info = assign_risk_color(prob)
        vessel_preds[vessel] = {
            "probability": round(prob, 4),
            "stenosis_predicted": prob >= 0.5,
            "risk_level": color_info["risk_level"],
            "color_hex": color_info["color_hex"],
            "recommendation": color_info["recommendation"]
        }
        
    cad_prob = float(trained_models["Cath"].predict_proba(df_single)[0, 1])
    cad_color_info = assign_risk_color(cad_prob)
    
    return {
        "patient_id": patient_id,
        "overall_cad": {
            "probability": round(cad_prob, 4),
            "cad_predicted": cad_prob >= 0.5,
            "risk_level": cad_color_info["risk_level"],
            "color_hex": cad_color_info["color_hex"]
        },
        "vessel_predictions": vessel_preds,
        "key_physiological_measurements": {
            k: patient_record[k] for k in ["Age", "BP", "PR", "FBS", "TG", "LDL", "HDL", "EF-TTE", "Region RWMA"] if k in patient_record
        },
        "clinical_safety_disclaimer": "FOR DECISION SUPPORT & RESEARCH PURPOSES ONLY. Not a substitute for formal diagnostic angiography."
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_modeling.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/modeling.py tests/test_modeling.py
git commit -m "feat(modeling): implement multi-target evaluation and 3D visualization payload generator"
```

---

### Task 3: Build & Execute Master Jupyter Notebook (`cardiovascular_risk_analysis.ipynb`)

**Files:**
- Create: `cardiovascular_risk_analysis.ipynb`
- Create: `tests/test_notebook_execution.py`
- Output Artifacts:
  - `artifacts/sample_patient_3d_payload.json`
  - `artifacts/scored_patient_cohort.csv`
  - `artifacts/model_pipeline_weights.joblib`

**Interfaces:**
- Consumes: `extention of Z-Alizadeh sani dataset.xlsx`, `src/data_processing.py`, `src/modeling.py`
- Produces: Executed `.ipynb` notebook with all Markdown explanations, Seaborn plots, Plotly visualizations, SHAP summary & waterfall figures, and exported 3D JSON artifacts.

- [ ] **Step 1: Write test for notebook execution**

```python
# tests/test_notebook_execution.py
import os
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor

def test_notebook_executes_successfully():
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
    assert os.path.exists("artifacts/sample_patient_3d_payload.json")
    assert os.path.exists("artifacts/scored_patient_cohort.csv")
    assert os.path.exists("artifacts/model_pipeline_weights.joblib")
```

- [ ] **Step 2: Generate the complete master Jupyter notebook**
Assemble the notebook with all 7 comprehensive sections:
1. Executive Summary & Clinical Context (Problem statement overview, anatomical vessel map context, CAD definition, Clinical Safety Disclaimer).
2. Data Ingestion & Clinical Auditing (Shape 303x59, typo corrections, zero-variance feature removal).
3. Exploratory Data Analysis & Visualizations (Multi-vessel disease classification, target co-occurrence, lipid & metabolic boxplots, ECG lead change cross-tabulations, EF-TTE & RWMA distributions, clustered correlation heatmap, interactive Plotly 3D scatter).
4. Data Preprocessing & Target Leakage Prevention (Strict removal of `['Cath', 'LAD', 'LCX', 'RCA']` from $X$, ColumnTransformer).
5. Multi-Target Predictive Modeling (Stratified 5-Fold CV evaluation across XGBoost, Random Forest, Logistic Regression; ROC curves and confusion matrices for CAD, LAD, LCX, RCA).
6. Explainable AI (SHAP) (TreeSHAP summary beeswarm plots for all targets; local patient waterfall plots explaining high-risk vs low-risk cases).
7. Downstream 3D Heart Mapping Integration & Export (Radar/schematic vessel risk map, JSON payload export for 3D web viewer, batch cohort scoring CSV export, and joblib model weight serialization).

- [ ] **Step 3: Run notebook execution test to verify all cells run cleanly**

Run: `pytest tests/test_notebook_execution.py -v`  
Expected: PASS (generates all figures, runs all ML pipelines, outputs artifacts).

- [ ] **Step 4: Commit**

```bash
git add cardiovascular_risk_analysis.ipynb tests/test_notebook_execution.py artifacts/
git commit -m "feat(notebook): create and execute comprehensive cardiovascular risk analysis notebook"
```

---

### Task 4: Final Documentation & Verification

**Files:**
- Create: `README.md`
- Verify: Full test suite passes (`pytest tests/ -v`).

- [ ] **Step 1: Create README.md with comprehensive project documentation**
Document dataset background, problem statement overview, notebook structure, execution instructions, model performance metrics, and 3D visualization mapping schema.

- [ ] **Step 2: Run all unit and integration tests**

Run: `pytest tests/ -v`  
Expected: All tests PASS.

- [ ] **Step 3: Final Git Commit**

```bash
git add README.md
git commit -m "docs: add project README and evaluation guide"
```

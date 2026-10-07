# Design Specification: Cardiovascular Risk Analysis & Visualization Notebook

**Project:** Multimodal AI Hackathon 2026 — Track A: Cardiovascular Risk Visualization & Prediction  
**Date:** 2026-10-07  
**Status:** Approved by User  
**Target File:** `cardiovascular_risk_analysis.ipynb`  
**Dataset Source:** `extention of Z-Alizadeh sani dataset.xlsx` (303 records, 59 features)  
**Problem Statement Reference:** `Track A.pdf`

---

## 1. Executive Summary & Goals

The objective of this specification is to deliver a comprehensive, end-to-end data science Jupyter notebook for **Track A: Cardiovascular Risk Visualization & Prediction**.

The notebook serves two critical purposes:
1. **Clinical Exploratory Data Analysis & Visualization:** In-depth statistical analysis across demographics, symptoms, laboratory biomarkers, ECG anomalies, and echocardiographic parameters, uncovering the physiological hallmarks of Coronary Artery Disease (CAD) and multi-vessel stenosis.
2. **Predictive Modeling & Explainability (SHAP):** Training multi-target machine learning models to predict overall CAD status as well as vessel-specific stenosis in the Left Anterior Descending (LAD), Left Circumflex (LCX), and Right Coronary Artery (RCA), strictly enforcing zero target leakage, and providing local & global SHAP explanations and JSON payloads for 3D anatomical heart visualization.

---

## 2. Clinical Data Architecture & Preprocessing

### 2.1 Feature Taxonomy
The 59 columns in the Z-Alizadeh Sani extension dataset are grouped into distinct clinical categories:
- **Demographics & Anthropometrics:** `Age`, `Weight`, `Length`, `Sex`, `BMI`, `Obesity`.
- **Lifestyle & Comorbidities:** `Current Smoker`, `EX-Smoker`, `FH` (Family History), `DM` (Diabetes Mellitus), `HTN` (Hypertension), `CRF` (Chronic Renal Failure), `CVA` (Cerebrovascular Accident), `Airway disease`, `Thyroid Disease`, `CHF` (Congestive Heart Failure), `DLP` (Dyslipidemia).
- **Physical Examination & Symptoms:** `BP` (Blood Pressure), `PR` (Pulse Rate), `Edema`, `Weak Peripheral Pulse`, `Lung rales`, `Systolic Murmur`, `Diastolic Murmur`, `Typical Chest Pain`, `Dyspnea`, `Function Class`, `Atypical`, `Nonanginal`, `Exertional CP`, `LowTH Ang`.
- **Electrocardiography (ECG):** `Q Wave`, `St Elevation`, `St Depression`, `Tinversion`, `LVH` (Left Ventricular Hypertrophy), `Poor R Progression`, `BBB` (Bundle Branch Block: Normal, LBBB, RBBB).
- **Laboratory Biomarkers:** `FBS` (Fasting Blood Sugar), `CR` (Creatinine), `TG` (Triglycerides), `LDL`, `HDL`, `BUN`, `ESR`, `HB`, `K`, `Na`, `WBC`, `Lymph`, `Neut`, `PLT`.
- **Echocardiography (Echo):** `EF-TTE` (Ejection Fraction), `Region RWMA` (Regional Wall Motion Abnormality score), `VHD` (Valvular Heart Disease: N, mild, Moderate, Severe).
- **Ground-Truth Targets:**
  - `Cath`: Catheterization ground truth for overall CAD (`CAD` vs `Normal`).
  - `LAD`: Left Anterior Descending stenosis (`Stenotic` vs `Normal`).
  - `LCX`: Left Circumflex stenosis (`Stenotic` vs `Normal`).
  - `RCA`: Right Coronary Artery stenosis (`Stenotic` vs `Normal`).

### 2.2 Data Cleaning & Sanitization Rules
1. **Typo Harmonization:** Map `'Fmale'` to `'Female'` in `Sex`.
2. **Zero-Variance Feature Handling:** Identify and drop features with zero variance across all 303 samples (e.g., `Exertional CP` where 100% of rows are `'N'`).
3. **Strict Target Leakage Prevention (Track A Requirement 1d):**
   The feature matrix $X$ strictly drops `['Cath', 'LAD', 'LCX', 'RCA']`. No vessel target label is permitted in the feature space when predicting another vessel or overall CAD.
4. **Encoding Pipeline:**
   - Binary categorical features (e.g., Y/N flags) mapped to binary $\{0, 1\}$.
   - Multi-class nominal categoricals (`BBB`, `VHD`) transformed via one-hot encoding or ordinal scaling.
   - Continuous numerical features scaled using `StandardScaler`.

---

## 3. Exploratory Data Analysis & Visualization Suite

A hybrid visualization strategy combining **Seaborn/Matplotlib** (static publication figures) and **Plotly** (interactive exploration):

### 3.1 Target Prevalence & Multi-Vessel Burden
- Target distribution breakdown across all 4 targets (`CAD`: 71.3%, `LAD`: 58.4%, `LCX`: 39.3%, `RCA`: 37.6%).
- Multi-vessel stenosis classification:
  - Normal (0 vessels stenotic)
  - Single-Vessel Disease (SVD)
  - Double-Vessel Disease (DVD)
  - Triple-Vessel Disease (TVD)
- Coronary vessel co-occurrence heatmap evaluating pairwise co-stenosis rates between LAD, LCX, and RCA.

### 3.2 Demographic & Lifestyle Profiling
- Age distribution KDE curves and violin plots stratified by sex and CAD status.
- Comorbidity prevalence comparison (DM, HTN, Smoking, Family History) across CAD and non-CAD cohorts.

### 3.3 Laboratory Biomarkers & Cardiac Risk Ratios
- Box and violin plots comparing lipid fractions (`TG`, `LDL`, `HDL`) and glycemic control (`FBS`) against CAD status.
- Derived atherogenic risk ratios: `TG / HDL` and `LDL / HDL`.
- Renal and inflammatory markers: `BUN`, `CR`, `ESR`, `WBC`.

### 3.4 ECG & Echocardiographic Findings
- Cross-tabulation of ischemic ECG abnormalities (`ST Elevation`, `ST Depression`, `Tinversion`, `Q Wave`) against coronary artery territories.
- Analysis of Left Ventricular Ejection Fraction (`EF-TTE`) and `Region RWMA` across normal vs single-vessel vs multi-vessel disease.

### 3.5 Correlation & Multicollinearity
- High-dimensional hierarchically clustered correlation heatmap between clinical features and CAD/vessel targets.

### 3.6 Interactive Plotly Explorer
- Plotly 3D scatter plot (`Age` $\times$ `EF-TTE` $\times$ `LDL` colored by multi-vessel disease tier with patient metadata hover tooltips).
- Plotly interactive vessel stenosis prevalence explorer.

---

## 4. Multi-Target Predictive Modeling & Evaluation

### 4.1 Problem Formulation
Four supervised binary classification models:
1. $\mathcal{M}_{\text{CAD}}(X) \rightarrow \hat{y}_{\text{CAD}} \in \{0, 1\}$
2. $\mathcal{M}_{\text{LAD}}(X) \rightarrow \hat{y}_{\text{LAD}} \in \{0, 1\}$
3. $\mathcal{M}_{\text{LCX}}(X) \rightarrow \hat{y}_{\text{LCX}} \in \{0, 1\}$
4. $\mathcal{M}_{\text{RCA}}(X) \rightarrow \hat{y}_{\text{RCA}} \in \{0, 1\}$

### 4.2 Algorithms & Validation Strategy
- **Algorithms:**
  - **XGBoost Classifier** (Gradient boosted trees)
  - **Random Forest Classifier** (Bagging ensemble)
  - **Logistic Regression (L2-regularized)** (Clinical linear benchmark)
- **Validation Scheme:** Stratified 5-Fold Cross-Validation to guarantee balanced class representation across all folds and prevent test leakage.

### 4.3 Evaluation Metrics (Track A Requirement 1e)
- Accuracy, Precision, Recall (Sensitivity), Specificity, F1-Score, and ROC-AUC.
- Receiver Operating Characteristic (ROC) curves plotted for each target.
- Confusion matrices annotated with clinical implications (false negatives vs false positives).

---

## 5. Explainable AI (SHAP) & Clinical Interpretability

Directly addressing **Requirements 3b & 3c**:
- **Global Interpretability:**
  - TreeSHAP summary beeswarm plots highlighting the top 15 features for overall CAD and each specific coronary vessel.
  - Quantitative feature attribution breakdown revealing directional impacts (e.g., low EF-TTE elevating CAD risk, anterior lead ST changes elevating LAD stenosis probability).
- **Local Patient Interpretability (Case Studies):**
  - High-risk patient case study: SHAP waterfall plot detailing why the model classified the patient as high risk for multi-vessel CAD.
  - Low-risk patient case study: SHAP waterfall plot highlighting protective physiological values.

---

## 6. Downstream Integration & 3D Mapping Support

Directly addressing **Requirement 2** and preparing artifacts for the 3D heart visualization viewer:
1. **Risk Probability to Color Schema:**
   - Green (`#10B981`): Low Risk ($p < 0.35$)
   - Amber/Yellow (`#F59E0B`): Moderate Risk ($0.35 \le p < 0.65$)
   - Crimson Red (`#EF4444`): High Risk ($p \ge 0.65$)
2. **Schema & Artifact Generation:**
   - `artifacts/sample_patient_3d_payload.json`: JSON payload containing a sample patient's physiological features, predicted probabilities (`p_CAD`, `p_LAD`, `p_LCX`, `p_RCA`), assigned color hex codes, and top SHAP drivers.
   - `artifacts/scored_patient_cohort.csv`: Full cohort scored with out-of-fold predicted probabilities and risk tiers.
   - `artifacts/model_pipeline_weights.joblib`: Serialized model pipelines for direct integration with the FastAPI backend.
3. **Clinical Safety Disclaimer (Requirement 5):**
   Explicit visual disclaimer embedded in both the notebook and exported payload metadata.

---

## 7. Deliverables & Acceptance Criteria

- [x] Standalone runnable Jupyter notebook `cardiovascular_risk_analysis.ipynb`.
- [x] Zero target leakage verified (`Cath`, `LAD`, `LCX`, `RCA` excluded from $X$).
- [x] Comprehensive EDA with static (Seaborn) and interactive (Plotly) figures.
- [x] Trained models for CAD, LAD, LCX, RCA evaluated with 5-fold cross validation.
- [x] SHAP beeswarm and waterfall explanations.
- [x] Exported integration payloads for the 3D heart model.

# CardioVision AI - System Architecture & Technical Specification

## 1. System Overview

CardioVision AI is a multi-task, clinically interpretable machine learning system designed to predict overall Coronary Artery Disease (CAD) and vessel-specific stenosis in the three primary coronary arteries (LAD, LCX, RCA). It pairs calibrated predictive machine learning with real-time 3D anatomical visualization and TreeSHAP explainability.

---

## 2. Architecture Diagram

```mermaid
flowchart TD
    subgraph Data Layer
        A[Extension of Z-Alizadeh Sani Dataset<br/>303 Patients, 59 Columns] --> B[Leakage Prevention Filter<br/>Exclude Cath, CAD, LAD, LCX, RCA]
        B --> C[Clinical Feature Engineering<br/>Pulse Pressure, MAP, Lipid Ratios, ECG Score, Metabolic Index]
    end

    subgraph Multi-Target Machine Learning
        C --> D[Stratified 10-Fold Cross-Validation]
        D --> E[Benchmark Models<br/>CatBoost, XGBoost, LightGBM, Random Forest, Extra Trees, LogReg]
        E --> F[Soft-Voting Calibrated Ensemble]
        F --> G[Probability Calibration<br/>Platt Sigmoid 0-100%]
        F --> H[TreeSHAP Explainer<br/>Feature Attributions]
    end

    subgraph Backend Service [FastAPI Modular Architecture]
        G --> I[FastAPI REST API]
        H --> I
        J[(SQLite / PostgreSQL DB<br/>Patient Assessments & Audits)] <--> I
    end

    subgraph 3D Anatomical Processing
        K[BodyParts3D OBJ Models] --> L[Mesh Extraction & Normalization<br/>LAD, LCX, RCA, Myocardium]
        L --> M[Three.js BufferGeometry Payload]
        M --> I
    end

    subgraph Frontend Application [React + Vite + TypeScript + Tailwind]
        I --> N[Clinical Input Dashboard]
        I --> O[Calibrated Risk Gauges]
        I --> P[Three.js Interactive 3D Heart]
        I --> Q[SHAP Contribution Waterfall]
        I --> R[10-Fold CV Benchmark Modal]
    end
```

---

## 3. Machine Learning Performance (Stratified 10-Fold CV)

All metrics were computed across 10 stratified folds on the full 303-patient cohort without data leakage:

| Target Territory | Best Model | ROC-AUC | F1 Score | Accuracy | Primary Clinical Biomarkers |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **Overall CAD (Cath)** | **Soft-Voting Ensemble** | **93.2%** | **91.1%** | **87.1%** | Typical Chest Pain, Echo EF, Age, Region RWMA |
| **LAD Stenosis** | **Extra Trees / CatBoost** | **85.3%** | **84.6%** | **81.2%** | Typical Angina, ST Elevation, Regional RWMA |
| **LCX Stenosis** | **Soft-Voting Ensemble** | **74.2%** | **59.0%** | **70.3%** | Function Class, Age, LDL/HDL Ratio, Dyspnea |
| **RCA Stenosis** | **Extra Trees / Ensemble** | **71.7%** | **53.4%** | **66.3%** | BP, ST Depression, T-Inversion, Dyslipidemia |

---

## 4. 3D Anatomical Vessel Color Standards

Risk probabilities are converted to standardized color states in the 3D Three.js anatomical canvas:

- **Green (`#10B981`)**: Probability $< 35\%$ — Normal / Low Stenosis Likelihood
- **Amber (`#F59E0B`)**: $35\% \le$ Probability $< 65\%$ — Borderline / Intermediate Risk
- **Red (`#EF4444`)**: Probability $\ge 65\%$ — Significant Stenosis Likelihood

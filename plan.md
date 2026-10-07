# CardioVision AI - Machine Learning Prediction Pipeline
## Technical Design Plan (plan.md)

**Project:** Cardiovascular Risk Visualization & Prediction
**Dataset:** Extension of Z-Alizadeh Sani Dataset (303 Patients)
**Version:** 1.0

---

# 1. Objective

Build a clinically interpretable multi-task machine learning system capable of predicting:

1. Overall Coronary Artery Disease (CAD)
2. LAD Stenosis
3. LCX Stenosis
4. RCA Stenosis

using demographic, clinical, laboratory, ECG, and echocardiographic features while excluding target leakage variables.

The final model must provide:

- High predictive accuracy
- Probability outputs
- Clinical explainability (SHAP)
- Fast inference
- Reliability on small medical datasets
- Easy deployment with FastAPI

---

# 2. Dataset Characteristics

## Number of Samples

Approximately 303 patients

## Data Type

Mixed tabular medical dataset

Contains

- Numerical variables
- Binary variables
- Categorical variables

No images.

No signals.

No time-series.

---

# 3. Dataset Challenges

The dataset presents several common issues found in clinical datasets:

- Small sample size
- Mixed feature types
- Potential class imbalance
- Correlated medical variables
- High feature interaction
- Risk of overfitting
- Requirement for model interpretability

Therefore, algorithms that perform well on structured/tabular medical data are preferred over deep learning.

---

# 4. Machine Learning Tasks

## Task 1

Predict

CAD

Type

Binary Classification

Output

Healthy / CAD

---

## Task 2

Predict

LAD Stenosis

Binary Classification

---

## Task 3

Predict

LCX Stenosis

Binary Classification

---

## Task 4

Predict

RCA Stenosis

Binary Classification

---

# 5. Input Features

Allowed Inputs

- Demographics
- Symptoms
- Clinical Examination
- Vital Signs
- Laboratory Results
- ECG Findings
- Echocardiography

Do NOT use

- CAD
- LAD
- LCX
- RCA
- Cath

These are target variables and would cause target leakage.

---

# 6. Recommended Pipeline

```
Raw Dataset
      │
      ▼
Data Cleaning
      │
      ▼
Missing Value Handling
      │
      ▼
Categorical Encoding
      │
      ▼
Feature Scaling
      │
      ▼
Feature Engineering
      │
      ▼
Feature Selection
      │
      ▼
Cross Validation
      │
      ▼
Model Training
      │
      ▼
Hyperparameter Optimization
      │
      ▼
Model Evaluation
      │
      ▼
Probability Calibration
      │
      ▼
SHAP Explanation
      │
      ▼
FastAPI Deployment
```

---

# 7. Data Preprocessing

## Missing Values

Numerical

Median Imputation

Categorical

Mode Imputation

Reason

Medical datasets usually contain missing observations.

Median is robust against outliers.

---

## Duplicate Removal

Remove duplicated records.

---

## Outlier Handling

Detect using

- IQR
- Isolation Forest

Do NOT aggressively remove clinical outliers because they may represent true disease.

---

## Encoding

Binary

Label Encoding

Categorical

One-Hot Encoding

---

## Feature Scaling

Required for

- Logistic Regression
- SVM
- Neural Networks

Scaler

StandardScaler

Tree models do not require scaling.

---

# 8. Feature Engineering

Create clinically meaningful features.

Examples

## Blood Pressure Features

Pulse Pressure

MAP

---

## Cholesterol Features

LDL / HDL Ratio

Total Cholesterol Ratio

---

## Obesity Features

BMI

BMI Categories

---

## ECG Features

ECG Abnormality Score

Combine

- ST Elevation
- T inversion
- LVH

---

## Metabolic Features

Combine

- Diabetes
- Cholesterol
- Triglycerides

into one metabolic risk score.

---

## Lifestyle Features

Smoking

Family History

Hypertension

Create Lifestyle Risk Index.

---

# 9. Feature Selection

Use multiple methods.

## Method 1

Mutual Information

---

## Method 2

ANOVA F-test

---

## Method 3

Recursive Feature Elimination

---

## Method 4

Tree Feature Importance

---

## Method 5

SHAP Importance

Final features should be selected using medical relevance plus statistical importance.

---

# 10. Model Candidates

## Model 1

Logistic Regression

Advantages

- Very interpretable
- Clinical baseline
- Fast

Expected Accuracy

75–85%

Use as baseline only.

---

## Model 2

Decision Tree

Advantages

Easy interpretation

Cons

High overfitting

Expected Accuracy

75–85%

---

## Model 3

Random Forest ⭐⭐⭐⭐

Advantages

Excellent on tabular medical data

Handles nonlinear relationships

Feature importance

Robust

Expected Accuracy

85–92%

Recommended

YES

---

## Model 4

Extra Trees ⭐⭐⭐⭐

Advantages

Lower variance

Fast

Excellent on small datasets

Expected Accuracy

86–93%

Recommended

YES

---

## Model 5

Gradient Boosting

Advantages

Strong performance

Expected Accuracy

87–93%

Recommended

YES

---

## Model 6

XGBoost ⭐⭐⭐⭐⭐

Advantages

Industry standard

Excellent for structured data

Missing value handling

Regularization

Expected Accuracy

90–96%

Recommended

Highly Recommended

---

## Model 7

LightGBM ⭐⭐⭐⭐⭐

Advantages

Very fast

Excellent accuracy

Handles categorical interactions

Expected Accuracy

90–96%

Recommended

Highly Recommended

---

## Model 8

CatBoost ⭐⭐⭐⭐⭐

Advantages

Excellent for categorical medical datasets

Minimal preprocessing

Stable

Expected Accuracy

91–97%

Recommended

Highly Recommended

---

## Model 9

Support Vector Machine

Advantages

Works well on small datasets

Disadvantages

Slow tuning

Poor explainability

Expected Accuracy

86–92%

Recommended

Optional

---

## Model 10

Neural Network

Dataset too small.

High risk of overfitting.

Not recommended.

---

# 11. Final Recommended Models

Priority

1. CatBoost
2. XGBoost
3. LightGBM
4. Random Forest
5. Extra Trees

These five models should be benchmarked.

---

# 12. Ensemble Strategy

Final production model

```
CatBoost
      │
XGBoost
      │
LightGBM
      │
Random Forest
      │
Extra Trees
      │
Voting Classifier
      │
Probability Averaging
      │
Final Prediction
```

Soft voting is preferred to preserve probability estimates.

---

# 13. Cross Validation

Use

Stratified K-Fold

```
K = 10
```

Maintains class distribution.

Avoid simple train-test splits.

---

# 14. Hyperparameter Optimization

Preferred

Optuna

Alternative

Randomized Search

Avoid exhaustive Grid Search due to computational cost.

Optimize:

- Tree depth
- Learning rate
- Number of estimators
- Minimum samples
- Regularization
- Feature fraction
- Subsample ratio

---

# 15. Class Imbalance

Check distribution first.

If imbalance exists

Use

- Class Weight
- SMOTE (training only)
- Balanced Random Forest

Never oversample the test set.

---

# 16. Evaluation Metrics

Primary

- ROC-AUC
- F1 Score

Secondary

- Accuracy
- Precision
- Recall
- Specificity
- MCC
- PR-AUC

Clinical evaluation should prioritize sensitivity and balanced performance rather than accuracy alone.

---

# 17. Explainable AI

Use SHAP.

Display

Global

- Feature Importance
- Summary Plot

Patient-Level

- Force Plot
- Waterfall Plot

Clinical Categories

- Demographics
- ECG
- Laboratory
- Echo
- Symptoms

---

# 18. Probability Calibration

Medical AI requires calibrated probabilities.

Apply

- Platt Scaling
- Isotonic Regression

Output

```
CAD Probability

0–100%
```

instead of only binary predictions.

---

# 19. Multi-Task Prediction Architecture

```
                  Patient Data
                       │
        Feature Engineering Pipeline
                       │
               Shared Preprocessing
                       │
       ┌───────────────┼───────────────┐
       │               │               │
    CAD Model      LAD Model      LCX Model
                                       │
                                  RCA Model
```

Each target is trained independently while sharing the same preprocessing pipeline.

---

# 20. Deployment Pipeline

```
Dataset
    │
Training
    │
Model Selection
    │
SHAP Explainer
    │
Model Serialization (.joblib)
    │
FastAPI
    │
REST API
    │
Frontend Dashboard
    │
3D Heart Visualization
```

---

# 21. Recommended Technology Stack

Training

- Python
- Scikit-learn
- XGBoost
- LightGBM
- CatBoost
- Optuna
- SHAP
- Pandas
- NumPy

Backend

- FastAPI

Visualization

- Plotly
- SHAP
- React
- Three.js

Deployment

- Docker
- Nginx

---

# 22. Development Roadmap

### Phase 1
- Data exploration
- Cleaning
- Feature engineering

### Phase 2
- Baseline models
- Logistic Regression
- Random Forest

### Phase 3
- Boosting models
- XGBoost
- LightGBM
- CatBoost

### Phase 4
- Hyperparameter tuning with Optuna

### Phase 5
- Ensemble learning

### Phase 6
- SHAP explainability

### Phase 7
- FastAPI inference service

### Phase 8
- Dashboard integration

### Phase 9
- 3D anatomical visualization

### Phase 10
- Clinical validation and final testing

---

# 23. Final Recommendation

Considering the dataset size (≈303 records), mixed clinical features, and the requirement for high accuracy, probability estimates, and explainability, **deep neural networks are not the optimal choice**.

The strongest approach is:

- **Primary model:** CatBoost
- **Secondary models:** XGBoost and LightGBM
- **Robust baseline:** Random Forest
- **Production model:** Soft-voting ensemble of CatBoost, XGBoost, LightGBM, Random Forest, and Extra Trees
- **Interpretability:** SHAP
- **Hyperparameter tuning:** Optuna
- **Validation:** Stratified 10-fold cross-validation

This architecture offers an excellent balance of predictive performance, robustness, calibration, and clinical interpretability for a small structured medical dataset.
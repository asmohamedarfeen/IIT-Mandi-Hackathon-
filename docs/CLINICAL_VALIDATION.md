# Clinical Validation & Explainable AI Guide

## 1. Clinical Context & Anatomy

Coronary Artery Disease (CAD) develops through atherosclerotic plaque accumulation within the epicardial coronary arteries. Clinically significant coronary stenosis is defined as $\ge 50\%$ diameter reduction in at least one major vessel during coronary angiography (`Cath`).

The three primary vascular territories evaluated by CardioVision AI are:

1. **Left Anterior Descending (LAD):**
   - Supplies the anterior wall of the left ventricle and anterior interventricular septum.
   - Occlusion carries the highest mortality risk ("the widowmaker").
2. **Left Circumflex Artery (LCX):**
   - Supplies the lateral and posterior left ventricular walls.
3. **Right Coronary Artery (RCA):**
   - Supplies the right ventricle, inferior wall of the left ventricle, and cardiac conduction system (sinoatrial and atrioventricular nodes).

---

## 2. Target Leakage Prevention

In retrospective catheterization cohorts such as the Z-Alizadeh Sani dataset, features directly derived from catheterization findings (`Cath`, `LAD`, `LCX`, `RCA`) represent ground-truth outcomes. 

In CardioVision AI:
- `Cath` (Overall CAD), `LAD`, `LCX`, and `RCA` are strictly quarantined as target training labels.
- The input feature matrix $X$ only contains non-invasive pre-procedural observations: Demographics, Vital Signs, Physical Exam, ECG, Standard Laboratory Biomarkers, and Transthoracic Echocardiography (`EF-TTE`, `Region RWMA`).

---

## 3. TreeSHAP Local & Global Explanations

To satisfy clinical governance standards, black-box predictions are avoided. CardioVision AI employs TreeSHAP (SHapley Additive exPlanations):

$$f(x) = \phi_0 + \sum_{i=1}^{M} \phi_i(x)$$

Where:
- $\phi_0$ is the baseline expected log-odds across the patient population.
- $\phi_i(x)$ is the exact marginal attribution of patient feature $i$.
- $\phi_i > 0$ increases the predicted probability of stenosis.
- $\phi_i < 0$ acts protectively, decreasing predicted probability of stenosis.

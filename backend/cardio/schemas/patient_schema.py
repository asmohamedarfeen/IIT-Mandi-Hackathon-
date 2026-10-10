"""
Pydantic schemas for patient clinical data input and validation.
"""

from typing import Optional, Dict, Any, Union, Literal
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
from backend.cardio.constants import CATEGORY_CODES, encode_category


class PatientInputSchema(BaseModel):
    """
    Comprehensive patient clinical parameter schema for cardiovascular prediction.
    Features are strictly partitioned into demographic, physical, lab, ECG, and symptomatic domains.
    Accepts both standard text codes ('Y'/'N', 'Male'/'Female') and numerical encodings (1/0).
    """
    patient_id: Optional[str] = Field("PATIENT-001", description="De-identified patient ID")

    assessment_mode: Literal["demo", "reviewed"] = "demo"
    confirmed_measurements: list[str] = Field(default_factory=list)
    input_sources: Dict[str, Literal["supplied", "defaulted", "calculated", "unknown"]] = Field(default_factory=dict)

    # Demographics & Body Metrics
    Age: int = Field(55, ge=18, le=120, description="Age in years")
    Sex: Union[str, int, float] = Field("Male", description="Biological sex ('Male'/'Female' or 1/0)")
    Weight: float = Field(72.0, ge=30.0, le=250.0, description="Weight in kg")
    Length: float = Field(170.0, ge=100.0, le=220.0, description="Height/Length in cm")
    BMI: Optional[float] = Field(None, gt=0, description="Body Mass Index (computed if omitted)")

    # Medical History & Risk Factors
    DM: Union[int, float] = Field(0, description="Diabetes Mellitus (0=No, 1=Yes)")
    HTN: Union[int, float] = Field(0, description="Hypertension (0=No, 1=Yes)")
    Current_Smoker: Union[int, float] = Field(0, alias="Current Smoker", description="Current smoker (0=No, 1=Yes)")
    EX_Smoker: Union[int, float] = Field(0, alias="EX-Smoker", description="Ex-smoker (0=No, 1=Yes)")
    FH: Union[int, float] = Field(0, description="Family History of CAD (0=No, 1=Yes)")
    Obesity: Union[str, int, float] = Field("N", description="'Y'/'N' or 1/0")
    CRF: Union[str, int, float] = Field("N", description="Chronic Renal Failure ('Y'/'N' or 1/0)")
    CVA: Union[str, int, float] = Field("N", description="Cerebrovascular Accident ('Y'/'N' or 1/0)")
    Airway_disease: Union[str, int, float] = Field("N", alias="Airway disease", description="Airway disease ('Y'/'N' or 1/0)")
    Thyroid_Disease: Union[str, int, float] = Field("N", alias="Thyroid Disease", description="Thyroid disease ('Y'/'N' or 1/0)")
    CHF: Union[str, int, float] = Field("N", description="Congestive Heart Failure ('Y'/'N' or 1/0)")
    DLP: Union[str, int, float] = Field("N", description="Dyslipidemia ('Y'/'N' or 1/0)")

    # Vitals & Physical Examination
    BP: int = Field(120, ge=70, le=240, description="Systolic Blood Pressure (mmHg)")
    PR: int = Field(75, ge=40, le=180, description="Pulse Rate (bpm)")
    Edema: Union[int, float] = Field(0, description="Peripheral Edema (0=No, 1=Yes)")
    Weak_Peripheral_Pulse: Union[str, int, float] = Field("N", alias="Weak Peripheral Pulse", description="'Y'/'N' or 1/0")
    Lung_rales: Union[str, int, float] = Field("N", alias="Lung rales", description="'Y'/'N' or 1/0")
    Systolic_Murmur: Union[str, int, float] = Field("N", alias="Systolic Murmur", description="'Y'/'N' or 1/0")
    Diastolic_Murmur: Union[str, int, float] = Field("N", alias="Diastolic Murmur", description="'Y'/'N' or 1/0")

    # Symptoms
    Typical_Chest_Pain: Union[int, float] = Field(0, alias="Typical Chest Pain", description="0=No, 1=Yes")
    Dyspnea: Union[str, int, float] = Field("N", description="'Y'/'N' or 1/0")
    Function_Class: Union[int, float] = Field(0, alias="Function Class", description="NYHA Function Class 0-4")
    Atypical: Union[str, int, float] = Field("N", description="Atypical chest pain ('Y'/'N' or 1/0)")
    Nonanginal: Union[str, int, float] = Field("N", description="Non-anginal chest pain ('Y'/'N' or 1/0)")
    Exertional_CP: Union[str, int, float] = Field("N", alias="Exertional CP", description="'Y'/'N' or 1/0")
    LowTH_Ang: Union[str, int, float] = Field("N", alias="LowTH Ang", description="'Y'/'N' or 1/0")

    # ECG & Cardiac Conduction
    Q_Wave: Union[int, float] = Field(0, alias="Q Wave", description="Pathologic Q wave (0/1)")
    St_Elevation: Union[int, float] = Field(0, alias="St Elevation", description="ST Elevation (0/1)")
    St_Depression: Union[int, float] = Field(0, alias="St Depression", description="ST Depression (0/1)")
    Tinversion: Union[int, float] = Field(0, description="T wave inversion (0/1)")
    LVH: Union[str, int, float] = Field("N", description="Left Ventricular Hypertrophy ('Y'/'N' or 1/0)")
    Poor_R_Progression: Union[str, int, float] = Field("N", alias="Poor R Progression", description="'Y'/'N' or 1/0)")
    BBB: Union[str, int, float] = Field("N", description="Bundle Branch Block ('N', 'LBBB', 'RBBB' or 0/1/2)")

    # Laboratory Biomarkers
    FBS: float = Field(90.0, ge=50.0, le=500.0, description="Fasting Blood Sugar (mg/dL)")
    CR: float = Field(0.9, ge=0.2, le=15.0, description="Serum Creatinine (mg/dL)")
    TG: float = Field(130.0, ge=30.0, le=1000.0, description="Triglycerides (mg/dL)")
    LDL: float = Field(100.0, ge=20.0, le=400.0, description="LDL Cholesterol (mg/dL)")
    HDL: float = Field(45.0, ge=10.0, le=120.0, description="HDL Cholesterol (mg/dL)")
    BUN: float = Field(15.0, ge=2.0, le=150.0, description="Blood Urea Nitrogen (mg/dL)")
    ESR: float = Field(12.0, ge=1.0, le=120.0, description="Erythrocyte Sedimentation Rate")
    HB: float = Field(14.0, ge=5.0, le=22.0, description="Hemoglobin (g/dL)")
    K: float = Field(4.2, ge=2.0, le=8.0, description="Serum Potassium (mEq/L)")
    Na: float = Field(140.0, ge=110.0, le=165.0, description="Serum Sodium (mEq/L)")
    WBC: float = Field(6500.0, ge=1000.0, le=40000.0, description="White Blood Cell count")
    Lymph: float = Field(30.0, ge=1.0, le=90.0, description="Lymphocyte percentage")
    Neut: float = Field(60.0, ge=1.0, le=95.0, description="Neutrophil percentage")
    PLT: float = Field(220.0, ge=20.0, le=900.0, description="Platelets (1000/uL)")

    # Echocardiography
    EF_TTE: float = Field(55.0, ge=10.0, le=80.0, alias="EF-TTE", description="Ejection Fraction (%)")
    Region_RWMA: Union[int, float] = Field(0, alias="Region RWMA", description="Regional Wall Motion Abnormality score")
    VHD: Union[str, int, float] = Field("N", description="Valvular Heart Disease ('N', 'mild', 'Moderate', 'Severe' or 0/1/2/3)")

    model_config = ConfigDict(populate_by_name=True, extra="ignore", allow_inf_nan=False, validate_default=True)

    @field_validator("*", mode="before")
    @classmethod
    def validate_categories(cls, value, info):
        field = cls.model_fields[info.field_name]
        name = field.alias or info.field_name
        return encode_category(value, name) if name in CATEGORY_CODES else value

    @model_validator(mode="after")
    def validate_reviewed_measurements(self):
        metadata = {"patient_id", "assessment_mode", "confirmed_measurements", "input_sources"}
        aliases = {name: field.alias or name for name, field in type(self).model_fields.items() if name not in metadata}
        allowed = set(aliases.values())
        unknown = (set(self.confirmed_measurements) | set(self.input_sources)) - allowed
        if unknown:
            raise ValueError("Unknown measurement: " + ", ".join(sorted(unknown)))
        supplied = {aliases[name] for name in self.model_fields_set if name in aliases}
        if self.assessment_mode == "reviewed":
            required = allowed - {"BMI", "Exertional CP"}
            if self.BMI is not None and self.input_sources.get("BMI", "supplied") != "calculated":
                required.add("BMI")
            missing = sorted(key for key in required if key not in supplied or key not in self.confirmed_measurements or self.input_sources.get(key, "supplied") != "supplied")
            if missing:
                raise ValueError("Reviewed case requires explicitly supplied and confirmed measurements: " + ", ".join(missing))
        return self

    def input_provenance(self) -> Dict[str, Any]:
        metadata = {"patient_id", "assessment_mode", "confirmed_measurements", "input_sources"}
        measurements = {}
        for name, field in type(self).model_fields.items():
            if name in metadata:
                continue
            key = field.alias or name
            source = self.input_sources.get(key, "supplied" if name in self.model_fields_set else "defaulted")
            if key == "BMI" and (name not in self.model_fields_set or "BMI" not in self.input_sources and self.BMI is None):
                source = "calculated"
            measurements[key] = {"source": source, "confirmed": key in self.confirmed_measurements, "value": getattr(self, name), "modeled": key != "Exertional CP"}
        return {"assessment_mode": self.assessment_mode, "measurements": measurements}

    @model_validator(mode="after")
    def compute_missing_bmi(self):
        if self.BMI is None or self.input_sources.get("BMI") == "calculated":
            self.input_sources["BMI"] = "calculated"
            self.BMI = self.Weight / (self.Length / 100.0) ** 2
        return self


class SamplePatientItem(BaseModel):
    patient_id: str
    ground_truth: Dict[str, str]
    features: Dict[str, Any]

import type { PatientData, SamplePatient } from "./types";
export const DEFAULT_PATIENT: PatientData = {
  patient_id: "",
  Age: 55,
  Sex: "Male",
  Weight: 72,
  Length: 170,
  BMI: 24.9,
  DM: 0,
  HTN: 0,
  "Current Smoker": 0,
  "EX-Smoker": 0,
  FH: 0,
  Obesity: "N",
  CRF: "N",
  CVA: "N",
  "Airway disease": "N",
  "Thyroid Disease": "N",
  CHF: "N",
  DLP: "N",
  BP: 120,
  PR: 75,
  Edema: 0,
  "Weak Peripheral Pulse": "N",
  "Lung rales": "N",
  "Systolic Murmur": "N",
  "Diastolic Murmur": "N",
  "Typical Chest Pain": 0,
  Dyspnea: "N",
  "Function Class": 0,
  Atypical: "N",
  Nonanginal: "N",
  "Exertional CP": "N",
  "LowTH Ang": "N",
  "Q Wave": 0,
  "St Elevation": 0,
  "St Depression": 0,
  Tinversion: 0,
  LVH: "N",
  "Poor R Progression": "N",
  BBB: "N",
  FBS: 90,
  CR: 0.9,
  TG: 130,
  LDL: 100,
  HDL: 45,
  BUN: 15,
  ESR: 12,
  HB: 14,
  K: 4.2,
  Na: 140,
  WBC: 6500,
  Lymph: 30,
  Neut: 60,
  PLT: 220,
  "EF-TTE": 55,
  "Region RWMA": 0,
  VHD: "N",
};

export type Field = {
  key: keyof PatientData;
  label: string;
  unit?: string;
  min?: number;
  max?: number;
  step?: string;
  options?: string[];
};
const yesNo = ["No", "Yes"];
const binary = (key: keyof PatientData, label: string = key): Field => ({
  key,
  label,
  options: yesNo,
});
const number = (
  key: keyof PatientData,
  label: string,
  unit: string,
  min: number,
  max: number,
  step = "any",
): Field => ({ key, label, unit, min, max, step });
export const FIELD_GROUPS: { title: string; fields: Field[] }[] = [
  {
    title: "Patient profile",
    fields: [
      number("Age", "Age", "years", 18, 120, "1"),
      { key: "Sex", label: "Biological sex", options: ["Female", "Male"] },
      number("Weight", "Weight", "kg", 30, 250),
      number("Length", "Height", "cm", 100, 220),
    ],
  },
  {
    title: "History & risk factors",
    fields: [
      binary("DM", "Diabetes"),
      binary("HTN", "Hypertension"),
      binary("Current Smoker"),
      binary("EX-Smoker", "Former smoker"),
      binary("FH", "Family history of CAD"),
      binary("Obesity"),
      binary("CRF", "Chronic renal failure"),
      binary("CVA", "Cerebrovascular accident"),
      binary("Airway disease"),
      binary("Thyroid Disease"),
      binary("CHF", "Congestive heart failure"),
      binary("DLP", "Dyslipidemia"),
    ],
  },
  {
    title: "Vitals & examination",
    fields: [
      number("BP", "Systolic pressure", "mmHg", 70, 240, "1"),
      number("PR", "Pulse rate", "bpm", 40, 180, "1"),
      binary("Edema"),
      binary("Weak Peripheral Pulse"),
      binary("Lung rales"),
      binary("Systolic Murmur"),
      binary("Diastolic Murmur"),
    ],
  },
  {
    title: "Symptoms",
    fields: [
      binary("Typical Chest Pain"),
      binary("Dyspnea"),
      {
        key: "Function Class",
        label: "Function class",
        options: ["0", "I", "II", "III", "IV"],
      },
      binary("Atypical", "Atypical chest pain"),
      binary("Nonanginal", "Nonanginal discomfort"),
      binary("Exertional CP", "Exertional chest pain"),
      binary("LowTH Ang", "Low-threshold angina"),
    ],
  },
  {
    title: "ECG findings",
    fields: [
      binary("Q Wave"),
      binary("St Elevation", "ST elevation"),
      binary("St Depression", "ST depression"),
      binary("Tinversion", "T-wave inversion"),
      binary("LVH", "Left ventricular hypertrophy"),
      binary("Poor R Progression"),
      {
        key: "BBB",
        label: "Bundle branch block",
        options: ["None", "LBBB", "RBBB"],
      },
    ],
  },
  {
    title: "Laboratory & echo",
    fields: [
      number("FBS", "Fasting glucose", "mg/dL", 50, 500),
      number("CR", "Creatinine", "mg/dL", 0.2, 15),
      number("TG", "Triglycerides", "mg/dL", 30, 1000),
      number("LDL", "LDL", "mg/dL", 20, 400),
      number("HDL", "HDL", "mg/dL", 10, 120),
      number("BUN", "Blood urea nitrogen", "mg/dL", 2, 150),
      number("ESR", "Sedimentation rate", "mm/h", 1, 120),
      number("HB", "Hemoglobin", "g/dL", 5, 22),
      number("K", "Potassium", "mEq/L", 2, 8),
      number("Na", "Sodium", "mEq/L", 110, 165),
      number("WBC", "White blood cells", "/µL", 1000, 40000),
      number("Lymph", "Lymphocytes", "%", 1, 90),
      number("Neut", "Neutrophils", "%", 1, 95),
      number("PLT", "Platelets", "10³/µL", 20, 900),
      number("EF-TTE", "Ejection fraction", "%", 10, 80),
      {
        key: "Region RWMA",
        label: "Regional wall motion score",
        options: ["0", "1", "2", "3", "4"],
      },
      {
        key: "VHD",
        label: "Valvular heart disease",
        options: ["None", "Mild", "Moderate", "Severe"],
      },
    ],
  },
];
export function normalizePatient(
  raw: Partial<PatientData> | Record<string, unknown>,
  id = "",
): PatientData {
  const output: Record<string, unknown> = {
    ...DEFAULT_PATIENT,
    patient_id: id,
  };
  for (const { fields } of FIELD_GROUPS)
    for (const field of fields) {
      // Sample responses also contain engineered features; send only raw inputs.
      const value = raw[field.key] ?? output[field.key];
      if (field.options) {
        const labels: Record<string, number> = {
          n: 0,
          y: 1,
          no: 0,
          yes: 1,
          male: 1,
          female: 0,
          fmale: 0,
          lbbb: 1,
          rbbb: 2,
          mild: 1,
          moderate: 2,
          severe: 3,
        };
        const text = String(value).trim().toLowerCase();
        const option = field.options.findIndex(
          (label) => label.toLowerCase() === text,
        );
        output[field.key] =
          option >= 0 ? option : (labels[text] ?? Number(value));
      } else output[field.key] = Number(value);
    }
  output.BMI =
    raw.BMI != null
      ? Number(raw.BMI)
      : Number(output.Weight) / (Number(output.Length) / 100) ** 2;
  return output as unknown as PatientData;
}
export function updatePatient(
  patient: PatientData,
  key: keyof PatientData,
  value: string | number,
): PatientData {
  const next = { ...patient, [key]: value };
  if (key === "Weight" || key === "Length")
    next.BMI = next.Weight / (next.Length / 100) ** 2;
  return next;
}
export function sampleVessels(sample: SamplePatient): string {
  return (
    (["LAD", "LCX", "RCA"] as const)
      .filter((key) =>
        ["1", "stenotic", "positive", "yes"].includes(
          String(sample.ground_truth[key]).toLowerCase(),
        ),
      )
      .join(" + ") || "See recorded labels"
  );
}

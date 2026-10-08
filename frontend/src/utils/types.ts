/**
 * Type definitions for CardioVision AI client-side state and API payloads.
 */

export interface PatientData {
  patient_id?: string;
  Age: number;
  Sex: string | number;
  Weight: number;
  Length: number;
  BMI?: number;
  DM: number;
  HTN: number;
  "Current Smoker": number;
  "EX-Smoker": number;
  FH: number;
  Obesity: string | number;
  CRF: string | number;
  CVA: string | number;
  "Airway disease": string | number;
  "Thyroid Disease": string | number;
  CHF: string | number;
  DLP: string | number;
  BP: number;
  PR: number;
  Edema: number;
  "Weak Peripheral Pulse": string | number;
  "Lung rales": string | number;
  "Systolic Murmur": string | number;
  "Diastolic Murmur": string | number;
  "Typical Chest Pain": number;
  Dyspnea: string | number;
  "Function Class": number;
  Atypical: string | number;
  Nonanginal: string | number;
  "Exertional CP": string | number;
  "LowTH Ang": string | number;
  "Q Wave": number;
  "St Elevation": number;
  "St Depression": number;
  Tinversion: number;
  LVH: string | number;
  "Poor R Progression": string | number;
  BBB: string | number;
  FBS: number;
  CR: number;
  TG: number;
  LDL: number;
  HDL: number;
  BUN: number;
  ESR: number;
  HB: number;
  K: number;
  Na: number;
  WBC: number;
  Lymph: number;
  Neut: number;
  PLT: number;
  "EF-TTE": number;
  "Region RWMA": number;
  VHD: string | number;
}

export interface VesselRiskInfo {
  vessel: string;
  probability: number;
  probability_percent: number;
  risk_level: string;
  color_hex: string;
  anatomical_description: string;
}

export interface SHAPFeatureImpact {
  feature: string;
  display_name: string;
  contribution: number;
  patient_value: any;
  impact_direction: "increases_risk" | "decreases_risk";
}

export interface PredictionResponse {
  patient_id: string;
  overall_cad: VesselRiskInfo;
  vessels: {
    LAD: VesselRiskInfo;
    LCX: VesselRiskInfo;
    RCA: VesselRiskInfo;
  };
  vessel_colors_3d: {
    lad: string;
    lcx: string;
    rca: string;
    myocardium: string;
  };
  shap_explanations: {
    CAD: SHAPFeatureImpact[];
    LAD: SHAPFeatureImpact[];
    LCX: SHAPFeatureImpact[];
    RCA: SHAPFeatureImpact[];
  };
  disclaimer: string;
}

export interface SamplePatient {
  patient_id: string;
  ground_truth: {
    CAD: string;
    LAD: string;
    LCX: string;
    RCA: string;
  };
  features: Record<string, any>;
}

export interface ModelCVMetrics {
  accuracy: number;
  precision: number;
  recall: number;
  f1: number;
  roc_auc: number;
  specificity: number;
  mcc: number;
}

export interface BenchmarkData {
  targets: Record<string, Record<string, ModelCVMetrics>>;
  global_importances: Record<
    string,
    Array<{ feature: string; importance: number; mean_val: number }>
  >;
}

export interface ThreeDStructureData {
  positions: number[];
  indices: number[];
  vertex_count: number;
  face_count: number;
}

export interface ThreeDAnatomyPayload {
  metadata: {
    scale: number;
    center: number[];
  };
  structures: {
    lad: ThreeDStructureData;
    lcx: ThreeDStructureData;
    rca: ThreeDStructureData;
    myocardium: ThreeDStructureData;
    left_main?: ThreeDStructureData;
  };
}

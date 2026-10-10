export type QualityTarget = "CAD" | "LAD" | "LCX" | "RCA";
export type ReportFormat = "pdf" | "csv" | "json";
export type ReportSection = "metrics" | "results" | "confusion-matrices" | "calibration" | "roc" | "pr" | "shap" | "feature-stability" | "thresholds" | "histogram" | "class-distribution" | "reproducibility";
export interface QualityReportRequest { format: ReportFormat; section: ReportSection; target?: QualityTarget; model?: string; models?: string[]; threshold?: number; expected_run_id?: string; }
export interface Counts { positive: number; negative: number; total: number; }
export interface ThresholdPoint { threshold: number; tn: number; fp: number; fn: number; tp: number; precision?: number | null; recall?: number | null; sensitivity?: number | null; specificity?: number | null; f1?: number | null; }
export interface CalibrationBin { lower: number; upper: number; count: number; mean_probability: number | null; fraction_positive: number | null; }
export interface ModelResult {
  metrics: Record<string, number | null>;
  undefined_metrics: Record<string, string>;
  fold_metrics: Array<Record<string, number | null>>;
  diagnostics: {
    confusion_matrix: ThresholdPoint;
    calibration: CalibrationBin[];
    probability_histogram?: Array<{ lower: number; upper: number; count: number }>;
    roc: { fpr: number[]; tpr: number[]; thresholds: Array<number | null> };
    pr: { precision: number[]; recall: number[]; thresholds: number[] };
    thresholds: ThresholdPoint[];
  };
}
export interface Stability {
  model: string; method: string;
  features: Array<{feature: string; mean: number; std: number; top_k_frequency: number; fold_values: number[]; rank_mean: number; rank_std: number}>;
  mean_rank_correlation: number | null; mean_top_k_jaccard: number | null;
}
export interface TargetQuality {
  production_configuration?: {name:string;decision_threshold:number;calibration_method:string;calibration_folds:number};
  class_distribution: Counts;
  folds: Array<{fold: number; train: Counts; test: Counts}>;
  models: Record<string, ModelResult>;
  feature_stability: Stability;
  shap_stability: Stability;
}
export interface ModelQualityOverview {
  schema_version: number; run_id: string; generated_at: string; selected_model: string; stale: boolean; status: "ready" | "stale";
  provenance: {dataset_sha256?: string; model_sha256?: string; command?: string; random_seed?: number; outer_folds?: number; inner_folds?: number; [key:string]: unknown};
  data_quality: { rows: number; missing_values: Record<string, number>; duplicates: number; leakage_checks: Array<{check:string;passed:boolean;detail:string}> };
  models: Array<{id:string;name:string;production_configuration:boolean;configuration_source:string;parameters:unknown}>;
  targets: Partial<Record<QualityTarget, TargetQuality>>;
  limitations: string[];
  supplied_benchmarks?: {evaluation?:unknown;targets: Record<string, Record<string, Record<string, number | null>>>};
}
export interface PlotSeries { name: string; points: Array<{x: number; y: number}>; }

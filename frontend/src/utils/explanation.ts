import type { PredictionEvidence, SHAPFeatureImpact } from "./types";
import { FIELD_GROUPS } from "./patient.ts";
import { formatMeasurement } from "./evidence.ts";

export function measurementLabel(key: string) {
  if (key === "BMI") return "BMI";
  return FIELD_GROUPS.flatMap(group => group.fields).find(field => field.key === key)?.label;
}

export function rankedFactors(items: SHAPFeatureImpact[] = []) {
  return [...items].filter(item => Number.isFinite(item.contribution))
    .sort((a, b) => Math.abs(b.contribution) - Math.abs(a.contribution));
}

export function factorDirection(value: number) {
  return value > 0 ? "Increases explanation-model output" : value < 0 ? "Decreases explanation-model output" : "No change in explanation-model output";
}

export function factorSources(item: SHAPFeatureImpact, evidence?: PredictionEvidence) {
  const inputs = evidence?.clinical_inputs;
  if (!inputs) return [];
  const keys = item.source_measurements?.length
    ? item.source_measurements.map(source => source.input_key)
    : measurementLabel(item.feature) && item.feature_kind !== "derived" && item.feature_kind !== "unmapped" ? [item.feature] : [];
  return [...new Set(keys)].flatMap(key => {
    const label = measurementLabel(key);
    const recorded_value = inputs[key];
    if (!label || !Object.prototype.hasOwnProperty.call(inputs, key) || recorded_value == null) return [];
    return [{ input_key: key, recorded_value, label, formatted_value: formatMeasurement(key, recorded_value) }];
  });
}

export function formatModelValue(value: unknown) {
  return typeof value === "number" && Number.isFinite(value) ? String(Number(value.toPrecision(6))) : "Unavailable";
}

export function factorValue(item: SHAPFeatureImpact, evidence?: PredictionEvidence) {
  if (item.feature_kind === "derived") return `Calculated value ${formatModelValue(item.model_input_value ?? item.patient_value)}`;
  if (measurementLabel(item.feature) && item.feature_kind !== "unmapped") {
    const value = evidence?.clinical_inputs[item.feature];
    return value == null ? "Recorded value unavailable" : formatMeasurement(item.feature, value);
  }
  return `Model feature value ${formatModelValue(item.model_input_value ?? item.patient_value)}`;
}

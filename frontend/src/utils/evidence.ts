import type { PredictionResponse, Vessel, CoronaryTarget } from "./types";
import { FIELD_GROUPS } from "./patient.ts";

export function vesselEvidence(prediction: PredictionResponse | null, selected: Vessel | null, stale: boolean) {
  if (!prediction || !selected || stale) return null;
  const target = selected.toUpperCase() as CoronaryTarget;
  const risk = prediction.vessels[target];
  if (!risk) return null;
  return {
    target,
    risk,
    meshColor: prediction.vessel_colors_3d[selected],
    factors: [...(prediction.shap_explanations[target] || [])]
      .filter(item => Number.isFinite(item.contribution))
      .sort((a, b) => Math.abs(b.contribution) - Math.abs(a.contribution)),
    context: prediction.evidence,
  };
}

export function formatMeasurement(key: string, value: unknown): string {
  if (value == null || (typeof value === "number" && !Number.isFinite(value))) return "Unavailable";
  if (key === "BMI") return `${Number(value).toFixed(1)} kg/m²`;
  const field = FIELD_GROUPS.flatMap(group => group.fields).find(field => field.key === key);
  if (field?.options) return field.options[Number(value)] ?? String(value);
  return `${value}${field?.unit ? ` ${field.unit}` : ""}`;
}

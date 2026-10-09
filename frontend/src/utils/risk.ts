import type { PredictionResponse, SHAPFeatureImpact } from "./types";

export function riskBand(percent?: number) {
  if (percent === undefined || !Number.isFinite(percent) || percent < 0 || percent > 100) return "unknown";
  return percent >= 65 ? "high" : percent >= 35 ? "moderate" : "low";
}

export function rankedVessels(prediction: PredictionResponse | null) {
  if (!prediction) return [];
  return (["lad", "lcx", "rca"] as const)
    .map((key) => ({ key, risk: prediction.vessels[key.toUpperCase() as "LAD" | "LCX" | "RCA"] }))
    .filter(({ risk }) => riskBand(risk?.probability_percent) !== "unknown")
    .sort((first, second) => second.risk.probability_percent - first.risk.probability_percent);
}

export function leadingContributors(features?: SHAPFeatureImpact[]) {
  return (features || [])
    .filter((feature) => Number.isFinite(feature.contribution) && feature.contribution > 0)
    .sort((first, second) => second.contribution - first.contribution)
    .slice(0, 2);
}

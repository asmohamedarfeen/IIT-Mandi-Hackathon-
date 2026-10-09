import { useId } from "react";
import type { VesselRiskInfo, SHAPFeatureImpact } from "../utils/types";
import { leadingContributors, riskBand } from "../utils/risk";

export function VesselDetail({
  name,
  risk,
  contributions,
  stale = false,
}: {
  name: string;
  risk?: VesselRiskInfo;
  contributions?: SHAPFeatureImpact[];
  stale?: boolean;
}) {
  const gradient = useId();
  const band = stale ? "unknown" : riskBand(risk?.probability_percent);
  const factors = stale ? [] : leadingContributors(contributions);
  return (
    <section className="vessel-detail-panel" aria-label={`${name} detail`}>
      <div className="vessel-detail-heading" data-risk={band} aria-live="polite">
        <h3>{name}</h3>
        {stale ? <p>Inputs changed. Run a new assessment.</p> : risk ? (
          <p><strong style={{ color: risk.color_hex }}>{risk.probability_percent.toFixed(1)}%</strong> model risk · {risk.risk_level}</p>
        ) : <p>Run an assessment to see this artery’s risk.</p>}
      </div>
      <p className="vessel-review-note">{band === "high" ? "⚠ High model score — review this artery’s result." : band === "moderate" ? "⚠ Moderate model score — review this artery’s result." : band === "low" ? "Low model score — disease is not ruled out." : "This artery has not been assessed with current inputs."}</p>
      <p className="vessel-factors">{factors.length ? `Leading contributors (surrogate model): ${factors.map((feature) => feature.display_name).join(" · ")}` : "No positive contributing factors available."}</p>
      <svg viewBox="0 0 600 160" role="img" aria-label="Illustrative artery cutaways: an open lumen and a lumen narrowed by plaque. Not patient-specific.">
        <defs>
          <linearGradient id={`${gradient}-wall`} x1="0" y1="0" x2="0" y2="1">
            <stop stopColor="#fa8b77" />
            <stop offset="0.48" stopColor="#762823" />
            <stop offset="1" stopColor="#e67461" />
          </linearGradient>
          <linearGradient id={`${gradient}-plaque`} x1="0" y1="0" x2="0" y2="1">
            <stop stopColor="#f5df9d" />
            <stop offset="1" stopColor="#b69b4e" />
          </linearGradient>
        </defs>
        <text x="140" y="20" textAnchor="middle">Open artery</text>
        <text x="450" y="20" textAnchor="middle">Plaque narrowing</text>
        <path d="M20 50 Q140 40 270 50 L270 130 Q140 120 20 130 Z" fill={`url(#${gradient}-wall)`} stroke="#f0a18c" strokeWidth="2" />
        <path d="M20 63 Q140 53 270 63 L270 117 Q140 107 20 117 Z" fill="#391b1c" />
        <path d="M330 50 Q450 40 580 50 L580 130 Q450 120 330 130 Z" fill={`url(#${gradient}-wall)`} stroke="#f0a18c" strokeWidth="2" />
        <path d="M330 63 Q450 53 580 63 L580 117 Q450 107 330 117 Z" fill="#391b1c" />
        <path d="M345 62 C385 58 405 89 450 87 S512 59 563 62 Q450 50 345 62 Z" fill={`url(#${gradient}-plaque)`} />
        <path d="M345 115 C395 112 415 94 450 96 S510 113 563 115 Q450 105 345 115 Z" fill={`url(#${gradient}-plaque)`} />
        <path d="M65 89 H225 M375 91 H410" stroke="#e7efec" strokeWidth="2" />
        <path d="M215 84 L225 89 L215 94 M400 86 L410 91 L400 96" fill="none" stroke="#e7efec" strokeWidth="2" />
        <text x="140" y="153" textAnchor="middle">Open lumen</text>
        <text x="450" y="153" textAnchor="middle">Plaque in the artery wall</text>
      </svg>
      <p className="vessel-illustration-note">Illustrative comparison · The model does not measure blockage location or percentage.</p>
      <a className="vessel-evidence-link" href="#coronary-evidence">View complete artery evidence ↓</a>
    </section>
  );
}

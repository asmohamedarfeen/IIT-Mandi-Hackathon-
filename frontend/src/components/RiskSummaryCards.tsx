import { PredictionResponse, Vessel } from "../utils/types";
import { riskBand } from "../utils/risk";
export function RiskSummaryCards({
  prediction,
  stale,
  selectedVessel,
  onSelectVessel,
}: {
  prediction: PredictionResponse | null;
  stale: boolean;
  selectedVessel?: Vessel | null;
  onSelectVessel?: (vessel: Vessel) => void;
}) {
  const items = [
    ["CAD", "Overall coronary disease", prediction?.overall_cad],
    ["LAD", "Left anterior descending", prediction?.vessels.LAD],
    ["LCX", "Left circumflex", prediction?.vessels.LCX],
    ["RCA", "Right coronary artery", prediction?.vessels.RCA],
  ] as const;
  return (
    <div className={"risk-grid" + (stale ? " is-stale" : "")}>
      {items.map(([key, label, data]) => (
        <article key={key} className="risk-card" data-risk={stale ? "unknown" : riskBand(data?.probability_percent)}>
          <div className="risk-card-top">
            <h3>{key}</h3>
            <span>
              {data
                ? stale
                  ? "Needs reassessment"
                  : `${riskBand(data.probability_percent) === "high" || riskBand(data.probability_percent) === "moderate" ? "⚠ " : ""}${data.risk_level}`
                : "Awaiting assessment"}
            </span>
          </div>
          <div className="risk-value">
            {data ? data.probability_percent.toFixed(1) : "—"}
            {data && <span>%</span>}
          </div>
          <p>{label}</p>
          <div className="risk-meter">
            <span
              style={{
                width: data ? `${data.probability_percent}%` : "0%",
                background: stale ? "#818779" : data?.color_hex,
              }}
            />
          </div>
          <small>{stale ? "Previous result · reassessment required" : data?.predicted_status ? `Model probability · Predicted status: ${data.predicted_status}` : data ? "Model probability" : "No result yet"}</small>
          {key !== "CAD" && onSelectVessel && <button className="text-button" aria-pressed={selectedVessel === key.toLowerCase()} onClick={() => onSelectVessel(key.toLowerCase() as Vessel)}>Inspect {key} evidence →</button>}
        </article>
      ))}
    </div>
  );
}

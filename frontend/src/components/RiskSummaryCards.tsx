import { PredictionResponse } from "../utils/types";
export function RiskSummaryCards({
  prediction,
  stale,
}: {
  prediction: PredictionResponse | null;
  stale: boolean;
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
        <article key={key} className="risk-card">
          <div className="risk-card-top">
            <h3>{key}</h3>
            <span>
              {data
                ? stale
                  ? "Needs reassessment"
                  : data.risk_level
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
                background: data?.color_hex,
              }}
            />
          </div>
          <small>{data ? "Model probability" : "No result yet"}</small>
        </article>
      ))}
    </div>
  );
}

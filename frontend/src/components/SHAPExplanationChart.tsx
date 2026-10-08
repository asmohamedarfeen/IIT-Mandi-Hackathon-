import { useState } from "react";
import { PredictionResponse } from "../utils/types";
export function SHAPExplanationChart({
  prediction,
  stale,
}: {
  prediction: PredictionResponse | null;
  stale: boolean;
}) {
  const [target, setTarget] = useState<"CAD" | "LAD" | "LCX" | "RCA">("CAD");
  const items = prediction?.shap_explanations[target] || [];
  const max = Math.max(...items.map((i) => Math.abs(i.contribution)), 0.01);
  return (
    <section className="explanation" aria-labelledby="explanation-title">
      <div className="explanation-intro">
        <h2 id="explanation-title">Contributing factors</h2>
        <p>
          SHAP contributions from a separate explanation model, not exact
          explanations of the assessment score.
        </p>
        <div className="shap-legend">
          <span>
            <i />
            Increases model output
          </span>
          <span>
            <i />
            Decreases model output
          </span>
        </div>
      </div>
      <div className="explanation-content">
        <div className="segmented">
          {(["CAD", "LAD", "LCX", "RCA"] as const).map((t) => (
            <button
              key={t}
              aria-pressed={t === target}
              onClick={() => setTarget(t)}
            >
              {t}
            </button>
          ))}
        </div>
        {stale && (
          <p className="stale-note">
            Previous assessment · inputs have changed.
          </p>
        )}
        {items.length ? (
          items.map((item) => (
            <div className="shap-row" key={item.feature}>
              <div>
                <span>{item.display_name}</span>
                <small>Value {String(item.patient_value)}</small>
                <strong
                  className={item.contribution > 0 ? "positive" : "negative"}
                >
                  {item.contribution > 0 ? "+" : ""}
                  {item.contribution.toFixed(3)}
                </strong>
              </div>
              <div className="shap-track">
                <span
                  className={item.contribution > 0 ? "positive" : "negative"}
                  style={{
                    width: `${(Math.abs(item.contribution) / max) * 50}%`,
                    left:
                      item.contribution > 0
                        ? "50%"
                        : `${50 - (Math.abs(item.contribution) / max) * 50}%`,
                  }}
                />
              </div>
            </div>
          ))
        ) : (
          <div className="explanation-empty">
            <p>No explanation available for this target.</p>
          </div>
        )}
      </div>
    </section>
  );
}

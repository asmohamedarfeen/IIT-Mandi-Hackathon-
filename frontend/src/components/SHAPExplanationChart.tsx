import { useEffect, useId, useState } from "react";
import { PredictionResponse } from "../utils/types";
import { factorDirection, factorValue, rankedFactors } from "../utils/explanation";
import { PredictionFactorDetail } from "./PredictionFactorDetail";
export function SHAPExplanationChart({
  prediction,
  stale,
  target: controlledTarget,
  onViewInput,
}: {
  prediction: PredictionResponse | null;
  stale: boolean;
  target?: "CAD" | "LAD" | "LCX" | "RCA";
  onViewInput?: (inputKey: string) => boolean;
}) {
  const titleId = useId();
  const [localTarget, setTarget] = useState<"CAD" | "LAD" | "LCX" | "RCA">("CAD");
  const target = controlledTarget ?? localTarget;
  const [expanded, setExpanded] = useState<{ prediction: PredictionResponse; target: string; feature: string } | null>(null);
  useEffect(() => { setExpanded(null); }, [prediction, prediction?.evidence?.assessment_id, target, stale]);
  const items = stale ? [] : rankedFactors(prediction?.shap_explanations[target]);
  const max = Math.max(...items.map((i) => Math.abs(i.contribution)), 0.01);
  return (
    <section className="explanation" aria-labelledby={titleId}>
      <div className="explanation-intro">
        <h2 id={titleId}>What drives this prediction?</h2>
        <p className="factor-context">{target} contributing factors · {prediction?.patient_id || "Awaiting assessment"}</p>
        <p>
          SHAP contributions from a separate explanation model, not exact
          explanations of the assessment score. Values are in log-odds, not percentage points.
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
        {!controlledTarget && <div className="segmented">
          {(["CAD", "LAD", "LCX", "RCA"] as const).map((t) => (
            <button
              key={t}
              aria-pressed={t === target}
              onClick={() => setTarget(t)}
            >
              {t}
            </button>
          ))}
        </div>}
        {items.length > 0 && <p className="factor-list-note">Up to 8 strongest contributing factors · select a factor to inspect its measurements.</p>}
        {stale && (
          <p className="stale-note">
            Previous assessment · inputs have changed.
          </p>
        )}
        {items.length ? (
          items.map((item, index) => {
            const open = expanded?.prediction === prediction && expanded?.target === target && expanded?.feature === item.feature;
            const detailId = `${titleId}-factor-${index}`;
            return <div className="shap-row" key={item.feature}>
              <button type="button" className="factor-toggle" aria-expanded={open} aria-controls={detailId} onClick={() => setExpanded(open || !prediction ? null : { prediction, target, feature: item.feature })}>
                <span className="factor-rank">{index + 1}</span>
                <span className="factor-name">{item.display_name}<small>{factorValue(item, prediction?.evidence)}</small></span>
                <strong
                  className={item.contribution > 0 ? "positive" : item.contribution < 0 ? "negative" : ""}
                >
                  {item.contribution > 0 ? "+" : ""}
                  {item.contribution.toFixed(4)}<small>log-odds</small>
                </strong>
                <span className="factor-disclosure" aria-hidden="true">{open ? "−" : "+"}</span>
                <span className="factor-direction">{factorDirection(item.contribution)}</span>
              <span className="shap-track" aria-hidden="true">
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
              </span>
              </button>
              {open && <div id={detailId}><PredictionFactorDetail key={`${target}-${item.feature}`} item={item} evidence={prediction?.evidence} onViewInput={onViewInput} /></div>}
            </div>
          })
        ) : (
          <div className="explanation-empty">
            <p>No explanation available for this target.</p>
          </div>
        )}
        {items.length > 0 && !items.some(item => item.contribution < 0) && <p className="factor-list-note">The displayed factors contain no decreasing contributions.</p>}
      </div>
    </section>
  );
}

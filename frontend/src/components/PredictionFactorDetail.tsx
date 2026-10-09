import { useState } from "react";
import type { PredictionEvidence, SHAPFeatureImpact } from "../utils/types";
import { factorDirection, factorSources, factorValue, formatModelValue } from "../utils/explanation";

export function PredictionFactorDetail({ item, evidence, onViewInput }: {
  item: SHAPFeatureImpact;
  evidence?: PredictionEvidence;
  onViewInput?: (inputKey: string) => boolean;
}) {
  const sources = factorSources(item, evidence);
  const [navigationError, setNavigationError] = useState("");
  return (
    <div className="factor-detail">
      <h3>{item.display_name} · assessed evidence</h3>
      <p>{factorDirection(item.contribution)} by <strong>{item.contribution > 0 ? "+" : ""}{item.contribution.toFixed(4)} log-odds</strong> relative to the explanation model’s baseline.</p>
      <dl className="factor-model-values">
        <div><dt>{item.feature_kind === "derived" ? "Calculated feature" : "Assessed value"}</dt><dd>{factorValue(item, evidence)}</dd></div>
        <div><dt>{item.feature_kind === "derived" ? "Model input" : "Model encoding / input"}</dt><dd title={String(item.model_input_value ?? item.patient_value)}>{formatModelValue(item.model_input_value ?? item.patient_value)}</dd></div>
      </dl>
      {item.derivation && <p className="factor-derivation">{item.derivation}</p>}
      <h4>Original assessment measurements</h4>
      {sources.length ? <ul className="factor-sources">{sources.map(source => <li key={source.input_key}>
        <div><span>{source.label}</span><strong>{source.formatted_value}</strong></div>
        {onViewInput ? <button type="button" className="text-button" onClick={() => {
          setNavigationError(onViewInput(source.input_key) ? "" : "This source input is currently unavailable.");
        }}>View {source.label} input →</button> : <small>Source input navigation unavailable.</small>}
      </li>)}</ul> : <p>Source measurements unavailable.</p>}
      {navigationError && <p role="status">{navigationError}</p>}
      <p className="factor-assessment-ref">Values used in assessment {evidence?.assessment_id || "(reference unavailable)"}{evidence?.generated_at ? ` · ${evidence.generated_at}` : ""}.</p>
      <p className="factor-caveat">This contribution explains the independent XGBoost model. It is not a percentage-point change in the ensemble probability or proof that this factor caused disease.</p>
    </div>
  );
}

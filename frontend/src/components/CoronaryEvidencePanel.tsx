import type { PredictionResponse, Vessel } from "../utils/types";
import { VESSELS } from "../utils/vessels";
import { FIELD_GROUPS } from "../utils/patient";
import { formatMeasurement, vesselEvidence } from "../utils/evidence";
import { SHAPExplanationChart } from "./SHAPExplanationChart";

export function CoronaryEvidencePanel({ prediction, selected, onSelect, stale, busy, onViewInput }: {
  prediction: PredictionResponse | null;
  selected: Vessel | null;
  onSelect: (vessel: Vessel) => void;
  stale: boolean;
  busy: boolean;
  onViewInput?: (inputKey: string) => boolean;
}) {
  const evidence = vesselEvidence(prediction, selected, stale);
  const vessel = VESSELS.find(vessel => vessel.key === selected);
  const context = evidence?.context;
  const inputs = context?.clinical_inputs;
  const sourceLabel = (key: string) => {
    const metadata = context?.input_provenance?.measurements[key];
    return metadata ? `${metadata.source} · ${metadata.confirmed ? "confirmed" : "unconfirmed"}${metadata.modeled === false ? " · excluded from model" : ""}` : "Source/confirmation unavailable";
  };
  return (
    <section id="coronary-evidence" className="coronary-evidence" aria-labelledby="coronary-evidence-title" aria-busy={busy}>
      <div className="evidence-header">
        <div>
          <p className="eyebrow">Evidence → anatomy</p>
          <h2 id="coronary-evidence-title">Coronary evidence</h2>
          <p>Select an artery on the heart or below to follow its evidence.</p>
        </div>
        <div className="segmented" aria-label="Select artery evidence">
          {VESSELS.map(vessel => <button key={vessel.key} aria-pressed={selected === vessel.key} onClick={() => onSelect(vessel.key)}>{vessel.key.toUpperCase()}</button>)}
        </div>
      </div>
      <p className="evidence-status" role="status">
        {busy ? "Updating inference. Evidence will refresh together with the heart." : stale ? "Inputs changed. Previous evidence is hidden until a new assessment completes." : !prediction ? "Run an assessment to generate artery evidence." : !selected ? "Choose LAD, LCX or RCA to inspect this assessment." : `Showing ${evidence?.target || selected.toUpperCase()} evidence · ${prediction.patient_id}`}
      </p>
      {evidence && vessel && <>
        <div className="evidence-grid">
          <div className="evidence-score">
            <p className="eyebrow">{evidence.target} · {vessel.name}</p>
            <div className="evidence-probability">{evidence.risk.probability_percent.toFixed(1)}<span>%</span></div>
            <p>Predicted stenosis probability · model estimate</p>
            <p className="evidence-risk"><i style={{ background: evidence.meshColor }} />{evidence.risk.risk_level}</p>
            <p>{evidence.risk.anatomical_description || vessel.description}</p>
            <div className="evidence-color-map">
              <strong>What controls the artery color</strong>
              <code>vessels.{evidence.target}.probability = {evidence.risk.probability}</code>
              <code>vessel_colors_3d.{selected} = {evidence.meshColor}</code>
              <p>Green &lt;35% · Amber 35–&lt;65% · Red ≥65%. Applied in Risk map mode.</p>
            </div>
          </div>
          <div className="evidence-measurements">
            <h3>Measurements used in this assessment</h3>
            <p>These inputs inform all vessel models. They are not direct measurements of this artery.</p>
            {inputs ? <>
              <p>Assessment mode: {context?.input_provenance?.assessment_mode ?? "unavailable (historical snapshot)"}. Sources and review attestations belong to this saved assessment.</p>
              <dl className="measurement-grid">
                {(["Age", "BP", "LDL", "HDL", "FBS", "EF-TTE", "BMI", "DM"] as const).map(key => <div key={key}>
                  <dt>{key === "EF-TTE" ? "Ejection fraction" : key === "DM" ? "Diabetes" : key === "BP" ? "Systolic pressure" : key}</dt>
                  <dd>{formatMeasurement(key, inputs[key])}<small>{sourceLabel(key)}</small></dd>
                </div>)}
              </dl>
              <details className="evidence-inputs">
                <summary>View all assessed clinical inputs</summary>
                {FIELD_GROUPS.map(group => <div key={group.title}><h4>{group.title}</h4><dl className="measurement-grid">
                  {group.fields.map(field => <div key={field.key}><dt>{field.label}</dt><dd>{formatMeasurement(field.key, inputs[field.key])}<small>{sourceLabel(field.key)}</small></dd></div>)}
                </dl></div>)}
              </details>
            </> : <p>Input provenance is unavailable from this model service. Update the backend and reassess.</p>}
          </div>
        </div>
        <SHAPExplanationChart prediction={prediction} stale={stale} target={evidence.target} onViewInput={onViewInput} />
        <div className="evidence-limits">
          <div><h3>Confidence & limitations</h3><p>Confidence interval: unavailable. A high probability is not a measure of model certainty.</p></div>
          <ul>{(context?.limitations || ["Clinical calibration and external validation have not been established.", "SHAP contributions explain an independent XGBoost model, not the ensemble probability.", "Reference anatomy does not locate lesions or measure percentage blockage."]).map(limit => <li key={limit}>{limit}</li>)}</ul>
        </div>
        <details className="evidence-provenance">
          <summary>Exact prediction result & provenance</summary>
          <dl>
            <dt>Assessment ID</dt><dd>{context?.assessment_id || "Unavailable"}</dd>
            <dt>Generated at (UTC)</dt><dd>{context?.generated_at || "Unavailable"}</dd>
            <dt>Prediction model</dt><dd>{context?.prediction_model || "Unavailable"}</dd>
            <dt>Explanation model</dt><dd>{context?.explanation_model || "Unavailable"}</dd>
          </dl>
          <pre>{JSON.stringify({ assessment_id: context?.assessment_id, patient_id: prediction?.patient_id, target: evidence.target, result: evidence.risk, mesh_color: evidence.meshColor, input_provenance: context?.input_provenance, shap_explanations: evidence.factors }, null, 2)}</pre>
        </details>
      </>}
    </section>
  );
}

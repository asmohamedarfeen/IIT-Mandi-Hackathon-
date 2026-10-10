import { ArrowUpRight } from "lucide-react";
import { PatientData } from "../utils/types";
import { FIELD_GROUPS, updatePatient, reviewedIssues } from "../utils/patient";
import { measurementAnchorId } from "../utils/measurementNavigation";
interface Props {
  patientData: PatientData;
  onChange: (data: PatientData) => void;
  onSubmit: (data: PatientData) => void;
  isLoading: boolean;
  ready: boolean;
  hasAssessment?: boolean;
}
export function PatientForm({
  patientData,
  onChange,
  onSubmit,
  isLoading,
  ready,
  hasAssessment = false,
}: Props) {
  const reviewed = patientData.assessment_mode === "reviewed";
  const missing = reviewedIssues(patientData);
  const modeledCount = FIELD_GROUPS.flatMap(group => group.fields).filter(field => field.key !== "Exertional CP").length + (patientData.input_sources?.BMI === "supplied" ? 1 : 0);
  const fieldError = (field: typeof FIELD_GROUPS[number]["fields"][number]) => {
    const value = Number(patientData[field.key]);
    return !Number.isFinite(value) || (field.options ? !Number.isInteger(value) || value < 0 || value >= field.options.length : value < field.min! || value > field.max! || field.step === "1" && !Number.isInteger(value));
  };
  return (
    <form
      className="patient-form"
      onSubmit={(e) => {
        e.preventDefault();
        if (!missing.length) onSubmit(patientData);
      }}
      onInvalidCapture={(e) => {
        const group = (e.target as HTMLElement).closest("details");
        if (group) group.open = true;
      }}
    >
      <div className="form-intro">
        <div>
          <h2>Patient details</h2>
        </div>
        <p>
          {reviewed ? "Confirm measurements against a case record. Unknown values cannot be assessed." : "Demonstration mode uses synthetic defaults; results are examples."}
          {hasAssessment && " Valid edits automatically reassess after a short pause."}
        </p>
      </div>
      <fieldset className="assessment-mode">
        <legend>Assessment mode</legend>
        <label><input type="radio" name="assessment-mode" checked={!reviewed} onChange={() => onChange({ ...patientData, assessment_mode: "demo", confirmed_measurements: [] })} /> Demonstration</label>{" "}
        <label><input type="radio" name="assessment-mode" checked={reviewed} onChange={() => onChange({ ...patientData, assessment_mode: "reviewed", confirmed_measurements: [] })} /> Reviewed case</label>
        <p>Review confirmation records your attestation; it is not a clinical validation.</p>
        {reviewed && <p role="status">{modeledCount - missing.length} / {modeledCount} modeled measurements confirmed. BMI is calculated from height and weight unless recorded.</p>}
      </fieldset>
      <label className="patient-id">
        Case reference <span>Optional · use a de-identified ID</span>
        <input
          value={patientData.patient_id || ""}
          placeholder="Enter case reference"
          maxLength={100}
          onChange={(e) =>
            onChange(updatePatient(patientData, "patient_id", e.target.value))
          }
        />
      </label>
      {FIELD_GROUPS.map((group, index) => (
        <details
          key={group.title}
          className="form-group"
          open={index === 0 ? true : undefined}
        >
          <summary>
            {group.title}
            <span>
              {group.fields.length} inputs <span aria-hidden="true">+</span>
            </span>
          </summary>
          {reviewed && <label className="review-attestation">
            <input type="checkbox"
              checked={group.fields.filter(field => field.key !== "Exertional CP").every(field => patientData.confirmed_measurements?.includes(field.key)) && (index !== 0 || patientData.input_sources?.BMI !== "supplied" || Boolean(patientData.confirmed_measurements?.includes("BMI")))}
              disabled={group.fields.some(fieldError)}
              onChange={e => {
                const keys = group.fields.filter(field => field.key !== "Exertional CP").map(field => field.key);
                if (index === 0 && patientData.input_sources?.BMI === "supplied") keys.push("BMI");
                const confirmed = new Set(patientData.confirmed_measurements ?? []);
                const sources = { ...patientData.input_sources };
                keys.forEach(key => { if (e.target.checked) { confirmed.add(key); sources[key] = "supplied"; } else confirmed.delete(key); });
                onChange({ ...patientData, confirmed_measurements: [...confirmed], input_sources: sources });
              }} />
            I verified each modeled measurement in {group.title.toLowerCase()} against the case record. Unknown measurements must be cleared, not marked absent.
          </label>}
          <div className="field-grid">
            {group.fields.map((field) => (
              <label key={field.key} className="field">
                {field.label}
                {field.unit && <span className="unit">{field.unit}</span>}
                <span className="unit">{field.key === "Exertional CP" ? "Informational · excluded from model" : patientData.confirmed_measurements?.includes(field.key) ? "Confirmed" : patientData.input_sources?.[field.key] ?? "Defaulted"}</span>
                {field.options ? (
                  <select
                    id={measurementAnchorId(field.key)}
                    required
                    aria-invalid={fieldError(field)}
                    aria-describedby={fieldError(field) ? measurementAnchorId(field.key) + "-error" : undefined}
                    value={
                      field.options[Number(patientData[field.key])] !==
                      undefined
                        ? String(patientData[field.key])
                        : ""
                    }
                    onChange={(e) =>
                      onChange(
                        updatePatient(
                          patientData,
                          field.key,
                          e.target.value === "" ? NaN : Number(e.target.value),
                        ),
                      )
                    }
                  >
                    <option value="">
                      Unknown / not recorded
                    </option>
                    {field.options.map((label, i) => (
                      <option value={i} key={label}>
                        {label}
                      </option>
                    ))}
                  </select>
                ) : (
                  <input
                    id={measurementAnchorId(field.key)}
                    type="number"
                    required
                    aria-invalid={fieldError(field)}
                    aria-describedby={fieldError(field) ? measurementAnchorId(field.key) + "-error" : undefined}
                    min={field.min}
                    max={field.max}
                    step={field.step}
                    value={
                      Number.isFinite(patientData[field.key])
                        ? patientData[field.key]
                        : ""
                    }
                    onChange={(e) =>
                      onChange(
                        updatePatient(
                          patientData,
                          field.key,
                          e.target.value === "" ? NaN : Number(e.target.value),
                        ),
                      )
                    }
                  />
                )}
                {fieldError(field) && <span id={measurementAnchorId(field.key) + "-error"} role="alert">{field.options ? `Choose a supported ${field.label} value` : `Enter ${field.label} between ${field.min} and ${field.max} ${field.unit ?? ""}`}</span>}
              </label>
            ))}
            {index === 0 && (
              <div className="bmi-readout" id={measurementAnchorId("BMI")} tabIndex={-1} aria-label="BMI input readout">
                {patientData.input_sources?.BMI === "supplied" ? "Recorded BMI" : "Calculated BMI"}{" "}
                <strong>
                  {Number.isFinite(patientData.BMI)
                    ? patientData.BMI?.toFixed(1)
                    : "—"}
                </strong>
                <span>kg/m² · updates with height and weight</span>
              </div>
            )}
          </div>
        </details>
      ))}
      <div className="form-submit">
        <p>
          {ready
            ? "Inputs and results are saved. Use de-identified data."
            : "Waiting for the model service. Inputs and results will be saved."}
        </p>
        <button
          className="button primary"
          disabled={isLoading || !ready || missing.length > 0}
          type="submit"
        >
          {isLoading ? "Assessing…" : "Run assessment"}
          <ArrowUpRight size={18} />
        </button>
      </div>
    </form>
  );
}

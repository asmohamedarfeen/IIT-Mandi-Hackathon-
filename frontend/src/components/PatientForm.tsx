import { ArrowUpRight } from "lucide-react";
import { PatientData } from "../utils/types";
import { FIELD_GROUPS, updatePatient } from "../utils/patient";
interface Props {
  patientData: PatientData;
  onChange: (data: PatientData) => void;
  onSubmit: (data: PatientData) => void;
  isLoading: boolean;
  ready: boolean;
}
export function PatientForm({
  patientData,
  onChange,
  onSubmit,
  isLoading,
  ready,
}: Props) {
  return (
    <form
      className="patient-form"
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit(patientData);
      }}
      onInvalidCapture={(e) => {
        const group = (e.target as HTMLElement).closest("details");
        if (group) group.open = true;
      }}
    >
      <div className="form-intro">
        <div>
          <p className="eyebrow">Clinical workspace</p>
          <h2>Build the full picture.</h2>
        </div>
        <p>
          Review every group before assessment. Initial values are editable
          defaults.
        </p>
      </div>
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
          <div className="field-grid">
            {group.fields.map((field) => (
              <label key={field.key} className="field">
                {field.label}
                {field.unit && <span className="unit">{field.unit}</span>}
                {field.options ? (
                  <select
                    required
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
                          Number(e.target.value),
                        ),
                      )
                    }
                  >
                    <option value="" disabled>
                      Choose a value
                    </option>
                    {field.options.map((label, i) => (
                      <option value={i} key={label}>
                        {label}
                      </option>
                    ))}
                  </select>
                ) : (
                  <input
                    type="number"
                    required
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
              </label>
            ))}
            {index === 0 && (
              <div className="bmi-readout">
                Calculated BMI{" "}
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
            ? "Ready when you are. Review, then assess."
            : "Assessment requires a ready model service."}
        </p>
        <button
          className="button primary"
          disabled={isLoading || !ready}
          type="submit"
        >
          {isLoading ? "Assessing…" : "Run assessment"}
          <ArrowUpRight size={18} />
        </button>
      </div>
    </form>
  );
}

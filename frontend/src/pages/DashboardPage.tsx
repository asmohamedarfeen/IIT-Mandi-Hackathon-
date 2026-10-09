import { useEffect, useRef, useState, useCallback, useMemo } from "react";
import {
  ArrowUpRight,
  ArrowLeft,
  ArrowRight,
  RefreshCw,
} from "lucide-react";
import { HeartViewer3D } from "../components/HeartViewer3D";
import { RiskSummaryCards } from "../components/RiskSummaryCards";
import { PatientForm } from "../components/PatientForm";
import { CoronaryEvidencePanel } from "../components/CoronaryEvidencePanel";
import { SHAPExplanationChart } from "../components/SHAPExplanationChart";
import { EvidenceReportDownload } from "../components/EvidenceReportDownload";
import { createAssessmentRunner } from "../utils/assessment";
import { rankedVessels } from "../utils/risk";
import { focusMeasurement } from "../utils/measurementNavigation";
import { apiService } from "../services/api";
import {
  DEFAULT_PATIENT,
  normalizePatient,
  sampleVessels,
} from "../utils/patient";
import {
  PatientData,
  PredictionResponse,
  SamplePatient,
  ThreeDAnatomyPayload,
  Vessel,
} from "../utils/types";
export function DashboardPage({ active = true }: { active?: boolean }) {
  const activeRef = useRef(active);
  activeRef.current = active;
  const formHost = useRef<HTMLDivElement>(null);
  const viewInput = useCallback((inputKey: string) => {
    return Boolean(formHost.current && focusMeasurement(formHost.current, inputKey, matchMedia("(prefers-reduced-motion: reduce)").matches));
  }, []);
  const [selectedVessel, setSelectedVessel] = useState<Vessel | null>(null);
  const [patient, setPatient] = useState(() =>
    normalizePatient(DEFAULT_PATIENT),
  );
  const [prediction, setPrediction] = useState<PredictionResponse | null>(null),
    [stale, setStale] = useState(false),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const [anatomy, setAnatomy] = useState<ThreeDAnatomyPayload | null>(null),
    [anatomyError, setAnatomyError] = useState(false);
  const [samples, setSamples] = useState<SamplePatient[]>([]),
    [sampleError, setSampleError] = useState(false),
    [sampleIndex, setSampleIndex] = useState(0),
    [selectedSample, setSelectedSample] = useState("");
  const [health, setHealth] = useState<"checking" | "ready" | "unavailable">(
    "checking",
  );
  const checkHealth = useCallback(() => {
    setHealth("checking");
    apiService
      .checkHealth()
      .then((h) => setHealth(h.models_ready ? "ready" : "unavailable"))
      .catch(() => setHealth("unavailable"));
  }, []);
  const assessment = useMemo(() => createAssessmentRunner(apiService.predictPatient, {
    onStart: () => { setBusy(true); setError(""); setStale(true); },
    onResult: (result, automatic) => {
      setPrediction(result);
      setStale(false);
      setHealth("ready");
      setSelectedVessel(current => current ?? rankedVessels(result)[0]?.key ?? "lad");
      if (!automatic && activeRef.current) document.querySelector("#results")?.scrollIntoView({
        behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth",
        block: "start",
      });
    },
    onError: () => {
      setError("The assessment could not be completed. Check the model service, review the inputs, and try again.");
      checkHealth();
    },
    onFinish: () => setBusy(false),
  }), [checkHealth]);
  const loadAnatomy = useCallback(() => {
    setAnatomyError(false);
    apiService
      .getHeartAnatomy()
      .then(setAnatomy)
      .catch(() => setAnatomyError(true));
  }, []);
  const loadSamples = useCallback(() => {
    setSampleError(false);
    apiService
      .getSamplePatients()
      .then(setSamples)
      .catch(() => setSampleError(true));
  }, []);
  useEffect(() => {
    checkHealth();
    loadAnatomy();
    loadSamples();
    return () => {
      assessment.dispose();
    };
  }, [checkHealth, loadAnatomy, loadSamples, assessment]);
  function changePatient(next: PatientData) {
    assessment.invalidate();
    setBusy(false);
    setPatient(next);
    setStale(Boolean(prediction));
    setError("");
    setSelectedSample("");
    if (prediction && health === "ready") {
      assessment.schedule(next, () => Boolean(formHost.current?.querySelector("form")?.checkValidity()));
    }
  }
  function selectSample(sample: SamplePatient) {
    changePatient(normalizePatient(sample.features, sample.patient_id));
    setSelectedSample(sample.patient_id);
    document.querySelector("#patient-inputs")?.scrollIntoView({
      behavior: matchMedia("(prefers-reduced-motion: reduce)").matches
        ? "auto"
        : "smooth",
      block: "start",
    });
  }
  const sample = samples[sampleIndex];
  return (
    <div>
      <section
        id="assessment"
        className="assessment-section"
        aria-labelledby="assessment-title"
      >
        <div className="section-heading">
          <div>
            <h1 id="assessment-title">Heart risk assessment</h1>
            <p className="assessment-intro">Load a sample case or enter patient details.</p>
          </div>
          <div className={"service-state " + health} role="status">
            <i />
            <span>
              {health === "ready"
                ? "Model service ready"
                : health === "checking"
                  ? "Checking model service…"
                  : "Model service unavailable"}
            </span>
            <button
              onClick={checkHealth}
              disabled={health === "checking"}
              aria-label="Recheck model service"
            >
              <RefreshCw size={14} />
            </button>
          </div>
        </div>
        <div className="case-carousel">
          <div className="case-intro">
            <p className="eyebrow">Sample cases</p>
            <p>Examples from the training dataset.</p>
          </div>
          <div className="case-body" aria-live="polite">
            {sample ? (
              <>
                <div className="case-ident">
                  <span>
                    {String(sampleIndex + 1).padStart(2, "0")} /{" "}
                    {String(samples.length).padStart(2, "0")}
                  </span>
                  <h3>{sample.patient_id.replace(/_/g, " ")}</h3>
                  <p>
                    {sample.features.Age} years ·{" "}
                    {Number(sample.features.Sex) === 1 ||
                    sample.features.Sex === "Male"
                      ? "Male"
                      : "Female"}{" "}
                    · Recorded CAD: {sample.ground_truth.CAD}
                  </p>
                </div>
                <div className="case-targets">
                  <span>Recorded vessel involvement</span>
                  <strong>{sampleVessels(sample)}</strong>
                  <details>
                    <summary>View source labels</summary>
                    <p>
                      {Object.entries(sample.ground_truth)
                        .map(([key, value]) => `${key}: ${value}`)
                        .join(" · ")}
                    </p>
                  </details>
                </div>
                <button className="button" onClick={() => selectSample(sample)}>
                  Use this case <ArrowUpRight size={16} />
                </button>
              </>
            ) : (
              <p>
                {sampleError
                  ? "Recorded cases could not be loaded."
                  : "Loading recorded cases…"}
                {sampleError && (
                  <button className="text-button" onClick={loadSamples}>
                    Retry cases
                  </button>
                )}
              </p>
            )}
          </div>
          <div className="carousel-controls">
            <button
              aria-label="Previous sample case"
              disabled={!samples.length}
              onClick={() =>
                setSampleIndex(
                  (sampleIndex - 1 + samples.length) % samples.length,
                )
              }
            >
              <ArrowLeft size={19} />
            </button>
            <button
              aria-label="Next sample case"
              disabled={!samples.length}
              onClick={() => setSampleIndex((sampleIndex + 1) % samples.length)}
            >
              <ArrowRight size={19} />
            </button>
          </div>
        </div>
        <div className="workspace-grid">
          <div id="patient-inputs" ref={formHost}>
            {selectedSample && (
              <div className="loaded-case" role="status">
                {selectedSample} loaded. Review the inputs before assessing.
              </div>
            )}
            <PatientForm
              patientData={patient}
              onChange={changePatient}
              onSubmit={assessment.run}
              isLoading={busy}
              ready={health === "ready"}
              hasAssessment={Boolean(prediction)}
            />
            {error && (
              <div className="error-message" role="alert">
                {error}
                <button className="text-button" onClick={checkHealth}>
                  Recheck connection
                </button>
              </div>
            )}
          </div>
          <HeartViewer3D
            active={active}
            anatomyData={anatomy}
            prediction={stale ? null : prediction}
            stale={stale}
            error={anatomyError}
            onRetry={loadAnatomy}
            selectedVessel={selectedVessel}
            onSelectVessel={setSelectedVessel}
          />
        </div>
        <div id="results" className="results-header">
          <h2>Results</h2>
          <p role="status">
            {busy
              ? "Assessment in progress…"
              : stale
                ? "Inputs changed. Valid edits update automatically; review invalid fields or retry the assessment."
                : prediction
                  ? `Assessment complete · ${prediction.patient_id}`
                  : "Complete the form to generate model estimates."}
          </p>
        </div>
        <EvidenceReportDownload prediction={prediction} stale={stale} busy={busy} />
        <RiskSummaryCards prediction={prediction} stale={stale} selectedVessel={selectedVessel} onSelectVessel={setSelectedVessel} />
        <p className="result-caveat">
          Model probabilities are experimental estimates. Risk colors indicate
          whole-vessel output, not the location or severity of a lesion.
        </p>
      </section>
      <CoronaryEvidencePanel prediction={prediction} selected={selectedVessel} onSelect={setSelectedVessel} stale={stale} busy={busy} onViewInput={viewInput} />
      {prediction && <SHAPExplanationChart prediction={prediction} stale={stale} target="CAD" onViewInput={viewInput} />}
    </div>
  );
}

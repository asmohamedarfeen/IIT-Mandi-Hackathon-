import { useEffect, useRef, useState, useCallback } from "react";
import {
  ArrowUpRight,
  ArrowLeft,
  ArrowRight,
  Activity,
  RefreshCw,
} from "lucide-react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { useGSAP } from "@gsap/react";
import { HeartViewer3D } from "../components/HeartViewer3D";
import { RiskSummaryCards } from "../components/RiskSummaryCards";
import { PatientForm } from "../components/PatientForm";
import { SHAPExplanationChart } from "../components/SHAPExplanationChart";
import { VESSELS } from "../utils/vessels";
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
} from "../utils/types";
gsap.registerPlugin(ScrollTrigger, useGSAP);
export function DashboardPage() {
  const root = useRef<HTMLDivElement>(null),
    revision = useRef(0),
    request = useRef(0);
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
      request.current++;
    };
  }, [checkHealth, loadAnatomy, loadSamples]);
  useGSAP(
    () => {
      const media = gsap.matchMedia();
      media.add(
        "(min-width: 1000px) and (prefers-reduced-motion: no-preference)",
        () => {
          gsap.from(".hero-copy > *", {
            y: 24,
            opacity: 0,
            duration: 0.9,
            stagger: 0.09,
            ease: "power2.out",
          });
          ScrollTrigger.create({
            trigger: ".anatomy-story",
            start: "top 120px",
            end: "bottom 660px",
            pin: ".story-title",
            pinSpacing: false,
          });
          gsap.utils
            .toArray<HTMLElement>(".story-card")
            .forEach((card, index) => {
              if (index < 2)
                gsap.to(card, {
                  scale: 0.96,
                  y: -12,
                  transformOrigin: "top center",
                  scrollTrigger: {
                    trigger: card,
                    start: "top 160px",
                    end: "bottom 150px",
                    scrub: true,
                  },
                });
            });
        },
      );
      return () => media.revert();
    },
    { scope: root },
  );
  function changePatient(next: PatientData) {
    revision.current++;
    request.current++;
    setBusy(false);
    setPatient(next);
    setStale(Boolean(prediction));
    setError("");
    setSelectedSample("");
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
  async function assess(data: PatientData) {
    const token = ++request.current,
      currentRevision = revision.current;
    setBusy(true);
    setError("");
    try {
      const result = await apiService.predictPatient(data);
      if (token !== request.current || revision.current !== currentRevision)
        return;
      setPrediction(result);
      setStale(false);
      setHealth("ready");
      document.querySelector("#results")?.scrollIntoView({
        behavior: matchMedia("(prefers-reduced-motion: reduce)").matches
          ? "auto"
          : "smooth",
        block: "start",
      });
    } catch {
      if (token === request.current) {
        setError(
          "The assessment could not be completed. Check the model service, review the inputs, and try again.",
        );
        checkHealth();
      }
    } finally {
      if (token === request.current) setBusy(false);
    }
  }
  const sample = samples[sampleIndex];
  return (
    <div ref={root}>
      <section className="hero" aria-labelledby="hero-title">
        <div className="hero-heading">
          <p className="eyebrow">Coronary intelligence, in context</p>
          <h1 id="hero-title">
            See the heart.
            <br />
            <span>Understand the risk.</span>
          </h1>
        </div>
        <div className="hero-composition">
          <div className="hero-copy">
            <div className="hero-rule" />
            <p className="hero-lead">
              A new perspective
              <br />
              on the clinical picture.
            </p>
            <p>
              Bring clinical inputs, vessel-level estimates, and anatomical
              exploration into one considered workspace.
            </p>
            <a className="button primary" href="#assessment">
              Begin an assessment <ArrowUpRight size={18} />
            </a>
            <p className="hero-footnote">
              A research tool for exploration.
              <br />
              Clinical judgment remains essential.
            </p>
          </div>
          <HeartViewer3D
            anatomyData={anatomy}
            prediction={stale ? null : prediction}
            error={anatomyError}
            onRetry={loadAnatomy}
          />
        </div>
      </section>
      <section
        id="assessment"
        className="assessment-section"
        aria-labelledby="assessment-title"
      >
        <div className="section-heading">
          <div>
            <p className="eyebrow">From inputs to insight</p>
            <h2 id="assessment-title">Your clinical workspace.</h2>
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
            <p className="eyebrow">Explore a recorded case</p>
            <p>
              Real examples from the training dataset. Select one to populate
              the inputs, then run an assessment.
            </p>
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
          <aside className="workspace-context">
            <Activity size={31} strokeWidth={1.25} />
            <h3>
              Every input{" "}
              <br />
              adds context.
            </h3>
            <p>
              The assessment combines patient history, symptoms, examination,
              ECG, laboratory markers, and echocardiography.
            </p>
            <ol>
              <li>
                <strong>Prepare the case</strong>
                <span>
                  Load a recorded example or enter de-identified clinical data.
                </span>
              </li>
              <li>
                <strong>Review the details</strong>
                <span>
                  Open each group. Height and weight automatically update BMI.
                </span>
              </li>
              <li>
                <strong>Explore the estimate</strong>
                <span>
                  Compare the four model outputs and their surrogate
                  explanations.
                </span>
              </li>
            </ol>
            <p className="small-note">
              Submitting an assessment stores its inputs and result in the
              connected research database. Use de-identified records.
            </p>
          </aside>
          <div id="patient-inputs">
            {selectedSample && (
              <div className="loaded-case" role="status">
                {selectedSample} loaded. Review the inputs before assessing.
              </div>
            )}
            <PatientForm
              patientData={patient}
              onChange={changePatient}
              onSubmit={assess}
              isLoading={busy}
              ready={health === "ready"}
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
        </div>
        <div id="results" className="results-header">
          <h3>Assessment overview</h3>
          <p role="status">
            {busy
              ? "Assessment in progress…"
              : stale
                ? "Inputs changed. Run a new assessment to update these results."
                : prediction
                  ? `Assessment complete · ${prediction.patient_id}`
                  : "Complete the form to generate model estimates."}
          </p>
        </div>
        <RiskSummaryCards prediction={prediction} stale={stale} />
        <p className="result-caveat">
          Model probabilities are experimental estimates. Risk colors indicate
          whole-vessel output, not the location or severity of a lesion.
        </p>
      </section>
      <SHAPExplanationChart prediction={prediction} stale={stale} />
      <section className="anatomy-story">
        <div className="story-title">
          <p className="eyebrow">Anatomy, made tangible</p>
          <h2>
            Three vessels.
            <br />
            One connected{" "}
            <br />
            perspective.
          </h2>
          <p>
            Follow each coronary tree through the same registered reference
            heart. The shape stays true to the supplied anatomy.
          </p>
          <a className="text-link" href="#top">
            Explore the interactive heart <ArrowUpRight size={17} />
          </a>
        </div>
        <div className="story-cards">
          {VESSELS.map((v) => (
            <article className="story-card" key={v.key}>
              <div className="story-vessel-title">
                <span style={{ color: v.color }}>{v.key.toUpperCase()}</span>
                <span className="vessel-line" style={{ background: v.color }} />
              </div>
              <h3>{v.name}</h3>
              <details className="story-details">
                <summary>
                  Explore this vessel <span aria-hidden="true">+</span>
                </summary>
                <p>{v.description}</p>
              </details>
              <p className="small-note">
                Reference anatomy · vessel-level exploration
              </p>
            </article>
          ))}
        </div>
      </section>
      <section className="closing">
        <p className="eyebrow">A considered next step</p>
        <h2>Bring the picture together.</h2>
        <a className="button primary" href="#assessment">
          Start in the workspace <ArrowUpRight size={18} />
        </a>
      </section>
    </div>
  );
}

import { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { RotateCcw, Maximize2, HeartPulse, Minus, Plus, TriangleAlert } from "lucide-react";
import { ThreeDAnatomyPayload, PredictionResponse, Vessel } from "../utils/types";
import { VESSELS } from "../utils/vessels";
import { toggleFullscreen } from "../utils/fullscreen";
import { createRenderLoop } from "../utils/renderLoop";
import { VesselDetail } from "./VesselDetail";
import { rankedVessels, riskBand } from "../utils/risk";
import {
  createAnatomyMeshes,
  updateAnatomyMeshes,
  disposeAnatomyMeshes,
  pickCoronaryVessel,
  type AnatomyMesh,
} from "../utils/anatomy";
interface SceneState {
  renderer: THREE.WebGLRenderer;
  camera: THREE.PerspectiveCamera;
  controls: OrbitControls;
  group: THREE.Group;
  meshes: Record<string, AnatomyMesh>;
  fit: (animate?: boolean) => void;
}
export function HeartViewer3D({
  anatomyData,
  prediction,
  stale = false,
  error,
  onRetry,
  selectedVessel,
  onSelectVessel,
  active = true,
}: {
  anatomyData: ThreeDAnatomyPayload | null;
  prediction: PredictionResponse | null;
  stale?: boolean;
  error: boolean;
  onRetry: () => void;
  selectedVessel: Vessel | null;
  onSelectVessel: (vessel: Vessel | null) => void;
  active?: boolean;
}) {
  const activeRef = useRef(active);
  const loopRef = useRef<ReturnType<typeof createRenderLoop> | null>(null);
  useEffect(() => {
    activeRef.current = active;
    loopRef.current?.setActive(active);
  }, [active]);
  const focus = selectedVessel;
  const selectRef = useRef(onSelectVessel);
  useEffect(() => { selectRef.current = onSelectVessel; }, [onSelectVessel]);
  const host = useRef<HTMLDivElement>(null),
    stage = useRef<HTMLDivElement>(null),
    sceneRef = useRef<SceneState | null>(null),
    pulseRef = useRef(false),
    focusRef = useRef<Vessel | null>(null),
    reducedRef = useRef(false);
  const [mode, setMode] = useState<"anatomy" | "risk">("anatomy"),
    [pulse, setPulse] = useState(false),
    [opacity, setOpacity] = useState(1),
    [visible, setVisible] = useState(true),
    [webglError, setWebglError] = useState(false),
    [attempt, setAttempt] = useState(0),
    [reduced, setReduced] = useState(false),
    [fullscreenMessage, setFullscreenMessage] = useState<string | null>(null),
    [fullscreen, setFullscreen] = useState(false);
  useEffect(() => {
    const query = matchMedia("(prefers-reduced-motion: reduce)");
    const change = () => setReduced(query.matches);
    change();
    query.addEventListener("change", change);
    return () => query.removeEventListener("change", change);
  }, []);
  useEffect(() => {
    pulseRef.current = pulse && !reduced;
    reducedRef.current = reduced;
  }, [pulse, reduced]);
  useEffect(() => {
    if (prediction && !stale) setMode("risk");
  }, [prediction, stale]);
  useEffect(() => {
    const change = () => setFullscreen(document.fullscreenElement === stage.current);
    document.addEventListener("fullscreenchange", change);
    return () => document.removeEventListener("fullscreenchange", change);
  }, []);
  // Only new anatomy or an explicit recovery rebuilds the renderer. Controls and materials update in place.
  useEffect(() => {
    if (!host.current || !anatomyData) return;
    const element = host.current;
    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({
        antialias: true,
        alpha: true,
        powerPreference: "high-performance",
      });
    } catch {
      setWebglError(true);
      return;
    }
    setWebglError(false);
    renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
    renderer.setClearColor("#121918", 0);
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.35;
    element.appendChild(renderer.domElement);
    renderer.domElement.setAttribute(
      "aria-label",
      "Interactive BodyParts3D reference heart",
    );
    const scene = new THREE.Scene(),
      camera = new THREE.PerspectiveCamera(34, 1, 0.01, 100),
      group = new THREE.Group();
    scene.add(group);
    scene.add(new THREE.HemisphereLight("#f4e4d7", "#292722", 2.0));
    const key = new THREE.DirectionalLight("#ffe3d0", 4.0);
    key.position.set(-4, 6, 6);
    scene.add(key);
    const fill = new THREE.DirectionalLight("#d1e6ea", 1.6);
    fill.position.set(4, 1, 4);
    scene.add(fill);
    const rim = new THREE.DirectionalLight("#edc5b7", 3);
    rim.position.set(2, 3, -4);
    scene.add(rim);
    const meshes = createAnatomyMeshes(anatomyData);
    group.add(...Object.values(meshes));
    const box = new THREE.Box3().setFromObject(group);
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.enablePan = false;
    controls.minDistance = 0.5;
    controls.maxDistance = 20;
    let transition: {
      start: number;
      fromPosition: THREE.Vector3;
      fromTarget: THREE.Vector3;
      position: THREE.Vector3;
      target: THREE.Vector3;
    } | null = null;
    const stopTransition = () => { transition = null; };
    controls.addEventListener("start", stopTransition);
    const state: SceneState = {
      renderer,
      camera,
      controls,
      group,
      meshes,
      fit: (animate = false) => {
        const vessel = focusRef.current;
        const bounds = vessel ? meshes[vessel]?.geometry.boundingBox || box : box;
        const center = bounds.getCenter(new THREE.Vector3());
        const radius = bounds.getBoundingSphere(new THREE.Sphere()).radius;
        const halfFov = THREE.MathUtils.degToRad(camera.fov / 2);
        const distance = radius / Math.sin(Math.min(halfFov, Math.atan(Math.tan(halfFov) * camera.aspect))) * 1.08;
        const directions = {
          lad: new THREE.Vector3(0.5, 0.15, 1),
          lcx: new THREE.Vector3(0.9, 0.25, -1),
          rca: new THREE.Vector3(-0.8, 0.1, 1),
        };
        const direction = vessel ? directions[vessel] : new THREE.Vector3(0.14, 0.03, 1);
        const position = center.clone().add(direction.normalize().multiplyScalar(distance));
        controls.maxDistance = Math.max(20, distance * 2);
        if (animate && !reducedRef.current) {
          transition = {
            start: performance.now(),
            fromPosition: camera.position.clone(),
            fromTarget: controls.target.clone(),
            position,
            target: center,
          };
        } else {
          transition = null;
          camera.position.copy(position);
          controls.target.copy(center);
        }
        controls.update();
      },
    };
    sceneRef.current = state;
    const raycaster = new THREE.Raycaster();
    let pointerStart: { x: number; y: number; id: number } | null = null;
    const pointerDown = (event: PointerEvent) => {
      pointerStart = event.isPrimary && event.button === 0 ? { x: event.clientX, y: event.clientY, id: event.pointerId } : null;
    };
    const pointerUp = (event: PointerEvent) => {
      const start = pointerStart;
      pointerStart = null;
      if (!start || start.id !== event.pointerId || Math.hypot(event.clientX - start.x, event.clientY - start.y) > 5) return;
      const bounds = renderer.domElement.getBoundingClientRect();
      if (!bounds.width || !bounds.height) return;
      raycaster.setFromCamera(new THREE.Vector2(
        (event.clientX - bounds.left) / bounds.width * 2 - 1,
        -(event.clientY - bounds.top) / bounds.height * 2 + 1,
      ), camera);
      group.updateMatrixWorld(true);
      const selected = pickCoronaryVessel(raycaster, meshes);
      if (selected) selectRef.current(selected);
    };
    const pointerCancel = () => { pointerStart = null; };
    renderer.domElement.addEventListener("pointerdown", pointerDown);
    renderer.domElement.addEventListener("pointerup", pointerUp);
    renderer.domElement.addEventListener("pointercancel", pointerCancel);
    const resize = () => {
      const width = element.clientWidth,
        height = element.clientHeight;
      if (!width || !height) return;
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
      renderer.setSize(width, height);
      state.fit(Boolean(transition));
    };
    const observer = new ResizeObserver(resize);
    observer.observe(element);
    resize();
    const lost = (event: Event) => {
      event.preventDefault();
      setWebglError(true);
      loopRef.current?.setActive(false);
    };
    renderer.domElement.addEventListener("webglcontextlost", lost);
    const start = performance.now();
    const animate = (now: number) => {
      if (transition) {
        const progress = Math.min((now - transition.start) / 450, 1);
        const eased = 1 - (1 - progress) ** 3;
        camera.position.lerpVectors(transition.fromPosition, transition.position, eased);
        controls.target.lerpVectors(transition.fromTarget, transition.target, eased);
        if (progress === 1) transition = null;
      }
      const t = ((now - start) / 1000) % 1.15;
      const beat = pulseRef.current
        ? 0.012 * Math.exp(-(((t - 0.18) / 0.07) ** 2)) +
          0.006 * Math.exp(-(((t - 0.35) / 0.09) ** 2))
        : 0;
      group.scale.setScalar(1 + beat);
      controls.update();
      renderer.render(scene, camera);
    };
    const loop = createRenderLoop(animate);
    loopRef.current = loop;
    loop.setActive(activeRef.current);
    return () => {
      loop.dispose();
      loopRef.current = null;
      observer.disconnect();
      controls.removeEventListener("start", stopTransition);
      controls.dispose();
      renderer.domElement.removeEventListener("webglcontextlost", lost);
      renderer.domElement.removeEventListener("pointerdown", pointerDown);
      renderer.domElement.removeEventListener("pointerup", pointerUp);
      renderer.domElement.removeEventListener("pointercancel", pointerCancel);
      disposeAnatomyMeshes(meshes);
      scene.clear();
      renderer.dispose();
      renderer.forceContextLoss();
      renderer.domElement.remove();
      sceneRef.current = null;
    };
  }, [anatomyData, attempt]);
  useEffect(() => {
    focusRef.current = focus;
    sceneRef.current?.fit(true);
  }, [focus]);
  useEffect(() => {
    const state = sceneRef.current;
    if (!state) return;
    updateAnatomyMeshes(state.meshes, {
      mode,
      prediction: stale ? null : prediction,
      opacity: mode === "risk" ? Math.min(opacity, 0.18) : opacity,
      visible,
      focus,
    });
  }, [anatomyData, attempt, mode, prediction, opacity, visible, focus, stale]);
  function focusVessel(vessel: Vessel | null) {
    if (vessel === focus) {
      sceneRef.current?.fit(true);
      return;
    }
    onSelectVessel(vessel);
  }
  const zoom = (factor: number) => {
    const s = sceneRef.current;
    if (s) {
      s.camera.position
        .sub(s.controls.target)
        .multiplyScalar(factor)
        .add(s.controls.target);
      s.controls.update();
    }
  };
  const isolated = mode === "risk" && focus !== null;
  const selectedAnatomy = VESSELS.find((vessel) => vessel.key === focus);
  const currentPrediction = stale ? null : prediction;
  const ranked = rankedVessels(currentPrediction);
  const concerning = ranked.filter(({ risk }) => ["high", "moderate"].includes(riskBand(risk.probability_percent)));
  const highest = concerning[0];
  return (
    <div className={"anatomical-stage" + (isolated ? " has-vessel-detail" : "") + (mode === "risk" ? " risk-mode" : "")} ref={stage}>
      <div className="stage-top">
        <div>
          <span className="stage-overline">{isolated ? "ISOLATED ARTERY" : "ANATOMICAL ATLAS"}</span>
          <p>{isolated ? `${focus.toUpperCase()} · reference anatomy` : "The coronary heart"}</p>
        </div>
        <div className="segmented dark">
          <button
            aria-pressed={mode === "anatomy"}
            onClick={() => { setMode("anatomy"); focusVessel(null); }}
          >
            Anatomy
          </button>
          <button
            aria-pressed={mode === "risk"}
            onClick={() => { setMode("risk"); focusVessel(null); }}
          >
            Risk map
          </button>
        </div>
      </div>
      {mode === "risk" && (
        <div className="risk-attention" data-risk={stale ? "unknown" : riskBand(highest?.risk.probability_percent)}>
          <div role="status">
            <strong>{stale ? "Inputs changed — reassess" : !currentPrediction ? "No current assessment" : highest ? "Model flags for review" : ranked.length < 3 ? "Incomplete vessel scores" : "No elevated vessel scores"}</strong>
            <p>{stale ? "Previous risk highlights are hidden." : !currentPrediction ? "Run an assessment. Unassessed arteries are gray." : highest ? concerning.map(({ key, risk }) => `${key.toUpperCase()} ${risk.probability_percent.toFixed(1)}%`).join(" · ") : ranked.length < 3 ? "Run a new assessment to obtain all vessel scores." : "Low model scores do not rule out disease."}</p>
          </div>
          {highest && (
            <button onClick={() => focusVessel(highest.key)}>
              <TriangleAlert size={16} /> Inspect {highest.key.toUpperCase()}
            </button>
          )}
        </div>
      )}
      <div className="heart-canvas" ref={host} />
      {(!anatomyData || webglError) && (
        <div className="viewer-state">
          <HeartPulse size={32} />
          <p role="status">
            {webglError
              ? "The 3D view is unavailable in this browser."
              : error
                ? "The reference anatomy could not be loaded."
                : "Loading reference anatomy…"}
          </p>
          {(error || webglError) && (
            <button
              className="button light"
              onClick={() => {
                if (webglError) setAttempt((v) => v + 1);
                else onRetry();
              }}
            >
              Retry 3D view
            </button>
          )}
          <table className="vessel-fallback">
            <caption>Coronary vessel assessment · reference anatomy</caption>
            <thead><tr><th scope="col">Vessel</th><th scope="col">Model result</th></tr></thead>
            <tbody>{VESSELS.map(vessel => {
              const risk = currentPrediction?.vessels[vessel.key.toUpperCase() as "LAD" | "LCX" | "RCA"];
              return <tr key={vessel.key}>
                <th scope="row"><button aria-label={`Select ${vessel.key.toUpperCase()} detail`} aria-pressed={focus === vessel.key} onClick={() => { setMode("risk"); focusVessel(vessel.key); }}>{vessel.key.toUpperCase()}</button></th>
                <td>{stale ? "Needs reassessment" : risk ? `${risk.probability_percent.toFixed(1)}% · ${risk.risk_level} · ${risk.predicted_status ?? "Status unavailable"}` : "Awaiting assessment"}</td>
              </tr>;
            })}</tbody>
          </table>
          <small>Select a vessel for its detail and linked evidence below.</small>
        </div>
      )}
      <div className="stage-side">
        <button aria-label="Zoom in" onClick={() => zoom(0.85)}>
          <Plus size={17} />
        </button>
        <button aria-label="Zoom out" onClick={() => zoom(1.15)}>
          <Minus size={17} />
        </button>
        <button
          aria-label={fullscreen ? "Exit fullscreen heart viewer" : "Expand heart viewer"}
          onClick={async () => {
            setFullscreenMessage(await toggleFullscreen(stage.current, document));
          }}
        >
          <Maximize2 size={16} />
        </button>
      </div>
      <div className="stage-caption">
        <span>BodyParts3D · reference anatomy</span>
        <span>Click an artery · drag to rotate · scroll to zoom</span>
      </div>
      {isolated && selectedAnatomy && (
        <VesselDetail
          name={selectedAnatomy.name}
          risk={currentPrediction?.vessels[focus.toUpperCase() as "LAD" | "LCX" | "RCA"]}
          contributions={currentPrediction?.shap_explanations[focus.toUpperCase() as "LAD" | "LCX" | "RCA"]}
          stale={stale}
        />
      )}
      <div className="stage-bottom">
        <div className="vessel-controls" aria-label="Focus a coronary vessel">
          {VESSELS.map((v) => (
            <button
              key={v.key}
              aria-pressed={focus === v.key}
              onClick={() => focusVessel(focus === v.key ? null : v.key)}
            >
              <i
                style={{
                  background:
                    mode === "risk"
                      ? currentPrediction?.vessel_colors_3d[v.key] || "#94a3b8"
                      : v.color,
                }}
              />
              {v.key.toUpperCase()}
              {mode === "risk" && currentPrediction && (
                <span>
                  {currentPrediction.vessels[
                    v.key.toUpperCase() as "LAD" | "LCX" | "RCA"
                  ].probability_percent.toFixed(0)}
                  %
                </span>
              )}
              {mode === "risk" && currentPrediction && ["high", "moderate"].includes(riskBand(currentPrediction.vessels[v.key.toUpperCase() as "LAD" | "LCX" | "RCA"].probability_percent)) && <TriangleAlert size={12} aria-label="Elevated model score" />}
            </button>
          ))}
          <button className="reset-view" onClick={() => focusVessel(null)}>
            <RotateCcw size={13} />
            {isolated ? "All arteries" : "Reset view"}
          </button>
        </div>
        <div className="tissue-controls">
          <label>
            <input
              type="checkbox"
              disabled={isolated}
              checked={visible}
              onChange={(e) => setVisible(e.target.checked)}
            />
            Tissue
          </label>
          <label className="opacity-control">
            {mode === "risk" ? "Tissue dimmed" : "Opacity"}
            <input
              aria-label="Tissue opacity"
              disabled={isolated || !visible || mode === "risk"}
              type="range"
              min="0.1"
              max="1"
              step="0.05"
              value={opacity}
              onChange={(e) => setOpacity(Number(e.target.value))}
            />
          </label>
          <button
            aria-pressed={pulse && !reduced}
            disabled={reduced}
            onClick={() => setPulse((v) => !v)}
          >
            <HeartPulse size={15} />
            Pulse {pulse && !reduced ? "on" : "off"}
          </button>
        </div>
        {fullscreenMessage && <p className="stage-note" role="status">{fullscreenMessage}</p>}
        <p className="stage-note">
          {mode === "risk" && !prediction
            ? "Run a current assessment to see risk colors. "
            : ""}
          {reduced ? "Reduced motion enabled. " : "Pulse is illustrative. "}
          Reference anatomy is not patient-specific.
        </p>
      </div>
    </div>
  );
}

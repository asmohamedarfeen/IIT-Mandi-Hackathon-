import { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { RotateCcw, Maximize2, HeartPulse, Minus, Plus } from "lucide-react";
import { ThreeDAnatomyPayload, PredictionResponse } from "../utils/types";
import { VESSELS } from "../utils/vessels";
import { toggleFullscreen } from "../utils/fullscreen";
import {
  createAnatomyMeshes,
  updateAnatomyMeshes,
  disposeAnatomyMeshes,
  type AnatomyMesh,
} from "../utils/anatomy";
type Vessel = "lad" | "lcx" | "rca";
interface SceneState {
  renderer: THREE.WebGLRenderer;
  camera: THREE.PerspectiveCamera;
  controls: OrbitControls;
  group: THREE.Group;
  meshes: Record<string, AnatomyMesh>;
  fit: () => void;
  center: THREE.Vector3;
  distance: number;
}
export function HeartViewer3D({
  anatomyData,
  prediction,
  error,
  onRetry,
}: {
  anatomyData: ThreeDAnatomyPayload | null;
  prediction: PredictionResponse | null;
  error: boolean;
  onRetry: () => void;
}) {
  const host = useRef<HTMLDivElement>(null),
    stage = useRef<HTMLDivElement>(null),
    sceneRef = useRef<SceneState | null>(null),
    pulseRef = useRef(false);
  const [mode, setMode] = useState<"anatomy" | "risk">("anatomy"),
    [pulse, setPulse] = useState(false),
    [opacity, setOpacity] = useState(1),
    [visible, setVisible] = useState(true),
    [focus, setFocus] = useState<Vessel | null>(null),
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
  }, [pulse, reduced]);
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
    const box = new THREE.Box3().setFromObject(group),
      center = box.getCenter(new THREE.Vector3()),
      size = box.getSize(new THREE.Vector3());
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.enablePan = false;
    controls.minDistance = 2;
    controls.maxDistance = 12;
    controls.target.copy(center);
    const state: SceneState = {
      renderer,
      camera,
      controls,
      group,
      meshes,
      center,
      distance: 7,
      fit: () => {
        const halfFov = THREE.MathUtils.degToRad(camera.fov / 2);
        state.distance =
          Math.max(
            size.y / 2 / Math.tan(halfFov),
            size.x / 2 / (Math.tan(halfFov) * camera.aspect),
          ) +
          size.z / 2;
        state.distance *= 1.13;
        camera.position
          .copy(center)
          .add(
            new THREE.Vector3(0.14, 0.03, 1)
              .normalize()
              .multiplyScalar(state.distance),
          );
        controls.target.copy(center);
        controls.update();
      },
    };
    sceneRef.current = state;
    const resize = () => {
      const width = element.clientWidth,
        height = element.clientHeight;
      if (!width || !height) return;
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
      renderer.setSize(width, height);
      state.fit();
    };
    const observer = new ResizeObserver(resize);
    observer.observe(element);
    resize();
    const lost = (event: Event) => {
      event.preventDefault();
      setWebglError(true);
    };
    renderer.domElement.addEventListener("webglcontextlost", lost);
    let frame = 0;
    const start = performance.now();
    const animate = (now: number) => {
      frame = requestAnimationFrame(animate);
      const t = ((now - start) / 1000) % 1.15;
      const beat = pulseRef.current
        ? 0.012 * Math.exp(-(((t - 0.18) / 0.07) ** 2)) +
          0.006 * Math.exp(-(((t - 0.35) / 0.09) ** 2))
        : 0;
      group.scale.setScalar(1 + beat);
      controls.update();
      renderer.render(scene, camera);
    };
    frame = requestAnimationFrame(animate);
    return () => {
      cancelAnimationFrame(frame);
      observer.disconnect();
      controls.dispose();
      renderer.domElement.removeEventListener("webglcontextlost", lost);
      disposeAnatomyMeshes(meshes);
      scene.clear();
      renderer.dispose();
      renderer.forceContextLoss();
      renderer.domElement.remove();
      sceneRef.current = null;
    };
  }, [anatomyData, attempt]);
  useEffect(() => {
    const state = sceneRef.current;
    if (!state) return;
    updateAnatomyMeshes(state.meshes, {
      mode,
      prediction,
      opacity,
      visible,
      focus,
    });
  }, [anatomyData, attempt, mode, prediction, opacity, visible, focus]);
  function focusVessel(vessel: Vessel | null) {
    setFocus(vessel);
    const state = sceneRef.current;
    if (!state) return;
    if (!vessel) {
      state.fit();
      return;
    }
    const mesh = state.meshes[vessel];
    if (!mesh) return;
    const center = mesh.geometry.boundingBox!.getCenter(new THREE.Vector3());
    const directions = {
      lad: new THREE.Vector3(0.5, 0.15, 1),
      lcx: new THREE.Vector3(0.9, 0.25, -1),
      rca: new THREE.Vector3(-0.8, 0.1, 1),
    };
    state.controls.target.copy(center);
    state.camera.position
      .copy(center)
      .add(directions[vessel].normalize().multiplyScalar(state.distance * 0.8));
    state.controls.update();
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
  return (
    <div className="anatomical-stage" ref={stage}>
      <div className="stage-top">
        <div>
          <span className="stage-overline">ANATOMICAL ATLAS</span>
          <p>The coronary heart</p>
        </div>
        <div className="segmented dark">
          <button
            aria-pressed={mode === "anatomy"}
            onClick={() => setMode("anatomy")}
          >
            Anatomy
          </button>
          <button
            aria-pressed={mode === "risk"}
            onClick={() => setMode("risk")}
          >
            Risk map
          </button>
        </div>
      </div>
      <div className="heart-canvas" ref={host} />
      {(!anatomyData || webglError) && (
        <div className="viewer-state" role="status">
          <HeartPulse size={32} />
          <p>
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
          <small>Assessment results remain available below.</small>
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
        <span>Drag to rotate / scroll to zoom</span>
      </div>
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
                    mode === "risk" && prediction
                      ? prediction.vessel_colors_3d[v.key]
                      : v.color,
                }}
              />
              {v.key.toUpperCase()}
              {mode === "risk" && prediction && (
                <span>
                  {prediction.vessels[
                    v.key.toUpperCase() as "LAD" | "LCX" | "RCA"
                  ].probability_percent.toFixed(0)}
                  %
                </span>
              )}
            </button>
          ))}
          <button className="reset-view" onClick={() => focusVessel(null)}>
            <RotateCcw size={13} />
            Reset view
          </button>
        </div>
        <div className="tissue-controls">
          <label>
            <input
              type="checkbox"
              checked={visible}
              onChange={(e) => setVisible(e.target.checked)}
            />
            Tissue
          </label>
          <label className="opacity-control">
            Opacity
            <input
              aria-label="Tissue opacity"
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

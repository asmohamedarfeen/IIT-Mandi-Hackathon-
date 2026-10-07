import React, { useEffect, useRef, useState, useCallback } from 'react';
import * as THREE from 'three';
import {
  RotateCcw,
  Eye,
  Zap,
  Layers,
  Activity,
  Sliders,
  Sparkles,
  Info,
  Check
} from 'lucide-react';
import { ThreeDAnatomyPayload } from '../utils/types';

interface HeartViewer3DProps {
  anatomyData: ThreeDAnatomyPayload | null;
  vesselColors: {
    lad: string;
    lcx: string;
    rca: string;
    myocardium: string;
  };
  vesselRisks?: {
    LAD?: { probability_percent: number; risk_level: string };
    LCX?: { probability_percent: number; risk_level: string };
    RCA?: { probability_percent: number; risk_level: string };
  };
  isLoading?: boolean;
}

// Fixed anatomical centroids computed from BodyParts3D vertices
const VESSEL_CENTROIDS: Record<string, THREE.Vector3> = {
  lad: new THREE.Vector3(0.814, 0.28, 0.76),
  lcx: new THREE.Vector3(0.561, -0.264, -0.877),
  rca: new THREE.Vector3(-0.649, -0.236, 0.612),
};

const ANATOMICAL_COLORS: Record<string, string> = {
  lad: '#06B6D4', // Cyan
  lcx: '#A855F7', // Purple/Violet
  rca: '#F59E0B', // Amber/Orange
};

const VESSEL_METADATA: Record<string, { name: string; territory: string; code: string }> = {
  lad: {
    code: 'LAD',
    name: 'Left Anterior Descending',
    territory: 'Anterior wall, apex & anterior interventricular septum',
  },
  lcx: {
    code: 'LCX',
    name: 'Left Circumflex Artery',
    territory: 'Lateral & posterior left ventricular myocardium',
  },
  rca: {
    code: 'RCA',
    name: 'Right Coronary Artery',
    territory: 'Right ventricle, inferior LV wall & conduction nodes',
  },
};

export const HeartViewer3D: React.FC<HeartViewer3DProps> = ({
  anatomyData,
  vesselColors,
  vesselRisks,
  isLoading = false,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const heartGroupRef = useRef<THREE.Group | null>(null);
  const meshRefs = useRef<{ [key: string]: THREE.Mesh }>({});

  // View & differentiation states
  const [colorMode, setColorMode] = useState<'anatomy' | 'risk'>('anatomy');
  const [pulseEnabled, setPulseEnabled] = useState(true);
  const [showMyocardium, setShowMyocardium] = useState(true);
  const [myocardiumOpacity, setMyocardiumOpacity] = useState(0.35);
  const [activeVesselFilter, setActiveVesselFilter] = useState<'all' | 'lad' | 'lcx' | 'rca'>('all');
  const [hoveredVessel, setHoveredVessel] = useState<string | null>(null);
  const [showPins, setShowPins] = useState(true);

  // 2D Screen-space coordinates for 3D pinned tags
  const [pins2D, setPins2D] = useState<{
    lad?: { x: number; y: number; visible: boolean };
    lcx?: { x: number; y: number; visible: boolean };
    rca?: { x: number; y: number; visible: boolean };
  }>({});

  // Target rotation for smooth camera/heart orientation
  const targetRotationRef = useRef<{ x: number; y: number } | null>(null);

  // Initialize Three.js scene
  useEffect(() => {
    if (!containerRef.current) return;
    const container = containerRef.current;
    const width = container.clientWidth;
    const height = container.clientHeight;

    // Scene
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x060911);
    sceneRef.current = scene;

    // Camera
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
    camera.position.set(0, 0, 4.2);
    cameraRef.current = camera;

    // Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.25;
    rendererRef.current = renderer;

    container.innerHTML = '';
    container.appendChild(renderer.domElement);

    // Lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.9);
    scene.add(ambientLight);

    const keyLight = new THREE.DirectionalLight(0xffffff, 1.4);
    keyLight.position.set(6, 8, 6);
    scene.add(keyLight);

    const fillLight = new THREE.DirectionalLight(0x38bdf8, 0.7);
    fillLight.position.set(-6, -4, -4);
    scene.add(fillLight);

    const backLight = new THREE.DirectionalLight(0xa855f7, 0.5);
    backLight.position.set(0, 6, -8);
    scene.add(backLight);

    // Heart container group
    const heartGroup = new THREE.Group();
    heartGroup.rotation.y = 0.25;
    heartGroup.rotation.x = 0.1;
    scene.add(heartGroup);
    heartGroupRef.current = heartGroup;

    // Orbit & Pan Controls
    let isDragging = false;
    let prevMousePos = { x: 0, y: 0 };

    const onMouseDown = (e: MouseEvent) => {
      isDragging = true;
      targetRotationRef.current = null; // user manual control cancels auto-alignment
      prevMousePos = { x: e.clientX, y: e.clientY };
    };

    const onMouseMove = (e: MouseEvent) => {
      if (!heartGroupRef.current) return;

      if (isDragging) {
        const deltaX = e.clientX - prevMousePos.x;
        const deltaY = e.clientY - prevMousePos.y;
        heartGroupRef.current.rotation.y += deltaX * 0.008;
        heartGroupRef.current.rotation.x += deltaY * 0.008;
        prevMousePos = { x: e.clientX, y: e.clientY };
      }
    };

    const onMouseUp = () => {
      isDragging = false;
    };

    const onWheel = (e: WheelEvent) => {
      e.preventDefault();
      if (!cameraRef.current) return;
      cameraRef.current.position.z = Math.max(
        2.2,
        Math.min(7.5, cameraRef.current.position.z + e.deltaY * 0.003)
      );
    };

    container.addEventListener('mousedown', onMouseDown);
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
    container.addEventListener('wheel', onWheel, { passive: false });

    // Touch Support
    let touchStartDist = 0;
    const onTouchStart = (e: TouchEvent) => {
      targetRotationRef.current = null;
      if (e.touches.length === 1) {
        isDragging = true;
        prevMousePos = { x: e.touches[0].clientX, y: e.touches[0].clientY };
      } else if (e.touches.length === 2) {
        const dx = e.touches[0].clientX - e.touches[1].clientX;
        const dy = e.touches[0].clientY - e.touches[1].clientY;
        touchStartDist = Math.hypot(dx, dy);
      }
    };

    const onTouchMove = (e: TouchEvent) => {
      if (e.touches.length === 1 && isDragging && heartGroupRef.current) {
        const deltaX = e.touches[0].clientX - prevMousePos.x;
        const deltaY = e.touches[0].clientY - prevMousePos.y;
        heartGroupRef.current.rotation.y += deltaX * 0.008;
        heartGroupRef.current.rotation.x += deltaY * 0.008;
        prevMousePos = { x: e.touches[0].clientX, y: e.touches[0].clientY };
      } else if (e.touches.length === 2 && cameraRef.current) {
        const dx = e.touches[0].clientX - e.touches[1].clientX;
        const dy = e.touches[0].clientY - e.touches[1].clientY;
        const dist = Math.hypot(dx, dy);
        const factor = (touchStartDist - dist) * 0.01;
        cameraRef.current.position.z = Math.max(2.2, Math.min(7.5, cameraRef.current.position.z + factor));
        touchStartDist = dist;
      }
    };

    const onTouchEnd = () => {
      isDragging = false;
    };

    container.addEventListener('touchstart', onTouchStart, { passive: true });
    window.addEventListener('touchmove', onTouchMove, { passive: true });
    window.addEventListener('touchend', onTouchEnd, { passive: true });

    // Animation Loop
    let animId: number;
    const clock = new THREE.Clock();

    const animate = () => {
      animId = requestAnimationFrame(animate);

      if (heartGroupRef.current) {
        // Smooth interpolation to target rotation if set
        if (targetRotationRef.current) {
          heartGroupRef.current.rotation.y +=
            (targetRotationRef.current.y - heartGroupRef.current.rotation.y) * 0.08;
          heartGroupRef.current.rotation.x +=
            (targetRotationRef.current.x - heartGroupRef.current.rotation.x) * 0.08;
          if (
            Math.abs(targetRotationRef.current.y - heartGroupRef.current.rotation.y) < 0.005 &&
            Math.abs(targetRotationRef.current.x - heartGroupRef.current.rotation.x) < 0.005
          ) {
            targetRotationRef.current = null;
          }
        } else if (!isDragging && activeVesselFilter === 'all') {
          // Slow passive rotation when idle
          heartGroupRef.current.rotation.y += 0.0012;
        }

        // Heartbeat pulsation
        if (pulseEnabled) {
          const t = clock.getElapsedTime() * 3.5;
          const beat = Math.sin(t) * Math.exp(-Math.pow((t % Math.PI) - 1.5, 2)) * 0.035;
          const s = 1.0 + Math.max(0, beat);
          heartGroupRef.current.scale.set(s, s, s);
        } else {
          heartGroupRef.current.scale.set(1, 1, 1);
        }

        // Project 3D centroids to 2D screen positions for floating pins
        if (containerRef.current && cameraRef.current) {
          const w = containerRef.current.clientWidth;
          const h = containerRef.current.clientHeight;
          const newPins: any = {};

          ['lad', 'lcx', 'rca'].forEach((key) => {
            const centroid = VESSEL_CENTROIDS[key];
            if (centroid) {
              const worldPos = centroid.clone().applyMatrix4(heartGroupRef.current!.matrixWorld);
              const screenPos = worldPos.clone().project(cameraRef.current!);

              // Visible if in front of camera
              const isVisible = screenPos.z < 1.0;
              const x = (screenPos.x * 0.5 + 0.5) * w;
              const y = (-screenPos.y * 0.5 + 0.5) * h;

              newPins[key] = { x, y, visible: isVisible };
            }
          });
          setPins2D(newPins);
        }
      }

      renderer.render(scene, camera);
    };

    animate();

    const onResize = () => {
      if (!container || !renderer || !camera) return;
      const w = container.clientWidth;
      const h = container.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener('resize', onResize);

    return () => {
      cancelAnimationFrame(animId);
      container.removeEventListener('mousedown', onMouseDown);
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
      container.removeEventListener('wheel', onWheel);
      container.removeEventListener('touchstart', onTouchStart);
      window.removeEventListener('touchmove', onTouchMove);
      window.removeEventListener('touchend', onTouchEnd);
      window.removeEventListener('resize', onResize);
      renderer.dispose();
    };
  }, [pulseEnabled, activeVesselFilter]);

  // Build Geometry Meshes from Anatomy Data
  useEffect(() => {
    if (!anatomyData || !heartGroupRef.current) return;
    const group = heartGroupRef.current;

    // Clean existing
    while (group.children.length > 0) {
      const obj = group.children[0];
      group.remove(obj);
      if (obj instanceof THREE.Mesh) {
        obj.geometry.dispose();
        if (Array.isArray(obj.material)) obj.material.forEach((m) => m.dispose());
        else obj.material.dispose();
      }
    }
    meshRefs.current = {};

    const structures = anatomyData.structures;

    // 1. Myocardium Shell
    if (structures.myocardium) {
      const geo = new THREE.BufferGeometry();
      geo.setAttribute(
        'position',
        new THREE.Float32BufferAttribute(structures.myocardium.positions, 3)
      );
      geo.setIndex(structures.myocardium.indices);
      geo.computeVertexNormals();

      const mat = new THREE.MeshStandardMaterial({
        color: new THREE.Color('#334155'),
        roughness: 0.65,
        metalness: 0.15,
        transparent: true,
        opacity: myocardiumOpacity,
        depthWrite: false,
        side: THREE.DoubleSide,
      });

      const mesh = new THREE.Mesh(geo, mat);
      mesh.name = 'myocardium';
      mesh.visible = showMyocardium;
      group.add(mesh);
      meshRefs.current['myocardium'] = mesh;
    }

    // Helper for creating coronary artery meshes
    const addVesselMesh = (key: 'lad' | 'lcx' | 'rca') => {
      if (!structures[key]) return;
      const geo = new THREE.BufferGeometry();
      geo.setAttribute('position', new THREE.Float32BufferAttribute(structures[key].positions, 3));
      geo.setIndex(structures[key].indices);
      geo.computeVertexNormals();

      const initialHex =
        colorMode === 'anatomy' ? ANATOMICAL_COLORS[key] : vesselColors[key] || '#10B981';

      const mat = new THREE.MeshStandardMaterial({
        color: new THREE.Color(initialHex),
        roughness: 0.2,
        metalness: 0.5,
        emissive: new THREE.Color(initialHex),
        emissiveIntensity: 0.4,
        side: THREE.DoubleSide,
        transparent: true,
        opacity: 1.0,
      });

      const mesh = new THREE.Mesh(geo, mat);
      mesh.name = key;
      group.add(mesh);
      meshRefs.current[key] = mesh;
    };

    addVesselMesh('lad');
    addVesselMesh('lcx');
    addVesselMesh('rca');
  }, [anatomyData]);

  // Update Materials based on Mode, Filter, and Hover
  useEffect(() => {
    ['lad', 'lcx', 'rca'].forEach((key) => {
      const mesh = meshRefs.current[key];
      if (!mesh || !(mesh.material instanceof THREE.MeshStandardMaterial)) return;

      const isFilteredActive = activeVesselFilter === 'all' || activeVesselFilter === key;
      const isHovered = hoveredVessel === key;

      // Base color depends on color mode
      const baseHex =
        colorMode === 'anatomy'
          ? ANATOMICAL_COLORS[key]
          : vesselColors[key as 'lad' | 'lcx' | 'rca'] || '#10B981';

      mesh.material.color.set(baseHex);

      if (isFilteredActive) {
        mesh.material.opacity = 1.0;
        mesh.material.emissive.set(baseHex);
        mesh.material.emissiveIntensity = isHovered ? 0.9 : activeVesselFilter === key ? 0.75 : 0.4;
      } else {
        // Dim other vessels when one territory is isolated
        mesh.material.opacity = 0.15;
        mesh.material.emissive.set('#000000');
        mesh.material.emissiveIntensity = 0.0;
      }
    });

    const myoMesh = meshRefs.current['myocardium'];
    if (myoMesh && myoMesh.material instanceof THREE.MeshStandardMaterial) {
      myoMesh.visible = showMyocardium;
      myoMesh.material.opacity = myocardiumOpacity;
    }
  }, [colorMode, vesselColors, activeVesselFilter, hoveredVessel, showMyocardium, myocardiumOpacity]);

  // Rotate camera smoothly to territory
  const focusTerritory = useCallback((territory: 'all' | 'lad' | 'lcx' | 'rca') => {
    setActiveVesselFilter(territory);

    if (territory === 'all') {
      targetRotationRef.current = { x: 0.1, y: 0.25 };
      if (cameraRef.current) cameraRef.current.position.set(0, 0, 4.2);
    } else if (territory === 'lad') {
      // Front anterior groove
      targetRotationRef.current = { x: 0.1, y: 0.1 };
      if (cameraRef.current) cameraRef.current.position.set(0, 0, 3.8);
    } else if (territory === 'lcx') {
      // Rotate around to lateral/posterior circumflex branch
      targetRotationRef.current = { x: 0.15, y: -1.35 };
      if (cameraRef.current) cameraRef.current.position.set(0, 0, 3.8);
    } else if (territory === 'rca') {
      // Rotate to right atrioventricular groove
      targetRotationRef.current = { x: 0.1, y: 1.45 };
      if (cameraRef.current) cameraRef.current.position.set(0, 0, 3.8);
    }
  }, []);

  const resetCamera = () => {
    focusTerritory('all');
  };

  return (
    <div className="relative flex flex-col h-full w-full rounded-2xl border border-slate-800 bg-slate-900/40 p-4 backdrop-blur-md overflow-hidden">
      {/* Top Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800/80 pb-3">
        <div>
          <h2 className="text-base font-semibold text-white flex items-center gap-2">
            <Activity className="h-4 w-4 text-rose-500 animate-pulse" />
            3D Anatomical Coronary Tree
          </h2>
          <p className="text-xs text-slate-400">
            Differentiated spatial mapping of LAD, LCX, and RCA coronary arterial branches
          </p>
        </div>

        {/* Color Mode Toggle (Anatomical Differentiation vs Risk Level) */}
        <div className="flex items-center gap-2">
          <div className="flex items-center rounded-lg border border-slate-800 bg-slate-950 p-1 text-xs">
            <button
              onClick={() => setColorMode('anatomy')}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md font-medium transition-all ${
                colorMode === 'anatomy'
                  ? 'bg-sky-500/20 text-sky-300 border border-sky-500/30 shadow'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
              title="Show distinct anatomical colors for LAD, LCX, and RCA"
            >
              <Sparkles className="h-3.5 w-3.5 text-cyan-400" />
              <span>Differentiate Regions</span>
            </button>
            <button
              onClick={() => setColorMode('risk')}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md font-medium transition-all ${
                colorMode === 'risk'
                  ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30 shadow'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
              title="Color vessels based on predicted stenosis risk percentages"
            >
              <Activity className="h-3.5 w-3.5 text-rose-400" />
              <span>Stenosis Risk</span>
            </button>
          </div>
        </div>
      </div>

      {/* Territory Filter & Differentiation Legend */}
      <div className="mt-3 flex flex-wrap items-center justify-between gap-2 bg-slate-950/60 p-2.5 rounded-xl border border-slate-800/80">
        {/* Territory Focus Tabs */}
        <div className="flex items-center gap-1.5 text-xs">
          <span className="text-slate-400 font-medium mr-1 hidden sm:inline">Territory:</span>
          <button
            onClick={() => focusTerritory('all')}
            className={`px-2.5 py-1 rounded-lg font-medium transition-all ${
              activeVesselFilter === 'all'
                ? 'bg-slate-800 text-white border border-slate-600'
                : 'text-slate-400 hover:bg-slate-900 hover:text-slate-200'
            }`}
          >
            All Vessels
          </button>
          <button
            onClick={() => focusTerritory('lad')}
            onMouseEnter={() => setHoveredVessel('lad')}
            onMouseLeave={() => setHoveredVessel(null)}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg font-medium border transition-all ${
              activeVesselFilter === 'lad'
                ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/50 shadow-md shadow-cyan-500/10'
                : 'text-slate-300 border-slate-800 hover:border-cyan-500/40 hover:bg-slate-900'
            }`}
          >
            <span className="h-2 w-2 rounded-full bg-[#06B6D4]" />
            <span>LAD (Anterior)</span>
          </button>
          <button
            onClick={() => focusTerritory('lcx')}
            onMouseEnter={() => setHoveredVessel('lcx')}
            onMouseLeave={() => setHoveredVessel(null)}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg font-medium border transition-all ${
              activeVesselFilter === 'lcx'
                ? 'bg-purple-500/20 text-purple-300 border-purple-500/50 shadow-md shadow-purple-500/10'
                : 'text-slate-300 border-slate-800 hover:border-purple-500/40 hover:bg-slate-900'
            }`}
          >
            <span className="h-2 w-2 rounded-full bg-[#A855F7]" />
            <span>LCX (Lateral)</span>
          </button>
          <button
            onClick={() => focusTerritory('rca')}
            onMouseEnter={() => setHoveredVessel('rca')}
            onMouseLeave={() => setHoveredVessel(null)}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg font-medium border transition-all ${
              activeVesselFilter === 'rca'
                ? 'bg-amber-500/20 text-amber-300 border-amber-500/50 shadow-md shadow-amber-500/10'
                : 'text-slate-300 border-slate-800 hover:border-amber-500/40 hover:bg-slate-900'
            }`}
          >
            <span className="h-2 w-2 rounded-full bg-[#F59E0B]" />
            <span>RCA (Right)</span>
          </button>
        </div>

        {/* Legend Indicator */}
        <div className="flex items-center gap-2 text-[11px] text-slate-400">
          {colorMode === 'anatomy' ? (
            <div className="flex items-center gap-2">
              <span className="flex items-center gap-1 text-cyan-400">
                <span className="h-2 w-2 rounded-full bg-cyan-400" /> LAD
              </span>
              <span className="flex items-center gap-1 text-purple-400">
                <span className="h-2 w-2 rounded-full bg-purple-400" /> LCX
              </span>
              <span className="flex items-center gap-1 text-amber-400">
                <span className="h-2 w-2 rounded-full bg-amber-400" /> RCA
              </span>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <span className="flex items-center gap-1 text-emerald-400">
                <span className="h-2 w-2 rounded-full bg-emerald-500" /> &lt;35%
              </span>
              <span className="flex items-center gap-1 text-amber-400">
                <span className="h-2 w-2 rounded-full bg-amber-500" /> 35-65%
              </span>
              <span className="flex items-center gap-1 text-rose-400">
                <span className="h-2 w-2 rounded-full bg-rose-500" /> &ge;65%
              </span>
            </div>
          )}
        </div>
      </div>

      {/* 3D Canvas Container */}
      <div className="relative flex-1 min-h-[390px] w-full mt-2 rounded-xl overflow-hidden cursor-grab active:cursor-grabbing">
        <div ref={containerRef} className="absolute inset-0 h-full w-full" />

        {/* Loading Overlay */}
        {isLoading && (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-slate-950/80 backdrop-blur-sm z-20">
            <div className="h-10 w-10 animate-spin rounded-full border-4 border-rose-500 border-t-transparent" />
            <p className="mt-3 text-xs font-medium text-slate-300">Evaluating 3D Coronary Perfusion...</p>
          </div>
        )}

        {/* Floating 3D Positioned Territory Pins */}
        {showPins &&
          (['lad', 'lcx', 'rca'] as const).map((key) => {
            const pin = pins2D[key];
            if (!pin || !pin.visible) return null;

            const meta = VESSEL_METADATA[key];
            const riskInfo = vesselRisks?.[meta.code as 'LAD' | 'LCX' | 'RCA'];
            const isTargetActive = activeVesselFilter === 'all' || activeVesselFilter === key;
            const isHovered = hoveredVessel === key;
            const regionColor = ANATOMICAL_COLORS[key];
            const riskColor = vesselColors[key] || '#10B981';

            return (
              <div
                key={key}
                style={{
                  left: `${pin.x}px`,
                  top: `${pin.y}px`,
                  transform: 'translate(-50%, -100%)',
                }}
                className={`absolute pointer-events-auto transition-transform z-10 ${
                  isTargetActive ? 'opacity-100 scale-100' : 'opacity-30 scale-90'
                }`}
                onMouseEnter={() => setHoveredVessel(key)}
                onMouseLeave={() => setHoveredVessel(null)}
                onClick={() => focusTerritory(key)}
              >
                <div
                  className={`group cursor-pointer rounded-lg border px-2.5 py-1.5 shadow-xl backdrop-blur-md flex items-center gap-2 transition-all ${
                    isHovered || activeVesselFilter === key
                      ? 'border-white bg-slate-900/95 shadow-lg scale-105'
                      : 'border-slate-700/80 bg-slate-950/80 hover:border-slate-500'
                  }`}
                  style={{
                    boxShadow: isHovered ? `0 0 15px ${regionColor}50` : undefined,
                  }}
                >
                  <div
                    className="flex h-5 w-5 items-center justify-center rounded-full text-[10px] font-bold text-white shrink-0"
                    style={{ backgroundColor: colorMode === 'anatomy' ? regionColor : riskColor }}
                  >
                    {meta.code[0]}
                  </div>

                  <div className="flex flex-col text-left">
                    <div className="flex items-center gap-1.5">
                      <span className="text-xs font-bold text-white">{meta.code}</span>
                      {riskInfo && (
                        <span
                          className="rounded px-1 text-[10px] font-mono font-semibold"
                          style={{
                            color: riskColor,
                            backgroundColor: `${riskColor}20`,
                          }}
                        >
                          {riskInfo.probability_percent}%
                        </span>
                      )}
                    </div>
                    <span className="text-[10px] text-slate-400 font-normal leading-tight hidden group-hover:block whitespace-nowrap">
                      {meta.name}
                    </span>
                  </div>
                </div>

                {/* Pin pointer stem */}
                <div
                  className="mx-auto h-2 w-0.5"
                  style={{ backgroundColor: regionColor }}
                />
              </div>
            );
          })}

        {/* Hover Territory Card */}
        {hoveredVessel && VESSEL_METADATA[hoveredVessel] && (
          <div className="absolute top-3 left-3 z-20 max-w-xs rounded-xl border border-slate-700 bg-slate-950/90 p-3 shadow-2xl backdrop-blur-md animate-in fade-in">
            <div className="flex items-center gap-2">
              <span
                className="h-3 w-3 rounded-full"
                style={{ backgroundColor: ANATOMICAL_COLORS[hoveredVessel] }}
              />
              <h4 className="text-xs font-bold text-white">
                {VESSEL_METADATA[hoveredVessel].name} ({VESSEL_METADATA[hoveredVessel].code})
              </h4>
            </div>
            <p className="mt-1 text-[11px] text-slate-400">
              {VESSEL_METADATA[hoveredVessel].territory}
            </p>
            {vesselRisks?.[VESSEL_METADATA[hoveredVessel].code as 'LAD' | 'LCX' | 'RCA'] && (
              <div className="mt-2 flex items-center justify-between border-t border-slate-800 pt-2 text-xs">
                <span className="text-slate-400">Stenosis Likelihood:</span>
                <span className="font-mono font-bold text-white">
                  {vesselRisks[VESSEL_METADATA[hoveredVessel].code as 'LAD' | 'LCX' | 'RCA']?.probability_percent}% (
                  {vesselRisks[VESSEL_METADATA[hoveredVessel].code as 'LAD' | 'LCX' | 'RCA']?.risk_level})
                </span>
              </div>
            )}
          </div>
        )}

        {/* Bottom Utility Controls */}
        <div className="absolute bottom-3 left-3 flex flex-wrap items-center gap-1.5 z-10">
          <button
            onClick={() => setPulseEnabled(!pulseEnabled)}
            className={`flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-medium border backdrop-blur-md transition-all ${
              pulseEnabled
                ? 'bg-rose-500/20 border-rose-500/40 text-rose-300'
                : 'bg-slate-800/60 border-slate-700 text-slate-400 hover:text-slate-200'
            }`}
            title="Toggle Cardiac Pulsation"
          >
            <Zap className="h-3.5 w-3.5" />
            <span>Pulse</span>
          </button>

          <button
            onClick={() => setShowMyocardium(!showMyocardium)}
            className={`flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-medium border backdrop-blur-md transition-all ${
              showMyocardium
                ? 'bg-sky-500/20 border-sky-500/40 text-sky-300'
                : 'bg-slate-800/60 border-slate-700 text-slate-400 hover:text-slate-200'
            }`}
            title="Toggle Myocardium Shell"
          >
            <Layers className="h-3.5 w-3.5" />
            <span>Chambers</span>
          </button>

          <button
            onClick={() => setShowPins(!showPins)}
            className={`flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-medium border backdrop-blur-md transition-all ${
              showPins
                ? 'bg-cyan-500/20 border-cyan-500/40 text-cyan-300'
                : 'bg-slate-800/60 border-slate-700 text-slate-400 hover:text-slate-200'
            }`}
            title="Toggle 3D Vessel Floating Labels"
          >
            <Info className="h-3.5 w-3.5" />
            <span>3D Labels</span>
          </button>

          <button
            onClick={resetCamera}
            className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-medium bg-slate-800/60 border border-slate-700 text-slate-300 hover:bg-slate-700 backdrop-blur-md transition-all"
            title="Reset 3D Viewpoint"
          >
            <RotateCcw className="h-3.5 w-3.5" />
            <span>Reset</span>
          </button>
        </div>

        {/* Myocardium Transparency Slider Popover */}
        {showMyocardium && (
          <div className="absolute bottom-3 right-3 flex items-center gap-2 bg-slate-900/80 px-2.5 py-1.5 rounded-lg border border-slate-800 text-xs text-slate-400 backdrop-blur-md z-10">
            <span>Chamber Opacity:</span>
            <input
              type="range"
              min="0.05"
              max="0.75"
              step="0.05"
              value={myocardiumOpacity}
              onChange={(e) => setMyocardiumOpacity(parseFloat(e.target.value))}
              className="h-1.5 w-16 accent-rose-500 cursor-pointer"
            />
          </div>
        )}
      </div>

      <div className="mt-2 text-[11px] text-slate-500 text-center flex items-center justify-center gap-1.5">
        <Eye className="h-3 w-3" />
        <span>Drag to rotate 3D heart &bull; Click LAD / LCX / RCA buttons to isolate & orbit territory &bull; Hover labels for details</span>
      </div>
    </div>
  );
};

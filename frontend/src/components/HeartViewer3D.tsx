import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { RotateCcw, Eye, Zap, Layers, Activity } from 'lucide-react';
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
  
  const [pulseEnabled, setPulseEnabled] = useState(true);
  const [showMyocardium, setShowMyocardium] = useState(true);
  const [focusedVessel, setFocusedVessel] = useState<string | null>(null);

  // Initialize Three.js scene
  useEffect(() => {
    if (!containerRef.current) return;
    const container = containerRef.current;
    const width = container.clientWidth;
    const height = container.clientHeight;

    // Scene
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x070b14);
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
    renderer.toneMappingExposure = 1.2;
    rendererRef.current = renderer;

    container.innerHTML = '';
    container.appendChild(renderer.domElement);

    // Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.85);
    scene.add(ambientLight);

    const dirLight1 = new THREE.DirectionalLight(0xffffff, 1.2);
    dirLight1.position.set(5, 8, 5);
    scene.add(dirLight1);

    const dirLight2 = new THREE.DirectionalLight(0x38bdf8, 0.6);
    dirLight2.position.set(-5, -5, -3);
    scene.add(dirLight2);

    // Heart container group
    const heartGroup = new THREE.Group();
    // Default slight anatomical tilt
    heartGroup.rotation.y = 0.2;
    heartGroup.rotation.x = 0.1;
    scene.add(heartGroup);
    heartGroupRef.current = heartGroup;

    // Mouse Interaction / Orbit Controls (custom lightweight implementation)
    let isDragging = false;
    let prevMousePos = { x: 0, y: 0 };

    const onMouseDown = (e: MouseEvent) => {
      isDragging = true;
      prevMousePos = { x: e.clientX, y: e.clientY };
    };

    const onMouseMove = (e: MouseEvent) => {
      if (!isDragging || !heartGroupRef.current) return;
      const deltaX = e.clientX - prevMousePos.x;
      const deltaY = e.clientY - prevMousePos.y;

      heartGroupRef.current.rotation.y += deltaX * 0.008;
      heartGroupRef.current.rotation.x += deltaY * 0.008;

      prevMousePos = { x: e.clientX, y: e.clientY };
    };

    const onMouseUp = () => {
      isDragging = false;
    };

    const onWheel = (e: WheelEvent) => {
      e.preventDefault();
      if (!cameraRef.current) return;
      cameraRef.current.position.z = Math.max(
        2.2,
        Math.min(8.0, cameraRef.current.position.z + e.deltaY * 0.003)
      );
    };

    container.addEventListener('mousedown', onMouseDown);
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
    container.addEventListener('wheel', onWheel, { passive: false });

    // Touch support for mobile / tablets
    let touchStartDist = 0;
    const onTouchStart = (e: TouchEvent) => {
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
        cameraRef.current.position.z = Math.max(2.2, Math.min(8.0, cameraRef.current.position.z + factor));
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
    let clock = new THREE.Clock();

    const animate = () => {
      animId = requestAnimationFrame(animate);

      if (heartGroupRef.current) {
        // Slow natural idle rotation when not dragging
        if (!isDragging) {
          heartGroupRef.current.rotation.y += 0.0015;
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
      }

      renderer.render(scene, camera);
    };

    animate();

    // Resize Handler
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
  }, [pulseEnabled]);

  // Load and populate 3D meshes when anatomyData changes
  useEffect(() => {
    if (!anatomyData || !heartGroupRef.current) return;
    const group = heartGroupRef.current;

    // Clear existing meshes
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

    // 1. Myocardium (Translucent Chamber Shell)
    if (structures.myocardium) {
      const geo = new THREE.BufferGeometry();
      geo.setAttribute('position', new THREE.Float32BufferAttribute(structures.myocardium.positions, 3));
      geo.setIndex(structures.myocardium.indices);
      geo.computeVertexNormals();

      const mat = new THREE.MeshStandardMaterial({
        color: new THREE.Color('#334155'),
        roughness: 0.7,
        metalness: 0.1,
        transparent: true,
        opacity: 0.45,
        depthWrite: false,
        side: THREE.DoubleSide,
      });

      const mesh = new THREE.Mesh(geo, mat);
      mesh.name = 'myocardium';
      mesh.visible = showMyocardium;
      group.add(mesh);
      meshRefs.current['myocardium'] = mesh;
    }

    // Helper for coronary vessels
    const addCoronaryVessel = (key: 'lad' | 'lcx' | 'rca', defaultColor: string) => {
      if (!structures[key]) return;
      const geo = new THREE.BufferGeometry();
      geo.setAttribute('position', new THREE.Float32BufferAttribute(structures[key].positions, 3));
      geo.setIndex(structures[key].indices);
      geo.computeVertexNormals();

      const mat = new THREE.MeshStandardMaterial({
        color: new THREE.Color(vesselColors[key] || defaultColor),
        roughness: 0.25,
        metalness: 0.4,
        emissive: new THREE.Color(vesselColors[key] || defaultColor),
        emissiveIntensity: 0.35,
        side: THREE.DoubleSide,
      });

      const mesh = new THREE.Mesh(geo, mat);
      mesh.name = key;
      group.add(mesh);
      meshRefs.current[key] = mesh;
    };

    // 2. Coronary Arteries (LAD, LCX, RCA)
    addCoronaryVessel('lad', '#10B981');
    addCoronaryVessel('lcx', '#10B981');
    addCoronaryVessel('rca', '#10B981');
  }, [anatomyData]);

  // Update mesh colors when vesselColors change
  useEffect(() => {
    ['lad', 'lcx', 'rca'].forEach((key) => {
      const mesh = meshRefs.current[key];
      if (mesh && mesh.material instanceof THREE.MeshStandardMaterial) {
        const hex = vesselColors[key as 'lad' | 'lcx' | 'rca'] || '#10B981';
        mesh.material.color.set(hex);
        mesh.material.emissive.set(hex);
        mesh.material.emissiveIntensity = focusedVessel === key ? 0.8 : 0.35;
      }
    });

    const myoMesh = meshRefs.current['myocardium'];
    if (myoMesh) {
      myoMesh.visible = showMyocardium;
    }
  }, [vesselColors, showMyocardium, focusedVessel]);

  const handleResetCamera = () => {
    if (cameraRef.current && heartGroupRef.current) {
      cameraRef.current.position.set(0, 0, 4.2);
      heartGroupRef.current.rotation.set(0.1, 0.2, 0);
      setFocusedVessel(null);
    }
  };

  const handleFocusVessel = (vesselKey: string) => {
    setFocusedVessel(vesselKey === focusedVessel ? null : vesselKey);
    if (!heartGroupRef.current) return;
    if (vesselKey === 'lad') {
      heartGroupRef.current.rotation.set(0.1, 0.1, 0);
    } else if (vesselKey === 'lcx') {
      heartGroupRef.current.rotation.set(0.1, -1.2, 0);
    } else if (vesselKey === 'rca') {
      heartGroupRef.current.rotation.set(0.1, 1.4, 0);
    }
  };

  return (
    <div className="relative flex flex-col h-full w-full rounded-2xl border border-slate-800 bg-slate-900/40 p-4 backdrop-blur-md overflow-hidden">
      {/* Header / Vessel Legend */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800/80 pb-3">
        <div>
          <h2 className="text-base font-semibold text-white flex items-center gap-2">
            <Activity className="h-4 w-4 text-rose-500 animate-pulse" />
            3D Anatomical Coronary Tree
          </h2>
          <p className="text-xs text-slate-400">
            Interactive spatial mapping of patient-specific stenosis risks
          </p>
        </div>

        {/* Risk Color Legend */}
        <div className="flex items-center gap-2 text-xs">
          <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
            <span className="h-2 w-2 rounded-full bg-emerald-500" />
            <span>&lt; 35% Normal</span>
          </div>
          <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-amber-500/10 border border-amber-500/20 text-amber-400">
            <span className="h-2 w-2 rounded-full bg-amber-500" />
            <span>35-65% Borderline</span>
          </div>
          <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-rose-500/10 border border-rose-500/20 text-rose-400">
            <span className="h-2 w-2 rounded-full bg-rose-500" />
            <span>&ge; 65% Stenotic</span>
          </div>
        </div>
      </div>

      {/* 3D Canvas Container */}
      <div className="relative flex-1 min-h-[380px] w-full mt-2 rounded-xl overflow-hidden cursor-grab active:cursor-grabbing">
        <div ref={containerRef} className="absolute inset-0 h-full w-full" />

        {/* Loading Overlay */}
        {isLoading && (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-slate-950/80 backdrop-blur-sm z-20">
            <div className="h-10 w-10 animate-spin rounded-full border-4 border-rose-500 border-t-transparent" />
            <p className="mt-3 text-xs font-medium text-slate-300">Evaluating 3D Coronary Perfusion...</p>
          </div>
        )}

        {/* Overlay Controls */}
        <div className="absolute bottom-3 left-3 flex items-center gap-2 z-10">
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
            title="Toggle Chamber Shell"
          >
            <Layers className="h-3.5 w-3.5" />
            <span>Chambers</span>
          </button>

          <button
            onClick={handleResetCamera}
            className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-medium bg-slate-800/60 border border-slate-700 text-slate-300 hover:bg-slate-700 backdrop-blur-md transition-all"
            title="Reset 3D Camera"
          >
            <RotateCcw className="h-3.5 w-3.5" />
            <span>Reset</span>
          </button>
        </div>

        {/* Quick Vessel Territory Focus Buttons */}
        <div className="absolute top-3 right-3 flex flex-col gap-1.5 z-10">
          <button
            onClick={() => handleFocusVessel('lad')}
            className={`px-3 py-1 rounded-lg text-xs font-semibold border backdrop-blur-md text-left transition-all ${
              focusedVessel === 'lad'
                ? 'bg-slate-800 border-white text-white shadow-lg'
                : 'bg-slate-900/80 border-slate-700/80 text-slate-300 hover:bg-slate-800'
            }`}
          >
            <div className="flex items-center justify-between gap-3">
              <span>LAD</span>
              <span
                className="h-2 w-2 rounded-full"
                style={{ backgroundColor: vesselColors.lad }}
              />
            </div>
            {vesselRisks?.LAD && (
              <span className="text-[10px] text-slate-400 font-normal">
                {vesselRisks.LAD.probability_percent}%
              </span>
            )}
          </button>

          <button
            onClick={() => handleFocusVessel('lcx')}
            className={`px-3 py-1 rounded-lg text-xs font-semibold border backdrop-blur-md text-left transition-all ${
              focusedVessel === 'lcx'
                ? 'bg-slate-800 border-white text-white shadow-lg'
                : 'bg-slate-900/80 border-slate-700/80 text-slate-300 hover:bg-slate-800'
            }`}
          >
            <div className="flex items-center justify-between gap-3">
              <span>LCX</span>
              <span
                className="h-2 w-2 rounded-full"
                style={{ backgroundColor: vesselColors.lcx }}
              />
            </div>
            {vesselRisks?.LCX && (
              <span className="text-[10px] text-slate-400 font-normal">
                {vesselRisks.LCX.probability_percent}%
              </span>
            )}
          </button>

          <button
            onClick={() => handleFocusVessel('rca')}
            className={`px-3 py-1 rounded-lg text-xs font-semibold border backdrop-blur-md text-left transition-all ${
              focusedVessel === 'rca'
                ? 'bg-slate-800 border-white text-white shadow-lg'
                : 'bg-slate-900/80 border-slate-700/80 text-slate-300 hover:bg-slate-800'
            }`}
          >
            <div className="flex items-center justify-between gap-3">
              <span>RCA</span>
              <span
                className="h-2 w-2 rounded-full"
                style={{ backgroundColor: vesselColors.rca }}
              />
            </div>
            {vesselRisks?.RCA && (
              <span className="text-[10px] text-slate-400 font-normal">
                {vesselRisks.RCA.probability_percent}%
              </span>
            )}
          </button>
        </div>
      </div>

      <div className="mt-2 text-[11px] text-slate-500 text-center flex items-center justify-center gap-1.5">
        <Eye className="h-3 w-3" />
        <span>Drag to rotate 3D heart &bull; Scroll to zoom &bull; Click vessel tags to orbit territory</span>
      </div>
    </div>
  );
};

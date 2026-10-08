import * as THREE from "three";
import type { ThreeDAnatomyPayload, PredictionResponse } from "./types";

export type AnatomyMesh = THREE.Mesh<
  THREE.BufferGeometry,
  THREE.MeshPhysicalMaterial
>;
const ANATOMY_COLORS: Record<string, string> = {
  myocardium: "#a53632",
  lad: "#8F1D1D",
  lcx: "#1E3E6D",
  rca: "#5B1D5B",
  left_main: "#731616",
};

/** Every supplied position/index is retained in the shared coordinate system. */
export function createAnatomyMeshes(
  anatomy: ThreeDAnatomyPayload,
): Record<string, AnatomyMesh> {
  const meshes: Record<string, AnatomyMesh> = {};
  for (const [name, data] of Object.entries(anatomy.structures)) {
    if (!data) continue;
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute(
      "position",
      new THREE.Float32BufferAttribute(data.positions, 3),
    );
    geometry.setIndex(data.indices);
    geometry.computeVertexNormals();
    geometry.computeBoundingBox();
    const tissue = name === "myocardium";
    const material = new THREE.MeshPhysicalMaterial({
      color: ANATOMY_COLORS[name] || ANATOMY_COLORS.left_main,
      roughness: tissue ? 0.48 : 0.58,
      metalness: 0,
      clearcoat: tissue ? 0.22 : 0,
      clearcoatRoughness: 0.5,
      side: THREE.DoubleSide,
    });
    const mesh = new THREE.Mesh(geometry, material);
    mesh.name = name;
    mesh.renderOrder = tissue ? 0 : 1;
    meshes[name] = mesh;
  }
  return meshes;
}

/** Material/visibility changes never replace geometry, controls, or the scene. */
export function updateAnatomyMeshes(
  meshes: Record<string, AnatomyMesh>,
  {
    mode,
    prediction,
    opacity,
    visible,
    focus,
  }: {
    mode: "anatomy" | "risk";
    prediction: PredictionResponse | null;
    opacity: number;
    visible: boolean;
    focus: "lad" | "lcx" | "rca" | null;
  },
) {
  const baseTissueColor = new THREE.Color(ANATOMY_COLORS.myocardium);
  const darkTissueColor = new THREE.Color("#180607");
  const transparency = Math.max(0, Math.min(1, 1 - opacity));

  for (const [name, mesh] of Object.entries(meshes)) {
    if (name === "myocardium") {
      mesh.visible = visible;
      mesh.material.opacity = opacity;
      mesh.material.transparent = opacity < 1;
      mesh.material.depthWrite = opacity === 1;
      mesh.material.color
        .copy(baseTissueColor)
        .lerp(darkTissueColor, transparency * 0.82);
      mesh.renderOrder = 0;
    } else {
      const vessel = (["lad", "lcx", "rca"] as const).find(
        (key) => key === name,
      );
      const risk = vessel ? prediction?.vessel_colors_3d[vessel] : undefined;
      // The left main has no model target. Missing/currently stale results use anatomy colors.
      const color =
        mode === "risk" && risk
          ? risk
          : ANATOMY_COLORS[name] || ANATOMY_COLORS.left_main;
      mesh.material.color.set(color);
      mesh.material.emissive.set(color);
      mesh.material.emissiveIntensity = focus === name ? 0.14 : 0.02;
      mesh.material.opacity =
        focus && focus !== name && name !== "left_main" ? 0.3 : 1;
      mesh.material.transparent = mesh.material.opacity < 1;
      mesh.material.depthWrite = !mesh.material.transparent;
      mesh.renderOrder = 1;
    }
    mesh.material.needsUpdate = true;
  }
}

export function disposeAnatomyMeshes(meshes: Record<string, AnatomyMesh>) {
  for (const mesh of Object.values(meshes)) {
    mesh.geometry.dispose();
    mesh.material.dispose();
  }
}

import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import * as THREE from "three";
import {
  createAnatomyMeshes,
  updateAnatomyMeshes,
  disposeAnatomyMeshes,
  pickCoronaryVessel,
} from "../src/utils/anatomy.ts";

test("mesh picking selects visible coronary surfaces and ignores neutral anatomy", () => {
  const make = (name, z) => {
    const mesh = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), new THREE.MeshBasicMaterial({ side: THREE.DoubleSide }));
    mesh.name = name;
    mesh.position.z = z;
    mesh.updateMatrixWorld();
    return mesh;
  };
  const meshes = { myocardium: make("myocardium", 3), left_main: make("left_main", 2), lad: make("lad", 1), lcx: make("lcx", 0) };
  const ray = new THREE.Raycaster(new THREE.Vector3(0, 0, 5), new THREE.Vector3(0, 0, -1));
  assert.equal(pickCoronaryVessel(ray, meshes), "lad");
  meshes.lad.visible = false;
  assert.equal(pickCoronaryVessel(ray, meshes), "lcx");
  meshes.lcx.visible = false;
  assert.equal(pickCoronaryVessel(ray, meshes), null);
  for (const mesh of Object.values(meshes)) { mesh.geometry.dispose(); mesh.material.dispose(); }
});
const anatomy = JSON.parse(
  await readFile(
    new URL("../public/heart_model_anatomy.json", import.meta.url),
  ),
);

test("all complete anatomical surfaces retain coordinates, indices, and computed normals", () => {
  const meshes = createAnatomyMeshes(anatomy);
  assert.deepEqual(Object.keys(meshes).sort(), [
    "lad",
    "lcx",
    "left_main",
    "myocardium",
    "rca",
  ]);
  let vertices = 0,
    triangles = 0;
  for (const [name, mesh] of Object.entries(meshes)) {
    const source = anatomy.structures[name];
    const positions = mesh.geometry.getAttribute("position");
    assert.equal(positions.count, source.vertex_count);
    assert.equal(mesh.geometry.getIndex().count, source.face_count * 3);
    assert.equal(
      mesh.geometry.getAttribute("normal").count,
      source.vertex_count,
    );
    assert.deepEqual(
      Array.from(positions.array),
      Array.from(new Float32Array(source.positions)),
    );
    assert.deepEqual(
      Array.from(mesh.geometry.getIndex().array),
      source.indices,
    );
    assert.deepEqual(mesh.position.toArray(), [0, 0, 0]);
    assert.ok(
      mesh.geometry.boundingBox && !mesh.geometry.boundingBox.isEmpty(),
    );
    vertices += positions.count;
    triangles += mesh.geometry.getIndex().count / 3;
  }
  assert.equal(vertices, 95363);
  assert.equal(triangles, 171186);
  disposeAnatomyMeshes(meshes);
});

test("risk, focus, tissue opacity and visibility update the existing resources; unknown risk stays neutral", () => {
  const meshes = createAnatomyMeshes(anatomy);
  const originals = Object.values(meshes).map((mesh) => [
    mesh,
    mesh.geometry,
    mesh.material,
  ]);
  const settings = {
    mode: "risk",
    prediction: {
      vessel_colors_3d: { lad: "#EF4444", lcx: "#F59E0B", rca: "#10B981" },
    },
    opacity: 0.45,
    visible: false,
    focus: "lad",
  };
  updateAnatomyMeshes(meshes, settings);
  assert.equal(meshes.lad.material.color.getHexString(), "ef4444");
  assert.equal(meshes.lcx.material.opacity, 0.3);
  assert.equal(meshes.myocardium.material.opacity, 0.45);
  assert.equal(meshes.myocardium.visible, false);
  assert.equal(meshes.myocardium.material.depthWrite, false);
  assert.equal(meshes.left_main.material.color.getHexString(), "94a3b8");
  assert.equal(meshes.left_main.material.opacity, 1);
  assert.equal(meshes.myocardium.renderOrder, 0);
  assert.equal(meshes.lad.renderOrder, 1);
  // Myocardium color darkens as opacity is reduced below 1.0
  const reducedOpacityColor = meshes.myocardium.material.color.getHexString();
  assert.notEqual(reducedOpacityColor, "a53632");
  const focusedEmissive = meshes.lad.material.emissiveIntensity;

  updateAnatomyMeshes(meshes, {
    ...settings,
    prediction: null,
    focus: null,
    visible: true,
    opacity: 1,
  });
  assert.equal(meshes.lad.material.color.getHexString(), "94a3b8");
  assert.equal(meshes.lcx.material.opacity, 1);
  assert.equal(meshes.myocardium.material.depthWrite, true);
  // At opacity 1, myocardium returns to natural base color and vessels have subtle base emissive
  assert.equal(meshes.myocardium.material.color.getHexString(), "a53632");
  assert.ok(meshes.lad.material.emissiveIntensity < focusedEmissive);
  Object.values(meshes).forEach((mesh, index) => {
    assert.equal(mesh, originals[index][0]);
    assert.equal(mesh.geometry, originals[index][1]);
    assert.equal(mesh.material, originals[index][2]);
  });
  const group = new THREE.Group();
  group.add(...Object.values(meshes));
  group.scale.setScalar(1.012);
  assert.equal(group.children.length, 5);
  assert.ok(
    group.children.every((mesh) =>
      mesh.scale.equals(new THREE.Vector3(1, 1, 1)),
    ),
  );
  disposeAnatomyMeshes(meshes);
});

test("viewer resource cleanup disposes every mesh geometry and material", () => {
  const meshes = createAnatomyMeshes(anatomy);
  const disposed = [];
  for (const [name, mesh] of Object.entries(meshes)) {
    mesh.geometry.addEventListener("dispose", () =>
      disposed.push(`${name}:geometry`),
    );
    mesh.material.addEventListener("dispose", () =>
      disposed.push(`${name}:material`),
    );
  }
  disposeAnatomyMeshes(meshes);
  assert.equal(disposed.length, 10);
  assert.equal(new Set(disposed).size, 10);
});

test("risk focus isolates each artery and reset restores the user's tissue visibility", () => {
  const meshes = createAnatomyMeshes(anatomy);
  const settings = { mode: "risk", prediction: null, opacity: 0.45, visible: true };
  for (const focus of ["lad", "lcx", "rca"]) {
    updateAnatomyMeshes(meshes, { ...settings, focus });
    assert.deepEqual(Object.keys(meshes).filter((name) => meshes[name].visible), [focus]);
  }
  updateAnatomyMeshes(meshes, { ...settings, focus: null });
  assert.ok(Object.values(meshes).every((mesh) => mesh.visible));
  updateAnatomyMeshes(meshes, { ...settings, focus: null, visible: false });
  assert.equal(meshes.myocardium.visible, false);
  assert.ok(["lad", "lcx", "rca", "left_main"].every((name) => meshes[name].visible));
  updateAnatomyMeshes(meshes, { ...settings, mode: "anatomy", focus: "lad" });
  assert.ok(Object.values(meshes).every((mesh) => mesh.visible));
  disposeAnatomyMeshes(meshes);
});

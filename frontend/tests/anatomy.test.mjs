import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import * as THREE from "three";
import {
  createAnatomyMeshes,
  updateAnatomyMeshes,
  disposeAnatomyMeshes,
} from "../src/utils/anatomy.ts";
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
  assert.equal(meshes.left_main.material.color.getHexString(), "d9c8b5");
  assert.equal(meshes.left_main.material.opacity, 1);
  updateAnatomyMeshes(meshes, {
    ...settings,
    prediction: null,
    focus: null,
    visible: true,
    opacity: 1,
  });
  assert.equal(meshes.lad.material.color.getHexString(), "ebc79b");
  assert.equal(meshes.lcx.material.opacity, 1);
  assert.equal(meshes.myocardium.material.depthWrite, true);
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

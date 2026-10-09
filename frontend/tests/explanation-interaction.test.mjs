import test from "node:test";
import assert from "node:assert/strict";
import React from "react";
import TestRenderer, { act } from "react-test-renderer";
import { createServer } from "vite";
import { FIELD_GROUPS, DEFAULT_PATIENT, normalizePatient } from "../src/utils/patient.ts";
import { measurementAnchorId } from "../src/utils/measurementNavigation.ts";

const compiler = await createServer({ root: new URL("../", import.meta.url).pathname, server: { middlewareMode: true, hmr: false, ws: false }, appType: "custom" });
const { SHAPExplanationChart } = await compiler.ssrLoadModule("/src/components/SHAPExplanationChart.tsx");
const { PatientForm } = await compiler.ssrLoadModule("/src/components/PatientForm.tsx");
test.after(() => compiler.close());
const st = { feature: "St Depression", display_name: "ST depression", contribution: .4, patient_value: 1, impact_direction: "increases_risk", feature_kind: "recorded", model_input_value: 1, source_measurements: [{ input_key: "St Depression", recorded_value: 1 }] };
const ratio = { feature: "Castelli_Risk_Index_II", display_name: "LDL / HDL ratio", contribution: -.8, patient_value: 4, impact_direction: "decreases_risk", feature_kind: "derived", model_input_value: 4, derivation: "LDL / HDL", source_measurements: [{ input_key: "LDL", recorded_value: 160 }, { input_key: "HDL", recorded_value: 40 }] };
const prediction = {
  patient_id: "case-one", overall_cad: {}, vessels: {}, vessel_colors_3d: {}, disclaimer: "Experimental",
  shap_explanations: { CAD: [st, ratio], LAD: [{ ...st, contribution: -.2 }], LCX: [], RCA: [] },
  evidence: { assessment_id: "assessment-one", generated_at: "2026-10-09T10:00:00Z", clinical_inputs: { "St Depression": 1, LDL: 160, HDL: 40 }, prediction_model: "Ensemble", explanation_model: "XGBoost", confidence_interval: null, limitations: [] },
};
const rows = renderer => renderer.root.findAllByType("button").filter(button => button.props["aria-controls"]);
const nodeText = node => typeof node === "string" ? node : (node.children || []).map(nodeText).join("");
const text = renderer => nodeText(renderer.root);
function chart(props = {}) {
  let renderer;
  act(() => { renderer = TestRenderer.create(React.createElement(SHAPExplanationChart, { prediction, stale: false, target: "CAD", ...props })); });
  return renderer;
}

test("factor activation expands assessed evidence, switches one open factor and collapses it", () => {
  const renderer = chart();
  assert.match(nodeText(rows(renderer)[0]), /LDL \/ HDL ratio/);
  act(() => rows(renderer)[0].props.onClick());
  assert.equal(rows(renderer)[0].props["aria-expanded"], true);
  assert.match(text(renderer), /160 mg\/dL/);
  assert.match(text(renderer), /40 mg\/dL/);
  assert.match(text(renderer), /assessment-one/);
  assert.match(text(renderer), /-0.8000/);
  const id = rows(renderer)[0].props["aria-controls"];
  assert.equal(renderer.root.findByProps({ id }).type, "div");
  act(() => rows(renderer)[1].props.onClick());
  assert.equal(rows(renderer)[0].props["aria-expanded"], false);
  assert.equal(rows(renderer)[1].props["aria-expanded"], true);
  assert.match(text(renderer), /Original assessment measurements/);
  assert.match(text(renderer), /\+0.4000/);
  assert.match(text(renderer), /Yes/);
  act(() => rows(renderer)[1].props.onClick());
  assert.equal(rows(renderer)[1].props["aria-expanded"], false);
  act(() => renderer.unmount());
});

test("source buttons navigate by the raw measurement alias and report missing inputs", () => {
  const visited = [];
  const renderer = chart({ onViewInput: key => { visited.push(key); return false; } });
  act(() => rows(renderer)[1].props.onClick());
  const source = renderer.root.findAllByType("button").find(button => nodeText(button).startsWith("View "));
  act(() => source.props.onClick());
  assert.deepEqual(visited, ["St Depression"]);
  assert.match(text(renderer), /source input is currently unavailable/);
  act(() => renderer.unmount());
});

test("target changes and new assessment objects close old details even when the feature name repeats", () => {
  const renderer = chart();
  act(() => rows(renderer)[1].props.onClick());
  act(() => renderer.update(React.createElement(SHAPExplanationChart, { prediction, stale: false, target: "LAD" })));
  assert.equal(rows(renderer)[0].props["aria-expanded"], false);
  assert.match(text(renderer), /-0.2000/);
  act(() => rows(renderer)[0].props.onClick());
  const next = { ...prediction, evidence: { ...prediction.evidence, assessment_id: "assessment-two", clinical_inputs: { ...prediction.evidence.clinical_inputs, "St Depression": 0 } } };
  act(() => renderer.update(React.createElement(SHAPExplanationChart, { prediction: next, stale: false, target: "LAD" })));
  assert.equal(rows(renderer)[0].props["aria-expanded"], false);
  act(() => rows(renderer)[0].props.onClick());
  assert.match(text(renderer), /assessment-two/);
  assert.doesNotMatch(text(renderer), /assessment-one/);
  act(() => renderer.unmount());
});

test("stale updates hide open factors and do not reopen them when stale clears", () => {
  const renderer = chart();
  act(() => rows(renderer)[1].props.onClick());
  act(() => renderer.update(React.createElement(SHAPExplanationChart, { prediction, stale: true, target: "CAD" })));
  assert.equal(rows(renderer).length, 0);
  assert.doesNotMatch(text(renderer), /Original assessment measurements/);
  act(() => renderer.update(React.createElement(SHAPExplanationChart, { prediction, stale: false, target: "CAD" })));
  assert.ok(rows(renderer).every(row => row.props["aria-expanded"] === false));
  act(() => renderer.unmount());
});

test("legacy responses close details when their prediction object changes; calculated sources are not guessed", () => {
  const legacy = { ...prediction, evidence: undefined };
  const renderer = chart({ prediction: legacy });
  act(() => rows(renderer)[0].props.onClick());
  assert.match(text(renderer), /Source measurements unavailable/);
  act(() => renderer.update(React.createElement(SHAPExplanationChart, { prediction: { ...legacy }, stale: false, target: "CAD" })));
  assert.ok(rows(renderer).every(row => !row.props["aria-expanded"]));
  act(() => renderer.unmount());
});

test("every recorded source has a real form anchor, including a focusable BMI readout", () => {
  let renderer;
  act(() => { renderer = TestRenderer.create(React.createElement(PatientForm, { patientData: normalizePatient(DEFAULT_PATIENT), onChange: () => assert.fail("navigation must not edit inputs"), onSubmit: () => assert.fail("navigation must not submit"), isLoading: false, ready: true })); });
  for (const group of FIELD_GROUPS) for (const field of group.fields) {
    const control = renderer.root.findByProps({ id: measurementAnchorId(field.key) });
    assert.ok(["input", "select"].includes(control.type));
  }
  const bmi = renderer.root.findByProps({ id: measurementAnchorId("BMI") });
  assert.equal(bmi.type, "div");
  assert.equal(bmi.props.tabIndex, -1);
  act(() => renderer.unmount());
});

test("all-positive and zero contributions use truthful text and non-finite factors are omitted", () => {
  const response = { ...prediction, shap_explanations: { ...prediction.shap_explanations, CAD: [st, { ...ratio, contribution: 0 }, { ...st, feature: "Invalid", contribution: Infinity }] } };
  const renderer = chart({ prediction: response });
  assert.equal(rows(renderer).length, 2);
  assert.match(text(renderer), /displayed factors contain no decreasing contributions/);
  assert.match(text(renderer), /No change in explanation-model output/);
  assert.doesNotMatch(text(renderer), /Infinity/);
  act(() => renderer.unmount());
});

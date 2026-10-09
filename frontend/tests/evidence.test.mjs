import test from "node:test";
import assert from "node:assert/strict";
import { vesselEvidence, formatMeasurement } from "../src/utils/evidence.ts";

const prediction = {
  patient_id: "case-1",
  vessels: { LAD: { probability: .7 }, LCX: { probability: .2 }, RCA: { probability: .4 } },
  vessel_colors_3d: { lad: "#ff0000", lcx: "#00ff00", rca: "#ffaa00" },
  shap_explanations: {
    LAD: [{ feature: "Age", contribution: .3 }, { feature: "LDL", contribution: -.8 }, { feature: "BP", contribution: NaN }],
    LCX: [{ feature: "HDL", contribution: -.1 }], RCA: [],
  },
  evidence: { assessment_id: "run-1", clinical_inputs: { Age: 67, BP: 140, Sex: 1, BMI: 26.123 } },
};

test("selected vessel evidence uses its own score, mesh color and signed contributors", () => {
  const lad = vesselEvidence(prediction, "lad", false);
  assert.equal(lad.risk.probability, .7);
  assert.equal(lad.meshColor, "#ff0000");
  assert.deepEqual(lad.factors.map(f => f.feature), ["LDL", "Age"]);
  assert.equal(lad.factors[0].contribution, -.8);
  assert.equal(lad.context.assessment_id, "run-1");
  assert.equal(lad.context.clinical_inputs.Age, 67);
  const lcx = vesselEvidence(prediction, "lcx", false);
  assert.equal(lcx.risk.probability, .2);
  assert.deepEqual(lcx.factors.map(f => f.feature), ["HDL"]);
  assert.equal(prediction.shap_explanations.LAD[0].feature, "Age");
});

test("stale, unassessed and unselected arteries cannot present current evidence", () => {
  assert.equal(vesselEvidence(prediction, "lad", true), null);
  assert.equal(vesselEvidence(null, "lad", false), null);
  assert.equal(vesselEvidence(prediction, null, false), null);
  assert.deepEqual(vesselEvidence(prediction, "rca", false).factors, []);
});

test("measurements preserve units and category meaning and do not invent missing values", () => {
  assert.equal(formatMeasurement("BP", 140), "140 mmHg");
  assert.equal(formatMeasurement("Sex", 1), "Male");
  assert.equal(formatMeasurement("DM", 0), "No");
  assert.equal(formatMeasurement("BMI", 26.123), "26.1 kg/m²");
  assert.equal(formatMeasurement("LDL", undefined), "Unavailable");
  assert.equal(formatMeasurement("Age", NaN), "Unavailable");
});

import test from "node:test";
import assert from "node:assert/strict";
import { rankedFactors, factorSources, factorValue, factorDirection } from "../src/utils/explanation.ts";

const context = { clinical_inputs: { "St Depression": 1, LDL: 160, HDL: 40 } };
const factor = { feature: "St Depression", display_name: "ECG ST Depression", contribution: -.4, patient_value: 1, feature_kind: "recorded", model_input_value: 1, source_measurements: [{ input_key: "St Depression", recorded_value: 1 }] };

test("patient factors rank by magnitude without changing signs or source order", () => {
  const items = [{ ...factor, contribution: .2 }, { ...factor, contribution: -.8 }, { ...factor, contribution: NaN }];
  assert.deepEqual(rankedFactors(items).map(f => f.contribution), [-.8, .2]);
  assert.equal(items[0].contribution, .2);
  assert.equal(factorDirection(-.4), "Decreases explanation-model output");
  assert.equal(factorDirection(.4), "Increases explanation-model output");
  assert.equal(factorDirection(0), "No change in explanation-model output");
});

test("recorded factors use assessed categorical values with original field aliases", () => {
  assert.equal(factorValue(factor, context), "Yes");
  assert.deepEqual(factorSources(factor, context), [{ input_key: "St Depression", recorded_value: 1, label: "ST depression", formatted_value: "Yes" }]);
  assert.equal(factorValue({ ...factor, feature: "LDL", source_measurements: [] }, context), "160 mg/dL");
});

test("derived factors expose each source and never display a calculated value as a measurement", () => {
  const derived = { ...factor, feature: "Castelli_Risk_Index_II", feature_kind: "derived", model_input_value: 4, source_measurements: [{ input_key: "LDL", recorded_value: 999 }, { input_key: "HDL", recorded_value: 40 }] };
  assert.equal(factorValue(derived, context), "Calculated value 4");
  assert.deepEqual(factorSources(derived, context).map(s => s.formatted_value), ["160 mg/dL", "40 mg/dL"]);
});

test("older raw factors can use snapshots but unknown sources and missing snapshots cannot invent links", () => {
  const legacy = { ...factor, feature_kind: undefined, source_measurements: undefined };
  assert.equal(factorSources(legacy, context)[0].input_key, "St Depression");
  assert.deepEqual(factorSources({ ...legacy, feature: "Unknown_Ratio" }, context), []);
  assert.deepEqual(factorSources(factor, undefined), []);
  assert.equal(factorValue(factor, undefined), "Recorded value unavailable");
  assert.equal(factorValue({ ...legacy, feature: "Unknown_Ratio" }, context), "Model feature value 1");
  assert.deepEqual(factorSources({ ...factor, source_measurements: [{ input_key: "Fake Feature", recorded_value: 4 }] }, { clinical_inputs: { "Fake Feature": 4 } }), []);
});

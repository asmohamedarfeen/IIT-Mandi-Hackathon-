import test from "node:test";
import assert from "node:assert/strict";
import { measurementAnchorId, focusMeasurement } from "../src/utils/measurementNavigation.ts";

test("measurement aliases generate distinct IDs without unsafe selector characters", () => {
  const keys = ["St Depression", "St-Depression", "EF-TTE", "Current Smoker", "BMI", "a\"b"];
  const ids = keys.map(measurementAnchorId);
  assert.equal(new Set(ids).size, keys.length);
  assert.ok(ids.every(id => !/[\s"\\]/.test(id)));
});

test("source navigation opens its collapsed group and focuses the exact control without editing it", () => {
  const group = { open: false };
  const actions = [];
  const input = { value: "1", closest: () => group, scrollIntoView: options => actions.push(options.behavior), focus: options => actions.push(options.preventScroll), animate: () => actions.push("highlight") };
  const root = { querySelector: selector => selector === `[id="${measurementAnchorId("St Depression")}"]` ? input : null };
  assert.equal(focusMeasurement(root, "St Depression", false), true);
  assert.equal(group.open, true);
  assert.equal(input.value, "1");
  assert.deepEqual(actions, ["smooth", true, "highlight"]);
});

test("reduced motion avoids animation and BMI readout can be focused; absent sources fail cleanly", () => {
  const actions = [];
  const readout = { closest: () => null, scrollIntoView: options => actions.push(options.behavior), focus: () => actions.push("focus"), animate: () => actions.push("animated") };
  const root = { querySelector: selector => selector.includes(measurementAnchorId("BMI")) ? readout : null };
  assert.equal(focusMeasurement(root, "BMI", true), true);
  assert.deepEqual(actions, ["auto", "focus"]);
  assert.equal(focusMeasurement(root, "missing", false), false);
});

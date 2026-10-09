import test from "node:test";
import assert from "node:assert/strict";
import { riskBand, rankedVessels, leadingContributors } from "../src/utils/risk.ts";

test("display bands use the existing model thresholds and reject missing or invalid scores", () => {
  for (const value of [undefined, NaN, -1, 101]) assert.equal(riskBand(value), "unknown");
  assert.equal(riskBand(0), "low");
  assert.equal(riskBand(34.99), "low");
  assert.equal(riskBand(35), "moderate");
  assert.equal(riskBand(64.99), "moderate");
  assert.equal(riskBand(65), "high");
  assert.equal(riskBand(100), "high");
});

test("arteries are ranked by current score without mutating results; missing results are not low risk", () => {
  const prediction = { vessels: { LAD: { probability_percent: 20 }, LCX: { probability_percent: 85 }, RCA: { probability_percent: 40 } } };
  assert.deepEqual(rankedVessels(prediction).map((item) => item.key), ["lcx", "rca", "lad"]);
  assert.deepEqual(rankedVessels(null), []);
  assert.deepEqual(Object.keys(prediction.vessels), ["LAD", "LCX", "RCA"]);
});

test("leading contributors only show finite positive impacts from the selected target", () => {
  const features = [
    { display_name: "Negative", contribution: -4 },
    { display_name: "Small", contribution: 0.1 },
    { display_name: "Large", contribution: 0.8 },
    { display_name: "Invalid", contribution: NaN },
    { display_name: "Zero", contribution: 0 },
  ];
  assert.deepEqual(leadingContributors(features).map((item) => item.display_name), ["Large", "Small"]);
  assert.equal(features[0].display_name, "Negative");
  assert.deepEqual(leadingContributors(undefined), []);
});

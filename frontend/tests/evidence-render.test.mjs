import test from "node:test";
import assert from "node:assert/strict";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { createServer } from "vite";

// Render real components through the project's TSX compiler, without a browser.
const compiler = await createServer({ root: new URL("../", import.meta.url).pathname, server: { middlewareMode: true, hmr: false, ws: false }, appType: "custom" });
const { CoronaryEvidencePanel } = await compiler.ssrLoadModule("/src/components/CoronaryEvidencePanel.tsx");
const { SHAPExplanationChart } = await compiler.ssrLoadModule("/src/components/SHAPExplanationChart.tsx");
test.after(() => compiler.close());
const risk = (vessel, score) => ({ vessel, probability: score / 100, probability_percent: score, color_hex: "#22C55E", risk_level: "Low Risk", anatomical_description: `${vessel} territory` });
const prediction = {
  patient_id: "test-case",
  overall_cad: risk("CAD", 30),
  vessels: { LAD: risk("LAD", 21.5), LCX: risk("LCX", 11.2), RCA: risk("RCA", 32.3) },
  vessel_colors_3d: { lad: "#22C55E", lcx: "#22C55E", rca: "#22C55E", myocardium: "#64748B" },
  shap_explanations: { CAD: [], LAD: [{ feature: "LDL", display_name: "LAD factor", patient_value: 110, contribution: -.45, impact_direction: "decreases_risk" }], LCX: [{ feature: "Age", display_name: "LCX factor", patient_value: 67, contribution: .7, impact_direction: "increases_risk" }], RCA: [] },
  evidence: { assessment_id: "assessment-one", generated_at: "2026-10-09T10:00:00+00:00", clinical_inputs: { Age: 67, BP: 140, LDL: 110 }, prediction_model: "Ensemble", explanation_model: "XGBoost", confidence_interval: null, limitations: ["External validation unavailable"] },
  disclaimer: "Experimental",
};
const render = (selected, stale = false, result = prediction) => renderToStaticMarkup(React.createElement(CoronaryEvidencePanel, { prediction: result, selected, stale, busy: false, onSelect: () => {} }));

test("rendered evidence switches probability, contributions and exact color source with the selected artery", () => {
  const lad = render("lad");
  assert.match(lad, /21\.5/);
  assert.match(lad, /LAD factor/);
  assert.doesNotMatch(lad, /LCX factor/);
  assert.match(lad, /vessel_colors_3d\.lad = #22C55E/);
  assert.match(lad, /140 mmHg/);
  assert.match(lad, /assessment-one/);
  const lcx = render("lcx");
  assert.match(lcx, /11\.2/);
  assert.match(lcx, /LCX factor/);
  assert.doesNotMatch(lcx, /LAD factor/);
  assert.match(lcx, /Confidence interval: unavailable/);
});

test("stale rendering hides probability, measurements, contributors and raw provenance together", () => {
  const stale = render("lad", true);
  for (const previous of [/21\.5/, /LAD factor/, /140 mmHg/, /assessment-one/]) assert.doesNotMatch(stale, previous);
  assert.match(stale, /Previous evidence is hidden/);
});

test("older backends, absent explanations and unassessed states remain usable", () => {
  assert.match(render("lad", false, { ...prediction, evidence: undefined }), /Input provenance is unavailable/);
  assert.match(render("rca"), /No explanation available/);
  assert.match(render("lad", false, null), /Run an assessment/);
  assert.match(render(null), /Choose LAD, LCX or RCA/);
});

test("artery evidence and overall CAD explanation have distinct accessible heading IDs", () => {
  const html = renderToStaticMarkup(React.createElement(React.Fragment, null,
    React.createElement(CoronaryEvidencePanel, { prediction, selected: "lad", stale: false, busy: false, onSelect: () => {} }),
    React.createElement(SHAPExplanationChart, { prediction, stale: false, target: "CAD" }),
  ));
  const ids = [...html.matchAll(/id="([^"]+)"/g)].map(match => match[1]);
  assert.equal(new Set(ids).size, ids.length);
  assert.match(html, /CAD contributing factors/);
  assert.match(html, /LAD contributing factors/);
});

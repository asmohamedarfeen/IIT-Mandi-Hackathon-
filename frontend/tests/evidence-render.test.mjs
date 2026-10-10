import test from "node:test";
import assert from "node:assert/strict";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { createServer } from "vite";

// Render real components through the project's TSX compiler, without a browser.
const compiler = await createServer({ root: new URL("../", import.meta.url).pathname, server: { middlewareMode: true, hmr: false, ws: false }, appType: "custom" });
const { CoronaryEvidencePanel } = await compiler.ssrLoadModule("/src/components/CoronaryEvidencePanel.tsx");
const { SHAPExplanationChart } = await compiler.ssrLoadModule("/src/components/SHAPExplanationChart.tsx");
const { RiskSummaryCards } = await compiler.ssrLoadModule("/src/components/RiskSummaryCards.tsx");
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

test("risk cards show model classification separately from probability bands and hide stale status", () => {
  const result = { ...prediction, overall_cad: { ...prediction.overall_cad, predicted_status: "CAD", decision_threshold: .25 } };
  const html = renderToStaticMarkup(React.createElement(RiskSummaryCards, { prediction: result, stale: false }));
  assert.match(html, /Predicted status: CAD/);
  assert.match(html, /Low Risk/);
  const stale = renderToStaticMarkup(React.createElement(RiskSummaryCards, { prediction: result, stale: true }));
  assert.doesNotMatch(stale, /Predicted status: CAD/);
});

test('assessment measurements expose saved source and confirmation rather than current form assumptions',()=>{
 const result = {...prediction,evidence:{...prediction.evidence,input_provenance:{assessment_mode:'demo',measurements:{Age:{source:'supplied',confirmed:false},BP:{source:'defaulted',confirmed:false}}}}};
 const html = render('lad',false,result);
 assert.match(html,/Assessment mode: demo/);
 assert.match(html,/supplied · unconfirmed/);
 assert.match(html,/defaulted · unconfirmed/);
 assert.match(html,/Source\/confirmation unavailable/);
});

test('primary deployed explanation shows additive probability units and remains hidden when stale',()=>{
 const explanation = {method:'exact_domain_shapley',reference_type:'synthetic_default_profile',reference_inputs:{Age:55,BP:120},baseline_probability:.2,predicted_probability:.3,reconstruction_error:0,groups:[{id:'profile',label:'Profile domain',contribution:.1}],limitations:'Dependent derived inputs recomputed.'};
 const result = {...prediction,prediction_explanations:{LAD:explanation}};
 const html = render('lad',false,result);
 assert.match(html,/Deployed predictor explanation/);
 assert.match(html,/Profile domain/);
 assert.match(html,/Synthetic default profile/);
 assert.match(html,/Inspect reference measurements/);
 assert.match(html,/120 mmHg/);
 assert.match(html,/10.00 probability points/);
 assert.match(html,/Baseline probability: 20.00%/);
 assert.match(html,/Historical independent XGBoost factors/);
 assert.doesNotMatch(render('lad',true,result),/Profile domain/);
});

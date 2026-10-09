import test from "node:test";
import assert from "node:assert/strict";
import React from "react";
import TestRenderer, { act } from "react-test-renderer";
import { renderToStaticMarkup } from "react-dom/server";
import { createServer } from "vite";

const compiler = await createServer({ root: new URL("../", import.meta.url).pathname, server: { middlewareMode: true, ws: false }, appType: "custom" });
test.after(() => compiler.close());
const text = node => typeof node === "string" ? node : (node.children || []).map(text).join("");
const matrix = { threshold: .5, tn: 3, fp: 1, fn: 2, tp: 4, precision: .8, recall: 2/3, sensitivity: 2/3, specificity: .75, f1: 8/11 };
const stability = { model: "XGBoost", method: "Held-out folds", features: [{ feature: "Age", mean: .12, std: .02, top_k_frequency: 1, fold_values: [.1, .14], rank_mean: 1, rank_std: 0 }], mean_rank_correlation: .9, mean_top_k_jaccard: .8 };
const model = { metrics: { roc_auc: .75, pr_auc: .7, accuracy: .7, brier_score: .18 }, undefined_metrics: {}, fold_metrics: [{ roc_auc: .7 }, { roc_auc: .8 }], diagnostics: { confusion_matrix: matrix, thresholds: [{ ...matrix, threshold: .4, tn: 2, fp: 2, fn: 1, tp: 5 }, matrix], calibration: [{ lower: 0, upper: .5, count: 4, mean_probability: .2, fraction_positive: .25 }], roc: { fpr: [0,.25,1], tpr: [0,.75,1], thresholds: [null,.5,0] }, pr: { recall: [1,.75,0], precision: [.6,.8,1], thresholds: [.1,.5] } } };
const target = { class_distribution: { positive: 6, negative: 4, total: 10 }, folds: [{ fold: 1, train: {positive:3,negative:2,total:5}, test: {positive:3,negative:2,total:5} }], models: { Voting: model, CalibratedVoting: { ...model, metrics: { ...model.metrics, roc_auc: .8 } } }, feature_stability: stability, shap_stability: stability };
const fixture = { schema_version: 1, run_id: "heldout-run", generated_at: "2026-10-09T12:00:00Z", selected_model: "CalibratedVoting", status: "ready", stale: false, provenance: { dataset_sha256: "dataset-hash", model_sha256: "model-hash", command: "python scripts/evaluate_models.py", random_seed: 42, outer_folds: 2, inner_folds: 2 }, data_quality: { rows: 10, missing_values: { Age: 1 }, duplicates: 0, leakage_checks: [{check:"Targets excluded",passed:true,detail:"Verified"}] }, models: [{id:"Voting",name:"Voting",production_configuration:false,configuration_source:"pipeline",parameters:{}},{id:"CalibratedVoting",name:"Calibrated voting",production_configuration:true,configuration_source:"pipeline",parameters:{}}], targets: { CAD: target, LAD: {...target,class_distribution:{positive:2,negative:8,total:10}}, LCX: target, RCA: target }, limitations: ["Internal validation only"], supplied_benchmarks: {targets:{}} };

test("Lab renders actual aggregate data, production configuration, and provenance", async () => {
  const { ModelQualityLab } = await compiler.ssrLoadModule("/src/model-quality/ModelQualityLab.tsx");
  const html = renderToStaticMarkup(React.createElement(ModelQualityLab, { initialData: fixture }));
  assert.match(html, /heldout-run/);
  assert.match(html, /dataset-hash/);
  assert.match(html, /Targets excluded/);
  assert.match(html, /Internal validation only/);
  assert.match(html, /0\.800/);
  assert.match(html, /Age/);
  assert.match(html, /SHAP stability/);
});

test("threshold slider selects exact saved counts and target switching updates class balance", async () => {
  const { ModelQualityLab } = await compiler.ssrLoadModule("/src/model-quality/ModelQualityLab.tsx");
  let renderer;
  act(() => { renderer = TestRenderer.create(React.createElement(ModelQualityLab, { initialData: fixture })); });
  act(() => renderer.root.findByProps({ id: "mq-threshold" }).props.onChange({target:{value:"0.4"}}));
  const matrixTable = renderer.root.findByProps({ "aria-label": "Confusion counts" });
  assert.match(text(matrixTable), /5/);
  assert.match(text(renderer.root), /40%/);
  act(() => renderer.root.findByProps({id:"mq-target"}).props.onChange({target:{value:"LAD"}}));
  assert.match(text(renderer.root.findByProps({id:"mq-class-balance"})), /2 positive/);
  act(() => renderer.unmount());
});

test("undefined threshold points and missing diagnostic series are unavailable, never approximated", async () => {
  const { ModelQualityLab } = await compiler.ssrLoadModule("/src/model-quality/ModelQualityLab.tsx");
  let renderer;
  act(() => { renderer = TestRenderer.create(React.createElement(ModelQualityLab, { initialData: fixture })); });
  act(() => renderer.root.findByProps({ id: "mq-threshold" }).props.onChange({target:{value:"0.41"}}));
  assert.match(text(renderer.root.findByProps({id:"mq-confusion"})), /Unavailable/);
  act(() => renderer.unmount());
  const { Charts } = await compiler.ssrLoadModule("/src/model-quality/Charts.tsx");
  const html = renderToStaticMarkup(React.createElement(Charts,{kind:"roc", series:[]}));
  assert.match(html, /Unavailable/);
  assert.doesNotMatch(html, /<polyline/);
});

test("SVG curves retain API coordinates, text equivalents, and unique accessible IDs", async () => {
  const { Charts } = await compiler.ssrLoadModule("/src/model-quality/Charts.tsx");
  const html = renderToStaticMarkup(React.createElement(React.Fragment,null,
    React.createElement(Charts,{kind:"roc",series:[{name:"Voting",points:[{x:0,y:0},{x:.123456789,y:.987654321},{x:.25,y:.75},{x:1,y:1}]}]}),
    React.createElement(Charts,{kind:"pr",series:[{name:"Voting",points:[{x:1,y:.6},{x:0,y:1}]}]})));
  assert.match(html,/>0\.25</);
  assert.match(html,/>0\.75</);
  assert.match(html,/>0\.123456789</);
  assert.match(html,/>0\.987654321</);
  assert.match(html,/role="img"/);
  const ids = [...html.matchAll(/id="([^"]+)"/g)].map(match=>match[1]);
  assert.equal(new Set(ids).size,ids.length);
});

test("API downloads real report artifacts with the displayed selection and refuses HTML", async t => {
  const { apiService } = await compiler.ssrLoadModule("/src/services/api.ts");
  assert.equal(typeof apiService.downloadModelQualityReport,"function");
  const originalDocument = globalThis.document;
  const events=[];
  const link={click:()=>events.push("click"),remove:()=>events.push("remove")};
  globalThis.document={createElement:()=>link,body:{appendChild:()=>events.push("append")}};
  t.after(()=>{if(originalDocument===undefined)delete globalThis.document;else globalThis.document=originalDocument;});
  t.mock.method(URL,"createObjectURL",()=>"blob:quality");
  t.mock.method(URL,"revokeObjectURL",()=>{});
  t.mock.method(globalThis,"setTimeout",fn=>{fn();return 1;});
  t.mock.method(globalThis,"fetch",async(url,options)=>{
    assert.match(url,/\/model-quality\/report\?/);
    const query=new URL(url,"http://localhost").searchParams;
    assert.equal(query.get("section"),"roc"); assert.equal(query.get("target"),"LAD"); assert.equal(query.get("model"),"Voting");
    assert.equal(query.get("expected_run_id"),"heldout-run");
    assert.equal(options.cache,"no-store");
    return new Response('{"run_id":"heldout-run"}',{headers:{"content-type":"application/json","content-disposition":'attachment; filename="model-quality-heldout-run-roc-LAD-Voting.json"'}});
  });
  await apiService.downloadModelQualityReport({format:"json",section:"roc",target:"LAD",model:"Voting",threshold:.4,expected_run_id:"heldout-run"});
  assert.deepEqual(events,["append","click","remove"]);
  assert.equal(link.download,"model-quality-heldout-run-roc-LAD-Voting.json");
  t.mock.method(globalThis,"fetch",async()=>new Response("<html>offline</html>",{headers:{"content-type":"text/html"}}));
  await assert.rejects(apiService.downloadModelQualityReport({format:"json",section:"roc"}),/unavailable|Invalid/);
  t.mock.method(globalThis,"fetch",async()=>new Response('{"detail":"Saved run changed"}',{status:409,headers:{"content-type":"application/json"}}));
  await assert.rejects(apiService.downloadModelQualityReport({format:"json",section:"roc",expected_run_id:"heldout-run"}),/Saved run changed.*Refresh/);
});

test("failed initial requests have honest retry and generation instructions", async () => {
  const { ModelQualityLab } = await compiler.ssrLoadModule("/src/model-quality/ModelQualityLab.tsx");
  let renderer;
  await act(async()=>{renderer=TestRenderer.create(React.createElement(ModelQualityLab,{loadOverview:async()=>{throw new Error("offline");}}));});
  assert.match(text(renderer.root),/Unavailable/);
  assert.match(text(renderer.root),/evaluate_model_quality/);
  assert.ok(renderer.root.findAllByType("button").some(button=>text(button).includes("Retry")));
  act(()=>renderer.unmount());
});

test("sorting keeps undefined scores last and changes metric order independently of model selection", async () => {
  const { ModelQualityLab } = await compiler.ssrLoadModule("/src/model-quality/ModelQualityLab.tsx");
  const withMissing={...fixture,targets:{...fixture.targets,CAD:{...target,models:{...target.models,Missing:{...model,metrics:{roc_auc:null,brier_score:null}}}}}};
  let renderer;
  act(()=>{renderer=TestRenderer.create(React.createElement(ModelQualityLab,{initialData:withMissing}));});
  const table=()=>renderer.root.findByProps({"aria-label":"Sortable model metrics"});
  const names=()=>table().findByType("tbody").findAllByType("tr").map(row=>text(row.findByType("th")));
  assert.match(names()[0],/Calibrated voting/);
  assert.equal(names().at(-1),"Missing");
  act(()=>table().findAllByType("button").find(button=>text(button).startsWith("ROC AUC")).props.onClick());
  assert.equal(names()[0],"Voting");
  assert.equal(names().at(-1),"Missing");
  assert.equal(renderer.root.findByProps({id:"mq-model"}).props.value,"CalibratedVoting");
  act(()=>renderer.unmount());
});

test("superseded overview responses cannot replace the newest saved run", async () => {
  const { useQualityOverview } = await compiler.ssrLoadModule("/src/model-quality/hooks.ts");
  const pending=[];let state;
  const loader=signal=>new Promise(resolve=>pending.push({resolve,signal}));
  function Probe(){state=useQualityOverview(undefined,loader);return React.createElement("p",null,state.data?.run_id||"loading");}
  let renderer;
  act(()=>{renderer=TestRenderer.create(React.createElement(Probe));});
  let refresh;
  act(()=>{refresh=state.reload();});
  assert.equal(pending[0].signal.aborted,true);
  await act(async()=>{pending[1].resolve({...fixture,run_id:"newest"});await refresh;});
  await act(async()=>{pending[0].resolve({...fixture,run_id:"obsolete"});await Promise.resolve();});
  assert.equal(text(renderer.root),"newest");
  act(()=>renderer.unmount());
});

test("changing a report selection aborts a download and suppresses stale errors", async () => {
  const { useQualityDownload } = await compiler.ssrLoadModule("/src/model-quality/hooks.ts");
  let state,signal,reject;
  const loader=async(options,abortSignal)=>{signal=abortSignal;return new Promise((_,no)=>{reject=no;});};
  function Probe({identity}){state=useQualityDownload(identity,loader);return React.createElement("p",null,state.message);}
  let renderer;
  act(()=>{renderer=TestRenderer.create(React.createElement(Probe,{identity:"CAD:Voting:.5"}));});
  let download;
  act(()=>{download=state.download({format:"csv",section:"roc",target:"CAD",model:"Voting"});});
  assert.equal(state.busy,true);
  act(()=>renderer.update(React.createElement(Probe,{identity:"LAD:Voting:.5"})));
  assert.equal(signal.aborted,true);
  await act(async()=>{reject(new Error("late failure"));await download;});
  assert.equal(state.busy,false);
  assert.equal(text(renderer.root),"");
  act(()=>renderer.unmount());
});

test("switching between Assessment and Lab preserves entered patient values in the mounted workspace", async t => {
  const { default: App } = await compiler.ssrLoadModule("/src/App.tsx");
  const originalDocument=globalThis.document,originalMedia=globalThis.matchMedia;
  globalThis.document={addEventListener(){},removeEventListener(){},fullscreenElement:null};
  globalThis.matchMedia=()=>({matches:false,addEventListener(){},removeEventListener(){}});
  t.after(()=>{if(originalDocument===undefined)delete globalThis.document;else globalThis.document=originalDocument;if(originalMedia===undefined)delete globalThis.matchMedia;else globalThis.matchMedia=originalMedia;});
  t.mock.method(globalThis,"fetch",async url=>{
    const path=String(url);
    if(path.endsWith("/benchmarks"))return Response.json({targets:{},global_importances:{}});
    if(path.endsWith("/health"))return Response.json({status:"ok",service:"test",models_ready:true});
    if(path.endsWith("/sample-patients"))return Response.json([]);
    if(path.endsWith("/overview"))return Response.json(fixture);
    if(path.endsWith("/3d-anatomy"))return Response.json(null);
    return new Response("Unavailable",{status:404});
  });
  let renderer;
  await act(async()=>{renderer=TestRenderer.create(React.createElement(App));});
  act(()=>renderer.root.findByProps({id:"patient-measurement-Age"}).props.onChange({target:{value:"77"}}));
  const workspaceButton=name=>renderer.root.findAllByType("button").find(button=>text(button)===name);
  await act(async()=>{workspaceButton("Model Quality Lab").props.onClick();});
  const patientControl=renderer.root.findByProps({id:"patient-measurement-Age"});
  assert.equal(patientControl.props.value,77);
  assert.equal(renderer.root.findAllByProps({className:"workspace-panel"})[0].props.hidden,true);
  act(()=>workspaceButton("Assessment").props.onClick());
  assert.equal(renderer.root.findByProps({id:"patient-measurement-Age"}).props.value,77);
  assert.equal(renderer.root.findAllByProps({className:"workspace-panel"})[0].props.hidden,false);
  act(()=>renderer.unmount());
});

test("system dark appearance offers a light theme action and switches appearance on the first click", async t => {
  const { ModelQualityLab } = await compiler.ssrLoadModule("/src/model-quality/ModelQualityLab.tsx");
  const original=globalThis.matchMedia;
  globalThis.matchMedia=()=>({matches:true,addEventListener(){},removeEventListener(){}});
  t.after(()=>{if(original===undefined)delete globalThis.matchMedia;else globalThis.matchMedia=original;});
  let renderer;
  act(()=>{renderer=TestRenderer.create(React.createElement(ModelQualityLab,{initialData:fixture}));});
  const button=renderer.root.findByProps({"aria-label":"Switch to light Lab theme"});
  act(()=>button.props.onClick());
  assert.equal(renderer.root.findByProps({id:"model-quality-lab"}).props["data-theme"],"light");
  assert.ok(renderer.root.findByProps({"aria-label":"Switch to dark Lab theme"}));
  act(()=>renderer.unmount());
});

test("threshold, histogram, class balance and reproducibility downloads request their matching sections", async t => {
  const { ModelQualityLab } = await compiler.ssrLoadModule("/src/model-quality/ModelQualityLab.tsx");
  const originalDocument=globalThis.document;
  globalThis.document={createElement:()=>({click(){},remove(){}}),body:{appendChild(){}}};
  t.after(()=>{if(originalDocument===undefined)delete globalThis.document;else globalThis.document=originalDocument;});
  t.mock.method(URL,"createObjectURL",()=>"blob:quality");
  t.mock.method(URL,"revokeObjectURL",()=>{});
  t.mock.method(globalThis,"setTimeout",fn=>{fn();return 1;});
  const requests=[];
  t.mock.method(globalThis,"fetch",async url=>{
    const query=new URL(url,"http://localhost").searchParams;
    requests.push(Object.fromEntries(query));
    return new Response("run_id,section,path,value\nheldout-run,test,count,10",{headers:{"content-type":"text/csv"}});
  });
  let renderer;
  act(()=>{renderer=TestRenderer.create(React.createElement(ModelQualityLab,{initialData:fixture}));});
  for(const id of ["mq-thresholds","mq-histogram","mq-class-balance","mq-provenance"]){
    const section=renderer.root.findByProps({id});
    const button=section.findAllByType("button").find(button=>text(button)==="Download");
    assert.ok(button,`${id} exposes a report download`);
    await act(async()=>{button.props.onClick();await Promise.resolve();});
  }
  assert.deepEqual(requests.map(request=>request.section),["thresholds","histogram","class-distribution","reproducibility"]);
  assert.equal(requests[0].model,"CalibratedVoting");
  assert.equal(requests[0].target,"CAD");
  assert.equal(requests[2].model,undefined);
  assert.equal(requests[3].target,undefined);
  assert.ok(requests.every(request=>request.expected_run_id==="heldout-run"));
  act(()=>renderer.unmount());
});

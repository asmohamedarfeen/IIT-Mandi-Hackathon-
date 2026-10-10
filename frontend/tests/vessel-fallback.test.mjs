import test from 'node:test';
import assert from 'node:assert/strict';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { createServer } from 'vite';
const compiler = await createServer({ root: new URL('../', import.meta.url).pathname, optimizeDeps: { noDiscovery: true, include: [] }, server: { middlewareMode: true, hmr: false, ws: false }, appType: 'custom' });
const { HeartViewer3D } = await compiler.ssrLoadModule('/src/components/HeartViewer3D.tsx');
test.after(() => compiler.close());
const risk = { probability_percent: 43.2, risk_level: 'Moderate Risk', predicted_status: 'Stenotic', decision_threshold: .4 };
const prediction = { vessels: { LAD:risk, LCX:risk, RCA:risk }, vessel_colors_3d:{}, shap_explanations:{} };
const render = stale => renderToStaticMarkup(React.createElement(HeartViewer3D,{anatomyData:null,prediction,stale,error:true,onRetry:()=>{},selectedVessel:'rca',onSelectVessel:()=>{}}));
test('missing WebGL/anatomy has an equivalent vessel table with named selection buttons',()=>{
 const html = render(false);
 assert.match(html,/<table/);
 assert.match(html,/Coronary vessel assessment/);
 assert.match(html,/43.2%/);
 assert.match(html,/Stenotic/);
 assert.match(html,/Select RCA detail/);
 assert.match(html,/aria-pressed="true"/);
});
test('fallback hides old scores when inputs changed',()=>{
 const html = render(true);
 assert.doesNotMatch(html,/43.2%/);
 assert.match(html,/Needs reassessment/);
});

test('fallback native buttons route keyboard activation to shared vessel selection',async()=>{
 const {default: TestRenderer} = await import('react-test-renderer');
 const previousDocument = globalThis.document;
 const previousMedia = globalThis.matchMedia;
 globalThis.document = {addEventListener(){},removeEventListener(){},fullscreenElement:null};
 globalThis.matchMedia = ()=>({matches:true,addEventListener(){},removeEventListener(){}});
 let selected;
 let view;
 try {
  TestRenderer.act(()=>{view=TestRenderer.create(React.createElement(HeartViewer3D,{anatomyData:null,prediction,error:true,onRetry:()=>{},selectedVessel:null,onSelectVessel:value=>{selected=value}}));});
  const button = view.root.findAllByType('button').find(button=>button.props['aria-label']==='Select RCA detail');
  TestRenderer.act(()=>button.props.onClick());
  assert.equal(selected,'rca');
  assert.equal(button.type,'button');
 } finally {
  if(view) TestRenderer.act(()=>view.unmount());
  globalThis.document=previousDocument;
  globalThis.matchMedia=previousMedia;
 }
});

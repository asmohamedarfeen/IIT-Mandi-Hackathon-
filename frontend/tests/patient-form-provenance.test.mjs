import test from 'node:test';
import assert from 'node:assert/strict';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { createServer } from 'vite';
const compiler = await createServer({ root: new URL('../', import.meta.url).pathname, optimizeDeps: { noDiscovery: true, include: [] }, server: { middlewareMode: true, hmr: false, ws: false }, appType: 'custom' });
const { PatientForm } = await compiler.ssrLoadModule('/src/components/PatientForm.tsx');
const { normalizePatient, DEFAULT_PATIENT } = await compiler.ssrLoadModule('/src/utils/patient.ts');
test.after(() => compiler.close());
const render = patientData => renderToStaticMarkup(React.createElement(PatientForm, {patientData,onChange:()=>{},onSubmit:()=>{},isLoading:false,ready:true}));
test('reviewed form shows completion and review attestations distinct from demo defaults',()=>{
 const html = render({...normalizePatient(DEFAULT_PATIENT), assessment_mode:'reviewed'});
 assert.match(html,/Reviewed case/);
 assert.match(html,/verified each modeled measurement/);
 assert.match(html,/not a clinical validation/);
 assert.match(html,/0 \/ 53/);
});
test('invalid numeric control exposes field guidance and accessible error linkage',()=>{
 const html = render({...normalizePatient(DEFAULT_PATIENT), Age:NaN});
 assert.match(html,/aria-invalid="true"/);
 assert.match(html,/Enter Age between 18 and 120/);
 assert.match(html,/aria-describedby/);
});

test('explicitly unknown categorical measurement stays unknown instead of becoming No', async()=>{
 const { default: TestRenderer } = await import('react-test-renderer');
 let changed;
 const view = TestRenderer.create(React.createElement(PatientForm, {patientData:normalizePatient(DEFAULT_PATIENT),onChange:value=>{changed=value},onSubmit:()=>{},isLoading:false,ready:true}));
 const select = view.root.findAllByType('select').find(control=>control.props.id==='patient-measurement-DM');
 const unknown = select.findAllByType('option').find(option=>option.props.value==='');
 assert.notEqual(unknown.props.disabled, true);
 select.props.onChange({target:{value:''}});
 assert.ok(Number.isNaN(changed.DM));
 assert.equal(changed.input_sources.DM,'unknown');
 view.unmount();
});

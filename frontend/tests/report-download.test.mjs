import test from "node:test";
import assert from "node:assert/strict";
import React from "react";
import TestRenderer, { act } from "react-test-renderer";
import { createServer } from "vite";

const compiler = await createServer({ root: new URL("../", import.meta.url).pathname, server: { middlewareMode: true, ws: false }, appType: "custom" });
const { EvidenceReportDownload } = await compiler.ssrLoadModule("/src/components/EvidenceReportDownload.tsx");
const { apiService } = await compiler.ssrLoadModule("/src/services/api.ts");
test.after(() => compiler.close());
const prediction = { evidence: { assessment_id: "report-one", report_available: true } };
const text = node => typeof node === "string" ? node : (node.children || []).map(text).join("");
function render(props = {}) {
  let renderer;
  act(() => { renderer = TestRenderer.create(React.createElement(EvidenceReportDownload, { prediction, stale: false, busy: false, ...props })); });
  return renderer;
}

test("report button is disabled for unassessed, stale, busy and unsaved results", () => {
  for (const props of [{ prediction: null }, { stale: true }, { busy: true }, { prediction: { evidence: { assessment_id: "old", report_available: false } } }]) {
    const renderer = render(props);
    assert.equal(renderer.root.findByType("button").props.disabled, true);
    act(() => renderer.unmount());
  }
});

test("one click downloads exactly the completed assessment and permits retry after a failure", async () => {
  const calls = [];
  let attempt = 0;
  const renderer = render({ onDownload: async (id, signal) => {
    calls.push([id, signal.aborted]);
    if (!attempt++) throw new Error("offline");
  } });
  await act(async () => { await renderer.root.findByType("button").props.onClick(); });
  assert.match(text(renderer.root), /could not be downloaded/);
  assert.equal(renderer.root.findByType("button").props.disabled, false);
  await act(async () => { await renderer.root.findByType("button").props.onClick(); });
  assert.deepEqual(calls, [["report-one", false], ["report-one", false]]);
  assert.doesNotMatch(text(renderer.root), /could not be downloaded/);
  act(() => renderer.unmount());
});

test("editing inputs aborts a pending download and suppresses its stale error", async () => {
  let reject, signal;
  const pending = new Promise((_, no) => { reject = no; });
  const renderer = render({ onDownload: async (_, abortSignal) => { signal = abortSignal; return pending; } });
  let running;
  act(() => { running = renderer.root.findByType("button").props.onClick(); });
  assert.equal(renderer.root.findByType("button").props.disabled, true);
  act(() => renderer.update(React.createElement(EvidenceReportDownload, { prediction, stale: true, busy: false })));
  assert.equal(signal.aborted, true);
  await act(async () => { reject(new Error("cancelled")); await running; });
  assert.doesNotMatch(text(renderer.root), /could not be downloaded/);
  act(() => renderer.unmount());
});

test("download service creates and cleans up a PDF download for the requested assessment", async t => {
  const events = [];
  const originalDocument = globalThis.document;
  const link = { click: () => events.push("click"), remove: () => events.push("remove") };
  globalThis.document = { createElement: () => link, body: { appendChild: () => events.push("append") } };
  t.after(() => { if (originalDocument === undefined) delete globalThis.document; else globalThis.document = originalDocument; });
  t.mock.method(globalThis, "fetch", async (url, options) => {
    assert.match(url, /\/assessments\/assessment-one\/report$/);
    assert.equal(options.cache, "no-store");
    return new Response("%PDF-1.4 test", { headers: { "content-type": "application/pdf" } });
  });
  t.mock.method(URL, "createObjectURL", () => "blob:test-report");
  t.mock.method(URL, "revokeObjectURL", url => { assert.equal(url, "blob:test-report"); events.push("revoke"); });
  t.mock.method(globalThis, "setTimeout", fn => { fn(); return 1; });
  await apiService.downloadEvidenceReport("assessment-one");
  assert.equal(link.download, "cardiovision-evidence-assessment-one.pdf");
  assert.equal(link.href, "blob:test-report");
  assert.deepEqual(events, ["append", "click", "remove", "revoke"]);
});

test("download service rejects error or invalid responses and does not save a cancelled report", async t => {
  t.mock.method(URL, "createObjectURL", () => { throw new Error("must not create a file"); });
  for (const response of [
    new Response("unavailable", { status: 503 }),
    new Response("not a PDF", { headers: { "content-type": "application/pdf" } }),
    new Response("%PDF-1.4", { headers: { "content-type": "text/html" } }),
  ]) {
    t.mock.method(globalThis, "fetch", async () => response);
    await assert.rejects(apiService.downloadEvidenceReport("assessment-one"), /unavailable|Invalid/);
  }
  t.mock.method(globalThis, "fetch", async () => new Response("%PDF-1.4", { headers: { "content-type": "application/pdf" } }));
  const controller = new AbortController();
  controller.abort();
  await apiService.downloadEvidenceReport("assessment-one", controller.signal);
});

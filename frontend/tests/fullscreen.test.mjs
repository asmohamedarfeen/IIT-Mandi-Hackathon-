import test from "node:test";
import assert from "node:assert/strict";
import { toggleFullscreen } from "../src/utils/fullscreen.ts";

test("unsupported fullscreen remains actionable with visible feedback", async () => {
  assert.match(await toggleFullscreen({}, { fullscreenElement: null }), /unavailable/);
  assert.match(await toggleFullscreen({ requestFullscreen: async () => assert.fail() }, {
    fullscreenElement: null, fullscreenEnabled: false,
  }), /unavailable/);
  assert.match(await toggleFullscreen(null, { fullscreenElement: {} }), /unavailable/);
});
test("fullscreen entry and exit rejection return concise recovery feedback", async () => {
  const denied = () => Promise.reject(new Error("Policy denied"));
  assert.match(await toggleFullscreen({ requestFullscreen: denied }, { fullscreenElement: null }), /could not be opened/);
  assert.match(await toggleFullscreen(null, { fullscreenElement: {}, exitFullscreen: denied }), /Escape/);
  assert.match(await toggleFullscreen({ requestFullscreen: () => { throw new Error(); } }, { fullscreenElement: null }), /could not be opened/);
});
test("fullscreen enters and exits through the owning optional API", async () => {
  let entered = false, exited = false;
  const stage = { requestFullscreen: async function () { assert.equal(this, stage); entered = true; } };
  const page = { fullscreenElement: {}, exitFullscreen: async function () { assert.equal(this, page); exited = true; } };
  assert.equal(await toggleFullscreen(stage, { fullscreenElement: null }), null);
  assert.equal(await toggleFullscreen(null, page), null);
  assert.ok(entered && exited);
});

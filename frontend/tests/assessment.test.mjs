import test from "node:test";
import assert from "node:assert/strict";
import { createAssessmentRunner } from "../src/utils/assessment.ts";

function deferred() {
  let resolve, reject;
  const promise = new Promise((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
}
function setup(predict, delay = 700) {
  const events = [];
  const runner = createAssessmentRunner(predict, {
    onStart: () => events.push("start"),
    onResult: (result, auto) => events.push([result, auto]),
    onError: () => events.push("error"),
    onFinish: () => events.push("finish"),
  }, delay);
  return { runner, events };
}

test("rapid edits run only the final snapshot after the debounce", async t => {
  t.mock.timers.enable({ apis: ["setTimeout"] });
  const { runner, events } = setup(async data => data.Age);
  runner.schedule({ Age: 50 }, () => true);
  t.mock.timers.tick(500);
  runner.schedule({ Age: 65 }, () => true);
  t.mock.timers.tick(699);
  assert.deepEqual(events, []);
  t.mock.timers.tick(1);
  await Promise.resolve();
  assert.deepEqual(events, ["start", [65, true], "finish"]);
  runner.dispose();
});

test("invalid inputs do not run and manual submission cancels pending automatic work", async t => {
  t.mock.timers.enable({ apis: ["setTimeout"] });
  const { runner, events } = setup(async data => data.Age);
  runner.schedule({ Age: NaN }, () => false);
  t.mock.timers.tick(700);
  assert.deepEqual(events, []);
  runner.schedule({ Age: 70 }, () => true);
  await runner.run({ Age: 55 });
  t.mock.timers.tick(700);
  assert.deepEqual(events, ["start", [55, false], "finish"]);
  runner.dispose();
});

test("invalidation aborts inference and discards a late response even if the server ignores abort", async () => {
  const old = deferred();
  let signal;
  const { runner, events } = setup((data, abortSignal) => {
    if (data.Age === 50) { signal = abortSignal; return old.promise; }
    return Promise.resolve("new");
  });
  const first = runner.run({ Age: 50 });
  runner.invalidate();
  assert.equal(signal.aborted, true);
  await runner.run({ Age: 60 });
  old.resolve("old");
  await first;
  assert.deepEqual(events.filter(Array.isArray), [["new", false]]);
});

test("failure finishes loading and a manual retry can succeed", async () => {
  let attempts = 0;
  const { runner, events } = setup(async () => {
    if (!attempts++) throw new Error("offline");
    return "recovered";
  });
  await runner.run({ Age: 50 });
  assert.deepEqual(events, ["start", "error", "finish"]);
  await runner.run({ Age: 50 });
  assert.deepEqual(events.slice(3), ["start", ["recovered", false], "finish"]);
});

test("dispose cancels scheduled updates and suppresses pending error callbacks", async t => {
  t.mock.timers.enable({ apis: ["setTimeout"] });
  const pending = deferred();
  const { runner, events } = setup(() => pending.promise);
  const first = runner.run({ Age: 50 });
  runner.dispose();
  pending.reject(new Error("aborted"));
  await first;
  assert.equal(events.includes("error"), false);
  runner.schedule({ Age: 60 }, () => true);
  runner.dispose();
  t.mock.timers.tick(700);
  assert.equal(events.filter(e => e === "start").length, 1);
});

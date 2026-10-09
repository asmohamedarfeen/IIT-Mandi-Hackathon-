import test from 'node:test';
import assert from 'node:assert/strict';
import { createRenderLoop } from '../src/utils/renderLoop.ts';

test('hidden workspace pauses rendering without destroying its scene and resumes once', () => {
  const callbacks = new Map(); let next = 0, rendered = 0;
  const loop = createRenderLoop(() => rendered++, fn => { callbacks.set(++next, fn); return next; }, id => callbacks.delete(id));
  loop.setActive(true);
  loop.setActive(true);
  assert.equal(callbacks.size, 1);
  const [id, callback] = [...callbacks][0]; callbacks.delete(id); callback(10);
  assert.equal(rendered, 1);
  loop.setActive(false);
  assert.equal(callbacks.size, 0);
  loop.setActive(true);
  assert.equal(callbacks.size, 1);
  loop.dispose();
  loop.setActive(true);
  assert.equal(callbacks.size, 0);
});

/** Pause hidden scenes while keeping their camera, meshes and controls alive. */
export function createRenderLoop(
  render: (time: number) => void,
  schedule: (callback: FrameRequestCallback) => number = requestAnimationFrame,
  cancel: (id: number) => void = cancelAnimationFrame,
) {
  let frame: number | undefined;
  let active = false;
  let disposed = false;
  function tick(time: number) {
    frame = undefined;
    if (!active || disposed) return;
    render(time);
    frame = schedule(tick);
  }
  function setActive(next: boolean) {
    if (disposed || next === active) return;
    active = next;
    if (frame !== undefined) cancel(frame);
    frame = next ? schedule(tick) : undefined;
  }
  function dispose() {
    setActive(false);
    disposed = true;
  }
  return { setActive, dispose };
}

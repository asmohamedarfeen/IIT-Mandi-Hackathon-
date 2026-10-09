export function measurementAnchorId(inputKey: string): string {
  return `patient-measurement-${encodeURIComponent(inputKey)}`;
}

/** Source navigation reads/focuses the form; it never changes values or submits it. */
export function focusMeasurement(root: HTMLElement, inputKey: string, reducedMotion: boolean): boolean {
  const input = root.querySelector<HTMLElement>(`[id="${measurementAnchorId(inputKey)}"]`);
  if (!input) return false;
  const group = input.closest("details");
  if (group) group.open = true;
  input.scrollIntoView({ behavior: reducedMotion ? "auto" : "smooth", block: "center" });
  input.focus({ preventScroll: true });
  if (!reducedMotion) input.animate?.([
    { outline: "3px solid #697c43", outlineOffset: "4px" },
    { outline: "3px solid transparent", outlineOffset: "4px" },
  ], { duration: 2200, easing: "ease-out" });
  return true;
}

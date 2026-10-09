import type { PatientData, PredictionResponse } from "./types";

/** One inference owns all result views; superseded requests cannot publish results. */
export function createAssessmentRunner<T = PredictionResponse>(
  predict: (patient: PatientData, signal: AbortSignal) => Promise<T>,
  callbacks: {
    onStart: () => void;
    onResult: (result: T, automatic: boolean) => void;
    onError: () => void;
    onFinish: () => void;
  },
  delay = 700,
) {
  let generation = 0;
  let timer: ReturnType<typeof setTimeout> | undefined;
  let controller: AbortController | undefined;
  function invalidate() {
    generation++;
    clearTimeout(timer);
    timer = undefined;
    if (controller) {
      controller.abort();
      controller = undefined;
      callbacks.onFinish();
    }
  }
  async function run(patient: PatientData, automatic = false) {
    invalidate();
    const token = generation;
    controller = new AbortController();
    callbacks.onStart();
    try {
      const result = await predict({ ...patient }, controller.signal);
      if (token === generation) callbacks.onResult(result, automatic);
    } catch {
      if (token === generation) callbacks.onError();
    } finally {
      if (token === generation) {
        controller = undefined;
        callbacks.onFinish();
      }
    }
  }
  function schedule(patient: PatientData, canRun: () => boolean) {
    invalidate();
    const snapshot = { ...patient };
    timer = setTimeout(() => {
      timer = undefined;
      if (canRun()) void run(snapshot, true);
    }, delay);
  }
  function dispose() {
    // Avoid React state callbacks during unmount cleanup.
    generation++;
    clearTimeout(timer);
    timer = undefined;
    controller?.abort();
    controller = undefined;
  }
  return { run, schedule, invalidate, dispose };
}

import { useCallback, useEffect, useRef, useState } from "react";
import { apiService } from "../services/api";
import type { ModelQualityOverview, QualityReportRequest, ThresholdPoint } from "./types";

export function displayMetric(value: unknown, digits = 3) {
  return typeof value === "number" && Number.isFinite(value) ? value.toFixed(digits) : "Unavailable";
}
export function exactThreshold(points: ThresholdPoint[] | undefined, threshold: number) {
  return points?.find(point => Math.abs(point.threshold - threshold) < 1e-9);
}
export function useQualityOverview(initialData?: ModelQualityOverview, loadOverview = apiService.getModelQualityOverview) {
  const [data, setData] = useState(initialData ?? null);
  const [loading, setLoading] = useState(!initialData);
  const [error, setError] = useState("");
  const controller = useRef<AbortController | null>(null);
  const reload = useCallback(async () => {
    controller.current?.abort();
    const request = new AbortController();
    controller.current = request;
    setLoading(true); setError("");
    try {
      const result = await loadOverview(request.signal);
      if (controller.current === request && !request.signal.aborted) setData(result);
    } catch (failure) {
      if (controller.current === request && !request.signal.aborted) setError(failure instanceof Error ? failure.message : "Model quality data unavailable");
    } finally {
      if (controller.current === request && !request.signal.aborted) { setLoading(false); controller.current = null; }
    }
  }, [loadOverview]);
  useEffect(() => {
    if (!initialData) void reload();
    return () => { controller.current?.abort(); controller.current = null; };
  }, [initialData, reload]);
  return {data, loading, error, reload};
}
export function useQualityDownload(identity: string, onDownload = apiService.downloadModelQualityReport) {
  const request = useRef<AbortController | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState(false);
  useEffect(() => {
    request.current?.abort(); request.current = null;
    setBusy(false); setMessage(""); setError(false);
    return () => { request.current?.abort(); request.current = null; };
  }, [identity]);
  async function download(options: QualityReportRequest) {
    if (request.current) return;
    const controller = new AbortController(); request.current = controller;
    setBusy(true); setMessage(""); setError(false);
    try {
      await onDownload(options, controller.signal);
      if (request.current === controller && !controller.signal.aborted) setMessage(`${options.format.toUpperCase()} artifact downloaded.`);
    } catch (failure) {
      if (request.current === controller && !controller.signal.aborted) { setMessage(failure instanceof Error && failure.message.startsWith("Saved run changed.") ? failure.message : "Download unavailable. Retry this artifact."); setError(true); }
    } finally {
      if (request.current === controller && !controller.signal.aborted) { request.current = null; setBusy(false); }
    }
  }
  return {busy, message, error, download};
}

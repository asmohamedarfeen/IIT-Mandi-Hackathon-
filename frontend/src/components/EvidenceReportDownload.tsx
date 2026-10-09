import { useEffect, useRef, useState } from "react";
import { Download } from "lucide-react";
import type { PredictionResponse } from "../utils/types";
import { apiService } from "../services/api";

export function EvidenceReportDownload({ prediction, stale, busy, onDownload = apiService.downloadEvidenceReport }: {
  prediction: PredictionResponse | null;
  stale: boolean;
  busy: boolean;
  onDownload?: (assessmentId: string, signal: AbortSignal) => Promise<void>;
}) {
  const request = useRef<AbortController | null>(null);
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const id = prediction?.evidence?.assessment_id;
  const eligible = Boolean(id && prediction?.evidence?.report_available && !stale && !busy);
  useEffect(() => {
    request.current?.abort();
    request.current = null;
    setDownloading(false);
    setError("");
    setMessage("");
    return () => { request.current?.abort(); };
  }, [prediction, id, stale, busy]);

  async function download() {
    if (!eligible || !id || request.current) return;
    const controller = new AbortController();
    request.current = controller;
    setDownloading(true);
    setError("");
    setMessage("");
    try {
      await onDownload(id, controller.signal);
      if (request.current === controller && !controller.signal.aborted) setMessage("Evidence PDF downloaded.");
    } catch {
      if (request.current === controller && !controller.signal.aborted) setError("The report could not be downloaded. Please try again.");
    } finally {
      if (request.current === controller && !controller.signal.aborted) {
        request.current = null;
        setDownloading(false);
      }
    }
  }
  return <div className="evidence-report-download">
    <button type="button" className="button" disabled={!eligible || downloading} onClick={download}>
      <Download size={16} /> {downloading ? "Preparing report…" : error ? "Retry evidence report" : "Download evidence report"}
    </button>
    <p role={error ? "alert" : "status"}>
      {error || message || (eligible ? "PDF · assessed inputs, results and model evidence" : stale || busy ? "Available when the current assessment completes." : "Requires a completed, saved assessment.")}
    </p>
  </div>;
}

/**
 * API Service for communicating with FastAPI backend.
 * Uses environment variable VITE_API_BASE_URL or falls back to relative /api/v1.
 */

import {
  PatientData,
  PredictionResponse,
  SamplePatient,
  BenchmarkData,
  ThreeDAnatomyPayload,
} from "../utils/types";
import type { ModelQualityOverview, QualityReportRequest } from "../model-quality/types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api/v1";

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const errorBody = await res.text();
    let detail = `Server responded with ${res.status}: ${res.statusText}`;
    try {
      const parsed = JSON.parse(errorBody);
      if (parsed.detail) detail = parsed.detail;
    } catch {
      // ignore
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

export const apiService = {
  async getModelQualityOverview(signal?: AbortSignal): Promise<ModelQualityOverview> {
    const response = await fetch(`${API_BASE_URL}/model-quality/overview`, { signal, cache: "no-store" });
    return handleResponse<ModelQualityOverview>(response);
  },
  async downloadModelQualityReport(options: QualityReportRequest, signal?: AbortSignal): Promise<void> {
    const query = new URLSearchParams({ format: options.format, section: options.section });
    if (options.target) query.set("target", options.target);
    if (options.model) query.set("model", options.model);
    if (options.models?.length) query.set("models", options.models.join(","));
    if (options.threshold !== undefined) query.set("threshold", String(options.threshold));
    if (options.expected_run_id) query.set("expected_run_id", options.expected_run_id);
    const response = await fetch(`${API_BASE_URL}/model-quality/report?${query}`, { signal, cache: "no-store" });
    if (response.status === 409) throw new Error("Saved run changed. Refresh the Lab before downloading this artifact.");
    const contentType = response.headers.get("content-type") || "";
    const validType = options.format === "pdf" ? contentType.includes("application/pdf") : options.format === "json" ? contentType.includes("application/json") : contentType.includes("text/csv");
    if (!response.ok || !validType) throw new Error("Model quality artifact unavailable");
    const blob = await response.blob();
    if (options.format === "pdf" && !(await blob.slice(0, 5).text()).startsWith("%PDF-")) throw new Error("Invalid model quality artifact");
    if (options.format === "json") { try { JSON.parse(await blob.text()); } catch { throw new Error("Invalid model quality artifact"); } }
    if (signal?.aborted) return;
    const suppliedFilename = response.headers.get("content-disposition")?.match(/filename="([A-Za-z0-9_.-]+)"/)?.[1];
    saveBlob(blob, suppliedFilename || `cardiovision-model-quality-${options.section}${options.target ? `-${options.target}` : ""}${options.model ? `-${options.model}` : ""}.${options.format}`);
  },
  async downloadEvidenceReport(assessmentId: string, signal?: AbortSignal): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/assessments/${encodeURIComponent(assessmentId)}/report`, { signal, cache: "no-store" });
    if (!response.ok || !response.headers.get("content-type")?.includes("application/pdf")) {
      throw new Error("Evidence report unavailable");
    }
    const blob = await response.blob();
    if (!(await blob.slice(0, 5).text()).startsWith("%PDF-")) throw new Error("Invalid evidence report");
    if (signal?.aborted) return;
    saveBlob(blob, `cardiovision-evidence-${assessmentId}.pdf`);
  },
  /**
   * Submit patient clinical parameters to run calibrated multi-vessel prediction and SHAP analysis.
   */
  async predictPatient(data: PatientData, signal?: AbortSignal): Promise<PredictionResponse> {
    const response = await fetch(`${API_BASE_URL}/predict`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
      signal,
    });
    return handleResponse<PredictionResponse>(response);
  },

  /**
   * Fetch 10-fold cross-validation performance benchmarks across all candidate models.
   */
  async getBenchmarks(): Promise<BenchmarkData> {
    const response = await fetch(`${API_BASE_URL}/benchmarks`);
    return handleResponse<BenchmarkData>(response);
  },

  /**
   * Retrieve pre-loaded sample patients for 1-click clinical testing in the UI.
   */
  async getSamplePatients(): Promise<SamplePatient[]> {
    const response = await fetch(`${API_BASE_URL}/sample-patients`);
    return handleResponse<SamplePatient[]>(response);
  },

  /**
   * Load normalized 3D heart anatomical structures (LAD, LCX, RCA, Myocardium).
   */
  async getHeartAnatomy(): Promise<ThreeDAnatomyPayload> {
    try {
      // First try local static public folder
      const localRes = await fetch("/heart_model_anatomy.json");
      if (localRes.ok) {
        return (await localRes.json()) as ThreeDAnatomyPayload;
      }
    } catch {
      // fallback to backend endpoint
    }
    const response = await fetch(`${API_BASE_URL}/3d-anatomy`);
    return handleResponse<ThreeDAnatomyPayload>(response);
  },

  /**
   * Check backend service health.
   */
  async checkHealth(): Promise<{
    status: string;
    service: string;
    models_ready: boolean;
  }> {
    const response = await fetch(`${API_BASE_URL}/health`);
    return handleResponse<{
      status: string;
      service: string;
      models_ready: boolean;
    }>(response);
  },
};

function saveBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url; link.download = filename;
  document.body.appendChild(link);
  try { link.click(); }
  finally { link.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000); }
}

/**
 * API Service for communicating with FastAPI backend.
 * Uses environment variable VITE_API_BASE_URL or falls back to relative /api/v1.
 */

import {
  PatientData,
  PredictionResponse,
  SamplePatient,
  BenchmarkData,
  ThreeDAnatomyPayload
} from '../utils/types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

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
  /**
   * Submit patient clinical parameters to run calibrated multi-vessel prediction and SHAP analysis.
   */
  async predictPatient(data: PatientData): Promise<PredictionResponse> {
    const response = await fetch(`${API_BASE_URL}/predict`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
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
      const localRes = await fetch('/heart_model_anatomy.json');
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
  async checkHealth(): Promise<{ status: string; service: string }> {
    const response = await fetch(`${API_BASE_URL}/health`);
    return handleResponse<{ status: string; service: string }>(response);
  },
};

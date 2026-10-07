import React, { useState, useEffect } from 'react';
import { HeartViewer3D } from '../components/HeartViewer3D';
import { RiskSummaryCards } from '../components/RiskSummaryCards';
import { PatientForm } from '../components/PatientForm';
import { SHAPExplanationChart } from '../components/SHAPExplanationChart';
import { apiService } from '../services/api';
import {
  PatientData,
  PredictionResponse,
  SamplePatient,
  ThreeDAnatomyPayload,
} from '../utils/types';
import { AlertTriangle, RefreshCw } from 'lucide-react';

const DEFAULT_PATIENT: PatientData = {
  patient_id: 'PATIENT-001',
  Age: 55,
  Sex: 'Male',
  Weight: 72,
  Length: 170,
  BMI: 24.9,
  DM: 0,
  HTN: 0,
  'Current Smoker': 0,
  'EX-Smoker': 0,
  FH: 0,
  Obesity: 'N',
  CRF: 'N',
  CVA: 'N',
  'Airway disease': 'N',
  'Thyroid Disease': 'N',
  CHF: 'N',
  DLP: 'N',
  BP: 120,
  PR: 75,
  Edema: 0,
  'Weak Peripheral Pulse': 'N',
  'Lung rales': 'N',
  'Systolic Murmur': 'N',
  'Diastolic Murmur': 'N',
  'Typical Chest Pain': 0,
  Dyspnea: 'N',
  'Function Class': 0,
  Atypical: 'N',
  Nonanginal: 'N',
  'Exertional CP': 'N',
  'LowTH Ang': 'N',
  'Q Wave': 0,
  'St Elevation': 0,
  'St Depression': 0,
  Tinversion: 0,
  LVH: 'N',
  'Poor R Progression': 'N',
  BBB: 'N',
  FBS: 90,
  CR: 0.9,
  TG: 130,
  LDL: 100,
  HDL: 45,
  BUN: 15,
  ESR: 12,
  HB: 14,
  K: 4.2,
  Na: 140,
  WBC: 6500,
  Lymph: 30,
  Neut: 60,
  PLT: 220,
  'EF-TTE': 55,
  'Region RWMA': 0,
  VHD: 'N',
};

export const DashboardPage: React.FC = () => {
  const [patientData, setPatientData] = useState<PatientData>(DEFAULT_PATIENT);
  const [prediction, setPrediction] = useState<PredictionResponse | null>(null);
  const [anatomyData, setAnatomyData] = useState<ThreeDAnatomyPayload | null>(null);
  const [samplePatients, setSamplePatients] = useState<SamplePatient[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Initial load
  useEffect(() => {
    const initData = async () => {
      try {
        setIsLoading(true);

        // Load 3D anatomy and sample cohorts in parallel
        const [anatomy, samples] = await Promise.all([
          apiService.getHeartAnatomy().catch((err) => {
            console.warn('Could not load 3D anatomy:', err);
            return null;
          }),
          apiService.getSamplePatients().catch((err) => {
            console.warn('Could not load sample patients:', err);
            return [];
          }),
        ]);

        if (anatomy) setAnatomyData(anatomy);
        if (samples.length > 0) setSamplePatients(samples);

        // Run baseline prediction on default patient
        const initialPred = await apiService.predictPatient(DEFAULT_PATIENT);
        setPrediction(initialPred);
      } catch (err: any) {
        setError(err.message || 'Initialization failed.');
      } finally {
        setIsLoading(false);
      }
    };

    initData();
  }, []);

  const handlePredict = async (data: PatientData) => {
    try {
      setIsLoading(true);
      setError(null);
      const res = await apiService.predictPatient(data);
      setPrediction(res);
    } catch (err: any) {
      setError(err.message || 'Prediction failed. Check backend status.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Error banner */}
      {error && (
        <div className="flex items-center gap-2 rounded-xl border border-rose-500/30 bg-rose-500/10 p-3.5 text-xs text-rose-300">
          <AlertTriangle className="h-4 w-4 shrink-0 text-rose-400" />
          <span>{error}</span>
        </div>
      )}

      {/* Multi-Target Calibrated Risk Summary Cards */}
      <RiskSummaryCards
        overallCad={prediction?.overall_cad}
        vessels={prediction?.vessels}
      />

      {/* Main Grid: 3D Heart Viewer & Patient Clinical Input */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: 3D Anatomical Heart (7 cols on desktop) */}
        <div className="lg:col-span-7 h-[560px]">
          <HeartViewer3D
            anatomyData={anatomyData}
            vesselColors={
              prediction?.vessel_colors_3d || {
                lad: '#10B981',
                lcx: '#10B981',
                rca: '#10B981',
                myocardium: '#64748B',
              }
            }
            vesselRisks={prediction?.vessels}
            isLoading={isLoading}
          />
        </div>

        {/* Right Column: Patient Clinical Form (5 cols on desktop) */}
        <div className="lg:col-span-5">
          <PatientForm
            patientData={patientData}
            onChange={setPatientData}
            onSubmit={handlePredict}
            samplePatients={samplePatients}
            isLoading={isLoading}
          />
        </div>
      </div>

      {/* Bottom Section: Explainable AI TreeSHAP feature impacts */}
      <div>
        <SHAPExplanationChart explanations={prediction?.shap_explanations} />
      </div>
    </div>
  );
};

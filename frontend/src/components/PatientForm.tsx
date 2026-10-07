import React, { useState } from 'react';
import { PatientData, SamplePatient } from '../utils/types';
import { User, Activity, Stethoscope, HeartPulse, FlaskConical, Play, RefreshCw, CheckCircle2 } from 'lucide-react';

interface PatientFormProps {
  patientData: PatientData;
  onChange: (data: PatientData) => void;
  onSubmit: (data: PatientData) => void;
  samplePatients: SamplePatient[];
  isLoading: boolean;
}

export const PatientForm: React.FC<PatientFormProps> = ({
  patientData,
  onChange,
  onSubmit,
  samplePatients,
  isLoading,
}) => {
  const [activeTab, setActiveTab] = useState<'demo' | 'vitals' | 'symptoms' | 'ecg' | 'labs'>('demo');

  const updateField = (field: keyof PatientData, value: any) => {
    onChange({
      ...patientData,
      [field]: value,
    });
  };

  const handleLoadSample = (sample: SamplePatient) => {
    const raw = sample.features;
    onChange({
      ...patientData,
      patient_id: sample.patient_id,
      Age: Number(raw.Age ?? 55),
      Sex: raw.Sex === 1 || raw.Sex === 'Male' ? 'Male' : 'Female',
      Weight: Number(raw.Weight ?? 72),
      Length: Number(raw.Length ?? 170),
      BMI: Number(raw.BMI ?? 25),
      DM: Number(raw.DM ?? 0),
      HTN: Number(raw.HTN ?? 0),
      "Current Smoker": Number(raw["Current Smoker"] ?? 0),
      "EX-Smoker": Number(raw["EX-Smoker"] ?? 0),
      FH: Number(raw.FH ?? 0),
      Obesity: raw.Obesity ?? 'N',
      CRF: raw.CRF ?? 'N',
      CVA: raw.CVA ?? 'N',
      "Airway disease": raw["Airway disease"] ?? 'N',
      "Thyroid Disease": raw["Thyroid Disease"] ?? 'N',
      CHF: raw.CHF ?? 'N',
      DLP: raw.DLP ?? 'N',
      BP: Number(raw.BP ?? 120),
      PR: Number(raw.PR ?? 75),
      Edema: Number(raw.Edema ?? 0),
      "Weak Peripheral Pulse": raw["Weak Peripheral Pulse"] ?? 'N',
      "Lung rales": raw["Lung rales"] ?? 'N',
      "Systolic Murmur": raw["Systolic Murmur"] ?? 'N',
      "Diastolic Murmur": raw["Diastolic Murmur"] ?? 'N',
      "Typical Chest Pain": Number(raw["Typical Chest Pain"] ?? 0),
      Dyspnea: raw.Dyspnea ?? 'N',
      "Function Class": Number(raw["Function Class"] ?? 0),
      Atypical: raw.Atypical ?? 'N',
      Nonanginal: raw.Nonanginal ?? 'N',
      "Exertional CP": raw["Exertional CP"] ?? 'N',
      "LowTH Ang": raw["LowTH Ang"] ?? 'N',
      "Q Wave": Number(raw["Q Wave"] ?? 0),
      "St Elevation": Number(raw["St Elevation"] ?? 0),
      "St Depression": Number(raw["St Depression"] ?? 0),
      Tinversion: Number(raw.Tinversion ?? 0),
      LVH: raw.LVH ?? 'N',
      "Poor R Progression": raw["Poor R Progression"] ?? 'N',
      BBB: raw.BBB ?? 'N',
      FBS: Number(raw.FBS ?? 90),
      CR: Number(raw.CR ?? 0.9),
      TG: Number(raw.TG ?? 130),
      LDL: Number(raw.LDL ?? 100),
      HDL: Number(raw.HDL ?? 45),
      BUN: Number(raw.BUN ?? 15),
      ESR: Number(raw.ESR ?? 12),
      HB: Number(raw.HB ?? 14),
      K: Number(raw.K ?? 4.2),
      Na: Number(raw.Na ?? 140),
      WBC: Number(raw.WBC ?? 6500),
      Lymph: Number(raw.Lymph ?? 30),
      Neut: Number(raw.Neut ?? 60),
      PLT: Number(raw.PLT ?? 220),
      "EF-TTE": Number(raw["EF-TTE"] ?? 55),
      "Region RWMA": Number(raw["Region RWMA"] ?? 0),
      VHD: raw.VHD ?? 'N',
    });
  };

  const tabs = [
    { id: 'demo', label: 'Demographics', icon: User },
    { id: 'vitals', label: 'Vitals & Exam', icon: Activity },
    { id: 'symptoms', label: 'Symptoms', icon: Stethoscope },
    { id: 'ecg', label: 'ECG Findings', icon: HeartPulse },
    { id: 'labs', label: 'Labs & Echo', icon: FlaskConical },
  ] as const;

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-5 backdrop-blur-md">
      {/* Sample Patient Cohort Bar */}
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
          Load Benchmark Cases:
        </span>
        <div className="flex flex-wrap items-center gap-1.5">
          {samplePatients.map((sp, idx) => {
            const label =
              idx === 0
                ? 'Case 1: Normal'
                : idx === 1
                ? 'Case 2: LAD Stenosis'
                : 'Case 3: Multivessel CAD';
            return (
              <button
                key={sp.patient_id}
                type="button"
                onClick={() => handleLoadSample(sp)}
                className="rounded-lg border border-slate-700 bg-slate-800/80 px-2.5 py-1 text-xs font-medium text-slate-300 hover:border-rose-500/50 hover:bg-slate-700 hover:text-white transition-all"
              >
                {label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex border-b border-slate-800 space-x-1 overflow-x-auto pb-1">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-1.5 px-3 py-2 text-xs font-medium rounded-lg whitespace-nowrap transition-all ${
                isActive
                  ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <Icon className="h-3.5 w-3.5" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Tab Panels */}
      <div className="mt-4 min-h-[220px]">
        {/* DEMOGRAPHICS */}
        {activeTab === 'demo' && (
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
            <div>
              <label className="text-slate-400 font-medium">Age (years)</label>
              <input
                type="number"
                min="18"
                max="100"
                value={patientData.Age}
                onChange={(e) => updateField('Age', parseInt(e.target.value) || 50)}
                className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-white focus:border-rose-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="text-slate-400 font-medium">Biological Sex</label>
              <select
                value={String(patientData.Sex)}
                onChange={(e) => updateField('Sex', e.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-white focus:border-rose-500 focus:outline-none"
              >
                <option value="Male">Male</option>
                <option value="Female">Female</option>
              </select>
            </div>
            <div>
              <label className="text-slate-400 font-medium">Weight (kg)</label>
              <input
                type="number"
                value={patientData.Weight}
                onChange={(e) => updateField('Weight', parseFloat(e.target.value) || 70)}
                className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-white focus:border-rose-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="text-slate-400 font-medium">Height (cm)</label>
              <input
                type="number"
                value={patientData.Length}
                onChange={(e) => updateField('Length', parseFloat(e.target.value) || 170)}
                className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-white focus:border-rose-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="text-slate-400 font-medium">Diabetes Mellitus (DM)</label>
              <select
                value={patientData.DM}
                onChange={(e) => updateField('DM', parseInt(e.target.value))}
                className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-white focus:border-rose-500 focus:outline-none"
              >
                <option value={0}>No (0)</option>
                <option value={1}>Yes (1)</option>
              </select>
            </div>
            <div>
              <label className="text-slate-400 font-medium">Hypertension (HTN)</label>
              <select
                value={patientData.HTN}
                onChange={(e) => updateField('HTN', parseInt(e.target.value))}
                className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-white focus:border-rose-500 focus:outline-none"
              >
                <option value={0}>No (0)</option>
                <option value={1}>Yes (1)</option>
              </select>
            </div>
            <div>
              <label className="text-slate-400 font-medium">Current Smoker</label>
              <select
                value={patientData['Current Smoker']}
                onChange={(e) => updateField('Current Smoker', parseInt(e.target.value))}
                className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-white focus:border-rose-500 focus:outline-none"
              >
                <option value={0}>No (0)</option>
                <option value={1}>Yes (1)</option>
              </select>
            </div>
            <div>
              <label className="text-slate-400 font-medium">Family History (FH)</label>
              <select
                value={patientData.FH}
                onChange={(e) => updateField('FH', parseInt(e.target.value))}
                className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-white focus:border-rose-500 focus:outline-none"
              >
                <option value={0}>No (0)</option>
                <option value={1}>Yes (1)</option>
              </select>
            </div>
            <div>
              <label className="text-slate-400 font-medium">Dyslipidemia (DLP)</label>
              <select
                value={String(patientData.DLP)}
                onChange={(e) => updateField('DLP', e.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-white focus:border-rose-500 focus:outline-none"
              >
                <option value="N">No (N)</option>
                <option value="Y">Yes (Y)</option>
              </select>
            </div>
          </div>
        )}

        {/* VITALS & EXAM */}
        {activeTab === 'vitals' && (
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
            <div>
              <label className="text-slate-400 font-medium">Systolic BP (mmHg)</label>
              <input
                type="number"
                value={patientData.BP}
                onChange={(e) => updateField('BP', parseInt(e.target.value) || 120)}
                className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-white focus:border-rose-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="text-slate-400 font-medium">Pulse Rate (bpm)</label>
              <input
                type="number"
                value={patientData.PR}
                onChange={(e) => updateField('PR', parseInt(e.target.value) || 75)}
                className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-white focus:border-rose-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="text-slate-400 font-medium">NYHA Function Class</label>
              <select
                value={patientData['Function Class']}
                onChange={(e) => updateField('Function Class', parseInt(e.target.value))}
                className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-white focus:border-rose-500 focus:outline-none"
              >
                <option value={0}>Class 0 (Normal)</option>
                <option value={1}>Class I</option>
                <option value={2}>Class II</option>
                <option value={3}>Class III</option>
              </select>
            </div>
            <div>
              <label className="text-slate-400 font-medium">Peripheral Edema</label>
              <select
                value={patientData.Edema}
                onChange={(e) => updateField('Edema', parseInt(e.target.value))}
                className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-white focus:border-rose-500 focus:outline-none"
              >
                <option value={0}>None (0)</option>
                <option value={1}>Present (1)</option>
              </select>
            </div>
            <div>
              <label className="text-slate-400 font-medium">Weak Pulse</label>
              <select
                value={String(patientData['Weak Peripheral Pulse'])}
                onChange={(e) => updateField('Weak Peripheral Pulse', e.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-white focus:border-rose-500 focus:outline-none"
              >
                <option value="N">No (N)</option>
                <option value="Y">Yes (Y)</option>
              </select>
            </div>
            <div>
              <label className="text-slate-400 font-medium">Lung Rales</label>
              <select
                value={String(patientData['Lung rales'])}
                onChange={(e) => updateField('Lung rales', e.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-white focus:border-rose-500 focus:outline-none"
              >
                <option value="N">No (N)</option>
                <option value="Y">Yes (Y)</option>
              </select>
            </div>
          </div>
        )}

        {/* SYMPTOMS */}
        {activeTab === 'symptoms' && (
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
            <div>
              <label className="text-slate-400 font-medium">Typical Chest Pain</label>
              <select
                value={patientData['Typical Chest Pain']}
                onChange={(e) => updateField('Typical Chest Pain', parseInt(e.target.value))}
                className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-white focus:border-rose-500 focus:outline-none"
              >
                <option value={0}>No (0)</option>
                <option value={1}>Yes (1)</option>
              </select>
            </div>
            <div>
              <label className="text-slate-400 font-medium">Dyspnea</label>
              <select
                value={String(patientData.Dyspnea)}
                onChange={(e) => updateField('Dyspnea', e.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-white focus:border-rose-500 focus:outline-none"
              >
                <option value="N">No (N)</option>
                <option value="Y">Yes (Y)</option>
              </select>
            </div>
            <div>
              <label className="text-slate-400 font-medium">Atypical Chest Pain</label>
              <select
                value={String(patientData.Atypical)}
                onChange={(e) => updateField('Atypical', e.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-white focus:border-rose-500 focus:outline-none"
              >
                <option value="N">No (N)</option>
                <option value="Y">Yes (Y)</option>
              </select>
            </div>
            <div>
              <label className="text-slate-400 font-medium">Exertional Chest Pain</label>
              <select
                value={String(patientData['Exertional CP'])}
                onChange={(e) => updateField('Exertional CP', e.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-white focus:border-rose-500 focus:outline-none"
              >
                <option value="N">No (N)</option>
                <option value="Y">Yes (Y)</option>
              </select>
            </div>
            <div>
              <label className="text-slate-400 font-medium">Non-anginal Discomfort</label>
              <select
                value={String(patientData.Nonanginal)}
                onChange={(e) => updateField('Nonanginal', e.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-white focus:border-rose-500 focus:outline-none"
              >
                <option value="N">No (N)</option>
                <option value="Y">Yes (Y)</option>
              </select>
            </div>
          </div>
        )}

        {/* ECG */}
        {activeTab === 'ecg' && (
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
            <div>
              <label className="text-slate-400 font-medium">ST Elevation</label>
              <select
                value={patientData['St Elevation']}
                onChange={(e) => updateField('St Elevation', parseInt(e.target.value))}
                className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-white focus:border-rose-500 focus:outline-none"
              >
                <option value={0}>Absent (0)</option>
                <option value={1}>Present (1)</option>
              </select>
            </div>
            <div>
              <label className="text-slate-400 font-medium">ST Depression</label>
              <select
                value={patientData['St Depression']}
                onChange={(e) => updateField('St Depression', parseInt(e.target.value))}
                className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-white focus:border-rose-500 focus:outline-none"
              >
                <option value={0}>Absent (0)</option>
                <option value={1}>Present (1)</option>
              </select>
            </div>
            <div>
              <label className="text-slate-400 font-medium">T Wave Inversion</label>
              <select
                value={patientData.Tinversion}
                onChange={(e) => updateField('Tinversion', parseInt(e.target.value))}
                className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-white focus:border-rose-500 focus:outline-none"
              >
                <option value={0}>Absent (0)</option>
                <option value={1}>Present (1)</option>
              </select>
            </div>
            <div>
              <label className="text-slate-400 font-medium">Q Wave</label>
              <select
                value={patientData['Q Wave']}
                onChange={(e) => updateField('Q Wave', parseInt(e.target.value))}
                className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-white focus:border-rose-500 focus:outline-none"
              >
                <option value={0}>Absent (0)</option>
                <option value={1}>Present (1)</option>
              </select>
            </div>
            <div>
              <label className="text-slate-400 font-medium">Left Ventricular Hypertrophy (LVH)</label>
              <select
                value={String(patientData.LVH)}
                onChange={(e) => updateField('LVH', e.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-white focus:border-rose-500 focus:outline-none"
              >
                <option value="N">No (N)</option>
                <option value="Y">Yes (Y)</option>
              </select>
            </div>
            <div>
              <label className="text-slate-400 font-medium">Bundle Branch Block (BBB)</label>
              <select
                value={String(patientData.BBB)}
                onChange={(e) => updateField('BBB', e.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-white focus:border-rose-500 focus:outline-none"
              >
                <option value="N">Normal (N)</option>
                <option value="LBBB">LBBB</option>
                <option value="RBBB">RBBB</option>
              </select>
            </div>
          </div>
        )}

        {/* LABS & ECHO */}
        {activeTab === 'labs' && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
            <div>
              <label className="text-slate-400 font-medium">EF-TTE (%)</label>
              <input
                type="number"
                value={patientData['EF-TTE']}
                onChange={(e) => updateField('EF-TTE', parseFloat(e.target.value) || 50)}
                className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-white focus:border-rose-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="text-slate-400 font-medium">Region RWMA</label>
              <input
                type="number"
                value={patientData['Region RWMA']}
                onChange={(e) => updateField('Region RWMA', parseInt(e.target.value) || 0)}
                className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-white focus:border-rose-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="text-slate-400 font-medium">FBS (mg/dL)</label>
              <input
                type="number"
                value={patientData.FBS}
                onChange={(e) => updateField('FBS', parseFloat(e.target.value) || 90)}
                className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-white focus:border-rose-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="text-slate-400 font-medium">Creatinine (mg/dL)</label>
              <input
                type="number"
                step="0.1"
                value={patientData.CR}
                onChange={(e) => updateField('CR', parseFloat(e.target.value) || 0.9)}
                className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-white focus:border-rose-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="text-slate-400 font-medium">LDL (mg/dL)</label>
              <input
                type="number"
                value={patientData.LDL}
                onChange={(e) => updateField('LDL', parseFloat(e.target.value) || 100)}
                className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-white focus:border-rose-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="text-slate-400 font-medium">HDL (mg/dL)</label>
              <input
                type="number"
                value={patientData.HDL}
                onChange={(e) => updateField('HDL', parseFloat(e.target.value) || 45)}
                className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-white focus:border-rose-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="text-slate-400 font-medium">TG (mg/dL)</label>
              <input
                type="number"
                value={patientData.TG}
                onChange={(e) => updateField('TG', parseFloat(e.target.value) || 130)}
                className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-white focus:border-rose-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="text-slate-400 font-medium">BUN (mg/dL)</label>
              <input
                type="number"
                value={patientData.BUN}
                onChange={(e) => updateField('BUN', parseFloat(e.target.value) || 15)}
                className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-white focus:border-rose-500 focus:outline-none"
              />
            </div>
          </div>
        )}
      </div>

      {/* Submission CTA */}
      <div className="mt-5 border-t border-slate-800 pt-4 flex items-center justify-end">
        <button
          type="button"
          disabled={isLoading}
          onClick={() => onSubmit(patientData)}
          className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-rose-600 to-red-600 px-5 py-2.5 text-xs font-semibold text-white shadow-lg shadow-rose-600/30 hover:from-rose-500 hover:to-red-500 focus:outline-none disabled:opacity-50 transition-all"
        >
          {isLoading ? (
            <>
              <RefreshCw className="h-4 w-4 animate-spin" />
              <span>Analyzing Patient Data...</span>
            </>
          ) : (
            <>
              <Play className="h-4 w-4 fill-white" />
              <span>Run AI Risk & 3D Mapping Assessment</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
};

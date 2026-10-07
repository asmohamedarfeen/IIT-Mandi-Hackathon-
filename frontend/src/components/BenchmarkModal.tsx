import React, { useState } from 'react';
import { X, Award, CheckCircle, BarChart3, HelpCircle } from 'lucide-react';
import { BenchmarkData } from '../utils/types';

interface BenchmarkModalProps {
  isOpen: boolean;
  onClose: () => void;
  benchmarkData: BenchmarkData | null;
}

export const BenchmarkModal: React.FC<BenchmarkModalProps> = ({
  isOpen,
  onClose,
  benchmarkData,
}) => {
  const [selectedTarget, setSelectedTarget] = useState<'CAD' | 'LAD' | 'LCX' | 'RCA'>('CAD');

  if (!isOpen) return null;

  const targets = benchmarkData?.targets || {};
  const currentTargetModels = targets[selectedTarget] || {};

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-in fade-in">
      <div className="relative w-full max-w-4xl max-h-[90vh] overflow-hidden rounded-2xl border border-slate-800 bg-slate-900 shadow-2xl flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 p-5">
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-rose-500/10 p-2 text-rose-400 border border-rose-500/20">
              <BarChart3 className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">
                Stratified 10-Fold Cross-Validation Benchmarks
              </h2>
              <p className="text-xs text-slate-400">
                Rigorous evaluation across 303 patient cohort strictly excluding target leakage
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-white transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Target Switcher */}
        <div className="flex border-b border-slate-800 bg-slate-950/50 px-5 pt-3 gap-2">
          {(['CAD', 'LAD', 'LCX', 'RCA'] as const).map((tgt) => (
            <button
              key={tgt}
              onClick={() => setSelectedTarget(tgt)}
              className={`px-4 py-2 text-xs font-semibold rounded-t-lg transition-all ${
                selectedTarget === tgt
                  ? 'border-b-2 border-rose-500 text-rose-400 bg-slate-900'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {tgt === 'CAD' ? 'Overall CAD (Cath)' : `${tgt} Stenosis`}
            </button>
          ))}
        </div>

        {/* Table Content */}
        <div className="flex-1 overflow-auto p-5">
          <div className="overflow-x-auto rounded-xl border border-slate-800">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950 text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4 font-semibold">Model Candidate</th>
                  <th className="py-3 px-4 font-semibold text-rose-400">ROC-AUC</th>
                  <th className="py-3 px-4 font-semibold text-rose-400">F1 Score</th>
                  <th className="py-3 px-4 font-semibold">Accuracy</th>
                  <th className="py-3 px-4 font-semibold">Precision</th>
                  <th className="py-3 px-4 font-semibold">Recall</th>
                  <th className="py-3 px-4 font-semibold">Specificity</th>
                  <th className="py-3 px-4 font-semibold">MCC</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {Object.entries(currentTargetModels).map(([modelName, metrics]) => {
                  const isEnsemble = modelName.includes('Ensemble');
                  return (
                    <tr
                      key={modelName}
                      className={
                        isEnsemble
                          ? 'bg-rose-950/20 font-bold text-white'
                          : 'text-slate-300 hover:bg-slate-800/40'
                      }
                    >
                      <td className="py-3 px-4 font-sans font-medium flex items-center gap-1.5">
                        {isEnsemble && <Award className="h-3.5 w-3.5 text-rose-400 shrink-0" />}
                        <span>{modelName}</span>
                      </td>
                      <td className="py-3 px-4 text-rose-400 font-bold">
                        {(metrics.roc_auc * 100).toFixed(1)}%
                      </td>
                      <td className="py-3 px-4 text-emerald-400 font-semibold">
                        {(metrics.f1 * 100).toFixed(1)}%
                      </td>
                      <td className="py-3 px-4">{(metrics.accuracy * 100).toFixed(1)}%</td>
                      <td className="py-3 px-4">{(metrics.precision * 100).toFixed(1)}%</td>
                      <td className="py-3 px-4">{(metrics.recall * 100).toFixed(1)}%</td>
                      <td className="py-3 px-4">{(metrics.specificity * 100).toFixed(1)}%</td>
                      <td className="py-3 px-4">{metrics.mcc.toFixed(3)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Validation Protocol Details */}
          <div className="mt-5 rounded-xl border border-slate-800 bg-slate-950/40 p-4 text-xs text-slate-300 space-y-2">
            <h4 className="font-semibold text-white flex items-center gap-1.5">
              <CheckCircle className="h-4 w-4 text-emerald-400" />
              Methodological Rigor & Target Leakage Prevention
            </h4>
            <ul className="list-disc list-inside space-y-1 text-slate-400 text-[11px]">
              <li>
                <strong className="text-slate-200">Zero Target Leakage:</strong> All target variables (<code>Cath</code>, <code>CAD</code>, <code>LAD</code>, <code>LCX</code>, <code>RCA</code>) are strictly removed from candidate feature vectors before model training.
              </li>
              <li>
                <strong className="text-slate-200">Stratified 10-Fold CV:</strong> Folds preserve class prevalence to ensure balanced sensitivity and specificity across small medical sample sizes.
              </li>
              <li>
                <strong className="text-slate-200">Calibrated Probabilities:</strong> Platt scaling / Sigmoid probability calibration ensures risk scores represent authentic diagnostic likelihoods (0-100%).
              </li>
            </ul>
          </div>
        </div>

        {/* Footer */}
        <div className="border-t border-slate-800 p-4 bg-slate-950/60 flex justify-end">
          <button
            onClick={onClose}
            className="rounded-lg bg-slate-800 px-4 py-2 text-xs font-semibold text-white hover:bg-slate-700 transition-colors"
          >
            Close Benchmarks
          </button>
        </div>
      </div>
    </div>
  );
};

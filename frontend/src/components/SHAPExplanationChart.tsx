import React, { useState } from 'react';
import { SHAPFeatureImpact } from '../utils/types';
import { HelpCircle, TrendingUp, TrendingDown, Sparkles } from 'lucide-react';

interface SHAPExplanationChartProps {
  explanations?: {
    CAD: SHAPFeatureImpact[];
    LAD: SHAPFeatureImpact[];
    LCX: SHAPFeatureImpact[];
    RCA: SHAPFeatureImpact[];
  };
}

export const SHAPExplanationChart: React.FC<SHAPExplanationChartProps> = ({ explanations }) => {
  const [activeTarget, setActiveTarget] = useState<'CAD' | 'LAD' | 'LCX' | 'RCA'>('CAD');

  if (!explanations) {
    return (
      <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-5 backdrop-blur-md animate-pulse">
        <div className="h-5 w-48 bg-slate-800 rounded mb-4" />
        <div className="space-y-3">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-6 w-full bg-slate-800/60 rounded" />
          ))}
        </div>
      </div>
    );
  }

  const items = explanations[activeTarget] || [];
  const maxAbs = Math.max(...items.map((it) => Math.abs(it.contribution)), 0.01);

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-5 backdrop-blur-md">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div>
          <h3 className="text-base font-semibold text-white flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-amber-400" />
            Explainable AI: Patient SHAP Contributions
          </h3>
          <p className="text-xs text-slate-400">
            TreeSHAP feature impact on log-odds risk prediction for this patient
          </p>
        </div>

        {/* Target Selector Tabs */}
        <div className="flex items-center gap-1 rounded-lg border border-slate-800 bg-slate-950/80 p-1">
          {(['CAD', 'LAD', 'LCX', 'RCA'] as const).map((tgt) => (
            <button
              key={tgt}
              onClick={() => setActiveTarget(tgt)}
              className={`px-3 py-1 rounded text-xs font-semibold transition-all ${
                activeTarget === tgt
                  ? 'bg-rose-600 text-white shadow'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              {tgt}
            </button>
          ))}
        </div>
      </div>

      {/* Feature Impact List */}
      <div className="mt-4 space-y-3">
        {items.length === 0 ? (
          <p className="text-xs text-slate-400 py-6 text-center">
            No significant feature contributions found for this territory.
          </p>
        ) : (
          items.map((item, idx) => {
            const isRiskIncreaser = item.contribution > 0;
            const barWidth = Math.min(100, Math.round((Math.abs(item.contribution) / maxAbs) * 100));

            return (
              <div
                key={idx}
                className="group rounded-lg border border-slate-800/60 bg-slate-950/40 p-2.5 transition-colors hover:border-slate-700 hover:bg-slate-900/40"
              >
                <div className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2 min-w-0">
                    {isRiskIncreaser ? (
                      <TrendingUp className="h-3.5 w-3.5 text-rose-400 shrink-0" />
                    ) : (
                      <TrendingDown className="h-3.5 w-3.5 text-emerald-400 shrink-0" />
                    )}
                    <span className="font-medium text-slate-200 truncate">
                      {item.display_name}
                    </span>
                    <span className="rounded bg-slate-800 px-1.5 py-0.2 text-[10px] text-slate-400 font-mono">
                      val: {String(item.patient_value)}
                    </span>
                  </div>

                  <span
                    className={`font-mono text-xs font-semibold shrink-0 ml-2 ${
                      isRiskIncreaser ? 'text-rose-400' : 'text-emerald-400'
                    }`}
                  >
                    {item.contribution > 0 ? '+' : ''}
                    {item.contribution.toFixed(4)}
                  </span>
                </div>

                {/* Relative impact bar */}
                <div className="mt-2 flex h-1.5 w-full overflow-hidden rounded-full bg-slate-800">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${
                      isRiskIncreaser ? 'bg-rose-500' : 'bg-emerald-500'
                    }`}
                    style={{ width: `${barWidth}%` }}
                  />
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Legend / Guide */}
      <div className="mt-4 flex items-center justify-between text-[11px] text-slate-400 border-t border-slate-800/80 pt-3">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-rose-500" />
            <span>Positive SHAP: Increases Stenosis Risk</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-emerald-500" />
            <span>Negative SHAP: Protective / Decreases Risk</span>
          </div>
        </div>
        <span className="text-slate-500 hidden sm:inline">Additive TreeSHAP log-odds</span>
      </div>
    </div>
  );
};

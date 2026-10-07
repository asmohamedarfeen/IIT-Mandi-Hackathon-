import React from 'react';
import { VesselRiskInfo } from '../utils/types';
import { ShieldAlert, ShieldCheck, AlertTriangle } from 'lucide-react';

interface RiskSummaryCardsProps {
  overallCad?: VesselRiskInfo;
  vessels?: {
    LAD: VesselRiskInfo;
    LCX: VesselRiskInfo;
    RCA: VesselRiskInfo;
  };
}

export const RiskSummaryCards: React.FC<RiskSummaryCardsProps> = ({ overallCad, vessels }) => {
  if (!overallCad || !vessels) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {['Overall CAD', 'LAD Stenosis', 'LCX Stenosis', 'RCA Stenosis'].map((name, i) => (
          <div
            key={i}
            className="animate-pulse rounded-xl border border-slate-800 bg-slate-900/40 p-4"
          >
            <div className="h-4 w-24 bg-slate-800 rounded mb-2" />
            <div className="h-7 w-16 bg-slate-800 rounded mb-3" />
            <div className="h-2 w-full bg-slate-800 rounded" />
          </div>
        ))}
      </div>
    );
  }

  const items = [
    { key: 'CAD', label: 'Overall CAD Status', data: overallCad, isPrimary: true },
    { key: 'LAD', label: 'LAD Artery', data: vessels.LAD, isPrimary: false },
    { key: 'LCX', label: 'LCX Artery', data: vessels.LCX, isPrimary: false },
    { key: 'RCA', label: 'RCA Artery', data: vessels.RCA, isPrimary: false },
  ];

  const getBadgeIcon = (level: string) => {
    if (level.includes('Low')) return <ShieldCheck className="h-3.5 w-3.5 text-emerald-400" />;
    if (level.includes('Intermediate')) return <AlertTriangle className="h-3.5 w-3.5 text-amber-400" />;
    return <ShieldAlert className="h-3.5 w-3.5 text-rose-400" />;
  };

  const ANATOMY_BADGES: Record<string, { label: string; color: string }> = {
    LAD: { label: 'Anterior Territory', color: '#06B6D4' },
    LCX: { label: 'Lateral/Posterior', color: '#A855F7' },
    RCA: { label: 'Right Sulcus', color: '#F59E0B' },
  };

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
      {items.map(({ key, label, data, isPrimary }) => {
        const pct = data.probability_percent;
        const color = data.color_hex;
        const anat = ANATOMY_BADGES[key];

        return (
          <div
            key={key}
            className={`relative rounded-xl border p-4 transition-all ${
              isPrimary
                ? 'border-rose-500/40 bg-gradient-to-br from-rose-950/20 via-slate-900/60 to-slate-900/80 shadow-lg shadow-rose-950/20'
                : 'border-slate-800 bg-slate-900/50 hover:border-slate-700'
            }`}
          >
            {/* Header */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                {anat && (
                  <span
                    className="h-2.5 w-2.5 rounded-full shrink-0"
                    style={{ backgroundColor: anat.color }}
                    title={`3D Region: ${anat.label}`}
                  />
                )}
                <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  {label}
                </span>
              </div>
              <div
                className="flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium border"
                style={{
                  backgroundColor: `${color}15`,
                  borderColor: `${color}40`,
                  color: color,
                }}
              >
                {getBadgeIcon(data.risk_level)}
                <span>{data.risk_level}</span>
              </div>
            </div>

            {/* Probability Percentage */}
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-3xl font-extrabold text-white tracking-tight">
                {pct}%
              </span>
              <span className="text-xs text-slate-400">calibrated risk</span>
            </div>

            {/* Progress Bar */}
            <div className="mt-3 h-2 w-full rounded-full bg-slate-800 overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-700 ease-out"
                style={{
                  width: `${pct}%`,
                  backgroundColor: color,
                  boxShadow: `0 0 10px ${color}80`,
                }}
              />
            </div>

            {/* Description */}
            <p className="mt-2.5 text-[11px] text-slate-400 line-clamp-1" title={data.anatomical_description}>
              {data.anatomical_description}
            </p>
          </div>
        );
      })}
    </div>
  );
};

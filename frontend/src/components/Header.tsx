import React from 'react';
import { Activity, ShieldCheck, BarChart3, Heart, Info } from 'lucide-react';

interface HeaderProps {
  onOpenBenchmarks: () => void;
  onOpenAnatomyInfo: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onOpenBenchmarks, onOpenAnatomyInfo }) => {
  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-800 bg-slate-950/80 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-rose-600 to-red-500 shadow-lg shadow-rose-500/20">
            <Heart className="h-5 w-5 text-white animate-heart-pulse fill-white/20" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-lg font-bold tracking-tight text-white">
                CardioVision <span className="text-rose-500">AI</span>
              </span>
              <span className="rounded-full bg-rose-500/10 px-2 py-0.5 text-xs font-semibold text-rose-400 border border-rose-500/20">
                Multi-Task 3D
              </span>
            </div>
            <p className="text-xs text-slate-400 hidden sm:block">
              Anatomical Visualization & Coronary Stenosis Risk System
            </p>
          </div>
        </div>

        {/* Status & Actions */}
        <div className="flex items-center gap-3">
          <div className="hidden md:flex items-center gap-2 rounded-lg border border-slate-800 bg-slate-900/60 px-3 py-1.5 text-xs text-slate-300">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <span>Calibrated Ensemble (CatBoost+XGB+LGBM+RF)</span>
          </div>

          <button
            onClick={onOpenBenchmarks}
            className="flex items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-800/80 px-3 py-1.5 text-xs font-medium text-slate-200 transition-colors hover:bg-slate-700 hover:text-white"
          >
            <BarChart3 className="h-3.5 w-3.5 text-rose-400" />
            <span>10-Fold CV Benchmarks</span>
          </button>

          <button
            onClick={onOpenAnatomyInfo}
            className="flex items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-800/80 px-3 py-1.5 text-xs font-medium text-slate-200 transition-colors hover:bg-slate-700 hover:text-white"
          >
            <Info className="h-3.5 w-3.5 text-cyan-400" />
            <span>Vessel Guide</span>
          </button>
        </div>
      </div>
    </header>
  );
};

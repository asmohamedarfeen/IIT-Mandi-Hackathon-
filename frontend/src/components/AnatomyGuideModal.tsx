import React from 'react';
import { X, Heart, Shield, Activity, Info } from 'lucide-react';

interface AnatomyGuideModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const AnatomyGuideModal: React.FC<AnatomyGuideModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-in fade-in">
      <div className="relative w-full max-w-2xl max-h-[90vh] overflow-hidden rounded-2xl border border-slate-800 bg-slate-900 shadow-2xl flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 p-5">
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-sky-500/10 p-2 text-sky-400 border border-sky-500/20">
              <Heart className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">Coronary Anatomy & Clinical Guide</h2>
              <p className="text-xs text-slate-400">
                Major arterial territories and 3D visualization risk conventions
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

        {/* Content */}
        <div className="flex-1 overflow-auto p-5 space-y-4 text-xs text-slate-300">
          <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-4 space-y-3">
            <h3 className="font-semibold text-white flex items-center gap-2">
              <Activity className="h-4 w-4 text-rose-500" />
              Primary Coronary Arteries Evaluated
            </h3>

            <div className="space-y-2.5">
              <div className="border-l-2 border-emerald-500 pl-3">
                <span className="font-bold text-white text-sm">LAD (Left Anterior Descending)</span>
                <p className="text-slate-400 mt-0.5">
                  Supplies approximately 45-55% of the left ventricle, including the anterior free wall, anterior 2/3 of the interventricular septum, and apex. Critical prognostic vessel.
                </p>
              </div>

              <div className="border-l-2 border-amber-500 pl-3">
                <span className="font-bold text-white text-sm">LCX (Left Circumflex Artery)</span>
                <p className="text-slate-400 mt-0.5">
                  Branches from the left main trunk to course along the coronary sulcus, perfusing the lateral and posterior left ventricular myocardium and left atrium.
                </p>
              </div>

              <div className="border-l-2 border-sky-500 pl-3">
                <span className="font-bold text-white text-sm">RCA (Right Coronary Artery)</span>
                <p className="text-slate-400 mt-0.5">
                  Perfuses the right ventricle, inferior wall of the left ventricle, posterior 1/3 of the septum, and critical conduction pacemakers (SA and AV nodes).
                </p>
              </div>
            </div>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-4 space-y-2">
            <h3 className="font-semibold text-white flex items-center gap-2">
              <Shield className="h-4 w-4 text-amber-400" />
              Risk Color Standards (3D Model)
            </h3>
            <div className="grid grid-cols-3 gap-2 mt-2">
              <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 p-3 text-center">
                <span className="h-3 w-3 rounded-full bg-emerald-500 inline-block mb-1" />
                <div className="font-bold text-emerald-400">&lt; 35%</div>
                <div className="text-[10px] text-slate-400">Normal / Low Stenosis Risk</div>
              </div>
              <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-3 text-center">
                <span className="h-3 w-3 rounded-full bg-amber-500 inline-block mb-1" />
                <div className="font-bold text-amber-400">35% - 65%</div>
                <div className="text-[10px] text-slate-400">Borderline / Intermediate Risk</div>
              </div>
              <div className="rounded-lg border border-rose-500/30 bg-rose-500/10 p-3 text-center">
                <span className="h-3 w-3 rounded-full bg-rose-500 inline-block mb-1" />
                <div className="font-bold text-rose-400">&ge; 65%</div>
                <div className="text-[10px] text-slate-400">High Stenosis Likelihood</div>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="border-t border-slate-800 p-4 bg-slate-950/60 flex justify-end">
          <button
            onClick={onClose}
            className="rounded-lg bg-slate-800 px-4 py-2 text-xs font-semibold text-white hover:bg-slate-700 transition-colors"
          >
            Got It
          </button>
        </div>
      </div>
    </div>
  );
};

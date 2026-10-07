import React, { useState } from 'react';
import { Header } from '../components/Header';
import { BenchmarkModal } from '../components/BenchmarkModal';
import { AnatomyGuideModal } from '../components/AnatomyGuideModal';
import { BenchmarkData } from '../utils/types';
import { AlertCircle } from 'lucide-react';

interface MainLayoutProps {
  children: React.ReactNode;
  benchmarkData: BenchmarkData | null;
}

export const MainLayout: React.FC<MainLayoutProps> = ({ children, benchmarkData }) => {
  const [benchmarksOpen, setBenchmarksOpen] = useState(false);
  const [anatomyGuideOpen, setAnatomyGuideOpen] = useState(false);

  return (
    <div className="min-h-screen flex flex-col bg-[#080C15] text-slate-100">
      <Header
        onOpenBenchmarks={() => setBenchmarksOpen(true)}
        onOpenAnatomyInfo={() => setAnatomyGuideOpen(true)}
      />

      <main className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {children}
      </main>

      {/* Clinical Disclaimer Footer */}
      <footer className="w-full border-t border-slate-900 bg-slate-950 py-4 px-4 text-center text-xs text-slate-500">
        <div className="max-w-4xl mx-auto flex items-center justify-center gap-2">
          <AlertCircle className="h-4 w-4 text-amber-500 shrink-0" />
          <p>
            <strong>Clinical Safety Disclaimer:</strong> CardioVision AI is an experimental decision-support and 3D visualization research system. Predictions do not replace invasive coronary angiography or clinical diagnostic guidelines.
          </p>
        </div>
      </footer>

      {/* Modals */}
      <BenchmarkModal
        isOpen={benchmarksOpen}
        onClose={() => setBenchmarksOpen(false)}
        benchmarkData={benchmarkData}
      />

      <AnatomyGuideModal
        isOpen={anatomyGuideOpen}
        onClose={() => setAnatomyGuideOpen(false)}
      />
    </div>
  );
};

import { ReactNode, useState } from "react";
import { Header } from "../components/Header";
import { BenchmarkModal } from "../components/BenchmarkModal";
import { AnatomyGuideModal } from "../components/AnatomyGuideModal";
import { BenchmarkData } from "../utils/types";
export function MainLayout({
  children,
  benchmarkData,
  onRetry,
  loading,
}: {
  children: ReactNode;
  benchmarkData: BenchmarkData | null;
  onRetry: () => void;
  loading: boolean;
}) {
  const [benchmarks, setBenchmarks] = useState(false),
    [anatomy, setAnatomy] = useState(false);
  return (
    <div className="cardiovision" id="top">
      <a href="#assessment" className="skip-link">
        Skip to assessment
      </a>
      <Header
        onOpenBenchmarks={() => setBenchmarks(true)}
        onOpenAnatomyInfo={() => setAnatomy(true)}
      />
      <main>{children}</main>
      <footer className="site-footer">
        <a href="#top" className="wordmark">
          CardioVision
        </a>
        <p>
          Research MVP · Experimental estimates, not a diagnosis.
        </p>
      </footer>
      <BenchmarkModal
        isOpen={benchmarks}
        onClose={() => setBenchmarks(false)}
        benchmarkData={benchmarkData}
        onRetry={onRetry}
        loading={loading}
      />
      <AnatomyGuideModal isOpen={anatomy} onClose={() => setAnatomy(false)} />
    </div>
  );
}

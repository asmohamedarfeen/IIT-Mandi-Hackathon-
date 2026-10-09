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
  workspace = "assessment",
  onWorkspaceChange,
}: {
  children: ReactNode;
  benchmarkData: BenchmarkData | null;
  onRetry: () => void;
  loading: boolean;
  workspace?: "assessment" | "quality";
  onWorkspaceChange?: (workspace:"assessment"|"quality")=>void;
}) {
  const [benchmarks, setBenchmarks] = useState(false),
    [anatomy, setAnatomy] = useState(false);
  return (
    <div className="cardiovision" id="top">
      <a href={workspace==="assessment"?"#assessment":"#model-quality-lab"} className="skip-link">
        Skip to {workspace==="assessment"?"assessment":"Model Quality Lab"}
      </a>
      <Header
        onOpenBenchmarks={() => setBenchmarks(true)}
        onOpenAnatomyInfo={() => setAnatomy(true)}
        workspace={workspace}
        onWorkspaceChange={onWorkspaceChange}
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

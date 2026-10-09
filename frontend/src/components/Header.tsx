import { Activity, ArrowUpRight } from "lucide-react";
export function Header({
  onOpenBenchmarks,
  onOpenAnatomyInfo,
  workspace = "assessment",
  onWorkspaceChange,
}: {
  onOpenBenchmarks: () => void;
  onOpenAnatomyInfo: () => void;
  workspace?: "assessment"|"quality";
  onWorkspaceChange?: (workspace:"assessment"|"quality")=>void;
}) {
  return (
    <header className="site-header">
      <a className="wordmark" href="#top" aria-label="CardioVision home">
        <Activity size={28} strokeWidth={1.5} />
        <span>CardioVision</span>
      </a>
      <nav aria-label="Main navigation">
        {onWorkspaceChange && <div className="workspace-switch" aria-label="Workspaces"><button type="button" aria-pressed={workspace==="assessment"} onClick={()=>onWorkspaceChange("assessment")}>Assessment</button><button type="button" aria-pressed={workspace==="quality"} onClick={()=>onWorkspaceChange("quality")}>Model Quality Lab</button></div>}
        <button onClick={onOpenAnatomyInfo}>Anatomy guide</button>
        <button onClick={onOpenBenchmarks}>Model evidence</button>
        <a className="nav-action" href="#assessment" onClick={()=>onWorkspaceChange?.("assessment")}>
          Open workspace <ArrowUpRight size={16} />
        </a>
      </nav>
    </header>
  );
}

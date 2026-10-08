import { Activity, ArrowUpRight } from "lucide-react";
export function Header({
  onOpenBenchmarks,
  onOpenAnatomyInfo,
}: {
  onOpenBenchmarks: () => void;
  onOpenAnatomyInfo: () => void;
}) {
  return (
    <header className="site-header">
      <a className="wordmark" href="#top" aria-label="CardioVision home">
        <Activity size={28} strokeWidth={1.5} />
        <span>CardioVision</span>
      </a>
      <nav aria-label="Main navigation">
        <button onClick={onOpenAnatomyInfo}>Anatomy guide</button>
        <button onClick={onOpenBenchmarks}>Model evidence</button>
        <a className="nav-action" href="#assessment">
          Open workspace <ArrowUpRight size={16} />
        </a>
      </nav>
    </header>
  );
}

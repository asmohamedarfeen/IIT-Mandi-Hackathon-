import { useState, useEffect, useCallback, lazy, Suspense } from "react";
import { MainLayout } from "./layouts/MainLayout";
import { DashboardPage } from "./pages/DashboardPage";
import { apiService } from "./services/api";
import { BenchmarkData } from "./utils/types";
import "./model-quality/styles.css";
const ModelQualityLab = lazy(() => import("./model-quality/ModelQualityLab").then(module=>({default:module.ModelQualityLab})));
export default function App() {
  const [workspace,setWorkspace] = useState<"assessment"|"quality">("assessment");
  const [qualityVisited,setQualityVisited] = useState(false);
  const changeWorkspace = (next: "assessment"|"quality") => { setWorkspace(next); if(next==="quality")setQualityVisited(true); };
  const [data, setData] = useState<BenchmarkData | null>(null),
    [loading, setLoading] = useState(false);
  const load = useCallback(() => {
    setLoading(true);
    apiService
      .getBenchmarks()
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, []);
  useEffect(load, [load]);
  return (
    <MainLayout benchmarkData={data} onRetry={load} loading={loading} workspace={workspace} onWorkspaceChange={changeWorkspace}>
      <div className="workspace-panel" hidden={workspace!=="assessment"}><DashboardPage active={workspace==="assessment"}/></div>
      {qualityVisited && <div className="workspace-panel" hidden={workspace!=="quality"}><Suspense fallback={<p role="status" style={{padding:"32px 5%"}}>Loading Model Quality Lab…</p>}><ModelQualityLab /></Suspense></div>}
    </MainLayout>
  );
}

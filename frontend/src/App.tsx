import { useState, useEffect, useCallback } from "react";
import { MainLayout } from "./layouts/MainLayout";
import { DashboardPage } from "./pages/DashboardPage";
import { apiService } from "./services/api";
import { BenchmarkData } from "./utils/types";
export default function App() {
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
    <MainLayout benchmarkData={data} onRetry={load} loading={loading}>
      <DashboardPage />
    </MainLayout>
  );
}

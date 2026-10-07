import React, { useState, useEffect } from 'react';
import { MainLayout } from './layouts/MainLayout';
import { DashboardPage } from './pages/DashboardPage';
import { apiService } from './services/api';
import { BenchmarkData } from './utils/types';

export const App: React.FC = () => {
  const [benchmarkData, setBenchmarkData] = useState<BenchmarkData | null>(null);

  useEffect(() => {
    apiService.getBenchmarks()
      .then(setBenchmarkData)
      .catch((err) => console.warn('Could not fetch benchmarks:', err));
  }, []);

  return (
    <MainLayout benchmarkData={benchmarkData}>
      <DashboardPage />
    </MainLayout>
  );
};

export default App;

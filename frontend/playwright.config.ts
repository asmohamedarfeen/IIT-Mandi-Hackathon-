import { defineConfig, devices } from '@playwright/test';

// Each run uses a disposable database, never the local research history.
const python = process.env.E2E_PYTHON || '../.venv/bin/python';
const database = `sqlite:////tmp/cardiovision-browser-${process.pid}.db`;
export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  workers: 1,
  timeout: 120_000,
  expect: { timeout: 20_000 },
  use: { baseURL: 'http://127.0.0.1:15173', trace: 'retain-on-failure' },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: [
    {
      command: `cd .. && ${python.startsWith('../') ? python.slice(3) : python} -m alembic upgrade head && ${python.startsWith('../') ? python.slice(3) : python} -m uvicorn backend.main:app --host 127.0.0.1 --port 18080 --no-access-log`,
      url: 'http://127.0.0.1:18080/health',
      timeout: 120_000,
      reuseExistingServer: false,
      env: { DATABASE_URL: database, AUTO_CREATE_TABLES: 'false', API_TOKEN: '', ALLOWED_ORIGINS: '["http://127.0.0.1:15173"]', MPLCONFIGDIR: '/tmp/cardiovision-e2e-matplotlib' },
    },
    {
      command: 'npm run dev -- --host 127.0.0.1 --port 15173 --strictPort',
      url: 'http://127.0.0.1:15173',
      timeout: 60_000,
      reuseExistingServer: false,
      env: { VITE_API_BASE_URL: 'http://127.0.0.1:18080/api/v1' },
    },
  ],
});

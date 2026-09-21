import { defineConfig, devices } from '@playwright/test';
import path from 'path';

/**
 * Playwright end-to-end regression suite for the TraderX React frontend.
 *
 * The suite drives the real stack: the FastAPI monolith on :8000 (which seeds
 * the deterministic golden data from traderx-monolith/app/seed.py into an
 * empty SQLite DB on startup) and the CRA dev server on :18094.
 *
 * Both servers are declared under `webServer`, so `npm run e2e` boots whatever
 * is not already running. Set E2E_BASE_URL / E2E_BACKEND_URL to point at
 * servers started elsewhere.
 */
const FRONTEND_PORT = process.env.WEB_SERVICE_REACT_PORT || '18094';
const BASE_URL = process.env.E2E_BASE_URL || `http://localhost:${FRONTEND_PORT}`;
const BACKEND_URL = process.env.E2E_BACKEND_URL || 'http://localhost:8000';

const MONOLITH_DIR = path.resolve(__dirname, '../../traderx-monolith');

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 2 : undefined,
  reporter: process.env.CI
    ? [['list'], ['html', { open: 'never' }]]
    : [['list'], ['html', { open: 'on-failure' }]],
  timeout: 30_000,
  expect: { timeout: 10_000 },
  use: {
    baseURL: BASE_URL,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: [
    {
      command: 'python run.py',
      cwd: MONOLITH_DIR,
      url: `${BACKEND_URL}/health`,
      reuseExistingServer: true,
      timeout: 60_000,
      stdout: 'ignore',
      stderr: 'pipe',
    },
    {
      command: `npm start`,
      cwd: __dirname,
      url: BASE_URL,
      reuseExistingServer: true,
      timeout: 180_000,
      env: { BROWSER: 'none', WEB_SERVICE_REACT_PORT: FRONTEND_PORT },
      stdout: 'ignore',
      stderr: 'pipe',
    },
  ],
});

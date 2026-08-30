import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  use: {
    baseURL: "http://localhost:3000",
    trace: "on-first-retry",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    {
      command: "cd ../api && .venv\\Scripts\\python -m uvicorn app.main:app --port 8000",
      url: "http://localhost:8000/v1/health",
      reuseExistingServer: true,
      timeout: 120_000,
    },
    {
      command: "npm run dev",
      url: "http://localhost:3000/login",
      reuseExistingServer: true,
      timeout: 120_000,
      env: {
        ...process.env,
        SESSION_SECRET: "dev-session-secret-min-32-chars-long!!",
        API_INTERNAL_URL: "http://localhost:8000",
      },
    },
  ],
});

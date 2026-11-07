import { defineConfig, devices } from "@playwright/test";
export default defineConfig({
  testDir: "./tests",
  testMatch: "integration.spec.ts",
  timeout: 30000,
  workers: 1,
  use: {
    baseURL: process.env.DAILY_COMMIT_TEST_URL || "http://127.0.0.1:8000",
    ...devices["Pixel 7"],
    channel: process.env.PLAYWRIGHT_CHANNEL || undefined,
    trace: "retain-on-failure",
  },
});

import { defineConfig, devices } from "@playwright/test";

process.env.NO_PROXY = "127.0.0.1,localhost";
process.env.no_proxy = "127.0.0.1,localhost";
delete process.env.HTTP_PROXY;
delete process.env.HTTPS_PROXY;
delete process.env.ALL_PROXY;
delete process.env.http_proxy;
delete process.env.https_proxy;
delete process.env.all_proxy;

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  reporter: "list",
  use: {
    baseURL: "http://127.0.0.1:4173",
    trace: "on-first-retry",
  },
  webServer: {
    command: "npm run build && npm run preview -- --port 4173",
    url: "http://127.0.0.1:4173",
    reuseExistingServer: true,
    timeout: 120_000,
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});

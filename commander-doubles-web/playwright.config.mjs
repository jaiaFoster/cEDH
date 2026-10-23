import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./tests/browser",
  timeout: 240000,
  expect: { timeout: 15000 },
  workers: 1,
  retries: 0,
  reporter: [
    ["list"],
    ["json", { outputFile: "reports/browser.json" }],
    ["junit", { outputFile: "reports/browser.xml" }],
  ],
  use: {
    baseURL: process.env.BASE_URL || "http://127.0.0.1:3000",
    channel: process.env.CI ? undefined : "chrome",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    headless: true,
  },
});

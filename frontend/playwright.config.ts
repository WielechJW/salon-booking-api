import { defineConfig, devices } from '@playwright/test'
import { fileURLToPath } from 'node:url'

const python = process.env.PYTHON || fileURLToPath(new URL('../.venv/bin/python', import.meta.url))
const shellQuote = (value: string) => `'${value.replace(/'/g, "'\\''")}'`

export default defineConfig({
  testDir: './e2e',
  timeout: 30_000,
  fullyParallel: false,
  workers: 1,
  reporter: 'list',
  use: {
    baseURL: 'http://127.0.0.1:5180',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    ...devices['Desktop Chrome'],
    channel: 'chrome',
    launchOptions: { args: ['--no-sandbox'] },
  },
  webServer: [
    {
      command: `${shellQuote(python)} e2e/serve_api.py`,
      url: 'http://127.0.0.1:18100/salon',
      reuseExistingServer: false,
      timeout: 60_000,
    },
    {
      command: 'npm run dev -- --port 5180',
      url: 'http://127.0.0.1:5180',
      env: { API_PROXY_TARGET: 'http://127.0.0.1:18100' },
      reuseExistingServer: false,
      timeout: 60_000,
    },
  ],
})

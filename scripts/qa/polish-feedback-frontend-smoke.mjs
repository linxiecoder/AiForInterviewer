import { spawnSync } from "node:child_process";
import { mkdirSync, mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { parseArgs, resolvePython, validateScenario } from "./polish-feedback-smoke/cli.mjs";
import { startForcedTruncationProvider } from "./polish-feedback-smoke/forced-provider.mjs";
import {
  requestJson,
  runForcedFeedbackTruncationScenario,
  waitForJson,
  waitForText,
} from "./polish-feedback-smoke/http-evidence.mjs";
import { createSmokeRuntime, delay, resolvePort } from "./polish-feedback-smoke/runtime.mjs";
import {
  appendToTask6TextArtifacts,
} from "./polish-feedback-smoke/sensitive-scan.mjs";
import { runSensitiveScanSelfTest } from "./polish-feedback-smoke/sensitive-scan-self-test.mjs";

const ROOT_DIR = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const args = parseArgs(process.argv.slice(2));
const scenario = args.get("scenario") ?? "seeded-feedback-states";
const evidenceDir = path.resolve(
  ROOT_DIR,
  args.get("evidence-dir") ?? ".omo/evidence/polish-feedback-generation-observability-fix",
);
const API_PORT = await resolvePort("AIFI_FEEDBACK_SMOKE_API_PORT", 18181);
const WEB_PORT = await resolvePort("AIFI_FEEDBACK_SMOKE_WEB_PORT", 15273);
const PROVIDER_PORT = await resolvePort("AIFI_FEEDBACK_SMOKE_PROVIDER_PORT", 19081);
const DEV_PASSWORD = process.env.AIFI_FEEDBACK_SMOKE_DEV_PASSWORD ?? "polish-feedback-smoke-password";
const DEV_EMAIL = "developer@example.com";
const API_BASE = `http://127.0.0.1:${API_PORT}`;
const WEB_BASE = `http://127.0.0.1:${WEB_PORT}`;
const PROVIDER_BASE = `http://127.0.0.1:${PROVIDER_PORT}/v1`;
const PYTHON = resolvePython(ROOT_DIR);
const KEEP_ALIVE_MS = Number.parseInt(process.env.AIFI_FEEDBACK_SMOKE_KEEP_ALIVE_MS ?? "0", 10);
const tempDir = mkdtempSync(path.join(tmpdir(), "aifi-auth-smoke-"));
const databasePath = path.join(tempDir, "smoke.sqlite3");
const databaseUrl = `sqlite+pysqlite:///${databasePath}`;
const apiLogPath = path.join(ROOT_DIR, "tmp/logs/api-dev.log");
const runtime = createSmokeRuntime({
  rootDir: ROOT_DIR,
  tempDir,
  evidenceDir,
  scenario,
  ports: {
    api: API_PORT,
    web: WEB_PORT,
    provider: PROVIDER_PORT,
  },
  appendToTextArtifacts: (section) => appendToTask6TextArtifacts(evidenceDir, section),
});

if (args.has("self-test-sensitive-scan")) {
  try {
    mkdirSync(evidenceDir, { recursive: true });
    runSensitiveScanSelfTest();
    console.log(JSON.stringify({
      ok: true,
      scenario: "sensitive-scan-self-test",
    }, null, 2));
  } finally {
    await runtime.cleanup();
  }
  process.exit(0);
}

try {
  mkdirSync(evidenceDir, { recursive: true });
  validateScenario(scenario);
  if (scenario === "forced-feedback-truncation") {
    runtime.setProviderServer(await startForcedTruncationProvider({ providerPort: PROVIDER_PORT }));
  }
  const seedResult = seedDatabase();
  const api = runtime.startProcess({
    name: "api",
    command: PYTHON,
    args: [
      "-m",
      "uvicorn",
      "app.main:app",
      "--app-dir",
      "apps/api",
      "--host",
      "127.0.0.1",
      "--port",
      API_PORT,
    ],
    env: smokeEnv(),
  });
  const web = runtime.startProcess({
    name: "web",
    command: process.execPath,
    args: [
      path.join(ROOT_DIR, "node_modules/vite/bin/vite.js"),
      path.join(ROOT_DIR, "apps/web"),
      "--host",
      "127.0.0.1",
      "--port",
      WEB_PORT,
      "--strictPort",
    ],
    env: {
      ...process.env,
      VITE_API_PROXY_TARGET: API_BASE,
    },
  });

  await waitForJson({
    label: "api health",
    url: `${API_BASE}/api/v1/health`,
    predicate: (body) => body?.status === "ok",
    runtime,
  });
  await waitForText({
    label: "interview route html",
    url: `${WEB_BASE}/interview/${encodeURIComponent(seedResult.session_id)}`,
    predicate: (body) => body.includes('<div id="root"></div>'),
    runtime,
  });
  await waitForJson({
    label: "proxied health",
    url: `${WEB_BASE}/api/v1/health`,
    predicate: (body) => body?.status === "ok",
    runtime,
  });

  const login = await requestJson(`${WEB_BASE}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ identifier: "developer", password: DEV_PASSWORD }),
  });
  const cookie = extractSessionCookie(login.response);
  const detail = await requestJson(`${WEB_BASE}/api/v1/polish-sessions/${encodeURIComponent(seedResult.session_id)}`, {
    headers: { Cookie: cookie },
  });
  const answers = detail.body?.data?.turns?.flatMap((turn) => turn.answers ?? []) ?? [];
  assert(answers.length === 3, "feedback smoke should expose three seeded answers");

  const samples = Object.fromEntries(answers.map((answer) => [answer.answer_id, {
    feedback_id: answer.feedback_id ?? null,
    status: answer.feedback_payload?.status ?? "pending",
    feedback_text: answer.feedback_payload?.feedback_text ?? answer.feedback_text ?? null,
  }]));
  assert(samples.ans_feedback_smoke_pending?.status === "pending", "pending answer should expose pending fallback payload");
  assert(samples.ans_feedback_smoke_generated?.status === "generated", "generated answer should expose generated payload");
  assert(samples.ans_feedback_smoke_failed?.status === "generation_failed", "failed answer should expose generation_failed payload");
  assert(!JSON.stringify(samples).includes("provider_payload_should_not_render"), "API samples should not leak provider payload fixtures");

  if (scenario === "forced-feedback-truncation") {
    const forcedResult = await runForcedFeedbackTruncationScenario({
      rootDir: ROOT_DIR,
      evidenceDir,
      tempDir,
      webBase: WEB_BASE,
      apiLogPath,
      seedResult,
      cookie,
      runtime,
    });
    console.log(JSON.stringify(forcedResult, null, 2));
  }

  console.log(JSON.stringify({
    ok: true,
    scenario,
    session_id: seedResult.session_id,
    api_base: API_BASE,
    web_base: WEB_BASE,
    samples,
  }, null, 2));

  if (Number.isFinite(KEEP_ALIVE_MS) && KEEP_ALIVE_MS > 0) {
    await delay(KEEP_ALIVE_MS);
  }
} finally {
  await runtime.cleanup();
}

function seedDatabase() {
  const result = spawnSync(PYTHON, ["scripts/qa/seed_polish_feedback_frontend_smoke.py"], {
    cwd: ROOT_DIR,
    env: smokeEnv(),
    encoding: "utf8",
  });
  if (result.status !== 0) {
    throw new Error(`seed failed\nstdout:\n${result.stdout}\nstderr:\n${result.stderr}`);
  }
  return JSON.parse(result.stdout.trim());
}

function smokeEnv() {
  const pythonPath = [ROOT_DIR, path.join(ROOT_DIR, "apps/api")].join(path.delimiter);
  return {
    ...process.env,
    API_AUTH_ENV: "test",
    API_ENV: "test",
    API_AUTH_DEV_USER_ENABLED: "true",
    API_AUTH_DEV_USER_IDENTIFIER: "developer",
    API_AUTH_DEV_USER_EMAIL: DEV_EMAIL,
    API_AUTH_DEV_USER_USERNAME: "developer",
    API_AUTH_DEV_DISPLAY_NAME: "Polish Feedback Smoke User",
    API_AUTH_DEV_USER_PASSWORD: DEV_PASSWORD,
    API_PORT,
    API_DATABASE_URL: databaseUrl,
    API_LOG_FILE: apiLogPath,
    API_LOG_FILE_ENABLED: "true",
    API_DB_AUTO_MIGRATE: "false",
    LLM_PROVIDER: "openai_compatible",
    LLM_OPENAI_API_KEY: "smoke-redacted-key",
    LLM_OPENAI_BASE_URL: PROVIDER_BASE,
    LLM_OPENAI_MODEL: "deepseek-v4-pro-smoke",
    LLM_OPENAI_MAX_TOKENS: "4800",
    PYTHONPATH: process.env.PYTHONPATH ? `${pythonPath}${path.delimiter}${process.env.PYTHONPATH}` : pythonPath,
  };
}

function extractSessionCookie(response) {
  const setCookieValues = typeof response.headers.getSetCookie === "function"
    ? response.headers.getSetCookie()
    : [response.headers.get("set-cookie")].filter(Boolean);
  const setCookie = setCookieValues.find((value) => value.startsWith("aifi_session="));
  assert(setCookie, "login should set aifi_session cookie");
  return setCookie.split(";", 1)[0];
}

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

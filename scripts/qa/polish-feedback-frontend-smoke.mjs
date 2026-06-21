import { spawn, spawnSync } from "node:child_process";
import { existsSync, mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { createServer } from "node:net";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT_DIR = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const API_PORT = await resolvePort("AIFI_FEEDBACK_SMOKE_API_PORT", 18181);
const WEB_PORT = await resolvePort("AIFI_FEEDBACK_SMOKE_WEB_PORT", 15273);
const DEV_PASSWORD = process.env.AIFI_FEEDBACK_SMOKE_DEV_PASSWORD ?? "polish-feedback-smoke-password";
const DEV_EMAIL = "developer@example.com";
const API_BASE = `http://127.0.0.1:${API_PORT}`;
const WEB_BASE = `http://127.0.0.1:${WEB_PORT}`;
const PYTHON = resolvePython();
const KEEP_ALIVE_MS = Number.parseInt(process.env.AIFI_FEEDBACK_SMOKE_KEEP_ALIVE_MS ?? "0", 10);
const tempDir = mkdtempSync(path.join(tmpdir(), "aifi-auth-smoke-"));
const databasePath = path.join(tempDir, "smoke.sqlite3");
const databaseUrl = `sqlite+pysqlite:///${databasePath}`;
const children = [];

try {
  const seedResult = seedDatabase();
  const api = startProcess("api", PYTHON, [
    "-m",
    "uvicorn",
    "app.main:app",
    "--app-dir",
    "apps/api",
    "--host",
    "127.0.0.1",
    "--port",
    API_PORT,
  ], smokeEnv());
  const web = startProcess("web", process.execPath, [
    path.join(ROOT_DIR, "node_modules/vite/bin/vite.js"),
    path.join(ROOT_DIR, "apps/web"),
    "--host",
    "127.0.0.1",
    "--port",
    WEB_PORT,
    "--strictPort",
  ], {
    ...process.env,
    VITE_API_PROXY_TARGET: API_BASE,
  });

  await waitForJson("api health", `${API_BASE}/api/v1/health`, (body) => body?.status === "ok", [api, web]);
  await waitForText("interview route html", `${WEB_BASE}/interview/${encodeURIComponent(seedResult.session_id)}`, (body) => body.includes('<div id="root"></div>'), [api, web]);
  await waitForJson("proxied health", `${WEB_BASE}/api/v1/health`, (body) => body?.status === "ok", [api, web]);

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

  console.log(JSON.stringify({
    ok: true,
    session_id: seedResult.session_id,
    api_base: API_BASE,
    web_base: WEB_BASE,
    samples,
  }, null, 2));

  if (Number.isFinite(KEEP_ALIVE_MS) && KEEP_ALIVE_MS > 0) {
    await delay(KEEP_ALIVE_MS);
  }
} finally {
  await cleanup();
}

function resolvePython() {
  const candidates = [
    process.env.PYTHON,
    path.join(ROOT_DIR, ".venv/bin/python"),
    path.join(ROOT_DIR, ".venv/Scripts/python.exe"),
    "python3",
    "python",
  ].filter(Boolean);
  return candidates.find((candidate) => candidate === "python3" || candidate === "python" || existsSync(candidate)) ?? "python";
}

async function resolvePort(envName, defaultPort) {
  const configured = process.env[envName];
  if (configured?.trim()) {
    return configured.trim();
  }
  for (let port = defaultPort; port < defaultPort + 100; port += 1) {
    if (await canListen(port)) {
      return String(port);
    }
  }
  throw new Error(`No free port found near ${defaultPort} for ${envName}`);
}

function canListen(port) {
  return new Promise((resolve) => {
    const server = createServer();
    server.once("error", () => resolve(false));
    server.once("listening", () => server.close(() => resolve(true)));
    server.listen(port, "127.0.0.1");
  });
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
    LLM_PROVIDER: "",
    PYTHONPATH: process.env.PYTHONPATH ? `${pythonPath}${path.delimiter}${process.env.PYTHONPATH}` : pythonPath,
  };
}

function startProcess(name, command, args, env) {
  const child = spawn(command, args, { cwd: ROOT_DIR, env, stdio: ["ignore", "pipe", "pipe"] });
  const state = { name, child, exited: false, output: [] };
  children.push(state);
  const remember = (chunk) => {
    const lines = chunk.toString().split(/\r?\n/).filter(Boolean);
    state.output.push(...lines.map((line) => `[${name}] ${line}`));
    if (state.output.length > 80) {
      state.output.splice(0, state.output.length - 80);
    }
  };
  child.stdout.on("data", remember);
  child.stderr.on("data", remember);
  child.on("exit", () => {
    state.exited = true;
  });
  return state;
}

async function waitForJson(label, url, predicate, watchedProcesses) {
  await waitFor(label, async () => {
    const { body } = await requestJson(url);
    return predicate(body);
  }, watchedProcesses);
}

async function waitForText(label, url, predicate, watchedProcesses) {
  await waitFor(label, async () => {
    const response = await fetch(url);
    const body = await response.text();
    return response.ok && predicate(body);
  }, watchedProcesses);
}

async function waitFor(label, probe, watchedProcesses) {
  const started = Date.now();
  let lastError = null;
  while (Date.now() - started < 45_000) {
    for (const processState of watchedProcesses) {
      if (processState.exited) {
        throw new Error(`${processState.name} exited while waiting for ${label}\n${processState.output.join("\n")}`);
      }
    }
    try {
      if (await probe()) {
        console.log(`[feedback-smoke] ${label} ok`);
        return;
      }
    } catch (error) {
      lastError = error;
    }
    await delay(500);
  }
  throw new Error(`Timed out waiting for ${label}${lastError ? `: ${lastError.message}` : ""}`);
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, options);
  const raw = await response.text();
  const body = raw ? JSON.parse(raw) : null;
  if (!response.ok) {
    throw new Error(`${options.method ?? "GET"} ${url} -> ${response.status}: ${raw}`);
  }
  return { response, body };
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

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function cleanup() {
  for (const { child } of [...children].reverse()) {
    if (child.exitCode === null && child.signalCode === null) {
      child.kill("SIGTERM");
    }
  }
  await delay(500);
  rmSync(tempDir, { recursive: true, force: true });
}

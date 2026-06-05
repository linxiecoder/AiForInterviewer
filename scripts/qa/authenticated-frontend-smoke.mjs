import { spawn, spawnSync } from "node:child_process";
import { existsSync, mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { createServer } from "node:net";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT_DIR = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const API_PORT = await resolvePort("AIFI_AUTH_SMOKE_API_PORT", 18081);
const WEB_PORT = await resolvePort("AIFI_AUTH_SMOKE_WEB_PORT", 15173);
const DEV_PASSWORD = process.env.AIFI_AUTH_SMOKE_DEV_PASSWORD ?? "phase-2c-auth-smoke-password";
const DEV_EMAIL = "developer@example.com";
const API_BASE = `http://127.0.0.1:${API_PORT}`;
const WEB_BASE = `http://127.0.0.1:${WEB_PORT}`;
const PYTHON = existsSync(path.join(ROOT_DIR, ".venv/bin/python"))
  ? path.join(ROOT_DIR, ".venv/bin/python")
  : "python3";

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
  await waitForText("/interview html", `${WEB_BASE}/interview`, (body) => body.includes('<div id="root"></div>'), [api, web]);
  await waitForText("main tsx served", `${WEB_BASE}/src/main.tsx`, (body) => body.includes("createRoot"), [api, web]);
  await waitForJson("proxied health", `${WEB_BASE}/api/v1/health`, (body) => body?.status === "ok", [api, web]);

  const login = await requestJson(`${WEB_BASE}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ identifier: "developer", password: DEV_PASSWORD }),
  });
  assert(login.body?.resource_type === "current_user", "login response should be current_user");
  const cookie = extractSessionCookie(login.response);

  const me = await requestJson(`${WEB_BASE}/api/v1/auth/me`, { headers: { Cookie: cookie } });
  assert(me.body?.data?.email === DEV_EMAIL, "auth/me should return the injected dev user");

  const list = await requestJson(`${WEB_BASE}/api/v1/polish-sessions`, { headers: { Cookie: cookie } });
  assert(list.body?.resource_type === "polish_session_list", "polish session list should return a success envelope");
  assert(Array.isArray(list.body.data), "polish session list data should be an array");
  assert(list.body.data.some((session) => session.session_id === seedResult.session_id), "seeded smoke session should be visible in the authenticated list");

  const detail = await requestJson(`${WEB_BASE}/api/v1/polish-sessions/${encodeURIComponent(seedResult.session_id)}`, {
    headers: { Cookie: cookie },
  });
  const turn = detail.body?.data?.turns?.[0];
  assert(detail.body?.resource_type === "polish_session", "session detail should return a polish_session envelope");
  assert(turn?.question_text?.includes("前端工作台路径"), "session detail should include the smoke question");
  assert(turn?.question_metadata?.question_pattern === "authenticated_frontend_smoke", "session detail should include question_metadata");

  await waitForText(
    "/interview/:sessionId html",
    `${WEB_BASE}/interview/${encodeURIComponent(seedResult.session_id)}`,
    (body) => body.includes('<div id="root"></div>'),
    [api, web],
  );

  console.log(`[auth-smoke] OK session=${seedResult.session_id} api=${API_BASE} web=${WEB_BASE}`);
} finally {
  await cleanup();
}

function smokeEnv() {
  const pythonPath = path.join(ROOT_DIR, "apps/api");
  return {
    ...process.env,
    API_AUTH_ENV: "test",
    API_ENV: "test",
    API_AUTH_DEV_USER_ENABLED: "true",
    API_AUTH_DEV_USER_IDENTIFIER: "developer",
    API_AUTH_DEV_USER_EMAIL: DEV_EMAIL,
    API_AUTH_DEV_USER_USERNAME: "developer",
    API_AUTH_DEV_DISPLAY_NAME: "Phase 2C Smoke User",
    API_AUTH_DEV_USER_PASSWORD: DEV_PASSWORD,
    API_PORT,
    API_DATABASE_URL: databaseUrl,
    LLM_PROVIDER: "",
    PYTHONPATH: process.env.PYTHONPATH ? `${pythonPath}${path.delimiter}${process.env.PYTHONPATH}` : pythonPath,
  };
}

async function resolvePort(envName, defaultPort) {
  const configured = process.env[envName];
  if (configured !== undefined && configured.trim() !== "") {
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
    server.once("listening", () => {
      server.close(() => resolve(true));
    });
    server.listen(port, "127.0.0.1");
  });
}

function seedDatabase() {
  const result = spawnSync(PYTHON, ["scripts/qa/seed_authenticated_frontend_smoke.py"], {
    cwd: ROOT_DIR,
    env: smokeEnv(),
    encoding: "utf8",
  });
  if (result.status !== 0) {
    throw new Error(`seed failed\nstdout:\n${result.stdout}\nstderr:\n${result.stderr}`);
  }
  try {
    return JSON.parse(result.stdout.trim());
  } catch (error) {
    throw new Error(`seed returned invalid JSON: ${result.stdout.trim()}`);
  }
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
        console.log(`[auth-smoke] ${label} ok`);
        return;
      }
    } catch (error) {
      lastError = error;
    }
    await delay(500);
  }
  const logs = watchedProcesses.flatMap((processState) => processState.output).join("\n");
  throw new Error(`Timed out waiting for ${label}${lastError ? `: ${lastError.message}` : ""}\n${logs}`);
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, options);
  const raw = await response.text();
  let body = null;
  if (raw) {
    try {
      body = JSON.parse(raw);
    } catch (error) {
      throw new Error(`${options.method ?? "GET"} ${url} returned non-JSON ${response.status}: ${raw.slice(0, 500)}`);
    }
  }
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
  const activeChildren = [...children].reverse();
  for (const { child } of activeChildren) {
    if (isProcessRunning(child)) {
      child.kill("SIGTERM");
    }
  }
  await Promise.all(activeChildren.map((state) => waitForExit(state, 1_500)));
  for (const { child } of activeChildren) {
    if (isProcessRunning(child)) {
      child.kill("SIGKILL");
    }
  }
  await Promise.all(activeChildren.map((state) => waitForExit(state, 500)));
  rmSync(tempDir, { recursive: true, force: true });
}

function isProcessRunning(child) {
  return child.exitCode === null && child.signalCode === null;
}

function waitForExit({ child }, timeoutMs) {
  if (!isProcessRunning(child)) {
    return Promise.resolve();
  }
  return new Promise((resolve) => {
    const timer = setTimeout(resolve, timeoutMs);
    child.once("exit", () => {
      clearTimeout(timer);
      resolve();
    });
  });
}

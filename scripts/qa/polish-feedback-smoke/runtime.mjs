import { spawn, spawnSync } from "node:child_process";
import { rmSync, writeFileSync } from "node:fs";
import { createServer as createNetServer } from "node:net";
import path from "node:path";

export async function resolvePort(envName, defaultPort) {
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

export function createSmokeRuntime(config) {
  const children = [];
  let providerServer = null;
  return {
    get tempDir() {
      return config.tempDir;
    },
    get children() {
      return children;
    },
    setProviderServer(server) {
      providerServer = server;
    },
    startProcess(processConfig) {
      const child = spawn(processConfig.command, processConfig.args, {
        cwd: config.rootDir,
        env: processConfig.env,
        stdio: ["ignore", "pipe", "pipe"],
      });
      const state = { name: processConfig.name, child, exited: false, output: [] };
      children.push(state);
      const remember = (chunk) => {
        const lines = chunk.toString().split(/\r?\n/).filter(Boolean);
        state.output.push(...lines.map((line) => `[${processConfig.name}] ${line}`));
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
    },
    async waitFor(label, probe) {
      await waitForProcessBackedProbe(label, probe, children);
    },
    async cleanup() {
      if (providerServer !== null) {
        await new Promise((resolve) => providerServer.close(resolve));
        providerServer = null;
      }
      for (const { child } of [...children].reverse()) {
        if (isProcessRunning(child)) {
          child.kill("SIGTERM");
        }
      }
      await delay(500);
      writeCleanupReceipt(config);
      rmSync(config.tempDir, { recursive: true, force: true });
    },
  };
}

export function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function waitForProcessBackedProbe(label, probe, watchedProcesses) {
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

function canListen(port) {
  return new Promise((resolve) => {
    const server = createNetServer();
    server.once("error", () => resolve(false));
    server.once("listening", () => server.close(() => resolve(true)));
    server.listen(port, "127.0.0.1");
  });
}

function isProcessRunning(child) {
  return child.exitCode === null && child.signalCode === null;
}

function writeCleanupReceipt(config) {
  if (config.scenario !== "forced-feedback-truncation") {
    return;
  }
  const checkedPorts = `${config.ports.api},${config.ports.web},${config.ports.provider}`;
  const command = `Get-NetTCPConnection -LocalPort ${checkedPorts} -ErrorAction SilentlyContinue | Where-Object { $_.State -eq 'Listen' } | Select-Object LocalAddress,LocalPort,State,OwningProcess`;
  const result = spawnSync("powershell.exe", ["-NoProfile", "-Command", command], {
    cwd: config.rootDir,
    encoding: "utf8",
    timeout: 15_000,
  });
  const output = `${result.stdout ?? ""}${result.stderr ?? ""}`.trim();
  const receipt = [
    "surface: cleanup receipt",
    "scenario: forced-feedback-truncation",
    `command: powershell.exe -NoProfile -Command "${command}"`,
    `exit_status: ${result.status}`,
    `checked_ports: ${checkedPorts}`,
    output ? `output:\n${output}` : "output: <no listeners>",
  ].join("\n");
  writeFileSync(path.join(config.evidenceDir, "task-6-cleanup.txt"), receipt, "utf8");
  config.appendToTextArtifacts([
    "",
    "[cleanup receipt]",
    "artifact: task-6-cleanup.txt",
    `checked_ports: ${checkedPorts}`,
    output ? "result: listeners still reported; inspect cleanup artifact" : "result: <no listeners>",
  ].join("\n"));
}

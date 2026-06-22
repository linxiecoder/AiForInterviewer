import { existsSync } from "node:fs";
import path from "node:path";

export function parseArgs(argv) {
  const parsed = new Map();
  for (let index = 0; index < argv.length; index += 1) {
    const item = argv[index];
    if (!item.startsWith("--")) {
      continue;
    }
    const [rawKey, inlineValue] = item.slice(2).split("=", 2);
    if (inlineValue !== undefined) {
      parsed.set(rawKey, inlineValue);
      continue;
    }
    const nextValue = argv[index + 1];
    if (nextValue !== undefined && !nextValue.startsWith("--")) {
      parsed.set(rawKey, nextValue);
      index += 1;
    } else {
      parsed.set(rawKey, "true");
    }
  }
  return parsed;
}

export function resolvePython(rootDir) {
  const candidates = [
    process.env.PYTHON,
    path.join(rootDir, ".venv/bin/python"),
    path.join(rootDir, ".venv/Scripts/python.exe"),
    "python3",
    "python",
  ].filter(Boolean);
  return candidates.find((candidate) => candidate === "python3" || candidate === "python" || existsSync(candidate)) ?? "python";
}

export function validateScenario(value) {
  if (value !== "seeded-feedback-states" && value !== "forced-feedback-truncation") {
    throw new Error(`Unsupported scenario: ${value}`);
  }
}

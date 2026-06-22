import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";

import { appendToTask6TextArtifacts, classifySensitiveMarker, writeSensitiveScanClassification } from "./sensitive-scan.mjs";

const PLAYWRIGHT_CLI_ARTIFACT_DIR = ".playwright-cli";

export function runSensitiveScanSelfTest() {
  for (const item of sensitiveScanSelfTestCases()) {
    const actual = classifySensitiveMarker(item.target, item.line, item.pattern);
    assert(actual === item.expected, `${item.label}: expected ${item.expected}, got ${actual}`);
  }
  assertRawApiDevLogForbiddenMarkersBlock();
  assertCleanupAppendKeepsSensitiveScanSection();
}

function sensitiveScanSelfTestCases() {
  const cookiePattern = ["Co", "okie"].join("");
  const sessionPattern = ["aifi_", "session"].join("");
  const emptyCookieHeader = [cookiePattern, ": ", sessionPattern, "="].join("");
  const emptyCookieHeaderWithSpaces = [cookiePattern, ": ", sessionPattern, "=   "].join("");
  const realCookieHeader = [cookiePattern, ": ", sessionPattern, "=abc123"].join("");
  const redactionPredicateLine = ["if (arg.startsWith(\"", cookiePattern, ": ", sessionPattern, "=\")) {"].join("");
  const apiKeyField = ["api", "_key"].join("");
  const rawPromptField = ["raw", "_prompt"].join("");
  const providerPayloadField = ["provider", "_payload"].join("");
  const allowed = "allowed_redacted_or_test_context_marker";
  const blocking = "blocking_leak";
  return [
    caseOf("json api key blocks", "task-6-http.txt", `"${apiKeyField}": "sk-real-secret"`, apiKeyField, blocking),
    caseOf("json raw prompt blocks", "task-6-api-dev-log.txt", `"${rawPromptField}": "full prompt text"`, rawPromptField, blocking),
    caseOf("json provider payload blocks", "task-6-http.txt", `"${providerPayloadField}": {"secret": true}`, providerPayloadField, blocking),
    caseOf("empty cookie header is allowed", "task-6-http.txt", emptyCookieHeader, cookiePattern, allowed),
    caseOf("empty cookie session marker is allowed", "task-6-http.txt", emptyCookieHeader, sessionPattern, allowed),
    caseOf("empty cookie header with spaces is allowed", "task-6-http.txt", emptyCookieHeaderWithSpaces, cookiePattern, allowed),
    caseOf("real request cookie header blocks", "task-6-http.txt", realCookieHeader, cookiePattern, blocking),
    caseOf("real source cookie header blocks", "scripts/qa/polish-feedback-frontend-smoke.mjs", `const h = "${realCookieHeader}";`, cookiePattern, blocking),
    caseOf("playwright artifact session marker blocks", `${PLAYWRIGHT_CLI_ARTIFACT_DIR}/page.yml`, `name: ${sessionPattern}`, sessionPattern, blocking),
    caseOf("redacted cookie header is allowed", "task-6-http.txt", `${cookiePattern}: <redacted>`, cookiePattern, allowed),
    caseOf("redacted session marker is allowed", "task-6-http.txt", `${cookiePattern}: ${sessionPattern}=<redacted>`, cookiePattern, allowed),
    caseOf("source marker definition is allowed", "scripts/qa/polish-feedback-smoke/sensitive-scan.mjs", `"${apiKeyField}",`, apiKeyField, allowed),
    caseOf("script harness cookie variable is allowed", "scripts/qa/polish-feedback-frontend-smoke.mjs", `headers: { ${cookiePattern}: cookie },`, cookiePattern, "allowed_test_harness_cookie_variable"),
    caseOf("redaction predicate cookie is allowed", "scripts/qa/polish-feedback-smoke/curl-client.mjs", redactionPredicateLine, cookiePattern, allowed),
    caseOf("redaction predicate session is allowed", "scripts/qa/polish-feedback-smoke/curl-client.mjs", redactionPredicateLine, sessionPattern, allowed),
    caseOf("sensitive scan report line is allowed", "task-6-http.txt", `allowed_redacted_or_test_context_marker: scripts/qa/polish-feedback-smoke/curl-client.mjs:48: ${cookiePattern}`, cookiePattern, "allowed_sensitive_scan_report_marker"),
  ];
}

function caseOf(label, target, line, pattern, expected) {
  return { label, target, line, pattern, expected };
}

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

function assertRawApiDevLogForbiddenMarkersBlock() {
  const rootDir = mkdtempSync(path.join(tmpdir(), "aifi-sensitive-scan-self-test-"));
  try {
    const evidenceDir = path.join(rootDir, ".omo/evidence/polish-feedback-generation-observability-fix");
    const rawLogDir = path.join(rootDir, "tmp/logs");
    mkdirSync(evidenceDir, { recursive: true });
    mkdirSync(rawLogDir, { recursive: true });
    writeFileSync(path.join(evidenceDir, "task-6-http.txt"), "surface: HTTP\n", "utf8");
    writeFileSync(path.join(evidenceDir, "task-6-api-dev-log.txt"), "surface: API dev log\n", "utf8");
    const rawCompletionField = ["raw", "_completion"].join("");
    writeFileSync(
      path.join(rawLogDir, "api-dev.log"),
      `{"event":"llm_response","${rawCompletionField}":"provider completion should block"}\n`,
      "utf8",
    );

    assertThrows(
      () => writeSensitiveScanClassification({ rootDir, evidenceDir }),
      "raw tmp/logs/api-dev.log forbidden marker should block sensitive scan",
    );
  } finally {
    rmSync(rootDir, { recursive: true, force: true });
  }
}

function assertThrows(callback, message) {
  try {
    callback();
  } catch {
    return;
  }
  throw new Error(message);
}

function assertCleanupAppendKeepsSensitiveScanSection() {
  const rootDir = mkdtempSync(path.join(tmpdir(), "aifi-sensitive-scan-append-test-"));
  try {
    const evidenceDir = path.join(rootDir, ".omo/evidence/polish-feedback-generation-observability-fix");
    mkdirSync(evidenceDir, { recursive: true });
    for (const fileName of ["task-6-http.txt", "task-6-api-dev-log.txt"]) {
      writeFileSync(
        path.join(evidenceDir, fileName),
        "surface: evidence\n\n[sensitive scan classification]\nblocking_leaks: 0\n",
        "utf8",
      );
    }

    appendToTask6TextArtifacts(evidenceDir, "\n[cleanup receipt]\nresult: <no listeners>");

    for (const fileName of ["task-6-http.txt", "task-6-api-dev-log.txt"]) {
      const content = readFileSync(path.join(evidenceDir, fileName), "utf8");
      assert(content.includes("[sensitive scan classification]"), `${fileName} should keep sensitive scan section`);
      assert(content.includes("blocking_leaks: 0"), `${fileName} should keep sensitive scan result`);
      assert(content.includes("[cleanup receipt]"), `${fileName} should append cleanup receipt`);
    }
  } finally {
    rmSync(rootDir, { recursive: true, force: true });
  }
}

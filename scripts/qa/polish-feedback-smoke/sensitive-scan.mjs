import { existsSync, readFileSync, readdirSync, statSync, writeFileSync } from "node:fs";
import path from "node:path";

const PLAYWRIGHT_CLI_ARTIFACT_DIR = ".playwright-cli";
const RAW_API_DEV_LOG_TARGET = "tmp/logs/api-dev.log";
const MAX_SCAN_FILE_BYTES = 1_000_000;

const SOURCE_CONTEXT_TARGETS = [
  "scripts/qa/polish-feedback-frontend-smoke.mjs",
  "scripts/qa/polish-feedback-smoke/browser-artifact.mjs",
  "scripts/qa/polish-feedback-smoke/cli.mjs",
  "scripts/qa/polish-feedback-smoke/curl-client.mjs",
  "scripts/qa/polish-feedback-smoke/feedback-polling.mjs",
  "scripts/qa/polish-feedback-smoke/forced-provider.mjs",
  "scripts/qa/polish-feedback-smoke/http-artifact.mjs",
  "scripts/qa/polish-feedback-smoke/http-evidence.mjs",
  "scripts/qa/polish-feedback-smoke/log-artifact.mjs",
  "scripts/qa/polish-feedback-smoke/runtime.mjs",
  "scripts/qa/polish-feedback-smoke/sensitive-scan.mjs",
  "scripts/qa/polish-feedback-smoke/sensitive-scan-self-test.mjs",
];

const SENSITIVE_PATTERNS = [
  "Cookie",
  "aifi_session",
  "api_key",
  "provider_payload",
  "raw_prompt",
  "raw_completion",
  "reasoning_content",
  "authorization",
  "bearer ",
];

export function forbiddenEvidenceMarkers() {
  return [
    "raw_prompt",
    "raw_completion",
    "raw_provider_payload",
    "provider_payload_should_not_render",
    "reasoning_content",
    "api_key",
    "authorization",
    "cookie",
    "aifi_session",
    "bearer ",
  ];
}

export function writeSensitiveScanClassification({ rootDir, evidenceDir }) {
  const scanTargets = buildScanTargets(rootDir, evidenceDir);
  const matches = [];
  for (const target of scanTargets) {
    const fullPath = path.join(rootDir, target);
    if (!existsSync(fullPath)) {
      continue;
    }
    const lines = readFileSync(fullPath, "utf8").split(/\r?\n/);
    for (const [index, line] of lines.entries()) {
      for (const pattern of SENSITIVE_PATTERNS) {
        if (!line.toLowerCase().includes(pattern.toLowerCase())) {
          continue;
        }
        matches.push({
          target,
          line: index + 1,
          pattern,
          classification: classifySensitiveMarker(target, line, pattern),
        });
      }
    }
  }
  const blocking = matches.filter((match) => match.classification === "blocking_leak");
  const report = [
    "",
    "[sensitive scan classification]",
    `command: node-internal scan of ${scanTargets.join(", ")}`,
    `total_matches: ${matches.length}`,
    `blocking_leaks: ${blocking.length}`,
    ...matches.map((match) => `${match.classification}: ${match.target}:${match.line}: ${match.pattern}`),
  ].join("\n");
  appendToTask6TextArtifacts(evidenceDir, report);
  if (blocking.length > 0) {
    throw new Error(`Sensitive scan found blocking leaks:\n${blocking.map((match) => `${match.target}:${match.line}:${match.pattern}`).join("\n")}`);
  }
}

export function classifySensitiveMarker(target, line, pattern) {
  const normalized = line.toLowerCase();
  const normalizedPattern = pattern.toLowerCase();
  if (isSensitiveScanReportLine(normalized)) {
    return "allowed_sensitive_scan_report_marker";
  }
  if (isConcreteSensitiveValue(normalized, normalizedPattern)) {
    return "blocking_leak";
  }
  if ((normalizedPattern === "cookie" || normalizedPattern === "aifi_session") && isEmptyAifiSessionCookie(normalized)) {
    return "allowed_redacted_or_test_context_marker";
  }
  if (pattern === "Cookie" && normalized.includes("headers: { cookie: cookie }")) {
    return "allowed_test_harness_cookie_variable";
  }
  if (isSourceContextTarget(target) && isAllowedSourceMarker(normalized, pattern)) {
    return "allowed_redacted_or_test_context_marker";
  }
  if (
    normalized.includes("<redacted>")
    || normalized.includes("redaction:")
    || normalized.includes("forbiddenevidencemarkers")
    || normalized.includes("sensitive_patterns")
    || normalized.includes("provider_payload_should_not_render")
    || normalized.includes("raw prompt/raw completion")
    || normalized.includes("api key omitted")
    || normalized.includes("only structured safe log lines")
    || normalized.includes("cookievalue")
    || normalized.includes("cookie: <redacted>")
    || normalized.includes("cookie header redacted")
    || normalized.includes("aifi_session=<redacted>")
    || normalized.includes("smoke-redacted-key")
    || isAllowedQuotedMarkerDefinition(normalized, normalizedPattern)
  ) {
    return "allowed_redacted_or_test_context_marker";
  }
  return "blocking_leak";
}

export function appendToTask6TextArtifacts(evidenceDir, section) {
  const isSensitiveScanSection = section.trimStart().startsWith("[sensitive scan classification]");
  for (const fileName of ["task-6-http.txt", "task-6-api-dev-log.txt"]) {
    const artifactPath = path.join(evidenceDir, fileName);
    if (existsSync(artifactPath)) {
      const current = readFileSync(artifactPath, "utf8");
      const baseContent = isSensitiveScanSection ? stripSensitiveScanSections(current).trimEnd() : current.trimEnd();
      const nextContent = `${baseContent}\n${section.trimEnd()}\n`;
      writeFileSync(artifactPath, nextContent, "utf8");
    }
  }
}

export function buildScanTargets(rootDir, evidenceDir) {
  const httpArtifact = path.relative(rootDir, path.join(evidenceDir, "task-6-http.txt")).replaceAll(path.sep, "/");
  const apiLogArtifact = path.relative(rootDir, path.join(evidenceDir, "task-6-api-dev-log.txt")).replaceAll(path.sep, "/");
  const playwrightArtifacts = collectExistingScanFiles(rootDir, PLAYWRIGHT_CLI_ARTIFACT_DIR);
  return [...SOURCE_CONTEXT_TARGETS, ...playwrightArtifacts, RAW_API_DEV_LOG_TARGET, httpArtifact, apiLogArtifact];
}

function stripSensitiveScanSections(content) {
  const markerWithLeadingNewline = "\n[sensitive scan classification]";
  const markerIndex = content.indexOf(markerWithLeadingNewline);
  if (markerIndex >= 0) {
    return content.slice(0, markerIndex);
  }
  if (content.startsWith("[sensitive scan classification]")) {
    return "";
  }
  return content;
}

function collectExistingScanFiles(rootDir, relativePath) {
  const absolutePath = path.join(rootDir, relativePath);
  if (!existsSync(absolutePath)) {
    return [];
  }
  const stats = statSync(absolutePath);
  if (stats.isFile()) {
    return stats.size <= MAX_SCAN_FILE_BYTES ? [relativePath.replaceAll(path.sep, "/")] : [];
  }
  if (!stats.isDirectory()) {
    return [];
  }
  return readdirSync(absolutePath).flatMap((name) => collectExistingScanFiles(rootDir, path.join(relativePath, name)));
}

function isAllowedSourceMarker(normalized, pattern) {
  return pattern === "Cookie" || pattern === "aifi_session" || ["provider_payload_should_not_render", "raw_provider_payload", "raw_prompt", "raw_completion", "reasoning_content", "api_key", "authorization", "bearer "].some((marker) => normalized.includes(marker));
}

function isSensitiveScanReportLine(normalized) {
  return normalized.startsWith("[sensitive scan classification]") || normalized.startsWith("command: node-internal scan of ") || normalized.startsWith("total_matches:") || normalized.startsWith("blocking_leaks:") || /^(allowed_[a-z_]+|blocking_leak): .+:\d+: [a-z_ ]+$/.test(normalized);
}

function isConcreteSensitiveValue(normalized, normalizedPattern) {
  if (normalized.includes("<redacted>") || normalized.includes("redacted")) {
    return false;
  }
  if (["api_key", "provider_payload", "raw_prompt", "raw_completion", "reasoning_content"].includes(normalizedPattern)) {
    return containsConcreteJsonFieldValue(normalized, normalizedPattern);
  }
  if (normalizedPattern === "cookie") {
    return containsConcreteCookieValue(normalized);
  }
  if (normalizedPattern === "aifi_session") {
    return /\baifi_session\s*=\s*[a-z0-9_.=-]+/.test(normalized);
  }
  if (normalizedPattern === "authorization" || normalizedPattern === "bearer ") {
    return /\bauthorization\s*:\s*bearer\s+[a-z0-9._=-]+/.test(normalized)
      || /\bbearer\s+[a-z0-9._=-]{8,}/.test(normalized);
  }
  return false;
}

function containsConcreteJsonFieldValue(normalized, fieldName) {
  const quotedKey = `"${fieldName}"`;
  const keyIndex = normalized.indexOf(quotedKey);
  if (keyIndex < 0) {
    return false;
  }
  const value = normalized.slice(keyIndex + quotedKey.length).trimStart();
  if (!value.startsWith(":")) {
    return false;
  }
  return !isAllowedJsonPlaceholder(value.slice(1).trimStart());
}

function isAllowedJsonPlaceholder(value) {
  return value === "" || value.startsWith("\"\"") || value.startsWith("null") || value.includes("redacted") || value.includes("smoke-redacted-key");
}

function containsConcreteCookieValue(normalized) {
  if (isEmptyAifiSessionCookie(normalized)) {
    return false;
  }
  return /\baifi_session\s*=\s*[a-z0-9_.=-]+/.test(normalized)
    || /\bcookie\s*:\s*(?!cookie\b)[a-z0-9_.=-]+/.test(normalized);
}

function isEmptyAifiSessionCookie(normalized) {
  return /\bcookie\s*:\s*aifi_session\s*=\s*(?:"|'|\)|,|;|$)/.test(normalized);
}

function isSourceContextTarget(target) {
  return SOURCE_CONTEXT_TARGETS.some((sourceTarget) => target.endsWith(sourceTarget));
}

function isAllowedQuotedMarkerDefinition(normalized, normalizedPattern) {
  const trimmed = normalized.trim();
  return trimmed === `"${normalizedPattern}",` || trimmed === `'${normalizedPattern}',` || trimmed === `"${normalizedPattern}"` || trimmed === `'${normalizedPattern}'`;
}

import { spawnSync } from "node:child_process";

export function runCurlJson(context) {
  const curlArgs = ["-i", "-sS", "-X", context.method, context.url, "-H", `Cookie: ${context.cookie}`];
  for (const [name, value] of Object.entries(context.headers)) {
    curlArgs.push("-H", `${name}: ${value}`);
  }
  if (context.body !== null && context.body !== undefined) {
    curlArgs.push("--data-binary", JSON.stringify(context.body));
  }
  const result = spawnSync("curl.exe", curlArgs, {
    cwd: context.rootDir,
    encoding: "utf8",
    timeout: 45_000,
  });
  if (result.status !== 0) {
    throw new Error(`${context.label} curl failed\nstdout:\n${result.stdout}\nstderr:\n${result.stderr}`);
  }
  const parsed = parseCurlResponse(result.stdout);
  if (parsed.statusCode < 200 || parsed.statusCode >= 300) {
    throw new Error(`${context.label} curl returned ${parsed.statusCode}\n${result.stdout}`);
  }
  return {
    invocation: redactCurlInvocation(["curl.exe", ...curlArgs]),
    raw: result.stdout,
    statusCode: parsed.statusCode,
    headers: parsed.headers,
    body: parsed.body,
  };
}

function parseCurlResponse(raw) {
  const sections = raw.split(/\r?\n\r?\n/).filter(Boolean);
  const bodyText = sections.pop() ?? "";
  const headerText = sections.pop() ?? "";
  const statusLine = headerText.split(/\r?\n/, 1)[0] ?? "";
  const statusMatch = statusLine.match(/HTTP\/\S+\s+(\d+)/);
  const statusCode = statusMatch ? Number(statusMatch[1]) : 0;
  return {
    statusCode,
    headers: headerText,
    body: JSON.parse(bodyText),
  };
}

function redactCurlInvocation(invocationArgs) {
  return invocationArgs.map((arg) => {
    if (arg.startsWith("Cookie: aifi_session=")) {
      return '"Cookie: aifi_session=<redacted>"';
    }
    return quoteShellArg(arg.replaceAll("smoke-redacted-key", "<redacted>"));
  }).join(" ");
}

function quoteShellArg(arg) {
  if (/^[A-Za-z0-9_./:=?-]+$/.test(arg)) {
    return arg;
  }
  return `"${arg.replaceAll('"', '\\"')}"`;
}

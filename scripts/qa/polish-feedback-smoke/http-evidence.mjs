import path from "node:path";

import { captureBrowserArtifact } from "./browser-artifact.mjs";
import { runCurlJson } from "./curl-client.mjs";
import { waitForTerminalFeedback } from "./feedback-polling.mjs";
import { writeHttpArtifact } from "./http-artifact.mjs";
import { writeApiLogArtifact } from "./log-artifact.mjs";
import { writeSensitiveScanClassification } from "./sensitive-scan.mjs";

export async function requestJson(url, options = {}) {
  const response = await fetch(url, options);
  const raw = await response.text();
  const body = raw ? JSON.parse(raw) : null;
  if (!response.ok) {
    throw new Error(`${options.method ?? "GET"} ${url} -> ${response.status}: ${raw}`);
  }
  return { response, body };
}

export async function waitForJson({ label, url, predicate, runtime }) {
  await runtime.waitFor(label, async () => {
    const { body } = await requestJson(url);
    return predicate(body);
  });
}

export async function waitForText({ label, url, predicate, runtime }) {
  await runtime.waitFor(label, async () => {
    const response = await fetch(url);
    const body = await response.text();
    return response.ok && predicate(body);
  });
}

export async function runForcedFeedbackTruncationScenario(context) {
  const runId = Date.now();
  const requestId = `task-6-forced-feedback-truncation-request-${runId}`;
  const traceId = `task-6-forced-feedback-truncation-trace-${runId}`;
  const answerText = `Forced truncation smoke answer task-6 ${runId}`;
  const answerCurl = runCurlJson({
    ...context,
    label: "create answer",
    url: `${context.webBase}/api/v1/polish-sessions/${encodeURIComponent(context.seedResult.session_id)}/answers`,
    method: "POST",
    body: {
      question_id: "que_auth_frontend_smoke",
      answer_text: answerText,
    },
    headers: {
      "Content-Type": "application/json",
      "Idempotency-Key": `task-6-answer-${Date.now()}`,
      "X-Request-Id": `${requestId}-answer`,
      "X-Trace-Id": traceId,
    },
  });
  const answerId = answerCurl.body.data.answer_id;
  const feedbackCurl = runCurlJson({
    ...context,
    label: "create feedback task",
    url: `${context.webBase}/api/v1/polish-sessions/${encodeURIComponent(context.seedResult.session_id)}/feedback`,
    method: "POST",
    body: { answer_id: answerId },
    headers: {
      "Content-Type": "application/json",
      "Idempotency-Key": `polish-feedback-${answerId}`,
      "X-Request-Id": requestId,
      "X-Trace-Id": traceId,
    },
  });
  const terminal = await waitForTerminalFeedback({
    ...context,
    answerId,
    aiTaskId: feedbackCurl.body.data.ai_task_id,
  });
  assert(terminal.feedbackPayload.status === "generation_failed", "forced truncation should fail closed as generation_failed");
  assert(feedbackCurl.body.data.ai_task_id === terminal.feedbackTask.ai_task_id, "feedback task id should match session detail");
  const qaMarker = buildQaMarker(answerId, terminal.feedbackTask.ai_task_id);
  writeHttpArtifact({
    ...context,
    requestId,
    traceId,
    answerId,
    answerText,
    qaMarker,
    answerCurl,
    feedbackCurl,
    terminal,
  });
  const logArtifact = await writeApiLogArtifact({
    ...context,
    requestId,
    traceId,
    aiTaskId: terminal.feedbackTask.ai_task_id,
    sessionId: context.seedResult.session_id,
    questionId: "que_auth_frontend_smoke",
    answerId,
    qaMarker,
  });
  await captureBrowserArtifact({
    ...context,
    sessionId: context.seedResult.session_id,
    answerText,
    qaMarker,
    expectedPanelText: "生成失败",
  });
  writeSensitiveScanClassification({
    rootDir: context.rootDir,
    evidenceDir: context.evidenceDir,
  });
  return {
    ok: true,
    scenario: "forced-feedback-truncation",
    session_id: context.seedResult.session_id,
    answer_id: answerId,
    ai_task_id: terminal.feedbackTask.ai_task_id,
    terminal_status: terminal.feedbackPayload.status,
    qa_marker: qaMarker,
    artifacts: {
      http: path.join(context.evidenceDir, "task-6-http.txt"),
      browser: path.join(context.evidenceDir, "task-6-browser.png"),
      api_log: logArtifact,
    },
  };
}

function buildQaMarker(answerId, aiTaskId) {
  return `T6 ans:${shortId(answerId)} task:${shortId(aiTaskId)}`;
}

function shortId(value) {
  const text = String(value);
  return text.length <= 12 ? text : text.slice(-12);
}

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

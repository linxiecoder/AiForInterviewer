import { writeFileSync } from "node:fs";
import path from "node:path";

export function writeHttpArtifact(context) {
  const feedbackData = context.feedbackCurl.body.data;
  const feedbackPayload = context.terminal.feedbackPayload;
  const artifact = [
    "surface: HTTP API via curl -i",
    "scenario: forced-feedback-truncation",
    `session_id: ${context.seedResult.session_id}`,
    "question_id: que_auth_frontend_smoke",
    `answer_id: ${context.answerId}`,
    `ai_task_id: ${feedbackData.ai_task_id}`,
    `request_id: ${context.requestId}`,
    `trace_id: ${context.traceId}`,
    `qa_marker: ${context.qaMarker}`,
    `terminal_status: ${feedbackPayload.status}`,
    `answer_text_marker: ${context.answerText}`,
    "",
    "[create-answer invocation]",
    context.answerCurl.invocation,
    `[create-answer status] ${context.answerCurl.statusCode}`,
    `[create-answer response summary] ${JSON.stringify({
      answer_id: context.answerCurl.body.data.answer_id,
      question_id: context.answerCurl.body.data.question_id,
      status: context.answerCurl.body.data.status,
    }, null, 2)}`,
    "",
    "[create-feedback invocation]",
    context.feedbackCurl.invocation,
    `[create-feedback status] ${context.feedbackCurl.statusCode}`,
    `[create-feedback response summary] ${JSON.stringify({
      ai_task_id: feedbackData.ai_task_id,
      status: feedbackData.status,
      feedback_status: feedbackData.feedback_status,
      retryable: feedbackData.retryable,
      feedback_payload_status: feedbackData.feedback_payload?.status,
      error_code: feedbackData.feedback_payload?.error?.code,
      validation_errors: feedbackData.validation_errors,
    }, null, 2)}`,
    "",
    "[session-detail terminal summary]",
    context.terminal.detailCurl.invocation,
    `[session-detail status] ${context.terminal.detailCurl.statusCode}`,
    JSON.stringify({
      answer_id: context.terminal.answer.answer_id,
      feedback_id: context.terminal.answer.feedback_id,
      feedback_payload_status: feedbackPayload.status,
      feedback_text: feedbackPayload.feedback_text,
      retryable: feedbackPayload.retryable,
      error_code: feedbackPayload.error?.code,
      qa_marker: context.qaMarker,
    }, null, 2),
    "",
    "redaction: cookie/auth headers/provider payload/raw prompt/raw completion/reasoning/API key omitted",
  ].join("\n");
  writeFileSync(path.join(context.evidenceDir, "task-6-http.txt"), artifact, "utf8");
}

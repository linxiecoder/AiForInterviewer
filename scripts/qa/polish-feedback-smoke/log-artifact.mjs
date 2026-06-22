import { existsSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";

export async function writeApiLogArtifact(context) {
  await context.runtime.waitFor("api-dev.log matching terminal lines", async () => {
    if (!existsSync(context.apiLogPath)) {
      return false;
    }
    const lines = matchingLogLines(context);
    return lines.some((line) => line.includes("feedback_generation_failed"))
      && lines.some((line) => line.includes("llm_transport_request_failed"));
  });
  const lines = matchingLogLines(context);
  const content = [
    "surface: API dev log",
    "source: tmp/logs/api-dev.log",
    "scenario: forced-feedback-truncation",
    `request_id: ${context.requestId}`,
    `trace_id: ${context.traceId}`,
    `ai_task_id: ${context.aiTaskId}`,
    `session_id: ${context.sessionId}`,
    `question_id: ${context.questionId}`,
    `answer_id: ${context.answerId}`,
    `qa_marker: ${context.qaMarker}`,
    "",
    ...lines,
    "",
    "redaction: only structured safe log lines matching this scenario are included",
  ].join("\n");
  const artifactPath = path.join(context.evidenceDir, "task-6-api-dev-log.txt");
  writeFileSync(artifactPath, content, "utf8");
  return artifactPath;
}

function matchingLogLines(context) {
  const content = readFileSync(context.apiLogPath, "utf8");
  return content.split(/\r?\n/).filter((line) => {
    if (!line.trim().startsWith("{")) {
      return false;
    }
    return (
      line.includes(context.requestId)
      || line.includes(context.traceId)
      || line.includes(context.aiTaskId)
      || (
        line.includes(context.sessionId)
        && line.includes(context.questionId)
        && line.includes(context.answerId)
      )
    );
  });
}

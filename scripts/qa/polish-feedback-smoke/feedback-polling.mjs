import { runCurlJson } from "./curl-client.mjs";
import { delay } from "./runtime.mjs";

export async function waitForTerminalFeedback(context) {
  const started = Date.now();
  let lastCurl = null;
  while (Date.now() - started < 45_000) {
    const detailCurl = runCurlJson({
      ...context,
      label: "fetch session detail",
      url: `${context.webBase}/api/v1/polish-sessions/${encodeURIComponent(context.seedResult.session_id)}`,
      method: "GET",
      body: null,
      headers: {
        "X-Request-Id": `task-6-session-detail-${Date.now()}`,
      },
    });
    lastCurl = detailCurl;
    const answer = findAnswer(detailCurl.body.data, context.answerId);
    const feedbackPayload = answer?.feedback_payload;
    if (feedbackPayload?.status === "generation_failed" || feedbackPayload?.status === "generated") {
      return {
        detail: detailCurl.body,
        detailCurl,
        answer,
        feedbackPayload,
        feedbackTask: {
          ai_task_id: context.aiTaskId,
        },
      };
    }
    await delay(750);
  }
  throw new Error(`Timed out waiting for terminal feedback for ${context.answerId}: ${JSON.stringify(lastCurl?.body)}`);
}

function findAnswer(sessionDetail, answerId) {
  const answers = sessionDetail?.turns?.flatMap((turn) => turn.answers ?? []) ?? [];
  return answers.find((answer) => answer.answer_id === answerId) ?? null;
}

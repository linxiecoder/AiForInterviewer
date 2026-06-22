import { createServer as createHttpServer } from "node:http";

export async function startForcedTruncationProvider({ providerPort }) {
  const server = createHttpServer(async (request, response) => {
    if (request.method !== "POST" || !request.url?.endsWith("/chat/completions")) {
      response.writeHead(404, { "Content-Type": "application/json" });
      response.end(JSON.stringify({ error: "not_found" }));
      return;
    }
    await consumeRequestBody(request);
    response.writeHead(200, { "Content-Type": "application/json" });
    response.end(JSON.stringify({
      id: "chatcmpl_task_6_forced_feedback_truncation",
      model: "deepseek-v4-pro-smoke",
      choices: [
        {
          finish_reason: "length",
          message: { content: "{\"feedback_text\":\"partial" },
        },
      ],
      usage: {
        prompt_tokens: 4200,
        completion_tokens: 4800,
        total_tokens: 9000,
        completion_tokens_details: {
          reasoning_tokens: 3658,
        },
      },
    }));
  });
  await new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(Number(providerPort), "127.0.0.1", resolve);
  });
  return server;
}

function consumeRequestBody(request) {
  return new Promise((resolve, reject) => {
    request.on("data", () => {});
    request.on("end", resolve);
    request.on("error", reject);
  });
}

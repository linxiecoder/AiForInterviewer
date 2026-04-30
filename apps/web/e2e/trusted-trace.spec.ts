import { expect, test } from "@playwright/test";

const trustedTracePayload = {
  record_id: "record-r1-trace",
  owner_id: "owner-e2e",
  session_id: "session-r1-trace",
  status: "feedback_ready",
  trace_summary: {
    status: "available",
    counts: {
      total: 7,
      interview: 3,
      rag_evidence: 2,
      review_export: 2,
    },
    session_refs: ["session-r1-trace"],
    turn_refs: ["turn-r1-01"],
    answer_refs: ["answer:turn-r1-01"],
    score_refs: ["score:session-r1-trace:r1-score-v1"],
    review_refs: ["review:session-r1-trace:r1-review-v1"],
    export_refs: ["export:session-r1-trace:r0-export-v1"],
    rag: {
      retrieval_query_refs: ["retrieval-query:session-r1-trace:0"],
      retrieval_result_refs: ["retrieval-result:session-r1-trace:0"],
      citation_refs: ["citation:resume-evidence:resume-evidence:chunk-0"],
      evidence_refs: ["evidence:session-r1-trace:resume-evidence"],
      evidence_gap_refs: [
        "gap:no_result",
        "gap:permission_filtered_empty",
        "gap:index_pending",
        "gap:index_failed",
        "gap:rag_unavailable",
      ],
      statuses: ["degraded", "failed", "retryable"],
      citations: [
        {
          citation_ref: "citation:resume-evidence:resume-evidence:chunk-0",
          source_summary: "候选人简历片段",
          chunk_summary: "React 项目经历摘要",
          chunk_index: 0,
          position: "chunk-0",
        },
      ],
    },
    request_refs: [
      {
        trace_type: "interview",
        status: "completed",
        request_id: "request-safe-001",
        operation_id: "interview.detail",
      },
      {
        trace_type: "review_export",
        status: "failed",
        request_id: "request-safe-002",
        operation_id: "export.markdown",
      },
    ],
  },
  export: {
    format: "markdown",
    status: "failed",
    failure_reason: "Markdown export provider retry budget exhausted",
    retryable: true,
  },
  unsafe_debug: {
    full_prompt: "FULL_PROMPT_SHOULD_NOT_RENDER",
    raw_llm_response: "RAW_LLM_RESPONSE_SHOULD_NOT_RENDER",
    provider_secret: "super-secret-token",
    object_storage_path: "s3://private-bucket/raw-export.md",
    invisible_resource_id: "hidden-resource-id",
  },
};

const emptyTracePayload = {
  record_id: "record-empty-trace",
  owner_id: "owner-empty",
  session_id: "session-empty-trace",
  status: "archived",
  trace_summary: {
    status: "empty",
    counts: {
      total: 0,
      interview: 0,
      rag_evidence: 0,
      review_export: 0,
    },
    session_refs: [],
    turn_refs: [],
    answer_refs: [],
    score_refs: [],
    review_refs: [],
    export_refs: [],
    rag: {
      retrieval_query_refs: [],
      retrieval_result_refs: [],
      citation_refs: [],
      evidence_refs: [],
      evidence_gap_refs: [],
      statuses: [],
    },
    request_refs: [],
  },
};

test("面试详情页展示 R1 可信 trace、RAG citation、evidence gap 和 export 状态", async ({
  page,
}) => {
  await page.route("**/api/v1/interviews/session-r1-trace?owner_id=owner-e2e", async (route) => {
    await route.fulfill({ json: trustedTracePayload });
  });

  await page.goto("/interviews/session-r1-trace?owner_id=owner-e2e");

  await expect(page.getByRole("heading", { name: "R1 可信 Trace" })).toBeVisible();
  await expect(page.getByText("trace_summary: available")).toBeVisible();
  await expect(page.getByText("session-r1-trace", { exact: true })).toBeVisible();
  await expect(page.getByText("turn-r1-01", { exact: true })).toBeVisible();
  await expect(page.getByText("answer:turn-r1-01", { exact: true })).toBeVisible();
  await expect(page.getByText("候选人简历片段")).toBeVisible();
  await expect(page.getByText("React 项目经历摘要")).toBeVisible();
  await expect(page.getByText("chunk-0")).toBeVisible();
  await expect(page.getByText("no_result")).toBeVisible();
  await expect(page.getByText("permission_filtered")).toBeVisible();
  await expect(page.getByText("index_pending")).toBeVisible();
  await expect(page.getByText("index_failed")).toBeVisible();
  await expect(page.getByText("rag_unavailable")).toBeVisible();
  await expect(page.getByText("degraded", { exact: true })).toBeVisible();
  await expect(page.getByText("failed", { exact: true })).toBeVisible();
  await expect(page.getByText("retryable", { exact: true })).toBeVisible();
  await expect(page.getByText("score:session-r1-trace:r1-score-v1")).toBeVisible();
  await expect(page.getByText("review:session-r1-trace:r1-review-v1")).toBeVisible();
  await expect(page.getByText("export:session-r1-trace:r0-export-v1")).toBeVisible();
  await expect(page.getByText("Export status: failed")).toBeVisible();
  await expect(page.getByText("可重试")).toBeVisible();
  await expect(page.getByText("Markdown export provider retry budget exhausted")).toBeVisible();

  await expect(page.getByText("FULL_PROMPT_SHOULD_NOT_RENDER")).toHaveCount(0);
  await expect(page.getByText("RAW_LLM_RESPONSE_SHOULD_NOT_RENDER")).toHaveCount(0);
  await expect(page.getByText("super-secret-token")).toHaveCount(0);
  await expect(page.getByText("s3://private-bucket/raw-export.md")).toHaveCount(0);
  await expect(page.getByText("hidden-resource-id")).toHaveCount(0);
});

test("旧记录没有 trace 时展示稳定空态", async ({ page }) => {
  await page.route(
    "**/api/v1/interviews/session-empty-trace?owner_id=owner-empty",
    async (route) => {
      await route.fulfill({ json: emptyTracePayload });
    },
  );

  await page.goto("/interviews/session-empty-trace?owner_id=owner-empty");

  await expect(page.getByRole("heading", { name: "R1 可信 Trace" })).toBeVisible();
  await expect(page.getByText("trace_summary: empty")).toBeVisible();
  await expect(page.getByText("旧记录暂无 trace_summary")).toBeVisible();
  await expect(page.getByText("RAG citation 暂无可展示引用")).toBeVisible();
});

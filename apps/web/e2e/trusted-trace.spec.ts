import { expect, test } from "@playwright/test";

const trustedTracePayload = {
  record_id: "record-r1-trace",
  owner_id: "owner-e2e",
  session_id: "session-r1-trace",
  status: "feedback_ready",
  score: {
    score_total: 82,
    value: 82,
    status: "degraded",
    low_confidence: true,
    low_confidence_reason: "RAG evidence gap 存在，评分可信度降低。",
    dimensions: [
      {
        id: "technical_depth",
        label: "技术深度",
        score: 78,
        reason: "回答说明了 React 项目里的 API 边界和持久化取舍。",
        citation_refs: ["citation:resume-evidence:resume-evidence:chunk-0"],
        evidence_gap_refs: ["gap:no_result"],
        low_confidence: true,
        low_confidence_reason: "引用证据不足",
      },
    ],
    suggestions: ["补充量化结果。"],
    weak_areas: ["风险与不确定性"],
    review_summary: "整体表现稳定，但证据链仍需补齐。",
  },
  review: {
    review_summary: "整体表现稳定，但证据链仍需补齐。",
    suggestions: ["补充量化结果。"],
    weak_areas: ["风险与不确定性"],
    status: "degraded",
    degraded: true,
    retryable: false,
  },
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
    content_version: "r0-export-v1",
    snapshot_ref: "record-r1-trace:export",
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

test("工作台首页作为根路径展示 R1 布局并可进入可信详情", async ({ page }) => {
  await page.route("**/api/v1/interviews?owner_id=owner-e2e", async (route) => {
    await route.fulfill({
      json: {
        items: [
          {
            record_id: "record-r1-trace",
            owner_id: "owner-e2e",
            session_id: "session-r1-trace",
            status: "feedback_ready",
            mode: "r1_trusted",
            turn_index: 1,
            created_at: "2026-05-01T01:00:00Z",
            updated_at: "2026-05-01T03:20:00Z",
            trace_summary: trustedTracePayload.trace_summary,
            unsafe_debug: trustedTracePayload.unsafe_debug,
          },
        ],
      },
    });
  });
  await page.route("**/api/v1/interviews/session-r1-trace?owner_id=owner-e2e", async (route) => {
    await route.fulfill({ json: trustedTracePayload });
  });

  await page.goto("/?owner_id=owner-e2e");

  await expect(page.getByRole("heading", { name: "AI 模拟面试工作台" })).toBeVisible();
  await expect(page.getByText("R1 可信工作台闭环")).toBeVisible();
  const statusTags = page.getByLabel("R1 工作台状态");
  await expect(statusTags.getByText("traceability", { exact: true })).toBeVisible();
  await expect(statusTags.getByText("RAG citation", { exact: true })).toBeVisible();
  await expect(page.getByLabel("可信能力摘要").getByText("evidence gap", { exact: true })).toBeVisible();
  await expect(statusTags.getByText("0-100 scoring", { exact: true })).toBeVisible();
  await expect(page.getByText("trace 7 / RAG 2 / export 2")).toBeVisible();
  await expect(page.getByText("feedback_ready", { exact: true })).toBeVisible();
  await expect(page.getByText("FULL_PROMPT_SHOULD_NOT_RENDER")).toHaveCount(0);
  await expect(page.getByText("W10 首切片 / apps/web mock 原型")).toHaveCount(0);
  await expect(page.getByText("AI 模拟面试首切片原型")).toHaveCount(0);
  await expect(page.getByText("Mock LLM")).toHaveCount(0);
  await expect(page.getByText("单次会话临时数据")).toHaveCount(0);
  await expect(page.getByText("不连接真实 LLM，不做登录或长期保存")).toHaveCount(0);

  await page.getByRole("link", { name: "查看可信详情" }).click();
  await expect(page).toHaveURL(/\/interviews\/session-r1-trace\?owner_id=owner-e2e$/);
  await expect(page.getByRole("heading", { name: "评分 / 复盘详情" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "可信复盘工作区" })).toBeVisible();
  await expect(page.locator(".ant-card").filter({ hasText: "Trace refs" })).toBeVisible();
  await expect(page.locator(".ant-collapse").filter({ hasText: "RAG citation 详情" })).toBeVisible();
  await expect(page.getByText("Evidence gap", { exact: true })).toBeVisible();
  await expect(page.getByText("总分 82")).toBeVisible();
  await expect(page.getByText("Markdown export provider retry budget exhausted")).toBeVisible();
  await expect(page.getByText("FULL_PROMPT_SHOULD_NOT_RENDER")).toHaveCount(0);
  await expect(page.getByText("RAW_LLM_RESPONSE_SHOULD_NOT_RENDER")).toHaveCount(0);
  await expect(page.getByText("super-secret-token")).toHaveCount(0);

  await page.goto("/legacy-mock");
  await expect(page.getByRole("heading", { name: "旧 Mock 原型 / Legacy" })).toBeVisible();
  await expect(page.getByText("AI 模拟面试首切片原型")).toBeVisible();
});

test("工作台首页主入口进入真实页面且不再使用锚点假入口", async ({ page }) => {
  await page.route("**/api/v1/interviews?owner_id=owner-e2e", async (route) => {
    await route.fulfill({ json: { items: [] } });
  });

  await page.goto("/?owner_id=owner-e2e");

  await expect(page.getByRole("heading", { name: "AI 模拟面试工作台" })).toBeVisible();
  const expectedEntries = [
    { name: "发起模拟面试", url: /\/interviews\/new$/ },
    { name: "历史记录", url: /\/interviews$/ },
    { name: "岗位管理", url: /\/jobs$/ },
    { name: "简历管理", url: /\/resumes$/ },
    { name: "复盘", url: /\/reviews$/ },
  ];

  for (const entry of expectedEntries) {
    const action = page.getByTestId(`primary-action-${entry.name}`);
    await expect(action).toHaveAttribute("href", /^(?!#)/);
    await action.click();
    await expect(page).toHaveURL(entry.url);
    await expect(page.getByRole("heading", { name: entry.name })).toBeVisible();
    await page.goto("/?owner_id=owner-e2e");
  }
});

test("面试详情页展示 R1 可信 trace、RAG citation、evidence gap 和 export 状态", async ({
  page,
}) => {
  await page.route("**/api/v1/interviews/session-r1-trace?owner_id=owner-e2e", async (route) => {
    await route.fulfill({ json: trustedTracePayload });
  });

  await page.goto("/interviews/session-r1-trace?owner_id=owner-e2e");

  await expect(page.getByRole("heading", { name: "评分 / 复盘详情" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "可信复盘工作区" })).toBeVisible();
  await expect(page.locator(".ant-card").filter({ hasText: "Trace refs" })).toBeVisible();
  await expect(page.locator(".ant-collapse").filter({ hasText: "RAG citation 详情" })).toBeVisible();
  await expect(page.getByText("trace_summary: available")).toBeVisible();
  await expect(page.getByText("总分 82")).toBeVisible();
  await expect(page.getByText("技术深度")).toBeVisible();
  await expect(page.getByText("回答说明了 React 项目里的 API 边界和持久化取舍。")).toBeVisible();
  await expect(page.getByText("RAG evidence gap 存在，评分可信度降低。")).toBeVisible();
  await expect(page.getByText("补充量化结果。")).toBeVisible();
  await expect(page.getByText("风险与不确定性")).toBeVisible();
  await expect(page.getByText("整体表现稳定，但证据链仍需补齐。")).toBeVisible();
  await expect(page.getByText("session-r1-trace", { exact: true })).toBeVisible();
  await expect(page.getByText("turn-r1-01", { exact: true })).toBeVisible();
  await expect(page.getByText("answer:turn-r1-01", { exact: true })).toBeVisible();
  await expect(page.getByText("候选人简历片段")).toBeVisible();
  await expect(page.getByText("React 项目经历摘要")).toBeVisible();
  await expect(page.getByText("chunk-0", { exact: true })).toBeVisible();
  await expect(page.getByText("no_result", { exact: true })).toBeVisible();
  await expect(page.getByText("permission_filtered", { exact: true })).toBeVisible();
  await expect(page.getByText("index_pending", { exact: true })).toBeVisible();
  await expect(page.getByText("index_failed", { exact: true })).toBeVisible();
  await expect(page.getByText("rag_unavailable", { exact: true })).toBeVisible();
  await expect(page.getByText("degraded", { exact: true })).toBeVisible();
  await expect(page.getByText("failed", { exact: true })).toBeVisible();
  await expect(page.getByText("retryable", { exact: true })).toBeVisible();
  await expect(page.getByText("score:session-r1-trace:r1-score-v1")).toBeVisible();
  await expect(page.getByText("review:session-r1-trace:r1-review-v1")).toBeVisible();
  await expect(page.getByText("export:session-r1-trace:r0-export-v1")).toBeVisible();
  await expect(page.getByText("Export status: failed")).toBeVisible();
  await expect(page.getByText("content_version: r0-export-v1")).toBeVisible();
  await expect(page.getByText("snapshot_ref: record-r1-trace:export")).toBeVisible();
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

  await expect(page.getByRole("heading", { name: "评分 / 复盘详情" })).toBeVisible();
  await expect(page.getByText("trace_summary: empty")).toBeVisible();
  await expect(page.getByText("旧记录暂无评分复盘")).toBeVisible();
  await expect(page.getByText("暂无评分维度")).toBeVisible();
  await expect(page.locator(".ant-empty").filter({ hasText: "旧记录暂无 trace_summary" })).toBeVisible();
  await expect(page.getByText("旧记录暂无 trace_summary")).toBeVisible();
  await expect(page.getByText("RAG citation 暂无可展示引用")).toBeVisible();
});

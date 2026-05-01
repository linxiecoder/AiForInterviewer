import assert from "node:assert/strict";
import test from "node:test";

import { buildTrustedTraceViewModel } from "./traceViewModel.js";
import type { TrustedInterviewDetail } from "./traceTypes.js";

test("buildTrustedTraceViewModel normalizes trusted trace refs and evidence gaps", () => {
  const detail: TrustedInterviewDetail = {
    session_id: "session-r1",
    score: {
      score_total: 82,
      status: "degraded",
      low_confidence: true,
      low_confidence_reason: "存在 evidence gap",
      dimensions: [
        {
          id: "technical_depth",
          label: "技术深度",
          score: 78,
          reason: "回答覆盖了 API 和持久化权衡。",
          citation_refs: ["citation:resume:resume:chunk-0"],
          evidence_gap_refs: ["gap:permission_filtered_empty"],
          low_confidence: true,
          low_confidence_reason: "引用不足",
        },
      ],
      suggestions: ["补充结果指标。"],
      weak_areas: ["风险与不确定性"],
      review_summary: "整体表现稳定。",
    },
    review: {
      review_summary: "整体表现稳定。",
      suggestions: ["补充结果指标。"],
      weak_areas: ["风险与不确定性"],
      status: "degraded",
      degraded: true,
      retryable: false,
    },
    trace_summary: {
      status: "available",
      counts: { total: 1, interview: 1, rag_evidence: 0, review_export: 0 },
      session_refs: ["session-r1"],
      turn_refs: ["turn-r1"],
      answer_refs: ["answer:turn-r1"],
      score_refs: ["score:session-r1"],
      review_refs: ["review:session-r1"],
      export_refs: ["export:session-r1"],
      rag: {
        retrieval_query_refs: [],
        retrieval_result_refs: [],
        citation_refs: ["citation:resume:resume:chunk-0"],
        evidence_refs: [],
        evidence_gap_refs: ["gap:permission_filtered_empty"],
        statuses: ["degraded"],
      },
      request_refs: [{ trace_type: "interview", status: "completed", operation_id: "detail" }],
    },
    export: {
      status: "failed",
      retryable: true,
      failure_reason: "export failed",
      content_version: "r0-export-v1",
      snapshot_ref: "record-r1:export",
    },
  };

  const viewModel = buildTrustedTraceViewModel(detail);

  assert.equal(viewModel.traceStatus, "available");
  assert.deepEqual(viewModel.evidenceGapLabels, ["permission_filtered"]);
  assert.equal(viewModel.citationItems[0]?.chunkIndex, "0");
  assert.ok(viewModel.statusLabels.includes("degraded"));
  assert.ok(viewModel.statusLabels.includes("retryable"));
  assert.equal(viewModel.exportStatus, "failed");
  assert.deepEqual(viewModel.exportMetadata, ["content_version: r0-export-v1", "snapshot_ref: record-r1:export"]);
  assert.equal(viewModel.scoreTotal, 82);
  assert.equal(viewModel.scoreStatus, "degraded");
  assert.equal(viewModel.lowConfidence, true);
  assert.equal(viewModel.dimensionItems[0]?.label, "技术深度");
  assert.equal(viewModel.dimensionItems[0]?.reason, "回答覆盖了 API 和持久化权衡。");
  assert.deepEqual(viewModel.suggestions, ["补充结果指标。"]);
  assert.deepEqual(viewModel.weakAreas, ["风险与不确定性"]);
  assert.equal(viewModel.reviewSummary, "整体表现稳定。");
});

test("buildTrustedTraceViewModel keeps legacy empty trace stable", () => {
  const viewModel = buildTrustedTraceViewModel({ session_id: "session-empty" });

  assert.equal(viewModel.traceStatus, "empty");
  assert.equal(viewModel.isEmptyTrace, true);
  assert.deepEqual(viewModel.sessionRefs, ["session-empty"]);
  assert.deepEqual(viewModel.citationItems, []);
  assert.equal(viewModel.scoreTotal, undefined);
  assert.deepEqual(viewModel.dimensionItems, []);
});

test("buildTrustedTraceViewModel keeps legacy score value and pending failed statuses stable", () => {
  const viewModel = buildTrustedTraceViewModel({
    session_id: "session-legacy-score",
    score: {
      value: 64,
      status: "pending",
    },
    review: {
      summary: "旧记录复盘可读。",
      status: "failed",
      degraded: true,
      retryable: true,
    },
  });

  assert.equal(viewModel.scoreTotal, 64);
  assert.equal(viewModel.scoreStatus, "pending");
  assert.equal(viewModel.lowConfidence, true);
  assert.equal(viewModel.reviewSummary, "旧记录复盘可读。");
  assert.ok(viewModel.statusLabels.includes("pending"));
  assert.ok(viewModel.statusLabels.includes("failed"));
  assert.ok(viewModel.statusLabels.includes("retryable"));
  assert.deepEqual(viewModel.dimensionItems, []);
});

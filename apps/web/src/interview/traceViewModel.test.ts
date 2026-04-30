import assert from "node:assert/strict";
import test from "node:test";

import { buildTrustedTraceViewModel } from "./traceViewModel.js";
import type { TrustedInterviewDetail } from "./traceTypes.js";

test("buildTrustedTraceViewModel normalizes trusted trace refs and evidence gaps", () => {
  const detail: TrustedInterviewDetail = {
    session_id: "session-r1",
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
    export: { status: "failed", retryable: true, failure_reason: "export failed" },
  };

  const viewModel = buildTrustedTraceViewModel(detail);

  assert.equal(viewModel.traceStatus, "available");
  assert.deepEqual(viewModel.evidenceGapLabels, ["permission_filtered"]);
  assert.equal(viewModel.citationItems[0]?.chunkIndex, "0");
  assert.ok(viewModel.statusLabels.includes("degraded"));
  assert.ok(viewModel.statusLabels.includes("retryable"));
  assert.equal(viewModel.exportStatus, "failed");
});

test("buildTrustedTraceViewModel keeps legacy empty trace stable", () => {
  const viewModel = buildTrustedTraceViewModel({ session_id: "session-empty" });

  assert.equal(viewModel.traceStatus, "empty");
  assert.equal(viewModel.isEmptyTrace, true);
  assert.deepEqual(viewModel.sessionRefs, ["session-empty"]);
  assert.deepEqual(viewModel.citationItems, []);
});

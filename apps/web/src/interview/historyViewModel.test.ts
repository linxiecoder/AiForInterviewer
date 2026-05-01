import assert from "node:assert/strict";
import test from "node:test";

import { buildHistoryViewModel } from "./historyViewModel.js";
import type { InterviewHistoryResponse } from "./traceTypes.js";

test("buildHistoryViewModel maps real history contract into safe recent records", () => {
  const response: InterviewHistoryResponse = {
    items: [
      {
        record_id: "record-r1-history",
        session_id: "session-r1-history",
        owner_id: "owner-history",
        status: "feedback_ready",
        mode: "r1_trusted",
        turn_index: 2,
        created_at: "2026-05-01T01:00:00Z",
        updated_at: "2026-05-01T03:20:00Z",
        trace_summary: {
          status: "available",
          counts: { total: 4, interview: 2, rag_evidence: 1, review_export: 1 },
          session_refs: ["session-r1-history"],
          turn_refs: ["turn-r1-01"],
          answer_refs: ["answer:turn-r1-01"],
          score_refs: ["score:session-r1-history:r1-score-v1"],
          review_refs: ["review:session-r1-history:r1-review-v1"],
          export_refs: ["export:session-r1-history:r0-export-v1"],
          rag: {
            retrieval_query_refs: [],
            retrieval_result_refs: [],
            citation_refs: ["citation:resume:chunk-0"],
            evidence_refs: [],
            evidence_gap_refs: ["gap:no_result"],
            statuses: ["degraded", "retryable"],
          },
          request_refs: [],
        },
        unsafe_debug: {
          full_prompt: "FULL_PROMPT_SHOULD_NOT_RENDER",
          raw_llm_response: "RAW_LLM_RESPONSE_SHOULD_NOT_RENDER",
          provider_secret: "super-secret-token",
          object_storage_path: "s3://private-bucket/raw-export.md",
          invisible_resource_id: "hidden-resource-id",
        },
      },
    ],
  };

  const viewModel = buildHistoryViewModel(response, "owner-history");

  assert.equal(viewModel.items.length, 1);
  assert.equal(viewModel.items[0]?.sessionId, "session-r1-history");
  assert.equal(viewModel.items[0]?.ownerId, "owner-history");
  assert.equal(viewModel.items[0]?.href, "/interviews/session-r1-history?owner_id=owner-history");
  assert.equal(viewModel.items[0]?.status, "feedback_ready");
  assert.equal(viewModel.items[0]?.traceStatus, "available");
  assert.equal(viewModel.items[0]?.traceCountLabel, "trace 4 / RAG 1 / export 1");
  assert.deepEqual(viewModel.items[0]?.statusLabels, ["degraded", "retryable"]);
  assert.deepEqual(viewModel.items[0]?.evidenceGapLabels, ["no_result"]);
  assert.equal(viewModel.items[0]?.updatedAt, "2026-05-01T03:20:00Z");
  const serialized = JSON.stringify(viewModel);
  assert.equal(serialized.includes("FULL_PROMPT_SHOULD_NOT_RENDER"), false);
  assert.equal(serialized.includes("RAW_LLM_RESPONSE_SHOULD_NOT_RENDER"), false);
  assert.equal(serialized.includes("super-secret-token"), false);
  assert.equal(serialized.includes("s3://private-bucket/raw-export.md"), false);
  assert.equal(serialized.includes("hidden-resource-id"), false);
});

test("buildHistoryViewModel keeps empty and old history records stable", () => {
  const viewModel = buildHistoryViewModel(
    {
      items: [
        {
          session_id: "session-old",
          owner_id: "owner-old",
          status: "archived",
          updated_at: "2026-04-30T09:00:00Z",
        },
      ],
    },
    "owner-old",
  );

  assert.equal(viewModel.isEmpty, false);
  assert.equal(viewModel.items[0]?.traceStatus, "empty");
  assert.equal(viewModel.items[0]?.traceCountLabel, "trace 0 / RAG 0 / export 0");
  assert.deepEqual(viewModel.items[0]?.statusLabels, []);
  assert.deepEqual(viewModel.items[0]?.evidenceGapLabels, []);
});

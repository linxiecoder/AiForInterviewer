import type { InterviewHistoryResponse, TraceSummary } from "./traceTypes.js";

export interface HistoryRecordViewItem {
  key: string;
  sessionId: string;
  ownerId: string;
  href: string;
  title: string;
  status: string;
  mode: string;
  turnIndex: number;
  updatedAt: string;
  traceStatus: string;
  traceCountLabel: string;
  statusLabels: string[];
  evidenceGapLabels: string[];
}

export interface HistoryViewModel {
  ownerId: string;
  isEmpty: boolean;
  items: HistoryRecordViewItem[];
}

export function buildHistoryViewModel(
  response: InterviewHistoryResponse,
  ownerId: string,
): HistoryViewModel {
  const items = (response.items ?? [])
    .map((item, index): HistoryRecordViewItem | undefined => {
      const sessionId = normalizeString(item.session_id);
      if (!sessionId) {
        return undefined;
      }
      const recordOwnerId = normalizeString(item.owner_id) || ownerId;
      const traceSummary = item.trace_summary ?? emptyTraceSummary(sessionId);
      const rag = traceSummary.rag ?? emptyTraceSummary(sessionId).rag;
      const counts = traceSummary.counts ?? emptyTraceSummary(sessionId).counts;

      return {
        key: normalizeString(item.record_id) || sessionId || `history-${index}`,
        sessionId,
        ownerId: recordOwnerId,
        href: `/interviews/${encodeURIComponent(sessionId)}?owner_id=${encodeURIComponent(recordOwnerId)}`,
        title: `模拟记录 ${sessionId}`,
        status: normalizeString(item.status) || "unknown",
        mode: normalizeString(item.mode) || "unknown",
        turnIndex: typeof item.turn_index === "number" ? item.turn_index : 0,
        updatedAt: normalizeString(item.updated_at) || normalizeString(item.created_at) || "unknown",
        traceStatus: normalizeString(traceSummary.status) || "empty",
        traceCountLabel: `trace ${counts.total ?? 0} / RAG ${counts.rag_evidence ?? 0} / export ${
          counts.review_export ?? 0
        }`,
        statusLabels: buildStatusLabels(traceSummary),
        evidenceGapLabels: uniqueStrings(rag.evidence_gap_refs.map(normalizeEvidenceGapRef)),
      };
    })
    .filter((item): item is HistoryRecordViewItem => Boolean(item));

  return {
    ownerId,
    isEmpty: items.length === 0,
    items,
  };
}

function emptyTraceSummary(sessionId: string): TraceSummary {
  return {
    status: "empty",
    counts: {
      total: 0,
      interview: 0,
      rag_evidence: 0,
      review_export: 0,
    },
    session_refs: sessionId ? [sessionId] : [],
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
  };
}

function buildStatusLabels(traceSummary: TraceSummary): string[] {
  const degradedStatuses = new Set([
    "degraded",
    "failed",
    "retryable",
    "index_pending",
    "index_failed",
    "rag_unavailable",
  ]);
  const rag = traceSummary.rag ?? emptyTraceSummary("").rag;
  return uniqueStrings([
    ...rag.statuses.filter((status) => degradedStatuses.has(status)),
    ...traceSummary.request_refs
      .map((item) => item.status)
      .filter((status): status is string => Boolean(status && degradedStatuses.has(status))),
  ]);
}

function normalizeEvidenceGapRef(value: string | undefined): string | undefined {
  const normalized = value?.replace(/^gap:/, "").replace("_empty", "");
  return normalized || undefined;
}

function normalizeString(value: unknown): string {
  return typeof value === "string" ? value.trim() : "";
}

function uniqueStrings(values: Array<string | undefined>): string[] {
  const result: string[] = [];
  for (const value of values) {
    const normalized = value?.trim();
    if (normalized && !result.includes(normalized)) {
      result.push(normalized);
    }
  }
  return result;
}

import type {
  RagCitationSummary,
  ScoreDimension,
  TraceSummary,
  TrustedInterviewDetail,
} from "./traceTypes.js";

export interface CitationViewItem {
  key: string;
  sourceSummary: string;
  chunkSummary: string;
  chunkIndex: string;
  position: string;
}

export interface TrustedTraceViewModel {
  traceStatus: string;
  isEmptyTrace: boolean;
  scoreTotal?: number;
  scoreStatus: string;
  lowConfidence: boolean;
  lowConfidenceReason: string;
  dimensionItems: DimensionViewItem[];
  reviewSummary: string;
  suggestions: string[];
  weakAreas: string[];
  counts: Array<{ label: string; value: number }>;
  sessionRefs: string[];
  turnRefs: string[];
  answerRefs: string[];
  scoreRefs: string[];
  reviewRefs: string[];
  exportRefs: string[];
  citationItems: CitationViewItem[];
  evidenceGapLabels: string[];
  statusLabels: string[];
  requestRefs: Array<{ key: string; label: string }>;
  exportStatus: string;
  exportFailureReason: string;
  exportRetryable: boolean;
}

export interface DimensionViewItem {
  key: string;
  label: string;
  score?: number;
  reason: string;
  citationRefs: string[];
  evidenceGapRefs: string[];
  lowConfidence: boolean;
  lowConfidenceReason: string;
}

const emptyTraceSummary = (sessionId: string): TraceSummary => ({
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
});

export function buildTrustedTraceViewModel(detail: TrustedInterviewDetail): TrustedTraceViewModel {
  const traceSummary = detail.trace_summary ?? emptyTraceSummary(detail.session_id);
  const rag = traceSummary.rag ?? emptyTraceSummary(detail.session_id).rag;
  const exportSummary = detail.export ?? {};
  const score = detail.score ?? {};
  const review = detail.review ?? {};
  const scoreTotal = normalizeScoreTotal(score.score_total ?? score.value ?? review.score_total);
  const lowConfidence = Boolean(score.low_confidence) || Boolean(review.degraded);
  const statusLabels = uniqueStrings([
    traceSummary.status,
    score.status,
    review.status,
    lowConfidence ? "low_confidence" : undefined,
    ...rag.statuses,
    ...traceSummary.request_refs.map((item) => item.status),
    exportSummary.status,
    review.retryable ? "retryable" : undefined,
    exportSummary.retryable ? "retryable" : undefined,
  ]);

  return {
    traceStatus: traceSummary.status,
    isEmptyTrace: traceSummary.status === "empty" || traceSummary.counts.total === 0,
    scoreTotal,
    scoreStatus: score.status ?? review.status ?? "empty",
    lowConfidence,
    lowConfidenceReason: score.low_confidence_reason ?? "",
    dimensionItems: buildDimensionItems(score.dimensions ?? review.dimensions),
    reviewSummary: review.review_summary ?? review.summary ?? score.review_summary ?? "",
    suggestions: safeStringList(review.suggestions ?? score.suggestions),
    weakAreas: safeStringList(review.weak_areas ?? score.weak_areas),
    counts: [
      { label: "total", value: traceSummary.counts.total },
      { label: "interview", value: traceSummary.counts.interview },
      { label: "rag_evidence", value: traceSummary.counts.rag_evidence },
      { label: "review_export", value: traceSummary.counts.review_export },
    ],
    sessionRefs: safeList(traceSummary.session_refs, detail.session_id ? [detail.session_id] : []),
    turnRefs: safeList(traceSummary.turn_refs),
    answerRefs: safeList(traceSummary.answer_refs),
    scoreRefs: safeList(traceSummary.score_refs),
    reviewRefs: safeList(traceSummary.review_refs),
    exportRefs: safeList(traceSummary.export_refs),
    citationItems: buildCitationItems(rag.citations, rag.citation_refs),
    evidenceGapLabels: uniqueStrings(rag.evidence_gap_refs.map(normalizeEvidenceGapRef)),
    statusLabels,
    requestRefs: traceSummary.request_refs.map((item, index) => ({
      key: `${item.trace_type ?? "trace"}-${item.operation_id ?? index}`,
      label: [item.trace_type, item.status, item.operation_id, item.request_id]
        .filter((value): value is string => Boolean(value))
        .join(" / "),
    })),
    exportStatus: exportSummary.status ?? "empty",
    exportFailureReason: exportSummary.failure_reason ?? "none",
    exportRetryable: Boolean(exportSummary.retryable),
  };
}

function buildDimensionItems(dimensions: ScoreDimension[] | undefined): DimensionViewItem[] {
  if (!dimensions) {
    return [];
  }
  return dimensions.map((dimension, index) => ({
    key: dimension.id ?? `dimension-${index}`,
    label: dimension.label ?? dimension.id ?? `dimension-${index + 1}`,
    score: normalizeScoreTotal(dimension.score),
    reason: dimension.reason ?? "暂无 reason",
    citationRefs: safeStringList(dimension.citation_refs),
    evidenceGapRefs: safeStringList(dimension.evidence_gap_refs),
    lowConfidence: Boolean(dimension.low_confidence),
    lowConfidenceReason: dimension.low_confidence_reason ?? "",
  }));
}

function buildCitationItems(
  citations: RagCitationSummary[] | undefined,
  citationRefs: string[],
): CitationViewItem[] {
  if (citations && citations.length > 0) {
    return citations.map((citation, index) => {
      const fallback = parseCitationRef(citation.citation_ref ?? citationRefs[index] ?? "");
      const chunkIndex =
        typeof citation.chunk_index === "number" ? String(citation.chunk_index) : fallback.chunkIndex;

      return {
        key: citation.citation_ref ?? fallback.key,
        sourceSummary: citation.source_summary ?? fallback.sourceSummary,
        chunkSummary: citation.chunk_summary ?? fallback.chunkSummary,
        chunkIndex,
        position: citation.position ?? fallback.position,
      };
    });
  }

  return citationRefs.map((citationRef) => parseCitationRef(citationRef));
}

function parseCitationRef(citationRef: string): CitationViewItem {
  const safeRef = citationRef.trim();
  const withoutPrefix = safeRef.replace(/^citation:/, "");
  const parts = withoutPrefix.split(":").filter(Boolean);
  const source = parts[0] ?? "unknown-source";
  const chunk = parts[parts.length - 1] ?? "chunk-unknown";
  const chunkMatch = chunk.match(/chunk-(\d+)/);

  return {
    key: safeRef || "citation-empty",
    sourceSummary: source,
    chunkSummary: safeRef || "citation ref unavailable",
    chunkIndex: chunkMatch?.[1] ?? "unknown",
    position: chunk,
  };
}

function normalizeEvidenceGapRef(value: string | undefined): string | undefined {
  const normalized = value?.replace(/^gap:/, "").replace("_empty", "");
  return normalized || undefined;
}

function safeList(values: string[] | undefined, fallback: string[] = []): string[] {
  return values && values.length > 0 ? values : fallback;
}

function safeStringList(values: string[] | undefined): string[] {
  return values && values.length > 0 ? values : [];
}

function normalizeScoreTotal(value: number | undefined): number | undefined {
  return typeof value === "number" && Number.isFinite(value) ? value : undefined;
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

export interface TraceCounts {
  total: number;
  interview: number;
  rag_evidence: number;
  review_export: number;
}

export interface TraceRequestRef {
  trace_type?: string;
  status?: string;
  request_id?: string;
  operation_id?: string;
}

export interface RagCitationSummary {
  citation_ref?: string;
  source_summary?: string;
  chunk_summary?: string;
  chunk_index?: number;
  position?: string;
}

export interface RagTraceSummary {
  retrieval_query_refs: string[];
  retrieval_result_refs: string[];
  citation_refs: string[];
  evidence_refs: string[];
  evidence_gap_refs: string[];
  statuses: string[];
  citations?: RagCitationSummary[];
}

export interface TraceSummary {
  status: "empty" | "available" | string;
  counts: TraceCounts;
  session_refs: string[];
  turn_refs: string[];
  answer_refs: string[];
  score_refs: string[];
  review_refs: string[];
  export_refs: string[];
  rag: RagTraceSummary;
  request_refs: TraceRequestRef[];
}

export interface MarkdownExportSummary {
  format?: string;
  status?: string;
  failure_reason?: string;
  retryable?: boolean;
}

export interface TrustedInterviewDetail {
  record_id?: string;
  owner_id?: string;
  session_id: string;
  status?: string;
  trace_summary?: TraceSummary;
  export?: MarkdownExportSummary;
}

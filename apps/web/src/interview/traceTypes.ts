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
  [key: string]: unknown;
  format?: string;
  status?: string;
  content_version?: string;
  snapshot_ref?: string;
  failure_reason?: string;
  retryable?: boolean;
  metadata?: Record<string, unknown>;
}

export interface ScoreDimension {
  id?: string;
  label?: string;
  score?: number;
  reason?: string;
  evidence_refs?: string[];
  citation_refs?: string[];
  evidence_gap_refs?: string[];
  low_confidence?: boolean;
  low_confidence_reason?: string;
}

export interface ScoreSummary {
  value?: number;
  score_total?: number;
  dimensions?: ScoreDimension[];
  status?: string;
  low_confidence?: boolean;
  low_confidence_reason?: string;
  suggestions?: string[];
  weak_areas?: string[];
  review_summary?: string;
}

export interface ReviewSummary {
  summary?: string;
  review_summary?: string;
  score_total?: number;
  dimensions?: ScoreDimension[];
  suggestions?: string[];
  weak_areas?: string[];
  citation_refs?: string[];
  evidence_gap_refs?: string[];
  status?: string;
  degraded?: boolean;
  retryable?: boolean;
}

export interface TrustedInterviewDetail {
  [key: string]: unknown;
  record_id?: string;
  owner_id?: string;
  session_id: string;
  status?: string;
  trace_summary?: TraceSummary;
  score?: ScoreSummary;
  review?: ReviewSummary;
  export?: MarkdownExportSummary;
}

export interface InterviewHistoryItem {
  [key: string]: unknown;
  record_id?: string;
  owner_id?: string;
  session_id?: string;
  status?: string;
  mode?: string;
  turn_index?: number;
  created_at?: string;
  updated_at?: string;
  trace_summary?: TraceSummary;
}

export interface InterviewHistoryResponse {
  [key: string]: unknown;
  items?: InterviewHistoryItem[];
}

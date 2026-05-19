export type VersionRef = {
  resource_type: string;
  resource_id: string;
  version_id: string;
};

export interface JobBindingSummary {
  status: "bound" | "not_bound";
  resume_job_binding_id?: string | null;
  resume_id?: string | null;
  resume_title?: string | null;
  resume_version_ref?: VersionRef | null;
  bound_at?: string | null;
}

export interface JobMatchSummary {
  status: string;
  analysis_id?: string | null;
  display_score?: number | null;
  score_scale?: string | null;
  score_version?: string | null;
  rubric_version?: string | null;
  confidence_level?: string | null;
  summary_text?: string | null;
  generated_at?: string | null;
  stale_reason?: string | null;
}

export type JobMatchOverallLevel =
  | "strong_match"
  | "medium_match"
  | "weak_match"
  | "insufficient_evidence";

export type JobMatchConfidence = "high" | "medium" | "low" | "insufficient";

export type JobMatchDimensionKey =
  | "requirement_alignment"
  | "experience_evidence"
  | "skill_coverage"
  | "gap_risk"
  | "readiness_actions";

export interface JobMatchEvidenceRef {
  chunk_id: string;
  quote?: string | null;
}

export interface JobMatchDimensionScore {
  key: JobMatchDimensionKey;
  score: number;
  max_score: number;
  rationale: string;
  supporting_evidence: JobMatchEvidenceRef[];
  gaps: string[];
  confidence: JobMatchConfidence;
}

export interface JobMatchMatchedRequirement {
  requirement_chunk_id: string;
  resume_evidence_chunk_ids: string[];
  rationale: string;
  confidence: JobMatchConfidence;
}

export interface JobMatchMissingRequirement {
  requirement_chunk_id?: string | null;
  reason: string;
  confidence: JobMatchConfidence;
  evidence_insufficient?: boolean;
}

export interface JobMatchResumeEvidence {
  chunk_id: string;
  summary: string;
  confidence: JobMatchConfidence;
}

export interface JobMatchRiskFlag {
  risk_type: string;
  description: string;
  severity: "low" | "medium" | "high";
  supporting_evidence: JobMatchEvidenceRef[];
}

export interface JobMatchResultPayload {
  overall_score: number;
  overall_level: JobMatchOverallLevel;
  confidence: JobMatchConfidence;
  summary: string;
  dimension_scores: JobMatchDimensionScore[];
  matched_requirements: JobMatchMatchedRequirement[];
  missing_requirements: JobMatchMissingRequirement[];
  resume_evidence: JobMatchResumeEvidence[];
  risk_flags: JobMatchRiskFlag[];
  interview_focus: string[];
  suggested_questions: string[];
  markdown_report: string;
}

export interface CreateJobMatchAnalysisRequest {
  resume_job_binding_id: string;
}

export interface JobMatchAnalysis {
  analysis_id: string;
  resume_job_binding_id: string;
  resume_id: string;
  resume_version_id: string;
  job_id: string;
  job_version_id: string;
  status: "completed" | "failed";
  overall_score: number | null;
  overall_level: JobMatchOverallLevel | null;
  confidence: JobMatchConfidence | null;
  result_payload: JobMatchResultPayload;
  markdown_report_text?: string | null;
  score_rule_version: string;
  prompt_version: string;
  model_name: string;
  source_digest: string;
  created_at: string;
  updated_at: string;
}

export interface JobSummary {
  job_id: string;
  title: string;
  company: string | null;
  department: string | null;
  application_status: string;
  current_version_ref: VersionRef;
  archived_at: string | null;
  binding_summary: JobBindingSummary;
  latest_match_summary: JobMatchSummary;
  status: string;
  record_version: number;
  created_at: string;
  updated_at: string;
}

export interface JobDetail extends JobSummary {
  department: string | null;
  responsibilities: string[];
  requirements: string[];
  other_notes: string | null;
}

export interface JobCreateRequest {
  title: string;
  company?: string | null;
  department?: string | null;
  responsibilities: string[];
  requirements: string[];
  other_notes?: string | null;
  application_status?: string;
}

export interface JobUpdateRequest {
  title?: string;
  company?: string | null;
  department?: string | null;
  responsibilities?: string[];
  requirements?: string[];
  other_notes?: string | null;
  application_status?: string;
  status?: string;
  base_version_ref?: VersionRef;
  record_version?: number;
}

export interface CreateBindingRequest {
  resume_id: string;
  job_id: string;
  resume_version_id?: string;
  job_version_id?: string;
}

export interface DeleteBindingRequest {
  base_version_ref?: VersionRef;
  record_version?: number;
  reason?: string;
}

export interface JobResumeBinding {
  binding_id: string;
  resume_ref: VersionRef;
  job_ref: VersionRef;
  binding_status: string;
  created_at: string;
  unbound_at: string | null;
  unbound_by: { owner_id: string } | null;
  record_version: number;
  resume_job_binding_id: string | null;
}

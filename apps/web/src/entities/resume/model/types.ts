import { VersionRef } from "../../job/model/types";

export interface ResumeScoreSummary {
  status?: string | null;
  display_score?: number | null;
  score_scale?: string | null;
  generated_at?: string | null;
}

export interface ResumeSummary {
  resume_id: string;
  title: string | null;
  updated_at: string;
  status?: string | null;
  current_version_ref: VersionRef;
  current_version_id?: string | null;
  file_name?: string | null;
  created_at: string;
  binding_eligible?: boolean;
  latest_version_summary?: string | null;
  latest_score_summary?: ResumeScoreSummary | null;
}

export interface ResumeDetail extends ResumeSummary {
  markdown_text: string;
  derived_outline?: Record<string, unknown> | null;
}

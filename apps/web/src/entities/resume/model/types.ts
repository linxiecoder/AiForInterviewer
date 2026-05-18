import { VersionRef } from "../../job/model/types";

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
}

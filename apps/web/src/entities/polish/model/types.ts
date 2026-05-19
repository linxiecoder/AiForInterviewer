export interface PolishSessionSummary {
  id: string;
  session_id: string;
  title: string;
  mode: "polish";
  status: string;
  resume_job_binding_id: string;
  resume_id: string;
  resume_version_id: string;
  job_id: string;
  job_version_id: string;
  topic_id?: string | null;
  subtopic_id?: string | null;
  custom_topic_text_summary?: string | null;
  created_at: string;
  updated_at: string;
}

export type AssetRef = Record<string, unknown> & {
  resource_type?: string;
  resource_id?: string;
  version_id?: string;
  label?: string;
};

export type AssetStatus =
  | "asset_candidate_generated"
  | "asset_confirmed"
  | "asset_rejected"
  | "asset_archived"
  | "superseded"
  | "disabled"
  | (string & {});

export interface AssetVersion {
  asset_version_id: string;
  asset_id: string;
  status: string;
  version_number: number;
  content?: string | null;
  edit_summary?: string | null;
  created_by_actor_id?: string | null;
  created_from_candidate_id?: string | null;
  created_at: string;
  updated_at: string;
}

export interface AssetSummary {
  asset_id: string;
  owner_id: string;
  status: AssetStatus;
  asset_type?: string | null;
  title?: string | null;
  summary?: string | null;
  current_version_id?: string | null;
  source_refs: AssetRef[];
  evidence_refs: AssetRef[];
  trace_refs: AssetRef[];
  resume_version_ref?: AssetRef | null;
  job_version_ref?: AssetRef | null;
  question_pattern?: string | null;
  created_from_candidate_id?: string | null;
  user_confirmation_ref?: AssetRef | null;
  fact_source?: string | null;
  created_at: string;
  updated_at: string;
}

export interface AssetDetail extends AssetSummary {
  content?: string | null;
  versions: AssetVersion[];
}

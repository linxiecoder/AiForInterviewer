export type WeaknessRef = Record<string, unknown> & {
  resource_type?: string;
  resource_id?: string;
  version_id?: string;
  label?: string;
};

export type WeaknessStatus =
  | "weakness_detected"
  | "weakness_confirmed"
  | "low_priority"
  | "ignored"
  | "resolved"
  | "reopened"
  | (string & {});

export type WeaknessSeverity = "low" | "medium" | "high" | "critical" | (string & {});

export interface WeaknessRelatedRefs {
  sessions?: WeaknessRef[];
  feedback?: WeaknessRef[];
  questions?: WeaknessRef[];
  answers?: WeaknessRef[];
  loss_points?: WeaknessRef[];
  repeated_loss_points?: WeaknessRef[];
}

export interface WeaknessSummary {
  weakness_id: string;
  owner_id: string;
  status: WeaknessStatus;
  title?: string | null;
  summary?: string | null;
  severity?: WeaknessSeverity | null;
  confidence_level?: string | null;
  dimension?: string | null;
  source_refs: WeaknessRef[];
  evidence_refs: WeaknessRef[];
  trace_refs: WeaknessRef[];
  occurrence_count: number;
  first_seen_at?: string | null;
  last_seen_at?: string | null;
  archived_at?: string | null;
  created_from_candidate_id?: string | null;
  user_confirmation_ref?: WeaknessRef | null;
  suggested_training_actions: string[];
  created_at: string;
  updated_at: string;
}

export interface WeaknessDetail extends WeaknessSummary {
  related_refs: WeaknessRelatedRefs;
}

-- ST13_20 R0 minimal persistence schema.
-- Scope: stores one simulated interview record payload for save, restore,
-- history listing, review readback, and export traceability metadata.
-- Out of scope: complete business database design, full migration framework,
-- ORM mapping, LLM/RAG provider data, frontend state, and R1/R2 training or
-- asset lifecycle records.

-- Table purpose:
-- interview_records keeps the smallest durable record needed by the R0 main
-- path. The payload_json column stores the current minimal structured payload
-- while stable metadata columns support ownership, restore lookup, history
-- listing, and export traceability.
CREATE TABLE IF NOT EXISTS interview_records (
    -- Stable restore key returned by the API after save.
    id TEXT PRIMARY KEY,
    -- Minimal ownership boundary for later permission filtering.
    owner_id TEXT NOT NULL,
    -- Traceability source for save/review/export provenance.
    source TEXT NOT NULL,
    -- Content contract version for future compatibility checks.
    version INTEGER NOT NULL,
    -- JSON payload containing job/resume/interview/review/export fragments.
    payload_json TEXT NOT NULL,
    -- Creation time used by history and export traceability.
    created_at TEXT NOT NULL,
    -- Last persistence update time; R0 only writes it at create time.
    updated_at TEXT NOT NULL
);

-- History listing index:
-- owner_id supports the later permission-filtered history list; updated_at
-- keeps newest records first without changing the API response shape.
CREATE INDEX IF NOT EXISTS idx_interview_records_owner_updated
ON interview_records(owner_id, updated_at DESC);

-- Restore lookup index:
-- SQLite already indexes PRIMARY KEY(id); this note records that restore by id
-- intentionally relies on the table primary key rather than a separate index.

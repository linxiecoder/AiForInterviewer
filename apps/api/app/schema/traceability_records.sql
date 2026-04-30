-- ST13_20 R1 数据追踪 schema 切片。
-- 范围：保存 job、resume、interview、answer、RAG evidence、score、
-- review、export、source snapshot 与失败状态之间的最小引用关系。
-- 禁止范围：完整 migration framework、ORM mapping、完整 prompt 或
-- LLM response 持久化、embedding 向量、provider secret、对象存储真实路径、
-- R2 训练闭环、资产归档和批量导出。

CREATE TABLE IF NOT EXISTS traceability_records (
    id TEXT PRIMARY KEY,
    owner_id TEXT NOT NULL,
    trace_type TEXT NOT NULL,
    status TEXT NOT NULL CHECK (
        status IN (
            'pending',
            'running',
            'failed',
            'completed',
            'archived',
            'degraded',
            'retryable'
        )
    ),
    request_id TEXT NOT NULL,
    operation_id TEXT NOT NULL,
    job_ref TEXT,
    resume_ref TEXT,
    session_ref TEXT,
    turn_ref TEXT,
    answer_ref TEXT,
    score_ref TEXT,
    review_ref TEXT,
    export_ref TEXT,
    retrieval_query_ref TEXT,
    retrieval_result_ref TEXT,
    citation_refs_json TEXT NOT NULL DEFAULT '[]',
    evidence_refs_json TEXT NOT NULL DEFAULT '[]',
    evidence_gap_ref TEXT,
    source_snapshot_ref TEXT,
    schema_version INTEGER NOT NULL,
    content_version TEXT,
    retryable INTEGER NOT NULL DEFAULT 0,
    failure_reason TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_traceability_records_owner_type
ON traceability_records(owner_id, trace_type, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_traceability_records_session
ON traceability_records(session_ref, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_traceability_records_request
ON traceability_records(request_id, operation_id);

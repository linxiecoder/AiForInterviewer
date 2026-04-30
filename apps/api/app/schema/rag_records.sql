-- ST13_20 R1 RAG 最小持久化 schema 切片。
-- 范围：保存 knowledge document 摘要、deterministic chunk、index status、
-- retrieval result、citation refs、evidence refs、evidence gap refs 与 trace 关联。
-- 禁止范围：embedding 向量、vector store、复杂 reranking、完整上传后台、
-- 完整 prompt / LLM response、provider secret、对象存储真实路径、R2 训练闭环。

CREATE TABLE IF NOT EXISTS rag_documents (
    id TEXT PRIMARY KEY,
    owner_id TEXT NOT NULL,
    document_id TEXT NOT NULL,
    visibility TEXT NOT NULL CHECK (visibility IN ('private', 'public')),
    source_type TEXT NOT NULL,
    source_label TEXT NOT NULL,
    content_summary TEXT NOT NULL DEFAULT '',
    source_version TEXT NOT NULL,
    index_status TEXT NOT NULL CHECK (index_status IN ('pending', 'indexed', 'failed')),
    failure_reason TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(owner_id, document_id)
);

CREATE INDEX IF NOT EXISTS idx_rag_documents_owner_status
ON rag_documents(owner_id, index_status, updated_at DESC);

CREATE TABLE IF NOT EXISTS rag_chunks (
    id TEXT PRIMARY KEY,
    owner_id TEXT NOT NULL,
    document_id TEXT NOT NULL,
    resource_id TEXT NOT NULL,
    chunk_ref TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    visibility TEXT NOT NULL CHECK (visibility IN ('private', 'public')),
    source_type TEXT NOT NULL,
    source_label TEXT NOT NULL,
    content_summary TEXT NOT NULL DEFAULT '',
    source_version TEXT NOT NULL,
    start_offset INTEGER NOT NULL DEFAULT 0,
    end_offset INTEGER NOT NULL DEFAULT 0,
    index_status TEXT NOT NULL CHECK (index_status IN ('pending', 'indexed', 'failed')),
    failure_reason TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(owner_id, document_id, chunk_ref)
);

CREATE INDEX IF NOT EXISTS idx_rag_chunks_document
ON rag_chunks(owner_id, document_id, chunk_index ASC);

CREATE INDEX IF NOT EXISTS idx_rag_chunks_resource
ON rag_chunks(resource_id, chunk_ref);

CREATE TABLE IF NOT EXISTS rag_retrieval_records (
    id TEXT PRIMARY KEY,
    owner_id TEXT NOT NULL,
    trace_ref TEXT,
    request_id TEXT NOT NULL,
    operation_id TEXT NOT NULL,
    session_ref TEXT,
    turn_ref TEXT,
    answer_ref TEXT,
    retrieval_query_ref TEXT NOT NULL,
    retrieval_result_ref TEXT NOT NULL,
    query_summary TEXT NOT NULL,
    top_k INTEGER NOT NULL,
    trigger TEXT NOT NULL,
    visibility_filter TEXT NOT NULL,
    hit_count INTEGER NOT NULL,
    hit_summary_json TEXT NOT NULL DEFAULT '[]',
    empty_reason TEXT,
    degraded INTEGER NOT NULL DEFAULT 0,
    retryable INTEGER NOT NULL DEFAULT 0,
    citation_refs_json TEXT NOT NULL DEFAULT '[]',
    evidence_refs_json TEXT NOT NULL DEFAULT '[]',
    evidence_gap_ref TEXT,
    source_snapshot_ref TEXT,
    permission_filtered_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_rag_retrieval_records_owner_session
ON rag_retrieval_records(owner_id, session_ref, created_at ASC);

CREATE INDEX IF NOT EXISTS idx_rag_retrieval_records_trace
ON rag_retrieval_records(trace_ref);

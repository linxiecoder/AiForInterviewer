---
title: 数据库信息说明
type: guide
permalink: ai-for-interviewer/development/database
---

# 数据库信息说明

本文档说明当前 R0/R1 本地数据库边界。本文档只描述现状，不引入新的 schema、migration、ORM 或 API contract。

## 当前数据库类型

当前后端支持 PostgreSQL runtime，并保留 SQLite fallback。访问层位于 `apps/api/app/persistence.py`。

运行时数据库选择规则：

- `DATABASE_URL` 非空时优先使用显式 database URL。
- `DATABASE_URL` 未设置时，使用 `API_DATABASE_PATH` 对应的 SQLite 文件。
- `API_DATABASE_PATH` 也未设置时，默认路径为系统临时目录下的 `ai-for-interviewer/api.sqlite3`。
- `postgresql://...` 会归一化为 `postgresql+psycopg://...`，以使用当前唯一 PostgreSQL driver `psycopg[binary]`。

测试用例会通过 `ManagedTempArtifacts` 创建隔离临时目录，并将 `API_DATABASE_PATH` 指向测试内的 `.sqlite3` 文件。

## schema-loader 机制

schema 初始化发生在应用 startup 或测试显式初始化边界：

- `apps/api/app/main.py` 创建 `InterviewRecordStore`、`TraceabilityStore`、`RAGPersistenceStore`。
- `create_app(..., initialize_schema=True)` 用于测试中提前初始化 schema。
- 常规运行时在 FastAPI lifespan 中调用各 store 的 `initialize()`。
- `persistence.py` 的 `_initialize_schema()` 会识别 SQLAlchemy dialect。
- SQLite 分支继续使用 raw connection 执行 `_load_schema_sql()`，保持本地 fallback 与既有测试行为。
- PostgreSQL 分支使用 SQLAlchemy connection 逐条执行 `_schema_statements(_load_schema_sql())` 拆出的 DDL。
- `_load_schema_sql()` 以 UTF-8 读取并拼接当前三个 schema 文件。

schema-loader 只负责执行 `CREATE TABLE IF NOT EXISTS` 与索引定义，不承担版本迁移、回滚或数据修复。

## schema 文件列表

当前 schema 文件固定为：

- `apps/api/app/schema/interview_records.sql`
- `apps/api/app/schema/traceability_records.sql`
- `apps/api/app/schema/rag_records.sql`

`interview_records.sql` 保存 R0 主链路最小面试记录。`traceability_records.sql` 保存 R1 traceability 最小引用关系。`rag_records.sql` 保存 R1 RAG 文档、chunk 和 retrieval 摘要。

## SQLAlchemy Core 使用范围

`apps/api/app/persistence.py` 使用 SQLAlchemy Core 的 `MetaData`、`Table`、`Column`、`select`、`insert`、`delete`，并按 dialect 使用 SQLite / PostgreSQL upsert。

当前约束是：

- schema DDL 仍来自 `.sql` 文件。
- runtime DML / SELECT 使用 SQLAlchemy Core Table 定义。
- engine 由 `_create_database_engine()` 创建，支持 SQLite 路径、SQLite URL 和 PostgreSQL URL。
- `:memory:` 使用 `StaticPool` 和 `check_same_thread=False`，文件数据库使用 `sqlite+pysqlite` URL。
- PostgreSQL 使用 `psycopg[binary]`，不引入第二个 PG driver。
- RAG document upsert 通过 dialect insert helper 分流到 `sqlite_insert` 或 `postgresql_insert`。

## 为什么不使用手写 SQL 拼接

运行时读写不使用手写 SQL 拼接，原因是：

- 减少字符串拼接造成的字段漂移和注入风险。
- 让列名集中在 Table 定义和字段 tuple 中。
- 让测试可以检查 DML / SELECT 是否基于 SQLAlchemy Core Table。
- 保持 SQLite 当前实现与后续迁移评估之间的边界更清晰。

schema-loader 只执行仓库内固定 schema 文件，不接收用户输入。PostgreSQL 分支逐条执行固定 DDL，不拼接用户输入。

## 为什么当前不启用 ORM / Alembic

当前 R0/R1 仍是最小本地持久化切片，数据库对象少，字段关系以安全引用和摘要为主。此阶段不启用 ORM / Alembic 的原因是：

- 避免在 R1 可信展示面之前引入迁移框架复杂度。
- 当前 schema 仍由任务包明确控制，尚未进入多环境迁移治理阶段。
- SQLAlchemy Core 已能覆盖当前 typed DML / SELECT 需求。
- ORM 映射会扩大改动面，不符合 R1 最小闭环目标。

当 schema 出现多版本线上升级、回滚、数据修复或跨环境部署需求时，再重新评估 Alembic。

## PostgreSQL runtime 与 SQLite fallback

PostgreSQL runtime 的目标是让 R1 traceability、RAG persistence 和 interview record store 能在真实数据库上运行。当前不改变 API contract，也不改变 schema 事实源。

真实数据库用户名、密码和连接串只能配置在本地 `.env`。仓库文档和 `.env.example` 只展示变量名或 `<...>` 占位符；完整规则见 [密钥与环境变量策略](secrets-and-env.md)。

本地 PostgreSQL 示例：

```bash
docker compose -f docker-compose.pg.yml up -d
```

启动 API 示例：

```bash
DATABASE_URL=<postgresql_database_url> .venv/bin/python -m uvicorn app.main:app --app-dir apps/api --host 127.0.0.1 --port 8001
```

其中 `<postgresql_database_url>` 的格式为 `postgresql+psycopg://<user>:<password>@localhost:5432/<database>`。

SQLite fallback 示例：

```bash
API_DATABASE_PATH=<local_sqlite_file_path> .venv/bin/python -m uvicorn app.main:app --app-dir apps/api --host 127.0.0.1 --port 8001
```

`.env.example` 只提供占位说明，不包含真实数据库密码或真实生产连接串。

## Store 职责

### InterviewRecordStore

`InterviewRecordStore` 负责：

- 保存 R0 面试记录。
- 按 `record_id` 恢复记录。
- 按 `owner_id` 列出历史摘要。
- 保存 `payload_json`，其中包含当前最小 job / resume / interview / review / export 片段。

它不负责 RAG 检索、traceability 聚合、训练闭环或资产归档。

### TraceabilityStore

`TraceabilityStore` 负责：

- 保存 R1 traceability record。
- 按 trace id 读取单条 trace。
- 按 `owner_id`、可选 `trace_type`、可选 `session_ref` 列出 trace records。
- 保存 session / turn / answer / score / review / export / RAG evidence 之间的安全引用。

`build_trace_summary()` 位于 `apps/api/app/traceability.py`，负责把 trace records 转换为前端可展示的安全摘要。

### RAGPersistenceStore

`RAGPersistenceStore` 负责：

- 保存 knowledge document 摘要。
- 保存 deterministic chunks。
- 按 owner/document 读取 document 和 chunk。
- 基于已持久化 chunk 执行本地 keyword / substring retrieval。
- 保存 retrieval record，包括 query summary、hit summary、citation refs、evidence refs、evidence gap ref、degraded、retryable。

它不负责 vector store、复杂 reranking、完整上传后台或 embedding 持久化。

## RAG 数据关系

当前 RAG 表之间的关系是最小引用关系：

- `rag_documents`：按 `owner_id + document_id` 唯一保存文档摘要、可见性、来源类型、来源标签、版本和 index status。
- `rag_chunks`：按 `owner_id + document_id + chunk_ref` 唯一保存 chunk 摘要、`resource_id`、`chunk_index`、offset、可见性和 index status。
- `rag_retrieval_records`：保存一次 retrieval 的 request/operation/session/turn/answer 引用、query summary、hit summary、citation refs、evidence refs、evidence gap 和降级状态。

RAG citation 通过 `citation_refs_json` 进入 retrieval record，并可经 traceability 汇总到 `trace_summary.rag.citation_refs`。

## traceability 关系

`traceability_records` 使用引用字段连接 R1 可信链路：

- `session_ref` 连接一次面试 session。
- `turn_ref` 连接面试轮次。
- `answer_ref` 连接候选人回答。
- `score_ref` 连接评分结果。
- `review_ref` 连接复盘结果。
- `export_ref` 连接 Markdown export。
- `retrieval_query_ref` / `retrieval_result_ref` 连接 RAG 检索。
- `citation_refs_json` / `evidence_refs_json` / `evidence_gap_ref` 连接 RAG citation 和 evidence gap。

前端可信 trace 页面只展示这些安全摘要和引用，不展示 provider 原始载荷。

## 不持久化内容

当前数据库边界不持久化：

- provider secret。
- 完整 prompt 原文。
- 完整 LLM response 原文。
- embedding 向量。
- 对象存储真实路径。
- R2 训练闭环数据。
- 完整资产归档。
- 批量导出结果。

RAG document / chunk 中保存的是 `content_summary`，不是完整知识库治理后台或 vector store。

## 测试数据库和测试命令

RAG / traceability / review-export targeted API 测试：

```bash
.venv/bin/python -m tools.test_runner.run_tests --pytest-args tests/api/test_traceability_integration.py tests/api/test_traceability_persistence.py tests/api/test_rag_foundation.py tests/api/test_rag_persistence.py tests/api/test_review_export.py -q
```

完整 API 测试：

```bash
.venv/bin/python -m tools.test_runner.run_tests --pytest-args tests/api -q
```

SQLAlchemy Core access layer 测试：

```bash
.venv/bin/python -m tools.test_runner.run_tests --pytest-args tests/api/test_persistence_sql_access_layer.py -q
```

R0 主链路持久化 smoke：

```bash
.venv/bin/python -m tools.test_runner.run_tests --pytest-args tests/api/test_r0_e2e.py -q
```

PostgreSQL runtime 定向测试：

```bash
.venv/bin/python -m tools.test_runner.run_tests --pytest-args tests/api/test_postgresql_runtime.py -q
```

该测试文件默认会验证 `DATABASE_URL` 优先级、PostgreSQL engine 创建、SQLite fallback 和 schema statement 解析。需要真实连接 PostgreSQL 的 round trip 测试会在未设置 `TEST_DATABASE_URL` 时 skip。

启用 PG integration tests 示例：

```bash
TEST_DATABASE_URL=<postgresql_test_database_url> .venv/bin/python -m tools.test_runner.run_tests --pytest-args tests/api/test_postgresql_runtime.py -q
```

其中 `<postgresql_test_database_url>` 的格式为 `postgresql+psycopg://<user>:<password>@localhost:5432/<test_database>`。

所有正式 Python 测试仍应使用 `.venv/bin/python`。

## 后续 migration / Alembic 评估时机

出现以下情况时，再评估 migration framework 或 Alembic：

- 需要对已有用户数据库做兼容升级。
- schema 需要版本号、迁移历史和回滚策略。
- 多环境部署需要可重复迁移流程。
- ORM 映射能明显降低复杂度，并且不会扩大 R1/R2 边界。
- 数据修复、索引演进或字段拆分无法再由当前最小 schema-loader 安全承接。

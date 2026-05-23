---
title: 前后端验证计划
type: delivery-planning
status: draft-pr1
owner: 项目交付
permalink: ai-for-interviewer/docs/03-delivery/refactor-multiagent-langgraph/validation-plan
---

# 前后端验证计划

## 1. 文档目的

本文定义 PR1-PR8 的分阶段验证骨架，并单列 PR1.5 Data Model / Persistence / Replay 文档收口验证、PR2 AI Runtime 基础模型 preflight、redaction scan、未决标记 scan、`docs/tmp` canonical scan、checkpoint business truth source scan 和 raw payload scan。

本轮 SubAgent C 只修改 05 / 10 / 15 三份文档，不运行业务测试，不启动前后端服务，不调用 provider，不安装依赖，不修改 apps / tests / migration / CI。

## 2. 输入来源

- active docs：`BACKLOG.md`、`DELIVERY_PLAN.md`、`TEST_POLICY.md`、`SECURITY_PRIVACY.md`、`PERSISTENCE_MODEL.md`、`DATA_MODEL.md`、`API_SPEC.md`、`APPLICATION_FLOW_SPEC.md`
- `05_BACKEND_LLM_TRACE_PERSISTENCE_PLAN.md`
- `10_DATA_MODEL_AND_MIGRATION_PLAN.md`
- `13_TEST_PLAN_BACKEND.md`
- `14_TEST_PLAN_FRONTEND.md`
- 当前 package scripts、pytest 结构和 SQLAlchemy model skeleton 只读盘点

## 3. 当前状态

当前仓库常用验证入口包括 `git status`、`git diff --check`、`.venv/bin/python -m pytest ...`、`npm run web:test`、`npm run web:build` 和文档治理命令。PR1 / PR1.5 是文档规划阶段，验证目标是文档一致性、边界清晰、禁止项无残留，不运行 Core Business API / repository / frontend 业务测试。

## 4. Scope Lock 验证

### 4.1 PR1.5 Data Model / Persistence / Replay 文档收口

| Gate | Command | Pass condition | Failure handling |
|---|---|---|---|
| repo-state gate | `git status --short --untracked-files=all` | 只出现 05 / 10 / 15 三份授权文档变更；无 apps/tests/依赖/migration/CI 变更 | 停止并交给主 Agent 判断越界文件 |
| diff stat | `git diff --stat -- docs/03-delivery/refactor-multiagent-langgraph/05_BACKEND_LLM_TRACE_PERSISTENCE_PLAN.md docs/03-delivery/refactor-multiagent-langgraph/10_DATA_MODEL_AND_MIGRATION_PLAN.md docs/03-delivery/refactor-multiagent-langgraph/15_VALIDATION_PLAN.md` | 变更范围只限三份文档 | 停止并收窄 diff |
| whitespace | `git diff --check -- docs/03-delivery/refactor-multiagent-langgraph/05_BACKEND_LLM_TRACE_PERSISTENCE_PLAN.md docs/03-delivery/refactor-multiagent-langgraph/10_DATA_MODEL_AND_MIGRATION_PLAN.md docs/03-delivery/refactor-multiagent-langgraph/15_VALIDATION_PLAN.md` | 无 trailing whitespace / conflict marker | 修正文档格式 |
| required terms | `rg -n "agent_runs|agent_node_runs|agent_interrupts|agent_checkpoint_refs|llm_calls|llm_call_payloads|LlmTraceContext|LlmPayloadCapturePolicy|PersistedLlmTransport|side-effect|idempotency|production resume|debug replay" docs/03-delivery/refactor-multiagent-langgraph/05_BACKEND_LLM_TRACE_PERSISTENCE_PLAN.md docs/03-delivery/refactor-multiagent-langgraph/10_DATA_MODEL_AND_MIGRATION_PLAN.md docs/03-delivery/refactor-multiagent-langgraph/15_VALIDATION_PLAN.md` | 必要术语均有命中 | 补正文档，不进入代码 |
| no business tests | `true # PR1.5 intentionally does not run pytest/npm business tests` | 明确不运行 `.venv/bin/python -m pytest ...`、`npm run web:test`、`npm run web:build` | 如需运行，由主 Agent 另开验证任务 |

### 4.2 PR2 AI Runtime 基础模型 preflight

PR2 开始写代码前先跑 preflight，确认模型风格、bootstrap、边界和文档输入稳定。

| Gate | Command | Pass condition | Failure handling |
|---|---|---|---|
| repo-state gate | `git status --short --untracked-files=all` | 无未解释越界改动 | 停止，主 Agent 处理并行 worker 冲突 |
| branch / HEAD / divergence | `git branch --show-current`; `git rev-parse HEAD`; `git rev-list --left-right --count origin/main...HEAD` | 分支、HEAD 和 divergence 已记录 | 状态异常时不开始 PR2 |
| model style scan | `rg -n "class .*\\(OwnedRecordMixin, Base\\)|__tablename__|mapped_column\\(|JSON|DateTime\\(timezone=True\\)|String\\(80\\)" apps/api/app/infrastructure/db/models tests/api/test_db_schema_bootstrap.py tests/api/test_model_imports.py` | PR2 与现有 model skeleton 风格一致 | PR2 先更新设计或拆小 diff |
| forbidden dependency scan | `rg -n "LangGraph|langgraph|AgentState|application/agents|from app.application.agents|import langgraph" apps/api/app/infrastructure/db/models apps/api/app/application` | Core Business models / repositories 不依赖 LangGraph internals | 停止并修依赖方向 |
| schema bootstrap preflight | `.venv/bin/python -m pytest tests/api/test_model_imports.py tests/api/test_db_schema_bootstrap.py -q` | 模型 import 和 schema bootstrap 通过 | 修 PR2 schema / import |
| no provider | `rg -n "LLM_OPENAI_API_KEY|AIFI_.*REAL_PROVIDER|REAL_PROVIDER|provider manual" tests apps/api` | PR2 不需要真实 provider gate | provider gate 命中时移出 PR2 |

## 5. PR1-PR8 验证矩阵

| 阶段 | 验证命令 | 通过条件 | 失败处理 |
|---|---|---|---|
| PR1 docs 验证 | `git status --short --untracked-files=all`; `git diff --stat`; `git diff --check`; doc governor minimal | 只变更允许文档；无 whitespace error；docs gate 通过 | 停止并修正文档/索引 |
| PR1.5 Data / Persistence / Replay docs | §4.1 commands + §6 scans | 05/10/15 implementation-ready；无 raw / checkpoint / 未决标记边界违规 | 停止并修三份文档 |
| PR2 AI Runtime 基础模型验证 | §4.2 preflight；`.venv/bin/python -m pytest tests/api/test_model_imports.py tests/api/test_db_schema_bootstrap.py tests/api/test_agent_run_repository.py tests/api/test_llm_call_repository.py tests/api/test_sensitive_payload_redaction.py -q` | 表/仓储/脱敏通过；raw 默认关闭；owner scoped | rollback migration 或修 schema |
| PR3 AI Orchestration Facade 验证 | `.venv/bin/python -m pytest tests/api/test_agent_contracts.py tests/api/test_agent_graph_runner.py tests/api/test_architecture_boundaries.py -q` | Core 不 import LangGraph；facade contract 通过 | 停止迁移业务 graph |
| PR4 LangGraph Runtime + Fake Graph 验证 | `.venv/bin/python -m pytest tests/api/test_langgraph_checkpointer_factory.py tests/api/test_agent_interrupt_replay.py tests/api/test_agent_runtime_api.py tests/api/test_agent_replay_resume_policy.py -q` | fake graph start/resume/replay/timeline 通过；production resume 不调用 provider | 关闭 runtime feature flag |
| PR5 Job Match Graph 验证 | `.venv/bin/python -m pytest tests/api/test_agent_graphs.py tests/api/test_architecture_boundaries.py tests/api/test_job_match_api.py -q` | score、analysis、candidate-only 通过 | fallback legacy path 或禁用 graph |
| PR6 Polish Question / Feedback Graph 验证 | `.venv/bin/python -m pytest tests/api/test_polish_api.py tests/api/test_polish_question_llm.py tests/api/test_polish_feedback_llm.py tests/api/test_agent_side_effect_idempotency.py -q` | answer save no LLM；feedback independent task；replay 不重复创建 question/feedback | fallback deterministic / legacy path |
| PR7 Frontend AI Runtime UI 验证 | `npm run web:test`; `npm run web:build` | status/timeline/interrupt/candidate UI 编译/测试通过 | 关闭 UI feature flag |
| PR8 Report / Review / Candidate Closure 验证 | `.venv/bin/python -m pytest tests/api/test_report_api.py tests/api/test_review_api.py tests/api/test_candidate_confirmation.py tests/api/test_sensitive_payload_redaction.py -q`; `npm run web:test`; optional `npm run web:smoke:auth` | copy boundary、confirmation、redaction 通过 | 禁用 graph/candidate closure |

## 6. Static scans

### 6.1 Redaction scan

```bash
rg -n "raw_prompt|raw_completion|provider_payload|system prompt|hidden_rubric|api_key|token|cookie|secret|full_resume|full_jd|request_body|response_body" docs/03-delivery/refactor-multiagent-langgraph apps/api tests/api apps/web/src
```

通过条件：

- 在 05/10/15 中命中只允许出现在禁止项、扫描项或 redaction policy 中。
- 在 apps/tests 中命中必须是 sanitizer 测试、fake leak marker、禁止项断言或日志脱敏断言。
- API response、summary、timeline、checkpoint ref、copy content 不得把这些字段作为可见字段。

### 6.2 Raw payload scan

```bash
rg -n "raw payload|raw_payload|raw prompt|raw completion|provider payload|raw_payload_ciphertext_ref|encryption_key_ref|AIFI_LLM_DEBUG_RAW_PAYLOAD_ENABLED" docs/03-delivery/refactor-multiagent-langgraph apps/api tests/api
```

通过条件：

- raw 默认关闭。
- raw 如开启必须同段写明 feature flag + encryption + TTL + audit + owner access control。
- `raw_payload_ciphertext_ref` 和 `encryption_key_ref` 不进入 API summary。

### 6.3 未决标记 / vague wording scan

```bash
rg -n "T[B]D|T[O]DO|后续[[:space:]]*补充|根据[[:space:]]*情况[[:space:]]*处理|适当[[:space:]]*调整|待[[:space:]]*后续|视[[:space:]]*情况|占位[[:space:]]*待定" docs/03-delivery/refactor-multiagent-langgraph/05_BACKEND_LLM_TRACE_PERSISTENCE_PLAN.md docs/03-delivery/refactor-multiagent-langgraph/10_DATA_MODEL_AND_MIGRATION_PLAN.md docs/03-delivery/refactor-multiagent-langgraph/15_VALIDATION_PLAN.md
```

通过条件：

- 05/10/15 不出现模糊承诺词、空泛处置词或未绑定 PR / 文件 / symbol / 冻结边界的未决标记。
- PR1.5 目标是不保留未决标记。

### 6.4 `docs/tmp` canonical scan

```bash
rg -n "docs/tmp|CODEX_LANGGRAPH_AI_NON_AI_BOUNDARY|canonical|事实源|truth source|source of truth|active docs" AGENTS.md docs/00-governance/DOCS_INDEX.md docs/03-delivery/refactor-multiagent-langgraph
```

通过条件：

- `docs/tmp/CODEX_LANGGRAPH_AI_NON_AI_BOUNDARY.md` 只能作为 PR1 输入和边界参考。
- 05/10/15 不得把 `docs/tmp` 标记为 canonical / active truth source。
- 当前事实源仍是 `DOCS_INDEX.md` 登记的 active docs 和 AIFI-BE-002 planning package 边界。

### 6.5 Checkpoint business truth source scan

```bash
rg -n "checkpoint.*(truth source|source of truth|业务事实|业务真相|formal object|business result)|业务事实.*checkpoint|业务真相.*checkpoint|source of truth.*checkpoint" docs/03-delivery/refactor-multiagent-langgraph apps/api tests/api
```

通过条件：

- checkpoint 只能用于 runtime recovery、resume、time travel、debug replay。
- 业务 API / Core Business Tables 才是 `Question`、`Feedback`、`Report`、`Review`、`Weakness`、`Asset`、`Training` 的 truth source。
- `agent_checkpoint_refs` 只暴露 ref / metadata，不保存或返回 checkpoint payload。

### 6.6 Replay / idempotency scan

```bash
rg -n "production resume|debug replay|replay_reused|replay_blocked|pending_writes|persist_question_once|persist_feedback_once|side-effect|idempotency_key_hash" docs/03-delivery/refactor-multiagent-langgraph
```

通过条件：

- production resume 复用旧 sanitized result 或 fail closed，不重新调用 provider。
- debug replay 不写 Core Business Tables。
- `persist_question` / `persist_feedback` 通过 side-effect idempotency key 阻止重复创建。

## 7. Fake / real provider gate

| Gate | 默认 | 条件 |
|---|---|---|
| fake transport gate | PR4-PR8 必跑 | 所有 graph tests 使用 deterministic fake；fake 可制造 raw leak marker 验证 sanitizer。 |
| real provider gated manual test | 默认不跑 | 只能在显式 env flag、人工批准、raw-off scan、redaction scan、access audit path 通过后执行；PR1 / PR1.5 / PR2 不执行。 |
| sensitive redaction scan | PR1.5 起必跑 | 扫描 docs、response/log/timeline/checkpoint ref；不扫描 raw store 内容。 |

## 8. 通用命令

PR2 之后可使用以下通用命令；PR1.5 本轮只运行文档相关 gate，不运行这些业务测试。

```bash
git status --short --untracked-files=all
git diff --stat
git diff --check
.venv/bin/python -m pytest tests/api/test_architecture_boundaries.py -q
npm run web:test
npm run web:build
```

## 9. 与 active docs 的关系

本文提供验证计划，不替代 `TEST_POLICY.md`、`SECURITY_PRIVACY.md` 或后续 F7 测试计划。每个 PR 的实际结果必须写入对应 PR 总结或 active delivery docs。`API_SPEC.md` 仍是 API semantic / handoff contract；本文不把它改写为完整 endpoint catalog，也不绕过 `BACKLOG.md` 或 `DELIVERY_PLAN.md`。

## 10. 非目标

- 不默认执行全量业务测试。
- 不默认执行真实 provider。
- 不以 smoke 代替 security/privacy。
- 不把测试全绿写成 release Go。
- 不把 docs/tmp 作为 canonical truth source。
- 不把 checkpoint 作为业务 truth source。

## 11. Definition of Done

- PR1-PR8 验证矩阵已覆盖。
- PR1.5 文档收口 gate、PR2 preflight、redaction scan、未决标记 scan、`docs/tmp` canonical scan、checkpoint business truth source scan、raw payload scan 已列为可执行命令。
- 明确 PR1.5 不运行业务测试、不启动服务、不调用 provider。
- 明确 production resume、debug replay、side-effect idempotency 和 raw payload gate 的验证断言。

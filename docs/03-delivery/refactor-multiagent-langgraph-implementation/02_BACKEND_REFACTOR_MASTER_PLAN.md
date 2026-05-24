---
title: LangGraph MultiAgent Backend Refactor Master Plan
type: delivery-planning
status: draft-f5-langgraph-implementation-consolidation
owner: 后端架构 / 项目交付
permalink: ai-for-interviewer/docs/03-delivery/refactor-multiagent-langgraph-implementation/backend-refactor-master-plan
---

# LangGraph MultiAgent Backend Refactor Master Plan

## 1. 文档目的

本文是后端迁移总计划的唯一位置。本文只定义 PR 顺序、scope、门禁、验证、回滚和启动条件，不维护 graph node 级实现、ORM 字段级表、Prompt / Skill / Trace 细节或前端 UI 状态机。

## 2. 总体原则

| 原则 | 规则 |
|---|---|
| 单微服务双域 | 保持现有 FastAPI 单后端；新增 AI Runtime 域，不拆独立 AI service |
| Core 不依赖 LangGraph | Core UseCase 只能通过 facade / port 调用 AI Runtime |
| PR 小步迁移 | PR2 到 PR8 分层推进，每个 PR 有 allowed / forbidden scope |
| PR2 default-off | PR2 只落 inert data/repository/tests，不启用 runtime |
| checkpoint 非事实源 | checkpoint 只恢复 runtime control state |
| raw-off | raw prompt / completion / provider payload 默认禁止 |
| candidate/formal | AI 只产出 candidate / suggestion；formal 写入需 Core command 或用户确认 |

## 3. PR 总览

| PR | 目标 | Scope | Allowed | Forbidden | Done condition |
|---|---|---|---|---|---|
| PR2 | AI Runtime 基础模型 | inert data model / repository / backend tests | `20_PR2_PREFLIGHT_READINESS_REPORT.md` exact scope lock 中列出的文件 | LangGraph runtime、graph execution、real provider、frontend、dependency、migration、business graph | schema/import/bootstrap/repository/redaction/idempotency/boundary tests pass |
| PR3 | AI Orchestration Facade + application contracts | facade、runner port、registry、guard、handoff、interrupt contracts | `apps/api/app/application/ai_runtime/**` and tests after explicit PR3 scope lock | concrete LangGraph import、adapter、checkpointer、business graph | Core only sees project-owned DTO / port |
| PR4-LG-DEP | LangGraph dependency spike gate | dependency / fake graph spike only | dependency files and `infrastructure/ai_runtime/langgraph/**` after explicit authorization | business graph、real provider、frontend | dependency pin、serializer/checkpointer/fake graph verified |
| PR4 | LangGraph runtime + fake graph | concrete adapter、checkpointer、fake graph runtime API | AI Runtime infrastructure + runtime API + tests | business graph migration、provider calls | fake graph start/resume/replay/timeline sanitized |
| PR5 | Polish first migration target | progress tree / question / feedback graph | Polish graph descriptors, facade wiring and compatibility tests | JobMatch / ResumeAnalysis graph、Pressure / report / frontend、candidate enhancement / formal closure | existing Polish API compatibility preserved；answer save remains non-AI；feedback remains independent task |
| PR6 | Graph Configuration Backend / Registry Config API | graph descriptor API、graph config schema、enablement/default-off config API、placeholder registry、policy refs、admin audit | graph descriptor API、graph config schema、graph enablement/default-off config API、placeholder graph registry、prompt/eval/provider policy refs、admin/owner scope、config audit | business full graph migration、provider call、raw prompt/completion/provider payload exposure、LangGraph debug internals exposure、frontend | config API default-off；placeholder registry only；audit sanitized；admin/owner scoped |
| PR7 | Graph Configuration Frontend / AI Runtime graph configuration console | graph list/detail/config form、placeholder graph view、sanitized health/status/audit view | graph list page、graph detail/config page、enable/disable form using PR6 API、prompt/eval/model policy refs display、sanitized health/status/audit view | Agent debug page for normal users、AgentState/checkpoint/raw payload display、backend graph logic、provider secret/model key exposure | controlled configuration console works against PR6 API；no raw internals；no normal-user debug page |
| PR8 | JobMatch / ResumeAnalysis / Pressure / Report / Review / Candidate / Skill / Training conditional later migrations | conditional business graph migrations after PR5-PR7 foundation and config console | scoped backend + frontend files after explicit PR8 authorization | export/download、exact probability、silent formal write、unapproved provider calls、raw payload exposure | each migrated graph passes parity, privacy, copy, candidate/formal and rollback gates |

### 3.1 PR6 Graph Configuration Backend scope

本阶段不再迁移 JobMatch / ResumeAnalysis 业务 graph。目标是建立 default-off 的 Graph Configuration Backend / Registry Config API，使后续业务 graph 可以被描述、登记、配置、审计和按 owner/admin scope 受控启用。

Allowed scope:

- graph descriptor API。
- graph config schema。
- graph enablement/default-off config API。
- placeholder graph registry。
- prompt/eval/provider policy refs。
- admin/owner scope。
- config audit。

Forbidden scope:

- JobMatch / ResumeAnalysis full graph。
- Pressure / Report / Review graph。
- provider call。
- raw prompt/completion/provider payload exposure。
- LangGraph debug internals exposure。

### 3.2 PR7 Graph Configuration Frontend scope

本阶段不再是普通 task status only runtime UI，也不是 LangGraph debug page。目标是 AI Runtime graph configuration console，只消费 PR6 提供的 sanitized config/status/audit API。

Allowed scope:

- graph list page。
- graph detail/config page。
- enable/disable form using PR6 API。
- prompt/eval/model policy refs display。
- sanitized health/status/audit view。

Forbidden scope:

- Agent debug page for normal users。
- AgentState/checkpoint/raw payload display。
- backend graph logic。
- provider secret/model key exposure。

## 4. PR2 exact scope

PR2 仍是 `CONDITIONAL GO`，并且在编辑代码前必须采用 `docs/03-delivery/refactor-multiagent-langgraph/20_PR2_PREFLIGHT_READINESS_REPORT.md` 的 exact Scope Lock。

Allowed PR2 files are limited to:

- `apps/api/app/infrastructure/db/models/ai_runtime.py`
- `apps/api/app/infrastructure/db/repositories/ai_runtime/**`
- `tests/api/test_model_imports.py`
- `tests/api/test_db_schema_bootstrap.py`
- `tests/api/test_agent_run_repository.py`
- `tests/api/test_agent_interrupt_repository.py`
- `tests/api/test_llm_call_repository.py`
- `tests/api/test_sensitive_payload_redaction.py`
- `tests/api/test_agent_side_effect_idempotency.py`
- `tests/api/test_agent_replay_resume_policy.py`
- `tests/api/test_architecture_boundaries.py` for PR2 import-boundary assertions only

PR2 forbidden operations:

- runtime enablement or runtime flag implementation。
- graph runner / facade / adapter / checkpointer / serializer implementation。
- LangGraph / LangChain dependency or import。
- real provider call or provider smoke。
- business graph directory or business graph migration。
- frontend edits。
- migration / Alembic edits。
- CI edits。
- PR2 scope 外业务代码 edits。

## 5. PR2 launch gates

| Gate | Required evidence | Status |
|---|---|---|
| AIFI-BE-004 Pressure blocker | `PRESSURE_MODE_SPEC.md` accepted and Pressure graph excluded from PR2 | satisfied for PR2 |
| AIFI-ARCH-007 Skill Model blocker | `SKILL_MODEL_SPEC.md` accepted; no temporary skill key in PR2 | satisfied for PR2 |
| AIFI-PROMPT-002 Prompt Asset / Evaluation blocker | `PROMPT_ASSET_SPEC.md` / `PROMPT_EVALUATION_SPEC.md` accepted | satisfied for PR2 |
| AIFI-ARCH-008 directory boundary | final directory is `application/ai_runtime/**` + `infrastructure/ai_runtime/langgraph/**` | satisfied for PR2 |
| AIFI-BE-005 / AIFI-BE-006 | PR2 readiness is `CONDITIONAL GO` with exact scope lock | satisfied for PR2 |
| ADR-0005 | remains `Proposed`; PR2-only accepted risk recorded | conditional |
| active docs backfill | deferred for PR2 only; required before PR3/PR4 runtime exposure | conditional |

## 6. Backfill gates before PR3 / PR4

Before runtime exposure in PR3 / PR4, the owner must either backfill active docs or record a new accepted risk:

| Active doc | Required backfill |
|---|---|
| `DATA_MODEL.md` | `AgentRun`、`AgentNodeRun`、`AgentInterrupt`、`LlmCall`、`AgentCheckpointRef` logical objects |
| `PERSISTENCE_MODEL.md` | AI Runtime tables, checkpoint ref, migration / rollback / in-flight task policy |
| `SECURITY_PRIVACY.md` | raw-off, checkpoint/timeline/debug visibility, redaction, retention, audit |
| `APPLICATION_FLOW_SPEC.md` | facade, runtime event flow, handoff, interrupt/resume orchestration |
| `API_SPEC.md` | Agent Runtime API, timeline, interrupt resume, sanitized LLM summary |

## 7. Validation commands

Docs-only consolidation validation:

```bash
git status --short --untracked-files=all
git diff --stat
git diff --check
.venv/bin/python -m tools.doc_governor.cli doc-quality-gate --repo-root .
```

后续 PR2 implementation 还必须运行 exact scope lock 中列出的 PR2 backend subset 和 forbidden scan。

## 8. Rollback policy

| PR | Rollback rule |
|---|---|
| PR2 | Revert inert runtime models/repositories/tests; no runtime disable needed because runtime remains default-off |
| PR3 | Disable facade wiring and restore legacy direct AI task path; no LangGraph dependency should exist |
| PR4-LG-DEP | Revert dependency files and fake adapter spike; no business graph state should exist |
| PR4 | Disable runtime feature flag and fake graph API; checkpoint refs must not be used as business facts |
| PR5 | Keep Polish direct path available until graph parity; cancel / fail in-flight Polish graph runs before fallback |
| PR6 | Disable graph configuration API / feature flag and keep all graph configs default-off; no business graph state should exist; sanitized config audit remains reviewable |
| PR7 | Disable graph configuration console route or navigation entry; backend config state remains default-off and owner/admin scoped |
| PR8 | Keep Core business formal objects authoritative; cancel / fail in-flight agent runs before fallback |

## 9. Stop conditions

Stop before implementation if any of the following is true:

- PR scope cannot be mapped to a current AIFI task or explicit PR scope.
- `git status --short --untracked-files=all` shows unexplained dirty files outside the PR scope.
- The requested PR needs real provider calls.
- The implementation requires files outside allowed scope.
- The implementer cannot adopt the exact PR2 scope for PR2.
- Active docs backfill is required but neither completed nor accepted as bounded risk.

## 10. Old-doc handling

旧 `docs/03-delivery/refactor-multiagent-langgraph/` 保留为 evidence-only。本文在本目录内替代旧 PR sequence 文档的后端迁移总计划职责，但不修改 `BACKLOG.md`、`DELIVERY_PLAN.md`、ADR-0005 或任何旧文档。

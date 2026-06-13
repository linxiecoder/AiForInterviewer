---
title: ADR-0005-langgraph-agentic-workflow-runtime
type: decision
status: proposed
owner: 后端架构
date: 2026-05-24
permalink: ai-for-interviewer/docs/04-decisions/adr-0005-langgraph-agentic-workflow-runtime
---

# ADR-0005 LangGraph Agentic Workflow Runtime

## 状态

Proposed

PR2 governance closure：本 ADR 仍保持 `Proposed`，不在本轮升级为完整 PR3-PR8 / business graph 的长期 Accepted 决策。AIFI-ARCH-008 已在 `BACKLOG.md` 同步为 `ACCEPTED` 并关闭 AI/Core directory shape open issue：最终目录形态为 `application/ai_runtime/**` + `infrastructure/ai_runtime/langgraph/**`。

PR2-only accepted risk：主 Agent 曾接受在受限 exact scope lock 内实施 inert AI Runtime data model / repository / backend tests 的有限风险；该 historical scope lock 所在旧规划目录已去层删除。后续 PR2 / PR3 / PR4 implementation 必须重新以 active design docs、`docs/03-implementation/F5_BACKEND_IMPLEMENTATION_NOTES.md` 中已迁入的实现证据和当轮 fresh scope lock 为准。该接受不授权 LangGraph runtime enablement、graph execution、real provider call、business graph migration、runtime facade / adapter、frontend UI 或 active docs 全量 backfill；这些仍需后续 PR scope 重新授权。

PR3 / PR4 active docs backfill：2026-05-24 已将 Runtime Contracts 所需的 `AgentRun`、`AgentNodeRun`、`AgentInterrupt`、`AgentCheckpointRef`、`LlmCall`、`LlmCallPayload`、runtime persistence rules、raw-off / checkpoint / timeline visibility、facade flow 和 Agent Runtime API skeleton 回写到 active design docs。该回写只解除 PR3 implementation 的文档阻断；不授权 PR4 dependency / concrete runtime、business graph、frontend、real provider default-on、migration、CI 或 PR5+ formal write implementation。

## Context

AIFI-BE-002 的 PR1 专题规划包已经登记 LangGraph MultiAgent 重构方向，但 `DONE` 只代表 planning package skeleton 完成，不代表实现完成。当前 active docs 已冻结 AI task、Prompt contract、candidate / formal object、trace / evidence、security / privacy、API async task 和 persistence handoff 边界；缺口在于后续 PR2-PR8 需要一个长期架构决策来约束 Agent Runtime、checkpoint、timeline、interrupt/resume、raw payload 和业务写入边界。

本 ADR 不把 `docs/tmp` 或历史 planning package 提升为 canonical active docs。历史 planning package 状态为 superseded; see Git history。本 ADR 只记录长期架构决策候选；API、数据、Prompt、安全和应用编排事实仍需回写到 active docs 或由后续 accepted risk 显式登记。

## Decision

采用 Option C：LangGraph-first Agentic Workflow Runtime，并保持单后端微服务内的 Core Business Domain / AI Agentic Workflow Domain 双域架构。

固定决策如下：

1. Core Business 不依赖 LangGraph、AgentState、graph node、checkpoint schema 或 provider payload。
2. Core UseCase 只能通过 `AiOrchestrationFacade` 或等价 application port 触达 AI Runtime。
3. LangGraph concrete import 只能出现在 `apps/api/app/infrastructure/ai_runtime/langgraph/**`。
4. LangGraph checkpoint 只用于 resume、replay、debug 和 runtime recovery，不是 business truth source。
5. AI node 只能产出结构化结果、candidate、suggestion、validation、low confidence、trace 或 interrupt；formal object 必须由 Core command、用户确认或显式业务动作写入。
6. raw prompt、raw completion、provider request / response payload 默认不保存、不进入日志、不进入 checkpoint、不进入 API response、不进入普通 trace 可见正文。
7. PR2 仅允许在 fresh scope lock 下落 AI Runtime data model、repository、schema / bootstrap / redaction / idempotency tests；PR2 不启用 LangGraph runtime、graph execution、real provider call 或 business graph migration。PR3 再落 facade / runner port；PR4 再落 concrete LangGraph adapter、fake graph、interrupt/resume 和 timeline；PR5-PR8 逐 graph 迁移。已删除的 historical planning 目录不得作为 executable source of truth 复用。
8. `apps/api/app/application/ai_runtime/**` 取代 PR1.5 中的 `application/ai/**` 与 `application/agents/**`；`apps/api/app/infrastructure/ai_runtime/langgraph/**` 取代 `infrastructure/agent_runtime/langgraph/**`；application layer 不创建 `langgraph_adapters/**`。

## PR2 Default-Off Rule

PR2 runtime foundation 必须默认关闭：

1. PR2 不创建或修改 runtime enablement flag、per-graph flag、real-provider gate 或 `runtime_flags.py`。
2. PR2 不创建 `apps/api/app/application/ai_runtime/graphs/**`，不创建 graph node、edge、runner、facade、adapter、checkpointer factory、serializer 或 business graph migration。
3. PR2 不新增 LangGraph / LangChain 依赖，不 import `langgraph`、`langchain`、`langchain_core` 或 `langchain_openai`。
4. PR2 不调用真实 LLM provider，不依赖 real-provider env gate，不新增 provider manual smoke。
5. PR2 repository 只能保存 owner-scoped runtime metadata、checkpoint refs 和 sanitized LLM summaries；raw prompt、raw completion、provider payload、system prompt、token、cookie、secret 和 hidden scoring rules 默认不保存。

## Options Considered

| Option | 结论 | 原因 |
|---|---|---|
| Option A：在现有 LLM service 内局部接入 LangGraph | Rejected for mainline | 容易让 Core import LangGraph、checkpoint 误作业务事实源、raw payload 和 candidate/formal 边界不可验证 |
| Option B：半分层 Agent Runtime | Accepted as explicit fallback only | 可作为阶段性降级，但必须登记范围、截止 PR 和退出条件；不得形成双入口长期架构 |
| Option C：LangGraph-first Agentic Workflow Runtime | Proposed；PR2 runtime foundation accepted risk only | 最能支撑多 graph、runtime timeline、interrupt/resume、raw-off、安全审计和候选确认边界；本轮只接受 PR2 inert data/repository/test foundation，不接受 runtime/graph 启用 |

## Consequences

正向影响：

- Core Business、AI Runtime、LLM transport、checkpoint、trace 和 business handoff 的依赖方向可通过测试验证。
- checkpoint、timeline、debug/admin 视图和 API response 可以统一执行 raw-off 和 sanitized summary policy。
- 多 graph 迁移可以按 PR2-PR8 拆分，避免一次性替换所有业务链路。
- candidate / suggestion / formal object 边界可以通过 Core command、confirmation、audit 和 trace 固化。

成本和约束：

- PR2-PR4 初始实现成本高于局部接入。
- 需要新增 AI Runtime tables、runtime repositories、runner port、adapter、fake graph 和 boundary tests。
- 每个业务 graph 迁移前都必须补 active docs 回写，不允许只依赖专题包。
- AI/Core directory shape 已由 AIFI-ARCH-008 收敛为唯一最终形态：`application/ai_runtime/**` + `infrastructure/ai_runtime/langgraph/**`。不得把 `application/ai/**`、`application/agents/**`、`infrastructure/agent_runtime/**` 或 application-level `langgraph_adapters/**` 作为 PR2-PR8 创建目标。
- Option B fallback 必须显式登记，不能以临时兼容为由长期保留双入口。

## Boundaries

本 ADR 在 PR2 exact scope lock 内允许：

- 在 PR2 设计和实现 `agent_runs`、`agent_node_runs`、`agent_interrupts`、`llm_calls`、`agent_checkpoint_refs` 等 inert AI Runtime 基础对象、repository 和后端测试。
- 在 PR3 设计和实现 `AiOrchestrationFacade`、`AgentGraphRunner` port、runtime command/result contract。
- 在 PR4 设计和实现 concrete LangGraph adapter、fake graph、checkpointer factory、interrupt/resume、sanitized timeline。
- 在 PR5 迁移 Polish first graph target。
- 在 PR6 建立 Graph Configuration Backend / Registry Config API，包括 default-off graph descriptor、config schema、policy refs、placeholder registry 和 sanitized config audit。
- 在 PR7 建立 AI Runtime graph configuration console，只消费 sanitized configuration/status/audit API，不提供普通用户 Agent debug page。
- 在 PR8 以后按条件迁移 JobMatch、ResumeAnalysis、Pressure、Report、Review、Weakness、Asset、Training 等业务 graph。

本 ADR 禁止：

- Core Business service、domain、repository、DB model 或 non-AI API schema 直接依赖 LangGraph。
- 从 checkpoint payload 组装 business read model、正式报告、复盘、资产、薄弱项或训练结果。
- 在日志、checkpoint、API response、copy content、普通 trace 可见正文中保存 raw prompt、raw completion、provider payload、token、cookie、secret 或隐藏评分规则。
- AI node、LangGraph adapter 或 runtime repository 直接写 formal object。
- 把 `docs/tmp`、专题包或本 ADR 当作替代 `docs/02-design/*` 的完整 active docs。
- 将 `application/ai/**`、`application/agents/**`、`infrastructure/agent_runtime/**` 或 application-level `langgraph_adapters/**` 作为替代目录形态重新引入。

## Rollback

若 PR2-PR4 发现 Option C 实施风险超过当前阶段承载能力，允许回滚到 Option B fallback，但必须满足：

1. 主 Agent 在 BACKLOG 或后续受权文档中登记 fallback 范围、影响 PR、退出条件和验证命令。
2. 保留 Core 不 import LangGraph、checkpoint 非事实源、raw-off payload、candidate/formal、owner enforcement 和 audit/trace redaction 六条硬边界。
3. 已创建的 runtime 表或代码必须能通过 migration rollback、feature flag disable 或 adapter disable 停止新写入。
4. queued / running AI task 在 rollback 时必须 cancel、timeout、mark generation_failed 或阻断 result write，不能产生 late formal write。
5. 回滚不得恢复 Option A direct import 主干。

## Follow-up Active Docs Backfill

| Active doc | 回写内容 | PR |
|---|---|---|
| `docs/02-design/PERSISTENCE_MODEL.md` | AI Runtime Tables、checkpoint ref、migration / rollback / in-flight task policy | Completed 2026-05-24 for PR3 / PR4 contract gate；future PR4 implementation still needs explicit scope |
| `docs/02-design/DATA_MODEL.md` | `AgentRun`、`AgentNodeRun`、`AgentInterrupt`、`LlmCall`、`LlmCallPayload`、`AgentCheckpointRef` 逻辑对象和状态域 | Completed 2026-05-24 for PR3 / PR4 contract gate |
| `docs/02-design/SECURITY_PRIVACY.md` | raw-off payload、checkpoint / timeline / debug 可见性、redaction、retention、audit 边界 | Completed 2026-05-24；raw debug and real provider remain default-off |
| `docs/02-design/APPLICATION_FLOW_SPEC.md` | `AiOrchestrationFacade`、runtime event flow、business handoff、interrupt/resume 编排 | Completed 2026-05-24 for PR3 contract start |
| `docs/02-design/API_SPEC.md` | Agent Runtime API、timeline、interrupt resume、sanitized LLM summary response | Completed 2026-05-24 as PR3 / PR4 skeleton；not frontend authorization |
| `docs/02-design/PROMPT_SPEC.md` 与 `prompt-contracts/*.md` | contract 到 graph/node 的 execution mapping | PR5-PR8 |
| `docs/02-design/SCORING_SPEC.md` | graph 评分节点和 `ScoreRuleVersion` handoff | PR5/PR8 |
| `docs/02-design/UX_SPEC.md`、`UI_DESIGN_SYSTEM.md` | Graph Configuration Console、timeline、interrupt drawer、candidate confirmation、low confidence / validation failed UI 状态 | PR7/PR8 |
| `docs/00-governance/DOCS_INDEX.md` | 登记本 ADR 和 implementation set 边界 | 主 Agent 受权 PR |
| `docs/03-implementation/BACKLOG.md` | 消除 AIFI-BE-002 DONE 等于 skeleton 的歧义，登记 PR1.6 blockers，并承接 PR2-PR8 后续任务 | 主 Agent 受权 PR |

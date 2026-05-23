---
title: LangGraph MultiAgent 架构重构实施计划索引
type: delivery-planning
status: draft-pr1
owner: 项目交付
permalink: ai-for-interviewer/docs/03-delivery/refactor-multiagent-langgraph/readme
---

# LangGraph MultiAgent 架构重构实施计划索引

## 1. 文档目的

本文件是 LangGraph MultiAgent 重构专题设计包的阅读入口，用于把 PR1 的文档治理登记、架构边界、PR1-PR8 实施顺序和后续回写规则集中说明清楚。

专题目标是用 LangGraph-first / Option C 方式规划 AI Agentic Workflow Runtime，同时保持当前单后端微服务形态：Core Business 继续承载业务事实，AI Runtime 承载 agent run、node run、interrupt、checkpoint ref 和 LLM trace。

本专题不是最小改动策略，因为当前需求同时涉及多条 AI 链路、候选确认、report/review、runtime trace、checkpoint/resume 和前端 timeline。如果只把 LangGraph 嵌到现有 LLM service 内，会扩大隐式依赖、让 checkpoint 被误当业务事实源，并让 raw payload / trace / candidate formalization 边界难以验证。

## 2. 输入来源

- `docs/tmp/CODEX_LANGGRAPH_MULTIAGENT_README.md`
- `docs/tmp/CODEX_LANGGRAPH_AI_NON_AI_BOUNDARY.md`
- `docs/02-design/APPLICATION_FLOW_SPEC.md`
- `docs/02-design/PERSISTENCE_MODEL.md`
- `docs/02-design/DATA_MODEL.md`
- `docs/02-design/PROMPT_SPEC.md`
- `docs/02-design/SCORING_SPEC.md`
- `docs/02-design/SECURITY_PRIVACY.md`
- `docs/02-design/API_SPEC.md`
- `docs/02-design/UX_SPEC.md`
- `docs/02-design/UI_DESIGN_SYSTEM.md`
- `docs/02-design/prompt-contracts/*.md`
- `docs/03-delivery/DELIVERY_PLAN.md`
- `docs/03-delivery/BACKLOG.md`

`docs/tmp` 只作为本轮规划输入，不是事实源；后续只有回写到 active docs 或 ADR 的结论才可作为执行依据。

## 3. 当前状态

PR1 只创建 planning package，并在 `BACKLOG.md` 和 `DOCS_INDEX.md` 登记专题边界。当前包不替代 `APPLICATION_FLOW_SPEC.md`、`PERSISTENCE_MODEL.md`、`DATA_MODEL.md`、`PROMPT_SPEC.md`、`SCORING_SPEC.md`、`SECURITY_PRIVACY.md`、`API_SPEC.md`、`UX_SPEC.md` 或 prompt contract active docs。

AIFI-BE-002 当前状态为 `DONE`，含义仅限“PR1 专题规划包骨架与治理登记已完成”。它不表示 LangGraph runtime、AI Runtime tables、Agent Runtime API、business graph、frontend timeline、测试实现或安全隐私发布验证已经完成；这些实现工作必须由 PR2-PR8 和对应 active docs 回写继续承接。

已冻结的 PR1 规划边界：

- 推荐 Option C：LangGraph-first Agentic Workflow Runtime。
- 仍采用单后端微服务，不拆出独立 AI service。
- Core Business 不依赖 LangGraph、AgentState、graph node 或 checkpoint schema。
- Core UseCase 只通过 `AiOrchestrationFacade` 触达 AI Runtime。
- LangGraph checkpoint 不是业务事实源。
- LLM node 不直接写 formal object。
- candidate / suggestion 不能静默升级为 formal object。
- raw prompt、raw completion、provider payload 不进入普通日志、checkpoint 或 API response。

## 3.1 PR1 与 PR1.5 区别

| 项 | PR1 planning package | PR1.5 implementation-ready spec |
|---|---|---|
| 主要目的 | 创建专题包、登记边界、收集 SubAgent recon 和 PR1-PR8 骨架 | 把 PR1 规划包提升为可指导 PR2 的治理 / 架构权威输入 |
| 决策状态 | 推荐 Option C，但尚未形成长期 ADR 决策 | 新增 `ADR-0005-langgraph-agentic-workflow-runtime.md`，以 `proposed` 状态冻结 Option C 的执行前提和回滚边界 |
| 文档权威 | 本目录仅是 planning evidence；`docs/tmp` 只是输入 | 本目录仍是 planning evidence；PR2 可引用 README、01、02、16 和 ADR-0005 的 PR2 允许部分，但不得绕过 active docs |
| PR2 readiness | 只能说明“方向建议” | 明确硬条件、fallback 条件、raw-off policy、checkpoint 非事实源、PR2 启动检查清单和 active docs 回写矩阵 |
| AIFI-BE-002 DONE 语义 | 容易被误读为重构完成 | 明确只代表 PR1 skeleton / planning package DONE，不代表 implementation DONE |

## 3.2 Implementation-ready 判定标准

PR1.5 达到 implementation-ready 只表示 PR2 可以启动 AI Runtime 基础层的受控实现，不表示 PR3-PR8 可以同时展开。判定标准如下：

1. `01_ARCHITECTURE_OPTIONS.md` 已给出 Option A / B / C 的硬条件、fallback 条件、禁止进入主干条件、权重和得分矩阵。
2. `02_RECOMMENDED_ARCHITECTURE.md` 已定义路径级架构图解释、runtime event flow、business handoff flow、replay/resume write policy、raw-off payload policy 和可见数据矩阵。
3. `16_DESIGN_DOCS_REFACTOR_PLAN.md` 已把回写目标精确到 active doc 章节、PR 编号和冲突优先级。
4. ADR-0005 以 `proposed` 状态记录 Option C 长期架构决策候选、边界、回滚和 active docs backfill。
5. PR2 的允许依据被限制为 AI Runtime data / migration / rollback / raw-off trace 基础，不允许直接迁移业务 graph 或前端 timeline。
6. `docs/tmp` 继续只作输入证据；执行依据必须来自 active docs、已登记 ADR、BACKLOG / DELIVERY_PLAN 和本专题中已标注可指导 PR2 的部分。

## 4. 目标输出

PR1 输出以下规划包：

| 顺序 | 文档 | 用途 |
|---|---|---|
| 00 | `00_SUBAGENT_RECON_REPORT.md` | 汇总 SubAgent 只读发现、冲突和主 Agent 决策 |
| 01 | `01_ARCHITECTURE_OPTIONS.md` | 比较 Option A / B / C |
| 02 | `02_RECOMMENDED_ARCHITECTURE.md` | 固化推荐架构骨架 |
| 03 | `03_TARGET_DIRECTORY_STRUCTURE.md` | 规划前后端目标目录边界 |
| 04-05 | backend runtime / LLM trace plan | 规划 agent runtime、trace、payload policy |
| 06-09 | graph plans | 规划各业务 graph |
| 10-11 | data / API plan | 规划 runtime 表、migration 和 endpoint |
| 12-15 | frontend / tests / validation | 规划前端实现、测试和验证 |
| 16-17 | docs refactor / PR sequence | 规划 active docs 回写和 PR1-PR8 拆分 |
| 18 | `18_LANGGRAPH_DEPENDENCY_AND_SPIKE_PLAN.md` | 规划 LangGraph / LangGraph checkpointer / serializer / fake graph spike 的 PR4-LG-DEP 依赖引入门槛 |

推荐阅读顺序：README -> 00 -> 01 -> 02 -> 03 -> 04 -> 10 -> 11 -> 06-09 -> 05 -> 12 -> 13-15 -> 16 -> 17 -> 18。

## 5. 必须覆盖范围

PR1 必须覆盖：

- 文档治理登记：`BACKLOG.md` 新增 AIFI 任务，`DOCS_INDEX.md` 登记专题包。
- AI / 非 AI 双域边界：Core Business、AI Runtime、shared infrastructure。
- Option A / B / C 比较与 Option C 推荐。
- 后端 agent runtime、LLM trace、data model、API schema 骨架。
- 全部 graph skeleton：resume、job match、polish、pressure、report、review、weakness、asset、training、confirmation interrupt。
- 前端 AI task / agent run / timeline / interrupt / candidate confirmation UI skeleton。
- 后端、前端、分阶段验证和 active docs 回写计划。
- PR1-PR8 Scope / Allowed files / Forbidden files / Tests / Validation / Rollback / DoD。

## 6. 与 active docs 的关系

本目录是专题设计包，不替代 active canonical docs。后续 PR 只能把本包作为 planning evidence 使用；一旦结论需要长期生效，必须按 `16_DESIGN_DOCS_REFACTOR_PLAN.md` 回写到对应 active docs 或 ADR。

必须回写的长期事实包括：

- `APPLICATION_FLOW_SPEC.md`：facade、agent run、interrupt/resume、timeline、handoff。
- `PERSISTENCE_MODEL.md` / `DATA_MODEL.md`：Core Business Tables、AI Runtime Tables、LangGraph Checkpoint Tables。
- `API_SPEC.md`：Agent Runtime API 和 sanitized LLM summary API。
- `PROMPT_SPEC.md` / `prompt-contracts/*.md`：contract 到 graph/node 的执行映射。
- `SECURITY_PRIVACY.md`：raw payload、checkpoint、timeline、trace、retention 和 audit 边界。

权威优先级如下：

| 优先级 | 文档 | 规则 |
|---:|---|---|
| 1 | `AGENTS.md`、`DOCS_INDEX.md`、`BACKLOG.md`、`DELIVERY_PLAN.md`、已登记 ADR | 决定治理边界、任务状态、阶段和长期架构决策 |
| 2 | `docs/02-design/*` 和 `prompt-contracts/*.md` active docs | 决定 API、数据、Prompt、安全、应用编排和持久化事实 |
| 3 | 本专题 `README`、`01`、`02`、`16`、`17` 中标注为 PR2-ready 的部分 | 只能作为 PR2 实施输入，且不得与 active docs 冲突 |
| 4 | 本专题其他 planning 文档 | 作为 PR3-PR8 planning evidence，需在对应 PR 回写 active docs 后才能成为执行依据 |
| 5 | `docs/tmp/*` | 临时输入，不作为 canonical 或执行依据 |

## 7. 非目标

- 不做 PR2-PR8 实现。
- 不修改 `apps/**`、`tests/**`、依赖文件、migration 文件、业务代码、前端代码或后端代码。
- 不调用真实 LLM provider。
- 不新增 roadmap、plan-v2、latest-plan、codex-plan 或并行任务体系。
- 不把 `archive/` 或 `docs/tmp` 当作当前执行依据。
- 不把 ADR-0005 的 `proposed` 状态误读为 active docs 已完成回写；PR2 只能按该 ADR 的 Boundaries 和 Follow-up backfill 执行。

## 8. 后续 PR 使用方式

| PR | 使用方式 |
|---|---|
| PR2 | 可依据 `01`、`02`、`04`、`05`、`10`、`16`、ADR-0005 的 PR2 部分，落 AI Runtime 基础模型、migration/rollback、checkpoint ref 和 raw-off trace policy；不得迁移业务 graph |
| PR3 | 需先回写 `APPLICATION_FLOW_SPEC.md` / `API_SPEC.md` 后，再依据 `04`、`11` 落 `AiOrchestrationFacade`、`AgentGraphRunner` port 和 API command/result contract |
| PR4 | 需先回写 runtime API / checkpoint / interrupt policy 后，再依据 `04`、`05`、`10`、`11`、`18` 落 LangGraph adapter、fake graph、checkpoint、interrupt/resume、timeline；依赖引入必须走 `PR4-LG-DEP` gate |
| PR5 | 依据 `06` 前必须补 `PROMPT_SPEC.md` / `prompt-contracts` 的 Job Match graph execution mapping |
| PR6 | 依据 `07` 前必须补 Polish question / feedback graph execution mapping 和 answer-save-no-LLM 边界 |
| PR7 | 依据 `12`、`14` 前必须补 `UX_SPEC.md` / `UI_DESIGN_SYSTEM.md` 的 timeline、interrupt、candidate confirmation 可见状态 |
| PR8 | 依据 `08`、`09`、`13`、`15` 前必须补 Report / Review / Candidate Closure 的 active docs 回写和 release/security 验收输入 |

PR1.5 后可直接指导 PR2 的文档：`README.md`、`01_ARCHITECTURE_OPTIONS.md`、`02_RECOMMENDED_ARCHITECTURE.md`、`04_BACKEND_AGENT_RUNTIME_PLAN.md` 中 runtime skeleton 部分、`05_BACKEND_LLM_TRACE_PERSISTENCE_PLAN.md`、`10_DATA_MODEL_AND_MIGRATION_PLAN.md`、`16_DESIGN_DOCS_REFACTOR_PLAN.md` 中 PR2 行、ADR-0005 的 Boundaries / Follow-up backfill。

PR1.5 后仍只能作为 planning evidence 的文档：`06`、`07`、`08`、`09`、`11`、`12`、`13`、`14`、`15`、`17` 中涉及业务 graph、Agent Runtime API 细节、frontend UI 和验证命令的部分；这些内容必须在对应 PR 回写 active docs 或形成代码 / 测试证据后才能指导实现。

## 8.1 PR2 启动前检查清单

PR2 启动前必须逐项满足：

| 检查项 | 通过标准 | 未通过处理 |
|---|---|---|
| repo scope | 当前窗口只授权 PR2 文件；无未解释 staged / unstaged 改动影响 PR2 | 停止并请求主 Agent 重新锁定 scope |
| ADR 状态 | ADR-0005 存在且 status 为 `proposed`；PR2 仅执行其 Boundaries 内事项 | 若 ADR 缺失或被拒绝，PR2 不得按 Option C 写 runtime schema |
| active docs 关系 | 未把本专题或 `docs/tmp` 写成替代 active docs | 回到 16 补回写矩阵或请求主 Agent 汇总 |
| checkpoint policy | checkpoint 仅用于 resume/replay/debug，业务读取不以 checkpoint payload 为事实源 | PR2 禁止落 checkpoint payload business read path |
| raw-off policy | schema、日志、trace、API response 均无 raw prompt/raw completion/provider payload 字段 | 阻断 PR2，先修 data/API/security plan |
| migration/rollback | migration plan 包含 in-flight task、candidate/formal、trace/audit、source availability rollback 检查 | PR2 不得提交不可回滚 runtime 表 |
| boundary tests | PR2 计划包含 Core 不 import LangGraph、raw-off、owner scoped runtime refs 的测试 | 缺测试时不得标记 PR2 implementation-ready |

## 9. Definition of Done

- `BACKLOG.md` 已新增 PR1 对应 AIFI 任务。
- `DOCS_INDEX.md` 已登记本专题包且明确不替代 active docs。
- 本目录创建完整规划文档清单。
- 每份文档都包含目的、输入、状态、输出、覆盖范围、active docs 关系、非目标、后续 PR 用法和 DoD。
- 所有 PR2-PR8 内容只停留在规划骨架，不实现代码。
- 验证命令至少覆盖 `git status --short --untracked-files=all`、`git diff --stat`、`git diff --check` 和最小 doc governance gate。

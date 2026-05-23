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

已冻结的 PR1 规划边界：

- 推荐 Option C：LangGraph-first Agentic Workflow Runtime。
- 仍采用单后端微服务，不拆出独立 AI service。
- Core Business 不依赖 LangGraph、AgentState、graph node 或 checkpoint schema。
- Core UseCase 只通过 `AiOrchestrationFacade` 触达 AI Runtime。
- LangGraph checkpoint 不是业务事实源。
- LLM node 不直接写 formal object。
- candidate / suggestion 不能静默升级为 formal object。
- raw prompt、raw completion、provider payload 不进入普通日志、checkpoint 或 API response。

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

推荐阅读顺序：README -> 00 -> 01 -> 02 -> 03 -> 04 -> 10 -> 11 -> 06-09 -> 05 -> 12 -> 13-15 -> 16 -> 17。

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

## 7. 非目标

- 不做 PR2-PR8 实现。
- 不修改 `apps/**`、`tests/**`、依赖文件、migration 文件、业务代码、前端代码或后端代码。
- 不调用真实 LLM provider。
- 不新增 roadmap、plan-v2、latest-plan、codex-plan 或并行任务体系。
- 不把 `archive/` 或 `docs/tmp` 当作当前执行依据。
- 不创建 ADR；若 Option C 后续确认为长期架构决策，由后续受权 PR 写入 `docs/04-decisions/ADR-*.md`。

## 8. 后续 PR 使用方式

| PR | 使用方式 |
|---|---|
| PR2 | 依据 04、05、10 落 AI Runtime 基础模型、migration/rollback 和 raw-off trace policy |
| PR3 | 依据 04、11 落 `AiOrchestrationFacade`、`AgentGraphRunner` port 和 API command/result contract |
| PR4 | 依据 04、05、10、11 落 LangGraph adapter、fake graph、checkpoint、interrupt/resume、timeline |
| PR5 | 依据 06 落 Job Match Graph |
| PR6 | 依据 07 迁移 Polish Question / Feedback Graphs |
| PR7 | 依据 12、14 落 Frontend AI Runtime UI |
| PR8 | 依据 08、09、13、15 闭合 Report / Review / Candidate Closure |

## 9. Definition of Done

- `BACKLOG.md` 已新增 PR1 对应 AIFI 任务。
- `DOCS_INDEX.md` 已登记本专题包且明确不替代 active docs。
- 本目录创建完整规划文档清单。
- 每份文档都包含目的、输入、状态、输出、覆盖范围、active docs 关系、非目标、后续 PR 用法和 DoD。
- 所有 PR2-PR8 内容只停留在规划骨架，不实现代码。
- 验证命令至少覆盖 `git status --short --untracked-files=all`、`git diff --stat`、`git diff --check` 和最小 doc governance gate。


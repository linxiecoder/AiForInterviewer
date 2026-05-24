---
title: Backend Function Packages README
type: delivery-planning
status: draft-f5-langgraph-implementation-consolidation
owner: 后端架构 / AI 架构
permalink: ai-for-interviewer/docs/03-delivery/refactor-multiagent-langgraph-implementation/backend-function-packages/readme
---

# Backend Function Packages README

## 1. 文档定位

本文件是 backend function packages 的索引。根 `../README.md` 仍是整个 implementation set 的唯一入口。

Backend function package docs 承载 method-level、field-level、Agent / Graph / Prompt / Skill / Trace implementation plans。后端 PR 执行时必须先读取根 README、`02_BACKEND_REFACTOR_MASTER_PLAN.md`，再读取对应 package。

## 2. Package 清单

| Package | 文件 | 主要 PR | 职责 |
|---|---|---:|---|
| AI Runtime Infra | `01_AI_RUNTIME_INFRA_PACKAGE.md` | PR3 / PR4 | Facade、runner port、registry、guard、handoff、interrupt、LangGraph adapter contract |
| LLM Trace / Persistence | `02_LLM_TRACE_PERSISTENCE_PACKAGE.md` | PR2 / PR4 | Runtime tables、LLM trace、payload、repository、retention、raw-off tests |
| Job Match Agent | `03_JOB_MATCH_AGENT_PACKAGE.md` | PR6 if still needed | PR2-PR5 只允许 descriptor / DTO / trace-compatible wrapper / placeholder；完整 JobMatch / ResumeAnalysis graph 只能在 PR6 决策仍需要后实施 |
| Polish Agent | `04_POLISH_AGENT_PACKAGE.md` | PR5 | Polish first migration target；progress tree、question、feedback graph、answer-save boundary |
| Pressure Agent | `05_PRESSURE_AGENT_PACKAGE.md` | PR8 or separate authorized Pressure PR | Pressure session lifecycle、turn loop、pace、end condition、report input |
| Report / Review Agent | `06_REPORT_REVIEW_AGENT_PACKAGE.md` | PR8 | Report generation、mock review、real review、copy boundary、privacy redaction |
| Candidate / Skill / Training | `07_CANDIDATE_SKILL_TRAINING_PACKAGE.md` | PR8 | Candidate schema、Skill mapping、confirmation interrupt、formal write handoff、training suggestion |

## 3. 跨包硬规则

| Rule | Required behavior |
|---|---|
| owner scope | All runtime, graph, trace, interrupt, candidate and confirmation reads/writes require owner-scoped access |
| raw-off | logs、checkpoint、API response 或普通 trace 中不得出现 raw prompt、raw completion、provider payload、system prompt、token、cookie、secret 或 hidden scoring rule |
| checkpoint | Checkpoint is runtime recovery only; never business truth source |
| candidate/formal | Graphs may create candidate/suggestion refs; formal write requires Core command or explicit user confirmation |
| real provider | 除非后续 PR 明确授权且 real-provider gates 满足，否则不得调用 real provider |
| PR2 | PR2 cannot use package docs to expand beyond exact `20_PR2_PREFLIGHT_READINESS_REPORT.md` scope |
| PR order | PR5 是 Polish first migration target；PR6 才评估 JobMatch / ResumeAnalysis trace-compatible wrapper 或 graph；PR7 是 Frontend；PR8 是 Pressure / Report / Review / Candidate / Skill / Training closure |

## 4. Package 使用规则

1. 只读取当前 PR 需要的 package，避免把 later PR 计划提前执行。
2. Package 中的 method / field / graph 计划是 implementation guidance，不替代 active `API_SPEC.md`、`DATA_MODEL.md`、`PROMPT_SPEC.md` 或 `SECURITY_PRIVACY.md`。
3. 当 package 与 active docs 冲突时，停止并回到 `BACKLOG.md` / active docs / accepted risk 流程。
4. 每个 PR 结束时只声明该 PR 范围内的 package 项通过，不声明完整 MultiAgent 完成。

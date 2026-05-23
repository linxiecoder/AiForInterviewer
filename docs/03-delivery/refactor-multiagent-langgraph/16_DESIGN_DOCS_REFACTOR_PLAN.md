---
title: 设计文档输出与重构计划
type: delivery-planning
status: draft-pr1
owner: 项目交付
permalink: ai-for-interviewer/docs/03-delivery/refactor-multiagent-langgraph/design-docs-refactor-plan
---

# 设计文档输出与重构计划

## 1. 文档目的

本文说明 LangGraph MultiAgent 重构后如何回写 active docs，避免专题设计包变成并行事实源。

## 2. 输入来源

- `AGENTS.md`
- `docs/00-governance/DOCS_INDEX.md`
- `docs/00-governance/DOCS_GOVERNANCE.md`
- active design docs：`APPLICATION_FLOW_SPEC.md`、`PERSISTENCE_MODEL.md`、`DATA_MODEL.md`、`PROMPT_SPEC.md`、`SCORING_SPEC.md`、`SECURITY_PRIVACY.md`、`API_SPEC.md`、`UX_SPEC.md`、`UI_DESIGN_SYSTEM.md`
- `prompt-contracts/*.md`
- 本专题 PR1 规划包

## 3. 当前状态

`docs/tmp` 是临时输入；本目录是 PR1 planning package；active facts 仍在 `docs/02-design/*`、`docs/03-delivery/*` 和已登记 ADR 中。

## 4. 目标输出

输出：

- 文档变更矩阵占位。
- source of truth 决策占位。
- 哪些内容留在专题设计包。
- 哪些内容必须回写 active docs。
- archive 规则。
- 文档验收标准。

## 5. 必须覆盖范围

### 5.1 文档变更矩阵占位

| Active doc | 必须回写内容 | 保留在专题包的内容 | 回写 PR |
|---|---|---|---|
| `APPLICATION_FLOW_SPEC.md` | `AiOrchestrationFacade`、AgentRun、interrupt/resume、timeline、persistence handoff | PR1 比较材料、SubAgent recon | PR3/PR4 |
| `PERSISTENCE_MODEL.md` | Core tables / AI runtime tables / checkpoint tables 分离；migration/rollback handoff | 字段草案备忘 | PR2 |
| `DATA_MODEL.md` | `AgentRun`、`AgentNodeRun`、`AgentInterrupt`、`LlmCall`、checkpoint ref 关系 | 早期表格草案 | PR2 |
| `PROMPT_SPEC.md` | contract 到 graph/node 的执行映射；trace context | Option 比较 | PR5-PR8 |
| `SCORING_SPEC.md` | graph 评分节点不得绕过 `ScoreRuleVersion`；score result handoff | graph skeleton | PR5/PR6/PR8 |
| `SECURITY_PRIVACY.md` | checkpoint、timeline、LLM trace、debug data、redaction、retention、raw-off | 风险草案 | PR2/PR4/PR8 |
| `prompt-contracts/**` | 仅补已登记 contract 的 graph execution mapping | 未确认 graph 选项 | PR5-PR8 |
| `API_SPEC.md` | `/ai-tasks`、`/agent-runs`、timeline、interrupt resume、LLM summary、report/review generation | endpoint 草案比较 | PR3/PR4/PR8 |
| `UX_SPEC.md` | AI task status、timeline、interrupt、candidate confirmation、low confidence、validation failed | PR7 UI planning | PR7 |
| `UI_DESIGN_SYSTEM.md` | runtime status badge、timeline、drawer、banner、panel 状态规则 | 组件草案 | PR7 |
| `DELIVERY_PLAN.md` | 仅在阶段/里程碑需要调整时更新 | PR breakdown 证据 | 受权后 |
| `BACKLOG.md` | AIFI 任务状态和后续任务 | 规划细节 | PR1 起 |
| `DOCS_INDEX.md` | 专题包登记和 active/证据边界 | 无 | PR1 起 |
| `ADR-*` | Option C 若长期架构决策需保存 | 方案比较细节 | 受权后 |

### 5.2 Source of truth 决策占位

| 事实类型 | Source of truth | 本专题包角色 |
|---|---|---|
| 产品需求 | `PRD.md` | 不改写 |
| API 字段 | `API_SPEC.md` | 草案输入 |
| 数据模型 | `DATA_MODEL.md` / `PERSISTENCE_MODEL.md` | 草案输入 |
| Prompt contract | `PROMPT_SPEC.md` / `prompt-contracts/*.md` | execution mapping 草案 |
| 安全隐私 | `SECURITY_PRIVACY.md` | 风险和验证补充 |
| 交付任务 | `BACKLOG.md` | PR1 已登记 |
| 长期架构决策 | ADR | 后续候选 |

### 5.3 Archive 规则

本专题包不移动 archive 文件。若后续任何文件下线，必须登记 `archive/MANIFEST.md`，并说明原路径、归档路径、原因、替代路径、状态和阻断条件。

## 6. 与 active docs 的关系

专题包只能作为 staging evidence。active docs 回写后才是执行依据；不得引用 `docs/tmp` 或本目录绕过 active docs。

## 7. 非目标

- 不把 `docs/tmp` 迁为 canonical。
- 不创建 roadmap-v2。
- 不把 archive/review docs 当当前事实。
- 不在 PR1 修改 `docs/02-design/**`。

## 8. 后续 PR 使用方式

PR2-PR8 在实现证据稳定后最小回写 active docs。每次回写必须说明：来源、目标 active doc、变更事实、验证命令、是否需要 ADR。

## 9. Definition of Done

- 回写矩阵覆盖用户指定 active docs。
- 明确哪些留在专题包、哪些回写 active docs。
- archive 规则明确。
- 专题包不成为并行事实源。


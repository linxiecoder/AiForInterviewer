---
title: ADR-0003-high-fidelity-design-tooling
type: decision
status: proposed
owner: 文档治理
date: 2026-05-05
permalink: ai-for-interviewer/docs/04-decisions/adr-0003-high-fidelity-design-tooling
---

# ADR-0003: Use OpenDesign as a high-fidelity exploration tool

## Status

Proposed

## Context

当前项目处于 F3 / AIFI-UI-001 阶段。docs/02-design/UI_DESIGN_SYSTEM.md 是 F3 设计系统草案和当前设计规范事实源。Figma 仍是最终高保真稿、Prototype 和 M3 高保真评审的主证据。

团队希望引入 OpenDesign 作为高保真视觉方向、页面草稿、组件方案的探索工具，以提高设计探索效率。

该工具不得覆盖 active docs，不得替代 Figma，不得作为 M3 评审的单独通过证据。

## Decision

采用方案 B：OpenDesign 作为高保真探索工具。

决策如下：

- OpenDesign 可用于生成候选高保真视觉方向。
- OpenDesign 可用于探索页面布局、组件风格、报告页、工作台、Dashboard 等候选方案。
- OpenDesign 输出默认状态为 CANDIDATE / UNVERIFIED / NOT_ACTIVE_SOURCE。
- OpenDesign 输出必须经过 Claude Code 审计和人工确认后，才能进入 Figma 或 active docs。
- Figma 仍是 M3 高保真评审主证据。
- docs/02-design/UI_DESIGN_SYSTEM.md 仍是 F3 设计系统规范事实源。
- M3 评审不得只依据 OpenDesign artifact。

## Non-goals

明确禁止：

- 不允许 OpenDesign 直接修改 PRD.md。
- 不允许 OpenDesign 直接修改 UX_SPEC.md。
- 不允许 OpenDesign 直接修改 UI_DESIGN_SYSTEM.md。
- 不允许 OpenDesign 直接修改 BACKLOG.md 或 DELIVERY_PLAN.md。
- 不允许 OpenDesign 生成物直接作为 M3 通过证据。
- 不允许 OpenDesign 输出替代 Figma Prototype。
- 不允许把 OpenDesign 视觉稿写成已验证事实。
- 不允许 OpenDesign 输出绕过 WARN / UNKNOWN / CONFLICT 台账。

## Required Review Workflow

1. Generate Candidate  
   OpenDesign 生成候选视觉方向或页面草稿。

2. Mark as Candidate  
   产物必须标记为 CANDIDATE / UNVERIFIED / NOT_ACTIVE_SOURCE。

3. Claude Code Audit  
   对照 PRD.md、UX_SPEC.md、UI_DESIGN_SYSTEM.md 审计候选输出。

4. Human Review  
   人工确认是否采纳。

5. Figma Translation  
   被采纳内容进入 Figma 高保真稿。

6. Active Docs Update  
   如需更新 UI_DESIGN_SYSTEM.md，必须单独授权。

7. M3 Review  
   以 Figma Prototype、UI_DESIGN_SYSTEM.md、WARN / UNKNOWN / CONFLICT 台账关闭情况作为 M3 依据。

## Acceptance Criteria

- OpenDesign 输出不得自动进入 active docs。
- OpenDesign 输出不得自动成为 Figma 最终稿。
- 所有采纳内容必须能追溯到 PRD.md、UX_SPEC.md 或 UI_DESIGN_SYSTEM.md。
- 所有偏离 active docs 的内容必须标记 WARN / CONFLICT。
- 所有无法验证的内容必须标记 UNKNOWN。
- M3 评审不得只依据 OpenDesign artifact。
- Figma 高保真稿和 Prototype 仍是 M3 主证据。
- UI_DESIGN_SYSTEM.md 仍是设计系统规范事实源。

## Consequences

正向影响：

- 可提高高保真探索效率。
- 可快速生成多个视觉方向。
- 可辅助 UI_DESIGN_SYSTEM.md 的组件风格探索。
- 可在进入 Figma 前提前发现视觉方向和布局问题。

负向影响：

- 需要额外审计环节。
- 可能产生与 active docs 不一致的候选方案。
- 可能诱导团队把候选稿误认为已验证设计事实。
- 不能替代 Figma、Prototype 和 M3 评审。

## Risks

### MUST

- OpenDesign 输出不得覆盖 PRD.md、UX_SPEC.md、UI_DESIGN_SYSTEM.md。
- OpenDesign 输出不得成为 M3 单独通过证据。
- OpenDesign 输出不得绕过 Claude Code 审计和人工确认。
- OpenDesign 输出不得替代 Figma Prototype。

### SHOULD

- OpenDesign 候选稿应明确标记 CANDIDATE / UNVERIFIED。
- 被采纳内容应进入 Figma 后再参与 M3 评审。
- 与 active docs 不一致的内容应登记 WARN / CONFLICT。
- 无法验证的内容应登记 UNKNOWN。

### COULD

- OpenDesign 可用于探索工作台、报告页、Dashboard、组件视觉方向。
- OpenDesign 可用于生成对比方案或视觉草稿。

### LATER

- 后续可评估是否将 OpenDesign 试运行流程写入 AI_WORKFLOW.md。
- 后续可评估是否新增 AIFI-* 任务追踪设计工具链。
- 后续可评估是否创建 .mcp.json 或其他工具配置；本 ADR 不授权执行。

## Follow-up

后续如需真正接入工具，需要单独授权：

- 是否安装 OpenDesign。
- 是否创建 .mcp.json。
- 是否更新 docs/00-governance/AI_WORKFLOW.md。
- 是否新增 AIFI-* 任务。
- 是否纳入 CI 或脚本审计。
- 是否登记到 docs/00-governance/DOCS_INDEX.md。

ADR-0003 已在后续授权中登记到 docs/00-governance/DOCS_INDEX.md。OpenDesign 仍仅作为 F3 高保真探索工具，不改变 Figma Prototype、UI_DESIGN_SYSTEM.md 和 M3 评审主证据地位。

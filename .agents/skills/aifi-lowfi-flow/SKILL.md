---
name: aifi-lowfi-flow
description: Plan or review AiForInterviewer low-fidelity UX flows against PRD scenarios, page states, exception paths, and F2 acceptance evidence.
---

# aifi-lowfi-flow

## Purpose

规划或审阅 F2 低保真用户流程，确保 `UX_SPEC.md` 覆盖 PRD 场景、页面状态和异常路径。

## Applicable phases

- F2 低保真设计
- M2 低保真评审通过

## Required context

1. 先读取 `AGENTS.md`、`AGENTS.md`、`docs/00-governance/DOCS_INDEX.md`。
2. 必须读取 `docs/01-product/PRD.md`、`docs/02-design/UX_SPEC.md`、`docs/03-delivery/BACKLOG.md`、`docs/03-delivery/DELIVERY_PLAN.md`。
3. 默认先运行或建议 `/aifi-drift-check`。
4. 未读取事实标记为 `UNKNOWN`。

## Delegatable SubAgents

- `aifi-ux-flow-designer`
- `aifi-product-requirements-owner`

## Execution steps

1. 确认 `UX_SPEC.md` 已登记为 F2 active 入口。
2. 对照 PRD 场景检查主路径和异常路径。
3. 检查页面、状态、文案和交互是否能支撑验收。
4. 输出 F2 低保真缺口与待确认项。

## Forbidden actions

- 不得假设 Figma 内容；未接入 Figma MCP 时标记 `UNKNOWN`。
- 不得创建新 roadmap、临时计划入口或并行任务体系。
- 不得把 `archive/` 作为当前执行依据。
- 不得修改 `docs/` 或 `archive/`，除非当前任务明确授权。

## Output format

- `## 结论`
- `## 证据`
- `## 风险`
- `## 待处理文件`
- `## 下一步动作`

## Acceptance criteria

- 每个 UX 覆盖判断引用 PRD、UX 或 BACKLOG 证据。
- 主路径、异常路径和 `UNKNOWN` 输入均被区分。
- Figma 未读取时不得声称已核验设计稿。

## Risk markers

- PRD 场景未映射到 UX 流程。
- 页面状态缺失。
- 异常路径未定义。
- Figma 状态未知。

## Recommended read-only commands

```bash
git status --short --ignored
grep -RIn "UNKNOWN\|待核查\|AIFI-" docs/01-product docs/02-design docs/03-delivery 2>/dev/null || true
```

## Write authorization rules

默认只读。低保真设计更新必须进入 `docs/02-design/UX_SPEC.md`，任务补充必须进入 `docs/03-delivery/BACKLOG.md`，且需要当前任务明确授权。

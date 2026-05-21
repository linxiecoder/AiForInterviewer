---
name: aifi-ui-consistency-check
description: Check AiForInterviewer frontend UI against UX_SPEC, UI design system, Figma registration, component states, copy, and interaction evidence.
---

# aifi-ui-consistency-check

## Purpose

检查前端 UI 与 `UX_SPEC.md`、UI 设计系统、Figma 登记、组件状态、文案和交互证据的一致性。

## Applicable phases

- F3 高保真设计与设计系统
- F6 前端开发
- F7 联调、测试与质量加固

## Required context

1. 先读取 `AGENTS.md`、`AGENTS.md`、`docs/00-governance/DOCS_INDEX.md`。
2. 必须读取 `docs/02-design/UX_SPEC.md`、`docs/03-delivery/BACKLOG.md`。
3. 如 UI 设计系统已创建且登记，再读取；否则标记 `UNKNOWN`。
4. 读取相关前端代码和测试。
5. 默认先运行或建议 `/aifi-drift-check`。

## Delegatable SubAgents

- `aifi-ui-consistency-reviewer`
- `aifi-figma-ux-auditor`

## Execution steps

1. 确认 UX 和设计系统 active 状态。
2. 对照前端代码检查页面、组件、状态和文案。
3. Figma MCP 未接入时仅检查仓库登记。
4. 输出 UI 偏差、待核查项和修复建议。

## Forbidden actions

- 不得假设 Figma 内容。
- 不得调用不存在的 Figma MCP tool。
- 不得创建新 roadmap、临时计划入口或并行任务体系。
- 不得直接修改文件，除非当前任务明确授权。

## Output format

- `## 结论`
- `## 证据`
- `## 风险`
- `## 待处理文件`
- `## 下一步动作`

## Acceptance criteria

- 每条 UI 一致性判断引用设计、代码或测试证据。
- 未验证浏览器行为标记 `待核查`。
- Figma 未接入状态标记 `UNKNOWN`。

## Risk markers

- UI 与 UX 偏离。
- 组件状态缺失。
- 文案不一致。
- Figma 或浏览器行为未验证。

## Recommended read-only commands

```bash
git status --short --ignored
find apps/web/src docs/02-design -maxdepth 4 -type f | sort
grep -RIn "Figma\|component\|组件\|状态\|copy\|文案" apps/web docs/02-design 2>/dev/null || true
```

## Write authorization rules

默认只读。UI 修复只能在明确授权的前端任务范围内修改代码；设计文档更新必须进入已登记 active 文档；任务进入 `BACKLOG.md`。

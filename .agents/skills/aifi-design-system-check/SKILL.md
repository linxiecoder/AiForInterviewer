---
name: aifi-design-system-check
description: Check AiForInterviewer UI design system readiness, component states, UX alignment, and implementation consistency for F3 and later UI work.
---

# aifi-design-system-check

## Purpose

检查 UI 设计系统是否已创建、登记并覆盖 UX 页面、组件、状态和前端实现一致性。

## Applicable phases

- F3 高保真设计与设计系统
- F6 前端开发
- F7 联调、测试与质量加固

## Required context

1. 先读取 `AGENTS.md`、`AGENTS.md`、`docs/00-governance/DOCS_INDEX.md`。
2. 必须读取 `docs/02-design/UX_SPEC.md`。
3. 如 `docs/02-design/UI_DESIGN_SYSTEM.md` 未创建或未登记，标记为 `UNKNOWN`。
4. 涉及实现时读取相关前端代码。
5. 默认先运行或建议 `/aifi-drift-check`。

## Delegatable SubAgents

- `aifi-ui-design-system-owner`
- `aifi-ui-consistency-reviewer`

## Execution steps

1. 确认设计系统文档是否为 active 入口。
2. 对照 UX 检查组件、布局、状态和文案覆盖。
3. 对照前端代码检查实现偏差。
4. 输出设计系统断链、风险和待补项。

## Forbidden actions

- 不得把未登记设计系统文档当作 active 依据。
- 不得假设 Figma 内容。
- 不得创建新 roadmap、临时计划入口或并行任务体系。
- 不得直接修改文件；除非当前任务明确授权。

## Output format

- `## 结论`
- `## 证据`
- `## 风险`
- `## 待处理文件`
- `## 下一步动作`

## Acceptance criteria

- 设计系统状态明确为 active、未登记或 `UNKNOWN`。
- 每条一致性判断引用设计、UX 或代码证据。
- 缺口与 `AIFI-*` 任务关系清晰。

## Risk markers

- 设计系统未登记。
- 组件状态缺失。
- 前端实现偏离 UX。
- Figma 状态未知。

## Recommended read-only commands

```bash
git status --short --ignored
find docs/02-design -maxdepth 1 -type f | sort
grep -RIn "component\|组件\|状态\|AIFI-" docs/02-design apps/web 2>/dev/null || true
```

## Write authorization rules

默认只读。设计系统更新必须进入已登记的 active 设计文档；任务补充必须进入 `docs/03-delivery/BACKLOG.md`；需要当前任务明确授权。

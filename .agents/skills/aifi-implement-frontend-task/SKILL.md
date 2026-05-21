---
name: aifi-implement-frontend-task
description: Implement an authorized AiForInterviewer frontend AIFI task while preserving React, route state, API contract, UX, and UI consistency.
---

# aifi-implement-frontend-task

## Purpose

在明确授权的 `AIFI-*` 任务范围内实现前端变更，并保持 React、路由状态、API 契约、UX 和 UI 一致性。

## Applicable phases

- F6 前端开发
- F7 联调、测试与质量加固

## Required context

1. 先读取 `AGENTS.md`、`AGENTS.md`、`docs/00-governance/DOCS_INDEX.md`。
2. 必须读取 `docs/03-delivery/BACKLOG.md` 中对应 `AIFI-*` 任务。
3. 必须读取 `docs/02-design/UX_SPEC.md`。
4. 如 UI 设计系统或 API 规范已创建且登记，再读取；否则标记 `UNKNOWN`。
5. 读取相关 `apps/web/` 代码和测试。
6. 默认先运行或建议 `/aifi-drift-check`。

## Delegatable SubAgents

- `aifi-frontend-implementer`
- `aifi-ui-consistency-reviewer`

## Execution steps

1. 确认任务授权、UX 范围和验收标准。
2. 定位最小前端修改路径。
3. 实现交互、状态和 API 调用变更。
4. 运行相关 web 测试或 build。
5. 如涉及 UI 行为，启动 dev server 并浏览器验证；无法验证需说明原因。

## Forbidden actions

- 不得修改 `docs/` 或 `archive/`，除非当前任务明确授权。
- 不得创建新 roadmap、临时计划入口或并行任务体系。
- 不得调用不存在的 Figma 或 Playwright MCP tool。
- 不得扩大到无关重构。

## Output format

- `## 结论`
- `## 证据`
- `## 风险`
- `## 待处理文件`
- `## 下一步动作`

## Acceptance criteria

- 前端改动对应明确 `AIFI-*` 任务。
- 测试、build 或浏览器验证结果被报告。
- UX/UI/API 未登记依赖标记 `UNKNOWN`。

## Risk markers

- UI 未浏览器验证。
- API 契约未知。
- 设计系统未登记。
- 前端测试失败或未运行。

## Recommended read-only commands

```bash
git status --short --ignored
find apps/web/src -maxdepth 4 -type f | sort
grep -RIn "AIFI-\|fetch\|route\|state" apps/web docs 2>/dev/null || true
```

## Write authorization rules

只有在当前任务明确授权实现某个 `AIFI-*` 后才能修改 `apps/web/` 或相关测试；任务补充必须进入 `docs/03-delivery/BACKLOG.md`。

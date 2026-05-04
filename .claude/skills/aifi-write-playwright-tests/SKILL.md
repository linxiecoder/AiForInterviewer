---
name: aifi-write-playwright-tests
description: Write authorized AiForInterviewer Playwright tests from code and local command evidence while marking unavailable Playwright MCP evidence as UNKNOWN.
---

# aifi-write-playwright-tests

## Purpose

在明确授权下编写或调整 Playwright 测试；无 Playwright MCP 时仅基于代码、文档和本地命令证据工作。

## Applicable phases

- F7 联调、测试与质量加固
- F8 发布、复盘与下一轮迭代

## Required context

1. 先读取 `CLAUDE.md`、`AGENTS.md`、`docs/00-governance/DOCS_INDEX.md`。
2. 必须读取 `docs/03-delivery/BACKLOG.md` 中对应 `AIFI-*` 任务。
3. 必须读取 `docs/01-product/PRD.md`、`docs/02-design/UX_SPEC.md`。
4. 读取相关 `apps/web/` 代码和现有 E2E 测试。
5. 默认先运行或建议 `/aifi-drift-check`。
6. Playwright MCP 不可用时，浏览器 MCP 证据为 `UNKNOWN`。

## Delegatable SubAgents

- `aifi-qa-e2e-engineer`
- `aifi-regression-analyst`

## Execution steps

1. 确认测试任务、目标路径和授权范围。
2. 对照 PRD/UX 编写主链路或异常路径测试。
3. 使用本地命令运行 E2E 或报告无法运行原因。
4. 对失败输出做最小回归分析。
5. 输出覆盖范围和残余风险。

## Forbidden actions

- 不得调用不存在的 Playwright MCP tool。
- 不得声称完成浏览器 MCP 验证，除非实际可用并执行。
- 不得跳过失败测试或绕过 hooks。
- 不得创建新 roadmap、临时计划入口或并行任务体系。
- 不得修改 `docs/` 或 `archive/`，除非当前任务明确授权。

## Output format

- `## 结论`
- `## 证据`
- `## 风险`
- `## 待处理文件`
- `## 下一步动作`

## Acceptance criteria

- 测试对应明确 `AIFI-*` 任务或发布门禁。
- 命令输出被引用。
- MCP 不可用和未验证路径标记 `UNKNOWN`。

## Risk markers

- E2E 环境不可用。
- 主链路未覆盖。
- 测试不稳定。
- 浏览器验证未完成。

## Recommended read-only commands

```bash
git status --short --ignored
find apps/web -maxdepth 5 -type f | sort
grep -RIn "playwright\|test\|e2e\|AIFI-" apps/web docs 2>/dev/null || true
```

## Write authorization rules

只有在当前任务明确授权 E2E 测试变更时才能修改 Playwright 测试文件；任何任务或测试计划落库必须进入已登记 active 入口。

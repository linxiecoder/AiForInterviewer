---
name: aifi-e2e-plan
description: Plan AiForInterviewer E2E coverage for MVP main flows, exception paths, Playwright readiness, and release quality gates.
---

# aifi-e2e-plan

## Purpose

规划 MVP 主链路、关键异常路径、Playwright 覆盖和发布质量门禁的 E2E 测试范围。

## Applicable phases

- F7 联调、测试与质量加固
- F8 发布、复盘与下一轮迭代

## Required context

1. 先读取 `CLAUDE.md`、`AGENTS.md`、`docs/00-governance/DOCS_INDEX.md`。
2. 必须读取 `docs/01-product/PRD.md`、`docs/02-design/UX_SPEC.md`、`docs/03-delivery/BACKLOG.md`。
3. 如 `TEST_PLAN.md` 或发布清单已创建且登记，再读取；否则标记 `UNKNOWN`。
4. 读取相关前端测试和应用入口。
5. 默认先运行或建议 `/aifi-drift-check`。

## Delegatable SubAgents

- `aifi-qa-e2e-engineer`
- `aifi-product-requirements-owner`

## Execution steps

1. 对照 PRD 和 UX 列出主链路和异常路径。
2. 检查现有 E2E 或测试计划覆盖。
3. 标记环境、数据、浏览器和 MCP 限制。
4. 输出 E2E 覆盖矩阵和发布阻断风险。

## Forbidden actions

- 不得调用不存在的 Playwright MCP tool。
- 不得创建新 roadmap、临时计划入口或并行任务体系。
- 不得修改测试或文档，除非当前任务明确授权。
- 不得把未登记测试计划当作 active 依据。

## Output format

- `## 结论`
- `## 证据`
- `## 风险`
- `## 待处理文件`
- `## 下一步动作`

## Acceptance criteria

- E2E 覆盖结论引用 PRD、UX、任务或测试证据。
- 未运行或 MCP 不可用标记为 `UNKNOWN`。
- 发布阻断风险明确。

## Risk markers

- 主链路无 E2E 覆盖。
- 异常路径缺失。
- 测试环境不可用。
- Playwright MCP 未接入。

## Recommended read-only commands

```bash
git status --short --ignored
find apps/web -maxdepth 4 -type f | sort
grep -RIn "e2e\|playwright\|AIFI-" apps/web docs/03-delivery docs/01-product 2>/dev/null || true
```

## Write authorization rules

默认只读。E2E 计划若需落库，必须写入已登记 active 测试文档或 `BACKLOG.md` 任务；测试代码变更需要当前任务明确授权。

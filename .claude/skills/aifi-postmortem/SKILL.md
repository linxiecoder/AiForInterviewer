---
name: aifi-postmortem
description: Prepare AiForInterviewer postmortem inputs from release evidence, regression analysis, residual risks, follow-up AIFI tasks, and next-iteration recommendations.
---

# aifi-postmortem

## Purpose

整理发布后复盘输入，包括发布证据、回归分析、残余风险、后续 `AIFI-*` 任务和下一轮迭代建议。

## Applicable phases

- F8 发布、复盘与下一轮迭代

## Required context

1. 先读取 `CLAUDE.md`、`AGENTS.md`、`docs/00-governance/DOCS_INDEX.md`。
2. 必须读取 `docs/03-delivery/DELIVERY_PLAN.md`、`docs/03-delivery/BACKLOG.md`。
3. 按任务读取发布清单、测试计划、安全审阅和回归输出；未登记则标记 `UNKNOWN`。
4. 默认先运行或建议 `/aifi-drift-check`。

## Delegatable SubAgents

- `aifi-release-manager`
- `aifi-regression-analyst`

## Execution steps

1. 汇总已验证发布事实和未验证项。
2. 汇总回归、风险、阻断项和缓解措施。
3. 提出后续 `AIFI-*` 任务候选和优先级建议。
4. 标记需要用户确认的长期决策或 ADR 候选。
5. 输出复盘输入，不直接创建新计划体系。

## Forbidden actions

- 不得创建新 roadmap、临时计划入口或并行任务体系。
- 不得把复盘建议当作已批准任务。
- 不得修改共享系统、关闭 issue/PR 或发布内容，除非用户明确授权。
- 不得修改 `docs/` 或 `archive/`，除非当前任务明确授权。

## Output format

- `## 结论`
- `## 证据`
- `## 风险`
- `## 待处理文件`
- `## 下一步动作`

## Acceptance criteria

- 复盘输入引用发布、测试、任务或回归证据。
- 后续工作只作为 `AIFI-*` 候选，不创建并行体系。
- 未验证项标记为 `UNKNOWN`。

## Risk markers

- 发布证据缺失。
- 回归根因未关闭。
- 残余风险未分级。
- 后续任务未落入 `BACKLOG.md`。

## Recommended read-only commands

```bash
git status --short --ignored
git diff --stat
grep -RIn "M8\|发布\|回归\|risk\|风险\|AIFI-" docs apps tests 2>/dev/null || true
```

## Write authorization rules

默认只读。复盘或后续任务落库必须写入已登记 active 文档；任务只能进入 `docs/03-delivery/BACKLOG.md`；重大决策需确认后进入 ADR。

---
name: aifi-prd-freeze
description: Freeze AiForInterviewer MVP PRD scope by checking product requirements, traceability, backlog coverage, and unresolved requirement risks before F1 completion.
---

# aifi-prd-freeze

## Purpose

冻结 F1 MVP 产品需求范围，确认 `PRD.md`、`REQUIREMENT_TRACEABILITY.md` 与 `BACKLOG.md` 的需求关系可追踪。

## Applicable phases

- F1 产品需求冻结
- M1 MVP 需求冻结

## Required context

1. 先读取 `CLAUDE.md`、`AGENTS.md`、`docs/00-governance/DOCS_INDEX.md`。
2. 必须读取 `docs/01-product/PRD.md`、`docs/01-product/REQUIREMENT_TRACEABILITY.md`、`docs/03-delivery/BACKLOG.md`、`docs/03-delivery/DELIVERY_PLAN.md`。
3. 默认先运行或建议 `/aifi-drift-check`。
4. 未读取事实标记为 `UNKNOWN`。

## Delegatable SubAgents

- `aifi-product-requirements-owner`
- `aifi-requirements-traceability-auditor`

## Execution steps

1. 确认目标文档已登记且可作为 active 入口。
2. 对照 PRD 范围、历史需求追踪和 `AIFI-*` 任务覆盖。
3. 标记未决策需求、范围冲突和缺失验收标准。
4. 输出是否满足 M1 冻结条件。

## Forbidden actions

- 不得创建新 roadmap、临时计划入口或并行任务体系。
- 不得把 `archive/` 作为当前执行依据。
- 不得绕过 `BACKLOG.md` 直接新增任务。
- 不得修改 `docs/` 或 `archive/`，除非当前任务明确授权。

## Output format

- `## 结论`
- `## 证据`
- `## 风险`
- `## 待处理文件`
- `## 下一步动作`

## Acceptance criteria

- 每条冻结判断引用本轮读取文件路径。
- 需求、历史来源和 `AIFI-*` 任务关系清晰。
- 未验证内容均标记为 `UNKNOWN` 或 `待核查`。

## Risk markers

- PRD 未登记或内容缺失。
- 历史需求未追踪。
- 需求无 `AIFI-*` 承接任务。
- 存在未决策 MVP 范围。

## Recommended read-only commands

```bash
git status --short --ignored
grep -RIn "AIFI-" docs/01-product docs/03-delivery 2>/dev/null || true
```

## Write authorization rules

默认只读。需求更新必须进入 `docs/01-product/PRD.md`，历史需求处理必须进入 `docs/01-product/REQUIREMENT_TRACEABILITY.md`，任务必须进入 `docs/03-delivery/BACKLOG.md`，且需要当前任务明确授权。

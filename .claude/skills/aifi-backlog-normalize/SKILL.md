---
name: aifi-backlog-normalize
description: Normalize AiForInterviewer BACKLOG entries against delivery phases, milestones, priorities, and PRD traceability without creating parallel task systems.
---

# aifi-backlog-normalize

## Purpose

规范化 `BACKLOG.md` 中的 `AIFI-*` 任务，确保任务、阶段、里程碑和优先级符合当前治理体系。

## Applicable phases

- F0 文档治理与需求继承审计
- F1 产品需求冻结
- F2 至 F8 的任务入口维护

## Required context

1. 先读取 `CLAUDE.md`、`AGENTS.md`、`docs/00-governance/DOCS_INDEX.md`。
2. 必须读取 `docs/03-delivery/BACKLOG.md`、`docs/03-delivery/DELIVERY_PLAN.md`。
3. 涉及需求时读取 `docs/01-product/PRD.md`、`docs/01-product/REQUIREMENT_TRACEABILITY.md`。
4. 默认先运行或建议 `/aifi-drift-check`。
5. 未读取事实标记为 `UNKNOWN`。

## Delegatable SubAgents

- `aifi-product-requirements-owner`
- `aifi-delivery-plan-auditor`

## Execution steps

1. 检查任务编号是否全部使用 `AIFI-*`。
2. 检查阶段、里程碑和优先级是否使用允许值。
3. 对照 `DELIVERY_PLAN.md` 判断任务阶段归属。
4. 对照 PRD 和需求追踪判断任务来源。
5. 输出规范化建议或授权写入范围。

## Forbidden actions

- 不得创建新 roadmap、临时计划入口或并行任务体系。
- 不得恢复旧编号或旧阶段体系作为 active 体系。
- 不得把 `archive/` 作为当前执行依据。
- 不得修改 `docs/` 或 `archive/`，除非当前任务明确授权。

## Output format

- `## 结论`
- `## 证据`
- `## 风险`
- `## 待处理文件`
- `## 下一步动作`

## Acceptance criteria

- 所有任务入口判断引用 `BACKLOG.md` 或 `DELIVERY_PLAN.md` 证据。
- 任务编号、阶段、里程碑和优先级问题被明确列出。
- 未验证来源标记为 `UNKNOWN`。

## Risk markers

- 任务无需求来源。
- 阶段或里程碑断链。
- 优先级不在允许集合。
- 存在并行任务入口。

## Recommended read-only commands

```bash
git status --short --ignored
grep -RIn "AIFI-" docs/03-delivery docs/01-product 2>/dev/null || true
```

## Write authorization rules

默认只读。任务变更必须写入 `docs/03-delivery/BACKLOG.md`；阶段和里程碑变更必须写入 `docs/03-delivery/DELIVERY_PLAN.md`；任何写入都需要当前任务明确授权。

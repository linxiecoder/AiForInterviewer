---
title: PLAN_LATEST
type: note
permalink: ai-for-interviewer/plan-latest-1
---

> 强引用：有效文档白名单见 `docs/governance/ACTIVE_DOC_CANON.md`。


# AI 模拟面试系统当前仓库执行计划

## 1. 文档定位

本文档是当前规划入口，只回答“当前阶段、当前窗口、下一窗口、阻断项和下一步怎么推进”。本文档不承载完整长期计划、需求正文、设计正文、任务正文、执行日志或状态写回。

完整 R0/R1/R2 长期阶段计划由 `docs/planning/workbench-mvp/MASTER_IMPLEMENTATION_PLAN.md` 承载；本文档只保留当前 execution / current window 视角。

## 2. 当前规划事实

| domain | current entry | planning role |
| --- | --- | --- |
| requirements | `docs/requirements/workbench-mvp/**` | 输入范围、边界和验收口径 |
| design | `docs/design/workbench-mvp/**` | 输入设计约束和设计分解依据 |
| state truth | `docs/governance/DOC_STATE.yaml` | 判断正式状态、required docs 和 gate |
| current execution plan | `PLAN_LATEST.md` | 当前阶段、当前窗口、下一窗口和阻断项 |
| long-term implementation plan | `docs/planning/workbench-mvp/MASTER_IMPLEMENTATION_PLAN.md` | R0/R1/R2 完整长期阶段计划 |
| task entry | `TASK_INDEX.md` | 当前任务入口 |
| delegated state-bound references | `docs/planning/2026-04-25-current-repo-execution-plan.md`、`docs/tasks/workbench-mvp/2026-04-25-workbench-mvp-task-remap.md` | 迁移前状态引用对象，不是当前 planning / task 主入口 |
| task required docs | `docs/tasks/workbench-mvp/st13-task-packages/**` | ST13 任务 ID 对应 required docs；状态层路径已同步 |
| backlog | `docs/planning/workbench-mvp/2026-04-25-workbench-mvp-backlog-roadmap.md` | 后续 backlog 与路线图 |

## 3. 当前阶段

当前仓库处于文档体系重构收口与任务开窗前置治理阶段。planning / task 文档目录迁移已完成，正式状态层路径已同步。

当前阶段允许：

- 清理需求、设计、规划、任务、过程、治理、索引、归档职责边界。
- 创建或校准 Workbench MVP 需求层。
- 校准 planning / task 文档迁移后的索引和内部引用。
- 归档已完成且不再作为当前入口的过程文档。
- 按当前仓库事实修复文档口径：`apps/api`、`apps/web` 已存在，当前后端为 FastAPI，当前前端为 Vite + React，数据库事实为 PostgreSQL runtime + SQLite fallback。
- 运行只读状态验证和引用扫描。

当前阶段不允许：

- 打开 formal window。
- 生成 implementation packet。
- 进入业务代码实现。
- 提升 implementation readiness。

## 4. 当前窗口与阻断项

| item | current value |
| --- | --- |
| current window | `R0-W05-FINAL-GOVERNANCE-CLOSURE` |
| current goal | 完成 state-bound 迁移计划、gate/test 验证、执行日志写回，并判定是否允许进入 R0 主链路实现 |
| next window | 由本窗口验证结果决定；若全部通过，候选为 `R0-W08-MAIN-CHAIN-IMPLEMENTATION-ENTRY` |
| main blockers | state-bound 文档未完成 state/source_doc migration；gate/test/doc-quality 复核结果未写回前不得移动、删除或归档 state-bound 文档 |
| current window card summary | 当前治理收口窗口只允许写 state-bound 迁移计划、最小入口索引和执行日志；禁止修改 `DOC_STATE.yaml`、业务代码、tools、tests、archive、previews 或 packets |

## 5. 下一步推进顺序

1. 完成 `R0-W05-FINAL-GOVERNANCE-CLOSURE`，形成 `docs/governance/STATE_BOUND_MIGRATION_PLAN.md` 并完成 gate/test/doc-quality 验证。
2. 在 state migration 未完成前，不得移动、删除或归档 state-bound 文档；`docs/planning/2026-04-25-current-repo-execution-plan.md`、`docs/tasks/workbench-mvp/2026-04-25-workbench-mvp-task-remap.md`、`docs/tasks/workbench-mvp/st13-task-packages/**`、previews 和 packets 均需先解除引用。
3. 是否允许进入 R0 主链路实现，以本窗口验证结果和 `EXECUTION_LOG.md` 写回结论为准。
4. 后续如需 formal window / implementation packet，必须由独立状态流程开启。

## 6. 验证入口

```powershell
python -m tools.doc_governor.cli validate-state --input docs/governance/DOC_STATE.yaml
python -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml
git diff --check
git status --short
```
## 7. 历史过程归档入口

- 规划历史过程、阶段性确认卡与旧体系细节已归档，不在本文件展开。
- 归档台账：`archive/governance/archive-ledger.md`。
- 规划历史快照：`archive/planning/workbench-mvp/2026-04-25-workbench-mvp-backlog-roadmap.history-2026-05-01.md`。
- 本轮审计包 `archive/governance/2026-05-02-doc-convergence-audit/**` 仅作为 archive/governance evidence，不作为 current facts source。
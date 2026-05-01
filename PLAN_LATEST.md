---
title: PLAN_LATEST
type: note
permalink: ai-for-interviewer/plan-latest
---

# AI 模拟面试系统当前仓库执行计划

## 1. 文档定位

本文档是当前规划入口，只回答“当前怎么推进”。本文档不承载需求正文、设计正文、任务正文、执行日志或状态写回。

## 2. 当前规划事实

| domain | current entry | planning role |
| --- | --- | --- |
| requirements | `docs/requirements/workbench-mvp/**` | 输入范围、边界和验收口径 |
| design | `docs/design/workbench-mvp/**` | 输入设计约束和设计分解依据 |
| state truth | `docs/governance/DOC_STATE.yaml` | 判断正式状态、required docs 和 gate |
| execution plan | `docs/planning/2026-04-25-current-repo-execution-plan.md` | 当前仓库执行顺序；状态层路径已同步 |
| task remap | `docs/tasks/workbench-mvp/2026-04-25-workbench-mvp-task-remap.md` | Workbench MVP 任务重映射；状态层路径已同步 |
| task docs | `docs/tasks/workbench-mvp/st13-task-packages/**` | ST13 当前任务双文档；状态层路径已同步 |
| backlog | `docs/planning/workbench-mvp/2026-04-25-workbench-mvp-backlog-roadmap.md` | 后续 backlog 与路线图 |

## 3. 当前阶段

当前仓库处于文档体系重构收口与任务开窗前置治理阶段。planning / task 文档目录迁移已完成，正式状态层路径已同步。

当前阶段允许：

- 清理需求、设计、规划、任务、过程、治理、索引、归档职责边界。
- 创建或校准 Workbench MVP 需求层。
- 校准 planning / task 文档迁移后的索引和内部引用。
- 归档已完成且不再作为当前入口的过程文档。
- 运行只读状态验证和引用扫描。

当前阶段不允许：

- 打开 formal window。
- 生成 implementation packet。
- 进入业务代码实现。
- 提升 implementation readiness。

## 4. 下一步推进顺序

1. 完成文档体系迁移后的人工 diff review。
2. 确认 `validate-state` / `evaluate-state`、引用扫描和禁止范围检查均为绿。
3. 进入 commit 准备。
4. 后续如需 formal window / implementation packet，必须由独立状态流程开启。

## 5. 验证入口

```powershell
python -m tools.doc_governor.cli validate-state --input docs/governance/DOC_STATE.yaml
python -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml
git diff --check
git status --short
```
## 6. 历史过程归档入口

- 规划历史过程、阶段性确认卡与旧体系细节已归档，不在本文件展开。
- 归档台账：`archive/governance/archive-ledger.md`。
- 规划历史快照：`archive/planning/workbench-mvp/2026-04-25-workbench-mvp-backlog-roadmap.history-2026-05-01.md`。

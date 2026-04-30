---
title: 2026-04-25-current-repo-execution-plan
type: note
permalink: ai-for-interviewer/docs/planning/2026-04-25-current-repo-execution-plan
---

# AI 模拟面试系统当前仓库执行计划

## 1. 文档定位

本文档是当前仓库执行 planning 文档。本文档已迁入 `docs/planning/**`，`docs/governance/DOC_STATE.yaml` 中的受管路径已同步。

本文档不承载需求正文、设计正文、执行日志、状态写回、formal window 或 implementation packet。

## 2. 当前仓库定位

当前仓库以文档治理、需求/设计事实源收敛、任务开窗前置准备为主。当前业务实现目录尚未作为可实施工作面打开。

| domain | current entry | role |
| --- | --- | --- |
| requirements | `docs/requirements/workbench-mvp/**` | 产品目标、范围边界、验收口径 |
| design | `docs/design/workbench-mvp/**` | Workbench MVP 设计事实 |
| task | `TASK_INDEX.md`、`docs/tasks/workbench-mvp/st13-task-packages/**` | 任务入口与 required docs |
| state | `docs/governance/DOC_STATE.yaml` | 正式结构化状态真值 |
| process | `EXECUTION_LOG.md` | 执行记录 |

## 3. W0-W7 已完成事项

| area | current meaning |
| --- | --- |
| 文档治理规则 | 已形成 AGENTS、DOC_GOVERNANCE、DOC_AUTOMATION 等协作与自动化边界 |
| doc-governor 工具链 | 已具备 validate/evaluate/report/confirm 等治理能力 |
| Workbench MVP 设计 | 已归位到 `docs/design/workbench-mvp/**` |
| Workbench MVP 需求 | 已独立到 `docs/requirements/workbench-mvp/**` |
| ST13 任务文档 | 已迁入 `docs/tasks/workbench-mvp/st13-task-packages/**` |

## 4. 当前主项目设计开发的真实前置条件

1. 需求、设计、规划、任务、过程、治理、索引、归档职责清晰分离。
2. `validate-state` 与 `evaluate-state` 未引入新增错误。
3. ST13 task docs 的 required doc slot 与实际路径保持一致。
4. formal window 由状态流程单独打开。
5. implementation packet 由状态流程单独生成。

## 5. 当前不直接落未来业务目录结构的原因

- 当前阶段仍处于文档与状态治理前置阶段。
- `DOC_STATE.yaml` 尚未放行具体 implementation-ready。
- 业务目录、工具目录、测试目录不应被文档体系重构顺手改动。
- ST13 task docs 已完成路径迁移，业务目录、工具目录、测试目录仍不应被文档体系重构顺手改动。

## 6. 下一步建议

1. 完成文档体系重构和引用清理。
2. 人工 review 本轮 diff，确认没有误删需求或设计事实。
3. 确认 `DOC_STATE.yaml`、索引文档和 generated reports 不再保留旧 active path。
4. 状态 gate 允许后，再打开 formal window 并生成 implementation packet。

## 7. 验证命令

```powershell
python -m tools.doc_governor.cli validate-state --input docs/governance/DOC_STATE.yaml
python -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml
git diff --check
git status --short
```

## 8. 与 `DOC-PLAN-P1` 的关系

本文档只保留当前仓库执行计划职责。`DOC-PLAN-P1` 相关状态仍以 `DOC_STATE.yaml` 和当前活动 planning/task 文档为准。
---
title: ACTIVE_DOC_CANON
type: note
permalink: ai-for-interviewer/active-doc-canon
---

> 强约束：本文件是当前仓库“有效文档白名单”规范。除本文件显式列出的主入口外，其余同类入口一律视为非主入口；如被替代，必须标记 `superseded` 并提供替代路径与生效日期。

# 有效文档白名单（Active Doc Canon）

## 1. 目的与适用范围

- 统一“当前唯一有效入口”，防止多入口并存导致事实源分叉。
- 约束需求、设计、计划、任务、状态、日志、问题七类文档的主入口。
- 适用于仓库根目录与 `docs/` 下所有治理、规划、任务、需求、设计相关文档。

## 2. 当前唯一有效入口（按类别）

| 类别 | 唯一主入口 | 说明 |
| --- | --- | --- |
| 需求（requirements） | `docs/requirements/workbench-mvp/README.md` | 需求目录入口与当前需求事实源导航 |
| 设计（design） | `docs/design/workbench-mvp/README.md` | 设计目录入口与设计事实源导航 |
| 计划（planning） | `PLAN_LATEST.md` | 当前推进顺序与执行计划总入口 |
| 任务（tasks） | `TASK_INDEX.md` | 当前任务索引总入口 |
| 状态（state truth） | `docs/governance/DOC_STATE.yaml` | 唯一正式结构化状态真值 |
| 日志（execution log） | `EXECUTION_LOG.md` | 过程记录唯一主入口 |
| 问题（open questions） | `OPEN_QUESTIONS.md` | 待确认问题唯一主入口 |

## 3. 单主入口规则

1. 每类文档只允许一个主入口。
2. 任何新文档不得声明自己为同类“并行主入口”。
3. 如确需替换主入口，必须同时完成：
   - 更新本白名单；
   - 将旧入口标记为 `superseded`；
   - 在旧入口文件头写明“已废弃 + 替代路径 + 生效日期”；
   - 在 `archive/ARCHIVE_INDEX.md` 记录归档信息。

## 4. superseded 标记规范（文件头模板）

对被替代入口，必须在 YAML 头之后、正文之前加入如下块：

```md
> superseded: true
> 已废弃：是
> 替代路径：<new-canonical-path>
> 生效日期：YYYY-MM-DD
> 说明：该文件不再作为当前主入口，仅保留历史参考。
```

## 5. 当前已标记 superseded 的入口

- `docs/planning/2026-04-25-current-repo-execution-plan.md`（被 `PLAN_LATEST.md` 替代为计划主入口，2026-05-01 生效）
- `docs/tasks/workbench-mvp/2026-04-25-workbench-mvp-task-remap.md`（被 `TASK_INDEX.md` 替代为任务主入口，2026-05-01 生效）

## 6. 执行与校验

- 在 `AGENTS.md`、`PLAN_LATEST.md`、`TASK_INDEX.md` 顶部必须保留对本文件的强引用。
- 若发现同类多入口冲突，以本文件第 2 节“唯一主入口”表为准。
- 任何变更应在同次提交内同步更新 `archive/ARCHIVE_INDEX.md`。

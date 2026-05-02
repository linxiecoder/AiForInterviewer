---
title: ACTIVE_DOC_CANON
type: note
permalink: ai-for-interviewer/active-doc-canon
Owner: 文档治理
Last Updated: 2026-05-02
Scope: 有效文档白名单、当前主入口与 state-bound / generated / archive 边界
Depends On: AGENTS.md, docs/governance/DOC_AUTOMATION.md, docs/governance/DOC_STATE.yaml
Supersedes: none
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
| 规划目录索引（planning index） | `docs/planning/workbench-mvp/README.md` | `docs/planning/workbench-mvp/` 目录导航，不是当前执行计划入口 |
| 长期计划（long-term implementation） | `docs/planning/workbench-mvp/MASTER_IMPLEMENTATION_PLAN.md` | R0/R1/R2 完整长期阶段实施计划，不替代当前窗口入口 |
| 任务（tasks） | `TASK_INDEX.md` | 当前任务索引总入口 |
| 状态（state truth） | `docs/governance/DOC_STATE.yaml` | 唯一正式结构化状态真值 |
| 治理迁移计划（governance migration plan） | `docs/governance/STATE_BOUND_MIGRATION_PLAN.md` | state-bound 归档迁移前置计划；不是当前事实源，不替代 `DOC_STATE.yaml`，不授权直接移动或删除 state-bound 文档 |
| 日志（execution log） | `EXECUTION_LOG.md` | 过程记录唯一主入口 |
| 问题（open questions） | `OPEN_QUESTIONS.md` | 待确认问题唯一主入口 |

## 3. 单主入口规则

1. 每类文档只允许一个主入口。
2. 任何新文档不得声明自己为同类“并行主入口”。
3. 新增正式文档必须列入本文件或对应目录 README / 索引后，Daily Check 才能将其视为 active；未列入的材料只能作为 archive、generated 或 temporary evidence。
4. 如确需替换主入口，必须同时完成：
   - 更新本白名单；
   - 将旧入口标记为 `superseded`；
   - 在旧入口文件头写明“已废弃 + 替代路径 + 生效日期”；
   - 在 `archive/ARCHIVE_INDEX.md` 记录归档信息。

## 3.1 state-bound / generated / archive 边界

- `superseded` 不等于可移动或可删除。若旧文档仍被 `docs/governance/DOC_STATE.yaml`、required doc slot、`meta.path`、`source_doc`、transition history 或 implementation packet 引用，必须先完成 state / source_doc migration。
- `docs/planning/2026-04-25-current-repo-execution-plan.md` 与 `docs/tasks/workbench-mvp/2026-04-25-workbench-mvp-task-remap.md` 当前是 delegated state-bound historical source，不是 planning / task 主入口。
- `docs/governance/STATE_BOUND_MIGRATION_PLAN.md` 是 governance migration plan，仅用于说明后续 state/source_doc migration、generated artifact policy 和 archive cleanup 的前置条件；它不是当前需求、设计、规划、任务或状态事实源。
- `docs/planning/workbench-mvp/README.md` 只作为 planning 目录索引；`PLAN_LATEST.md` 仍是当前执行计划入口，`docs/planning/workbench-mvp/MASTER_IMPLEMENTATION_PLAN.md` 仍是长期实施计划。
- `docs/governance/DOC_GOVERNOR_REPORT.md`、`docs/governance/DOC_QUALITY_GATE_REPORT.md`、`docs/governance/BOOTSTRAP_REPORT.md`、`docs/governance/previews/**`、`docs/governance/packets/**` 是 generated / preview / packet artifact，不是当前事实源，不能替代 `DOC_STATE.yaml` 或主入口文档。
- `archive/**` 只作为 historical evidence 或 archive ledger；`archive/governance/2026-05-02-doc-convergence-audit/**` 是本轮收敛审计证据，不是 current facts source。

## 3.2 正式文档语言规则

- 项目正式文档默认使用中文。
- 标题、章节名、说明文字和表格字段说明应使用中文。
- 代码标识符、命令、路径、文件名、API 名称、库名、框架名、协议名、配置键、错误码、测试名、Git 分支 / commit 和必要技术术语可以保留英文。
- 新增正式文档必须遵守该规则，并先纳入本白名单或对应目录 README / 索引。
- 审计包和归档文档原则上也遵守中文优先规则；历史已生成审计包的语言统一可另开窗口处理，不在本文件登记时批量翻译。

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
- 涉及归档动作或主入口替换的变更，应在同次提交内同步更新 `archive/ARCHIVE_INDEX.md`。

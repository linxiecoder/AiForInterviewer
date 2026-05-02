---
title: MODULE_TASK_INDEX
type: note
permalink: ai-for-interviewer/docs/modules/m08-review-and-replay/module-task-index
---

# M08 复盘与回放 - 模块任务索引

## 0. Workbench MVP 当前需求与设计输入

- 当前需求输入：`docs/requirements/workbench-mvp/`。
- 当前设计输入：`docs/design/workbench-mvp/`。
- 重点引用：`information-architecture.md`、`object-model-rag-multiround-backend.md`、`scoring-review-export-dod.md`。
- 模块承接摘要：模拟复盘、真实面试复盘、逐题拆解、导出和归档入口。
- 后续补齐项：按真实 / 模拟复盘、低置信度校对、Markdown 导出和证据展示补齐模块设计。
- 边界：本节只记录模块摘要、入口关系和后续补齐项；不复制正式设计正文，不提升模块成熟度，不放行 formal window、implementation packet 或代码实现。

## 1. 模块任务总表

| Subtask ID | 子任务名称 | 状态 | 文档成熟度 | 关联问题 / 当前输入 | 目录 | 是否具备实施条件 |
| --- | --- | --- | --- | --- | --- | --- |
| ST08_01 | 复盘总对象与列表/详情 | todo | 仅有骨架 | 无当前 open；复盘结构见当前评分 / 复盘 / 导出 / DoD 设计输入 | [sub_modules/ST08_01-review-aggregate/](sub_modules/ST08_01-review-aggregate/) | 否 |
| ST08_02 | 真实面试导入与逐题分析 | todo | 仅有骨架 | OQ-015 已由 `FC-11` confirmed；见当前评分 / 复盘 / 导出 / DoD 设计输入 | [sub_modules/ST08_02-real-interview-intake/](sub_modules/ST08_02-real-interview-intake/) | 否 |
| ST08_03 | 模拟面试复盘回放与导出 | todo | 仅有骨架 | OQ-010 / OQ-014 已由 `FC-14` / `FC-17` confirmed；见当前对象模型和评分设计输入 | [sub_modules/ST08_03-simulated-review-replay/](sub_modules/ST08_03-simulated-review-replay/) | 否 |

## 2. 使用规则

- 模块内推进顺序应优先参考依赖关系和开放问题数量。
- 子任务设计先成熟，再推进子任务实施。
- 当前需求与设计输入只清理旧阻塞语义，不自动激活历史任务条目，也不改变“是否具备实施条件=否”的判断。
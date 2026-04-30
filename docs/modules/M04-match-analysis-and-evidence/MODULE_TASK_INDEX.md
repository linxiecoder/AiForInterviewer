---
title: MODULE_TASK_INDEX
type: note
permalink: ai-for-interviewer/docs/modules/m04-match-analysis-and-evidence/module-task-index
---

# M04 匹配分析与训练证据 - 模块任务索引

## 0. Workbench MVP 当前需求与设计输入

- 当前需求输入：`docs/requirements/workbench-mvp/`。
- 当前设计输入：`docs/design/workbench-mvp/`。
- 重点引用：`scope.md`、`object-model-rag-multiround-backend.md`、`scoring-review-export-dod.md`。
- 模块承接摘要：岗位-简历绑定、匹配分析、评分证据、规则版本和训练信号输入。
- 后续补齐项：补齐评分证据、规则版本、WeaknessItem 输入和异常路径。
- 边界：本节只记录模块摘要、入口关系和后续补齐项；不复制正式设计正文，不提升模块成熟度，不放行 formal window、implementation packet 或代码实现。

## 1. 模块任务总表

| Subtask ID | 子任务名称 | 状态 | 文档成熟度 | 待确认问题 | 目录 | 是否具备实施条件 |
| --- | --- | --- | --- | --- | --- | --- |
| ST04_01 | 岗位-简历绑定与输入契约 | todo | 仅有骨架 | - | sub_modules/ST04_01-bindings-and-input-contract/ | 否 |
| ST04_02 | 匹配分析、评分与证据 | todo | 仅有骨架 | historical：OQ-008 已由 FC-17 / DD-009 覆盖 | sub_modules/ST04_02-analysis-scoring-and-evidence/ | 否 |
| ST04_03 | 分析展示与训练入口 | todo | 仅有骨架 | historical：OQ-008 已由 FC-17 / DD-009 覆盖 | sub_modules/ST04_03-analysis-ui-and-training-entry/ | 否 |

## 2. 使用规则

- 模块内推进顺序应优先参考依赖关系和开放问题数量。
- 子任务设计先成熟，再推进子任务实施。
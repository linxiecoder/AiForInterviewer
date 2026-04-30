---
title: MODULE_TASK_INDEX
type: note
permalink: ai-for-interviewer/docs/modules/m10-admin-governance-and-observability/module-task-index
---

# M10 管理台、治理与可观测性 - 模块任务索引

## 0. Workbench MVP 当前需求与设计输入

- 当前需求输入：`docs/requirements/workbench-mvp/`。
- 当前设计输入：`docs/design/workbench-mvp/`。
- 重点引用：`README.md`、`scope.md`、`object-model-rag-multiround-backend.md`、`scoring-review-export-dod.md`。
- 模块承接摘要：管理员入口、公共知识库、LLM provider、日志、审计、配置、测试与治理收口。
- 后续补齐项：补齐最小运维 / 观测边界，完整管理台和 Basic Memory 写回继续后置。
- 边界：本节只记录模块摘要、入口关系和后续补齐项；不复制正式设计正文，不提升模块成熟度，不放行 formal window、implementation packet 或代码实现。

## 1. 模块任务总表

| Subtask ID | 子任务名称 | 状态 | 文档成熟度 | 关联问题 / 当前输入 | 目录 | 是否具备实施条件 |
| --- | --- | --- | --- | --- | --- | --- |
| ST10_01 | 成员治理与角色操作 | todo | 仅有骨架 | OQ-004 / OQ-005 已由 `FC-02` confirmed；见 当前范围需求与设计输入 | [sub_modules/ST10_01-admin-member-and-role-ops/](sub_modules/ST10_01-admin-member-and-role-ops/) | 否 |
| ST10_02 | 模型目录、评分规则与系统设置 | todo | 仅有骨架 | OQ-007 / OQ-017 已由 `FC-12` / `FC-18` confirmed；见当前评分和对象模型设计输入 | [sub_modules/ST10_02-models-rules-and-settings/](sub_modules/ST10_02-models-rules-and-settings/) | 否 |
| ST10_03 | 可观测性、CI/E2E 与 snapshot 运维 | todo | 仅有骨架 | OQ-002 historical；OQ-018 已由 `FC-18` confirmed；见当前对象模型 / RAG / 多轮 / 后端边界设计输入 | [sub_modules/ST10_03-observability-ci-and-snapshot-ops/](sub_modules/ST10_03-observability-ci-and-snapshot-ops/) | 否 |

## 2. 使用规则

- 模块内推进顺序应优先参考依赖关系和开放问题数量。
- 子任务设计先成熟，再推进子任务实施。
- 当前需求与设计输入只清理旧阻塞语义，不自动激活历史任务条目，也不改变“是否具备实施条件=否”的判断。
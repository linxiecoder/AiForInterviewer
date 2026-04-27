# M09 训练中心与薄弱项生命周期 - 模块任务索引

## 0. Workbench MVP 当前需求与设计输入

- 当前需求输入：`docs/requirements/workbench-mvp/`。
- 当前设计输入：`docs/design/workbench-mvp/`。
- 重点引用：`scope.md`、`object-model-rag-multiround-backend.md`、`scoring-review-export-dod.md`。
- 模块承接摘要：WeaknessItem、训练抽屉、证据聚合、消减、停练和训练生命周期。
- 后续补齐项：区分薄弱项中心与待打磨执行层，补齐训练状态和回写边界。
- 边界：本节只记录模块摘要、入口关系和后续补齐项；不复制正式设计正文，不提升模块成熟度，不放行 formal window、implementation packet 或代码实现。

## 1. 模块任务总表

| Subtask ID | 子任务名称 | 状态 | 文档成熟度 | 关联问题 / 当前输入 | 目录 | 是否具备实施条件 |
| --- | --- | --- | --- | --- | --- | --- |
| ST09_01 | 薄弱项聚合与训练中心 | todo | 仅有骨架 | OQ-016 已由 `FC-13` confirmed；见当前对象模型 / RAG / 多轮 / 后端边界设计输入 | [sub_modules/ST09_01-weakness-aggregation/](sub_modules/ST09_01-weakness-aggregation/) | 否 |
| ST09_02 | 训练抽屉与待打磨入列 | todo | 仅有骨架 | OQ-016 已由 `FC-13` confirmed；见当前对象模型 / RAG / 多轮 / 后端边界设计输入 | [sub_modules/ST09_02-training-drawer-and-intake/](sub_modules/ST09_02-training-drawer-and-intake/) | 否 |
| ST09_03 | 生命周期、消减与停练规则 | todo | 仅有骨架 | OQ-014 / OQ-016 已由 `FC-17` / `FC-13` confirmed；见当前评分和对象模型设计输入 | [sub_modules/ST09_03-lifecycle-rules/](sub_modules/ST09_03-lifecycle-rules/) | 否 |

## 2. 使用规则

- 模块内推进顺序应优先参考依赖关系和开放问题数量。
- 子任务设计先成熟，再推进子任务实施。
- 当前需求与设计输入只清理旧阻塞语义，不自动激活旧 ST 条目，也不改变“是否具备实施条件=否”的判断。

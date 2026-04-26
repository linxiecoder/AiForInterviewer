# M07 打磨模式、评估与进度 - 模块任务索引

## 0. Workbench MVP Design Canon 承接

- 当前正式设计事实源：`docs/design/workbench-mvp/`。
- 重点引用：`scope.md`、`object-model-rag-multiround-backend.md`、`scoring-review-export-dod.md`。
- 模块承接摘要：打磨模式、ProgressTree、题级反馈、能力树、训练入口和部分导出。
- 后续补齐项：明确打磨模式不固定轮次，并与压力面评分和训练闭环分离。
- 边界：本节只记录模块摘要、入口关系和后续补齐项；不复制正式设计正文，不提升模块成熟度，不放行 formal window、implementation packet 或代码实现。

## 1. 模块任务总表

| Subtask ID | 子任务名称 | 状态 | 文档成熟度 | 关联问题 / W13 事实源 | 目录 | 是否具备实施条件 |
| --- | --- | --- | --- | --- | --- | --- |
| ST07_01 | 打磨主题推荐与启动 | todo | 仅有骨架 | OQ-013 已由 `FC-13` / `FC-17` confirmed；见 W13 事实源 | [sub_modules/ST07_01-practice-topic-recommendation/](sub_modules/ST07_01-practice-topic-recommendation/) | 否 |
| ST07_02 | 能力树蓝图与节点状态 | todo | 仅有骨架 | OQ-014 已由 `FC-17` confirmed；见 W13 评分事实源 | [sub_modules/ST07_02-capability-tree-and-node-state/](sub_modules/ST07_02-capability-tree-and-node-state/) | 否 |
| ST07_03 | 逐题评估与进度快照 | todo | 仅有骨架 | OQ-008 / OQ-014 已由 `FC-17` confirmed；见 W13 评分事实源 | [sub_modules/ST07_03-assessment-and-progress/](sub_modules/ST07_03-assessment-and-progress/) | 否 |

## 2. 使用规则

- 模块内推进顺序应优先参考依赖关系和开放问题数量。
- 子任务设计先成熟，再推进子任务实施。
- W13 confirmed 只清理旧阻塞语义，不自动激活旧 ST 条目，也不改变“是否具备实施条件=否”的判断。

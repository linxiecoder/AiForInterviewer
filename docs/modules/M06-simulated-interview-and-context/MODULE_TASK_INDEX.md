# M06 模拟面试、上下文与导出 - 模块任务索引

## 0. Workbench MVP 当前需求与设计输入

- 当前需求输入：`docs/requirements/workbench-mvp/`。
- 当前设计输入：`docs/design/workbench-mvp/`。
- 重点引用：`scope.md`、`information-architecture.md`、`object-model-rag-multiround-backend.md`。
- 模块承接摘要：模拟记录列表、发起模拟、面试台、上下文包、多轮状态机和模拟复盘输入。
- 后续补齐项：按记录列表默认入口、打磨模式和压力面模式重切会话链路。
- 边界：本节只记录模块摘要、入口关系和后续补齐项；不复制正式设计正文，不提升模块成熟度，不放行 formal window、implementation packet 或代码实现。

## 1. 模块任务总表

| Subtask ID | 子任务名称 | 状态 | 文档成熟度 | 待确认问题 | 目录 | 是否具备实施条件 |
| --- | --- | --- | --- | --- | --- | --- |
| ST06_01 | 面试会话创建与列表 | todo | 仅有骨架 | - | sub_modules/ST06_01-interview-session-bootstrap/ | 否 |
| ST06_02 | 上下文包与问题来源规则 | todo | 仅有骨架 | historical：OQ-009 / OQ-011 / OQ-012 / OQ-018 已由 FC-05 / FC-18 / DD-008 / DD-021 覆盖 | sub_modules/ST06_02-context-pack-and-question-source/ | 否 |
| ST06_03 | 消息流、trace、报告与导出 | todo | 仅有骨架 | historical：OQ-012 已由 FC-05 / DD-021 覆盖 | sub_modules/ST06_03-message-trace-report-and-export/ | 否 |

## 2. 使用规则

- 模块内推进顺序应优先参考依赖关系和开放问题数量。
- 子任务设计先成熟，再推进子任务实施。

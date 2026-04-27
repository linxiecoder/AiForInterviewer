# M05 资产库、归档与检索 - 模块任务索引

## 0. Workbench MVP 当前需求与设计输入

- 当前需求输入：`docs/requirements/workbench-mvp/`。
- 当前设计输入：`docs/design/workbench-mvp/`。
- 重点引用：`scope.md`、`information-architecture.md`、`object-model-rag-multiround-backend.md`、`scoring-review-export-dod.md`。
- 模块承接摘要：知识库、RAG、检索引用、资产归档和动态 schema 子集。
- 后续补齐项：补齐知识库索引、检索失败降级、资产归档和引用证据边界。
- 边界：本节只记录模块摘要、入口关系和后续补齐项；不复制正式设计正文，不提升模块成熟度，不放行 formal window、implementation packet 或代码实现。

## 1. 模块任务总表

| Subtask ID | 子任务名称 | 状态 | 文档成熟度 | 待确认问题 | 目录 | 是否具备实施条件 |
| --- | --- | --- | --- | --- | --- | --- |
| ST05_01 | 资产类型与资产域 | todo | 仅有骨架 | - | sub_modules/ST05_01-asset-type-and-asset-domain/ | 否 |
| ST05_02 | 归档记录与来源追踪 | todo | 仅有骨架 | historical：OQ-010 已由 FC-14 / DD-027 覆盖 | sub_modules/ST05_02-archive-records-and-source-linkage/ | 否 |
| ST05_03 | 检索分块与索引入库 | todo | 仅有骨架 | historical：OQ-009 已由 FC-05 / DD-021 覆盖 | sub_modules/ST05_03-retrieval-chunking-and-index-ingestion/ | 否 |

## 2. 使用规则

- 模块内推进顺序应优先参考依赖关系和开放问题数量。
- 子任务设计先成熟，再推进子任务实施。

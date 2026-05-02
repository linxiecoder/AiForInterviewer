---
title: README
type: note
permalink: ai-for-interviewer/docs/design/workbench-mvp/readme
---

# Workbench MVP 设计入口

## 1. 文档定位

本目录是 Workbench MVP 当前设计事实源，回答“如何设计”。产品目标、范围边界、用户角色和验收口径归入 `docs/requirements/workbench-mvp/**`。

本目录不承载执行日志、迁移过程、任务流水、状态写回或实施包内容。

## 2. 文档索引

| 文档 | 职责 | 当前设计事实源 |
| --- | --- | --- |
| [scope.md](scope.md) | 设计范围边界、设计非目标、与需求层的关系 | yes |
| [information-architecture.md](information-architecture.md) | 信息架构、用户旅程、导航与页面组织 | yes |
| [object-model-rag-multiround-backend.md](object-model-rag-multiround-backend.md) | 对象模型、RAG、多轮会话与后端边界 | yes |
| [scoring-review-export-dod.md](scoring-review-export-dod.md) | 评分、复盘、导出、质量门禁和设计完成定义 | yes |

## 3. 与其他文档的关系

| 文档层 | 职责 |
| --- | --- |
| `docs/requirements/workbench-mvp/**` | 定义要什么、不要什么、验收到什么程度 |
| `docs/design/workbench-mvp/**` | 定义如何组织信息、对象、交互、数据和质量门禁 |
| `PLAN_LATEST.md` | 定义当前推进顺序 |
| `TASK_INDEX.md` | 定义当前任务入口和阻断状态 |
| `EXECUTION_LOG.md` | 记录过程 |

## 4. 总体设计事实

- 一期工作台以文本模拟面试闭环为主。
- 设计覆盖岗位与简历材料、面试记录、面试工作台、LLM/RAG/多轮、评分复盘、导出和弱点训练材料。
- 后端边界以支撑保存、恢复、评分、复盘和上下文引用为目标。
- 当前实现事实：后端为 FastAPI，前端为 Vite + React，数据库事实为 PostgreSQL runtime + SQLite fallback。
- Next.js / App Router 只能作为历史口径或未来替换候选，不作为当前实现事实。
- Redis、pgvector、对象存储、MinIO 或 S3-compatible 存储不作为 R0 必需 runtime；如后续需要，必须由 R1/R2 或独立窗口补齐设计与 gate。
- 是否进入实现由状态层 gate 决定，本目录不声明 implementation-ready。

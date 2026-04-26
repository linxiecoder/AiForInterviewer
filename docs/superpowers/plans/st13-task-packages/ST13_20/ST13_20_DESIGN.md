# ST13_20 DESIGN：服务端保存 / 数据库

## 1. 文档状态

- 状态：`draft`
- 实施状态：`not implementation-ready`
- formal window：`formal window closed`
- implementation packet：`implementation packet forbidden`
- 本文件是 W13-E8 创建的正式双文档实体之一，但尚未写入 `DOC_STATE.yaml` required doc slot。

## 2. 关联 ST13 / WT13

- ST13：`ST13_20`
- WT13 alias：`WT13-20`
- 任务名称：服务端保存 / 数据库
- 当前来源状态：`task_packet_draft_created` -> `double_doc_created`

## 3. 关联模块

- 主模块：M01
- 横向关联：M01-M10
- 关键 blocker：M02 权限边界仍需后续模块同步；数据 contract 可以创建文档，但不能进入实现。

## 4. 关联 W13 事实源

- `docs/superpowers/plans/2026-04-25-workbench-mvp-scope.md`
- `docs/superpowers/plans/2026-04-25-workbench-mvp-ia-user-journey.md`
- `docs/superpowers/plans/2026-04-25-workbench-mvp-object-model-rag-multiround-backend.md`
- `docs/superpowers/plans/2026-04-25-workbench-mvp-scoring-review-export-dod.md`
- `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-readiness-audit.md`
- `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-first-contract-task-packages.md`
- `docs/superpowers/plans/st13-task-packages/ST13_21/ST13_21_DESIGN.md`

## 5. 背景

一期 MVP 已 confirmed 必须服务端保存简历、面试过程、历史记录、复盘、评分证据、RAG query/topK、脱敏 LLM 记录、导出记录和训练相关结果。PostgreSQL 是当前已确认主路线，但 schema、migration、ORM、repository 都仍未放行实现。

## 6. 目标

- 建立服务端保存和数据库 contract。
- 明确 PostgreSQL 数据域、核心对象、关系、审计、删除、归档、隐私隔离和回退策略。
- 为 `ST13_21` API、`ST13_24` 测试验收和后续业务任务提供数据 contract 输入。

## 7. 非目标

- 不创建数据库。
- 不创建 migration。
- 不创建 ORM model。
- 不实现 repository、service 或 API。
- 不修改 `DOC_STATE.yaml`。
- 不生成 implementation packet，不打开 formal window。

## 8. 输入

- W13 四份事实源。
- `ST13_21` API / 后端服务边界设计。
- W13-E5 readiness audit 和 W13-E6 / E7 任务包文档。
- 当前状态层中 `ST13_20` 的 blocked / missing doc slot 事实。
- `OQ-111=A`、`OQ-112=A`、`OQ-113=B` 用户确认结果。

## 9. 输出

- PostgreSQL 数据域清单。
- 核心实体、关系、生命周期、索引、唯一约束、审计字段草案。
- 数据保存、脱敏、删除、归档、导出、回退策略。
- 下游 `ST13_24` required tests 输入。

## 10. 依赖

- 前置依赖：`ST13_21` API domain 边界。
- 并行依赖：权限、RAG、导出、评分、复盘对象模型。
- 下游依赖：`ST13_24`、`ST13_05`、`ST13_10`、`ST13_13~ST13_19`。

## 11. contract 范围

### 11.1 服务端保存目标

服务端保存必须覆盖一期主链：岗位 / 简历 / 知识库 / 面试会话 / 多轮 / 回答 / 评分 / 复盘 / 导出 / 训练 / 资产。

### 11.2 PostgreSQL 主路线

PostgreSQL 是已确认主路线；当前只定义 schema contract，不创建数据库或 migration。

### 11.3 User / Account / Role / Permission

- 用户账号、角色、权限、session 关联、管理员能力边界。
- 资源可见范围需支撑“我的记录”和管理员筛选。

### 11.4 Job

- 岗位列表、详情、创建编辑、归档、面试发起引用、评分证据引用。

### 11.5 Resume

- 简历内容、版本、上传 / 粘贴来源、归档、面试和复盘引用。

### 11.6 KnowledgeBase / KnowledgeDocument / KnowledgeChunk

- 用户私有知识库、管理员公共知识库、文档解析状态、chunk、索引状态和权限过滤。

### 11.7 RetrievalQuery / RetrievalResult / Citation / Evidence

- query、topK、检索结果、引用证据、无命中降级、证据缺口。

### 11.8 InterviewSession / InterviewRound / InterviewTurn

- 会话状态、模式、轮次、turn、暂停 / 继续 / 完成、历史记录回写。

### 11.9 InterviewAnswer / FeedbackSummary / ScoreReport

- 回答原文、题级反馈、整场反馈、评分维度、评分证据、评分版本。

### 11.10 WeaknessItem / TrainingTask / Asset

- 薄弱项累计 / 消减、训练动作、训练抽屉、整份 / 单题资产归档。

### 11.11 ExportSnapshot / ExportRecord

- Markdown export 内容快照、复制 / 下载记录、状态、权限和保留策略。

### 11.12 LLMGenerationRequest / Result 保存策略

- 只保存脱敏 prompt、模型名、模板版本、provider 状态、重试信息和结果摘要。
- 不保存 provider key，不保存超出权限范围的原文。

### 11.13 脱敏、删除、归档、审计边界

- 简历、真实面试材料、LLM 日志、RAG evidence 和导出快照必须明确脱敏规则。
- 删除、归档、审计字段必须支持后续回溯和用户可见范围。

## 12. 数据 / API / UI / 状态边界

- 数据边界：只定义 schema contract，不建库。
- API 边界：依赖 `ST13_21`，不定义 endpoint 实现。
- UI 边界：只说明页面数据需求，不设计页面。
- 状态边界：不修改 `DOC_STATE.yaml`；required doc slot 后续单独 State Update。

## 13. 权限 / 安全 / 隐私边界

- 用户私有数据、管理员公共知识库和导出记录必须按角色过滤。
- LLMGenerationRequest / Result 必须脱敏保存。
- 删除和归档要保留审计要求，避免误删评分、复盘、导出 evidence。

## 14. 错误态 / 空状态

- 数据不存在、已归档、无权限、schema 不匹配、索引未完成。
- 知识库空、检索无结果、会话中断、评分未生成、导出失败。

## 15. 验收标准

- 明确 User / Account / Role / Permission、Job、Resume、KnowledgeBase / KnowledgeDocument / KnowledgeChunk、RetrievalQuery / RetrievalResult / Citation / Evidence、InterviewSession / InterviewRound / InterviewTurn、InterviewAnswer / FeedbackSummary / ScoreReport、WeaknessItem / TrainingTask / Asset、ExportSnapshot / ExportRecord、LLMGenerationRequest / Result 的保存边界。
- 明确 PostgreSQL 主路线和未来 schema / migration 前置条件。
- 明确不创建数据库、migration、ORM 或 repository。

## 16. 测试要求

未来 required tests 至少包括：

- schema relation validation。
- migration up/down dry-run。
- 权限过滤数据可见性测试。
- 模拟记录、评分、复盘、导出链路数据一致性测试。
- RAG evidence 引用完整性测试。

本窗口不创建 `tests/**`。

## 17. 允许修改范围

本窗口允许：

- `docs/superpowers/plans/st13-task-packages/ST13_20/ST13_20_DESIGN.md`
- `docs/superpowers/plans/st13-task-packages/ST13_20/ST13_20_IMPLEMENTATION.md`
- 用户授权的父索引与 W13 计划文档同步。

## 18. 禁止修改范围

- `apps/**`
- `infra/**`
- `tools/**`
- `tests/**`
- `docs/governance/**`
- `docs/governance/DOC_STATE.yaml`
- 数据库配置、migration、ORM、repository 代码
- `docs/modules/**`
- `package.json`、`package-lock.json`、`pnpm-lock.yaml`

## 19. 用户确认项

- `OQ-111=A`：采用集中任务包目录。
- `OQ-112=A`：允许创建第一批正式双文档。
- `OQ-113=B`：后续单独 State Update 更新 required doc slot。

## 20. 下游任务

- `ST13_21`：API contract 的数据对象消费者。
- `ST13_24`：测试 / 验收 / DoD。
- `ST13_05`、`ST13_10`、`ST13_13~ST13_19`：记录、RAG、评分、复盘、导出和训练链路。

## 21. 当前不进入实现说明

本文件创建后，`ST13_20` 仍是 `not implementation-ready`。当前不创建数据库，不创建 migration，不创建 ORM，不生成 implementation packet，不打开 formal window。

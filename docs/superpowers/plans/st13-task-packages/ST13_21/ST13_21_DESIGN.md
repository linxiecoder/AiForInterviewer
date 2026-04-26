# ST13_21 DESIGN：API / 后端服务边界

## 1. 文档状态

- 状态：`draft`
- 实施状态：`not implementation-ready`
- formal window：`formal window closed`
- implementation packet：`implementation packet forbidden`
- 本文件是 W13-E8 创建的正式双文档实体之一，但尚未写入 `DOC_STATE.yaml` required doc slot。

## 2. 关联 ST13 / WT13

- ST13：`ST13_21`
- WT13 alias：`WT13-21`
- 任务名称：API / 后端服务边界
- 当前来源状态：`task_packet_draft_created` -> `double_doc_created`

## 3. 关联模块

- 主模块：M01
- 横向关联：M01-M10
- 关键 blocker：M02 权限边界仍需后续模块同步；该 blocker 不阻止文档创建，但阻止 implementation-ready。

## 4. 关联 W13 事实源

- `docs/superpowers/plans/2026-04-25-workbench-mvp-scope.md`
- `docs/superpowers/plans/2026-04-25-workbench-mvp-ia-user-journey.md`
- `docs/superpowers/plans/2026-04-25-workbench-mvp-object-model-rag-multiround-backend.md`
- `docs/superpowers/plans/2026-04-25-workbench-mvp-scoring-review-export-dod.md`
- `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-readiness-audit.md`
- `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-first-contract-task-packages.md`
- `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-first-contract-double-doc-plan.md`

## 5. 背景

一期 MVP 已确认为工作台级范围，包含真实 LLM、登录 / 权限、服务端保存、历史 / 复盘、RAG / 知识库、多轮高阶面试、0-100 多维评分、复制 / Markdown 下载。当前 W10 `apps/web/**` 原型只作为参考证据，不能作为正式一期 MVP 起点。

API / 后端服务边界是后续数据、页面、LLM、RAG、评分、复盘和导出的共同 contract 前置。当前窗口只创建文档，不创建 `apps/api/**`。

## 6. 目标

- 建立一期工作台 MVP 的 API / 后端服务边界设计文档。
- 明确 Auth、权限、岗位、简历、知识库、RAG、面试、多轮、评分、复盘、导出、运维观测的 API domain。
- 为 `ST13_20`、`ST13_24`、`ST13_23` 和后续业务 ST13 提供 contract 输入。

## 7. 非目标

- 不实现 FastAPI 服务。
- 不创建 `apps/api/**`、`apps/web/**`、`infra/**`。
- 不生成 OpenAPI 文件、路由、service、repository 或测试代码。
- 不修改 `docs/governance/DOC_STATE.yaml`。
- 不生成 implementation packet，不打开 formal window。

## 8. 输入

- W13 四份事实源和 W13-E5 / W13-E6 / W13-E7 文档。
- `DOC_STATE.yaml` 中 `ST13_21` 当前 blocked / missing doc slot 状态摘录。
- `OPEN_QUESTIONS.md` 中 `OQ-111=A`、`OQ-112=A`、`OQ-113=B` 的用户确认结果。
- M01-M10 模块文档仅作为历史和模块边界参考。

## 9. 输出

- API domain list。
- endpoint / command / query 边界清单。
- request / response DTO 草案。
- 认证、权限、错误态、分页、筛选、排序、幂等、版本、异步任务状态的 contract。
- 下游任务的 API contract 输入和验收要求。

## 10. 依赖

- 前置依赖：W13 四份事实源、W13-E5 readiness audit、W13-E6 第一批任务包草案、用户确认 `OQ-111=A / OQ-112=A / OQ-113=B`。
- 并行依赖：`ST13_20` 数据 contract 可并行草拟，但必须消费本任务的 API domain 边界。
- 下游依赖：`ST13_20`、`ST13_23`、`ST13_24`、`ST13_01` 以及多数业务 ST13。

## 11. contract 范围

### 11.1 Auth API

- 登录、登出、session 刷新、当前用户、权限不足响应。
- 一期默认采用 session cookie 方向，但具体实现仍需后续 formal window。

### 11.2 Account / Role / Permission API

- 用户账号、普通用户 / 管理员角色、资源可见范围、管理员公共知识库能力边界。
- 一期只定义最小权限 contract，不扩展完整组织管理。

### 11.3 Job API

- 岗位列表、详情、创建、编辑、归档、作为发起模拟面试必选输入。

### 11.4 Resume API

- 简历列表、详情、上传 / 粘贴 / 编辑、版本、归档、面试和复盘引用。

### 11.5 KnowledgeBase / KnowledgeDocument API

- 用户私有知识库、管理员公共知识库、文档上传、解析状态、索引状态、权限可见范围。

### 11.6 Retrieval API

- `RetrievalQuery`、`RetrievalResult`、`Citation / Evidence`、无命中降级、证据缺口标注。

### 11.7 InterviewSession API

- 发起、暂停、继续、完成、取消、状态查询、历史记录回写。

### 11.8 InterviewRound / Turn API

- 多轮状态、当前 turn、上下文保存、回答提交、追问、模式状态。

### 11.9 Question Generation API

- 首题生成、题组生成、打磨模式下一题建议、压力面题组策略。

### 11.10 Follow-up Generation API

- 基于用户回答、RAG evidence、岗位 / 简历上下文生成追问；失败可重试。

### 11.11 Answer Submission API

- 回答提交、原文保存、版本 / 时间戳、可见范围、空回答和超时处理。

### 11.12 Feedback / Score API

- 题级反馈、整场评分、`ScoreReport`、`ScoreDimension`、证据绑定、版本化。

### 11.13 SessionRecord API

- 历史模拟记录列表、筛选、排序、复盘入口、导出入口、权限可见范围。

### 11.14 Markdown Export API

- 复制内容、Markdown 下载、导出状态、导出记录、禁止完整 PDF。

### 11.15 Admin / Permission API 一期边界

- 管理员账号管理、公共知识库管理、可见范围筛选；不做完整团队管理。

### 11.16 Health / Config / Observability 最小边界

- health check、配置可见项、request_id / task_id、provider、latency、error_code、token / cost 候选字段。

## 12. 数据 / API / UI / 状态边界

- 数据边界：只定义 API 需要的数据对象，不落库。
- API 边界：只定义 contract-first 输入输出，不实现 endpoint。
- UI 边界：为 `ST13_23` 页面规格提供调用约束，不做页面设计。
- 状态边界：不修改 `DOC_STATE.yaml`；required doc slot 后续单独 State Update。

## 13. 权限 / 安全 / 隐私边界

- 所有 API 必须带用户身份上下文和资源可见范围。
- 简历、回答、RAG evidence、导出内容、LLM 日志必须有脱敏和权限过滤要求。
- 管理员公共知识库与用户私有知识库必须隔离。
- provider key、session secret、模型密钥不得写入文档样例或日志。

## 14. 错误态 / 空状态

- 未登录、权限不足、资源不存在、已归档、输入校验失败。
- 知识库空、RAG 无命中、LLM provider 失败、异步任务超时。
- 历史记录为空、复盘尚未生成、导出尚未完成。

## 15. 验收标准

- API domain 覆盖 Auth、Account、Role、Permission、Job、Resume、KnowledgeBase、KnowledgeDocument、Retrieval、InterviewSession、InterviewRound、InterviewTurn、Question Generation、Follow-up Generation、Answer Submission、Feedback / Score、SessionRecord、Markdown Export、Admin / Permission、Health / Config / Observability。
- 每个 domain 至少说明输入、输出、权限上下文、错误态和下游依赖。
- 明确 contract-first，且不得出现实现代码或目录创建。

## 16. 测试要求

未来 required tests 至少包括：

- API contract schema validation。
- 权限矩阵测试。
- API error taxonomy 测试。
- 幂等与状态流转测试。
- LLM / RAG / scoring / export 异步任务状态测试。

本窗口不创建 `tests/**`。

## 17. 允许修改范围

本窗口允许：

- `docs/superpowers/plans/st13-task-packages/ST13_21/ST13_21_DESIGN.md`
- `docs/superpowers/plans/st13-task-packages/ST13_21/ST13_21_IMPLEMENTATION.md`
- 用户授权的父索引与 W13 计划文档同步。

未来实现窗口是否允许创建 `apps/api/**` 仍需 formal window。

## 18. 禁止修改范围

- `apps/**`
- `infra/**`
- `tools/**`
- `tests/**`
- `docs/governance/**`
- `docs/governance/DOC_STATE.yaml`
- `docs/modules/**`
- `package.json`、`package-lock.json`、`pnpm-lock.yaml`
- Git 提交、推送、reset、clean、stash、rebase、merge、checkout

## 19. 用户确认项

- `OQ-111=A`：采用集中任务包目录。
- `OQ-112=A`：允许 W13-E8 创建第一批正式双文档。
- `OQ-113=B`：required doc slot 后续单独 State Update，不在本窗口修改 `DOC_STATE.yaml`。

## 20. 下游任务

- `ST13_20`：服务端保存 / 数据库。
- `ST13_23`：前端工作台 UI / 页面集合。
- `ST13_24`：测试 / 验收 / DoD。
- `ST13_01`：账号 / 登录 / 权限。
- 后续业务 ST13 的 API 调用和错误态验收。

## 21. 当前不进入实现说明

本文件创建后，`ST13_21` 仍是 `not implementation-ready`。当前不创建 `apps/api/**`，不生成 implementation packet，不打开 formal window，不把 API contract 草案写成已实现。

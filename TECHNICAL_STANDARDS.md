# AI 模拟面试 P1 技术标准

## 1. 文档定位

- 本文档沉淀当前项目的全局技术标准与默认工程口径。
- 本文档不承载一期 MVP 范围、IA、对象模型、评分、复盘、导出或 DoD 的完整事实正文；这些内容以 `PLAN_LATEST.md` 和四份 W13 唯一事实源为准。
- `FC-01~FC-19` 已完成用户确认；历史 OQ / MQ 不再在本文档中作为 active `open` 或 `proposed-default` 技术阻塞出现。
- 仍需复核的技术细节必须写成 `needs-review` 或 implementation packet 输入，不得写成 confirmed。

## 2. 已确认标准

- 文档主体默认使用中文，代码与技术标识保持英文。
- 正式文档新增后，必须同步更新 `AGENTS.md` 索引。
- 文档体系采用 `global -> module -> subtask` 分层。
- 子任务设计文档与实施文档必须分离。
- 单次执行单位必须是一个子任务目录中的 `SUBTASK_IMPLEMENTATION.md`。
- Markdown 正文中的成熟度、readiness、candidate 或 review 自我宣称不得反推 `DOC_STATE.yaml`。

## 3. confirmed 技术口径

### 3.1 仓库与目标代码结构

- 当前仓库实现布局：以设计文档、治理状态、`doc_governor` 工具链和测试验证为主，而不是已经落地的业务 monorepo。
- 当前目录真值：根目录全局文档、`docs/governance/`、`docs/modules/`、`docs/superpowers/`、`tools/doc_governor/`、`tests/doc_governor/`、`requirements.txt`。
- 当前不把 `node_modules/`、`.serena/`、`.worktrees/`、`__pycache__/`、临时缓存目录计入正式项目结构。
- 目标产品代码结构采用 `apps/web + packages/shared + apps/api`。
- 在 `TASK_INDEX.md` 写入明确正式任务 ID 和允许修改范围前，不得创建或扩展业务实现目录。

### 3.2 后端、数据与部署

- 后端采用 FastAPI。
- 数据库采用 PostgreSQL。
- API contract 先行。
- 部署目标为单机服务器。
- 日志覆盖应用、LLM 与 RAG。
- 简历、面试记录、复盘、脱敏 LLM 记录、RAG query/topK、完整问答、摘要与评分证据都由服务端保存。

### 3.3 登录、权限与可见范围

- 一期采用 session cookie。
- 账号由管理员创建。
- 角色为普通用户 / 管理员两级。
- 记录默认展示“我的记录”，管理员可额外按团队筛选。

### 3.4 LLM 与 RAG

- LLM 采用可插拔 provider 抽象，并先接一个默认 provider。
- 系统记录脱敏 prompt、模型名和模板版本。
- LLM 失败状态可重新生成。
- RAG 支持用户私有上传 + 管理员公共知识库，团队共享后置。
- RAG 采用混合检索。
- RAG 失败时降级继续，并标注证据缺口。
- RAG 进入评分证据，但不直接决定分数。

### 3.5 Web 最小共享层

- 共享 Web 契约维持最小共享层，不扩展为完整设计系统。
- `PageHeader` / 摘要区只承载最小语义，不冻结完整 props catalog。
- 列表查询状态采用最小共享查询层：`page`、`page_size`、`q`、`status`、`sort`、`order`。
- 分页响应复用统一骨架：`items`、`page`、`page_size`、`total`、`total_pages`。
- Web 可见文案统一通过 `getMessages(locale)` 与最小 namespace 读取。
- 首轮 locale seed 为 `zh-CN`、`en-US`，默认 locale 为 `zh-CN`。

### 3.6 导出与渲染边界

- 一期导出采用复制 / Markdown 下载。
- 详情页提供复制 / 下载，列表只保留快捷入口。
- 导出内容为完整复盘 + RAG 引用 + 训练建议。
- 导出包含原始回答，但不包含真实面试材料原文。
- 上传同步入库，转换和导出异步。

## 4. 仍需 implementation packet 复核的内容

- Web framework、包管理、构建方式、测试矩阵和共享包构建方式仍为 `DD-005` 的 `needs-review` 范围。
- Markdown 预览、下载、复制与未来 PDF 是否共用同一渲染链仍为 `DD-007` 的 `needs-review` 范围。
- 具体 API 路由、schema 字段、错误码、CI/E2E、对象存储部署、缓存、任务队列与运维脚本仍需在正式任务 ID 和 implementation packet 中细化。
- 本节内容不得绕过 `TASK_INDEX.md` 的正式开窗资格进入代码实施。

## 5. 标准变更后需要同步回写

- `DESIGN_DECISIONS.md`
- `OPEN_QUESTIONS.md`
- `MODULE_INDEX.md`
- `DOCUMENT_PROGRESS.md`
- `DOCUMENT_MATURITY.md`
- 受影响的模块文档

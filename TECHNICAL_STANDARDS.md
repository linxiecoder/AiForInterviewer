---
title: TECHNICAL_STANDARDS
type: note
permalink: ai-for-interviewer/technical-standards
---

# AI 模拟面试 P1 技术标准

## 1. 文档定位

- 本文档沉淀当前项目的全局技术标准与默认工程口径。
- 本文档不承载一期 MVP 范围、IA、对象模型、评分、复盘、导出或 DoD 的完整事实正文；需求事实以 `docs/requirements/workbench-mvp/**` 为准，设计事实以 `docs/design/workbench-mvp/**` 为准。
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
- 当前目录真值：根目录全局文档、`docs/requirements/`、`docs/design/`、`docs/planning/`、`docs/tasks/`、`docs/governance/`、`docs/modules/`、`tools/doc_governor/`、`tests/doc_governor/`、`requirements.txt`。
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

## 4. Python 与工程卫生规则

本节沉淀项目级 Python / SQL / 配置 / 测试工程规范。业务实现窗口仍必须以 `DOC_STATE.yaml`、implementation packet、allowed paths、forbidden paths 和对应 DoD 为准；本文档只定义通用工程底线，不单独授权任何实现。

### 4.1 变更范围与评审粒度

- 默认使用最小安全 diff，一个 patch 只解决一个明确问题。
- 不做无关重构、不做无关格式化、不升级依赖。
- 不修改公共 API、架构边界、数据持久化边界或错误 envelope，除非任务与 implementation packet 明确授权。
- 规则修改、业务代码修改、测试扩展应尽量分阶段处理，避免混入一个不可评审的大 diff。
- 发现额外清理机会时，作为 follow-up 输出，不混入当前 patch。

### 4.2 Python 模块与导入副作用

- Python 项目规范优先遵循本仓库既有 import、命名、类型注解、测试和错误处理风格。
- Python 模块 import 时不得执行建表、写文件、发网络请求、启动服务、运行测试等副作用。
- app 初始化、schema 初始化、资源初始化必须有显式边界。
- 脚本入口应使用 `main` guard 或项目既有入口模式。
- 模块应保持可被测试、可被文档工具导入。

### 4.3 DDL 与运行时代码分离

- Python 业务代码、router、service、repository、adapter 中不得内嵌 DDL。
- Python 文件中不得出现 `CREATE TABLE`、`CREATE INDEX`、`ALTER TABLE`、`DROP TABLE`。
- DDL 必须放入独立 `.sql` schema / migration 文件。
- Python 只能通过显式 schema init / migration / loader 边界加载 SQL 文件。
- 不得在 import 时自动建表，不得在每个请求中重复建表。
- 测试可以显式调用 schema init 创建临时数据库 schema。
- Python 中允许保留参数化 `SELECT` / `INSERT` / `UPDATE` / `DELETE`。
- 禁止通过字符串拼接用户输入生成 SQL。
- 不引入完整 migration 框架或 ORM，除非任务明确授权且项目已有模式要求。

### 4.4 版权声明与 license header

- 新增 Python / SQL / 关键工程文件必须遵循项目已有版权 / license header 规范。
- 如果项目已有 SPDX 或 Copyright 头，必须沿用一致格式。
- 如果项目没有统一版权头规范，不得编造版权主体、公司名、年份或许可证文本。
- 未发现统一版权头规范时，只补必要 module docstring / 文件说明，并在最终输出中说明。

### 4.5 注释、docstring 与文档说明

- 新增 Python 模块必须有 module docstring。
- 新增公开 class / function、router handler、adapter method 必须有简洁 docstring。
- 非显然逻辑应有解释性注释，解释 why，不重复 what。
- schema init、persistence boundary、connection lifecycle、traceability metadata、error envelope 适配点必须有必要说明。
- SQL schema 文件必须说明表用途、字段边界、metadata 字段用途和索引用途，尤其说明 `created_at`、`updated_at`、`source`、`version` 等可追溯字段。
- 禁止大段空泛注释、逐行废话注释、误导性未来承诺，以及无 owner / blocker 的 TODO。

### 4.6 硬编码引用收敛

- 重复出现的表名、列名、payload key、response key、metadata key、env key、error code、默认 `source` / `version` 和能力名等，应收敛到清晰常量或项目已有 config / helper / model 边界。
- 不允许 router、service、persistence、tests 各自散落维护同一批裸字符串。
- 优先使用轻量方案，例如模块级常量、`constants.py`、项目已有 config / helper / model 模式。
- 不为了“零字符串”引入过度抽象。
- SQL schema 文件中可以保留 DDL 字段名；Python 中重复引用这些字段时必须集中管理。
- 测试中可以保留少量为了可读性的 expected literal，但不得复制大量裸字段名。

### 4.7 测试与验证

- 生产逻辑变更必须伴随相关测试，或明确说明无法测试的原因。
- 优先运行 targeted tests，再运行更大范围验证。
- 测试代码也要保持可维护，不能因为是测试就接受复杂、脆弱、重复的结构。
- 测试应覆盖关键边界、错误路径和回归风险。
- 不能编造测试结果；验证结论必须来自本轮实际命令输出。
- 如果验证失败，必须区分本次变更引入的问题、既有问题和环境问题。
- 测试入口和临时产物治理规则见 `docs/governance/TEST_POLICY.md`。

### 4.8 配置、安全与可追溯

- env key、配置默认值、路径、错误码不得散落。
- 不提交真实 secret、token、password、个人路径或本地绝对路径。
- 默认配置必须适合本地开发和测试，不得隐式破坏生产数据。
- 数据保存能力必须保留必要 traceability metadata。
- error envelope、审计字段、`created_at`、`updated_at`、`source`、`version` 等应有清晰边界。

## 5. 仍需 implementation packet 复核的内容

- Web framework、包管理、构建方式、测试矩阵和共享包构建方式仍为 `DD-005` 的 `needs-review` 范围。
- Markdown 预览、下载、复制与未来 PDF 是否共用同一渲染链仍为 `DD-007` 的 `needs-review` 范围。
- 具体 API 路由、schema 字段、错误码、CI/E2E、对象存储部署、缓存、任务队列与运维脚本仍需在正式任务 ID 和 implementation packet 中细化。
- 本节内容不得绕过 `TASK_INDEX.md` 的正式开窗资格进入代码实施。

## 6. 标准变更后需要同步回写

- `DESIGN_DECISIONS.md`
- `OPEN_QUESTIONS.md`
- `MODULE_INDEX.md`
- `DOCUMENT_PROGRESS.md`
- `DOCUMENT_MATURITY.md`
- 受影响的模块文档
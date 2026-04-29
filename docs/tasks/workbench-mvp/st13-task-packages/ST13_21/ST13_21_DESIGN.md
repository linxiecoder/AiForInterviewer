# ST13_21 DESIGN：R0 最小 API / 后端服务边界

## 1. 文档状态

- 状态：`draft`
- 文档性质：ST13 任务设计文档；不是 implementation packet，不是 official state。
- 实施状态：`not implementation-ready`
- formal window：`formal window closed`
- implementation packet：`implementation packet forbidden`
- 当前定位：为后续 `ST13_21` state sync / preview / formal window readiness 准备文档输入。
- 本窗口不修改 `DOC_STATE.yaml`，不打开 formal window，不生成 packet，不进入 implementation。

## 2. 关联 ST13 / WT13

- ST13：`ST13_21`
- WT13 alias：`WT13-21`
- 任务名称：API / 后端服务边界
- 当前收敛范围：R0 minimal API service boundary
- 当前来源状态：`double_doc_registered`；M02 upstream blocker 已由 `7ece932` 状态同步解除，但 `ST13_21` 自身 official state 仍 blocked。

## 3. 当前 official blocker 背景

截至本轮文档修正前，`evaluate-state --entity-type subtask --entity-id ST13_21` 已不再报告 M02 downstream blocker；剩余 blocker 属于 `ST13_21` 自身字段或开窗条件：

- `acceptance_criteria_missing`
- `implementation_doc_not_active`
- `implementation_scope_unclear`
- `required_tests_missing`
- `formal_window_closed`
- `implementation_approval_missing`
- `maturity_missing`
- `official_readiness_blocked`

本文只修正双文档输入，不把上述 blocker 写成已关闭；后续仍需 state sync / preview / formal window 流程。

## 4. R0 目标

`ST13_21` 在 R0 的目标不是定义完整业务 API 合同，而是在 `ST01_01` 最小 FastAPI runtime 基础上建立后端服务边界骨架：

- 统一 `/api/v1` prefix。
- 明确 router organization 和 router registration 的最小模式。
- 保持 `GET /api/v1/health` 可达，不因 API 边界整理被迁移或破坏。
- 定义最小 error response / error envelope 边界。
- 定义最小配置读取边界。
- 为后续 Job / Resume / Knowledge / Interview / Score / Review / Export 路由保留 future contract boundary。
- 只消费 M02 的身份上下文和权限语义输入，不实现完整身份系统。

## 5. R0 范围内

本任务后续如进入 formal window，只允许围绕以下最小 API service boundary 做骨架级实现：

| 范围 | R0 最小含义 | 不代表 |
| --- | --- | --- |
| FastAPI runtime 承接 | 基于 ST01_01 已落地的最小 API runtime 继续组织服务边界 | 不重建 runtime，不扩展基础设施 |
| `/api/v1` prefix | 所有后续业务路由统一挂载到 `/api/v1` 下 | 不实现业务 endpoint |
| Router organization | 明确 API router 的分组、注册入口和未来扩展方式 | 不生成完整 OpenAPI 文件 |
| Health endpoint | 保持 `GET /api/v1/health` 继续可达 | 不把 health 迁入业务 router 导致回归 |
| Error envelope | 定义最小错误响应字段、错误码位置和 request id 语义 | 不完成全量业务错误 taxonomy |
| Config boundary | 只读取最小运行参数和非敏感配置 | 不接入 DB、Redis、MinIO、LLM、RAG |
| Future routes placeholder | 为后续业务 domain 保留路由边界或注释型占位 | 不实现 Job / Resume / Interview 等业务 |
| M02 identity input | 消费 `CurrentUserContext`、`401/403/404` 和 admin/member 语义 | 不实现完整 login/session/OAuth/JWT |

## 6. 明确延期 / 排除

以下内容不属于 `ST13_21` R0 minimal scope，后续必须由对应任务或另窗授权承接：

- 完整登录、session、OAuth、JWT、刷新 token、撤销 token。
- 团队管理、成员高级管理、完整成员 CRUD、管理员后台。
- 岗位业务 API、简历业务 API、知识库业务 API。
- 面试会话业务 API、回答提交业务 API、追问业务 API。
- 评分业务 API、复盘业务 API、导出业务 API。
- DB / ORM / migration / repository。
- LLM provider、RAG、embedding、向量检索。
- Redis / PostgreSQL / MinIO 真实接入。
- 文件上传、对象存储、真实 bucket / client / provider 初始化。
- `apps/web/**`、Dashboard、App Shell、PageHeader、DataTable。
- `tests/**`，除非后续 packet 明确授权。
- `.github/**`、完整 CI、E2E、多平台矩阵。
- 大规模重构或跨模块业务实现。

## 7. API service boundary 设计

### 7.1 Prefix 与 router registration

后续实现只能建立最小 router registration 模式：

1. API 入口统一挂载 `/api/v1`。
2. health endpoint 继续保留现有可达路径，不能被 router 重组破坏。
3. future routers 只能以边界占位方式存在，例如 auth、jobs、resumes、knowledge、interviews、scores、reviews、exports 的注册位置说明。
4. 未来业务 router 是否创建实际 endpoint，必须由对应 ST13 formal window 决定。

### 7.2 错误响应与 error envelope

R0 最小错误边界只要求后续服务骨架能表达稳定错误形状：

- `error.code`：机器可读错误码。
- `error.message`：面向调用方的简短说明。
- `error.request_id`：用于追踪的请求 ID。
- `error.details`：可选字段级错误，不包含敏感数据。

R0 只冻结 envelope 位置和最小字段，不完成业务错误全集。完整的权限、RAG、LLM、导出、状态冲突错误 taxonomy 作为后续 contract 或测试任务继续承接。

### 7.3 配置读取边界

R0 配置读取只覆盖最小运行参数：

- API title / version / environment。
- 非敏感 feature flag 或运行模式。
- request id / logging 的最小开关。

R0 不读取真实数据库 DSN、Redis URL、MinIO endpoint、LLM provider key、embedding provider 或对象存储 secret。`.env.example` 只能出现安全占位，不得包含真实 secret。

### 7.4 未来路由占位边界

允许在文档和后续骨架中保留 future contract boundary：

- Auth / Identity：只保留身份上下文与权限语义边界。
- Job / Resume：只保留未来路由分组，不实现保存、读取或业务校验。
- Knowledge / RAG：只保留未来路由分组，不实现上传、切块、索引、检索。
- Interview：只保留未来路由分组，不实现会话启动、回答提交或追问。
- Score / Review / Export：只保留未来路由分组，不实现评分、复盘、导出。

placeholder 不等于 endpoint 已实现，也不等于 OpenAPI 已冻结。

## 8. M02 downstream input 边界

M02 当前只作为 `ST13_21` 的 downstream identity boundary input：

- `CurrentUserContext`：`user_id / team_id / role / status`。
- 开发态 auth 语义：`/api/v1/auth/login`、`/api/v1/auth/me`、`/api/v1/auth/logout=204`。
- 成员目录最小读取语义：`GET /api/v1/members`、`GET /api/v1/members/{member_id}`。
- 权限错误语义：`401 / 403 / 404`。

`ST13_21` 不在本任务中实现完整身份系统，不扩展 session、OAuth、JWT、团队管理或成员管理后台。

## 9. 与 ST13_20 的关系

`ST13_20` 承接服务端保存 / 数据库边界。`ST13_21` R0 minimal scope 只提供 API service skeleton，不提前实现：

- PostgreSQL schema。
- migration。
- ORM model。
- repository。
- 业务数据保存。
- 数据回退或审计 retention。

如果后续 API 字段需要保存、不保存、脱敏、归档或审计策略，必须回到 `ST13_20` 数据 contract 复核。

## 10. 与 ST13_24 的关系

`ST13_24` 承接测试 / 验收 / DoD。`ST13_21` 只在实施文档中提供候选 required validation，不创建测试文件。

后续测试矩阵至少应覆盖：

- governance validation。
- API import / route smoke。
- health endpoint regression smoke。
- error envelope contract smoke。
- 禁止范围检查。

这些验证只有在 formal window / packet 授权后才可扩展为测试代码。

## 11. 验收方向

后续 state sync / preview 可从本文和实施文档中消费以下输入：

- goal 非空，且只覆盖 R0 minimal API service boundary。
- allowed paths 候选明确。
- forbidden paths 明确。
- acceptance criteria 非空。
- required validation 非空。
- M02 关系已降级为 downstream input / placeholder。
- 完整 API contract、DB、LLM、RAG、Redis、PostgreSQL、MinIO、业务 API 均明确延期。

## 12. 当前不进入实现说明

本文修正完成后，`ST13_21` 仍不是 implementation-ready。原因是：

- official `DOC_STATE.yaml` 仍未写入 `ST13_21` 的 maturity / readiness / implementation_doc_state。
- formal window 仍关闭。
- implementation approval 尚未完成。
- 本窗口不生成 implementation packet。
- 本窗口不创建或修改 `apps/**`、`tests/**`、`tools/**` 或 `docs/governance/**`。

## 13. 后续动作

建议下一步不是实现，而是开启 `ST13_21 state sync preview`：

1. 基于本双文档重新生成或审查 readiness preview。
2. 确认 preview 只影响 `ST13_21` 指定状态字段和 packet input。
3. 继续保持 formal window closed，直到用户另窗确认。
4. 若 preview 显示仍有文档字段缺口，先回到文档修正，而不是打开 implementation。

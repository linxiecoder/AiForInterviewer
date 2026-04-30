# ST13_21 DESIGN：R0 最小 API / 后端服务边界

## 1. 文档状态

- 状态：`draft`
- 文档性质：ST13 任务设计文档；记录 ST13_21 R0 minimal API service boundary 的设计边界与实施后同步事实；不是 implementation packet，不是 official state。
- official gate：formal window 已打开；implementation approval 已批准；当前 `implementation_ready=true`，`can_generate_implementation_packet=true`。
- packet 状态：implementation packet 已重新生成并提交，提交为 `89d82cf gov: generate ST13_21 implementation packet`。
- implementation 状态：R0 minimal API service boundary 已完成并通过 acceptance refresh；实现提交为 `b9d7fd3`，TestClient 依赖提交为 `1f65274`。
- 当前定位：为 `ST13_21` post-implementation docs / module sync 提供与 official state 和实际实现一致的文档事实。
- 本窗口不修改 `DOC_STATE.yaml`，不修改 packet，不继续 implementation，不扩大业务 API 范围。

## 2. 关联 ST13 / WT13

- ST13：`ST13_21`
- WT13 alias：`WT13-21`
- 任务名称：API / 后端服务边界
- 当前收敛范围：R0 minimal API service boundary
- 当前 official state：`implementation_doc_state=active_working_doc`，`maturity=L5`，`readiness=downstream_ready`，`formal_window_status=open`，`implementation_approval_status=approved`。
- 当前 evaluate / preflight 派生状态：blockers `[]`，`implementation_ready=true`，`can_generate_implementation_packet=true`。
- 当前实现结果：已按 packet 完成最小 `/api/v1` router registration、`GET /api/v1/health` regression、minimal error envelope、minimal config boundary 和未注册 future route placeholders；acceptance refresh 已通过。

## 3. 当前 official gate 背景

截至本轮 post-implementation 文档同步，`ST13_21` 已完成 state sync、scoped formal window sync、implementation approval、packet generation / commit、minimal API service boundary implementation 和 acceptance refresh。当前 official gate 事实为：

- `formal_window_status=open`
- `implementation_approval_status=approved`
- `implementation_ready=true`
- `can_generate_implementation_packet=true`
- `evaluate-state` / `preflight-open-window` 对 `ST13_21` 的 blocker 结果为 `[]`
- implementation packet 已提交：`89d82cf`
- implementation commit 已提交：`b9d7fd3`
- TestClient smoke 依赖 commit 已提交：`1f65274`

本文只同步 implementation 后事实，不写 official state，不修改 packet，不继续 implementation。

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

本任务已在 implementation window 内只围绕以下最小 API service boundary 做骨架级实现：

| 范围 | R0 最小含义 | 不代表 |
| --- | --- | --- |
| FastAPI runtime 承接 | 基于 ST01_01 已落地的最小 API runtime 继续组织服务边界 | 不重建 runtime，不扩展基础设施 |
| `/api/v1` prefix | 所有后续业务路由统一挂载到 `/api/v1` 下 | 不实现业务 endpoint |
| Router organization | 明确 API router 的分组、注册入口和未来扩展方式 | 不生成完整 OpenAPI 文件 |
| Health endpoint | 保持 `GET /api/v1/health` 继续可达 | 不把 health 迁入业务 router 导致回归 |
| Error envelope | 定义最小错误响应字段和错误码位置 | 不完成全量业务错误 taxonomy |
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

已落地的最小 router registration 模式为：

1. `apps/api/app/main.py` 创建 FastAPI app，并注册 `build_api_v1_router(settings.api_prefix)`。
2. `settings.api_prefix` 默认来自 `API_PREFIX=/api/v1`。
3. `apps/api/app/api/v1/__init__.py` 统一管理 `/api/v1` 下路由注册。
4. 当前只注册 health router，`GET /api/v1/health` 继续返回 `{ "status": "ok" }`。
5. future route names 仅作为未注册常量存在，未创建 `/auth`、`/jobs`、`/resumes`、`/interviews`、`/scores`、`/reviews`、`/exports` 等业务 endpoint。

### 7.2 错误响应与 error envelope

R0 最小错误边界只要求当前服务骨架能表达稳定错误形状：

- `error.code`：机器可读错误码。
- `error.message`：面向调用方的简短说明。
- `error.request_id` / `error.details` 未在本次 R0 implementation 中落地，后续如需扩展必须由单独 contract / test 任务承接。

当前实现通过 `http_exception_handler` 将 Starlette / FastAPI HTTPException 转为 `{"error": {"code": "HTTP_<status>", "message": "<detail>"}}`。R0 只冻结 envelope 位置和最小字段，不完成业务错误全集。完整的权限、RAG、LLM、导出、状态冲突错误 taxonomy 作为后续 contract 或测试任务继续承接。

### 7.3 配置读取边界

R0 配置读取只覆盖最小运行参数：

- API title / version / environment。
- API prefix。
- API host / port。

当前实现通过 `ApiSettings` 读取 `API_TITLE`、`API_VERSION`、`ENVIRONMENT`、`API_PREFIX`、`API_HOST`、`API_PORT`。R0 不读取真实数据库 DSN、Redis URL、MinIO endpoint、LLM provider key、embedding provider 或对象存储 secret。`.env.example` 只能出现安全占位，不得包含真实 secret。

### 7.4 未来路由占位边界

允许在文档和骨架中保留 future contract boundary：

- Auth / Identity：只保留身份上下文与权限语义边界。
- Job / Resume：只保留未来路由分组，不实现保存、读取或业务校验。
- Knowledge / RAG：只保留未来路由分组，不实现上传、切块、索引、检索。
- Interview：只保留未来路由分组，不实现会话启动、回答提交或追问。
- Score / Review / Export：只保留未来路由分组，不实现评分、复盘、导出。

placeholder 不等于 endpoint 已实现，也不等于 OpenAPI 已冻结。当前实现只保留未注册 placeholder 常量，不暴露业务 endpoint。

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

`ST13_24` 承接测试 / 验收 / DoD。`ST13_21` 只在实施文档中提供 required validation，不创建测试文件。

当前已完成的验证事实：

- `validate-state`、`evaluate-state ST13_21`、`preflight-open-window ST13_21` 通过。
- `git diff --check` 通过。
- 非 sandbox 环境 uvicorn + curl smoke 通过，`GET /api/v1/health` 返回 HTTP 200 + `{ "status": "ok" }`。
- missing route 返回 minimal error envelope。
- `httpx>=0.27,<1.0` 已加入 `requirements.txt`，用于 FastAPI `TestClient` smoke。
- 非 sandbox 环境 `TestClient` smoke 通过；sandbox 内 TestClient 可能超时，记录为 runtime limitation。
- 未新增或修改 `tests/**`。

这些验证不等于 ST13_24 测试体系已完成，也不授权新增 `tests/**`。

## 11. 验收结果

当前 acceptance refresh 可从本文和实施文档中消费以下事实：

- goal 仍只覆盖 R0 minimal API service boundary。
- allowed / forbidden paths 未突破 packet。
- `/api/v1` router registration 已落地。
- `GET /api/v1/health` 已验证。
- minimal error envelope 已落地。
- minimal config boundary 已落地，且不读取外部服务配置。
- future route placeholders 仅为未注册常量。
- M02 关系仍为 downstream input / placeholder。
- 完整 API contract、DB、LLM、RAG、Redis、PostgreSQL、MinIO、业务 API 均未实现。
- `tests/**` 与 `apps/web/**` 未修改。

## 12. 当前 state 与后续收口说明

`ST13_21` implementation 已完成并通过 acceptance refresh，但 official `DOC_STATE.yaml` 尚未在本窗口写入 accepted / done / implementation result。当前事实为：

- official `DOC_STATE.yaml` 已记录 `implementation_doc_state=active_working_doc`、`maturity=L5`、`readiness=downstream_ready`、`formal_window_status=open`、`implementation_approval_status=approved`。
- `evaluate-state` / `preflight-open-window` 派生 `implementation_ready=true`、`can_generate_implementation_packet=true`。
- packet 已生成并提交：`89d82cf gov: generate ST13_21 implementation packet`。
- implementation 已提交：`b9d7fd3 feat(ST13_21): add minimal API service boundary`。
- TestClient 依赖已提交：`1f65274 test(ST13_21): add httpx for FastAPI TestClient smoke`。
- 本窗口不写 official state，不修改 packet，不继续 implementation。

## 13. 后续动作

建议下一步是提交本次 post-implementation docs / index / log sync；随后另窗判断是否需要 official state accepted / done / implementation result transition。

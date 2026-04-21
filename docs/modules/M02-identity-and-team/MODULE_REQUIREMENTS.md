# M02 鉴权、团队与成员 - 模块需求

## 1. 文档定位

- 本文档用于把原始设计稿、原始实现计划与当前全局冻结口径中属于 `M02` 的部分收敛为模块级需求基线。
- 本轮目标是把 `M02` 设计包收敛为可评审、可供模块内依赖对齐的需求基线，供模块评审与总控复核，而不是伪装成“可直接实施”或“已放行正式候选”。
- 下游输入目标：
  - `MODULE_DESIGN.md`
  - `MODULE_API_DESIGN.md`
  - `MODULE_SCHEMA_DESIGN.md`
  - `MODULE_LOGIC_DESIGN.md`
  - `MODULE_TASK_INDEX.md`
  - `MODULE_DEPENDENCIES.md`

## 2. 来源文档

### 2.1 原始需求引用

- `docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md`
  - `3.1 用户与团队模型`
  - `7.1 团队与用户`
  - `12 权限与治理`
  - `14 页面信息架构`

### 2.2 原始实施计划引用

- `docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md`
  - `数据对象总表 -> 身份与团队域`
  - `API 总表 -> 鉴权与成员`
  - `里程碑 3：鉴权、团队与成员目录`
  - `权限矩阵与鉴权验证基线`
  - `软删除 / 索引与查询规范`

### 2.3 上游文档输入

- `AGENTS.md`
- `docs/DOC_GOVERNANCE.md`
- `PLAN_LATEST.md`
- `TECHNICAL_STANDARDS.md`
- `DESIGN_DECISIONS.md`
- `OPEN_QUESTIONS.md`
- `docs/modules/M01-foundation-and-platform/**`

## 3. 本轮默认冻结口径

- `OQ-004`：P1 当前采用“JWT 前的开发态认证适配层”，对外统一暴露 `Authorization: Bearer <token>` 与 `login / me / logout` 边界；本轮不扩展为 JWT、session cookie、刷新 token 或外部身份系统。
- `MQ-201`：开发态认证适配层已冻结为至少两组演示身份映射：
  - `admin` 一组凭据 + 一组 `Bearer token`
  - `member` 一组凭据 + 一组 `Bearer token`
  - 全部从 `.env` 或 seed 读取，业务层不得依赖 token 内部结构
- `MQ-202`：`/members` 已冻结为“团队内基础成员目录”：
  - `admin` 与 `member` 都可读取本团队成员目录
  - 首轮基础字段集只包含 `id`、`displayName`、`role`、`status`
  - 跨团队成员详情访问统一返回 `403`
- `MQ-204`：`teams.status` 与 `users.status` 已按方案 A 冻结：
  - `P1` 只冻结 `active`
  - 软删除继续由 `deleted_at` 表达
  - `disabled / invited / suspended / archived` 等状态不进入本轮模块契约
- `OQ-005`：权限矩阵首轮只覆盖当前 `P1` 已定义页面与 API，不扩展到未来多团队治理与运营场景。
- 基于以上冻结口径，本模块只承接：
  - 当前用户与当前团队上下文
  - 成员目录读取边界
  - 管理员 / 成员 / 未登录 / 跨团队访问规则
  - `401 / 403 / 404 / 软删除` 的鉴权验证基线

## 4. 模块目标

- 为 `P1` 提供身份模型、团队隔离规则和成员目录基线，供模块评审、共享契约吸收与白名单观察使用。
- 为后续业务模块输出稳定的 `current_user / role / team_id` 访问上下文。
- 为 `P1` 页面与 API 输出首轮权限矩阵与跨团队访问规则。

## 5. 用户价值与业务结果

- 未登录用户能够通过受控登录入口进入工作台。
- 已登录用户只能看到当前团队可见的数据与页面入口。
- 团队管理员与成员的权限边界可以被评审、测试并被其他模块复用。
- 后续模块不需要重新发明团队隔离与角色校验规则。

## 6. 模块范围内

- 登录、当前用户、退出登录的模块级边界定义。
- `Team` 与 `User` 的核心对象、关系与团队隔离约束。
- 成员目录读取契约：
  - `GET /api/v1/members`
  - `GET /api/v1/members/{member_id}`
  - `/login`
  - `/(dashboard)/members`
- 首轮权限矩阵：
  - 普通受保护页面 / API
  - 管理台页面 / API
  - 跨团队访问与软删除访问规则
- 鉴权验证硬约束：
  - 未登录 `401`
  - 角色不足 `403`
  - 成员目录跨团队详情访问 `403`
  - 软删除对象不可见

## 7. 不在本模块范围内

- 生产级 SSO、OAuth、JWT 刷新链路、session 持久化存储。
- 多团队管理界面、邀请流程、复杂租户治理、计费与组织树。
- 外部用户系统集成、密码找回、邮箱验证、二次验证。
- `/(dashboard)/admin/members` 与 `/api/v1/admin/members` 的完整管理台实现细节。
  - 本模块负责输出鉴权与授权规则。
  - 具体管理台读写页面 / API 已冻结为由后续治理模块承接。

## 8. 关键角色与核心对象

### 8.1 关键角色

- `admin`
  - 当前团队管理员。
  - 可访问管理台页面 / API，并管理团队成员与配置类能力。
- `member`
  - 当前团队普通成员。
  - 可访问本团队业务页面 / API，但不能访问管理台专属能力。
- `unauthenticated`
  - 未登录访问者。
  - 只能访问登录入口与公开健康检查。
- `cross-team user`
  - 已登录但试图访问非当前团队资源的用户。
  - 不视为独立业务角色，而是鉴权 / 授权路径中的异常访问条件。

### 8.2 核心对象

- `Team`
  - 当前团队主对象。
  - 为所有后续团队作用域数据提供 `team_id` 来源。
- `User`
  - P1 中直接通过 `users.team_id` 归属到团队。
  - 本轮不额外发明 `membership` 持久化表。
- `CurrentUserContext`
  - 由开发态 `Bearer token` 适配层解析得到的当前用户上下文投影。
- `MemberDirectoryItem`
  - 面向 `members` 列表 / 详情的安全字段投影。
- `AuthorizationPolicy`
  - 角色、团队、软删除与页面 / API 分组的访问判断基线。

## 9. 关键流程

### 9.1 登录与当前用户上下文

- 用户通过 `/login` 输入账号密码。
- 后端校验演示账号或种子用户凭据。
- 校验成功后返回开发态 `Bearer token` 与当前用户基础信息。
- 后续受保护请求通过 `Authorization: Bearer <token>` 解析当前用户与当前团队。

### 9.2 成员目录读取

- 当前用户进入 `/(dashboard)/members`。
- 前端使用当前登录态请求成员目录接口。
- 后端仅返回当前团队、未软删除的成员基础投影。
- `admin` 与 `member` 都可读取该目录。
- 首轮目录字段集只冻结：
  - `id`
  - `displayName`
  - `role`
  - `status`

### 9.3 管理员 / 成员权限分流

- 普通业务页面 / API 允许 `admin` 与 `member` 在本团队范围内访问。
- `/(dashboard)/admin/**` 与 `/api/v1/admin/**` 仅允许 `admin`。
- 角色不足时必须进入统一拒绝路径，而不是在业务层静默失败。

### 9.4 跨团队与软删除访问

- 所有团队作用域资源都从当前用户上下文派生 `team_id`，而不是相信客户端传入团队标识。
- 成员目录跨团队详情访问统一返回 `403`。
- 软删除对象默认不出现在列表，也不能通过详情接口直接读取。

## 10. 业务规则与验收口径

- `P1` 是单团队交付形态，但核心对象与后续业务表保留 `team_id`。
- 鉴权凭据必须从 `.env` 或种子配置读取，不能把真实凭据硬编码到业务实现中。
- 受保护页面 / API 必须先建立当前用户上下文，再进入业务服务层。
- 当前团队成员目录与后续业务对象都必须遵守相同的团队过滤与软删除过滤规则。
- 权限矩阵必须至少覆盖：
  - `/login`
  - `/(dashboard)/members`
  - `/(dashboard)/admin/**`
  - `/api/v1/auth/*`
  - `/api/v1/members*`
  - `/api/v1/admin/**`
  - 其他团队作用域业务页面 / API 组
- 测试基线必须覆盖：
  - 未登录访问受保护接口
  - 成员访问管理员接口
  - 本团队访问本团队资源
  - 跨团队成员目录详情访问 `403`
  - 软删除对象访问与列表过滤
- 持久化层字段命名统一使用 `snake_case`，对外 JSON / 前端消费字段统一使用 `camelCase`。
  - 至少明确：`display_name -> displayName`、`team_id -> teamId`
- `teams.id` 是物理主键，`teams.team_id` 仅作为与全局 `team_id` 约定对齐的同值逻辑键。
  - `users.team_id`、`CurrentUserContext.team_id` 与接口层 `teamId` 都应围绕这一团队作用域键表达，不得发明第二套团队身份。
- `POST /api/v1/auth/logout` 的成功语义冻结为 `204 No Content`。
  - 前端以成功状态码为准清空本地登录态，不依赖响应体字段。
- `/members` 列表必须保持“成员条目投影 + 服务端分页方向”与 `M01` 列表原语兼容。
  - 在 `OQ-021` 冻结前，不单独发明模块私有的查询参数或 response envelope。

## 11. 对下游文档的输出要求

- `MODULE_DESIGN.md`
  - 明确认证解析、成员目录、授权策略与前端页面承接关系。
- `MODULE_API_DESIGN.md`
  - 明确 `/auth/*`、`/members*` 与导出给其他模块的授权约束。
- `MODULE_SCHEMA_DESIGN.md`
  - 明确 `teams`、`users`、安全字段投影与索引 / 软删除规则。
- `MODULE_LOGIC_DESIGN.md`
  - 明确登录、鉴权、团队过滤、角色拒绝与软删除路径。
- `MODULE_TASK_INDEX.md`
  - 明确 `ST02_01 ~ ST02_03` 的推进顺序、阻塞与是否具备子任务设计前置条件。

## 12. 当前缺口与待确认问题

- 模块内部的业务边界、角色口径和状态口径已基本收敛，当前不再需要为了继续写模块文档而新增业务假设。
- 当前仍存在会影响子任务设计启动的共享契约阻塞：
  - `MQ-205` / `OQ-021`：`/members` 列表的 envelope、分页参数与查询状态映射已在模块内闭合到共享最小层；该结论只表示 `M02` 不再私补共享协议，仍不构成正式候选放行依据。
  - `MQ-206` / `OQ-022`：`/login` 与 `/(dashboard)/members` 已获得最小 i18n 共享默认口径，但页面面仍需继续按既有默认口径吸收；即使 `/members` 已闭合到共享最小层，也仍不应直接启动页面子任务设计。
- 若后续需要引入非 `active` 状态，或扩展成员目录字段集，应作为新一轮评审项提出，而不是在子任务中隐式补充。
- 因此当前判断应为“`/members` 已闭合到共享最小层，但仍未放行正式候选，`MT02_01 / MT02_02` 仍只是观察面”，而不是“已可直接拆分全部子任务”。

## 13. 关联文档

- `MODULE_DESIGN.md`
- `MODULE_API_DESIGN.md`
- `MODULE_SCHEMA_DESIGN.md`
- `MODULE_LOGIC_DESIGN.md`
- `MODULE_TASK_INDEX.md`
- `MODULE_DEPENDENCIES.md`
- `MODULE_OPEN_QUESTIONS.md`

# M02 鉴权、团队与成员 - API 设计

## 1. 文档定位

- 本文档用于沉淀 `M02` 直接负责的接口契约，以及本模块输出给其他模块复用的权限矩阵基线。
- 当前目标是提供“可作为下游输入”的候选接口边界，待总控复核，而不是把所有字段细节伪装成已经完全定稿。

## 2. 接口范围

### 2.1 本模块直接承接的接口

- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `POST /api/v1/auth/logout`
- `GET /api/v1/members`
- `GET /api/v1/members/{member_id}`

### 2.2 本模块输出给其他模块复用的授权约束

- `/(dashboard)/admin/**`
- `/api/v1/admin/**`
- 所有团队作用域业务页 / API 的：
  - 登录态要求
  - 团队过滤要求
  - `401 / 403 / 404` 语义基线

## 3. 通用契约

### 3.1 鉴权方式

- 除 `POST /api/v1/auth/login` 外，其他本模块接口均为受保护接口。
- 受保护接口统一使用：
  - `Authorization: Bearer <token>`
- 当前口径定义为“JWT 前的开发态认证适配层”。
- 当前 `Bearer token` 只承担开发态认证适配职责，不应被业务层或前端当成最终认证形态。
- 当前已冻结的开发态身份映射至少包含：
  - `admin` 一组凭据 + 一组 token
  - `member` 一组凭据 + 一组 token
- token 来源必须是 `.env` 或种子配置，不允许在业务代码中写死真实凭据。

### 3.2 当前用户与当前团队

- 当前用户上下文必须由 `Bearer token` 解析得到。
- 团队作用域不得由客户端直接指定 `team_id` 覆盖。
- 所有团队作用域详情查询默认同时满足：
  - `team_id = current_user.team_id`
  - `deleted_at IS NULL`

### 3.3 通用错误语义

- `400`：请求结构不合法或字段缺失。
- `401`：未登录、token 无效、凭据校验失败。
- `403`：已登录但角色不足，或本模块已冻结的成员目录跨团队详情访问被拒绝。
- `404`：资源不存在或资源已软删除。

## 4. 直接接口契约

### 4.1 `POST /api/v1/auth/login`

#### 作用

- 校验账号密码并返回开发态 `Bearer token` 与当前用户上下文。

#### 请求体

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `email` | `string` | 登录邮箱 |
| `password` | `string` | 登录密码 |

#### 成功响应

```json
{
  "token": "dev-admin-token",
  "user": {
    "id": "user_admin",
    "email": "admin@example.com",
    "displayName": "管理员",
    "role": "admin",
    "status": "active",
    "teamId": "team_default"
  }
}
```

#### 评审基线

- `token` 为开发态认证适配层发放的 `Bearer token`，当前已冻结为至少两组演示身份映射：`admin` 与 `member`。
- `user` 必须至少返回：
  - `id`
  - `email`
  - `role`
  - `status`
  - `teamId`
- `status` 在 `P1` 当前只冻结 `active`，不引入额外状态机语义。
- 若前端需要统一封装 `tokenType`，默认使用 `Bearer`，无需额外引入新鉴权类型。
- 后续若切换为 JWT，应只替换 token 签发与解析实现，不改变本接口的外部鉴权头格式和 `CurrentUserContext` 语义。

#### 失败响应

- `401 invalid_credentials`

### 4.2 `GET /api/v1/auth/me`

#### 作用

- 根据当前 `Bearer token` 返回当前登录用户上下文。

#### 鉴权要求

- 必须携带有效 `Authorization` 头。

#### 成功响应

```json
{
  "user": {
    "id": "user_admin",
    "email": "admin@example.com",
    "displayName": "管理员",
    "role": "admin",
    "status": "active",
    "teamId": "team_default"
  }
}
```

#### 评审基线

- 本轮冻结 `user` 负载，不额外发明完整 `team` 摘要或权限快照对象。
- 其他模块如需团队显示名或权限摘要，应在后续子任务设计阶段显式扩展，而不是隐式依赖。

#### 失败响应

- `401 unauthorized`

### 4.3 `POST /api/v1/auth/logout`

#### 作用

- 结束当前前端登录态，并为后续审计留出统一退出入口。

#### 鉴权要求

- 需要当前有效登录态。

#### 成功语义

- 本轮只冻结“成功结束当前登录态”的语义，不把该接口扩展为复杂令牌失效系统。
- 成功响应可以为空成功响应；具体 payload 在子任务设计阶段细化。

#### 失败响应

- `401 unauthorized`

### 4.4 `GET /api/v1/members`

#### 作用

- 返回当前团队基础成员目录列表。

#### 鉴权要求

- 需要当前有效登录态。

#### 查询语义

- 必须只查询 `current_user.team_id` 下的成员。
- 默认过滤软删除成员。
- 列表 envelope 与分页参数最终需与 `M01` 列表原语对齐；本轮只冻结成员条目字段与安全过滤规则。

#### 成员条目冻结字段集

| 字段 | 说明 |
| --- | --- |
| `id` | 成员 ID |
| `displayName` | 展示名 |
| `role` | `admin` / `member` |
| `status` | 当前状态 |

#### 评审基线

- `/members` 已冻结为团队内基础成员目录，`admin` 与 `member` 都可读取本团队成员列表。
- 无论最终可见范围如何，列表都不得返回：
  - `email`
  - `password_hash`
  - 跨团队成员
  - 已软删除成员

#### 失败响应

- `401 unauthorized`

### 4.5 `GET /api/v1/members/{member_id}`

#### 作用

- 返回当前团队某成员的基础详情投影。

#### 鉴权要求

- 需要当前有效登录态。

#### 详情字段冻结基线

| 字段 | 说明 |
| --- | --- |
| `id` | 成员 ID |
| `displayName` | 展示名 |
| `role` | 角色 |
| `status` | 状态 |

#### 错误语义

- 目标成员不属于当前团队：`403`
- 目标成员已软删除：`404`
- 当前角色不具备读取权限：`403`

## 5. P1 页面 / API 权限矩阵基线

| 路由分组 | 归属说明 | admin | member | 未登录 | 跨团队 |
| --- | --- | --- | --- | --- | --- |
| `/login`、`POST /api/v1/auth/login` | 登录入口 | 允许 | 允许 | 允许 | 不适用 |
| `GET /api/v1/auth/me`、`POST /api/v1/auth/logout` | 当前登录态接口 | 允许 | 允许 | `401` | 不适用 |
| `/(dashboard)/members`、`GET /api/v1/members*` | 成员目录读取面 | 允许 | 允许读取本团队基础成员目录 | `401` / 跳转登录 | `403` |
| 普通团队业务页 / API | 如岗位、简历、面试、复盘、资产、训练 | 允许 | 允许访问本团队资源 | `401` / 跳转登录 | `404` 或 `403` |
| `/(dashboard)/admin/**`、`/api/v1/admin/**` | 管理台专属能力 | 允许 | `403` | `401` / 跳转登录 | `403` |

## 6. 鉴权测试硬约束映射

- 所有新增受保护接口必须覆盖：
  - 未登录 `401`
  - `member` 访问 `admin` 接口 `403`
  - 本团队访问本团队资源 `200 / 201`
  - 跨团队成员目录详情访问 `403`
  - 软删除资源详情 `404`
  - 软删除资源不出现在列表
- 权限矩阵专门测试文件基线：
  - `apps/api/tests/test_authorization_matrix.py`

## 7. 当前缺口

- `logout` 成功响应是否采用 `204` 还是轻量确认体，本轮未强行定稿。
- `members` 列表 envelope / 分页参数仍需与 `M01` 列表原语最终对齐。

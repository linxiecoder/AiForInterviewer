---
title: MODULE_SCHEMA_DESIGN
type: note
permalink: ai-for-interviewer/docs/modules/m02-identity-and-team/module-schema-design
---

# M02 鉴权、团队与成员 - Schema 设计

## 1. 文档定位

- 本文档用于沉淀 `M02` 的持久化对象、字段约束、安全投影与索引基线。
- 当前目标是达到“可作为下游输入”的候选状态，待总控复核，不擅自发明上游未冻结的持久化契约。

## 2. 设计原则

- `P1` 单团队交付，但对象保留 `team_id` 以支撑后续扩展。
- 当前上游只明确 `teams` 与 `users` 两个持久化对象。
- 本轮不额外发明：
  - `memberships` 持久化表
  - 会话表
  - token 黑名单表
- 所有正式业务删除默认软删除，默认查询过滤 `deleted_at IS NULL`。

## 3. 持久化实体

### 3.1 `teams`

| 字段 | 类型建议 | 约束 / 说明 |
| --- | --- | --- |
| `id` | `uuid` / `string` | 主键 |
| `team_id` | `uuid` / `string` | 逻辑团队键，值必须与 `id` 相同；用于与全局 `team_id` 约定对齐，不引入第二套团队身份 |
| `display_name` | `string` | 团队展示名 |
| `team_key` | `string` | 对外可读业务键，需唯一 |
| `status` | `enum-like string` | `P1` 只冻结 `active`；其他状态值不进入当前模块契约 |
| `plan_tier` | `string` | 套餐或版本标识 |
| `created_at` | `datetime` | 创建时间 |
| `updated_at` | `datetime` | 更新时间 |
| `created_by` | `string` | 创建人 `user_id` |
| `updated_by` | `string` | 更新人 `user_id` |
| `deleted_at` | `datetime?` | 软删除时间 |
| `deleted_by` | `string?` | 软删除执行人 |

### 3.2 `users`

| 字段 | 类型建议 | 约束 / 说明 |
| --- | --- | --- |
| `id` | `uuid` / `string` | 主键 |
| `team_id` | `uuid` / `string` | 外键，指向 `teams.id` |
| `email` | `string` | 团队内唯一业务键之一 |
| `display_name` | `string` | 展示名 |
| `password_hash` | `string` | 凭据哈希，不进入对外接口 |
| `role` | `enum` | `admin` / `member` |
| `status` | `enum-like string` | `P1` 只冻结 `active`；其他状态值不进入当前模块契约 |
| `last_login_at` | `datetime?` | 最近登录时间 |
| `created_at` | `datetime` | 创建时间 |
| `updated_at` | `datetime` | 更新时间 |
| `created_by` | `string` | 创建人 `user_id` |
| `updated_by` | `string` | 更新人 `user_id` |
| `deleted_at` | `datetime?` | 软删除时间 |
| `deleted_by` | `string?` | 软删除执行人 |

## 4. 非持久化投影对象

### 4.1 `CurrentUserContext`

> 该对象由 token 解析得到，用于服务层与接口层，不单独落表。

| 字段 | 说明 |
| --- | --- |
| `user_id` | 当前用户 ID |
| `team_id` | 当前团队 ID |
| `role` | 当前角色 |
| `status` | 当前用户状态 |
| `token_key` | 当前 bearer token 的识别值 |

### 4.2 `MemberDirectoryItem`

> 该对象是成员目录的安全字段投影，不等于 `users` 全字段。

| 字段 | 说明 |
| --- | --- |
| `id` | 成员 ID |
| `display_name` | 展示名 |
| `role` | 角色 |
| `status` | 状态 |

### 4.3 命名映射规范

| 存储层字段 | 接口 / 前端字段 | 说明 |
| --- | --- | --- |
| `display_name` | `displayName` | 由序列化层完成映射 |
| `team_id` | `teamId` | 统一表达团队作用域键 |
| `last_login_at` | `lastLoginAt` | 若对外暴露，沿用相同映射原则 |

- 数据库与 ORM 模型保持 `snake_case`。
- JSON payload、前端状态与页面 props 保持 `camelCase`。
- 不允许在同一层同时混用 `display_name` 与 `displayName`，或把 `team_id` 与 `teamId` 当作不同语义字段。

## 5. 关系与约束

### 5.1 关系

- `teams.team_id = teams.id`
- `users.team_id -> teams.id`
- 当前 `P1` 不引入 `many-to-many` 团队成员关系。
- 团队成员身份直接由 `users.team_id + users.role` 表达。

### 5.2 唯一性

- `teams.team_key` 应在未软删除集合中唯一。
- `users.email` 应至少在 `(team_id, email, deleted_at)` 维度上满足可区分唯一性。
- 若后续进入多团队增强，再评估是否需要从 `users.email` 升级为全局唯一或引入邀请 / membership 模型。

### 5.3 索引

- `teams`
  - `(team_id, deleted_at)`
  - `team_key` 唯一索引或逻辑唯一约束
- `users`
  - `(team_id, deleted_at)`
  - `(team_id, role, status, deleted_at)`
  - `(team_id, email, deleted_at)`

### 5.4 软删除策略

- `teams`、`users` 默认软删除。
- 列表默认追加 `deleted_at IS NULL`。
- 详情默认不可返回软删除对象。
- 软删除对象的外键读取必须在服务层显式过滤，避免误把失效成员返回给业务层。

## 6. 安全字段边界

- 以下字段只允许出现在存储层或服务层，不得进入成员目录或当前用户公开 payload：
  - `password_hash`
  - 未来若存在的密钥、token 原文、认证 secret
- 对外接口只返回 `users` 的安全投影，而不是原表全量字段。

## 7. 生命周期与状态说明

### 7.1 团队

- 当前评审基线只要求：
  - 团队存在 `active` 态
  - 软删除团队不能被普通请求读取
- `P1` 不冻结 `suspended / archived` 等团队状态行为；若后续需要引入，应单独评审。

### 7.2 用户

- 当前评审基线只要求：
  - `active` 用户可登录、可进入成员目录
  - 软删除用户不可登录、不可出现在目录中
- `disabled / invited / archived` 等状态不进入 `P1` 当前模块契约。

## 8. 迁移影响与扩展约束

- 若未来从单团队扩展到多团队，当前最可能变化的是：
  - `users.team_id` 单归属关系
  - 管理员与成员的授权模型
  - 目录可见范围与成员管理流程
- 在这些问题未冻结前，不应在子任务或代码层偷偷引入 `membership` 表来掩盖设计缺口。

## 9. 当前缺口

- 固定 token 与用户身份的映射仍是逻辑层问题，不属于本 schema 文档直接定稿范围。
- schema 层的命名与主键漂移已在本轮收口：
  - 存储层使用 `display_name` / `team_id`
  - `teams.id` 与 `teams.team_id(=id)` 的关系已明确
- 剩余阻塞来自共享列表 / i18n 契约，而不是 schema 本身的字段歧义。
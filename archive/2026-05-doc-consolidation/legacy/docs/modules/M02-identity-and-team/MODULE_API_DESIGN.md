---
title: MODULE_API_DESIGN
type: note
permalink: ai-for-interviewer/docs/modules/m02-identity-and-team/module-api-design
---

# M02 鉴权、团队与成员 - API 设计

## 1. 当前作用与 R0 责任边界

本文档是 M02 身份与团队模块在 R0 阶段对外的 API 边界定义；不替代子任务设计或实现文档。

- `M02` 在 R0 的职责：定义最小身份上下文、用户身份/角色/权限的 API 语义以及与成员目录相关的访问边界。
- `M02` 在 R0 的最小目标：让 `ST13_21`（API / 后端服务边界）和 `ST13_20`（服务端保存 / 数据库）能明确消费：
  - 当前登录身份上下文
  - 团队作用域
  - 角色权限判断（admin / member）
  - `/members` 的基础成员目录读取语义
- `M02` 不在本模块承担的职责：
  - 完整 session 生命周期与安全模型（持久化 session、刷新 token、黑名单）
  - OAuth / 企业 SSO / 第三方鉴权接入
  - 团队管理、邀请、角色扩展、复杂组织治理
  - 成员管理后台的完整 CRUD 与审批流程

## 2. 最小身份上下文边界（R0）

### 2.1 身份解析与凭据模型

- 统一使用开发态 `Bearer token` 作为身份载体（用于 R0 最小实现）。
- 当前上游口径要求：`admin` 与 `member` 各保留一组演示身份映射，配置可来源于 `.env` / seed。
- token 仅用于当前用户上下文建立；业务逻辑不得解读 token 为生产鉴权来源。

### 2.2 统一上下文输出

`CurrentUserContext` 的消费字段：

| 字段 | 含义 | 强制性 |
| --- | --- | --- |
| `user_id` | 当前用户 ID | 必须 |
| `team_id` | 当前团队 ID | 必须 |
| `role` | 角色：`admin` / `member` | 必须 |
| `status` | 状态：`active` 为主 |
| `email` | 登录名相关标识（仅在 auth 信息中使用） | 建议 |

### 2.3 团队作用域边界

- 所有团队作用域资源查询都由 `CurrentUserContext.team_id` 引导。
- 列表与详情均默认执行：
  - `team_id = 当前用户团队`
  - 软删除过滤（`deleted_at IS NULL`）
- 跨团队访问默认不返回错误详情（`403/404` 视场景而定），避免越权推断。

## 3. 用户身份 / 角色 / 权限 API 抽象

### 3.1 认证与身份 API

- `POST /api/v1/auth/login`
  - 输入：`email`, `password`
  - 输出：`user`（含 `id`,`email`,`displayName`,`role`,`status`,`teamId`）与开发态 `token`
  - 失败：`401 invalid_credentials`

- `GET /api/v1/auth/me`
  - 输入：`Authorization: Bearer <token>`
  - 输出：`user`（`id`,`displayName`,`role`,`status`,`teamId`）
  - 失败：`401 unauthorized`

- `POST /api/v1/auth/logout`
  - 输入：已登录请求
  - 成功语义：`204 No Content`
  - 失败：`401 unauthorized`
  - 说明：本轮只冻结“前端清空登录态语义”，不构建服务端 token 失效流水线

### 3.2 成员目录 API

- `GET /api/v1/members`
  - 作用：返回本团队成员列表基础投影
  - 返回字段（固定）：`id`,`displayName`,`role`,`status`
  - 过滤：团队过滤 + 软删除过滤
  - 只读集合语义，不定义私有分页 query（沿用 `OQ-021` 的共享最小层）
  - 失败：`401 unauthorized`

- `GET /api/v1/members/{member_id}`
  - 作用：返回成员目录详情基础投影
  - 返回字段（固定）：`id`,`displayName`,`role`,`status`
  - 非本团队成员：`403`
  - 软删除成员：`404`

### 3.3 权限语义（供下游共享）

| 场景 | 结论 |
| --- | --- |
| 未登录访问受保护接口 | `401` |
| role 不足 | `403` |
| 成员目录跨团队详情 | `403` |
| 软删除成员/团队详情 | `404` |
| 成员目录与详情成功返回 | `200/200` |

## 4. 与 ST13_21 的依赖关系（R0 minimal API boundary）

`ST13_21` 在设计与后续 contract 执行中，以下输入依赖于 M02：

1. `CurrentUserContext`：`user_id / team_id / role / status`
2. 成员目录最小读 API：`GET /api/v1/auth/me`、`GET /api/v1/members*`
3. 权限语义基线：`401/403/404`
4. 统一登录态边界：`/api/v1/auth/logout=204`

`ST13_21` 仅能基于上述边界定义其依赖，不应把其下游任务范围扩展为：

- 完整 session 架构
- OAuth / JWT 切换策略
- 成员组织管理 UI 与 API 的完整管理台实现

## 5. R0 可实现与非 R0 部分

### 5.1 R0 当前作为 placeholder 处理的内容

以下内容在本轮不定义为已实现，只能作为 R0 的上下文占位与明确后续承接点：

- token 持久化与刷新链路
- 成员邀请、组织关系变更、复杂权限矩阵细化
- admin 成员的完整变更管理能力（用户禁用/角色变更/移除）
- 完整 i18n 命名空间和页面级权限提示文本

### 5.2 后续由其他任务承接的内容

- 完整登录 / 会话 / OAuth / JWT 演进（后续 auth 专题或 `ST13_21` 后续窗口）
- 团队管理界面、团队成员写操作、管理台成员管理 API（后续治理/平台任务）
- `/members` 的高级查询能力（自定义 filter、复杂排序策略、定制分页 envelope）

## 6. 当前阻塞收口声明

- 本文件不再用“已完成”描述尚未在状态层激活的范围。
- 当前保持的最小承诺：`M02` 的 API 边界可为 R0 提供稳定的身份上下文和最小成员目录读取能力。
- `M02` 模块不以实现状态替代文档状态；若需要进入 implementation-ready，需要单独状态窗口完成 `DOC_STATE.yaml` 状态 writeback 与 confirm。

## 7. 与 ST13_21 对齐的最小接口消费清单

| ST13_21 依赖点 | M02 提供值 | 备注 |
| --- | --- | --- |
| auth 入口 | `/api/v1/auth/login`, `/api/v1/auth/me`, `/api/v1/auth/logout` | 开发态鉴权适配层口径 |
| 团队作用域 | `team_id` 透传、跨团队拒绝、软删除过滤 | 列表与详情均受同一边界约束 |
| 成员目录 | `GET /api/v1/members`, `GET /api/v1/members/{member_id}` | 字段固定为基础目录投影 |
| 错误语义 | `401/403/404` | 与下游权限测试对齐 |
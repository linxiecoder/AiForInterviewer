# M02 鉴权、团队与成员 - 模块待确认问题

## 1. 文档定位

- 本文档用于记录 `M02` 模块内部仍未收敛、会影响模块设计评审或后续子任务设计的问题。
- 本文档只记录模块级问题，不替代根目录 `OPEN_QUESTIONS.md` 的全局问题总表。

## 2. 已采用的上游默认口径

| OQ ID | 当前状态 | 本轮采用方式 | 影响文档 |
| --- | --- | --- | --- |
| `OQ-004` | `proposed-default` | 按“JWT 前的开发态认证适配层”推进 `M02` 收敛到 `L5` 候选，不扩展 JWT / session cookie | `MODULE_REQUIREMENTS.md`、`MODULE_API_DESIGN.md`、`MODULE_LOGIC_DESIGN.md` |
| `OQ-005` | `proposed-default` | 按“首轮只覆盖 P1 页面与 API 权限矩阵”推进，不扩展未来多租户治理 | `MODULE_REQUIREMENTS.md`、`MODULE_DESIGN.md`、`MODULE_API_DESIGN.md` |

## 3. 问题表

| MQ ID | 问题 | 状态 | 影响范围 | 当前建议 | 是否需上升到全局 | 需回写文档 |
| --- | --- | --- | --- | --- | --- | --- |
| `MQ-201` | 作为“JWT 前的开发态认证适配层”，是否需要至少为 `admin` / `member` 各冻结一组独立 token 与演示凭据 | `confirmed` | `MODULE_API_DESIGN` / `MODULE_LOGIC_DESIGN` / `ST02_01` | 已确认采用默认方案：提供两组演示身份映射，全部从 `.env` 或 seed 读取，并明确业务层不得依赖 token 内部结构 | 否 | `MODULE_API_DESIGN.md`、`MODULE_LOGIC_DESIGN.md`、`MODULE_TASK_INDEX.md` |
| `MQ-202` | `/(dashboard)/members` 与 `GET /api/v1/members*` 是“团队内可读目录”还是“管理员专属目录” | `confirmed` | `MODULE_API_DESIGN` / `MODULE_LOGIC_DESIGN` / `ST02_02` / `ST02_03` | 已确认采用默认方案：`/members` 为团队内基础成员目录，`admin` 与 `member` 都可读取本团队成员；首轮字段集只冻结 `id`、`displayName`、`role`、`status`；跨团队成员详情访问统一返回 `403` | 否 | `MODULE_REQUIREMENTS.md`、`MODULE_API_DESIGN.md`、`MODULE_LOGIC_DESIGN.md`、`MODULE_SCHEMA_DESIGN.md` |
| `MQ-203` | `/(dashboard)/admin/members` 与 `/api/v1/admin/members` 的完整实现归属是由 `M02` 继续承接，还是由后续治理模块承接、`M02` 只输出鉴权规则 | `confirmed` | `MODULE_DESIGN` / `MODULE_DEPENDENCIES` / `ST02_03` / 后续管理台模块 | 已确认采用方案 B：`M02` 负责身份解析、授权规则、权限矩阵与最小契约；完整成员管理页面 / API 实现由后续治理模块承接 | 是 | `MODULE_DESIGN.md`、`MODULE_DEPENDENCIES.md`、`MODULE_TASK_INDEX.md` |
| `MQ-204` | `teams.status`、`users.status` 在 `P1` 最小交付中需要冻结到什么粒度 | `confirmed` | `MODULE_SCHEMA_DESIGN` / `MODULE_LOGIC_DESIGN` / `ST02_01` / `ST02_02` | 已确认采用方案 A：`P1` 只冻结 `active`；软删除继续由 `deleted_at` 表达；`disabled / invited / suspended / archived` 等状态不进入当前模块契约 | 否 | `MODULE_SCHEMA_DESIGN.md`、`MODULE_LOGIC_DESIGN.md`、`MODULE_TASK_INDEX.md` |

## 4. 当前高优问题

- 当前模块级待确认问题已清空。

## 5. 需要升级到全局的问题

- `MQ-203`
  - 原因：涉及 `M02` 与后续管理台模块的职责拆分，属于跨模块共享契约。
  - 本轮处理：模块内已按方案 B 冻结；后续仅需由总控决定是否同步到根目录 `OPEN_QUESTIONS.md`。

## 6. 当前判断

- `M02` 设计包当前已可进入 `L5` 候选复核。
- `M02` 模块内关键待确认问题已全部冻结；后续是否正式记为 `L5` 并进入子任务设计，取决于模块评审与总控成熟度回写。

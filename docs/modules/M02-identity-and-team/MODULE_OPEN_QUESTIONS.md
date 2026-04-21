# M02 鉴权、团队与成员 - 模块待确认问题

## 1. 文档定位

- 本文档用于记录 `M02` 模块内部仍未收敛、会影响模块设计评审或后续子任务设计的问题。
- 本文档只记录模块级问题，不替代根目录 `OPEN_QUESTIONS.md` 的全局问题总表。

## 2. 已采用的上游默认口径

| OQ ID | 当前状态 | 本轮采用方式 | 影响文档 |
| --- | --- | --- | --- |
| `OQ-004` | `proposed-default` | 按“JWT 前的开发态认证适配层”推进 `M02` 收敛到 `L5` 候选，不扩展 JWT / session cookie | `MODULE_REQUIREMENTS.md`、`MODULE_API_DESIGN.md`、`MODULE_LOGIC_DESIGN.md` |
| `OQ-005` | `proposed-default` | 按“首轮只覆盖 P1 页面与 API 权限矩阵”推进，不扩展未来多租户治理 | `MODULE_REQUIREMENTS.md`、`MODULE_DESIGN.md`、`MODULE_API_DESIGN.md` |
| `OQ-023` | `proposed-default` | 按方案 B 推进：`M02` 只负责身份解析、授权规则、权限矩阵与最小鉴权契约，完整成员管理页面 / API 由后续治理模块承接 | `MODULE_DESIGN.md`、`MODULE_DEPENDENCIES.md`、`MODULE_TASK_INDEX.md` |
| `OQ-024` | `proposed-default` | 旧 `ST02_*` 目录只保留为历史容器；正式入口以后续 `MT02_*` 蓝本和总控映射策略为准 | `MODULE_TASK_INDEX.md`、`MODULE_DEPENDENCIES.md`、`MODULE_DESIGN.md`、`MODULE_API_DESIGN.md` |

## 3. 问题表

| MQ ID | 问题 | 状态 | 影响范围 | 当前建议 | 是否需上升到全局 | 需回写文档 |
| --- | --- | --- | --- | --- | --- | --- |
| `MQ-201` | 作为“JWT 前的开发态认证适配层”，是否需要至少为 `admin` / `member` 各冻结一组独立 token 与演示凭据 | `confirmed` | `MODULE_API_DESIGN` / `MODULE_LOGIC_DESIGN` / `MT02_01` / `MT02_02` | 已确认采用默认方案：提供两组演示身份映射，全部从 `.env` 或 seed 读取，并明确业务层不得依赖 token 内部结构 | 否 | `MODULE_API_DESIGN.md`、`MODULE_LOGIC_DESIGN.md`、`MODULE_TASK_INDEX.md` |
| `MQ-202` | `/(dashboard)/members` 与 `GET /api/v1/members*` 是“团队内可读目录”还是“管理员专属目录” | `confirmed` | `MODULE_API_DESIGN` / `MODULE_LOGIC_DESIGN` / `MT02_04` / `MT02_06` / `MT02_08` | 已确认采用默认方案：`/members` 为团队内基础成员目录，`admin` 与 `member` 都可读取本团队成员；首轮字段集只冻结 `id`、`displayName`、`role`、`status`；跨团队成员详情访问统一返回 `403` | 否 | `MODULE_REQUIREMENTS.md`、`MODULE_API_DESIGN.md`、`MODULE_LOGIC_DESIGN.md`、`MODULE_SCHEMA_DESIGN.md` |
| `MQ-203` | `/(dashboard)/admin/members` 与 `/api/v1/admin/members` 的完整实现归属是由 `M02` 继续承接，还是由后续治理模块承接、`M02` 只输出鉴权规则 | `confirmed` | `MODULE_DESIGN` / `MODULE_DEPENDENCIES` / `MT02_07` / 后续管理台模块 | 已确认采用方案 B，且已与全局 `OQ-023` 对齐：`M02` 负责身份解析、授权规则、权限矩阵与最小契约；完整成员管理页面 / API 实现由后续治理模块承接 | 是 | `MODULE_DESIGN.md`、`MODULE_DEPENDENCIES.md`、`MODULE_TASK_INDEX.md` |
| `MQ-204` | `teams.status`、`users.status` 在 `P1` 最小交付中需要冻结到什么粒度 | `confirmed` | `MODULE_SCHEMA_DESIGN` / `MODULE_LOGIC_DESIGN` / `MT02_03` / `MT02_04` | 已确认采用方案 A：`P1` 只冻结 `active`；软删除继续由 `deleted_at` 表达；`disabled / invited / suspended / archived` 等状态不进入当前模块契约 | 否 | `MODULE_SCHEMA_DESIGN.md`、`MODULE_LOGIC_DESIGN.md`、`MODULE_TASK_INDEX.md` |
| `MQ-205` | `/api/v1/members` 的列表 envelope、分页参数与查询状态，应如何与 `M01` `DataTable` / `Pagination` 的最小共享契约对齐 | `proposed-default` | `MODULE_API_DESIGN` / `MODULE_LOGIC_DESIGN` / `MODULE_DEPENDENCIES` / `MT02_04` / `MT02_06` / `MT02_08` | 已与全局 `OQ-021` 对齐：沿用共享 `ListQueryState`、`page/page_size/q/status/sort/order` 最小映射与统一分页骨架；在 `confirmed` 前不补 `M02` 私有 query / envelope / URL 协议 | 否 | `MODULE_API_DESIGN.md`、`MODULE_LOGIC_DESIGN.md`、`MODULE_DEPENDENCIES.md`、`MODULE_TASK_INDEX.md` |
| `MQ-206` | `/login` 与 `/(dashboard)/members` 复用的 i18n namespace / locale fallback，是否已足以作为页面子任务输入下发 | `proposed-default` | `MODULE_DESIGN` / `MODULE_DEPENDENCIES` / `MT02_05` / `MT02_06` | 当前按全局 `OQ-022` 默认口径推进：继承 `M01` 的集中入口、locale seed、统一 fallback 与最小 namespace 边界；在模块完成吸收前，不补模块私有 namespace / fallback 规则 | 否 | `MODULE_REQUIREMENTS.md`、`MODULE_DESIGN.md`、`MODULE_DEPENDENCIES.md`、`MODULE_TASK_INDEX.md` |
| `MQ-207` | 在 `OQ-024` 默认口径下，`ST02_01 ~ ST02_03` 应如何映射到 `MT02_01 ~ MT02_08`，以及何时允许总控正式下发入口 | `proposed-default` | `MODULE_TASK_INDEX` / `MODULE_DEPENDENCIES` / `MODULE_DESIGN` / `MODULE_API_DESIGN` / 下一轮 `P03` 子任务设计窗口 | 已按全局 `OQ-024` 采用默认口径：`ST02_01 -> MT02_01/MT02_02/MT02_05`、`ST02_02 -> MT02_03/MT02_04/MT02_06`、`ST02_03 -> MT02_07/MT02_08`；旧目录只保留为历史容器，在总控正式下发前不得直开旧目录，也不得把 `MT02_*` 误写成正式入口 | 是 | `MODULE_TASK_INDEX.md`、`MODULE_DEPENDENCIES.md`、`MODULE_DESIGN.md`、`MODULE_API_DESIGN.md`、`MODULE_EXECUTION_LOG.md` |
| `MQ-208` | `M02` 首轮是否需要独立成员详情页 UI，还是只冻结成员列表页 + 详情 API 语义 | `proposed-default` | `MODULE_DESIGN` / `MODULE_TASK_INDEX` / `MT02_04` / `MT02_06` | 当前建议只冻结成员列表页承接与 `GET /api/v1/members/{member_id}` 详情 API 语义，不单列成员详情页 UI；若后续确需页面，再新增微任务 | 否 | `MODULE_DESIGN.md`、`MODULE_TASK_INDEX.md`、`MODULE_EXECUTION_LOG.md` |

## 4. 当前高优问题

| 优先级 | MQ ID | 当前阻塞文档 | 原因 | 本轮处理要求 |
| --- | --- | --- | --- | --- |
| `P0` | `MQ-205` | `MODULE_API_DESIGN.md`、`MODULE_LOGIC_DESIGN.md`、`MODULE_TASK_INDEX.md` | 若不按全局默认口径吸收列表集合契约，`MT02_04` / `MT02_06` 会继续缺少稳定输入 | 本轮按 `proposed-default` 吸收，不在 `M02` 内私自补协议 |
| `P0` | `MQ-206` | `MODULE_DESIGN.md`、`MODULE_DEPENDENCIES.md`、`MODULE_TASK_INDEX.md` | 若页面 i18n 默认口径未被模块吸收，登录页与成员页子任务仍容易各写一套 namespace / fallback | 按总控 `proposed-default` 口径吸收，不在 `M02` 内私自扩张 i18n 规则 |
| `P1` | `MQ-207` | `MODULE_TASK_INDEX.md`、`MODULE_DEPENDENCIES.md`、`MODULE_DESIGN.md`、`MODULE_API_DESIGN.md` | 若不把 `OQ-024` 的默认映射写死，非页面候选也会继续被旧入口拖回粗粒度任务包 | 本轮按 `proposed-default` 回写历史容器与映射关系，不重命名目录，也不放开子任务入口 |
| `P1` | `MQ-208` | `MODULE_DESIGN.md`、`MODULE_TASK_INDEX.md` | 若成员详情页 UI 范围不收紧，新的成员目录微任务仍会把页面目标、API 语义和 schema 混成一个任务包 | 本轮先按“列表页 + 详情 API”默认口径收缩 |

## 5. 需要升级到全局的问题

- `MQ-203`
  - 原因：涉及 `M02` 与后续管理台模块的职责拆分，属于跨模块共享契约。
  - 本轮处理：已对齐到全局 `OQ-023`，不再作为模块内独立阻塞。
- `MQ-205`
  - 原因：本质上是共享列表 query / pagination / envelope 契约问题。
  - 本轮处理：映射到全局 `OQ-021`，模块内只保留影响说明。
- `MQ-206`
  - 原因：本质上是共享 i18n namespace / fallback 契约问题。
  - 本轮处理：映射到全局 `OQ-022`，并按 `proposed-default` 口径在模块内只保留影响说明与吸收约束。
- `MQ-207`
  - 原因：若多个模块都进入任务重切，遗留子任务目录的迁移策略会影响全局编号与窗口编排。
  - 本轮处理：已升级并对齐到全局 `OQ-024`；模块内只保留 `M02` 的具体映射与 readiness 影响，不再把“是否继续沿用旧入口”保持为 `open`。

## 6. 当前判断

- `M02` 模块内的业务边界、角色边界和 schema 口径已基本收口。
- 当前剩余阻塞以共享契约问题和任务入口放行问题为主：`MQ-205` / `OQ-021` 已转为 `proposed-default` 吸收阶段，`MQ-206` / `OQ-022` 仍是需继续吸收的共享默认口径，`MQ-207` / `OQ-024` 则要求旧入口继续停留在历史容器状态，直到总控正式下发映射。
- 因此 `M02` 当前判断应为“模块整体接近进入子任务设计候选，但当前没有任何任务可正式开窗”；非页面微任务最多只处于候选队列，而不是“模块内问题已清空即可自动视为 `L5`”。

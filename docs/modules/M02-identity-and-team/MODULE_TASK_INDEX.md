# M02 鉴权、团队与成员 - 模块任务索引

## 0. Workbench MVP Design Canon 承接

- 当前正式设计事实源：`docs/design/workbench-mvp/`。
- 重点引用：`scope.md`、`information-architecture.md`、`object-model-rag-multiround-backend.md`。
- 模块承接摘要：登录、session、角色、权限、记录可见范围和管理员入口。
- 后续补齐项：补齐权限消费边界，尤其是 API / 数据 contract 对 M02 的依赖。
- 边界：本节只记录模块摘要、入口关系和后续补齐项；不复制正式设计正文，不提升模块成熟度，不放行 formal window、implementation packet 或代码实现。

## 0. W13 事实源与父级索引边界

- 当前产品范围事实只引用 Workbench MVP 正式设计事实源；本文件中的 `ST02_*` / `MT02_*` 仅用于模块内历史索引、观察蓝本和结构归属说明，不激活旧任务，不新增正式子任务 ID。
- W10 `apps/web` 原型只能作为参考证据；当前仍暂停代码开发，回到设计文档补齐。
- 旧 `SUBTASK_DESIGN.md` / `SUBTASK_IMPLEMENTATION.md` 若仍为骨架或模板，不因被本索引链接而获得正式入口、candidate 或开窗资格。

| 历史 / 骨架文档 | 父级索引 | 当前用途 |
| --- | --- | --- |
| [`ST02_01/SUBTASK_DESIGN.md`](sub_modules/ST02_01-auth-mechanism-boundary/SUBTASK_DESIGN.md)、[`ST02_01/SUBTASK_IMPLEMENTATION.md`](sub_modules/ST02_01-auth-mechanism-boundary/SUBTASK_IMPLEMENTATION.md) | 本文件第 1 节 `ST02_01` 与第 2.1 节映射表 | 历史容器与骨架留存，不作为正式子任务入口 |
| [`ST02_02/SUBTASK_DESIGN.md`](sub_modules/ST02_02-team-user-member-domain/SUBTASK_DESIGN.md)、[`ST02_02/SUBTASK_IMPLEMENTATION.md`](sub_modules/ST02_02-team-user-member-domain/SUBTASK_IMPLEMENTATION.md) | 本文件第 1 节 `ST02_02` 与第 2.1 节映射表 | 历史容器与骨架留存，不作为正式子任务入口 |
| [`ST02_03/SUBTASK_DESIGN.md`](sub_modules/ST02_03-authorization-matrix/SUBTASK_DESIGN.md)、[`ST02_03/SUBTASK_IMPLEMENTATION.md`](sub_modules/ST02_03-authorization-matrix/SUBTASK_IMPLEMENTATION.md) | 本文件第 1 节 `ST02_03` 与第 2.1 节映射表 | 历史容器与骨架留存，不作为正式子任务入口 |

## 1. 遗留子任务诊断

| 遗留任务 | 当前覆盖面 | 问题类型 | 为什么不适合作为下一轮入口 | 建议动作 |
| --- | --- | --- | --- | --- |
| `ST02_01` | 开发态身份映射、token 解析、`/auth/*`、`CurrentUserContext`、`/login` 页面承接 | `过大`、`依赖过重`、`不可并行`、`不可验证` | 同时混合 backend auth 契约与 frontend 登录页承接，既受 `OQ-004` 影响，也受 `OQ-022` 页面共享口径影响，无法形成单一完成定义 | `拆分`，并把共享 auth 契约继续保留在模块层 |
| `ST02_02` | `teams/users` schema、成员目录读模型、`/members` 列表 / 详情 API、成员页面目标 | `过大`、`依赖过重`、`不可并行`、`不可验证` | 把 schema、projection、API、列表 / 详情页面、列表共享契约和 i18n 吸收全部捆在一起，是当前最失真的入口 | `上提 + 拆分 + 暂停`，禁止继续沿用旧入口直接开子任务 |
| `ST02_03` | 权限矩阵、admin 边界、`401/403/404` 语义、验证基线 | `过大`、`依赖过重`、`不可并行`、`不可验证` | 同时混合模块级 route policy、`M02/M10` 职责边界和验证型工作，容易把共享契约缺口继续下放到子任务层 | `上提 + 拆分`，把路由组语义留在模块层，验证另列微任务 |

## 2. 重切后的微任务清单

> 下表中的 `MT02_xx` 是本轮重切后建议采用的微任务候选 ID，不等于已存在的子任务目录；当前轮次里，只有 `MT02_01`、`MT02_02` 可被记录为“白名单观察面”，仍不等于正式子任务入口。下一轮若进入子任务设计，应以这些微任务为蓝本重建入口。

### 2.1 旧入口与新蓝本映射

| 旧入口 | 必须拆开的变化面 | 新微任务蓝本 | 仍必须保留在模块层的共享契约 | 当前准入判断 |
| --- | --- | --- | --- | --- |
| `ST02_01` | 身份源 / token resolver、`/auth/*`、`CurrentUserContext`、`/login` 页面承接 | `MT02_01`、`MT02_02`、`MT02_05` | `CurrentUserContext` 字段、`logout=204`、`401/403` 语义、`/login` 只消费共享页面与 i18n 口径 | 旧目录只保留为历史容器；`MT02_01/MT02_02` 仅进入本轮白名单观察面，`MT02_05` 继续后置，不得直开 |
| `ST02_02` | `Team/User` schema、目录安全投影、`/members` read API、`/(dashboard)/members` 页面承接 | `MT02_03`、`MT02_04`、`MT02_06` | `/members` 字段投影、跨团队 `403`、软删除过滤、列表共享契约最小层 | 旧目录只保留为历史容器；`MT02_03` 不进入本轮白名单，仅保留后续观察顺序；`MT02_04` 虽已吸收共享最小层，但这只代表模块内闭合而非正式候选已放行，该口径当前仍只处于 `OQ-021` 默认治理层，`MT02_06` 继续后置，不得直开 |
| `ST02_03` | admin route policy、`401/403/404` 语义、鉴权验证矩阵 | `MT02_07`、`MT02_08` | `/(dashboard)/admin/**` 与 `/api/v1/admin/**` 的权限矩阵、`M02/M10` 职责边界、验证基线 | 旧目录只保留为历史容器；`MT02_07` 不进入本轮白名单，仅保留后续观察顺序；`MT02_08` 必须等待上游 API / policy 稳定后再判断 |

| 微任务 ID | 微任务名称 | 来源 | 主要职责 | 前置依赖 | 共享契约闸门 | 冻结后可并行性 | 当前建议 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `MT02_01` | 身份源与 token resolver | `ST02_01` 拆分 | 固定 `Bearer token`、演示身份映射、resolver 输入输出 | 模块核心文档通过 `L5` 复核、`OQ-004` | 无新增共享闸门 | 否，作为 auth 基座优先冻结 | 本轮仅作为白名单观察面；除正式开窗层当前仍为空外，遗留 `ST02_01` 仍只有骨架 / 模板，不能充当正式入口证据 |
| `MT02_02` | `CurrentUserContext` 与 `/auth/*` 边界 | `ST02_01` 拆分 | `login/me/logout` payload、`CurrentUserContext`、`logout=204` | `MT02_01` | 无新增共享闸门 | 完成后可解锁多个并行面 | 本轮仅作为白名单观察面；即使 auth payload 已较稳定，也仍只允许消费模块层已冻结的 `CurrentUserContext` / `logout=204` / `401/403` / admin route group 边界，因为这些输出会被 `/login`、`MT02_07`、`MT02_08` 等共同消费；除总控把 `OQ-024` 正式开窗层从空推进为正式入口外，旧 `ST02_01` 仍是骨架 / 空白模板，不能视为正式入口 |
| `MT02_03` | `Team/User` schema 与安全投影 | `ST02_02` 拆分 | `teams/users` 字段、`team_id` 关系、`MemberDirectoryItem` projection | 模块 schema / design 稳定 | 无新增共享闸门 | 可与页面 / policy 面错峰并行 | 仅保留后续观察顺序，不纳入本轮白名单，也不得直开 |
| `MT02_04` | 成员目录 read API | `ST02_02` 拆分 | `GET /api/v1/members`、`GET /api/v1/members/{member_id}`、过滤与错误语义 | `MT02_02`、`MT02_03` | `OQ-021` | 可与 admin policy 面并行 | 即使 `/members` 已在模块内闭合到共享最小层，也只代表模块停止私补共享协议；在 `OQ-021` 仍为共享默认口径且 `MODULE_API_DESIGN.md` 仍是最低位期间继续阻塞，不进入子任务设计 |
| `MT02_05` | `/login` 页面 adapter | `ST02_01` 拆分 | 登录页表单、登录态承接、共享 i18n 消费 | `MT02_02` | `OQ-020`、`OQ-022` | 可与 schema / policy 面并行 | 明确保留在页面后置队列，不得与 auth backend 合并直开 |
| `MT02_06` | `/(dashboard)/members` 页面 adapter | `ST02_02` 拆分 | 列表页容器、`PageHeader` 承接、列表请求 adapter | `MT02_04` | `OQ-020`、`OQ-021`、`OQ-022` | 可与验证面并行 | 明确保留在页面后置队列；不得从“`/members` 已闭合”或“`MT02_04` 接近稳定”倒推 ready，仍需等待 API 与共享页面口径同时稳定后再判断 |
| `MT02_07` | admin 路由组 policy | `ST02_03` 拆分 | `/(dashboard)/admin/**`、`/api/v1/admin/**` 的角色判断与边界消费 | `MT02_02` | `OQ-005`、`OQ-023` | 可与成员目录 read API、登录页 adapter 并行 | 仅保留后续观察顺序，不纳入本轮白名单，也不得直开 |
| `MT02_08` | 鉴权验证矩阵 | `ST02_03` 拆分 | `401/403/404`、跨团队、软删除、角色矩阵验证 | `MT02_04`、`MT02_07` | 无新增共享闸门 | 可与 `MT02_06` 并行 | 作为收口型微任务继续后置，必须等待上游 API / policy 稳定 |

## 3. 共享契约冻结后的并行建议

| 并行组 | 前置条件 | 可并行微任务 | 说明 |
| --- | --- | --- | --- |
| A | `MT02_02` 已稳定，`OQ-022` 已被模块吸收 | `MT02_03`、`MT02_05`、`MT02_07` | schema / projection、登录页 adapter、admin policy 分属不同变化面，不应再绑成同一子任务 |
| B | `MT02_02` 已稳定，`OQ-021`、`OQ-023` 已按默认口径吸收 | `MT02_04`、`MT02_07` | 成员目录 read API 与 admin policy 分属读取面和授权面，可以并行推进，但需共享同一 `CurrentUserContext` 与 route group 语义 |
| C | `MT02_04`、`MT02_07` 已稳定，`OQ-020`、`OQ-022` 已被模块吸收 | `MT02_06`、`MT02_08` | 页面 adapter 与验证矩阵可以并行，一个负责承接 UI，一个负责验证全局权限行为 |

## 4. 当前判断

- `M02` 当前已经不是“模块内容太少”，而是“遗留子任务入口过粗”。
- 按文档治理规则，子任务设计启动前，`MODULE_REQUIREMENTS / DESIGN / API / SCHEMA / LOGIC` 至少都应达到 `L5` 或稳定 `L5` 候选；本轮先把任务入口清理正确。
- 全局 `OQ-024` 已写死为“历史容器固定、观察蓝本固定、正式开窗层当前为空”；模块本轮只吸收该引用，因此当前没有任何旧入口或新蓝本可以被视为“可直开子任务入口”。
- 当前不建议直接开启任何 `ST02_01 ~ ST02_03` 子任务设计窗口，也不建议把 `MT02_01 ~ MT02_08` 误写成已放行的正式子任务。
- 当前最多只能给出“白名单观察面”，而不是放行判断：
  - 本轮白名单观察面仅为：`MT02_01`、`MT02_02`
  - `MT02_03`、`MT02_07` 仅保留后续观察顺序，不纳入本轮白名单
  - 仍被阻塞：`MT02_04` 的 `/members` 列表契约虽已在模块内闭合到共享最小层，但该口径当前仍只处于 `OQ-021` 默认治理层且 `MODULE_API_DESIGN.md` 仍是最低位；`MT02_05/MT02_06` 受 `OQ-020/OQ-021/OQ-022`、页面 adapter 后置与入口映射约束；`MT02_08` 必须等待 `MT02_04`、`MT02_07`
- 白名单观察面只表示总控可继续复核的最小非页面变化面，不等于可以开子任务窗口，也不允许据此补写对应子任务双文档。
- `OQ-023` 已足以支撑职责重切，因此 `MT02_07` 可继续作为独立 policy 面候选，而不是继续挂在管理台实现里。

## 5. 下一轮开启子任务设计前必须满足

- 模块评审通过，并确认 `MODULE_REQUIREMENTS / DESIGN / API / SCHEMA / LOGIC` 已达到治理要求的下游输入成熟度。
- 总控基于已写死的 `OQ-024` 三层映射，在后续正式候选复评中把 `MT02_01 ~ MT02_08` 的部分蓝本从“观察层”推进到“正式入口 / 开窗层”。
- 总控明确把“白名单观察面”转换为“正式子任务候选”的触发条件，避免 `MT02_01/MT02_02` 被误写成已开窗任务。
- `MT02_02` 相关的 `CurrentUserContext`、`logout=204`、`401/403` 语义，以及 admin route group 的消费边界继续稳定留在模块层，不再回流到子任务层重新定义。
- `MQ-205` / `OQ-021` 的共享最小层已被 `M02` 模块文档完整吸收并闭合；但在总控明确其可作为正式候选输入前，`MT02_04/MT02_06` 仍不得开窗。
- `MQ-206` / `OQ-022` 的默认口径已被模块文档完整吸收，登录页 / 成员页不再需要各自补 namespace / fallback。
- 总控完成 `DOCUMENT_MATURITY.md`、`DOCUMENT_PROGRESS.md`、`MODULE_INDEX.md` 的正式回写，避免继续出现“模块自评已接近 `L5`、全局仍记录为 `L4`”的双重叙事。

## 6. 使用规则

- 在总控未正式回写 `L5` 前，不要直接补写遗留 `ST02_01 ~ ST02_03` 双文档来掩盖上游缺口。
- 下一轮若进入子任务设计，必须按新的微任务边界拆解，不再把 schema、API、page、policy、verification 混成一个目录。
- `MQ-202` 已冻结：`/members` 为团队内基础成员目录，字段集固定为 `id`、`displayName`、`role`、`status`，跨团队详情访问返回 `403`。
- `MQ-203` 已按方案 B 冻结：`M02` 只负责 admin 鉴权与最小契约，完整成员管理实现后移到后续治理模块。
- `MQ-204` 已按方案 A 冻结：`teams.status` / `users.status` 只冻结 `active`，软删除继续由 `deleted_at` 表达。
- 在 `MQ-205` 的实现级接口仍未细化前，不要在微任务或样例代码中擅自固定 `/members` 的 query / envelope 形态。
- 在 `MQ-206` 默认口径尚未被模块完整吸收前，不要在页面微任务中私自扩张 `M01` 之外的 locale namespace / fallback 规则。
- 本轮未创建新子任务目录；现有 `ST02_01 ~ ST02_03` 只保留为历史占位，直到总控确认新的编号和迁移策略。

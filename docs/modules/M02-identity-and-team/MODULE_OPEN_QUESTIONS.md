# M02 鉴权、团队与成员 - 模块待确认问题

> W13 事实源对齐：本文只保留 M02 模块内 MQ/OQ 治理记录。凡涉及一期 MVP 范围、IA / 用户旅程、对象模型 / RAG / 多轮 / 后端边界、评分 / 复盘 / 导出 / DoD 的当前事实，统一引用 `docs/design/workbench-mvp/scope.md`、`docs/design/workbench-mvp/information-architecture.md`、`docs/design/workbench-mvp/object-model-rag-multiround-backend.md`、`docs/design/workbench-mvp/scoring-review-export-dod.md`。旧 MQ/OQ 中若出现 W10 `apps/web` 原型、首切片 MVP、RAG / 知识库后续、多轮固定三轮或直接发起模拟面试等产品范围判断，一律按 historical / superseded 理解，不作为当前事实源。

## 1. 文档定位

- 本文档用于记录 `M02` 模块内部仍未收敛、会影响模块设计评审或后续子任务设计的问题。
- 本文档只记录模块级问题，不替代根目录 `OPEN_QUESTIONS.md` 的全局问题总表。

## 2. 已采用的上游默认口径

| OQ ID | 当前状态 | 本轮采用方式 | 影响文档 |
| --- | --- | --- | --- |
| `OQ-004` | `proposed-default` | 按“JWT 前的开发态认证适配层”推进 `M02` 收敛到 `L5` 候选，不扩展 JWT / session cookie | `MODULE_REQUIREMENTS.md`、`MODULE_API_DESIGN.md`、`MODULE_LOGIC_DESIGN.md` |
| `OQ-005` | `proposed-default` | 按“首轮只覆盖 P1 页面与 API 权限矩阵”推进，不扩展未来多租户治理 | `MODULE_REQUIREMENTS.md`、`MODULE_DESIGN.md`、`MODULE_API_DESIGN.md` |
| `OQ-023` | `proposed-default` | 按方案 B 推进：`M02` 只负责身份解析、授权规则、权限矩阵与最小鉴权契约，完整成员管理页面 / API 由后续治理模块承接 | `MODULE_DESIGN.md`、`MODULE_DEPENDENCIES.md`、`MODULE_TASK_INDEX.md` |
| `OQ-024` | `proposed-default` | 模块内已吸收总控写死的三层映射引用：旧 `ST02_*` 目录只保留为历史容器，`MT02_*` 只按观察蓝本口径记录，正式开窗层当前仍为空；模块不得自行宣布放行 | `MODULE_TASK_INDEX.md`、`MODULE_DEPENDENCIES.md`、`MODULE_DESIGN.md`、`MODULE_API_DESIGN.md` |

## 3. 问题表

| MQ ID | 问题 | 状态 | 影响范围 | 当前建议 | 是否需上升到全局 | 需回写文档 |
| --- | --- | --- | --- | --- | --- | --- |
| `MQ-201` | 作为“JWT 前的开发态认证适配层”，是否需要至少为 `admin` / `member` 各冻结一组独立 token 与演示凭据 | `confirmed` | `MODULE_API_DESIGN` / `MODULE_LOGIC_DESIGN` / `MT02_01` / `MT02_02` | 已确认采用默认方案：提供两组演示身份映射，全部从 `.env` 或 seed 读取，并明确业务层不得依赖 token 内部结构 | 否 | `MODULE_API_DESIGN.md`、`MODULE_LOGIC_DESIGN.md`、`MODULE_TASK_INDEX.md` |
| `MQ-202` | `/(dashboard)/members` 与 `GET /api/v1/members*` 是“团队内可读目录”还是“管理员专属目录” | `confirmed` | `MODULE_API_DESIGN` / `MODULE_LOGIC_DESIGN` / `MT02_04` / `MT02_06` / `MT02_08` | 已确认采用默认方案：`/members` 为团队内基础成员目录，`admin` 与 `member` 都可读取本团队成员；首轮字段集只冻结 `id`、`displayName`、`role`、`status`；跨团队成员详情访问统一返回 `403` | 否 | `MODULE_REQUIREMENTS.md`、`MODULE_API_DESIGN.md`、`MODULE_LOGIC_DESIGN.md`、`MODULE_SCHEMA_DESIGN.md` |
| `MQ-203` | `/(dashboard)/admin/members` 与 `/api/v1/admin/members` 的完整实现归属是由 `M02` 继续承接，还是由后续治理模块承接、`M02` 只输出鉴权规则 | `confirmed` | `MODULE_DESIGN` / `MODULE_DEPENDENCIES` / `MT02_07` / 后续管理台模块 | 已确认采用方案 B，且已与全局 `OQ-023` 对齐：`M02` 负责身份解析、授权规则、权限矩阵与最小契约；完整成员管理页面 / API 实现由后续治理模块承接 | 是 | `MODULE_DESIGN.md`、`MODULE_DEPENDENCIES.md`、`MODULE_TASK_INDEX.md` |
| `MQ-204` | `teams.status`、`users.status` 在 `P1` 最小交付中需要冻结到什么粒度 | `confirmed` | `MODULE_SCHEMA_DESIGN` / `MODULE_LOGIC_DESIGN` / `MT02_03` / `MT02_04` | 已确认采用方案 A：`P1` 只冻结 `active`；软删除继续由 `deleted_at` 表达；`disabled / invited / suspended / archived` 等状态不进入当前模块契约 | 否 | `MODULE_SCHEMA_DESIGN.md`、`MODULE_LOGIC_DESIGN.md`、`MODULE_TASK_INDEX.md` |
| `MQ-205` | `/api/v1/members` 的列表 envelope、分页参数与查询状态，应如何与 `M01` `DataTable` / `Pagination` 的最小共享契约对齐 | `proposed-default` | `MODULE_API_DESIGN` / `MODULE_LOGIC_DESIGN` / `MODULE_DEPENDENCIES` / `MT02_04` / `MT02_06` / `MT02_08` | 已与全局 `OQ-021` 对齐，并在模块内闭合到共享最小层：沿用 `page/page_size/q/status/sort/order` 与统一分页骨架；callback、URL 序列化与 request adapter 细节继续留在页面 / 实现层，不再补 `M02` 私有 query / envelope / URL 协议。该闭合只解决模块内误补协议，不构成 `MT02_04 / MT02_06` 的正式候选放行依据；其中 `MT02_06` 还额外受 `OQ-020 / OQ-022` 与页面 adapter 后置约束 | 否 | `MODULE_API_DESIGN.md`、`MODULE_LOGIC_DESIGN.md`、`MODULE_DEPENDENCIES.md`、`MODULE_TASK_INDEX.md` |
| `MQ-206` | `/login` 与 `/(dashboard)/members` 复用的 i18n namespace / locale fallback，是否已足以作为页面子任务输入下发 | `proposed-default` | `MODULE_DESIGN` / `MODULE_DEPENDENCIES` / `MT02_05` / `MT02_06` | 当前按全局 `OQ-022` 默认口径推进：继承 `M01` 的集中入口、locale seed、统一 fallback 与最小 namespace 边界；在模块完成吸收前，不补模块私有 namespace / fallback 规则 | 否 | `MODULE_REQUIREMENTS.md`、`MODULE_DESIGN.md`、`MODULE_DEPENDENCIES.md`、`MODULE_TASK_INDEX.md` |
| `MQ-207` | 在 `OQ-024` 正式映射已写死后，`M02` 应如何吸收其引用并避免把观察蓝本误写成正式入口 | `proposed-default` | `MODULE_TASK_INDEX` / `MODULE_DEPENDENCIES` / `MODULE_DESIGN` / `MODULE_API_DESIGN` / 下一轮 `P03` 子任务设计窗口 | 已按全局 `OQ-024` 吸收三层映射引用：`ST02_01 -> MT02_01/MT02_02/MT02_05`、`ST02_02 -> MT02_03/MT02_04/MT02_06`、`ST02_03 -> MT02_07/MT02_08`；旧目录只保留为历史容器，`MT02_*` 当前只可按观察蓝本口径引用；正式开窗层仍为空，因此不得直开旧目录，也不得把 `MT02_*` 误写成正式入口 | 是 | `MODULE_TASK_INDEX.md`、`MODULE_DEPENDENCIES.md`、`MODULE_DESIGN.md`、`MODULE_API_DESIGN.md`、`MODULE_EXECUTION_LOG.md` |
| `MQ-208` | `M02` 首轮是否需要独立成员详情页 UI，还是只冻结成员列表页 + 详情 API 语义 | `proposed-default` | `MODULE_DESIGN` / `MODULE_TASK_INDEX` / `MT02_04` / `MT02_06` | 当前建议只冻结成员列表页承接与 `GET /api/v1/members/{member_id}` 详情 API 语义，不单列成员详情页 UI；若后续确需页面，再新增微任务 | 否 | `MODULE_DESIGN.md`、`MODULE_TASK_INDEX.md`、`MODULE_EXECUTION_LOG.md` |
| `MQ-209` | 在“候选白名单准备”轮中，`MT02_01` / `MT02_02` 的白名单观察面结论应如何与正式子任务开窗条件分离，避免被误回写为已放行入口 | `confirmed` | `MODULE_API_DESIGN` / `MODULE_DEPENDENCIES` / `MODULE_TASK_INDEX` / `MODULE_EXECUTION_LOG` / 总控全局回写 | 已确认：白名单观察面只表示总控可继续跟踪的最小非页面变化面，不等于正式子任务设计候选；`MT02_01/MT02_02` 仍只是观察面，还因为 `MODULE_API_DESIGN.md` 仍是模块最低位高 `L4`。全局 `OQ-024` 虽已写死三层映射，但正式开窗层当前仍为空，正式开窗仍需总控在后续复评中把 `MT02_01/MT02_02` 从观察蓝本推进到正式候选，并同步全局成熟度回写；复读遗留 `ST02_01 / ST02_02` 后也已确认其 `SUBTASK_DESIGN.md` 仍标注“当前成熟度：仅有骨架”，父模块行仍残留 `$(System.Collections.Specialized.OrderedDictionary.Id)` 占位符，`SUBTASK_IMPLEMENTATION.md` 仍为空白实施模板，因此旧容器不得充当 `MT02_01/MT02_02` 的正式入口证明；`CurrentUserContext` / `401/403` / route group 消费边界继续留在模块层 | 是 | `MODULE_API_DESIGN.md`、`MODULE_DEPENDENCIES.md`、`MODULE_TASK_INDEX.md`、`MODULE_EXECUTION_LOG.md` |

## 4. 当前高优问题

| 优先级 | MQ ID | 当前阻塞文档 | 原因 | 本轮处理要求 |
| --- | --- | --- | --- | --- |
| `P0` | `MQ-205` | `MODULE_API_DESIGN.md`、`MODULE_LOGIC_DESIGN.md`、`MODULE_TASK_INDEX.md` | 若把 `/members` 共享列表契约“已闭合到共享最小层”误读成“已形成正式候选输入”，`MT02_04` / `MT02_06` 会被误判为接近放行 | 本轮已按共享最小层闭合吸收，并同步写明“闭合 != 放行”，不在 `M02` 内私自补协议或外推 ready |
| `P0` | `MQ-206` | `MODULE_DESIGN.md`、`MODULE_DEPENDENCIES.md`、`MODULE_TASK_INDEX.md` | 若页面 i18n 默认口径未被模块吸收，登录页与成员页子任务仍容易各写一套 namespace / fallback | 按总控 `proposed-default` 口径吸收，不在 `M02` 内私自扩张 i18n 规则 |
| `P1` | `MQ-207` | `MODULE_TASK_INDEX.md`、`MODULE_DEPENDENCIES.md`、`MODULE_DESIGN.md`、`MODULE_API_DESIGN.md` | 若不吸收 `OQ-024` 已写死的三层映射引用，非页面候选也会继续被旧入口拖回粗粒度任务包，或把观察蓝本误写成正式入口 | 本轮只吸收全局映射引用，不重命名目录，也不放开子任务入口 |
| `P1` | `MQ-208` | `MODULE_DESIGN.md`、`MODULE_TASK_INDEX.md` | 若成员详情页 UI 范围不收紧，新的成员目录微任务仍会把页面目标、API 语义和 schema 混成一个任务包 | 本轮先按“列表页 + 详情 API”默认口径收缩 |
| `P1` | `MQ-209` | `MODULE_API_DESIGN.md`、`MODULE_DEPENDENCIES.md`、`MODULE_TASK_INDEX.md`、`MODULE_EXECUTION_LOG.md` | 若不把白名单观察面和正式开窗条件拆开，总控与下游会把 `MT02_01/MT02_02` 误读为可立即创建子任务窗口，并把遗留 `ST02_*` 骨架设计文档 / 空白实施模板误当作正式入口证据，或把 `MT02_02` 误扩张成权限矩阵定义入口 | 本轮按 `confirmed` 回写模块结论，并只建议总控同步全局状态，不开放子任务窗口 |

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
  - 本轮处理：已升级并对齐到全局 `OQ-024`；模块内吸收的是“历史容器固定、观察蓝本固定、正式开窗层当前为空”的引用，不再把“是否继续沿用旧入口”保持为 `open`。
- `MQ-209`
  - 原因：涉及全局对白名单状态、正式开窗状态和模块成熟度状态的统一叙事。
  - 本轮处理：模块内已确认 `MT02_01/MT02_02` 只属于观察面；且补充确认现有遗留 `ST02_01` 双文档仍是骨架 / 模板，不能作为正式入口依据。需由总控同步 `DOCUMENT_MATURITY.md`、`DOCUMENT_PROGRESS.md`、`MODULE_INDEX.md`、`TASK_INDEX.md`、`OPEN_QUESTIONS.md` 等全局状态文档。

## 6. 当前判断

- `M02` 模块内的业务边界、角色边界和 schema 口径已基本收口。
- 当前剩余阻塞以共享契约问题、任务入口放行问题，以及“白名单观察面 vs 正式开窗状态”的治理边界为主：`MQ-205` / `OQ-021` 已在模块内闭合到共享最小层，但全局仍处于 `proposed-default` 吸收阶段；`MQ-206` / `OQ-022` 仍是需继续吸收的共享默认口径；`MQ-207` / `OQ-024` 当前要求旧入口继续停留在历史容器状态且正式开窗层维持为空；`MQ-209` 已确认本轮只能给出观察结论而不是开窗结论。
- 本轮补充复核后，`MT02_01/MT02_02` 仍不是正式子任务候选，原因不仅是全局映射与状态回写未完成，也包括 `MODULE_API_DESIGN.md` 仍是高 `L4` 最低位，以及复读遗留 `ST02_01 / ST02_02` 后确认其 `SUBTASK_DESIGN.md` 仍标注为“仅有骨架”且父模块行仍是占位符，`SUBTASK_IMPLEMENTATION.md` 仍为空白模板，不能作为正式入口的承接材料。
- 同时，`/members` 当前应被稳定解读为“模块内已闭合到共享最小层，但仍未放行正式候选输入”；因此既不能把 `MT02_04` 写成 ready，也不能把 `MT02_06` 写成 ready。
- 因此 `M02` 当前判断应为“模块整体可为总控提供白名单观察输入，但 `MT02_01/MT02_02` 仍未达到正式子任务开窗条件，`MT02_04/MT02_06` 也仍未达到正式候选判断条件”；非页面微任务最多只处于观察面或后续观察顺序，而不是“模块内问题已清空即可自动视为 `L5`”。

# AI 模拟面试 P1 待确认问题

## 1. 文档定位

- 本文档汇总当前项目的全局待确认问题。
- 本文档用于帮助总控 Codex、模块 Codex 和评审 Codex 判断：
  - 当前哪些问题会直接阻塞模块成熟度提升
  - 当前哪些问题只需要默认方案即可继续推进
  - 当前哪些问题已应被关闭或降级
- 状态使用：
  - `open`
  - `proposed-default`
  - `confirmed`
  - `superseded`

## 2. 问题表

| OQ ID | 问题 | 状态 | 关联模块 | 当前建议 | 需回写文档 |
| --- | --- | --- | --- | --- | --- |
| OQ-001 | 目标产品代码结构是否固定为 monorepo（`apps/web` + `apps/api` + `infra`），并与当前文档治理仓分层共存 | proposed-default | M01-M10 | 当前仓库继续保持“根目录全局文档 + `docs/` + `tools/doc_governor/` + `tests/doc_governor/`”布局；`W10-D-Gate` 已确认当前阶段只允许在正式开窗层为空时进入首切片最小原型探索，且仅允许创建 `apps/web/**` 最小原型骨架，`apps/api/**` 与 `infra/**` 本轮继续禁止；若后续进入更完整业务代码实施，monorepo 目标形态仍只作为后续阶段候选推进 | `DESIGN_DECISIONS.md`、`TECHNICAL_STANDARDS.md` |
| OQ-002 | 首轮是否只建立最小运行时、测试和 CI 基线 | proposed-default | M01、M10 | 最小运行时、测试和 CI 基线只在 `W10-D` 被条件放行时作为最小骨架输入使用，不构成 `W10-A` 直接创建业务代码目录的依据 | `PLAN_LATEST.md`、`TECHNICAL_STANDARDS.md` |
| OQ-003 | 视觉规范首轮需要沉淀到什么粒度 | proposed-default | M01 | 本轮只沉淀壳层、头部、列表原语与基础页面样式 | `TECHNICAL_STANDARDS.md` |
| OQ-004 | P1 鉴权机制采用固定 Bearer token、JWT 还是 session cookie | proposed-default | M02、M10 | 本轮先采用开发态 Bearer adapter：统一 `Authorization: Bearer <token>`、`current_user / role / team_id` 上下文，业务层不得依赖 token 内部结构 | `DESIGN_DECISIONS.md`、`TECHNICAL_STANDARDS.md` |
| OQ-005 | 团队管理员与普通成员的权限矩阵是否先只覆盖 P1 页面 | proposed-default | M02、M10 | 本轮先覆盖 P1 页面与 API，不扩展未来多租户治理场景 | `DESIGN_DECISIONS.md`、`MODULE_INDEX.md` |
| OQ-006 | Markdown 预览与导出是否必须共用同一渲染链 | proposed-default | M03 | 本轮按共用同一渲染链推进，以避免结果偏差 | `DESIGN_DECISIONS.md`、`TECHNICAL_STANDARDS.md` |
| OQ-007 | 上传、转换、导出在 P1 中哪些必须异步 | proposed-default | M03、M10 | 本轮按“上传同步入库，转换与导出异步”推进 | `TECHNICAL_STANDARDS.md` |
| OQ-008 | 匹配分析与评估规则是否需要版本化 | proposed-default | M04、M07、M10 | 本轮先按保留规则版本推进，便于解释与回放 | `TECHNICAL_STANDARDS.md`、`DESIGN_DECISIONS.md` |
| OQ-009 | Embedding 与向量化来源如何确定 | open | M05、M06 | 默认先抽象 provider 接口，并使用本地配置驱动 | `TECHNICAL_STANDARDS.md` |
| OQ-010 | 归档粒度是整份资产、片段还是题目级 | open | M05、M08 | 默认以资产级与片段级为主，题目级作为派生视图 | `MODULE_INDEX.md` |
| OQ-011 | Search snapshot 的来源只做导入还是需要抓取 | proposed-default | M06、M10 | 本轮先按 P1 只做导入，不做在线抓取推进 | `DESIGN_DECISIONS.md`、`TECHNICAL_STANDARDS.md` |
| OQ-012 | 上下文包中的 source priority 与引用摘要规则如何定稿 | open | M06 | 默认优先级为 JD > 简历 > 训练证据 > 资产检索 > search snapshot | `TECHNICAL_STANDARDS.md` |
| OQ-013 | 打磨主题推荐是规则、LLM 还是混合 | open | M07 | 默认首轮采用规则推荐 | `DESIGN_DECISIONS.md`、`TECHNICAL_STANDARDS.md` |
| OQ-014 | 模拟面试、打磨模式和复盘是否共用同一评估口径 | proposed-default | M07、M08、M09 | 本轮先按共享核心评估框架、允许场景级字段扩展推进 | `TECHNICAL_STANDARDS.md` |
| OQ-015 | 真实面试输入是结构化问答、自由 transcript 还是混合 | open | M08 | 默认采用混合输入模型 | `MODULE_INDEX.md` |
| OQ-016 | 薄弱项聚合 key、消减规则和停练规则如何定稿 | open | M09 | 默认按能力节点 + 题型 + 证据来源聚合，规则后续评审定稿 | `TECHNICAL_STANDARDS.md`、`DESIGN_DECISIONS.md` |
| OQ-017 | 管理台的模型推荐来源是本地 catalog 还是在线同步 | proposed-default | M10 | 本轮先按本地 catalog / seed 推进 | `DESIGN_DECISIONS.md`、`TECHNICAL_STANDARDS.md` |
| OQ-018 | 管理台是否负责 search snapshot 导入与运维 | proposed-default | M06、M10 | 本轮先按负责导入与运维入口、不承担抓取本身推进 | `TECHNICAL_STANDARDS.md`、`MODULE_INDEX.md` |
| OQ-019 | 根目录统一脚本与最小 CI 校验矩阵应冻结到什么粒度，才算满足平台基线的下游输入要求 | proposed-default | M01、M10 | 本轮先采用方案 B：冻结统一脚本命名（`dev:web` / `dev:api` / `test:web` / `test:api`）、最小存活检查（`GET /api/v1/health` -> `200 {\"status\":\"ok\"}`）与最小验证入口类型（API=`pytest`、Web=`vitest`），CI 只冻结 API/Web 两类最小校验 lane，不在当前轮冻结完整流水线矩阵 | `TECHNICAL_STANDARDS.md`、`DESIGN_DECISIONS.md`、`DOCUMENT_PROGRESS.md` |
| OQ-020 | 共享页面原语（`PageHeader` / Dashboard 摘要区）应冻结到什么最小接口边界，才能支撑后续页面复用 | proposed-default | M01、M02、M03 | 本轮先采用方案 B：冻结最小共享页面原语边界；`PageHeader` 只承载标题/说明/主次动作，摘要区独立承载 `status_badge` / `updated_at` / `summary_items` 与最小状态表达，不扩张为完整 props catalog | `TECHNICAL_STANDARDS.md`、`DESIGN_DECISIONS.md`、`DOCUMENT_PROGRESS.md` |
| OQ-021 | 列表查询状态、分页交互与 URL / callback 的映射规则应如何统一 | proposed-default | M01、M02、M03、M04-M10 | 当前默认采用方案 B，并按三层状态分层：共享最小层固定为 `page` / `page_size` / `q` / `status` / `sort` / `order` 与统一分页响应骨架；模块扩展层允许单独登记扩展查询键（如 `updated_after` / `updated_before`），但不得回写成共享前提；实现细节层中的 route / callback / request adapter 细节继续留在各模块最低位文档处理。该口径已足够支撑本轮最低位压缩，但仍未达到可直接放行正式候选的程度。本轮模块吸收摘要更新为：`M01` 已压到共享最小层输入且当前目标项已清理完成，但整体仍未被总控接受；`M02` 已在模块内把 `GET /api/v1/members` 闭合到共享最小层且明确“闭合 != 放行”，当前最小剩余缺口已进一步压实为“该共享最小层仍只停留在 `proposed-default` 治理层、尚未升格为正式候选输入 + 正式开窗层为空 + 权限消费边界留在模块层”；`M03` 已在最低位 API 文档稳定吸收且仍未放行 | `TECHNICAL_STANDARDS.md`、`DESIGN_DECISIONS.md`、`DOCUMENT_PROGRESS.md` |
| OQ-022 | locale fallback、切换策略与消息命名空间应冻结到什么程度，才能作为共享 Web 契约下发 | proposed-default | M01、M02、M03、M04-M10 | 本轮先采用方案 B：统一 `apps/web/src/i18n/**` + `getMessages(locale)` 入口，首轮 locale seed 固定为 `zh-CN` / `en-US`、默认 locale=`zh-CN`；切换由 layout / App Shell 统一解析 active locale；fallback 固定为“请求 locale -> `zh-CN` -> 记录缺失 key”，禁止组件硬编码兜底；namespace 只冻结“共享壳层一层、业务页面一层”的最小边界，不扩张为完整 i18n 架构 | `TECHNICAL_STANDARDS.md`、`DESIGN_DECISIONS.md`、`DOCUMENT_PROGRESS.md` |
| OQ-023 | `/(dashboard)/admin/members` 与 `/api/v1/admin/members` 的完整实现应继续由 M02 承接，还是由后续治理模块承接 | proposed-default | M02、M10 | 本轮先采用方案 B：`M02` 只负责身份解析、授权规则、权限矩阵与最小鉴权契约，完整成员管理页面 / API 由后续治理模块承接 | `DESIGN_DECISIONS.md`、`MODULE_INDEX.md` |
| OQ-024 | 计划重构后，旧 `ST02_* / ST03_*` 子任务目录是否应退役为历史容器，并按新的微任务蓝本重建正式入口 | proposed-default | M02、M03 | 当前按总控固定映射处理，并已写死为默认治理口径：历史容器层中，`ST02_01 / ST02_02 / ST02_03 / ST03_01 / ST03_02 / ST03_03` 全部固定为历史容器且禁止直开；观察蓝本层中，`M02` 当前只允许 `MT02_01 / MT02_02`，`M03` 当前只允许 `MT03_01 / MT03_03` 作为白名单观察入口，其余蓝本不得自行上推；正式开窗层中，本轮正式子任务 ID 名单固定为空，只有总控在后续正式候选复评完成后才能在 `TASK_INDEX.md` 中新增正式子任务 ID 与开窗资格。`MQ-209` 已吸收到本条叙事中。当前 `M01 / M02 / M03` 都不是正式子任务设计候选；本轮后续残余已不再是映射未同步或模块侧文案残差，而是正式开窗层持续为空所形成的治理性结构阻塞 | `TASK_INDEX.md`、`DOCUMENT_PROGRESS.md`、`MODULE_INDEX.md` |
| OQ-025 | `jobs.requirement_items_json` 的最小 item 结构、空值语义、排序规则与写入责任应冻结到什么程度，才能作为 M04 / M06 的稳定输入 | proposed-default | M03、M04、M06 | 当前按三层状态分层处理：最小共享输入层固定为 `item_key` / `text`、`null / []` 语义、数组顺序即消费顺序，以及“仅岗位写模型可整体替换”；扩展字段层继续保持未冻结，不进入共享稳定输入；完整链路语义层继续留在 `M03` 的最低位文档压缩，不据此宣布完整岗位链 / 下游链 ready。该口径已被 `M03` 吸收为最小共享输入，但不等于 `MT03_01 / MT03_03` 已升级为正式候选；当前对 `M04 / M06` 只可作为最小设计输入，不足以支撑上传 / 导出微任务或完整岗位链 ready。本轮状态补充为：`M03` 的直接结构性主阻塞已统一写成“正式开窗层为空 + 当前阶段关窗 + 上传 / 导出链依赖未变”，而最低位 API 高 `L4` 只是结果态 | `TECHNICAL_STANDARDS.md`、`DESIGN_DECISIONS.md`、`DOCUMENT_PROGRESS.md` |

## 3. 本轮高优问题处理判断

- 本轮（阶段 3 / 总控澄清 + 模块候选白名单准备轮）必须优先处理的问题：
  - `OQ-024` 旧入口退役后的全局映射与直开约束
  - `OQ-025` `jobs.requirement_items_json` 最小输入契约
  - `OQ-021` 共享最小映射与模块级扩展的边界澄清
- 本轮检查结论：
  - `OQ-021 / OQ-024 / OQ-025` 本轮统一继续保持 `proposed-default`，本轮目标是把三者的状态分层、模块吸收结果与真实剩余条件继续锁死，而不是把三者推进到 `confirmed`
  - `OQ-021` 继续保持 `proposed-default`，并正式分为“共享最小层 / 模块扩展层 / 实现细节层”；`updated_after` / `updated_before` 当前不属于共享最小层
  - `OQ-024` 继续保持 `proposed-default`，并正式分为“历史容器层 / 观察蓝本层 / 正式开窗层”；当前该三层映射已被总控写死，白名单观察面与正式子任务开窗条件必须显式分离
  - `OQ-025` 继续保持 `proposed-default`，并正式分为“最小共享输入层 / 扩展字段层 / 完整链路语义层”；当前只足够支撑最低位压缩与最小下游引用，不足以宣告岗位链整体 ready
  - 当前总控补充判断为：`M03` 对 `OQ-021 / OQ-025` 的最低位吸收已经基本稳定，应写成“已吸收但未放行”，且 `OQ-024` 不应再被写成“待同步”；`M02` 已在模块内把 `/members` 闭合到共享最小层，但当前最小剩余缺口已进一步压实为“该共享最小层尚未从 `proposed-default` 治理层升格为正式候选输入”；`M01` 已把 `OQ-021` 吸收为共享最小层输入，且当前目标项已清理完成，但这不等于模块整体候选已成立
  - 本轮不新增全局 OQ；模块局部问题继续只作为吸收记录：`MQ-205 -> OQ-021`、`MQ-207 / MQ-209 -> OQ-024`、`MQ-307 / MQ-308 / MQ-309 -> OQ-025`
  - `OQ-019~OQ-023` 继续维持上一轮已登记的默认冻结口径，不再作为本轮主阻塞重复讨论

| 优先级 | OQ ID | 当前状态 | 当前影响模块 | 本轮处理判断 |
| --- | --- | --- | --- | --- |
| P0 | OQ-001 | proposed-default | M01-M10 | 已按默认目标产品 monorepo 口径冻结，可作为本轮 `M01-M03` 输入；当前仓库布局仍以 `docs/` + `tools/doc_governor/` + `tests/doc_governor/` 为准 |
| P0 | OQ-004 | proposed-default | M02、M10 | 已按固定 Bearer token 冻结，可作为本轮 `M02` 输入 |
| P0 | OQ-006、OQ-007 | proposed-default | M03、M10 | 已按共享渲染链与“上传同步/转换导出异步”冻结，可作为本轮 `M03` 输入 |
| P0 | OQ-019 | proposed-default | M01、M10 | 已形成入口语义级默认冻结方案；可作为 `M01` 平台基线与 `M10` 治理边界切分输入，但暂不扩张为完整流水线定稿 |
| P0 | OQ-021 | proposed-default | M01、M02、M03、M04-M10 | 已形成三层状态：共享最小映射维持 `page/page_size/q/status/sort/order`、分页骨架与页面容器 adapter 职责；模块扩展键单独登记；route / callback / request adapter 细节继续留在最低位文档处理。模块吸收摘要：`M01` 已压到共享最小层输入且当前目标项已清理完成，`M02` 已在模块内闭合到共享最小层但 `GET /api/v1/members` 当前仍只停留在默认治理层、尚未升格为正式候选输入，`M03` 已吸收但未放行 |
| P0 | OQ-024 | proposed-default | M02、M03 | 已形成并写死三层状态：旧 `ST02_* / ST03_*` 为历史容器、`M02` 当前只允许 `MT02_01 / MT02_02`、`M03` 当前只允许 `MT03_01 / MT03_03` 作为观察蓝本、正式子任务 ID 与开窗资格继续后置到正式候选复评之后；当前正式开窗名单固定为空。`MR-18 / MR-23 / RV-09` 已把 `M03` 的现行口径压稳为“已吸收但未放行”，当前剩余只保留正式开窗层为空所形成的治理性结构阻塞，不再重开全局映射讨论 |
| P0 | OQ-025 | proposed-default | M03、M04、M06 | 已形成三层状态：`item_key` / `text`、`null` / `[]`、数组顺序与写入责任属于最小共享输入层；扩展字段继续未冻结；完整岗位链语义继续留在模块最低位文档处理。`M03` 已吸收最小共享输入，但该问题目前只足够支撑 `M04 / M06` 的最小设计输入，仍不足以支撑上传 / 导出微任务或完整岗位链 ready；当前直接结构性主阻塞已固定为“正式开窗层为空 + 当前阶段关窗 + 上传 / 导出链依赖未变”，最低位 API 高 `L4` 是结果态 |
| P1 | OQ-020 | proposed-default | M01、M02、M03 | 已形成方案 B 默认冻结候选；最小共享页面原语已足够支撑 `M01/M03` 继续推进，并为 `M02` 提供页面承接口径，但暂不升级为 `confirmed` |
| P1 | OQ-022 | proposed-default | M01、M02、M03、M04-M10 | 已形成最小 i18n 共享默认口径；可作为模块设计输入，但完整 locale 切换持久化、URL 策略与 formatter 规则仍未冻结 |
| P1 | OQ-023 | proposed-default | M02、M10 | 继续保持 `proposed-default`；本轮直接作为模块职责重切输入，不再回退为 `open` |
| P1 | OQ-008 | proposed-default | M04、M07、M10 | 已按“规则需要版本化”冻结，作为评审窗口基线 |
| P1 | OQ-011、OQ-018 | proposed-default | M06、M10 | 已按“snapshot 只导入、不抓取；管理台负责导入与运维入口”冻结，作为评审窗口基线 |
| P1 | OQ-012 | open | M06 | 暂不冻结；当前默认只覆盖 source priority，尚未覆盖引用摘要规则 |
| P1 | OQ-014 | proposed-default | M07、M08、M09 | 已按共享核心评估框架冻结，作为评审窗口基线 |
| P1 | OQ-016 | open | M09 | 暂不冻结；当前默认只覆盖聚合 key，尚未覆盖消减与停练规则 |
| P1 | OQ-017 | proposed-default | M10 | 已按本地 catalog / seed 冻结，作为评审窗口基线 |

## 4. 默认方案冻结建议

> 本节用于帮助总控 Codex 在“信息仍不充分”时决定：哪些问题可以先按默认方案冻结，从而继续推进模块文档。

| OQ ID | 本轮处理 | 默认方案是否足以继续推进 | 若冻结后优先推进模块 |
| --- | --- | --- | --- |
| OQ-001 | 已标记 `proposed-default` | 是，但当前只足够支撑首切片设计冻结，不足以在 `W10-A` 直接创建业务代码目录 | M01-M03 |
| OQ-002 | 已标记 `proposed-default` | 是，但仅在 `W10-D` 被条件放行后才进入最小骨架输入 | M01、M10 |
| OQ-003 | 已标记 `proposed-default` | 是 | M01 |
| OQ-004 | 已标记 `proposed-default` | 是，但需在设计决策中显式记录 | M02、M10 |
| OQ-005 | 已标记 `proposed-default` | 是 | M02 |
| OQ-006 | 已标记 `proposed-default` | 是 | M03 |
| OQ-007 | 已标记 `proposed-default` | 是 | M03 |
| OQ-008 | 已标记 `proposed-default` | 是 | M04、M07 |
| OQ-009 | 保持 `open` | 本轮暂不需要 | M05 |
| OQ-010 | 保持 `open` | 本轮暂不需要 | M05、M08 |
| OQ-011 | 已标记 `proposed-default` | 是 | M06、M10 |
| OQ-012 | 保持 `open` | 否，默认方案尚不足以覆盖引用摘要规则 | M06 |
| OQ-013 | 保持 `open` | 本轮暂不需要 | M07 |
| OQ-014 | 已标记 `proposed-default` | 是，但需跨模块同步 | M07、M08、M09 |
| OQ-015 | 保持 `open` | 本轮暂不需要 | M08 |
| OQ-016 | 保持 `open` | 否，默认方案尚不足以覆盖消减与停练规则 | M09 |
| OQ-017 | 已标记 `proposed-default` | 是 | M10 |
| OQ-018 | 已标记 `proposed-default` | 是 | M06、M10 |
| OQ-019 | 已标记 `proposed-default` | 是，可作为 `M01` 基线收口与 `M10` 职责切分输入 | M01、M10 |
| OQ-020 | 已标记 `proposed-default` | 是，可作为 `M01` 共享页面原语收口、`M03` 页面设计收缩与 `M02` 页面承接口径对齐输入 | M01、M02、M03 |
| OQ-021 | 已标记 `proposed-default` | 是，但共享最小层只覆盖 `page/page_size/q/status/sort/order`、分页骨架与职责边界；`updated_after` / `updated_before` 当前仅可作为模块级扩展，route / callback 细节继续留在最低位文档 | M01、M02、M03 |
| OQ-022 | 已标记 `proposed-default` | 是，可作为 `M01` 共享 i18n 收口、`M02` 模块重切与 `M03` 页面命名基线输入 | M01、M02、M03 |
| OQ-023 | 继续保持 `proposed-default` | 是 | M02、M10 |
| OQ-024 | 已标记 `proposed-default` | 是，可作为 `TASK_INDEX.md` 与模块入口同步的固定治理口径；历史容器、观察蓝本和正式开窗资格已分层且已写死，当前继续通过“正式开窗名单为空”的规则阻止任何观察面被误写成正式候选 | M02、M03 |
| OQ-025 | 已标记 `proposed-default` | 是，可作为 `M03 -> M04/M06` 的最小共享输入；扩展字段继续保持未冻结，完整链路语义继续留在模块最低位压缩，不据此宣告整体 ready | M03、M04、M06 |

## 5. W10-C 首切片问题分类

> 以下分类用于本轮关系补齐，不改变上方问题表的原始状态列。

### 5.1 已确认（关系层事实）

- `RQ01` 当前仍是首切片正式 requirement 入口。
- 首切片直接模块固定为 `M03 / M04 / M06 / M07`，`M01` 只作为条件性支撑模块。
- `MT03_01 / MT03_03` 只允许作为 `M03` 观察蓝本；`ST04_01 / ST04_02 / ST06_01 / ST06_02 / ST07_03` 只允许作为后续承接对象。
- 当前正式开窗层仍为空；本轮不新增正式子任务 ID，不重新激活旧 `ST03_*` 历史容器。

### 5.2 `proposed-default`（可作为本轮关系输入）

- `OQ-001`：当前不创建业务代码目录，未来 monorepo 蓝图不是本轮实施依据。
- `OQ-002`：最小运行时 / 测试 / CI 基线只在 `W10-D` 被条件放行后才可能进入。
- `OQ-006`：Markdown 预览与导出共用同一渲染链，作为 `M03` 的输入侧约束继续保留。
- `OQ-020 / OQ-021`：共享页面原语与列表 shared contract 继续只作为最小共享输入，不外推为正式开窗依据。
- `OQ-024 / OQ-025`：历史容器、观察蓝本、正式开窗层与 `jobs.requirement_items_json` 最小共享输入继续沿用当前默认冻结口径。

### 5.3 需要用户确认（当前不得由 Codex 自行确认）

- `OQ-004 / OQ-005`：在 `W10-D-Gate` 前，用户登录、会话与权限矩阵确需用户确认；本轮用户已确认 `W10-D` 不做登录，只保留轻量 `session / user context` 边界，但未来鉴权机制与权限矩阵仍未在本轮定稿。
- `OQ-008`：匹配分析 / 评分规则是否版本化在 `W10-D-Gate` 前确需用户确认；本轮用户已确认不生成数值评分、只输出文字反馈，但评分维度、评分版本化与正式评分标准仍未在本轮定稿。
- 真实 LLM API、长期记录 / 导出、RAG / search snapshot 是否进入当前切片，在 `W10-D-Gate` 前均需用户或总控明确确认；本轮用户已确认不接真实 LLM、只做会话内临时保存、不做导出，并继续排除 RAG / search snapshot / 资产库 / 管理台，详见 5.5。

### 5.4 本轮明确排除（不进入首切片关系主链）

- `OQ-007`：上传 / 转换 / 导出异步策略对应上传导出链，本轮不进入首切片主链。
- `OQ-009 / OQ-010`：Embedding / 向量化、资产归档粒度属于 `M05` 范围，本轮排除。
- `OQ-011 / OQ-012 / OQ-018`：search snapshot 导入 / 运维、上下文包多源优先级与引用摘要规则不进入当前只依赖 JD + 简历的最小链路。
- `OQ-013 / OQ-014 / OQ-016`：主题推荐、跨场景评估框架、长期进度与停练规则不进入本轮最小反馈摘要范围。
- `OQ-015 / OQ-017`：真实面试复盘输入模型与管理台模型目录继续排除在首切片之外。

### 5.5 W10-D-Gate 已确认（用户确认结果）

> 以下 8 项是用户在 `W10-D-Gate` 中已明确确认的当前阶段结论；它们属于 confirmed 的原型实施边界，不自动把其他未来阶段 OQ 一并升级为 confirmed。

- `Q1 / confirmed`：允许在正式开窗层为空时进入原型探索，但仅限首切片最小原型骨架；该探索不代表正式实施完成。
- `Q2 / confirmed`：首切片暂不接入真实 LLM API，必须保留 LLM adapter / provider 边界，并以 mock 输出驱动原型。
- `Q3 / confirmed`：本轮不做登录；只保留 `session / user context` 的轻量边界，避免后续接登录时大改。
- `Q4 / confirmed`：简历和问答记录只在单次会话内临时保存，不做长期持久化；数据结构需可迁移到本地或服务端存储。
- `Q5 / confirmed`：本轮不生成数值评分，只输出文字反馈；反馈模型可预留 optional `score` / `dimensions` 字段，但 UI 不展示评分。
- `Q6 / confirmed`：本轮不做导出，只页面返回 Markdown 兼容文本；复制或导出能力只作为后续阶段候选。
- `Q7 / confirmed`：只允许创建 `apps/web/**` 最小原型骨架；`apps/api/**`、`infra/**` 本轮继续明确禁止。
- `Q8 / confirmed`：首切片完成标准固定为“JD + 简历 Markdown -> 3 条首轮问题 -> 第 1 题问答 -> 简版反馈”。
- 本轮继续明确排除：RAG、资产库、管理台、多轮面试、完整权限体系、完整 CI/CD。

## 6. 使用说明

- 问题确认后，应将状态更新为 `confirmed`，并同步回写受影响文档。
- 若某问题暂未正式确认，但已允许本轮按默认口径继续推进，可在总控轮次中临时标记为 `proposed-default`，并同步回写相关文档。
- 若某问题不再适用，应标记为 `superseded`，并补充替代口径。
- 总控 Codex 每轮至少要检查：
  - 高优未解问题是否变化
  - 哪些问题已足以从 `open` 转为 `proposed-default`
  - 哪些问题若被冻结，能够显著提升模块成熟度推进速度

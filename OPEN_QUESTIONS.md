# AI 模拟面试 P1 待确认问题

## 1. 文档定位

- 本文档汇总当前项目的全局待确认问题。
- 本文档用于帮助总控 Codex、模块 Codex 和评审 Codex判断：
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
| OQ-001 | 仓库结构是否固定为 monorepo（`apps/web` + `apps/api` + `infra`） | proposed-default | M01-M10 | 本轮先按 monorepo 推进，待确认后固化到设计决策 | `DESIGN_DECISIONS.md`、`TECHNICAL_STANDARDS.md` |
| OQ-002 | 首轮是否只建立最小运行时、测试和 CI 基线 | proposed-default | M01、M10 | 本轮先做最小可运行骨架与验证入口 | `PLAN_LATEST.md`、`TECHNICAL_STANDARDS.md` |
| OQ-003 | 视觉规范首轮需要沉淀到什么粒度 | proposed-default | M01 | 本轮只沉淀壳层、头部、列表原语与基础页面样式 | `TECHNICAL_STANDARDS.md` |
| OQ-004 | P1 鉴权机制采用固定 Bearer token、JWT 还是 session cookie | proposed-default | M02、M10 | 本轮先采用开发态 Bearer adapter：统一 `Authorization: Bearer <token>`、`current_user / role / team_id` 上下文，业务层不得依赖 token 内部结构 | `DESIGN_DECISIONS.md`、`TECHNICAL_STANDARDS.md` |
| OQ-005 | 团队管理员与普通成员的权限矩阵是否先只覆盖 P1 页面 | proposed-default | M02、M10 | 本轮先覆盖 P1 页面与 API，不扩展未来多租户治理场景 | `DESIGN_DECISIONS.md`、`MODULE_INDEX.md` |
| OQ-006 | Markdown 预览与导出是否必须共用同一渲染链 | proposed-default | M03 | 本轮按共用同一渲染链推进，以避免结果偏差 | `DESIGN_DECISIONS.md`、`TECHNICAL_STANDARDS.md` |
| OQ-007 | 上传、转换、导出在 P1 中哪些必须异步 | proposed-default | M03、M10 | 本轮按“上传同步入库，转换与导出异步”推进 | `TECHNICAL_STANDARDS.md` |
| OQ-008 | 匹配分析与评估规则是否需要版本化 | proposed-default | M04、M07、M10 | 本轮先按保留规则版本推进，便于解释与回放 | `TECHNICAL_STANDARDS.md`、`DESIGN_DECISIONS.md` |
| OQ-009 | Embedding 与向量化来源如何确定 | open | M05、M06 | 默认先抽象 provider 接口，并使用本地配置驱动 | `TECHNICAL_STANDARDS.md` |
| OQ-010 | 归档粒度是整份资产、片段还是题目级 | open | M05、M08 | 默认以资产级与片段级为主，题目级作为派生视图 | `MODULE_INDEX.md` |
| OQ-011 | Search snapshot 的来源只做导入还是需要抓取 | proposed-default | M06、M10 | 本轮先按 P1 只做导入、不做在线抓取推进 | `DESIGN_DECISIONS.md`、`TECHNICAL_STANDARDS.md` |
| OQ-012 | 上下文包中的 source priority 与引用摘要规则如何固定 | open | M06 | 默认优先级为 JD > 简历 > 训练证据 > 资产检索 > search snapshot | `TECHNICAL_STANDARDS.md` |
| OQ-013 | 打磨主题推荐是规则、LLM 还是混合 | open | M07 | 默认首轮采用规则推荐 | `DESIGN_DECISIONS.md`、`TECHNICAL_STANDARDS.md` |
| OQ-014 | 模拟面试、打磨模式和复盘是否共用同一评估口径 | proposed-default | M07、M08、M09 | 本轮先按共享核心评估框架、允许场景级字段扩展推进 | `TECHNICAL_STANDARDS.md` |
| OQ-015 | 真实面试输入是结构化问答、自由 transcript 还是混合 | open | M08 | 默认采用混合输入模型 | `MODULE_INDEX.md` |
| OQ-016 | 薄弱项聚合 key、消减规则和停练规则如何定稿 | open | M09 | 默认按能力节点 + 题型 + 证据来源聚合，规则后续评审定稿 | `TECHNICAL_STANDARDS.md`、`DESIGN_DECISIONS.md` |
| OQ-017 | 管理台的模型推荐来源是本地 catalog 还是在线同步 | proposed-default | M10 | 本轮先按本地 catalog / seed 推进 | `DESIGN_DECISIONS.md`、`TECHNICAL_STANDARDS.md` |
| OQ-018 | 管理台是否负责 search snapshot 导入与运维 | proposed-default | M06、M10 | 本轮先按负责导入与运维入口、不承担抓取本身推进 | `TECHNICAL_STANDARDS.md`、`MODULE_INDEX.md` |
| OQ-019 | 根目录统一脚本与最小 CI 校验矩阵应冻结到什么粒度，才算满足平台基线的下游输入要求 | proposed-default | M01、M10 | 本轮先采用方案 B：冻结统一脚本命名（`dev:web` / `dev:api` / `test:web` / `test:api`）、最小存活检查（`GET /api/v1/health` -> `200 {"status":"ok"}`）与最小验证入口类型（API=`pytest`、Web=`vitest`），CI 只冻结 API/Web 两类最小校验 lane，不在当前轮冻结完整流水线矩阵 | `TECHNICAL_STANDARDS.md`、`DESIGN_DECISIONS.md`、`DOCUMENT_PROGRESS.md` |
| OQ-020 | 共享页面原语（`PageHeader` / Dashboard 摘要区）应冻结到什么最小接口边界，才能支撑后续页面复用 | proposed-default | M01、M02、M03 | 本轮先采用方案 B：冻结最小共享页面原语边界；`PageHeader` 只承载标题/说明/主次动作，摘要区独立承载 `status_badge` / `updated_at` / `summary_items` 与最小状态表达，不扩张为完整 props catalog | `TECHNICAL_STANDARDS.md`、`DESIGN_DECISIONS.md`、`DOCUMENT_PROGRESS.md` |
| OQ-021 | 列表查询状态、分页交互与 URL / callback 的映射规则应如何统一 | proposed-default | M01、M02、M03、M04-M10 | 本轮默认采用方案 B：冻结共享 `ListQueryState`、统一 query / pagination 最小映射与分页响应骨架，页面容器负责 state / URL / request adapter，共享列表原语不直接耦合 router；暂不冻结完整 props / callback catalog 与高级筛选序列化细节 | `TECHNICAL_STANDARDS.md`、`DESIGN_DECISIONS.md`、`DOCUMENT_PROGRESS.md` |
| OQ-022 | locale fallback、切换策略与消息命名空间应冻结到什么程度，才能作为共享 Web 契约下发 | proposed-default | M01、M02、M03、M04-M10 | 本轮先采用方案 B：统一 `apps/web/src/i18n/**` + `getMessages(locale)` 入口，首轮 locale seed 固定为 `zh-CN` / `en-US`、默认 locale=`zh-CN`；切换由 layout / App Shell 统一解析 active locale；fallback 固定为“请求 locale -> `zh-CN` -> 记录缺失 key”，禁止组件硬编码兜底；namespace 只冻结“共享壳层一层、业务页面一层”的最小边界，不扩张为完整 i18n 架构 | `TECHNICAL_STANDARDS.md`、`DESIGN_DECISIONS.md`、`DOCUMENT_PROGRESS.md` |
| OQ-023 | `/(dashboard)/admin/members` 与 `/api/v1/admin/members` 的完整实现应继续由 M02 承接，还是由后续治理模块承接 | proposed-default | M02、M10 | 本轮先采用方案 B：`M02` 只负责身份解析、授权规则、权限矩阵与最小鉴权契约，完整成员管理页面 / API 由后续治理模块承接 | `DESIGN_DECISIONS.md`、`MODULE_INDEX.md` |
| OQ-024 | 计划重构后，旧 `ST02_* / ST03_*` 子任务目录是否应退役为历史容器，并按新的微任务蓝本重建正式入口 | proposed-default | M02、M03 | 本轮先按默认口径推进：旧目录只保留为历史容器，禁止在 `TASK_INDEX.md` 中继续作为直开入口；后续正式入口以 `MT02_* / MT03_*` 微任务蓝本和总控映射策略为准，再决定是否复用旧目录编号 | `TASK_INDEX.md`、`DOCUMENT_PROGRESS.md`、`MODULE_INDEX.md` |
| OQ-025 | `jobs.requirement_items_json` 的最小 item 结构、空值语义、排序规则与写入责任应冻结到什么程度，才能作为 M04 / M06 的稳定输入 | open | M03、M04、M06 | 当前建议先在模块 / 总控层冻结最小可消费 item schema、空值语义、排序规则与写入责任；在冻结前，下游模块不得自行扩张 JSON 契约 | `TECHNICAL_STANDARDS.md`、`DESIGN_DECISIONS.md`、`DOCUMENT_PROGRESS.md` |

## 3. 本轮高优问题处理判断

- 本轮（`R-Refactor-01` / 计划重构执行轮）必须优先处理的问题：
  - `OQ-019` 根目录统一脚本与最小 CI 校验矩阵的冻结粒度
  - `OQ-020` 共享页面原语最小接口边界
  - `OQ-021` 列表查询状态、分页交互与 URL / callback 映射
  - `OQ-022` locale fallback、切换策略与消息命名空间
  - `OQ-023` admin 成员管理完整实现归属
- 本轮检查结论：
  - `OQ-019` 已形成 `proposed-default` 默认冻结候选，可作为 `M01/M10` 继续推进输入，但暂不升级为 `confirmed`
  - `OQ-020` 已形成 `proposed-default` 默认冻结候选，可作为 `M01` 共享页面原语收口、`M03` 页面设计收缩与 `M02` 页面承接口径对齐输入
  - `OQ-021` 已形成 `proposed-default` 默认冻结候选，可作为 `M01-M03` 继续推进输入，但暂不升级为 `confirmed`
  - `OQ-022` 已形成 `proposed-default` 默认冻结候选，可作为 `M01` i18n 共享契约收口与 `M02` 模块重切输入，但暂不升级为 `confirmed`
  - `OQ-023` 继续保持 `proposed-default`，直接作为 `M02/M10` 职责重切输入
  - `OQ-024` 已由 `MQ-207` + `MQ-306` 上升为新的全局问题，并已足够登记为 `proposed-default`：旧 `ST02_* / ST03_*` 目录只保留为历史容器、不得继续直开
  - `OQ-025` 已由 `MQ-307` 上升为新的全局输入契约问题，但当前仍不足以冻结为 `proposed-default`，下一轮应优先继续收口

| 优先级 | OQ ID | 当前状态 | 当前影响模块 | 本轮处理判断 |
| --- | --- | --- | --- | --- |
| P0 | OQ-001 | proposed-default | M01-M10 | 已按默认 monorepo 冻结，可作为本轮 `M01-M03` 输入 |
| P0 | OQ-004 | proposed-default | M02、M10 | 已按固定 Bearer token 冻结，可作为本轮 `M02` 输入 |
| P0 | OQ-006、OQ-007 | proposed-default | M03、M10 | 已按共享渲染链与“上传同步/转换导出异步”冻结，可作为本轮 `M03` 输入 |
| P0 | OQ-019 | proposed-default | M01、M10 | 已形成入口语义级默认冻结方案；可作为 `M01` 平台基线与 `M10` 治理边界切分输入，但暂不扩张为完整流水线定稿 |
| P0 | OQ-021 | proposed-default | M01、M02、M03、M04-M10 | 已形成最小共享契约候选：统一 `ListQueryState`、query 映射、分页骨架与页面容器 adapter 职责；可作为本轮 `M01-M03` 输入，但暂不扩张为完整实现级交互定稿 |
| P0 | OQ-024 | proposed-default | M02、M03 | 已形成默认冻结候选：旧 `ST02_* / ST03_*` 目录只保留为历史容器、禁止直开；下一轮正式入口以模块微任务蓝本和总控映射策略为准 |
| P0 | OQ-025 | open | M03、M04、M06 | 新升级的输入契约问题；在冻结最小 item schema、空值语义、排序规则与写入责任前，不得把 `jobs.requirement_items_json` 作为稳定下游输入 |
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
| OQ-001 | 已标记 `proposed-default` | 是 | M01-M03 |
| OQ-002 | 已标记 `proposed-default` | 是 | M01、M10 |
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
| OQ-021 | 已标记 `proposed-default` | 是，但仅覆盖共享 state model、query 映射、分页骨架与职责边界；不覆盖完整实现级交互细节 | M01、M02、M03 |
| OQ-022 | 已标记 `proposed-default` | 是，可作为 `M01` 共享 i18n 收口、`M02` 模块重切与 `M03` 页面命名基线输入 | M01、M02、M03 |
| OQ-023 | 继续保持 `proposed-default` | 是 | M02、M10 |
| OQ-024 | 已标记 `proposed-default` | 是，可作为 `TASK_INDEX.md` 与模块入口同步的默认口径 | M02、M03 |
| OQ-025 | 保持 `open` | 否，当前尚不足以冻结 `jobs.requirement_items_json` 的最小 item 结构与写入责任 | M03、M04、M06 |

## 5. 使用说明

- 问题确认后，应将状态更新为 `confirmed`，并同步回写受影响文档。
- 若某问题暂未正式确认，但已允许本轮按默认口径继续推进，可在总控轮次中临时标记为 `proposed-default`，并同步回写相关文档。
- 若某问题不再适用，应标记为 `superseded`，并补充替代口径。
- 总控 Codex 每轮至少要检查：
  - 高优未解问题是否变化
  - 哪些问题已足以从 `open` 转为 `proposed-default`
  - 哪些问题若被冻结，能够显著提升模块成熟度推进速度

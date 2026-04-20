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
| OQ-019 | 根目录统一脚本与最小 CI 校验矩阵应冻结到什么粒度，才算满足平台基线的下游输入要求 | open | M01、M10 | 默认先冻结统一脚本命名、最小存活检查与最小验证入口类型，不在当前轮冻结完整流水线矩阵 | `TECHNICAL_STANDARDS.md`、`DESIGN_DECISIONS.md` |
| OQ-020 | 共享页面原语（`PageHeader` / Dashboard 摘要区）应冻结到什么最小接口边界，才能支撑后续页面复用 | open | M01、M02、M03 | 默认先冻结最小对象模型、交互状态和摘要区职责，不扩张为完整设计系统 props catalog | `TECHNICAL_STANDARDS.md`、`DESIGN_DECISIONS.md` |
| OQ-021 | 列表查询状态、分页交互与 URL / callback 的映射规则应如何统一 | open | M01、M02、M03、M04-M10 | 默认先冻结“筛选 / 排序 / 分页必须共用同一状态模型”，但精确映射规则仍待继续收口 | `TECHNICAL_STANDARDS.md`、`DESIGN_DECISIONS.md` |
| OQ-022 | locale fallback、切换策略与消息命名空间应冻结到什么程度，才能作为共享 Web 契约下发 | open | M01、M02、M03、M04-M10 | 默认先冻结集中取词入口与 locale seed，完整 fallback / namespace 规则仍待继续收口 | `TECHNICAL_STANDARDS.md`、`DESIGN_DECISIONS.md` |
| OQ-023 | `/(dashboard)/admin/members` 与 `/api/v1/admin/members` 的完整实现应继续由 M02 承接，还是由后续治理模块承接 | proposed-default | M02、M10 | 本轮先采用方案 B：`M02` 只负责身份解析、授权规则、权限矩阵与最小鉴权契约，完整成员管理页面 / API 由后续治理模块承接 | `DESIGN_DECISIONS.md`、`MODULE_INDEX.md` |

## 3. 本轮高优问题处理判断

- 本轮新增问题：
  - `OQ-019` 根目录统一脚本与最小 CI 校验矩阵的冻结粒度
  - `OQ-020` 共享页面原语最小接口边界
  - `OQ-021` 列表查询状态、分页交互与 URL / callback 映射
  - `OQ-022` locale fallback、切换策略与消息命名空间
  - `OQ-023` admin 成员管理完整实现归属
- 本轮高优问题不再一律视为“未解即阻塞”，而是区分为“可按默认方案冻结”和“仍需保持 open”。

| 优先级 | OQ ID | 当前状态 | 当前影响模块 | 本轮处理判断 |
| --- | --- | --- | --- | --- |
| P0 | OQ-001 | proposed-default | M01-M10 | 已按默认 monorepo 冻结，可作为本轮 `M01-M03` 输入 |
| P0 | OQ-004 | proposed-default | M02、M10 | 已按固定 Bearer token 冻结，可作为本轮 `M02` 输入 |
| P0 | OQ-006、OQ-007 | proposed-default | M03、M10 | 已按共享渲染链与“上传同步/转换导出异步”冻结，可作为本轮 `M03` 输入 |
| P0 | OQ-019 | open | M01、M10 | 已上升为全局问题；暂不冻结，当前默认建议不足以支撑 `M01` 正式升入 `L5` |
| P0 | OQ-021 | open | M01、M02、M03、M04-M10 | 已上升为全局问题；暂不冻结，`/members` 列表与后续页面列表仍缺统一映射规则 |
| P1 | OQ-020 | open | M01、M02、M03 | 已上升为全局问题；暂不冻结，页面头部与摘要区最小接口仍需再收口 |
| P1 | OQ-022 | open | M01、M02、M03、M04-M10 | 已上升为全局问题；暂不冻结，当前默认只覆盖集中入口与 seed，尚未覆盖 fallback / namespace 规则 |
| P1 | OQ-023 | proposed-default | M02、M10 | 已按方案 B 记为跨模块默认口径，后续只待总控进一步确认或收敛为设计决策 |
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
| OQ-019 | 保持 `open` | 否，默认方案尚不足以覆盖最小脚本与 CI 矩阵的验收粒度 | M01、M10 |
| OQ-020 | 保持 `open` | 否，默认方案尚不足以覆盖共享页面原语的最小接口边界 | M01、M02、M03 |
| OQ-021 | 保持 `open` | 否，默认方案尚不足以覆盖列表查询状态与 URL / callback 的精确映射 | M01、M02、M03、M04-M10 |
| OQ-022 | 保持 `open` | 否，默认方案尚不足以覆盖 locale fallback / namespace 的共享规则 | M01、M02、M03、M04-M10 |
| OQ-023 | 已新增为 `proposed-default` | 是 | M02、M10 |

## 5. 使用说明

- 问题确认后，应将状态更新为 `confirmed`，并同步回写受影响文档。
- 若某问题暂未正式确认，但已允许本轮按默认口径继续推进，可在总控轮次中临时标记为 `proposed-default`，并同步回写相关文档。
- 若某问题不再适用，应标记为 `superseded`，并补充替代口径。
- 总控 Codex 每轮至少要检查：
  - 高优未解问题是否变化
  - 哪些问题已足以从 `open` 转为 `proposed-default`
  - 哪些问题若被冻结，能够显著提升模块成熟度推进速度

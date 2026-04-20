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
| OQ-001 | 仓库结构是否固定为 monorepo（`apps/web` + `apps/api` + `infra`） | open | M01-M10 | 默认按 monorepo 推进，待确认后固化到设计决策 | `DESIGN_DECISIONS.md`、`TECHNICAL_STANDARDS.md` |
| OQ-002 | 首轮是否只建立最小运行时、测试和 CI 基线 | open | M01、M10 | 默认先做最小可运行骨架与验证入口 | `PLAN_LATEST.md`、`TECHNICAL_STANDARDS.md` |
| OQ-003 | 视觉规范首轮需要沉淀到什么粒度 | open | M01 | 默认只沉淀壳层、头部、列表原语与基础页面样式 | `TECHNICAL_STANDARDS.md` |
| OQ-004 | P1 鉴权机制采用固定 Bearer token、JWT 还是 session cookie | open | M02、M10 | 默认先用固定 Bearer token 作为 P1 开发口径 | `DESIGN_DECISIONS.md`、`TECHNICAL_STANDARDS.md` |
| OQ-005 | 团队管理员与普通成员的权限矩阵是否先只覆盖 P1 页面 | open | M02、M10 | 默认先覆盖 P1 页面与 API，不扩展未来多租户治理场景 | `DESIGN_DECISIONS.md`、`MODULE_INDEX.md` |
| OQ-006 | Markdown 预览与导出是否必须共用同一渲染链 | open | M03 | 默认共用同一渲染链以避免结果偏差 | `DESIGN_DECISIONS.md`、`TECHNICAL_STANDARDS.md` |
| OQ-007 | 上传、转换、导出在 P1 中哪些必须异步 | open | M03、M10 | 默认上传可同步入库，转换与导出走异步任务 | `TECHNICAL_STANDARDS.md` |
| OQ-008 | 匹配分析与评估规则是否需要版本化 | open | M04、M07、M10 | 默认需要保留规则版本，便于解释与回放 | `TECHNICAL_STANDARDS.md`、`DESIGN_DECISIONS.md` |
| OQ-009 | Embedding 与向量化来源如何确定 | open | M05、M06 | 默认先抽象 provider 接口，并使用本地配置驱动 | `TECHNICAL_STANDARDS.md` |
| OQ-010 | 归档粒度是整份资产、片段还是题目级 | open | M05、M08 | 默认以资产级与片段级为主，题目级作为派生视图 | `MODULE_INDEX.md` |
| OQ-011 | Search snapshot 的来源只做导入还是需要抓取 | open | M06、M10 | 默认 P1 只做导入，不做在线抓取 | `DESIGN_DECISIONS.md`、`TECHNICAL_STANDARDS.md` |
| OQ-012 | 上下文包中的 source priority 与引用摘要规则如何固定 | open | M06 | 默认优先级为 JD > 简历 > 训练证据 > 资产检索 > search snapshot | `TECHNICAL_STANDARDS.md` |
| OQ-013 | 打磨主题推荐是规则、LLM 还是混合 | open | M07 | 默认首轮采用规则推荐 | `DESIGN_DECISIONS.md`、`TECHNICAL_STANDARDS.md` |
| OQ-014 | 模拟面试、打磨模式和复盘是否共用同一评估口径 | open | M07、M08、M09 | 默认共享核心评估框架，并允许场景级字段扩展 | `TECHNICAL_STANDARDS.md` |
| OQ-015 | 真实面试输入是结构化问答、自由 transcript 还是混合 | open | M08 | 默认采用混合输入模型 | `MODULE_INDEX.md` |
| OQ-016 | 薄弱项聚合 key、消减规则和停练规则如何定稿 | open | M09 | 默认按能力节点 + 题型 + 证据来源聚合，规则后续评审定稿 | `TECHNICAL_STANDARDS.md`、`DESIGN_DECISIONS.md` |
| OQ-017 | 管理台的模型推荐来源是本地 catalog 还是在线同步 | open | M10 | 默认首轮采用本地 catalog / seed | `DESIGN_DECISIONS.md`、`TECHNICAL_STANDARDS.md` |
| OQ-018 | 管理台是否负责 search snapshot 导入与运维 | open | M06、M10 | 默认负责导入与运维入口，不承担抓取本身 | `TECHNICAL_STANDARDS.md`、`MODULE_INDEX.md` |

## 3. 本轮高优未解问题

- 本轮新增问题：无
- 本轮仍未解决且直接阻塞模块成熟度提升的问题如下：

| 优先级 | OQ ID | 当前阻塞模块 | 原因 | 本轮处理要求 |
| --- | --- | --- | --- | --- |
| P0 | OQ-001 | M01-M10 | monorepo 是否冻结会影响目录规划、实施路径和后续子任务目标区域 | 至少冻结默认口径，再继续细化 `M01` 设计包 |
| P0 | OQ-004 | M02、M10 | 鉴权方式会影响 API、会话、测试夹具和权限矩阵 | 在 `M02` 设计收敛前优先确认或冻结默认口径 |
| P0 | OQ-006、OQ-007 | M03、M10 | 渲染链一致性和异步边界会同时影响文档处理、导出和后台治理 | 在 `M03` API / logic 设计前先收敛 |
| P1 | OQ-008 | M04、M07 | 评分/versioning 口径未定会阻塞分析结果可追溯性与复盘复现 | 在启动 `M04` 深化设计前先定默认口径 |
| P1 | OQ-011、OQ-012、OQ-018 | M06、M10 | snapshot 来源、source priority 和管理台职责边界未定 | 在启动 `M06` 深化设计前先分清 ownership |
| P1 | OQ-014、OQ-016 | M07、M08、M09 | 共享评估口径与薄弱项生命周期规则未定 | 在启动 `M07-M09` 深化设计前先冻结跨模块契约 |
| P1 | OQ-017 | M10 | 模型目录来源会直接改变管理台范围与配置方式 | 在 `M10` 设计前确认“本地 catalog / seed”是否继续作为默认口径 |

## 4. 默认方案冻结建议

> 本节用于帮助总控 Codex 在“信息仍不充分”时决定：哪些问题可以先按默认方案冻结，从而继续推进模块文档。

| OQ ID | 建议动作 | 默认方案是否足以继续推进 | 若冻结后优先推进模块 |
| --- | --- | --- | --- |
| OQ-001 | 建议先冻结 | 是 | M01-M03 |
| OQ-002 | 建议先冻结 | 是 | M01、M10 |
| OQ-003 | 建议先冻结 | 是 | M01 |
| OQ-004 | 建议先冻结 | 是，但需在设计决策中显式记录 | M02、M10 |
| OQ-005 | 建议先冻结 | 是 | M02 |
| OQ-006 | 建议先冻结 | 是 | M03 |
| OQ-007 | 建议先冻结 | 是 | M03 |
| OQ-008 | 建议先冻结 | 是 | M04、M07 |
| OQ-009 | 建议先冻结 | 是 | M05 |
| OQ-010 | 建议先冻结 | 是 | M05、M08 |
| OQ-011 | 建议先冻结 | 是 | M06、M10 |
| OQ-012 | 建议先冻结 | 是 | M06 |
| OQ-013 | 建议先冻结 | 是 | M07 |
| OQ-014 | 建议先冻结 | 是，但需跨模块同步 | M07、M08、M09 |
| OQ-015 | 建议先冻结 | 是 | M08 |
| OQ-016 | 建议先冻结 | 是，但需后续评审收敛 | M09 |
| OQ-017 | 建议先冻结 | 是 | M10 |
| OQ-018 | 建议先冻结 | 是 | M06、M10 |

## 5. 使用说明

- 问题确认后，应将状态更新为 `confirmed`，并同步回写受影响文档。
- 若某问题暂未正式确认，但已允许本轮按默认口径继续推进，可在总控轮次中临时标记为 `proposed-default`，并同步回写相关文档。
- 若某问题不再适用，应标记为 `superseded`，并补充替代口径。
- 总控 Codex 每轮至少要检查：
  - 高优未解问题是否变化
  - 哪些问题已足以从 `open` 转为 `proposed-default`
  - 哪些问题若被冻结，能够显著提升模块成熟度推进速度
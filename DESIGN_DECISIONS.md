# AI 模拟面试 P1 设计决策

## 1. 文档定位

- 本文档记录全局级设计决策、当前有效口径和后续回写动作。
- 决策状态使用：`proposed`、`confirmed`、`superseded`、`rejected`、`needs-review`。
- W13-Cleanup 后，已被用户 confirmed 的 `FC-01~FC-19` 结果应优先于旧 `proposed-default`、历史 OQ/MQ 和 W10 原型口径。

## 2. 决策表

| 决策 ID | 决策 | 状态 | 当前口径 | 影响范围 | 后续动作 |
| --- | --- | --- | --- | --- | --- |
| DD-001 | 文档体系采用 `global -> module -> subtask` 分层 | confirmed | 全局文档负责约束与导航，模块文档承接设计，子任务文档承接实施准备。 | 全局 | 所有新增文档继续遵循该分层。 |
| DD-002 | 原始设计稿与原始实现计划保留为上游源文档 | confirmed | `docs/superpowers/specs/...` 与早期实现计划不再承担当轮事实源；当前事实源由 W13 四份计划文档承担。 | 全局 | 后续回写进入根目录全局文档、W13 事实源文档与 `docs/modules/`。 |
| DD-003 | 单次实施单位限定为一个子任务 | confirmed | 只有单个 `SUBTASK_IMPLEMENTATION.md` 达到可实施后，才进入代码执行。 | 全局实施流程 | 在任务索引与成熟度文档中持续约束。 |
| DD-004 | 目标产品代码结构采用 `apps/web + packages/shared + apps/api` | confirmed | `FC-01` 已确认目标结构；但本仓库当前仍是设计文档、治理状态、`tools/doc_governor/` 与 `tests/doc_governor/` 承载仓库，W13-F 前不得直接创建目录或实施服务。 | 全局、M01-M10 | 实现目录创建、后端服务和部署仍需 `TASK_INDEX.md` 写入明确任务 ID 与正式开窗资格。 |
| DD-005 | 后端采用 FastAPI；完整技术栈仍需实施包阶段复核 | needs-review | `FC-01` 已确认后端采用 FastAPI；Web framework、前端工程细节和共享包构建方式不得从旧实现计划或 W10 原型直接推导为 confirmed。 | M01-M10 | 后续实现包评估时再确认 Web framework、包管理、构建与测试矩阵。 |
| DD-006 | 文档默认使用中文 | confirmed | 文档主体、界面文案和说明均使用中文，技术标识保持英文。 | 全局 | 受 [AGENTS.md](AGENTS.md) 与 [docs/project-language-rules.md](docs/project-language-rules.md) 约束。 |
| DD-007 | Markdown 预览与导出是否共用同一渲染链仍需复核 | needs-review | `FC-12` 已确认复制 / Markdown 下载、导出范围和异步策略；但 Markdown 预览、下载、复制与未来 PDF 是否共用同一渲染链仍不直接升为 confirmed。 | M03、M08 | 由后续导出实现包在不扩展一期范围的前提下复核。 |
| DD-008 | Search snapshot 只导入不抓取 | confirmed | `FC-18` 已确认 snapshot 只导入不抓取；管理台负责导入与运维入口，在线同步不进入当前一期默认主链。 | M06、M10 | 后续 M10 / 运维文档只按导入与运维入口承接。 |
| DD-009 | 匹配分析与评估采用规则版本化 + 共享核心评估框架 + 规则推荐优先 | confirmed | `FC-17` 已确认该口径。 | M04、M07、M08、M09、M10 | LLM 推荐或混合推荐不得默认替代。 |
| DD-010 | 模型推荐来源采用本地 catalog / seed | confirmed | `FC-18` 已确认模型 catalog / seed 采用本地来源；管理台负责导入与运维入口。 | M10 | 在线模型同步继续后置；M10 不得把完整配置中心写成一期主链。 |
| DD-011 | 平台基线仅作为工程输入，不等于当前可实施目录 | confirmed | `FC-01` 已确认文档先行、目标结构、API contract、部署与日志边界；旧最小脚本 / health check 口径只作为工程基线输入。 | M01、M10 | 正式脚本、health check 和 CI lane 仍需 implementation packet 细化后再实施。 |
| DD-012 | Web i18n 维持最小共享层 | confirmed | `FC-15` 已确认 `getMessages(locale)` 与最小 namespace，细节留模块 / 实现层。 | M01、M02、M03、M04-M10 | 不得扩展为完整 i18n 架构。 |
| DD-013 | 共享页面原语维持最小共享层 | confirmed | `FC-15` 已确认 `PageHeader` / 摘要区及最小状态表达，细节留模块 / 实现层。 | M01、M02、M03 | 不得上推为完整 props catalog 或设计系统。 |
| DD-014 | 列表查询状态采用最小共享查询层 | confirmed | `FC-15` 已确认 `page/page_size/q/status/sort/order` 与统一分页骨架；模块扩展键仍留模块层。 | M01、M02、M03、M04-M10 | 各模块仅可在该最小层上扩展，不得把扩展键反写成全局前提。 |
| DD-015 | W10 “最小功能切片优先”首切片 | superseded | W10 首切片固定为“岗位 JD 手工输入 + 简历 Markdown 粘贴/编辑 -> 生成首轮模拟面试问题 -> 记录 1 轮问答 -> 输出简版反馈摘要”；该口径已被 `DD-018` 取代。 | W10 历史原型 | 保留为历史记录，不再作为当前一期 MVP 范围。 |
| DD-016 | W10 首切片关系层 `RQ01 -> M03 / M04 / M06 / M07 (+ 条件性 M01)` | superseded | 该关系层只解释 W10 原型探索如何落到最小 mock 原型，不再作为一期工作台 MVP 的模块关系依据。 | W10 历史原型 | 后续以 W13 事实源重新建模。 |
| DD-017 | `W10-D` 首切片最小 Web 原型探索闸门 | superseded | W10 `apps/web/**` mock 原型只作为参考证据；mock LLM、无登录、会话内临时数据、无数值评分、不导出等边界不得继续前推为当前一期 MVP。 | `apps/web/**` 原型、W10 历史记录 | 后续若复用交互或组件，必须先经 W13 事实源重新裁剪。 |
| DD-018 | 一期 MVP 重新定义为工作台级 MVP | confirmed | 一期必须包含服务端历史 / 复盘记录、真实 LLM、完整登录 / 权限、简历与面试记录服务端保存、完整 `0-100` 多维评分、复制 / Markdown 下载、RAG / 知识库、多轮高阶面试和历史模拟记录列表入口。 | 全局产品范围、M02-M10 | 唯一事实源见 `docs/superpowers/plans/2026-04-25-workbench-mvp-scope.md`。 |
| DD-019 | W10 `apps/web/**` 原型降级为参考证据并暂停代码开发 | confirmed | `apps/web/**` 原型不作为正式一期 MVP 开发起点；当前暂停代码开发，直到 W13 事实源和正式任务开窗完成。 | 当前推进路径、`apps/web/**` | 不得继续扩展 `apps/web/**`、创建 `apps/api/**`、接真实 LLM、做数据库、登录、评分或后端实现。 |
| DD-020 | W13-B 初稿 IA 口径 | superseded | 该条保留为 W13-B 初稿历史记录；其中“资产库、训练中心、管理台等仍作为后续占位”的旧口径已被 `FC-13`、`FC-14`、`FC-18` 与当前唯一事实源取代。 | W13-B、IA | 当前 IA 事实源为 `docs/superpowers/plans/2026-04-25-workbench-mvp-ia-user-journey.md`。 |
| DD-021 | 一期 MVP 包含 RAG / 知识库能力 | confirmed | RAG / 知识库进入一期 MVP；支持用户私有上传 + 管理员公共知识库，团队共享后置，混合检索，失败时降级继续并标注证据缺口。 | M05、M06、M08、M10 | 唯一事实源见对象模型文档与评分 / 复盘 / 导出 / DoD 文档。 |
| DD-022 | 一期 MVP 包含多轮高阶面试能力 | confirmed | 多轮高阶面试进入一期 MVP；固定 3 轮不再是总规则，只能作为压力面题组策略候选。 | M06、M07、M08、M09 | 唯一事实源见 IA、对象模型和评分 / 复盘 / 导出 / DoD 文档。 |
| DD-023 | 模拟面试模块默认入口为历史模拟记录列表 | confirmed | 发起模拟面试从记录列表进入，面试完成后回写历史记录 / 复盘。 | M02、M06、M08 | W13-C 补记录列表查询、权限过滤、状态机和归档 / 删除边界。 |
| DD-024 | 一期模拟面试可从岗位详情或模拟面试模块发起 | confirmed | 发起时选择岗位、简历、模式；系统整理参考材料包并生成面试策略与首题。 | M03、M04、M05、M06、M07、M08 | 缺失输入和失败处理继续由对象模型事实源承接。 |
| DD-025 | 一期至少包含打磨模式和压力面模式 | confirmed | 打磨模式由 `ProgressTree` 驱动，用户决定继续或结束；压力面由 `InterviewQuestionSet` 驱动，题目完成后结束。`FC-06D` 完整语义为：压力面模式支持按岗位自动生成默认题型组合，并允许用户手动调整；打磨模式支持用户自定义主题 / 题型，并可结合岗位与薄弱项自动推荐，但不强制固定题组。 | M06、M07、M08、M09 | 评分 / 复盘 / DoD 按两种模式分别承接。 |
| DD-026 | 一期复盘来源包括真实面试材料和模拟面试结果 | confirmed | `FC-11D` 完整语义为：真实面试输入支持用户上传逐字稿原文，不要求用户先按题目拆分；系统由大模型自动识别问题与回答边界，再输出逐题拆解复盘；若切分置信度不足，提示用户校对。模拟面试复盘展示整场判断、多维评分、岗位匹配度、通过概率、逐题点评和改进建议。 | M08、M09、M10 | 唯一事实源见评分 / 复盘 / 导出 / DoD 文档。 |
| DD-027 | 一期支持整份和单题归档到资产库 | confirmed | 归档时选择资产类型；类型带 schema 时动态渲染字段表单；资产库采用归档动作 + 最小资产列表 / 详情 + schema 子集动态字段。 | M05、M08、M10 | 唯一事实源见对象模型文档。 |
| DD-028 | 薄弱项与训练抽屉进入一期训练闭环设计 | confirmed | `WeaknessItem` 是可训练、可累计、可消减、可停练的中粒度训练主题；薄弱项按岗位聚合、按主题归并、保留所有证据；状态包括 `active / low_priority / dismissed / resolved`；训练抽屉是统一训练入口。 | M04、M06、M07、M08、M09 | 唯一事实源见对象模型文档与评分 / 复盘 / 导出 / DoD 文档。 |
| DD-029 | 多轮面试按打磨模式与压力面模式拆分，不采用固定 3 轮作为总规则 | confirmed | 此前 W13-C “多轮范围 = A：固定 3 轮”的推荐不再作为 confirmed 或默认总规则。 | M06、M07、M08、M09、W13-C、W13-D | 固定 3 轮最多只作为压力面题组策略候选。 |
| DD-030 | W13-D 评分、复盘、导出与 MVP DoD 已由用户 confirmed 为当前事实源，但不放行实现 | confirmed | `FC-07`、`FC-08`、`FC-11`、`FC-12`、`FC-13`、`FC-14` 已确认评分维度、总分关系、真实面试复盘、Markdown 导出、训练闭环、资产库最小范围与五层 DoD。 | 全局、M03、M05、M06、M07、M08、M09、M10、W13-F | `docs/superpowers/plans/2026-04-25-workbench-mvp-scoring-review-export-dod.md` 是评分 / 复盘 / 导出 / DoD 唯一事实源；该确认不代表可以创建业务代码目录或 implementation packet。 |
| DD-031 | W13 `FC-01~FC-19` confirmed 结果已成为当前 OQ / DD 清理基准 | confirmed | `OPEN_QUESTIONS.md` 已回压为 `confirmed / historical`，不再存在 active `open / proposed-default` 项；四份 W13 计划文档分别作为范围、IA、对象模型和评分复盘导出的唯一事实源。 | 全局、W13-B、W13-C、W13-D、W13-F | W13-F 只负责 Basic Memory / Superpowers 写回与实施包评估，不得重新打开已 confirmed 的 OQ。 |

## 3. 当前唯一事实源索引

| 内容类别 | 唯一事实源 |
| --- | --- |
| 一期 MVP 范围 | `docs/superpowers/plans/2026-04-25-workbench-mvp-scope.md` |
| IA / 用户旅程 | `docs/superpowers/plans/2026-04-25-workbench-mvp-ia-user-journey.md` |
| 对象模型 / RAG / 多轮 / 后端边界 | `docs/superpowers/plans/2026-04-25-workbench-mvp-object-model-rag-multiround-backend.md` |
| 评分 / 复盘 / 导出 / DoD | `docs/superpowers/plans/2026-04-25-workbench-mvp-scoring-review-export-dod.md` |
| OQ confirmed / historical 归并索引 | `OPEN_QUESTIONS.md` |
| 历史执行记录 | `EXECUTION_LOG.md` |

## 4. 使用说明

- 新增全局级关键口径时，应先补充本文档，再更新相关事实源文档、模块文档或执行计划。
- 已标记为 `superseded` 的 DD 不得继续作为当前一期 MVP 输入；只能作为历史解释。
- `needs-review` 表示已有部分 confirmed 内容，但仍不能直接进入实现。
- 决策状态变化后，应同步回写 `OPEN_QUESTIONS.md`、`PLAN_LATEST.md` 和必要的进展文档。

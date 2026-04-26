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
| DD-004 | 目标产品代码结构采用 `apps/web + packages/shared + apps/api` | confirmed | `FC-01` 已确认目标结构；但本仓库当前仍是设计文档、治理状态、`tools/doc_governor/` 与 `tests/doc_governor/` 承载仓库，正式任务与状态层开窗前不得直接创建目录或实施服务。 | 全局、M01-M10 | 实现目录创建、后端服务和部署仍需 `TASK_INDEX.md` 写入明确任务 ID 与正式开窗资格。 |
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
| DD-031 | W13 `FC-01~FC-19` confirmed 结果已成为当前 OQ / DD 清理基准 | confirmed | `OPEN_QUESTIONS.md` 已将 W13 产品事实回压为 `confirmed / historical`；W13-E 新增的 `OQ-090~OQ-092` 仅处理任务治理确认，不改变四份 W13 计划文档作为范围、IA、对象模型和评分复盘导出的唯一事实源。 | 全局、W13-B、W13-C、W13-D、W13-F、W13-E | W13-F 已完成阶段写回；W13-E 增量如需沉淀由后续收口窗口负责 Basic Memory / Superpowers 写回，不得重新打开已 confirmed 的产品范围 OQ。 |
| DD-032 | W13-E Task Remap 只形成候选任务治理草案，不放行实现 | confirmed | `docs/superpowers/plans/2026-04-25-workbench-mvp-task-remap.md` 已将 W13 工作台级 MVP 映射为候选任务树、确认卡、模块映射和状态层后续改造方案；W13-E 本身不修改 `DOC_STATE.yaml`，不生成 implementation packet，不创建业务代码目录。 | 全局、M01-M10、W13-E | 已由 `DD-033` 吸收用户对 W13-E 推荐组合的确认；Preview YAML 确认结果见 `DD-034`，正式状态层写入仍需后续 State Write 确认。 |
| 状态层 Preview YAML | `docs/superpowers/plans/2026-04-25-workbench-mvp-doc-state-preview.yaml` |
| DD-033 | W13-E2 吸收 W13-E 用户确认组合并完成状态层 dry-run，不放行实现 | confirmed | 用户已确认 `WT13-xx` 作为候选任务域命名、旧 `STxx_*` 后续映射为 `superseded`、暂不直接写 `DOC_STATE.yaml` 而先做 W13-E2 dry-run。W13-E2 结论是当前 `doc_governor` 状态层不直接接受 `WT13-xx` 作为 `subtasks` key，因此下一步推荐先创建 preview YAML。 | 全局、状态层、TASK_INDEX、MODULE_INDEX、W13-E2 | Preview YAML 已由 `DD-034` 确认；正式 `DOC_STATE.yaml` 写入、旧 ST 迁移或实现开窗仍不得写成 confirmed。 |
| DD-034 | OQ-093 确认采用方案 B：创建 Preview YAML 且不修改正式 DOC_STATE.yaml | confirmed | 用户已确认 `OQ-093=B`，本轮创建 `docs/superpowers/plans/2026-04-25-workbench-mvp-doc-state-preview.yaml`；`WT13-xx` 继续作为业务任务域 ID，`ST13_01~ST13_25` 仅作为 `doc_governor` 兼容的 preview alias；旧 `STxx_*` 仅写入 `w13_superseded_preview` 预览信息，不改变正式状态层。 | 状态层、W13-E3、TASK_INDEX、MODULE_INDEX | 只确认 preview 路径与 preview 文件，不确认正式 `DOC_STATE.yaml` 写入，不形成 implementation-ready。 |
| DD-035 | W13-E4-A 确认采用 C-Phased 高层 State Write 策略 | confirmed | 用户已确认最终目标是分阶段把 `ST13_01~ST13_25` 写入正式 `DOC_STATE.yaml`，再逐步将旧 `STxx_*` 标记为 `superseded / historical-reference`、移出正式任务容器并准备 archive 迁移。该决策只确认“必须分阶段”的高层策略，不确认 `W13-E4-B` 具体写入方案，不确认旧 ST 的正式字段表达，不确认备份方式。 | 状态层、W13-E4-A、TASK_INDEX、MODULE_INDEX、旧 ST 归档准备 | 具体执行仍以 `OQ-094~OQ-096` 用户确认卡为准；确认前不得修改正式 `DOC_STATE.yaml` 或进入 implementation-ready。 |
| DD-036 | W13-E4-B 阶段 1 写入正式 `ST13_01~ST13_25`，旧 `STxx_*` 保持并存 | confirmed | 用户已确认 `OQ-094=B`、`OQ-095` 阶段 1 方案 C / 阶段 2 方案 B、`OQ-096=B`。本轮只把 `ST13_01~ST13_25` 写入正式 `DOC_STATE.yaml`，追加 `RQ01.facts.task_ids`，并创建阶段 1 变更与回退说明；旧 `STxx_*` 未移除、未改写、未标记 superseded。 | 状态层、W13-E4-B、TASK_INDEX、MODULE_INDEX、OPEN_QUESTIONS | 阶段 2 仍需另开窗口确认并执行；不得把阶段 1 误读为 implementation-ready、formal window open 或 archive 迁移完成。 |
| DD-037 | W13-E4-C 阶段 2 用 facts 表达旧 `STxx_*` historical-reference / superseded | confirmed | 用户已确认采用方案 B：不移出旧 `STxx_*`，只在旧任务 `facts` 中写入 `w13_status=superseded`、`w13_role=historical-reference`、`w13_superseded_by`、`w13_alias_target`、`w13_archive_candidate=true` 和 `w13_current_implementation_entry=false`。旧任务仍保留在正式 `subtasks` 容器中，后续是否移出留到阶段 3。 | 状态层、W13-E4-C、TASK_INDEX、MODULE_INDEX、OPEN_QUESTIONS | 不得把阶段 2 误读为阶段 3、archive 迁移、formal window open、implementation-ready 或可进入实现。 |
| DD-038 | W13-E4-D 阶段 3 只做 dry-run / 影响分析，不正式移出旧 `STxx_*` | confirmed | 用户已确认进入 W13-E4-D 且采用方案 B：本窗口只做旧 ST 引用链审计、`RQ01.facts.task_ids` 影响分析、Stage3 Preview 方案和正式阶段 3 执行草案；正式 `DOC_STATE.yaml` 不修改，旧 `STxx_*` 不移出、不删除、不迁移 archive。 | 状态层、W13-E4-D、TASK_INDEX、MODULE_INDEX、OPEN_QUESTIONS | 下一步只可进入 Stage3 Preview 窗口；Stage3 Preview 路径确认见 `DD-039`，正式移出、正式 `RQ01.facts.task_ids` 改写和 archive 迁移仍待 Preview 验证后再确认，不得写成已完成或 implementation-ready。 |
| DD-039 | OQ-097~OQ-099 确认采用 Stage3 Preview 路径，不直接正式移出旧 `STxx_*` | confirmed | 用户已确认 `OQ-097=B`、`OQ-098=先做方案B的Preview，不正式移出旧STxx_*`、`OQ-099=先做方案B的Preview，在Preview中移除旧ST01_01、ST09_03`。该决策只确认下一窗口创建并验证 Stage3 Preview YAML；Preview 中可测试移出 30 个旧 `STxx_*` 以及从 `RQ01.facts.task_ids` 移除旧 `ST01_01`、`ST09_03`。 | 状态层、W13-E4-E、OPEN_QUESTIONS、TASK_INDEX、MODULE_INDEX、RQ01 | 不得据此直接修改正式 `DOC_STATE.yaml`，不得正式移出旧 `STxx_*`，不得正式改写 `RQ01.facts.task_ids`，不得生成 implementation packet 或标记 implementation-ready。 |
| DD-040 | W13-E4-E Stage3 Preview 已通过 | confirmed | 已创建 `docs/superpowers/plans/2026-04-25-workbench-mvp-doc-state-stage3-preview.yaml`；preview 中 `subtasks` 只保留 `ST13_01~ST13_25`，`RQ01.facts.task_ids` 只保留 `ST13_01~ST13_25`，`validate-state / evaluate-state` 均为 `ok=true,error=0,warning=0`。 | 状态层、W13-E4-E、RQ01、TASK_INDEX、MODULE_INDEX | 该决策只确认 preview 结果；后续正式 Stage 3 已由 `DD-041` / `OQ-100` 承接，不得写成 implementation-ready 或 formal window open。 |
| DD-041 | W13-E4-F 正式 State Write Stage 3 已执行，但不放行实现 | confirmed | 用户已确认 `OQ-100` 方案 B：基于 Stage3 Preview 执行正式 Stage 3。正式 `DOC_STATE.yaml.subtasks` 已只保留 `ST13_01~ST13_25`，旧 `ST01_01~ST10_03` 已从 current 容器移出，`RQ01.facts.task_ids` 已只保留 `ST13_01~ST13_25`。旧 `STxx_*` 仍保留为历史参考 / reusable evidence / archive candidate，未迁移 archive。 | 状态层、W13-E4-F、RQ01、TASK_INDEX、MODULE_INDEX、OPEN_QUESTIONS | 不得写成 implementation-ready，不得写成 formal window open，不得写成 archive 迁移完成；后续只能进入 archive 迁移评估或任务包 / 子任务文档准备。 |
| DD-042 | W13-E5 仅完成 ST13 readiness audit，不放行任务包以外的后续动作 | confirmed | W13-E5 只审计 `ST13_01~ST13_25` 的任务包准备缺口、依赖排序、formal window 条件、实现前置依赖和模块文档映射；25 个 ST13 均仍不具备 implementation-ready。 | W13-E5、TASK_INDEX、MODULE_INDEX、OPEN_QUESTIONS、后续任务包窗口 | `OQ-101~OQ-110` 已由 W13-E6 / `DD-043` 承接确认；W13-E5 的不放行 implementation-ready 结论仍有效。 |
| DD-043 | W13-E6 确认第一批只生成四个横向 contract 任务包草案 | confirmed | 用户已确认 `OQ-101=A`、`OQ-102=A`、`OQ-103=A`、`OQ-104=B`、`OQ-105=A`、`OQ-106=A`、`OQ-107=A`、`OQ-108=A`、`OQ-109=A`、`OQ-110=C`；W13-E6 只生成 `ST13_21 / ST13_20 / ST13_24 / ST13_25` 四个任务包草案，顺序为 `ST13_21 -> ST13_20 -> ST13_24 -> ST13_25`。 | W13-E6、OPEN_QUESTIONS、TASK_INDEX、后续 W13-E7 | 该决策不放行实现，不创建 `apps/**` / `infra/**`，不创建正式子任务目录，不生成 implementation packet，不打开 formal window；后续正式双文档和状态层动作仍需另开窗口。 |
| DD-044 | W13-E8 确认集中任务包目录并创建第一批 ST13 正式双文档 | confirmed | 用户已确认 `OQ-111=A`、`OQ-112=A`、`OQ-113=B`；本轮在 `docs/superpowers/plans/st13-task-packages/` 下创建 `ST13_21 / ST13_20 / ST13_24 / ST13_25` 四个任务包目录和 8 个 `ST13_XX_DESIGN.md` / `ST13_XX_IMPLEMENTATION.md` 双文档。 | W13-E8、OPEN_QUESTIONS、TASK_INDEX、MODULE_INDEX、AGENTS、后续 State Update | 双文档创建只表示 `double_doc_created`；`DOC_STATE.yaml` required doc slot 仍需后续单独 State Update，formal window 仍关闭，implementation packet 仍禁止，仍不得进入实现。 |
| DD-045 | W13-E8.5 第一批 ST13 required doc slot 已登记但不放行实现 | confirmed | 已按 `OQ-113=B` 在单独 State Update 窗口中，把 `ST13_21 / ST13_20 / ST13_24 / ST13_25` 的 DESIGN / IMPLEMENTATION 文档路径写入 `DOC_STATE.yaml` 既有 `facts.design_doc` / `facts.implementation_doc` slot。 | W13-E8.5、DOC_STATE.yaml、TASK_INDEX、MODULE_INDEX、PLAN_LATEST、后续 W13-E9 | 该登记只表示 `double_doc_registered`；不得写成 implementation-ready，不得写成 formal window open，不得生成 implementation packet，不得进入代码实现。 |
| DD-046 | W13-E11 确认第一批 ST13 formal window candidate 文档层分级，但不打开 formal window | confirmed | 用户已确认 `OQ-114=A`、`OQ-115=B`、`OQ-116=A`、`OQ-117=A`：接受 `ST13_24 / ST13_25 = ready_for_formal_window_candidate`，`ST13_21 / ST13_20 = near_ready_for_formal_window_candidate`；W13-E11 后再开 State Update；不新增 W13-E10.5；继续禁止 OpenAPI、schema、`tests/**`、`apps/**`、implementation packet、formal window open 和实现。 | W13-E11、OPEN_QUESTIONS、TASK_INDEX、MODULE_INDEX、PLAN_LATEST、后续 State Update | 该确认只形成文档层候选评估和后续 State Update 依据；不得写成 `candidate_status=candidate` 已写入，不得写成 formal window 已打开，不得写成 implementation-ready。 |
| DD-047 | W13-E13 只创建 candidate State Preview，且 Preview 验证失败后不进入正式 State Update | confirmed | 用户已确认 `OQ-118=B`、`OQ-119=A`、`OQ-120=B`：W13-E13 只在 preview 中测试 `ST13_24 / ST13_25` candidate 相关字段，`ST13_21 / ST13_20` near-ready 只保留文档层，先创建 preview YAML 且不修改正式 `DOC_STATE.yaml`。W13-E13 preview 验证发现当前规则不允许在 `formal_window_open=false` 时写入 `candidate_status=candidate`，且 `readiness=downstream_ready` 要求目标 `maturity` 非空。 | W13-E13、OPEN_QUESTIONS、candidate state preview、State Update plan | 正式 `DOC_STATE.yaml` 未修改；formal window 未打开；implementation packet 未生成；implementation-ready 未形成；不得直接进入 W13-E14 正式写入，需先确认 `OQ-121`。 |
| DD-048 | W13-E13 Preview 失败后暂停 W13-E14，并先修正 candidate 状态表达策略 | confirmed | 用户已确认 `OQ-121=A`：暂不执行正式 State Update，只保留失败 Preview，并先修正后续状态表达策略。该确认只覆盖“暂停 W13-E14 / 不写正式状态 / 先做策略修正”，不确认 facts-only、observe 或 maturity 方案已经可正式写入。 | W13-E13.5、OPEN_QUESTIONS、candidate strategy fix、后续 Candidate Preview | 正式 `DOC_STATE.yaml` 未修改；`ST13_24 / ST13_25` 仍只保留文档层 `formal_window_candidate_recommended`；后续 `OQ-122 / OQ-123` 确认前，不得把新策略写成 confirmed 或进入正式 State Update。 |
| DD-049 | W13-E13.6 创建 facts-only Candidate Preview，但不执行正式 State Update | confirmed | 用户已确认 `OQ-122=A`、`OQ-123=A`：下一轮 Candidate Preview 采用 facts-only 方案，并继续禁止 W13-E14 直到新 Preview 全绿。W13-E13.6 已创建 `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-candidate-state-facts-preview.yaml`，仅在 `ST13_24 / ST13_25.facts` 写入 `formal_window_candidate_recommended=true` 等推荐事实，不写 `candidate_status=candidate`，不写 `readiness=downstream_ready`。 | W13-E13.6、OPEN_QUESTIONS、facts-only candidate preview、State Update plan | 正式 `DOC_STATE.yaml` 未修改；Preview `validate-state / evaluate-state` 为 `ok=true,error=0,warning=0`，但完整 Preview `documents_blocked_count=1`；进入 W13-E14 需先处理或确认该 path-scan blocker，并由 `OQ-124` 单独确认。 |
| DD-050 | W13-E13.8 使用 docs/governance/previews 路径 Preview 后执行 facts-only 正式 State Update | confirmed | 用户已确认 `OQ-124` 方案 A：把 facts-only Preview 放到 `docs/governance/previews/` 下重新验证；Preview 严格全绿后，再把相同 facts-only candidate 推荐字段正式写入 `DOC_STATE.yaml`。W13-E13.8 已新增 `docs/governance/previews/DOC_STATE_W13_E13_8_CANDIDATE_FACTS_PREVIEW.yaml`，Preview 与正式状态写入后均 `validate-state / evaluate-state` 全绿且 `documents_blocked_count=0`。 | W13-E13.8、OPEN_QUESTIONS、DOC_STATE.yaml、facts-only candidate preview、State Update plan | 正式写入只覆盖 `ST13_24 / ST13_25.facts.formal_window_candidate_*`；不得误读为 `candidate_status=candidate`、`readiness=downstream_ready`、formal window open、implementation-ready 或 implementation packet 可生成。`ST13_21 / ST13_20` 仍只保留文档层 near-ready。 |

## 3. 当前唯一事实源索引

| 内容类别 | 唯一事实源 |
| --- | --- |
| 一期 MVP 范围 | `docs/superpowers/plans/2026-04-25-workbench-mvp-scope.md` |
| IA / 用户旅程 | `docs/superpowers/plans/2026-04-25-workbench-mvp-ia-user-journey.md` |
| 对象模型 / RAG / 多轮 / 后端边界 | `docs/superpowers/plans/2026-04-25-workbench-mvp-object-model-rag-multiround-backend.md` |
| 评分 / 复盘 / 导出 / DoD | `docs/superpowers/plans/2026-04-25-workbench-mvp-scoring-review-export-dod.md` |
| 任务重映射与状态层 dry-run | `docs/superpowers/plans/2026-04-25-workbench-mvp-task-remap.md` |
| State Write 分阶段计划 | `docs/superpowers/plans/2026-04-25-workbench-mvp-state-write-plan.md` |
| State Write 阶段 1 变更与回退说明 | `docs/superpowers/plans/2026-04-25-workbench-mvp-state-write-stage1.md` |
| State Write 阶段 2 变更与回退说明 | `docs/superpowers/plans/2026-04-25-workbench-mvp-state-write-stage2.md` |
| State Write 阶段 3 dry-run 与影响分析 | `docs/superpowers/plans/2026-04-25-workbench-mvp-state-write-stage3-dry-run.md` |
| Stage3 Preview YAML | `docs/superpowers/plans/2026-04-25-workbench-mvp-doc-state-stage3-preview.yaml` |
| State Write 阶段 3 变更与回退说明 | `docs/superpowers/plans/2026-04-25-workbench-mvp-state-write-stage3.md` |
| ST13 readiness audit | `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-readiness-audit.md` |
| ST13 第一批 contract 任务包草案 | `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-first-contract-task-packages.md` |
| ST13 第一批 contract 双文档准备方案 | `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-first-contract-double-doc-plan.md` |
| ST13 required doc slot State Update | `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-required-doc-slot-update.md` |
| ST13 第一批 contract readiness 复核 | `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-first-contract-readiness-review.md` |
| ST13 第一批 formal window candidate 评估 | `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-first-contract-formal-window-candidate-evaluation.md` |
| ST13 candidate State Update 准备方案 | `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-state-update-plan.md` |
| ST13 candidate State Update Preview YAML | `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-candidate-state-preview.yaml` |
| ST13 candidate 状态表达策略修正 | `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-candidate-state-strategy-fix.md` |
| 待办与路线图清单 | `docs/superpowers/plans/2026-04-25-workbench-mvp-backlog-roadmap.md` |
| OQ confirmed / historical 归并索引 | `OPEN_QUESTIONS.md` |
| 历史执行记录 | `EXECUTION_LOG.md` |

## 4. 使用说明

- 新增全局级关键口径时，应先补充本文档，再更新相关事实源文档、模块文档或执行计划。
- 已标记为 `superseded` 的 DD 不得继续作为当前一期 MVP 输入；只能作为历史解释。
- `needs-review` 表示已有部分 confirmed 内容，但仍不能直接进入实现。
- 决策状态变化后，应同步回写 `OPEN_QUESTIONS.md`、`PLAN_LATEST.md` 和必要的进展文档。

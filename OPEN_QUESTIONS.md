# AI 模拟面试 P1 待确认问题

## 1. 文档定位

- 本文档是全局 OQ / MQ 的唯一归并入口，用于判断哪些问题仍需要用户确认、哪些已被 confirmed 结论覆盖、哪些只保留为历史来源追踪。
- W13-Cleanup 后，`OQ-001~OQ-089` 已按 `FC-01~FC-19` 用户 confirmed 结果回压到问题层。
- W13-E 新增 `OQ-090~OQ-092`，仅用于任务 ID、旧 `STxx_*` 处理和 `DOC_STATE.yaml` 写入节奏确认；用户已确认三项 W13-E 结果，这些问题不改变 W13 产品范围 confirmed 事实。
- W13-E2 新增 `OQ-093`，用户已确认方案 B：先创建 preview YAML，不修改正式 `DOC_STATE.yaml`；W13-E3 已据此新增状态层 Preview YAML。
- W13-E4-A 新增 `OQ-094~OQ-096`，用于确认后续 State Write 的阶段 1 写入、旧 `STxx_*` superseded 表达和备份方式；用户已确认 `OQ-094=B`、`OQ-095` 阶段 1 方案 C / 阶段 2 方案 B、`OQ-096=B`，且 `W13-E4-C` 已按该确认执行阶段 2。
- W13-E4-D 新增 `OQ-097~OQ-099`，用于确认是否创建 Stage3 Preview YAML、旧 `STxx_*` 正式移出策略和 `RQ01.facts.task_ids` 旧任务处理；用户已确认 `OQ-097=B`、`OQ-098=先做方案B的Preview，不正式移出旧STxx_*`、`OQ-099=先做方案B的Preview，在Preview中移除旧ST01_01、ST09_03`。W13-E4-E 已创建并验证 Stage3 Preview YAML，W13-E4-F 已基于该 preview 执行正式 Stage 3。
- W13-E4-E 新增 `OQ-100`，用于确认是否基于已通过的 Stage3 Preview 执行正式 Stage 3；用户已确认方案 B，W13-E4-F 已正式移出旧 `STxx_*` 并改写 `RQ01.facts.task_ids`。
- W13-E6 已确认 `OQ-101~OQ-110`：第一批只生成 `ST13_21 / ST13_20 / ST13_24 / ST13_25` 的横向 contract / 测试 / 治理任务包草案；任务包准备与实现严格拆窗；formal window、implementation packet、实现目录创建仍禁止，直到后续逐项满足 gate 并再次确认。
- W13-E8 已确认并吸收 `OQ-111~OQ-113`：ST13 双文档路径采用集中任务包目录，允许创建第一批 `ST13_21 / ST13_20 / ST13_24 / ST13_25` 正式双文档，required doc slot 后续单独 State Update；三项均为 `confirmed`。W13-E8.5 已承接 `OQ-113=B` 完成第一批 required doc slot 登记。
- W13-E10 新增 `OQ-114~OQ-117`：用于确认第一批 ST13 formal window candidate 分级、后续 State Update 节奏、是否需要 W13-E10.5 补文档，以及是否继续禁止实现类动作；用户已在 W13-E11 确认 `OQ-114=A`、`OQ-115=B`、`OQ-116=A`、`OQ-117=A`。
- W13-E12 新增 `OQ-118~OQ-120`：用于确认是否允许下一窗口为 `ST13_24 / ST13_25` 准备 candidate 状态 preview、`ST13_21 / ST13_20` 是否写入状态层 near-ready，以及后续是否先创建 preview YAML；用户已确认 `OQ-118=B`、`OQ-119=A`、`OQ-120=B`。W13-E13 已创建 preview，但验证发现当前规则不允许在 `formal_window_open=false` 时写入 `candidate_status=candidate`。
- W13-E13 新增 `OQ-121`：用于确认 Preview 失败后的下一步处理；用户已确认 `OQ-121=A`，即暂不执行正式 State Update，只保留失败 Preview，并先修正后续状态表达策略。
- W13-E13.8 已吸收 `OQ-124`：用户确认采用方案 A，把 Preview 放到 `docs/governance/previews/` 下重新验证；Preview 严格全绿后，已执行 facts-only 正式 State Update。
- W13-E15 新增 `OQ-125~OQ-127`：用于确认是否允许后续单独窗口打开 formal window、formal window open 后是否允许同窗生成 implementation packet、formal window open 后是否允许同窗进入实现；三项均为 `proposed-default`，等待用户确认，不得写成 `confirmed`。
- 状态使用：
  - `open`
  - `proposed-default`
  - `confirmed`
  - `superseded`
  - `historical`

## 2. 清理后状态总览

| 类别 | 数量 | 说明 |
| --- | ---: | --- |
| `confirmed` | 122 | 已由 `W13-A`、`DD-018~DD-050`、`FC-01~FC-18` 或 W13-E / W13-E3 / W13-E4-A / W13-E4-B / W13-E4-C / W13-E4-D / W13-E4-E / W13-E4-F / W13-E6 / W13-E8 / W13-E11 / W13-E13 / W13-E13.5 / W13-E13.6 / W13-E13.8 过程确认覆盖，不再作为待确认阻塞。 |
| `historical` | 2 | `OQ-002`、`OQ-003` 只保留为 W10 旧口径来源追踪，不再作为当前一期 MVP 事实源。 |
| `open` | 0 | 当前没有 active 产品范围待确认项。 |
| `proposed-default` | 3 | `OQ-125~OQ-127` 为 W13-E15 formal window open 前置确认卡；确认前不得写成 confirmed。 |

M01-M10 的旧 MQ/OQ 已完成第一轮模块侧标记和补链：旧问题按 `confirmed / historical / superseded / open` 保留治理语义，模块索引和子文档父模块链接已补强。该处理不等于放行正式子任务窗口，也不等于旧 STxx_* 骨架已迁移到 archive。

## 3. 唯一事实源清单

| 内容类别 | 唯一事实源 |
| --- | --- |
| 一期 MVP 范围 | `docs/design/workbench-mvp/scope.md` |
| IA / 用户旅程 | `docs/design/workbench-mvp/information-architecture.md` |
| 对象模型 / RAG / 多轮 / 后端边界 | `docs/design/workbench-mvp/object-model-rag-multiround-backend.md` |
| 评分 / 复盘 / 导出 / DoD | `docs/design/workbench-mvp/scoring-review-export-dod.md` |
| 待办与路线图清单 | `docs/superpowers/plans/2026-04-25-workbench-mvp-backlog-roadmap.md` |
| 状态层 Preview YAML | `docs/superpowers/plans/2026-04-25-workbench-mvp-doc-state-preview.yaml` |
| State Write 分阶段计划 | `docs/superpowers/plans/2026-04-25-workbench-mvp-state-write-plan.md` |
| State Write 阶段 1 变更与回退说明 | `docs/superpowers/plans/2026-04-25-workbench-mvp-state-write-stage1.md` |
| State Write 阶段 2 变更与回退说明 | `docs/superpowers/plans/2026-04-25-workbench-mvp-state-write-stage2.md` |
| State Write 阶段 3 dry-run 与影响分析 | `docs/superpowers/plans/2026-04-25-workbench-mvp-state-write-stage3-dry-run.md` |
| State Write 阶段 3 变更与回退说明 | `docs/superpowers/plans/2026-04-25-workbench-mvp-state-write-stage3.md` |
| ST13 第一批 contract 双文档准备方案 | `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-first-contract-double-doc-plan.md` |
| ST13 第一批 contract readiness 复核 | `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-first-contract-readiness-review.md` |
| ST13 第一批 formal window candidate 评估 | `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-first-contract-formal-window-candidate-evaluation.md` |
| ST13 第一批 State Update 准备方案 | `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-state-update-plan.md` |
| ST13 candidate 状态表达策略修正 | `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-candidate-state-strategy-fix.md` |
| ST13 formal window open 前置确认 | `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-formal-window-open-precheck.md` |
| 决策索引 | `DESIGN_DECISIONS.md` |
| 历史执行记录 | `EXECUTION_LOG.md` |

其他文档不得重复维护上述内容的大段正文；需要引用时只保留摘要并指向对应唯一事实源。

## 4. OQ 归并索引

`FC-01~FC-19` 原始确认卡正文不再作为当前事实源逐项展开；当前以用户已确认结果和下列归并索引为准。若后续需要审计原始卡片措辞，应从会话记录或历史执行记录回溯，不应覆盖本文件的 confirmed 结论。

| 归并主题 | 覆盖 OQ / MQ | 当前状态 | 当前口径 |
| --- | --- | --- | --- |
| `W13-A` 工作台级 MVP 与 W10 原型降级 | `OQ-026`、`OQ-033` | confirmed | 一期 MVP 是工作台级；W10 `apps/web/**` 原型只作为参考证据，不再作为正式一期 MVP 起点。 |
| `FC-01` 代码结构、后端框架、API、部署与日志 | `OQ-001`、`OQ-019`、`OQ-052`、`OQ-062`、`OQ-063`、`OQ-064`、`OQ-065`、`OQ-066` | confirmed | 目标结构采用 `apps/web + packages/shared + apps/api`；后端 FastAPI；数据库 PostgreSQL；API contract 先行；部署目标为单机服务器；日志覆盖应用、LLM 与 RAG。W13-F 前不得直接创建目录或实现服务。 |
| `FC-02` 登录、账号、角色、权限与记录可见范围 | `OQ-004`、`OQ-005`、`OQ-029`、`OQ-035`、`OQ-036`、`OQ-046`、`OQ-061`、`OQ-067`、`OQ-068` | confirmed | 一期采用 session cookie；账号由管理员创建；角色为普通用户 / 管理员两级；记录默认展示“我的记录”，管理员可额外按团队筛选。 |
| `FC-03` 服务端保存与上下文保存深度 | `OQ-027`、`OQ-030`、`OQ-053`、`OQ-054`、`OQ-055` | confirmed | PostgreSQL 保存会话、简历、复盘、脱敏 LLM 记录、RAG query/topK、完整问答、摘要与评分证据。 |
| `FC-04` 真实 LLM provider 与失败策略 | `OQ-028`、`OQ-058`、`OQ-059`、`OQ-060` | confirmed | 建立可插拔 provider 抽象并先接一个默认 provider；记录脱敏 prompt、模型名和模板版本；失败状态可重新生成。 |
| `FC-05` RAG / 知识库 | `OQ-009`、`OQ-012`、`OQ-043`、`OQ-048`、`OQ-049`、`OQ-056`、`OQ-086` | confirmed | 支持用户私有上传 + 管理员公共知识库；团队共享后置；采用混合检索；失败时降级继续并标注证据缺口；RAG 进入评分证据但不直接决定分数。 |
| `FC-06` 模拟启动、多轮、暂停与模式节奏 | `OQ-037`、`OQ-038`、`OQ-044`、`OQ-045`、`OQ-047`、`OQ-050`、`OQ-051`、`OQ-057`、`OQ-069`、`OQ-079` | confirmed | 模拟面试默认入口是历史模拟记录列表；打磨模式由 `ProgressTree` 驱动，用户决定继续或结束；压力面由 `InterviewQuestionSet` 驱动，题目完成后结束；固定 3 轮不再是多轮总规则。`FC-06D` 完整语义为：压力面模式支持按岗位自动生成默认题型组合，并允许用户手动调整；打磨模式支持用户自定义主题 / 题型，并可结合岗位与薄弱项自动推荐，但不强制固定题组。 |
| `FC-07` 评分维度、权重、题级得分与评分证据 | `OQ-031`、`OQ-039`、`OQ-080`、`OQ-081`、`OQ-082`、`OQ-083`、`OQ-084`、`OQ-086` | confirmed | 评分维度为表达结构、技术深度、岗位匹配、证据充分度、风险控制；岗位匹配 / 技术深度权重更高；打磨题级分只用于训练进展，压力面题级分进入整场总分；RAG 证据进入评分证据但不直接决定分数。 |
| `FC-08` MVP DoD 与正式开工门槛 | `OQ-024`、`OQ-034`、`OQ-089` | confirmed | MVP DoD 采用产品、数据、UI、工程、收口五层；W13-F 可做写回和实施包评估；正式开窗仍需 `TASK_INDEX.md` 写入明确任务 ID。 |
| `FC-09` 工作台 IA 与后续能力占位 | `OQ-041`、`OQ-042` | confirmed | 工作台首页采用行动型摘要 + 后续能力折叠菜单；后续能力不得干扰一期主链。 |
| `FC-10` 岗位 / 简历管理与发起入口 | `OQ-025`、`OQ-037`、`OQ-047` | confirmed | 岗位和简历都列表化管理，且发起模拟时必选。 |
| `FC-11` 真实面试复盘与复盘展示结构 | `OQ-015`、`OQ-038`、`OQ-074`、`OQ-085` | confirmed | `FC-11D` 完整语义为：真实面试输入支持用户上传逐字稿原文，不要求用户先按题目拆分；系统由大模型自动识别问题与回答边界，再输出逐题拆解复盘；若切分置信度不足，提示用户校对。 |
| `FC-12` Markdown 导出、渲染链、原文范围与异步策略 | `OQ-006`、`OQ-007`、`OQ-032`、`OQ-040`、`OQ-087`、`OQ-088` | confirmed | 详情页提供复制 / 下载；导出完整复盘 + RAG 引用 + 训练建议；包含原始回答但不含真实面试材料原文；上传同步入库，转换和导出异步。 |
| `FC-13` 打磨、薄弱项、能力树、训练抽屉与消减规则 | `OQ-013`、`OQ-016`、`OQ-070`、`OQ-071`、`OQ-073`、`OQ-075`、`OQ-076`、`OQ-078` | confirmed | `WeaknessItem` 是可训练、可累计、可消减、可停练的中粒度训练主题；轻量能力树进入一期；训练抽屉是统一训练入口；每题反馈结构化保存；消减建议由用户确认后生效。 |
| `FC-14` 资产库归档范围与资产类型 schema | `OQ-010`、`OQ-072`、`OQ-077` | confirmed | 支持整份和单题归档到资产库；归档时选择资产类型；类型带 schema 时动态渲染字段表单；资产库采用归档动作 + 最小资产列表 / 详情 + schema 子集动态字段。 |
| `FC-15` 共享 Web 契约 | `OQ-020`、`OQ-021`、`OQ-022` 与 M01/M02/M03 相关 MQ | confirmed | 共享 Web 契约维持最小共享层：`PageHeader` / 摘要区、`page/page_size/q/status/sort/order`、统一分页骨架、`getMessages(locale)` 与最小 namespace；细节留模块 / 实现层。 |
| `FC-16` 正式开窗层、历史容器与观察面 | `OQ-024` 与 M01/M02/M03 相关 MQ | confirmed | 历史容器禁止直开；观察蓝本仅观察；正式开窗层仍为空；只有总控后续写入正式子任务 ID 才能开窗。 |
| `FC-17` 匹配分析、评估版本化与主题推荐 | `OQ-008`、`OQ-013`、`OQ-014` | confirmed | 匹配分析与评估采用规则版本化 + 共享核心评估框架 + 规则推荐优先。 |
| `FC-18` 管理台、snapshot、模型 catalog 与运维占位 | `OQ-011`、`OQ-017`、`OQ-018`、`OQ-023`、`OQ-042` | confirmed | Snapshot 只导入不抓取；管理台负责导入与运维入口；模型采用本地 catalog / seed；完整成员管理由治理模块承接；后续能力低干扰占位。 |
| `FC-19` 历史 W10 proposed-default 清理策略 | `OQ-002`、`OQ-003` 与 W10 历史段落 | historical | 历史 W10 `proposed-default` 保留为历史 / 辅助输入，并已在本轮降级或吸收到 Workbench MVP 正式设计事实源。 |

## 5. 已标记为 historical / superseded 的内容

- `OQ-002`：W10 首切片时期的最小运行时、测试与 CI 基线口径，仅作历史来源追踪。
- `OQ-003`：W10 首切片时期的视觉规范粒度口径，仅作历史来源追踪。
- W10 首切片“JD + 简历 Markdown -> 3 条问题 -> 第 1 题问答 -> 简版反馈”已由 `DD-018` 的工作台级 MVP 取代。
- W10 `apps/web/**` mock 原型只作参考证据，已由 `DD-019` 固定，不得作为正式一期 MVP 起点。

## 6. W13-E / W13-E2 / W13-E4 任务治理确认卡

这些确认卡来源于 `docs/superpowers/plans/2026-04-25-workbench-mvp-task-remap.md`。它们只处理任务治理和状态层写入节奏，不改变 `FC-01~FC-19` 已 confirmed 的产品事实。

| OQ ID | 问题 | 状态 | 推荐方案 | 备选方案 | 当前处理要求 |
| --- | --- | --- | --- | --- | --- |
| `OQ-090` | W13 工作台级任务 ID 如何命名？ | confirmed | 方案 A：使用 `WT13-xx`，例如 `WT13-01`、`WT13-02` | 方案 B：`WB-MVP-xx`；方案 C：`ST13_xx`；方案 D：用户自定义 | 用户已确认 `WT13-xx` 作为候选任务域命名；W13-E2 结论是当前状态层不能直接把它作为 `DOC_STATE.yaml.subtasks` key。 |
| `OQ-091` | 旧 `STxx_*` 在 W13 Task Remap 中如何处理？ | confirmed | 方案 B：建立新 W13 任务后，将旧 `STxx_*` 映射为 `superseded`，后续状态层窗口迁入 archive | 方案 A：全部保留为 `historical-reference`；方案 C：逐个精审；方案 D：用户自定义 | `W13-E4-C` 已用 `DOC_STATE.yaml.facts` 表达旧 `STxx_*` 的 `historical-reference / superseded`；本阶段不删除、不迁移、不移出正式容器。 |
| `OQ-092` | W13 任务树是否应在下一窗口写入 `DOC_STATE.yaml`？ | confirmed | 方案 A：暂不写 `DOC_STATE.yaml`，先做 W13-E2 dry-run | 方案 B：下一窗口写入新任务但暂不移除旧 `STxx_*`；方案 C：同时写入新任务并移出旧 `STxx_*`；方案 D：用户自定义 | 用户已确认先做 W13-E2 dry-run；本轮不写正式 `DOC_STATE.yaml`。 |
| `OQ-093` | W13-E3 是否允许写入 `DOC_STATE.yaml`？ | confirmed | 方案 B：创建 preview YAML，不修改正式 `DOC_STATE.yaml` | 方案 A：仍不写 `DOC_STATE.yaml`，只维护索引和路线图；方案 C：直接写正式 `DOC_STATE.yaml`，但不移除旧 `STxx_*`；方案 D：用户自定义 | 用户已确认 `OQ-093=B`；已新增 `docs/superpowers/plans/2026-04-25-workbench-mvp-doc-state-preview.yaml` 并完成预检。正式 `DOC_STATE.yaml` 未修改。用户已确认后续采用 C-Phased 高层策略，但具体 State Write 阶段仍需以下确认卡。 |
| `OQ-094` | 是否允许 W13-E4-B 写入 `ST13_01~ST13_25`，但不移除旧 `STxx_*`？ | confirmed | 方案 B：写入 `ST13_01~ST13_25`，不移除旧 `STxx_*` | 方案 A：继续只保留 Preview；方案 C：写入新任务并同时标记旧任务 superseded；方案 D：用户自定义 | 用户已确认方案 B；W13-E4-B 阶段 1 已写入正式 `DOC_STATE.yaml`，旧 `STxx_*` 保持未修改。 |
| `OQ-095` | 旧 `STxx_*` superseded 表达方式如何处理？ | confirmed | 第一阶段采用方案 C：先不表达 superseded，只并存新旧任务；第二阶段采用方案 B：在 `DOC_STATE.yaml` 中用现有字段表达 superseded / historical-reference | 方案 A：只在索引和 task-remap 表达；方案 D：用户自定义 | 用户已确认该分阶段口径；`W13-E4-B` 已完成阶段 1，`W13-E4-C` 已完成阶段 2，用旧任务 facts 写入 `w13_status`、`w13_role`、`w13_superseded_by` 与 `w13_alias_target`。 |
| `OQ-096` | 是否创建正式 State Write 备份文件？ | confirmed | 方案 B：在 `docs/superpowers/plans` 下创建 State Write 变更说明和回退说明，不复制 `DOC_STATE` | 方案 A：不创建备份；方案 C：创建写入前快照副本到 preview / backup 目录；方案 D：用户自定义 | 用户已确认方案 B；已新增 `docs/superpowers/plans/2026-04-25-workbench-mvp-state-write-stage1.md`，未复制正式 `DOC_STATE.yaml`。 |
| `OQ-097` | 是否创建 Stage3 Preview YAML？ | confirmed | 方案 B：下一窗口创建 Stage3 Preview YAML，不修改正式 `DOC_STATE.yaml` | 方案 A：不创建 Preview YAML，只保留 dry-run；方案 C：跳过 preview 直接正式移出旧 `STxx_*`；方案 D：用户自定义 | 用户已确认 `OQ-097=B`，且 W13-E4-E 已创建并验证 `docs/superpowers/plans/2026-04-25-workbench-mvp-doc-state-stage3-preview.yaml`；正式 `DOC_STATE.yaml` 未修改。 |
| `OQ-098` | 旧 `STxx_*` 正式移出策略如何处理？ | confirmed | 先做方案 B 的 preview：正式阶段 3 移出旧 `STxx_*`，同时保留合法历史引用 | 方案 A：暂不移出；方案 C：只移出确认无引用风险的旧任务；方案 D：用户自定义 | 用户已确认先做方案 B 的 Preview；W13-E4-E 已验证，W13-E4-F 已正式移出旧 `STxx_*`。旧任务只保留为历史参考 / reusable evidence / archive candidate。 |
| `OQ-099` | `RQ01.facts.task_ids` 中旧 `ST01_01`、`ST09_03` 如何处理？ | confirmed | 方案 B：阶段 3 preview 中移除 `ST01_01`、`ST09_03`，只保留 `ST13_01~ST13_25` | 方案 A：暂时保留；方案 C：移到历史说明字段，如果 schema 支持；方案 D：用户自定义 | 用户已确认先做方案 B 的 Preview；W13-E4-F 已在正式 `RQ01.facts.task_ids` 中移除旧 `ST01_01`、`ST09_03`，只保留 `ST13_01~ST13_25`。 |
| `OQ-100` | 是否基于 Stage3 Preview 执行正式 Stage 3？ | confirmed | 方案 B：执行正式 Stage 3，移出旧 `STxx_*`，并从 `RQ01.facts.task_ids` 移除旧 `ST01_01`、`ST09_03` | 方案 A：暂不执行正式 Stage 3；方案 C：只移出 `RQ01.facts.task_ids` 的旧任务但旧 `STxx_*` 暂留；方案 D：用户自定义 | 用户已确认方案 B；W13-E4-F 已完成正式 Stage 3 写入，验证结果为 `ok=true,error=0,warning=0`，且仍不放行 implementation-ready。 |

### 6.1 W13-E5 ST13 readiness audit 确认卡

完整卡片见 `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-readiness-audit.md` 第 11 节；用户已在 W13-E6 确认 `OQ-101=A`、`OQ-102=A`、`OQ-103=A`、`OQ-104=B`、`OQ-105=A`、`OQ-106=A`、`OQ-107=A`、`OQ-108=A`、`OQ-109=A`、`OQ-110=C`。确认结果只放行任务包草案，不放行 implementation packet、formal window 或代码实现。

| OQ ID | 问题 | 状态 | 推荐方案 | 备选方案 | 当前处理要求 |
| --- | --- | --- | --- | --- | --- |
| `OQ-101` | 是否允许生成 ST13 任务包草案？ | confirmed | 方案 A：先只生成 `ST13_21 / ST13_20 / ST13_24 / ST13_25` 四个横向 contract / 测试 / 治理任务包草案 | 方案 B：全量生成；方案 C：先补模块同步；方案 D：用户自定义 | 用户已确认 `A`；W13-E6 只生成第一批任务包草案，不生成 implementation packet。 |
| `OQ-102` | ST13 任务包生成顺序如何确定？ | confirmed | 方案 A：横向 contract 先行 | 方案 B：用户旅程先行；方案 C：模块成熟度先行；方案 D：用户自定义 | 用户已确认 `A`；第一批顺序为 `ST13_21 -> ST13_20 -> ST13_24 -> ST13_25`。 |
| `OQ-103` | 哪些 ST13 可先做 contract？ | confirmed | 方案 A：只做 `ST13_21 / ST13_20 / ST13_24 / ST13_25` | 方案 B：加入 `ST13_01 / ST13_10 / ST13_11 / ST13_12 / ST13_13`；方案 C：页面优先；方案 D：用户自定义 | 用户已确认 `A`；不得扩大到其他 ST13 或实现窗口。 |
| `OQ-104` | 是否允许创建 ST13 专属子任务文档？ | confirmed | 方案 B：先在 `docs/superpowers/plans/**` 生成任务包草案，不创建模块子任务目录 | 方案 A：直接创建专属子任务文档；方案 C：先更新模块任务索引；方案 D：用户自定义 | 用户已确认 `B`；W13-E6 不创建模块子任务目录或正式双文档。 |
| `OQ-105` | 何时允许创建 `apps/api/**`、`apps/web/**` 或 `infra/**`？ | confirmed | 方案 A：formal window 和 implementation packet 前一律禁止创建 | 方案 B：允许空骨架；方案 C：contract 后创建最小骨架；方案 D：用户自定义 | 用户已确认 `A`；当前仍禁止创建实现目录。 |
| `OQ-106` | 何时允许生成 implementation packet？ | confirmed | 方案 A：所有 P0 gate 补齐前禁止生成 | 方案 B：dry-run packet；方案 C：contract packet 草案；方案 D：用户自定义 | 用户已确认 `A`；当前禁止生成 implementation packet。 |
| `OQ-107` | formal window 何时打开？ | confirmed | 方案 A：每个 ST13 的任务包、双文档、验收、测试和用户确认齐备后逐个打开 | 方案 B：按阶段批量打开；方案 C：全量任务包完成后统一打开；方案 D：用户自定义 | 用户已确认 `A`；当前 formal window 仍关闭。 |
| `OQ-108` | 任务包准备与实现是否拆窗？ | confirmed | 方案 A：严格拆窗，任务包准备窗口不写代码 | 方案 B：同窗准备后继续实现；方案 C：contract 任务同窗实现；方案 D：用户自定义 | 用户已确认 `A`；任务包准备窗口不写代码。 |
| `OQ-109` | 先做 API contract 还是 UI skeleton？ | confirmed | 方案 A：API contract 先行 | 方案 B：UI skeleton 先行；方案 C：二者并行但只写文档；方案 D：用户自定义 | 用户已确认 `A`；不得绕过 API contract。 |
| `OQ-110` | 一期 MVP 实现准备先做后端还是前端？ | confirmed | 方案 C：后端 contract 与前端页面规格并行，等 contract 合并后再实现 | 方案 A：后端 / API / 数据先行；方案 B：前端页面规格先行；方案 D：用户自定义 | 用户已确认 `C`；后续可并行准备前端页面规格文档，但 contract 合并前不实现。 |

### 6.2 W13-E7 ST13 双文档准备确认卡

完整卡片见 `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-first-contract-double-doc-plan.md` 第 11 节。用户已在 W13-E8 确认 `OQ-111=A`、`OQ-112=A`、`OQ-113=B`；W13-E8 创建正式双文档，W13-E8.5 已按 `OQ-113=B` 更新 `DOC_STATE.yaml` required doc slot。

| OQ ID | 问题 | 状态 | 推荐方案 | 备选方案 | 当前处理要求 |
| --- | --- | --- | --- | --- | --- |
| `OQ-111` | ST13 双文档路径方案如何选择？ | confirmed | 方案 A：集中任务包目录，路径为 `docs/superpowers/plans/st13-task-packages/ST13_XX/ST13_XX_DESIGN.md` 与 `ST13_XX_IMPLEMENTATION.md` | 方案 B：模块子任务目录；方案 C：只冻结路径和模板；方案 D：用户自定义 | 用户已确认 `OQ-111=A`；W13-E8 已按集中任务包目录创建第一批双文档。 |
| `OQ-112` | 是否允许下一窗口创建第一批正式双文档？ | confirmed | 方案 A：允许 W13-E8 创建 `ST13_21 / ST13_20 / ST13_24 / ST13_25` 的正式双文档 | 方案 B：暂不创建；方案 C：只创建一个试点；方案 D：用户自定义 | 用户已确认 `OQ-112=A`；本轮只创建文档，仍不实现。 |
| `OQ-113` | 是否允许下一窗口更新 `DOC_STATE.yaml` 的 required doc slot？ | confirmed | 方案 B：创建双文档后，在后续单独 State Update 窗口更新 required doc slot | 方案 A：暂不更新 state；方案 C：创建双文档同窗更新 state；方案 D：用户自定义 | 用户已确认 `OQ-113=B`；W13-E8 不修改 `DOC_STATE.yaml`，W13-E8.5 已另窗完成第一批 required doc slot 登记。 |

### 6.3 W13-E10 readiness review 确认卡

完整卡片见 `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-first-contract-readiness-review.md` 第 14 节；用户已在 W13-E11 确认四项推荐方案。

| ID | 问题 | 状态 | 推荐方案 | 其他方案 | 当前处理 |
| --- | --- | --- | --- | --- | --- |
| `OQ-114` | 是否接受 W13-E10 formal window candidate 分级？ | confirmed | 方案 A：接受 `ST13_24 / ST13_25 = ready_for_formal_window_candidate`，`ST13_21 / ST13_20 = near_ready_for_formal_window_candidate`，进入 W13-E11 candidate 评估 | 方案 B：四个全部 near-ready；方案 C：四个全部 not-ready；方案 D：用户自定义 | 用户已确认 A；W13-E11 只形成文档层 candidate 评估，不直接写 `candidate_status`，不打开 formal window。 |
| `OQ-115` | 是否允许后续 State Update 处理 readiness / candidate_status？ | confirmed | 方案 B：W13-E11 后再开 State Update | 方案 A：暂不 State Update；方案 C：先 State Update 再 W13-E11；方案 D：用户自定义 | 用户已确认 B；本窗口不修改 `DOC_STATE.yaml`，后续另开 State Update。 |
| `OQ-116` | 是否需要 W13-E10.5 补齐 acceptance criteria / required tests / implementation scope？ | confirmed | 方案 A：不新增 W13-E10.5，直接进入 W13-E11 candidate 评估 | 方案 B：只补 `ST13_21 / ST13_20`；方案 C：四个全部补；方案 D：用户自定义 | 用户已确认 A；不新增 W13-E10.5。 |
| `OQ-117` | 是否保持 OpenAPI、schema、`tests/**`、`apps/**`、implementation packet、formal window open 和实现继续禁止？ | confirmed | 方案 A：继续全部禁止，直到用户另窗确认 formal window 和 implementation packet 条件 | 方案 B：允许后续仅创建 OpenAPI / schema 文档；方案 C：允许后续创建测试文件或应用目录骨架；方案 D：用户自定义 | 用户已确认 A；当前仍不写代码、不创建目录、不生成 packet、不打开 formal window。 |

### 6.4 W13-E12 State Update 准备确认卡

完整卡片见 `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-state-update-plan.md` 第 7 节；W13-E12 只输出确认卡，不修改 `DOC_STATE.yaml`。

| ID | 问题 | 状态 | 推荐方案 | 其他方案 | 当前处理 |
| --- | --- | --- | --- | --- | --- |
| `OQ-118` | 是否允许后续 W13-E13 在 `DOC_STATE.yaml` 中为 `ST13_24 / ST13_25` 写入 formal_window_candidate 相关状态？ | confirmed | 方案 B：下一窗口仅在 preview 中测试 `ST13_24 / ST13_25` 的 candidate 相关字段，保持 `formal_window_open=false`、`implementation-ready=false`，且不修改正式 `DOC_STATE.yaml` | 方案 A：暂不更新 `DOC_STATE.yaml`；方案 C：同时准备 formal window open；方案 D：用户自定义 | 用户已确认 `OQ-118=B`；W13-E13 已创建 preview，验证结果显示该组合当前不兼容。 |
| `OQ-119` | 是否允许后续 W13-E13 在 `DOC_STATE.yaml` 中为 `ST13_21 / ST13_20` 写入 near-ready 状态？ | confirmed | 方案 A：暂不写入状态层 near-ready，只保留文档层 near-ready | 方案 B：用 `facts` 字段表达 near_ready_for_formal_window_candidate 但不写 `candidate_status`；方案 C：直接写 `candidate_status` 但标记 near-ready；方案 D：用户自定义 | 用户已确认 `OQ-119=A`；`ST13_21 / ST13_20` 不写状态层 near-ready，也不写 candidate。 |
| `OQ-120` | 后续 State Update 是否需要先创建 preview YAML？ | confirmed | 方案 B：先创建 State Update preview YAML，不修改正式 `DOC_STATE.yaml` | 方案 A：不做 preview 直接写正式状态；方案 C：同一窗口先 preview 后正式写入；方案 D：用户自定义 | 用户已确认 `OQ-120=B`；W13-E13 已创建 `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-candidate-state-preview.yaml`，正式状态未修改。 |
| `OQ-121` | 是否基于 W13-E13 Preview 执行 W13-E14 正式 State Update？ | confirmed | 方案 A：暂不执行正式 State Update，只保留失败 Preview 并修正后续策略 | 方案 B：执行 W13-E14 正式 State Update；方案 C：执行 State Update 并准备 formal window open；方案 D：用户自定义 | 用户已确认 `OQ-121=A`；W13-E13.5 只修正表达策略，不进入 W13-E14。 |
| `OQ-122` | W13-E13.5 后是否创建新的 Candidate State Preview？ | confirmed | 方案 A：创建 facts-only Candidate Preview，`ST13_24 / ST13_25` 只用 facts 字段表达 `formal_window_candidate_recommended`，不写 `candidate_status=candidate`，不写 `readiness=downstream_ready` | 方案 B：创建 `candidate_status=observe` Preview；方案 C：创建 maturity + downstream_ready Preview；方案 D：用户自定义 | 用户已确认 `OQ-122=A`；W13-E13.6 已创建 facts-only Preview。 |
| `OQ-123` | 是否继续禁止 W13-E14 正式 State Update？ | confirmed | 方案 A：继续禁止，直到新的 Preview 全绿 | 方案 B：允许在 facts-only 方案下直接正式写入；方案 C：formal window open 前置确认后再写 `candidate_status=candidate`；方案 D：用户自定义 | 用户已确认 `OQ-123=A`；W13-E13.6 不进入 W13-E14，正式 `DOC_STATE.yaml` 未修改。 |
| `OQ-124` | 是否基于 W13-E13.6 facts-only Preview 执行后续 facts-only 正式 State Update？ | confirmed | 方案 A：把 Preview 放到 `docs/governance/previews/` 下重新验证；Preview 严格全绿后，再执行 facts-only 正式 State Update | 方案 B：继续只保留 Preview；方案 C：继续尝试 `candidate_status=observe` Preview；方案 D：用户自定义 | 用户已确认方案 A；W13-E13.8 已创建 `docs/governance/previews/DOC_STATE_W13_E13_8_CANDIDATE_FACTS_PREVIEW.yaml` 并通过 validate/evaluate，随后仅为 `ST13_24 / ST13_25` 写入 facts-only candidate 推荐字段。未写 `candidate_status=candidate`，未写 `readiness=downstream_ready`，未打开 formal window，未形成 implementation-ready。 |

### 6.5 W13-E15 formal window open 前置确认卡

完整卡片见 `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-formal-window-open-precheck.md` 第 9 节。W13-E15 只输出前置确认卡，不修改 `DOC_STATE.yaml`，不打开 formal window，不生成 implementation packet，不进入实现。

| ID | 问题 | 状态 | 推荐方案 | 其他方案 | 当前处理 |
| --- | --- | --- | --- | --- | --- |
| `OQ-125` | 是否允许后续单独窗口打开 `ST13_24 / ST13_25` 的 formal window？ | proposed-default | 方案 B：后续单独开 formal window open 窗口，只打开 `ST13_24`。 | 方案 A：暂不进入 formal window open；方案 C：只打开 `ST13_25`；方案 D：同时打开 `ST13_24 / ST13_25`；方案 E：用户自定义。 | 推荐 `ST13_24` 作为测试 / 验收 / DoD 试点；确认前不得执行状态写入，不得写成 `formal_window_open=true`。 |
| `OQ-126` | 如果后续打开 formal window，是否允许同一窗口生成 implementation packet？ | proposed-default | 方案 A：不允许。同一窗口只打开 formal window，packet 必须另开窗口并通过 preflight / packet gate。 | 方案 B：同窗尝试 packet dry-run；方案 C：直接生成正式 packet；方案 D：用户自定义。 | 推荐拆窗；确认前不得生成 packet，方案 C 不推荐且不得作为默认。 |
| `OQ-127` | 如果后续 formal window open 成功，是否允许立刻进入代码实现？ | proposed-default | 方案 A：不允许。formal window open 后仍需 packet 准备和用户确认。 | 方案 B：允许同窗进入实现；方案 C：只做文档实现；方案 D：用户自定义。 | 推荐保持 open-window、packet、实现三段式门禁；确认前不得创建 `apps/**`、`infra/**`、`tests/**` 或进入实现。 |

## 7. 使用说明

- 新增或恢复待确认问题时，必须写入 `open` 或 `proposed-default`，并说明为什么没有被现有 `FC` / `DD` / 唯一事实源覆盖；推荐方案不得在用户确认前写成 `confirmed`。
- 不得把 W10 首切片、mock LLM、无登录、会话内临时数据、无数值评分、不导出、无 RAG、无多轮等旧原型边界重新写成当前一期 MVP 范围。
- 读取本文件时，以第 3 节唯一事实源和第 4 节 OQ 归并索引为准，不再回溯已删除的确认前选项卡。

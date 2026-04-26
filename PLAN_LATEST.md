# AI 模拟面试系统当前推进计划

## 1. 文档定位

- 本文档是当前仓库推进入口，只保留当前阶段、事实源、阻断项和下一步。
- 历史治理轮次、W10 原型探索和完整确认卡正文保留在 `EXECUTION_LOG.md` 或 Git 历史中，不在本文档重复展开。
- 当前仓库仍以设计文档、治理状态、`doc_governor` 工具链和测试验证为主；不是可直接进入业务代码实施的 monorepo 实现仓库。

## 2. 当前阶段

- 当前阶段：`W13-E15 / formal window open 前置确认窗口` 已完成；已新增前置确认文档，复核 `ST13_24 / ST13_25` 可进入用户确认窗口，但不直接打开 formal window。
- 当前边界：正式 `DOC_STATE.yaml` 未在本窗口修改；`ST13_24 / ST13_25` 仍只保留 facts-only candidate 推荐字段，未写 `candidate_status=candidate`，未写 `readiness=downstream_ready`，未打开 formal window，未标记 implementation-ready，未生成 implementation packet，未创建 `apps/**` / `infra/**` / `tests/**`，未进入实现。
- 验证结论：`git status --short` 为空，`main...origin/main` 为 `0 0`；正式 `DOC_STATE.yaml` 的 `validate-state / evaluate-state` 均为 `ok=true,error=0,warning=0`，`documents_blocked_count=0`。
- preflight 结论：`ST13_24 / ST13_25` 均为 `gate_result=blocked`，`can_open_formal_window=false`、`can_generate_implementation_packet=false`、`can_mark_implementation_ready=false`；主要 blockers 包含 `formal_window_closed`、`official_readiness_blocked`、`implementation_doc_not_active`、`acceptance_criteria_missing`、`required_tests_missing` 和 `implementation_scope_unclear`。
- 当前边界：W13-E8.5 已登记 required doc slot，W13-E14-Merge 已补齐文档层前置材料；但 formal window、implementation doc activation、packet inputs、implementation-ready 和实现仍未闭合。
- 代码开发状态：暂停。不得扩展 `apps/web/**`，不得创建 `apps/api/**`、`infra/**`，不得接真实 LLM、数据库、登录、评分、RAG、多轮、复盘、导出、薄弱项、训练抽屉、资产库或后端实现。
- W10 `apps/web/**` 原型只作为参考证据，不是正式一期 MVP 起点。

## 3. 当前唯一事实源

| 内容类别 | 唯一事实源 |
| --- | --- |
| 一期 MVP 范围 | `docs/superpowers/plans/2026-04-25-workbench-mvp-scope.md` |
| IA / 用户旅程 | `docs/superpowers/plans/2026-04-25-workbench-mvp-ia-user-journey.md` |
| 对象模型 / RAG / 多轮 / 后端边界 | `docs/superpowers/plans/2026-04-25-workbench-mvp-object-model-rag-multiround-backend.md` |
| 评分 / 复盘 / 导出 / DoD | `docs/superpowers/plans/2026-04-25-workbench-mvp-scoring-review-export-dod.md` |
| 任务重映射草案 | `docs/superpowers/plans/2026-04-25-workbench-mvp-task-remap.md` |
| ST13 readiness audit | `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-readiness-audit.md` |
| ST13 第一批 contract 任务包草案 | `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-first-contract-task-packages.md` |
| ST13 第一批 contract 双文档准备方案 | `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-first-contract-double-doc-plan.md` |
| ST13 required doc slot State Update | `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-required-doc-slot-update.md` |
| ST13 第一批 contract readiness 复核 | `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-first-contract-readiness-review.md` |
| ST13 第一批 formal window candidate 评估 | `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-first-contract-formal-window-candidate-evaluation.md` |
| ST13 candidate State Update 准备方案 | `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-state-update-plan.md` |
| ST13 candidate State Update Preview YAML | `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-candidate-state-preview.yaml` |
| ST13 candidate 状态表达策略修正 | `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-candidate-state-strategy-fix.md` |
| ST13 formal window open 前置确认 | `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-formal-window-open-precheck.md` |
| ST13 第一批正式双文档 / contract 细化 | `docs/superpowers/plans/st13-task-packages/ST13_21/ST13_21_DESIGN.md`、`docs/superpowers/plans/st13-task-packages/ST13_20/ST13_20_DESIGN.md`、`docs/superpowers/plans/st13-task-packages/ST13_24/ST13_24_DESIGN.md`、`docs/superpowers/plans/st13-task-packages/ST13_25/ST13_25_DESIGN.md` |
| 状态层 Preview YAML | `docs/superpowers/plans/2026-04-25-workbench-mvp-doc-state-preview.yaml` |
| State Write 分阶段计划 | `docs/superpowers/plans/2026-04-25-workbench-mvp-state-write-plan.md` |
| State Write 阶段 1 变更与回退说明 | `docs/superpowers/plans/2026-04-25-workbench-mvp-state-write-stage1.md` |
| State Write 阶段 2 变更与回退说明 | `docs/superpowers/plans/2026-04-25-workbench-mvp-state-write-stage2.md` |
| State Write 阶段 3 dry-run 与影响分析 | `docs/superpowers/plans/2026-04-25-workbench-mvp-state-write-stage3-dry-run.md` |
| Stage3 Preview YAML | `docs/superpowers/plans/2026-04-25-workbench-mvp-doc-state-stage3-preview.yaml` |
| State Write 阶段 3 变更与回退说明 | `docs/superpowers/plans/2026-04-25-workbench-mvp-state-write-stage3.md` |
| 待办与路线图清单 | `docs/superpowers/plans/2026-04-25-workbench-mvp-backlog-roadmap.md` |
| 决策索引 | `DESIGN_DECISIONS.md` |
| OQ / MQ 归并入口 | `OPEN_QUESTIONS.md` |
| 历史执行记录 | `EXECUTION_LOG.md` |

## 4. 当前 confirmed 主口径

- 一期 MVP 是工作台级，包含服务端历史 / 复盘记录、真实 LLM、完整登录 / 权限、简历与面试记录服务端保存、完整 `0-100` 多维评分、复制 / Markdown 下载、RAG / 知识库和多轮高阶面试。
- 模拟面试默认入口是历史模拟记录列表；可从岗位详情或模拟面试模块发起；发起时选择岗位、简历、模式；系统整理参考材料包并生成策略与首题。
- 打磨模式由 `ProgressTree` 驱动，用户决定继续或结束；压力面模式由 `InterviewQuestionSet` 驱动，题目完成后结束；固定 3 轮不再是多轮总规则。
- 真实面试复盘与模拟面试复盘都进入一期复盘设计；复盘、评分、RAG 证据、训练建议和 Markdown 导出以评分 / 复盘 / 导出 / DoD 文档为准。
- `WeaknessItem`、训练抽屉、资产库归档动作和最小资产列表 / 详情进入一期设计闭环。

## 5. 当前主线窗口

| 窗口 | 状态 | 作用 |
| --- | --- | --- |
| W13-B | 已产出，作为当前 IA / 用户旅程事实源 | 维护工作台 IA、模拟记录入口、RAG / 知识库入口、多轮入口和页面流转。 |
| W13-C | 已产出，作为当前对象模型 / RAG / 多轮 / 后端边界事实源 | 维护对象模型、服务端保存、权限、RAG、LLM、多轮状态机和后端边界。 |
| W13-D | 已产出，作为当前评分 / 复盘 / 导出 / DoD 事实源 | 维护评分、复盘、导出、错误态、空状态和 DoD。 |
| W13-Cleanup / W13-FC-RefAudit | 已完成项目级清理 | 清理旧 OQ/MQ、旧 DD、重复确认卡、孤立文档候选和唯一事实源引用。 |
| W13-GOV-MergeArchive | 已完成 | 合并旧实现计划归档、M01-M10 旧 MQ/OQ 标记和模块子文档补链结果；确认剩余归档问题不阻断 W13 后续设计。 |
| W13-StateArchive | 已完成 | 将旧 P1 设计稿从当前 `documents` 受管集合移出并迁入 archive；旧 STxx_* 骨架因仍在状态层和索引层引用，本轮不迁移。 |
| W13-F | 已完成阶段收口核验 | 已验证 W13-D 存在且内容完整，完成 Basic Memory 写回与回读验证；Superpowers / 当前执行计划正文未在本轮扩写。 |
| W13-E | 当前草案已形成 | 已新增任务重映射草案，建立 `WT13-xx` 候选任务树、旧 `STxx_*` 处理策略、模块映射、开窗顺序和 `DOC_STATE.yaml` 后续改造确认卡；仍不放行实现。 |
| W13-E2 | 当前 dry-run 收口 | 已检查 `WT13-xx` 与当前 schema 不直接兼容，旧 `STxx_*` 到 `WT13` 映射草案形成，并新增 backlog-roadmap 作为后续事项追踪清单；仍不写 `DOC_STATE.yaml`。 |
| W13-E3 | Preview YAML 已创建 | 用户确认 `OQ-093=B` 后，已新增 `docs/superpowers/plans/2026-04-25-workbench-mvp-doc-state-preview.yaml`；其中 `ST13_01~ST13_25` 是兼容状态层的 preview alias，映射到 `WT13-01~WT13-25`；30 个旧 `STxx_*` 仅加入 superseded preview 信息，正式 `DOC_STATE.yaml` 未修改。 |
| W13-E4-A | 计划已完成 | 已新增 `docs/superpowers/plans/2026-04-25-workbench-mvp-state-write-plan.md`，吸收用户确认的 C-Phased 高层策略，定义四阶段 State Write、验证矩阵、回退方案、`ST13_01~ST13_25` 写入草案和三张确认卡；阶段 1 已由 `W13-E4-B` 执行。 |
| W13-E4-B | 阶段 1 已执行 | 已按 `OQ-094=B`、`OQ-095` 阶段 1 方案 C、`OQ-096=B` 写入正式 `ST13_01~ST13_25`，追加 `RQ01.facts.task_ids`，保留旧 `STxx_*`，并新增阶段 1 变更与回退说明；仍不放行实现。 |
| W13-E4-C | 阶段 2 已执行 | 已按用户确认的方案 B 在 30 个旧 `STxx_*` 的 `facts` 中表达 `historical-reference / superseded`，写入 `w13_superseded_by` 与 `w13_alias_target` 映射；旧任务仍保留在正式 `subtasks` 容器中，未移出、未归档、未放行实现。 |
| W13-E4-D | dry-run 与确认吸收已完成 | 已新增阶段 3 dry-run 文档，完成旧 `STxx_*` 引用链、`RQ01.facts.task_ids`、`subtasks` 容器移出策略、Stage3 Preview 方案和正式阶段 3 执行草案；用户已确认 `OQ-097~OQ-099` 采用 Preview 路径。该阶段本身不移出旧任务，不放行实现。 |
| W13-E4-E | Stage3 Preview 已完成 | 已新增 `docs/superpowers/plans/2026-04-25-workbench-mvp-doc-state-stage3-preview.yaml`，在 preview 中将 `subtasks` 收敛为 `ST13_01~ST13_25`，并将 `RQ01.facts.task_ids` 收敛为 `ST13_01~ST13_25`；preview `validate-state / evaluate-state` 均为 `ok=true,error=0,warning=0`，正式 `DOC_STATE.yaml` 未修改，仍不放行实现。 |
| W13-E4-F | Stage 3 正式写入已完成 | 已基于用户确认方案 B 将正式 `DOC_STATE.yaml.subtasks` 收敛为 `ST13_01~ST13_25`，并从正式 `RQ01.facts.task_ids` 移除旧 `ST01_01`、`ST09_03`；新增阶段 3 变更与回退说明。旧 `STxx_*` 文档未删除、未迁移 archive，仍不放行实现。 |
| W13-E5 | ST13 readiness audit 已完成 | 已新增 `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-readiness-audit.md`，逐项审计 `ST13_01~ST13_25` 的任务包准备缺口、formal window 条件、实现前置依赖和模块文档映射；仍不放行 implementation-ready。 |
| W13-E6 | ST13 第一批 contract 任务包草案已完成 | 用户已确认 `OQ-101=A`、`OQ-102=A`、`OQ-103=A`、`OQ-104=B`、`OQ-105=A`、`OQ-106=A`、`OQ-107=A`、`OQ-108=A`、`OQ-109=A`、`OQ-110=C`；已新增第一批 `ST13_21 -> ST13_20 -> ST13_24 -> ST13_25` 任务包草案；仍不放行 implementation packet、formal window 或实现。 |
| W13-E7 | ST13 第一批 contract 双文档准备方案已完成 | 已新增 `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-first-contract-double-doc-plan.md`，审计四个 ST13 的草案缺口，定义双文档模板、路径方案、前置清单、contract 摘要、父索引同步方案和 `OQ-111~OQ-113` 确认卡；当时只到 `double_doc_path_planned`，不创建双文档、不写 state、不实现。 |
| W13-E8 | ST13 第一批正式双文档已创建 | 用户已确认 `OQ-111=A`、`OQ-112=A`、`OQ-113=B`；已在 `docs/superpowers/plans/st13-task-packages/` 下创建 `ST13_21 / ST13_20 / ST13_24 / ST13_25` 四个目录和 8 个 `DESIGN` / `IMPLEMENTATION` 文档；仍不修改 `DOC_STATE.yaml`、不放行 implementation-ready。 |
| W13-E8.5 | ST13 第一批 required doc slot 已登记 | 已按 `OQ-113=B` 将 `ST13_21 / ST13_20 / ST13_24 / ST13_25` 的 DESIGN / IMPLEMENTATION 路径写入 `DOC_STATE.yaml` 既有 `facts.design_doc` / `facts.implementation_doc` slot；仍不放行 implementation-ready，不生成 implementation packet，不打开 formal window。 |
| W13-E9 | ST13 第一批 contract 细化已完成 | 已清理 8 个双文档中的 required doc slot 过时表述，并细化 `ST13_21` API contract、`ST13_20` 数据 contract、`ST13_24` 测试 / DoD contract、`ST13_25` 文档治理 / 收口 / Basic Memory contract；仍不放行 implementation-ready，不生成 implementation packet，不打开 formal window。 |
| W13-E10 | ST13 第一批 readiness 复核已完成 | 已复核四个 contract_refined 双文档的 acceptance criteria、required tests、implementation scope 和 formal window candidate 输入；`ST13_24 / ST13_25` 建议为 `ready_for_formal_window_candidate`，`ST13_21 / ST13_20` 建议为 `near_ready_for_formal_window_candidate`；仍不修改 `DOC_STATE.yaml`，不生成 implementation packet，不打开 formal window。 |
| W13-E11 | ST13 第一批 formal window candidate 评估已完成 | 已吸收用户确认：`OQ-114=A`、`OQ-115=B`、`OQ-116=A`、`OQ-117=A`。`ST13_24 / ST13_25` 形成文档层 `formal_window_candidate_recommended`；`ST13_21 / ST13_20` 形成文档层 `near_ready_for_formal_window_candidate_confirmed`。仍不修改 `DOC_STATE.yaml`，不打开 formal window，不生成 implementation packet。 |
| W13-E12 | ST13 candidate State Update 准备已完成 | 已新增 State Update 准备方案，确认当前 schema 支持 `candidate_status=candidate`、`review_status=pending_confirmation`、`readiness=downstream_ready` 等 preview 候选组合；`ST13_24 / ST13_25` 可进入 W13-E13 preview，`ST13_21 / ST13_20` 默认保留文档层 near-ready。正式 `DOC_STATE.yaml` 未修改。 |
| W13-E13 | ST13 candidate State Preview 已创建但验证失败 | 已新增 `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-candidate-state-preview.yaml`；preview 中仅尝试更新 `ST13_24 / ST13_25` candidate 相关字段，`ST13_21 / ST13_20` 保持原样。验证失败原因是 `formal_window_open=false` 时禁止 candidate，且 `downstream_ready` 需要非空 maturity。正式 `DOC_STATE.yaml` 未修改。 |
| W13-E13.5 | Candidate State 表达策略修正已完成 | 已新增 `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-candidate-state-strategy-fix.md`；`OQ-121=A` 已吸收，`W13-E14` 暂不执行。后续优先创建 facts-only Candidate Preview，备选验证 `candidate_status=observe`；正式 `DOC_STATE.yaml` 未修改。 |
| W13-E13.6 | facts-only Candidate Preview 已创建 | 已新增 `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-candidate-state-facts-preview.yaml`；`ST13_24 / ST13_25` 仅写入 facts-only candidate 推荐字段，`ST13_21 / ST13_20` 保持正式状态原样。Preview `validate-state / evaluate-state` 均为 `ok=true,error=0,warning=0`，但 `documents_blocked_count=1` 来自 plan-path Preview 的 document 扫描根目录副作用；正式 `DOC_STATE.yaml` 未修改，仍不放行实现。 |
| W13-E13.8 | docs/governance/previews 路径 Preview 与 facts-only 正式 State Update 已完成 | 已新增 `docs/governance/previews/DOC_STATE_W13_E13_8_CANDIDATE_FACTS_PREVIEW.yaml`；Preview 与正式 `DOC_STATE.yaml` 均通过 `validate-state / evaluate-state`，且 `documents_blocked_count=0`。正式状态层只为 `ST13_24 / ST13_25` 写入 facts-only candidate 推荐字段；`ST13_21 / ST13_20` 仍不写 candidate，formal window、implementation packet 和实现仍关闭。 |
| W13-E14-Merge | formal window 前置补齐合并已完成 | 已接收并复核 W13-E14-A/B/C/D 四个并行窗口结果。`ST13_24 / ST13_25` 的 formal window 前置材料进一步补齐；`ST13_21 / ST13_20` 的 near-ready blocker 进一步明确。未修改 `DOC_STATE.yaml`，未创建实现目录，仍不能实现、不能生成 implementation packet、不能打开 formal window。 |
| W13-E15 | formal window open 前置确认已完成 | 已新增 `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-formal-window-open-precheck.md`，确认 `ST13_24 / ST13_25` 可进入 formal window open 用户确认窗口；推荐后续单独窗口只打开 `ST13_24` 作为试点，packet 和实现继续拆窗。未修改 `DOC_STATE.yaml`，未打开 formal window，未生成 implementation packet，未进入实现。 |

## 6. 当前阻断与风险

- 当前没有 active 产品范围 `open` OQ；`OQ-111~OQ-124` 已由用户确认并写回 confirmed，`OQ-124` 已由 W13-E13.8 吸收为 docs/governance/previews 路径 Preview 严格全绿后执行 facts-only 正式 State Update。
- `OQ-090~OQ-110` 已按用户确认吸收，其中 `OQ-097~OQ-099` 已落实到 Stage3 Preview 创建与验证，`OQ-100` 已落实到正式 Stage 3 写入，`OQ-101~OQ-110` 已落实到 W13-E6 第一批任务包草案边界。
- `DD-005` 与 `DD-007` 仍为 `needs-review`：后端 FastAPI 与导出形态已 confirmed，但完整 Web framework / 渲染链实现细节不得直接进入代码。
- 正式开窗层仍为空；`TASK_INDEX.md` 仅新增 W13-E 候选任务树摘要，任何实现仍必须等待用户确认、状态层改造和正式开窗。
- 旧实现计划正文已迁移到 `archive/docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md`；原路径只保留跳转说明，不作为当前事实源。
- 旧 P1 设计稿已从 `DOC_STATE.yaml` 当前 `documents` 受管集合移出，并迁移到 `archive/docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md`；原路径只保留跳转说明，不作为当前事实源。
- M01-M10 的旧 MQ/OQ 标记和模块子文档补链已完成第一轮；旧 `STxx_*` 骨架已从正式 `DOC_STATE.yaml.subtasks` current 容器移出，但仍保留在 `TASK_INDEX.md`、`MODULE_INDEX.md`、stage-write 文档和模块历史索引中作为历史参考 / reusable evidence / archive candidate，当前仍不得迁移 archive。
- Basic Memory 已完成 W13-F 阶段收口摘要写回并回读验证；W13-E2 / W13-E3 增量本轮不写 Basic Memory，如需沉淀由后续专门收口窗口统一写回。
- `DOC_STATE.yaml` 已在阶段 1 写入 `ST13_01~ST13_25`，阶段 2 为 30 个旧 `STxx_*` 写入历史化 facts，阶段 3 正式移出旧 `STxx_*` 并收敛 `RQ01.facts.task_ids`；当前 formal `subtasks` 数量为 25，旧 `STxx_*` formal 数量为 0。
- `W13-E4-E` Stage3 Preview 已作为正式 Stage 3 的验证依据被吸收；`W13-E4-F` 已执行正式写入，结果与 preview 的核心状态层结论一致。
- `WT13-xx` 继续作为文档层任务域 alias，正式状态层入口使用兼容的 `ST13_01~ST13_25`。
- `docs/superpowers/plans/2026-04-25-workbench-mvp-backlog-roadmap.md` 已成为项目待办、状态层后续、二期 / 三期和归档后续事项的持续追踪入口。
- W13-E5 审计确认：25 个 ST13 均缺 ST13 专属设计 / 实施双文档、acceptance criteria、required tests 和 formal window；其中 `ST13_20`、`ST13_21`、`ST13_24`、`ST13_25` 仅可作为下一窗口任务包准备候选，不表示可实现。
- W13-E6 任务包草案确认：第一批四个 ST13 已形成任务包草案，但状态仍为 `task_packet_draft_created` / `not_ready_for_implementation`；`DOC_STATE.yaml` 中 25 个 ST13 仍 blocked。
- W13-E13.8 facts-only State Update：`OQ-124` 已确认并吸收；`ST13_24 / ST13_25` 的 candidate 推荐已以 facts-only 字段进入正式状态层，但不等于 `candidate_status=candidate`、不等于 formal window open、也不等于 implementation-ready。
- W13-E14-Merge 已完成四个并行前置补齐窗口的合并核验：`ST13_24 / ST13_25` 已补齐 formal window 前置材料，`ST13_21 / ST13_20` 已补齐 near-ready blocker 和升级条件；该结论仍只属于文档层前置补齐，不等于开窗、packet 或 implementation-ready。
- W13-E15 已完成 formal window open 前置确认：`ST13_24 / ST13_25` 可进入用户确认窗口，但 preflight 仍 blocked；当前推荐只把 `ST13_24` 作为后续 open-window 试点，不同窗生成 packet，不进入实现。

## 7. 下一步

1. 等待用户确认 `OQ-125~OQ-127`：是否允许后续 formal window open 执行窗口、packet 是否拆窗、实现是否拆窗。
2. 推荐下一窗口只执行 `ST13_24` formal window open 状态治理试点；该窗口仍不得生成 implementation packet 或进入实现。
3. 在 formal window 另行确认并通过状态层 gate 前，仍不能生成 implementation packet，不能标记 implementation-ready，不能创建 `apps/**`、`infra/**`、`tests/**` 或进入实现。
4. 不得因文档层 candidate 推荐、facts-only 状态记录或 W13-E15 推荐方案而写 `candidate_status=candidate`、打开 formal window 或进入实现。
5. `ST13_25` 可作为第二个治理任务候选，但 Basic Memory / Superpowers 写回必须另开授权窗口；当前不写 Basic Memory。
6. `ST13_21 / ST13_20` 继续保持 near-ready，等待 M02、OpenAPI、schema、`apps/api/**`、migration / ORM 等授权闭合后再评估。
7. 旧 `STxx_*` archive 迁移评估必须另开确认窗口；当前不得直接迁移旧文档。

## 8. 验证命令

验证命令以执行窗口的实际输出为准；本文档不再内嵌关键字复扫表达式，避免验证命令本身成为误命中来源。

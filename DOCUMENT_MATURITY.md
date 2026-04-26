# AI 模拟面试 P1 文档成熟度

## 1. 文档定位

- 本文档用于登记当前文档体系的成熟度摘要。
- 本文档不再承载完整产品事实、完整 OQ/MQ 正文或历史模块推进长记录。
- 当前产品事实以 `PLAN_LATEST.md` 和四份 W13 唯一事实源为准。
- 当前 OQ / MQ 状态以 `OPEN_QUESTIONS.md` 为准。
- 当前进展摘要以 `DOCUMENT_PROGRESS.md` 为准。

## 2. 成熟度等级定义

| 等级 | 名称 | 说明 | 可作为下游输入 | 可直接用于实施 |
| --- | --- | --- | --- | --- |
| L0 | 未创建 | 文档不存在或仅在索引中占位 | 否 | 否 |
| L1 | 仅有骨架 | 只有标题、章节或极少量提示信息 | 否 | 否 |
| L2 | 初稿 | 已有初步内容，但边界、输入输出、依赖和问题仍不稳定 | 否 | 否 |
| L3 | 待澄清 | 结构基本完整，但仍有会阻塞下游的关键问题 | 否 | 否 |
| L4 | 可评审 | 已具备稳定结构，可用于组织评审，但尚未细化到实施粒度 | 部分 | 否 |
| L5 | 可作为下游输入 | 已能稳定支撑下游设计或拆分 | 是 | 否 |
| L6 | 可直接用于实施 | 已明确目标、范围、文件边界、实施步骤、验证方式和 DoD | 是 | 是 |
| L7 | 稳定维护 | 已经过多轮使用和回写，只做增量维护 | 是 | 是 |

## 3. 当前全局文档成熟度摘要

| 文档路径 | 当前等级 | 当前角色 | 是否可作为下游输入 | 是否可直接用于实施 |
| --- | --- | --- | --- | --- |
| `AGENTS.md` | L5 | 项目协作入口和索引 | 是 | 否 |
| `docs/DOC_GOVERNANCE.md` | L5 | 人工协作与文档治理总则 | 是 | 否 |
| `PLAN_LATEST.md` | L5 | 当前推进入口和唯一事实源索引 | 是 | 否 |
| `OPEN_QUESTIONS.md` | L5 | OQ / MQ confirmed / historical 归并入口 | 是 | 否 |
| `DESIGN_DECISIONS.md` | L5 | DD confirmed / superseded / needs-review 决策索引 | 是 | 否 |
| `TECHNICAL_STANDARDS.md` | L4 | confirmed 技术标准摘要，仍保留 implementation packet 复核边界 | 部分 | 否 |
| `TASK_INDEX.md` | L4 | 当前任务索引；已同步 `ST13_01~ST13_25` 正式状态层入口、`WT13-xx` alias、旧 `STxx_*` historical 口径、第一批 `ST13_20/21/24/25` contract_refined 状态、W13-E13 candidate preview 失败结果、W13-E13.5 candidate 状态表达策略修正和 W13-E14-Merge formal window 前置补齐合并结果，但未形成正式开窗或 implementation-ready | 部分 | 否 |
| `MODULE_INDEX.md` | L4 | 当前模块索引；已写入 W13 候选任务域、`ST13 / WT13` 模块映射、旧 `STxx_*` 历史参考口径、第一批 contract_refined 模块影响、W13-E13.5 candidate 状态表达策略对 M01/M10 的非放行结论和 W13-E14-Merge 模块影响，但模块同步仍待后续窗口 | 部分 | 否 |
| `DOCUMENT_PROGRESS.md` | L4 | 当前进展摘要 + 历史归档和补链入口 | 部分 | 否 |
| `DOCUMENT_MATURITY.md` | L4 | 当前成熟度摘要 + 历史归档和补链入口 | 部分 | 否 |
| `EXECUTION_LOG.md` | L4 | 历史执行记录 | 部分 | 否 |
| `docs/superpowers/plans/2026-04-25-workbench-mvp-task-remap.md` | L4 | W13-E / W13-E2 任务重映射与状态层 dry-run 草案，包含候选任务树、旧 ST 映射和状态层后续改造方案 | 部分 | 否 |
| `docs/superpowers/plans/2026-04-25-workbench-mvp-doc-state-preview.yaml` | L3 | W13-E3 状态层 preview YAML；已通过 `validate-state` / `evaluate-state` 预检，用于验证 W13 任务别名和旧 ST superseded preview 表达；正式 `documents` 分支因非 governance 路径的 repo_root 解析差异暂不纳入。 | 否 | 否 |
| `docs/superpowers/plans/2026-04-25-workbench-mvp-state-write-plan.md` | L4 | W13-E4-A State Write 分阶段计划，包含 C-Phased 四阶段计划、验证矩阵、回退方案、`ST13_01~ST13_25` 写入草案和确认卡 | 部分 | 否 |
| `docs/superpowers/plans/2026-04-25-workbench-mvp-state-write-stage1.md` | L4 | W13-E4-B State Write 阶段 1 变更与回退说明，记录正式写入、验证结果、旧任务保留和回退步骤 | 部分 | 否 |
| `docs/superpowers/plans/2026-04-25-workbench-mvp-state-write-stage2.md` | L4 | W13-E4-C State Write 阶段 2 变更与回退说明，记录旧任务 facts historical / superseded 写入、完整映射、验证结果和回退步骤 | 部分 | 否 |
| `docs/superpowers/plans/2026-04-25-workbench-mvp-state-write-stage3-dry-run.md` | L4 | W13-E4-D State Write 阶段 3 dry-run 与影响分析，记录旧 ST 引用链、RQ01 task_ids 影响、Preview 方案和正式阶段 3 执行草案 | 部分 | 否 |
| `docs/superpowers/plans/2026-04-25-workbench-mvp-doc-state-stage3-preview.yaml` | L3 | W13-E4-E Stage3 Preview YAML；仅用于验证旧 `STxx_*` 移出与 `RQ01.facts.task_ids` 收敛影响，不是正式状态真值 | 部分 | 否 |
| `docs/superpowers/plans/2026-04-25-workbench-mvp-state-write-stage3.md` | L4 | W13-E4-F State Write 阶段 3 变更与回退说明，记录正式移出旧 `STxx_*`、收敛 `RQ01.facts.task_ids`、验证结果和回退步骤 | 部分 | 否 |
| `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-readiness-audit.md` | L4 | W13-E5 ST13 任务包准备前置审计，记录 `ST13_01~ST13_25` 缺口、依赖、formal window 条件、实现前置依赖、模块映射和用户确认卡 | 部分 | 否 |
| `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-first-contract-task-packages.md` | L4 | W13-E6 第一批 contract 任务包草案，记录 `ST13_21 / ST13_20 / ST13_24 / ST13_25` 的任务目标、输入输出、边界、依赖、验收和测试要求 | 部分 | 否 |
| `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-first-contract-double-doc-plan.md` | L4 | W13-E7 第一批 contract 双文档准备方案，记录四个 ST13 的草案审计、双文档模板、路径方案、前置清单、contract 摘要、父索引同步方案和确认卡 | 部分 | 否 |
| `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-required-doc-slot-update.md` | L4 | W13-E8.5 第一批 ST13 required doc slot State Update 说明，记录状态层登记、验证和回退步骤 | 部分 | 否 |
| `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-first-contract-readiness-review.md` | L4 | W13-E10 第一批 ST13 readiness 复核说明，记录四个 contract_refined 双文档的验收、测试、scope、candidate 判断、State Update 需求和确认卡；不放行实现 | 部分，供 W13-E11 使用 | 否 |
| `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-first-contract-formal-window-candidate-evaluation.md` | L4 | W13-E11 第一批 ST13 formal window candidate 评估说明，吸收 `OQ-114~OQ-117` 用户确认并形成后续 State Update 建议；不放行实现 | 部分，供 State Update 使用 | 否 |
| `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-state-update-plan.md` | L4 | W13-E12 ST13 candidate State Update 准备方案，记录字段影响分析、`ST13_24 / ST13_25` candidate preview 方案、`ST13_21 / ST13_20` near-ready 策略、确认卡、验证矩阵和回退方案；W13-E13.5 已回写原 candidate/downstream 组合不可直接采用 | 部分，供后续修正 Candidate Preview 参考 | 否 |
| `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-candidate-state-preview.yaml` | L2 | W13-E13 ST13 candidate State Update Preview YAML；仅用于验证 `ST13_24 / ST13_25` candidate 字段组合，当前 `validate-state / evaluate-state` 未通过，不是正式状态真值 | 否 | 否 |
| `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-candidate-state-strategy-fix.md` | L4 | W13-E13.5 candidate 状态表达策略修正文档，记录 Preview 失败复盘、规则分析、facts-only / observe / maturity 候选方案、确认卡和不进入实现边界；不写正式状态 | 部分，供下一轮 Candidate Preview 使用 | 否 |
| `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-candidate-state-facts-preview.yaml` | L2 | W13-E13.6 facts-only Candidate Preview YAML；仅用于验证 `ST13_24 / ST13_25` 的 facts-only candidate 推荐字段，`validate-state / evaluate-state` 为 `ok=true,error=0,warning=0`，但完整 Preview `documents_blocked_count=1`；不是正式状态真值 | 部分，供后续确认卡评估 | 否 |
| `docs/governance/previews/DOC_STATE_W13_E13_8_CANDIDATE_FACTS_PREVIEW.yaml` | L2 | W13-E13.8 docs/governance/previews 路径 facts-only Candidate Preview YAML；验证 `ST13_24 / ST13_25` 的 facts-only candidate 推荐字段在路径等价位置下 `validate-state / evaluate-state` 全绿，`documents_blocked_count=0`；不是正式状态真值 | 是，已作为正式 State Update 前置验证证据 | 否 |
| `docs/superpowers/plans/st13-task-packages/ST13_21/ST13_21_DESIGN.md` | L4 | W13-E14-Merge 已复核的 `ST13_21 / WT13-21` API / 后端服务边界设计文档；near-ready blocker、API contract readiness 和升级条件已进一步明确，仍 not implementation-ready | 是，供 formal window 前置确认 | 否 |
| `docs/superpowers/plans/st13-task-packages/ST13_21/ST13_21_IMPLEMENTATION.md` | L4 | W13-E14-Merge 已复核的 `ST13_21 / WT13-21` API / 后端服务边界实施说明；implementation plan only，未来实现窗口约束已更新 | 是，供 formal window 前置确认 | 否 |
| `docs/superpowers/plans/st13-task-packages/ST13_20/ST13_20_DESIGN.md` | L4 | W13-E14-Merge 已复核的 `ST13_20 / WT13-20` 服务端保存 / 数据库设计文档；near-ready blocker、数据 contract readiness 和升级条件已进一步明确，仍 not implementation-ready | 是，供 formal window 前置确认 | 否 |
| `docs/superpowers/plans/st13-task-packages/ST13_20/ST13_20_IMPLEMENTATION.md` | L4 | W13-E14-Merge 已复核的 `ST13_20 / WT13-20` 服务端保存 / 数据库实施说明；implementation plan only，未来实现窗口约束已更新 | 是，供 formal window 前置确认 | 否 |
| `docs/superpowers/plans/st13-task-packages/ST13_24/ST13_24_DESIGN.md` | L4 | W13-E14-Merge 已复核的 `ST13_24 / WT13-24` 测试 / 验收 / DoD 设计文档；acceptance criteria、required tests、scope 和 formal window 前置材料已进一步补齐，但不创建测试代码 | 是，供 formal window 前置确认 | 否 |
| `docs/superpowers/plans/st13-task-packages/ST13_24/ST13_24_IMPLEMENTATION.md` | L4 | W13-E14-Merge 已复核的 `ST13_24 / WT13-24` 测试 / 验收 / DoD 实施说明；implementation plan only，未来测试窗口约束已更新 | 是，供 formal window 前置确认 | 否 |
| `docs/superpowers/plans/st13-task-packages/ST13_25/ST13_25_DESIGN.md` | L4 | W13-E14-Merge 已复核的 `ST13_25 / WT13-25` 文档治理 / 收口 / Basic Memory 设计文档；收口、fallback 和授权边界已进一步补齐，本轮禁止 Basic Memory 写回 | 是，供 formal window 前置确认 | 否 |
| `docs/superpowers/plans/st13-task-packages/ST13_25/ST13_25_IMPLEMENTATION.md` | L4 | W13-E14-Merge 已复核的 `ST13_25 / WT13-25` 文档治理 / 收口 / Basic Memory 实施说明；implementation plan only，未来治理收口窗口约束已更新 | 是，供 formal window 前置确认 | 否 |
| `docs/superpowers/plans/2026-04-25-workbench-mvp-backlog-roadmap.md` | L4 | 项目待办、状态层后续、二期 / 三期和历史归档后续事项追踪清单 | 部分 | 否 |
| `archive/docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md` | L4 | 历史设计稿归档快照 | 部分 | 否 |

## 4. W13 唯一事实源成熟度

| 文档路径 | 当前等级 | 当前角色 | 是否可作为下游输入 |
| --- | --- | --- | --- |
| `docs/superpowers/plans/2026-04-25-workbench-mvp-scope.md` | L5 | 一期 MVP 范围唯一事实源 | 是 |
| `docs/superpowers/plans/2026-04-25-workbench-mvp-ia-user-journey.md` | L5 | IA / 用户旅程唯一事实源 | 是 |
| `docs/superpowers/plans/2026-04-25-workbench-mvp-object-model-rag-multiround-backend.md` | L5 | 对象模型 / RAG / 多轮 / 后端边界唯一事实源 | 是 |
| `docs/superpowers/plans/2026-04-25-workbench-mvp-scoring-review-export-dod.md` | L5 | 评分 / 复盘 / 导出 / DoD 唯一事实源 | 是 |

## 5. 当前模块成熟度摘要

| 模块 | 当前整体成熟度 | 当前判断 | 是否可进入子任务设计 |
| --- | --- | --- | --- |
| M01 | L4 | 接近候选但未接受；不因 FC confirmed 自动升级 | 否 |
| M02 | L4 | `/members` 共享最小层已确认，但正式开窗层仍为空，权限消费边界仍需模块层复核 | 否 |
| M03 | L4 | 已吸收但未放行；正式开窗层为空、当前阶段关窗、上传 / 导出链依赖未变 | 否 |
| M04 | L1 | 骨架级；旧 OQ/MQ 已标记并补链，仍需按 W13 同步匹配分析、评分证据和训练入口 | 否 |
| M05 | L1 | 骨架级；旧 OQ/MQ 已标记并补链，仍需按 W13 同步 RAG / 知识库、资产归档与 schema 边界 | 否 |
| M06 | L1 | 骨架级；旧 OQ/MQ 已标记并补链，仍需按 W13 同步模拟记录列表、多轮、上下文包与面试台边界 | 否 |
| M07 | L1 | 骨架级；旧 OQ/MQ 已标记并补链，仍需按 W13 同步打磨模式、进展树、题级反馈与训练进展 | 否 |
| M08 | L1 | 骨架级；旧 OQ/MQ 已标记并补链，仍需按 W13 同步真实面试复盘、模拟复盘、逐题拆解与导出 | 否 |
| M09 | L1 | 骨架级；旧 OQ/MQ 已标记并补链，仍需按 W13 同步薄弱项、训练抽屉、消减和停练规则 | 否 |
| M10 | L1 | 骨架级；旧 OQ/MQ 已标记并补链，仍需按 W13 同步管理台入口、模型 catalog、snapshot 与运维边界 | 否 |

## 6. 当前可作为下游输入的文档

- `AGENTS.md`
- `docs/DOC_GOVERNANCE.md`
- `PLAN_LATEST.md`
- `OPEN_QUESTIONS.md`
- `DESIGN_DECISIONS.md`
- 四份 W13 唯一事实源文档
- `docs/superpowers/plans/2026-04-25-workbench-mvp-task-remap.md`
- `docs/superpowers/plans/2026-04-25-workbench-mvp-backlog-roadmap.md`
- `docs/superpowers/plans/2026-04-25-workbench-mvp-state-write-plan.md`
- `docs/superpowers/plans/2026-04-25-workbench-mvp-state-write-stage1.md`
- `docs/superpowers/plans/2026-04-25-workbench-mvp-state-write-stage2.md`
- `docs/superpowers/plans/2026-04-25-workbench-mvp-state-write-stage3-dry-run.md`
- `docs/superpowers/plans/2026-04-25-workbench-mvp-doc-state-stage3-preview.yaml`
- `docs/superpowers/plans/2026-04-25-workbench-mvp-state-write-stage3.md`
- `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-readiness-audit.md`
- `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-first-contract-task-packages.md`
- `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-first-contract-double-doc-plan.md`
- `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-required-doc-slot-update.md`
- `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-state-update-plan.md`
- `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-candidate-state-strategy-fix.md`

说明：
- 上述“可作为下游输入”仅表示可用于继续做文档设计、任务重映射和模块同步。
- 这不等于可以直接进入代码实施。
- 当前没有任何模块或子任务被登记为可直接实施。
- W13-E13.8 已完成第一批 `ST13_24 / ST13_25` candidate 推荐的 facts-only 正式状态层写入；该写入只记录推荐事实，不写 `candidate_status=candidate`，不写 `readiness=downstream_ready`，不打开 formal window，25 个 ST13 的 implementation-ready 仍未形成。
- `W13-E` 任务重映射草案、W13-E2 backlog-roadmap、W13-E3 Preview YAML、W13-E4-A State Write 计划、W13-E4-B 阶段 1说明、W13-E4-C 阶段 2说明、W13-E4-D 阶段 3 dry-run、W13-E4-E Stage3 Preview、W13-E4-F 阶段 3正式写入说明、W13-E5 readiness audit、W13-E6 第一批 contract 任务包草案、W13-E7 第一批 contract 双文档准备方案、W13-E8 第一批正式双文档、W13-E8.5 required doc slot update、W13-E9 contract_refined 双文档、W13-E10 readiness review、W13-E11 candidate evaluation、W13-E12 State Update plan、W13-E13 failed preview、W13-E13.5 strategy fix、W13-E13.6 facts-only Preview、W13-E13.8 facts-only State Update 和 W13-E14-Merge formal window 前置补齐合并可作为后续确认卡输入；正式状态层入口仍以 `DOC_STATE.yaml` 中的 `ST13_01~ST13_25` 为准。

## 7. 当前可直接用于实施的子任务

- 暂无。

## 8. 历史归档说明

- W10 首切片、阶段 3 白名单治理、模块最低位压缩、`MR-*` / `RV-*` / `GC-*` 细节均属于历史治理过程。
- 上述历史内容不再作为当前一期 MVP 范围、模块优先级、正式开窗或 implementation readiness 的依据。
- 旧实现计划正文已迁移到 `archive/docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md`；原路径只保留跳转说明。
- 旧 P1 设计稿已迁移到 `archive/docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md`；原路径只保留跳转说明，`DOC_STATE.yaml` 当前 `documents` 受管集合不再登记 `DOC-SPEC-P1`。
- 旧 STxx_* 骨架已从正式 `DOC_STATE.yaml.subtasks` current 容器移出；阶段 1 已写入新 `ST13_*` 任务，阶段 2 已用 facts 表达旧任务 historical / superseded，阶段 3 已正式收敛 current 任务入口。旧 STxx_* 仍通过 `TASK_INDEX.md`、`MODULE_INDEX.md`、阶段说明文档和 Git 历史保留追溯，archive 准备仍需另行确认。
- 需要追溯历史判断时，优先查看 `EXECUTION_LOG.md`、Git 历史和对应模块目录下的 `MODULE_EXECUTION_LOG.md`。

## 9. 下一等级所需动作

1. W13-E14-Merge 已完成 formal window 前置补齐合并；下一轮如继续推进，适合进入 formal window open 确认窗口，但仍不得把 facts-only 推荐或双文档补齐写成 `candidate_status=candidate`、`readiness=downstream_ready`、formal window open 或 implementation-ready。
2. `MODULE_INDEX.md` 需要在模块同步窗口后回写 W13 模块优先级，而不是继续沿用 W10 首切片顺序。
3. `M02` 需要优先修正 API / open_questions 模块 blocker；`M05 / M06 / M08 / M09 / M10` 需要按 confirmed 范围补齐模块级设计，尤其是 RAG、多轮、复盘、训练、资产归档和管理台入口。
4. 旧 `STxx_*` 骨架如需归档，必须另行执行 archive 迁移评估与确认；确认前不直接移动这些文档。
5. 后续 Basic Memory / Superpowers 写回必须另开授权窗口；当前不写 Basic Memory。
6. 正式开窗层写入前，所有子任务仍不得进入 implementation-ready 或代码实施；当前仍不能 formal window open、生成 implementation packet 或进入实现。

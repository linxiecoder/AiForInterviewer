---
title: F0_DUPLICATE_DEPRECATED_CONFLICTS
type: note
permalink: ai-for-interviewer/archive/2026-05-doc-consolidation/audit/f0-duplicate-deprecated-conflicts-1
---

# F0 重复 / 废弃 / 冲突文档识别

## 1. 重复文档

- 完全相同文件组：0。
- 未发现 SHA-256 完全相同的 Markdown/MDX 文件。

- 正文完全重复文件组（去除 YAML front matter 后）：2。
- 28 个文件：`docs/modules/M01-foundation-and-platform/sub_modules/ST01_02-workspace-shell-and-i18n/SUBTASK_IMPLEMENTATION.md`, `docs/modules/M01-foundation-and-platform/sub_modules/ST01_03-testing-logging-and-doc-governance/SUBTASK_IMPLEMENTATION.md`, `docs/modules/M02-identity-and-team/sub_modules/ST02_01-auth-mechanism-boundary/SUBTASK_IMPLEMENTATION.md`, `docs/modules/M02-identity-and-team/sub_modules/ST02_02-team-user-member-domain/SUBTASK_IMPLEMENTATION.md`, `docs/modules/M02-identity-and-team/sub_modules/ST02_03-authorization-matrix/SUBTASK_IMPLEMENTATION.md`, `docs/modules/M03-jobs-resumes-and-documents/sub_modules/ST03_01-job-domain-and-pages/SUBTASK_IMPLEMENTATION.md`, `docs/modules/M03-jobs-resumes-and-documents/sub_modules/ST03_02-resume-domain-versioning-and-editor/SUBTASK_IMPLEMENTATION.md`, `docs/modules/M03-jobs-resumes-and-documents/sub_modules/ST03_03-upload-transform-export/SUBTASK_IMPLEMENTATION.md`, `docs/modules/M04-match-analysis-and-evidence/sub_modules/ST04_01-bindings-and-input-contract/SUBTASK_IMPLEMENTATION.md`, `docs/modules/M04-match-analysis-and-evidence/sub_modules/ST04_02-analysis-scoring-and-evidence/SUBTASK_IMPLEMENTATION.md` ...
- 3 个文件：`docs/modules/M04-match-analysis-and-evidence/MODULE_EXECUTION_LOG.md`, `docs/modules/M05-assets-and-retrieval/MODULE_EXECUTION_LOG.md`, `docs/modules/M06-simulated-interview-and-context/MODULE_EXECUTION_LOG.md`

## 2. 同名多文件

| basename | count | 说明 |
|---|---:|---|
| `SUBTASK_DESIGN.md` | 31 | 模块/子任务模板多份存在；需区分结构复用与内容重复。 |
| `SUBTASK_IMPLEMENTATION.md` | 31 | 模块/子任务模板多份存在；需区分结构复用与内容重复。 |
| `MODULE_DESIGN.md` | 11 | 模块/子任务模板多份存在；需区分结构复用与内容重复。 |
| `MODULE_API_DESIGN.md` | 10 | 模块/子任务模板多份存在；需区分结构复用与内容重复。 |
| `MODULE_DEPENDENCIES.md` | 10 | 模块/子任务模板多份存在；需区分结构复用与内容重复。 |
| `MODULE_EXECUTION_LOG.md` | 10 | 模块/子任务模板多份存在；需区分结构复用与内容重复。 |
| `MODULE_LOGIC_DESIGN.md` | 10 | 模块/子任务模板多份存在；需区分结构复用与内容重复。 |
| `MODULE_OPEN_QUESTIONS.md` | 10 | 模块/子任务模板多份存在；需区分结构复用与内容重复。 |
| `MODULE_REQUIREMENTS.md` | 10 | 模块/子任务模板多份存在；需区分结构复用与内容重复。 |
| `MODULE_SCHEMA_DESIGN.md` | 10 | 模块/子任务模板多份存在；需区分结构复用与内容重复。 |
| `MODULE_TASK_INDEX.md` | 10 | 模块/子任务模板多份存在；需区分结构复用与内容重复。 |
| `README.md` | 6 | 模块/子任务模板多份存在；需区分结构复用与内容重复。 |

## 3. 高占位/模板痕迹文件 Top 80

| path | placeholder_hits | lines | 建议 |
|---|---:|---:|---|
| `archive/docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md` | 392 | 4331 | KEEP_ARCHIVE_EVIDENCE：仅历史来源；如内容仍有效，迁移到 active docs 并登记 traceability |
| `docs/governance/DOC_GOVERNOR_REPORT.md` | 385 | 429 | MIGRATE_TO docs/00-governance/* 或 docs/04-decisions/ADR-* |
| `EXECUTION_LOG.md` | 60 | 2359 | REVIEW：需人工决定目标归属 |
| `docs/SUBTASK_DOC_TEMPLATES.md` | 40 | 469 | REVIEW：需人工决定目标归属 |
| `archive/docs/superpowers/plans/2026-04-25/2026-04-25-workbench-mvp-state-write-plan.md` | 35 | 610 | KEEP_ARCHIVE_EVIDENCE：仅历史来源；如内容仍有效，迁移到 active docs 并登记 traceability |
| `archive/docs/superpowers/plans/2026-04-25/2026-04-25-workbench-mvp-state-write-stage3-dry-run.md` | 29 | 396 | KEEP_ARCHIVE_EVIDENCE：仅历史来源；如内容仍有效，迁移到 active docs 并登记 traceability |
| `docs/governance/DOC_AUTOMATION.md` | 28 | 455 | MIGRATE_TO docs/00-governance/* 或 docs/04-decisions/ADR-* |
| `docs/governance/BOOTSTRAP_REPORT.md` | 20 | 107 | MIGRATE_TO docs/00-governance/* 或 docs/04-decisions/ADR-* |
| `docs/development/database.md` | 18 | 242 | REVIEW：需人工决定目标归属 |
| `docs/modules/M01-foundation-and-platform/MODULE_TASK_INDEX.md` | 18 | 69 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/DOC_GOVERNANCE.md` | 16 | 493 | REVIEW：需人工决定目标归属 |
| `archive/docs/superpowers/plans/2026-04-25/2026-04-25-workbench-mvp-state-write-stage3.md` | 15 | 206 | KEEP_ARCHIVE_EVIDENCE：仅历史来源；如内容仍有效，迁移到 active docs 并登记 traceability |
| `docs/modules/M03-jobs-resumes-and-documents/MODULE_TASK_INDEX.md` | 15 | 112 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/tasks/workbench-mvp/st13-task-packages/ST13_20/ST13_20_DESIGN.md` | 15 | 708 | MIGRATE_TO docs/03-delivery/DELIVERY_PLAN.md / BACKLOG.md；旧路径归档前需 state/source_doc 核查 |
| `archive/docs/superpowers/plans/2026-04-25/2026-04-25-workbench-mvp-st13-first-contract-double-doc-plan.md` | 14 | 414 | KEEP_ARCHIVE_EVIDENCE：仅历史来源；如内容仍有效，迁移到 active docs 并登记 traceability |
| `docs/development/secrets-and-env.md` | 14 | 83 | REVIEW：需人工决定目标归属 |
| `docs/modules/M02-identity-and-team/MODULE_TASK_INDEX.md` | 14 | 101 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/tasks/workbench-mvp/st13-task-packages/ST13_20/ST13_20_IMPLEMENTATION.md` | 14 | 561 | MIGRATE_TO docs/03-delivery/DELIVERY_PLAN.md / BACKLOG.md；旧路径归档前需 state/source_doc 核查 |
| `docs/development/local-startup.md` | 13 | 253 | REVIEW：需人工决定目标归属 |
| `archive/docs/superpowers/plans/2026-04-25/2026-04-25-workbench-mvp-st13-readiness-audit.md` | 12 | 635 | KEEP_ARCHIVE_EVIDENCE：仅历史来源；如内容仍有效，迁移到 active docs 并登记 traceability |
| `archive/docs/superpowers/plans/2026-04-25/2026-04-25-workbench-mvp-st13-state-update-plan.md` | 11 | 512 | KEEP_ARCHIVE_EVIDENCE：仅历史来源；如内容仍有效，迁移到 active docs 并登记 traceability |
| `archive/docs/superpowers/plans/2026-04-27-document-system-refactor-plan.md` | 11 | 448 | KEEP_ARCHIVE_EVIDENCE：仅历史来源；如内容仍有效，迁移到 active docs 并登记 traceability |
| `archive/docs/superpowers/plans/2026-04-25/2026-04-25-workbench-mvp-state-write-stage1.md` | 10 | 146 | KEEP_ARCHIVE_EVIDENCE：仅历史来源；如内容仍有效，迁移到 active docs 并登记 traceability |
| `archive/planning/workbench-mvp/2026-04-25-workbench-mvp-backlog-roadmap.history-2026-05-01.md` | 10 | 169 | KEEP_ARCHIVE_EVIDENCE：仅历史来源；如内容仍有效，迁移到 active docs 并登记 traceability |
| `docs/modules/M01-foundation-and-platform/sub_modules/ST01_01-runtime-and-repo-baseline/SUBTASK_IMPLEMENTATION.md` | 10 | 241 | DEDUP_TEMPLATE_OR_ARCHIVE_AFTER_TRACE：重复子任务模板，若无执行事实则归档/用单一模板替代 |
| `docs/planning/workbench-mvp/2026-04-25-workbench-mvp-backlog-roadmap.md` | 10 | 171 | MIGRATE_TO docs/03-delivery/DELIVERY_PLAN.md / BACKLOG.md；旧路径归档前需 state/source_doc 核查 |
| `AGENTS.md` | 9 | 549 | MIGRATE_REWRITE：保留根入口职责，替换为目标文档体系索引，移除旧推进体系 active 规则 |
| `docs/governance/DOC_GOVERNOR_RUNBOOK.md` | 9 | 486 | MIGRATE_TO docs/00-governance/* 或 docs/04-decisions/ADR-* |
| `archive/docs/superpowers/plans/2026-04-25/2026-04-25-workbench-mvp-state-write-stage2.md` | 8 | 280 | KEEP_ARCHIVE_EVIDENCE：仅历史来源；如内容仍有效，迁移到 active docs 并登记 traceability |
| `docs/governance/packets/ST13_19.implementation.packet.md` | 8 | 95 | ARCHIVE_OR_DELETE_GENERATED_AFTER_POLICY_CHECK：生成产物/packet，需确认 gate/state 无依赖 |
| `docs/modules/M01-foundation-and-platform/MODULE_LOGIC_DESIGN.md` | 8 | 174 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/governance/packets/ST01_01.implementation.packet.md` | 7 | 105 | ARCHIVE_OR_DELETE_GENERATED_AFTER_POLICY_CHECK：生成产物/packet，需确认 gate/state 无依赖 |
| `docs/governance/packets/ST13_12.implementation.packet.md` | 7 | 89 | ARCHIVE_OR_DELETE_GENERATED_AFTER_POLICY_CHECK：生成产物/packet，需确认 gate/state 无依赖 |
| `docs/modules/M01-foundation-and-platform/MODULE_DEPENDENCIES.md` | 7 | 121 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M01-foundation-and-platform/sub_modules/ST01_02-workspace-shell-and-i18n/SUBTASK_IMPLEMENTATION.md` | 7 | 229 | DEDUP_TEMPLATE_OR_ARCHIVE_AFTER_TRACE：重复子任务模板，若无执行事实则归档/用单一模板替代 |
| `docs/modules/M01-foundation-and-platform/sub_modules/ST01_03-testing-logging-and-doc-governance/SUBTASK_IMPLEMENTATION.md` | 7 | 229 | DEDUP_TEMPLATE_OR_ARCHIVE_AFTER_TRACE：重复子任务模板，若无执行事实则归档/用单一模板替代 |
| `docs/modules/M02-identity-and-team/sub_modules/ST02_01-auth-mechanism-boundary/SUBTASK_IMPLEMENTATION.md` | 7 | 229 | DEDUP_TEMPLATE_OR_ARCHIVE_AFTER_TRACE：重复子任务模板，若无执行事实则归档/用单一模板替代 |
| `docs/modules/M02-identity-and-team/sub_modules/ST02_02-team-user-member-domain/SUBTASK_IMPLEMENTATION.md` | 7 | 229 | DEDUP_TEMPLATE_OR_ARCHIVE_AFTER_TRACE：重复子任务模板，若无执行事实则归档/用单一模板替代 |
| `docs/modules/M02-identity-and-team/sub_modules/ST02_03-authorization-matrix/SUBTASK_IMPLEMENTATION.md` | 7 | 229 | DEDUP_TEMPLATE_OR_ARCHIVE_AFTER_TRACE：重复子任务模板，若无执行事实则归档/用单一模板替代 |
| `docs/modules/M03-jobs-resumes-and-documents/sub_modules/ST03_01-job-domain-and-pages/SUBTASK_IMPLEMENTATION.md` | 7 | 229 | DEDUP_TEMPLATE_OR_ARCHIVE_AFTER_TRACE：重复子任务模板，若无执行事实则归档/用单一模板替代 |
| `docs/modules/M03-jobs-resumes-and-documents/sub_modules/ST03_02-resume-domain-versioning-and-editor/SUBTASK_IMPLEMENTATION.md` | 7 | 229 | DEDUP_TEMPLATE_OR_ARCHIVE_AFTER_TRACE：重复子任务模板，若无执行事实则归档/用单一模板替代 |
| `docs/modules/M03-jobs-resumes-and-documents/sub_modules/ST03_03-upload-transform-export/SUBTASK_IMPLEMENTATION.md` | 7 | 229 | DEDUP_TEMPLATE_OR_ARCHIVE_AFTER_TRACE：重复子任务模板，若无执行事实则归档/用单一模板替代 |
| `docs/modules/M04-match-analysis-and-evidence/sub_modules/ST04_01-bindings-and-input-contract/SUBTASK_IMPLEMENTATION.md` | 7 | 229 | DEDUP_TEMPLATE_OR_ARCHIVE_AFTER_TRACE：重复子任务模板，若无执行事实则归档/用单一模板替代 |
| `docs/modules/M04-match-analysis-and-evidence/sub_modules/ST04_02-analysis-scoring-and-evidence/SUBTASK_IMPLEMENTATION.md` | 7 | 229 | DEDUP_TEMPLATE_OR_ARCHIVE_AFTER_TRACE：重复子任务模板，若无执行事实则归档/用单一模板替代 |
| `docs/modules/M04-match-analysis-and-evidence/sub_modules/ST04_03-analysis-ui-and-training-entry/SUBTASK_IMPLEMENTATION.md` | 7 | 229 | DEDUP_TEMPLATE_OR_ARCHIVE_AFTER_TRACE：重复子任务模板，若无执行事实则归档/用单一模板替代 |
| `docs/modules/M05-assets-and-retrieval/sub_modules/ST05_01-asset-type-and-asset-domain/SUBTASK_IMPLEMENTATION.md` | 7 | 229 | DEDUP_TEMPLATE_OR_ARCHIVE_AFTER_TRACE：重复子任务模板，若无执行事实则归档/用单一模板替代 |
| `docs/modules/M05-assets-and-retrieval/sub_modules/ST05_02-archive-records-and-source-linkage/SUBTASK_IMPLEMENTATION.md` | 7 | 229 | DEDUP_TEMPLATE_OR_ARCHIVE_AFTER_TRACE：重复子任务模板，若无执行事实则归档/用单一模板替代 |
| `docs/modules/M05-assets-and-retrieval/sub_modules/ST05_03-retrieval-chunking-and-index-ingestion/SUBTASK_IMPLEMENTATION.md` | 7 | 229 | DEDUP_TEMPLATE_OR_ARCHIVE_AFTER_TRACE：重复子任务模板，若无执行事实则归档/用单一模板替代 |
| `docs/modules/M06-simulated-interview-and-context/sub_modules/ST06_01-interview-session-bootstrap/SUBTASK_IMPLEMENTATION.md` | 7 | 229 | DEDUP_TEMPLATE_OR_ARCHIVE_AFTER_TRACE：重复子任务模板，若无执行事实则归档/用单一模板替代 |
| `docs/modules/M06-simulated-interview-and-context/sub_modules/ST06_02-context-pack-and-question-source/SUBTASK_IMPLEMENTATION.md` | 7 | 229 | DEDUP_TEMPLATE_OR_ARCHIVE_AFTER_TRACE：重复子任务模板，若无执行事实则归档/用单一模板替代 |
| `docs/modules/M06-simulated-interview-and-context/sub_modules/ST06_03-message-trace-report-and-export/SUBTASK_IMPLEMENTATION.md` | 7 | 229 | DEDUP_TEMPLATE_OR_ARCHIVE_AFTER_TRACE：重复子任务模板，若无执行事实则归档/用单一模板替代 |
| `docs/modules/M07-polish-assessment-and-progress/sub_modules/ST07_01-practice-topic-recommendation/SUBTASK_IMPLEMENTATION.md` | 7 | 229 | DEDUP_TEMPLATE_OR_ARCHIVE_AFTER_TRACE：重复子任务模板，若无执行事实则归档/用单一模板替代 |
| `docs/modules/M07-polish-assessment-and-progress/sub_modules/ST07_02-capability-tree-and-node-state/SUBTASK_IMPLEMENTATION.md` | 7 | 229 | DEDUP_TEMPLATE_OR_ARCHIVE_AFTER_TRACE：重复子任务模板，若无执行事实则归档/用单一模板替代 |
| `docs/modules/M07-polish-assessment-and-progress/sub_modules/ST07_03-assessment-and-progress/SUBTASK_IMPLEMENTATION.md` | 7 | 229 | DEDUP_TEMPLATE_OR_ARCHIVE_AFTER_TRACE：重复子任务模板，若无执行事实则归档/用单一模板替代 |
| `docs/modules/M08-review-and-replay/sub_modules/ST08_01-review-aggregate/SUBTASK_IMPLEMENTATION.md` | 7 | 229 | DEDUP_TEMPLATE_OR_ARCHIVE_AFTER_TRACE：重复子任务模板，若无执行事实则归档/用单一模板替代 |
| `docs/modules/M08-review-and-replay/sub_modules/ST08_02-real-interview-intake/SUBTASK_IMPLEMENTATION.md` | 7 | 229 | DEDUP_TEMPLATE_OR_ARCHIVE_AFTER_TRACE：重复子任务模板，若无执行事实则归档/用单一模板替代 |
| `docs/modules/M08-review-and-replay/sub_modules/ST08_03-simulated-review-replay/SUBTASK_IMPLEMENTATION.md` | 7 | 229 | DEDUP_TEMPLATE_OR_ARCHIVE_AFTER_TRACE：重复子任务模板，若无执行事实则归档/用单一模板替代 |
| `docs/modules/M09-training-and-weakness-lifecycle/sub_modules/ST09_01-weakness-aggregation/SUBTASK_IMPLEMENTATION.md` | 7 | 229 | DEDUP_TEMPLATE_OR_ARCHIVE_AFTER_TRACE：重复子任务模板，若无执行事实则归档/用单一模板替代 |
| `docs/modules/M09-training-and-weakness-lifecycle/sub_modules/ST09_02-training-drawer-and-intake/SUBTASK_IMPLEMENTATION.md` | 7 | 229 | DEDUP_TEMPLATE_OR_ARCHIVE_AFTER_TRACE：重复子任务模板，若无执行事实则归档/用单一模板替代 |
| `docs/modules/M10-admin-governance-and-observability/sub_modules/ST10_01-admin-member-and-role-ops/SUBTASK_IMPLEMENTATION.md` | 7 | 229 | DEDUP_TEMPLATE_OR_ARCHIVE_AFTER_TRACE：重复子任务模板，若无执行事实则归档/用单一模板替代 |
| `docs/modules/M10-admin-governance-and-observability/sub_modules/ST10_02-models-rules-and-settings/SUBTASK_IMPLEMENTATION.md` | 7 | 229 | DEDUP_TEMPLATE_OR_ARCHIVE_AFTER_TRACE：重复子任务模板，若无执行事实则归档/用单一模板替代 |
| `docs/modules/M10-admin-governance-and-observability/sub_modules/ST10_03-observability-ci-and-snapshot-ops/SUBTASK_IMPLEMENTATION.md` | 7 | 229 | DEDUP_TEMPLATE_OR_ARCHIVE_AFTER_TRACE：重复子任务模板，若无执行事实则归档/用单一模板替代 |
| `docs/tasks/workbench-mvp/st13-task-packages/ST13_12/ST13_12_IMPLEMENTATION.md` | 7 | 104 | MIGRATE_TO docs/03-delivery/DELIVERY_PLAN.md / BACKLOG.md；旧路径归档前需 state/source_doc 核查 |
| `docs/tasks/workbench-mvp/st13-task-packages/ST13_19/ST13_19_IMPLEMENTATION.md` | 7 | 107 | MIGRATE_TO docs/03-delivery/DELIVERY_PLAN.md / BACKLOG.md；旧路径归档前需 state/source_doc 核查 |
| `docs/governance/packets/ST13_13.implementation.packet.md` | 6 | 112 | ARCHIVE_OR_DELETE_GENERATED_AFTER_POLICY_CHECK：生成产物/packet，需确认 gate/state 无依赖 |
| `docs/governance/packets/ST13_15.implementation.packet.md` | 6 | 115 | ARCHIVE_OR_DELETE_GENERATED_AFTER_POLICY_CHECK：生成产物/packet，需确认 gate/state 无依赖 |
| `docs/modules/M01-foundation-and-platform/MODULE_API_DESIGN.md` | 6 | 245 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `archive/docs/superpowers/plans/2026-04-25/2026-04-25-workbench-mvp-st13-required-doc-slot-update.md` | 5 | 154 | KEEP_ARCHIVE_EVIDENCE：仅历史来源；如内容仍有效，迁移到 active docs 并登记 traceability |
| `docs/modules/M01-foundation-and-platform/MODULE_SCHEMA_DESIGN.md` | 5 | 188 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M01-foundation-and-platform/sub_modules/ST01_01-runtime-and-repo-baseline/SUBTASK_DESIGN.md` | 5 | 235 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/tasks/workbench-mvp/st13-task-packages/ST13_11/ST13_11_IMPLEMENTATION.md` | 5 | 147 | MIGRATE_TO docs/03-delivery/DELIVERY_PLAN.md / BACKLOG.md；旧路径归档前需 state/source_doc 核查 |
| `docs/tasks/workbench-mvp/st13-task-packages/ST13_13/ST13_13_IMPLEMENTATION.md` | 5 | 126 | MIGRATE_TO docs/03-delivery/DELIVERY_PLAN.md / BACKLOG.md；旧路径归档前需 state/source_doc 核查 |
| `docs/tasks/workbench-mvp/st13-task-packages/ST13_15/ST13_15_IMPLEMENTATION.md` | 5 | 128 | MIGRATE_TO docs/03-delivery/DELIVERY_PLAN.md / BACKLOG.md；旧路径归档前需 state/source_doc 核查 |
| `docs/tasks/workbench-mvp/st13-task-packages/ST13_21/ST13_21_DESIGN.md` | 5 | 477 | MIGRATE_TO docs/03-delivery/DELIVERY_PLAN.md / BACKLOG.md；旧路径归档前需 state/source_doc 核查 |
| `TECHNICAL_STANDARDS.md` | 4 | 170 | MIGRATE：拆分到 docs/02-design/TECH_DESIGN.md 与 docs/04-decisions/ADR-* |
| `docs/governance/DISCUSSION_WORKFLOW.md` | 4 | 349 | MIGRATE_TO docs/00-governance/* 或 docs/04-decisions/ADR-* |
| `docs/governance/packets/ST13_11.implementation.packet.md` | 4 | 96 | ARCHIVE_OR_DELETE_GENERATED_AFTER_POLICY_CHECK：生成产物/packet，需确认 gate/state 无依赖 |
| `docs/governance/packets/ST13_20.implementation.packet.md` | 4 | 134 | ARCHIVE_OR_DELETE_GENERATED_AFTER_POLICY_CHECK：生成产物/packet，需确认 gate/state 无依赖 |
| `docs/modules/M02-identity-and-team/MODULE_EXECUTION_LOG.md` | 4 | 565 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M04-match-analysis-and-evidence/MODULE_TASK_INDEX.md` | 4 | 29 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |

## 4. 旧推进体系冲突

- 非 archive/test 的 Markdown/MDX 中，含旧推进体系词的文件数：183 / 224。
- 这些文件不得继续作为 active 阶段/任务体系来源；有效内容必须迁入 F0-F8、M0-M8、AIFI-* 体系。

| path | legacy_terms | R | P | W13 | ST | 建议 |
|---|---:|---:|---:|---:|---:|---|
| `EXECUTION_LOG.md` | 510 | 19 | 43 | 226 | 222 | REVIEW：需人工决定目标归属 |
| `docs/governance/DOC_GOVERNOR_REPORT.md` | 410 | 0 | 0 | 0 | 410 | MIGRATE_TO docs/00-governance/* 或 docs/04-decisions/ADR-* |
| `docs/planning/workbench-mvp/2026-04-25-workbench-mvp-backlog-roadmap.md` | 383 | 60 | 4 | 231 | 88 | MIGRATE_TO docs/03-delivery/DELIVERY_PLAN.md / BACKLOG.md；旧路径归档前需 state/source_doc 核查 |
| `docs/design/workbench-mvp/r1-penpot-lowfi-spec.md` | 236 | 236 | 0 | 0 | 0 | MIGRATE_TO docs/02-design/*；移除旧阶段标签，保留设计事实 |
| `docs/tasks/workbench-mvp/st13-task-packages/ST13_20/ST13_20_DESIGN.md` | 167 | 46 | 2 | 19 | 100 | MIGRATE_TO docs/03-delivery/DELIVERY_PLAN.md / BACKLOG.md；旧路径归档前需 state/source_doc 核查 |
| `docs/tasks/workbench-mvp/st13-task-packages/ST13_20/ST13_20_IMPLEMENTATION.md` | 119 | 40 | 0 | 9 | 70 | MIGRATE_TO docs/03-delivery/DELIVERY_PLAN.md / BACKLOG.md；旧路径归档前需 state/source_doc 核查 |
| `docs/tasks/workbench-mvp/st13-task-packages/ST13_21/ST13_21_DESIGN.md` | 109 | 68 | 0 | 0 | 41 | MIGRATE_TO docs/03-delivery/DELIVERY_PLAN.md / BACKLOG.md；旧路径归档前需 state/source_doc 核查 |
| `docs/tasks/workbench-mvp/st13-task-packages/ST13_25/ST13_25_DESIGN.md` | 96 | 0 | 0 | 46 | 50 | MIGRATE_TO docs/03-delivery/DELIVERY_PLAN.md / BACKLOG.md；旧路径归档前需 state/source_doc 核查 |
| `docs/tasks/workbench-mvp/st13-task-packages/ST13_24/ST13_24_DESIGN.md` | 73 | 0 | 8 | 21 | 44 | MIGRATE_TO docs/03-delivery/DELIVERY_PLAN.md / BACKLOG.md；旧路径归档前需 state/source_doc 核查 |
| `AGENTS.md` | 67 | 55 | 0 | 0 | 12 | MIGRATE_REWRITE：保留根入口职责，替换为目标文档体系索引，移除旧推进体系 active 规则 |
| `docs/governance/BOOTSTRAP_REPORT.md` | 67 | 0 | 0 | 0 | 67 | MIGRATE_TO docs/00-governance/* 或 docs/04-decisions/ADR-* |
| `docs/tasks/workbench-mvp/st13-task-packages/ST13_10/ST13_10_DESIGN.md` | 67 | 40 | 0 | 0 | 27 | MIGRATE_TO docs/03-delivery/DELIVERY_PLAN.md / BACKLOG.md；旧路径归档前需 state/source_doc 核查 |
| `docs/governance/DOC_GOVERNOR_TOOL_DEBT.md` | 64 | 0 | 52 | 8 | 4 | MIGRATE_TO docs/00-governance/* 或 docs/04-decisions/ADR-* |
| `docs/tasks/workbench-mvp/st13-task-packages/ST13_21/ST13_21_IMPLEMENTATION.md` | 61 | 34 | 0 | 0 | 27 | MIGRATE_TO docs/03-delivery/DELIVERY_PLAN.md / BACKLOG.md；旧路径归档前需 state/source_doc 核查 |
| `docs/planning/workbench-mvp/2026-05-01-r-stage-mapping.md` | 53 | 36 | 9 | 6 | 2 | MIGRATE_TO docs/03-delivery/DELIVERY_PLAN.md / BACKLOG.md；旧路径归档前需 state/source_doc 核查 |
| `docs/modules/M01-foundation-and-platform/MODULE_TASK_INDEX.md` | 48 | 1 | 0 | 0 | 47 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M03-jobs-resumes-and-documents/MODULE_TASK_INDEX.md` | 41 | 0 | 0 | 0 | 41 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M01-foundation-and-platform/MODULE_DEPENDENCIES.md` | 39 | 1 | 0 | 0 | 38 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/tasks/workbench-mvp/st13-task-packages/ST13_10/ST13_10_IMPLEMENTATION.md` | 39 | 15 | 0 | 0 | 24 | MIGRATE_TO docs/03-delivery/DELIVERY_PLAN.md / BACKLOG.md；旧路径归档前需 state/source_doc 核查 |
| `docs/planning/workbench-mvp/MASTER_IMPLEMENTATION_PLAN.md` | 38 | 38 | 0 | 0 | 0 | MIGRATE_TO docs/03-delivery/DELIVERY_PLAN.md / BACKLOG.md；旧路径归档前需 state/source_doc 核查 |
| `docs/modules/M02-identity-and-team/MODULE_TASK_INDEX.md` | 37 | 0 | 0 | 0 | 37 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/tasks/workbench-mvp/st13-task-packages/ST13_12/ST13_12_DESIGN.md` | 37 | 10 | 0 | 0 | 27 | MIGRATE_TO docs/03-delivery/DELIVERY_PLAN.md / BACKLOG.md；旧路径归档前需 state/source_doc 核查 |
| `docs/tasks/workbench-mvp/st13-task-packages/ST13_24/ST13_24_IMPLEMENTATION.md` | 37 | 0 | 4 | 9 | 24 | MIGRATE_TO docs/03-delivery/DELIVERY_PLAN.md / BACKLOG.md；旧路径归档前需 state/source_doc 核查 |
| `TASK_INDEX.md` | 34 | 10 | 4 | 2 | 18 | SUPERSEDE_AFTER_MIGRATION：内容迁入 docs/03-delivery 后再标记废弃；需先核查 state/source_doc 绑定 |
| `docs/tasks/workbench-mvp/st13-task-packages/ST13_13/ST13_13_DESIGN.md` | 32 | 8 | 0 | 0 | 24 | MIGRATE_TO docs/03-delivery/DELIVERY_PLAN.md / BACKLOG.md；旧路径归档前需 state/source_doc 核查 |
| `docs/modules/M01-foundation-and-platform/sub_modules/ST01_01-runtime-and-repo-baseline/SUBTASK_DESIGN.md` | 30 | 0 | 0 | 0 | 30 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M01-foundation-and-platform/sub_modules/ST01_01-runtime-and-repo-baseline/SUBTASK_IMPLEMENTATION.md` | 30 | 0 | 0 | 0 | 30 | DEDUP_TEMPLATE_OR_ARCHIVE_AFTER_TRACE：重复子任务模板，若无执行事实则归档/用单一模板替代 |
| `docs/tasks/workbench-mvp/st13-task-packages/ST13_15/ST13_15_DESIGN.md` | 28 | 7 | 0 | 0 | 21 | MIGRATE_TO docs/03-delivery/DELIVERY_PLAN.md / BACKLOG.md；旧路径归档前需 state/source_doc 核查 |
| `docs/tasks/workbench-mvp/st13-task-packages/ST13_19/ST13_19_DESIGN.md` | 26 | 8 | 0 | 0 | 18 | MIGRATE_TO docs/03-delivery/DELIVERY_PLAN.md / BACKLOG.md；旧路径归档前需 state/source_doc 核查 |
| `docs/modules/M03-jobs-resumes-and-documents/MODULE_OPEN_QUESTIONS.md` | 25 | 0 | 9 | 0 | 16 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/tasks/workbench-mvp/st13-task-packages/ST13_25/ST13_25_IMPLEMENTATION.md` | 25 | 0 | 0 | 13 | 12 | MIGRATE_TO docs/03-delivery/DELIVERY_PLAN.md / BACKLOG.md；旧路径归档前需 state/source_doc 核查 |
| `docs/governance/packets/ST13_20.implementation.packet.md` | 23 | 5 | 0 | 0 | 18 | ARCHIVE_OR_DELETE_GENERATED_AFTER_POLICY_CHECK：生成产物/packet，需确认 gate/state 无依赖 |
| `docs/modules/M02-identity-and-team/MODULE_OPEN_QUESTIONS.md` | 23 | 3 | 0 | 0 | 20 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/governance/packets/ST13_10.implementation.packet.md` | 22 | 5 | 0 | 0 | 17 | ARCHIVE_OR_DELETE_GENERATED_AFTER_POLICY_CHECK：生成产物/packet，需确认 gate/state 无依赖 |
| `docs/modules/M01-foundation-and-platform/MODULE_OPEN_QUESTIONS.md` | 22 | 0 | 7 | 0 | 15 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/governance/packets/ST13_13.implementation.packet.md` | 21 | 3 | 0 | 0 | 18 | ARCHIVE_OR_DELETE_GENERATED_AFTER_POLICY_CHECK：生成产物/packet，需确认 gate/state 无依赖 |
| `docs/governance/packets/ST13_19.implementation.packet.md` | 21 | 3 | 0 | 0 | 18 | ARCHIVE_OR_DELETE_GENERATED_AFTER_POLICY_CHECK：生成产物/packet，需确认 gate/state 无依赖 |
| `docs/governance/packets/ST13_15.implementation.packet.md` | 20 | 3 | 0 | 0 | 17 | ARCHIVE_OR_DELETE_GENERATED_AFTER_POLICY_CHECK：生成产物/packet，需确认 gate/state 无依赖 |
| `docs/modules/M02-identity-and-team/MODULE_API_DESIGN.md` | 20 | 12 | 0 | 0 | 8 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/governance/packets/ST13_12.implementation.packet.md` | 18 | 1 | 0 | 0 | 17 | ARCHIVE_OR_DELETE_GENERATED_AFTER_POLICY_CHECK：生成产物/packet，需确认 gate/state 无依赖 |
| `docs/modules/M02-identity-and-team/MODULE_EXECUTION_LOG.md` | 18 | 0 | 0 | 0 | 18 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M03-jobs-resumes-and-documents/MODULE_REQUIREMENTS.md` | 18 | 4 | 14 | 0 | 0 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/tasks/workbench-mvp/st13-task-packages/ST13_12/ST13_12_IMPLEMENTATION.md` | 18 | 3 | 0 | 0 | 15 | MIGRATE_TO docs/03-delivery/DELIVERY_PLAN.md / BACKLOG.md；旧路径归档前需 state/source_doc 核查 |
| `docs/tasks/workbench-mvp/st13-task-packages/ST13_13/ST13_13_IMPLEMENTATION.md` | 18 | 4 | 0 | 0 | 14 | MIGRATE_TO docs/03-delivery/DELIVERY_PLAN.md / BACKLOG.md；旧路径归档前需 state/source_doc 核查 |
| `docs/tasks/workbench-mvp/st13-task-packages/ST13_19/ST13_19_IMPLEMENTATION.md` | 18 | 4 | 0 | 0 | 14 | MIGRATE_TO docs/03-delivery/DELIVERY_PLAN.md / BACKLOG.md；旧路径归档前需 state/source_doc 核查 |
| `docs/development/database.md` | 17 | 17 | 0 | 0 | 0 | REVIEW：需人工决定目标归属 |
| `docs/modules/M03-jobs-resumes-and-documents/MODULE_DESIGN.md` | 17 | 2 | 0 | 0 | 15 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/tasks/workbench-mvp/st13-task-packages/ST13_15/ST13_15_IMPLEMENTATION.md` | 17 | 4 | 0 | 0 | 13 | MIGRATE_TO docs/03-delivery/DELIVERY_PLAN.md / BACKLOG.md；旧路径归档前需 state/source_doc 核查 |
| `docs/governance/packets/ST01_01.implementation.packet.md` | 16 | 0 | 0 | 0 | 16 | ARCHIVE_OR_DELETE_GENERATED_AFTER_POLICY_CHECK：生成产物/packet，需确认 gate/state 无依赖 |
| `docs/tasks/workbench-mvp/st13-task-packages/ST13_11/ST13_11_IMPLEMENTATION.md` | 16 | 2 | 0 | 0 | 14 | MIGRATE_TO docs/03-delivery/DELIVERY_PLAN.md / BACKLOG.md；旧路径归档前需 state/source_doc 核查 |
| `docs/governance/packets/ST13_21.implementation.packet.md` | 14 | 3 | 0 | 0 | 11 | ARCHIVE_OR_DELETE_GENERATED_AFTER_POLICY_CHECK：生成产物/packet，需确认 gate/state 无依赖 |
| `docs/planning/workbench-mvp/README.md` | 14 | 9 | 4 | 1 | 0 | MIGRATE_TO docs/03-delivery/DELIVERY_PLAN.md / BACKLOG.md；旧路径归档前需 state/source_doc 核查 |
| `docs/development/r1-trusted-trace-ui-compliance.md` | 13 | 13 | 0 | 0 | 0 | REVIEW：需人工决定目标归属 |
| `docs/governance/STATE_BOUND_MIGRATION_PLAN.md` | 13 | 4 | 1 | 0 | 8 | MIGRATE_TO docs/00-governance/* 或 docs/04-decisions/ADR-* |
| `docs/governance/packets/ST13_11.implementation.packet.md` | 13 | 1 | 0 | 0 | 12 | ARCHIVE_OR_DELETE_GENERATED_AFTER_POLICY_CHECK：生成产物/packet，需确认 gate/state 无依赖 |
| `docs/modules/M01-foundation-and-platform/MODULE_REQUIREMENTS.md` | 13 | 1 | 12 | 0 | 0 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M02-identity-and-team/MODULE_DEPENDENCIES.md` | 13 | 0 | 0 | 0 | 13 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `PLAN_LATEST.md` | 12 | 11 | 0 | 0 | 1 | SUPERSEDE_AFTER_MIGRATION：内容迁入 docs/03-delivery 后再标记废弃；需先核查 state/source_doc 绑定 |
| `docs/modules/M02-identity-and-team/MODULE_DESIGN.md` | 12 | 0 | 3 | 0 | 9 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M02-identity-and-team/MODULE_REQUIREMENTS.md` | 12 | 0 | 10 | 0 | 2 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M06-simulated-interview-and-context/MODULE_REQUIREMENTS.md` | 12 | 0 | 12 | 0 | 0 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M03-jobs-resumes-and-documents/MODULE_EXECUTION_LOG.md` | 11 | 0 | 0 | 0 | 11 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M05-assets-and-retrieval/MODULE_REQUIREMENTS.md` | 11 | 0 | 11 | 0 | 0 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/tasks/workbench-mvp/2026-04-25-workbench-mvp-task-remap.md` | 11 | 0 | 0 | 0 | 11 | MIGRATE_TO docs/03-delivery/DELIVERY_PLAN.md / BACKLOG.md；旧路径归档前需 state/source_doc 核查 |
| `docs/modules/M03-jobs-resumes-and-documents/MODULE_DEPENDENCIES.md` | 10 | 1 | 0 | 0 | 9 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M07-polish-assessment-and-progress/MODULE_REQUIREMENTS.md` | 10 | 0 | 10 | 0 | 0 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M10-admin-governance-and-observability/MODULE_REQUIREMENTS.md` | 10 | 0 | 10 | 0 | 0 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/tasks/workbench-mvp/st13-task-packages/ST13_11/ST13_11_DESIGN.md` | 10 | 5 | 0 | 0 | 5 | MIGRATE_TO docs/03-delivery/DELIVERY_PLAN.md / BACKLOG.md；旧路径归档前需 state/source_doc 核查 |
| `docs/modules/M07-polish-assessment-and-progress/MODULE_TASK_INDEX.md` | 9 | 0 | 0 | 0 | 9 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M08-review-and-replay/MODULE_TASK_INDEX.md` | 9 | 0 | 0 | 0 | 9 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M09-training-and-weakness-lifecycle/MODULE_REQUIREMENTS.md` | 9 | 0 | 9 | 0 | 0 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M09-training-and-weakness-lifecycle/MODULE_TASK_INDEX.md` | 9 | 0 | 0 | 0 | 9 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M10-admin-governance-and-observability/MODULE_TASK_INDEX.md` | 9 | 0 | 0 | 0 | 9 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M04-match-analysis-and-evidence/MODULE_REQUIREMENTS.md` | 8 | 0 | 8 | 0 | 0 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M08-review-and-replay/MODULE_REQUIREMENTS.md` | 8 | 0 | 8 | 0 | 0 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `README.md` | 7 | 7 | 0 | 0 | 0 | MIGRATE_REWRITE：保留根入口职责，替换为目标文档体系索引，移除旧推进体系 active 规则 |
| `docs/governance/DOC_AUTOMATION.md` | 7 | 3 | 3 | 1 | 0 | MIGRATE_TO docs/00-governance/* 或 docs/04-decisions/ADR-* |
| `docs/modules/M02-identity-and-team/MODULE_SCHEMA_DESIGN.md` | 6 | 0 | 6 | 0 | 0 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M04-match-analysis-and-evidence/MODULE_DESIGN.md` | 6 | 0 | 0 | 0 | 6 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M04-match-analysis-and-evidence/MODULE_TASK_INDEX.md` | 6 | 0 | 0 | 0 | 6 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M05-assets-and-retrieval/MODULE_DESIGN.md` | 6 | 0 | 0 | 0 | 6 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M05-assets-and-retrieval/MODULE_TASK_INDEX.md` | 6 | 0 | 0 | 0 | 6 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M06-simulated-interview-and-context/MODULE_DESIGN.md` | 6 | 0 | 0 | 0 | 6 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M06-simulated-interview-and-context/MODULE_TASK_INDEX.md` | 6 | 0 | 0 | 0 | 6 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M07-polish-assessment-and-progress/MODULE_DESIGN.md` | 6 | 0 | 0 | 0 | 6 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M08-review-and-replay/MODULE_DESIGN.md` | 6 | 0 | 0 | 0 | 6 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M09-training-and-weakness-lifecycle/MODULE_DESIGN.md` | 6 | 0 | 0 | 0 | 6 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M10-admin-governance-and-observability/MODULE_DESIGN.md` | 6 | 0 | 0 | 0 | 6 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/development/local-startup.md` | 5 | 5 | 0 | 0 | 0 | REVIEW：需人工决定目标归属 |
| `docs/modules/M01-foundation-and-platform/MODULE_API_DESIGN.md` | 5 | 2 | 0 | 0 | 3 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M02-identity-and-team/MODULE_LOGIC_DESIGN.md` | 5 | 0 | 5 | 0 | 0 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M06-simulated-interview-and-context/MODULE_OPEN_QUESTIONS.md` | 5 | 0 | 0 | 0 | 5 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/planning/2026-04-25-current-repo-execution-plan.md` | 5 | 0 | 2 | 0 | 3 | MIGRATE_TO docs/03-delivery/DELIVERY_PLAN.md / BACKLOG.md；旧路径归档前需 state/source_doc 核查 |
| `docs/SUBTASK_DOC_TEMPLATES.md` | 4 | 0 | 2 | 0 | 2 | REVIEW：需人工决定目标归属 |
| `docs/governance/DOC_GOVERNOR_RUNBOOK.md` | 4 | 0 | 3 | 0 | 1 | MIGRATE_TO docs/00-governance/* 或 docs/04-decisions/ADR-* |
| `docs/modules/M03-jobs-resumes-and-documents/MODULE_LOGIC_DESIGN.md` | 4 | 2 | 0 | 0 | 2 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `TECHNICAL_STANDARDS.md` | 3 | 3 | 0 | 0 | 0 | MIGRATE：拆分到 docs/02-design/TECH_DESIGN.md 与 docs/04-decisions/ADR-* |
| `docs/design/workbench-mvp/README.md` | 3 | 3 | 0 | 0 | 0 | MIGRATE_TO docs/02-design/*；移除旧阶段标签，保留设计事实 |
| `docs/governance/ACTIVE_DOC_CANON.md` | 3 | 3 | 0 | 0 | 0 | MIGRATE_TO docs/00-governance/* 或 docs/04-decisions/ADR-* |
| `docs/governance/DISCUSSION_WORKFLOW.md` | 3 | 0 | 2 | 0 | 1 | MIGRATE_TO docs/00-governance/* 或 docs/04-decisions/ADR-* |
| `docs/modules/M01-foundation-and-platform/MODULE_DESIGN.md` | 3 | 0 | 0 | 0 | 3 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M01-foundation-and-platform/MODULE_EXECUTION_LOG.md` | 3 | 0 | 0 | 0 | 3 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M02-identity-and-team/sub_modules/ST02_01-auth-mechanism-boundary/SUBTASK_DESIGN.md` | 3 | 0 | 2 | 0 | 1 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M02-identity-and-team/sub_modules/ST02_03-authorization-matrix/SUBTASK_DESIGN.md` | 3 | 0 | 2 | 0 | 1 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M03-jobs-resumes-and-documents/MODULE_API_DESIGN.md` | 3 | 0 | 0 | 0 | 3 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M03-jobs-resumes-and-documents/MODULE_SCHEMA_DESIGN.md` | 3 | 0 | 0 | 0 | 3 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M04-match-analysis-and-evidence/MODULE_DEPENDENCIES.md` | 3 | 0 | 0 | 0 | 3 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M05-assets-and-retrieval/MODULE_DEPENDENCIES.md` | 3 | 0 | 0 | 0 | 3 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M06-simulated-interview-and-context/MODULE_DEPENDENCIES.md` | 3 | 0 | 0 | 0 | 3 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M07-polish-assessment-and-progress/MODULE_DEPENDENCIES.md` | 3 | 0 | 0 | 0 | 3 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M07-polish-assessment-and-progress/MODULE_EXECUTION_LOG.md` | 3 | 0 | 0 | 3 | 0 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M08-review-and-replay/MODULE_DEPENDENCIES.md` | 3 | 0 | 0 | 0 | 3 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M08-review-and-replay/MODULE_EXECUTION_LOG.md` | 3 | 0 | 0 | 3 | 0 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M09-training-and-weakness-lifecycle/MODULE_DEPENDENCIES.md` | 3 | 0 | 0 | 0 | 3 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M09-training-and-weakness-lifecycle/MODULE_EXECUTION_LOG.md` | 3 | 0 | 0 | 3 | 0 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M10-admin-governance-and-observability/MODULE_DEPENDENCIES.md` | 3 | 0 | 0 | 0 | 3 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M10-admin-governance-and-observability/MODULE_EXECUTION_LOG.md` | 3 | 0 | 0 | 3 | 0 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M10-admin-governance-and-observability/MODULE_OPEN_QUESTIONS.md` | 3 | 0 | 3 | 0 | 0 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `DAILY_EXECUTION_PANEL.md` | 2 | 2 | 0 | 0 | 0 | REVIEW：需人工决定目标归属 |
| `OPEN_QUESTIONS.md` | 2 | 0 | 0 | 0 | 2 | REVIEW：需人工决定目标归属 |
| `docs/modules/M01-foundation-and-platform/MODULE_LOGIC_DESIGN.md` | 2 | 1 | 0 | 0 | 1 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M01-foundation-and-platform/sub_modules/ST01_02-workspace-shell-and-i18n/SUBTASK_IMPLEMENTATION.md` | 2 | 0 | 2 | 0 | 0 | DEDUP_TEMPLATE_OR_ARCHIVE_AFTER_TRACE：重复子任务模板，若无执行事实则归档/用单一模板替代 |
| `docs/modules/M01-foundation-and-platform/sub_modules/ST01_03-testing-logging-and-doc-governance/SUBTASK_IMPLEMENTATION.md` | 2 | 0 | 2 | 0 | 0 | DEDUP_TEMPLATE_OR_ARCHIVE_AFTER_TRACE：重复子任务模板，若无执行事实则归档/用单一模板替代 |
| `docs/modules/M02-identity-and-team/sub_modules/ST02_01-auth-mechanism-boundary/SUBTASK_IMPLEMENTATION.md` | 2 | 0 | 2 | 0 | 0 | DEDUP_TEMPLATE_OR_ARCHIVE_AFTER_TRACE：重复子任务模板，若无执行事实则归档/用单一模板替代 |
| `docs/modules/M02-identity-and-team/sub_modules/ST02_02-team-user-member-domain/SUBTASK_DESIGN.md` | 2 | 0 | 1 | 0 | 1 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M02-identity-and-team/sub_modules/ST02_02-team-user-member-domain/SUBTASK_IMPLEMENTATION.md` | 2 | 0 | 2 | 0 | 0 | DEDUP_TEMPLATE_OR_ARCHIVE_AFTER_TRACE：重复子任务模板，若无执行事实则归档/用单一模板替代 |
| `docs/modules/M02-identity-and-team/sub_modules/ST02_03-authorization-matrix/SUBTASK_IMPLEMENTATION.md` | 2 | 0 | 2 | 0 | 0 | DEDUP_TEMPLATE_OR_ARCHIVE_AFTER_TRACE：重复子任务模板，若无执行事实则归档/用单一模板替代 |
| `docs/modules/M03-jobs-resumes-and-documents/sub_modules/ST03_01-job-domain-and-pages/SUBTASK_IMPLEMENTATION.md` | 2 | 0 | 2 | 0 | 0 | DEDUP_TEMPLATE_OR_ARCHIVE_AFTER_TRACE：重复子任务模板，若无执行事实则归档/用单一模板替代 |
| `docs/modules/M03-jobs-resumes-and-documents/sub_modules/ST03_02-resume-domain-versioning-and-editor/SUBTASK_IMPLEMENTATION.md` | 2 | 0 | 2 | 0 | 0 | DEDUP_TEMPLATE_OR_ARCHIVE_AFTER_TRACE：重复子任务模板，若无执行事实则归档/用单一模板替代 |
| `docs/modules/M03-jobs-resumes-and-documents/sub_modules/ST03_03-upload-transform-export/SUBTASK_DESIGN.md` | 2 | 0 | 1 | 0 | 1 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M03-jobs-resumes-and-documents/sub_modules/ST03_03-upload-transform-export/SUBTASK_IMPLEMENTATION.md` | 2 | 0 | 2 | 0 | 0 | DEDUP_TEMPLATE_OR_ARCHIVE_AFTER_TRACE：重复子任务模板，若无执行事实则归档/用单一模板替代 |
| `docs/modules/M04-match-analysis-and-evidence/MODULE_OPEN_QUESTIONS.md` | 2 | 0 | 0 | 0 | 2 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M04-match-analysis-and-evidence/sub_modules/ST04_01-bindings-and-input-contract/SUBTASK_IMPLEMENTATION.md` | 2 | 0 | 2 | 0 | 0 | DEDUP_TEMPLATE_OR_ARCHIVE_AFTER_TRACE：重复子任务模板，若无执行事实则归档/用单一模板替代 |
| `docs/modules/M04-match-analysis-and-evidence/sub_modules/ST04_02-analysis-scoring-and-evidence/SUBTASK_IMPLEMENTATION.md` | 2 | 0 | 2 | 0 | 0 | DEDUP_TEMPLATE_OR_ARCHIVE_AFTER_TRACE：重复子任务模板，若无执行事实则归档/用单一模板替代 |
| `docs/modules/M04-match-analysis-and-evidence/sub_modules/ST04_03-analysis-ui-and-training-entry/SUBTASK_IMPLEMENTATION.md` | 2 | 0 | 2 | 0 | 0 | DEDUP_TEMPLATE_OR_ARCHIVE_AFTER_TRACE：重复子任务模板，若无执行事实则归档/用单一模板替代 |
| `docs/modules/M05-assets-and-retrieval/MODULE_OPEN_QUESTIONS.md` | 2 | 0 | 0 | 0 | 2 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M05-assets-and-retrieval/sub_modules/ST05_01-asset-type-and-asset-domain/SUBTASK_IMPLEMENTATION.md` | 2 | 0 | 2 | 0 | 0 | DEDUP_TEMPLATE_OR_ARCHIVE_AFTER_TRACE：重复子任务模板，若无执行事实则归档/用单一模板替代 |
| `docs/modules/M05-assets-and-retrieval/sub_modules/ST05_02-archive-records-and-source-linkage/SUBTASK_IMPLEMENTATION.md` | 2 | 0 | 2 | 0 | 0 | DEDUP_TEMPLATE_OR_ARCHIVE_AFTER_TRACE：重复子任务模板，若无执行事实则归档/用单一模板替代 |
| `docs/modules/M05-assets-and-retrieval/sub_modules/ST05_03-retrieval-chunking-and-index-ingestion/SUBTASK_IMPLEMENTATION.md` | 2 | 0 | 2 | 0 | 0 | DEDUP_TEMPLATE_OR_ARCHIVE_AFTER_TRACE：重复子任务模板，若无执行事实则归档/用单一模板替代 |
| `docs/modules/M06-simulated-interview-and-context/sub_modules/ST06_01-interview-session-bootstrap/SUBTASK_IMPLEMENTATION.md` | 2 | 0 | 2 | 0 | 0 | DEDUP_TEMPLATE_OR_ARCHIVE_AFTER_TRACE：重复子任务模板，若无执行事实则归档/用单一模板替代 |
| `docs/modules/M06-simulated-interview-and-context/sub_modules/ST06_02-context-pack-and-question-source/SUBTASK_IMPLEMENTATION.md` | 2 | 0 | 2 | 0 | 0 | DEDUP_TEMPLATE_OR_ARCHIVE_AFTER_TRACE：重复子任务模板，若无执行事实则归档/用单一模板替代 |
| `docs/modules/M06-simulated-interview-and-context/sub_modules/ST06_03-message-trace-report-and-export/SUBTASK_IMPLEMENTATION.md` | 2 | 0 | 2 | 0 | 0 | DEDUP_TEMPLATE_OR_ARCHIVE_AFTER_TRACE：重复子任务模板，若无执行事实则归档/用单一模板替代 |
| `docs/modules/M07-polish-assessment-and-progress/sub_modules/ST07_01-practice-topic-recommendation/SUBTASK_IMPLEMENTATION.md` | 2 | 0 | 2 | 0 | 0 | DEDUP_TEMPLATE_OR_ARCHIVE_AFTER_TRACE：重复子任务模板，若无执行事实则归档/用单一模板替代 |
| `docs/modules/M07-polish-assessment-and-progress/sub_modules/ST07_02-capability-tree-and-node-state/SUBTASK_IMPLEMENTATION.md` | 2 | 0 | 2 | 0 | 0 | DEDUP_TEMPLATE_OR_ARCHIVE_AFTER_TRACE：重复子任务模板，若无执行事实则归档/用单一模板替代 |
| `docs/modules/M07-polish-assessment-and-progress/sub_modules/ST07_03-assessment-and-progress/SUBTASK_IMPLEMENTATION.md` | 2 | 0 | 2 | 0 | 0 | DEDUP_TEMPLATE_OR_ARCHIVE_AFTER_TRACE：重复子任务模板，若无执行事实则归档/用单一模板替代 |
| `docs/modules/M08-review-and-replay/sub_modules/ST08_01-review-aggregate/SUBTASK_IMPLEMENTATION.md` | 2 | 0 | 2 | 0 | 0 | DEDUP_TEMPLATE_OR_ARCHIVE_AFTER_TRACE：重复子任务模板，若无执行事实则归档/用单一模板替代 |
| `docs/modules/M08-review-and-replay/sub_modules/ST08_02-real-interview-intake/SUBTASK_IMPLEMENTATION.md` | 2 | 0 | 2 | 0 | 0 | DEDUP_TEMPLATE_OR_ARCHIVE_AFTER_TRACE：重复子任务模板，若无执行事实则归档/用单一模板替代 |
| `docs/modules/M08-review-and-replay/sub_modules/ST08_03-simulated-review-replay/SUBTASK_IMPLEMENTATION.md` | 2 | 0 | 2 | 0 | 0 | DEDUP_TEMPLATE_OR_ARCHIVE_AFTER_TRACE：重复子任务模板，若无执行事实则归档/用单一模板替代 |
| `docs/modules/M09-training-and-weakness-lifecycle/sub_modules/ST09_01-weakness-aggregation/SUBTASK_IMPLEMENTATION.md` | 2 | 0 | 2 | 0 | 0 | DEDUP_TEMPLATE_OR_ARCHIVE_AFTER_TRACE：重复子任务模板，若无执行事实则归档/用单一模板替代 |
| `docs/modules/M09-training-and-weakness-lifecycle/sub_modules/ST09_02-training-drawer-and-intake/SUBTASK_IMPLEMENTATION.md` | 2 | 0 | 2 | 0 | 0 | DEDUP_TEMPLATE_OR_ARCHIVE_AFTER_TRACE：重复子任务模板，若无执行事实则归档/用单一模板替代 |
| `docs/modules/M10-admin-governance-and-observability/sub_modules/ST10_01-admin-member-and-role-ops/SUBTASK_IMPLEMENTATION.md` | 2 | 0 | 2 | 0 | 0 | DEDUP_TEMPLATE_OR_ARCHIVE_AFTER_TRACE：重复子任务模板，若无执行事实则归档/用单一模板替代 |
| `docs/modules/M10-admin-governance-and-observability/sub_modules/ST10_02-models-rules-and-settings/SUBTASK_IMPLEMENTATION.md` | 2 | 0 | 2 | 0 | 0 | DEDUP_TEMPLATE_OR_ARCHIVE_AFTER_TRACE：重复子任务模板，若无执行事实则归档/用单一模板替代 |
| `docs/modules/M10-admin-governance-and-observability/sub_modules/ST10_03-observability-ci-and-snapshot-ops/SUBTASK_IMPLEMENTATION.md` | 2 | 0 | 2 | 0 | 0 | DEDUP_TEMPLATE_OR_ARCHIVE_AFTER_TRACE：重复子任务模板，若无执行事实则归档/用单一模板替代 |
| `DOCUMENT_PROGRESS.md` | 1 | 0 | 0 | 0 | 1 | REVIEW：需人工决定目标归属 |
| `docs/design/workbench-mvp/scoring-review-export-dod.md` | 1 | 0 | 0 | 0 | 1 | MIGRATE_TO docs/02-design/*；移除旧阶段标签，保留设计事实 |
| `docs/modules/M01-foundation-and-platform/sub_modules/ST01_02-workspace-shell-and-i18n/SUBTASK_DESIGN.md` | 1 | 0 | 0 | 0 | 1 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M01-foundation-and-platform/sub_modules/ST01_03-testing-logging-and-doc-governance/SUBTASK_DESIGN.md` | 1 | 0 | 0 | 0 | 1 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M03-jobs-resumes-and-documents/sub_modules/ST03_01-job-domain-and-pages/SUBTASK_DESIGN.md` | 1 | 0 | 0 | 0 | 1 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M03-jobs-resumes-and-documents/sub_modules/ST03_02-resume-domain-versioning-and-editor/SUBTASK_DESIGN.md` | 1 | 0 | 0 | 0 | 1 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M04-match-analysis-and-evidence/MODULE_EXECUTION_LOG.md` | 1 | 0 | 0 | 1 | 0 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M04-match-analysis-and-evidence/sub_modules/ST04_01-bindings-and-input-contract/SUBTASK_DESIGN.md` | 1 | 0 | 0 | 0 | 1 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M04-match-analysis-and-evidence/sub_modules/ST04_02-analysis-scoring-and-evidence/SUBTASK_DESIGN.md` | 1 | 0 | 0 | 0 | 1 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M04-match-analysis-and-evidence/sub_modules/ST04_03-analysis-ui-and-training-entry/SUBTASK_DESIGN.md` | 1 | 0 | 0 | 0 | 1 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M05-assets-and-retrieval/MODULE_EXECUTION_LOG.md` | 1 | 0 | 0 | 1 | 0 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M05-assets-and-retrieval/sub_modules/ST05_01-asset-type-and-asset-domain/SUBTASK_DESIGN.md` | 1 | 0 | 0 | 0 | 1 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M05-assets-and-retrieval/sub_modules/ST05_02-archive-records-and-source-linkage/SUBTASK_DESIGN.md` | 1 | 0 | 0 | 0 | 1 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M05-assets-and-retrieval/sub_modules/ST05_03-retrieval-chunking-and-index-ingestion/SUBTASK_DESIGN.md` | 1 | 0 | 0 | 0 | 1 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M06-simulated-interview-and-context/MODULE_EXECUTION_LOG.md` | 1 | 0 | 0 | 1 | 0 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M06-simulated-interview-and-context/sub_modules/ST06_01-interview-session-bootstrap/SUBTASK_DESIGN.md` | 1 | 0 | 0 | 0 | 1 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M06-simulated-interview-and-context/sub_modules/ST06_02-context-pack-and-question-source/SUBTASK_DESIGN.md` | 1 | 0 | 0 | 0 | 1 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M06-simulated-interview-and-context/sub_modules/ST06_03-message-trace-report-and-export/SUBTASK_DESIGN.md` | 1 | 0 | 0 | 0 | 1 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M07-polish-assessment-and-progress/sub_modules/ST07_01-practice-topic-recommendation/SUBTASK_DESIGN.md` | 1 | 0 | 0 | 0 | 1 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M07-polish-assessment-and-progress/sub_modules/ST07_02-capability-tree-and-node-state/SUBTASK_DESIGN.md` | 1 | 0 | 0 | 0 | 1 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M07-polish-assessment-and-progress/sub_modules/ST07_03-assessment-and-progress/SUBTASK_DESIGN.md` | 1 | 0 | 0 | 0 | 1 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M08-review-and-replay/sub_modules/ST08_01-review-aggregate/SUBTASK_DESIGN.md` | 1 | 0 | 0 | 0 | 1 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M08-review-and-replay/sub_modules/ST08_02-real-interview-intake/SUBTASK_DESIGN.md` | 1 | 0 | 0 | 0 | 1 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M08-review-and-replay/sub_modules/ST08_03-simulated-review-replay/SUBTASK_DESIGN.md` | 1 | 0 | 0 | 0 | 1 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M09-training-and-weakness-lifecycle/sub_modules/ST09_01-weakness-aggregation/SUBTASK_DESIGN.md` | 1 | 0 | 0 | 0 | 1 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M09-training-and-weakness-lifecycle/sub_modules/ST09_02-training-drawer-and-intake/SUBTASK_DESIGN.md` | 1 | 0 | 0 | 0 | 1 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M09-training-and-weakness-lifecycle/sub_modules/ST09_03-lifecycle-rules/SUBTASK_DESIGN.md` | 1 | 0 | 0 | 0 | 1 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M10-admin-governance-and-observability/sub_modules/ST10_01-admin-member-and-role-ops/SUBTASK_DESIGN.md` | 1 | 0 | 0 | 0 | 1 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M10-admin-governance-and-observability/sub_modules/ST10_02-models-rules-and-settings/SUBTASK_DESIGN.md` | 1 | 0 | 0 | 0 | 1 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
| `docs/modules/M10-admin-governance-and-observability/sub_modules/ST10_03-observability-ci-and-snapshot-ops/SUBTASK_DESIGN.md` | 1 | 0 | 0 | 0 | 1 | MIGRATE_RELEVANT_FACTS_TO PRD/UX/API/DATA/TECH/PROMPT/BACKLOG；模块原文不作为唯一 active 入口 |
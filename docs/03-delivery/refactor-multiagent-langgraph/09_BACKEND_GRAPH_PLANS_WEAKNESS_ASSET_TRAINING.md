---
title: 薄弱项、资产、训练闭环 LangGraph 实施计划
type: delivery-planning
status: draft-pr1
owner: 项目交付
permalink: ai-for-interviewer/docs/03-delivery/refactor-multiagent-langgraph/backend-graph-plans-weakness-asset-training
---

# 薄弱项、资产、训练闭环 LangGraph 实施计划

## 1. 文档目的

本文规划 `weakness_candidate_graph`、`asset_candidate_graph`、`training_suggestion_graph`、`candidate_confirmation_interrupt_graph` 的 skeleton，重点冻结 candidate / suggestion / formal object 边界。

## 2. 输入来源

- `docs/tmp/CODEX_LANGGRAPH_AI_NON_AI_BOUNDARY.md`
- active docs：`APPLICATION_FLOW_SPEC.md`、`PERSISTENCE_MODEL.md`、`DATA_MODEL.md`、`PROMPT_SPEC.md`、`SECURITY_PRIVACY.md`、`API_SPEC.md`
- `docs/02-design/prompt-contracts/WEAKNESS_CONTRACTS.md`
- `docs/02-design/prompt-contracts/ASSET_CONTRACTS.md`
- `docs/02-design/prompt-contracts/TRAINING_CONTRACTS.md`

## 3. 当前状态

Active docs 已要求 candidate / suggestion 不能静默升级 formal object。正式 `Weakness`、`Asset`、`AssetVersion`、`TrainingRecommendation`、`TrainingTask` 必须来自用户确认、用户编辑、合并确认或显式业务 API。

## 4. 目标输出

- 三个 candidate/suggestion generation graph skeleton。
- 一个 confirmation interrupt/resume graph skeleton。
- 前端 confirmation drawer、audit、rollback 占位。

## 5. 必须覆盖范围

| Graph | 目标 | State 字段占位 | Node 清单 | Edge / conditional edge | Checkpoint | Retry / fallback | Persistence targets | LLM trace capture | 测试计划 |
|---|---|---|---|---|---|---|---|---|---|
| `weakness_candidate_graph` | 从 job match / polish / review 提炼薄弱项候选 | `source_refs`, `existing_weakness_refs`, `candidate_refs`, `merge_suggestion_refs`, `severity_refs`, `trace_refs` | `load_weakness_sources`, `build_weakness_context`, `extract_weakness_candidates`, `suggest_weakness_merge`, `assess_weakness_severity`, `weakness_candidate_quality_gate`, `persist_weakness_candidates`, `complete_ai_task` | duplicate -> merge suggestion; evidence missing -> low confidence; confirm -> external Core command | context 后、candidate 后、quality 后、persist 后 | schema retry；证据不足 candidate-only | weakness_candidates, merge suggestions, trace/evidence | source refs、validation summary | no formal Weakness、merge conflict、low confidence |
| `asset_candidate_graph` | 提炼资产候选和版本建议 | `source_refs`, `existing_asset_refs`, `asset_candidate_refs`, `version_suggestion_refs`, `trace_refs` | `load_asset_sources`, `build_asset_context`, `extract_asset_candidates`, `suggest_asset_version_update`, `asset_quality_gate`, `persist_asset_candidates`, `complete_ai_task` | existing asset -> version suggestion; insufficient facts -> low confidence; confirm -> Core command | context 后、candidate 后、quality 后、persist 后 | 不虚构经历；schema retry | asset_candidates, quality hints, version suggestions, trace/evidence | sanitized source refs | no formal Asset/AssetVersion |
| `training_suggestion_graph` | 基于 confirmed weakness/assets 生成训练建议 | `confirmed_weakness_refs`, `asset_refs`, `score_trend_refs`, `training_candidate_refs`, `priority_refs`, `trace_refs` | `load_training_sources`, `build_training_context`, `generate_training_suggestions`, `rank_training_priorities`, `training_suggestion_quality_gate`, `persist_training_suggestions`, `complete_ai_task` | no confirmed weakness -> blocked/low confidence; user starts task -> explicit API | context 后、suggestion 后、ranking 后、persist 后 | schema retry；不得自动创建 TrainingTask | training recommendation candidates, priority ranking, trace/evidence | ranking summary、validation | no auto TrainingTask、confirmed weakness required |
| `candidate_confirmation_interrupt_graph` | 管理 confirmation interrupt/resume | `candidate_ref`, `candidate_type`, `source_refs`, `confirmation_action`, `edited_payload_ref`, `audit_ref`, `rollback_ref`, `trace_refs` | `prepare_confirmation_interrupt`, `sanitize_candidate_for_drawer`, `interrupt_wait_user_action`, `resume_with_user_action`, `validate_confirmation_owner_and_version`, `validate_edited_candidate`, `call_core_formal_write_command`, `write_user_confirmation_ref`, `write_audit_event`, `rollback_on_failed_formal_write`, `publish_confirmation_result` | confirm/edit/merge -> Core command; skip/reject -> no formal write; validation failed -> drawer error | interrupt 前、resume 后、formal command 前、audit 后 | owner mismatch fail closed; conflict -> stale version | user_confirmations, audit_events, formal via Core command only | confirmation graph 默认非 LLM | confirm once、skip no formal、audit required、rollback |

前端 confirmation drawer 映射占位：candidate summary、source refs、evidence summary、confidence flags、confirm/edit/reject/merge/skip、validation error、audit marker。

## 6. 与 active docs 的关系

本文落实 active docs 中 candidate / suggestion / formal object、user confirmation、audit、copy/privacy 和 trace 边界。LangGraph 只生成候选、建议和 trace；正式对象由 Core Business command/API 承接。

## 7. 非目标

- 不实现 confirmation drawer UI。
- 不新增 API。
- 不写正式对象实现。
- 不自动创建训练任务。
- 不实现复杂合并算法。
- 不实现 rollback 工具。

## 8. 后续 PR 使用方式

PR8 或等价候选闭环 PR 使用本文先实现 candidate-only runtime，再接 confirmation interrupt/resume 与 Core formal write command。late graph result 不得绕过 confirmation。

## 9. Definition of Done

- 四个 graph skeleton 已覆盖。
- candidate 不能静默升级 formal object。
- formal object 必须来自用户确认或显式 API。
- interrupt/resume、confirmation drawer、audit、rollback 均有占位。
- raw LLM payload 禁止进入 checkpoint、日志、API response。


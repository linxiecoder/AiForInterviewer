---
title: Pressure Agent Package
type: delivery-planning
status: draft-f5-langgraph-implementation-consolidation
owner: 后端架构 / AI 架构 / 产品设计
permalink: ai-for-interviewer/docs/03-delivery/refactor-multiagent-langgraph-implementation/backend-function-packages/pressure-agent-package
---

# Pressure Agent Package

## 1. Package 目标

本 package 冻结 Pressure Mode 的 graph implementation plan。Pressure graph 不进入 PR2；默认进入 PR8，或进入一个由主 Agent 明确授权的独立 Pressure PR。

## 2. Active design boundary

`PRESSURE_MODE_SPEC.md` 是 Pressure mode-level lifecycle、turn、pace、API handoff、report / review handoff 和 PR2 hold 的 active design source。本文只把它转换为 implementation package，不替代 active API / DATA / PROMPT / SECURITY docs。

## 3. Pressure vs Polish boundary

| Item | Pressure rule |
|---|---|
| primary goal | simulate real interview cadence with continuous question, answer, assessment, follow-up, end condition |
| turn shape | question -> answer -> assessment -> follow-up / continue / end |
| answer save | synchronous Core action, no LLM |
| output | opening, first question, answer quality, strategy, follow-up question, pace, end condition, session score, report input package |
| formal write | candidate / suggestion refs only until confirmation |

## 4. Graph state

| Field group | Required fields |
|---|---|
| identity | `owner_id`, `actor_id`, `ai_task_id`, `agent_run_id`, `session_id` |
| turn | `turn_refs`, `question_refs`, `answer_refs`, `current_turn_ref`, `turn_index` |
| assessment | `answer_quality_ref`, `missing_point_refs`, `risk_signal_refs`, `score_ref` |
| strategy | `opening_strategy_ref`, `follow_up_strategy_ref`, `pace_state_ref`, `end_condition_ref` |
| handoff | `report_input_ref`, `review_handoff_refs`, `candidate_refs` |
| runtime | `trace_refs`, `evidence_refs`, `interrupt_refs`, `error_state` |

## 5. Node plan

| Node | Inputs | Outputs | Side effects | Idempotency key | Failure status | Tests |
|---|---|---|---|---|---|---|
| `load_pressure_context` | owner/session/job/resume refs | compact context refs | read only | `pressure:{owner_id}:{session_id}:load` | `source_unavailable` | owner/source |
| `generate_opening` | context | opening strategy ref | LLM via transport | `pressure:{session_id}:opening:{context_digest}` | `generation_failed` | no raw payload |
| `generate_first_question` | opening, anti-repeat refs | first question candidate | write question after validation | `pressure:{session_id}:first-question:{context_digest}` | `partial` / `generation_failed` | pressure question refs |
| `wait_for_answer_interrupt` | question ref | interrupt / waiting state | write interrupt record | `interrupt:{agent_run_id}:{question_ref}` | `timed_out` / `cancelled` | pause/resume |
| `save_answer_handoff` | answer ref from API | answer state patch | no LLM; no provider | `pressure:{session_id}:{answer_ref}:save-handoff` | `validation_failed` | answer save no LLM |
| `analyze_answer_quality` | answer/question refs | quality refs | optional feedback / quality refs | `pressure:{session_id}:{answer_ref}:quality` | `low_confidence` | answer quality |
| `select_follow_up_strategy` | quality refs, pace state | strategy ref | none | `pressure:{session_id}:{turn_index}:strategy` | `partial` | follow-up strategy |
| `generate_follow_up_question` | strategy | follow-up question candidate | write question after validation | `pressure:{session_id}:{turn_index}:follow-up` | `generation_failed` | no repeated question |
| `control_pace` | turn refs | pace state | update session summary refs | `pressure:{session_id}:{turn_index}:pace` | `partial` | pace state |
| `check_end_condition` | turn refs, pace state | continue / pause / end route | update end condition refs | `pressure:{session_id}:{turn_index}:end-check` | `partial` | end condition |
| `generate_session_score` | end condition, turn refs | score candidate/ref | validated `ScoreResult(pressure_session)` only after gate | `pressure_score:{owner_id}:{session_id}:{turn_hash}` | `low_confidence` / `validation_failed` | no exact probability |
| `assemble_report_input_package` | session/turn/score/evidence refs | report input package ref | persist package refs | `report_input:{owner_id}:{session_id}:{turn_hash}` | `partial` / `source_unavailable` | package is not report body |
| `complete_ai_task` | graph state | terminal task status | write task result/status | `ai_task:{ai_task_id}:complete` | terminal status | sanitized status |

## 6. Prompt bundle requirements

| Contract | Runtime bundle | Required before graph implementation |
|---|---|---|
| `P-PRESSURE-001` | `pressure_opening_strategy` | asset, schema id, validator, golden/negative fixtures |
| `P-PRESSURE-002` | `pressure_first_question_generation` | no same-question-loop fixture |
| `P-PRESSURE-003` | `pressure_answer_quality_assessment` | source unavailable and low confidence fixtures |
| `P-PRESSURE-004` | `pressure_follow_up_strategy` | strategy validator |
| `P-PRESSURE-005` | `pressure_follow_up_question_generation` | anti-repeat validator |
| `P-PRESSURE-006` | `pressure_pace_control` | pace state schema |
| `P-PRESSURE-007` | `pressure_end_condition_check` | end condition schema |
| `P-PRESSURE-008` | `pressure_session_score` | no exact probability fixture |
| `P-PRESSURE-009` | `pressure_report_input_assembly` | report input package schema |

## 7. Endpoint readiness before implementation

| Action | Requirement |
|---|---|
| create / start session | express active/running state and source refs |
| pause / resume session | persist minimum snapshot refs and validate owner/source availability |
| end session | record completed/cancelled/failed and user-selected path |
| generate pressure report | report endpoint consumes report input package ref; Pressure endpoint does not return report body |
| generate mock review from pressure | review endpoint consumes pressure session/report refs |

## 8. Persistence rules

| Concern | Rule |
|---|---|
| turn identity | may use existing question/answer/feedback/session summary refs unless a later schema creates `pressure_turns` |
| pace/end/report refs | may be typed refs or task result summaries until concrete tables are authorized |
| checkpoint | runtime state only; business reads use persisted refs and summaries |
| rollback | in-flight pressure tasks cancel/fail closed; no late formal write |
| raw-off | raw prompt/completion/provider payload absent from normal tables, checkpoint, trace-visible body, API, copy content |

## 9. Tests

| Area | Assertions |
|---|---|
| lifecycle | create/start/pause/resume/end states are owner scoped |
| turn loop | first question, answer save, quality, strategy, follow-up, end condition |
| report handoff | report input package exists and is not report body |
| scoring | 0-100 product scale, confidence/validation visible, no exact probability |
| candidate | candidate refs only, confirmation required |
| raw-off | no raw prompt/completion/provider/checkpoint payload visible |

## 10. Non-goals

- 不做 PR2 implementation。
- No report body generation in Pressure graph.
- No formal Weakness / Asset / TrainingRecommendation write.
- No TrainingTask creation.
- 默认不调用 real provider。

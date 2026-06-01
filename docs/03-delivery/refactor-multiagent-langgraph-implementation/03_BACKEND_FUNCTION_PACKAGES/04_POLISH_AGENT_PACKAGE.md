---
title: Polish Agent Package
type: delivery-planning
status: draft-f5-langgraph-implementation-consolidation
owner: 后端架构 / AI 架构
permalink: ai-for-interviewer/docs/03-delivery/refactor-multiagent-langgraph-implementation/backend-function-packages/polish-agent-package
---

# Polish Agent Package

## 1. Package 目标

本 package 冻结 PR5 Polish first migration target 的 implementation plan：`polish_progress_tree_graph`、`polish_question_graph`、`polish_feedback_graph`。它同时冻结 answer save 非 AI 边界。

PR5 只覆盖 progress tree、question 和 feedback graph parity。Candidate enhancement、candidate confirmation、formal Weakness / Asset / Training closure 留到 PR8，不作为 PR5 退出条件。

## 2. Non-negotiable boundaries

| Boundary | Rule |
|---|---|
| answer save | `PolishUseCases.create_answer` remains Core Business synchronous write; it does not call LLM and does not start graph |
| feedback generation | independent AI task; answer save cannot implicitly generate feedback；runtime calls `FeedbackGenerationService.generate()` and must not return legacy reserved compatibility as success；Phase 4 feedback rule fields are enforced by backend policy / validation |
| candidate | generated feedback may keep candidate-compatible fields, but formal Weakness / Asset / Training objects cannot be created without confirmation；full candidate extraction remains future scope |
| candidate generation | deferred until explicit authorization；not PR5 scope |
| raw-off | no raw prompt/completion/provider payload in checkpoint/log/API/timeline |
| Core dependency | Core Polish use case cannot import LangGraph or graph node |

## 3. Graph scope

| Graph | Target | Persistence targets | PR |
|---|---|---|---:|
| `polish_progress_tree_graph` | generate or refresh session progress tree | progress tree/state, AI task result, trace/evidence | PR5 |
| `polish_question_graph` | generate question from progress node and context | questions, AI task result, trace/evidence, low confidence flags | PR5 |
| `polish_feedback_graph` | target graph parity for existing `FeedbackGenerationService.generate()` direct path | generated feedback today；Phase 4 feedback rules must be preserved；candidate refs require later authorization | PR5 parity candidate; Phase 4 rules implemented in direct path |

## 4. `polish_question_graph` node plan

| Node | Inputs | Outputs | Side effects | Idempotency key | Failure status | Tests |
|---|---|---|---|---|---|---|
| `load_polish_session_context` | owner, session id | session detail refs, progress refs | read only | `polish_question:{owner_id}:{session_id}:load` | `not_found_or_inaccessible` / `source_unavailable` | owner/session status |
| `validate_question_request` | command, session detail | request metadata and generation mode | none | `polish_question:{session_id}:{request_digest}:validate` | `validation_failed` | invalid topic/node/mode |
| `resolve_progress_node` | progress plan/state/requested ref | resolved progress node | none | `polish_question:{session_id}:{requested_ref}:resolve-node` | `validation_failed` | requested node / current priority |
| `build_evidence_scope` | progress context, plan/state, resolved node, completed refs | `EvidenceScope`, evidence refs, question sources | none | `polish_question:{session_id}:{progress_node_ref}:scope:{completed_focus_hash}` | `validation_failed` / `low_confidence` | evidence selection and anti-repeat context |
| `build_question_blueprint` | `EvidenceScope` | `QuestionBlueprint` | none | `polish_question:{session_id}:{progress_node_ref}:blueprint:{scope_digest}` | `validation_failed` / `low_confidence` | blueprint kind, claim mode, expected dimensions |
| `render_surface_question` | `QuestionBlueprint`, `EvidenceScope` | surface question text and prompt metadata | none | `polish_question:{session_id}:{progress_node_ref}:surface:{blueprint_digest}` | `generation_failed` / `low_confidence` | no raw provider payload |
| `validate_question_grounding` | surface question, `QuestionBlueprint`, primary source type | grounding result | none | `polish_question:{session_id}:{progress_node_ref}:grounding:{question_digest}` | `validation_failed` | grounding failure does not repair, generate or persist question |
| `persist_question` | grounded question draft, metadata | question ref | write `questions` | `question:{owner_id}:{session_id}:{progress_node_ref}:{question_digest}` | `generation_failed` | API readback, no raw metadata |
| `complete_ai_task` | state and question ref | terminal task result | write task status | `ai_task:{ai_task_id}:complete` | terminal status | task contract shape |

## 5. `polish_progress_tree_graph` node plan

| Node | Inputs | Outputs | Side effects | Idempotency key | Failure status | Tests |
|---|---|---|---|---|---|---|
| `load_polish_session_context` | owner/session | detail refs, compact source refs | read only | `polish_tree:{owner_id}:{session_id}:load` | `not_found_or_inaccessible` / `source_unavailable` | owner scoped |
| `build_progress_context` | detail progress context | themed compact context | none | `polish_tree:{session_id}:context:{source_digest}` | `low_confidence` | compact only |
| `generate_progress_tree_plan` | context | plan/state artifacts | LLM if feature enabled | `polish_tree:{session_id}:{context_digest}:plan` | `generation_failed` / `low_confidence` | no fake tree |
| `progress_tree_quality_gate` | plan/state artifacts | validated artifacts | none | `polish_tree:{session_id}:{plan_digest}:gate` | `validation_failed` / `low_confidence` | node refs stable |
| `persist_progress_tree_state` | validated artifacts | persisted refs | update progress tree/state | `polish_tree:{owner_id}:{session_id}:{plan_digest}:persist` | `partial` | previous valid tree preserved |
| `complete_ai_task` | graph state | task result | write task status | `ai_task:{ai_task_id}:complete` | terminal status | task status |

## 6. `polish_feedback_graph` node plan

| Node | Inputs | Outputs | Side effects | Idempotency key | Failure status | Tests |
|---|---|---|---|---|---|---|
| `load_answer_context` | owner, session, answer | answer/question/previous feedback refs | read only | `polish_feedback:{owner_id}:{session_id}:{answer_id}:load` | `not_found_or_inaccessible` | answer/session/question owner |
| `validate_feedback_request` | answer context | request valid | none | `polish_feedback:{answer_id}:validate` | `validation_failed` / `low_confidence` | answer too short |
| `build_feedback_input` | session, question, answer, previous feedbacks | compact feedback input | none | `polish_feedback:{answer_id}:{answer_round}:input` | `partial` | compact previous feedback only |
| `build_deterministic_feedback_seed` | input and generated ids | deterministic fallback payload | none | `polish_feedback:{answer_id}:{feedback_id}:seed` | `low_confidence` | deterministic payload |
| `generate_feedback_candidate` | input and seed | feedback candidate payload | LLM via transport wrapper | `polish_feedback:{answer_id}:{input_digest}:llm` | `generation_failed` / `low_confidence` | fake accepted, fallback metadata |
| `feedback_schema_gate` | candidate payload | schema-valid payload | none | `polish_feedback:{feedback_id}:schema:{candidate_digest}` | `validation_failed` | schema invalid fallback |
| `feedback_consistency_gate` | schema-valid payload | normalized feedback and score candidate | none | `polish_feedback:{feedback_id}:consistency:{payload_digest}` | `validation_failed` / `low_confidence` | score repair and no leaks |
| `extract_weakness_asset_candidates` | normalized payload, question metadata | candidate refs/payloads | none | `polish_feedback:{feedback_id}:extract-candidates:{payload_digest}` | `partial` | candidate refs, no formal write |
| `enhance_candidates_with_llm_if_enabled` | candidate payload | enhanced candidate payload | PR8 only；LLM only if feature and provider gates allow | `polish_feedback:{feedback_id}:candidate-llm:{candidate_digest}` | `partial` / `low_confidence` | forbidden provider fallback |
| `persist_feedback` | normalized/enhanced payload | feedback ref | write `feedback` | `feedback:{owner_id}:{answer_id}:{feedback_id}` | `generation_failed` | legacy API sanitizer |
| `persist_score` | score candidate, feedback ref | score ref | write `ScoreResult(polish_answer)` when valid | `score_result:{owner_id}:polish_answer:{feedback_id}:{score_version}` | `partial` / `validation_failed` | invalid score skips formal score |
| `persist_candidates` | candidate payload | candidate refs | upsert candidates only | `polish_candidates:{owner_id}:{feedback_id}:{candidate_digest}` | `partial` | no formal write |
| `update_progress_state` | feedback/question/answer refs | progress update refs | update progress tree state | `polish_progress:{owner_id}:{session_id}:{answer_id}:feedback` | `partial` | state update logic |
| `complete_ai_task` | state refs | terminal task result | write task status | `ai_task:{ai_task_id}:complete` | terminal status | feedback independent task |

## 7. Migration mapping

| Existing symbol | Target | Strategy |
|---|---|---|
| `PolishUseCases.create_question_task` | `QuestionGenerationService.generate` / future `polish_question_graph` facade entry | keep facade boundary |
| `question_generation_service.py` | resolve progress node -> `EvidenceScope` / `CanonicalEvidencePack` -> `source_support_level` four-state path -> compact provider request / `QuestionBlueprint` -> surface question -> blocking/warning grounding | keep as current question hardening source of truth |
| `question_blueprint.py` | blueprint node | keep |
| `question_grounding.py` | grounding gate | keep |
| `PolishUseCases.refresh_progress_tree_state` | `polish_progress_tree_graph` entry | split |
| `PolishUseCases.create_answer` | Core answer save | keep |
| `PolishUseCases.create_feedback_task` | `FeedbackGenerationService.generate` / future `polish_feedback_graph` entry | keep direct generated path as source of truth until graph parity wraps it |
| `FeedbackGenerationService.generate` | generated feedback node | keep service call, validation, failure semantics, `CanonicalEvidencePack.canonical_project_assets` context, Phase 4 feedback fields and generated payload persistence/readback |
| `build_reserved_feedback_artifacts` / `build_reserved_feedback_payload` | legacy/fallback compatibility shape | keep only as compatibility; never as successful generated feedback |
| `SqlAlchemyPolishRepository.add_question/add_feedback/update_progress_tree/add_task` | persistence nodes | keep / wrap |

## 8. PR5 tests

| Test area | Assertions |
|---|---|
| question graph | existing question API shape preserved; owner scope; grounding failure returns validation_failed and writes no question; no raw LLM fields |
| progress tree | refresh keeps node refs; low confidence path does not wipe valid previous tree |
| answer save | answer save does not call LLM or start graph |
| feedback graph | independent AI task shape preserved; generated path calls `FeedbackGenerationService.generate()`, persists readable generated payload, preserves Phase 4 feedback fields, and maps provider / validation failure to `generation_failed` or equivalent failure state |
| candidate boundary | generated feedback cannot create formal candidate objects; future candidate refs cannot create formal objects before confirmation |

## 9. Non-goals

- 不执行 PR2。
- 不调用 real provider。
- No vector database.
- No hidden raw provider fields in API responses.
- No automatic formal candidate promotion.
- No candidate generation or formal closure without explicit authorization.

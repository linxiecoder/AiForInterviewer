---
title: G-003 Structured Answer Evaluation
type: temporary-goal-package
status: implemented-validated
updated: 2026-06-12
---

# G-003 Structured Answer Evaluation

## Status

| Field | Value |
| --- | --- |
| Goal ID | `G-003` |
| Goal name | Structured Answer Evaluation |
| Status | Implemented and validated |
| Approval | Implementation approved by user prompt on 2026-06-12 |
| Round 5 posture | Implemented within the explicit G-003 allowlist |
| Write boundary for this round | G-003 allowlisted production/test files plus `.codex-temp/interview-coach-refactor/05-goals/G-003-structured-answer-evaluation.md`, `.codex-temp/interview-coach-refactor/06-implementation/change-ledger.md`, `.codex-temp/interview-coach-refactor/07-validation/test-results.md`, and `.codex-temp/interview-coach-refactor/CONTROL.md` |
| Production code | Modified only G-003 allowlisted production files |
| Tests | Modified only G-003 allowlisted test files |
| `AGENTS.md` | Not modified in this round |

### Goal ID Handling

`G-002` is already used by `.codex-temp/interview-coach-refactor/05-goals/G-002-capture-analysis-separation.md` for Capture / Analysis Separation. Structured Answer Evaluation was therefore renamed from `G-002-structured-answer-evaluation.md` to `G-003-structured-answer-evaluation.md`. `G-003` is the next unused Goal ID under `.codex-temp/interview-coach-refactor/05-goals/` at the time of this refinement.

## Round 5 Implementation Record

### Implementation Steps Completed

1. Added failing backend tests for `low_confidence` status derivation, missing final `trace_refs` validation failure, validation-failed persistence, schema compatibility, and response-level embedded score boundary.
2. Added failing frontend tests for expanded status taxonomy, legacy `failed` alias handling, low-confidence display, validation/generation failure display, and sanitized trace metadata.
3. Updated `FeedbackGenerationService` to derive `low_confidence` from merged provider/rules `low_confidence_flags`, while keeping validation warnings as `partial` and final validation failures scoreless.
4. Updated `PolishFeedbackApplicationService` to persist validation-stage failures as `validation_failed` and provider/no-transport/fake/runtime failures as `generation_failed`; `score_result_id` remains `None`.
5. Widened API response schema compatibility for string or object `trace_refs` and `low_confidence_flags`; request shape remains unchanged and still requires saved `answer_id`.
6. Updated frontend types and `InterviewPage` feedback view model to render `generated`, `partial`, `low_confidence`, `validation_failed`, `generation_failed`, `pending`, and legacy `failed` compatibility without exposing raw trace ids or provider/prompt/completion payloads.
7. Verified no scoring API/model/repository files, transcript/storybank/outcome calibration, self-assessment delta, root-cause lifecycle, Weakness/Asset/Training/Report writes, or `AGENTS.md` were modified.

### Files Changed

| File | Change |
| --- | --- |
| `apps/api/app/application/polish/feedback_generation_service.py` | Derive final `low_confidence` status from merged low-confidence flags; keep `partial` for warnings and generated as clean default |
| `apps/api/app/application/polish/feedback_application_service.py` | Distinguish `validation_failed` from `generation_failed` in task, feedback row status, and stored failure payload; keep `score_result_id=None` |
| `apps/api/app/schemas/polish.py` | Allow response `trace_refs` and `low_confidence_flags` to contain strings or objects |
| `apps/web/src/entities/polish/model/types.ts` | Expand frontend feedback status union and low-confidence flag compatibility |
| `apps/web/src/pages/interview/InterviewPage.tsx` | Render expanded status taxonomy, status summaries, failure states, and sanitized trace metadata |
| `tests/api/test_polish_feedback_generation_service.py` | Add low-confidence status and missing trace validation failure tests |
| `tests/api/test_polish_application_service_split.py` | Add validation-failed persistence test and `score_result_id=None` assertion |
| `tests/api/test_polish_api.py` | Add schema compatibility test and response-level `score_result_id=None` assertion |
| `apps/web/src/pages/interview/InterviewPage.test.ts` | Add frontend status taxonomy and sanitized trace metadata coverage |
| `.codex-temp/interview-coach-refactor/05-goals/G-003-structured-answer-evaluation.md` | Record G-003 implementation and validation |
| `.codex-temp/interview-coach-refactor/06-implementation/change-ledger.md` | Add G-003 implementation ledger |
| `.codex-temp/interview-coach-refactor/07-validation/test-results.md` | Add G-003 validation evidence |
| `.codex-temp/interview-coach-refactor/CONTROL.md` | Mark G-003 implemented and validated |

### Validation Results

| Command | Exit | Result |
| --- | ---:| --- |
| `.venv/bin/python -m pytest tests/api/test_polish_feedback_generation_service.py -q` | 1 | Expected RED before implementation: 2 status derivation failures; assertions otherwise ran |
| `.venv/bin/python -m pytest tests/api/test_polish_application_service_split.py -q` | 1 | Expected RED before implementation: validation failure still mapped to `generation_failed` |
| `npm --workspace apps/web run test` | 2 | Expected RED before implementation: frontend status union only allowed `pending/generated/failed` |
| `AI_FOR_INTERVIEWER_ALLOW_TEST_DIR_LEAKS=1 .venv/bin/python -m pytest tests/api/test_polish_feedback_generation_service.py -q` | 0 | 39 passed |
| `AI_FOR_INTERVIEWER_ALLOW_TEST_DIR_LEAKS=1 .venv/bin/python -m pytest tests/api/test_polish_feedback_models.py tests/api/test_polish_feedback_pipeline_contract.py -q` | 0 | 15 passed |
| `AI_FOR_INTERVIEWER_ALLOW_TEST_DIR_LEAKS=1 .venv/bin/python -m pytest tests/api/test_polish_application_service_split.py -q` | 0 | 18 passed |
| `AI_FOR_INTERVIEWER_ALLOW_TEST_DIR_LEAKS=1 .venv/bin/python -m pytest tests/api/test_polish_api.py -q` | 0 | 130 passed |
| `npm --workspace apps/web run test` | 0 | `tsc -p tsconfig.json --noEmit` passed |

### Remaining Risks

| Risk | Status |
| --- | --- |
| Existing repo-root `tmp/` triggers pytest leak guard without override | Known environment risk; successful backend validation used `AI_FOR_INTERVIEWER_ALLOW_TEST_DIR_LEAKS=1` and did not delete/modify `tmp/` |
| Frontend only displays sanitized trace metadata count/type/status | Accepted G-003 scope; raw trace ids and provider/prompt/completion bodies remain hidden |
| Formal `ScoreResult` persistence | Deferred; this implementation keeps embedded `PolishFeedbackPayload.score_result` response-level only and `score_result_id=None` |
| Manual browser validation | Not run in this implementation window; automated backend/frontend contract tests passed |

## Decision Register

| Item | Decision | Evidence | Round 5 effect |
| --- | --- | --- | --- |
| Polish feedback `score_result` persisted as formal `ScoreResult` | Defer | Current Polish feedback writes embedded `score_result` but `apps/api/app/application/polish/feedback_application_service.py::PolishFeedbackApplicationService.create_feedback_task` sets `score_result_id=None` on generated and failed feedback. Formal scoring exists in `apps/api/app/application/scoring/use_cases.py::ScoringUseCases.create`, `apps/api/app/infrastructure/db/models/scoring.py::ScoreResult`, and `apps/api/app/api/v1/scoring.py::create_score_result`, but mapping feedback loss points to canonical score dimensions and wiring cross-service persistence would broaden this Goal. | Round 5 keeps embedded `PolishFeedbackPayload.score_result` as the user-visible score. It must test that this Goal does not create `score_results` rows and does not populate `Feedback.score_result_id`. |
| Frontend `resolvePolishFeedbackStatus` distinguishes `partial`, `low_confidence`, `validation_failed`, `generation_failed` | Include | Backend status vocabulary exists in `apps/api/app/domain/shared/enums.py::AiTaskStatus`; final feedback allows `generated`, `partial`, `low_confidence`, `validation_failed` in `apps/api/app/application/polish/feedback_models.py::FeedbackFinalPayload`; frontend currently narrows status to `pending/generated/failed` in `apps/web/src/pages/interview/InterviewPage.tsx::resolvePolishFeedbackStatus`. | Round 5 updates frontend type and view-model status mapping, and updates backend failure/status derivation where needed so the frontend receives distinct states. |
| `trace_refs` in Round 5 scope | Include, sanitized display only | `trace_refs` is required by `apps/api/app/application/polish/feedback_validation.py::validate_final_feedback_payload`, returned by `apps/api/app/api/v1/polish.py::_feedback_response`, and typed in `apps/web/src/entities/polish/model/types.ts::PolishFeedbackPayload`. Current `apps/web/src/pages/interview/InterviewPage.tsx::buildFeedbackTraceItems` returns an empty list. | Round 5 may surface safe trace metadata such as count/type/status in the feedback meta area. It must not display raw prompt, provider payload, raw completion, full resume, full JD, token, secret, cookie, or hidden scoring details. |
| `low_confidence` status in Round 5 scope | Include | Low-confidence flags already flow through `FeedbackGenerationResult`, `FeedbackFinalPayload`, `PolishTaskStatusResponse`, and frontend types, while current frontend status mapping hides it. | Round 5 makes low-confidence evaluation user-visible and not equivalent to generated success. |
| Self-evaluation delta | Defer | interview-coach uses self-assessment in `/tmp/interview-coach-skill/references/commands/analyze.md` and `/tmp/interview-coach-skill/references/commands/practice.md`. Current AIForInterviewer feedback request only has generic `CreateFeedbackTaskRequest.scoring_context`; no user-visible self-assessment UI, typed field, storage, or calibration contract was found in the Polish workbench path. | No self-assessment input, delta calculation, or calibration display in Round 5. |
| Root-cause fields | Defer explicit fields | interview-coach root-cause lifecycle depends on persistent coaching state and calibration tables in `/tmp/interview-coach-skill/references/rubrics-detailed.md` and `/tmp/interview-coach-skill/references/calibration-engine.md`. Current AIForInterviewer has per-answer `loss_points`, `feedback_cards`, `next_recommended_actions`, and formal scoring `primary_bottleneck`, but no approved `root_cause` feedback schema field or cross-session root-cause state. | Round 5 may improve wording around per-answer `loss_points.reason` and actions, but must not add `root_cause`, `root_cause_id`, or cross-session root-cause lifecycle fields. |
| Transcript analysis | Defer | Source transcript pipeline lives in `/tmp/interview-coach-skill/references/transcript-formats.md`, `/tmp/interview-coach-skill/references/transcript-processing.md`, and `/tmp/interview-coach-skill/references/commands/analyze.md`. Current AIForInterviewer Polish path has structured Question/Answer/Feedback records, not transcript upload, normalization, quality gate, parser, API, UI, or tests. | No transcript upload, transcript parser, speaker-turn normalization, transcript quality gate, or transcript-level scoring. |
| Storybank | Defer | Source storybank lives in `/tmp/interview-coach-skill/references/storybank-guide.md`, `/tmp/interview-coach-skill/references/story-mapping-engine.md`, and `/tmp/interview-coach-skill/references/commands/stories.md`. Current AIForInterviewer has adjacent Asset/Weakness/Training concepts, but no first-class Storybank/Story model, repository, API, or UI. | No storybank table, API, prompt, UI, story usage count, story freshness, or story mapping. |
| Outcome calibration | Defer | Source outcome calibration requires Score History, Outcome Log, external feedback, and Calibration State in `/tmp/interview-coach-skill/references/calibration-engine.md` and `/tmp/interview-coach-skill/references/commands/progress.md`. Current Polish path has no outcome log or real-outcome correlation lifecycle. | No outcome log, recruiter/interviewer feedback capture, scoring drift correction, or outcome-score correlation. |

## Source Inspiration

| Source capability | interview-coach file path | Capability summary | Pattern adapted for AIForInterviewer | Explicitly not copied |
| --- | --- | --- | --- | --- |
| Transcript per-unit scoring | `/tmp/interview-coach-skill/references/transcript-processing.md`; `/tmp/interview-coach-skill/references/commands/analyze.md` | Source detects transcript format, parses units, scores answers, and records quality/confidence. | Adapt the idea that an answer evaluation should be structured, inspectable, evidence-aware, and status-aware. Use the existing saved Polish answer as the unit, not transcript text. | No transcript ingestion, format detector, speaker normalization, transcript quality gate, or multi-answer transcript pipeline. |
| Rubric plus targeted gap explanation | `/tmp/interview-coach-skill/references/rubrics-detailed.md` | Source ties low scores to dimensions, root-cause patterns, and targeted fixes. | Adapt the principle that score, loss points, evidence, and next actions must be connected. Use AIForInterviewer `loss_points`, `score_result`, `answer_coverage`, `feedback_cards`, and `next_recommended_actions`. | No source scoring dimensions, 1-5 anchors, seniority bands, hire/no-hire language, or explicit cross-session root-cause fields. |
| Evidence and confidence discipline | `/tmp/interview-coach-skill/references/evidence-sourcing.md`; `/tmp/interview-coach-skill/SKILL.md` | Source requires meaningful recommendations to be grounded and uncertainty to be visible. | Adapt to existing `evidence_refs`, `trace_refs`, `low_confidence_flags`, validation errors, and safe frontend status display. | No external company/interviewer claims, no raw evidence body exposure, no source prompt prose. |
| Self-assessment delta | `/tmp/interview-coach-skill/references/commands/analyze.md`; `/tmp/interview-coach-skill/references/commands/practice.md`; `/tmp/interview-coach-skill/references/commands/progress.md` | Source scores independently, then compares with candidate self-assessment over time. | Record as future design inspiration only. | No Round 5 self-assessment UI, request field, persistence, or calibration metric. |
| State-aware next step | `/tmp/interview-coach-skill/references/commands/analyze.md`; `/tmp/interview-coach-skill/references/commands/progress.md` | Source chooses a single next step based on the bottleneck. | Adapt to existing `next_recommended_actions` generated from feedback state, coverage, loss points, and low-confidence/failure state. | No command recommendation system, menu, command names, or workflow wording. |
| Storybank and outcome calibration | `/tmp/interview-coach-skill/references/storybank-guide.md`; `/tmp/interview-coach-skill/references/calibration-engine.md` | Source maintains long-running story and outcome memory. | None for this Goal beyond noting boundaries. | No storybank, outcome log, calibration state, success pattern learning, or scoring drift lifecycle. |

## AIForInterviewer Landing Point

| Landing point | Symbol | Current behavior | Gap | Why this is the right landing point |
| --- | --- | --- | --- | --- |
| `apps/api/app/api/v1/polish.py` | `create_polish_feedback_task`, `_feedback_response`, `_task_response` | Feedback task accepts `answer_id`, reloads the session answer, and returns `feedback_status`, `score_result`, `score_result_id`, `feedback_payload`, `low_confidence_flags`, and `trace_refs`. | Response can carry richer statuses, but downstream frontend collapses them; failure mapping should distinguish validation failure from generation failure when backend evidence supports it. | This is the HTTP boundary for post-answer feedback generation and the source of frontend-visible task payloads. |
| `apps/api/app/schemas/polish.py` | `CreateFeedbackTaskRequest`, `PolishTaskStatusResponse`, `PolishFeedbackPayload` | Feedback request requires `answer_id`; task response includes feedback id/status, score fields, low-confidence flags, trace refs, and feedback payload. | Type contract should make Round 5 status taxonomy explicit and keep raw-answer bypass impossible. | This is the API schema boundary for the existing Polish workbench. |
| `apps/api/app/application/polish/feedback_generation_service.py` | `FeedbackGenerationService.generate`, `_build_final_payload`, `_feedback_status` | Normalizes context, builds prompt asset, validates candidate payload, applies deterministic core rules, validates final payload, and returns success/failure metadata. `_feedback_status` currently returns `partial` for validation warnings and otherwise `generated` unless status is already one of the allowed final statuses. | Low-confidence flags do not by themselves force a `low_confidence` final status. Validation failures return failure results, but the stored/task state is currently generalized by the application service. | This service owns parser, validation, final payload construction, and status derivation for structured answer evaluation. |
| `apps/api/app/application/polish/feedback_application_service.py` | `PolishFeedbackApplicationService.create_feedback_task`, `_generated_feedback_payload_for_storage`, `_failed_feedback_payload_for_storage` | Loads saved answer/question, prevents duplicate generated feedback under lock, stores generated payload or retryable failed payload. Both generated and failed feedback currently set `score_result_id=None`. Failed payload uses status `generation_failed` and `score_result=None`. | Failure status should distinguish validation failure vs generation failure when `generation_result.metadata.validation_stage` and errors indicate schema/final validation failure. Formal `ScoreResult` persistence remains out of scope. | This is the application boundary that attaches evaluation to a saved answer and persists feedback/task state. |
| `apps/api/app/application/polish/feedback_models.py` | `FeedbackCandidatePayload`, `FeedbackFinalPayload` | Candidate payload includes `feedback_text`, `answer_summary`, `score_reasoning`, `loss_points`, `reference_answer`, `same_question_effect`, `project_asset_update_candidates`, `low_confidence_flags`, and `evidence_refs`. Final payload allows `generated`, `partial`, `low_confidence`, and `validation_failed`. | Candidate `score_reasoning` can be missing as a warning. Final status contract exists but is not fully reflected in frontend display. | This is the model-facing and service-facing feedback schema source. |
| `apps/api/app/application/polish/feedback_validation.py` | `validate_feedback_candidate_payload`, `validate_final_feedback_payload` | Candidate validation normalizes recoverable aliases and records warnings. Final validation requires final fields, validates `score_result`, normalizes `loss_points`, and requires non-empty `trace_refs`. | Round 5 should cover recoverable parser fallback, hard validation failure, and trace requirement with focused tests. | This is the parser/validation gate that determines whether structured evaluation is valid, partial, or failed. |
| `apps/api/app/application/polish/feedback_rules.py` | `apply_feedback_core_rules` | Deterministically computes/enriches `score_result`, `answer_coverage`, `answer_change_analysis`, `feedback_cards`, `next_recommended_actions`, and low-confidence flags from the candidate payload and context. | Round 5 should verify server-side score remains authoritative and LLM-provided final score fields are not trusted. | This is the deterministic bridge between LLM candidate output and final structured evaluation. |
| `apps/api/app/domain/polish/policies/scoring_policy.py` | `ScoringPolicy.evaluate` | Computes `polish_answer` score from loss point severity on a 0-100 scale. | This is not formal `ScoreResult` persistence. Round 5 should keep it as embedded feedback scoring. | This is the existing, narrow scoring mechanism for Polish feedback. |
| `apps/api/app/infrastructure/db/models/feedback.py` | `Feedback.score_result_id` | Feedback rows can hold `score_result_id`, but current generated/failed feedback creation leaves it `None`. | The presence of the nullable column is not enough to approve formal persistence. | It documents why persistence is possible later and why this Goal must make the non-persistence decision explicit now. |
| `apps/api/app/application/scoring/use_cases.py` | `ScoringUseCases.create` | Creates formal owner-scoped `ScoreResult` rows from canonical dimensions, computes overall score, primary bottleneck, confidence, and next action type. | Not used by Polish feedback generation today. | It is a future integration point, not a Round 5 modified file for this Goal. |
| `apps/web/src/entities/polish/model/types.ts` | `PolishFeedbackPayload`, `PolishTaskStatus`, `PolishSessionAnswer` | Types include `score_result`, `loss_points`, `trace_refs`, `low_confidence_flags`, `feedback_status`, and `score_result_id`, but `PolishFeedbackPayload.status` currently narrows to `pending/generated/failed`. | Status type must represent `partial`, `low_confidence`, `validation_failed`, and `generation_failed`. | This is the frontend API contract boundary. |
| `apps/web/src/pages/interview/InterviewPage.tsx` | `buildFeedbackCardViewModel`, `resolvePolishFeedbackStatus`, `buildFeedbackTraceItems`, `buildScoreResultItems`, `buildLossPointRows`, `buildSelectedAnswerFeedbackMetaViewModel` | Feedback card renders score/loss/reference/sections. Status resolver collapses unknown statuses to `pending`; trace items are empty; failed state is separate. | Must render generated, partial, low-confidence, validation-failed, generation-failed, parser fallback, and legacy payload states without exposing raw traces. | This is the current workbench display surface used by users after answer submission. |
| `apps/web/src/pages/interview/InterviewPage.test.ts` | feedback card view-model tests | Existing tests cover feedback card sections, generated/pending/failed payloads, score result display, loss point table rows, hidden raw trace refs, and legacy payload display. | Extend these tests for the expanded status taxonomy and sanitized trace metadata. | This is the existing frontend contract-test surface. |
| `tests/api/test_polish_feedback_generation_service.py` | feedback generation tests | Existing tests cover no LLM transport failure, prompt budgets, bounded answer input, phase fields, server-side score override, and low-confidence warning behavior. | Add status taxonomy tests for partial, low-confidence, validation failure, and parser fallback. | This is the focused backend service test surface. |
| `tests/api/test_polish_feedback_models.py` and `tests/api/test_polish_feedback_pipeline_contract.py` | payload model and pipeline contract tests | Existing tests cover candidate normalization, provider metadata stripping, final payload model validation, and recoverable candidate behavior. | Add or adjust parser fallback and final status expectations if Round 5 changes status derivation. | These tests verify schema/parser boundaries without requiring HTTP setup. |
| `tests/api/test_polish_application_service_split.py` and `tests/api/test_polish_api.py` | application/API feedback tests | Existing tests cover split service boundaries, persisted feedback/task behavior, API sanitization, pending payload, generation failure, core question/answer/feedback path, retry behavior, and legacy compatibility. | Add tests proving no formal `ScoreResult` row/id is created, validation failure is distinguishable from generation failure, and saved-answer boundary remains intact. | These tests verify user-visible API behavior and persistence boundaries. |

## Requirement

### R-SEA-001 Structured Evaluation for Saved Answers

| Field | Detail |
| --- | --- |
| User-visible behavior | After a user submits an answer in the Polish workbench and requests feedback, the feedback panel displays an inspectable structured evaluation for that saved answer: summary, embedded 0-100 `polish_answer` score when available, loss points, reference answer, answer coverage/change analysis when available, next recommended actions, and status. |
| Source basis | `/tmp/interview-coach-skill/references/transcript-processing.md` and `/tmp/interview-coach-skill/references/commands/analyze.md` show structured per-unit evaluation. `/tmp/interview-coach-skill/references/rubrics-detailed.md` connects score, gaps, and fix direction. |
| AIForInterviewer landing point | `apps/api/app/application/polish/feedback_generation_service.py`, `apps/api/app/application/polish/feedback_rules.py`, `apps/api/app/api/v1/polish.py`, `apps/web/src/pages/interview/InterviewPage.tsx`. |
| Acceptance criteria | AC-SEA-001, AC-SEA-002, AC-SEA-003, AC-SEA-011. |

### R-SEA-002 Distinct Feedback Status Taxonomy

| Field | Detail |
| --- | --- |
| User-visible behavior | Users can distinguish `generated`, `partial`, `low_confidence`, `validation_failed`, `generation_failed`, `pending`, and legacy/unknown feedback states. Low-confidence and validation failure must not look like high-confidence success. |
| Source basis | `/tmp/interview-coach-skill/references/evidence-sourcing.md` requires uncertainty to be explicit. `/tmp/interview-coach-skill/references/transcript-processing.md` uses quality gates and reduced-confidence handling. |
| AIForInterviewer landing point | `apps/api/app/domain/shared/enums.py::AiTaskStatus`, `apps/api/app/application/polish/feedback_models.py::FeedbackFinalPayload`, `apps/api/app/application/polish/feedback_generation_service.py::_feedback_status`, `apps/api/app/application/polish/feedback_application_service.py::_failed_feedback_payload_for_storage`, `apps/web/src/entities/polish/model/types.ts::PolishFeedbackPayload`, `apps/web/src/pages/interview/InterviewPage.tsx::resolvePolishFeedbackStatus`. |
| Acceptance criteria | AC-SEA-004, AC-SEA-005, AC-SEA-006, AC-SEA-012. |

### R-SEA-003 Evidence, Confidence, and Trace Safety

| Field | Detail |
| --- | --- |
| User-visible behavior | Evaluation output makes evidence and low-confidence state visible through safe fields, while hiding raw prompt, raw completion, provider payload, full resume, full JD, tokens, secrets, cookies, and hidden scoring internals. |
| Source basis | `/tmp/interview-coach-skill/references/evidence-sourcing.md` requires real source grounding and plain uncertainty disclosure. |
| AIForInterviewer landing point | `apps/api/app/application/polish/feedback_prompt_assets.py::build_feedback_prompt_asset`, `apps/api/app/application/polish/feedback_validation.py::validate_final_feedback_payload`, `apps/api/app/api/v1/polish.py::_feedback_response`, `apps/web/src/pages/interview/InterviewPage.tsx::buildFeedbackTraceItems`. |
| Acceptance criteria | AC-SEA-007, AC-SEA-008, AC-SEA-009, AC-SEA-013. |

### R-SEA-004 Embedded Score Boundary

| Field | Detail |
| --- | --- |
| User-visible behavior | The feedback panel shows the embedded `PolishFeedbackPayload.score_result` as the answer evaluation score, but this Goal does not claim or create a formal persisted `ScoreResult` row. `score_result_id` remains absent/null unless another approved Goal implements formal scoring persistence later. |
| Source basis | `/tmp/interview-coach-skill/references/rubrics-detailed.md` inspires score-to-gap linkage, but AIForInterviewer code currently computes embedded Polish feedback score and separately has a formal scoring module. |
| AIForInterviewer landing point | `apps/api/app/domain/polish/policies/scoring_policy.py::ScoringPolicy.evaluate`, `apps/api/app/application/polish/feedback_rules.py::apply_feedback_core_rules`, `apps/api/app/infrastructure/db/models/feedback.py::Feedback.score_result_id`, `apps/api/app/application/scoring/use_cases.py::ScoringUseCases.create` as future non-modified integration point. |
| Acceptance criteria | AC-SEA-010, AC-SEA-014, AC-SEA-015. |

### R-SEA-005 Scope Guard Against Adjacent Capabilities

| Field | Detail |
| --- | --- |
| User-visible behavior | Round 5 improves structured evaluation of the current saved answer only. It does not add transcript analysis, storybank, outcome calibration, self-assessment delta, explicit root-cause fields, Weakness/Asset/Training/Report writes, or unrelated workflow changes. |
| Source basis | Source files for those capabilities exist, but current AIForInterviewer landing points are missing or too broad for this Goal. |
| AIForInterviewer landing point | Scope guard applies across the Round 5 allowlist and forbidden file list below. |
| Acceptance criteria | AC-SEA-016, AC-SEA-017. |

## Functional Specification

### Inputs

| Input | Source | Contract |
| --- | --- | --- |
| `session_id` | `apps/api/app/api/v1/polish.py::create_polish_feedback_task` | Existing path parameter. Must belong to authenticated owner. |
| `answer_id` | `apps/api/app/schemas/polish.py::CreateFeedbackTaskRequest` | Required. Must reference an existing saved answer under the session. Feedback generation must not accept raw answer text. |
| Saved answer text | `apps/api/app/application/polish/feedback_application_service.py::_build_feedback_generation_context` | Current answer text is the primary unit. Prompt asset must bound it with `answer_text_max_chars` and `full_answer_forbidden`. |
| Current question and question metadata | `_build_feedback_generation_context`; `apps/api/app/application/polish/feedback_prompt_assets.py::build_feedback_prompt_asset` | Bounded question text, progress node ref, question metadata, source refs, and evidence refs. |
| Same-question previous answers | `apps/api/app/application/polish/feedback_application_service.py::_feedback_same_question_answers` | Optional bounded retry/change context. Must not become full transcript ingestion. |
| Recent turns and progress node snapshot | `_feedback_recent_turns`, `_feedback_progress_node_snapshot` | Optional bounded context for repeated gaps and next actions. |
| Project asset summaries and canonical assets | `_canonical_project_asset_items`; `build_feedback_prompt_asset` | Only confirmed/safe summaries and refs. This Goal does not write formal Asset records. |
| Optional `scoring_context` | `apps/api/app/schemas/polish.py::CreateFeedbackTaskRequest.scoring_context` | Treated as existing internal optional context. Not a self-assessment contract for Round 5. |

### Outputs

| Output | Target | Contract |
| --- | --- | --- |
| Task response | `apps/api/app/schemas/polish.py::PolishTaskStatusResponse` | Must expose `status`, `user_visible_status`, `retryable`, `validation_errors`, `feedback_status`, `answer_id`, `feedback_payload`, `score_result`, `score_result_id`, `next_recommended_actions`, `low_confidence_flags`, and `trace_refs` where available. |
| Feedback payload | `apps/api/app/schemas/polish.py::PolishFeedbackPayload`; `apps/api/app/application/polish/feedback_models.py::FeedbackFinalPayload` | Must carry structured generated fields, or a safe failure payload with no fake score. |
| Embedded score | `apps/api/app/application/polish/feedback_rules.py::apply_feedback_core_rules`; `apps/api/app/domain/polish/policies/scoring_policy.py::ScoringPolicy.evaluate` | Must use 0-100 `polish_answer` scale and server-side loss-point scoring. |
| Frontend feedback card | `apps/web/src/pages/interview/InterviewPage.tsx::buildFeedbackCardViewModel` | Must render score, loss points, reference answer, structured sections, next actions, and status-specific feedback. |
| Sanitized trace metadata | `apps/web/src/pages/interview/InterviewPage.tsx::buildFeedbackTraceItems` | May show safe trace presence/count/type/status. Must not expose raw provider/prompt/completion bodies or unsafe identifiers as user-facing copy. |

### State Changes

- Generated, partial, low-confidence, validation-failed, and generation-failed feedback remain attached to the saved `Answer` through `PolishFeedback.answer_id`.
- Generated-like feedback stores `feedback_summary` as JSON via `apps/api/app/infrastructure/db/repositories/polish.py::add_feedback`.
- Failed feedback may store retryable failure payload through `_failed_feedback_payload_for_storage`.
- `Feedback.score_result_id` remains `None` for this Goal.
- No `ScoreResult` row is created by this Goal.
- No Weakness, Asset, Training, Report, transcript, storybank, outcome, calibration, or root-cause lifecycle record is created by this Goal.

### Status Taxonomy

| Status | Backend source | Frontend behavior | Score behavior |
| --- | --- | --- | --- |
| `pending` | No feedback record or pending placeholder from `apps/api/app/api/v1/polish.py::_pending_feedback_payload` | Show stable waiting/empty feedback state. | No score. |
| `generated` | Final payload validates, has no low-confidence flags and no validation warnings that force partial status. | Show standard structured feedback card. | Embedded `score_result` may display. |
| `partial` | Final payload validates but parser/core rules had recoverable warnings, missing optional model reasoning, or deterministic fallback-generated structured sections. | Show structured feedback with partial-state copy and safe warnings. | Embedded `score_result` may display if validation passed. |
| `low_confidence` | Final payload validates and `low_confidence_flags` is non-empty, or backend status explicitly says low confidence. | Show low-confidence treatment, flags, retry/provide-more-input actions, and no high-confidence success styling. | Embedded `score_result` may display with low-confidence warning; no formal `ScoreResult`. |
| `validation_failed` | Candidate/final validation failure or validation-stage metadata indicates schema/semantic validation failure and the backend can safely persist a validation-failed payload. | Show validation failure, validation errors, retry guidance, and no normal score card. | No score. |
| `generation_failed` | Provider unavailable, fake transport at runtime, no transport, timeout, provider error, context blocked, or hard failure without safe validation-failed payload. | Show generation failure and retry state. | No score. |
| `failed` | Legacy frontend/backend alias. | Treat as `generation_failed` while preserving old payload display. | No score unless a legacy payload already contains safe structured score data. |
| missing or unknown status | Legacy payload compatibility path. | If payload has safe generated content such as `feedback_text`, `score_result`, or `loss_points`, render as legacy generated-compatible card with no new claim. Otherwise render pending/unknown. | Display existing embedded score only if present. |

### Successful Structured Evaluation

1. `create_polish_feedback_task` receives a saved `answer_id`.
2. `PolishFeedbackApplicationService.create_feedback_task` loads session, answer, question, and bounded detail.
3. `FeedbackGenerationService.generate` validates context, calls provider, validates candidate payload, applies deterministic rules, validates final payload, and returns `succeeded=True`.
4. `_generated_feedback_payload_for_storage` adds server feedback id and metadata.
5. Feedback is persisted with status matching final payload category and `score_result_id=None`.
6. Frontend renders structured sections, status, embedded score, loss points, safe traces/flags, and next recommended actions.

### Partial Structured Evaluation

1. Candidate payload is recoverable or final payload is valid but contains validation warnings, such as missing optional `score_reasoning` recovered by model validation.
2. Backend stores a valid payload with `status=partial`.
3. Frontend displays score and structured sections when present, plus partial-state copy and retry/provide-more-input guidance.
4. Partial does not become formal `ScoreResult`.

### Low-Confidence Evaluation

1. Candidate, agent, or deterministic rules produce non-empty `low_confidence_flags`.
2. Backend derives `status=low_confidence` for the final payload unless a harder failure status applies.
3. Frontend shows low-confidence state distinctly and includes safe flag summaries.
4. Low-confidence score remains embedded only and cannot be represented as a high-confidence formal score.

### Validation Failure

1. Candidate or final validation fails due to schema, unsafe leakage, required final fields, invalid score, invalid loss points, or missing required `trace_refs`.
2. Backend stores a retryable validation-failed payload when it can do so safely; otherwise it stores generation-failed with validation errors.
3. Frontend displays validation failure and validation errors without score card success styling.
4. No score, formal object, or next action beyond retry/provide-more-input is created.

### Generation Failure

1. Context is blocked, LLM transport is unavailable, fake transport is injected in runtime, provider call fails, provider times out, or no safe payload can be produced.
2. Backend stores `status=generation_failed`, `score_result=None`, `loss_points=[]`, `trace_refs=[]`, `low_confidence_flags=[]`, `retryable=True`, and safe error metadata.
3. Frontend displays generation failure and retry state.
4. Answer capture remains intact.

### Parser Fallback

1. Recoverable aliases and missing optional fields are normalized by `FeedbackCandidatePayload` and `validate_feedback_candidate_payload`.
2. Fallback recovery is recorded in validation warnings and drives `partial` status when appropriate.
3. Unrecoverable identity/schema errors fail validation and do not fabricate score data.

### Legacy Response Compatibility

- Existing feedback payloads that lack new status values must remain renderable.
- Existing generated payloads with safe `score_result` and `loss_points` continue to display.
- Pending placeholders continue to display stable empty states.
- Existing tests that ensure raw `trace_refs` are not exposed must remain true; Round 5 can add sanitized trace metadata but must not print raw provider/prompt/completion content.

## Technical Design

### Affected Production Files Expected for Round 5

| File | Expected change |
| --- | --- |
| `apps/api/app/application/polish/feedback_generation_service.py` | Derive `low_confidence` status from non-empty `low_confidence_flags`; keep parser warnings mapped to `partial`; keep final validation failures from producing fake scores. |
| `apps/api/app/application/polish/feedback_application_service.py` | Map validation-stage failures to `validation_failed` payload/task state when safe; keep provider/no-transport/context failures as `generation_failed`; continue setting `score_result_id=None`. |
| `apps/api/app/schemas/polish.py` | If current schema typing blocks new statuses, widen/clarify response status fields without changing request shape. |
| `apps/api/app/api/v1/polish.py` | Preserve response fields and sanitization; adjust mapping only if backend task/payload status requires explicit response normalization. |
| `apps/web/src/entities/polish/model/types.ts` | Add explicit frontend status union for `pending`, `generated`, `partial`, `low_confidence`, `validation_failed`, `generation_failed`, `failed`, and legacy string compatibility. |
| `apps/web/src/pages/interview/InterviewPage.tsx` | Update `resolvePolishFeedbackStatus`, feedback card status handling, low-confidence/partial/validation/generation failure copy, and sanitized trace item generation. |

### Affected Test Files Expected for Round 5

| File | Expected test coverage |
| --- | --- |
| `tests/api/test_polish_feedback_generation_service.py` | Generated, partial, low-confidence, validation-failed, generation-failed, parser fallback, no fake score, trace required. |
| `tests/api/test_polish_feedback_models.py` | Candidate model parser fallback and final status model behavior if model-level change is needed. |
| `tests/api/test_polish_feedback_pipeline_contract.py` | Provider metadata stripping, recoverable candidate, final status/trace contract. |
| `tests/api/test_polish_application_service_split.py` | Saved-answer boundary, persisted failure status distinction, `score_result_id=None`, no formal `ScoreResult` creation through feedback path. |
| `tests/api/test_polish_api.py` | HTTP response status taxonomy, legacy compatibility, API sanitization, no raw answer bypass in feedback request. |
| `apps/web/src/pages/interview/InterviewPage.test.ts` | Frontend status mapping, safe low-confidence/trace display, partial/validation/generation failure cards, legacy payload display. |

### Data Model and Response Contract Changes

- No database migration.
- No new endpoint.
- No request body shape change.
- `CreateFeedbackTaskRequest` remains `answer_id` plus optional `scoring_context`.
- `PolishFeedbackPayload.status` and frontend status view models expand to cover existing backend statuses.
- `PolishFeedbackPayload.score_result` remains embedded feedback score data.
- `Feedback.score_result_id` remains nullable and unpopulated by this Goal.
- Formal `ScoreResult` integration is explicitly deferred.

### API and Service Implications

- `POST /api/v1/polish-sessions/{session_id}/feedback` continues returning `202 accepted`.
- Response data must distinguish feedback payload status from task status where they differ.
- Validation failures must be visible through `status`, `feedback_status`, `validation_errors`, `user_visible_status`, and/or safe error metadata.
- Backend must not collapse low-confidence or partial into generated success.
- Existing answer capture path is untouched.

### LLM Prompt and Output Schema Changes

- No provider-facing schema expansion is required for Round 5.
- `FeedbackCandidatePayload` remains candidate-only.
- LLM candidate output remains unable to author final `score_result`, `feedback_id`, final metadata, or formal score references.
- Service code remains authoritative for final status, score, coverage, feedback cards, and next actions.
- If tests reveal prompt/schema ambiguity around `low_confidence_flags`, Round 5 may clarify existing prompt rules in `apps/api/app/application/polish/feedback_prompt_assets.py` only with explicit GPT review approval. That file is not in the default Round 5 allowlist.

### Parser and Validation Logic

- Recoverable candidate normalization maps to `partial`.
- Non-empty `low_confidence_flags` maps to `low_confidence` unless a harder failure applies.
- Missing final `trace_refs` remains validation failure.
- Unsafe marker detection remains a hard failure.
- Missing optional `score_reasoning` remains a warning, not a hard error.
- LLM-provided final score fields remain ignored or rejected as candidate-forbidden/final-forbidden according to existing validators.

### Frontend Status Mapping

- `resolvePolishFeedbackStatus` must return an expanded status, not collapse unknown values to `pending` by default.
- `failed` maps to `generation_failed` as legacy alias.
- `validation_failed` and `generation_failed` must have separate card states.
- `partial` and `low_confidence` must render structured content when available, with clear state copy and actions.
- Legacy generated payloads without status continue rendering structured content.
- Sanitized trace metadata may render, but raw trace ids and raw payload markers stay hidden from visible copy.

### Persistence Decision

Round 5 must not call `ScoringUseCases.create`, must not use `SqlAlchemyScoringRepository.add_score_result`, and must not write `score_results` from Polish feedback generation. The only score displayed by this Goal is embedded `PolishFeedbackPayload.score_result` generated by Polish feedback rules.

### Compatibility and Rollback Notes

- The change is backward-compatible if new statuses are optional and frontend handles legacy payloads.
- Rollback can revert status derivation/display changes without data migration.
- Existing feedback rows remain readable because status interpretation is defensive.
- `generation_failed` failure payloads with no score remain valid.

## Implementation Plan

1. Read `G-003-structured-answer-evaluation.md`, `AGENTS.md`, `docs/00-governance/DOCS_INDEX.md`, `apps/api/app/application/polish/feedback_generation_service.py`, `apps/api/app/application/polish/feedback_application_service.py`, `apps/api/app/schemas/polish.py`, `apps/api/app/api/v1/polish.py`, `apps/web/src/entities/polish/model/types.ts`, and `apps/web/src/pages/interview/InterviewPage.tsx`.
2. Add backend service tests in `tests/api/test_polish_feedback_generation_service.py` proving a valid payload with warnings becomes `partial`, a valid payload with `low_confidence_flags` becomes `low_confidence`, validation failure returns no score, and no-transport/provider failure remains `generation_failed`.
3. Add parser/model tests in `tests/api/test_polish_feedback_models.py` or `tests/api/test_polish_feedback_pipeline_contract.py` only for any parser fallback or model status behavior changed by Step 2.
4. Update `apps/api/app/application/polish/feedback_generation_service.py::_feedback_status` so non-empty `low_confidence_flags` maps to `low_confidence`, validation warnings map to `partial`, and generated remains the default only when neither condition exists.
5. Add application/API tests in `tests/api/test_polish_application_service_split.py` and `tests/api/test_polish_api.py` proving validation-stage failures are distinct from provider generation failures, `score_result_id` remains `None`, and feedback generation still consumes only saved `answer_id`.
6. Update `apps/api/app/application/polish/feedback_application_service.py::_failed_feedback_payload_for_storage` and `create_feedback_task` only as needed to store/return `validation_failed` separately from `generation_failed`.
7. Update `apps/api/app/schemas/polish.py` only if current schema types reject the expanded status response.
8. Update `apps/api/app/api/v1/polish.py` only if response normalization is required to pass the API tests; keep forbidden payload sanitization intact.
9. Add frontend tests in `apps/web/src/pages/interview/InterviewPage.test.ts` for `partial`, `low_confidence`, `validation_failed`, `generation_failed`, legacy `failed`, unknown status with generated-looking legacy payload, and sanitized trace metadata.
10. Update `apps/web/src/entities/polish/model/types.ts` to model expanded feedback status while retaining string compatibility for legacy backend values.
11. Update `apps/web/src/pages/interview/InterviewPage.tsx::resolvePolishFeedbackStatus`, `buildFeedbackCardViewModel`, and `buildFeedbackTraceItems` to render the expanded status taxonomy and sanitized trace metadata.
12. Run focused backend tests for feedback generation/model/pipeline/application/API.
13. Run `npm --workspace apps/web run test`.
14. Run `git diff --check`, `git status --short --untracked-files=all`, `git status --short -- AGENTS.md`, and `git diff -- AGENTS.md`.
15. Update `.codex-temp/interview-coach-refactor/05-goals/G-003-structured-answer-evaluation.md` and `.codex-temp/interview-coach-refactor/CONTROL.md` with Round 5 implementation evidence only after implementation and validation are complete.

## Round 5 Affected-File Allowlist

### Production Files Allowed to Modify

- `apps/api/app/application/polish/feedback_generation_service.py`
- `apps/api/app/application/polish/feedback_application_service.py`
- `apps/api/app/schemas/polish.py`
- `apps/api/app/api/v1/polish.py`
- `apps/web/src/entities/polish/model/types.ts`
- `apps/web/src/pages/interview/InterviewPage.tsx`

### Test Files Allowed to Modify

- `tests/api/test_polish_feedback_generation_service.py`
- `tests/api/test_polish_feedback_models.py`
- `tests/api/test_polish_feedback_pipeline_contract.py`
- `tests/api/test_polish_application_service_split.py`
- `tests/api/test_polish_api.py`
- `apps/web/src/pages/interview/InterviewPage.test.ts`

### Temporary Files to Update After Round 5 Implementation

- `.codex-temp/interview-coach-refactor/05-goals/G-003-structured-answer-evaluation.md`
- `.codex-temp/interview-coach-refactor/CONTROL.md`

### Files Explicitly Forbidden for Round 5

- `AGENTS.md`
- `docs/**`
- `archive/**`
- `apps/api/migrations/**`
- `apps/api/app/api/v1/scoring.py`
- `apps/api/app/schemas/scoring.py`
- `apps/api/app/application/scoring/**`
- `apps/api/app/domain/scoring/**`
- `apps/api/app/infrastructure/db/models/scoring.py`
- `apps/api/app/infrastructure/db/repositories/scoring.py`
- `tests/api/test_scoring_api.py`
- Any new transcript, storybank, outcome, calibration, Weakness, Asset, Training, Report, or command-routing module

### Capabilities Explicitly Forbidden for Round 5

- Formal `ScoreResult` persistence for Polish feedback
- Transcript upload, transcript parser, speaker normalization, transcript quality gate
- Storybank, story mapping, story usage/freshness tracking
- Outcome log, recruiter/interviewer feedback capture, outcome-score correlation, scoring drift calibration
- Self-assessment delta UI, request field, persistence, or calibration metric
- Explicit `root_cause` fields or cross-session root-cause lifecycle
- Automatic Weakness, Asset, Training, Report, Review, or formal object writes from feedback
- Copying interview-coach commands, command names, directory model, prompt wording, output wording, scoring vocabulary, 1-5 anchors, hire/no-hire labels, or coaching voice

## Acceptance Criteria

| AC ID | Requirement mapping | Criterion |
| --- | --- | --- |
| AC-SEA-001 | R-SEA-001 | Generated feedback displays embedded `score_result.score_value`, `score_type=polish_answer`, loss point table rows, reference answer, and next recommended actions in the selected answer feedback panel. |
| AC-SEA-002 | R-SEA-001 | Server-side rules remain authoritative for embedded score; LLM candidate output cannot set final score authority directly. |
| AC-SEA-003 | R-SEA-001 | Recoverable parser fallback creates a valid `partial` evaluation with warnings rather than crashing or fabricating unsupported fields. |
| AC-SEA-004 | R-SEA-002 | API/task/payload/frontend can distinguish `generated`, `partial`, `low_confidence`, `validation_failed`, `generation_failed`, `pending`, and legacy `failed`. |
| AC-SEA-005 | R-SEA-002 | Low-confidence feedback is visible as low confidence and is not styled or copied as high-confidence success. |
| AC-SEA-006 | R-SEA-002 | Validation failure and generation failure show different user-visible states and both remain retryable or actionable without deleting the saved answer. |
| AC-SEA-007 | R-SEA-003 | Final generated/partial/low-confidence payloads include non-empty `trace_refs`; missing `trace_refs` fails validation. |
| AC-SEA-008 | R-SEA-003 | Frontend displays only sanitized trace metadata and does not expose raw prompt, provider payload, completion, full resume, full JD, token, secret, cookie, or raw trace body. |
| AC-SEA-009 | R-SEA-003 | API sanitization tests continue to reject or strip forbidden feedback payload keys and unsafe values. |
| AC-SEA-010 | R-SEA-004 | Generated feedback persists with `Feedback.score_result_id=None` and no new `score_results` row is created by the feedback generation path. |
| AC-SEA-011 | R-SEA-001 | Existing pending and legacy feedback payloads continue to render without runtime errors. |
| AC-SEA-012 | R-SEA-002 | `resolvePolishFeedbackStatus` no longer maps every unknown status to `pending`; generated-looking legacy payloads stay readable, and truly unknown empty payloads render as pending/unknown. |
| AC-SEA-013 | R-SEA-003 | `low_confidence_flags` and `validation_errors` are visible enough for user action, while retaining safe copy. |
| AC-SEA-014 | R-SEA-004 | Round 5 does not modify scoring API/use cases/repositories/models or `tests/api/test_scoring_api.py`. |
| AC-SEA-015 | R-SEA-004 | Formal `ScoreResult` persistence remains a documented deferred decision, not an implied implementation. |
| AC-SEA-016 | R-SEA-005 | No transcript, storybank, outcome calibration, self-assessment delta, explicit root-cause field, or command-routing capability is added. |
| AC-SEA-017 | R-SEA-005 | No Weakness, Asset, Training, Report, Review, or other formal object is written from structured answer evaluation. |

## Validation Plan

### No-Code Round Validation

| Command | Expected result |
| --- | --- |
| `git status --short --untracked-files=all` | Only allowed `.codex-temp/interview-coach-refactor/**` files are modified/untracked. |
| `git diff --check` | Exit 0, no whitespace errors. |
| `git status --short -- AGENTS.md` | No output. |
| `git diff -- AGENTS.md` | No output. |

### Round 5 Backend Validation

| Command | Expected result |
| --- | --- |
| `.venv/bin/python -m pytest tests/api/test_polish_feedback_generation_service.py -q` | Focused feedback generation tests pass. |
| `.venv/bin/python -m pytest tests/api/test_polish_feedback_models.py tests/api/test_polish_feedback_pipeline_contract.py -q` | Parser/model/pipeline contract tests pass. |
| `.venv/bin/python -m pytest tests/api/test_polish_application_service_split.py -q` | Application split and persistence boundary tests pass. |
| `.venv/bin/python -m pytest tests/api/test_polish_api.py -q` | Polish API contract, status, sanitization, legacy compatibility, and no raw answer bypass tests pass. |

### Round 5 Frontend Validation

| Command | Expected result |
| --- | --- |
| `npm --workspace apps/web run test` | TypeScript test command exits 0. |
| `npm --workspace apps/web run build` | Optional before merge; exits 0 if Round 5 reviewer asks for build validation. |

### Round 5 Scope Validation

| Command | Expected result |
| --- | --- |
| `git status --short --untracked-files=all` | Only Round 5 allowlisted production/test/temp files changed. |
| `git diff --stat` | Diff paths match the allowlist. |
| `git diff --check` | Exit 0. |
| `git status --short -- AGENTS.md` | No output. |
| `git diff -- AGENTS.md` | No output. |
| `rg -n "transcript|storybank|outcome|self_assessment|root_cause|ScoreResult\\(|ScoringUseCases\\.create|add_score_result" apps/api/app/application/polish apps/web/src/pages/interview apps/web/src/entities/polish tests/api apps/web/src/pages/interview/InterviewPage.test.ts` | Any matches are reviewed. New matches must be only explicit non-goal assertions or existing allowed references, not new capability implementation. |

### Manual Validation

- Submit an answer in the Polish workbench, trigger feedback, and inspect generated feedback card.
- Force a low-confidence fixture or mocked response and confirm the feedback panel shows low confidence.
- Force a candidate/final validation error and confirm validation failure differs from provider/generation failure.
- Confirm retry state is visible and the saved answer remains in the turn list.
- Confirm raw trace ids, prompt text, provider payload, full resume, full JD, tokens, secrets, and cookies are not visible.

## Risks

| Risk | Detail | Mitigation |
| --- | --- | --- |
| Implementation risk | Status derivation touches backend service, application persistence, API response, frontend types, and frontend view models. | Keep Round 5 allowlist narrow and add tests before behavior changes. |
| Compatibility risk | Existing payloads may have missing or legacy status values. | Preserve legacy render path and keep unknown/empty payload handling defensive. |
| LLM output instability risk | Candidate output may omit optional fields, include aliases, or include low-confidence flags inconsistently. | Keep service-side deterministic rules authoritative and test parser fallback. |
| Parser/fallback risk | Recoverable errors could be over-promoted to generated success or hard failures could be hidden. | Map recoverable warnings to `partial`; hard validation failures to `validation_failed` or safe `generation_failed`. |
| Persistence risk | Presence of `Feedback.score_result_id` and formal `ScoreResult` tables can tempt a broad persistence change. | Explicitly defer formal score persistence and forbid scoring module changes in Round 5. |
| Frontend display risk | Displaying traces or validation details could expose internal or unsafe data. | Only show sanitized trace metadata and keep raw payload/prompt/provider content hidden. |
| Scope creep risk | Structured evaluation is adjacent to transcript analysis, storybank, outcome calibration, self-assessment delta, and root-cause lifecycle. | Keep these as explicit Defer decisions and forbid related files/capabilities. |
| Design-code drift risk | Active docs describe richer formal scoring than current Polish feedback code. | Round 5 implements only current-code-backed response/status behavior; active doc migration happens later after evidence. |

## Migration Notes for Active Doc

Later, after GPT review, Round 5 implementation, and validation, `docs/active/interview-coach-refactor.md` should receive only a concise active-doc migration summary:

- `G-003 Structured Answer Evaluation` improves the existing Polish feedback path for saved answers.
- It formalizes response-level structured evaluation status taxonomy: `generated`, `partial`, `low_confidence`, `validation_failed`, `generation_failed`, `pending`, and legacy compatibility.
- It keeps `CreateFeedbackTaskRequest(answer_id)` as the saved-answer boundary and does not add raw answer feedback generation.
- It keeps `PolishFeedbackPayload.score_result` embedded and defers formal `ScoreResult` persistence.
- It includes safe `trace_refs` / `low_confidence_flags` visibility without raw prompt/provider payload exposure.
- It explicitly excludes transcript analysis, storybank, outcome calibration, self-assessment delta, explicit root-cause fields, and automatic formal object writes.

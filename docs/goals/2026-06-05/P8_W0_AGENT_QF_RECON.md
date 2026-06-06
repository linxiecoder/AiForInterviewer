---
title: P8_W0_AGENT_QF_RECON
type: report
status: warn
owner: P8-W0 Question / Feedback Integration Recon Agent
permalink: ai-for-interviewer/docs/goals/2026-06-05/p8-w0-agent-qf-recon
---

# P8-W0 Question / Feedback Integration Recon

Status: warn

本报告只记录 P8-W0 Question / Feedback read-only recon 结果，不声明 Phase 8 done，不授权实现补丁。当前代码存在可连接的 Question / Feedback planned workflow bridge；主要风险是 Feedback runtime 仍是 skeleton / generic candidate ref 形态，尚未产出 typed `feedback_candidate` / `asset_update_candidate` payload。

## Scope Lock

- task_id: P8-W0-QF-RECON
- allowed_ops: READ_ONLY；唯一写入本报告 `docs/goals/2026-06-05/P8_W0_AGENT_QF_RECON.md`
- forbidden_ops: 修改代码、依赖、配置、测试；改 prompt/provider/API/DB/frontend；绕过 handoff formal write；实现 Phase 11 / Phase 12；声称 L5 或 Phase 8 done
- done_condition: 读当前代码和项目源，指出 runtime adapter 可连接点、candidate refs、handoff/trace refs、P5/P6 语义风险、推荐 patch scope 和 stop conditions

## Files Read

- `AGENTS.md`
- `docs/00-governance/DOCS_INDEX.md`
- `docs/tmp/goal0605/phase8_codex_goal_pack/docs/P8_MASTER_GOAL.md`
- `docs/tmp/goal0605/phase8_codex_goal_pack/agents/C_QUESTION_FEEDBACK_INTEGRATION_RECON.md`
- `docs/project-sources/03_AGENT_PLATFORM_ARCHITECTURE.md`
- `docs/project-sources/17_PHASE_ROADMAP_LOCK.md`
- `docs/project-sources/18_AGENT_PLATFORM_C_TARGET.md`
- `docs/goals/README.md`
- `docs/goals/2026-06-05/P5P6-W1-C2-C3-PLANNED-WORKFLOW-L5-FOUNDATION/P5P6_W1_SCOPE_LOCK.md`
- `docs/goals/2026-06-05/P5P6-W1-C2-C3-PLANNED-WORKFLOW-L5-FOUNDATION/P5P6_W1_CLOSEOUT_REPORT.md`
- `docs/goals/2026-06-05/P5P6-W1.fix.02-VALIDATION-BLOCKER-REMEDIATION/P5P6_W1_FIX02_CLOSEOUT_REPORT.md`
- `apps/api/app/application/polish/agents/question/__init__.py`
- `apps/api/app/application/polish/agents/question/planned_workflow.py`
- `apps/api/app/application/polish/agents/feedback/__init__.py`
- `apps/api/app/application/polish/agents/feedback/planned_workflow.py`
- `apps/api/app/application/polish/use_cases.py`
- `apps/api/app/application/polish/feedback_rules.py`
- `apps/api/app/application/polish/feedback_validation.py`
- `apps/api/app/application/agents/runtime/__init__.py`
- `apps/api/app/application/agents/contracts/__init__.py`
- `apps/api/app/application/ai_runtime/contracts.py`
- `apps/api/app/application/ai_runtime/facade.py`
- `apps/api/app/application/ai_runtime/business_graphs/polish_question_graph.py`
- `apps/api/app/application/ai_runtime/business_graphs/polish_feedback_graph.py`
- `apps/api/app/infrastructure/ai_runtime/langgraph/polish_question_runtime.py`
- `apps/api/app/infrastructure/ai_runtime/langgraph/serializer.py`
- `tests/api/test_polish_question_graph_integration.py`
- `tests/api/test_pr5_polish_question_graph_persistence_handoff.py`
- `tests/api/test_pr5_polish_question_graph_candidate_parity.py`
- `tests/api/test_polish_canonical_evidence.py`
- `tests/api/test_polish_feedback_generation_service.py`
- `tests/api/test_polish_feedback_generation_schema.py`
- `tests/api/test_polish_feedback_runtime.py`
- `tests/api/test_polish_feedback_agent_io_alignment.py`
- `tests/architecture/test_agent_platform_c1_boundary.py`

## Findings

1. GITHUB_CODE: Question planned workflow is an application bridge that builds a `question_candidate` without writing formal data. `run_question_planned_workflow()` accepts either `generation_result` or `candidate_payload`, adds `planned_workflow`, `candidate_output`, `handoff_contract`, `trace_contract`, policy/skill/tool refs, and `fallback_reported_as_generated_success=false`; `build_question_candidate_validation_task()` returns `TraceRef(... trace_type="question_candidate")` with candidate refs, not a formal question write. Evidence: `apps/api/app/application/polish/agents/question/planned_workflow.py:78-164`, `apps/api/app/application/polish/agents/question/planned_workflow.py:278-296`, `apps/api/app/application/polish/agents/question/planned_workflow.py:451-474`.

2. GITHUB_CODE: `create_question_task()` already has the lowest-risk runtime adapter connection point. Graph path calls `_graph_status_candidate_payload()` then `run_question_planned_workflow()` before `build_question_result_write_plan()` and `AgentPersistenceHandoff().write_question_result()`; direct service fallback also calls `run_question_planned_workflow()` before any write plan. Evidence: `apps/api/app/application/polish/use_cases.py:583-648`, `apps/api/app/application/polish/use_cases.py:688-826`.

3. GITHUB_CODE: Question runtime can already emit typed candidate payloads. `PolishQuestionGraphRuntime.start()` maps agent output through `build_agent_candidate_payload_from_runtime_output()` into `AgentRunResult.candidate_payloads`, with `formal_refs=()` and `formal_write_blocked=True`; `AiOrchestrationFacade._status_ref()` preserves these payloads into `AgentTaskStatusRef`. Evidence: `apps/api/app/infrastructure/ai_runtime/langgraph/polish_question_runtime.py:98-198`, `apps/api/app/infrastructure/ai_runtime/langgraph/serializer.py:71-107`, `apps/api/app/application/ai_runtime/facade.py:287-297`.

4. GITHUB_CODE: Feedback planned workflow produces candidate refs and handoff metadata, but only after `FeedbackGenerationService.generate()` succeeds. `build_feedback_planned_handoff()` sets `candidate_output="feedback_candidate"`, `handoff_contract`, `trace_contract`, policy/validation/trace refs, `asset_update_formal_write_performed=false`, and `asset_update_user_confirmation_required`. It normalizes asset update candidates to `user_confirmation_required=true` and blocks formal asset write until confirmation. Evidence: `apps/api/app/application/polish/agents/feedback/planned_workflow.py:37-99`, `apps/api/app/application/polish/agents/feedback/planned_workflow.py:119-149`, `apps/api/app/application/polish/agents/feedback/planned_workflow.py:196-215`.

5. GITHUB_CODE: `create_feedback_task()` currently does not call `AiOrchestrationFacade.start_polish_feedback_generation()`. It calls `FeedbackGenerationService.generate()`, then wraps the generated payload with `build_feedback_planned_handoff()` before persisting feedback and task candidate refs. Evidence: `apps/api/app/application/polish/use_cases.py:1037-1123`; facade method exists at `apps/api/app/application/ai_runtime/facade.py:88-107`.

6. GITHUB_CODE: Feedback runtime graph remains skeleton-level for Q/F integration purposes. `run_polish_feedback_skeleton()` returns generic `output_refs`, `formal_refs=()`, and sanitized metadata, but no `candidate_payloads`; `_build_output_refs()` names candidate output as generic `candidate_ref_...`, not typed `feedback_candidate_ref_...` or `asset_update_candidate_ref_...`. Evidence: `apps/api/app/application/ai_runtime/business_graphs/polish_feedback_graph.py:157-196`, `apps/api/app/application/ai_runtime/business_graphs/polish_feedback_graph.py:491-513`.

7. GITHUB_CODE: AgentExecutor and C4-adjacent contracts are present as ports/contracts. `AgentExecutor` exposes start/resume/replay/status/timeline/cancel; `AgentExecutionResult` exposes `candidate_refs`, `trace`, `handoff_refs`, and metadata before handoff. Evidence: `apps/api/app/application/agents/runtime/__init__.py:13-24`, `apps/api/app/application/agents/contracts/__init__.py:208-276`.

8. PROJECT_SOURCE: Project source requires AgentExecutor to return candidate refs, record trace, not write formal business facts, and not bypass handoff. Candidate-only outputs include `question_candidate`, `feedback_candidate`, and `asset_update_candidate`. Evidence: `docs/project-sources/18_AGENT_PLATFORM_C_TARGET.md:299-330`.

9. PROJECT_SOURCE: Current P5/P6 status is C2/C3 L2 planned guarded workflow, not Phase 8 runtime, not Phase 11/12, not L5 release. Question is normalized to `question_candidate` before formal write decision; Feedback records `feedback_candidate` refs and asset update candidates require confirmation. Evidence: `docs/project-sources/17_PHASE_ROADMAP_LOCK.md:301-309`, `docs/project-sources/17_PHASE_ROADMAP_LOCK.md:348-370`.

10. TEST_RESULT: No tests were run in this recon because the task is read-only and only this report may be written. Recorded validation from the latest P5/P6 fix.02 closeout says focused Question, Feedback, eval, broad selector, and architecture commands passed: canonical evidence `1 passed`, Question persistence handoff `15 passed`, Question graph integration `12 passed`, Question phase1 refactor `64 passed`, Feedback runtime `7 passed`, evals `19 passed`, Question eval `3 total / 0 failed`, Feedback eval `5 total / 0 failed`, broad selector `300 passed, 323 deselected`, architecture `33 passed, 2 xfailed`. Evidence: `docs/goals/2026-06-05/P5P6-W1.fix.02-VALIDATION-BLOCKER-REMEDIATION/P5P6_W1_FIX02_CLOSEOUT_REPORT.md:43-58`.

11. TEST_RESULT: Test source asserts current candidate-only behavior. Question tests assert `run_question_planned_workflow` is invoked, validation failures return `question_candidate`, candidate refs include agent/candidate/validation/trace and exclude formal `question`, and metadata keeps `fallback_reported_as_generated_success=false`. Feedback runtime tests assert `feedback_candidate` refs, planned workflow metadata, handoff contract, and no formal asset update. Architecture tests assert Question exposes only `question_candidate` and Feedback exposes `feedback_candidate` / `asset_update_candidate`. Evidence: `tests/api/test_polish_question_graph_integration.py:60-90`, `tests/api/test_polish_question_graph_integration.py:190-205`, `tests/api/test_pr5_polish_question_graph_persistence_handoff.py:439-464`, `tests/api/test_polish_feedback_runtime.py:270-300`, `tests/architecture/test_agent_platform_c1_boundary.py:231-281`.

## Gaps

- Feedback has no typed runtime candidate payload path yet. The existing feedback graph skeleton does not emit `AgentCandidatePayload` and does not output `feedback_candidate` / `asset_update_candidate` refs that can be consumed by the current planned handoff.
- `create_feedback_task()` is not wired to `AiOrchestrationFacade.start_polish_feedback_generation()`. A P8 adapter can be connected there only after typed feedback candidate payload semantics are defined or bridged into `build_feedback_planned_handoff()`.
- Question generation service hard failure before a draft still returns a `validation_result` task with progress/evidence refs, not a `question_candidate` task. That may be acceptable for failed provider/config paths, but P8 should explicitly preserve fail-closed semantics and avoid reporting generated success.
- Current `AgentExecutionPlan` contract is still lighter than the full P8 project-source target: max_steps/max_retries/timeout/stop_conditions are in project source but not in this contract object. This is outside Q/F planned workflow scope but affects adapter readiness.
- This recon did not fresh-run pytest/evals. Treat recorded TEST_RESULT evidence as prior validation, not current execution proof.

## Recommended Patch Scope

- Question:
  - Reuse `AiOrchestrationFacade.start_polish_question_generation()` and existing `_graph_status_candidate_payload()` / `run_question_planned_workflow()` connection.
  - If P8 introduces a new AgentExecutor adapter, make it return `AgentTaskStatusRef` / `AgentCandidatePayload` compatible with current runtime policy and `question_candidate` schema instead of changing prompt/provider/API behavior.
  - Keep formal write routed through `build_question_result_write_plan()` and `AgentPersistenceHandoff().write_question_result()` only after planned workflow validation accepts the candidate.

- Feedback:
  - Add only a thin adapter/bridge that can map runtime output to the existing `build_feedback_planned_handoff()` input shape.
  - Prefer producing typed `AgentCandidatePayload` or an equivalent typed runtime output for `feedback_candidate` and optional `asset_update_candidate`; do not persist feedback from generic `candidate_ref_...` alone.
  - Preserve current `FeedbackGenerationService.generate()` behavior, `feedback_rules.py`, and `feedback_validation.py` semantics.

- Focused tests to add or update after controller approval:
  - Question adapter compatibility in `tests/api/test_polish_question_graph_integration.py` or `tests/api/test_pr5_polish_question_graph_persistence_handoff.py`.
  - Feedback runtime typed candidate/handoff behavior in `tests/api/test_polish_feedback_runtime.py`.
  - Candidate-only / handoff architecture guard in `tests/architecture/test_agent_platform_c1_boundary.py` or a Phase 8-specific architecture test.

## Recommended Forbidden Files

- `apps/api/app/application/polish/question_generation_prompts.py`
- `apps/api/app/application/polish/feedback_prompt_assets.py`
- `apps/api/app/application/polish/*prompt*`
- `apps/api/app/application/ai_provider/**`
- `apps/api/app/infrastructure/llm/**`
- `apps/api/app/infrastructure/db/**`
- database migrations
- `apps/api/app/api/v1/**`
- frontend paths
- `domain/polish/policies/**`
- production fake provider wiring
- any file that would require prompt/provider/API/DB behavior changes to make Q/F runtime wiring pass

## Stop-Condition Findings

- No hard stop condition is triggered by this recon alone.
- Stop if implementation requires prompt rewrite, provider behavior change, DB migration, API contract change, frontend change, or domain policy behavior change.
- Stop if Feedback runtime wiring tries to report success from generic `candidate_ref_...` without typed `feedback_candidate` / `asset_update_candidate` payload or planned handoff metadata.
- Stop if any runtime path writes a formal Question, Feedback, or Asset directly, bypassing Application Service -> Domain Policy -> Handoff -> Repository / Transaction.
- Stop if implementation weakens asset update user confirmation, allows `generate_next_question` on asset conflict/unresolved feedback, or reports provider/fallback/validation failure as generated success.
- Stop if any report or code comment marks Phase 8, Phase 11/12, autonomous Agent, L5 release gate, or C4 runtime foundation as done without the P8 master done criteria.

Confidence: high


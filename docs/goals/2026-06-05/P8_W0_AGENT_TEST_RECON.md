---
title: P8_W0_AGENT_TEST_RECON
type: report
status: recon_done_warn
owner: P8-W0-Test-Architecture-Gate-Recon
permalink: ai-for-interviewer/docs/goals/2026-06-05/p8-w0-agent-test-recon
---

# P8-W0 Agent Test / Architecture Gate Recon

Status: warn

本报告是 P8-W0 Test / Architecture Gate Recon 的只读结果。未修改代码、依赖、配置或测试；未运行 pytest 长测试；不声称 Phase 8 done。

## Scope Lock

task_id: N/A - P8 goal pack recon；未新开 AIFI-* 任务。
window_id: P8-W0-TEST-ARCHITECTURE-GATE-RECON
allowed_ops: READ_ONLY + EDIT_ONE_FILE
allowed_write_file: `docs/goals/2026-06-05/P8_W0_AGENT_TEST_RECON.md`
forbidden_ops: code edit, dependency edit, config edit, test edit, API/DB/frontend/prompt/provider behavior change, Phase8 done claim, L5 claim
done_condition: 产出测试 / 架构门禁 recon 报告，列出现有 must-pass 测试、Phase8 测试缺口、focused validation 顺序、full backend 命令和 frontend 适用性。

## Files read

- `AGENTS.md`
- `docs/00-governance/DOCS_INDEX.md`
- `docs/00-governance/TEST_POLICY.md`
- `docs/03-delivery/DELIVERY_PLAN.md`
- `docs/03-delivery/BACKLOG.md`
- `docs/tmp/goal0605/phase8_codex_goal_pack/docs/P8_MASTER_GOAL.md`
- `docs/tmp/goal0605/phase8_codex_goal_pack/validation/P8_VALIDATION_COMMANDS.md`
- `docs/tmp/goal0605/phase8_codex_goal_pack/agents/D_TEST_GATE_RECON.md`
- `pytest.ini`
- `requirements.txt`
- `package.json`
- `apps/web/package.json`
- `apps/api/app/application/agents/runtime/__init__.py`
- `tests/architecture/test_agent_platform_c0_boundary.py`
- `tests/architecture/test_agent_platform_c1_boundary.py`
- `tests/architecture/test_application_boundary.py`
- `tests/architecture/test_domain_polish_policy_boundary.py`
- `tests/architecture/test_provider_boundary_static.py`
- `tests/api/test_agent_contracts.py`
- `tests/api/test_agent_graph_runner.py`
- `tests/api/test_agent_runtime_flags.py`
- `tests/api/test_agent_candidate_payload_runtime_mapping.py`
- `tests/api/test_agent_fake_runtime.py`
- `tests/api/test_agent_interrupt_replay.py`
- `tests/api/test_agent_interrupt_repository.py`
- `tests/api/test_agent_replay_resume_policy.py`
- `tests/api/test_agent_side_effect_idempotency.py`
- `tests/api/test_agent_run_repository.py`
- `tests/api/test_ai_orchestration_facade.py`
- `tests/api/test_app_bootstrap.py`
- `tests/api/test_langgraph_dependency_spike.py`
- `tests/api/test_model_imports.py`
- `tests/api/test_pr4_fake_runtime_replay_resume.py`
- `tests/api/test_pr4_provider_gate.py`
- `tests/api/test_pr4_runtime_architecture_boundary.py`
- `tests/api/test_pr4_runtime_checkpointer.py`
- `tests/api/test_pr4_runtime_serializer.py`
- `tests/api/test_pr5_business_graph_boundaries.py`
- `tests/api/test_pr5_business_graph_skeleton.py`
- `tests/api/test_pr5_polish_question_graph_skeleton.py`
- `tests/api/test_pr5_polish_question_graph_candidate_parity.py`
- `tests/api/test_pr5_polish_question_graph_persistence_handoff.py`
- `tests/api/test_pr5_polish_question_quality_gate.py`
- `tests/api/test_pr5_polish_question_scenario_derivation.py`
- `tests/api/test_pr6_polish_fake_runtime_integration.py`
- `tests/api/test_pr7_polish_readonly_parity_gate.py`
- `tests/api/test_pr8_polish_provider_trace_gate.py`
- `tests/api/test_polish_question_graph_integration.py`
- `tests/api/test_polish_feedback_runtime.py`
- `tests/api/test_polish_question_refactor_phase1.py`
- `tests/api/test_polish_api.py`
- `tests/api/test_polish_candidates.py`
- `tests/api/test_polish_canonical_evidence.py`
- `tests/api/test_polish_feedback_agent_io_alignment.py`
- `tests/api/test_polish_feedback_generation_schema.py`
- `tests/api/test_polish_feedback_generation_service.py`
- `tests/evals/test_ai_eval_code_rules.py`
- `tests/evals/test_ai_eval_runners.py`
- Test directory and function inventory via `find` / `rg` over `tests/architecture`, `tests/application`, `tests/api`, `tests/evals`.

## Findings

1. [PROJECT_SOURCE] P8 goal pack defines Phase 8 as C4 LangGraph / multi-agent runtime foundation, not Phase 11 Supervisor, Phase 12 L5 release gate, or formal F8/M8 MVP release. The required test recon scope is `tests/architecture/**`, `tests/application/**`, `tests/api/**`, and `tests/evals/**`.

2. [PROJECT_SOURCE] P8 validation commands require `git status --short`, `git diff --check`, focused architecture tests, focused runtime/application tests, `tests/api/test_agent*`, `tests/api/test_polish*`, full backend `python -m pytest -q`, and frontend only if frontend/API contract changed.

3. [GITHUB_CODE] `tests/application/` does not exist. Therefore `python -m pytest tests/application -q` or `python -m pytest tests/application/agents -q` is not currently a valid focused command unless the controller maps this gate to existing paths or authorizes creating `tests/application/agents/**`.

4. [GITHUB_CODE] `tests/architecture/` has 5 active Python files. They cover Agent Platform C0/C1 public contract boundaries, candidate-only outputs, handoff metadata, tool exposure guards, application/domain forbidden imports, and provider-boundary static redaction.

5. [GITHUB_CODE] Current `AgentExecutor` exists as `app.application.agents.runtime.AgentExecutor`, but it is a Protocol with `AgentExecutionPlan` / `AgentExecutionResult` signatures. Existing tests only assert required method presence and separation from `AgentGraphRunner`; they do not prove a concrete LangGraph-backed adapter is wired through this boundary.

6. [GITHUB_CODE] `requirements.txt` already pins `langgraph==1.2.1`; `tests/api/test_langgraph_dependency_spike.py` asserts the dependency can be imported, invokes a spike graph, and checks that concrete LangGraph imports stay confined to infrastructure runtime paths.

7. [GITHUB_CODE] Existing must-pass agent/runtime contract tests include `tests/api/test_agent_contracts.py`, `test_agent_graph_runner.py`, `test_agent_runtime_flags.py`, `test_agent_candidate_payload_runtime_mapping.py`, `test_ai_orchestration_facade.py`, `test_app_bootstrap.py`, and `test_model_imports.py`.

8. [GITHUB_CODE] Existing replay / interrupt / checkpoint / side-effect tests include `tests/api/test_agent_interrupt_replay.py`, `test_agent_interrupt_repository.py`, `test_agent_replay_resume_policy.py`, `test_agent_side_effect_idempotency.py`, `test_agent_run_repository.py`, `test_pr4_fake_runtime_replay_resume.py`, `test_pr4_runtime_checkpointer.py`, `test_pr4_runtime_serializer.py`, and `test_pr6_polish_fake_runtime_integration.py`.

9. [GITHUB_CODE] Existing controlled loop tests are concentrated in `tests/api/test_agent_fake_runtime.py`: max retries, timeout, max steps exhausted, validation repair, structured logs, candidate payload sanitation, timeline sanitation, and status refs-only behavior. This is useful but not sufficient for all P8 stop conditions.

10. [GITHUB_CODE] Existing Question / Feedback graph and handoff regression surface includes `test_polish_question_graph_integration.py`, `test_pr5_polish_question_graph_*`, `test_pr6_polish_fake_runtime_integration.py`, `test_pr7_polish_readonly_parity_gate.py`, `test_pr8_polish_provider_trace_gate.py`, `test_polish_feedback_runtime.py`, `test_polish_question_refactor_phase1.py`, and broad `test_polish_api.py`.

11. [GITHUB_CODE] `tests/api/test_pr8_polish_provider_trace_gate.py` defines two helper functions with `_test_` names and registers them dynamically through `globals()` as pytest-visible tests. Static `def test_` counting will undercount this file; the dynamic registration should be preserved or converted to normal `def test_` functions in a future cleanup.

12. [GITHUB_CODE] `tests/evals/` has code-rule and runner tests for built-in datasets, forbidden sensitive keys, candidate output checks, report writing, invalid JSONL handling, and runner independence from `LLM_PROVIDER` / fake runtime. These are reference/eval smoke evidence, not C4 runtime behavior proof.

13. [TEST_RESULT] This recon ran only directory listing, `rg` search, `git diff --check`, `git diff --stat`, and `git status --short`; no pytest, frontend, or long validation command was executed. `git diff --check` exited 0 and `git diff --stat` was empty at the time checked.

14. [TEST_RESULT] `git status --short` showed an unrelated untracked file, `docs/goals/2026-06-05/P8_W0_AGENT_RISK_RECON.md`, created outside this test recon window. This report did not modify it.

## Existing must-pass test groups

Architecture gate:

```bash
python -m pytest tests/architecture -q
```

Agent runtime contract / adapter-adjacent gate:

```bash
python -m pytest \
  tests/api/test_agent_contracts.py \
  tests/api/test_agent_graph_runner.py \
  tests/api/test_agent_runtime_flags.py \
  tests/api/test_agent_candidate_payload_runtime_mapping.py \
  tests/api/test_ai_orchestration_facade.py \
  tests/api/test_app_bootstrap.py \
  tests/api/test_model_imports.py \
  tests/api/test_langgraph_dependency_spike.py \
  -q
```

Replay / interrupt / checkpoint / side-effect gate:

```bash
python -m pytest \
  tests/api/test_agent_interrupt_replay.py \
  tests/api/test_agent_interrupt_repository.py \
  tests/api/test_agent_replay_resume_policy.py \
  tests/api/test_agent_side_effect_idempotency.py \
  tests/api/test_agent_run_repository.py \
  tests/api/test_pr4_fake_runtime_replay_resume.py \
  tests/api/test_pr4_runtime_checkpointer.py \
  tests/api/test_pr4_runtime_serializer.py \
  tests/api/test_pr6_polish_fake_runtime_integration.py \
  -q
```

Controlled loop / provider / boundary gate:

```bash
python -m pytest \
  tests/api/test_agent_fake_runtime.py \
  tests/api/test_pr4_provider_gate.py \
  tests/api/test_pr4_runtime_architecture_boundary.py \
  tests/api/test_pr5_business_graph_boundaries.py \
  tests/api/test_pr8_polish_provider_trace_gate.py \
  -q
```

Question / Feedback regression gate:

```bash
python -m pytest \
  tests/api/test_polish_question_graph_integration.py \
  tests/api/test_pr5_polish_question_graph_skeleton.py \
  tests/api/test_pr5_polish_question_graph_candidate_parity.py \
  tests/api/test_pr5_polish_question_graph_persistence_handoff.py \
  tests/api/test_pr5_polish_question_quality_gate.py \
  tests/api/test_pr5_polish_question_scenario_derivation.py \
  tests/api/test_polish_feedback_runtime.py \
  tests/api/test_polish_question_refactor_phase1.py \
  tests/api/test_polish_feedback_agent_io_alignment.py \
  tests/api/test_polish_feedback_generation_schema.py \
  tests/api/test_polish_feedback_generation_service.py \
  tests/api/test_polish_candidates.py \
  tests/api/test_polish_canonical_evidence.py \
  -q
```

Eval smoke / reference gate:

```bash
python -m pytest tests/evals -q
```

Broad API regression gate after focused pass:

```bash
python -m pytest tests/api/test_agent* tests/api/test_pr4* tests/api/test_pr5* tests/api/test_pr6* tests/api/test_pr7* tests/api/test_pr8* -q
python -m pytest tests/api/test_polish* -q
```

Full backend gate for any `done` claim:

```bash
python -m pytest -q
```

Frontend applicability:

```text
not applicable: Phase 8 recon did not change frontend/API contract.
```

If a future P8 patch touches frontend or API contract despite the normal forbidden boundary, stop and require explicit controller decision before running:

```bash
npm run web:test
npm run web:smoke:auth
```

## Gaps

1. [GITHUB_CODE] No `tests/application/**` directory exists, so P8's focused application gate is missing.

2. [GITHUB_CODE] No P8/C4-named test files were found in `tests/architecture`, `tests/api`, or `tests/evals`; `rg` found no `Phase8`, `P8`, `C4`, or `RTE-*` test markers in those directories.

3. [GITHUB_CODE] Existing tests cover `AgentGraphRunner` and current in-memory runtime surfaces, but do not prove a concrete `AgentExecutor` adapter maps `AgentExecutionPlan` to LangGraph runtime start/resume/replay/status/timeline/cancel.

4. [GITHUB_CODE] Controlled loop coverage exists for question graph max steps, retry, timeout, repair, and provider-disabled fallback, but there is no explicit P8 stop-condition matrix for `max_steps_exceeded`, `timeout`, `validation_failed`, `tool_not_allowed`, `formal_write_requested`, `interrupt_required`, and `provider_failed`.

5. [GITHUB_CODE] Tool contract tests check `allowed_callers`, `side_effect_policy`, timeout seconds, forbidden data, and direct exposure at registry level; missing coverage proves runtime execution enforces the same tool permissions per call.

6. [GITHUB_CODE] Interrupt tests cover user confirmation, owner scope, resume schema, stale version, and idempotency conflicts. Missing P8-specific HITL trigger coverage for formal write attempt, asset conflict, low confidence formal update, ambiguous ownership, and validation failed with partial result.

7. [GITHUB_CODE] Replay tests cover read-only behavior for existing in-memory paths. Missing explicit Phase8 adapter test proving replay does not call provider, external tools, repositories, or formal persistence by default.

8. [GITHUB_CODE] Handoff tests cover candidate-only and some formal persistence via `AgentPersistenceHandoff`, but no typed multi-agent A -> B handoff test through `AgentExecutor` with `candidate_ref`, `candidate_type`, `payload_schema_id`, `trace_refs`, `validation_refs`, `side_effect_key`, and `idempotency_key`.

9. [GITHUB_CODE] Trace/timeline tests cover sanitation and event presence, but not the full P8 required completeness list: `agent_id`, `agent_version`, `run_id`, `ai_task_id`, `input_refs`, `plan_refs`, `skill_refs`, `tool_refs`, `policy_refs`, `provider_refs`, `candidate_refs`, `validation_refs`, `handoff_refs`, `output_refs`, `low_confidence_flags`, `failure_reason`, `fallback_reason`, and `events`.

10. [TEST_RESULT] No current pytest result was produced in this recon, so no test pass/fail status can be used to close P8 gates.

## Recommended patch scope

1. Add focused P8 tests before or with implementation:
   - `tests/architecture/test_agent_runtime_phase8_boundary.py`
   - `tests/application/agents/test_phase8_agent_executor_adapter.py`
   - `tests/api/test_agent_runtime_phase8.py`
   - `tests/api/test_agent_handoff_trace_phase8.py` if `test_agent_runtime_phase8.py` becomes too broad.

2. Phase8 architecture test should assert:
   - LangGraph concrete imports remain under `apps/api/app/infrastructure/ai_runtime/langgraph/**`.
   - `app.application.agents.runtime.AgentExecutor` remains the application boundary.
   - Application/domain/API layers do not import concrete LangGraph / LangChain.
   - Runtime / tools do not expose repository, db/session, raw prompt, raw provider payload, or formal write handles.
   - Infrastructure runtime contains no business policy or formal persistence path.

3. Phase8 application test should assert:
   - Concrete adapter implements `AgentExecutor`.
   - `start`, `resume`, `replay`, `get_status`, `get_timeline`, and `cancel` return project-owned DTOs.
   - Adapter output stays candidate-ref / trace-ref based and never returns formal refs.
   - Replay defaults read-only.

4. Phase8 API/runtime tests should assert:
   - Controlled loop bounds fail closed when max steps, retries, timeout, allowed tools/callers, side-effect policy, or stop conditions are invalid.
   - Stop-condition statuses are not reported as success.
   - Interrupt/resume validates owner scope, interrupt ref, checkpoint/base version, and allowed resume action.
   - Typed handoff preserves candidate and trace refs and blocks direct formal write.
   - Timeline completeness includes all required ref categories while excluding raw prompt, raw completion, provider payload, full resume/JD/asset body, secrets, tokens, cookies, and API keys.

5. Keep existing tests stable. Prefer adding P8-specific tests over rewriting older PR4-PR8 tests unless the old test is directly encoding an obsolete boundary.

6. Treat `tests/evals/**` as reference or non-quality smoke only unless the controller explicitly authorizes a new eval fixture. Do not use eval smoke as runtime done proof.

## Recommended forbidden files

For this test recon, all files except `docs/goals/2026-06-05/P8_W0_AGENT_TEST_RECON.md` are forbidden to write.

For future P8 implementation unless controller records an explicit new decision:

- `apps/api/app/application/polish/question_generation_prompts.py`
- `apps/api/app/application/polish/feedback_prompt_assets.py`
- `apps/api/app/application/polish/*prompt*`
- `apps/api/app/application/ai_provider/**`
- `apps/api/app/infrastructure/llm/**`
- `apps/api/app/infrastructure/db/**`
- `database migrations/**`
- `apps/api/app/api/v1/**`
- `frontend/**`
- `domain/polish/policies/**`
- production fake provider wiring
- broad rewrites of `tests/api/test_polish_api.py` unless a changed Phase8 contract directly requires a targeted assertion update

## Stop-condition findings

1. [PROJECT_SOURCE] Stop before any code patch if `docs/goals/2026-06-05/P8_W0_SCOPE_LOCK.md` does not exist. P8 Master requires controller merge and scope lock before implementation.

2. [PROJECT_SOURCE] Stop if a patch tries to mark Phase 8 `done` without focused tests, architecture tests, full backend validation, source backfill, final audits, and explicit C4-not-L5 wording.

3. [GITHUB_CODE] Stop or remap before using `python -m pytest tests/application -q` as a gate, because `tests/application/` currently does not exist.

4. [GITHUB_CODE] Stop if implementation depends on current `AgentExecutor` method-presence tests alone; they do not validate a concrete LangGraph adapter through the AgentExecutor boundary.

5. [GITHUB_CODE] Stop if implementation relies only on existing PR4-PR8 tests to claim P8 completion. Existing tests cover many pieces but lack P8/C4 named acceptance coverage and the full required trace/handoff/stop-condition matrix.

6. [PROJECT_SOURCE] Stop if frontend or API contract changes become necessary. P8 normally forbids API contract and frontend changes; frontend tests are conditional only after explicit authorization.

7. [TEST_RESULT] Stop any done claim from this recon. No pytest or frontend test result was produced here.

## Confidence

Confidence: high

理由：指定测试目录、P8 goal pack、治理入口、pytest/package/requirements 配置和关键 runtime-related tests 已完成静态核查；未执行测试体，因此对当前 pass/fail 结果的置信度为低，但对“现有测试覆盖面与缺口”的 recon 置信度为 high。

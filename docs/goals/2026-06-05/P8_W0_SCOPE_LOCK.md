---
title: P8_W0_SCOPE_LOCK
type: goal-evidence
status: scope_lock_created
owner: P8 Controller
permalink: ai-for-interviewer/docs/goals/2026-06-05/p8-w0-scope-lock
---

# P8-W0 Controller Scope Lock

Window ID: P8-GOAL-ONE-SHOT-C4-RUNTIME

Status: can_proceed_to_patch_with_constraints

本文件是 P8-W0 五个 recon agent 的 Controller merge 结果。它只授权后续受控实现窗口，不声明 Phase 8 done，不声明 L5 release，不替代 active docs、`BACKLOG.md`、`DELIVERY_PLAN.md`、ADR 或代码事实。

## Scope Lock

```text
task_id: N/A - P8 goal pack capability window; no new AIFI-* task is opened in this scope lock
files:
  READ:
    - AGENTS.md
    - docs/00-governance/DOCS_INDEX.md
    - docs/tmp/goal0605/phase8_codex_goal_pack/**
    - docs/project-sources/**
    - docs/goals/2026-06-05/**
    - apps/api/app/application/agents/**
    - apps/api/app/application/ai_runtime/**
    - apps/api/app/application/polish/agents/question/**
    - apps/api/app/application/polish/agents/feedback/**
    - apps/api/app/application/polish/use_cases.py
    - apps/api/app/infrastructure/ai_runtime/**
    - tests/architecture/**
    - tests/api/test_agent*
    - tests/api/test_pr4*
    - tests/api/test_pr5*
    - tests/api/test_pr6*
    - tests/api/test_pr7*
    - tests/api/test_pr8*
    - tests/api/test_polish*
    - tests/evals/**
    - requirements.txt
    - .env.example
  WRITE:
    - apps/api/app/application/agents/runtime/**
    - apps/api/app/application/agents/contracts/**
    - apps/api/app/application/agents/handoff/**
    - apps/api/app/application/agents/registry/**
    - apps/api/app/application/agents/definitions/**
    - apps/api/app/application/ai_runtime/**
    - apps/api/app/application/polish/agents/question/**
    - apps/api/app/application/polish/agents/feedback/**
    - apps/api/app/infrastructure/ai_runtime/**
    - tests/architecture/**
    - tests/api/test_agent*
    - tests/api/test_pr4*
    - tests/api/test_pr5*
    - tests/api/test_pr6*
    - tests/api/test_pr7*
    - tests/api/test_pr8*
    - tests/api/test_polish*
    - tests/application/agents/** only if the writer first records why the missing P8 application gate needs this path
    - docs/goals/2026-06-05/**
    - docs/project-sources/** only in P8-W5 after implementation validation
    - .env.example only for additive default-off runtime flags
figma_nodes: N/A
allowed_ops:
  - EDIT_LISTED_FILES for P8 implementation after this scope lock exists
  - READ_ONLY audit after patch
forbidden_ops:
  - prompt rewrite
  - provider behavior rewrite
  - API contract change
  - DB schema migration or migration file
  - frontend change
  - domain business policy change
  - production fake provider wiring
  - runtime direct formal write
  - unbounded autonomous swarm
  - Phase 11 Supervisor / Orchestrator implementation
  - Phase 12 L5 eval / release gate implementation
final_artifact:
  - P8 W1-W5 reports
  - P8 final boundary/runtime/source audits
  - P8 final execution report
done_condition:
  - all P8 no-false-done gates are checked against current files and command output
  - final status is one of done, partial_with_deferred_gaps, blocked_needs_controller_decision, recon_only_no_patch
```

## Multi-Agent Recon Board

| Agent | Output file | Status | Key finding |
|---|---|---|---|
| Runtime Surface Recon | `docs/goals/2026-06-05/P8_W0_AGENT_RUNTIME_RECON.md` | warn | LangGraph is declared and importable in `.venv`; active runtime uses `AgentGraphRunner` / `AiOrchestrationFacade`, not `AgentExecutor` as the concrete boundary. |
| Contract / Handoff / Trace Recon | `docs/goals/2026-06-05/P8_W0_AGENT_CONTRACT_RECON.md` | warn | Contract tests passed, but `AgentExecutor` / `AgentGraphRunner` and `AgentExecution*` / `AgentRun*` still have DTO and boundary drift. |
| Question / Feedback Integration Recon | `docs/goals/2026-06-05/P8_W0_AGENT_QF_RECON.md` | warn | Question has a low-risk adapter connection point; Feedback runtime remains skeleton/generic candidate ref and lacks typed `feedback_candidate` / `asset_update_candidate` runtime payloads. |
| Test / Architecture Gate Recon | `docs/goals/2026-06-05/P8_W0_AGENT_TEST_RECON.md` | warn | Existing tests are reusable but no P8/C4-named tests exist, and `tests/application/` is currently absent. |
| Risk / Source Backfill Recon | `docs/goals/2026-06-05/P8_W0_AGENT_RISK_RECON.md` | warn | Current source status remains `eligible_for_controller_decision` / `not_started`; source backfill must wait until runtime validation. |

## Confirmed Current Implementation Facts

- [GITHUB_CODE] `requirements.txt` already declares `langgraph==1.2.1`; `.venv` can import LangGraph 1.2.1. No dependency addition is authorized for P8.
- [GITHUB_CODE] Concrete LangGraph imports are currently confined to `apps/api/app/infrastructure/ai_runtime/langgraph/**`.
- [GITHUB_CODE] `app.application.agents.runtime.AgentExecutor` exposes `start`, `resume`, `replay`, `get_status`, `get_timeline`, and `cancel`, but it is a protocol surface and not the current concrete runtime wiring.
- [GITHUB_CODE] The active runtime wiring is closer to `application.ai_runtime.contracts.AgentGraphRunner` plus `AiOrchestrationFacade`.
- [GITHUB_CODE] `AiOrchestrationFacade` exposes start, resume, status, timeline, and cancel surfaces; replay is implemented on runner but not exposed as a facade method in recon evidence.
- [GITHUB_CODE] `InMemoryLangGraphRuntime` implements start/resume/replay/status/timeline/cancel with refs-only in-memory checkpoints and read-only replay semantics.
- [GITHUB_CODE] `PolishQuestionGraphRuntime` is the most complete concrete business runtime and emits candidate payloads, checkpoint refs, validation refs, sanitized metadata, and timeline events.
- [GITHUB_CODE] `polish_feedback_graph` remains placeholder / skeleton / fake-runtime oriented and does not yet emit typed `feedback_candidate` / `asset_update_candidate` runtime payloads.
- [GITHUB_CODE] Formal business writes are currently performed through application use cases and `AgentPersistenceHandoff`, not directly by the runtime runner.
- [GITHUB_CODE] `RuntimeFlagResolver` is fail-closed by default. `AIFI_AI_RUNTIME_LANGGRAPH_ENABLED` is used by runtime code but missing from `.env.example`.
- [GITHUB_CODE] Runtime persistence models/repositories exist, but the active runner path is still in-memory and does not wire persistent repositories into execution state.
- [TEST_RESULT] Contract-focused verification from Contract Recon passed: `20 passed in 0.20s`.
- [TEST_RESULT] No broad pytest, frontend, or current P8 runtime validation has run in P8-W0.
- [PROJECT_SOURCE] P8 is C4 LangGraph / multi-agent runtime foundation only. It is not Phase 11, Phase 12, product-level L5, or formal F8/M8 release.

## Behavior-Change Authorization

Authorized after this file exists:

- Add or adjust application/infrastructure runtime adapter code so current LangGraph-backed runtime can be used through the AgentExecutor-compatible boundary.
- Add controlled runtime loop policy and fail-closed validation for max steps, retries, timeout, stop conditions, tool permissions, allowed callers, owner scope, permission scope, and side-effect policy.
- Add or connect interrupt/resume/checkpoint/replay semantics if replay remains read-only by default and checkpoint remains runtime state, not business fact.
- Add typed multi-agent handoff and trace/timeline fields using candidate refs, trace refs, validation refs, handoff refs, side-effect keys, and idempotency keys.
- Add focused tests and architecture tests that prove the P8 behavior and forbid boundary drift.
- Add `.env.example` runtime flags only as default-off documentation of existing fail-closed runtime behavior.

Not authorized:

- Prompt text, prompt asset, provider request, provider fallback, DB schema, public API contract, frontend, or domain policy behavior changes.
- Any runtime, tool, replay, or agent path that writes formal business facts directly.
- Any dependency change. LangGraph dependency decision is `existing`.
- Any source backfill that marks P8 `done` before all done gates pass.

## LangGraph Dependency Decision

Decision: existing.

Evidence:

- `requirements.txt` declares `langgraph==1.2.1`.
- Runtime Recon verified `.venv` can import `langgraph==1.2.1`.
- System `/usr/bin/python3` cannot import LangGraph, so validation commands must use the project environment if the default `python` is not the project `.venv`.

Constraint:

- Do not modify `requirements.txt` or dependency lock files in this P8 window unless a later stop-and-report proves the current dependency is unusable.

## Ordered Sub-Windows

1. P8-W1 Runtime adapter / executor integration
   - Decide the compatibility mapping between `AgentExecutor` and `AgentGraphRunner`.
   - Prefer an adapter that preserves current DTO compatibility rather than duplicating runtime contracts.
   - Add or update focused tests proving start/resume/replay/status/timeline/cancel through the selected boundary.

2. P8-W2 Controlled tool loop
   - Promote bounds and stop-condition checks into a reusable runtime policy.
   - Missing bounds must fail closed.
   - Tool execution must validate allowed tools, allowed callers, owner scope, permission scope, side-effect policy, and forbidden data.

3. P8-W3 Interrupt / resume / checkpoint / replay
   - Expose replay at the selected facade/boundary only if no API contract change is required.
   - Validate owner scope, interrupt ref, checkpoint/base version, and allowed resume action.
   - Keep replay read-only by default and prevent provider/tool/repository/formal-write calls.

4. P8-W4 Typed multi-agent handoff and trace/timeline
   - Add typed handoff envelope fields or bridge existing contract surfaces without raw prompt sharing.
   - Fill P8 trace/timeline refs while keeping raw prompt, raw completion, provider payload, full resume/JD/asset body, secrets, tokens, cookies, and API keys out of persisted trace.
   - Preserve formal write route through Application Service -> Domain Policy / validation -> Handoff -> Repository / Transaction.

5. P8-W5 Validation, audits, source backfill, final report
   - Run focused tests first, then architecture tests, then full backend validation for any `done` claim.
   - Run frontend tests only if a separately authorized API/frontend change occurs.
   - Update `docs/project-sources/**` only after evidence exists.
   - Create final boundary/runtime/source audits and final execution report.

## Validation Plan

Use the project Python environment when needed, because Runtime Recon found system Python cannot import LangGraph.

Minimum validation sequence after implementation:

```bash
git status --short --untracked-files=all
git diff --check
python -m pytest tests/architecture -q
python -m pytest tests/api/test_agent* -q
python -m pytest tests/api/test_pr4* tests/api/test_pr5* tests/api/test_pr6* tests/api/test_pr7* tests/api/test_pr8* -q
python -m pytest tests/api/test_polish* -q
python -m pytest -q
```

If `python` is not the project environment, use:

```bash
.venv/bin/python -m pytest ...
```

Expected focused additions or updates:

- `tests/architecture/test_agent_runtime_phase8_boundary.py`
- `tests/application/agents/test_phase8_agent_executor_adapter.py` only if this new directory is created intentionally
- `tests/api/test_agent_runtime_phase8.py`
- `tests/api/test_agent_handoff_trace_phase8.py` if needed to keep runtime tests focused

Frontend:

```text
not applicable: no frontend/API contract changes are authorized in this P8 scope lock.
```

## Stop Conditions

Stop and report `blocked_needs_controller_decision` if any of these become necessary:

- Modifying prompt files, provider files, DB schema/migrations, API contract files, frontend files, or domain policy behavior.
- Adding or changing LangGraph dependency despite the current `existing` decision.
- Treating `AgentGraphRunner` as equivalent to `AgentExecutor` without an explicit adapter or compatibility mapping.
- Letting runtime/replay/tool loop call provider, external tools, repositories, or formal persistence in replay by default.
- Allowing runtime result to carry non-empty formal refs or to invoke `QuestionResultWritePlan` / repository writes directly.
- Keeping Feedback runtime as generic skeleton/fake semantics while reporting typed `feedback_candidate` / `asset_update_candidate` success.
- Implementing infrastructure business policy.
- Marking C4 as L5 release, Phase 11/12 complete, or formal F8/M8 release.
- Claiming Phase 8 `done` without focused tests, architecture tests, full backend validation, source backfill, final audits, and explicit C4-not-L5 wording.

## Final Decision

Phase 8 can proceed from P8-W0 to P8-W1 because all five recon reports exist, none reported a hard blocker, and LangGraph dependency is already available in the project environment.

Proceeding is conditional:

- P8-W1 must start with AgentExecutor / AgentGraphRunner compatibility, not with prompt/provider/API/DB/frontend changes.
- P8 status remains `scope_lock_created` / `partial_with_deferred_gaps` until implementation, validation, audits, and source backfill prove a stronger status.
- No final `done` claim is allowed from P8-W0 evidence alone.

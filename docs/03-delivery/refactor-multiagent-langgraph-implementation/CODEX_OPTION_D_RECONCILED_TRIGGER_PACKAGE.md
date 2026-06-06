---
title: CODEX_OPTION_D_RECONCILED_TRIGGER_PACKAGE
type: note
permalink: ai-for-interviewer/docs/03-delivery/refactor-multiagent-langgraph-implementation/codex-option-d-reconciled-trigger-package
---

# Codex Option D Reconciled Trigger Package

## Purpose

This package replaces the earlier generic Option D trigger with the current-code-informed reconciliation plan supplied by Codex Plan Mode.

User-confirmed target: **Option D: Local Complete Multi-Agent Capability**.

Option D means:

- Build a real, locally executable, controlled multi-agent system.
- Keep production release readiness out of scope.
- Keep A/B testing, traffic split, canary rollout, online experiment metrics, production observability/SLO, remote CI hard claim, and real-provider production certification out of scope unless separately authorized.
- Combine default-off local product/runtime wiring with local multi-agent replay, trace, HITL, bounded loop, and failure hardening.

## Source of Truth

1. USER_CONFIRMED Option D.
2. GitHub current code.
3. Current tests/evals.
4. Project sources.
5. GOAL0531 historical intent only.
6. Subwindow output only after 总控 audit.

## Audited Current Recon Summary

From the provided Option D Reconciliation Plan:

- Current branch: `refactor/option-d-local-multi-agent`.
- Branch is clean.
- HEAD is ahead of `origin/main` by one commit, containing only the Option D package.
- Architecture/eval smoke: `74 passed`.
- Phase 12 L5 runner: `9 passed / 0 blocking_failures`; negative control observed expected failure.
- Phase 9 replay: `30 passed / 2 deferred / 0 blocking_failures`; negative control observed expected failure.
- CodeGraph is available.
- Current repo has L5 eval foundation, but Option D has not yet been backfilled as Project source fact.
- L5-006 is still not split into `L5-006A local eval/replay/failure hardening` and `L5-006B production release deferred`.

## Critical Decision

Do **not** start implementation before W0.

The previous plan/package needs revision because:

- No standalone `remaining_refactor_exec_plan.md` was found.
- The current Option D package points to a canonical path that does not yet exist.
- It assumes a decision ID that may not be available.
- It predates current P12-W1 executable eval facts.
- Project sources do not yet record USER_CONFIRMED Option D or L5-006A/B split.

## Recommended Canonical Path

Use this canonical file path:

```text
docs/03-delivery/refactor-multiagent-langgraph-implementation/option_d_local_complete_multi_agent_goal.md
```

If the current file is:

```text
docs/03-delivery/refactor-multiagent-langgraph-implementation/CODEX_OPTION_D_LOCAL_MULTI_AGENT_GOAL_PACKAGE.md
```

then W0 should use `git mv` to rename it to the canonical path, or create the canonical replacement and mark the old file as superseded. Prefer `git mv` to avoid duplicate active goal documents.

## W0: Plan / Source Revision Prompt

Use this first. This is **not** the implementation goal.

```text
You are in the AiForInterviewer repository.

Window ID: D-W0-OPTION-D-SOURCE-REVISION
Phase: Phase 11/12 local capability target lock
Capability IDs: L5-002, L5-003, L5-004, L5-005, L5-006A, L5-006B, SRC-001, WIN-001

Goal:
Revise the current Option D plan/source package before implementation. Do not modify implementation files. Make Option D a Project-source-backed fact, split L5-006 into local hardening and production release, and standardize the canonical goal path.

Source of truth:
1. USER_CONFIRMED Option D.
2. GitHub current code.
3. Current tests/evals.
4. Project sources.
5. GOAL0531 historical intent only.
6. Subwindow output only after 总控 audit.

Must recon first:
- git fetch origin main
- git status --short --branch --untracked-files=all
- git rev-list --left-right --count HEAD...origin/main
- PYTHONPATH=.:apps/api .venv/bin/python -m pytest tests/architecture tests/evals -q
- Inspect docs/03-delivery/refactor-multiagent-langgraph-implementation/**
- Inspect docs/project-sources/09_REFACTOR_TRACEABILITY_MATRIX.md
- Inspect docs/project-sources/12_ACCEPTANCE_GATES.md
- Inspect docs/project-sources/13_DECISION_LOG.md
- Inspect docs/project-sources/14_RISK_REGISTER.md
- Inspect docs/project-sources/17_PHASE_ROADMAP_LOCK.md
- Inspect docs/project-sources/18_AGENT_PLATFORM_C_TARGET.md

Allowed files:
- docs/03-delivery/refactor-multiagent-langgraph-implementation/**
- docs/project-sources/09_REFACTOR_TRACEABILITY_MATRIX.md
- docs/project-sources/12_ACCEPTANCE_GATES.md
- docs/project-sources/13_DECISION_LOG.md
- docs/project-sources/14_RISK_REGISTER.md
- docs/project-sources/17_PHASE_ROADMAP_LOCK.md
- docs/project-sources/18_AGENT_PLATFORM_C_TARGET.md
- docs/goals/** only if already used by this repo for goal evidence

Forbidden files:
- apps/**
- tests/**
- scripts/**
- evals/**
- .github/**
- frontend
- DB schema/migration/model files
- API route/contract behavior
- provider/prompt behavior files
- lockfiles

Implementation requirements:
1. Canonicalize the Option D goal path as:
   docs/03-delivery/refactor-multiagent-langgraph-implementation/option_d_local_complete_multi_agent_goal.md
2. If CODEX_OPTION_D_LOCAL_MULTI_AGENT_GOAL_PACKAGE.md exists in the same directory, either git mv it to the canonical path or clearly mark it superseded. Prefer git mv.
3. Record a new decision using the next available ID, for example DEC-L5-015 or the next actual available ID. Do not reuse DEC-012 unless it is actually free and appropriate.
4. Decision text must state:
   - Option D = Local Complete Multi-Agent Capability.
   - It combines default-off local product/runtime wiring with local replay/trace/HITL/bounded-loop/failure hardening.
   - It excludes production release readiness and A/B testing.
5. Split L5-006 into:
   - L5-006A: Local multi-agent eval / replay / failure hardening.
   - L5-006B: Production release gate / remote CI hard claim / real-provider production certification / production observability / release decision.
6. Mark L5-006B as deferred/out of scope for Option D.
7. Update Matrix, Acceptance Gates, Decision Log, Risk Register, Roadmap, and Agent Platform C Target consistently.
8. Do not claim production L5 release.
9. Do not mark any capability done unless code, tests/evals, old-duty removal, no forbidden scope, source backfill, and gap closure/deferred reason are all proven.

Validation commands:
- git diff --check
- git diff -- docs/03-delivery/refactor-multiagent-langgraph-implementation docs/project-sources docs/goals

Rollback:
- Revert this docs-only commit.

Done criteria:
- Option D is recorded as user-confirmed Project source decision.
- L5-006A/B split is recorded.
- Production release and A/B testing are explicitly out of scope/deferred.
- Canonical goal path exists.
- No implementation/test/script/provider/API/DB/frontend files changed.

Final output:
1. Root Cause
2. What Changed
3. Files Changed
4. Behavior Before / After
5. Validation Commands and Results
6. Remaining Risks
7. Follow-up Goal

Stop conditions:
- Any implementation file needs modification.
- Decision ID conflict cannot be resolved safely.
- Existing docs contradict Option D and cannot be represented as a gap/deferred scope.
- Validation fails and requires non-doc changes.
```

Expected commit:

```bash
git add docs/03-delivery/refactor-multiagent-langgraph-implementation docs/project-sources docs/goals 2>/dev/null || true
git commit -m "docs(l5): reconcile option d local target"
```

## Master Goal After W0

After W0 is committed, trigger the persistent goal:

```text
/goal Implement Option D: Local Complete Multi-Agent Capability for AiForInterviewer by following docs/03-delivery/refactor-multiagent-langgraph-implementation/option_d_local_complete_multi_agent_goal.md. Build a real locally executable controlled multi-agent system, not a production release program. Use GitHub current code and current tests/evals as implementation facts; use Project sources as architecture and guardrails; use GOAL0531 as historical intent only. Work in W1-W4 scoped checkpoints. Keep production release readiness, A/B testing, traffic split, canary rollout, online experiment metrics, production observability/SLO, remote CI hard claim, and real-provider production certification out of scope unless separately authorized. Implement a default-off local multi-agent runtime path with Supervisor/Orchestrator, at least three business agents in one local product workflow, typed handoff, cross-agent state/trace/replay, bounded loop, HITL, candidate-only outputs, formal write through Application Service -> Domain Policy -> Handoff, compact fail-closed provider boundary, and fake-only tests/evals/replay. Validate after every checkpoint, repair before continuing, commit only validated capability groups, and backfill Project sources. Stop on forbidden scope, direct formal write, repository exposure, provider fail-open, or overclaiming production release.
```

## W1: Tests First Prompt

After the master goal is set, ask Codex to start with W1:

```text
Continue the active Option D goal with W1: default-off local runtime wiring tests first.

Window ID: D-W1-LOCAL-MULTI-AGENT-RUNTIME-TESTS
Phase: Phase 11 / Phase 12 local hardening
Capability IDs: L5-002, L5-003, L5-004, L5-005, L5-006A

Goal:
Specify failing or focused tests for local multi-agent runtime wiring before implementation. Do not implement runtime wiring in this window unless only test fixtures require minimal model imports.

Must recon first:
- apps/api/app/application/agents/**
- apps/api/app/application/ai_runtime/**
- apps/api/app/application/polish/**
- apps/api/app/infrastructure/ai_runtime/**
- tests/application/agents/**
- tests/architecture/**
- focused tests/api/** relevant to agent/handoff/runtime
- docs/project-sources/** Option D changes

Allowed files:
- tests/application/agents/**
- tests/architecture/**
- focused tests/api/**

Forbidden files:
- apps/** implementation files
- scripts/**
- evals/**
- .github/**
- frontend
- DB schema/migration/model files
- API route/contract behavior
- provider/prompt behavior files
- production config

Test requirements:
Create or update focused tests proving:
1. Flag off keeps existing behavior.
2. Flag on routes to local multi-agent orchestrator path.
3. At least three business agent refs participate through typed handoff.
4. Cross-agent trace includes plan_refs / skill_refs / tool_refs / policy_refs / handoff_refs / validation_refs.
5. Formal write is blocked unless routed through handoff.
6. Tool direct repository exposure is blocked.
7. Bounded loop has max_steps / max_retries / timeout / stop_conditions.
8. HITL triggers for asset conflict, formal write, low confidence, and ownership ambiguity.
9. Fake remains tests/evals/replay only.
10. Provider payload remains compact/fail-closed.

Validation:
- PYTHONPATH=.:apps/api .venv/bin/python -m pytest tests/application/agents tests/architecture -q
- PYTHONPATH=.:apps/api .venv/bin/python -m pytest tests/api -k "agent or handoff or runtime or multi_agent or l5" -q
- git diff --check

Expected result:
- New tests may fail before W2 implementation, but existing unrelated gates must still pass.
- If tests are intentionally red, clearly report expected failures and exact implementation gap.

Commit:
- test(l5): specify local multi-agent runtime wiring
```

## W2: Runtime / Product Wiring Prompt

```text
Continue the active Option D goal with W2: runtime/product wiring.

Window ID: D-W2-LOCAL-MULTI-AGENT-RUNTIME-WIRING
Phase: Phase 11
Capability IDs: L5-002, L5-003, L5-004, L5-005

Goal:
Implement the default-off local multi-agent runtime path required by W1 tests. Keep existing behavior unchanged when the local multi-agent flag is off.

Allowed files:
- apps/api/app/application/agents/**
- apps/api/app/application/ai_runtime/**
- apps/api/app/application/polish/**
- apps/api/app/infrastructure/ai_runtime/**
- tests/application/agents/** only for fixture adjustments
- tests/architecture/** only for boundary assertion adjustments

Forbidden files:
- apps/api/app/api/v1/**
- DB schema/migration/model files
- frontend
- domain policy behavior changes unless separately confirmed
- real provider config
- prompt rewrite
- .github/**
- production rollout/A-B/canary/traffic split

Implementation requirements:
1. Add/complete executable Supervisor/Orchestrator local runtime path.
2. Add default-off local runtime mode flag.
3. Register/match an orchestrator task/graph mapping if AgentGraphRegistry lacks it.
4. Ensure at least three business agents participate in one local product workflow.
5. Use typed handoff, not raw prompt sharing.
6. Return candidate refs and trace refs only.
7. Keep formal write behind Application Service -> Domain Policy -> Handoff.
8. Preserve replay read-only and formal-write-blocked guards.
9. Keep provider payload compact/fail-closed.
10. Keep fake only in tests/evals/replay.

Validation:
- PYTHONPATH=.:apps/api .venv/bin/python -m pytest tests/application/agents tests/architecture -q
- PYTHONPATH=.:apps/api .venv/bin/python -m pytest tests/api -k "agent or handoff or runtime or multi_agent or l5" -q
- PYTHONPATH=.:apps/api .venv/bin/python -m pytest tests/architecture tests/evals -q
- git diff --check

Commit:
- refactor(runtime): wire default-off local multi-agent path
```

## W3: Local Eval / Replay / Failure Hardening Prompt

```text
Continue the active Option D goal with W3: local eval/replay/failure hardening.

Window ID: D-W3-LOCAL-MULTI-AGENT-EVAL-REPLAY
Phase: Phase 12 local hardening subset
Capability IDs: L5-006A, L5-003, L5-005

Goal:
Validate Option D locally with deterministic multi-agent replay, trace report, and failure fixtures. Do not implement production release gate, A/B testing, remote CI hard claim, or real-provider production certification.

Allowed files:
- tests/evals/**
- scripts/evals/**
- tests/application/agents/**
- tests/architecture/**
- apps/** only if W2 exposes a narrow hardening gap and the change stays within Option D boundaries

Forbidden files:
- production release workflow
- remote CI hard claim
- .github/** unless separately authorized
- real-provider certification
- A/B or traffic experiment framework
- frontend
- DB schema/migration/model files
- API route/contract behavior

Requirements:
1. Local deterministic L5 eval suite includes a full local multi-agent scenario.
2. Replay reproduces one full local multi-agent run without raw prompt/raw provider payload persistence.
3. Failure fixtures cover insufficient context, asset conflict, provider unavailable, validation failed, handoff failure, replay mismatch, bounded-loop stop condition.
4. Negative controls still fail as expected.
5. Trace report includes agent_id / run_id / plan_refs / skill_refs / tool_refs / policy_refs / handoff_refs / validation_refs.
6. Any production release evidence remains deferred, not claimed.

Validation:
- PYTHONPATH=.:apps/api .venv/bin/python -m pytest tests/evals -q
- PYTHONPATH=.:apps/api .venv/bin/python scripts/evals/run_l5_eval_suite.py --mode deterministic --report-dir /tmp/aifi-phase12-l5-option-d
- PYTHONPATH=.:apps/api .venv/bin/python scripts/evals/run_eval_gate.py --suite phase9 --mode replay --report-dir /tmp/aifi-phase9-option-d
- Run the repository's negative-control command if present; expected failure must be observed.
- git diff --check

Commit:
- test(l5): validate local multi-agent eval and replay gates
```

## W4: Source Backfill / Closeout Prompt

```text
Continue the active Option D goal with W4: source backfill and closeout.

Window ID: D-W4-OPTION-D-SOURCE-BACKFILL-CLOSEOUT
Phase: Phase 12 local closeout
Capability IDs: L5-002, L5-003, L5-004, L5-005, L5-006A, L5-006B, SRC-001, WIN-001

Goal:
Backfill Project sources with actual Option D implementation evidence. Close local capability gaps only where proven. Explicitly defer production release/A-B/remote CI/real-provider certification.

Allowed files:
- docs/project-sources/09_REFACTOR_TRACEABILITY_MATRIX.md
- docs/project-sources/12_ACCEPTANCE_GATES.md
- docs/project-sources/13_DECISION_LOG.md
- docs/project-sources/14_RISK_REGISTER.md
- docs/project-sources/17_PHASE_ROADMAP_LOCK.md
- docs/project-sources/18_AGENT_PLATFORM_C_TARGET.md
- docs/03-delivery/refactor-multiagent-langgraph-implementation/option_d_local_complete_multi_agent_goal.md
- docs/goals/** only if already used by this repo for evidence

Forbidden files:
- implementation files
- tests
- scripts
- evals
- .github/**
- production release docs claiming done

Requirements:
1. Update Matrix states based on evidence, not intent.
2. L5-006A may be validated/done only if local eval/replay/failure gates passed.
3. L5-006B must remain deferred/out of scope for Option D.
4. Production L5 release must not be claimed.
5. A/B testing must be explicitly out of scope/not required.
6. Record remaining gaps with source tags.
7. Include validation command results.

Validation:
- PYTHONPATH=.:apps/api .venv/bin/python -m pytest tests/architecture tests/evals -q
- PYTHONPATH=.:apps/api .venv/bin/python scripts/evals/run_l5_eval_suite.py --mode deterministic --report-dir /tmp/aifi-phase12-l5-option-d-final
- PYTHONPATH=.:apps/api .venv/bin/python scripts/evals/run_eval_gate.py --suite phase9 --mode replay --report-dir /tmp/aifi-phase9-option-d-final
- git diff --check

Commit:
- docs(l5): backfill option d local capability evidence
```

## Final Status Language

Allowed:

```text
Option D local complete controlled multi-agent capability is implemented and locally validated.
```

Forbidden:

```text
Production L5 release is complete.
L5 is production-ready.
Remote CI release gate is proven.
Real-provider production quality is certified.
A/B rollout is ready.
```

## Expected Final Capability Status

- L5-002 Supervisor / Orchestrator Agent: validated/done if executable and tested.
- L5-003 Cross-agent handoff / state / trace: validated/done if replayable.
- L5-004 Multi-agent product workflow: validated for local default-off product path.
- L5-005 Controlled tool loop hardening: validated/done if bounded-loop and HITL tests pass.
- L5-006A Local eval / replay / failure hardening: validated/done if local gates pass.
- L5-006B Production release gate: deferred / out of scope for Option D.
- A/B testing: out_of_scope_not_required.
- Remote CI hard claim: deferred_not_required_for_local_execution.
- Real-provider production certification: deferred_not_required_for_local_execution.
---
title: option_d_local_complete_multi_agent_goal
type: note
permalink: ai-for-interviewer/docs/03-delivery/refactor-multiagent-langgraph-implementation/option-d-local-complete-multi-agent-goal
---

# Codex Goal Package — Option D: Local Complete Multi-Agent Capability

**Project:** AiForInterviewer 多 Agent / DDD 重构总控  
**Goal package version:** 2026-06-07-D-W0-source-revision
**Execution target:** Codex CLI, plan mode first, then goal mode  
**Primary outcome:** Build a real, locally executable, controlled multi-agent system.  
**Explicit non-outcome:** Do not implement production release governance, A/B testing, canary/traffic rollout, or production real-provider certification in this goal.
**Project source decision:** `DEC-L5-015 Option D Local Complete Multi-Agent Capability`

---

## 0. Why this package exists

This package replaces the earlier A/B/C choice with **Option D**.

Option D is user-confirmed as the current target:

> Build a complete local multi-agent capability by combining Option B's default-off product-runtime wiring with Option C's local replay / trace / failure hardening, while excluding production release readiness and A/B testing.

This is not a production rollout goal. It is a local capability completion goal.

---

## 1. Source of Truth

Use this priority order for every claim and implementation decision:

1. USER_CONFIRMED — the user's explicit Option D decision and later confirmations.
2. GITHUB_CODE — current `main` / current branch code after `git fetch` and local recon.
3. TEST_RESULT — current tests, evals, replay, negative controls, CI output visible locally.
4. PROJECT_SOURCE — docs/project-sources and refactor docs.
5. GOAL_SOURCE — GOAL0531 historical intent only.
6. HISTORY — previous chats only as clues.
7. SUBWINDOW_OUTPUT — Codex / sub-agent output only after 总控 audit.

If Project source / GOAL0531 / previous Codex plan conflicts with current GitHub code:

- Use GitHub code to describe current implementation.
- Use Project source to describe target architecture and guardrails.
- Use GOAL0531 to describe historical intent.
- Record the mismatch as a gap.
- Do not mark a capability done based on documents alone.

---

## 2. Option D Definition

### Name

`Option D — Local Complete Multi-Agent Capability`

### Goal

Implement a **real, locally executable, controlled L5-style multi-agent capability** for AiForInterviewer.

The system must include:

- Supervisor / Orchestrator Agent registered and executable.
- At least three business agents collaborating in one local product workflow.
- Typed handoff between agents, not raw prompt sharing.
- Shared CanonicalEvidencePack / InterviewContext / SourceSupportSummary.
- Cross-agent plan / state / trace / replay.
- Controlled loop with `max_steps`, `max_retries`, `timeout_seconds`, and `stop_conditions`.
- HITL protection for asset conflict, formal write, low confidence, and ownership ambiguity.
- Candidate-only outputs from all agents.
- Formal write path still going through `Application Service -> Domain Policy -> Handoff`.
- ToolRegistry / ToolDefinition boundaries that do not expose repositories directly.
- Provider request compact, schema-bound, redacted, traceable, and fail-closed.
- Fake provider restricted to tests / evals / replay only.
- Local deterministic multi-agent replay and failure fixtures.

### Explicitly out of scope

Do not implement or claim completion of:

- production rollout;
- A/B testing;
- traffic splitting;
- canary release;
- online experiment metrics;
- production observability / SLO / alerting;
- remote CI artifact hard claim;
- real-provider production quality certification;
- frontend behavior;
- DB schema / migration;
- API contract behavior change;
- prompt rewrite;
- real provider config change.

If any excluded item becomes required to make the local multi-agent system work, stop and report the blocker.

---

## 3. Current Recon Baseline to Revalidate

The following facts came from a user-pasted Codex Plan Mode output. Treat them as `USER_PROVIDED_SUBWINDOW`, not as final GitHub facts, until revalidated locally.

Expected recon baseline:

- `HEAD == origin/main == 12a140eeaf9ba89f3e475e7e81973623f15fd7d5` at the time of the pasted plan.
- Worktree was clean at that time.
- CodeGraph existed with `680 indexed files / 12294 nodes`.
- Architecture + eval sample command passed: `74 passed`.
- Phase 9 replay gate reportedly had `30 passed / 2 deferred`.
- Phase 12 L5 deterministic gate reportedly had `9 passed`.
- Negative controls reportedly failed as expected.
- C1/L5 contract catalog was reportedly in `apps/api/app/application/agents/definitions/catalog.py`.
- Runtime adapter was reportedly in `apps/api/app/application/agents/runtime/__init__.py` and instantiated by `apps/api/app/application/ai_runtime/facade.py`.
- Question / Feedback planned workflows were reportedly still called by `PolishUseCases`.
- Minimal three-agent slice was reportedly test-only with no product runtime caller.
- `build_validated_transport_request()` was reportedly used by Question, Feedback, progress tree, job match, and feedback graph trace.
- `LLM_PROVIDER=fake` reportedly fails closed in runtime env.

Revalidate these before patching. If they changed, update the local plan and gap register.

---

## 4. Capability Mapping for Option D

### Must close or validate locally

- `L5-002` — Supervisor / Orchestrator Agent registered and executable.
- `L5-003` — Cross-agent handoff / state / trace / replay.
- `L5-004` — Multi-agent product workflow with at least three business agents.
- `L5-005` — Controlled tool loop hardening with explicit bounds and stop conditions.
- `L5-006A` — Local multi-agent eval / replay / failure hardening.

### Must split / defer explicitly

Existing `L5-006` mixes local hardening with production release gate. Split it in source backfill:

- `L5-006A Local multi-agent eval / replay / failure hardening` — in scope for Option D.
- `L5-006B Production release gate / remote CI artifact / real-provider production certification / human production release decision` — out of scope and deferred.

### Must not overclaim

After Option D, the project may claim:

> Local complete controlled multi-agent capability is implemented and locally validated.

It must not claim:

> Production L5 release is complete.

unless a separate release goal later completes production release evidence.

---

## 5. Required End-to-End Local Workflow

Implement at least one end-to-end local product workflow with three or more collaborating business agents.

Recommended workflow:

```text
User answer submitted
  -> Supervisor / Orchestrator Agent
  -> polish_feedback_agent
  -> polish_asset_candidate_agent
  -> polish_progress_agent
  -> polish_question_agent, only if next-question gate allows
  -> MultiAgentRunResult with candidate refs, handoff refs, trace refs, HITL status
```

Minimum acceptable agent set:

```text
polish_feedback_agent
polish_asset_candidate_agent
polish_progress_agent
```

Preferred agent set:

```text
polish_feedback_agent
polish_asset_candidate_agent
polish_progress_agent
polish_question_agent
```

All outputs must be candidate / suggestion / validation / trace. No Agent may directly write formal business facts.

---

## 6. Runtime Mode

Add or reuse a local-only, default-off switch.

Acceptable names, depending on existing config style:

```text
AIFI_ENABLE_LOCAL_MULTI_AGENT_ORCHESTRATION=false
```

or

```text
AIFI_AGENT_RUNTIME_MODE=single_agent | local_multi_agent
```

Required semantics:

- Default behavior remains existing behavior.
- Flag off: existing Question / Feedback paths continue unchanged.
- Flag on: local product path can enter Supervisor / Orchestrator.
- The switch is not an experiment framework.
- No traffic split, cohort assignment, A/B variant, canary rollout, or production rollout logic.

---

## 7. Required Contracts / Models

Use existing contracts if already present. Add only minimal missing contracts.

Required concepts:

```text
MultiAgentCommand
MultiAgentRunResult
CrossAgentExecutionPlan
CrossAgentExecutionTrace
CrossAgentHandoff
MultiAgentStepResult
MultiAgentRunStatus
LocalMultiAgentRuntimeMode
BoundedLoopPolicy
HITLTrigger
ReplayFixtureRef
```

Required trace refs:

```text
agent_id
agent_version
run_id
input_refs
plan_refs
skill_refs
tool_refs
policy_refs
provider_refs
candidate_refs
validation_refs
handoff_refs
output_refs
low_confidence_flags
failure_reason
fallback_reason
```

Trace must not store:

```text
raw_prompt
system_prompt
developer_prompt
raw_provider_payload
raw_completion
full_resume
full_jd
full_asset_body
secrets
token
cookie
api_key
```

---

## 8. Execution Windows

### D-W0 — Option D Decision and Plan Backfill

Type: docs-only.

Goal:

- Persist Option D as the current implementation target.
- Record that production release and A/B testing are out of scope.
- Split `L5-006` into local hardening vs production release gate.
- Confirm capability statuses and gap taxonomy.

Allowed files:

```text
docs/03-delivery/refactor-multiagent-langgraph-implementation/**
docs/project-sources/**
docs/goals/**
```

Forbidden:

```text
apps/**
tests/**
evals/**
scripts/**
.github/**
package files
lockfiles
archive docs
```

Validation:

```bash
git diff --check
git diff -- docs/03-delivery/refactor-multiagent-langgraph-implementation docs/project-sources docs/goals
```

Commit:

```text
docs(l5): lock option d local multi-agent capability
```

---

### D-W1 — Recon and Gap Classification

Type: audit-first; patch only if missing architecture/boundary tests are trivial and within allowlist.

Goal:

- Revalidate current code facts.
- Locate current orchestrator/catalog/runtime/facade/replay/eval code.
- Confirm whether C0-C4 prerequisites are real or only wrappers.
- Produce an implementation gap map before editing runtime.

Must read first:

```text
AGENTS.md, if present
apps/api/app/application/agents/**
apps/api/app/application/ai_runtime/**
apps/api/app/application/polish/**
apps/api/app/domain/polish/policies/**
apps/api/app/application/llm/provider_boundary.py
apps/api/app/infrastructure/ai_runtime/**
tests/architecture/**
tests/application/agents/**
tests/domain/polish/**
tests/api/**
tests/evals/**
evals/**
scripts/evals/**
.github/workflows/eval-gate.yml, if present
docs/project-sources/**
docs/03-delivery/refactor-multiagent-langgraph-implementation/**
```

Required output artifact:

```text
docs/03-delivery/refactor-multiagent-langgraph-implementation/option_d_current_code_gap_map.md
```

Validation:

```bash
git status --short --branch --untracked-files=all
git rev-list --left-right --count HEAD...origin/main
PYTHONPATH=.:apps/api .venv/bin/python -m pytest tests/architecture tests/evals -q
git diff --check
```

Commit:

```text
docs(l5): add option d current-code gap map
```

---

### D-W2 — Orchestrator Contracts and Registry

Goal:

- Add or complete Supervisor / Orchestrator AgentDefinition.
- Ensure AgentDefinitionRegistry, SkillRegistry, ToolRegistry include all participants.
- Define cross-agent command/result/plan/trace/handoff contracts.
- Add architecture tests for candidate-only, no direct repository exposure, bounded loop policy, and trace redaction.

Allowed files:

```text
apps/api/app/application/agents/**
apps/api/app/application/polish/agents/**
tests/application/agents/**
tests/architecture/**
docs/project-sources/**
docs/03-delivery/refactor-multiagent-langgraph-implementation/**
```

Forbidden unless separately authorized:

```text
apps/api/app/api/v1/**
apps/api/app/infrastructure/db/**
database migrations
apps/web/**
prompt builders
real provider config
lockfiles
```

Validation:

```bash
PYTHONPATH=.:apps/api .venv/bin/python -m pytest tests/application/agents tests/architecture -q
git diff --check
```

Commit:

```text
refactor(agents): add local multi-agent orchestrator contracts
```

---

### D-W3 — Default-Off Local Product Runtime Wiring

Goal:

- Add a local-only default-off runtime path from Application Service / runtime facade into Supervisor / Orchestrator.
- Preserve existing behavior when flag is off.
- When flag is on, execute the local multi-agent workflow through typed handoff.
- Do not change public API contract.
- Do not write formal business facts from runtime.

Allowed files:

```text
apps/api/app/application/agents/runtime/**
apps/api/app/application/ai_runtime/**
apps/api/app/application/polish/**
apps/api/app/infrastructure/ai_runtime/**
tests/application/agents/**
tests/api/**
tests/architecture/**
```

Forbidden unless separately authorized:

```text
apps/api/app/api/v1/**
apps/api/app/infrastructure/db/**
database migrations
apps/web/**
prompt rewrite
real provider config
production deployment config
A/B experiment framework files
```

Validation:

```bash
PYTHONPATH=.:apps/api .venv/bin/python -m pytest tests/application/agents tests/architecture -q
PYTHONPATH=.:apps/api .venv/bin/python -m pytest tests/api -k "agent or handoff or runtime or multi_agent or l5" -q
git diff --check
```

Required tests:

- flag off preserves existing behavior;
- flag on enters orchestrator;
- no Agent direct formal write;
- no Tool direct repository exposure;
- candidate refs returned;
- formal write handoff required.

Commit:

```text
refactor(runtime): wire default-off local multi-agent path
```

---

### D-W4 — HITL, Bounded Loop, Replay, Failure Hardening

Goal:

- Add local replay fixtures.
- Add failure cases.
- Add HITL gates.
- Add bounded-loop enforcement.
- Ensure provider unavailable / validation failed / handoff failed do not become success.

Required failure fixtures:

```text
insufficient_context
asset_conflict
formal_write_required
low_confidence
ownership_ambiguity
provider_unavailable
validation_failed
handoff_failure
replay_mismatch
bounded_loop_stop
```

Allowed files:

```text
apps/api/app/application/agents/**
apps/api/app/application/ai_runtime/**
apps/api/app/infrastructure/ai_runtime/**
tests/application/agents/**
tests/evals/**
evals/**
scripts/evals/**
docs/project-sources/**
```

Forbidden:

```text
production release workflow
A/B testing
remote CI hard claim
real-provider production certification
DB schema change
API contract change
frontend
```

Validation:

```bash
PYTHONPATH=.:apps/api .venv/bin/python -m pytest tests/application/agents tests/evals tests/architecture -q
PYTHONPATH=.:apps/api .venv/bin/python scripts/evals/run_l5_eval_suite.py --mode deterministic --report-dir /tmp/aifi-option-d-l5-local
```

If the exact eval script or options differ, discover the current command from `scripts/evals/**` and document the actual command used.

Commit:

```text
test(l5): add local multi-agent replay and failure gates
```

---

### D-W5 — Local Eval Gate and Final Source Backfill

Goal:

- Run all local gates.
- Generate or update local trace/eval evidence without committing volatile reports unless the repo already tracks such reports.
- Backfill Matrix / Acceptance Gates / Decision Log / Risk Register / Roadmap.
- Explicitly defer production release, A/B testing, remote CI artifact hard claim, and real-provider production certification.

Allowed files:

```text
docs/project-sources/**
docs/03-delivery/refactor-multiagent-langgraph-implementation/**
docs/goals/**
tests/evals/**
evals/**
scripts/evals/**
.github/workflows/eval-gate.yml only if needed for local deterministic gate and already in current release scope
```

Forbidden unless separately authorized:

```text
production deployment config
A/B testing framework
remote release artifact automation
real provider config
frontend
DB schema/migration
API contract behavior
```

Validation:

```bash
PYTHONPATH=.:apps/api .venv/bin/python -m pytest tests/domain/polish tests/application/agents tests/architecture -q
PYTHONPATH=.:apps/api .venv/bin/python -m pytest tests/api -k "agent or handoff or canonical or source_support or provider or fake or runtime or multi_agent or l5" -q
PYTHONPATH=.:apps/api .venv/bin/python -m pytest tests/evals -q
PYTHONPATH=.:apps/api .venv/bin/python scripts/evals/run_eval_gate.py --suite phase9 --mode replay --report-dir /tmp/aifi-phase9-eval
PYTHONPATH=.:apps/api .venv/bin/python scripts/evals/run_l5_eval_suite.py --mode deterministic --report-dir /tmp/aifi-option-d-l5-local
git diff --check
```

Run negative controls if present. If the command is not known, search tests/evals and scripts/evals, run the discovered negative controls, and document the exact command. Expected negative controls must fail for the right reason.

Commit:

```text
docs(l5): backfill option d local capability evidence
```

---

## 9. Global Validation Commands

Preflight:

```bash
git fetch origin main
git status --short --branch --untracked-files=all
git rev-list --left-right --count HEAD...origin/main
PYTHONPATH=.:apps/api .venv/bin/python -m pytest tests/architecture tests/evals -q
```

Core local validation:

```bash
PYTHONPATH=.:apps/api .venv/bin/python -m pytest tests/domain/polish tests/application/agents tests/architecture -q
PYTHONPATH=.:apps/api .venv/bin/python -m pytest tests/api -k "agent or handoff or canonical or source_support or provider or fake or runtime or multi_agent or l5" -q
PYTHONPATH=.:apps/api .venv/bin/python -m pytest tests/evals -q
PYTHONPATH=.:apps/api .venv/bin/python scripts/evals/run_eval_gate.py --suite phase9 --mode replay --report-dir /tmp/aifi-phase9-eval
PYTHONPATH=.:apps/api .venv/bin/python scripts/evals/run_l5_eval_suite.py --mode deterministic --report-dir /tmp/aifi-option-d-l5-local
git diff --check
```

Optional full validation if local runtime wiring touches broad application behavior:

```bash
PYTHONPATH=.:apps/api .venv/bin/python -m pytest -q
```

Do not run web/frontend tests unless Option D changes relevant behavior or the repo's release gate requires them.

---

## 10. Commit Policy

Use small commits. Each commit covers one capability group and its tests/backfill.

Recommended sequence:

```text
1. docs(l5): lock option d local multi-agent capability
2. docs(l5): add option d current-code gap map
3. refactor(agents): add local multi-agent orchestrator contracts
4. refactor(runtime): wire default-off local multi-agent path
5. test(l5): add local multi-agent replay and failure gates
6. docs(l5): backfill option d local capability evidence
```

Do not mix provider, runtime, DB, frontend, eval, and docs closeout into one commit.

Before every commit:

```bash
git diff --check
git status --short --branch --untracked-files=all
```

Also run the window-specific validation commands.

Rollback:

- Prefer `git revert <commit>` for a scoped capability commit.
- Do not use `git reset --hard` as the default rollback method.
- Runtime behavior must remain protected by the default-off local switch.

---

## 11. Stop Conditions

Stop and report instead of patching if any of these occur:

- Need to modify forbidden files.
- Need DB schema / migration.
- Need API contract behavior change.
- Need frontend behavior change.
- Need prompt rewrite.
- Need real provider config change.
- Need production release / A/B / canary / traffic split infrastructure.
- Need remote CI artifact hard claim but the artifact is not visible locally.
- Need to claim real-provider production quality certification.
- Agent would directly write formal business facts.
- Tool would directly expose a repository.
- Runtime would bypass `Application Service -> Domain Policy -> Handoff`.
- Provider request would include full prompt, full resume, full JD, full asset body, raw provider payload, or secrets.
- Fake would be required outside tests / evals / replay.
- Current code contradicts Project source and the gap cannot be documented.
- Tests fail and repair requires forbidden scope.

---

## 12. Done Criteria for Option D

Option D is complete only when all of the following are true:

1. Local Option D decision is recorded in Project sources.
2. Current code recon is recorded with source tags.
3. Supervisor / Orchestrator Agent is registered and executable.
4. At least three business agents participate in one local product workflow.
5. Product/runtime caller exists behind local-only default-off switch.
6. Flag-off path preserves existing behavior.
7. Flag-on path enters Orchestrator and returns candidate refs.
8. All cross-agent communication uses typed handoff.
9. Shared CanonicalEvidencePack / InterviewContext / SourceSupportSummary is used or any gap is explicit.
10. Cross-agent plan / state / trace / replay exists.
11. Controlled loop has max_steps / max_retries / timeout / stop_conditions.
12. HITL covers asset conflict, formal write, low confidence, and ownership ambiguity.
13. Agents output only candidate / suggestion / validation / plan / trace.
14. Formal write remains `Application Service -> Domain Policy -> Handoff`.
15. ToolRegistry / ToolDefinition prevents direct repository exposure.
16. Provider boundary remains compact and fail-closed.
17. Fake remains tests / evals / replay only.
18. Local deterministic multi-agent replay passes.
19. Failure fixtures pass and negative controls fail for the expected reason.
20. Project source backfill is complete.
21. Production release / A/B testing / remote CI hard claim / real-provider production certification are explicitly deferred or out of scope.
22. No capability is marked `done` unless design, code, old-duty removal, unit/eval evidence, validation commands, no forbidden scope, source backfill, gap closure/deferred reason, and user-confirmed decisions are all present.

---

## 13. Final Report Required from Codex

At the end of every window and at the end of the full goal, report:

1. Root Cause
2. What Changed
3. Files Changed
4. Behavior Before / After
5. Validation Commands and Results
6. Capability Status Updates
7. Deferred Gaps
8. Remaining Risks
9. Rollback Plan
10. Follow-up Goal

The full-goal final report must explicitly say whether Option D is:

```text
completed
blocked
deferred
partially completed
```

and must not use production-release wording unless a separate release goal is completed.

---

# Trigger Prompts

## A. Codex `/plan` prompt

Paste this first in Codex CLI:

```text
/plan
You are in the AiForInterviewer repository.

Do not edit code yet.

Task: reconcile the user-confirmed Option D target with current GitHub code, tests, evals, Project sources, and the canonical Option D source package.

Option D means Local Complete Multi-Agent Capability:
- combine default-off product/runtime wiring with local multi-agent replay, trace, HITL, bounded-loop, and failure hardening;
- exclude production release readiness, A/B testing, traffic split, canary rollout, online experiment metrics, production observability/SLO, remote CI artifact hard claim, and real-provider production quality certification unless separately authorized.

Source of truth:
1. USER_CONFIRMED Option D.
2. GitHub current code.
3. Current tests/evals.
4. Project sources.
5. GOAL0531 historical intent only.
6. Subwindow output only after 总控 audit.

First revalidate the prior recon:
- git fetch origin main
- git status --short --branch --untracked-files=all
- git rev-list --left-right --count HEAD...origin/main
- PYTHONPATH=.:apps/api .venv/bin/python -m pytest tests/architecture tests/evals -q

Then inspect:
- AGENTS.md if present
- apps/api/app/application/agents/**
- apps/api/app/application/ai_runtime/**
- apps/api/app/application/polish/**
- apps/api/app/domain/polish/policies/**
- apps/api/app/application/llm/provider_boundary.py
- apps/api/app/infrastructure/ai_runtime/**
- tests/architecture/**
- tests/application/agents/**
- tests/evals/**
- scripts/evals/**
- docs/project-sources/**
- docs/03-delivery/refactor-multiagent-langgraph-implementation/**

Produce a plan only. Do not patch implementation files.

The plan must include:
1. Current code facts with source tags.
2. Option D gap map.
3. L5-006 split into L5-006A local eval/replay/failure hardening and L5-006B production release deferred.
4. Allowed/forbidden files per window.
5. Validation commands per window.
6. Commit boundaries.
7. Stop conditions.
8. Exact source backfill files.
9. Whether the previous current-code-informed plan needs revision before goal execution.
```

## B. Docs-only bootstrap prompt

After reviewing the plan, paste this as a normal Codex task, not `/goal`, to create the repo-local goal file:

```text
Revise the docs-only Option D goal package in the repository.

Allowed files:
- docs/03-delivery/refactor-multiagent-langgraph-implementation/option_d_local_complete_multi_agent_goal.md
- docs/project-sources/** only if needed to record `DEC-L5-015` Option D and split L5-006A/L5-006B
- docs/goals/** only if this repo already uses docs/goals for goal evidence

Forbidden:
- implementation files
- tests
- eval scripts
- API routes
- DB schema/migration
- frontend
- provider/prompt behavior files
- lockfiles

Content requirements:
- Record Option D as user-confirmed local complete multi-agent target.
- Explicitly exclude production release and A/B testing.
- Split L5-006 into L5-006A local hardening and L5-006B production release deferred.
- Include D-W0 through D-W5 windows, allowed/forbidden files, validations, commits, stop conditions, and done criteria.
- Mark any unverified current-code facts as needing local recon.

Validation:
- git diff --check
- git diff -- docs/03-delivery/refactor-multiagent-langgraph-implementation docs/project-sources docs/goals

Final report using the project window format.
```

Commit after successful docs-only validation:

```bash
git add docs/03-delivery/refactor-multiagent-langgraph-implementation/option_d_local_complete_multi_agent_goal.md docs/project-sources docs/goals 2>/dev/null || true
git commit -m "docs(l5): lock option d local multi-agent capability"
```

## C. Master `/goal` prompt

Use this after the Option D goal package exists in the repo:

```text
/goal Implement Option D: Local Complete Multi-Agent Capability for AiForInterviewer by following docs/03-delivery/refactor-multiagent-langgraph-implementation/option_d_local_complete_multi_agent_goal.md. Build a real locally executable controlled multi-agent system, not a production release program. Revalidate GitHub current code and tests before patching. Work in D-W0..D-W5 scoped checkpoints. Implement Supervisor/Orchestrator, at least three business agents in one local product workflow, typed handoff, cross-agent state/trace/replay, bounded loop, HITL, candidate-only outputs, formal write via Application Service -> Domain Policy -> Handoff, compact fail-closed provider boundary, and fake-only tests/evals/replay. Exclude production release readiness, A/B testing, traffic split, canary rollout, remote CI hard claim, and real-provider production certification unless separately authorized. Validate after every checkpoint, repair before continuing, commit only validated capability groups, and backfill Project sources. Stop on forbidden scope or if completion would require overclaiming production release.
```

## D. Goal lifecycle commands

```text
/goal
/goal pause
/goal resume
/goal clear
```

Use `/goal` with no arguments to inspect the active goal.

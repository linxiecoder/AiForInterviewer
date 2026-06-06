---
title: P11-W3-MULTI-AGENT-WORKFLOW
type: note
permalink: ai-for-interviewer/docs/goals/2026-06-07/windows/p11-w3-multi-agent-workflow
---

# P11-W3-MULTI-AGENT-WORKFLOW

## Activation rule

Execute only after P11-W1 and P11-W2 are validated. This window must return to 总控 after completion because it is the first product proof for L5-004.

## Window ID

`P11-W3-MULTI-AGENT-WORKFLOW`

## Phase

Phase 11 — L5 Controlled Multi-Agent Orchestration

## Capability IDs

- L5-004
- L5-003
- AGT-005
- AGT-006
- AGT-007
- QAG-004
- FAG-006
- FAG-007
- FAG-008

## Goal

Implement at least one end-to-end product workflow in which three or more business agents collaborate through typed candidate handoff.

Recommended candidate workflow:

```text
Question Agent -> Feedback Agent -> AssetCandidate Agent / Progress Agent / TrainingPlan Agent
```

Actual participating agents must be selected based on GitHub recon.

## Must recon first

- Question Agent planner/workflow
- Feedback Agent planner/workflow
- existing asset candidate/progress/training plan/report agent or service code
- application services owning formal writes
- domain policies for asset conflict / progress / next action
- handoff and trace contracts from P11-W2
- tests/evals for question/feedback and candidate handoff

## Allowed files

Candidate scope only; adjust after recon:

```text
apps/api/app/application/agents/**
apps/api/app/application/polish/agents/**
apps/api/app/application/polish/services/**
apps/api/app/application/polish/context/**
tests/architecture/**
tests/evals/**
tests/api/**
docs/**
project_sources/**
```

## Forbidden files

```text
apps/api/app/infrastructure/db/**
database migrations
apps/api/app/infrastructure/llm/**
prompt asset files unless explicitly required and approved
provider behavior implementation files unless explicitly approved
API contract changes unless explicitly approved
```

## Behavior change allowed

Limited behavior change is allowed only for the new L5 workflow path behind an explicit flag or isolated entrypoint. Existing Question / Feedback behavior must remain backward-compatible unless explicitly authorized.

## Prompt/schema/provider change allowed

No provider behavior rewrite. No prompt rewrite unless 总控 explicitly approves a prompt-specific window.

## DB schema change allowed

No.

## Implementation requirements

- Use typed handoff, not raw prompt sharing.
- Involve at least three business agents or agent-like registered definitions.
- Ensure each agent output is candidate/suggestion only.
- Ensure formal writes still go through Application Service + Domain Policy + Handoff.
- Record trace timeline with plan refs, skill refs, tool refs, policy refs, handoff refs, validation refs.
- Use shared CanonicalEvidencePack / InterviewContext / SourceSupportSummary where applicable.
- Add integration tests for happy path and at least one blocked handoff.
- Do not mark L5 done in this window; only L5-004 implemented/validated candidate.

## Validation commands

```bash
pytest tests/architecture
pytest tests/evals
pytest tests/api
```

If full `tests/api` is too broad or environment-bound, run targeted integration tests and record skipped coverage.

## Rollback

Revert changed files in allowed scope. Remove new workflow flag/entrypoint if added. No DB rollback.

## Done criteria

- One three-or-more-agent workflow exists and is tested.
- Handoff is typed and candidate-only.
- Formal write path remains unchanged and protected.
- Trace records cross-agent handoff refs.
- Tests/evals pass or blockers are returned to 总控.
- Source backfill updated or proposed.

## Stop conditions

Stop and return to 总控 if:

- fewer than three agents can be safely included;
- direct formal write seems necessary;
- DB schema change is required;
- provider/prompt rewrite is required;
- existing product behavior would change unexpectedly;
- tests fail in a way that compromises candidate/formal boundary.
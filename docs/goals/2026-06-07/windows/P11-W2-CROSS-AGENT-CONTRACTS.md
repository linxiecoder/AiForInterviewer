---
title: P11-W2-CROSS-AGENT-CONTRACTS
type: note
permalink: ai-for-interviewer/docs/goals/2026-06-07/windows/p11-w2-cross-agent-contracts
---

# P11-W2-CROSS-AGENT-CONTRACTS

## Activation rule

Execute only after `P11-W1-SUPERVISOR-ORCHESTRATOR-DEFINITION` is validated or explicitly approved to proceed.

## Window ID

`P11-W2-CROSS-AGENT-CONTRACTS`

## Phase

Phase 11 — L5 Controlled Multi-Agent Orchestration

## Capability IDs

- L5-003
- AGT-006
- AGT-007
- CTX-001
- CTX-002
- CTX-003

## Goal

Establish typed cross-agent plan, handoff, state, checkpoint, trace, and replay contracts.

## Must recon first

- existing handoff contracts
- existing trace contracts
- existing runtime/checkpoint/replay abstractions
- CanonicalEvidencePack / SourceSupportSummary / InterviewContext code
- Question / Feedback Agent candidate outputs
- architecture and eval tests

## Allowed files

```text
apps/api/app/application/agents/contracts/**
apps/api/app/application/agents/handoff/**
apps/api/app/application/agents/runtime/**
apps/api/app/application/agents/registry/**
apps/api/app/application/polish/context/**
tests/architecture/**
tests/evals/**
docs/**
project_sources/**
```

## Forbidden files

```text
apps/api/app/infrastructure/db/**
database migrations
apps/api/app/infrastructure/llm/**
prompt asset files
provider behavior implementation files
API route contract files
```

## Behavior change allowed

No product behavior change. Contract additions only.

## Prompt/schema/provider change allowed

No provider behavior change. Agent/handoff schemas may be added if backward-compatible.

## DB schema change allowed

No.

## Implementation requirements

- Add or align `CrossAgentPlan` contract.
- Add or align `CrossAgentHandoff` contract.
- Add or align `CrossAgentState` / checkpoint / replay refs.
- Add or align trace fields: `agent_id`, `run_id`, `plan_refs`, `skill_refs`, `tool_refs`, `policy_refs`, `handoff_refs`, `validation_refs`.
- Prohibit raw prompt, system prompt, developer prompt, raw provider payload, raw completion, full resume, full JD, secrets in trace/state.
- Ensure handoff remains candidate-only and formal write requires Application Service + Domain Policy.
- Add tests that fail if raw model IO or direct formal write is present in cross-agent contracts.

## Validation commands

```bash
pytest tests/architecture
pytest tests/evals || true
```

## Rollback

Revert changed files in allowed scope. No DB rollback.

## Done criteria

- Cross-agent plan/handoff/state/trace/replay contracts exist or are aligned.
- Forbidden trace/state keys are blocked or tested.
- Candidate-only and formal write handoff are enforced.
- No prompt/provider/DB/API behavior changed.
- Tests pass or inability is recorded with risk.
- Source backfill updated or proposed.

## Stop conditions

Stop and return to 总控 if this requires persistence schema migration, provider behavior changes, or formal write behavior changes.
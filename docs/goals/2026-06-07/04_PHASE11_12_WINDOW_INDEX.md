---
title: 04_PHASE11_12_WINDOW_INDEX
type: note
permalink: ai-for-interviewer/docs/goals/2026-06-07/04-phase11-12-window-index
---

# Phase 11 / Phase 12 Window Index

## Activation rule

These windows are draft execution targets. They must be activated only after:

1. `L5-READINESS-RECON-W1` returns GREEN; or
2. AMBER blockers are closed and 总控 approves entering Phase 11.

## Phase 11: L5 Controlled Multi-Agent Orchestration

| Order | Window ID | Purpose |
|---:|---|---|
| 1 | `P11-W1-SUPERVISOR-ORCHESTRATOR-DEFINITION` | Define/register Supervisor / Orchestrator Agent with bounded planning. |
| 2 | `P11-W2-CROSS-AGENT-CONTRACTS` | Establish cross-agent plan, handoff, state, checkpoint, trace, replay contracts. |
| 3 | `P11-W3-MULTI-AGENT-WORKFLOW` | Implement at least one three-or-more-agent typed handoff product workflow. |
| 4 | `P11-W4-CONTROLLED-TOOL-LOOP-HITL` | Harden max_steps, retries, timeout, stop_conditions, and HITL triggers. |
| 5 | `P11-W5-L5-INTEGRATION-BOUNDARY-TESTS-BACKFILL` | Add integration/boundary tests and source backfill for Phase 11. |

## Phase 12: L5 Eval, Hardening, and Release Gate

| Order | Window ID | Purpose |
|---:|---|---|
| 6 | `P12-W1-MULTI-AGENT-EVAL-SUITE` | Build L5 multi-agent eval suite and graders. |
| 7 | `P12-W2-REPLAY-RESUME-FAILURE-FIXTURES` | Add replay/resume/failure fixtures for cross-agent scenarios. |
| 8 | `P12-W3-CI-OBSERVABILITY-TRACE-REPORT` | Add CI gate, trace report, failure triage, rollback policy. |
| 9 | `P12-W4-RELEASE-READINESS-AUDIT-BACKFILL` | Final L5 audit, source backfill, human release decision. |

## Expected checkpoints

Mandatory:

- After `L5-READINESS-RECON-W1`.
- After `P11-W3-MULTI-AGENT-WORKFLOW`.
- After `P12-W1-MULTI-AGENT-EVAL-SUITE`.
- After `P12-W4-RELEASE-READINESS-AUDIT-BACKFILL`.

Recommended:

- After every failed test/eval.
- After any stop condition.
- Before marking any L5 capability validated/done.
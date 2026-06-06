---
title: README
type: note
permalink: ai-for-interviewer/docs/goals/2026-06-07/readme
---

# 2026-06-07 L5 Goal Pack

This pack is intended to be copied or unzipped at repository root so that files land under:

```text
docs/goals/2026-06-07/
```

## Purpose

Use one umbrella goal to govern the remaining L5 work, but execute the work through scoped windows.

The first executable window is:

```text
01_L5_READINESS_RECON_W1.md
```

All Phase 11 / Phase 12 window files under `windows/` are draft activation targets. They must not be executed automatically before `L5-READINESS-RECON-W1` is reviewed by 总控.

## Execution order

Recommended order:

1. Read `00_GOAL_L5_MASTER.md`.
2. Execute `01_L5_READINESS_RECON_W1.md` in Codex against GitHub main.
3. Archive the recon output.
4. Apply `03_RECON_DECISION_ROUTING.md`:
   - GREEN: proceed to Phase 11 window sequence.
   - AMBER: close named blockers first, then Phase 11.
   - RED: do not enter Phase 11; return to Phase 1-10 closure.
5. Use `02_EXECUTION_REVIEW_POLICY.md` to decide whether each window output must return to 总控.

## Important rule

Do not treat this pack as evidence that code has already reached L5. The repository state must be proven by GitHub main and current tests/evals.

## Files

```text
00_GOAL_L5_MASTER.md
01_L5_READINESS_RECON_W1.md
02_EXECUTION_REVIEW_POLICY.md
03_RECON_DECISION_ROUTING.md
04_PHASE11_12_WINDOW_INDEX.md
windows/
  P11-W1-SUPERVISOR-ORCHESTRATOR-DEFINITION.md
  P11-W2-CROSS-AGENT-CONTRACTS.md
  P11-W3-MULTI-AGENT-WORKFLOW.md
  P11-W4-CONTROLLED-TOOL-LOOP-HITL.md
  P11-W5-L5-INTEGRATION-BOUNDARY-TESTS-BACKFILL.md
  P12-W1-MULTI-AGENT-EVAL-SUITE.md
  P12-W2-REPLAY-RESUME-FAILURE-FIXTURES.md
  P12-W3-CI-OBSERVABILITY-TRACE-REPORT.md
  P12-W4-RELEASE-READINESS-AUDIT-BACKFILL.md
templates/
  MASTER_PROMPT_PREFIX.md
  WINDOW_RESULT_DIGEST.md
```
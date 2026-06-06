---
title: 03_RECON_DECISION_ROUTING
type: note
permalink: ai-for-interviewer/docs/goals/2026-06-07/03-recon-decision-routing
---

# Recon Decision Routing

Use this document after `L5-READINESS-RECON-W1` returns its final report.

## GREEN routing

Condition:

```text
Phase 1-10 foundation is sufficiently closed.
No L5 blocker outside Phase 11/12 remains.
Tests/evals are sufficient to enter Phase 11.
```

Action:

Proceed to:

```text
windows/P11-W1-SUPERVISOR-ORCHESTRATOR-DEFINITION.md
```

Recommended sequence:

```text
P11-W1 -> P11-W2 -> P11-W3 -> P11-W4 -> P11-W5 -> P12-W1 -> P12-W2 -> P12-W3 -> P12-W4
```

Checkpoint requirements:

- Return P11-W3 result to 总控 because it proves the first three-or-more-agent product workflow.
- Return P12-W1 result to 总控 because it defines the L5 eval suite.
- Return P12-W4 result to 总控 for human release decision.

## AMBER routing

Condition:

```text
Phase 11 is close, but 2-6 named foundation blockers remain.
```

Action:

Do not execute Phase 11 immediately. First generate or execute blocker windows in the order returned by recon.

Each blocker window must include:

- Window ID
- Phase
- Capability IDs
- allowed files
- forbidden files
- tests/evals
- rollback
- done criteria
- source backfill

After blockers:

- Run only the targeted tests/evals proving blocker closure.
- Re-run relevant parts of `L5-READINESS-RECON-W1` or create `L5-READINESS-RECON-W2`.
- Enter Phase 11 only after 总控 accepts the AMBER closure report.

## RED routing

Condition:

```text
Major Phase 1-10 foundation capabilities are missing or unvalidated.
```

Action:

Do not execute Phase 11 or Phase 12 windows.

Create a new closure roadmap:

```text
FOUNDATION-CLOSURE-ROADMAP-W1
```

Then resume from the earliest blocking Phase.

Likely blocker classes:

- DDD rails / PolishUseCases facade not sufficiently closed.
- CanonicalEvidencePack / SourceSupportSummary not unified.
- Domain Policies not migrated.
- Agent contracts / skills / tools incomplete.
- Question / Feedback planned workflows not validated.
- Provider fail-closed incomplete.
- Runtime/replay/trace foundation incomplete.
- Eval/CI/regression foundation insufficient.

## Never auto-upgrade to L5

Do not mark L5 done because:

- Question Agent exists.
- Feedback Agent exists.
- LangGraph runtime exists.
- Agent Platform C4 exists.
- Unit tests pass.
- Fake eval passes.

L5 requires Phase 11 / Phase 12 evidence, cross-agent workflow, eval/replay/CI, and human release decision.
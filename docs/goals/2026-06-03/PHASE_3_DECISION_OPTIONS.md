---
title: PHASE_3_DECISION_OPTIONS
type: decision-options
status: evidence-only
owner: P3-W0-DOMAIN-POLICY-SCOPE-LOCK
permalink: ai-for-interviewer/docs/goals/2026-06-03/phase-3-decision-options
---

# Phase 3 Decision Options

本文件记录 `P3-W0-DOMAIN-POLICY-SCOPE-LOCK` 后的 controller decision options。它只提供执行顺序建议，不授权实现。

## 1. Decision Context

P3-W0 recon found:

- Existing P3-W1 source support work is present and should be treated resume-aware.
- Phase 2 closeout evidence files requested by the P3-W0 prompt are missing from `docs/goals/2026-06-03/`.
- SRC-001 and CTX-002 remain deferred / partial.
- Question grounding, follow-up coverage, feedback review rules, and feedback next action are still primarily application-layer policy-like logic.

Any implementation window must wait for controller confirmation.

## 2. Options

| Option | Name | Sequence | Benefits | Risks | Recommendation |
| --- | --- | --- | --- | --- | --- |
| A | Resume-aware strict Phase 3 | Accept P3-W0 docs; treat P3-W1 as `partial_with_deferred_gap`; proceed to P3-W2, P3-W3, P3-W4, P3-W5, P3-W6; keep Phase 2 / SRC / CTX gaps explicit. | Fastest path to actual Domain Policy extraction; avoids duplicating P3-W1; respects current code. | Carries missing Phase 2 closeout evidence and CTX-002 gap into implementation. | Recommended if controller accepts deferred input gaps. |
| B | Governance backfill first | Stop implementation; create missing Phase 2 closeout / source backfill evidence and clarify P3-W1 sequence before P3-W2. | Cleans source hierarchy before code changes; reduces audit ambiguity. | Delays Phase 3 implementation; may become docs-heavy if no new code facts exist. | Recommended if controller wants clean governance order above speed. |
| C | CTX-002 repair before question policies | After P3-W0, open a dedicated SourceSupportSummary repair window; only then run P3-W2. | Reduces semantic dual-track between `SourceSupportDecision`, `source_support_level`, and target summary. | May require payload propagation decisions and could approach prompt/API boundaries; must be tightly scoped. | Use only if controller considers CTX-002 blocking. |
| D | Feedback-first extraction | Accept P3-W1 partial and skip question policies temporarily; run P3-W3 / P3-W4 first, then return to P3-W2. | Existing feedback tests are broad and feedback rules are concentrated in one module. | Leaves question grounding/follow-up policy drift open; may invert intended source-support-to-question sequence. | Not recommended unless question policy scope is blocked. |

## 3. Recommended Order

Recommended default: Option A.

Suggested next authorized prompt:

```text
/goal Continue Phase 3 using docs/goals/2026-06-03/PHASE_3_WINDOW_CATALOG.md.
Accept P3-W1 as partial_with_deferred_gap for now.
Execute only P3-W2-QUESTION-DOMAIN-POLICIES.
Do not modify prompt assets, provider behavior, DB schema, API contracts, Agent runtime, frontend, or formal write behavior.
Stop if the missing Phase 2 closeout evidence or CTX-002 gap becomes blocking.
```

If controller chooses governance backfill first, use:

```text
/goal Backfill missing Phase 2 closeout evidence before Phase 3 implementation.
Use docs/goals/2026-06-03/PHASE_3_ENTRY_GAP_REGISTER.md as input.
Docs only. Do not modify apps/** or tests/**.
```

If controller chooses CTX-002 repair first, use:

```text
/goal Open a dedicated CTX-002 SourceSupportSummary repair window.
Use docs/goals/2026-06-03/PHASE_3_ENTRY_GAP_REGISTER.md and keep prompt/provider/DB/API/Agent runtime changes forbidden unless explicitly approved.
```

## 4. Decision Questions

| Question | Required decision |
| --- | --- |
| Phase 2 missing closeout evidence | Should Phase 3 implementation proceed with the gap recorded, or should Phase 2 evidence be backfilled first? |
| Existing P3-W1 source support work | Should P3-W1 be accepted as partial, audited/repair-tested, or re-opened for CTX-002 work? |
| Next implementation window | Should the next authorized window be P3-W2, CTX-002 repair, or governance backfill? |
| Window granularity | Should P3-W2 remain combined for grounding + follow-up, or be split only after controller approval if recon shows it is too large? |

## 5. Non-Goals for All Options

All options keep these items out of scope unless controller explicitly stops and re-authorizes:

- Prompt rewrite.
- Provider request / transport behavior change.
- DB schema or migration change.
- API route or response contract change.
- LangGraph / Agent runtime replacement.
- Formal asset / weakness / training writes from Agent output.
- Frontend changes.
- New delivery, roadmap, or task system.

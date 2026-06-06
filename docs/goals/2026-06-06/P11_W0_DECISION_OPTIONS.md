---
title: P11_W0_DECISION_OPTIONS
type: goal-evidence
status: proposed_options
permalink: ai-for-interviewer/docs/goals/2026-06-06/p11-w0-decision-options
---

# P11-W0 Decision Options

Window ID: `P11-W0-L5-SCOPE-LOCK-GAP-RECONCILIATION`

All options below are proposed only. P11-W0 does not select, confirm, implement or sequence the next implementation window.

## Common Guardrails

Every option must preserve:

- Phase 0-10 as L5 Foundation `closed_with_deferred_gaps`, not L5 release.
- `deferred_remote_ci_gap` unless visible GitHub Actions evidence is cited in a separate verification window.
- Phase 8 runtime deferred gaps unless the option explicitly scopes implementation and tests for a specific gap.
- Stale committed eval report metadata risk unless a separate report refresh window is authorized.
- Candidate-only Agent outputs.
- Formal write path: Application Service -> Domain Policy -> Handoff.
- No prompt/provider/API/DB/frontend/domain/runtime behavior changes unless separately scoped.
- No committed eval report rewrite unless separately scoped.

## Option A: Contract-first Orchestrator

Status: `proposed`

Next window only adds:

- Supervisor / Orchestrator Agent definition.
- Typed cross-agent goal decomposition contract.
- Cross-agent plan contract.
- Typed cross-agent handoff / state / checkpoint / replay / trace contracts.
- Architecture and contract tests.

Pros:

- Safest boundary.
- Lowest behavior risk.
- Prevents fake Supervisor / Orchestrator implementation.

Cons:

- No user-visible multi-agent workflow yet.
- May leave product value unproven until a later vertical slice.

Must not claim:

- L5 release.
- Product-level multi-agent workflow.
- Runtime gap closure beyond the scoped contracts.

## Option B: Product Vertical Slice First

Status: `proposed`

Next window builds the smallest three-or-more-business-agent workflow, for example:

`Supervisor / Orchestrator -> Feedback Agent -> AssetCandidate Agent -> Progress / Weakness / TrainingPlan Agent`

Pros:

- Proves product value earlier.
- Reduces risk of contract-only platform growth without workflow evidence.

Cons:

- Higher runtime, handoff, HITL and trace risk.
- Must either close or explicitly carry more Phase 8 runtime gaps.

Required gates:

- Candidate-only output for each business agent.
- Typed handoff and trace timeline.
- HITL for asset conflict, formal write and validation-failed partial result.
- No Agent direct DB/repository write.

## Option C: Runtime-hardening First

Status: `proposed`

Next window closes selected Phase 8 runtime gaps before product orchestration:

- Future / indirect graph tool-loop coverage.
- Runner-bound HITL outside current generic/Question/Feedback paths.
- Complete trace population for remaining product/future runtime events.
- Runtime status taxonomy boundaries needed by orchestration.

Pros:

- Reduces replay, HITL and trace risk before L5 orchestration.
- Safer long-term foundation for the Supervisor / Orchestrator.

Cons:

- Delays visible L5 product workflow.
- Requires careful scope to avoid broad runtime refactor.

Must not claim:

- Supervisor / Orchestrator implementation unless included in a later option.
- L5 release or Phase 12 release gate.

## Option D: Eval-first L5 Harness

Status: `proposed`

Next window creates multi-agent eval fixtures and failure cases before implementation:

- Multi-agent regression suite design.
- Cross-agent replay fixture skeleton.
- Failure-mode cases for fake orchestration, serial calls disguised as MultiAgent, missing HITL, missing trace and candidate/formal boundary breach.
- CI/report contract draft for Phase 12.

Pros:

- Avoids false L5 claims.
- Makes Phase 11 implementation test-driven.

Cons:

- May produce eval scaffolding before product behavior exists.
- Cannot certify real-provider quality or L5 release by itself.

Must not claim:

- Real-provider quality certification.
- Remote CI success unless visible artifact exists.
- L5 release with replay-only evidence.

## Controller Decision Required

No option is confirmed by P11-W0. The next window must receive a fresh scope lock with one selected option, allowed files, forbidden files, behavior-change permission, validation plan and stop conditions.

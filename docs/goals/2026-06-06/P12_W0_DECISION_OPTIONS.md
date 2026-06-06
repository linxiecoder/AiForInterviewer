---
title: P12_W0_DECISION_OPTIONS
type: decision-options
status: proposed
permalink: ai-for-interviewer/docs/goals/2026-06-06/p12-w0-decision-options
---

# P12-W0 Decision Options

Window ID: `P12-W0-RELEASE-GATE-SCOPE-LOCK`

## 1. Decision Status

All next-window options in this document are `proposed`.

No option is confirmed by P12-W0. Controller/user confirmation is required before any Phase 12 implementation window starts.

## 2. Option A Eval-contract-first

Proposed next window:

- Create Phase 12 suite manifest.
- Create dataset skeleton for required case coverage.
- Create grader contract.
- Create report schema.
- Do not run CI.
- Do not generate a release report.
- Do not claim release evidence completion.

Pros:

- Safest first implementation step.
- Avoids fake release claims.
- Makes evidence shape explicit before runner / CI work.

Cons:

- No executable gate yet.
- CI artifact and replay proof remain open.

Required stop conditions:

- Stop if the window needs provider, prompt, API, DB, frontend, domain policy, eval report rewrite, script or workflow changes without explicit authorization.
- Stop if wording would mark `L5-006` implemented, validated or done before executable evidence exists.

## 3. Option B Replay-gate-first

Proposed next window:

- Implement replay fixtures for the P11 candidate product slice.
- Prove read-only replay.
- Prove formal-write-blocked replay.
- Prove zero provider, repository, DB and formal-write side effects.
- Compare candidate, validation, handoff and trace refs.

Pros:

- Directly tests multi-agent reproducibility.
- Closes replay evidence gap first.
- Strengthens candidate/formal boundary evidence before release wording.

Cons:

- Broader eval coverage remains incomplete.
- CI artifact and grader breadth may still be open.

Required stop conditions:

- Stop if replay needs runtime behavior changes outside the confirmed window.
- Stop if replay-only evidence is represented as real-provider quality or release readiness.

## 4. Option C CI-artifact-first

Proposed next window:

- Wire a Phase 12 CI gate with deterministic placeholder or existing focused commands.
- Define artifact upload policy.
- Define negative-control behavior.
- Keep default gate free of live provider credentials.
- Do not claim substantive release quality without eval/replay coverage.

Pros:

- Establishes release evidence logistics early.
- Prevents local-only quality claims.
- Gives a visible artifact path before release decision work.

Cons:

- Risk of CI plumbing before substantive eval coverage.
- A workflow file or local run could be misread as remote CI success if artifact evidence is absent.

Required stop conditions:

- Stop if remote CI success is claimed without visible passing run and artifact.
- Stop if workflow changes exceed the confirmed CI-only scope.

## 5. Option D Full Phase 12 eval gate slice

Proposed next window:

- Implement minimal multi-agent dataset.
- Implement deterministic grader coverage.
- Integrate runner behavior.
- Produce replay report.
- Produce CI artifact.
- Keep real-provider advisory mode out of the default gate.

Pros:

- Fastest path to an executable gate.
- Can close several evidence gaps in one controlled window if tightly scoped.

Cons:

- Highest scope risk.
- Easy to overclaim release, real-provider quality or CI success.
- Requires strict single-writer scope and final audit.

Required stop conditions:

- Stop if the window expands into provider, prompt, API, DB, frontend, domain policy or formal write behavior.
- Stop if a report rewrite is needed but not explicitly authorized.
- Stop if any `L5-*` capability would be marked done.

## 6. Recommendation

Recommended proposed option: Option A, Eval-contract-first.

Reason:

- It has the smallest blast radius.
- It makes Phase 12 evidence semantics executable-ready without touching CI/workflow or runtime behavior first.
- It reduces the risk that replay/fake/unit-test evidence is converted into a release claim.

This recommendation is not a Controller decision.

## 7. Required Controller Confirmation

Before the next Phase 12 window starts, Controller/user must confirm:

- selected option.
- allowed files.
- forbidden files.
- implementation vs docs-only boundary.
- validation commands.
- whether optional real-provider advisory evidence is out of scope, advisory-only or separately authorized.
- final status vocabulary.


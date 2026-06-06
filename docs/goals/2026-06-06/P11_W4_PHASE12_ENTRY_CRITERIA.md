---
title: P11_W4_PHASE12_ENTRY_CRITERIA
type: entry-criteria
status: phase12_entry_criteria_defined
permalink: ai-for-interviewer/docs/goals/2026-06-06/p11-w4-phase12-entry-criteria
---

# P11-W4 Phase 12 Entry Criteria

Window ID: `P11-W4-PHASE11-CLOSEOUT-SOURCE-SANITY`

## 1. Phase 12 Goal

Phase 12 is the L5 Eval, Hardening, and Release Gate phase.

Its goal is to decide whether the controlled multi-agent foundation and candidate-only product slice can move toward release evidence. It must not start by assuming release, provider quality or formal write completion.

## 2. Required Preconditions

Phase 12 may start only if all of these are true:

1. P11-W4 closeout is accepted.
2. P11-W3 post-push audit remains accepted as `post_push_audit_passed`.
3. `L5-004` remains candidate product slice only, not release.
4. `L5-005` remains runtime-hardening slice only, not full runtime closure.
5. `L5-006` remains `not_started` before Phase 12 work begins.
6. No L5 capability is marked `done`.
7. Deferred gaps are explicitly carried: Phase 12 release gate, remote CI artifact, real-provider quality certification, formal write, L5 release, eval / replay / release evidence.
8. The next Phase 12 scope lock lists allowed files, forbidden files, validation commands and stop conditions before any implementation.

## 3. Allowed Scope

Phase 12 may scope work for:

- multi-agent eval datasets.
- multi-agent graders.
- cross-agent replay fixtures.
- failure-mode regression cases.
- CI gate and artifact publication.
- trace / observability report.
- failure triage policy.
- rollback policy.
- human/controller release decision record.
- source backfill that records evidence without upgrading unsupported claims.

## 4. Forbidden Scope

Phase 12 must not:

- claim L5 release before release evidence exists.
- claim real-provider quality certification from fake-only, replay-only or unit-test-only evidence.
- claim remote CI success without visible passing run and artifact evidence.
- claim formal write completion without Application Service -> Domain Policy -> Handoff implementation and validation.
- bypass candidate-only and formal-write handoff boundaries.
- rewrite eval reports outside an explicitly authorized eval/report refresh window.
- change provider, prompt, API, DB, frontend or domain policy behavior unless separately authorized.
- mark `L5-006` implemented, validated or done before eval/replay/release gate evidence exists.
- mark any L5 capability `done` without satisfying the Matrix done gate.

## 5. Required Eval / Replay / CI Evidence

Phase 12 release-gate evidence must include:

- multi-agent eval suite IDs.
- dataset refs and grader refs.
- replay fixture refs.
- failure-mode case list.
- expected pass criteria and blocking failure policy.
- local eval command output.
- remote CI run URL or equivalent visible artifact evidence.
- artifact name, artifact location and commit SHA.
- explicit handling of skipped, deferred and non-blocking cases.
- negative-control or failure-injection evidence showing the gate can fail.

Replay/fake evidence may support regression confidence, but it cannot by itself certify real-provider quality.

## 6. Required Release Evidence

A release claim requires:

- completed eval/replay/CI gate evidence.
- trace / observability report.
- rollback policy.
- failure triage policy.
- known limitations list.
- unresolved gap disposition.
- human/controller release decision.
- source backfill that links evidence to Matrix, acceptance gates, decision log and risk register.

## 7. Required Non-Claims

Every Phase 12 window must repeat these non-claims until separately proven:

- P11-W4 did not claim L5 release.
- P11-W4 did not claim Phase 12 release gate completion.
- P11-W4 did not claim real-provider quality certification.
- P11-W4 did not claim remote CI success.
- P11-W4 did not claim formal write completion.
- P11-W4 did not mark `L5-006` implemented, validated or done.
- Candidate outputs remain candidate / suggestion / validation / plan / trace unless formal handoff is separately implemented and validated.

## 8. Stop Conditions

Stop and return to Controller if Phase 12 requires any of the following without explicit authorization:

- provider, prompt, API, DB, frontend or domain policy behavior changes.
- eval report rewrite outside scope.
- script or workflow changes outside scope.
- L5 release claim before remote artifact and release evidence.
- real-provider quality certification without real-provider evidence and human review.
- formal write completion claim without formal handoff implementation and validation.
- closing remote CI gap without visible passing CI evidence.
- marking `L5-006` or any L5 capability `done` without satisfying done gates.

## 9. Recommended First Phase 12 Window Options

| Option | Goal | Notes |
| --- | --- | --- |
| P12-W0 release-gate scope lock | Lock eval/replay/CI/release scope and file boundaries. | Safest first window. No implementation claim. |
| P12-W1 multi-agent eval design | Add or refine datasets, graders and suite contract. | Must preserve fake/replay non-claims. |
| P12-W2 replay and trace evidence | Build replay fixtures and trace / observability report. | Must keep candidate/formal boundaries explicit. |
| P12-W3 CI artifact gate | Produce visible remote CI artifact evidence. | Required before remote CI gap can close. |
| P12-W4 release decision closeout | Summarize release evidence and unresolved gaps for controller decision. | Only this can consider L5 release wording, and only with evidence. |

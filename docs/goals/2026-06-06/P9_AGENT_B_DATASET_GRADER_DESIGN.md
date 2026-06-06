---
title: P9_AGENT_B_DATASET_GRADER_DESIGN
type: goal-evidence
status: recon_only
permalink: ai-for-interviewer/docs/goals/2026-06-06/p9-agent-b-dataset-grader-design
---

# P9 Agent B — Dataset and Grader Design

## Scope Lock

- Role: read-only dataset / grader design.
- Agent id: `019e9c37-1b9d-7602-9b4d-c6bb51d4bcd5`.
- Output source: sub-agent final response, controller audited before single-writer patch.
- Forbidden: production prompt/provider/runtime/API/DB/domain changes, real-provider requirements, L5 release claim.

## Recommended Coverage

| Suite | Capability IDs | Required coverage |
|---|---|---|
| Canonical evidence | `CTX-001`, `CTX-002`, `CTX-003` | direct evidence, adjacent hypothetical, job-gap no fact claim, insufficient context deferred |
| Question Agent | `QAG-004`, `QAG-006`, `QAG-007` | grounding block, follow-up anti-repetition, fallback not success, `question_candidate` refs |
| Feedback Agent | `FAG-006`, `FAG-007`, `FAG-008` | asset conflict blocks next question, asset candidate confirmation, answer coverage, answer change, provider unavailable / validation failed not success |
| Provider boundary | `PRO-001`, `PRO-002` | forbidden data scanner, no full prompt asset fallback, fail-closed refs |
| Fake gate | `FAKE-001` | fake/replay visible, not real-provider quality, runtime fake remains rejected |
| Handoff / trace | `AGT-006`, `AGT-007` | candidate refs, validation refs, handoff refs, no formal refs/raw payload |
| Runtime non-claim | `RTE-*`, `L5-001` | existing-surface regression only; future runtime gaps deferred |

## Grader Strategy

- Prefer structured assertions over exact text.
- Keep recursive forbidden-data scanning.
- Add normalized forbidden key detection for hyphen/space variants.
- Add report scanner for JSON and Markdown output.
- Distinguish `blocking` failures from explicit `deferred_with_reason` cases.
- Add negative-control proof: a job-gap fixture that falsely claims completed work must fail and make the gate non-zero.

## Agent B Conclusion

The single writer should implement a suite manifest, deterministic Phase 9 datasets, extended code-rule graders, a unified gate runner, and report scanners under eval-only paths. Any required production behavior change must be recorded as a gap instead of patched.

---
title: 11_AGENT_B_DATASET_GRADER_DESIGN
type: note
permalink: ai-for-interviewer/docs/goals/2026-06-06/11-agent-b-dataset-grader-design-1
---

# Agent B — Dataset and Grader Design

Role: read-only design agent.

Goal: design Phase 9 regression dataset and grader coverage without changing code.

Inputs:

- Phase 9 master goal.
- Current Agent Definition / Skill / Tool contracts.
- Current Question and Feedback planned workflow files.
- Current provider/fake boundary tests.
- Current canonical evidence/source support policies and tests.

Design minimum suites:

1. `phase9_canonical_evidence_eval`
2. `phase9_question_agent_eval`
3. `phase9_feedback_agent_eval`
4. `phase9_provider_boundary_eval`
5. `phase9_fake_runtime_eval`
6. `phase9_handoff_trace_eval`
7. `phase9_runtime_foundation_contract_eval` only for existing Phase 8 surface; do not require missing runtime features.

For each suite, specify:

- capability_ids
- dataset cases
- fixture mode: replay / deterministic / fake-visible / optional-real-provider
- grader type: schema / reason-code / forbidden-key / invariant / report-metadata / negative-control
- blocking criteria
- deferred criteria
- risks

Output file: `docs/goals/2026-06-06/P9_AGENT_B_DATASET_GRADER_DESIGN.md`

Rules:

- Do not patch.
- Do not design evals that require prompt/provider/runtime behavior changes.
- Do not use fake-only results as real-provider quality.
- Include one negative-control design proving gate failure.
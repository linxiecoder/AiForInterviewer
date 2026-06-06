---
title: README
type: note
permalink: ai-for-interviewer/docs/goals/2026-06-06/readme
---

# Phase 9 Goal Pack — Eval / CI / Regression Gate

Workspace: AiForInterviewer
Recommended target path in repo: `docs/goals/2026-06-06/`

Use this pack as a controlled Codex CLI goal package. The package is designed for parallel read-only recon/design agents followed by exactly one writer agent. Phase 9 must build eval datasets, graders, runners, reports, regression gate, and CI integration. It must not silently complete Phase 8 runtime gaps or claim L5 release.

Suggested execution flow:

1. Copy this folder into `docs/goals/2026-06-06/`.
2. Start Codex CLI with the short objective in `00_CODEX_CLI_SHORT_OBJECTIVE.txt`.
3. Run parallel read-only agents from `10_AGENT_A_EVAL_BASELINE_RECON.md` through `14_AGENT_E_PHASE8_GAP_GUARD.md`.
4. Let the controller merge the reports and execute `20_SINGLE_WRITER_IMPLEMENTATION_GOAL.md`.
5. Run `30_FINAL_AUDIT_PROMPT.md` before committing/pushing.

Primary Phase 9 capability IDs:

- EVAL-001 AI Eval gate
- FAKE-001 Fake cleanup verification in eval/replay only
- PRO-002 Provider boundary regression verification
- QAG-004 / QAG-006 / QAG-007 Question Agent workflow eval coverage
- FAG-006 / FAG-007 / FAG-008 Feedback Agent workflow eval coverage
- AGT-006 / AGT-007 Handoff and trace eval coverage
- WIN-001 Execution-window traceability

Non-claims:

- Phase 9 is L5 Foundation only.
- Phase 9 does not close L5.
- Phase 9 does not implement Phase 11/12 Supervisor / Orchestrator or L5 multi-agent release gate.
- Phase 9 does not silently fix Phase 8 runtime gaps.
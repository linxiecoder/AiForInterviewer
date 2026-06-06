---
title: 10_AGENT_A_EVAL_BASELINE_RECON
type: note
permalink: ai-for-interviewer/docs/goals/2026-06-06/10-agent-a-eval-baseline-recon
---

# Agent A — Eval Baseline Recon

Role: read-only recon agent.

Goal: determine the current eval, test, runner, fixture, and report baseline before any patch.

Must inspect if present:

- `tests/evals/`, `evals/`, `scripts/evals/`, `scripts/qa/`
- `tests/architecture/`
- `tests/api/test_fake_llm_boundary.py`, `tests/api/test_llm_runtime.py`
- `.github/workflows/`, `pyproject.toml`, `pytest.ini`, `Makefile`, `package.json`
- `docs/goals/`, `docs/project-sources/`

Output file: `docs/goals/2026-06-06/P9_AGENT_A_EVAL_BASELINE_RECON.md`

Required report sections:

1. Current Eval Assets
2. Current Runner / Script Assets
3. Current CI Integration
4. Current Test Gates Relevant to Phase 9
5. Missing Pieces for Phase 9 Done Criteria
6. Recommended Minimal Allowed Files
7. Risks and Stop Conditions

Rules:

- Do not patch.
- Do not infer that eval exists unless files/tests prove it.
- Mark facts with source: GITHUB_CODE, TEST_RESULT, PROJECT_SOURCE, INFERENCE, UNKNOWN.
- If no eval assets exist, say so directly.
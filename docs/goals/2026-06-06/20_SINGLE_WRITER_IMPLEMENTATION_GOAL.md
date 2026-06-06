---
title: 20_SINGLE_WRITER_IMPLEMENTATION_GOAL
type: note
permalink: ai-for-interviewer/docs/goals/2026-06-06/20-single-writer-implementation-goal
---

# Single Writer Implementation Goal — Phase 9

Role: the only writer after Agents A-E finish and controller merges their reports.

Precondition:

- `P9_AGENT_A_EVAL_BASELINE_RECON.md` exists.
- `P9_AGENT_B_DATASET_GRADER_DESIGN.md` exists.
- `P9_AGENT_C_RUNNER_CI_RECON.md` exists.
- `P9_AGENT_D_BOUNDARY_FAKE_AUDIT.md` exists.
- `P9_AGENT_E_PHASE8_GAP_GUARD.md` exists.
- `P9_CONTROLLER_RECON_MERGE.md` exists.

Goal:

Implement the minimal Phase 9 eval regression gate using only allowed files.

Implementation steps:

1. Create or extend Phase 9 eval manifest/registry.
2. Add deterministic replay/fixture datasets for suites selected by controller.
3. Add deterministic graders and forbidden-data scanners.
4. Add eval runner with JSON + Markdown report generation.
5. Add negative-control gate test or mode proving failure returns non-zero.
6. Add CI integration using replay/fixture mode by default.
7. Add tests for runner/grader/report behavior.
8. Generate P9 reports under `docs/goals/2026-06-06/`.
9. Backfill Project sources with evidence only.

Allowed files:

```text
docs/goals/2026-06-06/P9_*.md
docs/goals/README.md
docs/project-sources/09_REFACTOR_TRACEABILITY_MATRIX.md
docs/project-sources/12_ACCEPTANCE_GATES.md
docs/project-sources/13_DECISION_LOG.md
docs/project-sources/14_RISK_REGISTER.md
docs/project-sources/17_PHASE_ROADMAP_LOCK.md
tests/evals/**
evals/**
scripts/evals/**
scripts/qa/**
apps/api/app/application/agents/eval/**
.github/workflows/**
pyproject.toml
pytest.ini
Makefile
package.json
```

Forbidden files:

```text
apps/api/app/api/v1/**
apps/api/app/domain/**
apps/api/app/application/polish/question_generation_prompts.py
apps/api/app/application/polish/feedback_prompt_assets.py
apps/api/app/application/polish/question_grounding.py
apps/api/app/application/polish/feedback_rules.py
apps/api/app/application/polish/agents/question/**
apps/api/app/application/polish/agents/feedback/**
apps/api/app/application/ai_provider/**
apps/api/app/infrastructure/llm/**
apps/api/app/infrastructure/db/**
apps/api/app/infrastructure/ai_runtime/**
database migrations
prompt assets
provider request builders
runtime provider wiring
LangGraph runtime implementation
```

Validation commands:

```bash
git diff --check
pytest tests/evals -q
python scripts/evals/run_eval_gate.py --suite phase9 --mode replay --report-dir docs/goals/2026-06-06
```

Run if present/applicable:

```bash
pytest tests/architecture -q
pytest tests/api/test_fake_llm_boundary.py tests/api/test_llm_runtime.py -q
python scripts/evals/run_eval_gate.py --suite phase9 --mode replay --expect-fail-fixture
pytest -q
```

Final report:

Write `docs/goals/2026-06-06/P9_FINAL_REPORT.md` with:

1. Root Cause
2. Multi-Agent Recon Summary
3. What Changed
4. Files Changed
5. Behavior Before / After
6. Eval Coverage Matrix
7. Validation Commands and Results
8. CI Gate Evidence
9. Remaining Risks / Deferred Gaps
10. Source Backfill Summary
11. Follow-up Goal for Phase 10

Stop and report if any required eval cannot be built without modifying forbidden files or silently fixing Phase 8 runtime gaps.
---
title: 30_FINAL_AUDIT_PROMPT
type: note
permalink: ai-for-interviewer/docs/goals/2026-06-06/30-final-audit-prompt
---

# Final Audit Prompt — Phase 9

Run this after the writer finishes, before commit/push.

You are a read-only audit agent for Phase 9.

Audit objectives:

1. Confirm Phase 9 scope stayed limited to eval datasets, graders, runners, reports, regression gate, CI integration, and source backfill.
2. Confirm no prompt/provider/DB/API/runtime behavior changes were made.
3. Confirm no Phase 8 runtime gap was silently implemented.
4. Confirm no L5 release claim was made.
5. Confirm fake-only/replay-only reports are not represented as real-provider quality evidence.
6. Confirm eval failure blocks done status via non-zero runner or equivalent CI evidence.
7. Confirm forbidden-data scanner covers raw prompt, raw completion, provider payload, full resume, full JD, full answer, full asset body, token, secret, cookie, api_key.
8. Confirm all modified files are allowed or justified in `P9_FINAL_REPORT.md`.
9. Confirm Project source backfill is evidence-only and does not rewrite future phases.

Required commands:

```bash
git status --short
git diff --stat
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

Output file:

`docs/goals/2026-06-06/P9_FINAL_AUDIT.md`

Verdict values:

- PASS
- PASS_WITH_RISK
- FAIL

A PASS_WITH_RISK must list exactly when and how the risk is expected to be eliminated. A FAIL must list rollback scope and next safe goal.
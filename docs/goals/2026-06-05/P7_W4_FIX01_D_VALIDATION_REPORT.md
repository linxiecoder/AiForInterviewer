---
title: P7_W4_FIX01_D_VALIDATION_REPORT
type: goal-evidence
status: evidence-only
permalink: ai-for-interviewer/docs/goals/2026-06-05/p7-w4-fix01-d-validation-report
---

# P7-W4.fix.01 D Validation Report

Window ID: `P7-W4.fix.01-FULL-VALIDATION-BLOCKER-REMEDIATION`

Agent: Full Validation Agent

Mode: `VALIDATION_ONLY`

## 结论

本轮 required validation 已通过：

- full-repo pytest: `1067 passed`
- `npm run web:test`: passed
- `npm run web:smoke:auth`: passed
- focused temp policy / fake rejection tests: `21 passed`
- auth smoke script 不再设置 `LLM_PROVIDER=fake`
- runtime fake rejection tests 仍通过

## Commands and Results

### git status

```bash
git status --short --untracked-files=all
```

Result:

```text
 M docs/00-governance/TEST_POLICY.md
 M scripts/qa/authenticated-frontend-smoke.mjs
 M tests/test_temp_artifact_policy.py
?? docs/goals/2026-06-05/P7_W4_FIX01_A_TEMP_POLICY_RECON.md
?? docs/goals/2026-06-05/P7_W4_FIX01_B_WEB_SMOKE_RECON.md
?? docs/goals/2026-06-05/P7_W4_FIX01_C_IMPLEMENTATION_REPORT.md
```

Validation 后补写本报告会新增 `P7_W4_FIX01_D_VALIDATION_REPORT.md`。

### git diff check

```bash
git diff --check
```

Result: `PASS`, no output.

### focused temp / fake policy tests

```bash
PYTHONPATH=.:apps/api PYTHONDONTWRITEBYTECODE=1 AI_FOR_INTERVIEWER_ALLOW_TEST_DIR_LEAKS=1 .venv/bin/python -m pytest -p no:cacheprovider tests/test_temp_artifact_policy.py tests/api/test_llm_runtime.py tests/api/test_fake_llm_boundary.py -q
```

Result:

```text
21 passed in 4.31s
```

### full-repo pytest

```bash
PYTHONPATH=.:apps/api PYTHONDONTWRITEBYTECODE=1 AI_FOR_INTERVIEWER_ALLOW_TEST_DIR_LEAKS=1 .venv/bin/python -m pytest -p no:cacheprovider apps/api tests -q
```

Result:

```text
1067 passed in 86.00s (0:01:26)
```

### web:test

```bash
npm run web:test
```

Result: `PASS`.

Observed output:

```text
> web:test
> npm --workspace apps/web run test

> @ai-for-interviewer/web@0.1.0 test
> tsc -p tsconfig.json --noEmit
```

### web:smoke:auth

```bash
npm run web:smoke:auth
```

Result: `PASS`.

Observed output:

```text
[auth-smoke] api health ok
[auth-smoke] /interview html ok
[auth-smoke] main tsx served ok
[auth-smoke] proxied health ok
[auth-smoke] /interview/:sessionId html ok
[auth-smoke] OK session=ses_auth_frontend_smoke api=http://127.0.0.1:18082 web=http://127.0.0.1:15173
```

### grep: auth smoke fake env

Required path note: the repository has no top-level `web/` directory; the web workspace is `apps/web`. The raw path list including `web` is therefore not applicable for this checkout and would fail only because the path is absent. Validation used the existing repository paths below.

```bash
rg -n "LLM_PROVIDER: \"fake\"|LLM_PROVIDER=fake|LLM_PROVIDER.*fake" package.json apps scripts tests
```

Result: `PASS` for auth smoke criterion.

Allowed hits:

- `apps/api/app/infrastructure/llm/runtime.py`: runtime fake rejection error text.
- `tests/api/test_llm_runtime.py`: negative tests for `LLM_PROVIDER=fake`.
- `tests/api/test_fake_llm_boundary.py`: static scanner and negative fake env tests.
- `tests/fakes/llm_transport.py`: test fake facade documentation.
- `tests/evals/test_ai_eval_runners.py`: eval runner isolation test.

No hit remains in `scripts/qa/authenticated-frontend-smoke.mjs`.

## Temp Artifact Policy Evidence

`tests/test_temp_artifact_policy.py` now covers:

- pytest-managed fixture names allowed when managed outside repo root.
- repo-root `tmp*` path construction still rejected even in a test that also uses `tmp_path`.
- direct low-level `tempfile.*`, `shutil.rmtree()`, direct `Path("tmp*")`, and `mkdir("tmp*")` patterns remain rejected.

## Fake Provider Non-Regression Evidence

`tests/api/test_llm_runtime.py` and `tests/api/test_fake_llm_boundary.py` still pass. `apps/api/app/infrastructure/llm/runtime.py` remains unchanged and still rejects `provider == "fake"`.

## Validation Verdict

`PASS`

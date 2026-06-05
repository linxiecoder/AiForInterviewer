---
title: P7_W4_FIX01_C_IMPLEMENTATION_REPORT
type: goal-evidence
status: evidence-only
permalink: ai-for-interviewer/docs/goals/2026-06-05/p7-w4-fix01-c-implementation-report
---

# P7-W4.fix.01 C Implementation Report

Window ID: `P7-W4.fix.01-FULL-VALIDATION-BLOCKER-REMEDIATION`

Agent: Single Writer Implementation Agent

Mode: `ONLY_WRITER`

## 结论

已完成两个 W4 validation blocker 的最小修复：

- Temp artifact policy checker 允许 pytest-managed temp fixtures，但继续拒绝 repo-root scratch artifact、低层 `tempfile.*` API 和手写清理。
- Auth smoke 不再设置 `LLM_PROVIDER=fake`，而是显式覆盖为空字符串，避免外部 fake env 污染。

未修改 runtime fake rejection、provider fail-closed policy、API route、DB、frontend feature、domain policy、Phase 8 runtime 或 Phase 9 eval / CI gate。

## 变更文件

| 文件 | 变更 |
|---|---|
| `tests/test_temp_artifact_policy.py` | 移除 pytest fixture 名称一刀切禁止；新增允许 pytest-managed fixture 与继续拒绝 repo-root tmp 的 focused tests |
| `docs/00-governance/TEST_POLICY.md` | 同步 Controller Decision B：允许 pytest 受管临时夹具在 repo-root 外使用；保留 repo-root scratch artifact 禁止 |
| `scripts/qa/authenticated-frontend-smoke.mjs` | 将 auth smoke env 中 `LLM_PROVIDER: "fake"` 改为 `LLM_PROVIDER: ""` |
| `docs/goals/2026-06-05/P7_W4_FIX01_A_TEMP_POLICY_RECON.md` | 写入 temp policy recon evidence |
| `docs/goals/2026-06-05/P7_W4_FIX01_B_WEB_SMOKE_RECON.md` | 写入 web smoke auth recon evidence |
| `docs/goals/2026-06-05/P7_W4_FIX01_C_IMPLEMENTATION_REPORT.md` | 写入 implementation evidence |

## Temp Artifact Policy Remediation

实现点：

- 删除 `PROHIBITED_PATTERNS` 中匹配 `tmp_path|tmp_path_factory|pytester|runpytest` 的规则。
- 新增 `test_policy_allows_pytest_managed_temp_fixtures_outside_repo_root`，证明 pytest-managed fixture 名称不再被 checker 误拒。
- 新增 `test_policy_still_rejects_repo_root_tmp_dir_with_pytest_fixture`，证明同一测试即使使用 pytest fixture，只要拼接 repo-root `tmp*` 目录仍会失败。
- 保留 `Path(__file__) / "tmp*"`、`Path("tmp*")`、`mkdir("tmp*")`、`tempfile.*`、`shutil.rmtree()` 的禁止规则。

## Web Smoke Auth Remediation

实现点：

- `scripts/qa/authenticated-frontend-smoke.mjs` 中 `smokeEnv()` 显式设置 `LLM_PROVIDER: ""`。
- 该改法覆盖外部 `LLM_PROVIDER=fake`，但不允许 runtime fake provider。
- 当前 auth smoke 只走认证态 API 和页面加载路径，不触发 LLM generate。

## Focused 验证

```bash
PYTHONPATH=.:apps/api PYTHONDONTWRITEBYTECODE=1 AI_FOR_INTERVIEWER_ALLOW_TEST_DIR_LEAKS=1 .venv/bin/python -m pytest -p no:cacheprovider tests/test_temp_artifact_policy.py -q
```

结果：`10 passed`。

```bash
PYTHONPATH=.:apps/api PYTHONDONTWRITEBYTECODE=1 AI_FOR_INTERVIEWER_ALLOW_TEST_DIR_LEAKS=1 .venv/bin/python -m pytest -p no:cacheprovider tests/api/test_llm_runtime.py tests/api/test_fake_llm_boundary.py -q
```

结果：`11 passed`。

```bash
rg "LLM_PROVIDER=fake|LLM_PROVIDER.*fake|fake" package.json apps scripts tests -n
```

结果：auth smoke script 不再命中 `LLM_PROVIDER.*fake`；剩余命中为 runtime rejection、fake facade、fake runtime 命名、negative tests 或 fake fixture 相关内容。

## Non-Changes

- 未修改 `apps/api/app/infrastructure/llm/runtime.py`。
- 未允许 `LLM_PROVIDER=fake`。
- 未修改 API route、DB、frontend feature、domain policy。
- 未启动 Phase 8 或 Phase 9。

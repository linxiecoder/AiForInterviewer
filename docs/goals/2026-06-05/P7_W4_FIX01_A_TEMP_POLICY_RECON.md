---
title: P7_W4_FIX01_A_TEMP_POLICY_RECON
type: goal-evidence
status: evidence-only
permalink: ai-for-interviewer/docs/goals/2026-06-05/p7-w4-fix01-a-temp-policy-recon
---

# P7-W4.fix.01 A Temp Policy Recon

Window ID: `P7-W4.fix.01-FULL-VALIDATION-BLOCKER-REMEDIATION`

Agent: Temp Artifact Policy Recon Agent

Mode: `READ_ONLY`

## 结论

P7-W4 full-repo pytest blocker 来自 `tests/test_temp_artifact_policy.py::TestTempArtifactPolicyTests::test_tests_do_not_reintroduce_forbidden_temp_dir_patterns` 的静态 regex 规则。旧规则把 `tmp_path`、`tmp_path_factory`、`pytester` 和 `runpytest` 标识符一律视为违规，因此扫描到 4 个测试文件中的 pytest-managed temp fixture 用法后失败。

该失败不是 repo-root scratch artifact 泄漏，也不是 Phase 7 provider / fake fail-closed 策略问题。Controller Decision B 已确认：允许 pytest-managed temp fixtures 在 repo-root 外由 pytest 管理和清理；继续禁止 repo-root scratch artifacts、泄漏 tmp 目录和 untracked execution artifacts。

## 读取范围

- `AGENTS.md`
- `docs/00-governance/DOCS_INDEX.md`
- `docs/00-governance/TEST_POLICY.md`
- `docs/goals/2026-06-05/P7_W4_FINAL_REPORT.md`
- `docs/project-sources/20_PHASE7_CLOSEOUT.md`
- `pytest.ini`
- `tests/conftest.py`
- `tests/api/conftest.py`
- `tests/test_temp_artifact_policy.py`
- `tools/testing/temp_artifacts.py`
- `tests/api/test_logging_util.py`
- `tests/api/test_openai_compatible_raw_debug.py`
- `tests/api/test_polish_feedback_runtime.py`
- `tests/evals/test_ai_eval_runners.py`

## 定位文件

| 文件 | 作用 | 证据 |
|---|---|---|
| `tests/test_temp_artifact_policy.py` | temp artifact policy checker | 旧 `PROHIBITED_PATTERNS` 包含 pytest fixture 名称 regex，导致 W4 25 个命中 |
| `tests/conftest.py` | pytest session temp leak guard | session start/finish 检查 repo root 和 `tests/` 下 temp-like 目录 |
| `tools/testing/temp_artifacts.py` | 受管临时目录与 repo-root 残留扫描 | `find_repo_temp_dir_residuals()` 扫描 repo root 和 `tests/` 下 `_tmp/tmp/temp*` |
| `docs/00-governance/TEST_POLICY.md` | active 测试临时产物治理说明 | 旧文案仍禁止 pytest temp fixtures，需要按 Controller Decision B 同步边界 |

## 失败根因

W4 报告记录 full-repo pytest：

- `1 failed, 1065 passed`
- failed test: `tests/test_temp_artifact_policy.py::TestTempArtifactPolicyTests::test_tests_do_not_reintroduce_forbidden_temp_dir_patterns`
- 25 个命中来自 `tmp_path` / pytester-style fixture 名称

本轮复现 focused test：

```bash
PYTHONPATH=.:apps/api PYTHONDONTWRITEBYTECODE=1 AI_FOR_INTERVIEWER_ALLOW_TEST_DIR_LEAKS=1 .venv/bin/python -m pytest -p no:cacheprovider tests/test_temp_artifact_policy.py -q
```

结果：`1 failed, 8 passed`。失败列表与 W4 报告一致，命中 4 个测试文件中的 pytest-managed fixture 名称。

## 受影响测试

| 文件 | 命中性质 |
|---|---|
| `tests/api/test_logging_util.py` | `tmp_path` 用于日志路径 |
| `tests/api/test_openai_compatible_raw_debug.py` | `tmp_path` 用于 raw dump 路径和 `monkeypatch.chdir()` |
| `tests/api/test_polish_feedback_runtime.py` | `tmp_path` 用于 SQLite 文件 |
| `tests/evals/test_ai_eval_runners.py` | `tmp_path` 用于 eval report / dataset 文件 |

## 允许 / 禁止边界

允许：

- pytest 在 repo-root 外创建并清理的 `tmp_path`、`tmp_path_factory`、`pytester`、`runpytest` 类受管临时 fixture。
- `ManagedTempArtifacts` / `ManagedTempArtifactsTestCase` 继续用于项目自建临时目录。

禁止：

- 在 repo root 或 `tests/` 下直接创建 `_tmp`、`tmp`、`temp` 或其变体目录。
- 使用低层 `tempfile.*` API 绕过受管临时目录策略。
- 手写 `shutil.rmtree()` 清理测试目录。
- 通过扩大 allowlist 隐藏 repo-root scratch artifact 泄漏。

## 建议的最小改法

- 从 `tests/test_temp_artifact_policy.py` 的禁止 regex 中移除 pytest fixture 名称一刀切规则。
- 增加 focused tests：证明 pytest-managed fixture 名称不再违规；同时证明含 pytest fixture 的测试如果仍拼接 repo-root `tmp*` 目录仍会被拒绝。
- 同步 `docs/00-governance/TEST_POLICY.md` 中的测试临时产物边界说明，避免 active policy doc 与 checker 冲突。

## 风险

- 若仅删除 fixture 禁止规则而不保留 repo-root scratch artifact tests，会弱化 temp leak governance。
- 若迁移 4 个业务测试而不改 checker，会违背本轮 Controller Decision B 的明确方向。
- 本 recon 报告是 evidence-only，不替代 active docs 或代码事实。

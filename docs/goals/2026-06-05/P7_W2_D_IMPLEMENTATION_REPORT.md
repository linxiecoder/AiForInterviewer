---
title: P7_W2_D_IMPLEMENTATION_REPORT
type: goal-evidence
status: evidence-only
permalink: ai-for-interviewer/docs/goals/2026-06-05/p7-w2-d-implementation-report
---

# P7-W2-D Implementation Report

模式：单写者实施

## Scope Lock

- Phase: `Phase 7 - Provider request fail-closed`
- 允许实施范围：provider boundary、DTO safety backstop、active provider caller 更新、provider boundary tests、static tests、source backfill docs。
- 已遵守禁止范围：未修改 API routes、DB migration、frontend、prompt、provider SDK transport、Phase 8 runtime、Phase 9 eval / CI gate。

## Red Evidence

| Command | Red Result |
|---|---|
| `pytest tests/architecture/test_provider_boundary_static.py -q` | 失败：`polish_feedback_graph.py`、`progress_tree.py`、`job_match.py` 存在生产直接构造 `LlmTransportRequest(...)`。 |
| `pytest tests/api/test_provider_global_backstop.py -q` | 失败：direct DTO / `replace(...)` forbidden-key bypass 未被拒绝；progress / job match 可到达 transport。 |

## What Changed

- `apps/api/app/application/llm/types.py`
  - 新增共享 `P7_PROVIDER_FORBIDDEN_KEYS`。
  - 新增 `LlmTransportRequestValidationError`。
  - 新增 `LlmTransportRequest.__post_init__` recursive forbidden-key backstop。
- `apps/api/app/application/llm/provider_boundary.py`
  - 复用 `types.py` 中的共享 forbidden-key catalog。
  - 允许 trace request 透传可选 `graph_name` / `node_name`。
- `apps/api/app/application/polish/progress_tree.py`
  - initial / refresh provider calls 改为使用 `build_validated_transport_request(...)`。
  - validation failure 返回 `provider_request_validation_failed` failed artifacts，且不调用 transport。
- `apps/api/app/infrastructure/llm/job_match.py`
  - job match provider call 改为使用 validated builder。
  - validation failure 在 transport 前抛出 `JobMatchAnalyzerUnavailableError("provider_request_validation_failed")`。
- `apps/api/app/application/ai_runtime/business_graphs/polish_feedback_graph.py`
  - default-off trace request 使用 validated builder，同时保留 PR8 refs / digests-only 行为。
- `tests/architecture/test_provider_boundary_static.py`
  - 新增 production static gate：只有 `provider_boundary.py` 可以调用 `LlmTransportRequest(...)`。
- `tests/api/test_provider_global_backstop.py`
  - 新增 DTO backstop、`replace(...)` 注入、progress tree、job match pre-transport 测试。

## Green Evidence

| Command | Result |
|---|---|
| `PYTHONPATH=.:apps/api ... pytest tests/architecture/test_provider_boundary_static.py tests/api/test_provider_global_backstop.py -q` | `7 passed` |
| `PYTHONPATH=.:apps/api ... pytest tests/api/test_pr8_polish_provider_trace_gate.py -q` | `10 passed` |
| `PYTHONPATH=.:apps/api ... pytest tests/api/test_job_match_api.py -q` | `11 passed` |
| `PYTHONPATH=.:apps/api ... pytest tests/api/test_provider_boundary.py -q` | `4 passed` |
| Required narrow suite + new global test | `144 passed` |
| New global test standalone | `4 passed` |

## Claim Ledger

| Claim | Status | Evidence |
|---|---|---|
| Active production provider callers 不再直接构造 `LlmTransportRequest(...)` | validated | `rg "LlmTransportRequest\\(" apps/api/app -n` 仅返回 `provider_boundary.py` |
| direct DTO forbidden-key bypass 被捕获 | validated | `test_provider_global_backstop.py` |
| `dataclasses.replace(...)` unsafe injection 被捕获 | validated | `test_provider_global_backstop.py` |
| job match unsafe request 在 transport 前失败 | validated | `test_provider_global_backstop.py`; `test_job_match_api.py` |
| progress tree unsafe request 在 transport 前失败 | validated | `test_provider_global_backstop.py` |
| answer excerpt 永不等于完整短回答 | not claimed | C report 分类为 deferred |
| full-repo / web / e2e 已通过 | not claimed | 未运行 |

## Final Implementation Status

`validated_with_deferred_gaps`

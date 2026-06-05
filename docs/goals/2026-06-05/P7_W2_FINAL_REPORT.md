---
title: P7_W2_FINAL_REPORT
type: goal-evidence
status: evidence-only
permalink: ai-for-interviewer/docs/goals/2026-06-05/p7-w2-final-report
---

# P7-W2 Final Report

Window ID: `P7-W2-PROVIDER-GLOBAL-BACKSTOP-AND-ANSWER-REDACTION-GAPS`

Phase: `Phase 7 - Provider request fail-closed`

Capability IDs: `PRO-001`, `PRO-002`, `FAKE-001`, `WIN-001`, `SRC-001`

Status: `validated_with_deferred_gaps`

本报告不得被解释为 Phase 7 `done`。

## 1. Root Cause

P7-W1 已验证 Q/F active provider fail-closed 行为，但当前 main 仍存在非 Q/F production provider call sites 直接构造 `LlmTransportRequest(...)`。`LlmTransportRequest` 自身未拒绝 forbidden keys，因此 direct bypass 或 `dataclasses.replace(...)` mutation 可能绕过 shared validator。Feedback answer excerpt policy 对短回答是否可完整发送仍未决。

## 2. P7-W1 Baseline

P7-W1 commit baseline: `48921f6cf2528729ececd0a1a27e7b736c576fcf`.

接受状态：`validated_with_deferred_gaps`，不是 `done`。

P7-W1 已验证：Q/F active paths、feedback full prompt fallback 被阻断、feedback direct fake non-success、forbidden-key catalog、source backfill。

## 3. Multi-Agent Execution Summary

| Agent | Output | Result |
|---|---|---|
| Provider Call-Site Recon | `P7_W2_A_PROVIDER_CALLSITE_RECON.md` | 发现 progress tree / job match active bypass |
| Global Backstop Design | `P7_W2_B_GLOBAL_BACKSTOP_DESIGN.md` | 选择 Option B |
| Answer Redaction Recon | `P7_W2_C_ANSWER_REDACTION_RECON.md` | answer excerpt 保留 deferred |
| Single Writer Implementation | `P7_W2_D_IMPLEMENTATION_REPORT.md` | 完成最小 provider boundary fix |
| Audit / Diff | `P7_W2_E_AUDIT_REPORT.md` | 允许 source backfill，不允许 done claim |
| Source Backfill | `P7_W2_F_SOURCE_BACKFILL_REPORT.md` | 更新 09 / 14 / 17 |

## 4. Provider Call-Site Inventory

当前 production direct `LlmTransportRequest(...)` constructors 仅限 `apps/api/app/application/llm/provider_boundary.py`。

`question_generation_service.py`、`feedback_agent.py`、`progress_tree.py`、`job_match.py`、`polish_feedback_graph.py` 现在都在 provider transport 前使用 `build_validated_transport_request(...)`。`polish_question_runtime.py` 仍是 `QuestionGenerationService` wrapper；DTO `replace(...)` unsafe injection 由 global backstop 覆盖。

## 5. Global Backstop Decision

选择：Option B，并增加一个 DTO-level safety addition。

- Builder 负责 per-task required / allowed top-level keys 和 redaction。
- DTO `__post_init__` 负责 direct construction 与 `replace(...)` 的 recursive forbidden-key rejection。
- Static architecture test 防止新增 production direct constructors。

这是 forbidden-key global backstop 加 builder / static schema gate，不是 universal runtime schema registry。

## 6. Answer Redaction / Excerpt Decision

Deferred。Feedback `current_answer.answer_text` 仍限制为 1200 chars，但短回答可能等于完整文本。本窗口不声明 leakage elimination，也未修改 prompt、scoring 或 persistence behavior。

## 7. What Changed

- P7 forbidden-key catalog 移入 `types.py` 作为共享 catalog。
- `LlmTransportRequest` 递归拒绝 forbidden keys。
- progress tree、job match、feedback trace request construction 改为使用 validated builder。
- Static gate 拒绝 provider boundary 之外的 production direct request constructors。
- 新增 global tests 覆盖 direct DTO bypass、`replace(...)`、progress tree、job match。

## 8. Files Changed

- `apps/api/app/application/llm/types.py`
- `apps/api/app/application/llm/provider_boundary.py`
- `apps/api/app/application/polish/progress_tree.py`
- `apps/api/app/infrastructure/llm/job_match.py`
- `apps/api/app/application/ai_runtime/business_graphs/polish_feedback_graph.py`
- `tests/architecture/test_provider_boundary_static.py`
- `tests/api/test_provider_global_backstop.py`
- `docs/goals/2026-06-05/P7_W2_*.md`
- `docs/project-sources/09_REFACTOR_TRACEABILITY_MATRIX.md`
- `docs/project-sources/14_RISK_REGISTER.md`
- `docs/project-sources/17_PHASE_ROADMAP_LOCK.md`

## 9. Behavior Before / After

| Area | Before | After |
|---|---|---|
| Production direct request constructors | progress tree、job match、feedback trace gate 绕过 builder | 仅 provider boundary 构造 DTO |
| Direct DTO forbidden keys | 未拒绝 | 由 `LlmTransportRequest.__post_init__` 拒绝 |
| `replace(...)` unsafe mutation | 未拒绝 | 已拒绝 |
| Progress tree unsafe provider prompt | 可到达 transport | transport 前返回 failed artifact |
| Job match unsafe provider payload | 可到达 transport | transport 前抛出 unavailable |
| Answer excerpt | bounded 但可能等于完整短回答 | 未改变；deferred |

## 10. Validation Commands and Results

| Command | Result |
|---|---|
| static + global provider tests | `7 passed` |
| PR8 trace gate | `10 passed` |
| job match | `11 passed` |
| provider boundary | `4 passed` |
| required narrow suite plus new global test | `144 passed` |
| new global test standalone | `4 passed` |
| `rg "LlmTransportRequest\\(" apps/api/app -n` | only `provider_boundary.py:77` |
| `rg "build_validated_transport_request\\(" apps/api/app -n` | Question / Feedback / progress tree / job match / feedback trace request / builder |
| recommended sensitive-key grep | expected denylist / test / auth-security hits; no new leakage claim |
| Markdown mojibake scan | no hits |
| `git diff --check` | clean |

## 11. Claim Ledger

| Claim | Status | Evidence |
|---|---|---|
| 当前所有 production `LlmTransportRequest(...)` callers 均通过 provider boundary | validated | code grep + static test |
| direct forbidden-key DTO bypass 被捕获 | validated | `test_provider_global_backstop.py` |
| active progress tree / job match unsafe requests 在 transport 前失败 | validated | `test_provider_global_backstop.py` |
| fake runtime false-success 未重新引入 | validated | required narrow suite |
| answer excerpt 永不等于完整短回答 | not claimed | deferred |
| full-repo / web / e2e 已通过 | not claimed | 未运行 |

## 12. Remaining Risks / Deferred Gaps

- `P7-GAP-003`: 短 `current_answer.answer_text` 仍可能作为 bounded excerpt 完整发送。
- `P7-GAP-005`: full-repo pytest、web tests、e2e tests 未运行。
- Phase 7 不是 `done`。

## 13. Source Backfill Result

已回填 `09_REFACTOR_TRACEABILITY_MATRIX.md`、`14_RISK_REGISTER.md`、`17_PHASE_ROADMAP_LOCK.md`。

未修改 `12_ACCEPTANCE_GATES.md` 和 `13_DECISION_LOG.md`，原因是现有 gates 覆盖本窗口，且未产生 durable ADR-level decision。

## 14. Final Status

`validated_with_deferred_gaps`

## 15. Follow-up Goal

决策 feedback providers 是否可以接收完整短 `current_answer` 作为 bounded excerpt。若不允许，应开启独立 P7 answer redaction policy window，定义 deterministic truncation / digest / omitted-length 行为，并评审 prompt 与 scoring 影响。

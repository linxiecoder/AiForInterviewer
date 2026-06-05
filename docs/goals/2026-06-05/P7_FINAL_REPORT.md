---
title: P7_FINAL_REPORT
type: note
permalink: ai-for-interviewer/docs/goals/2026-06-05/p7-final-report
---

# Phase 7 Final Report - Provider Request Fail-Closed

Window ID: `P7-W1-PROVIDER-FAIL-CLOSED-FAKE-CLEANUP`

Phase: `Phase 7 - Provider request fail-closed`

Capability IDs: `PRO-001`, `PRO-002`, `FAKE-001`, `WIN-001`, `SRC-001`

Author / Executor: `Codex Controller + Agent A/B/C/D/E/F`

Commit / HEAD: `be30e8b13ac863c18a1238005c3cf97a941f07d2`

Status: `validated_with_deferred_gaps`

本报告不得被解释为 Phase 7 `done`。

## 1. Root Cause

- [PROJECT_SOURCE + GITHUB_CODE] Question / Feedback provider path 缺少共享 compact provider boundary，存在将不合规 provider request 传入 transport 的风险。
- [GITHUB_CODE] Feedback `provider_prompt` 缺失时曾 fallback 到完整 `prompt_asset`。
- [GITHUB_CODE] Feedback direct service 使用 `FakeLlmTransport` 时曾返回 generated success，容易造成 runtime fake 污染或 false-success。
- [GITHUB_CODE] `ai_runtime.contracts` / `AgentOutputEnvelope` 的敏感字段 catalog 未覆盖 P7 forbidden-key 全集。

## 2. Multi-Agent Execution Summary

| Agent | Mode | Output Artifact | Result | Notes |
|---|---|---|---|---|
| Provider Boundary Recon Agent | read-only | `docs/goals/2026-06-05/P7_A_PROVIDER_BOUNDARY_RECON.md` | PASS | 识别 provider request / fallback / invocation gaps |
| Q/F Integration Recon Agent | read-only | `docs/goals/2026-06-05/P7_B_QF_INTEGRATION_RECON.md` | PASS | 识别 Q/F active path 与 false-success 风险 |
| Fake/Security Recon Agent | read-only | `docs/goals/2026-06-05/P7_C_FAKE_SECURITY_RECON.md` | PASS | 识别 fake runtime 与 trace/log safety 边界 |
| Single Writer Implementation Agent | write | `docs/goals/2026-06-05/P7_D_IMPLEMENTATION_REPORT.md` | PASS_WITH_GAPS | 仅写允许实现/测试文件，不声明 done |
| Audit/Diff Agent | read-only | `docs/goals/2026-06-05/P7_E_AUDIT_REPORT.md` | WARN | 允许 source backfill，但要求保留 deferred gaps |
| Source Backfill Agent | docs write | `docs/goals/2026-06-05/P7_F_SOURCE_BACKFILL_REPORT.md` | PASS_WITH_GAPS | 更新 09/14/17 与 F 报告，未改 12/13 |

## 3. Claim Ledger

| Claim | Status Claimed | Evidence | Evidence Label | Gate Impact | Verified? |
|---|---|---|---|---|---|
| P7 forbidden-key catalog exists | validated | `apps/api/app/application/llm/provider_boundary.py`; `tests/api/test_provider_boundary.py`; `tests/architecture/test_provider_boundary_static.py` | GITHUB_CODE + TEST_RESULT | Provider Gate | yes |
| Provider request schema gate and recursive reject exist | validated | `ProviderRequestValidator`; final aggregate pytest `146 passed` | GITHUB_CODE + TEST_RESULT | Provider Gate | yes |
| Question active path fails closed before transport | validated | `question_generation_service.py`; `test_polish_question_refactor_phase1.py` | GITHUB_CODE + TEST_RESULT | Provider Gate | yes |
| Feedback active path fails closed before transport | validated | `feedback_agent.py`; `test_polish_feedback_agent_io_alignment.py` | GITHUB_CODE + TEST_RESULT | Provider Gate | yes |
| Feedback no longer falls back to full `prompt_asset` when `provider_prompt` is missing | validated | `feedback_agent.py`; missing compact prompt test | GITHUB_CODE + TEST_RESULT | Provider Gate | yes |
| Feedback direct fake transport is fake-visible non-success | validated | `feedback_generation_service.py`; `test_polish_feedback_generation_service.py` | GITHUB_CODE + TEST_RESULT | Fake Gate | yes |
| Runtime fake rejection remains covered | validated | `test_fake_llm_boundary.py`; `test_llm_runtime.py` | TEST_RESULT | Fake Gate | yes |
| Source backfill completed without done claim | validated_with_deferred_gaps | `09_REFACTOR_TRACEABILITY_MATRIX.md`; `14_RISK_REGISTER.md`; `17_PHASE_ROADMAP_LOCK.md`; `P7_F_SOURCE_BACKFILL_REPORT.md` | PROJECT_SOURCE + GITHUB_CODE | SRC Gate | yes |
| All LLM provider call sites use the new boundary | not_claimed | Agent E gap ledger | UNKNOWN | Provider Gate | no |
| Bounded answer excerpt can never equal a full short answer | not_claimed | Agent E / F gap ledger | UNKNOWN | Provider Gate | no |

## 4. What Changed

- Added shared provider boundary validation for P7 forbidden keys, schema-bound top-level keys, recursive unsafe-key rejection, and credential-like value redaction.
- Wired Question and Feedback active provider paths to validate compact provider requests before `transport.generate()`.
- Removed Feedback full `prompt_asset` fallback when compact `provider_prompt` is missing.
- Changed Feedback direct fake transport behavior to fake-visible non-success.
- Aligned runtime/agent metadata denylist with the P7 forbidden-key catalog.
- Added provider boundary and Q/F regression tests.
- Backfilled Project sources with audited partial status and explicit gaps.

## 5. Files Changed

| File | Change Type | Reason | Scope Check |
|---|---|---|---|
| `apps/api/app/application/llm/provider_boundary.py` | added | Provider request boundary and validator | allowed |
| `apps/api/app/application/ai_runtime/contracts.py` | modified | P7 sensitive-key catalog alignment | allowed |
| `apps/api/app/application/llm/agent_io.py` | modified | Agent metadata denylist alignment | allowed |
| `apps/api/app/application/polish/question_generation_service.py` | modified | Question provider pre-transport fail-closed validation | allowed |
| `apps/api/app/application/polish/feedback_agent.py` | modified | Feedback provider pre-transport validation and no full prompt fallback | allowed |
| `apps/api/app/application/polish/feedback_generation_service.py` | modified | Fake direct service false-success prevention | allowed |
| `tests/architecture/test_provider_boundary_static.py` | modified | Static catalog / sanitizer guard | allowed |
| `tests/api/test_provider_boundary.py` | added | Provider boundary unit coverage | allowed |
| `tests/api/test_polish_question_refactor_phase1.py` | modified | Question fail-closed regression | allowed |
| `tests/api/test_polish_feedback_agent_io_alignment.py` | modified | Feedback fail-closed / trace safety regression | allowed |
| `tests/api/test_polish_feedback_generation_service.py` | modified | Fake direct service and fixture isolation regression | allowed |
| `docs/goals/2026-06-05/P7_A_PROVIDER_BOUNDARY_RECON.md` | added | Read-only recon evidence | allowed |
| `docs/goals/2026-06-05/P7_B_QF_INTEGRATION_RECON.md` | added | Read-only recon evidence | allowed |
| `docs/goals/2026-06-05/P7_C_FAKE_SECURITY_RECON.md` | added | Read-only recon evidence | allowed |
| `docs/goals/2026-06-05/P7_CONTROLLER_SCOPE_LOCK.md` | added | Controller scope lock evidence | allowed |
| `docs/goals/2026-06-05/P7_D_IMPLEMENTATION_REPORT.md` | added | Single-writer implementation report | allowed |
| `docs/goals/2026-06-05/P7_E_AUDIT_REPORT.md` | added | Read-only audit evidence | allowed |
| `docs/goals/2026-06-05/P7_F_SOURCE_BACKFILL_REPORT.md` | added | Source backfill report | allowed |
| `docs/goals/2026-06-05/P7_FINAL_REPORT.md` | added | Final controller report | allowed |
| `docs/project-sources/09_REFACTOR_TRACEABILITY_MATRIX.md` | modified | Capability status and P7 evidence backfill | allowed |
| `docs/project-sources/14_RISK_REGISTER.md` | modified | RISK-005 / RISK-006 / anti-fiction risk backfill | allowed |
| `docs/project-sources/17_PHASE_ROADMAP_LOCK.md` | modified | Phase 7 status and remaining gaps | allowed |

## 6. Behavior Before / After

| Area | Before | After | Evidence |
|---|---|---|---|
| Provider request shape | Q/F provider request checks were scattered | Q/F active provider requests pass shared schema / forbidden-key validation before transport | provider boundary tests; Q/F tests |
| Full prompt fallback | Feedback could fallback to full `prompt_asset` when `provider_prompt` was missing | Missing compact `provider_prompt` returns failed envelope and does not call transport | feedback agent tests |
| Forbidden keys | P7 forbidden catalog was not centrally enforced | P7 forbidden keys are rejected recursively in provider request data | provider boundary tests |
| Provider unavailable / validation failure | Validation failure could surface later or ambiguously | Validation failure fails closed before provider call | question / feedback fail-closed tests |
| Trace safety | Runtime / agent denylist did not include full P7 catalog | Runtime / agent denylist includes P7 catalog | architecture static tests |
| Fake runtime provider | Feedback direct fake transport could produce generated success | Fake direct service returns fake-visible non-success | feedback generation service tests |

## 7. Provider Gate Result

- Compact builder / equivalent required: yes.
- Question provider path wired: yes.
- Feedback provider path wired: yes.
- Forbidden keys rejected recursively: yes.
- No full prompt asset fallback: yes for Feedback missing `provider_prompt`; broader provider ecosystem not claimed.
- No full resume / JD / answer / asset body fallback: WARN, Q/F active request checks and tests cover forbidden keys, but bounded `current_answer` excerpt remains a deferred semantic gap.
- Provider unavailable fail-closed: yes for validation / fake direct service paths covered by this window.
- Validation/parser failure fail-closed: yes for provider request validation failures.
- Trace safe: yes for covered Q/F validation failure metadata; global transport trace backstop not claimed.

Provider Gate Verdict: `WARN`

## 8. Fake Gate Result

- Runtime fake rejected: yes.
- Fake only tests/evals/replay: yes for covered fixture isolation; Phase 9 CI eval gate not closed.
- Production wiring has no test-fake imports: yes for current scoped audit.
- Fake output trace-visible/fixture-labeled: yes for Feedback direct fake non-success.

Fake Gate Verdict: `WARN`

## 9. Test Commands and Results

| Command | Result | Evidence / Notes |
|---|---|---|
| `PYTHONPATH=.:apps/api PYTHONDONTWRITEBYTECODE=1 AI_FOR_INTERVIEWER_ALLOW_TEST_DIR_LEAKS=1 .venv/bin/python -m pytest -p no:cacheprovider tests/architecture tests/api/test_provider_boundary.py tests/api/test_fake_llm_boundary.py tests/api/test_llm_runtime.py tests/api/test_polish_question_refactor_phase1.py tests/api/test_polish_feedback_generation_service.py tests/api/test_polish_feedback_agent_io_alignment.py tests/api/test_polish_feedback_runtime.py -q` | PASS | `146 passed in 7.14s` |
| `git diff --check` | PASS | exit 0, no output |

Agent E 还审计过这些 focused commands：provider boundary static `2 passed`；provider / fake / runtime selector `15 passed`；Question regression `65 passed`；Feedback service / agent / runtime selector `44 passed`；provider selector `19 passed`；Feedback selector `63 passed`；architecture selector `22 passed`。

未运行 full-repo pytest、web tests、e2e tests。

## 10. Grep Gate Results

| Gate | Command / Pattern | Result | Interpretation |
|---|---|---|---|
| Forbidden provider keys | `rg` scoped to changed implementation/test files for P7 forbidden-key pattern | WARN | Hits are expected catalog, denylist, redaction regex, tests, and safety diagnostic strings; no changed-file hit proves raw/full provider request is sent at runtime. |
| Fake runtime wiring | `rg` scoped to changed files for `LLM_PROVIDER.*fake`, `FakeLLM`, `FakeProvider`, `FakeTransport` | PASS | Exit 1 / no matches in scoped changed production/test target list from controller run. |
| Done claim | `rg` for Phase 7 done / complete status under `docs/project-sources` and `docs/goals/2026-06-05` | PASS_WITH_NOTES | Only non-claim lines were found: D/E explicitly say Phase 7 was not claimed done. |
| Mojibake scan | `rg` for replacement char and common mojibake markers in changed P7 docs | PASS | Exit 1 / no matches. |
| Old plan residue | `rg` for `roadmap-v2`, `plan-v2`, `latest-plan`, `codex-plan` in changed source/goal docs, excluding this final report self-reference | PASS | Exit 1 / no matches. |

## 11. Source Backfill Result

| Source File | Updated? | Status Recorded | Evidence |
|---|---|---|---|
| `09_REFACTOR_TRACEABILITY_MATRIX.md` | yes | `validated_with_deferred_gaps` | `PRO-001`, `PRO-002`, `FAKE-001`, `WIN-001`, `SRC-001` rows and P7 evidence section |
| `12_ACCEPTANCE_GATES.md` | no | not needed | Existing gates already cover this window; no wording change |
| `13_DECISION_LOG.md` | no | not needed | No new long-term decision made |
| `14_RISK_REGISTER.md` | yes | `partially_mitigated` | RISK-005, RISK-006, RISK-P7-FALSE-SUCCESS |
| `17_PHASE_ROADMAP_LOCK.md` | yes | `validated_with_deferred_gaps` | P7-W1 status section |
| `docs/goals/2026-06-05/**` | yes | `validated_with_deferred_gaps` | A/B/C/D/E/F/final artifacts |

## 12. Remaining Risks / Deferred Gaps

| Gap ID | Description | Impact | Required Follow-up | Status |
|---|---|---|---|---|
| P7-GAP-001 | Only Q/F active provider paths are proven protected | Other provider call sites are not covered by this claim | Separate global provider backstop scope or explicit inactive-path proof | deferred |
| P7-GAP-002 | Provider boundary is not wired as a global `LlmTransportRequest` backstop | Future direct transport usage may bypass P7 validator | Add global transport boundary or architecture rule in a later approved window | deferred |
| P7-GAP-003 | Bounded `current_answer` excerpt may equal the full text for a short answer | Cannot claim all full-answer leakage risk is eliminated | Product / prompt policy decision or stricter excerpt semantics | deferred |
| P7-GAP-004 | Single-writer identity is `UNKNOWN` from worktree evidence | Governance proof is incomplete even though scope did not drift | Preserve agent report and controller audit; avoid using it as done evidence | deferred |
| P7-GAP-005 | Full-repo pytest, web tests, and e2e tests were not run | Release readiness not proven | Run broader gates in a separate authorized release / Phase 9 window | deferred |

## 13. Follow-up Goal

Because Phase 7 remains partial, the next goal must be a P7 remediation / scope decision if these gaps must be closed. Phase 8 / Phase 9 must not start from this record alone.

## 14. Final Verdict

Verdict: `WARN`

Completion status: `validated_with_deferred_gaps`

One-sentence reason:

Phase 7 provider request fail-closed behavior is implemented and tested for Question / Feedback active paths with source backfill, but audit-confirmed gaps prevent a `done` claim.

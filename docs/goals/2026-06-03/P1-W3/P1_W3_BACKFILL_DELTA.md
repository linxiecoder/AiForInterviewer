---
title: P1_W3_BACKFILL_DELTA
type: note
permalink: ai-for-interviewer/docs/goals/2026-06-03/p1-w3/backfill-delta
---

# P1-W3 Backfill Delta

## Purpose

本文件只记录 P1-W3 执行后建议回填到 source-pack Matrix / Risk / Decision 的 delta。按本窗口约束，本轮不直接修改 Project source、active product / design / delivery docs、ADR、archive 或业务实现。

## Proposed Matrix Updates

| ID | Proposed status | Evidence | Remaining gap |
| --- | --- | --- | --- |
| DDD-003 | advanced for Phase 1 boundary tests | `tests/architecture/test_application_boundary.py` 新增 domain / focused Polish application service AST import gate；`tests/architecture` 通过并记录 provider known gaps as xfail | 仍不是完整全仓 dependency direction matrix；provider sanitizer 的两个 forbidden keys 仍需实现窗口修复 |
| AGT-002 | C0 boundary locked | `test_agent_platform_c0_boundary.py` 继续锁定 AgentDefinition / SkillDefinition / ToolDefinition contract shape and candidate-only AgentExecutionResult | 未新增 runtime definitions；无 production prompt / provider integration |
| AGT-003 | C0 registry boundary strengthened | `ToolRegistry` 测试新增 repository、DB/session/engine/unit-of-work、formal writer handle 禁止断言 | 暂无持久化 registry、配置加载或 default registry bootstrap |
| AGT-004 | C0 executor port boundary unchanged and guarded | AgentExecutor 仍只是 port；tests 保持其独立于 existing graph runtime contracts | 未实现 executor，不接 LangGraph，不写 formal business facts |
| PRO-002 | test/gate added with known implementation gaps | Provider forbidden-key catalog 固化到 `tests/architecture/test_provider_boundary_static.py`；12 keys hard pass，`developer_prompt` / `full_asset_body` strict xfail | `app.application.ai_runtime.contracts` 当前未 block `developer_prompt` / `full_asset_body`，需后续实现窗口 |
| FAKE-001 | covered by existing runtime boundary tests | `tests/api/test_fake_llm_boundary.py` -> `5 passed`; `tests/api/test_llm_runtime.py` -> `6 passed`; fake provider remains rejected from env | 本窗口未改 runtime config；如后续 fake/runtime policy 变化需同步测试 |
| WIN-001 | pass for P1-W3 | Changed files stayed within tests/architecture, allowed API boundary tests, and docs/goals evidence allowlist; no app implementation changes | No broad CI workflow evidence claimed; Phase 1 still open |

## Proposed Risk Updates

| Risk | Proposed disposition | Evidence / rationale |
| --- | --- | --- |
| Domain importing infrastructure / API / provider code | Mitigated for P1-W3 gate | New AST import scan covers domain forbidden imports and passes. |
| Focused Polish services importing prompt/runtime/provider dependencies | Mitigated for P1-W3 gate | New AST import scan covers all `*_application_service.py` focused services and passes. |
| Agent Platform C0 drifting into DB/provider/runtime handles | Mitigated for C0 | Strengthened import markers and ToolRegistry direct-handle assertions pass. |
| Agent result bypassing candidate-only boundary | Mitigated for C0 | `AgentExecutionResult` field scan now rejects formal refs, formal outputs, and formal write result/path fields. |
| Provider sensitive-key denylist incomplete | Keep Open | `developer_prompt` and `full_asset_body` are strict xfail known gaps; implementation change is outside P1-W3. |
| Fake provider returning through runtime env | Mitigated by existing tests | Existing API tests verify `LLM_PROVIDER=fake` rejection and explicit test fake facade usage. |
| Phase status overclaim | Keep Open | P1-W3 evidence explicitly states Phase 1 remains open pending separate close-out assessment. |

## Proposed Decision Updates

- Decision: P1-W3 architecture tests use AST import scanning for dependency boundary assertions where possible.
- Decision: Focused Polish application services may depend on application DTOs, ports and domain value/error helpers, but must not import prompt builders/assets, provider/runtime, infrastructure DB, API routes, FastAPI, DB libraries, LangGraph, `app.application.ai_runtime` or `app.application.agents`.
- Decision: `ToolRegistry` remains a definition registry only and must not expose repository, DB/session/engine/unit-of-work or direct formal write handles.
- Decision: `AgentExecutionResult` remains candidate-only until handoff; formal business writes must not appear as result fields.
- Decision: Provider forbidden-key coverage for `developer_prompt` and `full_asset_body` is intentionally recorded as an implementation gap, not patched in P1-W3.
- Decision: P1-W3 does not complete Phase 1; close-out requires a separate assessment or explicit deferral of remaining P1 ownership work.

## Validation Evidence

- `tests/architecture -q` -> `21 passed, 2 xfailed`
- `tests/api/test_polish_application_service_split.py -q` -> `7 passed`
- `tests/api/test_fake_llm_boundary.py -q` -> `5 passed`
- `tests/api/test_llm_runtime.py -q` -> `6 passed`
- `compileall tests/architecture tests/api` -> passed
- `git diff --check` -> passed
- forbidden import scan -> no forbidden matches in scoped app paths
- provider forbidden-key scan -> key catalog present in test/gate files

## Remaining Gaps

- `developer_prompt` is not currently blocked by `app.application.ai_runtime.contracts.contains_sensitive_payload()` / `sanitize_payload()`.
- `full_asset_body` is not currently blocked by `app.application.ai_runtime.contracts.contains_sensitive_payload()` / `sanitize_payload()`.
- No business implementation changes were authorized or made to close those two gaps.
- No default AgentDefinition / SkillDefinition / ToolDefinition catalog entries were added.
- No AgentExecutor implementation or Question / Feedback runtime wiring was added.
- No broad CI workflow evidence is claimed.
- Phase 1 remains open.

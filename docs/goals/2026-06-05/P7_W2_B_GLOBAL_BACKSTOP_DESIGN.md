---
title: P7_W2_B_GLOBAL_BACKSTOP_DESIGN
type: goal-evidence
status: evidence-only
permalink: ai-for-interviewer/docs/goals/2026-06-05/p7-w2-b-global-backstop-design
---

# P7-W2-B Global Backstop Design

Mode: read-only design, then controller-chosen minimal option

## 结论

选择 Option B：迁移当前生产 `LlmTransportRequest(...)` 构造点到 `build_validated_transport_request(...)`，并增加严格静态 architecture gate。同时在 `LlmTransportRequest` DTO 上增加 P7 forbidden-key backstop，确保直接 DTO bypass 或 `dataclasses.replace(...)` 注入 forbidden key 会失败。

该方案不改 API contract、prompt 文案、DB、Phase 8 runtime、provider SDK transport 行为。

## Options

| Option | Description | Pros | Cons | Decision |
|---|---|---|---|---|
| A | 只加静态门禁 | 最小行为变化 | 不能关闭现有 bypass | not chosen |
| B | 迁移生产 callers 到 builder + 静态门禁 + DTO forbidden-key backstop | 覆盖当前 active callers，保持 provider SDK 不变 | 需要触碰多个 provider caller 文件 | chosen |
| C | 增加 transport wrapper | 最接近 runtime wrapper | 需要重接 transport 注入，影响面更大 | not chosen |

## Chosen Design

- `P7_PROVIDER_FORBIDDEN_KEYS` 成为 `types.py` 的共享 catalog，`provider_boundary.py` 复用该 catalog。
- `LlmTransportRequest.__post_init__` 拒绝 recursive forbidden keys；`dataclasses.replace(...)` 也会触发同一 backstop。
- `progress_tree.py` initial / refresh provider calls 使用 `build_validated_transport_request(...)`，并定义 per-task required / allowed top-level keys。
- `job_match.py` 使用 validated builder；validation failure 转为 `JobMatchAnalyzerUnavailableError("provider_request_validation_failed")`。
- `polish_feedback_graph.py` trace request 使用 validated builder，保留原 PR8 refs/digests-only evidence contract。
- `tests/architecture/test_provider_boundary_static.py` 禁止 `apps/api/app` 生产代码直接调用 `LlmTransportRequest(...)`，唯一例外是 `application/llm/provider_boundary.py`。

## Non-Goals

- 不重写 prompt。
- 不修改 provider SDK transport。
- 不改 API v1 routes。
- 不改 DB / migration。
- 不实现 Phase 8 LangGraph runtime。
- 不进入 Phase 9 eval / CI gate。

## Expected Status

Global forbidden-key backstop 可验证；per-task schema compactness 仍由 builder/static gate 证明。Answer excerpt policy 不在本设计中更改。

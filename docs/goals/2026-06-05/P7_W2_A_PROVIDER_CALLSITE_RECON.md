---
title: P7_W2_A_PROVIDER_CALLSITE_RECON
type: goal-evidence
status: evidence-only
permalink: ai-for-interviewer/docs/goals/2026-06-05/p7-w2-a-provider-callsite-recon
---

# P7-W2-A Provider Call-Site Recon

Window ID: `P7-W2-PROVIDER-GLOBAL-BACKSTOP-AND-ANSWER-REDACTION-GAPS`

Mode: read-only recon

## 结论

P7-W2 patch 前存在 active production provider bypass：`progress_tree.py` 两个调用点和 `job_match.py` 一个调用点直接构造 `LlmTransportRequest(...)` 并调用 `transport.generate(...)`，未经过 `build_validated_transport_request(...)`。

`question_generation_service.py` 与 `feedback_agent.py` 已使用 validated builder。`polish_question_runtime.py` 通过 `QuestionGenerationService` 上游进入 builder；`polish_feedback_graph.py` 是 default-off trace gate，仍需要迁移以满足静态门禁但不是 active feedback generation provider caller。

## Required Searches

| Command | Result |
|---|---|
| `rg "LlmTransportRequest\\(" apps/api/app tests -n` | 生产命中：`provider_boundary.py`、`polish_feedback_graph.py`、`progress_tree.py`、`job_match.py`；其余为测试。 |
| `rg "transport\\.generate\\(" apps/api/app tests -n` | 生产 caller：Question、Feedback、progress tree、job match、feedback trace gate、question runtime wrapper。 |
| `rg "build_validated_transport_request\\(" apps/api/app tests -n` | patch 前仅 Question / Feedback direct active paths 使用 builder。 |

## Call-Site Inventory

| Classification | Path | Evidence | Decision |
|---|---|---|---|
| already uses builder | `apps/api/app/application/polish/question_generation_service.py` | `build_validated_transport_request(...)` before `transport.generate(request)` | covered |
| already uses builder | `apps/api/app/application/polish/feedback_agent.py` | compact `provider_prompt` required; validation failure returns `provider_request_invalid` | covered |
| active production path needing boundary | `apps/api/app/application/polish/progress_tree.py` | initial and refresh provider calls directly built `LlmTransportRequest(...)` | must migrate |
| active production path needing boundary | `apps/api/app/infrastructure/llm/job_match.py` | active API bootstraps `LlmJobMatchAnalyzer` with runtime transport | must migrate |
| inactive/default-off trace gate | `apps/api/app/application/ai_runtime/business_graphs/polish_feedback_graph.py` | PR8 trace request uses refs/digests and provider gate is default-off | migrate for static consistency |
| infrastructure wrapper, not caller | `apps/api/app/infrastructure/ai_runtime/langgraph/polish_question_runtime.py` | delegates through `QuestionGenerationService`; wrapper mutates request with `replace(...)` | DTO backstop should catch unsafe replacement |
| test/debug only | `tests/**` direct request constructors | required transport/fake/raw-debug fixtures | excluded from production static gate |

## Gap Classification

- `P7-GAP-001`: patch 前仍 open；Q/F 以外 active callers 未证明受保护。
- `P7-GAP-002`: patch 前仍 open；`LlmTransportRequest` DTO 未提供 forbidden-key backstop。
- `P7-GAP-003`: 转交 C report；answer excerpt 仍需产品/隐私策略判断。

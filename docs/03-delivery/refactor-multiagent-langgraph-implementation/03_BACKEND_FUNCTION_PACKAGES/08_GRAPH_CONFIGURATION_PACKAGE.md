---
title: Graph Configuration Package
type: delivery-planning
status: draft-f5-langgraph-implementation-consolidation
owner: 后端架构 / AI Runtime
permalink: ai-for-interviewer/docs/03-delivery/refactor-multiagent-langgraph-implementation/backend-function-packages/graph-configuration-package
---

# Graph Configuration Package

## 1. Package 目标

本 package 定义 Graph Configuration Backend / Registry Config API 的 method、API、DTO、audit、role 和 scope plan。目标是在业务 graph 扩展前，先建立 default-off、owner/admin scoped、sanitized-only 的配置面。

本 package 不授权任何业务 graph execution，不授权 provider call，不暴露 LangGraph debug internals。

## 2. Allowed scope

| Scope | Required behavior |
|---|---|
| graph descriptor API | 返回 graph id、capability、status、migration stage、contract refs、policy refs 和 placeholder status |
| graph config schema | 定义 enablement、default mode、policy refs、health visibility、audit metadata 和 validation errors |
| graph enablement/default-off config API | 所有 graph 默认关闭；启用必须显式 owner/admin scoped action |
| placeholder graph registry | 可登记未迁移 graph 的 descriptor，不得执行 graph |
| prompt/eval/provider policy refs | 只展示 policy ref id、版本、状态和 redacted summary；不得展示 prompt/provider payload |
| admin/owner scope | 所有读写都需要 owner 或 admin scope；普通用户不得进入配置面 |
| config audit | 记录 actor、action、target graph、old/new sanitized summary、status、reason、error category |

## 3. Forbidden scope

| Forbidden | Reason |
|---|---|
| full business graph implementation | 本 package 只定义配置面，不实现业务 graph |
| provider call | 配置 API 不触发 LLM/provider 调用 |
| raw prompt / completion / provider payload exposure | 违反 raw-off 和 security/privacy boundary |
| provider secret / model key exposure | UI/API 只能显示 policy refs 和 redacted model policy summary |
| LangGraph debug internals exposure | 不返回 AgentState、checkpoint payload、compiled graph internals 或 node raw input/output |
| normal-user Agent debug page support | PR7 console 是受控配置页面，不是普通用户 debug page |

## 4. API plan

| Method | Path sketch | Purpose | Response rule |
|---|---|---|---|
| `list_graph_descriptors` | `GET /api/v1/ai-runtime/graphs` | 列出可配置 graph descriptor | sanitized list；default-off state；no raw internals |
| `get_graph_descriptor` | `GET /api/v1/ai-runtime/graphs/{graph_id}` | 读取单个 graph descriptor | includes migration stage、policy refs、placeholder status |
| `get_graph_config` | `GET /api/v1/ai-runtime/graphs/{graph_id}/config` | 读取当前配置 | owner/admin scoped；redacted policy summary |
| `update_graph_config` | `PUT /api/v1/ai-runtime/graphs/{graph_id}/config` | enable/disable 或更新 policy refs | validates default-off, policy refs and role scope |
| `list_graph_config_audit` | `GET /api/v1/ai-runtime/graphs/{graph_id}/audit-events` | 读取配置审计 | sanitized actor/action/status/error summary |
| `get_graph_health` | `GET /api/v1/ai-runtime/graphs/{graph_id}/health` | 读取配置可见的健康摘要 | no checkpoint、AgentState、prompt、completion or provider payload |

Path sketch 只表达 API intent；正式 endpoint 必须回写 `API_SPEC.md` 或受权 PR contract 后才能实现。

## 5. DTO plan

| DTO | Fields | Forbidden fields |
|---|---|---|
| `GraphDescriptorResponse` | `graph_id`, `display_name`, `capability`, `migration_stage`, `status`, `contract_refs`, `policy_refs`, `placeholder`, `owner_scope_required` | compiled graph, AgentState, checkpoint payload |
| `GraphConfigResponse` | `graph_id`, `enabled`, `default_off`, `mode`, `prompt_policy_ref`, `eval_policy_ref`, `provider_policy_ref`, `updated_by`, `updated_at`, `version` | raw prompt, completion, provider payload, secret key |
| `GraphConfigUpdateRequest` | `enabled`, `mode`, `prompt_policy_ref`, `eval_policy_ref`, `provider_policy_ref`, `reason`, `base_version` | provider credentials, raw prompt body |
| `GraphConfigAuditEventResponse` | `event_id`, `actor_ref`, `action`, `graph_id`, `old_summary`, `new_summary`, `status`, `reason`, `error_category`, `created_at` | raw config diff with secrets, raw provider response |
| `GraphHealthStatusResponse` | `graph_id`, `config_status`, `last_config_event_ref`, `runtime_available`, `blocked_reason`, `sanitized_error` | node raw input/output, checkpoint state |

## 6. Registry plan

Placeholder registry may include these descriptor names as metadata only:

- `polish_progress_tree_graph`
- `polish_question_graph`
- `polish_feedback_graph`
- `resume_analysis_graph`
- `job_match_graph`
- `pressure_interview_graph`
- `report_generation_graph`
- `mock_review_generation_graph`
- `real_review_generation_graph`
- `candidate_confirmation_interrupt_graph`
- `training_suggestion_graph`

Descriptor presence does not mean executable graph exists. Execution still requires the dedicated migration PR, feature flag, parity tests, rollback plan and active API contract.

## 7. Role and audit rules

| Rule | Required behavior |
|---|---|
| owner/admin only | config read/write is not exposed to normal user workflows |
| reason required | enable/disable or policy ref changes require a human-readable reason |
| optimistic concurrency | config update must include `base_version` and return sanitized 409 on stale write |
| audit before response | successful or failed config update writes sanitized audit before returning |
| no silent enablement | descriptor registration never enables graph execution |
| default-off | new descriptors and configs default to disabled |

## 8. Validation plan

| Gate | Required check |
|---|---|
| scope check | only graph config backend files after explicit PR scope lock |
| forbidden payload scan | no raw prompt/completion/provider payload/secret/checkpoint field in DTO/API response |
| owner/admin check | unauthorized normal user gets sanitized 403 |
| default-off check | new graph descriptor is disabled unless explicit config update succeeds |
| audit check | config change creates sanitized audit event |
| placeholder check | placeholder registry cannot execute graph or call provider |


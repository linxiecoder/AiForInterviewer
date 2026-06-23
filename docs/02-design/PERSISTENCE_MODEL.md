---
title: PERSISTENCE_MODEL
type: design
status: draft-f4-persistence-handoff
owner: 数据架构 / 后端架构
source_task: AIFI-ARCH-006
permalink: ai-for-interviewer/docs/02-design/persistence-model
---

# PERSISTENCE_MODEL

## 1. 文档状态与治理边界

- 本文件是 F5 persistence handoff，不是最终 DDL、ORM model、migration 或数据库选型文档。
- 本文件承接 `DATA_MODEL.md` 的逻辑对象，补齐人工审计中“数据模型只有逻辑模型，缺字段、API 映射、物理关系、1:N / M:N / join table 和去重设计”的整改。
- F5 可以按技术栈调整字段类型、索引名、分区策略和迁移顺序，但不得删除本文件冻结的 owner、version、status、trace、evidence、candidate / suggestion / confirmation 和历史引用语义。
- 本文件不要求 MVP 一次性实现复杂多租户、向量库物理 schema、真实招聘结果校准、自动去重算法或复杂合并算法。

## 2. 输入来源与非目标

| 来源 | 使用方式 |
|---|---|
| `DATA_MODEL.md` | 逻辑对象、引用模型、状态、版本、candidate / suggestion / confirmation 边界 |
| `API_SPEC.md` | API schema、异步任务、幂等、copy boundary、F7 contract tests |
| `PROMPT_SPEC.md` / `prompt-contracts/*.md` | AI task result、validation、low confidence、evidence、trace 和 persistence target |
| `SCORING_SPEC.md` | 评分规则、`ScoreResult`、`ScoreRuleVersion`、维度、权重和正式落库边界 |
| `SEMANTICS_GLOSSARY.md` | canonical enum、low confidence、source availability 和状态映射 |
| `SECURITY_PRIVACY.md` | owner、actor、隐私脱敏、retention、audit、禁止原始 Prompt / provider payload 暴露 |
| `PRESSURE_MODE_SPEC.md` | Pressure turn refs、pace/end/report input package、review handoff、raw-off 和 PR2 graph hold 的持久化承接 |

非目标：

- 不提供 SQL DDL、索引语法、ORM class、migration 文件或数据库供应商特性。
- 不保存 system prompt 原文、provider payload、completion 原文、token、cookie、secret 或未脱敏日志正文。
- 不把 candidate / suggestion 静默升级为 formal object。
- 不把 `ResumeMarkdownOutline`、`JobBindingSummary`、`JobMatchSummary` 等 read model 误建成不可回溯的业务真相。

## 3. 通用物理字段规则

除特别说明外，所有实体表至少包含：

| 字段组 | 规则 |
|---|---|
| primary key | 使用稳定业务 ID，例如 `res_*`、`job_*`、`score_*`；不得由 owner 推导 |
| owner / actor | `owner_id` 表示资源归属；mutation / audit / confirmation 必须记录 `actor_id` |
| version | `record_version` 用于乐观锁；历史内容另用 `VersionRef` / `SnapshotRef` |
| status | 使用 canonical enum 或领域状态；不得用 null 表示状态 |
| timestamps | `created_at`、`updated_at` 必填；历史 / 删除 / 禁用场景增加 `archived_at`、`deleted_at`、`disabled_at` |
| trace | AI、API、copy、confirmation 和评分结果必须可关联 `trace_refs` 或 `api_request_traces` |
| sensitivity | 敏感正文只进业务表或受控 summary，不进 audit body、trace body 或 copy event body |

## 4. 核心物理模型清单

| 物理模型 | PK | owner / actor | version | status | timestamps | 关键 FK | 唯一约束 | 关系 | 分类 |
|---|---|---|---|---|---|---|---|---|---|
| `user_accounts` | `user_id` | `owner_id=user_id` | `record_version` | `active / disabled / deleted` | `created_at / updated_at` | N/A | `email_normalized` | 1:N resumes, jobs, sessions, assets | aggregate root |
| `resumes` | `resume_id` | `owner_id` | `record_version` | `active / archived / deleted` | `created_at / updated_at` | `current_version_id` -> `resume_versions` | `(owner_id, resume_id)` | 1:N `resume_versions`; 1:N bindings | aggregate root |
| `resume_versions` | `resume_version_id` | `owner_id` | `record_version` | `current / superseded / archived` | `created_at / updated_at` | `resume_id` | `(resume_id, version_number)` | N:1 resume; 1:N evidence refs | entity / snapshot |
| `jobs` | `job_id` | `owner_id` | `record_version` | `active / archived / deleted` | `created_at / updated_at` | `current_version_id` -> `job_versions` | `(owner_id, job_id)` | 1:N `job_versions`; 1:N bindings | aggregate root |
| `job_versions` | `job_version_id` | `owner_id` | `record_version` | `current / superseded / archived` | `created_at / updated_at` | `job_id` | `(job_id, version_number)` | N:1 job; 1:N evidence refs | entity / snapshot |
| `resume_job_bindings` | `binding_id` | `owner_id / actor_id` | `record_version` | `active / unbound / stale / archived` | `created_at / updated_at / unbound_at` | `resume_id`, `job_id`, `resume_version_id`, `job_version_id` | `(owner_id, resume_id, job_id, status=active)` | N:1 resume; N:1 job; 1:N job match analyses | entity |
| `interview_sessions` | `session_id` | `owner_id / actor_id` | `record_version` | `draft / active / paused / completed / cancelled / failed` | `created_at / updated_at` | `binding_id`, `resume_version_id`, `job_version_id` | `(owner_id, session_id)` | 1:1 polish / pressure detail; 1:N questions / answers / reports | aggregate root |
| `polish_session_details` | `polish_detail_id` | `owner_id` | `record_version` | `active / paused / completed / failed` | `created_at / updated_at` | `session_id`, `topic_ref`, `subtopic_ref` | `session_id` | 1:1 interview session; 1:N feedback | entity |
| `pressure_session_details` | `pressure_detail_id` | `owner_id` | `record_version` | `active / paused / completed / failed` | `created_at / updated_at` | `session_id` | `session_id` | 1:1 interview session; 1:N follow-up / turn refs; report input package refs may use typed references | entity |
| `questions` | `question_id` | `owner_id / actor_id` | `record_version` | `draft / available / answered / skipped / invalid` | `created_at / updated_at` | `session_id`, `ai_task_id` | `(session_id, question_id)` | 1:N answers; N:1 session | entity |
| `answers` | `answer_id` | `owner_id / actor_id` | `record_version` | `submitted / superseded / invalid` | `created_at / updated_at` | `session_id`, `question_id` | `(question_id, answer_round)` | N:1 question; 1:N feedback; 1:N evidence refs | entity |
| `feedback` | `feedback_id` | `owner_id` | `record_version` | `available / partial / low_confidence / validation_failed` | `created_at / updated_at` | `session_id`, `answer_id`, `ai_task_id`, `score_result_id` | `(answer_id, ai_task_id)` | N:1 answer; 1:N loss points; N:M score results via refs | entity |
| `score_rule_sets` | `score_rule_set_id` | `owner_id` nullable for global | `record_version` | `active / deprecated / disabled` | `created_at / updated_at` | N/A | `(score_type, name, status=active)` | 1:N score_rule_versions | aggregate root |
| `score_rule_versions` | `score_rule_version_id` | `owner_id` nullable for global | `record_version` | `draft / active / deprecated / disabled` | `created_at / updated_at` | `score_rule_set_id` | `(score_rule_set_id, version)` | 1:N score_dimensions; 1:N score_results | entity / version |
| `score_dimensions` | `score_dimension_id` | `owner_id` nullable | `record_version` | `active / deprecated` | `created_at / updated_at` | `score_rule_version_id` | `(score_rule_version_id, dimension_key)` | N:1 score_rule_version; 1:N score evidence links | value object |
| `score_results` | `score_result_id` | `owner_id` | `record_version` | `candidate / valid / valid_with_warnings / invalid / manual_review_required` | `created_at / updated_at / generated_at` | `score_rule_version_id`, `ai_task_id`, `target_ref_id` | `(owner_id, target_ref_id, score_type, score_rule_version_id, ai_task_id)` | N:1 rule version; N:M evidence via `score_evidence_links`; N:M reports via reference table | entity / result |
| `score_evidence_links` | `score_evidence_link_id` | `owner_id` | `record_version` | `active / ignored / conflict` | `created_at / updated_at` | `score_result_id`, `score_dimension_id`, `evidence_ref_id` | `(score_result_id, score_dimension_id, evidence_ref_id)` | join score result to evidence | join table |
| `low_confidence_flags` | `low_confidence_flag_id` | `owner_id` | `record_version` | `active / resolved / ignored` | `created_at / updated_at` | `target_ref_id`, `validation_result_ref_id`, `trace_ref_id` | `(target_ref_id, reason, trace_ref_id)` | N:1 target; N:1 trace | trace / risk |
| `interview_reports` | `report_id` | `owner_id / actor_id` | `record_version` | `generating / available / partial / low_confidence / failed` | `created_at / updated_at / generated_at` | `session_id`, `ai_task_id`, `score_result_id` | `(owner_id, session_id, report_type, generated_at)` | 1:N report_sections; N:M score results via reference table | entity / snapshot-backed result |
| `report_sections` | `report_section_id` | `owner_id` | `record_version` | `available / partial / low_confidence / hidden` | `created_at / updated_at` | `report_id`, `score_result_id` nullable | `(report_id, section_key)` | N:1 report; N:1 score result | value object |
| `interview_reviews` | `review_id` | `owner_id / actor_id` | `record_version` | `generating / available / partial / low_confidence / failed` | `created_at / updated_at / generated_at` | `session_id`, `report_id`, `real_interview_input_ref`, `ai_task_id` | `(owner_id, review_type, source_ref_id, generated_at)` | 1:N review items via evidence refs; 1:N candidates | entity / result |
| `weaknesses` | `weakness_id` | `owner_id / actor_id` | `record_version` | `confirmed / low_priority / ignored / resolved_candidate / resolved / reopened` | `created_at / updated_at` | `created_from_candidate_id` nullable | `(owner_id, normalized_title, status in active_states)` | 1:N weakness_candidates; N:M evidence via `evidence_refs`; N:M training recommendations | entity |
| `weakness_candidates` | `weakness_candidate_id` | `owner_id` | `record_version` | `draft / needs_confirmation / merge_suggested / low_confidence / rejected / confirmed` | `created_at / updated_at` | `ai_task_id`, `target_weakness_id` nullable | `(owner_id, source_ref_id, normalized_title, ai_task_id)` | N:1 ai task; N:M evidence refs; N:M suggestions | candidate |
| `assets` | `asset_id` | `owner_id / actor_id` | `record_version` | `active / archived / disabled / deleted` | `created_at / updated_at` | `current_version_id` -> `asset_versions` | `(owner_id, normalized_title, status=active)` | 1:N asset_versions; 1:N asset_candidates | aggregate root |
| `asset_versions` | `asset_version_id` | `owner_id / actor_id` | `record_version` | `draft / active / superseded / archived` | `created_at / updated_at` | `asset_id`, `created_from_candidate_id` nullable | `(asset_id, version_number)` | N:1 asset; N:M source refs | entity / snapshot |
| `asset_candidates` | `asset_candidate_id` | `owner_id` | `record_version` | `draft / needs_confirmation / merge_suggested / low_confidence / rejected / confirmed` | `created_at / updated_at` | `ai_task_id`, `target_asset_id` nullable | `(owner_id, source_ref_id, normalized_title, ai_task_id)` | N:1 ai task; N:M source refs via `evidence_refs`; N:M suggestions | candidate |
| `training_recommendations` | `training_recommendation_id` | `owner_id / actor_id` | `record_version` | `candidate / confirmed / skipped / rejected / low_confidence / completed` | `created_at / updated_at` | `ai_task_id`, `confirmation_id` nullable | `(owner_id, normalized_topic, status in active_states)` | N:M weaknesses; N:M assets; 1:N training tasks | suggestion / entity |
| `ai_tasks` | `ai_task_id` | `owner_id / actor_id` | `record_version` | `queued / running / succeeded / partial / low_confidence / validation_failed / source_unavailable / generation_failed / timed_out / cancelled` | `created_at / updated_at / timeout_at` | `idempotency_record_id`, `target_ref_id` | `(owner_id, task_type, idempotency_record_id)` | 1:N ai_task_results; N:M input refs | api task entity |
| `ai_task_results` | `ai_task_result_id` | `owner_id` | `record_version` | `succeeded / partial / low_confidence / validation_failed / source_unavailable / generation_failed` | `created_at / updated_at` | `ai_task_id`, `validation_result_ref_id`, `trace_ref_id` | `(ai_task_id, result_sequence)` | N:1 ai task; N:M candidate / suggestion refs | task result |
| `agent_runs` | `agent_run_id` | `owner_id / actor_id` | `record_version` | `planned / running / interrupted / succeeded / partial / failed / cancelled / expired` | `created_at / updated_at / completed_at` | `ai_task_id`, `graph_descriptor_ref_id`, `idempotency_record_id` | `(owner_id, ai_task_id, graph_name, idempotency_record_id)` | 1:N agent_node_runs; 1:N interrupts; 1:N checkpoint refs; N:M input/result refs | AI Runtime control entity |
| `agent_node_runs` | `agent_node_run_id` | `owner_id` | `record_version` | `planned / running / succeeded / skipped / validation_failed / failed / cancelled` | `created_at / updated_at / started_at / finished_at` | `agent_run_id`, `validation_result_ref_id`, `trace_ref_id` | `(agent_run_id, node_name, sequence_number)` | N:1 agent run; N:M trace/evidence refs | AI Runtime node trace |
| `agent_interrupts` | `interrupt_id` | `owner_id / actor_id` | `record_version` | `pending / resumed / rejected / expired / cancelled` | `created_at / updated_at / expires_at / resolved_at` | `agent_run_id`, `resume_schema_ref_id`, `idempotency_record_id`, `audit_event_id` | `(owner_id, agent_run_id, interrupt_type, status=pending)` | N:1 agent run; N:M candidate refs; audit refs | AI Runtime interrupt |
| `agent_checkpoint_refs` | `checkpoint_ref_id` | `owner_id` | `record_version` | `active / expired / invalid / redacted` | `created_at / updated_at / expires_at` | `agent_run_id` | `(agent_run_id, namespace, thread_id, checkpoint_id)` | N:1 agent run; metadata-only checkpoint refs | AI Runtime checkpoint ref |
| `llm_calls` | `llm_call_id` | `owner_id / actor_id` | `record_version` | `planned / running / succeeded / validation_failed / provider_failed / cancelled / skipped` | `planned_at / started_at / finished_at / created_at / updated_at` | `ai_task_id`, `agent_run_id`, `agent_node_run_id`, `validation_result_ref_id` | `(owner_id, ai_task_id, call_sequence)` | N:1 AI task; optional N:1 agent run/node; 1:1 or 1:N payload refs | AI Runtime LLM call lifecycle |
| `llm_call_payloads` | `llm_call_payload_id` | `owner_id` | `record_version` | `summary_only / raw_disabled / raw_ref_available / expired / redacted` | `created_at / updated_at / expires_at` | `llm_call_id`, `audit_event_id` | `(llm_call_id, payload_kind)` | N:1 llm call; raw refs default null | restricted debug payload ref |
| `api_request_traces` | `api_request_trace_id` | `owner_id / actor_id` | `record_version` | `success / failed / denied / rate_limited` | `created_at / updated_at` | `audit_event_id` nullable | `(request_id, trace_id)` | 1:N audit events; N:M trace refs | trace |
| `audit_events` | `audit_event_id` | `owner_id / actor_id` | `record_version` | `recorded / redacted / rejected` | `created_at / updated_at` | `api_request_trace_id`, `target_ref_id` | `(owner_id, actor_id, event_type, created_at)` | N:1 trace; N:1 target | trace / audit |
| `evidence_refs` | `evidence_ref_id` | `owner_id` | `record_version` | `source_available / source_archived / source_deleted / source_disabled / source_unavailable` | `created_at / updated_at` | `source_ref_id`, `version_ref_id`, `snapshot_ref_id` | `(owner_id, source_ref_id, evidence_hash)` | typed reference table; supports M:N evidence links | reference table |
| `trace_refs` | `trace_ref_id` | `owner_id` | `record_version` | `active / redacted / expired` | `created_at / updated_at` | `api_request_trace_id`, `ai_task_id`, `audit_event_id` nullable | `(owner_id, trace_kind, trace_key)` | typed trace reference | reference table |
| `typed_reference_links` | `typed_reference_link_id` | `owner_id` | `record_version` | `active / removed / conflict` | `created_at / updated_at` | `source_ref_id`, `target_ref_id` | `(owner_id, source_ref_id, target_ref_id, relation_type)` | generic M:N links for report-score, training-weakness, training-asset and similar relations | join / reference table |
| `user_confirmations` | `confirmation_id` | `owner_id / actor_id` | `record_version` | `confirmed / edited / skipped / rejected / merge_requested / manual_review` | `created_at / updated_at` | `target_ref_id`, `audit_event_id` | `(owner_id, actor_id, target_ref_id, action, created_at)` | N:1 candidate / suggestion / formal target | confirmation |

## 5. M:N 与 join / reference table 规则

M:N 关系不得通过复制对象、重复建模型或在多个表中保存互相冲突的字段表达。F5 必须使用 join table 或 typed reference table。

| M:N 场景 | 推荐表达 | 理由 |
|---|---|---|
| score result 到 evidence | `score_evidence_links` | 每个维度可绑定不同 evidence role，能记录 conflict / ignored |
| report 到 score result | `report_sections.score_result_id` + 可选 `typed_reference_links(report_id, score_result_id, relation=uses_score)` | 报告可能引用总分和多个分项分，避免把分数复制进报告正文 |
| weakness 到 evidence | `evidence_refs` typed reference，relation=`weakness_evidence` | 弱项证据来自题答、评分、复盘、用户确认，来源多样 |
| asset candidate 到 source | `evidence_refs` typed reference，relation=`asset_candidate_source` | 候选来源可来自回答、参考答案、复盘、资产版本 |
| training recommendation 到 weakness / asset | `typed_reference_links(training_recommendation_id, weakness_id/asset_id)` | 训练建议可同时关联多个弱项和资产，不应重复训练建议 |

如果 F5 不新增通用 `typed_reference_links` 表，也必须以等价 join table 表达上述关系；不得使用逗号字符串、不可校验 JSON 文本或复制完整对象替代关系。

## 6. 逻辑对象 -> 物理模型 -> API schema 映射

| 逻辑对象 | 推荐物理模型 | API schema / endpoint |
|---|---|---|
| `Resume` / `ResumeVersion` | `resumes` / `resume_versions` | `ResumeSummary`、`ResumeDetail`、`CreateResumeRequest`、`UpdateResumeRequest` |
| `ResumeMarkdownOutline` | derived read model，可由 `resume_versions.markdown_text` 派生，可选 snapshot summary | `ResumeDetail.derived_outline` 或后续 summary 字段；不是 CRUD 资源 |
| `Job` / `JobVersion` | `jobs` / `job_versions` | `JobSummary`、`JobDetail`、`CreateJobRequest`、`UpdateJobRequest` |
| `JobBindingSummary` | derived read model from `resume_job_bindings` | `JobSummary.binding_summary`、`JobDetail.binding_summary` |
| `JobMatchSummary` | derived read model from latest `score_results` / job match task | `JobSummary.latest_match_summary`、`JobDetail.latest_match_summary` |
| `InterviewSession` | `interview_sessions` + mode detail table | `PolishSessionResponse`、`PressureSessionResponse` |
| `SessionSummary` | snapshot-backed summary linked to `interview_sessions` and `trace_refs` | `session_summary_ref`、Prompt input ref；不是唯一 truth source |
| `PressureTurn` / `PressureReportInputPackage` | reconstruct from `pressure_session_details` + `questions` / `answers` / `feedback` / `score_results` / `ai_task_results` + typed refs, unless later PR adds dedicated table | `PressureSessionResponse` refs、`AiTaskResultResponse`、`ReportResponse` input refs |
| `Question` / `Answer` / `Feedback` | `questions` / `answers` / `feedback` | `QuestionResponse`、`AnswerResponse`、`FeedbackResponse` |
| `ScoreResult` | `score_results` + `score_evidence_links` | `ScoreResultResponse`、`JobMatchSummary.display_score`、report `score_ref` |
| `InterviewReport` / `ReportSection` | `interview_reports` / `report_sections` | `ReportResponse`、`ReportCopyContentResponse` |
| `InterviewReview` | `interview_reviews` + evidence / trace refs | `ReviewSummary`、`ReviewResponse` |
| `WeaknessCandidate` / `Weakness` | `weakness_candidates` / `weaknesses` | `WeaknessCandidateResponse`、`WeaknessResponse` |
| `AssetCandidate` / `Asset` / `AssetVersion` | `asset_candidates` / `assets` / `asset_versions` | `AssetCandidateResponse`、`AssetResponse` |
| `TrainingRecommendation` | `training_recommendations` + reference links | `TrainingSuggestionResponse` |
| `AiTask` / `AiTaskResult` | `ai_tasks` / `ai_task_results` | `AiTaskStatusResponse`、`AiTaskResultResponse` |
| `AgentRun` / `AgentNodeRun` | `agent_runs` / `agent_node_runs` | `AgentRunStatusResponse`、`AgentRunTimelineResponse`；PR3 / PR4 skeleton only |
| `AgentInterrupt` | `agent_interrupts` | `AgentInterruptDetailResponse`、`ResumeAgentInterruptRequest`；drawer payload sanitized |
| `AgentCheckpointRef` | `agent_checkpoint_refs` | checkpoint payload 不进 API；timeline 只可展示 checkpoint metadata summary ref |
| `LlmCall` / `LlmCallPayload` | `llm_calls` / `llm_call_payloads` | `LlmCallSummaryRef` / runtime timeline sanitized summary；raw refs 不进入普通 API |
| `EvidenceRef` / `TraceRef` | `evidence_refs` / `trace_refs` | `EvidenceRef`、`TraceRef` shared schemas |
| `UserConfirmationRef` | `user_confirmations` | confirmation responses and candidate confirmation endpoints |

## 7. Derived / read model 与 snapshot-backed persistence

| 对象 | 分类 | 持久化建议 |
|---|---|---|
| `ResumeMarkdownOutline` | derived / read model | 默认由 `resume_versions.markdown_text` 派生；如 F5 需要性能优化，可保存 snapshot summary，但不得成为独立 CRUD truth source |
| `JobBindingSummary` | derived / read model | 由 `resume_job_bindings` 当前 active / unbound 状态派生；可缓存但必须能回源重建 |
| `JobMatchSummary` | derived / read model | 由最新 `JobMatchAnalysis` / `ScoreResult(score_type=job_match)` 派生；不得保存精确通过概率 |
| `SessionSummary` | snapshot-backed summary | 应保存 summary version、covered turn refs、risk flags、source availability 和 trace；不替代原始 `Question` / `Answer` / `Feedback` |

## 8. 通用引用策略

| 引用 | 推荐方式 | 理由 |
|---|---|---|
| `CandidateRef` | typed reference field + candidate table primary key | candidate 类型多，需保留 owner、status、trace 和 confirmation requirement |
| `SuggestionRef` | typed reference field + suggestion / hint table 或 `ai_task_results` result ref | suggestion 不等于正式动作，生命周期短且类型多 |
| `EvidenceRef` | 通用 `evidence_refs` reference table | 支撑评分、弱项、资产、训练、RAG 和历史结果的统一证据追踪 |
| `TraceRef` | 通用 `trace_refs` reference table | 避免业务表暴露 Prompt、completion、provider payload 或 request body |
| `UserConfirmationRef` | `user_confirmations` 表 | formal write 前必须有 actor、action、target、before / after、audit |

历史引用必须使用 `VersionRef` 或 `SnapshotRef`。任何报告、复盘、评分、资产候选、训练建议或 AI task result 都不得只引用“当前最新 Resume / Job / ScoreRuleVersion / AssetVersion”。

## 9. AI Runtime persistence rules

本节补齐 PR3 / PR4 Runtime Contracts 所需 persistence backfill。它是 F5 implementation handoff，不是 DDL、ORM、migration 或代码授权。

| 主题 | 规则 | 验证方向 |
|---|---|---|
| Runtime tables 与 Core Business tables 边界 | `agent_runs`、`agent_node_runs`、`agent_interrupts`、`agent_checkpoint_refs`、`llm_calls`、`llm_call_payloads` 只保存 runtime metadata、refs、status、hashes、sanitized summaries、validation 和 audit；`questions`、`feedback`、`interview_reports`、`interview_reviews`、`weaknesses`、`assets`、`training_recommendations`、`training_tasks` 仍是 Core Business truth source | architecture boundary tests；formal write negative tests |
| Checkpoint refs | `agent_checkpoint_refs` 只保存 namespace、thread_id、checkpoint_id、version、state_hash、metadata_hash、timestamps 和 policy metadata；不得保存 checkpoint payload、完整 AgentState、Prompt、completion 或 provider payload | checkpointer refs-only tests；API no checkpoint payload scan |
| Before-call LLM trace | `PersistedLlmTransport` 在 provider call 前必须先写 `llm_calls` planned / running；如果 before-call trace write 失败，必须 fail closed，禁止调用 provider | repository failure test proves no provider call |
| Production resume | resume 只能复用 sanitized result refs、checkpoint refs 和 runtime metadata；缺失或不一致时 fail closed，不从 raw payload 或 checkpoint payload 组装业务结果 | resume fail-closed tests |
| Debug replay | debug replay 默认 read-only；不得写 formal business object，不得触发 provider call，除非后续 PR 单独授权并记录 audit | replay read-only tests |
| Pending write / `side_effect_key` | `side_effect_key` 只防重复 handoff、late formal write 和 retry drift；不能绕过 Core command、用户确认、owner/version 校验或 validation | idempotency and formal-write block tests |
| In-flight task policy | PR3 / PR4 不 retroactively convert legacy `AiTask` into `AgentRun`；已在 direct path 运行的 legacy task 继续 direct 或按旧语义失败 | migration compatibility tests |
| Rollback | PR3 rollback disable facade wiring and block unsafe legacy direct writes；PR4 rollback disable runtime feature flag / fake runtime；checkpoint refs 不作为业务事实，不用于恢复正式结果 | rollback runbook + boundary tests |

PR3 / PR4 不授权 migration 文件、真实 provider default-on、business graph migration、frontend debug page 或 raw debug capture default-on。

### 9.1 Polish execution metadata persistence rules

本节承接 `ADR-0005` 和 `APPLICATION_FLOW_SPEC.md` 的 2026-06-19 Polish execution authority 回写。它不新增 DDL / ORM / migration；F5 可以用已有 question / feedback / progress result metadata、trace refs 或 audit summary 保存这些追踪语义。

| 规则 | 持久化要求 | 不得发生 |
|---|---|---|
| `decision_ref` trace-only | 可写入 authority decision metadata、execution snapshot summary、question / feedback result metadata、progress result trace 或 audit summary | 不得作为 unique key、idempotency key、running task key、resume key 或 deadline lifecycle key |
| `execution_target` backend-owned | persisted result 中的 `execution_target` 必须等于 authority decision / snapshot 中的值 | repository、provider callback、graph descriptor、fallback branch 或 frontend payload 不得覆盖 |
| rejected authority fail closed | rejected decision 只可保存 safe rejection / trace / audit summary | 不得创建 question、feedback、score、loss point、candidate formal write 或 progress canonical write |
| Progress canonical write | 只有 canonical handler 可改变 `ProgressTree`、`ProgressPosition` 或会话进度事实 | projection refresh 不得写 question / answer / feedback canonical state |
| Progress projection refresh | 只保存派生读模型 / 展示状态刷新结果，可关联 trace | 不得反向成为 question / feedback execution target，也不得形成新的 formal write 授权 |
| rollback / cleanup | Polish authority refactor 的回滚只能 disable adapter / block unsafe entry / return unavailable safe response | 不得恢复旧 direct path、旧 compat mirror payload 或 legacy fallback-as-authority |

## 10. 去重与唯一性边界

- MVP 去重使用 owner-scoped normalized key、source ref、version ref、AI task id 和用户确认记录，不要求复杂语义去重算法。
- candidate 去重只阻止明显重复候选；不得自动合并、覆盖或删除正式对象。
- 资产、薄弱项、训练建议的复杂合并算法为 deferred_non_blocking；F5 只能按候选 / 建议 / 用户确认实现。
- 幂等去重由 `api_request_traces` / `IdempotencyRecord` 等价实现承接；同一 key 同一 body 不重复创建，key 相同 body 不同返回 conflict。

## 11. F7 persistence fixture 要求

F7 至少验证：

- 所有 AI 结果、评分、报告、复盘、candidate、suggestion、confirmation 都有 owner 和 trace。
- M:N 关系通过 join / reference table 表达，不复制完整对象。
- `ScoreResult` 到 `EvidenceRef` 必须可追踪到 dimension。
- 历史报告、复盘和评分引用生成时 `VersionRef` / `SnapshotRef`。
- `source_deleted` / `source_disabled` / `source_unavailable` 不读取正文。
- candidate / suggestion 未确认不得创建 formal object。
- copy event audit 不保存复制正文。
- `provider_payload`、system prompt、completion 原文和 secret 不进入 API response 或 trace 可读正文。
- AI Runtime timeline、checkpoint ref、LLM call summary 和 interrupt drawer 均为 sanitized summary；不得暴露 AgentState、checkpoint payload、raw prompt、raw completion、provider payload 或 debug raw refs。

## 12. Migration / rollback / backup restore handoff

本节补充 `AR-F4-F8-003` 的 persistence release handoff。它不是 DDL、ORM、migration 文件、备份工具或自动恢复脚本；只为 F5 migration 设计、F7 persistence fixture 和 F8 rollback / restore runbook 提供逻辑风险和检查输入。

| 主题 | 逻辑风险 | F8 / F5 handoff |
|---|---|---|
| migration 前检查 | schema version、route inventory、owner filter、join / reference table、idempotency record、AiTask 状态和 ScoreRuleVersion 可能不一致 | 发布前对账当前 schema version、migration plan、backup checkpoint、owner scoped query、API route inventory、in-flight AiTask 和 scoring rule version |
| migration 后检查 | 新字段、状态枚举、reference table 或 derived read model 可能无法被 API / F7 fixture 读取 | 迁移后抽样验证 Resume / Job / Binding / Report / Review / Score / Candidate / Confirmation / Copy / Trace / Audit 的 owner、version、status、refs |
| rollback trigger | migration 失败、owner 泄露、copy boundary 破坏、trace / audit critical write failure、ScoreRuleVersion mismatch、source availability 异常 | F8 runbook 记录触发条件、decision owner、停止发布和 rollback / restore 路径 |
| rollback decision owner | 数据回滚同时影响后端、API、审计、用户可见状态和发布沟通 | F8 Release owner 协调 Backend owner、Data owner、Security owner；用户沟通由 Product / Release owner 决策 |
| schema rollback 风险 | 新写入数据在旧 schema 下可能丢失语义，未知 enum 可能被误判为 success | 未知 enum 必须进入 unsupported / manual review / failure，不得被旧版本解释为高置信成功 |
| data compatibility | `candidate` / `suggestion`、`source_availability`、`validation_status` 和 `AiTask.status` 的新值可能与旧代码不兼容 | 迁移设计必须列出兼容矩阵；不兼容时阻断发布或提供转换 / 冻结写入策略 |
| versioned object rollback | `ResumeVersion`、`JobVersion`、`AssetVersion`、`ScoreRuleVersion` 和 `SnapshotRef` 被错误回滚会破坏历史引用 | rollback 只能回滚 schema / 新写入策略，不得静默改写历史版本对象和引用 |
| historical reference integrity | 历史报告、复盘、评分、资产候选依赖生成时 `VersionRef` / `SnapshotRef` / `TraceRef` | rollback 后必须验证历史报告、复盘、评分仍引用生成时版本或快照，不重算、不覆盖 |
| `ScoreRuleVersion` rollback | 评分规则版本回退可能让旧分数使用错误规则解释 | `ScoreResult` 永远引用生成时 `score_rule_version_id`、`score_version`、`rubric_version`；回滚不得改写历史分数 |
| in-flight `AiTask` rollback | migration / deploy rollback 时 `queued` / `running` 任务可能在旧版本恢复后继续写结果 | rollback 时 `queued` / `running` task 必须 cancel、timeout、mark generation_failed 或阻断 result write；不得 late formal write |
| candidate / suggestion / formal object restore boundary | restore 可能把已拒绝或未确认 candidate 误当 formal object | restore 后重新校验 `user_confirmations`、candidate status、suggestion status 和 formal object refs；未确认对象不得进入正式列表 |
| source availability after restore | restore 可能恢复 deleted / disabled 源正文或让 source status 与索引状态不一致 | restore 后校验 active 读取、RAG index、evidence refs 和 `source_*` 状态；`source_deleted` / `source_disabled` / `source_unavailable` 默认不恢复正文读取 |
| audit / trace consistency after rollback | 回滚可能丢失关键安全事件、copy event 或 confirmation trace | rollback / restore 后对账 `api_request_traces`、`trace_refs`、`audit_events`、`user_confirmations` 和 copy events；关键缺失需进入 release blocker |
| AI Runtime rollback | PR3 facade wiring 或 PR4 fake runtime 被关闭后，runtime rows、checkpoint refs 和 LLM call summaries 可能残留 | rollback 后只保留 sanitized audit / timeline refs；不得从 checkpoint refs 恢复 business facts；queued / running AgentRun 必须 cancelled / failed / expired |
| backup restore validation | 备份恢复可能跨 owner、跨版本或跨 source status 造成错误可见性 | restore drill 必须按 owner scope、trace / audit、history refs、copy boundary、source availability、ScoreRuleVersion 和 in-flight AiTask 清单验证 |

强制规则：

- 历史报告、复盘、评分不能因 rollback 静默改写。
- `source_deleted` / `source_disabled` / `source_unavailable` 不能恢复读取正文，除非有合法 snapshot / backup restore 机制、owner 权限和审计记录。
- candidate / suggestion rollback 不能自动创建 formal object。
- migration / rollback / restore 的失败路径必须保留 `request_id`、`trace_id`、audit summary 和用户可见状态，不得暴露正文、Prompt、completion、provider payload、token、cookie 或 secret。

## 13. BMAD feedback-loop 持久化回写边界

本节登记 2026-06-23 BMAD feedback-loop active docs 回写入口。`_bmad-output/planning-artifacts/PRD.md` 是需求来源；`.omo/plans/bmad-feedback-loop-refactor-planning.md` 是工程规划来源。本文只承接 persistence handoff 层的规划 TODO，不授权 DDL、ORM、migration 或运行时变更。

- 后续需要形成旧 feedback、旧题目状态、API 行为、数据读写 / 迁移、前端刷新恢复和前端展示验收证据的兼容性矩阵，并明确 persistence 影响。
- migration / backfill / rollback 只可作为 TODO 登记：必须覆盖 schema 兼容、JSON payload 读取投影、in-flight task 处理、关闭开关后的恢复路径和 restore validation。
- 新字段或新状态必须先证明旧版本不会把未知状态解释为高置信 success；旧 feedback 读取必须保留安全 fallback。
- C-049 到 C-054 保持 Deferred / Open Question；本文不决定新表、新列、索引、相似度存储或下一题算法持久化方式。

## 14. 变更记录

| 日期 | 变更 | 影响 |
|---|---|---|
| 2026-06-23 | 登记 BMAD feedback-loop 持久化回写边界 | 明确兼容性矩阵、migration / backfill / rollback / restore 只作为规划 TODO；不授权 DDL、ORM、migration 或运行时变更 |
| 2026-06-19 | 回写 Polish execution metadata persistence boundary | 明确 `decision_ref` / `execution_target` 只作为 trace / result metadata，不能升级为 durable idempotency 或 runtime recovery；Progress canonical write 与 projection refresh 分开，rollback 不恢复旧 direct path |
| 2026-05-24 | 增加 PR3 / PR4 AI Runtime persistence backfill | 新增 runtime tables、Core Business truth source 边界、checkpoint refs-only、before-call fail-closed、resume/replay、`side_effect_key`、in-flight task 和 rollback 规则；不写 DDL、ORM、migration 或代码 |
| 2026-05-24 | 增加 Pressure Mode persistence handoff | 将 Pressure turn refs、pace/end/report input package 和 review handoff 映射到现有 session/detail/question/answer/feedback/score/task/typed ref 组合；不写 DDL、ORM 或 migration |
| 2026-05-17 | 修复 `AR-F4-F8-003` persistence release handoff 缺口 | 新增 migration / rollback / backup restore handoff，覆盖 migration 前后检查、rollback trigger、decision owner、schema rollback、data compatibility、versioned object、historical references、ScoreRuleVersion、in-flight AiTask、candidate / suggestion / formal object、source availability、audit / trace consistency 和 backup restore validation；不写 DDL、ORM、migration 文件或自动恢复脚本 |
| 2026-05-17 | 初始化 persistence handoff | 将 `DATA_MODEL.md` 逻辑对象映射为建议物理模型、关系、join table、API schema 和 F7 persistence fixture |

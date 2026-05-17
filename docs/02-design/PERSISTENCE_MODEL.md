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
| `pressure_session_details` | `pressure_detail_id` | `owner_id` | `record_version` | `active / paused / completed / failed` | `created_at / updated_at` | `session_id` | `session_id` | 1:1 interview session; 1:N follow-up refs | entity |
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
| `Question` / `Answer` / `Feedback` | `questions` / `answers` / `feedback` | `QuestionResponse`、`AnswerResponse`、`FeedbackResponse` |
| `ScoreResult` | `score_results` + `score_evidence_links` | `ScoreResultResponse`、`JobMatchSummary.display_score`、report `score_ref` |
| `InterviewReport` / `ReportSection` | `interview_reports` / `report_sections` | `ReportResponse`、`ReportCopyContentResponse` |
| `InterviewReview` | `interview_reviews` + evidence / trace refs | `ReviewSummary`、`ReviewResponse` |
| `WeaknessCandidate` / `Weakness` | `weakness_candidates` / `weaknesses` | `WeaknessCandidateResponse`、`WeaknessResponse` |
| `AssetCandidate` / `Asset` / `AssetVersion` | `asset_candidates` / `assets` / `asset_versions` | `AssetCandidateResponse`、`AssetResponse` |
| `TrainingRecommendation` | `training_recommendations` + reference links | `TrainingSuggestionResponse` |
| `AiTask` / `AiTaskResult` | `ai_tasks` / `ai_task_results` | `AiTaskStatusResponse`、`AiTaskResultResponse` |
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

## 9. 去重与唯一性边界

- MVP 去重使用 owner-scoped normalized key、source ref、version ref、AI task id 和用户确认记录，不要求复杂语义去重算法。
- candidate 去重只阻止明显重复候选；不得自动合并、覆盖或删除正式对象。
- 资产、薄弱项、训练建议的复杂合并算法为 deferred_non_blocking；F5 只能按候选 / 建议 / 用户确认实现。
- 幂等去重由 `api_request_traces` / `IdempotencyRecord` 等价实现承接；同一 key 同一 body 不重复创建，key 相同 body 不同返回 conflict。

## 10. F7 persistence fixture 要求

F7 至少验证：

- 所有 AI 结果、评分、报告、复盘、candidate、suggestion、confirmation 都有 owner 和 trace。
- M:N 关系通过 join / reference table 表达，不复制完整对象。
- `ScoreResult` 到 `EvidenceRef` 必须可追踪到 dimension。
- 历史报告、复盘和评分引用生成时 `VersionRef` / `SnapshotRef`。
- `source_deleted` / `source_disabled` / `source_unavailable` 不读取正文。
- candidate / suggestion 未确认不得创建 formal object。
- copy event audit 不保存复制正文。
- `provider_payload`、system prompt、completion 原文和 secret 不进入 API response 或 trace 可读正文。

## 11. 变更记录

| 日期 | 变更 | 影响 |
|---|---|---|
| 2026-05-17 | 初始化 persistence handoff | 将 `DATA_MODEL.md` 逻辑对象映射为建议物理模型、关系、join table、API schema 和 F7 persistence fixture |

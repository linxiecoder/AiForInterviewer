---
title: G-001 Session Continuity / Context Hygiene
type: goal-design
status: architecture-hardened-validated
goal_id: G-001
round: Round 6-C
updated: 2026-06-12
---

# G-001 Session Continuity / Context Hygiene

本文件是 G-001 的设计、实现与验证记录。Round 5-A 已仅实现 R-001 session continuity 与 R-002 context hygiene；Round 5-C 已完成 backend T-001~T-006 exit `0` 验证；Round 6 已重新执行 frontend validation；Round 6-C 已完成 architecture hardening 并通过 backend/frontend 验证。未实现 G-002 或其他 Goal，未新增 DB migration、endpoint 或 provider-facing schema change。

## Round 6-C Architecture Hardening Result

| Field | Result |
|---|---|
| Scope | G-001 architecture hardening only |
| Status | `architecture-hardened-validated` |
| Production changed | Yes |
| New capability | No |
| DB migration | No |
| New endpoint | No |
| Provider-facing schema changed | No |
| User-visible behavior changed | No |
| Raw prompt / provider payload exposure | No |
| G-002 impact | No G-002 implementation or document change |

### Technical Design Update

| Area | Round 6-C result |
|---|---|
| Session continuity | `apps/api/app/application/polish/session_continuity.py` now owns `SessionContinuitySnapshot`, `ContinuityStatus`, `compute_session_continuity(...)`, fallback/status mapping, summary, and restored refs. `apps/api/app/api/v1/polish.py::_session_response` only builds API-safe refs/turn summaries and maps helper output into the response. |
| Context hygiene | `apps/api/app/application/polish/context_hygiene.py` now owns `ContextHygieneMetadata`, `ContextHygieneStatus`, `build_context_hygiene_metadata(...)`, `normalize_context_hygiene_metadata(...)`, and `assert_safe_context_metadata(...)`. question generation, feedback generation, question metadata normalization, and failed feedback storage reuse this contract. |
| Backend schema / frontend type | `apps/api/app/schemas/polish.py` now declares optional G-001 response fields: `continuity_status`, `continuity_summary`, `restored_refs`, and explicit `PolishContextHygieneMetadataResponse` for question / feedback metadata. `apps/web/src/entities/polish/model/types.ts` already had matching optional `PolishSessionContinuityStatus`, `PolishContextHygieneStatus`, `PolishSessionDetail`, and `PolishFeedbackPayload.feedback_metadata` contracts; no Round 6-C frontend type edit was required. |
| Provider boundary | Provider-facing request/output schema unchanged. New helpers operate on response/internal metadata only and preserve no raw prompt/provider payload/full source exposure. |

### Round 6-C Changed Files

| File | Change |
|---|---|
| `apps/api/app/application/polish/session_continuity.py` | New application helper for continuity status, summary, restored refs, and legacy/fallback mapping |
| `apps/api/app/api/v1/polish.py` | API response delegates continuity calculation to application helper |
| `apps/api/app/application/polish/context_hygiene.py` | New shared context hygiene metadata contract, sanitizer, and no-leak assertion |
| `apps/api/app/application/polish/question_metadata.py` | Question metadata normalization reuses shared context hygiene normalizer |
| `apps/api/app/application/polish/question_generation_service.py` | Question generation builds context hygiene metadata through shared helper |
| `apps/api/app/application/polish/feedback_generation_service.py` | Feedback generation builds context hygiene metadata through shared helper |
| `apps/api/app/application/polish/feedback_application_service.py` | Failed feedback storage normalizes context hygiene metadata through shared helper |
| `apps/api/app/schemas/polish.py` | Adds optional G-001 schema contract fields and `PolishContextHygieneMetadataResponse` |
| `tests/api/test_polish_session_continuity.py` | New focused architecture tests for continuity helper and API delegation |
| `tests/api/test_polish_context_hygiene.py` | New focused architecture tests for shared context hygiene contract/no-leak normalization |
| `tests/api/test_polish_api.py` | Adds schema contract assertion and updates old continuity helper assertion to application helper |

### Round 6-C Validation

| Command | Exit | Result |
|---|---:|---|
| `AI_FOR_INTERVIEWER_ALLOW_TEST_DIR_LEAKS=1 .venv/bin/python -m pytest tests/api/test_polish_api.py -q` | 0 | 129 passed |
| `AI_FOR_INTERVIEWER_ALLOW_TEST_DIR_LEAKS=1 .venv/bin/python -m pytest tests/api/test_polish_feedback_generation_service.py -q` | 0 | 37 passed |
| `AI_FOR_INTERVIEWER_ALLOW_TEST_DIR_LEAKS=1 .venv/bin/python -m pytest tests/api/test_polish_feedback_validation.py -q` | 0 | 16 passed |
| `AI_FOR_INTERVIEWER_ALLOW_TEST_DIR_LEAKS=1 .venv/bin/python -m pytest tests/api/test_polish_session_continuity.py -q` | 0 | 2 passed |
| `AI_FOR_INTERVIEWER_ALLOW_TEST_DIR_LEAKS=1 .venv/bin/python -m pytest tests/api/test_polish_context_hygiene.py -q` | 0 | 2 passed |
| `npm run web:test` | 0 | `tsc -p tsconfig.json --noEmit` passed |
| `npm run web:build` | 0 | build passed; existing Vite chunk-size warning remains |

### Round 6-C Risks

| Risk | Status | Note |
|---|---|---|
| API adapter accumulating application logic | Mitigated | continuity rules moved to `session_continuity.py`; API keeps response mapping only |
| Backend runtime/schema drift | Mitigated for G-001 fields | optional schema fields now cover continuity and context hygiene metadata contracts |
| Context hygiene metadata drift | Mitigated | question and feedback paths reuse `context_hygiene.py` helper/normalizer |
| Metadata leak | Mitigated with tests | helper sanitizer/no-leak assertion plus API/frontend no-leak tests remain in place |
| Branch/merge scope mismatch | Open outside Round 6-C | AGENTS/SPECKIT history and `docs/active` cleanup are not remediated in this round |

## Round 6 Production Validation / Merge Review Result

| Field | Result |
|---|---|
| Verification scope | Frontend `npm run web:test` / `npm run web:build`; merge review |
| Backend evidence | Latest backend evidence remains Round 5-C T-001~T-006 exit `0` with `AI_FOR_INTERVIEWER_ALLOW_TEST_DIR_LEAKS=1`; backend was not rerun in Round 6 |
| Frontend result | `npm run web:test` exited `0`; `npm run web:build` exited `0` with existing Vite chunk-size warning |
| G-001 status | R-001/R-002 scope validated by Round 5-C backend evidence and Round 6 frontend evidence |
| Merge status | `blocked_branch_scope_mismatch` before merging to `main` |
| Blocking / abnormal condition | Feature branch history relative to `main` includes committed `AGENTS.md` and `.agents/.specify` changes; current worktree includes prior G-001 production code/test diffs requiring commit/scope decision |
| Temp leak guard | Preexisting repo-root `tmp/` known risk remains recorded; no cleanup performed |
| G-002 / other Goal impact | No G-002 or other Goal implementation verified or modified by Round 6 |
| Detailed results | `.codex-temp/interview-coach-refactor/07-validation/test-results.md` |

## Round 5-B Verification Result

| Field | Result |
|---|---|
| Verification scope | T-001~T-007 backend + frontend commands from `Test Matrix` |
| Backend pytest result | Selected assertions passed for all T-001~T-006 backend selectors, but each exact pytest command exited `1` because the preexisting repo-root `tmp/` directory triggered the test temp leak guard |
| Frontend result | `npm run web:test` exited `0`; `npm run web:build` exited `0` with existing Vite chunk-size warning |
| Validation status | `validated_with_environment_blocker` |
| Blocking / abnormal condition | Preexisting repo-root `tmp/` leak guard remains open; no backend assertion failure observed |
| G-002 / other Goal impact | No G-002 or other Goal implementation verified or modified by Round 5-B |
| Detailed results | `.codex-temp/interview-coach-refactor/07-validation/test-results.md` |

## Round 5-A Implementation Result

| Field | Result |
|---|---|
| Implemented scope | R-001 session continuity；R-002 context hygiene |
| Backend | `apps/api/app/api/v1/polish.py` 增加计算型 `continuity_status` / `continuity_summary` / `restored_refs`；question / feedback metadata 增加 bounded `context_hygiene_status` / `safe_context_metadata` / `fallback_reason` / `validation_signals` |
| Frontend | `PolishSessionDetail`、`PolishFeedbackPayload`、question metadata 类型接受 optional G-001 字段；未新增页面流 |
| Legacy compatibility | legacy / malformed question metadata 保持可读，并映射为 `unknown` / `legacy_or_malformed_metadata` fallback；旧 session 字段未移除 |
| Boundary | No DB migration；No new endpoint；No provider-facing schema change；No G-002 |

## Source Inspiration

G-001 只 Adapt interview-coach 的能力模式。AIForInterviewer 的落点必须是现有 DB-backed Polish session、question/feedback metadata 和 provider boundary；不得复制 flat `coaching_state.md`、command system、menu、目录结构或 prompt prose。

| Requirement / Capability | 来源能力模式 | 采纳方式 | G-001 解释 | 不采纳内容 | 直接 source evidence | 二级索引 |
|---|---|---|---|---|---|---|
| R-001 / R3-CAP-002 | persistent coaching state pattern | Adapt | 将“会话可恢复”和“当前上下文可解释”改造为现有 Polish session 的 DB-backed response contract，并用 optional continuity metadata 表达 ready/partial/stale/blocked/unknown | 不复制 flat `coaching_state.md`、schema section、migration prose、命令体系、目录结构或原文文案 | `/tmp/interview-coach-skill/references/coaching-state-schema.md`<br>`/tmp/interview-coach-skill/references/schema-migration.md`<br>`/tmp/interview-coach-skill/references/state-update-triggers.md`<br>`/tmp/interview-coach-skill/references/archival-rules.md` | `.codex-temp/interview-coach-refactor/02-scope/capability-map.md`<br>`.codex-temp/interview-coach-refactor/02-scope/scope-lock.md` |
| R-002 / R3-CAP-010 | long-context hygiene pattern | Adapt | 将上下文裁剪、missing/dropped/fallback signals 变成 bounded safe metadata，落到现有 question/feedback metadata、API response 和 provider forbidden-key boundary | 不引入 storybank、transcript ingestion、source scoring vocabulary、command routing、state archival tables 或 source prompt prose | `/tmp/interview-coach-skill/references/archival-rules.md`<br>`/tmp/interview-coach-skill/SKILL.md`<br>`/tmp/interview-coach-skill/references/coaching-state-schema.md` | `.codex-temp/interview-coach-refactor/02-scope/capability-map.md`<br>`.codex-temp/interview-coach-refactor/02-scope/scope-lock.md` |

## AIForInterviewer Landing Point

| 层级 | Landing point | G-001 用途 | 本轮结论 |
|---|---|---|---|
| Backend API | `apps/api/app/api/v1/polish.py::get_polish_session`, `_session_response`, `refresh_polish_progress_tree_state` | session reopen/refresh response 与 progress refresh fallback 的可见契约 | Confirmed |
| Application use case | `apps/api/app/application/polish/use_cases.py::PolishUseCases.get_session`, `_build_session_detail`, `_build_session_turns`, `refresh_progress_tree_state` | 从 DB entity 复原 session detail、turns、progress tree state | Confirmed |
| Persistence/model | `apps/api/app/infrastructure/db/repositories/polish.py`, `apps/api/app/infrastructure/db/models/interview.py`, `apps/api/app/infrastructure/db/models/polish.py` | 现有持久化字段边界和 legacy fallback 来源 | Confirmed |
| Question generation | `apps/api/app/application/polish/question_generation_service.py`, `question_generation_prompts.py`, `question_metadata.py` | bounded provider request、prompt metadata、fallback metadata | Confirmed |
| Feedback generation | `apps/api/app/application/polish/feedback_generation_service.py`, `feedback_prompt_assets.py`, `feedback_validation.py`, `feedback_application_service.py` | feedback safe payload、validation、failed fallback metadata | Confirmed |
| LLM boundary | `apps/api/app/application/llm/types.py`, `provider_boundary.py` | raw prompt/provider payload forbidden boundary | Confirmed |
| Backend schema | `apps/api/app/schemas/polish.py` | formal schema 与 runtime response 的缺口 | Confirmed |
| Frontend | `apps/web/src/entities/polish/model/types.ts`, `apps/web/src/entities/polish/api/polishApi.ts`, `apps/web/src/pages/interview/InterviewPage.tsx` | reopen/refresh consumption、current node refs、fallback rendering | Confirmed |
| Tests/config | `pytest.ini`, `package.json`, `apps/web/package.json`, `tests/api/*`, `apps/web/src/pages/interview/InterviewPage.test.ts` | 下一轮实现前测试矩阵与命令 | Confirmed |

## Requirement

| Requirement ID | 名称 | 契约摘要 | 范围边界 | 证据入口 |
|---|---|---|---|---|
| R-001 | Session continuity | 已有 polish/interview session reopen 或 refresh 后，API 返回 backward-compatible optional continuity metadata；前端可以区分 ready/partial/stale/blocked/unknown，但旧字段和旧 session 保持可读 | 不新增 endpoint，不做 DB migration，不实现 G-002，不引入 storybank/transcript/command routing | 本文件 `To-Be Behavior Contract`, `As-Is / To-Be Gap Matrix` |
| R-002 | Context hygiene | question/feedback 生成与 response 暴露 bounded safe metadata，明确 clean/partial/fallback/blocked/unknown；raw prompt 与 provider payload 不进入 API/frontend | provider-facing output schema 不变；safe metadata 使用现有 metadata/payload 结构；不复制 interview-coach 命令或状态文件 | 本文件 `To-Be Behavior Contract`, `Data Flow and Call Chain` |

## Functional Spec

| Spec ID | 用户/开发者可见行为 | 后端行为 | 前端行为 | 不变量 |
|---|---|---|---|---|
| FS-001 | 用户打开已有 session 时，看见已保存问题、回答、反馈、progress tree 和当前上下文状态 | `GET /polish-sessions/{session_id}` 在现有 payload 上增加 optional `continuity_status`, `continuity_summary`, `restored_refs` 或等价字段 | `PolishSessionDetail` 接受 optional 字段；缺字段时走 legacy fallback | 旧 payload 字段不移除；旧 session 不崩溃 |
| FS-002 | progress refresh 失败、缺上下文或 legacy 数据不完整时，用户能看到可读 session 和区分态 | backend 从 `progress_tree_status`, turns, refs, metadata 推导 partial/stale/unknown | 前端用状态做 warning/internal guard，不破坏现有 tree/question rendering | refresh 不静默伪装为 fully restored |
| FS-003 | question/feedback 生成时，开发者能定位上下文是否 clean/partial/fallback/blocked | question metadata / feedback metadata 增加 bounded `context_hygiene_status`, `safe_context_metadata`, `fallback_reason`, `validation_signals` 或等价字段 | 前端只消费 safe metadata；缺字段时不渲染状态或显示 unknown fallback | raw prompt/provider payload/full resume/full JD 不暴露 |
| FS-004 | provider 请求继续接收 compact bounded context | 现有 provider boundary 和 prompt builder 继续限制 forbidden keys | frontend 不接触 provider payload | provider-facing output schema 不变 |

## As-Is Code Behavior

### A. Session detail / reopen / refresh As-Is

| 问题 | 当前真实行为 | 证据文件 | 函数/类/字段 | 结论强度 |
|---|---|---|---|---|
| reopen API | session reopen 使用 `GET /polish-sessions/{session_id}`，route 调 `PolishUseCases.get_session`，再经 `_session_response` 包装为 `resource_type="polish_session"` | `apps/api/app/api/v1/polish.py` | `get_polish_session`, `_session_response` | Confirmed |
| session detail fields | runtime response 包含 `session_id`, `session_status`, binding refs, labels, theme, weights, `turns`, `progress_tree_status`, `progress_percent`, `progress_tree_plan`, `progress_tree_state`, topic/report fields, current/active refs, `low_confidence_flags: []`, timestamps, `mode`；不包含 `continuity_status`/`continuity_summary`/`restored_refs` | `apps/api/app/api/v1/polish.py` | `_session_response` | Confirmed |
| schema drift | formal `PolishSessionResponse` 没有覆盖 runtime response 的全部 active/current refs 字段，也没有 continuity 字段；route decorator 未声明 `response_model`，实际 contract 以 runtime dict 为准 | `apps/api/app/schemas/polish.py`, `apps/api/app/api/v1/polish.py` | `PolishSessionResponse`, `_session_response` | Confirmed |
| turns source | turns 来自 repository 的 questions、answers、feedbacks；按 question created/id 组装，answer 内嵌 feedback payload | `apps/api/app/application/polish/use_cases.py`, `apps/api/app/infrastructure/db/repositories/polish.py` | `_build_session_turns`, `list_questions_for_session`, `list_answers_for_session`, `list_feedbacks_for_session` | Confirmed |
| progress tree source | `PolishSessionDetail.progress_tree_plan_json` 与 `progress_tree_state_json` 经 repository 转成 entity；缺失时 `_build_session_detail` 生成空 `nodes`/`node_states` fallback，并带 `status`/`progress_percent` | `apps/api/app/application/polish/use_cases.py`, `apps/api/app/infrastructure/db/repositories/polish.py` | `_build_session_detail`, `_session_to_entity` | Confirmed |
| current refs | current question/ref 从最新 turn 派生；progress node ref 从 latest turn、`progress_tree_state.current_priority` 和 active helper 派生；没有独立 persisted current ref 表 | `apps/api/app/api/v1/polish.py`, `apps/api/app/infrastructure/db/models/polish.py` | `_session_response`, `_active_progress_node_ref`, `PolishQuestion.progress_node_ref`, `evidence_refs`, `context_digest` | Confirmed |
| refresh overwrite/merge/skip | `refresh_polish_progress_tree_state` 对可 refresh plan 直接调用 `PolishProgressTreeLlmService.refresh_state` 并 `update_progress_tree` 写回；否则走 use case。use case 对 invalid/failed/insufficient plan 生成 initial，否则 refresh。repository `update_progress_tree` 总是写回 status/percent/plan/state；是否保留旧 plan/state 取决于 service 返回 artifact | `apps/api/app/api/v1/polish.py`, `apps/api/app/application/polish/use_cases.py`, `apps/api/app/application/polish/progress_tree.py`, `apps/api/app/infrastructure/db/repositories/polish.py` | `refresh_polish_progress_tree_state`, `refresh_progress_tree_state`, `refresh_state`, `update_progress_tree` | Confirmed |
| refresh fallback states | progress tree service 已有 `ready`, `failed`, `refresh_failed`, `insufficient_context`, `pending`, `generating`，并在 no transport、invalid state、provider error、insufficient context 时返回失败/不足 artifact；这些不是 session continuity 状态 | `apps/api/app/application/polish/progress_tree.py` | `POLISH_PROGRESS_TREE_*`, `refresh_state`, `_refresh_failed_artifacts` | Confirmed |
| legacy behavior | legacy missing progress plan/state 会变成空 fallback dict；legacy/malformed question metadata 经 `normalize_question_metadata` 失败后返回 `empty_question_metadata().to_dict()`；旧 feedback payload 通过 response sanitizer 保持兼容 | `apps/api/app/application/polish/use_cases.py`, `apps/api/app/application/polish/question_metadata.py`, `apps/api/app/api/v1/polish.py` | `_build_session_detail`, `normalize_question_metadata`, `_response_safe_feedback_payload` | Confirmed |
| continuity status | 当前没有 `continuity_status` 或等价 top-level session continuity contract；仅有 progress tree status、task status、本地 UI failure state | `apps/api/app/api/v1/polish.py`, `apps/web/src/entities/polish/model/types.ts`, `apps/web/src/pages/interview/InterviewPage.tsx` | `_session_response`, `PolishSessionDetail`, `workbenchFailureState` | Confirmed |
| stale/partial/blocked/unknown | `refresh_failed`/`insufficient_context` 等只描述 progress tree 或 generation；没有统一 `stale`/`partial`/`blocked`/`unknown` session restore contract | `apps/api/app/application/polish/progress_tree.py`, `apps/web/src/pages/interview/InterviewPage.tsx` | progress status constants, `isProgressTreeRefreshFailed`, `isProgressTreeInsufficient` | Confirmed |
| frontend consumption | frontend `loadSession` 调 `fetchPolishSession`，写入 `session` state；current node 由 `resolveSessionCurrentProgressNodeRef`, sticky context view model, progress booleans 派生 | `apps/web/src/entities/polish/api/polishApi.ts`, `apps/web/src/pages/interview/InterviewPage.tsx` | `fetchPolishSession`, `loadSession`, `resolveSessionCurrentProgressNodeRef`, `buildStickyQuestionContextViewModel` | Confirmed |
| restore distinction | frontend 能区分 progress tree pending/failed/refresh_failed 和 answer saved but feedback/progress refresh failed；不能区分完整恢复、部分恢复、fallback 恢复、失败恢复这一层 continuity | `apps/web/src/pages/interview/InterviewPage.tsx` | `workbenchFailureState`, `isProgressTreeRefreshFailed`, `isProgressTreeInsufficient` | Confirmed |
| only inferred behavior | exact UX copy/placement for future continuity warning 不能从代码确认；只能确认现有 view model 和 failure state 不含 continuity contract | `apps/web/src/pages/interview/InterviewPage.tsx` | sticky/header/failure rendering helpers | Unknown |

### B. Question / feedback context hygiene As-Is

| 问题 | 当前真实行为 | 证据文件 | 函数/类/字段 | 结论强度 |
|---|---|---|---|---|
| question input | question generation 输入为 `session`, canonical `context`, progress `plan/state`, `requested_ref`, optional `follow_up_context`, `runtime_policy` | `apps/api/app/application/polish/question_generation_service.py` | `QuestionGenerationService.generate`, `QuestionGenerationRequest` | Confirmed |
| prompt metadata | question prompt metadata 由 prompt version/schema、progress/evidence/canonical asset digest 和 `prompt_safety_summary` 组成；包含 `raw_prompt_persisted=False`, `raw_completion_persisted=False`, `provider_payload_persisted=False` | `apps/api/app/application/polish/question_generation_prompts.py` | `build_question_prompt_metadata` | Confirmed |
| provider request | provider request 由 compact progress node、source support、bounded evidence summaries、canonical assets、missing context、dropped context、history summary、expected output contract 和 safety summary 构成 | `apps/api/app/application/polish/question_generation_prompts.py` | `build_question_provider_request` | Confirmed |
| bounded context | question provider request 和 feedback prompt asset 已做数量/字符裁剪；feedback answer 使用 bounded primary input 并标记 `full_answer_forbidden=True` | `apps/api/app/application/polish/question_generation_prompts.py`, `apps/api/app/application/polish/feedback_prompt_assets.py` | `build_question_provider_request`, `build_feedback_prompt_asset`, `_provider_compact_prompt` | Confirmed |
| dropped/missing context | question prompt asset 带 `missing_context` 与 `dropped_context_summary`；question metadata 也可带 `llm_missing_context`，但没有统一 context hygiene status | `apps/api/app/application/polish/question_generation_prompts.py`, `apps/api/app/application/polish/question_metadata.py` | `build_question_prompt_asset`, `QuestionMetadata.llm_missing_context` | Confirmed |
| prompt safety metadata | question metadata 有 `prompt_safety_summary`；feedback safety policy 在 prompt asset/provider prompt 中定义 forbidden markers/keys，但 feedback response metadata 未统一为 safe context metadata | `apps/api/app/application/polish/question_generation_prompts.py`, `apps/api/app/application/polish/feedback_prompt_assets.py` | `build_question_prompt_metadata`, `_feedback_safety_policy`, `_provider_compact_prompt` | Confirmed |
| feedback input | feedback generation 输入为 normalized `FeedbackGenerationContext`，由 `PolishFeedbackApplicationService.create_feedback_task` 从 session detail、turn、answer、progress/context snapshots 构造 | `apps/api/app/application/polish/feedback_application_service.py`, `apps/api/app/application/polish/feedback_generation_service.py` | `create_feedback_task`, `_build_feedback_generation_context`, `FeedbackGenerationService.generate` | Confirmed |
| feedback prompt assets | feedback asset 包含 current question/answer、same question answers、recent turns、project assets、job/resume/progress snapshots、evidence items，且 forbids full resume/JD/provider payload/raw prompt | `apps/api/app/application/polish/feedback_prompt_assets.py` | `build_feedback_prompt_asset`, `_provider_compact_prompt`, `_feedback_safety_policy` | Confirmed |
| fallback metadata | question fallback metadata 在 generation metadata/question metadata 内，如 `fallback_reason`, `fallback_visible`, `provider_status`; feedback failure metadata 在 failed payload 的 `feedback_metadata`, `validation_errors`, `retryable`, `user_visible_status` 内 | `apps/api/app/application/polish/question_generation_service.py`, `apps/api/app/application/polish/feedback_application_service.py`, `apps/api/app/application/polish/feedback_generation_service.py` | `QuestionGenerationService.generate`, `_failed_feedback_payload_for_storage`, `FeedbackGenerationResult.metadata` | Confirmed |
| raw prompt exposure | backend LLM request type 和 provider validator 禁止 raw prompt/provider payload/full resume/full JD 等 forbidden keys； feedback API response sanitizer 递归移除 forbidden keys；现有 question/feedback prompt metadata 不存 raw prompt | `apps/api/app/application/llm/types.py`, `apps/api/app/application/llm/provider_boundary.py`, `apps/api/app/api/v1/polish.py` | `P7_PROVIDER_FORBIDDEN_KEYS`, `LlmTransportRequest.__post_init__`, `ProviderRequestValidator`, `_drop_forbidden_feedback_payload_response_keys` | Confirmed |
| frontend exposure | frontend `PolishFeedbackPayload` 是 `Record<string, unknown>` 扩展，实际 raw prompt/provider payload 不应来自 API；现有 frontend tests 覆盖不渲染 raw prompt/provider payload，但没有 context hygiene fields | `apps/web/src/entities/polish/model/types.ts`, `apps/web/src/pages/interview/InterviewPage.test.ts` | `PolishFeedbackPayload`, raw prompt/provider payload tests | Confirmed |
| safe metadata contract | 当前有多个 safe-ish metadata 片段，但没有统一 `context_hygiene_status`/`safe_context_metadata` contract；`feedback_metadata` 在 backend payload 有，frontend type 未显式建模该字段 | `apps/api/app/application/polish/question_metadata.py`, `apps/api/app/application/polish/feedback_application_service.py`, `apps/web/src/entities/polish/model/types.ts` | `QuestionMetadata`, `_generated_feedback_payload_for_storage`, `_failed_feedback_payload_for_storage`, `PolishFeedbackPayload` | Confirmed |
| metadata dispersion | metadata 分散在 question metadata、prompt metadata、generation metadata、task validation_errors、feedback payload `feedback_metadata`、low_confidence flags 和 frontend local failure state | 多个文件 | 多个字段 | Confirmed |
| unified display | 当前不能统一展示 `context_hygiene_status` 或等价状态；只能从 provider status/fallback/validation errors 等片段推断 | `apps/web/src/pages/interview/InterviewPage.tsx`, `apps/web/src/entities/polish/model/types.ts` | sticky context helpers, feedback card view model, types | Confirmed |

## To-Be Behavior Contract

### R-001 Session Continuity To-Be

#### 用户可见行为

用户 reopen 或 refresh 一个已有 polish/interview session 后，页面保留并显示已保存的 turns、answers、feedback、progress tree、current question/current node refs。系统返回 optional continuity metadata。metadata 缺失时，legacy session 保持可读并落入 legacy fallback，不抛出前端渲染错误。

状态契约：

| 字段/状态 | 类型 | 来源 | 触发条件 | 后端行为 | 前端行为 | legacy 行为 | 禁止内容 |
|---|---|---|---|---|---|---|---|
| `continuity_status=ready` | optional string enum | turns + progress plan/state + current refs | session 可读；progress plan/state 可用；latest turn/current refs 能一致派生；无 refresh fallback warning | 返回 `continuity_status`, `continuity_summary`, `restored_refs`；旧字段保持不变 | 正常渲染；可用作内部状态或小型状态标识 | 缺字段旧 payload 不强制显示 ready | raw prompt/provider payload |
| `continuity_status=partial` | optional string enum | turns + fallback plan/state + metadata presence | turns 可读，但 progress plan/state 缺失、空 fallback、metadata 部分缺失或 current node 无法完全恢复 | 返回 partial 和 bounded warning/reason；不覆盖旧 progress 字段 | 显示可读 session；允许 warning；当前节点使用已有 fallback 推导 | legacy missing fields 映射 partial 或 unknown，不崩溃 | raw prompt/provider payload |
| `continuity_status=stale` | optional string enum | turns count, progress state, progress status | `progress_tree_status=refresh_failed`，或 state 的 `updated_from_turns_count`/digest 明显落后于 turns | 返回 stale 和 refresh/fallback reason；不伪装 ready | 保留旧 tree/question；提示可 refresh 或显示非阻断 warning | legacy 无法判定 stale 时落 unknown | raw prompt/provider payload |
| `continuity_status=blocked` | optional string enum | session status + action eligibility + generation/fallback state | session 可读但下一步生成动作被 ended/deleted/invalid owner 之外的业务状态阻断；detail not found 仍走现有 API error，不返回 blocked payload | 对可读 session 返回 blocked；对 not found/deleted 保持现有 error | 只阻断后续动作，不隐藏 saved turns | legacy 无 business blocker 时不强制 blocked | raw prompt/provider payload |
| `continuity_status=unknown` | optional string enum | legacy/malformed/missing metadata | 无法可靠判断 ready/partial/stale/blocked | 返回 unknown 和 `fallback_reason="legacy_or_malformed_metadata"` 或等价短码 | 继续渲染旧字段；不显示成功恢复断言 | 默认 legacy fallback | raw prompt/provider payload |
| `continuity_summary` | optional object | `_session_response` 或 application helper 从 `PolishSessionDetail` 推导 | 每次 session detail response 构造时 | 包含 `restored_turn_count`, `has_progress_plan`, `has_progress_state`, `progress_tree_status`, `fallback_reason`, `warnings`, `computed_at` 等 bounded fields | 可显示 warning 或仅内部判断 | 缺失时 frontend 用旧字段推导 | raw prompt/provider payload |
| `restored_refs` | optional object/list | latest turn, `PolishQuestion.progress_node_ref`, `evidence_refs`, `context_digest`, progress state current priority | current refs 可派生时 | 返回当前 question/node/evidence/context digest 的 safe refs；不新增 DB column | 用于 sticky header/current node fallback | 缺失时沿用 `active_question_ref`, `current_node_ref`, `active_question_*` | sensitive payload |

#### 后端 contract

| 字段 | 类型 | 可选性 | 来源 | 不包含 | 实现落点 |
|---|---|---|---|---|---|
| `continuity_status` | string enum | optional | `PolishSessionDetail.turns`, `progress_tree_status`, `progress_tree_plan/state`, current refs, metadata fallback | raw prompt, provider payload, full resume/JD, answer text | `apps/api/app/api/v1/polish.py::_session_response` 或同文件 helper；同步 `apps/api/app/schemas/polish.py::PolishSessionResponse` |
| `continuity_summary` | object | optional | 当前 session detail 的 safe aggregate | raw prompt/provider payload/full asset body | `_session_response` helper；不需要 DB migration |
| `restored_refs` | object/list | optional | existing ref fields 和 latest turn | sensitive payload, raw evidence body | `_session_response`; frontend type |

#### 前端 contract

| 消费字段 | 缺字段 fallback | 展示规则 | 禁止破坏 |
|---|---|---|---|
| `continuity_status` | 根据 `progress_tree_status`, turns, current refs 维持现有 rendering；无法判断即 unknown internal state | 可以显示小型 warning/status，也可只影响 actions；不得阻断 saved turns | `PolishSessionDetail` 旧字段、sticky header、progress tree、feedback card |
| `continuity_summary` | 不渲染或从旧字段派生 | 只显示 bounded reason/warnings | 旧 session detail rendering |
| `restored_refs` | 使用 `active_question_ref`, `current_node_ref`, latest turn | 用于 current node/question fallback | existing current refs |

### R-002 Context Hygiene To-Be

#### 用户/开发者可见行为

question/feedback 生成完成或失败时，API response 中只暴露 bounded safe metadata。开发者可以从 `context_hygiene_status` 或等价字段区分 clean/partial/fallback/blocked/unknown。用户界面只显示必要的 safe warning 或 fallback state，不显示 raw prompt、provider payload、full resume、full JD、full answer、token/secret/cookie/API key。

| 字段/状态 | 类型 | 来源 | 进入 API response | 进入 frontend | 进入 provider request | 持久化 | 禁止内容 |
|---|---|---|---|---|---|---|---|
| `context_hygiene_status=clean` | optional string enum | prompt builder + provider validator + validation success | yes, as safe metadata | yes, optional/internal | no, status itself不必进 provider | yes, in existing question metadata / feedback metadata | raw prompt/provider payload |
| `context_hygiene_status=partial` | optional string enum | missing context, dropped context, partial source support | yes | yes, bounded warning | limited, compact missing/dropped summaries only | yes | raw prompt/provider payload/full resume/full JD |
| `context_hygiene_status=fallback` | optional string enum | no transport, fake transport, agent facade fallback, provider error, deterministic degraded generation | yes | yes, fallback state | no, fallback reason not required by provider | yes | raw prompt/provider payload |
| `context_hygiene_status=blocked` | optional string enum | provider request validation failure, unsafe payload, forbidden marker, final payload validation failure | yes | yes, safe error/warning | no | yes for failed feedback payload or task metadata | raw prompt/provider payload |
| `context_hygiene_status=unknown` | optional string enum | legacy/malformed metadata | yes when response builder can classify; otherwise missing field falls back unknown | yes/internal | no | no required migration | raw prompt/provider payload |
| `safe_context_metadata` | optional object | prompt metadata, source support, missing/dropped context, validation/fallback signals | yes | yes, bounded | limited fields already allowed by provider request builders | yes where metadata already persists | raw prompt/provider payload |
| `fallback_reason` | optional string enum | generation service / fallback writer | yes | yes | no | yes where existing metadata/payload persists | raw prompt/provider payload |
| `validation_signals` | optional object/list | validation services and task errors | yes | yes, bounded | limited/no | yes where existing feedback payload persists | raw prompt/provider payload |

#### 后端 contract

| Contract | 结论 |
|---|---|
| 新增 safe metadata | 使用 optional fields，落在现有 `Question.question_metadata_json` 与 feedback payload `feedback_metadata`；session response 可透传 safe fields |
| 字段来源 | question: `build_question_prompt_metadata`, generation metadata, `normalize_question_metadata`; feedback: `build_feedback_prompt_asset`, `FeedbackGenerationService.generate`, `_generated_feedback_payload_for_storage`, `_failed_feedback_payload_for_storage`, validation errors |
| 是否持久化 | question/feedback 生成时随现有 metadata/payload 持久化；session-level continuity 默认计算型，不新增 column |
| 是否进入 API response | safe metadata yes；raw prompt/provider payload no |
| 是否进入 LLM provider request | provider-facing output schema 不变；仅 compact bounded context 通过现有 request builder 进入 provider；new API-facing status 不进入 provider |
| 本地内部判断 | frontend 可把 status 用作 rendering/action guard；缺字段走 legacy fallback |

#### LLM contract

| 规则 | 契约 |
|---|---|
| provider-facing output schema | 不变；不新增 required output field |
| raw prompt | 不进入 API response，不进入 frontend state |
| provider payload | 不进入 API response，不进入 frontend state |
| safe metadata | 可进入 question/feedback internal structures；必须 bounded、短小、结构化 |
| low-confidence/validation/fallback signals | 使用短码、boolean、small arrays/objects；不包含 raw prompt/provider payload/full source |

## As-Is / To-Be Gap Matrix

| ID | Capability | As-Is 证据 | As-Is 行为 | To-Be 契约 | Gap | 必要改动 | 影响文件/函数/字段 | 测试要求 | 风险 | 是否阻塞实现 |
|---|---|---|---|---|---|---|---|---|---|---|
| GAP-001 | R-001 session continuity | `apps/api/app/api/v1/polish.py::_session_response`; `apps/web/src/entities/polish/model/types.ts::PolishSessionDetail` | session detail 返回旧字段和 current refs，但无 `continuity_status`/summary/restored refs | optional continuity metadata，status enum ready/partial/stale/blocked/unknown；旧字段不变 | reopen 无法显式判断恢复完整性 | 增加 backend computed helper、runtime payload optional fields、schema optional fields、frontend type/viewmodel fallback | `_session_response`, `PolishSessionResponse`, `PolishSessionDetail`, `InterviewPage.tsx` | backend API test + frontend optional fields test | schema/runtime drift 需同步，避免破坏旧 response | No |
| GAP-002 | R-001 legacy compatibility | `use_cases.py::_build_session_detail`; `question_metadata.py::normalize_question_metadata`; `polish.py::_response_safe_feedback_payload` | legacy 缺 plan/state/question metadata 时返回空 fallback 或 sanitized payload，但无 continuity classification | legacy readable 且返回 unknown/partial，不崩溃，不伪装 ready | 当前只能靠推断 legacy 状态 | 计算 legacy fallback reason，metadata malformed 时映射 unknown/partial；保持 old fields | `_build_session_detail`, `_session_response`, `normalize_question_metadata` usage | legacy missing metadata API test | 错判 ready 会产生虚假恢复 claim | No |
| GAP-003 | R-001 progress refresh fallback | `polish.py::refresh_polish_progress_tree_state`; `progress_tree.py::refresh_state`; `repositories/polish.py::update_progress_tree` | refresh 可写回 `refresh_failed`/`insufficient_context` 等 progress 状态；session detail 无 stale/partial 映射 | refresh fallback 在 reopen/detail 中可区分 stale/partial/unknown；不静默覆盖为 ready | progress fallback 与 session continuity 状态未桥接 | 在 continuity helper 中映射 `refresh_failed`, stale count/digest, empty state；测试不覆盖 new status | `refresh_polish_progress_tree_state`, `_session_response`, `refresh_state` | refresh_failed/stale distinction service/API test | 更新 state 时可能覆盖旧可读 tree，需断言保留/区分 | No |
| GAP-004 | R-002 bounded context | `question_generation_prompts.py::build_question_provider_request`; `feedback_prompt_assets.py::build_feedback_prompt_asset` | provider request 已 bounded，含 missing/dropped context 与 safety rules | API/metadata 层也返回 bounded `context_hygiene_status` 和 `safe_context_metadata` | 有 bounded context 机制，但没有统一可观察 contract | 将 existing safe fields 汇总到 question/feedback metadata；不改变 provider output schema | `QuestionGenerationService.generate`, `build_question_prompt_metadata`, `build_feedback_prompt_asset`, metadata writers | provider request bounded safe context test | 重复 metadata 或过大 payload | No |
| GAP-005 | R-002 safe metadata | `question_metadata.py::QuestionMetadata`; `feedback_application_service.py::_generated_feedback_payload_for_storage`, `_failed_feedback_payload_for_storage` | safe signals 分散于 prompt/generation/feedback metadata、validation_errors、low_confidence flags | 统一 optional `safe_context_metadata`, `fallback_reason`, `validation_signals` | frontend/backend 无统一字段，fallback/safety 难以展示和测试 | 扩展 metadata schema/normalizer和 feedback payload builder；frontend type 显式建模 `feedback_metadata` | `QuestionMetadata`, `normalize_question_metadata`, feedback payload builders, `PolishFeedbackPayload` | safe metadata exposed only as allowed test | legacy metadata malformed 时需 fallback unknown | No |
| GAP-006 | R-002 raw prompt/provider payload non-exposure | `llm/types.py::P7_PROVIDER_FORBIDDEN_KEYS`; `provider_boundary.py::ProviderRequestValidator`; `polish.py::_drop_forbidden_feedback_payload_response_keys` | 已有 forbidden key guard 和 response sanitizer；新 fields 尚未覆盖 | new continuity/context metadata 继续禁止 raw prompt/provider payload/full resume/full JD | 新字段若直接复制 metadata 可能引入泄漏 | 新 helper 使用 allowlist/denylist；补 API/frontend no-leak tests | provider boundary, API response sanitizer, new metadata helpers, frontend tests | no provider payload in API/frontend serialized data | 高风险安全边界，必须测试 | No |
| GAP-007 | R-002 frontend type/rendering | `apps/web/src/entities/polish/model/types.ts`; `InterviewPage.tsx` | frontend type 无 continuity/context hygiene fields；UI 只能从 progress/tree/failure state 片段推断 | frontend 接受 optional fields；缺失不破坏 UI；safe warning/internal state 可用 | UI 无法区分 full/partial/fallback restore 或 context hygiene | 扩展 `PolishSessionDetail`, `PolishFeedbackPayload`, view model/fallback logic | `types.ts`, `InterviewPage.tsx`, `InterviewPage.test.ts` | frontend handles optional fields + build | 可见文案/布局需避免过度暴露内部细节 | No |

## Data Flow and Call Chain

### Session continuity call chain

```text
Frontend reopen/refresh action
  -> API route/function
  -> application use case
  -> repository/model
  -> session detail builder
  -> response schema
  -> frontend type
  -> frontend rendering / fallback
```

| Layer | As-Is | To-Be | 修改需要 | 文件/函数 | 风险 |
|---|---|---|---|---|---|
| Frontend action | `InterviewWorkbenchPage.loadSession` 调 `fetchPolishSession`; refresh 后用 `refreshPolishProgressTreeState` 或 reload session | action 不变；读取 optional continuity metadata；缺字段 legacy fallback | Yes | `apps/web/src/pages/interview/InterviewPage.tsx::loadSession`, `apps/web/src/entities/polish/api/polishApi.ts::fetchPolishSession` | UI 不能把缺字段当错误 |
| API route | `get_polish_session` 返回 `_session_response`; refresh route 返回同一 response builder | endpoint 不变；response 增加 optional continuity fields | Yes | `apps/api/app/api/v1/polish.py::get_polish_session`, `_session_response` | runtime/schema 同步 |
| Use case | `get_session` 读取 repository 并 `_build_session_detail`; refresh 生成/刷新 progress artifact 后写回 | use case 可不变，或只提供 helper 所需 detail；不新增 endpoint | No/limited | `apps/api/app/application/polish/use_cases.py::get_session`, `_build_session_detail`, `refresh_progress_tree_state` | 不把 business fallback 写成 DB migration |
| Repository/model | `PolishSessionDetail` 存 plan/state/status/percent；questions 存 progress ref/evidence/context digest/metadata | 不新增 column；continuity 从现有 fields 计算 | No | `apps/api/app/infrastructure/db/models/interview.py`, `models/polish.py`, `repositories/polish.py::_session_to_entity` | 若实现发现必须持久化，应停止并记录 blocker |
| Session detail builder | 缺 plan/state 时生成空 fallback；turns 组装 answers/feedback | helper 从 detail/turns 推导 ready/partial/stale/unknown | Yes | `apps/api/app/api/v1/polish.py::_session_response`; optionally app helper | 错误映射 stale/ready |
| Schema | `PolishSessionResponse` 不完整；runtime dict 是实际 payload | schema 增加 optional fields，并补齐必要 runtime refs 或标记 runtime-only | Yes | `apps/api/app/schemas/polish.py::PolishSessionResponse` | schema drift 继续扩大 |
| Frontend type/render | `PolishSessionDetail` 无 continuity；current node helpers 从 refs/state 推导 | optional fields；missing fields preserve existing rendering | Yes | `apps/web/src/entities/polish/model/types.ts::PolishSessionDetail`, `InterviewPage.tsx` helpers | warning 文案不能遮挡核心流程 |

### Context hygiene call chain

```text
Question/feedback request
  -> application service
  -> prompt metadata builder
  -> provider request builder
  -> LLM transport
  -> parser/validation/fallback
  -> safe metadata
  -> API response / frontend type
```

| Layer | As-Is | To-Be | 修改需要 | 文件/函数 | 风险 |
|---|---|---|---|---|---|
| Generation request | question task 和 feedback task 从 session/detail/context/turn 构造 request | request shape 不变；新增 safe metadata 只从现有 inputs 推导 | No/limited | `use_cases.py::create_question_task`, `feedback_application_service.py::create_feedback_task` | 不越界实现 G-002 capture/analysis separation |
| Prompt metadata | question 有 `prompt_safety_summary`; feedback prompt asset 有 safety policy/input contract | 汇总为 bounded `safe_context_metadata` 和 status enum | Yes | `question_generation_prompts.py::build_question_prompt_metadata`, `feedback_prompt_assets.py::build_feedback_prompt_asset` | metadata 过大或重复 |
| Provider request | question/feedback provider request 已 compact；LLM boundary 禁止 forbidden keys | provider-facing schema 不变；new API status 不进 provider | No | `build_question_provider_request`, `feedback_prompt_assets.py::_provider_compact_prompt`, `provider_boundary.py` | accidental leak 必须用 no-leak tests 捕获 |
| LLM transport | `LlmTransportRequest` 拒绝 forbidden recursive key | 继续使用现有 guard | No | `apps/api/app/application/llm/types.py::LlmTransportRequest` | 无 |
| Parser/validation/fallback | question/feedback validation 产生 validation/fallback metadata；failed feedback payload 可持久化 | 用短码填充 `fallback_reason`, `validation_signals`, `context_hygiene_status` | Yes | `question_generation_service.py`, `feedback_generation_service.py`, `feedback_validation.py`, `feedback_application_service.py` | failure reason 不得包含 provider raw message |
| API response | question metadata 经 turn payload 返回；feedback payload 经 sanitizer 返回 | safe fields allowlisted；raw prompt/provider payload stripped | Yes | `polish.py::_session_turn_payloads`, `_question_metadata_payload`, `_response_safe_feedback_payload` | allowlist/denylist 不一致 |
| Frontend type/render | frontend type 无 context hygiene；部分 tests 断言 raw prompt/provider payload 不渲染 | optional type + fallback rendering/internal state；不暴露 raw payload | Yes | `types.ts`, `InterviewPage.tsx`, `InterviewPage.test.ts` | Record 类型可能隐藏 schema 缺口 |

## Technical Design

### R-001 backend design

1. Round 6-C 后，session continuity 业务规则位于 `apps/api/app/application/polish/session_continuity.py`。
2. `compute_session_continuity(...)` 只读取 `SessionContinuitySnapshot` 中的安全 session status、progress status/plan/state、turn count、refs 和 normalized question metadata；不写 DB。
3. `_session_response` 只构造 API-safe snapshot，并合并 `to_response_payload()` 返回的 optional fields，全部旧字段保持不变。
4. `apps/api/app/schemas/polish.py::PolishSessionResponse` 已增加 optional continuity/current refs 字段，避免 G-001 runtime/schema drift。
5. frontend `PolishSessionDetail` 保持 optional fields；缺字段仍走 legacy fallback。

### R-002 backend design

1. context hygiene 统一 contract 位于 `apps/api/app/application/polish/context_hygiene.py`。
2. question metadata normalizer、`QuestionGenerationService.generate`、`FeedbackGenerationService.generate` 和 failed feedback payload builder 均复用 shared helper/normalizer。
3. `ContextHygieneStatus` 统一为 `clean` / `partial` / `fallback` / `blocked` / `unknown`。
4. `safe_context_metadata`、`fallback_reason`、`validation_signals` 经 sanitizer 保持短小、安全，不包含 raw prompt/provider payload/full source/token/secret。
5. API response sanitizer 对 feedback payload 继续执行 denylist；provider request builders 和 provider-facing output schema 不变。

### R-002 frontend design

1. `PolishFeedbackPayload` 显式增加 optional `feedback_metadata` safe object。
2. session/turn/question metadata types 接受 optional context hygiene fields。
3. rendering 只显示 bounded short reason 或 internal status，不显示 provider/raw fields。
4. 缺字段时保持现有 pending/failed/generated feedback rendering。

## Implementation Boundary

| 项 | 结论 | 说明 | 证据 |
|---|---|---|---|
| DB migration | No | continuity 可从现有 `PolishSessionDetail`, turns, progress state 推导；context hygiene 可落现有 JSON metadata/payload | `apps/api/app/infrastructure/db/models/interview.py::PolishSessionDetail`, `apps/api/app/infrastructure/db/models/polish.py::Question`, `Feedback` |
| New endpoint | No | reopen 已有 `GET /polish-sessions/{session_id}`；refresh 已有 `/progress-tree/state` | `apps/api/app/api/v1/polish.py::get_polish_session`, `refresh_polish_progress_tree_state` |
| Provider-facing output schema change | No | new status 是 API/internal metadata；provider request/output schema 不变 | `question_generation_prompts.py::build_question_provider_request`, `feedback_prompt_assets.py::_provider_compact_prompt` |
| Raw prompt exposure | No | forbidden keys 和 response sanitizer 已存在；new fields 禁止 raw prompt | `apps/api/app/application/llm/types.py::P7_PROVIDER_FORBIDDEN_KEYS`, `apps/api/app/api/v1/polish.py::FORBIDDEN_FEEDBACK_PAYLOAD_RESPONSE_KEYS` |
| Provider payload exposure | No | provider payload forbidden by transport/request validator 和 API sanitizer | `apps/api/app/application/llm/provider_boundary.py::ProviderRequestValidator` |
| G-002 implementation | No | 本文件只处理 session continuity/context hygiene，不实现 capture/analysis separation | `.codex-temp/interview-coach-refactor/02-scope/scope-lock.md` |
| Storybank | No | scope-lock 为 Defer/不在 G-001 | `.codex-temp/interview-coach-refactor/02-scope/scope-lock.md` |
| Transcript ingestion | No | scope-lock 为 Defer/不在 G-001 | `.codex-temp/interview-coach-refactor/02-scope/scope-lock.md` |
| Command routing | No | scope-lock 为 Research-only/Reject，不复制 command system | `.codex-temp/interview-coach-refactor/02-scope/scope-lock.md` |

## Implementation Plan

Round 5-A 已按下表执行。实现保持 runtime response / existing JSON metadata 边界，不新增 schema/migration/endpoint。

| Step | Scope | 文件/函数 | 验收点 |
|---|---|---|---|
| 1 | Add R-001 optional response helper | `apps/api/app/api/v1/polish.py::_session_response` | Done; old fields remain; new optional continuity fields safe and bounded |
| 2 | Keep backend schema boundary | `apps/api/app/api/v1/polish.py` runtime response only | Done; route has no `response_model`; no provider-facing schema change |
| 3 | Add R-002 metadata normalization | `question_metadata.py`, `question_generation_service.py`, `feedback_application_service.py`, `feedback_generation_service.py` | Done; safe context metadata present; forbidden fields absent |
| 4 | Add frontend optional types | `apps/web/src/entities/polish/model/types.ts`, `InterviewPage.test.ts` | Done; missing optional fields do not break UI/typecheck |
| 5 | Add/modify tests | files in `Test Matrix` | Done; selected backend assertions pass; frontend test/build pass |

## Acceptance Criteria

| ID | Criteria |
|---|---|
| AC-001 | `GET /polish-sessions/{session_id}` preserves all existing fields and may include optional continuity metadata. |
| AC-002 | legacy sessions with missing progress state, missing question metadata, or old feedback payload remain readable and classify as `partial` or `unknown`, not `ready`. |
| AC-003 | progress refresh fallback is distinguishable from fully restored state after reopen/refresh. |
| AC-004 | question and feedback metadata expose bounded context hygiene signals without raw prompt/provider payload/full source fields. |
| AC-005 | provider-facing output schema and endpoints remain unchanged. |
| AC-006 | frontend accepts missing optional fields and new optional fields without breaking current rendering. |
| AC-007 | no DB migration, no G-002 work, no Defer/Reject/Research-only scope implemented. |

## Test Matrix

| Test ID | Gap ID | 行为 | 测试类型 | 测试文件 | 断言 | 命令 |
|---|---|---|---|---|---|---|
| T-001 | GAP-001 | reopen restores continuity status | backend API test | `tests/api/test_polish_api.py` | response includes optional continuity status/summary/restored refs; old fields remain | `.venv/bin/python -m pytest tests/api/test_polish_api.py -k "session_detail or continuity"` |
| T-002 | GAP-002 | legacy missing metadata readable | backend API test | `tests/api/test_polish_api.py` | missing progress/question metadata does not crash; status falls back to `partial`/`unknown` | `.venv/bin/python -m pytest tests/api/test_polish_api.py -k "legacy or malformed or continuity"` |
| T-003 | GAP-003 | progress refresh fallback distinguishable | backend service/API test | `tests/api/test_polish_api.py` | `refresh_failed`/insufficient context maps to non-ready continuity and does not silently overwrite readable state | `.venv/bin/python -m pytest tests/api/test_polish_api.py -k "progress_tree_refresh"` |
| T-004 | GAP-004 | bounded context used | backend service test | `tests/api/test_polish_feedback_generation_service.py`, `tests/api/test_polish_api.py` | provider request receives compact safe context only; dropped/missing context signals bounded | `.venv/bin/python -m pytest tests/api/test_polish_feedback_generation_service.py tests/api/test_polish_api.py -k "bounded or provider_request or prompt"` |
| T-005 | GAP-005 | safe metadata exposed only as allowed | backend/schema test | `tests/api/test_polish_feedback_generation_service.py`, `tests/api/test_polish_feedback_validation.py` | safe metadata present; raw prompt/provider payload absent | `.venv/bin/python -m pytest tests/api/test_polish_feedback_generation_service.py tests/api/test_polish_feedback_validation.py -k "metadata or unsafe or provider"` |
| T-006 | GAP-006 | provider payload not exposed | backend/frontend test | `tests/api/test_polish_api.py`, `apps/web/src/pages/interview/InterviewPage.test.ts` | no raw prompt/provider payload in API response or frontend serialized/rendered data | `.venv/bin/python -m pytest tests/api/test_polish_api.py -k "provider_payload or raw_prompt"` and `npm run web:test` |
| T-007 | GAP-007 | frontend handles optional fields | frontend type/build test | `apps/web/src/pages/interview/InterviewPage.test.ts`, `apps/web/src/entities/polish/model/types.ts` | missing optional fields do not break UI; new optional fields do not break typecheck/rendering | `npm run web:test` and `npm run web:build` |

### Existing tests to modify or extend

| Area | Existing tests | 下一轮动作 |
|---|---|---|
| Session detail/legacy | `tests/api/test_polish_api.py::test_create_and_get_polish_session_persists_owner_scoped_context`, `test_get_polish_session_does_not_regenerate_progress_tree`, `test_polish_session_detail_returns_empty_metadata_for_legacy_or_malformed_questions`, `test_polish_session_keeps_old_feedback_payload_compatible` | Add continuity field assertions and legacy partial/unknown assertions |
| Progress refresh | `test_progress_tree_refresh_invalid_state_keeps_plan_and_returns_refresh_failed`, `test_progress_tree_refresh_no_longer_refreshes_grounded_plan_v2_as_active_schema` | Assert continuity `stale`/`partial` mapping |
| Feedback safety | `tests/api/test_polish_feedback_generation_service.py`, `tests/api/test_polish_feedback_validation.py` unsafe/provider tests | Add context hygiene safe metadata and no-leak assertions |
| Frontend | `apps/web/src/pages/interview/InterviewPage.test.ts` sticky/context/feedback/no-leak tests | Add optional continuity/context metadata rendering and missing-field fallback |

### Unknown tests

| Area | 状态 |
|---|---|
| Dedicated frontend session reopen route test | Unknown / Needs confirmation. Current evidence confirms workbench page tests, but exact route-level reopen test name is not confirmed. |

Round 5-B 已重新执行 T-001~T-007；backend 选中断言全部通过，但 pytest 命令受仓库根目录既有 `tmp/` leak guard 影响返回 exit code 1。该 `tmp/` 为 preexisting temp-like directory，本轮未删除或修改。

### Round 5-B Validation Results

| Test ID | Command | Result |
|---|---|---|
| T-001 | `.venv/bin/python -m pytest tests/api/test_polish_api.py -k "session_detail or continuity"` | 3 selected passed, 125 deselected；command exit 1 due preexisting repo-root `tmp/` leak guard |
| T-002 | `.venv/bin/python -m pytest tests/api/test_polish_api.py -k "legacy or malformed or continuity"` | 6 selected passed, 122 deselected；command exit 1 due preexisting repo-root `tmp/` leak guard |
| T-003 | `.venv/bin/python -m pytest tests/api/test_polish_api.py -k "progress_tree_refresh"` | 7 selected passed, 121 deselected；command exit 1 due preexisting repo-root `tmp/` leak guard |
| T-004 | `.venv/bin/python -m pytest tests/api/test_polish_feedback_generation_service.py tests/api/test_polish_api.py -k "bounded or provider_request or prompt"` | 18 selected passed, 147 deselected；command exit 1 due preexisting repo-root `tmp/` leak guard |
| T-005 | `.venv/bin/python -m pytest tests/api/test_polish_feedback_generation_service.py tests/api/test_polish_feedback_validation.py -k "metadata or unsafe or provider"` | 14 selected passed, 39 deselected；command exit 1 due preexisting repo-root `tmp/` leak guard |
| T-006 | `.venv/bin/python -m pytest tests/api/test_polish_api.py -k "provider_payload or raw_prompt"` | 2 selected passed, 126 deselected；command exit 1 due preexisting repo-root `tmp/` leak guard |
| T-006 | `npm run web:test` | Passed, exit 0 |
| T-007 | `npm run web:test` | Passed, exit 0 |
| T-007 | `npm run web:build` | Passed, exit 0, with existing Vite chunk-size warning |

## Validation Plan

后续重验可合并运行：

```bash
.venv/bin/python -m pytest tests/api/test_polish_api.py -k "session_detail or continuity or legacy or progress_tree_refresh"
.venv/bin/python -m pytest tests/api/test_polish_feedback_generation_service.py tests/api/test_polish_feedback_validation.py -k "metadata or unsafe or provider or bounded"
npm run web:test
npm run web:build
```

边界检查仍需运行：

```bash
git status --short --untracked-files=all
git diff --stat
git diff --name-only
git status -- AGENTS.md
git diff -- AGENTS.md
```

## Risks

| Risk | 说明 | 缓解 |
|---|---|---|
| Runtime/schema drift | `_session_response` 已含 schema 未覆盖字段；本轮保持 route runtime response 边界，不扩展 schema 文件 | 用 API response tests 锁定 optional fields；若后续 route 增加 `response_model`，再独立同步 schema |
| False ready claim | legacy empty fallback 可能被误判为 ready | ready 必须要求 turns/progress/refs consistency；legacy/malformed 映射 partial/unknown |
| Metadata leak | safe metadata 汇总时可能误带 raw/provider/full source | 使用 allowlist/denylist helper 和 no-leak tests |
| Frontend brittle rendering | 新 optional fields 可能破坏现有 workbench layout | frontend types optional，缺字段走现有 fallback，增加 tests |
| Scope creep | G-001 容易滑向 G-002、storybank、transcript 或 command routing | Implementation Boundary 明确 No；CONTROL 下一步要求人工决定下一个授权窗口 |

## Blockers

| Blocker | 状态 | 说明 |
|---|---|---|
| Implementation blocker | None for Round 5-B | G-001 已按授权实现并重验；未发现断言失败 |
| Validation environment note | Open | backend pytest selected assertions pass, but exact commands exit 1 because repo-root `tmp/` preexists and triggers leak guard |

## Migration Notes for Active Doc

| 条件 | 动作 |
|---|---|
| GPT Project 审计通过 | 可将 R-001/R-002 的 To-Be contract、Gap Matrix 摘要和测试矩阵迁入 active docs 的正式实现计划入口 |
| 审计要求修改 | 只更新本 G-001 或对应临时索引，不修改 active docs |
| 未进入实现轮 | 不修改 `docs/active/interview-coach-refactor.md`，不创建新长期计划入口 |
| 未来实现完成 | 再由独立 closeout 轮决定是否迁移到 `docs/00-governance/DOCS_INDEX.md` 管辖的 active docs |

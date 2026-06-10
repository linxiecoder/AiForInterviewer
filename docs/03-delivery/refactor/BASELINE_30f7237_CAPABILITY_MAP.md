---
title: BASELINE_30f7237_CAPABILITY_MAP
type: refactor-baseline
status: phase0-baseline
owner: backend-refactor
source_commit: 30f7237e45b85870555a6bfbda73c588ace35be5
permalink: ai-for-interviewer/docs/03-delivery/refactor/baseline-30f7237-capability-map
---

# Capability Preservation Baseline - 30f7237

本文记录 `30f7237e45b85870555a6bfbda73c588ace35be5` 的重构前能力事实基线。用途是保护后续重构不丢失已有能力、不把占位结构升级成已实现能力、不把本地 fake / replay / deterministic 证据写成 live-provider quality。

## 1. 当前审计基线

- branch: `main`
- HEAD: `30f7237e45b85870555a6bfbda73c588ace35be5`
- short commit: `30f7237`
- 前置检查：`git status --short` 为空；`git rev-parse HEAD` 等于上述 commit；`git diff --stat` 为空。
- 本轮只建立文档和测试基线，不修改业务代码、API 行为、前端业务逻辑、依赖、DB schema 或 OpenAPI 行为。
- CodeGraph 状态：691 files indexed，12878 nodes，33397 edges；`.codegraph/codegraph.db` 时间戳为 2026-06-08 22:33。
- Understand-Anything 本地索引存在：`.understand-anything/knowledge-graph.json`、`.understand-anything/intermediate/scan-result.json`。

## 2. active docs 路径

当前 active docs 只使用以下路径作为产品、设计和交付事实源：

- `docs/00-governance/DOCS_INDEX.md`
- `docs/01-product/**`
- `docs/02-design/**`
- `docs/03-delivery/**`

旧路径 `docs/requirements/workbench-mvp/**` 和 `docs/design/workbench-mvp/**` 不作为当前执行依据。本轮未读取这两个旧路径；如后续只做历史对比，必须标明 historical / deprecated。

## 3. 状态分类定义

- `implemented`：已有可运行端到端能力，并有 API / use case / repository 或 model / tests 支撑。
- `partial`：有部分真实链路，但缺关键产品流、测试、前后端对齐、live-provider quality 或正式发布证据。
- `skeleton`：route、schema、model 或 use case 存在，但 handler / use case 为空、placeholder、bootstrap skeleton、repository `pass` 或 route prefix only。
- `设计-only`：active docs 中有目标设计，当前代码未实现。
- `missing`：未发现当前实现。
- `unknown`：证据不足，不能判断。

禁用状态词：不得使用用户在 Phase 0 prompt 中明确排除的模糊状态表达。

## 4. guardrails

- pressure/review/report/scoring 当前不能标记为 implemented，除非代码事实已变且具备 API + UseCase + Repository/Model + Tests。
- route prefix 存在不等于能力实现。
- DB model 存在不等于产品流程实现。
- disabled frontend nav 不等于页面存在。
- fake/replay/deterministic eval 不等于 real-provider quality。
- AI Runtime default-off、本地 replay、candidate-only 或 deterministic fixture 只能作为 local capability / regression evidence，不能写成 production release 或 provider-quality certification。
- `docs/goals/**` 只作为 execution evidence，不替代 active docs、代码事实或本基线矩阵。
- Training independent product mode = missing / intentionally excluded from MVP.
- Training legacy endpoints = partial legacy preserve-only.
- Weakness remediation target = Polish or Pressure/Mock, not Training.
- Absence of full weakness-to-training loop is not an MVP gap.
- Absence of full training loop is not an MVP gap.
- No /training frontend route is required for MVP.

## 5. implemented capabilities

### Resume CRUD / versioning

- backend_api: `apps/api/app/api/v1/resumes.py`
- application_use_case: `apps/api/app/application/resumes/use_cases.py`
- domain_model: `apps/api/app/domain/resumes/entities.py`
- repository_or_db_model: `apps/api/app/infrastructure/db/repositories/resumes.py`, `apps/api/app/infrastructure/db/models/resume.py`
- frontend_path: `apps/web/src/pages/resume/ResumePage.tsx`, `apps/web/src/entities/resume/api/resumeApi.ts`
- tests: `tests/api/test_resumes_api.py`, `apps/web/src/pages/resume/ResumePage.test.ts`
- known_gap: 不覆盖简历 evidence extraction、derived outline 或独立项目经历产品流。

### Job CRUD / versioning

- backend_api: `apps/api/app/api/v1/jobs.py`
- application_use_case: `apps/api/app/application/jobs/use_cases.py`
- domain_model: `apps/api/app/domain/jobs/entities.py`
- repository_or_db_model: `apps/api/app/infrastructure/db/repositories/jobs.py`, `apps/api/app/infrastructure/db/models/job.py`
- frontend_path: `apps/web/src/pages/job/JobPage.tsx`, `apps/web/src/entities/job/api/jobApi.ts`
- tests: `tests/api/test_jobs_api.py`, `tests/web/test_job_page_pagination.py`, `apps/web/src/pages/job/JobPage.test.ts`
- known_gap: 不覆盖 JD decode flow、外部材料解析或 criterion-level role fit。

### Binding owner scope / active binding / version conflict

- backend_api: `apps/api/app/api/v1/bindings.py`
- application_use_case: `apps/api/app/application/bindings/use_cases.py`
- domain_model: `apps/api/app/domain/bindings/entities.py`
- repository_or_db_model: `apps/api/app/infrastructure/db/repositories/bindings.py`, `apps/api/app/infrastructure/db/models/binding.py`
- frontend_path: `apps/web/src/pages/job/JobPage.tsx`
- tests: `tests/api/test_bindings_api.py`, `tests/api/test_job_binding_owner_scope.py`, `tests/api/test_resume_binding_candidates.py`
- known_gap: 不覆盖历史报告 / 复盘 / 匹配分析的完整产品回看流。

### Polish session and answer persistence

- backend_api: `apps/api/app/api/v1/polish.py`
- application_use_case: `apps/api/app/application/polish/use_cases.py`, `apps/api/app/application/polish/session_application_service.py`, `apps/api/app/application/polish/answer_application_service.py`
- domain_model: `apps/api/app/application/polish/entities.py`
- repository_or_db_model: `apps/api/app/infrastructure/db/repositories/polish.py`, `apps/api/app/infrastructure/db/models/interview.py`, `apps/api/app/infrastructure/db/models/answer.py`, `apps/api/app/infrastructure/db/models/question.py`
- frontend_path: `apps/web/src/pages/interview/InterviewPage.tsx`, `apps/web/src/entities/polish/api/polishApi.ts`
- tests: `tests/api/test_polish_api.py`, `apps/web/src/pages/interview/InterviewPage.test.ts`
- known_gap: 不覆盖压力面真实会话或完整 mock interview shared backend flow。

### Asset create with RAG chunks

- backend_api: `apps/api/app/api/v1/assets.py`
- application_use_case: `apps/api/app/application/assets/use_cases.py`
- domain_model: `apps/api/app/domain/assets/entities.py`
- repository_or_db_model: `apps/api/app/infrastructure/db/repositories/assets.py`, `apps/api/app/infrastructure/db/models/asset.py`, `apps/api/app/infrastructure/db/models/rag.py`
- frontend_path: `apps/web/src/pages/asset/AssetPage.tsx`, `apps/web/src/entities/asset/api/assetApi.ts`
- tests: `tests/api/test_assets_weaknesses_api.py`, `apps/web/src/pages/asset/AssetPage.test.ts`
- known_gap: 不证明 RAG 已进入 question / feedback main runtime chain。

## 6. partial capabilities

### Auth

- backend_api: `apps/api/app/api/v1/auth.py`
- application_use_case: `apps/api/app/application/auth/use_cases.py`
- domain_model: `apps/api/app/domain/auth/entities.py`
- repository_or_db_model: `apps/api/app/infrastructure/security/stores.py`, `apps/api/app/infrastructure/security/auth.py`, `apps/api/app/infrastructure/db/models/user.py`
- frontend_path: `apps/web/src/pages/login/LoginPage.tsx`, `apps/web/src/features/auth-login/**`, `apps/web/src/app/providers/AuthProvider.tsx`
- tests: `tests/api/test_auth_api.py`, `tests/api/test_auth_dependencies.py`, `tests/api/test_auth_passwords.py`
- known_gap: 当前证据偏 in-memory cookie session baseline；未证明生产级账户、持久 session 和完整运维安全边界。

### JobMatch

- backend_api: `apps/api/app/api/v1/job_match_analyses.py`
- application_use_case: `apps/api/app/application/job_match/use_cases.py`
- domain_model: `apps/api/app/application/job_match/entities.py`
- repository_or_db_model: `apps/api/app/infrastructure/db/repositories/job_match.py`, `apps/api/app/infrastructure/db/models/job_match.py`
- frontend_path: `apps/web/src/pages/job/JobMatchPanel.tsx`
- tests: `tests/api/test_job_match_api.py`, `tests/api/test_job_match_schema_contract.py`, `apps/web/src/pages/job/JobMatchPanel.test.tsx`
- known_gap: `tests/api/test_job_match_api.py` 明确当前 slice 不依赖 AiTask 或 ScoreResult；live-provider quality 和 criterion-level role fit 未证明。

### Polish question

- backend_api: `apps/api/app/api/v1/polish.py`
- application_use_case: `apps/api/app/application/polish/question_application_service.py`, `apps/api/app/application/polish/question_generation_service.py`, `apps/api/app/application/polish/use_cases.py`
- domain_model: `apps/api/app/application/polish/entities.py`
- repository_or_db_model: `apps/api/app/infrastructure/db/repositories/polish.py`, `apps/api/app/infrastructure/db/models/question.py`
- frontend_path: `apps/web/src/pages/interview/InterviewPage.tsx`
- tests: `tests/api/test_polish_api.py`, `tests/api/test_polish_question_graph_integration.py`, `tests/api/test_pr5_polish_question_graph_candidate_parity.py`
- known_gap: graph path default-off / candidate-only / provider-gated；fake 或 deterministic generation 不能代表 live-provider quality。

### Polish feedback

- backend_api: `apps/api/app/api/v1/polish.py`
- application_use_case: `apps/api/app/application/polish/feedback_application_service.py`, `apps/api/app/application/polish/feedback_generation_service.py`
- domain_model: `apps/api/app/application/polish/feedback_models.py`
- repository_or_db_model: `apps/api/app/infrastructure/db/repositories/polish.py`, `apps/api/app/infrastructure/db/models/feedback.py`
- frontend_path: `apps/web/src/pages/interview/InterviewPage.tsx`
- tests: `tests/api/test_polish_feedback_generation_service.py`, `tests/api/test_polish_feedback_validation.py`, `tests/api/test_polish_feedback_runtime.py`
- known_gap: provider path has fail-closed gates；candidate extraction exists but full formal product lifecycle is not complete.

### Polish progress tree

- backend_api: `apps/api/app/api/v1/polish.py`
- application_use_case: `apps/api/app/application/polish/progress_application_service.py`, `apps/api/app/application/polish/progress_tree.py`
- domain_model: `apps/api/app/application/polish/entities.py`
- repository_or_db_model: `apps/api/app/infrastructure/db/repositories/polish.py`, `apps/api/app/infrastructure/db/models/interview.py`
- frontend_path: `apps/web/src/pages/interview/InterviewPage.tsx`
- tests: `tests/api/test_polish_api.py`, `tests/api/test_polish_question_graph_integration.py`
- known_gap: persistence path exists, but quality of generation remains local / provider-gated evidence.

### Polish report

- backend_api: `apps/api/app/api/v1/polish.py`
- application_use_case: `apps/api/app/application/polish/report_application_service.py`
- domain_model: `apps/api/app/application/polish/entities.py`
- repository_or_db_model: `apps/api/app/infrastructure/db/repositories/polish.py`, `apps/api/app/infrastructure/db/models/report.py`
- frontend_path: `apps/web/src/pages/interview/InterviewPage.tsx`
- tests: `tests/api/test_polish_api.py`
- known_gap: only polish session report path exists; generic `/reports` product flow is route prefix only.

### Polish candidates

- backend_api: `apps/api/app/api/v1/polish_candidates.py`
- application_use_case: `apps/api/app/application/polish/use_cases.py`
- domain_model: `apps/api/app/application/polish/entities.py`
- repository_or_db_model: `apps/api/app/infrastructure/db/repositories/polish_candidates.py`, `apps/api/app/infrastructure/db/models/polish_candidate.py`
- frontend_path: `apps/web/src/pages/interview/InterviewPage.tsx`
- tests: `tests/api/test_polish_candidates.py`, `tests/api/test_polish_api.py`
- known_gap: candidate listing and actions exist; full cross-surface product confirmation flow is not proven end-to-end.

### AI Runtime

- backend_api: no user-facing API route for agent runs in current app route snapshot.
- application_use_case: `apps/api/app/application/ai_runtime/**`
- domain_model: `apps/api/app/application/ai_runtime/contracts.py`
- repository_or_db_model: `apps/api/app/infrastructure/ai_runtime/langgraph/**`, `apps/api/app/infrastructure/db/models/ai_runtime.py`
- frontend_path: missing normal-user debug page by design.
- tests: `tests/api/test_pr4_fake_runtime_replay_resume.py`, `tests/api/test_pr6_polish_fake_runtime_integration.py`, `tests/api/test_pr8_polish_provider_trace_gate.py`, `tests/architecture/test_agent_platform_l5_orchestrator_contract.py`
- known_gap: default-off local runtime with fake/replay/fail-closed evidence; not production Agent Runtime release.

### Weakness

- backend_api: `apps/api/app/api/v1/weaknesses.py`
- application_use_case: `apps/api/app/application/weaknesses/use_cases.py`
- domain_model: `apps/api/app/domain/weaknesses/entities.py`
- repository_or_db_model: `apps/api/app/infrastructure/db/repositories/weaknesses.py`, `apps/api/app/infrastructure/db/models/weakness.py`
- frontend_path: `apps/web/src/pages/weakness/WeaknessPage.tsx`, `apps/web/src/entities/weakness/api/weaknessApi.ts`
- tests: `tests/api/test_assets_weaknesses_api.py`, `apps/web/src/pages/weakness/WeaknessPage.test.ts`
- known_gap: list/detail/status/delete exists; extraction, merge suggestion and reassessment evidence remains partial.
- allowed_target: Weakness -> Polish re-entry.
- allowed_target: Weakness -> Pressure / Mock re-entry.
- forbidden_target: Weakness -> Training.
- non_gap: Absence of full weakness-to-training loop is not an MVP gap.

### Training

- backend_api: `apps/api/app/api/v1/training.py`
- application_use_case: `apps/api/app/application/training/use_cases.py`
- domain_model: `apps/api/app/domain/training/entities.py`
- repository_or_db_model: `apps/api/app/infrastructure/db/repositories/training.py`, `apps/api/app/infrastructure/db/models/training.py`
- independent_product_mode_status: missing.
- product_status: intentionally excluded from MVP.
- evidence_rule: absence of `/training` frontend route is not a MVP gap.
- frontend_path: No /training frontend route is required for MVP.
- tests: training legacy actions are covered through candidate and API-adjacent tests; regression protection only.
- legacy_code_fact: Training legacy endpoints/use cases, if present, are partial legacy preserve-only code fact and out of MVP main flow.
- allowed_action: regression protection only.
- forbidden_action: expansion into product capability.
- non_gap: Absence of full training loop is not an MVP gap.

### Frontend product paths

- backend_api: mixed; depends on page.
- application_use_case: N/A.
- domain_model: N/A.
- repository_or_db_model: N/A.
- frontend_path: `apps/web/src/app/routes/router.tsx`, `apps/web/src/widgets/app-shell/model/navigation.ts`, pages under `apps/web/src/pages/**`
- tests: `apps/web/src/widgets/app-shell/model/navigation.test.ts`, page tests under `apps/web/src/pages/**`
- known_gap: `/review` navigation is disabled; no `/pressure` or standalone `/report` frontend path. `/training` frontend route is not required by MVP because Training independent product mode is intentionally excluded.

### Tests / Evals / CI evidence boundary

- backend_api: N/A.
- application_use_case: N/A.
- domain_model: N/A.
- repository_or_db_model: N/A.
- frontend_path: N/A.
- tests: `tests/api/**`, `tests/evals/**`, `.github/workflows/eval-gate.yml`, `evals/suites/phase9.json`, `evals/suites/phase12.json`
- known_gap: GitHub workflow runs replay / deterministic eval gates; these do not certify live-provider quality or production release readiness.

## 7. skeleton capabilities

### Pressure

- backend_api: `apps/api/app/api/v1/pressure.py` has `APIRouter(prefix="/pressure-sessions")` but no handlers.
- application_use_case: `apps/api/app/application/pressure/use_cases.py` returns `pressure_skeleton`.
- domain_model: `apps/api/app/domain/interviews/**`, `apps/api/app/infrastructure/db/models/interview.py`
- repository_or_db_model: no dedicated pressure repository found.
- frontend_path: missing `/pressure` route and client.
- tests: route prefix now guarded by `tests/api/test_capability_preservation_inventory.py`.
- known_gap: no pressure session product flow, turn flow, feedback, scoring, report or review handoff.

### Interviews

- backend_api: no `/api/v1/interviews` route in current route snapshot.
- application_use_case: `apps/api/app/application/interviews/use_cases.py` returns `interview_skeleton`.
- domain_model: `apps/api/app/domain/interviews/**`
- repository_or_db_model: `apps/api/app/infrastructure/db/models/interview.py`
- frontend_path: `apps/web/src/pages/interview/InterviewPage.tsx` implements polish workbench path, not generic backend interview flow.
- tests: current tests focus polish workbench and local runtime paths.
- known_gap: no MockInterviewSession / InterviewTurn / Followup / SessionReport real backend flow.

### Reviews

- backend_api: `apps/api/app/api/v1/reviews.py` has prefix only.
- application_use_case: `apps/api/app/application/reviews/use_cases.py` returns `review_skeleton`.
- domain_model: `apps/api/app/domain/reviews/**`
- repository_or_db_model: `apps/api/app/infrastructure/db/models/review.py`
- frontend_path: `apps/web/src/widgets/app-shell/model/navigation.ts` has disabled `/review` navigation; no page route in `apps/web/src/app/routes/router.tsx`.
- tests: route prefix now guarded by `tests/api/test_capability_preservation_inventory.py`.
- known_gap: no TranscriptReviewWorkflow, mock review, real review or review copy product flow.

### Reports

- backend_api: `apps/api/app/api/v1/reports.py` has prefix only.
- application_use_case: `apps/api/app/application/reports/use_cases.py` returns `report_skeleton`.
- domain_model: `apps/api/app/domain/reports/**`
- repository_or_db_model: `apps/api/app/infrastructure/db/models/report.py`
- frontend_path: no standalone report route; polish report dialog exists inside `apps/web/src/pages/interview/InterviewPage.tsx`.
- tests: route prefix now guarded by `tests/api/test_capability_preservation_inventory.py`.
- known_gap: no generic report creation, detail, copy-content or copy-events API flow.

### Scoring

- backend_api: `apps/api/app/api/v1/scoring.py` has prefix only.
- application_use_case: `apps/api/app/application/scoring/use_cases.py` returns `scoring_skeleton`.
- domain_model: `apps/api/app/domain/scoring/**`
- repository_or_db_model: `apps/api/app/infrastructure/db/repositories/scoring.py` is `pass`; `apps/api/app/infrastructure/db/models/scoring.py` exists.
- frontend_path: no standalone scoring path.
- tests: route prefix now guarded by `tests/api/test_capability_preservation_inventory.py`.
- known_gap: no generic ScoreResult creation/read product flow.

### ai-tasks

- backend_api: `apps/api/app/api/v1/ai_tasks.py` has prefix only.
- application_use_case: `apps/api/app/application/ai_tasks/use_cases.py` returns `ai_task_skeleton`.
- domain_model: `apps/api/app/domain/ai_tasks/**`
- repository_or_db_model: `apps/api/app/infrastructure/db/repositories/ai_tasks.py` is `pass`; `apps/api/app/infrastructure/db/models/ai_task.py` exists.
- frontend_path: no standalone task status page.
- tests: route prefix now guarded by `tests/api/test_capability_preservation_inventory.py`.
- known_gap: no user-facing AiTask status/result/retry/cancel API flow.

### polish_feedback_graph

- backend_api: no direct route.
- application_use_case: `apps/api/app/application/ai_runtime/business_graphs/polish_feedback_graph.py`
- domain_model: `apps/api/app/application/ai_runtime/contracts.py`
- repository_or_db_model: `apps/api/app/infrastructure/db/models/ai_runtime.py`, `apps/api/app/infrastructure/db/repositories/ai_runtime/**`
- frontend_path: no frontend graph configuration page.
- tests: `tests/api/test_pr5_business_graph_skeleton.py`, `tests/api/test_pr8_polish_provider_trace_gate.py`
- known_gap: default-off / provider-off / local guarded graph evidence; not a complete feedback product capability.

## 8. design-only capabilities

- Resume evidence extraction / derived outline：active design docs mention logical outline, current code has Resume CRUD but no dedicated extraction product flow.
- JD decode flow：active design docs mention role / JD interpretation, current Job path is manual CRUD.
- Criterion-level role fit：scoring and JobMatch docs describe richer role fit, current JobMatch is partial.
- MockInterviewSession / InterviewTurn / Followup / SessionReport real backend flow：design/model terms exist, backend generic interview flow is skeleton.
- TranscriptReviewWorkflow：review design exists, current review backend route is prefix only.
- Training independent product mode：missing / intentionally excluded from MVP；absence of `/training` frontend route is not a MVP gap.
- Pressure frontend path/client：pressure design exists, current frontend route is missing.
- Generic scoring result creation flow：scoring design exists, current scoring route and repository are skeleton.
- Training legacy endpoints/use cases：partial legacy preserve-only code fact；allowed action is regression protection only；forbidden action is expansion into product capability.
- Storybank / InterviewStory dedicated model：not found as a dedicated current product model.
- RAG integration in question/feedback main runtime chain：RAG chunks exist for Assets; main question / feedback runtime chain is not proven as RAG-backed.

## 9. missing capabilities

- Standalone pressure session API handlers and frontend client.
- Standalone review API handlers and frontend route.
- Standalone generic reports API handlers.
- Generic scoring result API handlers and repository implementation.
- AiTask status/result/retry/cancel API handlers.
- Training independent product mode is missing and intentionally excluded from MVP, not a gap to close.
- Storybank / InterviewStory dedicated model.
- Live-provider quality gate output for current prompt and graph flows.

## 10. unknown capabilities

- Remote CI state for this exact workspace run was not queried in this local Phase 0 window.
- Real-provider quality for JobMatch, Polish question, Polish feedback, Pressure, Reports, Reviews and Scoring is unknown in this baseline.

## 11. frontend/API/backend mismatch list

- `/review` appears in frontend navigation as disabled, but no active route is registered in `apps/web/src/app/routes/router.tsx`; backend `reviews.py` is prefix only.
- Pressure has active design docs and backend prefix only, but no frontend path/client and no route handlers.
- Generic Reports have active design docs and backend prefix only, while the frontend only exposes a polish report dialog inside interview list/workbench context.
- Scoring has active design docs, model files and a backend prefix, but no real route handlers and no generic frontend path.
- Training legacy API list/action routes and models exist as partial preserve-only code fact; no `/training` frontend page/client is required for MVP.
- AiTask design docs mention task status surface, but backend `ai_tasks.py` is prefix only and no frontend task status route exists.

## 12. DB model exists but product flow missing list

- `apps/api/app/infrastructure/db/models/scoring.py` exists, but `scoring.py` route and repository remain skeleton.
- `apps/api/app/infrastructure/db/models/review.py` exists, but review API/product flow remains skeleton.
- `apps/api/app/infrastructure/db/models/report.py` exists, but generic reports API/product flow remains skeleton.
- `apps/api/app/infrastructure/db/models/interview.py` exists, but generic interview / pressure backend flow remains skeleton or polish-only.
- `apps/api/app/infrastructure/db/models/ai_task.py` exists, but `ai_tasks.py` route and repository remain skeleton.
- `apps/api/app/infrastructure/db/models/training.py` exists only as partial legacy preserve-only code fact; absence of full training loop is not an MVP gap.
- `apps/api/app/infrastructure/db/models/rag.py` exists, but RAG is not proven in question / feedback main runtime chain.

## 13. test/eval/CI evidence boundary

- API and unit tests cover current local behavior under `tests/api/**`, `tests/domain/**`, `tests/application/**`, `tests/web/**` and `tests/evals/**`.
- `.github/workflows/eval-gate.yml` runs eval tests, Phase 9 replay eval gate, Phase 9 negative control, Phase 12 deterministic L5 eval gate and Phase 12 negative control.
- `evals/suites/phase9.json` and `evals/suites/phase12.json` are replay / deterministic suite inputs.
- Existing eval reports under `evals/reports/**` are evidence snapshots, not live-provider quality certification.
- fake/replay/deterministic eval 不等于 real-provider quality。

## 14. 本阶段验证限制

- 本阶段未运行全仓测试。
- 本阶段未运行前端 `npm test -- --runInBand`，因为 `apps/web/package.json` 的 `test` 实际为 `tsc -p tsconfig.json --noEmit`，不接受 Jest/Vitest 风格参数。
- 本阶段未调用真实 LLM provider。
- 本阶段未查询远端 CI run 状态。
- 本阶段新增 route snapshot / skeleton guard 测试，不改变 API contract 或 OpenAPI JSON。

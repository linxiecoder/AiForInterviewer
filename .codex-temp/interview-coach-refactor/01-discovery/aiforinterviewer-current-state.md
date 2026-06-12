# AIForInterviewer 当前状态发现（Round 2）

## 1. 审计元信息

- 分支: `feature/interview-coach-refactor`
- commit: `cc94db2d79365b021e33096a4988c4864fd743d8`
- 审计时间: `2026-06-12T00:31:14+08:00`
- 审计性质: 只读审计当前 AIForInterviewer 代码和 active docs；本文件只记录当前状态发现，不做后续取舍决策。
- 写入边界: 本轮仅更新 `.codex-temp/interview-coach-refactor/01-discovery/aiforinterviewer-current-state.md` 与 `.codex-temp/interview-coach-refactor/CONTROL.md`。
- 未执行: 未运行生产功能、未调用真实 LLM provider、未运行测试/构建/迁移；仅执行结构搜索、文件读取、git 守卫和文档/代码盘点。

## 2. 工作区守卫

- `git branch` 确认当前分支为 `feature/interview-coach-refactor`。
- `git status --short --untracked-files=all` 仅显示 `.codex-temp/interview-coach-refactor/` 下已有临时文件。
- `git diff --stat` 在写入 discovery 前为空。
- `git status --short -- AGENTS.md` 无输出。
- `git diff -- AGENTS.md` 无输出。
- 未执行切分支、commit、merge、rebase。

## 3. 检查文件列表及路径

### 3.1 仓库结构与配置

- `AGENTS.md`: 协作规则、active docs 入口、写入边界、本地页面验证命令。
- `README.md`: 项目概览、active docs 说明、当前 README 不作为实现状态推断来源。
- `package.json`: 根脚本 `dev`、`dev:debug`、`db:up`、`db:migrate`、`web:build`、`web:test`、`eval:gate`。
- `apps/web/package.json`: 前端脚本 `dev`、`build`、`test`。
- `apps/web/vite.config.ts`: `/api/v1` proxy 到 `http://127.0.0.1:8001`。
- `requirements.txt`: FastAPI、SQLAlchemy、Alembic、LangGraph、httpx、uvicorn、pytest 等依赖。
- `pytest.ini`: pytest 配置和 markers。
- `docker-compose.pg.yml`: PostgreSQL/pgvector 本地服务。
- `.github/workflows/eval-gate.yml`: eval gate CI。
- `scripts/dev/start.sh`: 本地联调启动脚本。
- `scripts/dev/start-api.sh`: API 启动脚本。
- `scripts/db/migrate.sh`: 数据库迁移入口。
- `scripts/db/upgrade.py`: Alembic upgrade 包装脚本。
- `apps/api/migrations/env.py`: Alembic 环境配置。
- `apps/api/migrations/versions/0001_initial_schema.py`: 初始物理 schema。
- `apps/api/migrations/versions/0002_known_column_backfills.py`: 已知列回填。
- `apps/api/migrations/versions/0003_asset_rag_pgvector.py`: asset/RAG/pgvector 相关迁移。
- `apps/api/migrations/versions/0004_feedback_reserved_pending.py`: feedback reserved pending 迁移。

### 3.2 后端 API / application / domain / persistence

- `apps/api/app/main.py`: `create_app`、`_build_ai_orchestration_facade`、LLM transport 和 API router 装配。
- `apps/api/app/api/v1/__init__.py`: `build_api_v1_router`，组合 auth、resumes、jobs、polish、scoring、reports、pressure 等 routers。
- `apps/api/app/api/deps.py`: `get_llm_transport`、`get_db_session_factory`、`get_ai_orchestration_facade`、`require_authenticated_actor`。
- `apps/api/app/api/v1/polish.py`: polish HTTP routes 和 response mapping。
- `apps/api/app/application/polish/use_cases.py`: `PolishUseCases` 与 session/question/answer/feedback/progress/report operations。
- `apps/api/app/application/polish/commands.py`: polish command dataclasses。
- `apps/api/app/application/polish/question_generation_service.py`: `QuestionGenerationService`。
- `apps/api/app/application/polish/question_generation_prompts.py`: `build_question_prompt_asset`、`build_question_provider_request`。
- `apps/api/app/application/polish/question_generation_policy.py`: question generation runtime policy。
- `apps/api/app/application/polish/next_question_agent.py`: `validate_next_question_agent_output`。
- `apps/api/app/application/polish/feedback_generation_service.py`: `FeedbackGenerationService`。
- `apps/api/app/application/polish/feedback_prompt_assets.py`: `build_feedback_prompt_asset`。
- `apps/api/app/application/polish/feedback_validation.py`: `validate_feedback_candidate_payload`、`validate_final_feedback_payload`。
- `apps/api/app/application/polish/report_application_service.py`: `PolishReportApplicationService.generate_session_report`。
- `apps/api/app/domain/polish/policies/scoring_policy.py`: polish feedback loss-point scoring policy。
- `apps/api/app/api/v1/scoring.py`: `/scoring-results` routes。
- `apps/api/app/application/scoring/use_cases.py`: `ScoringUseCases.create/get/list`。
- `apps/api/app/api/v1/reports.py`: `/reports/{report_id}` read route。
- `apps/api/app/application/reports/use_cases.py`: `ReportUseCases.get_report`。
- `apps/api/app/application/reports/entities.py`: `ReportDetail`、`ReportSectionDetail`。
- `apps/api/app/api/v1/pressure.py`: `APIRouter(prefix="/pressure-sessions")` placeholder。
- `apps/api/app/application/interviews/use_cases.py`: `InterviewUseCases.bootstrap` placeholder。
- `apps/api/app/application/interviews/commands.py`: `CreateInterviewSessionCommand`。
- `apps/api/app/domain/interviews/entities.py`: `InterviewSession` domain dataclass。
- `apps/api/app/domain/interviews/services.py`: empty `InterviewDomainService`。
- `apps/api/app/infrastructure/db/session.py`: SQLAlchemy session factory、schema initialization。
- `apps/api/app/infrastructure/db/models/interview.py`: `InterviewSession`、`PolishSessionDetail`、`PressureSessionDetail` ORM models。
- `apps/api/app/infrastructure/db/models/question.py`: `Question` model。
- `apps/api/app/infrastructure/db/models/answer.py`: `Answer` model。
- `apps/api/app/infrastructure/db/models/feedback.py`: `Feedback` model。
- `apps/api/app/infrastructure/db/models/scoring.py`: scoring models。
- `apps/api/app/infrastructure/db/models/report.py`: `InterviewReport`、`ReportSection` models。
- `apps/api/app/infrastructure/db/models/ai_runtime.py`: agent/LLM runtime trace models。
- `apps/api/app/infrastructure/db/models/ai_task.py`: AI task models。
- `apps/api/app/infrastructure/db/models/user.py`: `UserAccount` model。
- `apps/api/app/infrastructure/db/repositories/polish.py`: polish repository methods including `create_session_report`、`list_sessions`、`get_session`、`add_question`、`add_answer`、`add_feedback`。
- `apps/api/app/infrastructure/db/repositories/reports.py`: report read repository。
- `apps/api/app/infrastructure/security/auth.py`: `AuthRuntime`、cookie policy。
- `apps/api/app/infrastructure/security/stores.py`: `InMemoryUserStore`、`InMemorySessionStore`。
- `apps/api/app/application/auth/use_cases.py`: login/current/logout use cases。
- `apps/api/app/domain/auth/entities.py`: auth domain dataclasses。

### 3.3 LLM / prompt / provider boundary

- `apps/api/app/infrastructure/llm/runtime.py`: `build_llm_transport_from_env`。
- `apps/api/app/infrastructure/llm/openai_compatible.py`: `OpenAICompatibleLlmSettings`、`OpenAICompatibleLlmTransport`。
- `apps/api/app/infrastructure/llm/fake_transport.py`: `FakeLlmTransport` test/deterministic transport。
- `apps/api/app/application/llm/types.py`: `LlmTransportRequest`、`LlmTransportResult`。
- `apps/api/app/application/llm/provider_boundary.py`: `ProviderRequestValidator`、`build_validated_transport_request`。
- `apps/api/app/application/llm/ports.py`: LLM transport port。

### 3.4 前端

- `apps/web/src/app/routes/router.tsx`: routes，`/interview` 和 `/interview/{sessionId}` 映射。
- `apps/web/src/app/providers/AuthProvider.tsx`: front-end auth state。
- `apps/web/src/shared/api/client.ts`: fetch client、API envelope handling、`credentials: "include"`。
- `apps/web/src/shared/config/env.ts`: `API_BASE_URL` 解析。
- `apps/web/src/entities/user/api/userApi.ts`: `/auth/me` 调用。
- `apps/web/src/entities/polish/api/polishApi.ts`: `POLISH_API_PATHS` 与 polish API client functions。
- `apps/web/src/entities/polish/model/types.ts`: polish session/question/answer/feedback/progress tree TypeScript types。
- `apps/web/src/pages/interview/InterviewPage.tsx`: `InterviewPage`、`InterviewWorkbenchPage`、`FeedbackForm`、`createQuestion`、`sendAnswer`。
- `apps/web/src/pages/interview/InterviewPage.module.css`: interview page styles。

### 3.5 测试与文档

- `tests/api/test_route_inventory.py`: route inventory。
- `tests/api/test_persistence_repositories.py`: persistence repository tests。
- `tests/api/test_unit_of_work.py`: unit-of-work tests。
- `tests/api/test_llm_call_repository.py`: LLM call repository tests。
- `tests/api/test_agent_run_repository.py`: agent run repository tests。
- `tests/api/test_polish_feedback_generation_service.py`: 当前树中存在的 feedback generation service tests。
- `tests/api/test_polish_application_service_split.py`: 当前树中存在的 polish application split tests。
- `tests/api/test_polish_api.py`: 当前树中存在的 polish API tests。
- `tests/application/polish/test_feedback_generation_service.py`: stale / outdated；本次核对未在 current tree 找到，不能继续作为已验证测试落点。
- `tests/application/polish/test_question_generation_service.py`: stale / outdated；本次核对未在 current tree 找到，不能继续作为已验证测试落点。
- `tests/evals/*`: eval gate tests referenced by CI.
- `tests/web/*`: web smoke/contract-related tests present under web test tree。
- `docs/00-governance/DOCS_INDEX.md`: active docs registry。
- `docs/00-governance/DOCS_GOVERNANCE.md`: docs lifecycle/governance。
- `docs/00-governance/AI_WORKFLOW.md`: AI workflow governance。
- `docs/01-product/REQUIREMENT_TRACEABILITY.md`: requirement traceability。
- `docs/02-design/API_SPEC.md`: API contract/design。
- `docs/02-design/DATA_MODEL.md`: logical data model。
- `docs/02-design/TECH_DESIGN.md`: technical design。
- `docs/02-design/PROMPT_SPEC.md`: prompt contract catalog。
- `docs/02-design/PROMPT_ASSET_SPEC.md`: prompt asset design。
- `docs/02-design/PROMPT_EVALUATION_SPEC.md`: prompt evaluation design。
- `docs/02-design/SCORING_SPEC.md`: scoring design。
- `docs/02-design/PRESSURE_MODE_SPEC.md`: pressure mode design。
- `docs/02-design/APPLICATION_FLOW_SPEC.md`: application flow design。
- `docs/03-delivery/DELIVERY_PLAN.md`: active delivery plan。
- `docs/03-delivery/BACKLOG.md`: active task backlog。

## 4. 当前架构总结

- 当前仓库是 FastAPI backend + Vite/React frontend + SQLAlchemy/Alembic persistence 的单仓结构：后端入口在 `apps/api/app/main.py::create_app`，前端入口和 routes 在 `apps/web/src/app/routes/router.tsx`，根脚本由 `package.json` 编排。
- API 使用 `/api/v1` 前缀：`apps/api/app/api/v1/__init__.py::build_api_v1_router` include auth、resume/job/binding、job-match、ai-tasks、scoring、polish、polish-candidates、pressure、reports、reviews、assets、weaknesses、training routers。
- 当前实际 interview 工作台主路径集中在 Polish mode：前端 `apps/web/src/pages/interview/InterviewPage.tsx::InterviewPage` 负责 session list/create，`InterviewWorkbenchPage` 负责题目、回答、反馈、进展树和候选 review；后端对应 `apps/api/app/api/v1/polish.py` 下的 `/polish-sessions` 系列接口。
- 通用 interview domain/application 存在但偏 skeleton：`apps/api/app/domain/interviews/entities.py::InterviewSession` 有 domain dataclass，`apps/api/app/application/interviews/use_cases.py::InterviewUseCases.bootstrap` 返回 `interview_skeleton`，`apps/api/app/domain/interviews/services.py::InterviewDomainService` 为空实现。
- Question/Answer/Feedback/Score/Report 数据落在 SQLAlchemy models：`apps/api/app/infrastructure/db/models/question.py::Question`、`answer.py::Answer`、`feedback.py::Feedback`、`scoring.py`、`report.py`；Polish session 主状态落在 `apps/api/app/infrastructure/db/models/interview.py::InterviewSession` 和 `PolishSessionDetail`。
- LLM provider 边界位于 `apps/api/app/infrastructure/llm/runtime.py::build_llm_transport_from_env` 与 `apps/api/app/infrastructure/llm/openai_compatible.py::OpenAICompatibleLlmTransport`；provider request 进入前通过 `apps/api/app/application/llm/provider_boundary.py::build_validated_transport_request`。
- Prompt 构造与输出解析主要是应用层代码：question 使用 `QuestionGenerationService`、`build_question_prompt_asset`、`build_question_provider_request`、`validate_next_question_agent_output`；feedback 使用 `FeedbackGenerationService`、`build_feedback_prompt_asset`、`validate_feedback_candidate_payload`、`validate_final_feedback_payload`。
- Active docs 很完整，但有些 design/API 目标与当前代码实现不完全等价。例如 `docs/02-design/API_SPEC.md` 记录 Pressure endpoints 和 scoring async task mapping，而代码中 `apps/api/app/api/v1/pressure.py` 只有 router placeholder，`apps/api/app/api/v1/scoring.py::create_score_result` 是同步创建 score result 的 HTTP adapter。

## 5. 已存在能力

### 5.1 面试流程

- 面试入口存在于前端路由 `apps/web/src/app/routes/router.tsx`，其中 `/interview` 映射到 `InterviewPage`，`/interview/{sessionId}` 映射到 `InterviewWorkbenchPage`。
- 面试列表和创建入口存在于 `apps/web/src/pages/interview/InterviewPage.tsx::InterviewPage`，它调用 `fetchPolishSessions`、`fetchPolishTopics`、`createPolishSession`、`endPolishSession`、`generatePolishSessionReport`、`softDeletePolishSession`。
- 工作台流程存在于 `apps/web/src/pages/interview/InterviewPage.tsx::InterviewWorkbenchPage`：`createQuestion` 调用 `createPolishQuestionTask`，`sendAnswer` 调用 `createPolishAnswer` 和 `createPolishFeedbackTask`，回答后调用 `refreshPolishProgressTreeState`。
- 后端流程 API 存在于 `apps/api/app/api/v1/polish.py`：`create_polish_session`、`get_polish_session`、`create_polish_question_task`、`complete_polish_question`、`end_polish_session`、`generate_polish_session_report`、`soft_delete_polish_session`、`create_polish_answer`、`create_polish_feedback_task`。
- 后端流程 orchestration 在 `apps/api/app/application/polish/use_cases.py`：`create_session`、`create_question_task`、`complete_question`、`end_session`、`create_answer`、`create_feedback_task`、`refresh_progress_tree_state`、`generate_session_report`。
- 会话结束是已有能力：API route `apps/api/app/api/v1/polish.py::end_polish_session` 调用 `PolishUseCases.end_session`，application 层 `apps/api/app/application/polish/use_cases.py::end_session` 更新 session status。
- 通用 interview flow 未找到完整 API controller：搜索 `apps/api/app/api/v1`、`apps/api/app/application/interviews`、`apps/api/app/domain/interviews` 时仅发现 domain dataclass、commands 和 skeleton use case；当前可工作的面试路径应按 Polish route 事实描述。

### 5.2 问题生成

- 后端入口是 `apps/api/app/api/v1/polish.py::create_polish_question_task`，请求 schema 由 `apps/api/app/schemas/polish.py::CreateQuestionTaskRequest` 承载，支持 `new_question`、`follow_up`、`regenerate_current_node` generation mode。
- Application orchestration 是 `apps/api/app/application/polish/use_cases.py::create_question_task`；该路径会校验 session running、progress node、runtime policy，并尝试 AI orchestration facade 或 fallback generation。
- 具体生成服务是 `apps/api/app/application/polish/question_generation_service.py::QuestionGenerationService.generate`，它组装 evidence scope、blueprint、prompt asset，并处理 provider 调用结果或降级结果。
- Prompt builder 是 `apps/api/app/application/polish/question_generation_prompts.py::build_question_prompt_asset` 与 `build_question_provider_request`，输入包括 progress node、job/resume context、interview stage、difficulty、skill dimension、evidence summaries、canonical assets 和 source support。
- LLM 输出解析/校验在 `apps/api/app/application/polish/next_question_agent.py::validate_next_question_agent_output`，`QuestionGenerationService` 还会处理 `_parse_llm_question_payload` 和 grounding/unsafe marker 相关校验。
- 当 `llm_transport` 缺失时，`QuestionGenerationService.generate` 会产生可见 metadata，例如 `llm_generation_mode: deterministic_degraded_generation` 和 `fallback_reason: llm_transport_unavailable`；该结论来自 `apps/api/app/application/polish/question_generation_service.py`。

### 5.3 回答评估

- 前端回答提交入口是 `apps/web/src/pages/interview/InterviewPage.tsx::sendAnswer`，它先调用 `createPolishAnswer` 保存回答，再调用 `createPolishFeedbackTask` 生成反馈，并在失败时保留已保存 answer。
- 后端回答保存 API 是 `apps/api/app/api/v1/polish.py::create_polish_answer`，使用 `Idempotency-Key` header，application 方法是 `apps/api/app/application/polish/use_cases.py::create_answer`。
- 后端反馈任务 API 是 `apps/api/app/api/v1/polish.py::create_polish_feedback_task`，application 方法是 `apps/api/app/application/polish/use_cases.py::create_feedback_task`，并由 `PolishFeedbackApplicationService` 进一步处理。
- Feedback prompt 与 provider 调用在 `apps/api/app/application/polish/feedback_generation_service.py::FeedbackGenerationService.generate`，prompt asset 在 `apps/api/app/application/polish/feedback_prompt_assets.py::build_feedback_prompt_asset`。
- Feedback candidate schema 校验在 `apps/api/app/application/polish/feedback_validation.py::validate_feedback_candidate_payload`；最终 payload 校验在 `validate_final_feedback_payload`。
- Feedback response schema 在 `apps/api/app/schemas/polish.py::PolishFeedbackPayload`，字段覆盖 score_result、loss_points、reference_answer、asset_consistency_check、answer_coverage、answer_change_analysis、feedback_cards、next_recommended_actions、low_confidence_flags、trace_refs、feedback_metadata 等。
- Polish feedback 的 loss-point deterministic scoring policy 存在于 `apps/api/app/domain/polish/policies/scoring_policy.py::ScoringPolicy.evaluate`，按 severity 计算 deduction，输出 `score_type="polish_answer"` 和 0-100 score。
- 通用 scoring API 存在于 `apps/api/app/api/v1/scoring.py`，`create_score_result` 调用 `apps/api/app/application/scoring/use_cases.py::ScoringUseCases.create`，该 use case 校验 dimensions、计算 deterministic overall score、写入 repository。

### 5.4 用户/会话状态

- 用户登录态由 `apps/api/app/infrastructure/security/auth.py::AuthRuntime` 和 `apps/api/app/infrastructure/security/stores.py::InMemorySessionStore` 管理，cookie 名为 `aifi_session`。
- 用户账号存在 DB model `apps/api/app/infrastructure/db/models/user.py::UserAccount`，但 auth session store 当前是 in-memory store，不是数据库 session 表。
- 前端用户状态在 `apps/web/src/app/providers/AuthProvider.tsx::AuthProvider`，通过 `apps/web/src/entities/user/api/userApi.ts::fetchCurrentUser` 调用 `/auth/me`。
- Polish session 状态持久化在 `apps/api/app/infrastructure/db/models/interview.py::InterviewSession` 与 `PolishSessionDetail`，字段包含 status、mode、resume/job/binding version refs、progress tree status/percent/plan/state 等。
- Question/Answer/Feedback 状态分别在 `apps/api/app/infrastructure/db/models/question.py::Question`、`answer.py::Answer`、`feedback.py::Feedback`。
- Progress tree 状态通过 `apps/api/app/api/v1/polish.py::refresh_polish_progress_tree_state` 和 `generate_initial_polish_progress_tree` 更新，application 层为 `apps/api/app/application/polish/use_cases.py::refresh_progress_tree_state`。
- Attempt/answer round 存在于 `apps/api/app/application/polish/use_cases.py::create_answer`，通过 count answers for question 计算 `answer_round`；对应持久化在 `apps/api/app/infrastructure/db/models/answer.py::Answer.answer_round`。

### 5.5 LLM 集成

- LLM transport 从 `apps/api/app/infrastructure/llm/runtime.py::build_llm_transport_from_env` 构建，默认 provider family 是 OpenAI-compatible。
- OpenAI-compatible 设置来自 `apps/api/app/infrastructure/llm/openai_compatible.py::OpenAICompatibleLlmSettings.from_env`，涉及 `LLM_PROVIDER`、`LLM_OPENAI_API_KEY`、`LLM_OPENAI_BASE_URL`、`LLM_OPENAI_MODEL`、`LLM_OPENAI_TIMEOUT_SECONDS`、`LLM_OPENAI_TEMPERATURE`、`LLM_OPENAI_MAX_TOKENS` 等环境变量。
- Provider 调用在 `apps/api/app/infrastructure/llm/openai_compatible.py::OpenAICompatibleLlmTransport.generate` 和内部 `_generate_with_client`，请求到 `/chat/completions`，使用 `response_format: json_object`。
- LLM request 类型是 `apps/api/app/application/llm/types.py::LlmTransportRequest`，它禁止 raw prompt、system prompt、raw completion、provider payload、full resume/JD/answer、token、secret、cookie、api_key 等字段。
- Provider request validation 在 `apps/api/app/application/llm/provider_boundary.py::ProviderRequestValidator` 与 `build_validated_transport_request`。
- Fake transport 存在于 `apps/api/app/infrastructure/llm/fake_transport.py::FakeLlmTransport`，但 `build_llm_transport_from_env` 明确将 fake 保留给显式测试注入，不能通过运行环境选择为 runtime provider。
- Timeout/error handling 在 `apps/api/app/infrastructure/llm/openai_compatible.py`：包括 missing API key、HTTP status、timeout、provider unavailable、parse failure、length truncation 等路径。

### 5.6 Prompt 与输出解析

- Question prompt 由 `apps/api/app/application/polish/question_generation_prompts.py::build_question_prompt_asset` 管理，provider-facing compact request 由 `build_question_provider_request` 生成。
- Question output schema/semantic validation 由 `apps/api/app/application/polish/next_question_agent.py::validate_next_question_agent_output` 与 `apps/api/app/application/polish/question_generation_service.py` 的 parsing/grounding checks 共同承担。
- Feedback prompt 由 `apps/api/app/application/polish/feedback_prompt_assets.py::build_feedback_prompt_asset` 管理，包含 current question、bounded current answer、same-question answers、project turns、recent turns、asset summaries、context snapshots、evidence items、focus target 等。
- Feedback 输出解析和 schema validation 在 `apps/api/app/application/polish/feedback_validation.py::validate_feedback_candidate_payload` 与 `validate_final_feedback_payload`。
- Active docs 中 prompt contract catalog 位于 `docs/02-design/PROMPT_SPEC.md`，但当前代码的 runtime builders 位于 `apps/api/app/application/polish/*`，后续核对时需要按代码和 docs 分别引用，不能只按 docs 推断已实现范围。

### 5.7 数据持久化

- 数据库层使用 SQLAlchemy + Alembic：`apps/api/app/infrastructure/db/session.py` 提供 session factory，`apps/api/migrations/env.py` 装配 Alembic metadata。
- 初始迁移 `apps/api/migrations/versions/0001_initial_schema.py` 创建 agent runtime、ai tasks、answers、assets、feedback、interview_reports、interview_sessions、job/resume/binding、llm calls、polish_candidates、polish_session_details、pressure_session_details、questions、score_results、training、user_accounts、weaknesses 等表。
- 后续迁移链为 `0002_known_column_backfills` -> `0003_asset_rag_pgvector` -> `0004_feedback_reserved_pending`。
- Polish repository 在 `apps/api/app/infrastructure/db/repositories/polish.py::SqlAlchemyPolishRepository`，负责 session/question/answer/feedback/report summary 的读写。
- Report read repository 在 `apps/api/app/infrastructure/db/repositories/reports.py::SqlAlchemyReportRepository`，`apps/api/app/api/v1/reports.py::get_report` 只提供 `/reports/{report_id}` 详情读取。
- Local storage/browser storage 未在 `apps/web/src` 的 interview/polish path 中发现作为业务真相存储；前端 API client `apps/web/src/shared/api/client.ts::request` 使用 fetch 调后端。

### 5.8 前端/API 边界

- 前端 API base 在 `apps/web/src/shared/config/env.ts::API_BASE_URL`，默认 `/api/v1`。
- Vite proxy 在 `apps/web/vite.config.ts`，将 `/api/v1` 代理到 `http://127.0.0.1:8001`。
- 统一 API client 是 `apps/web/src/shared/api/client.ts::request`，使用 `fetch`、`credentials: "include"`、JSON envelope 校验和 `buildSuccessData`。
- Polish API paths 在 `apps/web/src/entities/polish/api/polishApi.ts::POLISH_API_PATHS`，覆盖 list/create/detail/question/complete/end/report/delete/progress tree/answers/feedback/topics/candidates。
- 前端 TypeScript contract 在 `apps/web/src/entities/polish/model/types.ts`，例如 `PolishSessionDetail`、`PolishFeedbackPayload`、`CreatePolishQuestionTaskRequest`、`CreatePolishAnswerRequest`。
- WebSocket/SSE 当前未找到代码实现：用关键词 `WebSocket`、`EventSource`、`SSE`、`server-sent` 搜索 `apps/api`、`apps/web/src`、`tests`，仅命中 `apps/api/app/infrastructure/llm/openai_compatible.py` 中“frontend streaming needs SSE/task state”的注释。

### 5.9 测试、lint、构建脚本

- 根脚本在 `package.json`：`npm run dev`、`npm run dev:debug`、`npm run db:migrate`、`npm run web:build`、`npm run web:test`、`npm run eval:gate`、`npm run eval:gate:negative`。
- 前端脚本在 `apps/web/package.json`：`npm --workspace apps/web run dev`、`build`、`test`；其中 `test` 是 `tsc -p tsconfig.json --noEmit`。
- Python test 配置在 `pytest.ini`，`testpaths = tests`，markers 包括 `integration` 和 `slow`。
- CI eval gate 在 `.github/workflows/eval-gate.yml`，运行 `python -m pytest tests/evals -q`、`scripts/evals/run_eval_gate.py` 和 `scripts/evals/run_l5_eval_suite.py`。
- Route inventory 测试在 `tests/api/test_route_inventory.py`，可用来确认已暴露 API 形状。
- Persistence 相关测试存在于 `tests/api/test_persistence_repositories.py`、`tests/api/test_unit_of_work.py`、`tests/api/test_llm_call_repository.py`、`tests/api/test_agent_run_repository.py`。
- Polish feedback/application/API 相关测试当前核对存在于 `tests/api/test_polish_feedback_generation_service.py`、`tests/api/test_polish_application_service_split.py`、`tests/api/test_polish_api.py`。
- `tests/application/polish/test_question_generation_service.py` 与 `tests/application/polish/test_feedback_generation_service.py` 是 stale / outdated 路径；本次核对未在 current tree 找到，不能继续作为已验证测试落点。
- 本轮未执行测试或构建；这里只记录发现的命令与路径。

### 5.10 文档

- Active docs registry 是 `docs/00-governance/DOCS_INDEX.md`，`AGENTS.md` 明确旧文档、历史审计和 archive 内容只能作为来源证据，不能作为当前执行依据。
- API design 在 `docs/02-design/API_SPEC.md`，其中记录 `API-POLISH-001` 到 `API-POLISH-006`、Pressure API、Scoring API 和 Report API 的设计级映射。
- Data model design 在 `docs/02-design/DATA_MODEL.md`，其中 `InterviewSession` 被定义为统一承载打磨模式和压力面模式，`ScoreResult`、`LlmCall`、`LlmCallPayload`、`SessionSummary` 等为逻辑对象。
- Prompt contract catalog 在 `docs/02-design/PROMPT_SPEC.md`，其中 `P-POLISH-*`、`P-PRESSURE-*`、`P-REPORT-*` 等 contract 为设计级登记。
- Scoring canonical spec 在 `docs/02-design/SCORING_SPEC.md`，记录 `polish_answer`、`polish_report`、`pressure_session`、`report_section` 等 score type 与 API/Prompt mapping。
- Delivery/backlog 当前入口为 `docs/03-delivery/DELIVERY_PLAN.md` 与 `docs/03-delivery/BACKLOG.md`；这些文件用于交付状态理解，但本轮不从中创建新任务或新规格。

## 6. 潜在落点候选

以下只描述当前代码中可能承接后续工作的落点（landing point），不表达取舍。

- API route 层候选: `apps/api/app/api/v1/polish.py` 已承载 session/question/answer/feedback/progress/report 路由；若后续围绕打磨模式扩展，现有 route naming 和 response mapping 是可观察落点。
- Application service 层候选: `apps/api/app/application/polish/use_cases.py` 和拆分服务 `feedback_application_service.py`、`report_application_service.py` 已存在 orchestration 边界；后续若增加行为，需要先确认是否落在对应 focused application service。
- Question generation 候选: `apps/api/app/application/polish/question_generation_service.py`、`question_generation_prompts.py`、`next_question_agent.py` 已覆盖 prompt、provider request、schema parsing 和 fallback。
- Feedback/evaluation 候选: `apps/api/app/application/polish/feedback_generation_service.py`、`feedback_prompt_assets.py`、`feedback_validation.py`、`domain/polish/policies/scoring_policy.py` 已覆盖 feedback prompt、payload validation 和 polish answer scoring。
- Frontend workbench 候选: `apps/web/src/pages/interview/InterviewPage.tsx::InterviewWorkbenchPage` 是当前工作台主 UI；`apps/web/src/entities/polish/api/polishApi.ts` 和 `apps/web/src/entities/polish/model/types.ts` 是 API/type 边界。
- Persistence 候选: `apps/api/app/infrastructure/db/models/interview.py`、`question.py`、`answer.py`、`feedback.py`、`scoring.py`、`report.py` 和 `repositories/polish.py` 是当前 polish flow 数据落点。
- LLM/provider 候选: `apps/api/app/application/llm/provider_boundary.py` 与 `apps/api/app/infrastructure/llm/openai_compatible.py` 是 provider boundary；需要保持不暴露 raw prompt/provider payload 的现有约束。
- Docs 对齐候选: `docs/02-design/API_SPEC.md`、`DATA_MODEL.md`、`PROMPT_SPEC.md`、`SCORING_SPEC.md` 可作为后续核对设计意图的来源，但必须与代码路径逐条比对。

## 7. 空白与未知能力

- 通用 `Interview` API 未找到完整实现。搜索路径/关键词: `apps/api/app/api/v1`、`apps/api/app/application/interviews`、`apps/api/app/domain/interviews`、关键词 `Interview`、`CreateInterviewSessionCommand`、`InterviewUseCases`；结果显示 `InterviewUseCases.bootstrap` 返回 `interview_skeleton`，当前实际 flow 走 `polish.py`。
- Pressure mode 代码实现未找到完整 endpoint。搜索路径/关键词: `apps/api/app/api/v1/pressure.py`、`apps/api/app/infrastructure/db/models/interview.py::PressureSessionDetail`、`docs/02-design/PRESSURE_MODE_SPEC.md`；代码层只看到 `APIRouter(prefix="/pressure-sessions")` 和 `PressureSessionDetail` model。
- WebSocket/SSE 运行实现未找到。搜索路径/关键词: `apps/api`、`apps/web/src`、`tests`，关键词 `WebSocket`、`EventSource`、`SSE`、`server-sent`；仅发现 `openai_compatible.py` 注释提到 streaming needs SSE/task state。
- Auth session 持久化未找到。搜索路径/关键词: `apps/api/app/infrastructure/security`、`apps/api/app/infrastructure/db/models/user.py`、关键词 `SessionStore`、`AuthSession`；当前 session token store 是 `InMemorySessionStore`。
- 完整面试 transcript 一级对象未找到。搜索路径/关键词: `apps/api/app/infrastructure/db/models`、`apps/api/app/application/polish`、`apps/web/src/entities/polish/model/types.ts`，关键词 `transcript`、`session turns`、`turns`；当前可见的是 question/answer/feedback records 和 API response assembled turns。
- Report 内容生成深度未知。代码确认 `apps/api/app/application/polish/report_application_service.py::generate_session_report` 通过 `SqlAlchemyPolishRepository.create_session_report` 创建 `polish_summary` report record；未在已读路径发现报告正文 LLM generation 或 section synthesis。
- Scoring API 与 docs 映射存在差异点需后续核对。`docs/02-design/API_SPEC.md` 将 `API-SCORING-001` 描述为 async scoring task；代码 `apps/api/app/api/v1/scoring.py::create_score_result` 当前同步调用 `ScoringUseCases.create`。
- 真实 provider runtime 未验证。`OpenAICompatibleLlmTransport` 存在，但本轮未设置 API key、未调用外部 provider、未验证网络/模型配置。

## 8. 风险

- 设计文档与当前代码实现粒度不一致：`docs/02-design/API_SPEC.md`、`DATA_MODEL.md`、`PROMPT_SPEC.md` 描述多个模式和 contract，但当前代码主工作流集中在 `apps/api/app/api/v1/polish.py` 与 `apps/web/src/pages/interview/InterviewPage.tsx`。
- Polish-specific coupling 较强：当前前端 `/interview` 页面、API client、types 和后端 flow 均围绕 polish session 命名；后续若扩展为更通用 interview coach，需要先锁定是否复用还是新增边界。
- Auth session 使用 `InMemorySessionStore`，服务重启会丢 session；与 `UserAccount` DB model 并存时容易误读为完整持久化 auth。
- Fake/deterministic fallback 存在于 `FakeLlmTransport` 和 question generation fallback，审计或测试材料中需要明确区分真实 provider 行为和 deterministic degraded/fake behavior。
- `apps/web/src/pages/interview/InterviewPage.tsx` 文件较大，`InterviewPage`、`InterviewWorkbenchPage`、`FeedbackForm`、progress tree、timeline、candidate panel 同处一文件；后续局部改动风险集中在同一页面文件。
- Report 当前可读/可创建 summary record，但已读代码未显示完整 report content generation；后续不能把 report docs 中的完整能力直接写成当前代码事实。
- Streaming/实时任务状态未见实现；当前前端 polish path 以 HTTP request 和 reload/refresh 为主。

## 9. 可供后续验证的命令

```bash
git branch
git status --short --untracked-files=all
git diff --stat
git status --short -- AGENTS.md
git diff -- AGENTS.md
```

```bash
npm run dev
npm run dev:debug
npm run db:migrate
npm run web:build
npm run web:test
npm run eval:gate
npm run eval:gate:negative
```

```bash
npm --workspace apps/web run dev
npm --workspace apps/web run build
npm --workspace apps/web run test
```

```bash
.venv/bin/python -m pytest tests/api/test_route_inventory.py -q
.venv/bin/python -m pytest tests/api/test_polish_feedback_generation_service.py -q
.venv/bin/python -m pytest tests/api/test_polish_application_service_split.py -q
.venv/bin/python -m pytest tests/api/test_persistence_repositories.py -q
```

```bash
python -m pytest tests/evals -q
scripts/evals/run_eval_gate.py --suite evals/suites/phase9.json --mode replay --output-json tmp/eval-gate/phase9-replay.json
scripts/evals/run_l5_eval_suite.py --mode deterministic --output-dir tmp/eval-gate/l5
```

## 10. 开放问题

- 后续范围是否只围绕 Polish mode 的 current workbench，还是需要把 `application/interviews` skeleton 提升为统一 interview boundary？
- 如果需要接入 canonical interview coach 能力，landing point 是复用 `polish` flow、扩展通用 `interviews` flow，还是建立新 mode？本轮只列候选，不做选择。
- 当前 `docs/02-design/API_SPEC.md` 中 Pressure/Scoring/Report 设计与代码实现差异，是否需要 Round 3 逐条映射为 capability matrix？
- Report 生成是否需要作为后续能力范围的一部分？当前代码只确认 `polish_summary` record 创建和 `/reports/{report_id}` 读取。
- 是否需要把 auth session persistence 纳入后续范围，还是保持为本轮外的基础设施风险？
- 后续验证是否需要运行 focused pytest 和 frontend typecheck？本轮只读审计未运行。

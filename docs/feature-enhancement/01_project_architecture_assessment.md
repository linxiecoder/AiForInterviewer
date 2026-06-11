---
title: Project Architecture and Feature Capability Assessment
type: assessment
status: draft
owner: architecture-review
permalink: ai-for-interviewer/feature-enhancement/project-architecture-assessment
---

# Project Architecture and Feature Capability Assessment

本文件是当前仓库的只读架构与功能能力盘点。它用于后续与参考 AI Skill / 工具实践分析合并，形成重构与强化候选清单；本文件本身不是 roadmap、Backlog、ADR 或实现计划。

# 1. Scope and Method

## Scope

本次评估覆盖当前工作树中的 active docs、后端 API、前端 Web、AI Runtime / Agent / Eval、文档治理工具和测试验证能力。

范围内证据：

- 协作与 active docs 边界：`AGENTS.md`、`docs/00-governance/DOCS_INDEX.md`、`docs/03-delivery/BACKLOG.md`、`docs/03-delivery/DELIVERY_PLAN.md`。
- 后端源码：`apps/api/app/main.py`、`apps/api/app/api/v1/**`、`apps/api/app/application/**`、`apps/api/app/domain/**`、`apps/api/app/infrastructure/**`、`apps/api/app/schemas/**`。
- 前端源码：`apps/web/src/app/routes/router.tsx`、`apps/web/src/shared/api/**`、`apps/web/src/entities/**`、`apps/web/src/pages/**`、`apps/web/src/widgets/**`。
- 工具与评估：`tools/doc_governor/**`、`tools/basic_memory_guard/**`、`evals/**`、`scripts/evals/**`、`scripts/dev/**`、`scripts/db/**`、`scripts/qa/**`。
- 测试与 CI：`tests/**`、`pytest.ini`、`package.json`、`apps/web/package.json`、`.github/workflows/eval-gate.yml`。

范围外：

- 不审计 `archive/**` 作为当前执行事实源；它只可作为历史证据。
- 不把 `docs/goals/**` 的历史执行记录升级为 active truth。
- 不运行 `/speckit.specify`、`/speckit.plan`、`/speckit.tasks`。
- 不提出具体 patch，不修改业务代码、测试代码、配置、依赖、锁文件或生成文件。

## Method

证据分级：

- `code fact`：当前源码、测试、配置或 CI 文件直接可见。
- `partial`：有部分 API / use case / repository / frontend / tests 证据，但不足以证明完整产品能力。
- `skeleton`：存在 prefix、schema、model、placeholder use case 或 repository `pass`，但无完整处理链路。
- `design-only`：只在 active design docs 中定义，当前源码未实现或未充分验证。
- `inference`：基于多处代码事实的工程判断。
- `UNKNOWN`：只读分析无法确认。
- `NEEDS_CONFIRMATION`：需要用户或后续参考 Skill 分析确认。

索引与图谱状态：

- CodeGraph 当前可用，状态显示已索引 710 个文件、13,336 个节点、34,757 条边；本次用它辅助定位入口、调用边界和高复杂度文件。
- `.understand-anything/meta.json` 存在，但记录的 `gitCommitHash` 是 `12a140eeaf9ba89f3e475e7e81973623f15fd7d5`，落后于当前 HEAD `62526743cf596eff5b9c65b880d104443c78a147`；因此只作为背景，不作为当前文件级事实。

# 2. Repository Overview

## Project Type

| 类型 | 当前判断 | 证据 |
|---|---|---|
| Web 应用 | 是。包含 React/Vite 前端和工作台页面。 | `apps/web/package.json`、`apps/web/src/app/routes/router.tsx`、`apps/web/src/pages/**` |
| API 服务 | 是。FastAPI app factory + v1 router。 | `apps/api/app/main.py`、`apps/api/app/api/v1/__init__.py` |
| Agent / AI 工具 | 是。包含 LLM provider boundary、AI Runtime facade、LangGraph default-off runtime、Agent contracts、eval gates。 | `apps/api/app/application/llm/**`、`apps/api/app/application/ai_runtime/**`、`apps/api/app/application/agents/**`、`evals/**` |
| CLI / 本地治理工具 | 是。doc-governor 和 basic-memory guard。 | `tools/doc_governor/cli.py`、`tools/basic_memory_guard/**` |
| Monorepo / Multi-package | 部分是。npm workspace 只有 `apps/web`，Python 后端在同仓库内但不是独立 Python package。 | `package.json`、`apps/web/package.json`、`requirements.txt` |
| SDK / Library | 不是主要形态。存在内部 application/domain libraries。 | `apps/api/app/domain/**`、`apps/api/app/application/**` |
| Plugin / Skill 系统 | 仓库内有 `.agents/skills/**`，但本项目主体不是通用 Skill runtime。 | `.agents/skills/**`、`AGENTS.md` |

## Technology Stack

| 维度 | 当前状态 | 证据 |
|---|---|---|
| 后端语言 | Python。 | `requirements.txt`、`apps/api/app/**/*.py` |
| 后端框架 | FastAPI + SQLAlchemy + Uvicorn；Alembic 依赖存在，`apps/api/migrations/**` 也存在。 | `requirements.txt`、`apps/api/app/main.py`、`apps/api/migrations/**` |
| AI runtime | LangGraph 依赖存在；runtime 默认关闭 / staged。 | `requirements.txt`、`apps/api/app/application/ai_runtime/runtime_flags.py`、`apps/api/app/infrastructure/ai_runtime/langgraph/**` |
| 前端语言 | TypeScript + TSX。 | `apps/web/tsconfig.json`、`apps/web/src/**/*.tsx` |
| 前端框架 | React 19 + Ant Design + Vite。 | `apps/web/package.json` |
| 构建系统 | npm workspace；web build 执行 `tsc --noEmit` 后 `vite build`。 | `package.json`、`apps/web/package.json` |
| 后端测试 | pytest。 | `pytest.ini`、`tests/**` |
| 前端测试 | 当前 `npm --workspace apps/web run test` 只执行 TypeScript typecheck；`.test.ts` 文件作为类型/纯函数 contract 参与编译，没有发现 Vitest/Jest 配置。 | `apps/web/package.json`、`apps/web/src/pages/interview/InterviewPage.test.ts`、`apps/web/tsconfig.json` |
| CI | 仅发现 eval gate workflow，覆盖 `tests/evals`、Phase 9 replay eval、Phase 12 deterministic eval。 | `.github/workflows/eval-gate.yml` |
| lint / format | 未发现 repo-local Ruff/Mypy/ESLint/Prettier 配置；`node_modules` 内配置不属于本项目规范。 | `rg --files` 配置扫描 |
| 运行时约束 | Node >=20；后端依赖 Python 3.12 运行于 CI；本地 dev 通过 Docker PostgreSQL + API + Vite。 | `package.json`、`.github/workflows/eval-gate.yml`、`AGENTS.md` |

# 3. Architecture Map

## Runtime Shape

当前仓库是“单后端服务 + 前端工作台 + AI Runtime/Eval 工具”的混合架构。

- 后端入口层：`apps/api/app/main.py` 创建 FastAPI app，装配 DB session factory、LLM transport、embedding provider、job match analyzer、AI orchestration facade、auth runtime、CORS、HTTP access logging 和 API v1 router。
- API 层：`apps/api/app/api/v1/__init__.py` 聚合 `auth`、`resumes`、`jobs`、`bindings`、`job_match_analyses`、`polish`、`polish_candidates`、`assets`、`weaknesses`、`training`、`reports`、`scoring`、`pressure`、`reviews`、`ai_tasks` 等 router。
- 应用服务层：大多数业务对象在 `apps/api/app/application/<module>/{commands,queries,ports,use_cases}.py` 下组织；`polish` 是最大聚合点。
- 领域逻辑层：`apps/api/app/domain/**` 包含 entities、services、value_objects、ports；Polish 纯策略集中在 `apps/api/app/domain/polish/policies/**`。
- 基础设施层：`apps/api/app/infrastructure/db/**`、`apps/api/app/infrastructure/llm/**`、`apps/api/app/infrastructure/security/**`、`apps/api/app/infrastructure/observability/**`、`apps/api/app/infrastructure/ai_runtime/**`。
- 配置层：后端配置分散在 `apps/api/app/main.py`、`apps/api/app/infrastructure/env_reader.py`、LLM / embedding / auth runtime builder 中；前端配置在 `apps/web/src/shared/config/env.ts` 与 Vite proxy。
- 外部集成层：LLM provider 通过 `apps/api/app/application/llm/provider_boundary.py` 与 `apps/api/app/infrastructure/llm/openai_compatible.py`；embedding provider 在 `apps/api/app/infrastructure/embeddings/**`。
- 测试层：API / architecture / domain / eval / doc_governor 测试覆盖较丰富；前端主要是 TypeScript contract harness，不是浏览器交互测试。

## Dependency Direction

当前已有显式边界保护：

- `tests/architecture/test_application_boundary.py` 禁止 `domain` 直接 import `app.api`、`app.infrastructure`、FastAPI、SQLAlchemy、LangGraph、provider SDK 和 prompt builder。
- 同一测试限制 focused Polish application services 不直接 import prompt/provider/db/API/runtime/agents。
- `tests/architecture/test_domain_polish_policy_boundary.py` 要求 `domain/polish/policies` 不依赖 API、infra、runtime、provider 或 prompt assets，并要求 application bridges 调用 domain policy entrypoints。
- `tests/architecture/test_provider_boundary_static.py` 要求生产 LLM transport request 通过 provider boundary 构造，并检查 forbidden sensitive keys。

当前未从只读 import 扫描发现 `apps/api/app/domain` 或 `apps/api/app/application` 直接 import `app.infrastructure` / `app.api` 的新增违规；但这不等于所有跨层调用都理想。`apps/api/app/api/v1/jobs.py` 中 route handler 直接实例化 SQLAlchemy repository 并在 helper 中访问 `BindingUseCases._binding_repository`，说明 API adapter 中仍有部分跨用例与私有属性耦合。

## High Coupling / High Dependence Areas

| 区域 | 判断 | 证据 |
|---|---|---|
| `apps/api/app/application/polish/use_cases.py` | 高复杂度应用编排文件，2,596 行。 | `wc -l apps/api/app/application/polish/use_cases.py` |
| `apps/api/app/api/v1/polish.py` | 高复杂度 HTTP adapter，1,291 行。 | `wc -l apps/api/app/api/v1/polish.py` |
| `apps/web/src/pages/interview/InterviewPage.tsx` | 高复杂度前端聚合文件，6,539 行，包含列表、创建、详情工作台、状态机、渲染 helper 和 contract exports。 | `wc -l apps/web/src/pages/interview/InterviewPage.tsx`、`apps/web/src/pages/interview/InterviewPage.test.ts` |
| `tools/doc_governor/cli.py` | CLI 命令聚合文件，3,774 行，包含大量 subparser 和 command dispatch。 | `wc -l tools/doc_governor/cli.py` |
| `app.main.create_app` | 启动装配集中，直接构建多个基础设施对象和 runtime facade。 | `apps/api/app/main.py` |

# 4. Module Inventory

| 模块 | 路径 | 职责 | 入口 | 核心依赖 | 被依赖情况 | 测试现状 | 强化优先级 | 证据 |
|---|---|---|---|---|---|---|---|---|
| App Bootstrap | `apps/api/app/main.py` | 构建 FastAPI app、配置 CORS、DB、LLM、embedding、auth、AI runtime、router。 | `app = create_app(settings)`、`npm run dev:api` | `EnvReader`、`configure_session_factory`、`build_llm_transport_from_env`、`AiOrchestrationFacade` | 所有 API 流量依赖 | `tests/api/test_app_bootstrap.py`、`tests/api/test_cors.py` | P1 | `apps/api/app/main.py` |
| API Router Composition | `apps/api/app/api/v1/__init__.py` | 聚合 v1 routers。 | `build_api_v1_router(prefix)` | 各 `app.api.v1.*` router | FastAPI app include | `tests/api/test_route_inventory.py`、`tests/api/test_capability_preservation_inventory.py` | P1 | `apps/api/app/api/v1/__init__.py` |
| Auth | `apps/api/app/api/v1/auth.py`、`apps/api/app/application/auth/**`、`apps/api/app/infrastructure/security/**` | 登录、会话、当前用户。 | `/api/v1/auth/login`、`/me`、`/logout` | auth runtime、session storage、cookie | 前端 `AuthProvider`、API deps | `tests/api/test_auth_api.py`、`test_auth_dependencies.py`、`test_auth_passwords.py` | P1 | route snapshot includes auth endpoints |
| Resume CRUD | `apps/api/app/api/v1/resumes.py`、`application/resumes/**`、`domain/resumes/**`、`infrastructure/db/repositories/resumes.py` | Markdown 简历记录与版本。 | `/api/v1/resumes` | SQLAlchemy repo、owner scope、version refs | Web resume page、bindings、job match | `tests/api/test_resumes_api.py` | P2 | `tests/api/test_capability_preservation_inventory.py` implemented expectations |
| Job / JD CRUD | `apps/api/app/api/v1/jobs.py`、`application/jobs/**` | 岗位手动录入、更新、删除、绑定摘要。 | `/api/v1/jobs` | Job repo、BindingUseCases、VersionRef | Web job page、bindings、job match | `tests/api/test_jobs_api.py`、`test_job_binding_owner_scope.py` | P2 | `apps/api/app/api/v1/jobs.py` |
| Resume-Job Binding | `apps/api/app/api/v1/bindings.py`、`application/bindings/**` | 简历与岗位绑定关系。 | `/api/v1/resume-job-bindings` | Resume repo、Job repo、Binding repo | Job/Resume/Polish create prerequisites | `tests/api/test_bindings_api.py` | P2 | route snapshot |
| Job Match | `apps/api/app/api/v1/job_match_analyses.py`、`application/job_match/**`、`infrastructure/llm/job_match.py` | 岗位匹配分析、评分、证据。 | `/api/v1/job-match-analyses` | LLM transport、schema contracts、repositories | Job page, weakness suggestions | `tests/api/test_job_match_api.py`、`test_job_match_schema_contract.py` | P1 | `package.json` eval scripts; `tests/api/test_job_match_schema_contract.py` |
| Polish Aggregate | `apps/api/app/api/v1/polish.py`、`application/polish/**`、`infrastructure/db/repositories/polish.py` | 打磨模式 session、question、answer、feedback、progress tree、report。 | `/api/v1/polish-sessions`、`/polish-topics` | Polish repositories、domain policies、LLM services、AI runtime optional path | 前端核心工作台、eval / runtime tests | `tests/api/test_polish_api.py`、`test_polish_question_refactor_phase1.py`、`test_polish_feedback_*` | P0 | `docs/03-delivery/refactor/CAPABILITY_PRESERVATION_MATRIX.md` marks aggregate partial |
| Polish Question Generation | `application/polish/question_generation_service.py`、`agents/question/planned_workflow.py`、`ai_runtime/handoff.py` | 题目生成、candidate/handoff、source support、progress node selection。 | `create_polish_question_task` route/use case | provider boundary、SourceSupportPolicy、AgentPersistenceHandoff | Polish workbench, runtime graph tests | `tests/api/test_polish_question_graph_integration.py`、`test_pr5_polish_question_graph_persistence_handoff.py` | P0 | CodeGraph shows `run_question_planned_workflow` caller in `use_cases.py` |
| Polish Feedback / Scoring Rules | `application/polish/feedback_generation_service.py`、`feedback_rules.py`、`feedback_validation.py`、`domain/polish/policies/**` | 反馈生成、失分点、server-side scoring、下一步建议。 | `/polish-sessions/{session_id}/feedback` | provider boundary、ScoringPolicy、AnswerCoveragePolicy、AssetConsistencyPolicy | Workbench feedback cards, candidates, weakness/asset flows | `tests/api/test_polish_feedback_generation_service.py`、`test_polish_feedback_validation.py`、`tests/domain/polish/**` | P0 | `domain/polish/policies/scoring_policy.py` |
| Polish Candidates | `apps/api/app/api/v1/polish_candidates.py`、`infrastructure/db/repositories/polish_candidates.py` | candidate list、confirm/dismiss/merge/archive；可能转正式 Asset / Weakness / TrainingRecommendation。 | `/api/v1/polish-candidates` | candidate repo、formal object repositories | Workbench candidate review | `tests/api/test_polish_candidates.py` | P1 | capability memory and route snapshot; formal-write risk |
| Asset Library | `apps/api/app/api/v1/assets.py`、`application/assets/**`、`domain/assets/**` | 资产 CRUD、确认沉淀边界。 | `/api/v1/assets` | Asset repo、RAG chunks | Workbench/candidates/weakness evidence | `tests/api/test_assets_weaknesses_api.py` | P1 | implemented route expectations include Assets |
| Weakness | `apps/api/app/api/v1/weaknesses.py`、`application/weaknesses/**`、`domain/weaknesses/**` | 薄弱项读取、状态、删除；与 candidate / training legacy 有关联。 | `/api/v1/weaknesses` | Weakness repo、owner scope | Asset/Polish/Training suggestions | `tests/api/test_assets_weaknesses_api.py` | P1 | route snapshot includes weakness routes |
| Reports | `apps/api/app/api/v1/reports.py`、`application/reports/**` | 当前主要是 existing `polish_summary` read。 | `/api/v1/reports/{report_id}` | Reports repo | Workbench report dialog | `tests/api/test_reports_api.py`、skeleton guard | P2 | capability matrix: Reports partial |
| Scoring | `apps/api/app/api/v1/scoring.py`、`application/scoring/**`、`domain/scoring/**` | 通用 score result API skeleton/limited flow，Polish feedback另有 server-side scoring policy。 | `/api/v1/scoring-results` | scoring repo / models | Reports / feedback future | `tests/api/test_scoring_api.py`、skeleton guard | P2 | capability matrix: Scoring skeleton |
| Pressure Mode | `apps/api/app/api/v1/pressure.py`、`application/pressure/**`、`docs/02-design/PRESSURE_MODE_SPEC.md` | 压力面 mode-level design；当前 route/use case placeholder。 | `/api/v1/pressure-sessions` prefix only | placeholder use case | 暂无前端 route | capability preservation tests | P3 | `PRESSURE_MODE_SPEC.md` and skeleton guard |
| Reviews | `apps/api/app/api/v1/reviews.py`、`application/reviews/**` | 面试复盘 / review placeholder。 | `/api/v1/reviews` prefix only | placeholder use case | disabled nav / no active route | capability preservation tests | P3 | `apps/api/app/api/v1/reviews.py` |
| AI Tasks | `apps/api/app/api/v1/ai_tasks.py`、`application/ai_tasks/**`、`infrastructure/db/repositories/ai_tasks.py` | AiTask status/result future boundary；当前 skeleton。 | `/api/v1/ai-tasks` prefix only | repository `pass` | AI Runtime future UI/API | skeleton guard | P2 | `tests/api/test_skeleton_guard.py` |
| AI Runtime Facade | `apps/api/app/application/ai_runtime/**`、`infrastructure/ai_runtime/langgraph/**` | default-off graph registry、runtime flags、start/resume/replay、handoff、trace refs。 | `AiOrchestrationFacade`、runtime graph functions | RuntimeFlagResolver、AgentGraphRegistry、LangGraph runtime | Polish question graph optional path, eval tests | `tests/api/test_ai_orchestration_facade.py`、`test_agent_graph_runner.py`、PR4-PR8 tests | P1 | `RuntimeFlagResolver` and `GraphDisabledError` paths |
| LLM Provider Boundary | `apps/api/app/application/llm/**`、`infrastructure/llm/**` | provider request validation, redaction, transport settings, fake runtime fail-closed。 | `build_llm_transport_from_env()` | OpenAI compatible transport、EnvReader、LogUtil | Job Match、Polish AI services、runtime | `tests/api/test_provider_boundary.py`、`test_llm_runtime.py`、`test_fake_llm_boundary.py` | P0 | `runtime.py` rejects `LLM_PROVIDER=fake` |
| Eval Gate | `evals/**`、`scripts/evals/**`、`tests/evals/**` | deterministic/replay eval, non-claim report, negative controls。 | `npm run eval:gate`、CI workflow | JSONL datasets、code_rules grader | CI, release evidence | `tests/evals/**`、`.github/workflows/eval-gate.yml` | P1 | Phase 9/12 scripts |
| Frontend Shell / Routing | `apps/web/src/app/routes/router.tsx`、`widgets/app-shell/**` | custom route provider、auth redirect、module shell/navigation。 | `<AppRouter />` | AuthProvider、pages | 全部前端页面 | `AppShell.test.ts`、`navigation.test.ts`、typecheck | P1 | no React Router; custom path routing |
| Frontend API Client | `apps/web/src/shared/api/client.ts`、`envelope.ts` | API envelope validation、fetch wrapper、error mapping。 | `request<T>()` | `API_BASE_URL`, `ApiHttpError` | 所有 entity API | typecheck only; no runtime unit runner found | P1 | `client.ts` |
| Interview Workbench Frontend | `apps/web/src/pages/interview/InterviewPage.tsx`、`InterviewWorkbench.module.css`、`InterviewPage.test.ts` | 模拟面试列表、创建抽屉、详情工作台、进展树、聊天、反馈、候选、报告。 | `/interview`、`/interview/:id` | polish API, job API, Ant Design, local view-model helpers | 用户核心路径 | TypeScript contract harness, no browser/e2e config found | P0 | `InterviewPage.tsx` 6,539 lines |
| Doc Governor CLI | `tools/doc_governor/**` | 文档治理 state、round、task、readiness、patch preview、validation。 | `tools/doc_governor/cli.py main()` | schema/state/render/history modules | docs workflow/tests | `tests/doc_governor/**` 45 files | P2 | `tools/doc_governor/cli.py` 3,774 lines |

# 5. Feature Quality Assessment

## Core Quality Matrix

| 维度 | 当前状态 | 问题表现 | 仓库证据 | 影响 | 是否值得强化 |
|---|---|---|---|---|---|
| 模块内聚性 | 后端 domain/application/infra 分层整体存在；Polish 和前端 Interview Workbench 是明显高聚合点。 | `application/polish/use_cases.py` 同时承载 session/question/answer/feedback/progress/report 编排；`InterviewPage.tsx` 同时承载列表、创建、详情、工作台状态和大量 view-model helpers。 | `wc -l` 显示 `use_cases.py` 2,596 行、`InterviewPage.tsx` 6,539 行、`api/v1/polish.py` 1,291 行。 | 新增打磨/反馈/进展树能力时容易触碰大文件，review 成本高。 | 是，P0/P1；但应按业务边界逐步拆，不做大爆炸。 |
| 边界清晰度 | 后端边界有 architecture tests；provider boundary 和 domain policy boundary 较清楚。 | API adapter 中仍有局部私有属性访问和跨 use case helper；skeleton routes 与 implemented routes 同在 router composition 中，容易被误解。 | `apps/api/app/api/v1/jobs.py` helper 使用 `binding_usecase._binding_repository`；`tests/api/test_skeleton_guard.py` 防止 skeleton 声明升级。 | 维护者可能把 route prefix、model 或 deterministic eval 误读为产品能力。 | 是，P0；优先强化 capability evidence 和 module boundary documentation/tests。 |
| 可测试性 | 后端 pytest 覆盖丰富；domain policy 有纯测试；eval 有 deterministic fixtures。 | 前端 `.test.ts` 主要通过 `tsc --noEmit` 执行类型/纯函数 contract，不是 UI runtime 测试；CI 只发现 eval workflow。 | `apps/web/package.json` test = `tsc -p tsconfig.json --noEmit`；`.github/workflows/eval-gate.yml` 只跑 eval tests/scripts。 | 前端交互、真实 API flow、浏览器状态和回归无法被 CI baseline 完整保护。 | 是，P0/P1；先补 baseline，再强化实现。 |
| 错误处理 | 后端有 `ApplicationResult`、`ApiHttpError`、provider/runtime error categories；前端有 `ApiHttpError` 解析。 | 错误分类存在多套：DomainError/ApplicationResult、HTTP error envelope、RuntimePolicyError、provider validation error、前端 `Error` 文本；一致性需要持续守卫。 | `apps/web/src/shared/api/client.ts`、`apps/api/app/api/errors.py`、`apps/api/app/application/ai_runtime/contracts.py`、`apps/api/app/application/llm/errors.py`。 | 错误信息若跨层丢失 details，会影响用户诊断和前端状态映射。 | 是，P1；以 contract tests 而不是风格重写开始。 |
| 配置能力 | `EnvReader`、`ApiSettings`、LLM runtime settings、RuntimeFlagResolver 已形成局部集中。 | `create_app()` 同时读取/装配 API、DB、LLM、embedding、AI runtime、auth；配置错误分类并不完全统一。 | `apps/api/app/main.py`、`apps/api/app/application/ai_runtime/runtime_flags.py`、`apps/api/app/infrastructure/llm/runtime.py`。 | 启动失败定位依赖日志；新 runtime capability 可能继续增加 app factory 负担。 | 是，P1；先强化启动诊断和配置清单。 |
| 扩展能力 | AI Runtime 有 registry/facade/flags；domain policies 可独立扩展；provider boundary 抽象存在。 | 部分 registry/graph 是 default-off/skeleton；新增 product capability 仍需 API、schema、use case、repo、frontend、多处 tests 同步。 | `AgentGraphRegistry.default()`、`RuntimeFlagResolver`、`CAPABILITY_PRESERVATION_MATRIX.md`。 | 扩展路径清楚但成本高；误开启 default-off runtime 的风险需要 guard。 | 是，P1；参考 Skill 时重点看 registry / command discovery / capability metadata。 |
| 兼容性 | API envelope、route snapshot、capability preservation tests 保护了部分 contract。 | 没有发现全量 OpenAPI contract CI；前端 API types 与后端 schemas 不是自动生成/同步。 | `tests/api/test_route_inventory.py`、`tests/api/test_capability_preservation_inventory.py`、`apps/web/src/entities/*/model/types.ts`。 | schema drift 可能由手写 TS types 引入，尤其 Polish 工作台。 | 是，P0/P1；先补 contract drift 检测。 |
| 可观测性 | 后端有 `LogUtil`、HTTP access middleware、LLM provider resolved logs、eval reports。 | 用户态 trace/timeline API 当前未完整产品化；CI upload 只 eval reports。 | `apps/api/app/infrastructure/observability/**`、`apps/api/app/main.py`、`scripts/evals/run_eval_gate.py`。 | 生产/本地失败可诊断性部分依赖日志和报告；普通用户 debug view 不应开放。 | 是，P1；强化结构化失败摘要和 release evidence。 |
| 文档与 DX | active docs 体系强，README 清楚说明 active truth 和 non-claims。 | 本地 setup 命令分散在 `AGENTS.md`、`package.json`、docs/goals 历史记录；缺少 root-level concise contributor/testing guide。 | `README.md` 明确 setup 不展开；`AGENTS.md` 有 dev 命令；`DOCS_INDEX.md` 复杂。 | 新贡献者需要较多上下文才能知道 baseline 命令和状态词。 | 是，P2；不优先于测试和 contract。 |

## Module-Specific Notes

- `Polish Aggregate` 是当前最核心也最容易被误声明的能力。`docs/03-delivery/refactor/CAPABILITY_PRESERVATION_MATRIX.md` 已明确其 aggregate remains partial；后续强化必须继续区分 route handler、use case、repository/model、frontend/user path、runtime quality 和 eval evidence。
- `Interview Workbench Frontend` 是用户价值最高的前端路径，但现有文件大小和 contract harness 形态说明其可维护性与真实交互验证都需要强化。
- `AI Runtime / Eval` 的工程价值高，但当前 default-off / deterministic / replay 证据主要是 contract/regression evidence；不应作为 live-provider quality 或 production Agent Runtime productization 证明。
- `Doc Governor CLI` 测试覆盖多，但 `tools/doc_governor/cli.py` command registration/dispatch 聚合过重；适合作为工具化架构优化候选，但不应抢占产品核心 P0。

# 6. Architecture Pain Points

| Pain ID | 问题描述 | 相关路径 | 具体证据 | 影响范围 | 严重程度 | 紧迫度 | 可能强化方向 |
|---|---|---|---|---|---|---|---|
| PAIN-001 | 前端核心工作台单文件过大且混合页面、状态机、view-model、contract exports。 | `apps/web/src/pages/interview/InterviewPage.tsx`、`InterviewPage.test.ts` | `InterviewPage.tsx` 6,539 行；test 从同一文件 import 大量 constants/helpers/types。 | 打磨模式用户主路径、后续 UI 切片、回归验证。 | high | now | 按纯 view-model、API action builder、状态派生、渲染区域逐步抽离；先补测试边界。 |
| PAIN-002 | Polish 后端 aggregate 编排过重。 | `apps/api/app/application/polish/use_cases.py`、`apps/api/app/api/v1/polish.py` | `use_cases.py` 2,596 行；`api/v1/polish.py` 1,291 行。 | session/question/answer/feedback/progress/report。 | high | now | 按已存在 application service seam 分阶段收敛，不改变 public API。 |
| PAIN-003 | Skeleton/partial/default-off 能力与真实产品能力混在 route/docs 中，容易误声明。 | `api/v1/ai_tasks.py`、`pressure.py`、`reviews.py`、`docs/03-delivery/refactor/CAPABILITY_PRESERVATION_MATRIX.md` | skeleton guard 要求 route prefix、repository `pass`、default-off eval 不得写成 implemented。 | 架构报告、release readiness、后续重构优先级。 | high | now | 强化 capability status inventory 与自动化 claim guard。 |
| PAIN-004 | 前端缺少真实 UI 测试 runner / E2E baseline。 | `apps/web/package.json`、`apps/web/src/**/*.test.ts` | `test` 只执行 `tsc --noEmit`；未发现 Vitest/Jest/Playwright config。 | 工作台交互、路由、弹窗、错误态、API error mapping。 | high | now | 先建立最小 UI/interaction baseline，再做大 UI 重构。 |
| PAIN-005 | CI baseline 偏 eval gate，未覆盖 full API/web baseline。 | `.github/workflows/eval-gate.yml` | workflow 只跑 `tests/evals` 和 Phase 9/12 scripts。 | PR 回归风险、release confidence。 | high | now | 增加分层 CI baseline 或明确本地 required checks。 |
| PAIN-006 | App factory 装配多个基础设施与 runtime，启动边界负载增加。 | `apps/api/app/main.py` | `create_app()` 构建 DB、LLM、embedding、job_match、AI facade、auth、middleware、router。 | 本地启动、测试注入、配置诊断。 | medium | later | 抽象 composition root / dependency bundle；先补启动配置诊断。 |
| PAIN-007 | API adapter 中存在局部跨 use case / 私有属性访问。 | `apps/api/app/api/v1/jobs.py` | `_binding_summary_builder` 访问 `binding_usecase._binding_repository`。 | Jobs / bindings summary，一致性和封装。 | medium | later | 提供 application query method 或 read model seam。 |
| PAIN-008 | 手写前后端 API types 容易 drift。 | `apps/web/src/entities/**/model/types.ts`、`apps/api/app/schemas/**` | 前端 `Polish` API types 与后端 Pydantic schemas 分开维护。 | API contract、前端错误态、candidate/feedback fields。 | high | now | contract snapshot / schema drift tests；是否 codegen 需后续评估。 |
| PAIN-009 | AI Runtime / Eval evidence taxonomy 复杂，易被当成 live provider quality。 | `scripts/evals/**`、`tests/evals/**`、`application/ai_runtime/**` | eval runner 写 `provider_evidence_type`；Phase 12 non-claims 包含 no real provider quality certification。 | release claims、docs closeout、runtime rollout。 | high | now | 强化 evidence type schema、报告模板和 release guard。 |
| PAIN-010 | CLI command surface 巨大，dispatch 聚合。 | `tools/doc_governor/cli.py` | 3,774 行，包含大量 argparse subcommands 和 dispatch。 | 文档治理工具维护成本。 | medium | watch | 参考外部 Skill 后判断是否按 command modules/registry 分拆。 |
| PAIN-011 | 配置和验证命令分散。 | `AGENTS.md`、`package.json`、`docs/goals/**`、`README.md` | README 明确 local setup 不展开；AGENTS.md 包含 dev 命令；historical docs 中有大量 pytest variants。 | 新贡献者 DX、验证一致性。 | medium | later | 建立 active testing/developer command matrix，不从 docs/goals 继承事实。 |
| PAIN-012 | Pressure/Reviews/AI Tasks route prefix 容易给人“已有能力”错觉。 | `apps/api/app/api/v1/pressure.py`、`reviews.py`、`ai_tasks.py` | placeholder route/use case markers；capability matrix marks skeleton。 | 产品计划、用户价值判断。 | medium | watch | 保留 skeleton guard；除非 Backlog 授权，不作为当前强化 P0。 |

# 7. Testing and Validation Baseline

## Current Verification Commands

| 命令 | 来源 | 验证范围 | 适合作为 baseline 吗 | 风险 | 备注 |
|---|---|---|---|---|---|
| `npm run dev` | `package.json`、`AGENTS.md` | 启动 PostgreSQL、后端 API、前端 Vite。 | 否，dev runtime，不是 CI baseline。 | 会启动服务、占用端口、改运行状态。 | 本地页面验证用。 |
| `npm run dev:debug` | `package.json`、`AGENTS.md` | 后端 debug mode + frontend。 | 否。 | 依赖 PyCharm debug server。 | 适合人工调试。 |
| `npm run web:test` | `package.json` | workspace web test。 | 是，前端 typecheck baseline。 | 不是 UI runtime test。 | 等价 `npm --workspace apps/web run test`。 |
| `npm --workspace apps/web run test` | `apps/web/package.json` | `tsc -p tsconfig.json --noEmit`。 | 是，但只保护类型/contract harness。 | 无 DOM / browser execution。 | 不要附 source-file 参数。 |
| `npm run web:build` | `package.json` | Typecheck + Vite build。 | 是，前端构建 baseline。 | 可能写 `apps/web/dist`。 | 修改前端时需要。 |
| `python -m pytest tests/evals -q` | `.github/workflows/eval-gate.yml` | Eval tests。 | 是，eval baseline。 | 需要 Python deps/PYTHONPATH。 | CI 已跑。 |
| `python scripts/evals/run_eval_gate.py --suite phase9 --mode replay --report-dir ...` | package scripts / CI | Phase 9 replay eval。 | 是，AI eval regression baseline。 | replay 不等于 live provider quality。 | 包含 report safety scanners。 |
| `python scripts/evals/run_eval_gate.py --suite phase9 --mode replay --expect-fail-fixture` | package scripts / CI | Phase 9 negative control。 | 是。 | 只证明负例被挡住。 | `npm run eval:gate:negative` 包装。 |
| `python scripts/evals/run_l5_eval_suite.py --mode deterministic --report-dir ...` | CI | Phase 12 L5 deterministic eval。 | 是，contract/regression baseline。 | non-claim：不是 L5 release 或 real provider quality。 | CI 已跑。 |
| `python scripts/evals/run_l5_eval_suite.py --mode deterministic --expect-fail-fixture` | CI | Phase 12 negative control。 | 是。 | deterministic only。 | CI 已跑。 |
| `PYTHONPATH=.:apps/api .venv/bin/python -m pytest tests/api -q` | docs/goals / tests convention | API focused/full-ish tests。 | 是，但未发现 CI 默认跑。 | repo-root temp leak guard 可能使断言通过后仍 exit non-zero。 | 常需 `AI_FOR_INTERVIEWER_ALLOW_TEST_DIR_LEAKS=1` 作为 workaround。 |
| `PYTHONPATH=.:apps/api .venv/bin/python -m pytest tests/architecture -q` | architecture tests | import boundary / provider boundary / agent boundary。 | 是。 | 需要正确 PYTHONPATH。 | 高价值边界 baseline。 |
| `git diff --check` | workflow convention | whitespace / conflict markers。 | 是，提交前 hygiene。 | 只检查 diff。 | 本次文档写入后必跑。 |

## Missing / Weak Verification Areas

- 缺少 repo-level CI workflow 跑 `tests/api`、`tests/architecture`、`npm run web:test`、`npm run web:build`。
- 缺少前端 runtime test runner；当前 `.test.ts` 更像 TypeScript contract harness。
- 缺少浏览器 E2E baseline 覆盖登录、简历/岗位、创建 Polish session、问题/回答/反馈主路径。
- 缺少自动前后端 schema drift gate；前端 `model/types.ts` 与后端 Pydantic schemas 手写维护。
- 缺少 live-provider quality gate；现有 eval 明确是 replay/deterministic/fixture/fake/mock/default-off regression evidence。

## Tests Needed Before Enhancement

| 强化方向 | 先补测试类型 | 原因 |
|---|---|---|
| Interview Workbench 拆分 | TypeScript pure helper tests + minimal UI runtime tests | 防止大文件拆分改变按钮、状态机、反馈展示和 regenerate/follow-up 语义。 |
| Polish use case 拆分 | focused API tests + application service tests + architecture boundary tests | 保持 public API、idempotency、candidate/formal handoff、owner scope。 |
| API schema drift | contract test / schema snapshot | 手写 TS/Pydantic 分离，字段 drift 高风险。 |
| AI Runtime evidence taxonomy | golden report / fixture tests | 防止 non-claim 被报告模板误升级。 |
| Provider boundary | negative contract tests | 防止 raw prompt/completion/provider payload 泄露。 |
| CLI doc_governor 分拆 | CLI smoke + command registry golden snapshot | 保持已有命令行为。 |

# 8. Enhancement Candidate List

## Value Matrix

| 强化候选 | 用户价值 | 工程价值 | 风险 | 成本 | 优先级建议 | 证据 |
|---|---|---|---|---|---|---|
| CAND-001 Interview Workbench 可维护性与真实交互验证 | 高：直接影响模拟面试主路径体验。 | 高：降低 UI 改动连锁风险。 | 中高：单文件大，行为多。 | 中高 | P0 | `InterviewPage.tsx` 6,539 行；`InterviewPage.test.ts` type contract harness。 |
| CAND-002 API / Frontend contract drift guard | 高：减少字段错配导致的用户不可用。 | 高：保护 Polish、Job、Resume、Assets 等接口。 | 中 | 中 | P0 | 手写 TS types 与 Pydantic schemas 分离；route snapshot tests 已存在。 |
| CAND-003 Capability status / non-claim guard | 中高：避免用户/维护者误解功能状态。 | 高：保护 release/readiness 质量。 | 低 | 中 | P0 | `CAPABILITY_PRESERVATION_MATRIX.md`、`test_skeleton_guard.py`。 |
| CAND-004 CI baseline expansion | 中高：减少回归进入主分支。 | 高：让本地证据转为 CI 证据。 | 中 | 中 | P1 | `.github/workflows/eval-gate.yml` 只跑 eval。 |
| CAND-005 Polish backend aggregate seam | 高：支持后续打磨模式强化。 | 高：降低 `use_cases.py` 复杂度。 | 高：核心业务路径。 | 高 | P1 | `use_cases.py` 2,596 行，API route 1,291 行。 |
| CAND-006 App composition / config diagnostics | 中：启动失败更可诊断。 | 中：减少 app factory 继续膨胀。 | 中 | 中 | P1 | `create_app()` 集中装配 DB/LLM/embedding/runtime/auth/router。 |
| CAND-007 AI Runtime evidence taxonomy | 中：减少对 AI 能力状态误判。 | 高：release/eval/agent rollout 更清晰。 | 中 | 中 | P1 | Phase 9/12 scripts 有 non-claims 和 provider_evidence_type。 |
| CAND-008 Provider boundary / redaction golden samples | 高：保护隐私和安全。 | 高：防止 raw payload 泄露回归。 | 中 | 中 | P1 | `provider_boundary.py`、`test_provider_boundary_static.py`。 |
| CAND-009 Doc Governor CLI command registry | 低中：维护者体验。 | 中：降低 CLI 分支复杂度。 | 中 | 中 | P2 | `tools/doc_governor/cli.py` 3,774 行，tests/doc_governor 丰富。 |
| CAND-010 Developer command matrix | 低中：降低入门成本。 | 中：减少验证命令混乱。 | 低 | 低 | P2 | README 不展开 setup；AGENTS/package/docs-goals 分散。 |

## Candidate YAML

```yaml
candidates:
  - id: CAND-001
    title: Interview Workbench modularity and runtime UI verification
    problem: InterviewPage.tsx concentrates list, create drawer, workbench state, render helpers, view models, API actions and exported test contracts in one 6539-line file.
    modules:
      - Frontend Interview Workbench
      - Polish frontend API
    paths:
      - apps/web/src/pages/interview/InterviewPage.tsx
      - apps/web/src/pages/interview/InterviewPage.test.ts
      - apps/web/src/pages/interview/InterviewWorkbench.module.css
    evidence:
      - wc -l reports InterviewPage.tsx has 6539 lines.
      - InterviewPage.test.ts imports many constants and helper functions from InterviewPage.tsx.
      - apps/web/package.json test only runs tsc --noEmit.
    desired_improvement: Split along stable pure view-model and state derivation seams after adding enough tests; preserve public UI behavior and current route paths.
    potential_reference_capability: UI action registry, view-model extraction, golden interaction fixtures, component-level smoke tests.
    requires_tests_first: true
    public_contract_sensitive: true
    risk_level: high
    priority: P0
  - id: CAND-002
    title: Backend/frontend API contract drift guard
    problem: Frontend model types and backend Pydantic schemas are maintained separately, while Polish candidate/feedback/session fields are broad and fast-moving.
    modules:
      - API schemas
      - Frontend entity APIs
      - Polish aggregate
    paths:
      - apps/api/app/schemas
      - apps/web/src/entities
      - tests/api/test_route_inventory.py
    evidence:
      - Route snapshot tests exist, but no generated OpenAPI/TS schema drift gate was found.
      - apps/web/src/shared/api/envelope.ts defines hand-written envelope fields.
    desired_improvement: Add contract snapshots or schema drift tests before any broad frontend/backend refactor.
    potential_reference_capability: Contract schema registry, generated client, fixture-based compatibility tests.
    requires_tests_first: true
    public_contract_sensitive: true
    risk_level: high
    priority: P0
  - id: CAND-003
    title: Capability status and non-claim guard hardening
    problem: Skeleton routes, repository pass, disabled nav, default-off graph and deterministic eval evidence can be mistaken for implemented product capability.
    modules:
      - Delivery governance
      - AI Runtime
      - Capability preservation tests
    paths:
      - docs/03-delivery/refactor/CAPABILITY_PRESERVATION_MATRIX.md
      - tests/api/test_skeleton_guard.py
      - tests/api/test_capability_preservation_inventory.py
    evidence:
      - Existing tests explicitly forbid skeleton/default-off evidence from being declared implemented.
      - README states ADR-0005 is Proposed and runtime is staged/default-off.
    desired_improvement: Keep automated claim checks close to route/runtime inventories and release/eval reports.
    potential_reference_capability: Status taxonomy, claim scanner, evidence-backed readiness report.
    requires_tests_first: false
    public_contract_sensitive: false
    risk_level: medium
    priority: P0
  - id: CAND-004
    title: CI baseline expansion beyond eval gate
    problem: The only discovered GitHub workflow runs eval gates, not full API, architecture, or web baselines.
    modules:
      - CI
      - Tests
      - Frontend build
    paths:
      - .github/workflows/eval-gate.yml
      - pytest.ini
      - package.json
      - apps/web/package.json
    evidence:
      - eval-gate.yml runs tests/evals and Phase 9/12 scripts only.
      - package.json contains web:test and web:build scripts that are not in the discovered CI workflow.
    desired_improvement: Define a minimal required CI baseline for architecture/API/web without weakening eval gates.
    potential_reference_capability: Multi-lane validation gates, required checks matrix, fast/slow split.
    requires_tests_first: false
    public_contract_sensitive: false
    risk_level: medium
    priority: P1
  - id: CAND-005
    title: Polish backend aggregate seam refinement
    problem: Polish use cases and API adapter are large aggregation points and remain partial as an aggregate capability.
    modules:
      - Polish aggregate
      - Question generation
      - Feedback generation
      - Progress tree
    paths:
      - apps/api/app/application/polish/use_cases.py
      - apps/api/app/api/v1/polish.py
      - apps/api/app/application/polish/*_application_service.py
    evidence:
      - use_cases.py has 2596 lines; api/v1/polish.py has 1291 lines.
      - tests/architecture/test_application_boundary.py already identifies focused application services as a boundary.
    desired_improvement: Continue extracting stable application-service seams while preserving API behavior, idempotency, owner scope and candidate/formal boundaries.
    potential_reference_capability: Use-case command handlers, workflow step registry, orchestration trace model.
    requires_tests_first: true
    public_contract_sensitive: true
    risk_level: high
    priority: P1
  - id: CAND-006
    title: App composition and configuration diagnostics
    problem: create_app constructs multiple infrastructure dependencies and runtime facades directly, increasing startup and test-injection coupling.
    modules:
      - App Bootstrap
      - Runtime Config
      - LLM Provider
    paths:
      - apps/api/app/main.py
      - apps/api/app/infrastructure/env_reader.py
      - apps/api/app/application/ai_runtime/runtime_flags.py
    evidence:
      - create_app configures DB session factory, LLM transport, embedding provider, job match analyzer, AI orchestration facade and auth runtime.
    desired_improvement: Make dependency composition and config failure summaries easier to inspect without changing runtime behavior.
    potential_reference_capability: Dependency container, config report, dry-run doctor command.
    requires_tests_first: true
    public_contract_sensitive: false
    risk_level: medium
    priority: P1
  - id: CAND-007
    title: AI Runtime and Eval evidence taxonomy
    problem: Deterministic/replay/fake/default-off evidence is valuable, but it must remain distinct from live-provider quality and production runtime readiness.
    modules:
      - AI Runtime
      - Eval Gate
      - Release evidence
    paths:
      - apps/api/app/application/ai_runtime
      - scripts/evals/run_eval_gate.py
      - scripts/evals/run_l5_eval_suite.py
      - tests/evals
    evidence:
      - Eval runners emit provider_evidence_type and non_claims.
      - RuntimeFlagResolver defaults graph/runtime to disabled unless explicitly enabled.
    desired_improvement: Strengthen report schema and release gates so evidence type cannot be confused with product readiness.
    potential_reference_capability: Evidence ledger, report schema validation, non-claim policy.
    requires_tests_first: true
    public_contract_sensitive: false
    risk_level: medium
    priority: P1
  - id: CAND-008
    title: Provider boundary redaction golden coverage
    problem: Provider boundary is security-critical and already has static tests; golden samples would make allowed/forbidden payload behavior easier to review.
    modules:
      - LLM Provider Boundary
      - Security / Privacy
    paths:
      - apps/api/app/application/llm/provider_boundary.py
      - tests/api/test_provider_boundary.py
      - tests/architecture/test_provider_boundary_static.py
    evidence:
      - Static tests enumerate forbidden keys such as raw_prompt, raw_completion, provider_payload, full_resume and api_key.
    desired_improvement: Add fixture/golden coverage for representative provider requests and sanitized trace summaries.
    potential_reference_capability: Payload sanitizer golden tests, privacy scanner, structured trace redaction.
    requires_tests_first: true
    public_contract_sensitive: true
    risk_level: medium
    priority: P1
  - id: CAND-009
    title: Doc Governor command dispatch maintainability
    problem: The CLI has a very large argparse setup and dispatch function.
    modules:
      - Doc Governor CLI
    paths:
      - tools/doc_governor/cli.py
      - tests/doc_governor
    evidence:
      - cli.py has 3774 lines.
      - tests/doc_governor contains 45 test files, giving refactor safety if scoped.
    desired_improvement: Consider command registry or per-command modules after higher-value product/test candidates.
    potential_reference_capability: Tool command registry, command metadata, help snapshot tests.
    requires_tests_first: false
    public_contract_sensitive: true
    risk_level: medium
    priority: P2
  - id: CAND-010
    title: Active developer command matrix
    problem: Verification and local setup commands are spread across AGENTS.md, package scripts, CI and historical docs/goals.
    modules:
      - Developer Experience
      - Test Policy
    paths:
      - AGENTS.md
      - package.json
      - apps/web/package.json
      - docs/00-governance/TEST_POLICY.md
    evidence:
      - README says local setup and verification commands are intentionally not expanded there.
      - AGENTS.md and package.json hold dev commands; docs/goals contains historical command variants.
    desired_improvement: Add or update an active command matrix only through existing governance rules.
    potential_reference_capability: Tool doctor, command catalog, validation profile metadata.
    requires_tests_first: false
    public_contract_sensitive: false
    risk_level: low
    priority: P2
```

# 9. Deferred or Rejected Areas

| 内容 | 处理建议 | 原因 | 证据 |
|---|---|---|---|
| 大爆炸式重构 `apps/api/app/application/polish` 或 `InterviewPage.tsx` | 暂缓 | 用户主路径和 contract 太多，需先补测试和稳定 seam。 | `tests/api/test_polish_*`、`InterviewPage.test.ts` |
| 直接实现 Pressure Mode | 暂缓 | 当前是 mode-level spec + skeleton；Backlog 尚未授权该实现作为当前任务。 | `docs/02-design/PRESSURE_MODE_SPEC.md`、`apps/api/app/api/v1/pressure.py` |
| 把 AI Runtime / LangGraph 默认打开 | 不建议 | README 和 runtime flags 明确 staged/default-off；eval 证据不等于 live-provider quality。 | `README.md`、`runtime_flags.py`、`scripts/evals/**` |
| 将 Training 当 MVP 独立产品模式强化 | 不建议 | 当前边界更像 legacy preserve-only，MVP remediation re-entry 应回 Polish 或 Pressure/Mock。 | `CAPABILITY_PRESERVATION_MATRIX.md`、route/nav 现状 |
| 只因文件大就拆 Doc Governor CLI | 暂缓 | 工程收益存在，但用户价值低于工作台、contract、CI baseline。 | `tools/doc_governor/cli.py`、`tests/doc_governor/**` |
| 引入新框架 / 新依赖解决测试或 schema | 暂缓待参考 Skill 分析 | 可能有效，但需先评估优秀 Skill 的实践和仓库治理约束。 | `package.json`、`requirements.txt`、AGENTS 写入边界 |
| 自动 codegen 前后端 API client | NEEDS_CONFIRMATION | 可降低 drift，但会引入生成文件、依赖和治理问题。 | 当前无 codegen 配置 |
| 真实 provider eval gate | NEEDS_CONFIRMATION | 用户价值高，但涉及密钥、成本、隐私、稳定性和 CI secret。 | `SECURITY_PRIVACY.md`、eval non-claims |

# 10. Open Questions

1. NEEDS_CONFIRMATION：下一阶段参考 Skill 是否包含可公开读取的 `SKILL.md`、examples、fixtures、tests 和工具入口？优先需要这些路径来比较能力设计。
2. NEEDS_CONFIRMATION：本轮后续强化是否优先服务产品主路径（Interview Workbench / Polish）还是工具治理路径（doc_governor / AI Skill system）？
3. NEEDS_CONFIRMATION：是否允许未来引入前端 runtime test runner（如 Vitest/Playwright）和必要依赖，还是必须先使用现有 `tsc --noEmit` harness？
4. NEEDS_CONFIRMATION：是否允许将 API schema drift 检查做成生成/快照类测试？这可能涉及生成文件治理。
5. UNKNOWN：当前远端 CI 是否还有未在 `.github/workflows/**` 中体现的外部保护规则；只读仓库内未发现。

下一阶段参考 Skill 重点分析能力：

- Skill / Tool 的 command discovery 和 registry 结构。
- 输入输出 schema、contract validation、golden fixtures。
- 状态 / evidence / trace / non-claim 记录方式。
- 错误分类、可诊断报告和用户可读 remediation。
- 测试分层：unit、contract、integration、snapshot/golden、negative control。
- 插件扩展点和 public API 兼容策略。

# 11. Evidence Index

## Governance and Active Docs

- `AGENTS.md`：中文协作、active docs、写入边界、本地 dev 命令。
- `docs/00-governance/DOCS_INDEX.md`：当前有效文档索引和 archive / docs/goals 边界。
- `docs/03-delivery/BACKLOG.md`：AIFI task 状态，F5 后端与 PR2/Runtime scope。
- `docs/03-delivery/DELIVERY_PLAN.md`：F0-F8 阶段状态和 F5/F6/F7/F8 退出标准。
- `docs/03-delivery/refactor/CAPABILITY_PRESERVATION_MATRIX.md`：implemented / partial / skeleton / design-only 分类和 non-claim guard。
- `docs/03-delivery/refactor/BASELINE_30f7237_CAPABILITY_MAP.md`：capability baseline。

## Backend Code

- `apps/api/app/main.py`：FastAPI app factory、dependency composition、runtime/logging/CORS/router。
- `apps/api/app/api/v1/__init__.py`：v1 router composition。
- `apps/api/app/api/v1/polish.py`：Polish HTTP adapter。
- `apps/api/app/application/polish/use_cases.py`：Polish aggregate orchestration。
- `apps/api/app/application/polish/feedback_rules.py`：feedback policy bridge。
- `apps/api/app/domain/polish/policies/**`：pure domain policies。
- `apps/api/app/application/llm/provider_boundary.py`：provider request validation/redaction boundary。
- `apps/api/app/infrastructure/llm/runtime.py`：LLM transport env wiring and fake fail-closed.
- `apps/api/app/application/ai_runtime/facade.py`：AI orchestration facade。
- `apps/api/app/application/ai_runtime/runtime_flags.py`：default-off runtime flag resolver。
- `apps/api/app/application/ai_runtime/business_graphs/**`：default-off / skeleton graph evidence.

## Frontend Code

- `apps/web/package.json`：React/Vite dependencies and build/test scripts.
- `apps/web/tsconfig.json`：strict TypeScript config, includes `src`.
- `apps/web/vite.config.ts`：Vite API proxy.
- `apps/web/src/app/routes/router.tsx`：custom route provider and active frontend routes.
- `apps/web/src/shared/api/client.ts`：fetch wrapper and API error parsing.
- `apps/web/src/shared/api/envelope.ts`：hand-written API envelope types.
- `apps/web/src/pages/interview/InterviewPage.tsx`：core interview list/workbench implementation.
- `apps/web/src/pages/interview/InterviewPage.test.ts`：TypeScript contract harness.
- `apps/web/src/entities/polish/api/polishApi.ts`：Polish frontend API paths and calls.

## Tests and CI

- `pytest.ini`：pytest config and test paths.
- `.github/workflows/eval-gate.yml`：eval-only GitHub workflow.
- `tests/architecture/test_application_boundary.py`：domain/application boundary import guards.
- `tests/architecture/test_domain_polish_policy_boundary.py`：Polish policy boundary and bridge guards.
- `tests/architecture/test_provider_boundary_static.py`：provider boundary static scanner.
- `tests/api/test_route_inventory.py`：route inventory baseline.
- `tests/api/test_capability_preservation_inventory.py`：implemented vs skeleton route inventory.
- `tests/api/test_skeleton_guard.py`：status vocabulary and non-claim guard.
- `tests/api/test_polish_api.py`、`tests/api/test_polish_question_refactor_phase1.py`、`tests/api/test_polish_feedback_*`：Polish core regression coverage.
- `tests/domain/polish/**`：domain policy tests.
- `tests/evals/**`：Phase 9 / Phase 12 eval tests.

## Tools and Eval

- `scripts/evals/run_eval_gate.py`：Phase 9 deterministic/replay eval runner.
- `scripts/evals/run_l5_eval_suite.py`：Phase 12 L5 deterministic eval runner.
- `evals/suites/phase9.json`、`tests/evals/phase12/suite.json`：eval manifests.
- `evals/datasets/**`：JSONL fixtures.
- `tools/doc_governor/cli.py`：doc-governor CLI command surface.
- `tools/doc_governor/**`、`tests/doc_governor/**`：文档治理工具和测试。

## Unknowns

- UNKNOWN：是否存在外部 CI required checks 不在 `.github/workflows/**` 中。
- UNKNOWN：是否计划将 `docs/feature-enhancement/**` 登记为 active docs；当前 `DOCS_INDEX.md` 未登记该目录为 active truth。
- UNKNOWN：未来参考 Skill 的具体路径和能力结构。

---
title: F5_BACKEND_IMPLEMENTATION_NOTES
type: implementation-note
status: f5-m0-baseline
owner: Backend
source_task: AIFI-BE-001
permalink: ai-for-interviewer/docs/03-implementation/f5-backend-implementation-notes-1
---

# F5 后端实现说明

## 1. F5-M0 目标

本文件记录 `AIFI-BE-001` 的 F5-M0 后端基础骨架与契约基线。本轮只建立 FastAPI 后端分层、Contract Baseline、Fake LLM Transport、SQLAlchemy model skeleton 和最小 API contract tests，不实现完整业务闭环，不启动 F6 / F7 / F8。

## 2. 已读取的设计输入

- `docs/02-design/reviews/F4_TO_F8_READINESS_ACCEPTANCE.md`
- `docs/03-implementation/DELIVERY_PLAN.md`
- `docs/03-implementation/BACKLOG.md`
- `docs/02-design/TECH_DESIGN.md`
- `docs/02-design/API_SPEC.md`
- `docs/02-design/DATA_MODEL.md`
- `docs/02-design/PERSISTENCE_MODEL.md`
- `docs/02-design/APPLICATION_FLOW_SPEC.md`
- `docs/02-design/SCORING_SPEC.md`
- `docs/02-design/SEMANTICS_GLOSSARY.md`
- `docs/02-design/PROMPT_SPEC.md`
- `docs/02-design/SECURITY_PRIVACY.md`
- `docs/02-design/RELEASE_HANDOFF_SPEC.md`
- `requirements.txt`
- `apps/api/app/main.py`
- `apps/api/app/api/v1/__init__.py`
- `apps/api/app/api/v1/health.py`

确认结果：F4 / M4 已 `Accepted`，F5 为 `READY_TO_START`，当前 API 入口是 FastAPI，`/api/v1/health` 已存在，依赖已有 FastAPI、SQLAlchemy、psycopg、pytest，本轮不需要新增依赖。

## 3. 本轮实现的 skeleton

| 层 | 本轮内容 |
|---|---|
| API | 新增 `deps.py`、`envelope.py`、`errors.py`、`/api/v1/contract-baseline` 和各业务 router boundary；保留 `/api/v1/health` |
| application | 新增 common primitives、各纵向模块的 command / query / use case / port 占位 |
| domain | 新增 shared kernel：ID、Ref、Trace、Evidence、Validation、DomainError、canonical enum；新增各业务域 entity / value object / service / event / port 骨架 |
| infrastructure | 新增 SQLAlchemy `Base`、session factory placeholder、Unit of Work placeholder、model skeleton、repository skeleton、安全与观测 adapter placeholder |
| schemas | 新增 `ApiSuccessEnvelope`、`ApiErrorEnvelope`、refs、pagination、resume/job/ai task/scoring 等 Pydantic DTO skeleton |
| shared | 新增低耦合 `constants.py`、`text.py`、`collections.py`；未创建无边界 `utils.py` |
| fake LLM | 新增 `FakeLlmTransport`，只返回 deterministic structured result，不调用真实 provider |
| tests | 新增 API bootstrap、contract baseline、enum、Fake LLM、route inventory、architecture boundary、model import tests |

## 4. 本轮未实现的业务能力

- 不实现真实 LLM provider。
- 不接入真实外部服务。
- 不实现完整 Resume / Job / Binding / Job Match / Polish / Pressure / Report / Review / Asset / Weakness / Training 业务闭环。
- 不实现文件上传解析、外部材料解析生成岗位、文件产物生成或下载能力。
- 不返回精确通过概率、offer 概率、录取概率或通过率百分比。
- 不暴露 system prompt、provider payload、completion 原文、hidden scoring rules、secret、token、cookie。
- 不把 candidate / suggestion 静默写成 formal object。
- 不创建 migration；如 F5-M1 / F5-M2 需要落库，再基于 `PERSISTENCE_MODEL.md` 冻结 migration 策略。

## 5. 后续模块顺序

- F5-M1 Resume
- F5-M2 Job + Binding
- F5-M3 Job Match + Scoring
- F5-M4 Polish Core
- F5-M5 Report + Copy
- F5-M6 Review
- F5-M7 Asset + Weakness
- F5-M8 Training
- F5-M9 Pressure

## 6. 后端目录说明

后端按 Pragmatic DDD + Clean Architecture 分层：

- `api/`：HTTP adapter、FastAPI router、dependency、envelope、error mapping、route composition。
- `application/`：use case、command、query、application service、transaction / idempotency boundary、port 调用。
- `domain/`：entity、value object、domain service、domain event、repository port、canonical enum、typed ref、trace / evidence / validation 概念。
- `infrastructure/`：SQLAlchemy model、repository implementation、Unit of Work implementation、Fake LLM transport、DB session、安全和观测 adapter。
- `schemas/`：Pydantic request / response DTO、envelope、refs、error schema。
- `shared/`：低耦合无业务工具。

边界约束：domain 不 import FastAPI / SQLAlchemy / Pydantic / infrastructure；application 不 import FastAPI / infrastructure；api 不 import `infrastructure.db.models`，也不直接调用 LLM transport。

## 7. F6 前端目录建议

F5-M0 不修改 `apps/web/**`。F6 推荐采用 Feature-Sliced Design + Domain UI Model：

```text
apps/web/src/
  app/
    App.tsx
    main.tsx
    providers/
    routes/
  pages/
    dashboard/
    resumes/
    jobs/
    polish/
    pressure/
    reports/
    reviews/
    assets/
    weaknesses/
    training/
  widgets/
    app-shell/
    sidebar/
    topbar/
    job-match-summary/
    interview-progress-tree/
    report-viewer/
    candidate-confirmation-drawer/
  features/
    resume-create/
    resume-edit/
    job-create/
    job-bind-resume/
    job-match-generate/
    polish-session-start/
    polish-answer-submit/
    polish-feedback-view/
    report-copy/
    review-create/
    asset-candidate-confirm/
    weakness-candidate-confirm/
    training-suggestion-confirm/
  entities/
    resume/
      model/
      api/
      ui/
    job/
    job-match/
    interview-session/
    question/
    answer/
    feedback/
    score/
    ai-task/
    report/
    review/
    asset/
    weakness/
    training/
  shared/
    api/
      client.ts
      envelope.ts
      errors.ts
      refs.ts
    config/
    hooks/
    lib/
      date.ts
      ids.ts
      text.ts
    ui/
      EmptyState.tsx
      ErrorState.tsx
      LoadingState.tsx
      StatusBadge.tsx
      CopyButton.tsx
    types/
      enums.ts
      refs.ts
      envelope.ts
```

F6 约束：

- `pages/` 只做页面组合。
- `widgets/` 放跨 feature 的页面区块。
- `features/` 放用户动作闭环。
- `entities/` 放业务实体 UI model、API adapter 和实体展示组件。
- `shared/` 放 API client、envelope、error handling、refs、通用 UI、hooks、工具函数。
- 前端不得从 UX/UI 反向发明 API 字段。
- 前端不得绕过 entity / shared API adapter 直接在页面中拼 fetch。
- 前端不得自造后端未定义的 score、low confidence、source availability、candidate / suggestion / formal object 字段。

## 8. 与设计文档的对应关系

| 文档 | 本轮对应 |
|---|---|
| `API_SPEC.md` | response / error envelope、stable error code、route boundary、no exact probability、no provider payload、copy / export boundary |
| `PERSISTENCE_MODEL.md` | SQLAlchemy model skeleton、owner / actor / version / status / trace / evidence 字段、reference table skeleton |
| `APPLICATION_FLOW_SPEC.md` | use case / command / query / port 边界、Fake LLM 可用于 deterministic orchestration fixture |
| `SCORING_SPEC.md` | `ScoreType`、0-100 product scale、confidence、validation、pass tendency、risk level、no exact probability |
| `SEMANTICS_GLOSSARY.md` | `confidence_level`、`validation_status`、`source_availability`、candidate / suggestion / formal object 边界 |
| `SECURITY_PRIVACY.md` | auth / session foundation、owner placeholder、trace / audit 最小暴露、Prompt / provider / completion / hidden scoring rules 禁止暴露 |
| `RELEASE_HANDOFF_SPEC.md` | route inventory、no export、provider failure、trace / audit、migration / rollback 后续输入 |

## 9. F5 auth / session foundation baseline

本轮在 F5-M0 skeleton 之上补齐第一批登录闭环后端 foundation：

- 新增 `domain/auth`、`application/auth`、`infrastructure/security`、`schemas/auth.py` 和 `api/v1/auth.py`，保持 domain 不依赖 FastAPI / SQLAlchemy / Pydantic / infrastructure，application 不依赖 FastAPI，router 只做 HTTP adapter。
- 新增 `POST /api/v1/auth/login`、`GET /api/v1/auth/me`、`POST /api/v1/auth/logout`；不新增 `GET /api/v1/auth/session`，因为 `/auth/me` 已覆盖 session validity 和 current user summary。
- 当前使用 in-memory user store 与 server-side session store，只作为 F5 foundation baseline；session cookie 名为 `aifi_session`，`HttpOnly`、`SameSite=Lax`、`Path=/api/v1`，local dev 默认不强制 `Secure`，非本地环境可通过配置开启。
- dev seed 凭据不再硬编码；`/api/v1` 登录种子改为 `API_AUTH_*` 环境变量驱动，`API_AUTH_DEV_USER_PASSWORD` 必填（当 `API_AUTH_DEV_USER_ENABLED=true` 且本地-like 时），未提供时默认不 seed（fail-closed）。
- 密码 baseline 使用标准库 `hashlib.pbkdf2_hmac`、`secrets.token_bytes` 和 `hmac.compare_digest`；响应、日志和 error envelope 不返回 password、password hash、salt、cookie、raw token 或 session digest。
- 当前 dev/test seed user 仅用于 local/test baseline，不代表生产账号体系，不记录或响应 seed password / hash / salt。
- 已新增 auth API、dependency、password/session store、route inventory 和 architecture boundary 测试，验证登录成功设置 HttpOnly cookie、错误密码 401、无 cookie 访问 `/auth/me` 401、cookie 登录态返回用户摘要、logout 清 cookie、无敏感字段暴露、无 `utils.py` 和无 export / download / upload 路由。

本轮不处理生产级账号注册、密码策略、邮件验证、OAuth / SSO、组织权限、多设备管理、持久化 session、CSRF token、登录限流或账号锁定。后续进入更完整 F5 hardening 时，需要补 DB migration、persistent session store、CSRF / rate-limit、审计持久化、账号禁用联动和部署 secret 策略。

## 9.1. 本轮 CORS baseline（本地开发）

- 已在 `apps/api/app/main.py` 增加本地开发 CORS baseline，使用 FastAPI/Starlette 内置 `CORSMiddleware`，默认 `allow_credentials=True`。
- 默认允许本地 origin：
  - `http://127.0.0.1:5173`
  - `http://localhost:5173`
  - `http://127.0.0.1:5174`
  - `http://localhost:5174`
- `OPTIONS` 与主流程允许的方法默认包含 `GET`、`POST`、`OPTIONS`。
- 允许的请求头默认包含 `Content-Type`、`Accept`、`Authorization`。
- `API_CORS_ALLOW_ORIGINS` 支持逗号分隔配置；缺省时按 `local`/`dev`/`test`/`development` 环境默认上述本地 origin；在生产语义下缺省空白列表。
- credentials 模式下禁止 `*`，若环境变量中包含 `*` 会在运行期去除。
- 不新增路由，也不改变现有 auth envelope / cookie 行为（`HttpOnly`、`SameSite=Lax` 等保持不变）。

## 10. 风险和后续待办

- 当前 SQLAlchemy model 是 skeleton，未冻结 DDL、索引、migration 和真实 repository 查询。
- 当前 auth / session 已具备 F5 foundation baseline，但仍是 in-memory store，尚未落库，也未实现 CSRF / rate-limit / 多设备管理 / persistent revocation。
- 当前 owner dependency 已从 `X-User-Id` placeholder 收敛为 cookie session actor baseline；F5-M1 起仍必须按业务资源逐步补齐 owner-scoped repository 查询和二次 owner enforcement。
- 当前业务 router 只登记边界，不返回伪造业务数据。
- 当前 Fake LLM 只用于 contract tests，不代表 Prompt 文案、provider 参数或真实生成质量。
- 下一步建议进入 F5-M1 Resume module：实现 Markdown 简历保存、版本引用、owner scope、最小 repository 和对应 API contract tests。

## 12. 本轮 dev seed 凭据配置方式（本地）

- 本地可使用 `.env` 注入如下变量（或临时导出）：
  - `API_AUTH_DEV_USER_ENABLED`
  - `API_AUTH_DEV_USER_IDENTIFIER`
  - `API_AUTH_DEV_USER_EMAIL`
  - `API_AUTH_DEV_USER_USERNAME`
  - `API_AUTH_DEV_USER_DISPLAY_NAME`
  - `API_AUTH_DEV_USER_PASSWORD`
- 建议加载示例：
  ```bash
  set -a
  . ./.env
  set +a
  python3 -m uvicorn apps.api.app.main:app --reload --host 127.0.0.1 --port 8000
  ```
- `.env.example` 只包含占位值，不含真实密码；`API_AUTH_DEV_USER_PASSWORD` 建议保持为 `change-me-local-only`。
- `.env` 默认不提交，仓库以 `.gitignore` 统一过滤；即使本地启用 seed，也不代表生产账号体系。生产/非 local-like 环境默认不启用 seed。

## 11. F5 第 2 批前端基础落地（本轮）

- 已建立 `apps/web/src` 的前端最小骨架，采用 Feature-Sliced Design + Domain UI Model 划分：
  - `app/`：应用入口、provider、路由管理。
  - `features/`：`auth-login`、`auth-logout` 的 API 与模型。
  - `entities/`：`user` 的模型与 API adapter。
  - `pages/`：`login` 与 `dashboard` 基础页。
  - `widgets/app-shell`：`AppShell`、`Topbar`、`Sidebar`、`UserMenu`。
  - `shared/`：API client、envelope、error、config、hooks、基础 UI 组件。
- 新增共享 API client：默认 `base url = /api/v1`，支持 `VITE_API_BASE_URL` 覆盖，统一 `credentials: "include"`，解析 success/error envelope，401 统一归类为 `unauthenticated`。
- 新增 auth state：包含 `currentUser/loading/error/login/logout/refreshCurrentUser`。
- 登录页要求达成：
  - `identifier`（邮箱/用户名）与 `password` 输入。
  - 登录提交 loading、错误提示。
  - 登录成功后由路由守卫进入 `/dashboard`。
- Dashboard Shell 达成：
  - Topbar、侧边栏、用户状态区、内容区。
  - 模块导航仅占位（`工作台 / 简历 / 岗位 / 打磨模式 / 压力面 / 报告 / 复盘 / 资产库 / 薄弱项 / 训练建议`），仅占位卡片与 disabled placeholder，不调用业务接口。
- 安全边界约束（本轮）：
  - 不使用 localStorage / sessionStorage 存储 token、cookie 或凭据。
  - 不新增依赖，不直接在页面拼接 `fetch`。
  - 不展示 cookie、session、token、provider payload、system prompt、隐藏评分规则等敏感内容。
  - 不展示精确概率与文件导出入口（PDF/docx/Markdown 下载不包含）。

## 13. Registry de-layer 后的已确认实现映射

本节迁入原 capability / planning 来源文档中的实现映射。原 standalone 来源文档删除后，本节只保留已验证的实现路径、测试证据和 non-claim，不创建新的能力定义。

### 13.1 Interview Coach G-003 / G-004 / Composition

| 能力切片 | 实现路径 | 验证证据 | non-claim |
|---|---|---|---|
| G-003 Transcript Structured Signal Extraction | `apps/api/app/application/polish/transcript_signal_parser.py`、`feedback_generation_service.py`、`feedback_prompt_assets.py` | 迁移证据记录 GREEN：`67 passed in 0.96s` with `AI_FOR_INTERVIEWER_ALLOW_TEST_DIR_LEAKS=1`；测试包括 `tests/api/test_polish_transcript_signal_parser.py`、`test_polish_feedback_generation_service.py`、`test_polish_feedback_pipeline_contract.py`、`test_polish_feedback_agent_io_alignment.py` | 只服务 evaluation / feedback，不成为 G-004、scoring、taxonomy 或 coaching |
| G-004 Transcript Understanding | `apps/api/app/application/transcript_analysis/models.py`、`parser.py`、`analyzer.py`、`service.py` | `tests/api/test_transcript_analysis.py`、`tests/api/test_transcript_analysis_contract_lock.py`；迁移 GREEN 证据覆盖 | 只拥有 `transcript_analysis_v1`；不输出 feedback、score、rubric verdict 或 coaching plan |
| Composition Layer | `apps/api/app/application/composition/service.py` | `tests/api/test_composition_layer.py` 覆盖 mode routing、analysis mode 不调用 G-003、G-003 / G-004 replacement independence 与 response field isolation | 只做 envelope-level routing / packaging，不做语义转换 |

### 13.2 Capability preservation baseline

| 能力 | 当前状态 | 核心路径 | 测试证据 | 边界 |
|---|---|---|---|---|
| Resume | `implemented` | `apps/api/app/api/v1/resumes.py`、`application/resumes/use_cases.py`、`infrastructure/db/repositories/resumes.py` | `tests/api/test_resumes_api.py`、`apps/web/src/pages/resume/ResumePage.test.ts` | 不包含 evidence extraction / derived outline |
| Job | `implemented` | `apps/api/app/api/v1/jobs.py`、`application/jobs/use_cases.py`、`infrastructure/db/repositories/jobs.py` | `tests/api/test_jobs_api.py`、`tests/web/test_job_page_pagination.py`、`apps/web/src/pages/job/JobPage.test.ts` | 不包含 JD decode flow / 外部材料解析 |
| Binding | `implemented` | `apps/api/app/api/v1/bindings.py`、`application/bindings/use_cases.py`、`infrastructure/db/repositories/bindings.py` | `tests/api/test_bindings_api.py`、`test_job_binding_owner_scope.py`、`test_resume_binding_candidates.py` | 不包含完整历史报告 / 复盘回看流 |
| Polish session / answer | `implemented` | `apps/api/app/api/v1/polish.py`、`session_application_service.py`、`answer_application_service.py`、`infrastructure/db/repositories/polish.py` | `tests/api/test_polish_api.py`、`apps/web/src/pages/interview/InterviewPage.test.ts` | 不包含 pressure session、generic interview 或 feedback/scoring quality |
| Polish module split | `implemented` | `apps/api/app/usecases/polish/fetch_candidate.py`、`apply_feedback.py`、`persist_result.py`、`repositories/polish_repository.py` | `tests/api/test_polish_m25_usecases.py`、`test_polish_application_service_split.py`、`test_polish_api.py`、`InterviewPage.test.ts` | 只代表 conservative split；aggregate Polish 仍是 `partial` |
| Assets | `implemented` | `apps/api/app/api/v1/assets.py`、`application/assets/use_cases.py`、`infrastructure/db/repositories/assets.py` | `tests/api/test_assets_weaknesses_api.py`、`apps/web/src/pages/asset/AssetPage.test.ts` | RAG chunks 存在不证明 all-runtime RAG |

### 13.3 Provider / Agent / Runtime / Eval implementation evidence

| 能力切片 | 实现路径 | 验证证据 | 边界 |
|---|---|---|---|
| Provider boundary | `apps/api/app/application/llm/provider_boundary.py`、`types.py`、Polish feedback / question / progress / job match provider call sites | P7-W4.fix.01 记录 full-repo pytest `1067 passed`、`npm run web:test`、`npm run web:smoke:auth`、provider focused selector `21 passed`、`git diff --check`；测试包括 `tests/api/test_provider_boundary.py`、`test_provider_global_backstop.py`、`tests/architecture/test_provider_boundary_static.py` | 不声明 real-provider quality certification |
| Runtime fake provider isolation | `apps/api/app/infrastructure/llm/runtime.py`、`feedback_generation_service.py`、`scripts/qa/authenticated-frontend-smoke.mjs`、`.github/workflows/eval-gate.yml` | `tests/api/test_llm_runtime.py`、`test_fake_llm_boundary.py`、`test_fake_llm_transport.py`；auth smoke 不依赖 `LLM_PROVIDER=fake` | fake / replay evidence 只算 regression evidence |
| Agent definitions / handoff contracts | `apps/api/app/application/agents/definitions/**`、`agents/contracts/__init__.py`、`agents/handoff/__init__.py`、`agents/runtime/__init__.py` | `tests/architecture/test_agent_platform_c1_boundary.py`、`tests/api/test_agent_contracts.py` | candidate / suggestion / validation / trace only；formal writes 仍归 Application Service / Domain Policy / Handoff |
| Question / Feedback planned workflows | `polish/agents/question/planned_workflow.py`、`question_application_service.py`、`feedback/planned_workflow.py`、`feedback_application_service.py`、`feedback_rules.py` | Question evidence includes `12 passed` graph integration、`15 passed` persistence handoff、`64 passed` phase1 refactor；Feedback evidence includes runtime `7 passed` and local eval `5 passed / 0 failed` | `validated_with_deferred_l5_runtime` 不等于 full runtime productization |
| AI Runtime / L5 local multi-agent | `ai_runtime/facade.py`、`agents/runtime/__init__.py`、`infrastructure/ai_runtime/langgraph/in_memory_runtime.py`、`agents/orchestration/minimal_three_agent_slice.py`、`business_graphs/local_multi_agent_orchestrator.py` | `tests/api/test_ai_orchestration_facade.py`、`tests/application/agents/test_phase11_runtime_hardening.py`、`test_phase11_three_agent_product_slice.py`、`test_option_d_local_multi_agent_runtime_wiring.py`、`tests/evals/test_phase12_l5_eval_gate.py` | default-off / local deterministic / refs-only；不声明 production L5 release、remote CI hard claim 或 real-provider certification |
| Eval regression gate | `evals/suites/phase9.json`、`evals/datasets/phase9/*.jsonl`、`scripts/evals/run_eval_gate.py`、`tests/evals/test_phase9_eval_gate.py`、`.github/workflows/eval-gate.yml` | 迁移证据记录 local replay gate `30 passed`、`0 blocking_failures`、`2 deferred`；negative control observed expected failure | `validated` 不是 `done`；remote GitHub Actions evidence remains deferred |

### 13.4 Explicit non-claims after de-layering

- No production L5 release is claimed.
- No real-provider production quality certification is claimed.
- No remote CI hard claim is made without visible passing GitHub Actions artifact evidence.
- P8 Runtime remains `validated_with_deferred_gaps` / partial foundation, not full product runtime completion.
- `L5-006B` remains deferred and out of scope.
- route prefix、DB model、disabled frontend nav、fallback、deterministic / replay / fake / mock eval、default-off graph 不能单独证明产品能力已实现。

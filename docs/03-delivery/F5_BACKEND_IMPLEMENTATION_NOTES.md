---
title: F5_BACKEND_IMPLEMENTATION_NOTES
type: implementation-note
status: f5-m0-baseline
owner: Backend
source_task: AIFI-BE-001
permalink: ai-for-interviewer/docs/03-delivery/f5-backend-implementation-notes
---

# F5 后端实现说明

## 1. F5-M0 目标

本文件记录 `AIFI-BE-001` 的 F5-M0 后端基础骨架与契约基线。本轮只建立 FastAPI 后端分层、Contract Baseline、Fake LLM Transport、SQLAlchemy model skeleton 和最小 API contract tests，不实现完整业务闭环，不启动 F6 / F7 / F8。

## 2. 已读取的设计输入

- `docs/02-design/reviews/F4_TO_F8_READINESS_ACCEPTANCE.md`
- `docs/03-delivery/DELIVERY_PLAN.md`
- `docs/03-delivery/BACKLOG.md`
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
| `SECURITY_PRIVACY.md` | owner placeholder、trace / audit 最小暴露、Prompt / provider / completion / hidden scoring rules 禁止暴露 |
| `RELEASE_HANDOFF_SPEC.md` | route inventory、no export、provider failure、trace / audit、migration / rollback 后续输入 |

## 9. 风险和后续待办

- 当前 SQLAlchemy model 是 skeleton，未冻结 DDL、索引、migration 和真实 repository 查询。
- 当前 auth / owner dependency 只是 F5-M0 placeholder，F5-M1 起必须按 `SECURITY_PRIVACY.md` 冻结真实 session / owner enforcement。
- 当前业务 router 只登记边界，不返回伪造业务数据。
- 当前 Fake LLM 只用于 contract tests，不代表 Prompt 文案、provider 参数或真实生成质量。
- 下一步建议进入 F5-M1 Resume module：实现 Markdown 简历保存、版本引用、owner scope、最小 repository 和对应 API contract tests。


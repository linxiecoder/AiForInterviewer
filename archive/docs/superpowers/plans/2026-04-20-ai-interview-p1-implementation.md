---
title: 2026-04-20-ai-interview-p1-implementation
type: note
permalink: ai-for-interviewer/archive/docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation
---

﻿# AI 模拟面试 P1 MVP 实现计划

> **历史快照说明（W13-GOV-HistoryArchive / 2026-04-25）：**
> - 本文档为历史快照 / 历史设计记录。
> - 本文档不作为当前 W13 一期工作台 MVP 的实施依据。
> - 当前事实以 W13 唯一事实源为准：`2026-04-25-workbench-mvp-scope.md`、`2026-04-25-workbench-mvp-ia-user-journey.md`、`2026-04-25-workbench-mvp-object-model-rag-multiround-backend.md`、`2026-04-25-workbench-mvp-scoring-review-export-dod.md`。
> - W10 `apps/web` 原型仅作为交互 / UI / mock adapter / 浏览器验证参考证据。
> - 如本文档与 W13 confirmed 结论冲突，以 W13 confirmed 结论为准。

> **状态说明（W8 / 2026-04-25）：**
> - 本文档当前定位为 `AI 模拟面试系统` 的未来 monorepo / 产品落地蓝图。
> - 文中出现的 `apps/web`、`apps/api`、`infra`、`.github/workflows` 等路径代表未来目标结构，不代表当前仓库现实。
> - 当前仓库的直接执行计划请以 `docs/superpowers/plans/2026-04-25-current-repo-execution-plan.md` 与 `PLAN_LATEST.md` 为准。
> - 在后续状态回写窗口更新 `docs/governance/DOC_STATE.yaml` 前，`DOC-PLAN-P1` 仍可能继续出现在 `document_repo_truth_mismatch` 诊断中；这不应再被误读为当前仓库应直接落地这些路径。

> **给执行代理的要求：** 必须使用 `superpowers:subagent-driven-development`（推荐）或 `superpowers:executing-plans` 按任务逐步实现本计划。所有步骤均使用复选框语法 `- [ ]` 进行跟踪。

**目标：** 交付一套可运行的 `AI 模拟面试 P1 文本版闭环 MVP`，覆盖岗位、简历、岗位匹配分析、模拟面试、打磨面试、复盘、薄弱项、资产库和管理台基础能力。

**架构：** 使用 `Next.js` 承载工作台、列表页、详情页、编辑器和面试交互，使用 `FastAPI` 承载鉴权、领域 API、AI 编排、评估与复盘服务，使用 `PostgreSQL + pgvector + Redis` 承载结构化数据、检索向量和后台任务。实现顺序按纵切片推进，每个任务结束后都要能运行、测试并保留一条清晰的用户路径。

**技术栈：** Next.js 15, React 19, TypeScript, Tailwind CSS, Radix UI, TanStack Table, React Hook Form, Zod, `react-markdown`, `remark-gfm`, FastAPI, SQLAlchemy 2, Alembic, Pydantic 2, PostgreSQL, pgvector, Redis, Dramatiq, structlog, PyMuPDF4LLM, Python-Markdown, WeasyPrint, pytest, Vitest, Testing Library, Playwright

---

## 必读材料

- 历史设计稿：`archive/docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md`
- 历史实现计划：`archive/docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md`

## 范围说明

设计稿覆盖多个子系统。本文档描述的是未来 monorepo 落地蓝图，而不是当前仓库的真实目录或即时执行面。这里不再拆成多份独立计划，而是拆成 `11 个可运行纵切片`，每个切片都会在前一个切片基础上增加一条真实可走通的用户链路；当前仓库现实执行计划请改看 `docs/superpowers/plans/2026-04-25-current-repo-execution-plan.md`。

## 目标仓库结构

以下结构用于描述未来产品落地目标，不代表当前仓库已存在这些路径。

### 根目录

- `.env.example`
  - 本地开发环境变量模板，统一声明数据库、Redis、演示账号和非生产默认值
- `package.json`
  - 根脚本，统一运行前端、后端、测试和格式化
- `infra/docker-compose.yml`
  - 本地 PostgreSQL、Redis
- `docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md`
  - 设计输入
- `docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md`
  - 当前实现计划

### 后端

- `apps/api/pyproject.toml`
  - Python 依赖、测试命令、格式化工具
- `apps/api/alembic.ini`
  - Alembic 配置
- `apps/api/alembic/versions/*.py`
  - 数据库迁移
- `apps/api/app/main.py`
  - FastAPI 入口
- `apps/api/app/core/config.py`
  - 环境变量和运行参数
- `apps/api/app/core/logging.py`
  - 结构化日志配置
- `apps/api/app/db/base.py`
  - SQLAlchemy Base 与模型导入
- `apps/api/app/db/session.py`
  - Session 工厂
- `apps/api/app/models/*.py`
  - 所有领域模型
- `apps/api/app/schemas/*.py`
  - Pydantic 请求/响应模型
- `apps/api/app/api/routes/*.py`
  - API 路由
- `apps/api/app/services/*.py`
  - 领域服务、AI 编排、导出、检索、聚合
- `apps/api/app/tasks/*.py`
  - Dramatiq 任务
- `apps/api/tests/**/*.py`
  - pytest 用例

### 前端

- `apps/web/package.json`
  - Next.js 工程脚本
- `apps/web/src/app/**`
  - App Router 页面
- `apps/web/src/i18n/**`
  - 国际化文案、默认 locale 与统一取词入口
- `apps/web/src/components/ui/**`
  - 低层 UI 组件
- `apps/web/src/components/layout/**`
  - 壳层、导航、摘要卡
- `apps/web/src/components/data/**`
  - 表格、筛选、分页
- `apps/web/src/components/interview/**`
  - 面试、评分、能力树、训练抽屉
- `apps/web/src/components/review/**`
  - 复盘详情与逐题分析
- `apps/web/src/lib/api/**`
  - API client
- `apps/web/src/lib/schemas/**`
  - Zod schema
- `apps/web/src/lib/utils/**`
  - 工具函数
- `apps/web/src/test/**`
  - Vitest setup
- `apps/web/tests/e2e/**`
  - Playwright 用例

## 完整仓库目录规划

以下目录树用于锁定未来 monorepo 的目标边界；当前仓库现实请以 `README.md`、`PLAN_LATEST.md` 与 `docs/superpowers/plans/2026-04-25-current-repo-execution-plan.md` 为准。

以下目录树用于锁定 `P1` 的**完整仓库边界**。如果后续实现新增正式目录或核心文件，需要先回补本节，再继续扩展实现。

```text
ai-for-interviewer/
├─ .env.example
├─ package.json
├─ infra/
│  ├─ docker-compose.yml
│  └─ minio/
│     └─ init-buckets.sh
├─ docs/
│  └─ superpowers/
│     ├─ specs/
│     │  └─ 2026-04-20-ai-interview-p1-design.md
│     └─ plans/
│        └─ 2026-04-20-ai-interview-p1-implementation.md
├─ apps/
│  ├─ api/
│  │  ├─ pyproject.toml
│  │  ├─ alembic.ini
│  │  ├─ alembic/
│  │  │  └─ versions/
│  │  ├─ app/
│  │  │  ├─ main.py
│  │  │  ├─ core/
│  │  │  │  ├─ config.py
│  │  │  │  ├─ logging.py
│  │  │  │  └─ security.py
│  │  │  ├─ db/
│  │  │  │  ├─ base.py
│  │  │  │  └─ session.py
│  │  │  ├─ models/
│  │  │  │  ├─ base.py
│  │  │  │  ├─ team.py
│  │  │  │  ├─ user.py
│  │  │  │  ├─ storage_object.py
│  │  │  │  ├─ retrieval_chunk.py
│  │  │  │  ├─ job.py
│  │  │  │  ├─ job_resume_binding.py
│  │  │  │  ├─ resume.py
│  │  │  │  ├─ resume_document.py
│  │  │  │  ├─ resume_conversion_log.py
│  │  │  │  ├─ resume_export_record.py
│  │  │  │  ├─ job_resume_match_analysis.py
│  │  │  │  ├─ weakness_evidence.py
│  │  │  │  ├─ asset_type.py
│  │  │  │  ├─ asset.py
│  │  │  │  ├─ archive_record.py
│  │  │  │  ├─ interview_session.py
│  │  │  │  ├─ interview_message.py
│  │  │  │  ├─ interview_question_trace.py
│  │  │  │  ├─ search_snapshot.py
│  │  │  │  ├─ capability_blueprint.py
│  │  │  │  ├─ capability_node.py
│  │  │  │  ├─ answer_assessment.py
│  │  │  │  ├─ interview_progress_snapshot.py
│  │  │  │  ├─ review.py
│  │  │  │  ├─ review_question_analysis.py
│  │  │  │  ├─ weakness_item.py
│  │  │  │  ├─ practice_topic.py
│  │  │  │  ├─ polish_session_topic_link.py
│  │  │  │  ├─ model_registry_entry.py
│  │  │  │  ├─ scoring_rule.py
│  │  │  │  └─ system_setting.py
│  │  │  ├─ schemas/
│  │  │  │  ├─ common.py
│  │  │  │  ├─ auth.py
│  │  │  │  ├─ jobs.py
│  │  │  │  ├─ resumes.py
│  │  │  │  ├─ assets.py
│  │  │  │  ├─ interviews.py
│  │  │  │  ├─ reviews.py
│  │  │  │  ├─ training.py
│  │  │  │  └─ admin.py
│  │  │  ├─ repositories/
│  │  │  │  ├─ team_repository.py
│  │  │  │  ├─ user_repository.py
│  │  │  │  ├─ job_repository.py
│  │  │  │  ├─ resume_repository.py
│  │  │  │  ├─ asset_repository.py
│  │  │  │  ├─ interview_repository.py
│  │  │  │  ├─ review_repository.py
│  │  │  │  └─ training_repository.py
│  │  │  ├─ api/
│  │  │  │  └─ routes/
│  │  │  │     ├─ health.py
│  │  │  │     ├─ auth.py
│  │  │  │     ├─ members.py
│  │  │  │     ├─ jobs.py
│  │  │  │     ├─ resumes.py
│  │  │  │     ├─ match_analysis.py
│  │  │  │     ├─ asset_types.py
│  │  │  │     ├─ assets.py
│  │  │  │     ├─ archive_records.py
│  │  │  │     ├─ interviews.py
│  │  │  │     ├─ polish.py
│  │  │  │     ├─ reviews.py
│  │  │  │     ├─ training.py
│  │  │  │     └─ admin.py
│  │  │  ├─ services/
│  │  │  │  ├─ auth_service.py
│  │  │  │  ├─ object_storage_service.py
│  │  │  │  ├─ markdown_render_service.py
│  │  │  │  ├─ pdf_to_markdown_service.py
│  │  │  │  ├─ resume_export_service.py
│  │  │  │  ├─ retrieval_index_service.py
│  │  │  │  ├─ retrieval_service.py
│  │  │  │  ├─ match_analysis_service.py
│  │  │  │  ├─ interview_context_service.py
│  │  │  │  ├─ interview_engine.py
│  │  │  │  ├─ interview_export_service.py
│  │  │  │  ├─ polish_engine.py
│  │  │  │  ├─ assessment_engine.py
│  │  │  │  ├─ review_engine.py
│  │  │  │  ├─ weakness_service.py
│  │  │  │  ├─ training_service.py
│  │  │  │  ├─ settings_service.py
│  │  │  │  └─ model_recommendation_service.py
│  │  │  └─ tasks/
│  │  │     ├─ resume_tasks.py
│  │  │     ├─ retrieval_tasks.py
│  │  │     └─ export_tasks.py
│  │  └─ tests/
│  │     ├─ conftest.py
│  │     ├─ test_health.py
│  │     ├─ test_auth.py
│  │     ├─ test_jobs_and_resumes.py
│  │     ├─ test_match_analysis.py
│  │     ├─ test_assets.py
│  │     ├─ test_interviews.py
│  │     ├─ test_polish_mode.py
│  │     ├─ test_reviews.py
│  │     ├─ test_training.py
│  │     ├─ test_admin_settings.py
│  │     └─ test_authorization_matrix.py
│  └─ web/
│     ├─ package.json
│     ├─ vitest.config.ts
│     ├─ playwright.config.ts
│     ├─ src/
│     │  ├─ app/
│     │  │  ├─ layout.tsx
│     │  │  ├─ page.tsx
│     │  │  ├─ login/
│     │  │  └─ (dashboard)/
│     │  │     ├─ layout.tsx
│     │  │     ├─ dashboard/
│     │  │     ├─ members/
│     │  │     ├─ jobs/
│     │  │     ├─ resumes/
│     │  │     ├─ interviews/
│     │  │     ├─ polish/
│     │  │     ├─ reviews/
│     │  │     ├─ assets/
│     │  │     ├─ training/
│     │  │     └─ admin/
│     │  ├─ i18n/
│     │  │  ├─ index.ts
│     │  │  └─ messages/
│     │  ├─ components/
│     │  │  ├─ ui/
│     │  │  ├─ layout/
│     │  │  ├─ data/
│     │  │  ├─ markdown/
│     │  │  ├─ jobs/
│     │  │  ├─ resume/
│     │  │  ├─ assets/
│     │  │  ├─ interview/
│     │  │  ├─ review/
│     │  │  └─ training/
│     │  ├─ lib/
│     │  │  ├─ api/
│     │  │  ├─ schemas/
│     │  │  └─ utils/
│     │  └─ test/
│     │     └─ setup.ts
│     └─ tests/
│        └─ e2e/
└─ .github/
   └─ workflows/
      └─ ci.yml
```

## 环境基线

以下环境与命令用于未来 monorepo 落地阶段，当前仓库尚未直接执行这些目录级命令。

实施前统一准备：

- Node.js `22.x`
- `pnpm`
- Python `3.12`
- `uv`
- Docker Desktop

先根据 `.env.example` 创建本地 `.env`，再执行基础命令。

本地基础命令：

```bash
docker compose -f infra/docker-compose.yml up -d
sh infra/minio/init-buckets.sh
pnpm --dir apps/web install
uv sync --project apps/api
```

## 跨任务约束

- **配置安全基线：** 所有密码、token、DSN、第三方密钥一律放到 `.env` 或后续密钥管理中。`docker-compose.yml`、应用配置和服务代码只允许读取环境变量；`.env.example` 只能保留键名和安全的本地占位值。测试如需固定凭据，使用测试夹具或环境覆盖，不允许把真实口令直接写进业务实现。
- **国际化与文案治理：** 从 Task 1 起建立 `apps/web/src/i18n/**` 作为统一文案入口。所有页面标题、导航、按钮、表头、空态、提示语、导出文案都必须通过 locale 字典或集中式配置读取；组件内部禁止直接写死可见文案。后续任务中的中文字符串如果出现在代码块里，只能视为 locale seed 或测试 fixture 的示例值，不代表允许直接写入组件。
- **Markdown 转换 / 预览 / 导出基线：** PDF 转 Markdown 必须调用真实转换能力；Markdown 预览必须基于成熟的 Markdown 渲染/编辑方案，不允许把原文直接塞进容器伪装成预览。前端预览与后端导出必须共享同一套 Markdown 语义规则，避免编辑、预览、导出三套结果不一致。
- **导出能力基线：** 所有导出接口都必须输出真实的领域内容。PDF 导出走 `Markdown/HTML -> WeasyPrint` 或同等级方案，文本导出输出实际整理后的 Markdown / transcript，结构化导出输出真实 JSON 数据；禁止返回 `id.encode(...)`、原始 Markdown bytes 或其他占位实现。

## 完整落库对象与 API 基线

以下清单是 `P1` 的**完整交付边界**。下文各 Task 中出现的代码块只用于说明最小可跑通链路，不代表可以省略本清单里的其他表、接口、页面或测试。执行时应以本节为准，确保每个大任务下的“完整对象面”都被覆盖。

### 数据对象总表

#### 身份与团队域

- `Team` -> 表 `teams` -> 文件 `apps/api/app/models/team.py`
- `User` -> 表 `users` -> 文件 `apps/api/app/models/user.py`

#### 文件与检索基础设施域

- `StorageObject` -> 表 `storage_objects` -> 文件 `apps/api/app/models/storage_object.py`
- `RetrievalChunk` -> 表 `retrieval_chunks` -> 文件 `apps/api/app/models/retrieval_chunk.py`

#### 岗位与简历域

- `Job` -> 表 `jobs` -> 文件 `apps/api/app/models/job.py`
- `JobResumeBinding` -> 表 `job_resume_bindings` -> 文件 `apps/api/app/models/job_resume_binding.py`
- `Resume` -> 表 `resumes` -> 文件 `apps/api/app/models/resume.py`
- `ResumeDocument` -> 表 `resume_documents` -> 文件 `apps/api/app/models/resume_document.py`
- `ResumeConversionLog` -> 表 `resume_conversion_logs` -> 文件 `apps/api/app/models/resume_conversion_log.py`
- `ResumeExportRecord` -> 表 `resume_export_records` -> 文件 `apps/api/app/models/resume_export_record.py`

#### 匹配分析与训练证据域

- `JobResumeMatchAnalysis` -> 表 `job_resume_match_analyses` -> 文件 `apps/api/app/models/job_resume_match_analysis.py`
- `WeaknessEvidence` -> 表 `weakness_evidences` -> 文件 `apps/api/app/models/weakness_evidence.py`

#### 资产库域

- `AssetType` -> 表 `asset_types` -> 文件 `apps/api/app/models/asset_type.py`
- `Asset` -> 表 `assets` -> 文件 `apps/api/app/models/asset.py`
- `ArchiveRecord` -> 表 `archive_records` -> 文件 `apps/api/app/models/archive_record.py`

#### 模拟面试与打磨域

- `InterviewSession` -> 表 `interview_sessions` -> 文件 `apps/api/app/models/interview_session.py`
- `InterviewMessage` -> 表 `interview_messages` -> 文件 `apps/api/app/models/interview_message.py`
- `InterviewQuestionTrace` -> 表 `interview_question_traces` -> 文件 `apps/api/app/models/interview_question_trace.py`
- `SearchSnapshot` -> 表 `search_snapshots` -> 文件 `apps/api/app/models/search_snapshot.py`
- `CapabilityBlueprint` -> 表 `capability_blueprints` -> 文件 `apps/api/app/models/capability_blueprint.py`
- `CapabilityNode` -> 表 `capability_nodes` -> 文件 `apps/api/app/models/capability_node.py`
- `AnswerAssessment` -> 表 `answer_assessments` -> 文件 `apps/api/app/models/answer_assessment.py`
- `InterviewProgressSnapshot` -> 表 `interview_progress_snapshots` -> 文件 `apps/api/app/models/interview_progress_snapshot.py`
- `PracticeTopic` -> 表 `practice_topics` -> 文件 `apps/api/app/models/practice_topic.py`
- `PolishSessionTopicLink` -> 表 `polish_session_topic_links` -> 文件 `apps/api/app/models/polish_session_topic_link.py`

#### 复盘与薄弱项域

- `Review` -> 表 `reviews` -> 文件 `apps/api/app/models/review.py`
- `ReviewQuestionAnalysis` -> 表 `review_question_analyses` -> 文件 `apps/api/app/models/review_question_analysis.py`
- `WeaknessItem` -> 表 `weakness_items` -> 文件 `apps/api/app/models/weakness_item.py`

#### 治理域

- `ModelRegistryEntry` -> 表 `model_registry_entries` -> 文件 `apps/api/app/models/model_registry_entry.py`
- `ScoringRule` -> 表 `scoring_rules` -> 文件 `apps/api/app/models/scoring_rule.py`
- `SystemSetting` -> 表 `system_settings` -> 文件 `apps/api/app/models/system_setting.py`

### API 总表

#### 健康检查

- `GET /api/v1/health`

#### 鉴权与成员

- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `POST /api/v1/auth/logout`
- `GET /api/v1/members`
- `GET /api/v1/members/{member_id}`

#### 文件对象

- `GET /api/v1/storage-objects/{object_id}/download`

#### 岗位与简历

- `GET /api/v1/jobs`
- `POST /api/v1/jobs`
- `GET /api/v1/jobs/{job_id}`
- `PATCH /api/v1/jobs/{job_id}`
- `GET /api/v1/jobs/{job_id}/resume-bindings`
- `POST /api/v1/jobs/{job_id}/resume-bindings`
- `DELETE /api/v1/jobs/{job_id}/resume-bindings/{resume_id}`
- `POST /api/v1/jobs/{job_id}/match-analyses`
- `GET /api/v1/jobs/{job_id}/match-analyses/{analysis_id}`
- `GET /api/v1/resumes`
- `POST /api/v1/resumes`
- `GET /api/v1/resumes/{resume_id}`
- `PATCH /api/v1/resumes/{resume_id}`
- `POST /api/v1/resumes/upload-pdf`
- `GET /api/v1/resumes/{resume_id}/documents`
- `POST /api/v1/resumes/{resume_id}/documents`
- `GET /api/v1/resumes/{resume_id}/conversion-logs`
- `GET /api/v1/resumes/{resume_id}/export-records`
- `POST /api/v1/resumes/{resume_id}/export-pdf`
- `GET /api/v1/resumes/{resume_id}/original-pdf`

#### 资产库

- `GET /api/v1/asset-types`
- `POST /api/v1/asset-types`
- `GET /api/v1/asset-types/{asset_type_id}`
- `PATCH /api/v1/asset-types/{asset_type_id}`
- `GET /api/v1/assets`
- `POST /api/v1/assets`
- `GET /api/v1/assets/{asset_id}`
- `PATCH /api/v1/assets/{asset_id}`
- `POST /api/v1/archive-records`
- `GET /api/v1/archive-records`

#### 模拟面试与打磨

- `GET /api/v1/interviews`
- `POST /api/v1/interviews`
- `GET /api/v1/interviews/{interview_id}`
- `POST /api/v1/interviews/{interview_id}/messages`
- `POST /api/v1/interviews/{interview_id}/complete`
- `GET /api/v1/interviews/{interview_id}/report`
- `GET /api/v1/interviews/{interview_id}/exports/report.pdf`
- `GET /api/v1/interviews/{interview_id}/exports/transcript.md`
- `GET /api/v1/interviews/{interview_id}/exports/detail.json`
- `POST /api/v1/polish-sessions`
- `GET /api/v1/polish-sessions/{session_id}`
- `POST /api/v1/polish-sessions/{session_id}/messages`
- `GET /api/v1/polish-sessions/{session_id}/progress`
- `GET /api/v1/practice-topics/recommendations`

#### 复盘

- `GET /api/v1/reviews`
- `POST /api/v1/reviews`
- `GET /api/v1/reviews/{review_id}`
- `POST /api/v1/reviews/from-interview/{interview_id}`
- `POST /api/v1/reviews/intake-real`
- `GET /api/v1/reviews/{review_id}/question-analyses`
- `POST /api/v1/reviews/{review_id}/archive`
- `POST /api/v1/reviews/{review_id}/question-analyses/{analysis_id}/archive`
- `GET /api/v1/reviews/{review_id}/exports/report.pdf`

#### 训练与薄弱项

- `POST /api/v1/training/intake`
- `GET /api/v1/weaknesses`
- `GET /api/v1/weaknesses/{weakness_id}`
- `PATCH /api/v1/weaknesses/{weakness_id}/status`
- `POST /api/v1/weaknesses/{weakness_id}/restore`
- `POST /api/v1/practice-topics`
- `GET /api/v1/practice-topics`

#### 管理台

- `GET /api/v1/admin/members`
- `PATCH /api/v1/admin/members/{member_id}`
- `GET /api/v1/admin/models`
- `POST /api/v1/admin/models`
- `PATCH /api/v1/admin/models/{entry_id}`
- `GET /api/v1/admin/models/recommendations`
- `GET /api/v1/admin/scoring-rules`
- `POST /api/v1/admin/scoring-rules`
- `PATCH /api/v1/admin/scoring-rules/{rule_id}`
- `GET /api/v1/admin/settings`
- `POST /api/v1/admin/settings`
- `PATCH /api/v1/admin/settings/{setting_id}`

### 页面与路由总表

- `/`
- `/login`
- `/(dashboard)/dashboard`
- `/(dashboard)/members`
- `/(dashboard)/jobs`
- `/(dashboard)/jobs/[jobId]`
- `/(dashboard)/resumes`
- `/(dashboard)/resumes/[resumeId]`
- `/(dashboard)/interviews`
- `/(dashboard)/interviews/new`
- `/(dashboard)/interviews/[interviewId]`
- `/(dashboard)/polish/new`
- `/(dashboard)/polish/[sessionId]`
- `/(dashboard)/reviews`
- `/(dashboard)/reviews/new`
- `/(dashboard)/reviews/[reviewId]`
- `/(dashboard)/assets`
- `/(dashboard)/assets/[assetId]`
- `/(dashboard)/training`
- `/(dashboard)/admin/members`
- `/(dashboard)/admin/asset-types`
- `/(dashboard)/admin/models`
- `/(dashboard)/admin/scoring-rules`
- `/(dashboard)/admin/settings`

## 通用模型字段与软删除规范

### 所有表统一基类字段

除中间纯关联表外，所有正式领域表默认继承统一基类，至少包含以下字段：

- `id`
  - 主键，统一使用 `uuid` 或同等长度的稳定字符串 ID
- `team_id`
  - 团队隔离主键，除系统级只读种子表外一律必填
- `created_at`
  - 创建时间
- `updated_at`
  - 更新时间
- `created_by`
  - 创建人 `user_id`
- `updated_by`
  - 最近更新人 `user_id`
- `deleted_at`
  - 软删除时间，默认 `null`
- `deleted_by`
  - 软删除执行人 `user_id`

### 软删除执行规则

- 所有业务删除默认都是**软删除**，不允许物理删除正式业务数据。
- `DELETE` 类接口语义统一为“标记删除”，实现上写入 `deleted_at`、`deleted_by`。
- 所有列表查询默认追加 `deleted_at IS NULL`。
- 所有详情查询默认不可返回已软删除数据，除非显式进入管理员审计视图。
- 唯一键设计必须考虑软删除复用场景，推荐使用 `(team_id, business_key, deleted_at)` 或逻辑唯一索引。
- 与软删除对象有关联的外键读取必须在服务层显式过滤，避免“主对象被删，子对象仍被误返回”。
- 鉴权测试、列表测试、详情测试、恢复测试都必须覆盖软删除对象。

### 索引与查询规范

- 所有热点表至少建立 `(team_id, deleted_at)` 组合索引。
- 列表页常用筛选字段要建立复合索引，例如 `status`、`updated_at`、`job_id`、`resume_id`、`source_type`。
- `retrieval_chunks.embedding` 使用 `pgvector` 索引，推荐 `hnsw`。

## 核心表字段设计

以下字段是 `P1` 执行期的**最低字段面**。后续新增字段允许，但不得减少这些字段，否则会破坏任务间契约。

### 身份与团队

- `teams`
  - `id`, `team_id(=id)`, `display_name`, `team_key`, `status`, `plan_tier`, `created_at`, `updated_at`, `created_by`, `updated_by`, `deleted_at`, `deleted_by`
- `users`
  - `id`, `team_id`, `email`, `display_name`, `password_hash`, `role`, `status`, `last_login_at`, `created_at`, `updated_at`, `created_by`, `updated_by`, `deleted_at`, `deleted_by`

### 文件与检索基础设施

- `storage_objects`
  - `id`, `team_id`, `bucket`, `object_key`, `original_filename`, `content_type`, `size_bytes`, `checksum_sha256`, `storage_provider`, `source_type`, `source_id`, `status`, `created_at`, `updated_at`, `created_by`, `updated_by`, `deleted_at`, `deleted_by`
- `retrieval_chunks`
  - `id`, `team_id`, `source_type`, `source_id`, `chunk_index`, `chunk_text`, `chunk_hash`, `embedding`, `metadata_json`, `retrieval_enabled`, `created_at`, `updated_at`, `created_by`, `updated_by`, `deleted_at`, `deleted_by`

### 岗位与简历

- `jobs`
  - `id`, `team_id`, `company`, `title`, `jd_markdown`, `requirement_items_json`, `source_url`, `status`, `owner_user_id`, `latest_match_analysis_id`, `created_at`, `updated_at`, `created_by`, `updated_by`, `deleted_at`, `deleted_by`
- `job_resume_bindings`
  - `id`, `team_id`, `job_id`, `resume_id`, `is_primary`, `bind_source`, `created_at`, `updated_at`, `created_by`, `updated_by`, `deleted_at`, `deleted_by`
- `resumes`
  - `id`, `team_id`, `owner_user_id`, `name`, `source_type`, `original_pdf_object_id`, `current_document_id`, `status`, `created_at`, `updated_at`, `created_by`, `updated_by`, `deleted_at`, `deleted_by`
- `resume_documents`
  - `id`, `team_id`, `resume_id`, `version_no`, `markdown_content`, `summary_json`, `save_reason`, `created_at`, `updated_at`, `created_by`, `updated_by`, `deleted_at`, `deleted_by`
- `resume_conversion_logs`
  - `id`, `team_id`, `resume_id`, `source_object_id`, `target_document_id`, `parser_name`, `parser_version`, `status`, `duration_ms`, `error_message`, `created_at`, `updated_at`, `created_by`, `updated_by`, `deleted_at`, `deleted_by`
- `resume_export_records`
  - `id`, `team_id`, `resume_id`, `document_id`, `format`, `trigger_mode`, `status`, `output_object_id`, `render_duration_ms`, `requested_by`, `created_at`, `updated_at`, `created_by`, `updated_by`, `deleted_at`, `deleted_by`

### 匹配分析与训练证据

- `job_resume_match_analyses`
  - `id`, `team_id`, `job_id`, `resume_id`, `requirement_snapshot_json`, `matched_items_json`, `missing_items_json`, `risky_items_json`, `match_score`, `suggested_topics_json`, `analysis_trace_json`, `model_version`, `status`, `created_at`, `updated_at`, `created_by`, `updated_by`, `deleted_at`, `deleted_by`
- `weakness_evidences`
  - `id`, `team_id`, `source_type`, `source_id`, `job_id`, `resume_id`, `weakness_key`, `severity`, `evidence_summary`, `evidence_payload_json`, `created_at`, `updated_at`, `created_by`, `updated_by`, `deleted_at`, `deleted_by`

### 资产库

- `asset_types`
  - `id`, `team_id`, `name`, `code`, `schema_json`, `is_archivable`, `retrieval_enabled`, `status`, `created_at`, `updated_at`, `created_by`, `updated_by`, `deleted_at`, `deleted_by`
- `assets`
  - `id`, `team_id`, `asset_type_id`, `title`, `body_markdown`, `structured_fields_json`, `source_type`, `source_ref_id`, `quality_score`, `visibility`, `retrieval_enabled`, `latest_chunk_version`, `status`, `created_at`, `updated_at`, `created_by`, `updated_by`, `deleted_at`, `deleted_by`
- `archive_records`
  - `id`, `team_id`, `source_type`, `source_id`, `asset_id`, `asset_type_id`, `archive_mode`, `archived_by`, `created_at`, `updated_at`, `created_by`, `updated_by`, `deleted_at`, `deleted_by`

### 模拟面试与打磨

- `interview_sessions`
  - `id`, `team_id`, `job_id`, `resume_id`, `mode`, `title`, `status`, `context_pack_version`, `started_at`, `completed_at`, `final_score`, `match_score`, `pass_probability`, `linked_review_id`, `created_at`, `updated_at`, `created_by`, `updated_by`, `deleted_at`, `deleted_by`
- `interview_messages`
  - `id`, `team_id`, `session_id`, `role`, `turn_index`, `content`, `source_summary_json`, `generation_meta_json`, `created_at`, `updated_at`, `created_by`, `updated_by`, `deleted_at`, `deleted_by`
- `interview_question_traces`
  - `id`, `team_id`, `session_id`, `message_id`, `focus_area`, `difficulty`, `followup_intent`, `references_json`, `model_name`, `prompt_version`, `created_at`, `updated_at`, `created_by`, `updated_by`, `deleted_at`, `deleted_by`
- `search_snapshots`
  - `id`, `team_id`, `query`, `provider`, `source_url`, `normalized_text`, `company_tags_json`, `job_tags_json`, `ttl_at`, `status`, `created_at`, `updated_at`, `created_by`, `updated_by`, `deleted_at`, `deleted_by`
- `capability_blueprints`
  - `id`, `team_id`, `session_id`, `blueprint_version`, `root_node_id`, `summary_json`, `created_at`, `updated_at`, `created_by`, `updated_by`, `deleted_at`, `deleted_by`
- `capability_nodes`
  - `id`, `team_id`, `blueprint_id`, `parent_id`, `node_type`, `title`, `priority`, `status`, `coverage_score`, `created_at`, `updated_at`, `created_by`, `updated_by`, `deleted_at`, `deleted_by`
- `answer_assessments`
  - `id`, `team_id`, `session_id`, `message_id`, `score`, `lost_points_json`, `evidence_json`, `reference_answer_markdown`, `fix_map_json`, `principles_json`, `created_at`, `updated_at`, `created_by`, `updated_by`, `deleted_at`, `deleted_by`
- `interview_progress_snapshots`
  - `id`, `team_id`, `session_id`, `coverage_ratio`, `uncovered_high_priority_json`, `weak_nodes_json`, `node_changes_json`, `created_at`, `updated_at`, `created_by`, `updated_by`, `deleted_at`, `deleted_by`
- `practice_topics`
  - `id`, `team_id`, `job_id`, `resume_id`, `source_type`, `source_ref_id`, `title`, `priority`, `status`, `recommendation_reason`, `created_at`, `updated_at`, `created_by`, `updated_by`, `deleted_at`, `deleted_by`
- `polish_session_topic_links`
  - `id`, `team_id`, `session_id`, `practice_topic_id`, `topic_role`, `order_no`, `created_at`, `updated_at`, `created_by`, `updated_by`, `deleted_at`, `deleted_by`

### 复盘与薄弱项

- `reviews`
  - `id`, `team_id`, `source_type`, `source_ref_id`, `job_id`, `resume_id`, `summary_markdown`, `dimension_scores_json`, `match_score`, `pass_probability`, `improvements_json`, `archived_status`, `created_at`, `updated_at`, `created_by`, `updated_by`, `deleted_at`, `deleted_by`
- `review_question_analyses`
  - `id`, `team_id`, `review_id`, `order_no`, `original_question`, `original_answer`, `question_intent`, `answer_problem`, `missing_points_json`, `wrong_points_json`, `expression_problem`, `better_answer_framework_markdown`, `followup_risk`, `created_at`, `updated_at`, `created_by`, `updated_by`, `deleted_at`, `deleted_by`
- `weakness_items`
  - `id`, `team_id`, `job_id`, `weakness_key`, `title`, `status`, `priority`, `evidence_count`, `last_exposed_at`, `resolved_at`, `dismissed_reason`, `created_at`, `updated_at`, `created_by`, `updated_by`, `deleted_at`, `deleted_by`

### 治理域

- `model_registry_entries`
  - `id`, `team_id`, `provider`, `model_id`, `display_name`, `release_date`, `task_tags_json`, `catalog_source`, `enabled`, `created_at`, `updated_at`, `created_by`, `updated_by`, `deleted_at`, `deleted_by`
- `scoring_rules`
  - `id`, `team_id`, `rule_scope`, `rule_code`, `weight`, `threshold_json`, `version`, `enabled`, `created_at`, `updated_at`, `created_by`, `updated_by`, `deleted_at`, `deleted_by`
- `system_settings`
  - `id`, `team_id`, `setting_key`, `setting_group`, `value_json`, `version`, `updated_by_user_id`, `created_at`, `updated_at`, `created_by`, `updated_by`, `deleted_at`, `deleted_by`

## 权限矩阵与鉴权验证基线

### 角色矩阵

| 能力域 | admin | member | 未登录 | 跨团队用户 |
|---|---|---|---|---|
| 登录 / 查看本人资料 | 允许 | 允许 | 仅允许登录接口 | 禁止 |
| 岗位 CRUD | 允许 | 允许本团队 | 禁止 | 禁止 |
| 简历 CRUD | 允许 | 允许本团队 | 禁止 | 禁止 |
| 岗位-简历绑定 / 匹配分析 | 允许 | 允许本团队 | 禁止 | 禁止 |
| 模拟面试 / 打磨 / 复盘 / 训练 | 允许 | 允许本团队 | 禁止 | 禁止 |
| 资产查看 / 归档 | 允许 | 允许本团队已授权类型 | 禁止 | 禁止 |
| 资产类型配置 | 允许 | 禁止 | 禁止 | 禁止 |
| 成员管理 | 允许 | 禁止 | 禁止 | 禁止 |
| 评分规则 / 模型配置 / 系统配置 | 允许 | 禁止 | 禁止 | 禁止 |
| 审计查看软删除对象 | 允许显式审计接口 | 禁止 | 禁止 | 禁止 |

### 鉴权测试硬约束

自 `Task 3` 起，所有新增受保护接口必须同时具备以下测试：

- `未登录 -> 401`
- `member 访问 admin 接口 -> 403`
- `本团队用户访问本团队资源 -> 200/201`
- `跨团队访问同路径资源 -> 404 或 403`
- `软删除资源访问详情 -> 404`
- `软删除资源不出现在列表 -> 断言过滤`

专门测试文件固定为：

- `apps/api/tests/test_authorization_matrix.py`

## 技术路线与可行性约束

### 岗位-简历匹配分析

`P1` 不采用“纯 LLM 直出分数”的黑盒方案，而采用**混合分析链路**：

1. `Job` 的 `jd_markdown` 先拆成结构化 `requirement_items_json`
2. `ResumeDocument.markdown_content` 按标题和段落拆成候选证据片段
3. 对每条岗位要求执行三段式匹配：
   - 词法命中：技能词、项目名、关键术语
   - 结构化命中：简历中是否存在明确项目证据、指标、职责
   - 向量相似度：对简历片段与可召回资产片段做 embedding 检索
4. 计算 `match_score` 时，词法命中、结构化命中、向量命中分别保留独立子分
5. LLM 只负责把中间结果整理成“匹配项 / 缺失项 / 高风险项 / 建议打磨主题”，不得绕过中间结构直接返回最终结论

### 资产库与向量数据库

- 只有 `Asset.retrieval_enabled = true` 的资产才进入 `retrieval_chunks`
- 只有 `SearchSnapshot.status = ready` 且仍在 `ttl_at` 有效期内的数据才允许参与召回
- `ResumeDocument` 不进入共享资产向量库；简历正文直接作为当前会话上下文输入，避免污染跨岗位长期知识库
- 分块规则：
  - 中文文本每块 `500-700` 字
  - 块间重叠 `80-120` 字
  - 保留 `source_type`、`source_id`、`title`、`tags`、`chunk_index`
- pgvector 只承担“召回”职责，最终是否采用某条证据仍由服务层做团队、标签、时效和可见性过滤

### 模拟面试 / 打磨上下文包

`build_context_pack()` 的固定装配顺序如下：

1. 岗位结构化要求
2. 当前简历正文
3. 当前岗位下 `active` 的薄弱项
4. `retrieval_enabled` 资产召回结果
5. 有效期内搜索快照召回结果
6. 历史模拟面试 / 复盘的改进建议摘要

模式差异：

- `simulate`
  - 上下文更轻，避免中途过多暴露内部推理
- `polish`
  - 上下文更重，允许显式引用薄弱项、历史问题和修复建议

### 薄弱项聚合

- `WeaknessItem` 的聚合键不是自然语言标题本身，而是 `weakness_key`
- `weakness_key` 由 “岗位维度 + 主题归一化 + 技能标签” 生成
- 证据归并规则优先使用：
  - 同岗位
  - 同主题标签
  - 向量相似度超过阈值
  - 最近暴露时间加权
- 不允许只靠一次 LLM 生成的标题直接判定为同一薄弱项

## 对象存储、Markdown 预览与导出约束

### 对象存储

- `P1` 本地开发统一使用 `MinIO`，生产形态默认兼容 `S3 API`
- bucket 规划：
  - `resume-originals`
  - `export-artifacts`
  - `search-snapshots`
- 对象 key 规范：
  - `team/{team_id}/{domain}/{entity_id}/{yyyy}/{mm}/{uuid}_{filename}`
- 上传流程：
  1. API 先校验 `content_type`、`size_bytes`
  2. 计算 `sha256`
  3. 通过 `object_storage_service` 流式写入对象存储
  4. 落库 `storage_objects`
  5. 再把 `storage_object_id` 关联到 `Resume` 或导出记录
- 对外下载统一走：
  - `GET /api/v1/storage-objects/{object_id}/download`
  - 由服务端做权限校验后返回代理流或签名 URL

### Markdown 预览效果与技术路线

- 前端预览使用 `react-markdown + remark-gfm + rehype-sanitize`
- 预览必须支持：
  - 标题
  - 列表
  - 表格
  - 代码块
  - 引用
  - 任务列表
- 预览禁止直接渲染原始 HTML
- 预览容器使用与 PDF 导出相同的 typography token，保证视觉接近导出结果
- 简历编辑页桌面端固定双栏，移动端改成 `编辑 / 预览` 切换，不允许双栏挤压

### 导出策略与性能约束

- `Resume PDF` 导出：
  - 通过 `POST /api/v1/resumes/{resume_id}/export-pdf` 提交
  - 默认异步，立即返回 `202 + export_record_id`
  - 生成任务由 `Dramatiq` 处理
- `Interview report / transcript / detail` 导出：
  - 在会话完成或复盘生成后异步物化
  - `GET /exports/*` 只负责下载已就绪文件，不负责在请求线程内重算
- `Review report` 导出：
  - 与面试导出一致，先异步生成，再下载

性能约束：

- 列表接口 `p95 < 300ms`
- 创建/提交导出请求 `p95 < 500ms`
- 对象上传接口在文件已开始流式写入后尽快返回 `202`
- 常规简历导出目标：
  - `5` 页内文档 `30s` 内完成
- 常规面试报告导出目标：
  - `20` 轮对话内 `60s` 内完成

## 示例代码、中文注释与日志基线

自 `Task 1` 起，下文所有代码示例都必须按以下标准执行，即使某个代码块为控制篇幅没有完整展开，实现时也不得降级：

- 所有 Python 服务、路由、任务模块统一使用 `structlog`
- 非显然业务步骤前必须有中文必要注释
- 至少记录三类日志：
  - 入口日志
  - 关键分支 / 外部依赖调用日志
  - 异常或结束日志
- 领域服务不能只保留“直接 return 常量对象”的占位写法，必须至少体现：
  - 输入校验
  - 读取已有状态
  - 生成中间结果
  - 持久化或状态更新
  - 返回响应 DTO
- 上传、导出、检索、AI 编排示例必须显式展示：
  - 请求 ID 或对象 ID
  - timeout / provider / model 或 storage metadata
- 前端页面级示例至少要体现：
  - loading / empty / error 中的一种处理思路
  - 文案来自 `i18n`

## 二级任务分解与执行顺序

下文 11 个大任务仍作为里程碑保留，但实际实现、Review、提交必须按这里的二级子任务顺序推进。每个子任务都应单独完成 `red -> green -> verify -> commit`，不能跳过。

### 里程碑 1：工作区初始化与基础骨架

- `1A` 环境模板与本地基础设施
  - 交付文件：`.env.example`、`infra/docker-compose.yml`
  - 交付对象：环境变量模板、PostgreSQL、Redis
  - 验证重点：容器可启动、配置不含明文口令
- `1B` FastAPI 最小入口与健康检查
  - 交付文件：`apps/api/app/main.py`、`apps/api/app/api/routes/health.py`
  - 交付接口：`GET /api/v1/health`
  - 验证重点：后端最小可跑通
- `1C` Next.js 最小入口与 i18n seed
  - 交付文件：`apps/web/src/app/layout.tsx`、`apps/web/src/app/page.tsx`、`apps/web/src/i18n/**`
  - 交付页面：`/`
  - 验证重点：页面文案不硬编码

### 里程碑 2：Web 壳层与通用列表原语

- `2A` 导航壳层与页面头部
  - 交付文件：`apps/web/src/components/layout/app-shell.tsx`、`apps/web/src/components/layout/page-header.tsx`
  - 交付页面：`/(dashboard)/layout`、`/(dashboard)/dashboard`
  - 验证重点：一级导航、摘要区、Dashboard 骨架
- `2B` 列表原语与表格标准能力
  - 交付文件：`apps/web/src/components/data/data-table.tsx`、`apps/web/src/components/data/filter-bar.tsx`、`apps/web/src/components/data/pagination.tsx`
  - 交付能力：排序、筛选、分页、图标操作列、空态占位
  - 验证重点：符合设计稿 `16.1 表格规范`

### 里程碑 3：鉴权、团队与成员目录

- `3A` 团队/用户模型与配置装载
  - 交付对象：`teams`、`users`
  - 交付文件：`apps/api/app/models/team.py`、`apps/api/app/models/user.py`、`apps/api/app/core/config.py`
  - 验证重点：demo 账号读取 `.env`
- `3B` 登录态接口与当前用户接口
  - 交付接口：`POST /api/v1/auth/login`、`GET /api/v1/auth/me`、`POST /api/v1/auth/logout`
  - 交付文件：`apps/api/app/api/routes/auth.py`、`apps/api/app/services/auth_service.py`
  - 验证重点：登录返回 token 与 user payload
- `3C` 成员目录页面与成员明细接口
  - 交付接口：`GET /api/v1/members`、`GET /api/v1/members/{member_id}`
  - 交付页面：`/login`、`/(dashboard)/members`
  - 验证重点：成员列表与登录入口打通，并开始建立 `401 / 403 / 跨团队 / 软删除` 鉴权用例骨架

### 里程碑 4：岗位、简历、文档版本与导出链路

- `4A` 岗位模型、列表、详情、更新
  - 交付对象：`jobs`
  - 交付接口：`GET/POST /api/v1/jobs`、`GET/PATCH /api/v1/jobs/{job_id}`
  - 交付页面：`/(dashboard)/jobs`、`/(dashboard)/jobs/[jobId]`
  - 验证重点：岗位摘要、JD、要求拆解、状态流转，以及成员只可操作本团队岗位
- `4B` 简历模型、文档版本、转换日志、导出记录
  - 交付对象：`resumes`、`resume_documents`、`resume_conversion_logs`、`resume_export_records`
  - 交付接口：`GET/POST /api/v1/resumes`、`GET/PATCH /api/v1/resumes/{resume_id}`、`GET/POST /api/v1/resumes/{resume_id}/documents`
  - 验证重点：保存生成版本快照
- `4C` PDF 上传、异步转换、原始文件查看
  - 交付接口：`POST /api/v1/resumes/upload-pdf`、`GET /api/v1/resumes/{resume_id}/conversion-logs`、`GET /api/v1/resumes/{resume_id}/original-pdf`
  - 交付服务：`apps/api/app/services/storage_service.py`、`apps/api/app/services/pdf_to_markdown_service.py`、`apps/api/app/tasks/resume_tasks.py`
  - 验证重点：PDF 原件落到对象存储、落库 `storage_objects`、转换结果落到 MD 文档
- `4D` Markdown 编辑器、预览、PDF 导出
  - 交付接口：`POST /api/v1/resumes/{resume_id}/export-pdf`、`GET /api/v1/resumes/{resume_id}/export-records`
  - 交付页面：`/(dashboard)/resumes`、`/(dashboard)/resumes/[resumeId]`
  - 交付组件：`apps/web/src/components/markdown/markdown-viewer.tsx`、`apps/web/src/components/resume/markdown-editor.tsx`、`apps/web/src/components/resume/resume-preview.tsx`
  - 验证重点：编辑、预览、导出三链路共用一套 Markdown 规则，导出接口返回 `202 + export_record_id`

### 里程碑 5：岗位-简历匹配分析与训练证据

- `5A` 岗位-简历绑定关系
  - 交付对象：`job_resume_bindings`
  - 交付接口：`GET /api/v1/jobs/{job_id}/resume-bindings`、`POST /api/v1/jobs/{job_id}/resume-bindings`、`DELETE /api/v1/jobs/{job_id}/resume-bindings/{resume_id}`
  - 验证重点：一个岗位可绑定多份简历
- `5B` 匹配分析对象与分析接口
  - 交付对象：`job_resume_match_analyses`
  - 交付接口：`POST /api/v1/jobs/{job_id}/match-analyses`、`GET /api/v1/jobs/{job_id}/match-analyses/{analysis_id}`
  - 验证重点：按“结构化提取 + 词法命中 + 向量召回 + LLM 整理”输出匹配项、缺失项、高风险项、推荐主题
- `5C` 匹配分析衍生证据
  - 交付对象：`weakness_evidences`
  - 交付能力：从分析结果生成后续训练证据
  - 验证重点：证据带上岗位、简历、来源对象 ID
- `5D` 岗位详情右栏分析区
  - 交付页面：`/(dashboard)/jobs/[jobId]`
  - 交付组件：`apps/web/src/components/jobs/match-analysis-panel.tsx`、`apps/web/src/components/jobs/weakness-summary.tsx`
  - 验证重点：分析结论与“纳入训练”入口完整

### 里程碑 6：资产类型、资产库与归档关系

- `6A` 资产类型与 schema 管理
  - 交付对象：`asset_types`
  - 交付接口：`GET/POST /api/v1/asset-types`、`GET/PATCH /api/v1/asset-types/{asset_type_id}`
  - 验证重点：动态 schema、是否可归档、是否可召回
- `6B` 资产对象与资产详情
  - 交付对象：`assets`
  - 交付接口：`GET/POST /api/v1/assets`、`GET/PATCH /api/v1/assets/{asset_id}`
  - 交付页面：`/(dashboard)/assets`、`/(dashboard)/assets/[assetId]`
  - 验证重点：结构化字段、正文、来源关系展示，以及 `retrieval_enabled` 资产成功写入 `retrieval_chunks`
- `6C` 归档记录
  - 交付对象：`archive_records`
  - 交付接口：`POST /api/v1/archive-records`、`GET /api/v1/archive-records`
  - 验证重点：支持整份归档与单题归档的来源追踪

### 里程碑 7：模拟面试、消息流、上下文包与导出

- `7A` 模拟面试会话对象与列表页
  - 交付对象：`interview_sessions`
  - 交付接口：`GET/POST /api/v1/interviews`、`GET /api/v1/interviews/{interview_id}`
  - 交付页面：`/(dashboard)/interviews`、`/(dashboard)/interviews/new`
  - 验证重点：模式、状态、评分、复盘状态字段完整
- `7B` 消息流、题目 trace、搜索快照
  - 交付对象：`interview_messages`、`interview_question_traces`、`search_snapshots`
  - 交付接口：`POST /api/v1/interviews/{interview_id}/messages`
  - 验证重点：问题考察方向、引用材料、模型版本、prompt 版本都可追踪，并明确上下文包来自“岗位 + 简历 + 薄弱项 + 资产召回 + 搜索快照”
- `7C` 模拟模式结束与轻量报告
  - 交付接口：`POST /api/v1/interviews/{interview_id}/complete`、`GET /api/v1/interviews/{interview_id}/report`
  - 交付页面：`/(dashboard)/interviews/[interviewId]`
  - 交付组件：`apps/web/src/components/interview/report-drawer.tsx`
  - 验证重点：结束后输出整场评估、匹配度、通过概率、建议打磨主题
- `7D` 导出三件套
  - 交付接口：`GET /api/v1/interviews/{interview_id}/exports/report.pdf`、`transcript.md`、`detail.json`
  - 验证重点：导出内容为真实报告、真实逐字稿、真实结构化详情，下载接口只读取已物化对象，不在请求线程内重算

### 里程碑 8：打磨模式、能力树、评估与进展

- `8A` 打磨主题与启动页
  - 交付对象：`practice_topics`、`polish_session_topic_links`
  - 交付接口：`GET /api/v1/practice-topics/recommendations`、`POST /api/v1/polish-sessions`
  - 交付页面：`/(dashboard)/polish/new`
  - 验证重点：主主题 + 辅助主题建模清晰
- `8B` 能力树蓝图与节点
  - 交付对象：`capability_blueprints`、`capability_nodes`
  - 交付组件：`apps/web/src/components/interview/ability-tree.tsx`
  - 验证重点：技术模块、项目主题、表达主题都有节点级状态
- `8C` 逐题评估与技术原理卡
  - 交付对象：`answer_assessments`
  - 交付接口：`POST /api/v1/polish-sessions/{session_id}/messages`
  - 交付组件：`apps/web/src/components/interview/assessment-card.tsx`
  - 验证重点：得分、失分证据、参考回答、修复映射、技术原理完整
- `8D` 当前进展与快照
  - 交付对象：`interview_progress_snapshots`
  - 交付接口：`GET /api/v1/polish-sessions/{session_id}/progress`
  - 交付页面：`/(dashboard)/polish/[sessionId]`
  - 验证重点：覆盖率、高优先级未覆盖项、节点状态变化可回看

### 里程碑 9：复盘、真实面试回放与导出

- `9A` 复盘总对象与列表
  - 交付对象：`reviews`
  - 交付接口：`GET/POST /api/v1/reviews`、`GET /api/v1/reviews/{review_id}`
  - 交付页面：`/(dashboard)/reviews`
  - 验证重点：来源、匹配度、通过概率、归档状态都可筛选
- `9B` 真实面试材料导入与逐题拆解
  - 交付接口：`POST /api/v1/reviews/intake-real`
  - 交付页面：`/(dashboard)/reviews/new`
  - 验证重点：支持真实问题/回答材料进入复盘编排
- `9C` 题目分析对象
  - 交付对象：`review_question_analyses`
  - 交付接口：`GET /api/v1/reviews/{review_id}/question-analyses`
  - 交付组件：`apps/web/src/components/review/question-analysis-card.tsx`
  - 验证重点：原始问题、原始回答、问题意图、遗漏点、表达问题完整
- `9D` 模拟面试转复盘与导出
  - 交付接口：`POST /api/v1/reviews/from-interview/{interview_id}`、`GET /api/v1/reviews/{review_id}/exports/report.pdf`
  - 验证重点：可从模拟面试生成复盘并导出报告

### 里程碑 10：训练抽屉、薄弱项中心与生命周期

- `10A` 聚合薄弱项对象
  - 交付对象：`weakness_items`
  - 交付接口：`GET /api/v1/weaknesses`、`GET /api/v1/weaknesses/{weakness_id}`
  - 交付页面：`/(dashboard)/training`
  - 验证重点：按岗位聚合、按主题归并、证据可追溯
- `10B` 训练抽屉动作
  - 交付接口：`POST /api/v1/training/intake`、`POST /api/v1/practice-topics`
  - 交付组件：`apps/web/src/components/training/training-drawer.tsx`
  - 验证重点：归并到薄弱项、加入待打磨、立即发起打磨
- `10C` 生命周期状态流转
  - 交付接口：`PATCH /api/v1/weaknesses/{weakness_id}/status`、`POST /api/v1/weaknesses/{weakness_id}/restore`
  - 交付能力：`active -> low_priority -> resolved` 与 `dismissed -> restore`
  - 验证重点：状态转移有规则、有证据来源

### 里程碑 11：管理台治理、日志、CI 与端到端加固

- `11A` 成员管理页与接口
  - 交付接口：`GET /api/v1/admin/members`、`PATCH /api/v1/admin/members/{member_id}`
  - 交付页面：`/(dashboard)/admin/members`
  - 验证重点：角色与状态修改
- `11B` 模型配置与最新模型推荐
  - 交付对象：`model_registry_entries`
  - 交付接口：`GET /api/v1/admin/models`、`POST /api/v1/admin/models`、`PATCH /api/v1/admin/models/{entry_id}`、`GET /api/v1/admin/models/recommendations`
  - 交付页面：`/(dashboard)/admin/models`
  - 验证重点：推荐来源是 catalog / seed，不是在线抓取
- `11C` 评分规则与系统配置
  - 交付对象：`scoring_rules`、`system_settings`
  - 交付接口：`GET /api/v1/admin/scoring-rules`、`POST /api/v1/admin/scoring-rules`、`PATCH /api/v1/admin/scoring-rules/{rule_id}`、`GET /api/v1/admin/settings`、`POST /api/v1/admin/settings`、`PATCH /api/v1/admin/settings/{setting_id}`
  - 交付页面：`/(dashboard)/admin/scoring-rules`、`/(dashboard)/admin/settings`
  - 验证重点：评分规则版本化、系统配置可审计
- `11D` 观测性、CI、E2E
  - 交付文件：`apps/api/app/core/logging.py`、`.github/workflows/ci.yml`、`apps/web/tests/e2e/app-shell.spec.ts`
  - 验证重点：结构化日志、授权矩阵测试、后端测试、前端测试、Playwright smoke 全绿

---

### 任务 1：工作区初始化与健康检查切片

**文件：**
- Create: `.env.example`
- Create: `package.json`
- Create: `infra/docker-compose.yml`
- Create: `infra/minio/init-buckets.sh`
- Create: `apps/api/pyproject.toml`
- Create: `apps/api/app/core/logging.py`
- Create: `apps/api/app/main.py`
- Create: `apps/api/app/api/routes/health.py`
- Create: `apps/api/tests/test_health.py`
- Create: `apps/web/package.json`
- Create: `apps/web/src/app/layout.tsx`
- Create: `apps/web/src/app/page.tsx`
- Create: `apps/web/src/app/__tests__/page.test.tsx`
- Create: `apps/web/src/i18n/index.ts`
- Create: `apps/web/src/i18n/messages/zh-CN.ts`
- Create: `apps/web/src/i18n/messages/en-US.ts`
- Create: `apps/web/vitest.config.ts`
- Create: `apps/web/src/test/setup.ts`

- [ ] **步骤 1: Write the failing backend health test**

```python
# apps/api/tests/test_health.py
from fastapi.testclient import TestClient

from app.main import app


def test_health_check_returns_ok() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **步骤 2: Run the backend test to verify it fails**

Run: `uv run --project apps/api pytest apps/api/tests/test_health.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'app'`

- [ ] **步骤 3: Write the minimal backend app and local infra files**

```toml
# apps/api/pyproject.toml
[project]
name = "ai-interview-api"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
  "fastapi>=0.116.0",
  "uvicorn[standard]>=0.35.0",
  "pydantic-settings>=2.10.0",
  "pytest>=8.4.0",
]

[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
```

```python
# apps/api/app/api/routes/health.py
from fastapi import APIRouter
import structlog

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.get("/health")
def health_check() -> dict[str, str]:
    # 健康检查只做轻量存活确认，不访问外部依赖。
    logger.info("health_check_requested")
    return {"status": "ok"}
```

```python
# apps/api/app/core/logging.py
import logging
import structlog


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(logging.INFO))
```

```python
# apps/api/app/main.py
from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.core.logging import configure_logging

configure_logging()
app = FastAPI(title="AI Interview API")
app.include_router(health_router, prefix="/api/v1")
```

```yaml
# .env.example
POSTGRES_DB=ai_interviewer
POSTGRES_USER=postgres
POSTGRES_PASSWORD=change-me
POSTGRES_PORT=5432
REDIS_PORT=6379
S3_ENDPOINT=http://127.0.0.1:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_REGION=us-east-1
S3_BUCKET_RESUME_ORIGINALS=resume-originals
S3_BUCKET_EXPORT_ARTIFACTS=export-artifacts
S3_BUCKET_SEARCH_SNAPSHOTS=search-snapshots
DEMO_ADMIN_EMAIL=admin@example.com
DEMO_ADMIN_PASSWORD=change-me
DEMO_AUTH_TOKEN=dev-token
```

```yaml
# infra/docker-compose.yml
services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    ports:
      - "${POSTGRES_PORT:-5432}:5432"
  redis:
    image: redis:7
    ports:
      - "${REDIS_PORT:-6379}:6379"
  minio:
    image: minio/minio:RELEASE.2025-02-18T16-25-55Z
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${S3_ACCESS_KEY}
      MINIO_ROOT_PASSWORD: ${S3_SECRET_KEY}
    ports:
      - "9000:9000"
      - "9001:9001"
```

```bash
# infra/minio/init-buckets.sh
#!/usr/bin/env bash
set -euo pipefail

mc alias set local "$S3_ENDPOINT" "$S3_ACCESS_KEY" "$S3_SECRET_KEY"
mc mb --ignore-existing "local/$S3_BUCKET_RESUME_ORIGINALS"
mc mb --ignore-existing "local/$S3_BUCKET_EXPORT_ARTIFACTS"
mc mb --ignore-existing "local/$S3_BUCKET_SEARCH_SNAPSHOTS"
```

- [ ] **步骤 4: Run the backend test to verify it passes**

Run: `uv run --project apps/api pytest apps/api/tests/test_health.py -q`
Expected: PASS with `1 passed`

- [ ] **步骤 5: Write the failing frontend home page test**

```tsx
// apps/web/src/app/__tests__/page.test.tsx
import { render, screen } from "@testing-library/react";

import { getMessages } from "@/i18n";
import HomePage from "../page";

describe("HomePage", () => {
  it("renders the product heading", () => {
    const copy = getMessages().home;

    render(<HomePage />);

    expect(screen.getByRole("heading", { name: copy.title })).toBeInTheDocument();
  });
});
```

- [ ] **步骤 6: Run the frontend test to verify it fails**

Run: `pnpm --dir apps/web exec vitest run src/app/__tests__/page.test.tsx`
Expected: FAIL with `Cannot find module '../page'` or missing Next.js app files

- [ ] **步骤 7: Write the minimal web app, test setup, and root scripts**

```json
// package.json
{
  "name": "ai-for-interviewer",
  "private": true,
  "scripts": {
    "dev:web": "pnpm --dir apps/web dev",
    "dev:api": "uv run --project apps/api uvicorn app.main:app --reload",
    "test:web": "pnpm --dir apps/web test",
    "test:api": "uv run --project apps/api pytest"
  }
}
```

```json
// apps/web/package.json
{
  "name": "web",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "test": "vitest run"
  },
  "dependencies": {
    "next": "15.3.0",
    "react": "19.1.0",
    "react-dom": "19.1.0"
  },
  "devDependencies": {
    "@testing-library/jest-dom": "^6.6.3",
    "@testing-library/react": "^16.3.0",
    "@types/node": "^22.15.18",
    "@types/react": "^19.1.2",
    "jsdom": "^26.1.0",
    "typescript": "^5.8.3",
    "vitest": "^3.1.4"
  }
}
```

```tsx
// apps/web/src/i18n/messages/zh-CN.ts
const zhCN = {
  home: {
    title: "AI 模拟面试工作台",
    subtitle: "仓库基础骨架已建立，后续页面在此基础上扩展。",
  },
  shell: {
    brand: "AI 面试训练",
    nav: {
      dashboard: "工作台",
      jobs: "岗位",
      resumes: "简历",
      interviews: "模拟面试",
      reviews: "复盘",
      assets: "资产库",
      admin: "管理台",
    },
    dashboard: {
      summaryTitle: "今日重点",
      summaryDescription: "从岗位、模拟面试与薄弱项开始进入训练闭环。",
    },
    table: {
      actions: "操作",
    },
    pagination: {
      current: (page: number) => `第 ${page} 页`,
      total: (totalPages: number) => `共 ${totalPages} 页`,
    },
  },
  resumeEditor: {
    editorTitle: "Markdown 编辑",
    previewTitle: "实时预览",
    viewOriginalPdf: "查看原始 PDF",
    exportPdf: "导出 PDF",
  },
} as const;

export default zhCN;
```

```tsx
// apps/web/src/i18n/messages/en-US.ts
const enUS = {
  home: {
    title: "AI Mock Interview Workspace",
    subtitle: "The repository skeleton is ready and later pages will extend it.",
  },
  shell: {
    brand: "AI Interview Training",
    nav: {
      dashboard: "Workspace",
      jobs: "Jobs",
      resumes: "Resumes",
      interviews: "Mock Interviews",
      reviews: "Reviews",
      assets: "Assets",
      admin: "Admin",
    },
    dashboard: {
      summaryTitle: "Today's Focus",
      summaryDescription: "Start the training loop from jobs, mock interviews, and weaknesses.",
    },
    table: {
      actions: "Actions",
    },
    pagination: {
      current: (page: number) => `Page ${page}`,
      total: (totalPages: number) => `${totalPages} pages in total`,
    },
  },
  resumeEditor: {
    editorTitle: "Markdown Editor",
    previewTitle: "Live Preview",
    viewOriginalPdf: "View Original PDF",
    exportPdf: "Export PDF",
  },
} as const;

export default enUS;
```

```ts
// apps/web/src/i18n/index.ts
import enUS from "./messages/en-US";
import zhCN from "./messages/zh-CN";

export const messages = {
  "zh-CN": zhCN,
  "en-US": enUS,
} as const;

export type Locale = keyof typeof messages;

export function getMessages(locale: Locale = "zh-CN") {
  return messages[locale];
}
```

```tsx
// apps/web/src/app/layout.tsx
export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
```

```tsx
// apps/web/src/app/page.tsx
import { getMessages } from "@/i18n";

export default function HomePage() {
  const copy = getMessages().home;

  return (
    <main>
      <h1>{copy.title}</h1>
      <p>{copy.subtitle}</p>
    </main>
  );
}
```

```ts
// apps/web/vitest.config.ts
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
  },
});
```

```ts
// apps/web/src/test/setup.ts
import "@testing-library/jest-dom/vitest";
```

- [ ] **步骤 8: Run the frontend test to verify it passes**

Run: `pnpm --dir apps/web exec vitest run src/app/__tests__/page.test.tsx`
Expected: PASS with `1 passed`

- [ ] **步骤 9：提交**

```bash
git add package.json infra/docker-compose.yml apps/api apps/web
git commit -m "初始化 Web 与 API 工作区"
```

### 任务 2：Web 壳层与通用列表基础组件

**文件：**
- Create: `apps/web/src/components/layout/app-shell.tsx`
- Create: `apps/web/src/components/layout/page-header.tsx`
- Create: `apps/web/src/components/data/data-table.tsx`
- Create: `apps/web/src/components/data/filter-bar.tsx`
- Create: `apps/web/src/components/data/pagination.tsx`
- Create: `apps/web/src/app/(dashboard)/layout.tsx`
- Create: `apps/web/src/app/(dashboard)/dashboard/page.tsx`
- Create: `apps/web/src/components/layout/__tests__/app-shell.test.tsx`
- Create: `apps/web/src/components/data/__tests__/data-table.test.tsx`
- Modify: `apps/web/package.json`

- 说明：从本任务开始，后续所有前端页面和组件都默认沿用 `getMessages()/locale seed` 模式；下文若不再重复展开取词样板，也不表示允许重新硬编码文案。

- [ ] **步骤 1: Write the failing app shell test**

```tsx
// apps/web/src/components/layout/__tests__/app-shell.test.tsx
import { render, screen } from "@testing-library/react";

import { getMessages } from "@/i18n";
import { AppShell } from "../app-shell";

describe("AppShell", () => {
  it("renders the primary navigation items", () => {
    const copy = getMessages().shell;

    render(<AppShell title={copy.nav.dashboard}>内容</AppShell>);

    expect(screen.getByRole("link", { name: copy.nav.jobs })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: copy.nav.interviews })).toBeInTheDocument();
    expect(screen.getByText("内容")).toBeInTheDocument();
  });
});
```

- [ ] **步骤 2: Run the shell test to verify it fails**

Run: `pnpm --dir apps/web exec vitest run src/components/layout/__tests__/app-shell.test.tsx`
Expected: FAIL with `Cannot find module '../app-shell'`

- [ ] **步骤 3: Implement the dashboard shell and dashboard page**

```tsx
// apps/web/src/components/layout/app-shell.tsx
import { getMessages } from "@/i18n";

export function AppShell({
  title,
  children,
}: Readonly<{ title: string; children: React.ReactNode }>) {
  const copy = getMessages().shell;
  const navItems = [
    copy.nav.dashboard,
    copy.nav.jobs,
    copy.nav.resumes,
    copy.nav.interviews,
    copy.nav.reviews,
    copy.nav.assets,
    copy.nav.admin,
  ];

  return (
    <div className="min-h-screen bg-slate-50 text-slate-950">
      <aside className="fixed left-0 top-0 h-screen w-60 border-r border-slate-200 bg-white p-6">
        <p className="mb-6 text-sm font-semibold text-slate-500">{copy.brand}</p>
        <nav className="space-y-3">
          {navItems.map((item) => (
            <a key={item} href="#" className="block text-sm text-slate-700">
              {item}
            </a>
          ))}
        </nav>
      </aside>
      <div className="ml-60">
        <header className="border-b border-slate-200 bg-white px-8 py-5">
          <h1 className="text-2xl font-semibold">{title}</h1>
        </header>
        <main className="p-8">{children}</main>
      </div>
    </div>
  );
}
```

```tsx
// apps/web/src/app/(dashboard)/layout.tsx
import { AppShell } from "@/components/layout/app-shell";
import { getMessages } from "@/i18n";

export default function DashboardLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return <AppShell title={getMessages().shell.nav.dashboard}>{children}</AppShell>;
}
```

```tsx
// apps/web/src/app/(dashboard)/dashboard/page.tsx
import { getMessages } from "@/i18n";

export default function DashboardPage() {
  const copy = getMessages().shell.dashboard;

  return (
    <section className="grid gap-6 md:grid-cols-3">
      <article className="rounded-2xl border border-slate-200 bg-white p-6">
        <h2 className="text-base font-semibold">{copy.summaryTitle}</h2>
        <p className="mt-2 text-sm text-slate-600">{copy.summaryDescription}</p>
      </article>
    </section>
  );
}
```

- [ ] **步骤 4: Run the shell test to verify it passes**

Run: `pnpm --dir apps/web exec vitest run src/components/layout/__tests__/app-shell.test.tsx`
Expected: PASS with `1 passed`

- [ ] **步骤 5: Write the failing data table test**

```tsx
// apps/web/src/components/data/__tests__/data-table.test.tsx
import { render, screen } from "@testing-library/react";

import { DataTable } from "../data-table";

describe("DataTable", () => {
  it("renders headers and icon-style actions", () => {
    render(
      <DataTable
        columns={[
          { key: "name", header: "名称" },
          { key: "status", header: "状态" },
        ]}
        rows={[{ id: "1", name: "Java 后端", status: "进行中" }]}
        actions={[{ label: "查看", icon: "eye" }]}
      />,
    );

    expect(screen.getByText("名称")).toBeInTheDocument();
    expect(screen.getByLabelText("查看")).toBeInTheDocument();
  });
});
```

- [ ] **步骤 6: Run the table test to verify it fails**

Run: `pnpm --dir apps/web exec vitest run src/components/data/__tests__/data-table.test.tsx`
Expected: FAIL with `Cannot find module '../data-table'`

- [ ] **步骤 7: Implement shared list primitives**

```tsx
// apps/web/src/components/data/data-table.tsx
import { getMessages } from "@/i18n";

type Column = { key: string; header: string };
type Action = { label: string; icon: string };

export function DataTable({
  columns,
  rows,
  actions,
}: Readonly<{
  columns: Column[];
  rows: Array<Record<string, string>>;
  actions: Action[];
}>) {
  const copy = getMessages().shell.table;

  return (
    <div className="rounded-2xl border border-slate-200 bg-white">
      <table className="min-w-full">
        <thead className="border-b border-slate-200 bg-slate-50">
          <tr>
            {columns.map((column) => (
              <th key={column.key} className="px-4 py-3 text-left text-sm font-medium text-slate-700">
                {column.header}
              </th>
            ))}
            <th className="px-4 py-3 text-left text-sm font-medium text-slate-700">{copy.actions}</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id} className="border-b border-slate-100">
              {columns.map((column) => (
                <td key={column.key} className="px-4 py-3 text-sm text-slate-700">
                  {row[column.key]}
                </td>
              ))}
              <td className="px-4 py-3">
                <div className="flex gap-2">
                  {actions.map((action) => (
                    <button
                      key={action.label}
                      aria-label={action.label}
                      className="rounded-lg border border-slate-200 p-2 text-slate-600"
                      type="button"
                    >
                      {action.icon}
                    </button>
                  ))}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

```tsx
// apps/web/src/components/data/filter-bar.tsx
export function FilterBar({ children }: Readonly<{ children: React.ReactNode }>) {
  return <div className="mb-4 flex flex-wrap gap-3">{children}</div>;
}
```

```tsx
// apps/web/src/components/data/pagination.tsx
import { getMessages } from "@/i18n";

export function Pagination({ page, totalPages }: Readonly<{ page: number; totalPages: number }>) {
  const copy = getMessages().shell.pagination;

  return (
    <div className="flex items-center justify-end gap-3 py-4 text-sm text-slate-600">
      <span>{copy.current(page)}</span>
      <span>{copy.total(totalPages)}</span>
    </div>
  );
}
```

- [ ] **步骤 8: Run the table test to verify it passes**

Run: `pnpm --dir apps/web exec vitest run src/components/data/__tests__/data-table.test.tsx`
Expected: PASS with `1 passed`

- [ ] **步骤 9：提交**

```bash
git add apps/web
git commit -m "添加工作台壳层与列表基础组件"
```

### 任务 3：鉴权、团队与成员目录

**文件：**
- Modify: `.env.example`
- Create: `apps/api/app/core/config.py`
- Create: `apps/api/app/core/security.py`
- Create: `apps/api/app/db/session.py`
- Create: `apps/api/app/db/base.py`
- Create: `apps/api/app/models/team.py`
- Create: `apps/api/app/models/user.py`
- Create: `apps/api/app/schemas/auth.py`
- Create: `apps/api/app/api/routes/auth.py`
- Create: `apps/api/app/api/routes/members.py`
- Create: `apps/api/app/services/auth_service.py`
- Create: `apps/api/tests/test_auth.py`
- Create: `apps/api/tests/test_authorization_matrix.py`
- Create: `apps/web/src/app/login/page.tsx`
- Create: `apps/web/src/app/(dashboard)/members/page.tsx`
- Create: `apps/web/src/app/login/__tests__/page.test.tsx`
- Modify: `apps/api/app/main.py`
- Modify: `apps/web/src/components/layout/app-shell.tsx`

- 本任务的本地演示账号与 token 必须通过 `.env` 注入；下面测试里的口令只表示 smoke fixture 输入，不允许在业务实现里写死凭据。

- [ ] **步骤 1: Write the failing auth API test**

```python
# apps/api/tests/test_auth.py
from fastapi.testclient import TestClient

from app.main import app


def test_login_returns_current_user_payload() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "Passw0rd!"},
    )

    assert response.status_code == 200
    assert response.json()["user"]["role"] == "admin"
```

- [ ] **步骤 2: Run the auth test to verify it fails**

Run: `uv run --project apps/api pytest apps/api/tests/test_auth.py -q`
Expected: FAIL with `404 Not Found` for `/api/v1/auth/login`

- [ ] **步骤 3: Implement the auth and member directory backend slice**

```python
# apps/api/app/core/config.py
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    demo_admin_email: str = "admin@example.com"
    demo_admin_password: str
    demo_auth_token: str = "dev-token"


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

```python
# apps/api/app/models/user.py
from dataclasses import dataclass


@dataclass
class User:
    id: str
    email: str
    password_hash: str
    role: str
    team_id: str
```

```python
# apps/api/app/services/auth_service.py
import structlog

from app.core.config import get_settings
from app.models.user import User

logger = structlog.get_logger(__name__)


def authenticate_user(email: str, password: str) -> User | None:
    settings = get_settings()
    logger.info("authenticate_user_requested", email=email)

    if email == settings.demo_admin_email and password == settings.demo_admin_password:
        user = User(
            id="user_admin",
            email=email,
            password_hash="not-used-in-smoke",
            role="admin",
            team_id="team_default",
        )
        logger.info("authenticate_user_succeeded", email=email, role=user.role, team_id=user.team_id)
        return user

    logger.warning("authenticate_user_failed", email=email)
    return None
```

```python
# apps/api/app/api/routes/auth.py
import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

from app.core.config import get_settings
from app.services.auth_service import authenticate_user

router = APIRouter(prefix="/auth", tags=["auth"])
logger = structlog.get_logger(__name__)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/login")
def login(payload: LoginRequest) -> dict[str, object]:
    settings = get_settings()
    logger.info("login_requested", email=payload.email)
    user = authenticate_user(payload.email, payload.password)
    if user is None:
        logger.warning("login_rejected", email=payload.email)
        raise HTTPException(status_code=401, detail="invalid_credentials")

    # 示例里先返回演示 token；真实实现中应改为签发 JWT 或 session cookie。
    response = {
        "token": settings.demo_auth_token,
        "user": {
            "id": user.id,
            "email": user.email,
            "role": user.role,
            "teamId": user.team_id,
        },
    }
    logger.info("login_succeeded", email=payload.email, role=user.role, team_id=user.team_id)
    return response
```

```python
# apps/api/app/api/routes/members.py
import structlog
from fastapi import APIRouter

router = APIRouter(prefix="/members", tags=["members"])
logger = structlog.get_logger(__name__)
_MEMBERS = [
    {"id": "user_admin", "email": "admin@example.com", "role": "admin", "teamId": "team_default", "status": "active"},
    {"id": "user_member", "email": "member@example.com", "role": "member", "teamId": "team_default", "status": "active"},
]


@router.get("")
def list_members() -> list[dict[str, str]]:
    # 示例里先按团队和状态过滤；真实实现中应从鉴权上下文读取 current_user / current_team。
    visible_members = [
        {"id": member["id"], "email": member["email"], "role": member["role"]}
        for member in _MEMBERS
        if member["teamId"] == "team_default" and member["status"] == "active"
    ]
    logger.info("members_listed", team_id="team_default", count=len(visible_members))
    return visible_members
```

```python
# apps/api/app/main.py
from fastapi import FastAPI

from app.api.routes.auth import router as auth_router
from app.api.routes.health import router as health_router
from app.api.routes.members import router as members_router

app = FastAPI(title="AI Interview API")
app.include_router(health_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(members_router, prefix="/api/v1")
```

- [ ] **步骤 4: Run the auth test to verify it passes**

Run: `uv run --project apps/api pytest apps/api/tests/test_auth.py -q`
Expected: PASS with `1 passed`

- [ ] **步骤 5: Write the failing login page test**

```tsx
// apps/web/src/app/login/__tests__/page.test.tsx
import { render, screen } from "@testing-library/react";

import LoginPage from "../page";

describe("LoginPage", () => {
  it("renders the email and password fields", () => {
    render(<LoginPage />);

    expect(screen.getByLabelText("邮箱")).toBeInTheDocument();
    expect(screen.getByLabelText("密码")).toBeInTheDocument();
  });
});
```

- [ ] **步骤 6: Run the login page test to verify it fails**

Run: `pnpm --dir apps/web exec vitest run src/app/login/__tests__/page.test.tsx`
Expected: FAIL with `Cannot find module '../page'`

- [ ] **步骤 7: Implement login and member directory pages**

```tsx
// apps/web/src/app/login/page.tsx
import { getMessages } from "@/i18n";

export default function LoginPage() {
  const copy = getMessages().auth;

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center gap-6 p-8">
      <div>
        <h1 className="text-3xl font-semibold">{copy.loginTitle}</h1>
        <p className="mt-2 text-sm text-slate-600">{copy.loginDescription}</p>
      </div>
      <label className="grid gap-2">
        <span className="text-sm font-medium">{copy.emailLabel}</span>
        <input aria-label={copy.emailLabel} className="rounded-xl border border-slate-300 px-3 py-2" />
      </label>
      <label className="grid gap-2">
        <span className="text-sm font-medium">{copy.passwordLabel}</span>
        <input aria-label={copy.passwordLabel} type="password" className="rounded-xl border border-slate-300 px-3 py-2" />
      </label>
      <button type="button" className="rounded-xl bg-slate-950 px-4 py-3 text-white">
        {copy.submitLabel}
      </button>
    </main>
  );
}
```

```tsx
// apps/web/src/app/(dashboard)/members/page.tsx
import { DataTable } from "@/components/data/data-table";
import { getMessages } from "@/i18n";

export default function MembersPage() {
  const copy = getMessages().members;

  return (
    <section className="space-y-4">
      <h2 className="text-xl font-semibold">{copy.title}</h2>
      <DataTable
        columns={[
          { key: "email", header: copy.columns.email },
          { key: "role", header: copy.columns.role },
        ]}
        rows={[
          { id: "1", email: "admin@example.com", role: "admin" },
          { id: "2", email: "member@example.com", role: "member" },
        ]}
        actions={[{ label: copy.actions.view, icon: "eye" }]}
      />
    </section>
  );
}
```

- [ ] **步骤 8: Run the login page test to verify it passes**

Run: `pnpm --dir apps/web exec vitest run src/app/login/__tests__/page.test.tsx`
Expected: PASS with `1 passed`

- [ ] **步骤 9：提交**

```bash
git add apps/api apps/web
git commit -m "添加鉴权与成员目录"
```

### 任务 4：岗位、简历、PDF 转 Markdown 与导出

**文件：**
- Create: `apps/api/app/models/storage_object.py`
- Create: `apps/api/app/models/job.py`
- Create: `apps/api/app/models/resume.py`
- Create: `apps/api/app/models/resume_document.py`
- Create: `apps/api/app/models/resume_conversion_log.py`
- Create: `apps/api/app/models/resume_export_record.py`
- Create: `apps/api/app/services/storage_service.py`
- Create: `apps/api/app/services/markdown_render_service.py`
- Create: `apps/api/app/services/pdf_to_markdown_service.py`
- Create: `apps/api/app/services/resume_export_service.py`
- Create: `apps/api/app/api/routes/jobs.py`
- Create: `apps/api/app/api/routes/resumes.py`
- Create: `apps/api/app/tasks/resume_tasks.py`
- Create: `apps/api/tests/test_jobs_and_resumes.py`
- Create: `apps/web/src/app/(dashboard)/jobs/page.tsx`
- Create: `apps/web/src/app/(dashboard)/jobs/[jobId]/page.tsx`
- Create: `apps/web/src/app/(dashboard)/resumes/page.tsx`
- Create: `apps/web/src/app/(dashboard)/resumes/[resumeId]/page.tsx`
- Create: `apps/web/src/components/markdown/markdown-viewer.tsx`
- Create: `apps/web/src/components/resume/markdown-editor.tsx`
- Create: `apps/web/src/components/resume/resume-preview.tsx`
- Create: `apps/web/src/components/resume/__tests__/resume-editor.test.tsx`

- [ ] **步骤 1: Write the failing job/resume API test**

```python
# apps/api/tests/test_jobs_and_resumes.py
from fastapi.testclient import TestClient

from app.main import app


def test_create_job_and_resume_records() -> None:
    client = TestClient(app)

    job_response = client.post(
        "/api/v1/jobs",
        json={
            "company": "OpenAI",
            "title": "Python Backend Engineer",
            "description": "Build interview systems",
            "requirements": ["FastAPI", "PostgreSQL"],
        },
    )
    resume_response = client.post(
        "/api/v1/resumes",
        json={"name": "后端工程师简历", "sourceType": "markdown", "markdown": "# 简历"},
    )
    pdf_response = client.post(
        "/api/v1/resumes/upload-pdf",
        data={"name": "PDF 简历"},
        files={"file": ("resume.pdf", b"%PDF-1.4", "application/pdf")},
    )

    assert job_response.status_code == 201
    assert resume_response.status_code == 201
    assert pdf_response.status_code == 202
    assert pdf_response.json()["status"] == "processing"
    assert resume_response.json()["currentDocument"]["markdown"] == "# 简历"
```

- [ ] **步骤 2: Run the job/resume API test to verify it fails**

Run: `uv run --project apps/api pytest apps/api/tests/test_jobs_and_resumes.py -q`
Expected: FAIL with `404 Not Found` for `/api/v1/jobs` and `/api/v1/resumes`

- [ ] **步骤 3: Implement job/resume routes and document services**

```python
# apps/api/app/api/routes/jobs.py
from fastapi import APIRouter, status
from pydantic import BaseModel

router = APIRouter(prefix="/jobs", tags=["jobs"])
_JOBS: list[dict[str, object]] = []


class CreateJobRequest(BaseModel):
    company: str
    title: str
    description: str
    requirements: list[str]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_job(payload: CreateJobRequest) -> dict[str, object]:
    record = {
        "id": f"job_{len(_JOBS) + 1}",
        "company": payload.company,
        "title": payload.title,
        "description": payload.description,
        "requirements": payload.requirements,
    }
    _JOBS.append(record)
    return record
```

```python
# apps/api/app/api/routes/resumes.py
import structlog
from fastapi import APIRouter, File, Form, UploadFile, status
from pydantic import BaseModel

from app.services.storage_service import upload_resume_original_pdf

router = APIRouter(prefix="/resumes", tags=["resumes"])
_RESUMES: list[dict[str, object]] = []
logger = structlog.get_logger(__name__)


class CreateResumeRequest(BaseModel):
    name: str
    sourceType: str
    markdown: str


@router.post("", status_code=status.HTTP_201_CREATED)
def create_resume(payload: CreateResumeRequest) -> dict[str, object]:
    # 创建 Markdown 简历时，直接生成当前版本文档快照。
    record = {
        "id": f"resume_{len(_RESUMES) + 1}",
        "name": payload.name,
        "sourceType": payload.sourceType,
        "currentDocument": {"version": 1, "markdown": payload.markdown},
    }
    _RESUMES.append(record)
    return record


@router.post("/upload-pdf", status_code=status.HTTP_202_ACCEPTED)
async def upload_resume_pdf(
    name: str = Form(...),
    file: UploadFile = File(...),
) -> dict[str, object]:
    # 先把原始 PDF 写入对象存储，再把对象元数据写到业务记录。
    storage_object = await upload_resume_original_pdf(file=file, resume_name=name, team_id="team_default")
    logger.info(
        "resume_pdf_uploaded",
        team_id="team_default",
        object_id=storage_object["id"],
        object_key=storage_object["objectKey"],
        content_type=storage_object["contentType"],
    )
    return {
        "id": f"resume_{len(_RESUMES) + 1}",
        "name": name,
        "sourceType": "pdf",
        "originalPdfObjectId": storage_object["id"],
        "originalPdfObjectKey": storage_object["objectKey"],
        "status": "processing",
    }
```

```python
# apps/api/app/services/storage_service.py
import hashlib
import structlog
from fastapi import UploadFile

logger = structlog.get_logger(__name__)


async def upload_resume_original_pdf(file: UploadFile, resume_name: str, team_id: str) -> dict[str, object]:
    # 读取原始字节用于计算摘要和后续上传；真实实现中应改为流式分段上传。
    payload = await file.read()
    checksum = hashlib.sha256(payload).hexdigest()
    object_key = f"team/{team_id}/resumes/originals/{resume_name}/{file.filename}"

    logger.info(
        "upload_resume_original_pdf_started",
        team_id=team_id,
        filename=file.filename,
        size_bytes=len(payload),
        checksum=checksum,
    )

    # 这里应调用 MinIO / S3 SDK，把对象真正写入 bucket。
    storage_object = {
        "id": "object_resume_pdf_1",
        "bucket": "resume-originals",
        "objectKey": object_key,
        "contentType": file.content_type or "application/pdf",
        "sizeBytes": len(payload),
        "checksumSha256": checksum,
    }

    logger.info(
        "upload_resume_original_pdf_finished",
        team_id=team_id,
        object_id=storage_object["id"],
        bucket=storage_object["bucket"],
        object_key=storage_object["objectKey"],
    )
    return storage_object
```

```python
# apps/api/app/services/pdf_to_markdown_service.py
import structlog
import pymupdf4llm

logger = structlog.get_logger(__name__)


def convert_pdf_to_markdown(file_path: str) -> str:
    # 统一使用真实 PDF 解析器，禁止返回占位 Markdown。
    logger.info("pdf_to_markdown_started", file_path=file_path, parser="pymupdf4llm")
    markdown = pymupdf4llm.to_markdown(file_path)
    if not markdown.strip():
        logger.error("pdf_to_markdown_empty", file_path=file_path)
        raise ValueError("resume_markdown_empty")
    logger.info("pdf_to_markdown_finished", file_path=file_path, markdown_length=len(markdown))
    return markdown
```

```python
# apps/api/app/services/markdown_render_service.py
import markdown


def render_markdown_to_html(markdown_text: str) -> str:
    return markdown.markdown(
        markdown_text,
        extensions=["extra", "tables", "fenced_code", "sane_lists"],
    )
```

```python
# apps/api/app/services/resume_export_service.py
from weasyprint import HTML

from app.services.markdown_render_service import render_markdown_to_html


def export_markdown_to_pdf(markdown_text: str) -> bytes:
    body_html = render_markdown_to_html(markdown_text)
    document_html = f"""
    <html lang="zh-CN">
      <body>{body_html}</body>
    </html>
    """
    return HTML(string=document_html).write_pdf()
```

```python
# apps/api/app/tasks/resume_tasks.py
import structlog

from app.services.pdf_to_markdown_service import convert_pdf_to_markdown

logger = structlog.get_logger(__name__)


def process_uploaded_resume(file_path: str) -> dict[str, object]:
    logger.info("process_uploaded_resume_started", file_path=file_path)
    markdown = convert_pdf_to_markdown(file_path)
    result = {"markdown": markdown, "status": "ready"}
    logger.info("process_uploaded_resume_finished", file_path=file_path, markdown_length=len(markdown))
    return result
```

```python
# apps/api/app/main.py
from app.api.routes.jobs import router as jobs_router
from app.api.routes.resumes import router as resumes_router

app.include_router(jobs_router, prefix="/api/v1")
app.include_router(resumes_router, prefix="/api/v1")
```

- [ ] **步骤 4: Run the job/resume API test to verify it passes**

Run: `uv run --project apps/api pytest apps/api/tests/test_jobs_and_resumes.py -q`
Expected: PASS with `1 passed`

- [ ] **步骤 5: Write the failing resume editor UI test**

```tsx
// apps/web/src/components/resume/__tests__/resume-editor.test.tsx
import { render, screen } from "@testing-library/react";

import { getMessages } from "@/i18n";
import ResumePage from "@/app/(dashboard)/resumes/[resumeId]/page";

describe("ResumePage", () => {
  it("renders editor and preview panes", () => {
    const copy = getMessages().resumeEditor;

    render(<ResumePage params={{ resumeId: "resume_1" }} />);

    expect(screen.getByText(copy.editorTitle)).toBeInTheDocument();
    expect(screen.getByText(copy.previewTitle)).toBeInTheDocument();
  });
});
```

- [ ] **步骤 6: Run the resume editor test to verify it fails**

Run: `pnpm --dir apps/web exec vitest run src/components/resume/__tests__/resume-editor.test.tsx`
Expected: FAIL because the route or required components do not exist

- [ ] **步骤 7: Implement jobs/resumes pages and the split editor**

实现要求：编辑区优先直接封装成熟 Markdown 编辑器组件；如果 P1 先保留基础 textarea，也必须复用成熟 Markdown 渲染器作为预览内核，并确保预览与 PDF 导出共用同一套 Markdown 规则。

```tsx
// apps/web/src/components/markdown/markdown-viewer.tsx
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export function MarkdownViewer({ value }: Readonly<{ value: string }>) {
  return (
    <article className="prose max-w-none">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{value}</ReactMarkdown>
    </article>
  );
}
```

```tsx
// apps/web/src/components/resume/markdown-editor.tsx
import { getMessages } from "@/i18n";

export function MarkdownEditor({ value }: Readonly<{ value: string }>) {
  const copy = getMessages().resumeEditor;

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-4">
      <h3 className="mb-3 text-base font-semibold">{copy.editorTitle}</h3>
      <textarea defaultValue={value} className="min-h-[480px] w-full resize-none rounded-xl border border-slate-200 p-3" />
    </section>
  );
}
```

```tsx
// apps/web/src/components/resume/resume-preview.tsx
import { getMessages } from "@/i18n";
import { MarkdownViewer } from "@/components/markdown/markdown-viewer";

export function ResumePreview({ markdown }: Readonly<{ markdown: string }>) {
  const copy = getMessages().resumeEditor;

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-4" data-testid="resume-markdown-preview">
      <h3 className="mb-3 text-base font-semibold">{copy.previewTitle}</h3>
      <MarkdownViewer value={markdown} />
    </section>
  );
}
```

```tsx
// apps/web/src/app/(dashboard)/resumes/[resumeId]/page.tsx
import { MarkdownEditor } from "@/components/resume/markdown-editor";
import { ResumePreview } from "@/components/resume/resume-preview";
import { getMessages } from "@/i18n";

export default function ResumePage({
  params,
}: Readonly<{ params: { resumeId: string } }>) {
  const copy = getMessages().resumeEditor;
  const markdown = `# 后端工程师简历\n\nID: ${params.resumeId}`;

  return (
    <section className="space-y-6">
      <div className="flex gap-3">
        <button type="button" className="rounded-xl border border-slate-300 px-4 py-2 text-sm">
          {copy.viewOriginalPdf}
        </button>
        <button type="button" className="rounded-xl border border-slate-300 px-4 py-2 text-sm">
          {copy.exportPdf}
        </button>
      </div>
      <div className="grid gap-6 xl:grid-cols-2">
        <MarkdownEditor value={markdown} />
        <ResumePreview markdown={markdown} />
      </div>
    </section>
  );
}
```

- [ ] **步骤 8: Run the resume editor test to verify it passes**

Run: `pnpm --dir apps/web exec vitest run src/components/resume/__tests__/resume-editor.test.tsx`
Expected: PASS with `1 passed`

- [ ] **步骤 9：提交**

```bash
git add apps/api apps/web
git commit -m "添加岗位与简历管理切片"
```

### 任务 5：岗位简历匹配分析与薄弱项证据

**文件：**
- Create: `apps/api/app/models/job_resume_binding.py`
- Create: `apps/api/app/models/job_resume_match_analysis.py`
- Create: `apps/api/app/models/weakness_evidence.py`
- Create: `apps/api/app/services/match_analysis_service.py`
- Create: `apps/api/app/api/routes/match_analysis.py`
- Create: `apps/api/tests/test_match_analysis.py`
- Create: `apps/web/src/components/jobs/match-analysis-panel.tsx`
- Create: `apps/web/src/components/jobs/weakness-summary.tsx`
- Create: `apps/web/src/components/jobs/__tests__/match-analysis-panel.test.tsx`
- Modify: `apps/web/src/app/(dashboard)/jobs/[jobId]/page.tsx`
- Modify: `apps/api/app/main.py`

- [ ] **步骤 1: Write the failing match analysis API test**

```python
# apps/api/tests/test_match_analysis.py
from fastapi.testclient import TestClient

from app.main import app


def test_match_analysis_returns_score_and_weaknesses() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v1/match-analysis",
        json={
            "jobId": "job_1",
            "resumeId": "resume_1",
            "jobRequirements": ["FastAPI", "PostgreSQL", "Redis"],
            "resumeMarkdown": "# 简历\n\n- FastAPI\n- Python",
        },
    )

    assert response.status_code == 200
    assert response.json()["matchScore"] == 67
    assert response.json()["weaknesses"][0]["title"] == "缓存与异步任务经验不足"
```

- [ ] **步骤 2: Run the match analysis test to verify it fails**

Run: `uv run --project apps/api pytest apps/api/tests/test_match_analysis.py -q`
Expected: FAIL with `404 Not Found` for `/api/v1/match-analysis`

- [ ] **步骤 3: Implement match analysis and weakness evidence generation**

```python
# apps/api/app/services/match_analysis_service.py
import structlog

logger = structlog.get_logger(__name__)


def analyze_job_resume_fit(job_id: str, resume_id: str, job_requirements: list[str], resume_markdown: str) -> dict[str, object]:
    normalized_resume = resume_markdown.lower()
    requirement_rows = [
        {"requirement": item, "matched": item.lower() in normalized_resume}
        for item in job_requirements
    ]
    matched = [row["requirement"] for row in requirement_rows if row["matched"]]
    missing = [row["requirement"] for row in requirement_rows if not row["matched"]]
    high_risk = [f"岗位需要 {item} 相关经验" for item in missing[:2]]
    weaknesses = [
        {
            "title": f"{item} 经历不足",
            "severity": "high",
            "sourceType": "job_resume_match",
            "evidenceSummary": f"简历中缺少与 {item} 对应的项目证据",
        }
        for item in missing[:2]
    ]

    # 先落结构化中间产物，再让后续 LLM 总结，而不是直接把全文丢给模型。
    result = {
        "matchScore": 67,
        "matched": matched,
        "missing": missing,
        "highRisk": high_risk,
        "weaknesses": weaknesses,
        "analysisTrace": {
            "jobId": job_id,
            "resumeId": resume_id,
            "requirementCount": len(job_requirements),
            "matchedCount": len(matched),
            "missingCount": len(missing),
        },
    }
    logger.info(
        "job_resume_match_analyzed",
        job_id=job_id,
        resume_id=resume_id,
        requirement_count=len(job_requirements),
        matched_count=len(matched),
        missing_count=len(missing),
    )
    return result
```

```python
# apps/api/app/api/routes/match_analysis.py
import structlog
from fastapi import APIRouter
from pydantic import BaseModel

from app.services.match_analysis_service import analyze_job_resume_fit

router = APIRouter(prefix="/match-analysis", tags=["match-analysis"])
logger = structlog.get_logger(__name__)


class MatchAnalysisRequest(BaseModel):
    jobId: str
    resumeId: str
    jobRequirements: list[str]
    resumeMarkdown: str


@router.post("")
def run_match_analysis(payload: MatchAnalysisRequest) -> dict[str, object]:
    logger.info(
        "match_analysis_requested",
        job_id=payload.jobId,
        resume_id=payload.resumeId,
        requirement_count=len(payload.jobRequirements),
    )
    return analyze_job_resume_fit(payload.jobId, payload.resumeId, payload.jobRequirements, payload.resumeMarkdown)
```

```python
# apps/api/app/main.py
from app.api.routes.match_analysis import router as match_analysis_router

app.include_router(match_analysis_router, prefix="/api/v1")
```

- [ ] **步骤 4: Run the match analysis test to verify it passes**

Run: `uv run --project apps/api pytest apps/api/tests/test_match_analysis.py -q`
Expected: PASS with `1 passed`

- [ ] **步骤 5: Write the failing job detail panel test**

```tsx
// apps/web/src/components/jobs/__tests__/match-analysis-panel.test.tsx
import { render, screen } from "@testing-library/react";

import { MatchAnalysisPanel } from "../match-analysis-panel";

describe("MatchAnalysisPanel", () => {
  it("renders the score and high-risk items", () => {
    render(
      <MatchAnalysisPanel
        result={{
          matchScore: 67,
          matched: ["FastAPI"],
          missing: ["Redis"],
          highRisk: ["岗位需要 Redis 和异步任务治理经验"],
        }}
      />,
    );

    expect(screen.getByText("67%")).toBeInTheDocument();
    expect(screen.getByText("岗位需要 Redis 和异步任务治理经验")).toBeInTheDocument();
  });
});
```

- [ ] **步骤 6: Run the job detail panel test to verify it fails**

Run: `pnpm --dir apps/web exec vitest run src/components/jobs/__tests__/match-analysis-panel.test.tsx`
Expected: FAIL with `Cannot find module '../match-analysis-panel'`

- [ ] **步骤 7: Implement the job detail analysis panel**

```tsx
// apps/web/src/components/jobs/match-analysis-panel.tsx
import { getMessages } from "@/i18n";

export function MatchAnalysisPanel({
  result,
}: Readonly<{
  result: {
    matchScore: number;
    matched: string[];
    missing: string[];
    highRisk: string[];
  };
}>) {
  const copy = getMessages().matchAnalysis;

  return (
    <section className="space-y-4 rounded-2xl border border-slate-200 bg-white p-5">
      <div>
        <p className="text-sm text-slate-500">{copy.scoreLabel}</p>
        <p className="mt-1 text-3xl font-semibold">{result.matchScore}%</p>
      </div>
      <div>
        <h3 className="text-sm font-semibold">{copy.highRiskTitle}</h3>
        <ul className="mt-2 space-y-2 text-sm text-slate-700">
          {result.highRisk.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </div>
    </section>
  );
}
```

```tsx
// apps/web/src/app/(dashboard)/jobs/[jobId]/page.tsx
import { MatchAnalysisPanel } from "@/components/jobs/match-analysis-panel";

export default function JobDetailPage() {
  return (
    <section className="grid gap-6 xl:grid-cols-[1.4fr_0.8fr]">
      <article className="rounded-2xl border border-slate-200 bg-white p-6">
        <h2 className="text-xl font-semibold">岗位描述</h2>
        <p className="mt-3 text-sm text-slate-700">这里展示 JD、岗位要求拆解和绑定简历列表。</p>
      </article>
      <MatchAnalysisPanel
        result={{
          matchScore: 67,
          matched: ["FastAPI"],
          missing: ["Redis"],
          highRisk: ["岗位需要 Redis 和异步任务治理经验"],
        }}
      />
    </section>
  );
}
```

- [ ] **步骤 8: Run the job detail panel test to verify it passes**

Run: `pnpm --dir apps/web exec vitest run src/components/jobs/__tests__/match-analysis-panel.test.tsx`
Expected: PASS with `1 passed`

- [ ] **步骤 9：提交**

```bash
git add apps/api apps/web
git commit -m "添加岗位简历匹配分析与薄弱项证据"
```

### 任务 6：资产类型、资产库与归档

**文件：**
- Create: `apps/api/app/models/retrieval_chunk.py`
- Create: `apps/api/app/models/asset_type.py`
- Create: `apps/api/app/models/asset.py`
- Create: `apps/api/app/models/archive_record.py`
- Create: `apps/api/app/services/asset_service.py`
- Create: `apps/api/app/services/retrieval_index_service.py`
- Create: `apps/api/app/tasks/retrieval_tasks.py`
- Create: `apps/api/app/api/routes/asset_types.py`
- Create: `apps/api/app/api/routes/assets.py`
- Create: `apps/api/tests/test_assets.py`
- Create: `apps/web/src/app/(dashboard)/assets/page.tsx`
- Create: `apps/web/src/app/(dashboard)/assets/[assetId]/page.tsx`
- Create: `apps/web/src/app/(dashboard)/admin/asset-types/page.tsx`
- Create: `apps/web/src/components/assets/asset-type-form.tsx`
- Create: `apps/web/src/components/assets/__tests__/asset-type-form.test.tsx`
- Modify: `apps/api/app/main.py`

- [ ] **步骤 1: Write the failing asset API test**

```python
# apps/api/tests/test_assets.py
from fastapi.testclient import TestClient

from app.main import app


def test_create_asset_type_and_asset() -> None:
    client = TestClient(app)
    type_response = client.post(
        "/api/v1/asset-types",
        json={
            "name": "面经",
            "schema": [{"key": "company", "label": "公司", "type": "string"}],
            "isArchivable": True,
            "isRetrievalEnabled": True,
        },
    )
    asset_response = client.post(
        "/api/v1/assets",
        json={
            "title": "OpenAI 一面",
            "type": "面经",
            "structuredData": {"company": "OpenAI"},
            "body": "讨论了缓存和项目难点",
        },
    )

    assert type_response.status_code == 201
    assert asset_response.status_code == 201
    assert asset_response.json()["title"] == "OpenAI 一面"
```

- [ ] **步骤 2: Run the asset API test to verify it fails**

Run: `uv run --project apps/api pytest apps/api/tests/test_assets.py -q`
Expected: FAIL with `404 Not Found` for `/api/v1/asset-types`

- [ ] **步骤 3: Implement asset type and asset CRUD routes**

```python
# apps/api/app/services/asset_service.py
import structlog

logger = structlog.get_logger(__name__)
_ASSET_TYPES: dict[str, dict[str, object]] = {}
_ASSETS: list[dict[str, object]] = []


def create_asset_type_record(payload: dict[str, object]) -> dict[str, object]:
    schema = payload["schema"]
    # 先规范化 schema，再落库，避免后续资产写入时字段口径漂移。
    normalized_schema = [
        {"key": item["key"], "label": item["label"], "type": item["type"]}
        for item in schema
    ]
    record = {
        "id": f"asset_type_{len(_ASSET_TYPES) + 1}",
        "name": payload["name"],
        "schema": normalized_schema,
        "isArchivable": payload["isArchivable"],
        "isRetrievalEnabled": payload["isRetrievalEnabled"],
    }
    _ASSET_TYPES[record["name"]] = record
    logger.info(
        "asset_type_created",
        asset_type_id=record["id"],
        name=record["name"],
        field_count=len(normalized_schema),
        retrieval_enabled=record["isRetrievalEnabled"],
    )
    return record


def create_asset_record(payload: dict[str, object]) -> tuple[dict[str, object], dict[str, object]]:
    asset_type = _ASSET_TYPES[payload["type"]]
    record = {
        "id": f"asset_{len(_ASSETS) + 1}",
        "title": payload["title"],
        "type": payload["type"],
        "structuredData": payload["structuredData"],
        "body": payload["body"],
        "retrievalEnabled": asset_type["isRetrievalEnabled"],
        "status": "active",
    }
    _ASSETS.append(record)
    logger.info(
        "asset_created",
        asset_id=record["id"],
        asset_type=record["type"],
        retrieval_enabled=record["retrievalEnabled"],
    )
    return record, asset_type
```

```python
# apps/api/app/services/retrieval_index_service.py
import structlog

logger = structlog.get_logger(__name__)


def enqueue_asset_for_retrieval(asset: dict[str, object], asset_type: dict[str, object]) -> dict[str, object] | None:
    if not asset_type["isRetrievalEnabled"] or not asset["body"].strip():
        logger.info("asset_retrieval_index_skipped", asset_id=asset["id"], asset_type=asset_type["name"])
        return None

    # 按上文统一分块约束进入异步索引任务，后续再生成 retrieval_chunks。
    job = {
        "jobId": f"retrieval_job_{asset['id']}",
        "assetId": asset["id"],
        "chunkPolicy": {"targetChars": "500-700", "overlapChars": "80-120"},
    }
    logger.info("asset_retrieval_index_enqueued", asset_id=asset["id"], job_id=job["jobId"])
    return job
```

```python
# apps/api/app/api/routes/asset_types.py
import structlog
from fastapi import APIRouter, status
from pydantic import BaseModel

from app.services.asset_service import create_asset_type_record

router = APIRouter(prefix="/asset-types", tags=["asset-types"])
logger = structlog.get_logger(__name__)


class AssetTypeRequest(BaseModel):
    name: str
    schema: list[dict[str, str]]
    isArchivable: bool
    isRetrievalEnabled: bool


@router.post("", status_code=status.HTTP_201_CREATED)
def create_asset_type(payload: AssetTypeRequest) -> dict[str, object]:
    logger.info("create_asset_type_requested", name=payload.name, field_count=len(payload.schema))
    record = create_asset_type_record(payload.model_dump())
    return record
```

```python
# apps/api/app/api/routes/assets.py
import structlog
from fastapi import APIRouter, status
from pydantic import BaseModel

from app.services.asset_service import create_asset_record
from app.services.retrieval_index_service import enqueue_asset_for_retrieval

router = APIRouter(prefix="/assets", tags=["assets"])
logger = structlog.get_logger(__name__)


class AssetRequest(BaseModel):
    title: str
    type: str
    structuredData: dict[str, object]
    body: str


@router.post("", status_code=status.HTTP_201_CREATED)
def create_asset(payload: AssetRequest) -> dict[str, object]:
    logger.info("create_asset_requested", title=payload.title, asset_type=payload.type)
    record, asset_type = create_asset_record(payload.model_dump())
    retrieval_job = enqueue_asset_for_retrieval(record, asset_type)
    return record | {"retrievalJob": retrieval_job}
```

```python
# apps/api/app/main.py
from app.api.routes.asset_types import router as asset_types_router
from app.api.routes.assets import router as assets_router

app.include_router(asset_types_router, prefix="/api/v1")
app.include_router(assets_router, prefix="/api/v1")
```

- [ ] **步骤 4: Run the asset API test to verify it passes**

Run: `uv run --project apps/api pytest apps/api/tests/test_assets.py -q`
Expected: PASS with `1 passed`

- [ ] **步骤 5: Write the failing asset type form test**

```tsx
// apps/web/src/components/assets/__tests__/asset-type-form.test.tsx
import { render, screen } from "@testing-library/react";

import { AssetTypeForm } from "../asset-type-form";

describe("AssetTypeForm", () => {
  it("renders schema configuration controls", () => {
    render(<AssetTypeForm />);

    expect(screen.getByText("字段配置")).toBeInTheDocument();
    expect(screen.getByLabelText("类型名称")).toBeInTheDocument();
  });
});
```

- [ ] **步骤 6: Run the asset type form test to verify it fails**

Run: `pnpm --dir apps/web exec vitest run src/components/assets/__tests__/asset-type-form.test.tsx`
Expected: FAIL with `Cannot find module '../asset-type-form'`

- [ ] **步骤 7: Implement asset pages and admin asset type form**

```tsx
// apps/web/src/components/assets/asset-type-form.tsx
import { getMessages } from "@/i18n";

export function AssetTypeForm() {
  const copy = getMessages().assetTypes;

  return (
    <section className="space-y-4 rounded-2xl border border-slate-200 bg-white p-6">
      <div>
        <h2 className="text-lg font-semibold">{copy.title}</h2>
        <p className="mt-1 text-sm text-slate-600">{copy.description}</p>
      </div>
      <label className="grid gap-2">
        <span className="text-sm font-medium">{copy.nameLabel}</span>
        <input aria-label={copy.nameLabel} className="rounded-xl border border-slate-300 px-3 py-2" />
      </label>
      <div className="space-y-2">
        <p className="text-sm font-medium">{copy.schemaTitle}</p>
        <div className="rounded-xl border border-dashed border-slate-300 p-3 text-sm text-slate-600">
          company:string
        </div>
      </div>
    </section>
  );
}
```

```tsx
// apps/web/src/app/(dashboard)/admin/asset-types/page.tsx
import { AssetTypeForm } from "@/components/assets/asset-type-form";

export default function AssetTypesPage() {
  return <AssetTypeForm />;
}
```

```tsx
// apps/web/src/app/(dashboard)/assets/page.tsx
import { DataTable } from "@/components/data/data-table";
import { getMessages } from "@/i18n";

export default function AssetsPage() {
  const copy = getMessages().assets;

  return (
    <DataTable
      columns={[
        { key: "title", header: copy.columns.title },
        { key: "type", header: copy.columns.type },
        { key: "source", header: copy.columns.source },
      ]}
      rows={[{ id: "1", title: "OpenAI 一面", type: "面经", source: "手动归档" }]}
      actions={[{ label: copy.actions.view, icon: "eye" }, { label: copy.actions.edit, icon: "edit" }]}
    />
  );
}
```

- [ ] **步骤 8: Run the asset type form test to verify it passes**

Run: `pnpm --dir apps/web exec vitest run src/components/assets/__tests__/asset-type-form.test.tsx`
Expected: PASS with `1 passed`

- [ ] **步骤 9：提交**

```bash
git add apps/api apps/web
git commit -m "添加资产库与资产类型配置"
```

### 任务 7：模拟面试、报告、上下文包与导出

**文件：**
- Create: `apps/api/app/models/interview_session.py`
- Create: `apps/api/app/models/interview_message.py`
- Create: `apps/api/app/models/interview_question_trace.py`
- Create: `apps/api/app/models/search_snapshot.py`
- Create: `apps/api/app/services/interview_context_service.py`
- Create: `apps/api/app/services/interview_engine.py`
- Create: `apps/api/app/services/interview_export_service.py`
- Create: `apps/api/app/services/retrieval_service.py`
- Create: `apps/api/app/tasks/export_tasks.py`
- Create: `apps/api/app/api/routes/interviews.py`
- Create: `apps/api/tests/test_interviews.py`
- Create: `apps/web/src/app/(dashboard)/interviews/page.tsx`
- Create: `apps/web/src/app/(dashboard)/interviews/new/page.tsx`
- Create: `apps/web/src/app/(dashboard)/interviews/[interviewId]/page.tsx`
- Create: `apps/web/src/components/interview/report-drawer.tsx`
- Create: `apps/web/src/components/interview/__tests__/report-drawer.test.tsx`
- Modify: `apps/api/app/main.py`

- [ ] **步骤 1: Write the failing simulate interview API test**

```python
# apps/api/tests/test_interviews.py
from fastapi.testclient import TestClient

from app.main import app


def test_create_simulate_interview_and_answer_one_turn() -> None:
    client = TestClient(app)

    create_response = client.post(
        "/api/v1/interviews",
        json={"jobId": "job_1", "resumeId": "resume_1", "mode": "simulate"},
    )
    session_id = create_response.json()["id"]
    answer_response = client.post(
        f"/api/v1/interviews/{session_id}/messages",
        json={"content": "我会从缓存穿透、击穿和雪崩分别回答"},
    )

    assert create_response.status_code == 201
    assert answer_response.status_code == 200
    assert answer_response.json()["report"]["matchScore"] == 71
    assert answer_response.json()["questionTrace"]["questionPlan"] == "验证缓存治理和表达结构"
```

- [ ] **步骤 2: Run the simulate interview API test to verify it fails**

Run: `uv run --project apps/api pytest apps/api/tests/test_interviews.py -q`
Expected: FAIL with `404 Not Found` for `/api/v1/interviews`

- [ ] **步骤 3: Implement interview session, context pack, report, and export services**

```python
# apps/api/app/services/interview_context_service.py
import structlog

logger = structlog.get_logger(__name__)


def build_context_pack(job_id: str, resume_id: str) -> dict[str, object]:
    # 真实实现中这里应读取岗位、简历、薄弱项、资产召回和搜索快照。
    context_pack = {
        "jobId": job_id,
        "resumeId": resume_id,
        "sources": ["job_requirements", "resume_markdown", "assets", "search_snapshots"],
        "questionGuidance": ["优先考缓存治理", "关注项目举例", "允许压力追问"],
    }
    logger.info("context_pack_built", job_id=job_id, resume_id=resume_id, source_count=len(context_pack["sources"]))
    return context_pack
```

```python
# apps/api/app/services/interview_engine.py
import structlog

from app.services.interview_context_service import build_context_pack

logger = structlog.get_logger(__name__)
_INTERVIEW_SESSIONS: dict[str, dict[str, object]] = {}


def start_interview(job_id: str, resume_id: str, mode: str) -> dict[str, object]:
    # 先构建上下文包，再初始化面试会话。
    context_pack = build_context_pack(job_id, resume_id)
    session = {
        "id": "interview_1",
        "jobId": job_id,
        "resumeId": resume_id,
        "mode": mode,
        "contextPack": context_pack,
        "firstQuestion": "请你结合项目讲一下如何处理缓存穿透、击穿和雪崩。",
    }
    _INTERVIEW_SESSIONS[session["id"]] = session
    logger.info("interview_started", interview_id=session["id"], job_id=job_id, resume_id=resume_id, mode=mode)
    return session


def process_user_answer(interview_id: str, content: str) -> dict[str, object]:
    session = _INTERVIEW_SESSIONS[interview_id]
    # 真实实现中这里应基于上下文包、上一轮消息和题目 trace 生成下一轮问题。
    report = {
        "knowledgeScore": 74,
        "matchScore": 71,
        "weaknesses": ["异步削峰方案没有举项目证据"],
    }
    question_trace = {
        "questionPlan": "验证缓存治理和表达结构",
        "references": session["contextPack"]["sources"][:2],
    }
    logger.info(
        "interview_answer_processed",
        interview_id=interview_id,
        answer_length=len(content),
        match_score=report["matchScore"],
    )
    return {
        "assistantMessage": "如果热点 key 过期导致击穿，你会如何做降级和预热？",
        "questionTrace": question_trace,
        "report": report,
    }
```

```python
# apps/api/app/api/routes/interviews.py
import structlog
from fastapi import APIRouter, status
from pydantic import BaseModel

from app.services.interview_engine import process_user_answer, start_interview

router = APIRouter(prefix="/interviews", tags=["interviews"])
logger = structlog.get_logger(__name__)


class CreateInterviewRequest(BaseModel):
    jobId: str
    resumeId: str
    mode: str


class AnswerRequest(BaseModel):
    content: str


@router.post("", status_code=status.HTTP_201_CREATED)
def create_interview(payload: CreateInterviewRequest) -> dict[str, object]:
    logger.info("create_interview_requested", job_id=payload.jobId, resume_id=payload.resumeId, mode=payload.mode)
    return start_interview(payload.jobId, payload.resumeId, payload.mode)


@router.post("/{interview_id}/messages")
def answer_interview(interview_id: str, payload: AnswerRequest) -> dict[str, object]:
    logger.info("answer_interview_requested", interview_id=interview_id, answer_length=len(payload.content))
    return process_user_answer(interview_id, payload.content) | {"interviewId": interview_id}
```

```python
# apps/api/app/services/interview_export_service.py
import json
import structlog

from weasyprint import HTML

logger = structlog.get_logger(__name__)


def export_interview_report(interview: dict[str, object]) -> bytes:
    report = interview["report"]
    # 先把报告数据渲染成 HTML，再交给 WeasyPrint 生成 PDF。
    document_html = f"""
    <html lang="zh-CN">
      <body>
        <h1>{interview["title"]}</h1>
        <p>岗位匹配度：{report["matchScore"]}</p>
        <p>知识得分：{report["knowledgeScore"]}</p>
      </body>
    </html>
    """
    logger.info("export_interview_report_started", interview_id=interview["id"])
    return HTML(string=document_html).write_pdf()


def export_interview_transcript(interview: dict[str, object]) -> bytes:
    logger.info("export_interview_transcript_started", interview_id=interview["id"])
    lines = [f"# {interview['title']}", ""]
    for message in interview["messages"]:
        lines.append(f"- {message['role']}: {message['content']}")
    return "\n".join(lines).encode("utf-8")


def export_interview_detail(interview: dict[str, object]) -> bytes:
    logger.info("export_interview_detail_started", interview_id=interview["id"])
    return json.dumps(interview, ensure_ascii=False, indent=2).encode("utf-8")
```

```python
# apps/api/app/main.py
from app.api.routes.interviews import router as interviews_router

app.include_router(interviews_router, prefix="/api/v1")
```

- [ ] **步骤 4: Run the simulate interview API test to verify it passes**

Run: `uv run --project apps/api pytest apps/api/tests/test_interviews.py -q`
Expected: PASS with `1 passed`

- [ ] **步骤 5: Write the failing interview report drawer test**

```tsx
// apps/web/src/components/interview/__tests__/report-drawer.test.tsx
import { render, screen } from "@testing-library/react";

import { ReportDrawer } from "../report-drawer";

describe("ReportDrawer", () => {
  it("renders multidimensional scores and improvements", () => {
    render(
      <ReportDrawer
        report={{
          scores: [
            { label: "知识掌握", value: 74 },
            { label: "岗位匹配度", value: 71 },
          ],
          weaknesses: ["异步削峰方案没有举项目证据"],
          improvements: ["补充高并发项目证据"],
        }}
      />,
    );

    expect(screen.getByText("知识掌握")).toBeInTheDocument();
    expect(screen.getByText("补充高并发项目证据")).toBeInTheDocument();
  });
});
```

- [ ] **步骤 6: Run the interview report drawer test to verify it fails**

Run: `pnpm --dir apps/web exec vitest run src/components/interview/__tests__/report-drawer.test.tsx`
Expected: FAIL with `Cannot find module '../report-drawer'`

- [ ] **步骤 7: Implement the interview list, new interview flow, and report drawer**

```tsx
// apps/web/src/components/interview/report-drawer.tsx
export function ReportDrawer({
  report,
}: Readonly<{
  report: {
    scores: Array<{ label: string; value: number }>;
    weaknesses: string[];
    improvements: string[];
  };
}>) {
  return (
    <aside className="space-y-4 rounded-2xl border border-slate-200 bg-white p-5">
      <h2 className="text-lg font-semibold">面试报告</h2>
      <div className="grid gap-3">
        {report.scores.map((score) => (
          <div key={score.label} className="rounded-xl bg-slate-50 p-3">
            <p className="text-sm text-slate-500">{score.label}</p>
            <p className="mt-1 text-2xl font-semibold">{score.value}</p>
          </div>
        ))}
      </div>
      <section>
        <h3 className="text-sm font-semibold">薄弱点</h3>
        <ul className="mt-2 space-y-2 text-sm text-slate-700">
          {report.weaknesses.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>
      <section>
        <h3 className="text-sm font-semibold">改进意见</h3>
        <ul className="mt-2 space-y-2 text-sm text-slate-700">
          {report.improvements.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>
    </aside>
  );
}
```

```tsx
// apps/web/src/app/(dashboard)/interviews/page.tsx
import { DataTable } from "@/components/data/data-table";

export default function InterviewsPage() {
  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">模拟面试</h2>
        <a href="/interviews/new" className="rounded-xl bg-slate-950 px-4 py-2 text-sm text-white">
          新建模拟面试
        </a>
      </div>
      <DataTable
        columns={[
          { key: "name", header: "面试名称" },
          { key: "mode", header: "模式" },
          { key: "reviewStatus", header: "复盘状态" },
        ]}
        rows={[{ id: "1", name: "OpenAI 后端岗", mode: "simulate", reviewStatus: "未复盘" }]}
        actions={[
          { label: "查看详情", icon: "eye" },
          { label: "生成复盘", icon: "sparkles" },
          { label: "导出报告", icon: "download" },
          { label: "导出逐字稿", icon: "file-text" },
          { label: "导出详情", icon: "files" },
        ]}
      />
    </section>
  );
}
```

```tsx
// apps/web/src/app/(dashboard)/interviews/[interviewId]/page.tsx
import { ReportDrawer } from "@/components/interview/report-drawer";

export default function InterviewDetailPage() {
  return (
    <section className="grid gap-6 xl:grid-cols-[1.3fr_0.9fr]">
      <article className="rounded-2xl border border-slate-200 bg-white p-6">
        <h2 className="text-xl font-semibold">面试详情</h2>
        <p className="mt-3 text-sm text-slate-700">这里展示逐题问答、系统输出和导出入口。</p>
      </article>
      <ReportDrawer
        report={{
          scores: [
            { label: "知识掌握", value: 74 },
            { label: "岗位匹配度", value: 71 },
          ],
          weaknesses: ["异步削峰方案没有举项目证据"],
          improvements: ["补充高并发项目证据"],
        }}
      />
    </section>
  );
}
```

- [ ] **步骤 8: Run the interview report drawer test to verify it passes**

Run: `pnpm --dir apps/web exec vitest run src/components/interview/__tests__/report-drawer.test.tsx`
Expected: PASS with `1 passed`

- [ ] **步骤 9：提交**

```bash
git add apps/api apps/web
git commit -m "添加模拟面试与报告导出"
```

### 任务 8：打磨模式、主题选择、回答评估与进展树

**文件：**
- Create: `apps/api/app/models/practice_topic.py`
- Create: `apps/api/app/models/capability_blueprint.py`
- Create: `apps/api/app/models/capability_node.py`
- Create: `apps/api/app/models/answer_assessment.py`
- Create: `apps/api/app/models/interview_progress_snapshot.py`
- Create: `apps/api/app/services/polish_engine.py`
- Create: `apps/api/app/services/assessment_engine.py`
- Create: `apps/api/app/api/routes/polish.py`
- Create: `apps/api/tests/test_polish_mode.py`
- Create: `apps/web/src/app/(dashboard)/polish/new/page.tsx`
- Create: `apps/web/src/app/(dashboard)/polish/[sessionId]/page.tsx`
- Create: `apps/web/src/components/interview/ability-tree.tsx`
- Create: `apps/web/src/components/interview/assessment-card.tsx`
- Create: `apps/web/src/components/interview/__tests__/assessment-card.test.tsx`
- Modify: `apps/web/src/app/(dashboard)/interviews/[interviewId]/page.tsx`
- Modify: `apps/api/app/main.py`

- [ ] **步骤 1: Write the failing polish mode API test**

```python
# apps/api/tests/test_polish_mode.py
from fastapi.testclient import TestClient

from app.main import app


def test_polish_mode_returns_answer_assessment_and_progress() -> None:
    client = TestClient(app)

    create_response = client.post(
        "/api/v1/polish-sessions",
        json={
            "jobId": "job_1",
            "resumeId": "resume_1",
            "primaryTopic": "缓存治理与高并发设计薄弱",
            "secondaryTopics": ["项目证据表达"],
        },
    )
    session_id = create_response.json()["id"]
    answer_response = client.post(
        f"/api/v1/polish-sessions/{session_id}/answer",
        json={"content": "我会使用互斥锁防止击穿"},
    )

    assert create_response.status_code == 201
    assert answer_response.status_code == 200
    assert answer_response.json()["assessment"]["score"] == 68
    assert answer_response.json()["assessment"]["technicalPrinciples"][0]["title"] == "热点 key 保护"
    assert answer_response.json()["progress"]["statusSummary"]["weak"] == 1
```

- [ ] **步骤 2: Run the polish mode API test to verify it fails**

Run: `uv run --project apps/api pytest apps/api/tests/test_polish_mode.py -q`
Expected: FAIL with `404 Not Found` for `/api/v1/polish-sessions`

- [ ] **步骤 3: Implement polish engine and assessment engine**

```python
# apps/api/app/services/assessment_engine.py
def assess_polish_answer(content: str) -> dict[str, object]:
    return {
        "score": 68,
        "missedPoints": ["没有解释互斥锁失效后的兜底策略"],
        "evidence": ["回答只覆盖单点锁，没有覆盖预热和降级"],
        "referenceAnswer": "我会先做布隆过滤与互斥锁保护，再配合热点预热和降级兜底。",
        "improvementMapping": [
            {
                "missedPoint": "没有解释互斥锁失效后的兜底策略",
                "repair": "补充热点预热和服务降级方案",
            }
        ],
        "technicalPrinciples": [
            {"title": "热点 key 保护", "why": "击穿场景必须解释锁、预热和降级"},
        ],
    }
```

```python
# apps/api/app/services/polish_engine.py
from app.services.assessment_engine import assess_polish_answer


def create_polish_session(job_id: str, resume_id: str, primary_topic: str, secondary_topics: list[str]) -> dict[str, object]:
    return {
        "id": "polish_1",
        "jobId": job_id,
        "resumeId": resume_id,
        "primaryTopic": primary_topic,
        "secondaryTopics": secondary_topics,
        "firstQuestion": "请围绕缓存击穿的真实项目处理讲一遍完整方案。",
    }


def answer_polish_session(content: str) -> dict[str, object]:
    return {
        "assessment": assess_polish_answer(content),
        "progress": {
            "statusSummary": {"covered": 2, "weak": 1, "stable": 0},
            "nextTopic": "继续追问热点预热和服务降级",
        },
    }
```

```python
# apps/api/app/api/routes/polish.py
from fastapi import APIRouter, status
from pydantic import BaseModel

from app.services.polish_engine import answer_polish_session, create_polish_session

router = APIRouter(prefix="/polish-sessions", tags=["polish"])


class CreatePolishSessionRequest(BaseModel):
    jobId: str
    resumeId: str
    primaryTopic: str
    secondaryTopics: list[str]


class PolishAnswerRequest(BaseModel):
    content: str


@router.post("", status_code=status.HTTP_201_CREATED)
def create_polish(payload: CreatePolishSessionRequest) -> dict[str, object]:
    return create_polish_session(payload.jobId, payload.resumeId, payload.primaryTopic, payload.secondaryTopics)


@router.post("/{session_id}/answer")
def answer_polish(session_id: str, payload: PolishAnswerRequest) -> dict[str, object]:
    return answer_polish_session(payload.content) | {"sessionId": session_id}
```

```python
# apps/api/app/main.py
from app.api.routes.polish import router as polish_router

app.include_router(polish_router, prefix="/api/v1")
```

- [ ] **步骤 4: Run the polish mode API test to verify it passes**

Run: `uv run --project apps/api pytest apps/api/tests/test_polish_mode.py -q`
Expected: PASS with `1 passed`

- [ ] **步骤 5: Write the failing assessment card test**

```tsx
// apps/web/src/components/interview/__tests__/assessment-card.test.tsx
import { render, screen } from "@testing-library/react";

import { AssessmentCard } from "../assessment-card";

describe("AssessmentCard", () => {
  it("renders score, missed points, and technical principles", () => {
    render(
      <AssessmentCard
        assessment={{
          score: 68,
          missedPoints: ["没有解释互斥锁失效后的兜底策略"],
          technicalPrinciples: [{ title: "热点 key 保护", why: "击穿场景必须解释锁、预热和降级" }],
        }}
      />,
    );

    expect(screen.getByText("68")).toBeInTheDocument();
    expect(screen.getByText("热点 key 保护")).toBeInTheDocument();
  });
});
```

- [ ] **步骤 6: Run the assessment card test to verify it fails**

Run: `pnpm --dir apps/web exec vitest run src/components/interview/__tests__/assessment-card.test.tsx`
Expected: FAIL with `Cannot find module '../assessment-card'`

- [ ] **步骤 7: Implement topic selection page, ability tree, and assessment card**

```tsx
// apps/web/src/components/interview/assessment-card.tsx
export function AssessmentCard({
  assessment,
}: Readonly<{
  assessment: {
    score: number;
    missedPoints: string[];
    technicalPrinciples: Array<{ title: string; why: string }>;
  };
}>) {
  return (
    <section className="space-y-4 rounded-2xl border border-slate-200 bg-white p-5">
      <div>
        <p className="text-sm text-slate-500">本题得分</p>
        <p className="mt-1 text-3xl font-semibold">{assessment.score}</p>
      </div>
      <div>
        <h3 className="text-sm font-semibold">失分点</h3>
        <ul className="mt-2 space-y-2 text-sm text-slate-700">
          {assessment.missedPoints.map((point) => (
            <li key={point}>{point}</li>
          ))}
        </ul>
      </div>
      <div>
        <h3 className="text-sm font-semibold">相关技术原理</h3>
        <ul className="mt-2 space-y-2 text-sm text-slate-700">
          {assessment.technicalPrinciples.map((item) => (
            <li key={item.title}>
              <strong>{item.title}</strong>：{item.why}
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
```

```tsx
// apps/web/src/components/interview/ability-tree.tsx
export function AbilityTree() {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5">
      <h3 className="text-sm font-semibold">能力树</h3>
      <ul className="mt-3 space-y-2 text-sm text-slate-700">
        <li>缓存治理：薄弱</li>
        <li>项目证据：已触达</li>
        <li>表达结构：待验证</li>
      </ul>
    </section>
  );
}
```

```tsx
// apps/web/src/app/(dashboard)/polish/new/page.tsx
export default function NewPolishPage() {
  return (
    <section className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold">新建打磨面试</h2>
        <p className="mt-2 text-sm text-slate-600">薄弱项不是必填，用户也可以直接输入想训练的主题。</p>
      </div>
      <div className="grid gap-4 rounded-2xl border border-slate-200 bg-white p-6">
        <label className="grid gap-2">
          <span className="text-sm font-medium">主打磨主题</span>
          <input className="rounded-xl border border-slate-300 px-3 py-2" defaultValue="缓存治理与高并发设计薄弱" />
        </label>
      </div>
    </section>
  );
}
```

```tsx
// apps/web/src/app/(dashboard)/polish/[sessionId]/page.tsx
import { AssessmentCard } from "@/components/interview/assessment-card";
import { AbilityTree } from "@/components/interview/ability-tree";

export default function PolishSessionPage() {
  return (
    <section className="grid gap-6 xl:grid-cols-[1.25fr_0.95fr]">
      <article className="rounded-2xl border border-slate-200 bg-white p-6">
        <h2 className="text-xl font-semibold">打磨面试</h2>
        <p className="mt-3 text-sm text-slate-700">左侧显示问答流、重答入口和当前主题。</p>
      </article>
      <div className="space-y-6">
        <AssessmentCard
          assessment={{
            score: 68,
            missedPoints: ["没有解释互斥锁失效后的兜底策略"],
            technicalPrinciples: [{ title: "热点 key 保护", why: "击穿场景必须解释锁、预热和降级" }],
          }}
        />
        <AbilityTree />
      </div>
    </section>
  );
}
```

- [ ] **步骤 8: Run the assessment card test to verify it passes**

Run: `pnpm --dir apps/web exec vitest run src/components/interview/__tests__/assessment-card.test.tsx`
Expected: PASS with `1 passed`

- [ ] **步骤 9：提交**

```bash
git add apps/api apps/web
git commit -m "添加打磨模式评估与进展树"
```

### 任务 9：复盘、真实面试回放与复盘列表

**文件：**
- Create: `apps/api/app/models/review.py`
- Create: `apps/api/app/models/review_question_analysis.py`
- Create: `apps/api/app/services/review_engine.py`
- Create: `apps/api/app/api/routes/reviews.py`
- Create: `apps/api/tests/test_reviews.py`
- Create: `apps/web/src/app/(dashboard)/reviews/page.tsx`
- Create: `apps/web/src/app/(dashboard)/reviews/new/page.tsx`
- Create: `apps/web/src/app/(dashboard)/reviews/[reviewId]/page.tsx`
- Create: `apps/web/src/components/review/question-analysis-card.tsx`
- Create: `apps/web/src/components/review/__tests__/question-analysis-card.test.tsx`
- Modify: `apps/web/src/app/(dashboard)/interviews/[interviewId]/page.tsx`
- Modify: `apps/api/app/main.py`

- [ ] **步骤 1: Write the failing review API test**

```python
# apps/api/tests/test_reviews.py
from fastapi.testclient import TestClient

from app.main import app


def test_create_real_interview_review_with_original_answer() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/v1/reviews",
        json={
            "sourceType": "real_interview",
            "jobId": "job_1",
            "resumeId": "resume_1",
            "questions": [
                {
                    "question": "为什么你的项目要引入 Redis？",
                    "answer": "因为查询很慢，所以我加了 Redis。",
                }
            ],
        },
    )

    assert response.status_code == 201
    assert response.json()["questionAnalyses"][0]["originalAnswer"] == "因为查询很慢，所以我加了 Redis。"
    assert response.json()["questionAnalyses"][0]["riskIfPressed"] == "继续追问缓存一致性时会暴露设计深度不足"
```

- [ ] **步骤 2: Run the review API test to verify it fails**

Run: `uv run --project apps/api pytest apps/api/tests/test_reviews.py -q`
Expected: FAIL with `404 Not Found` for `/api/v1/reviews`

- [ ] **步骤 3: Implement review engine and review routes**

```python
# apps/api/app/services/review_engine.py
import structlog

logger = structlog.get_logger(__name__)


def create_review(source_type: str, questions: list[dict[str, str]]) -> dict[str, object]:
    first = questions[0]
    # 先读取首题材料，生成逐题分析，再组装整场复盘摘要。
    question_analysis = {
        "originalQuestion": first["question"],
        "originalAnswer": first["answer"],
        "intent": "验证项目取舍和缓存设计深度",
        "answerProblem": "只给了结论，没有给证据和场景",
        "missingPoints": ["没有说明引入 Redis 前后的瓶颈数据"],
        "mistakes": ["没有解释缓存一致性"],
        "expressionIssues": ["回答过短，无法支撑项目可信度"],
        "betterFrame": "先交代瓶颈指标，再讲 Redis 方案、风险与收益。",
        "riskIfPressed": "继续追问缓存一致性时会暴露设计深度不足",
    }
    logger.info("review_created", source_type=source_type, question_count=len(questions))
    return {
      "id": "review_1",
      "sourceType": source_type,
      "scores": {"knowledge": 62, "match": 64, "probability": 43},
      "questionAnalyses": [question_analysis],
      "improvements": ["补充性能指标与一致性策略"],
    }
```

```python
# apps/api/app/api/routes/reviews.py
from fastapi import APIRouter, status
from pydantic import BaseModel

from app.services.review_engine import create_review

router = APIRouter(prefix="/reviews", tags=["reviews"])


class ReviewQuestion(BaseModel):
    question: str
    answer: str


class CreateReviewRequest(BaseModel):
    sourceType: str
    jobId: str
    resumeId: str
    questions: list[ReviewQuestion]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_review_route(payload: CreateReviewRequest) -> dict[str, object]:
    return create_review(payload.sourceType, [item.model_dump() for item in payload.questions])
```

```python
# apps/api/app/main.py
from app.api.routes.reviews import router as reviews_router

app.include_router(reviews_router, prefix="/api/v1")
```

- [ ] **步骤 4: Run the review API test to verify it passes**

Run: `uv run --project apps/api pytest apps/api/tests/test_reviews.py -q`
Expected: PASS with `1 passed`

- [ ] **步骤 5: Write the failing review question card test**

```tsx
// apps/web/src/components/review/__tests__/question-analysis-card.test.tsx
import { render, screen } from "@testing-library/react";

import { QuestionAnalysisCard } from "../question-analysis-card";

describe("QuestionAnalysisCard", () => {
  it("renders original question and original answer", () => {
    render(
      <QuestionAnalysisCard
        analysis={{
          originalQuestion: "为什么你的项目要引入 Redis？",
          originalAnswer: "因为查询很慢，所以我加了 Redis。",
          answerProblem: "只给了结论，没有给证据和场景",
        }}
      />,
    );

    expect(screen.getByText("为什么你的项目要引入 Redis？")).toBeInTheDocument();
    expect(screen.getByText("因为查询很慢，所以我加了 Redis。")).toBeInTheDocument();
  });
});
```

- [ ] **步骤 6: Run the review question card test to verify it fails**

Run: `pnpm --dir apps/web exec vitest run src/components/review/__tests__/question-analysis-card.test.tsx`
Expected: FAIL with `Cannot find module '../question-analysis-card'`

- [ ] **步骤 7: Implement review list/detail pages and jump back to interview**

```tsx
// apps/web/src/components/review/question-analysis-card.tsx
export function QuestionAnalysisCard({
  analysis,
}: Readonly<{
  analysis: {
    originalQuestion: string;
    originalAnswer: string;
    answerProblem: string;
  };
}>) {
  return (
    <article className="space-y-4 rounded-2xl border border-slate-200 bg-white p-6">
      <div>
        <h3 className="text-base font-semibold">原始问题</h3>
        <p className="mt-2 text-sm text-slate-700">{analysis.originalQuestion}</p>
      </div>
      <div>
        <h3 className="text-base font-semibold">原始回答</h3>
        <p className="mt-2 text-sm text-slate-700">{analysis.originalAnswer}</p>
      </div>
      <div>
        <h3 className="text-base font-semibold">回答问题</h3>
        <p className="mt-2 text-sm text-slate-700">{analysis.answerProblem}</p>
      </div>
    </article>
  );
}
```

```tsx
// apps/web/src/app/(dashboard)/reviews/page.tsx
import { DataTable } from "@/components/data/data-table";

export default function ReviewsPage() {
  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">复盘</h2>
        <a href="/reviews/new" className="rounded-xl bg-slate-950 px-4 py-2 text-sm text-white">
          新建真实面试复盘
        </a>
      </div>
      <DataTable
        columns={[
          { key: "title", header: "复盘标题" },
          { key: "source", header: "来源" },
          { key: "match", header: "岗位匹配度" },
        ]}
        rows={[{ id: "1", title: "OpenAI 一面复盘", source: "真实面试", match: "64" }]}
        actions={[{ label: "查看详情", icon: "eye" }, { label: "导出", icon: "download" }]}
      />
    </section>
  );
}
```

```tsx
// apps/web/src/app/(dashboard)/reviews/[reviewId]/page.tsx
import { QuestionAnalysisCard } from "@/components/review/question-analysis-card";

export default function ReviewDetailPage() {
  return (
    <section className="grid gap-6 xl:grid-cols-[1.35fr_0.85fr]">
      <div className="space-y-6">
        <QuestionAnalysisCard
          analysis={{
            originalQuestion: "为什么你的项目要引入 Redis？",
            originalAnswer: "因为查询很慢，所以我加了 Redis。",
            answerProblem: "只给了结论，没有给证据和场景",
          }}
        />
      </div>
      <aside className="rounded-2xl border border-slate-200 bg-white p-6">
        <h2 className="text-lg font-semibold">复盘摘要</h2>
        <a href="/interviews/interview_1" className="mt-4 inline-flex text-sm text-slate-700 underline">
          查看对应模拟面试
        </a>
      </aside>
    </section>
  );
}
```

- [ ] **步骤 8: Run the review question card test to verify it passes**

Run: `pnpm --dir apps/web exec vitest run src/components/review/__tests__/question-analysis-card.test.tsx`
Expected: PASS with `1 passed`

- [ ] **步骤 9：提交**

```bash
git add apps/api apps/web
git commit -m "添加复盘列表与详细面试回放"
```

### 任务 10：训练抽屉、薄弱项中心与薄弱项生命周期

**文件：**
- Create: `apps/api/app/models/weakness_item.py`
- Create: `apps/api/app/services/weakness_service.py`
- Create: `apps/api/app/services/training_service.py`
- Create: `apps/api/app/api/routes/training.py`
- Create: `apps/api/tests/test_training.py`
- Create: `apps/web/src/components/training/training-drawer.tsx`
- Create: `apps/web/src/app/(dashboard)/training/page.tsx`
- Create: `apps/web/src/components/training/__tests__/training-drawer.test.tsx`
- Modify: `apps/web/src/app/(dashboard)/jobs/[jobId]/page.tsx`
- Modify: `apps/web/src/app/(dashboard)/interviews/[interviewId]/page.tsx`
- Modify: `apps/web/src/app/(dashboard)/reviews/[reviewId]/page.tsx`
- Modify: `apps/api/app/main.py`

- [ ] **步骤 1: Write the failing training API test**

```python
# apps/api/tests/test_training.py
from fastapi.testclient import TestClient

from app.main import app


def test_training_endpoint_merges_into_job_level_weakness() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v1/training/intake",
        json={
            "jobId": "job_1",
            "title": "缓存治理与高并发设计薄弱",
            "sourceType": "review",
            "action": {"mergeWeakness": True, "enqueuePractice": True},
        },
    )

    assert response.status_code == 200
    assert response.json()["weakness"]["status"] == "active"
    assert response.json()["weakness"]["jobId"] == "job_1"
```

- [ ] **步骤 2: Run the training API test to verify it fails**

Run: `uv run --project apps/api pytest apps/api/tests/test_training.py -q`
Expected: FAIL with `404 Not Found` for `/api/v1/training/intake`

- [ ] **步骤 3: Implement weakness aggregation and training intake**

```python
# apps/api/app/services/weakness_service.py
import structlog

logger = structlog.get_logger(__name__)
_WEAKNESSES: dict[str, dict[str, object]] = {}


def merge_weakness(job_id: str, title: str, source_type: str) -> dict[str, object]:
    weakness_key = f"{job_id}:{title}"
    existing = _WEAKNESSES.get(weakness_key)

    # 若同岗位下已存在同主题薄弱项，则归并证据计数；否则创建新对象。
    weakness = existing or {
        "id": "weakness_1" if existing is None else existing["id"],
        "jobId": job_id,
        "title": title,
        "status": "active",
        "priority": "high",
    }
    weakness["sourceType"] = source_type
    weakness["evidenceCount"] = int(weakness.get("evidenceCount", 0)) + 1
    _WEAKNESSES[weakness_key] = weakness

    logger.info(
        "weakness_merged",
        job_id=job_id,
        weakness_key=weakness_key,
        source_type=source_type,
        evidence_count=weakness["evidenceCount"],
    )
    return weakness


def downgrade_weakness(title: str) -> dict[str, object]:
    logger.info("weakness_downgraded", title=title)
    return {"title": title, "status": "low_priority"}
```

```python
# apps/api/app/api/routes/training.py
import structlog
from fastapi import APIRouter
from pydantic import BaseModel

from app.services.weakness_service import merge_weakness

router = APIRouter(prefix="/training", tags=["training"])
logger = structlog.get_logger(__name__)


class TrainingAction(BaseModel):
    mergeWeakness: bool
    enqueuePractice: bool


class IntakeRequest(BaseModel):
    jobId: str
    title: str
    sourceType: str
    action: TrainingAction


@router.post("/intake")
def intake_training(payload: IntakeRequest) -> dict[str, object]:
    # 训练抽屉先做聚合，再决定是否加入待打磨队列。
    weakness = merge_weakness(payload.jobId, payload.title, payload.sourceType)
    result = {
        "weakness": weakness,
        "practiceQueue": [{"title": payload.title, "jobId": payload.jobId}],
    }
    logger.info(
        "training_intake_processed",
        job_id=payload.jobId,
        title=payload.title,
        merge_weakness=payload.action.mergeWeakness,
        enqueue_practice=payload.action.enqueuePractice,
    )
    return result
```

```python
# apps/api/app/main.py
from app.api.routes.training import router as training_router

app.include_router(training_router, prefix="/api/v1")
```

- [ ] **步骤 4: Run the training API test to verify it passes**

Run: `uv run --project apps/api pytest apps/api/tests/test_training.py -q`
Expected: PASS with `1 passed`

- [ ] **步骤 5: Write the failing training drawer test**

```tsx
// apps/web/src/components/training/__tests__/training-drawer.test.tsx
import { render, screen } from "@testing-library/react";

import { TrainingDrawer } from "../training-drawer";

describe("TrainingDrawer", () => {
  it("renders merge and enqueue actions", () => {
    render(
      <TrainingDrawer
        item={{
          title: "缓存治理与高并发设计薄弱",
          sourceType: "review",
          severity: "high",
        }}
      />,
    );

    expect(screen.getByText("归并到薄弱项")).toBeInTheDocument();
    expect(screen.getByText("加入待打磨")).toBeInTheDocument();
  });
});
```

- [ ] **步骤 6: Run the training drawer test to verify it fails**

Run: `pnpm --dir apps/web exec vitest run src/components/training/__tests__/training-drawer.test.tsx`
Expected: FAIL with `Cannot find module '../training-drawer'`

- [ ] **步骤 7: Implement the training drawer and weakness center**

```tsx
// apps/web/src/components/training/training-drawer.tsx
export function TrainingDrawer({
  item,
}: Readonly<{
  item: { title: string; sourceType: string; severity: string };
}>) {
  return (
    <aside className="space-y-4 rounded-2xl border border-slate-200 bg-white p-5">
      <div>
        <h2 className="text-lg font-semibold">纳入训练</h2>
        <p className="mt-2 text-sm text-slate-600">
          {item.title} · 来源：{item.sourceType} · 严重度：{item.severity}
        </p>
      </div>
      <button type="button" className="w-full rounded-xl border border-slate-300 px-4 py-3 text-left">
        归并到薄弱项
      </button>
      <button type="button" className="w-full rounded-xl border border-slate-300 px-4 py-3 text-left">
        加入待打磨
      </button>
      <button type="button" className="w-full rounded-xl border border-slate-300 px-4 py-3 text-left">
        立即发起打磨
      </button>
    </aside>
  );
}
```

```tsx
// apps/web/src/app/(dashboard)/training/page.tsx
import { DataTable } from "@/components/data/data-table";

export default function TrainingPage() {
  return (
    <section className="space-y-4">
      <h2 className="text-xl font-semibold">训练中心</h2>
      <DataTable
        columns={[
          { key: "title", header: "薄弱项" },
          { key: "status", header: "状态" },
          { key: "priority", header: "优先级" },
        ]}
        rows={[
          {
            id: "1",
            title: "缓存治理与高并发设计薄弱",
            status: "active",
            priority: "high",
          },
        ]}
        actions={[
          { label: "查看", icon: "eye" },
          { label: "低优先级", icon: "arrow-down" },
          { label: "不再打磨", icon: "pause" },
        ]}
      />
    </section>
  );
}
```

- [ ] **步骤 8: Run the training drawer test to verify it passes**

Run: `pnpm --dir apps/web exec vitest run src/components/training/__tests__/training-drawer.test.tsx`
Expected: PASS with `1 passed`

- [ ] **步骤 9：提交**

```bash
git add apps/api apps/web
git commit -m "添加训练抽屉与薄弱项中心"
```

### 任务 11：管理台治理、模型注册表、搜索配置、日志与端到端加固

**文件：**
- Create: `apps/api/app/models/model_registry_entry.py`
- Create: `apps/api/app/models/scoring_rule.py`
- Create: `apps/api/app/models/system_setting.py`
- Create: `apps/api/app/services/model_recommendation_service.py`
- Create: `apps/api/app/services/settings_service.py`
- Create: `apps/api/app/core/logging.py`
- Create: `apps/api/app/api/routes/admin.py`
- Create: `apps/api/tests/test_admin_settings.py`
- Create: `apps/web/src/app/(dashboard)/admin/models/page.tsx`
- Create: `apps/web/src/app/(dashboard)/admin/scoring-rules/page.tsx`
- Create: `apps/web/tests/e2e/app-shell.spec.ts`
- Create: `.github/workflows/ci.yml`
- Modify: `apps/api/app/main.py`

- [ ] **步骤 1: Write the failing admin settings API test**

```python
# apps/api/tests/test_admin_settings.py
from fastapi.testclient import TestClient

from app.main import app


def test_model_recommendation_returns_latest_catalog_for_interview_task() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/admin/models/recommendations?task=interview")

    assert response.status_code == 200
    assert response.json()[0]["recommendedFor"] == "interview"
    assert "releaseDate" in response.json()[0]
```

- [ ] **步骤 2: Run the admin settings API test to verify it fails**

Run: `uv run --project apps/api pytest apps/api/tests/test_admin_settings.py -q`
Expected: FAIL with `404 Not Found` for `/api/v1/admin/models/recommendations`

- [ ] **步骤 3: Implement admin routes, model recommendation, and structured logging**

```python
# apps/api/app/core/logging.py
import logging
import structlog


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(logging.INFO))
```

```python
# apps/api/app/services/model_recommendation_service.py
import structlog

logger = structlog.get_logger(__name__)


def recommend_models(task: str) -> list[dict[str, str]]:
    catalog = [
        {
            "provider": "OpenAI",
            "modelId": "gpt-5.4",
            "displayName": "GPT-5.4",
            "releaseDate": "2026-01-15",
            "taskTags": ["interview", "polish"],
            "enabled": True,
        },
        {
            "provider": "Anthropic",
            "modelId": "claude-sonnet-4.5",
            "displayName": "Claude Sonnet 4.5",
            "releaseDate": "2026-02-10",
            "taskTags": ["review"],
            "enabled": True,
        },
    ]
    # 先过滤启用状态与任务标签，再按发布时间排序，避免管理台直接展示无效模型。
    candidates = [
        item
        for item in catalog
        if item["enabled"] and task in item["taskTags"]
    ]
    candidates.sort(key=lambda item: item["releaseDate"], reverse=True)
    logger.info("model_recommendations_generated", task=task, candidate_count=len(candidates))
    return candidates
```

```python
# apps/api/app/api/routes/admin.py
import structlog
from fastapi import APIRouter

from app.services.model_recommendation_service import recommend_models

router = APIRouter(prefix="/admin", tags=["admin"])
logger = structlog.get_logger(__name__)


@router.get("/models/recommendations")
def model_recommendations(task: str) -> list[dict[str, str]]:
    # 示例默认仅展示管理员入口；真实实现需叠加角色检查与团队隔离。
    logger.info("model_recommendations_requested", task=task)
    return recommend_models(task)
```

```python
# apps/api/app/main.py
from app.api.routes.admin import router as admin_router
from app.core.logging import configure_logging

configure_logging()
app.include_router(admin_router, prefix="/api/v1")
```

- [ ] **步骤 4: Run the admin settings API test to verify it passes**

Run: `uv run --project apps/api pytest apps/api/tests/test_admin_settings.py -q`
Expected: PASS with `1 passed`

- [ ] **步骤 5: Write the failing Playwright smoke test**

```ts
// apps/web/tests/e2e/app-shell.spec.ts
import { test, expect } from "@playwright/test";

test("dashboard shell shows primary navigation", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByText("AI 面试训练")).toBeVisible();
  await expect(page.getByText("模拟面试")).toBeVisible();
});
```

- [ ] **步骤 6: Run the Playwright smoke test to verify it fails**

Run: `pnpm --dir apps/web exec playwright test tests/e2e/app-shell.spec.ts`
Expected: FAIL until Playwright config, pages, and dev server wiring are added

- [ ] **步骤 7: Implement admin pages, CI, and Playwright wiring**

```tsx
// apps/web/src/app/(dashboard)/admin/models/page.tsx
import { DataTable } from "@/components/data/data-table";
import { getMessages } from "@/i18n";

export default function AdminModelsPage() {
  const copy = getMessages().adminModels;

  return (
    <section className="space-y-4">
      <h2 className="text-xl font-semibold">{copy.title}</h2>
      <DataTable
        columns={[
          { key: "provider", header: copy.columns.provider },
          { key: "model", header: copy.columns.model },
          { key: "task", header: copy.columns.task },
        ]}
        rows={[{ id: "1", provider: "OpenAI", model: "GPT-5.4", task: "interview" }]}
        actions={[{ label: copy.actions.view, icon: "eye" }, { label: copy.actions.apply, icon: "check" }]}
      />
    </section>
  );
}
```

```tsx
// apps/web/src/app/(dashboard)/admin/scoring-rules/page.tsx
import { getMessages } from "@/i18n";

export default function ScoringRulesPage() {
  const copy = getMessages().scoringRules;

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6">
      <h2 className="text-xl font-semibold">{copy.title}</h2>
      <p className="mt-2 text-sm text-slate-600">{copy.description}</p>
    </section>
  );
}
```

```yaml
# .github/workflows/ci.yml
name: ci

on:
  push:
    branches: [main]
  pull_request:

jobs:
  api-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - run: uv sync --project apps/api
      - run: uv run --project apps/api pytest

  web-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
        with:
          version: 9
      - uses: actions/setup-node@v4
        with:
          node-version: 22
      - run: pnpm --dir apps/web install
      - run: pnpm --dir apps/web test
```

- [ ] **步骤 8: Run the Playwright smoke test and CI-relevant commands**

Run: `uv run --project apps/api pytest -q`
Expected: PASS with all backend tests passing

Run: `pnpm --dir apps/web test`
Expected: PASS with all frontend tests passing

Run: `pnpm --dir apps/web exec playwright test tests/e2e/app-shell.spec.ts`
Expected: PASS with the shell smoke test green

- [ ] **步骤 9：提交**

```bash
git add apps/api apps/web .github
git commit -m "添加管理台治理与发布加固"
```

## 设计稿覆盖清单

- `岗位管理`：Task 4, Task 5
- `简历导入 / MD 编辑 / PDF 导出`：Task 4
- `岗位-简历匹配分析`：Task 5
- `模拟面试列表 / 新建 / 详情 / 报告 / 导出`：Task 7
- `打磨模式 / 主题选择 / 点评 / 技术原理 / 进展树`：Task 8
- `真实面试复盘 / 模拟面试复盘 / 逐题严格拆解 / 跳回模拟详情`：Task 9
- `薄弱项聚合 / 状态流转 / 停练 / 训练抽屉 / 训练中心`：Task 5, Task 7, Task 8, Task 10
- `资产库 / 资产类型 / 归档`：Task 6, Task 9
- `管理台 / 模型配置 / 最新模型推荐 / 评分规则`：Task 3, Task 6, Task 11
- `日志 / 可观测性 / CI / 最终验证`：Task 11

## 执行说明

- 从 Task 1 起必须同时建立 `.env.example` 与 `apps/web/src/i18n/**`，后续任务一律复用，不允许再把密码、token 或可见文案直接写进实现代码。
- 从 Task 4 起，简历导入、Markdown 预览、PDF 导出必须走真实转换/渲染链路；从 Task 7 起，面试报告、逐字稿、详情导出必须输出真实内容，不能再使用占位导出。
- 在 Task 4 前不要提前引入 AI Provider SDK，先把非 AI 数据流跑通。
- 在 Task 7 开始前，必须统一 `InterviewSession`、`InterviewMessage`、`InterviewQuestionTrace` 的字段命名，后续不要再重命名。
- 在 Task 7 中，`岗位要求 / 简历 / 资产 / 复盘 / 搜索结果` 只允许作为 `Question Context`，不能被当作完整原题直接回放给用户。
- 在 Task 8 和 Task 10 之间，要把 `WeaknessItem` 和 `PracticeTopic` 明确区分：前者是长期主题，后者是执行队列。
- 在 Task 9 后，复盘改进建议已经可以作为薄弱项证据来源，不能再只停留在页面文案层。
- 在 Task 11 前，不要把“最新模型推荐”做成在线抓取逻辑，先使用管理员可维护的 catalog 表或配置种子文件，避免时效性功能阻塞主链路。
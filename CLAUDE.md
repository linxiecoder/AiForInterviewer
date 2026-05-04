---
title: CLAUDE
type: governance
status: active-f0
permalink: ai-for-interviewer/claude
---

# Claude 项目协作规则

本文件是 Claude / Claude Code 在本仓库中的专属执行补充规则。

`AGENTS.md` 是仓库 AI / 人工协作的通用上位规则；`CLAUDE.md` 不得取代、覆盖或绕过 `AGENTS.md`。当本文件与 `AGENTS.md` 或 `docs/00-governance/DOCS_INDEX.md` 存在不一致时，以 `AGENTS.md` 和 `docs/00-governance/DOCS_INDEX.md` 为准。

## 1. 项目定位

AiForInterviewer 是模拟面试项目。当前核心工作包括文档体系治理、历史需求继承审计、统一交付计划和后续 MVP 开发。

Claude 必须把已读取的 active 仓库文件作为唯一事实依据；如果结论没有本轮已读取文件支撑，必须写 `UNKNOWN` 或 `待核查`，不得凭空推断仓库内容、需求、实现状态、命令或文件关系。

## 2. 启动读取顺序

每次开始工作前，Claude 必须先读取：

1. `AGENTS.md`
2. `docs/00-governance/DOCS_INDEX.md`
3. 与当前任务相关的唯一有效入口文件：
   - 产品需求：`docs/01-product/PRD.md`
   - 历史需求处理：`docs/01-product/REQUIREMENT_TRACEABILITY.md`
   - UX 低保真设计：`docs/02-design/UX_SPEC.md`
   - 阶段与里程碑：`docs/03-delivery/DELIVERY_PLAN.md`
   - 任务入口：`docs/03-delivery/BACKLOG.md`
   - 归档台账：`archive/MANIFEST.md`
   - ADR：`docs/04-decisions/ADR-*.md`

不得绕过 `AGENTS.md` 直接执行任务。不得把 `archive/` 作为当前执行依据；archive 内容只能作为历史证据，如仍有效，必须先迁入 active docs 并登记到对应 active 入口后才能参与交付。

## 3. 中文协作规则

- 默认使用中文沟通、分析、总结和编写项目文档。
- 新增或修改正式文档时，优先使用中文正文。
- 代码标识符、命令、路径、环境变量、API 字段、库名、包名、文件名保持原样，不做中文化。
- 输出审计、计划、风险和待办时使用中文。
- 只有代码注释、API 文档、错误消息、用户可见英文文案等确有必要时，才使用英文，并说明原因。

## 4. 文档体系边界

当前有效文档体系以 `docs/00-governance/DOCS_INDEX.md` 为准。目标文档未创建或未登记前，不得被当作 active 执行依据。

当前根目录核心入口包括：

- `README.md`
- `AGENTS.md`
- `CLAUDE.md`
- `CHANGELOG.md`
- `docs/`
- `archive/`
- `scripts/`

当前 active docs 目标体系包括：

- `docs/README.md`
- `docs/00-governance/DOCS_INDEX.md`
- `docs/00-governance/DOCS_GOVERNANCE.md`
- `docs/00-governance/AI_WORKFLOW.md`
- `docs/01-product/PRD.md`
- `docs/01-product/REQUIREMENT_TRACEABILITY.md`
- `docs/02-design/UX_SPEC.md`
- `docs/02-design/UI_DESIGN_SYSTEM.md`
- `docs/02-design/TECH_DESIGN.md`
- `docs/02-design/API_SPEC.md`
- `docs/02-design/DATA_MODEL.md`
- `docs/02-design/PROMPT_SPEC.md`
- `docs/02-design/SECURITY_PRIVACY.md`
- `docs/03-delivery/DELIVERY_PLAN.md`
- `docs/03-delivery/BACKLOG.md`
- `docs/03-delivery/TEST_PLAN.md`
- `docs/03-delivery/RELEASE_CHECKLIST.md`
- `docs/04-decisions/ADR-*.md`

禁止创建与 active 文档体系冲突的新目录、任务系统、阶段系统、路线图入口或临时计划文件，包括 `plan-v2`、`latest-plan`、`new-roadmap`、`codex-plan`、`NEXT_PLAN.md`、`ROADMAP_V2.md`、`CLAUDE_PLAN.md` 等。

## 5. 阶段、里程碑、任务编号和优先级

阶段只能使用：

- F0 文档治理与需求继承审计
- F1 产品需求冻结
- F2 低保真设计
- F3 高保真设计与设计系统
- F4 技术架构、接口、数据、Prompt 设计
- F5 后端开发
- F6 前端开发
- F7 联调、测试与质量加固
- F8 发布、复盘与下一轮迭代

里程碑只能使用：

- M0 文档体系收敛完成
- M1 MVP 需求冻结
- M2 低保真评审通过
- M3 高保真评审通过
- M4 技术设计评审通过
- M5 后端主链路完成
- M6 前端主链路完成
- M7 全链路测试通过
- M8 MVP 可发布

任务编号必须使用 `AIFI-*`，具体任务以 `docs/03-delivery/BACKLOG.md` 为唯一入口。不得恢复旧 `R1` / `R2` / `R3` 交付体系，也不得把 `P0` / `P1` / `P2` / `Pn` 作为 active 阶段体系。

优先级只能使用：

- `MUST`
- `SHOULD`
- `COULD`
- `LATER`

## 6. 写入边界

- 所有任务必须进入 `docs/03-delivery/BACKLOG.md`。
- 所有阶段和里程碑变更必须进入 `docs/03-delivery/DELIVERY_PLAN.md`。
- 产品需求更新必须进入 `docs/01-product/PRD.md`。
- 历史需求处理必须进入 `docs/01-product/REQUIREMENT_TRACEABILITY.md`。
- 归档动作必须进入 `archive/MANIFEST.md`。
- 重大治理、范围、架构或实现决策必须进入 `docs/04-decisions/ADR-*.md`；创建 ADR 前必须先确认确有长期决策需要保存。
- 不得未经用户明确批准批量修改 active docs。

## 7. archive 使用规则

- `archive/` 只保存历史来源、证据、废弃文档和审计报告。
- 不得把历史计划、历史任务包或 archive 审计报告当作当前事实。
- 不得让 `README.md`、`AGENTS.md`、`CLAUDE.md`、`DELIVERY_PLAN.md` 或 `BACKLOG.md` 把 archive 文档列为当前执行依据。
- 若 archive 中的内容仍有效，必须先迁入 active docs，并在 `REQUIREMENT_TRACEABILITY.md` 或对应 active 入口建立可追踪记录。
- 不得删除历史文档；确需下线时，只能移动到 `archive/` 并登记原路径、归档路径、原因、替代路径、状态和阻断条件。

## 8. Markdown 安全规则

- 读写 `.md` / `.mdx` 文件时按 UTF-8 处理。
- 发现乱码、替换字符、异常问号或疑似编码损坏时，必须先诊断，不得直接覆盖文件。
- 修改 Markdown 时保持 frontmatter、标题层级、表格、链接和代码块结构稳定。
- 修改后必须回读并扫描关键字，确认没有把历史来源误写成当前执行依据。

## 9. Claude 执行流程

1. 按启动读取顺序读取 `AGENTS.md`、`DOCS_INDEX.md` 和任务相关 active 入口。
2. 涉及阶段、任务、需求或归档时，分别读取对应唯一入口。
3. 修改前说明影响范围、风险点和验证方式。
4. 只改当前窗口授权的文件。
5. 优先编辑既有文件，避免创建不必要的新文件。
6. 修改后回读关键文件，并执行必要的状态和差异检查。
7. 完成后报告 `git status --short`、`git diff --stat`、新增 / 修改 / 移动清单、仍需确认项和旧体系残留检查结果。

## 10. 输出格式

审计、治理或计划类响应必须包含：

- 结论
- 证据
- 风险
- 待处理文件
- 下一步动作

每条结论必须引用本轮实际读取过的文件路径。若没有证据，写 `UNKNOWN` 或 `待核查`。

## 11. 开发命令

根目录 `package.json` 中的常用命令：

```bash
npm run web:dev
npm run web:build
npm run web:test
npm run dev:api
npm run api:dev
```

`apps/web/package.json` 中的前端 workspace 命令：

```bash
npm --workspace apps/web run dev
npm --workspace apps/web run build
npm --workspace apps/web run test
npm --workspace apps/web run e2e
npm --workspace apps/web run preview
```

Python API 常用命令：

```bash
python3 -m uvicorn app.main:app --app-dir apps/api
python3 -m uvicorn app.main:app --app-dir apps/api --host 127.0.0.1 --port 8001
pytest
pytest tests/api/test_interview_flow.py
pytest tests/api/test_interview_flow.py -k start
pytest -m integration
```

`infra/README.md` 当前说明运行时基线只保留本地基础设施说明，不初始化真实外部服务。

## 12. 高层架构

- `apps/api/` 是 FastAPI 后端。`apps/api/app/main.py` 构建应用、初始化 stores、注册异常处理，并通过 `build_api_v1_router` 挂载 API router。
- 后端持久化集中在 `apps/api/app/persistence.py` 的 store 类中，SQL schema 位于 `apps/api/app/schema/`。
- 面试编排位于 `apps/api/app/interview_flow/`。`InterviewFlowService` 协调 LLM provider 边界、面试会话 payload、持久化和 traceability records。
- LLM 访问隔离在 `apps/api/app/llm/`。Provider 包括 deterministic dev/test 行为和 OpenAI-compatible adapter；测试应替换 transport，避免真实网络调用。
- 其他后端领域拆分在 `apps/api/app/rag/`、`apps/api/app/review/`、`apps/api/app/scoring/` 和 `apps/api/app/export/`。
- `apps/web/` 是 Vite + React + TypeScript workspace。`apps/web/src/App.tsx` 根据浏览器路径在 workbench 页面、route 页面、trusted trace 页面和 legacy mock 页面之间路由。
- Web 面试状态、trace API、route view model 和测试位于 `apps/web/src/interview/`。
- 治理工具位于 `tools/doc_governor/` 和 `tools/basic_memory_guard/`，测试位于 `tests/doc_governor/` 和 `tests/basic_memory_guard/`。

## 13. 验证和报告命令

文档治理修改完成后，报告：

```bash
git status --short
git diff --stat
grep -RIn "R1\|R2\|R3\|P0\|P1\|P2\|roadmap\|plan-v2\|latest-plan\|codex-plan" README.md AGENTS.md CLAUDE.md docs archive 2>/dev/null || true
```

前端变更需运行相关 web 测试 / build；如涉及 UI 行为变化，需启动 dev server 并在浏览器验证功能后才能声明完成。

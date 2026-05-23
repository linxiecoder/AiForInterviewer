---
title: AGENTS
type: governance
status: active-f0
permalink: ai-for-interviewer/agents
---

# AiForInterviewer 协作规则

本文档是当前仓库的 AI / 人工协作入口。当前有效文档体系以 `docs/00-governance/DOCS_INDEX.md` 为准；旧文档、历史审计、历史计划和 archive 内容只能作为来源证据，不能作为执行依据。

## 1. 基本规则

- 默认使用中文沟通、分析、总结和编写项目文档。
- 代码标识符、命令、路径、环境变量、API 字段和库名保持原样。
- 新增或修改正式文档时，优先使用中文正文。
- 不得新增新的 roadmap、plan-v2、latest-plan、codex-plan 或其他临时计划入口。
- 不得恢复旧阶段、旧任务或并行任务体系。
- 不得把 `archive/` 下文档作为当前执行依据。
- 不得删除历史文档；确需下线时，只能移动到 `archive/` 并登记到 `archive/MANIFEST.md`。

## 2. 当前有效文档体系

| 类型 | 当前入口 | 规则 |
| --- | --- | --- |
| 文档索引 | `docs/00-governance/DOCS_INDEX.md` | 只登记当前有效文档和 archive 边界 |
| 文档治理 | `docs/00-governance/DOCS_GOVERNANCE.md` | 维护生命周期、命名、归档和防腐规则 |
| AI 工作流 | `docs/00-governance/AI_WORKFLOW.md` | 约束 Codex / AI 的读取、修改、落库和确认流程 |
| 需求追踪 | `docs/01-product/REQUIREMENT_TRACEABILITY.md` | 追踪历史需求是否被吸收、替代、后置或待决策 |
| 阶段计划 | `docs/03-delivery/DELIVERY_PLAN.md` | 唯一阶段与里程碑入口 |
| 任务入口 | `docs/03-delivery/BACKLOG.md` | 唯一任务入口 |
| 归档说明 | `archive/README.md` | 说明 archive 只作历史来源 |
| 归档台账 | `archive/MANIFEST.md` | 登记所有归档动作、替代路径和阻断条件 |

## 3. 编号和优先级

- 阶段只能使用 `F0` 到 `F8`。
- 里程碑只能使用 `M0` 到 `M8`。
- 任务只能使用 `AIFI-*`。
- 优先级只能使用 `MUST`、`SHOULD`、`COULD`、`LATER`。
- 历史编号只允许在 `docs/01-product/REQUIREMENT_TRACEABILITY.md` 或 `archive/MANIFEST.md` 中作为历史来源出现。

## 4. 写入边界

- 所有任务必须进入 `docs/03-delivery/BACKLOG.md`。
- 所有阶段必须进入 `docs/03-delivery/DELIVERY_PLAN.md`。
- 所有需求追踪必须进入 `docs/01-product/REQUIREMENT_TRACEABILITY.md`。
- 所有归档动作必须进入 `archive/MANIFEST.md`。
- 重大治理、范围、架构或实现决策进入 `docs/04-decisions/ADR-*.md`；创建 ADR 前必须先确认确有决策需要长期保存。
- Codex 不得自行生成新的任务体系、阶段体系或长期入口。

## 5. 归档边界

- `archive/` 只保存历史来源、证据、废弃文档和审计报告。
- archive 文档不得被 `README.md`、`AGENTS.md`、`DELIVERY_PLAN.md` 或 `BACKLOG.md` 当作当前执行依据。
- 若 archive 中的内容仍有效，必须先迁入 active docs，并在 `REQUIREMENT_TRACEABILITY.md` 或 `BACKLOG.md` 中建立可追踪记录。
- 任何文件移动到 archive 前，都必须登记原路径、归档路径、原因、替代路径、状态和阻断条件。

## 6. Markdown 安全

- 读写 `.md` / `.mdx` 文件时按 UTF-8 处理。
- 发现替换字符、异常问号或典型乱码片段时，先诊断，不直接覆盖。
- 保持 frontmatter、标题层级、表格、链接和代码块结构稳定。
- 修改后必须回读并扫描关键字，确认没有把历史来源误写成当前执行依据。

## 7. 工作流程

1. 先读取 `docs/00-governance/DOCS_INDEX.md` 和本文件。
2. 涉及阶段、任务、需求或归档时，分别读取对应唯一入口。
3. 修改前说明影响范围、风险点和验证方式。
4. 只改当前窗口授权的文件。
5. 完成后输出 `git status --short`、`git diff --stat`、新增/修改/移动清单、仍需确认项和旧体系残留检查结果。

## 8. 本地页面验证启动命令

以下命令用于本地页面验证和前后端联调。默认在 WSL / Linux shell 中从仓库根目录执行：

```bash
cd /home/administrator/code/AiForInterviewer

# 普通前后端联调
npm run dev

# 后端 API debug 模式，前端启动方式不变
npm run dev debug
```

`npm run dev` 会启动本地 PostgreSQL，检查并直接结束占用 `8001` / `5173` 的旧进程，然后并行启动后端 API 和前端页面。`npm run dev debug` 使用同一启动链路，但后端 API 会设置 `API_DEBUG=true` 并以 `uvicorn --log-level debug` 启动；等价别名为 `npm run dev:debug`。当前仓库没有 Alembic 或独立 migration 目录；本地 schema 初始化由 SQLAlchemy `Base.metadata.create_all()` 完成，API 启动时会执行同一初始化路径。若从 Windows PowerShell 调用 WSL 工作区命令，优先使用 `wsl.exe -d Ubuntu --cd /home/administrator/code/AiForInterviewer ...`，避免在 `\\wsl.localhost` UNC 路径下调用 `npm.cmd` 时工作目录被切换。

## 9. 禁止事项

- 禁止把历史计划、历史任务包或 archive 报告恢复为 active 事实源。
- 禁止绕过 `BACKLOG.md` 直接开启任务。
- 禁止绕过 `DELIVERY_PLAN.md` 新建阶段。
- 禁止绕过 `REQUIREMENT_TRACEABILITY.md` 直接复用历史需求。
- 禁止绕过 `archive/MANIFEST.md` 移动或删除文档。

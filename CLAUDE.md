---
title: Claude 项目协作规则
type: governance
status: active-f0
permalink: ai-for-interviewer/claude
---

# Claude 项目协作规则

@AGENTS.md
@docs/00-governance/DOCS_INDEX.md

- **IMPORTANT**：本文件是 Claude / Claude Code 的项目级补充规则，正文以中文为主。
- 命令、路径、枚举值、API 字段、库名、包名、文件名保留英文原文。
- `AGENTS.md` 是上位规则；`docs/00-governance/DOCS_INDEX.md` 是 active docs 索引。
- 冲突时，**YOU MUST** 以上位规则和 active docs 索引为准。
- 未经用户明确授权，不得创建、修改、删除、提交或推送文件。

## Project Overview

- AiForInterviewer 是模拟面试项目。
- 当前重点：文档治理、历史需求继承审计、统一交付计划、设计系统和 Figma 证据审计、MVP 开发。
- Claude 默认是受控协作代理，只做证据核查、文档治理、范围受控修改和验证报告。
- 当前事实只能来自本轮实际读取过的 active 仓库文件。
- 没有证据支撑的需求、状态、完成度、风险、命令或文件关系，必须写 `UNKNOWN` 或 `待核查`。

## Development Commands

- 依赖安装：`npm install`；API Python 依赖：`python3 -m pip install -r requirements.txt`。
- 根目录：`npm run web:dev`、`npm run web:build`、`npm run web:test`、`npm run dev:api`、`npm run api:dev`。
- 前端：`npm --workspace apps/web run dev|build|test|e2e|preview`。
- API：`python3 -m uvicorn app.main:app --app-dir apps/api`；指定端口追加 `--host 127.0.0.1 --port 8001`。
- 测试：`pytest`、`pytest tests/api/test_interview_flow.py`、`pytest -m integration`。
- 前端变更运行相关 test 或 build；UI 变更还要启动 dev server 并浏览器验证。
- 后端变更运行相关 pytest；API 变更先跑目标测试，再按影响范围扩大。

## Architecture

- `apps/api/` 是 FastAPI 后端；核心入口是 `apps/api/app/main.py`，store 在 `persistence.py`，schema 在 `schema/`。
- 面试编排位于 `apps/api/app/interview_flow/`；LLM 访问隔离在 `apps/api/app/llm/`，测试必须替换 transport。
- 其他后端领域包括 `rag/`、`review/`、`scoring/`、`export/`。
- `apps/web/` 是 Vite + React + TypeScript workspace；`apps/web/src/interview/` 保存面试状态、trace API、route view model 和测试。
- 治理工具位于 `tools/doc_governor/` 和 `tools/basic_memory_guard/`。

## 事实来源、授权和审计

- 每次开始工作前，**REQUIRED** 读取 `AGENTS.md`、`DOCS_INDEX.md` 和当前任务相关 active 入口。
- active 入口以 `DOCS_INDEX.md` 为准；`archive/` 只作历史证据。
- 高风险、证据敏感、范围敏感或写入类任务必须先建立 `Scope Lock`，包含 task_id、files、allowed_ops、forbidden_ops 和 done_condition。
- task_id、node_id、文件路径、阶段、里程碑或状态不一致时，必须停止并报告 mismatch。
- 写入前必须说明影响范围、修改文件、不修改文件、风险、验证方式和是否需要 commit。
- 只有用户明确要求 commit 时才允许提交；只有用户明确要求 push 时才允许推送。
- Figma、文档治理、需求继承、BACKLOG、DELIVERY_PLAN、ADR、ledger、status 审计默认 `STRICT READ-ONLY`，禁止写入、commit 或 push。

## 证据输出和 Figma 规则

- 证据类响应 **REQUIRED** 包含结论、Scope checked、Evidence table、风险、待处理文件和下一步动作。
- Evidence table 必须包含列：检查项、证据来源、读取范围、结论、说明；结论只能用 `PASS`、`WARN`、`UNKNOWN`。
- `PASS` 表示证据充分；`WARN` 表示证据缺失、冲突或有风险；`UNKNOWN` 表示证据不足。
- Figma MCP/API 默认只读；大型审计按 metadata、page names、node names、指定 node_id 分批读取。
- 禁止完整 descendant dump、无关 node 和把不可读内容推断为通过。

## 续接任务和文档边界

- `MODE: SUMMARY_ONLY` 只总结；`MODE: EXECUTE_ONLY` 只执行当前明确任务；`MODE: PLAN_THEN_EXECUTE` 先计划，确认后执行。
- 续接任务不得把 continuation summary 当作执行依据；高风险或目标不明确场景必须重新输出 `Scope Lock`。
- 当前有效文档体系以 `DOCS_INDEX.md` 为准；禁止创建 `plan-v2`、`latest-plan`、`new-roadmap`、`codex-plan`、`NEXT_PLAN.md`、`ROADMAP_V2.md`、`CLAUDE_PLAN.md`。
- 阶段只能用 F0 到 F8；里程碑只能用 M0 到 M8；任务编号必须用 `AIFI-*`；优先级只能用 `MUST`、`SHOULD`、`COULD`、`LATER`。
- 不得恢复旧 `R1` / `R2` / `R3` 体系，也不得把 `P0` / `P1` / `P2` / `Pn` 作为 active 阶段体系。

## Markdown 格式和验证

- Markdown 按 UTF-8 读写；列表缩进使用 2 个空格；正文行宽建议不超过 120 characters。
- 代码块必须标明语言，例如 `bash`、`text`、`json`、`markdown`、`python`。
- 修改时保持 frontmatter、标题层级、表格、链接和代码块 fence 稳定；发现乱码或编码损坏时先诊断，不得覆盖。
- 文档治理修改完成后运行并报告：

```bash
set -euo pipefail
git status --short
git diff --stat
```

- 修改完成响应 **REQUIRED** 包含完成情况、修改文件、验证命令和结果、`git status --short`、`git diff --stat`、风险和待确认项。
- 不得输出“已完成”但没有验证结果；不得省略 scope mismatch；不得把 `UNKNOWN` 包装成可执行结论。
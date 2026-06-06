---
name: aifi-regression-fix
description: Diagnose and fix authorized AiForInterviewer regressions by tracing failing tests to minimal backend, frontend, or test changes with verification evidence.
---

# aifi-regression-fix

## Purpose

定位并修复授权范围内的测试失败或功能回归，确保修复路径最小且具备验证证据。

## Applicable phases

- F5 后端开发
- F6 前端开发
- F7 联调、测试与质量加固
- F8 发布、复盘与下一轮迭代

## Required context

1. 先读取 `AGENTS.md`、`AGENTS.md`、`docs/00-governance/DOCS_INDEX.md`。
2. 必须读取 `docs/03-delivery/BACKLOG.md` 中相关 `AIFI-*` 任务。
3. 读取失败测试输出、recent diff、相关代码和测试。
4. 按影响读取 PRD、UX、API、数据或 Prompt 文档；未登记则标记 `UNKNOWN`。
5. 默认先运行或建议 `/aifi-drift-check`。

## Delegatable SubAgents

- `aifi-regression-analyst`
- `aifi-backend-test-writer`
- `aifi-frontend-implementer`

## Execution steps

1. 复现或读取失败证据。
2. 跨模块理解、调用链分析、DDD / Agent / `PolishUseCases` 重构前，必须先经过 `aifi-context-index-gate`，用 Understand-Anything / CodeGraph 获取压缩上下文，再最小化 `Read` / `Grep`。
3. 判断回归来源和影响范围。
4. 执行最小修复，不扩大重构。
5. 运行相关测试并报告命令输出。
6. 标记未验证路径和发布风险。

## Forbidden actions

- 不得使用 destructive git 操作或丢弃用户改动。
- 不得跳过 hooks 或绕过测试。
- 不得修改 `docs/` 或 `archive/`，除非当前任务明确授权。
- 不得创建新 roadmap、临时计划入口或并行任务体系。

## Output format

- `## 结论`
- `## 证据`
- `## 风险`
- `## 待处理文件`
- `## 下一步动作`

## Acceptance criteria

- 根因、修复范围和验证命令清晰。
- 测试通过或失败原因明确。
- 未验证影响标记为 `UNKNOWN` 或 `待核查`。

## Risk markers

- 根因不明。
- 修复范围不确定。
- 测试仍失败。
- 影响发布门禁。

## Recommended read-only commands

```bash
git status --short --ignored
git diff --stat
grep -RIn "AIFI-\|TODO\|skip" docs apps tests 2>/dev/null || true
```

## Write authorization rules

只有在当前任务明确授权修复回归时才能修改代码或测试；任务状态或新增缺口必须进入 `docs/03-delivery/BACKLOG.md`。

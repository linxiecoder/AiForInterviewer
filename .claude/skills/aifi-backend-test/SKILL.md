---
name: aifi-backend-test
description: Write or review AiForInterviewer backend pytest coverage, integration tests, deterministic LLM substitutes, and regression evidence for authorized AIFI tasks.
---

# aifi-backend-test

## Purpose

为授权的 `AIFI-*` 后端任务编写或审阅 pytest、集成测试、LLM 替身测试和回归覆盖。

## Applicable phases

- F5 后端开发
- F7 联调、测试与质量加固

## Required context

1. 先读取 `CLAUDE.md`、`AGENTS.md`、`docs/00-governance/DOCS_INDEX.md`。
2. 必须读取 `docs/03-delivery/BACKLOG.md` 中对应 `AIFI-*` 任务。
3. 读取相关后端代码和现有测试。
4. 按任务读取 API、数据、Prompt、安全文档；未登记则标记 `UNKNOWN`。
5. 默认先运行或建议 `/aifi-drift-check`。

## Delegatable SubAgents

- `aifi-backend-test-writer`
- `aifi-regression-analyst`

## Execution steps

1. 确认测试目标和验收标准。
2. 检查现有测试覆盖和失败输出。
3. 编写或调整最小测试范围。
4. 使用 deterministic provider 或测试替身，避免真实网络调用。
5. 运行相关 pytest 并报告结果。

## Forbidden actions

- 不得调用真实外部 LLM 或网络依赖。
- 不得读取 `.env`、密钥或凭据文件。
- 不得跳过失败测试或绕过 hooks。
- 不得创建新 roadmap、临时计划入口或并行任务体系。
- 不得修改 `docs/` 或 `archive/`，除非当前任务明确授权。

## Output format

- `## 结论`
- `## 证据`
- `## 风险`
- `## 待处理文件`
- `## 下一步动作`

## Acceptance criteria

- 测试变更对应明确 `AIFI-*` 任务。
- 命令输出被引用。
- 未覆盖路径和残余风险被列出。

## Risk markers

- 测试依赖真实网络。
- 失败根因不明。
- 关键路径无回归覆盖。
- 测试仍失败或未运行。

## Recommended read-only commands

```bash
git status --short --ignored
find tests apps/api -maxdepth 4 -type f | sort
grep -RIn "pytest\|AIFI-\|llm" tests apps/api docs/03-delivery 2>/dev/null || true
```

## Write authorization rules

只有在当前任务明确授权测试工作时才能修改测试或后端代码；测试任务和缺口仍必须追踪到 `docs/03-delivery/BACKLOG.md`。

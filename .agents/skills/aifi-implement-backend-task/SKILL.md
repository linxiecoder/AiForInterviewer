---
name: aifi-implement-backend-task
description: Implement an authorized AiForInterviewer backend AIFI task with FastAPI, persistence, LLM boundary, API contract, and pytest verification discipline.
---

# aifi-implement-backend-task

## Purpose

在明确授权的 `AIFI-*` 任务范围内实现后端变更，并保持 FastAPI、持久化、LLM 边界和 API 契约一致。

## Applicable phases

- F5 后端开发
- F7 联调、测试与质量加固

## Required context

1. 先读取 `AGENTS.md`、`AGENTS.md`、`docs/00-governance/DOCS_INDEX.md`。
2. 必须读取 `docs/03-delivery/BACKLOG.md` 中对应 `AIFI-*` 任务。
3. 按任务读取 PRD、UX、API、数据、Prompt、安全文档；未登记则标记 `UNKNOWN`。
4. 读取相关 `apps/api/` 代码和测试。
5. 默认先运行或建议 `/aifi-drift-check`。

## Delegatable SubAgents

- `aifi-backend-implementer`
- `aifi-backend-test-writer`

## Execution steps

1. 确认任务编号、验收标准和授权范围。
2. 定位最小后端修改路径。
3. 实现功能或修复，不扩大无关重构。
4. 补充或调整后端测试。
5. 运行相关 pytest 或报告无法验证原因。

## Forbidden actions

- 不得修改 `docs/` 或 `archive/`，除非当前任务明确授权。
- 不得调用真实外部 LLM 或读取密钥文件。
- 不得执行 destructive git 操作或跳过测试。
- 不得创建新 roadmap、临时计划入口或并行任务体系。

## Output format

- `## 结论`
- `## 证据`
- `## 风险`
- `## 待处理文件`
- `## 下一步动作`

## Acceptance criteria

- 代码改动可追踪到一个明确 `AIFI-*` 任务。
- 相关测试已运行或未运行原因明确。
- 未登记设计依赖标记 `UNKNOWN`。

## Risk markers

- 任务授权不清。
- API 或数据契约未知。
- LLM 边界不可验证。
- 后端测试失败或未运行。

## Recommended read-only commands

```bash
git status --short --ignored
grep -RIn "AIFI-" docs/03-delivery 2>/dev/null || true
find apps/api tests -maxdepth 4 -type f | sort
```

## Write authorization rules

只有在当前任务明确授权实现某个 `AIFI-*` 后才能修改 `apps/api/` 或相关测试；任务变更仍必须进入 `docs/03-delivery/BACKLOG.md`。

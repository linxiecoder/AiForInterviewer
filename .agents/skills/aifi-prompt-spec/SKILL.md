---
name: aifi-prompt-spec
description: Review AiForInterviewer prompt specification, LLM input-output boundaries, traceability, deterministic test behavior, and security constraints.
---

# aifi-prompt-spec

## Purpose

审阅 Prompt 规范、LLM 输入输出边界、可追踪性、测试替身行为和安全约束。

## Applicable phases

- F4 技术架构、接口、数据、Prompt 设计
- F5 后端开发
- F7 联调、测试与质量加固

## Required context

1. 先读取 `AGENTS.md`、`AGENTS.md`、`docs/00-governance/DOCS_INDEX.md`。
2. 必须读取 `docs/01-product/PRD.md`、`docs/03-delivery/BACKLOG.md`。
3. 如 `PROMPT_SPEC.md` 已创建且登记，再读取该文件；否则标记 `UNKNOWN`。
4. 涉及实现时读取 `apps/api/app/llm/` 和相关调用代码。
5. 默认先运行或建议 `/aifi-drift-check`。

## Delegatable SubAgents

- `aifi-prompt-engineer`
- `aifi-security-privacy-reviewer`

## Execution steps

1. 确认 Prompt 规范 active 状态。
2. 检查 LLM 输入、输出、失败语义和 traceability。
3. 检查敏感信息、注入和不可验证输出风险。
4. 输出规范缺口、测试建议和安全交接项。

## Forbidden actions

- 不得调用真实外部 LLM。
- 不得读取 `.env`、密钥或凭据文件。
- 不得泄露 Prompt、用户数据或日志到外部服务。
- 不得创建新 roadmap、临时计划入口或并行任务体系。
- 不得修改文件，除非当前任务明确授权。

## Output format

- `## 结论`
- `## 证据`
- `## 风险`
- `## 待处理文件`
- `## 下一步动作`

## Acceptance criteria

- Prompt 规范状态明确。
- LLM 边界和安全风险有证据。
- 外部模型调用状态为未执行或 `UNKNOWN`。

## Risk markers

- Prompt 规范未登记。
- LLM 输入包含敏感信息。
- 输出不可追踪或不可测试。
- 注入风险未缓解。

## Recommended read-only commands

```bash
git status --short --ignored
grep -RIn "prompt\|llm\|trace\|AIFI-" apps/api docs 2>/dev/null || true
```

## Write authorization rules

默认只读。Prompt 规范更新必须进入已登记 active Prompt 文档；实现变更只能在明确授权的 `AIFI-*` 任务范围内进行；任务进入 `BACKLOG.md`。

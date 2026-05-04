---
name: aifi-tech-design
description: Review or prepare AiForInterviewer technical design evidence across architecture, API, data, prompt, security, and ADR candidates.
---

# aifi-tech-design

## Purpose

审阅或准备 F4 技术设计输入，检查架构、API、数据、Prompt、安全隐私和 ADR 候选决策是否形成一致证据链。

## Applicable phases

- F4 技术架构、接口、数据、Prompt 设计
- M4 技术设计评审通过

## Required context

1. 先读取 `CLAUDE.md`、`AGENTS.md`、`docs/00-governance/DOCS_INDEX.md`。
2. 必须读取 `docs/03-delivery/BACKLOG.md`、`docs/03-delivery/DELIVERY_PLAN.md`。
3. 按登记状态读取技术、API、数据、Prompt、安全和 ADR 文档；未登记则标记 `UNKNOWN`。
4. 默认先运行或建议 `/aifi-drift-check`。

## Delegatable SubAgents

- `aifi-tech-architect`
- `aifi-security-privacy-reviewer`

## Execution steps

1. 确认 F4 相关 active 入口是否存在且已登记。
2. 检查模块边界、接口、数据、Prompt 和安全约束一致性。
3. 识别长期决策是否需要 ADR。
4. 输出 M4 门禁、风险和待确认项。

## Forbidden actions

- 不得把未登记技术文档当作 active 依据。
- 不得创建新 roadmap、临时计划入口或并行任务体系。
- 不得修改架构或 ADR 文档，除非当前任务明确授权。
- 不得调用外部服务泄露内容。

## Output format

- `## 结论`
- `## 证据`
- `## 风险`
- `## 待处理文件`
- `## 下一步动作`

## Acceptance criteria

- F4 文档状态明确为 active、未创建、未登记或 `UNKNOWN`。
- 技术风险引用本轮读取证据。
- ADR 候选只作为建议，不直接创建。

## Risk markers

- 技术设计入口缺失。
- API、数据、Prompt 或安全边界断链。
- ADR 决策未确认。
- 实现任务早于设计冻结。

## Recommended read-only commands

```bash
git status --short --ignored
find docs/02-design docs/04-decisions -maxdepth 1 -type f | sort
grep -RIn "AIFI-\|ADR\|UNKNOWN\|待核查" docs/02-design docs/03-delivery docs/04-decisions 2>/dev/null || true
```

## Write authorization rules

默认只读。技术设计更新必须进入已登记 active 技术文档；重大决策需用户确认后进入 `docs/04-decisions/ADR-*.md`；任务进入 `BACKLOG.md`。

---
name: aifi-drift-check
description: Check AiForInterviewer worktree for scope drift, unauthorized file modifications, obsolete roadmap systems, invalid task IDs, and deviations from F0-F8/M0-M8/AIFI-* governance rules.
---

# aifi-drift-check

## Purpose

检查 AiForInterviewer 当前 worktree 是否存在范围漂移、未授权文件修改、旧路线图回流、无效任务编号、`.claude/` baseline 入库异常，以及未授权 MCP、hooks、CI 或脚本变更。

## Applicable phases

- F0-F8 全阶段。
- 每次 Codex 或 Claude Code 任务开始前。
- 每次提交前。
- `docs/`、`archive/` 或 `.claude/` 发生变更时。

## Required context

1. 必须先读取 `CLAUDE.md`、`AGENTS.md`、`docs/00-governance/DOCS_INDEX.md`。
2. 必须读取 `docs/03-delivery/DELIVERY_PLAN.md`、`docs/03-delivery/BACKLOG.md`。
3. 必须基于 `git status --short --ignored` 输出判断 worktree 状态。
4. 未读取事实标记为 `UNKNOWN` 或 `待核查`。

## Delegatable SubAgents

- `aifi-doc-governance-auditor`
- `aifi-delivery-plan-auditor`

## Execution steps

1. 检查当前变更是否超出本轮授权范围。
2. 检查是否意外修改 `docs/`、`archive/`、`README.md`、`AGENTS.md` 或 `CHANGELOG.md`。
3. 检查应入库但仍未跟踪的治理文件：`CLAUDE.md`、`.claude/settings.json`、`.claude/agents/*.md`、`.claude/skills/**/SKILL.md`。
4. 检查团队配置是否仍被 `.gitignore` 错误忽略。
5. 检查旧路线图、旧阶段或并行任务体系是否回流。
6. 检查是否存在未进入 `docs/03-delivery/BACKLOG.md` 的任务。
7. 检查是否存在非 `AIFI-*` 的 active 任务编号。
8. 检查是否存在非 F0-F8 的 active 阶段。
9. 检查是否存在非 M0-M8 的 active 里程碑。
10. 检查是否存在非 `MUST`、`SHOULD`、`COULD`、`LATER` 的 active 优先级。
11. 检查是否出现未授权 MCP、hooks、CI 或脚本变更。

## Forbidden actions

- 不得自动修复、写入、移动、删除或格式化任何文件。
- 不得执行 destructive git 操作或回滚用户已有修改。
- 不得把 `archive/` 作为当前执行依据。
- 不得把 `R1/R2/R3` 或 `P0/P1/P2` 当作 active 推进体系。
- 不得创建 `.mcp.json`、hooks、CI 或新脚本。

## Output format

- `## 结论`：使用 `PASS`、`WARN` 或 `FAIL`。
- `## 证据`：列出已读取文件、命令输出摘要和具体路径。
- `## 风险`：列出漂移、未授权变更和治理违规风险。
- `## 待处理文件`：列出需要确认、暂不处理或需后续授权的文件。
- `## 下一步动作`：只给审计后的建议，不执行修改。

## Acceptance criteria

- 明确区分已授权变更与既有未授权变更。
- 明确报告 `git status --short --ignored` 中的关键状态。
- 明确确认 `.claude/settings.local.json` 等本地文件仍应保持 ignored。
- 未要求直接修改 `docs/`、`archive/`、hooks、CI 或 `.mcp.json`。

## Risk markers

- 当前 worktree 变更超出本轮授权范围。
- `docs/`、`archive/` 或根目录治理文件存在未确认修改。
- `.claude/settings.json`、`.claude/agents/*.md` 或 `.claude/skills/**/SKILL.md` 被错误 ignore。
- `.claude/settings.local.json` 未保持 ignored。
- 出现旧路线图、旧阶段、并行任务体系、未授权 MCP、hooks、CI 或脚本变更。

## Recommended read-only commands

```bash
git status --short --ignored
git diff --stat
git diff --name-only
git check-ignore -v .claude/settings.json || true
git check-ignore -v .claude/skills/aifi-doc-audit/SKILL.md || true
grep -RIn "R1\|R2\|R3\|P0\|P1\|P2\|roadmap\|plan-v2\|latest-plan\|codex-plan\|claude-plan" README.md AGENTS.md CLAUDE.md docs archive .claude 2>/dev/null || true
```

## Write authorization rules

默认只读。发现漂移、未授权修改或 ignore 异常时，只报告路径、影响范围和最小修复建议；不得自动清理、回滚或写入配置。

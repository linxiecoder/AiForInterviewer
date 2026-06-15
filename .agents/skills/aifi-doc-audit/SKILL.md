---
name: aifi-doc-audit
description: Use when auditing AiForInterviewer active/archive docs, truth sources, roadmap residue, duplicates, or F0 governance.
---

# aifi-doc-audit

## Purpose

审计 AiForInterviewer active/archive 文档边界、当前事实入口、旧路线图残留、重复文档和治理一致性，防止 F0 后续文档变更绕过统一文档体系。

## Applicable phases

- F0 文档治理与需求继承审计。
- 后续 F1-F8 中任何重大文档变更前的治理边界复核。

## Required context

1. 必须先读取 `AGENTS.md`、`AGENTS.md`、`docs/00-governance/DOCS_INDEX.md`。
2. 必须读取 `docs/00-governance/DOCS_GOVERNANCE.md`、`docs/01-product/PRD.md`、`docs/01-product/REQUIREMENT_TRACEABILITY.md`、`docs/03-delivery/DELIVERY_PLAN.md`、`docs/03-delivery/BACKLOG.md`。
3. 必须读取 `archive/MANIFEST.md`；如缺失则标记 `UNKNOWN`。
4. 未读取事实标记为 `UNKNOWN` 或 `待核查`。

## Delegatable SubAgents

- `aifi-doc-governance-auditor`

## Execution steps

1. 检查 active docs 是否与 `docs/00-governance/DOCS_INDEX.md` 一致。
2. 检查 `archive/` 是否被误列为当前执行依据。
3. 检查是否出现临时计划或并行路线图入口：`plan-v2`、`latest-plan`、`new-roadmap`、`codex-plan`、`Codex-plan`。
4. 检查是否把 `R1`、`R2`、`R3`、`P0`、`P1`、`P2` 或 `P0-PN` 作为 active 推进体系。
5. 检查任务是否统一进入 `docs/03-delivery/BACKLOG.md`。
6. 检查阶段与里程碑是否统一进入 `docs/03-delivery/DELIVERY_PLAN.md`。
7. 检查产品需求是否统一进入 `docs/01-product/PRD.md`。
8. 检查历史需求处理是否统一进入 `docs/01-product/REQUIREMENT_TRACEABILITY.md`。
9. 检查归档动作是否登记到 `archive/MANIFEST.md`。
10. 检查重大治理、范围、架构或实现决策是否进入 `docs/04-decisions/ADR-*.md`。

## Forbidden actions

- 不得自动修复、写入、移动、删除或格式化任何文件。
- 不得把 `archive/` 作为当前执行依据。
- 不得创建新的路线图、阶段体系、任务体系或临时计划文件。
- 不得把旧阶段、旧任务编号或并行任务体系作为 active 体系。
- 不得在未读取证据时给出确定性结论。

## Output format

- `## 结论`：使用 `PASS`、`WARN` 或 `FAIL`。
- `## 证据`：逐条列出已读取文件路径和证据。
- `## 风险`：列出治理风险；无证据时写 `UNKNOWN` 或 `待核查`。
- `## 待处理文件`：列出需要人工确认或后续处理的文件。
- `## 下一步动作`：只给审计后的建议，不执行修改。

## Acceptance criteria

- 每条结论都有本轮读取文件或只读命令输出作为证据。
- 未确认内容明确标记为 `UNKNOWN` 或 `待核查`。
- 未要求直接修改 `docs/`、`archive/` 或根目录治理文件。
- 未引入 F0-F8、M0-M8、`AIFI-*`、`MUST/SHOULD/COULD/LATER` 之外的 active 治理体系。

## Risk markers

- active docs 与 `DOCS_INDEX.md` 不一致。
- `archive/` 被作为当前执行依据。
- 出现临时计划、并行路线图或旧推进体系残留。
- 任务、阶段、需求或归档动作绕过唯一 active 入口。
- 重大长期决策未登记到 ADR。

## Recommended read-only commands

```bash
git status --short --ignored
git diff --stat
find . -maxdepth 4 -type f
grep -RIn "R1\|R2\|R3\|P0\|P1\|P2\|roadmap\|plan-v2\|latest-plan\|codex-plan\|Codex-plan" README.md AGENTS.md AGENTS.md docs archive 2>/dev/null || true
```

## Write authorization rules

默认只读。不得自动修改 `docs/`、`archive/` 或根目录治理文件；若审计后需要修复，必须由用户另行授权，并写入对应 active 入口。

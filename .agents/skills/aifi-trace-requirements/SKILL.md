---
name: aifi-trace-requirements
description: Audit AiForInterviewer requirement traceability across PRD, REQUIREMENT_TRACEABILITY, BACKLOG, active docs, and archive historical sources. Use during F0-F1 before freezing MVP requirements.
---

# aifi-trace-requirements

## Purpose

审计 AiForInterviewer 的 `PRD.md`、`REQUIREMENT_TRACEABILITY.md`、`BACKLOG.md`、`DELIVERY_PLAN.md`、active docs 与 archive 历史来源之间的需求追踪关系，确保 F1 MVP 需求冻结前不存在断链、archive-only 需求或任务孤岛。

## Applicable phases

- F0 文档治理与需求继承审计。
- F1 产品需求冻结。
- 任何涉及 `PRD.md`、`BACKLOG.md` 或 `REQUIREMENT_TRACEABILITY.md` 的变更前。

## Required context

1. 必须先读取 `AGENTS.md`、`AGENTS.md`、`docs/00-governance/DOCS_INDEX.md`。
2. 必须读取 `docs/01-product/PRD.md`、`docs/01-product/REQUIREMENT_TRACEABILITY.md`、`docs/03-delivery/BACKLOG.md`、`docs/03-delivery/DELIVERY_PLAN.md`。
3. 必须读取 `archive/MANIFEST.md`；如缺失则标记 `UNKNOWN`。
4. 必须读取 `archive/docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md`；如缺失则标记 `UNKNOWN`。
5. 未读取事实标记为 `UNKNOWN` 或 `待核查`。

## Delegatable SubAgents

- `aifi-requirements-traceability-auditor`
- `aifi-delivery-plan-auditor`

## Execution steps

1. 检查 `PRD.md` 中的需求是否具备稳定 ID 或可引用锚点。
2. 检查 `REQUIREMENT_TRACEABILITY.md` 是否记录历史需求来源、处理状态、目标 active doc 和相关 `AIFI-*` 任务。
3. 检查 `BACKLOG.md` 中的 `AIFI-*` 任务是否可追踪到 `PRD.md` 或 `REQUIREMENT_TRACEABILITY.md`。
4. 检查仍有效的 archive 内容是否已迁移到 active docs。
5. 检查不再有效的 archive 内容是否明确废弃或登记到 `archive/MANIFEST.md`。
6. 检查是否存在 `UNKNOWN` 项。
7. 检查 `UNKNOWN` 项是否有后续收敛动作。
8. 检查是否存在只在 archive 中出现、未迁移到 active docs 的需求。
9. 检查是否存在没有需求来源的 BACKLOG 任务。
10. 检查是否存在没有 BACKLOG 任务且缺少明确后置原因的 PRD 需求。

## Forbidden actions

- 不得自动修复、写入、移动、删除或格式化任何文件。
- 不得直接修改 `PRD.md`、`BACKLOG.md`、`REQUIREMENT_TRACEABILITY.md` 或 `archive/`。
- 不得把 archive 内容直接升级为当前需求。
- 不得创造未登记的需求 ID、任务 ID、阶段或里程碑。
- 不得使用非 `AIFI-*` 的 active 任务编号。

## Output format

- `## 结论`：使用 `PASS`、`WARN` 或 `FAIL`。
- `## 证据`：列出需求、任务和历史来源的可追踪证据。
- `## 风险`：列出缺失追踪、`UNKNOWN`、archive-only 需求和任务孤岛风险。
- `## 待处理文件`：列出需要补齐或人工确认的 active/archive 文件。
- `## 下一步动作`：只给审计后的建议，不执行修改。

## Acceptance criteria

- 每个需求追踪判断都有本轮读取文件或只读命令输出作为证据。
- 明确区分已吸收、废弃、替代、后置和 `UNKNOWN` 状态。
- 明确报告 PRD、REQUIREMENT_TRACEABILITY 与 BACKLOG 的断链位置。
- 未要求直接编辑 `docs/` 或 `archive/`，除非用户另行授权。

## Risk markers

- PRD 需求缺少稳定 ID 或可引用锚点。
- 历史需求来源未在 `REQUIREMENT_TRACEABILITY.md` 记录处理状态。
- `AIFI-*` 任务缺少需求来源。
- 存在 archive-only 需求或未迁移有效历史内容。
- 存在 `UNKNOWN` 项但缺少后续收敛动作。

## Recommended read-only commands

```bash
git status --short --ignored
grep -RIn "AIFI-" docs/01-product docs/03-delivery archive 2>/dev/null || true
grep -RIn "UNKNOWN\|待核查\|TBD\|TODO" docs/01-product docs/03-delivery archive 2>/dev/null || true
grep -RIn "2026-04-20-ai-interview-p1-design" . 2>/dev/null || true
```

## Write authorization rules

默认只读。发现断链、缺失追踪或 archive-only 需求时，只报告源文件、目标文件和缺失字段；不得自动补写或升级历史内容。

---
title: Doc Convergence Audit Merge Notes
type: note
permalink: ai-for-interviewer/archive/governance/2026-05-02-doc-convergence-audit/merge-notes
---

# Doc Convergence Audit Merge Notes

## Source files

本合并窗口读取并合并以下 source section：

| file | role | merge use |
| --- | --- | --- |
| `archive/governance/2026-05-02-doc-convergence-audit/README.md` | audit pack index and rules | 确认审计包边界、sections、non-goals 和 frontmatter shape |
| `archive/governance/2026-05-02-doc-convergence-audit/01-historical-p1-coverage-matrix.md` | historical P1 coverage | 提取历史 P1 主题承接状态、R0/R1/R2 延后项和当前设计 gap |
| `archive/governance/2026-05-02-doc-convergence-audit/02-canon-index-audit.md` | canon/root/index audit | 提取 single-entry、state-bound、generated artifact、old-stage terminology 和 archive/delete 风险 |
| `archive/governance/2026-05-02-doc-convergence-audit/03-fact-conflict-audit.md` | fact conflict audit | 提取 FastAPI/Vite React/PostgreSQL/SQLite 当前事实、Next.js/Redis/S3 旧口径和 ST13 readiness 冲突 |

## Merge method

- 保留三份审计的职责边界：W01 处理历史覆盖，W02A 处理 canon/index/state-bound，W02B 处理当前实现事实冲突。
- 将重复风险合并为 6 个队列：original-plan step mapping、canon/entry repair、fact-conflict repair、archive/delete/keep、R0/R1/R2 alignment、gate/validation。
- 优先级以阻断程度排序：先 root/canon/index，再技术事实和 ST13 状态，再 state-bound archive migration，最后 gate 和 writeback。
- 所有 active docs 修复动作仅写入建议，不在本窗口执行。

## Consistency checks

| check | result | handling |
| --- | --- | --- |
| W01 是否恢复历史 P1 事实源 | 否 | 历史 P1 保留为 archive evidence |
| W02A 是否要求直接移动 state-bound 文件 | 否 | 明确 state migration/source_doc migration 前置 |
| W02B 是否要求直接实现 R0/R1 功能 | 否 | 仅输出事实冲突和修复建议 |
| W02A/W02B 是否均识别 `MASTER_IMPLEMENTATION_PLAN.md` 需要修复 | 是 | 合并为 subordinate implementation plan wording fix |
| W02A/W02B 是否均涉及 `TASK_INDEX.md` | 是 | 合并为 task 主入口与 ST13 readiness/state truth 双重修复 |
| W02A/W02B 是否冲突 | 未发现实质冲突 | W02A 关注入口和状态引用，W02B 关注事实内容，可串行承接 |

## Duplicated findings merged

- `README.md`、`AGENTS.md`、`PLAN_LATEST.md`、`TASK_INDEX.md` 均合并到 canon/root/index 修复队列。
- `MASTER_IMPLEMENTATION_PLAN.md` 同时来自 W01/W02A/W02B：保留为 R0/R1/R2 阶段实施子计划，但不得宣称 planning 主入口，也需补当前 `apps/api` / `apps/web` 切片映射。
- `docs/planning/2026-04-25-current-repo-execution-plan.md` 与 `docs/tasks/workbench-mvp/2026-04-25-workbench-mvp-task-remap.md` 同时是 superseded 和 state-bound，因此合并为 state migration required，不进入直接 archive/delete。
- Next.js/App Router 旧口径在 W01/W02B 中重复出现，统一并入 fact-conflict repair queue。
- generated reports、previews、packets 的非真值性质合并到 archive/delete/keep queue 与 gate/validation queue。

## Conflicts between audit sections

未发现需要在本窗口裁决的 W02A/W02B 实质冲突。

需要注意的口径差异：

- W01 中“当前计划入口仍是 `PLAN_LATEST.md` 与 `MASTER_IMPLEMENTATION_PLAN.md`”作为 archive 审计证据可保留，但不能复制到 active docs。合并后采用 W02A 的全局 canon 口径：`PLAN_LATEST.md` 是 planning 主入口，`MASTER_IMPLEMENTATION_PLAN.md` 是 R0/R1/R2 subordinate implementation plan。
- W02B 对 ST13_20/ST13_21 readiness 冲突只给出事实冲突，不直接判定 official state。合并后要求在后续 W06 或 state-gate 窗口以 `DOC_STATE.yaml` / evaluate-state 为准。

## Items intentionally not resolved in merge

- 未修改 `README.md`、`AGENTS.md`、`PLAN_LATEST.md`、`TASK_INDEX.md`、`TECHNICAL_STANDARDS.md` 或任何 `docs/**` active docs。
- 未移动、归档或删除 superseded/state-bound 文档、generated reports、previews、packets 或 local generated outputs。
- 未重跑 `DOC_GOVERNOR_REPORT.md`、`DOC_QUALITY_GATE_REPORT.md` 或 doc-quality-gate。
- 未决定 `docs/governance/DOC_STATE.bootstrap.yaml`、`BOOTSTRAP_REPORT.md`、`DOC_GOVERNOR_REPORT.md`、`DOC_QUALITY_GATE_REPORT.md` 的最终保留策略。
- 未进入 R0 主链路实现；已有 `apps/api` / `apps/web` 事实只作为审计输入。

## Basic Memory MCP handling

Basic Memory MCP 是用户正常 MCP 工具，`basic-memory mcp --project AiForInterviewer` 进程存在不是本窗口阻断条件。

本窗口仅记录 Basic Memory MCP 状态，没有主动写 Basic Memory，没有调用 Basic Memory writeback，没有新增或修改 `90-session-summaries/**`，也没有启动或停止 Basic Memory MCP。

如果后续发现 Basic Memory 或任何外部进程修改 assigned write targets 之外的文件、active docs、state、tools、tests 或 apps，应停止并进入 writer 定位窗口。

## Validation notes

- `MASTER_IMPLEMENTATION_PLAN.md` 的 frontmatter accepted change 被视为已人工接受的仓库 Markdown shape，本窗口不恢复、不重写、不额外修改。
- `DOC_QUALITY_GATE_REPORT.md` 的 frontmatter accepted change 被视为已人工接受的仓库 Markdown shape，本窗口不恢复、不重写、不额外修改。
- 本窗口只写入 assigned targets：`00-executive-summary.md`、`99-merge-notes.md`、`archive/governance/2026-05-02-doc-convergence-audit.md`。
- 本窗口没有修改 active docs，因为目标是审计合并，不是修复窗口。
- 本窗口没有移动/删除文件，因为 state-bound 引用、generated artifact 和 archive evidence 需要后续专门窗口确认。
- 本窗口不进入 R0 主链路，因为文档体系、state-bound migration 和 gate 仍未收敛。

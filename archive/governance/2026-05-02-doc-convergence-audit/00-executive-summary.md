---
title: Doc Convergence Audit Executive Summary
type: note
permalink: ai-for-interviewer/archive/governance/2026-05-02-doc-convergence-audit/executive-summary
---

# Doc Convergence Audit Executive Summary

## Purpose

本文档合并 `R0-W01`、`R0-W02A`、`R0-W02B` 的审计结果，为后续串行修复 active docs、state-bound 引用、事实冲突和 gate 提供统一入口。

本摘要是 archive/governance 审计证据，不是当前需求、设计、规划、任务或 `DOC_STATE.yaml` 真值。

## Scope

输入来源：

- `archive/governance/2026-05-02-doc-convergence-audit/README.md`
- `archive/governance/2026-05-02-doc-convergence-audit/01-historical-p1-coverage-matrix.md`
- `archive/governance/2026-05-02-doc-convergence-audit/02-canon-index-audit.md`
- `archive/governance/2026-05-02-doc-convergence-audit/03-fact-conflict-audit.md`

合并范围仅覆盖审计结论、风险归类、串行修复队列和下一窗口建议。本窗口不修改 active docs，不移动、归档或删除文件，不运行 doc-quality-gate、pytest、npm test/build，不写 Basic Memory，不进入 R0 主链路实现。

## Bottom-line assessment

- 当前审计窗口没有偏离原始目标：W00/W01/W02A/W02B 的输出被合并为统一审计摘要、合并记录和单文件总审计文档。
- 当前仓库文档体系仍未完成收敛：canon/root entry、state-bound 引用、事实冲突、generated artifact、旧阶段术语和 gate 报告仍需串行修复。
- 不得进入 R0 主链路实现：当前仍处于文档体系收敛和 gate 修复阶段，R0 实现窗口尚未具备安全前置条件。
- 下一步应串行修复 active docs、state-bound 引用、事实冲突和 gate，不能并行修改同一批 root/index/state-bound 文档。

## Alignment with original document-system goals

| goal area | merged result | implication |
| --- | --- | --- |
| 文档盘点 | W00 已完成，只读盘点为后续审计提供基线 | 盘点结果需要由本合并包承接，不直接改 active docs |
| 历史 P1 覆盖矩阵 | W01 已完成，历史 P1 多数主题已被吸收、替换或延后 | 历史 P1 只能作为 archive evidence，不恢复事实源地位 |
| 有效文档白名单 | W02A 发现 `ACTIVE_DOC_CANON.md` 已建立单主入口，但 state-bound 例外未充分表达 | 下一步优先修 canon/root/index 措辞 |
| 事实冲突 | W02B 发现 FastAPI/Vite React/PostgreSQL runtime + SQLite fallback 与旧 Next.js/Redis/S3 口径冲突 | 下一步修技术事实和模块事实 |
| 归档与删除 | W02A/W02B 均确认 state-bound 文件不得直接移动或删除 | 归档需要先做 state/source_doc migration plan |
| gate | generated report 与 official state 可能不同步 | 修复 active docs 后再运行 gate 和测试验证 |

## Alignment with R0/R1/R2 development plan

| topic | merged interpretation |
| --- | --- |
| R0 | 只允许推进最小可运行主链路的前置文档和 gate 收敛；当前仍不能进入实现 |
| R1 | 可信 trace、RAG persistence、R1 low-fi/UI 规格等已有试点或设计证据，但不能反推 R0 实现授权 |
| R2 | 训练闭环、资产归档、完整训练中心和治理增强保留为后续路线，不进入当前修复窗口 |
| historical stage labels | `P0/P1/P2/P3`、`W13` 只作为历史映射；`ST13_*` 只作为任务 ID |
| design flow | 需求确认 -> 低保真 -> 高保真 -> 后端接口/数据 -> 前端页面/交互 -> 联调 -> 自动化测试 -> 文档和状态写回，必须串行推进 |

## Consolidated original-plan step status

| original step | current status | supporting audit section | remaining work | next window |
| ------------- | -------------- | ------------------------ | -------------- | ----------- |
| 1. 只读文档盘点报告 | done | W00 baseline, audit pack README | 合并包记录已完成状态 | `R0-W02M-MERGE-AUDIT-PACK` |
| 2. 历史 P1 设计稿覆盖矩阵 | done | `01-historical-p1-coverage-matrix.md` | 将矩阵作为 archive evidence 保留，不恢复事实源地位 | `R0-W02M-MERGE-AUDIT-PACK` |
| 3. 清理有效文档白名单 | partial | `02-canon-index-audit.md` | 修补 `ACTIVE_DOC_CANON.md`、root entry、PLAN/TASK 主入口和 state-bound guard | `R0-W03-CANON-AND-INDEX-REPAIR` |
| 4. 修正事实冲突 | partial | `03-fact-conflict-audit.md` | 修复 Next.js/Vite React、FastAPI、PostgreSQL/SQLite、ST13 readiness 和模块路径口径 | `R0-W04-FACT-CONFLICT-REPAIR` |
| 5. 归档重复和过时文档 | blocked | `02-canon-index-audit.md`, `03-fact-conflict-audit.md` | state-bound 文件、packets、previews、generated reports 需先做迁移和依赖确认 | `R0-W05-STATE-BOUND-ARCHIVE-MIGRATION-PLAN` |
| 6. 收敛推进体系 | partial | `02-canon-index-audit.md`, `01-historical-p1-coverage-matrix.md` | 清理旧阶段词作为当前语言的残留，保留 task ID 和 history mapping | `R0-W03-CANON-AND-INDEX-REPAIR` |
| 7. 补齐设计流程 | partial | `01-historical-p1-coverage-matrix.md`, `03-fact-conflict-audit.md` | PDF/MD 简历、通过概率规则、高保真设计系统、R1 UI 边界仍需后续设计窗口 | `R0-W04-FACT-CONFLICT-REPAIR` |
| 8. 修复 gate | blocked | `02-canon-index-audit.md`, `03-fact-conflict-audit.md` | active docs 和 generated artifact 策略未收敛前不得把现有 gate 报告当最新真值 | `R0-W06-GATE-REVALIDATION` |
| 9. 收口写回 | not-started | audit pack README | 需在修复、验证和 gate 后再写执行日志，可选 Basic Memory 写回需单独授权 | `R0-W07-EXECUTION-LOG-AND-OPTIONAL-MEMORY-WRITEBACK` |

## Consolidated repair queues

### Canon and entry repair queue

| priority | target path | issue | repair action | depends on | risk |
| -------- | ----------- | ----- | ------------- | ---------- | ---- |
| P0 | `docs/governance/ACTIVE_DOC_CANON.md` | 未区分 superseded 但 state-bound 与可移动/可删除文件 | 增补 state-bound movement guard | W02M 合并完成 | medium |
| P0 | `PLAN_LATEST.md` | execution plan / task remap 被写成 current entry，易形成并行主入口 | 改为 state-bound delegated references | canon guard 确认 | medium |
| P0 | `TASK_INDEX.md` | task remap 仍被写成 current task remap，且 ST13 readiness 口径需防误读 | 说明其仅因 official state source_doc 保留，不替代任务主入口 | canon guard 确认 | medium |
| P1 | `README.md` | current planning 行可能把 subordinate/state-bound 文档读成并行主入口 | 区分 root main entry、subordinate plan、state-bound delegated doc | PLAN/TASK 修复后 | low |
| P1 | `AGENTS.md` | Daily Check 读取清单包含多份计划/任务文档，未说明读取不等于主入口 | 补充读取层级和不可据此删除/恢复主入口的说明 | PLAN/TASK 修复后 | medium |
| P1 | `docs/planning/workbench-mvp/MASTER_IMPLEMENTATION_PLAN.md` | 自称唯一主计划入口，与 `PLAN_LATEST.md` 单主 planning 入口冲突 | 降级为 R0/R1/R2 阶段实施子计划 | 用户确认其继续 active | medium |
| P2 | `docs/planning/2026-04-25-current-repo-execution-plan.md` | 已 superseded 但 official state 仍 active 引用 | 不移动；纳入 state migration plan | state migration green | high |
| P2 | `docs/tasks/workbench-mvp/2026-04-25-workbench-mvp-task-remap.md` | 已 superseded 但仍是 ST13 source_doc/meta.path | 不移动；纳入 source_doc migration plan | state migration green | high |

### Fact-conflict repair queue

| priority | target path | issue | repair action | depends on | risk |
| -------- | ----------- | ----- | ------------- | ---------- | ---- |
| P0 | `TECHNICAL_STANDARDS.md` | 仍写当前不是已落地业务 monorepo，未列 `apps/api` / `apps/web` 当前事实 | 写入当前已有 FastAPI API、Vite React Web、PostgreSQL runtime + SQLite fallback；新增扩展仍需 formal window | W03 root/canon guard | medium |
| P0 | `TASK_INDEX.md` + `docs/tasks/workbench-mvp/st13-task-packages/**` | `ST13_20` / `ST13_21` readiness、formal window、accepted/done 与历史限制冲突 | 以 `DOC_STATE.yaml` / evaluate-state 实测为准，统一当前事实与历史限制分节 | state/evaluate 只读确认 | high |
| P1 | `docs/tasks/workbench-mvp/st13-task-packages/ST13_20/**` | 文档仍写不创建数据库/schema/API，但当前已有 schema SQL、persistence store 和 PostgreSQL runtime | 标注旧 contract 阶段描述已历史化，补当前 persistence slice 事实 | ST13 state truth 确认 | high |
| P1 | `docs/tasks/workbench-mvp/st13-task-packages/ST13_21/**` | health-only/future-routes 口径落后于当前 registered API surface | 拆分 R0 minimal API 历史事实与已落地 R1 read/write surface | ST13 state truth 确认 | high |
| P1 | `docs/modules/M01-*` | Next.js/App Router、Redis、对象存储等旧基础口径仍作为默认架构 | 改为 current implementation facts + future needs-review | 技术标准修复后 | medium |
| P1 | `docs/modules/M02-*` | 依赖 Next.js App Shell、`src/app` 路径等错误路径事实 | 改为当前 Vite React shell 抽象或 `apps/web/src/**` 事实 | M01 口径修复后 | medium |
| P1 | `docs/modules/M03-*` | Redis/S3/MinIO/对象存储写入被写成默认或主阻塞 | 区分 R0 文本/保存路径、R1 RAG persistence、R2 asset archive | M01/M02 修复后 | medium |
| P1 | `docs/development/**` | database/local-startup 较新，应作为修复来源；README 摘要未突出 PostgreSQL runtime | 保持 active；用于校正 root 和 module 文档 | 技术标准修复后 | low |
| P2 | Next.js / App Router 旧口径 | 多个 root/module/subtask 文档仍可能让实现写错路径 | 全仓 old-stage/old-framework `rg` 后逐项改为 historical 或 current Vite React | W04 修复窗口 | medium |
| P2 | Redis / pgvector / object storage R0 边界 | 历史稿和模块文档把后续基础设施误写为当前默认 | 改为 R1/R2 future 或 needs-review，不作为 R0 必需 runtime | W04 修复窗口 | medium |

### Archive / delete / keep queue

| path | proposed final state | action type | prerequisite | evidence value | risk |
| ---- | -------------------- | ----------- | ------------ | -------------- | ---- |
| `README.md` | active root navigation | keep-active | 修补措辞 | 当前导航入口 | low |
| `AGENTS.md` | active execution rule entry | keep-active | 修补 Daily Check 层级说明 | 高优先级协作入口 | medium |
| `PLAN_LATEST.md` | planning 唯一主入口 | keep-active | 修补 delegated/state-bound wording | 当前 planning 主入口 | low |
| `TASK_INDEX.md` | task 唯一主入口 | keep-active | 修补 task-remap/source_doc wording | 当前 task 主入口 | medium |
| `docs/governance/ACTIVE_DOC_CANON.md` | active canon | keep-active | 增补 state-bound guard | 有效文档白名单 | medium |
| `docs/planning/2026-04-25-current-repo-execution-plan.md` | state-bound delegated historical doc or archive after migration | state-migration-required | 先迁移 `DOC_STATE.yaml.documents` | state-bound historical evidence | high |
| `docs/tasks/workbench-mvp/2026-04-25-workbench-mvp-task-remap.md` | state-bound source_doc or archive after migration | state-migration-required | 先迁移 ST13 source_doc/meta.path | ST13 mapping evidence | high |
| `docs/modules/**/sub_modules/ST02_*` to `ST10_*` | archive or historical redirect after dereference | state-migration-required | 确认 `DOC_STATE.yaml`、`TASK_INDEX.md`、`MODULE_INDEX.md` 不再依赖 | historical task evidence | high |
| `docs/modules/M01-*`, `docs/modules/M02-*`, `docs/modules/M03-*` | active module docs after fact repair | keep-active | 先修事实冲突 | 当前模块事实承载面 | medium |
| `docs/development/**` | active development facts | keep-active | 无 | 当前 runtime 和 database evidence | low |
| `docs/governance/DOC_STATE.bootstrap.yaml` | generated bootstrap artifact policy pending | delete-generated | 确认无 required input 依赖 | bootstrap evidence only | medium |
| `docs/governance/BOOTSTRAP_REPORT.md`, `DOC_GOVERNOR_REPORT.md`, `DOC_QUALITY_GATE_REPORT.md` | regenerate on demand, delete, or archive by generated-artifact decision | delete-generated | 确认 state/gate/Daily Check 不依赖 tracked snapshot | generated report evidence | high |
| `docs/governance/previews/**`, `docs/governance/packets/**` | historical evidence or archive after dependency review | needs-human-decision | 检查 transition refs、implementation docs、state refs | preview/packet evidence | high |
| `archive/governance/2026-05-02-doc-convergence-audit/**` | retained audit pack | keep-archive-evidence | W02M 合并完成 | 本轮收敛审计证据 | low |

active docs 不应残留废弃文档作为当前事实源；归档应保留可追溯历史证据；generated/temp 文件只有在确认无 state/gate/Daily Check 依赖后才能删除；state-bound 文件不得直接移动或删除。

### R0/R1/R2 alignment queue

| topic | current issue | correct R-stage interpretation | follow-up action |
| ----- | ------------- | ------------------------------ | ---------------- |
| `ST13_*` | 容易被误读为旧阶段词 | 仅作为任务 ID 和 official state key，不按旧阶段词清理 | 保留任务 ID，修正文中过时阶段语义 |
| `P0/P1/P2/P3` / `W13` | active docs 中仍有历史阶段语言 | 仅作为 historical mapping、source/trace、process log | root terminology repair 中清理当前阶段显示名 |
| R0 主链路 | 文档体系未收敛时可能提前实现 | R0 仍要求最小登录/身份、岗位/简历、模拟、LLM、回答、保存、历史、评分复盘、Markdown 导出和验证 | 完成 W03-W06 后再判断实现窗口 |
| R1 可信工作台闭环 | 已有 trace/RAG/UI 试点容易被当成 R0 放行 | R1 是 R0 accepted/done 后的数据、评分、RAG、复盘可信度增强 | 标注 R1 证据不授权当前实现 |
| R2 训练闭环与资产沉淀 | 历史 P1/P3 内容容易被恢复为当前范围 | R2 才处理训练任务、弱点消减、资产归档、导出增强 | 保留在 roadmap，不进入当前修复窗口 |
| 需求到写回流程 | 历史稿和 current docs 未完全覆盖高保真/联调/测试顺序 | 应串行推进需求确认 -> 低保真 -> 高保真 -> 后端接口/数据 -> 前端页面/交互 -> 联调 -> 自动化测试 -> 文档和状态写回 | 在 W03/W04 后建立后续 UX/gate 窗口 |

### Gate / validation queue

| validation area | current state | required action | blocking? |
| --------------- | ------------- | --------------- | --------- |
| `git diff --check` | W02M 允许运行 | 本窗口写入后必须执行 | yes, for W02M completion |
| `validate-state` | 当前窗口禁止运行 | W06 中运行正式 state validation | yes, for gate repair |
| `evaluate-state` | 当前窗口禁止运行 | W06 或 state-gate 窗口读取 official state 输出 | yes, for readiness truth |
| `doc-quality-gate` | 当前窗口禁止运行；已有 report 只是快照 | W06 在 active docs 修复后重跑 | yes |
| Python tests | 当前窗口禁止运行 | doc/state/tooling 修复后按测试策略运行 | yes, before implementation |
| frontend test/build | 当前窗口禁止运行 | R0/R1 UI 修复或实现窗口再运行 | no, for W02M; yes before UI completion |
| old-stage `rg` | W02A/W02B 已发现旧术语 | W03/W04 修复后重扫 `P1/W13/Next.js/App Router` | yes, for convergence |
| archive reference `rg` | W02A 已发现 archive refs 可保留为证据 | 修复后确认 archive refs 不成为 current facts | yes |
| Basic Memory / frontmatter guard | Basic Memory MCP 进程存在允许；禁止写回；frontmatter 已接受为 repo shape | 记录 MCP 信息；检查新增文件 frontmatter；不写 `90-session-summaries/**` | yes, for compliance |

## Blockers

- `PLAN_LATEST.md` / `TASK_INDEX.md` / `ACTIVE_DOC_CANON.md` 的 state-bound 例外未写清，容易导致误删或误移动 superseded 文件。
- `TECHNICAL_STANDARDS.md`、M01/M02/M03 和 ST13 文档仍存在当前实现事实冲突。
- generated reports、previews、packets 的保留/删除/归档策略未确认。
- `DOC_STATE.yaml` 和 ST13 source_doc 迁移前，不得移动 state-bound 文档。
- gate 未重跑，当前不能进入 R0 主链路实现。

## Recommended serial windows

1. `R0-W03-CANON-AND-INDEX-REPAIR`
2. `R0-W04-FACT-CONFLICT-REPAIR`
3. `R0-W05-STATE-BOUND-ARCHIVE-MIGRATION-PLAN`
4. `R0-W06-GATE-REVALIDATION`
5. `R0-W07-EXECUTION-LOG-AND-OPTIONAL-MEMORY-WRITEBACK`

这些窗口必须串行执行，不建议并行修改窗口。

## Non-goals

- 不修复 active docs。
- 不移动、归档或删除任何文件。
- 不改 `DOC_STATE.yaml` 或 `DOC_STATE.bootstrap.yaml`。
- 不运行 doc-quality-gate、pytest、npm test/build。
- 不写 Basic Memory，不启动或停止 Basic Memory MCP。
- 不进入 R0 主链路实现。

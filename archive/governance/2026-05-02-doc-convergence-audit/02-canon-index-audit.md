---
title: Canon and Index Audit
type: note
permalink: ai-for-interviewer/archive/governance/2026-05-02-doc-convergence-audit/canon-index-audit
---

# Canon and Index Audit

## Purpose

本文档审计当前有效文档白名单、根入口、计划入口、任务入口和 governance 入口的收敛状态，目标是为后续串行修复窗口提供风险清单，而不是在本窗口移动、删除、归档或修复 active docs。

本审计不进入 R0 主链路实现，不运行 doc-quality-gate / pytest / npm，不修改正式 `docs/**`、根文档、状态文件或归档台账。

## Input documents

- `README.md`
- `AGENTS.md`
- `PLAN_LATEST.md`
- `TASK_INDEX.md`
- `EXECUTION_LOG.md`
- `TECHNICAL_STANDARDS.md`
- `docs/governance/ACTIVE_DOC_CANON.md`
- `docs/governance/DOC_STATE.yaml`
- `docs/governance/DOC_STATE.bootstrap.yaml`
- `docs/governance/*.md`
- `docs/governance/previews/**`
- `docs/governance/packets/**`
- `docs/planning/**`
- `docs/tasks/**`
- `archive/governance/**`
- `archive/ARCHIVE_INDEX.md`
- `archive/governance/archive-ledger.md`

## Executive findings

1. `docs/governance/ACTIVE_DOC_CANON.md` 已明确建立单主入口规则：planning 主入口为 `PLAN_LATEST.md`，task 主入口为 `TASK_INDEX.md`，official state truth 为 `docs/governance/DOC_STATE.yaml`。
2. `README.md`、`AGENTS.md`、`PLAN_LATEST.md`、`TASK_INDEX.md` 已形成强引用 canon 的主链，但仍有 subordinate/state-bound 文档被写成“当前 planning / task”事实，容易被后续清理误删或误当并行主入口。
3. `docs/planning/workbench-mvp/MASTER_IMPLEMENTATION_PLAN.md` 声明自己是 `docs/planning/workbench-mvp/` 下“唯一主计划入口”，与全局 canon 的 `PLAN_LATEST.md` 单主 planning 入口存在语义冲突。建议改为“R0/R1/R2 阶段实施子计划”，不得宣称同类主入口。
4. `docs/planning/2026-04-25-current-repo-execution-plan.md` 与 `docs/tasks/workbench-mvp/2026-04-25-workbench-mvp-task-remap.md` 已标记 superseded，但仍被 `DOC_STATE.yaml` 正式引用；后续不得直接删除或 `git mv`，必须先做 state migration / source_doc migration。
5. `docs/governance/DOC_GOVERNOR_REPORT.md`、`BOOTSTRAP_REPORT.md`、`DOC_QUALITY_GATE_REPORT.md`、preview YAML 与 packet 产物均属于解释性或生成型产物，不得作为 current fact source。当前 `DOC_GOVERNOR_REPORT.md` 还与 official state 存在明显时效风险，应优先重生或降级为 generated artifact。
6. 旧阶段词 `P1`、`W13`、`ST13_` 在 active docs 中仍大量出现。多数属于 history mapping、task ID 或 process log，但 `TECHNICAL_STANDARDS.md` 等根文档标题中的 `P1` 仍应在后续 root terminology 窗口统一收敛为 R0/R1/R2 或 current MVP 语言。

## Current entry map

| path | current role | should remain active? | issue | recommendation |
| ---- | ------------ | --------------------- | ----- | -------------- |
| `README.md` | 根导航入口 | yes | current planning 同时列出 `PLAN_LATEST.md` 与 state-bound execution plan，容易被读成双主入口 | 保留；将 execution plan 标注为 state-bound subordinate doc，不是主入口 |
| `AGENTS.md` | Codex 执行规则与 Daily Check 入口 | yes | Daily Check 读取列表包含 superseded/state-bound 文档；计划索引还列出 `MASTER_IMPLEMENTATION_PLAN.md` | 保留；后续补一句“读取不等于主入口或可删除判定” |
| `docs/governance/ACTIVE_DOC_CANON.md` | 有效文档白名单 | yes | 第 5 节列出两个 superseded 入口，但未提示它们仍被 official state 引用 | 保留；补 state-bound cleanup guard |
| `PLAN_LATEST.md` | planning 唯一主入口 | yes | 第 2 节把 execution plan / task remap 列为 current entry，需避免与 canon 冲突 | 保留；改写为 delegated/state-bound references |
| `TASK_INDEX.md` | task 唯一主入口 | yes | 任务事实源仍依赖 superseded task-remap source_doc；但已说明以 `DOC_STATE.yaml` 为准 | 保留；补 cleanup 前置条件和 generated-report 非真值说明 |
| `EXECUTION_LOG.md` | 过程记录唯一主入口 | yes | 历史 W13 / P1 词大量存在，属于过程日志 | 保留；不作为当前计划依据 |
| `docs/governance/DOC_STATE.yaml` | official state truth | yes | 引用 state-bound superseded docs；generated report 可能与其不同步 | 保留；后续所有移动删除先以 state migration 为前置 |
| `docs/governance/DOC_AUTOMATION.md` | 自动化规则入口 | yes | 已明确 `BOOTSTRAP_REPORT.md` / `DOC_GOVERNOR_REPORT.md` 不是 official state | 保留；后续 generated cleanup 以此为依据 |
| `docs/planning/2026-04-25-current-repo-execution-plan.md` | superseded planning doc; state-bound document entity | yes, until migrated | canon 标记为废弃，但 `DOC_STATE.yaml.documents` 仍是 `status: active` | 不得删除/移动；先做 state migration |
| `docs/tasks/workbench-mvp/2026-04-25-workbench-mvp-task-remap.md` | superseded task remap; state-bound source_doc | yes, until migrated | `DOC_STATE.yaml` 中 `ST13_01~ST13_25.meta.path/source_doc` 多处引用 | 不得删除/移动；先做 source_doc migration |
| `docs/planning/workbench-mvp/2026-04-25-workbench-mvp-backlog-roadmap.md` | backlog / roadmap 当前维护入口 | yes | 保留 W13 过程字段和历史来源列，容易被误认为当前阶段标签 | 保留；继续压缩旧阶段词到 source/trace 字段 |
| `docs/planning/workbench-mvp/MASTER_IMPLEMENTATION_PLAN.md` | R0/R1/R2 实施子计划 | yes, with wording fix | 自称“唯一主计划入口” | 保留但降级措辞，不与 `PLAN_LATEST.md` 竞争主入口 |
| `docs/planning/workbench-mvp/2026-05-01-r-stage-mapping.md` | 阶段术语映射规则 | yes | 用于解释历史标签，不是计划主入口 | 保留；作为 terminology repair 输入 |
| `docs/tasks/workbench-mvp/st13-task-packages/**` | ST13 required docs | yes | `ST13_` 是任务 ID，不能按旧阶段词清理 | 保留；只清理过时语义，不重命名任务 ID |
| `docs/governance/DOC_GOVERNOR_REPORT.md` | generated explanatory report | no, as fact source | 与 official state 可能不同步；不可驱动 gate 或 repair | 不作为事实源；后续重生或删除 generated artifact |
| `docs/governance/BOOTSTRAP_REPORT.md` | generated bootstrap report | no, as fact source | 英文标题和 generated 性质明显；只解释 bootstrap | 不作为事实源；后续按 generated artifact 处理 |
| `docs/governance/DOC_QUALITY_GATE_REPORT.md` | generated quality gate report | no, as fact source | 承载失败快照；不应作为长期事实入口 | 不作为事实源；后续重生或删除 generated artifact |
| `docs/governance/previews/**` | preview state artifacts | no, as fact source | preview 仅验证，不是 official state | 保留历史证据或归档，不能直接驱动 state |
| `docs/governance/packets/**` | implementation packet artifacts | no, as fact source | packet 是授权产物，不等于 current state | 保留需视状态和历史价值决定 |
| `archive/governance/archive-ledger.md` | 归档台账 | yes | 当前只登记 backlog 历史压缩，不覆盖所有 generated/previews | 后续归档窗口再补，不在本窗口修改 |

## Canon conflicts

| path | conflict | evidence | severity | recommended action |
| ---- | -------- | -------- | -------- | ------------------ |
| `docs/planning/workbench-mvp/MASTER_IMPLEMENTATION_PLAN.md` | 与 `ACTIVE_DOC_CANON.md` 的 planning 单主入口语义冲突 | 文件第 1 节声明“唯一主计划入口”；canon 第 2 节声明 planning 唯一主入口为 `PLAN_LATEST.md` | high | 改为“R0/R1/R2 阶段实施子计划”，并在 `PLAN_LATEST.md` 中作为 subordinate plan 引用 |
| `docs/planning/2026-04-25-current-repo-execution-plan.md` | 已 superseded，但 official state 仍将其作为 active document entity | 文件头写 `superseded: true`；`DOC_STATE.yaml.documents.DOC-PLAN-CURRENT-REPO-2026-04-25.state.confirmed.status: active` | high | 不得删除/移动；先执行 document entity state migration |
| `docs/tasks/workbench-mvp/2026-04-25-workbench-mvp-task-remap.md` | 已 superseded，但仍是 `ST13_01~ST13_25` 的 `meta.path/source_doc` | 文件头写 `superseded: true`；`DOC_STATE.yaml` 多个 ST13 entry 指向该路径 | high | 不得删除/移动；先执行 task source_doc migration |
| `README.md` | 根事实源表可能把 subordinate execution plan 读成 planning 并行入口 | current planning 列出 `PLAN_LATEST.md` 与 `docs/planning/2026-04-25-current-repo-execution-plan.md` | medium | 保留二者，但将 execution plan 标为 state-bound delegated doc |
| `PLAN_LATEST.md` | 当前规划事实表列出已 superseded execution plan 和 task remap | 第 2 节列 `execution plan` 与 `task remap` 为 current entry | medium | 改为“state-bound reference / legacy delegated source”，避免双主入口 |
| `AGENTS.md` | 计划索引同时列出 `PLAN_LATEST.md`、current execution plan、backlog roadmap、`MASTER_IMPLEMENTATION_PLAN.md` | 2.4 计划列表包含多份计划类文档 | medium | 保留索引；补主入口与子计划/受管文档层级说明 |
| `docs/governance/DOC_GOVERNOR_REPORT.md` | generated report 可能被误读为 state truth，且与 official state 存在时效差 | 报告解释边界写“不是 DOC_STATE 文件的真值来源”；当前内容仍列 ST13 gate 阻断摘要 | high | 不作为修复依据；后续重跑生成或删除 generated artifact |
| `docs/governance/ACTIVE_DOC_CANON.md` | 归档规则未区分“superseded 但 state-bound”与“可归档/可删除” | 第 3 节要求旧入口标记 superseded 并记录归档信息；第 5 节列两个 superseded 文件 | medium | 增补 state-bound movement guard |

## Root entry conflicts

- `README.md` 当前总体方向正确：只作为导航，不承载需求、设计、执行日志或任务流水。
- `README.md` 的 current planning 行需要细分 `PLAN_LATEST.md` 与 state-bound execution plan 的关系，否则后续清理窗口可能误以为二者都可作为当前 planning fact source。
- `AGENTS.md` 是高优先级执行入口，Daily Check 读取清单合理，但读取清单不等于主入口清单；建议后续明确“读取 state-bound 文档用于验证，不等于恢复其主入口地位”。
- 根文档标题中仍有 `P1` 遗留，如 `TECHNICAL_STANDARDS.md`、`EXECUTION_LOG.md` 的标题。该问题不必阻断本轮，但应进入 root terminology repair。

## Plan/index conflicts

- `PLAN_LATEST.md` 与 `TASK_INDEX.md` 已承担主入口职责，且都强引用 `ACTIVE_DOC_CANON.md`。
- `PLAN_LATEST.md` 第 2 节的 execution plan / task remap 仍写成 current entry，推荐改为“受 state 绑定的 delegated reference”，防止与 canon 单主入口冲突。
- `TASK_INDEX.md` 第 2 节仍把 task remap 写成 current task remap；该路径当前确实被 official state 引用，不能删除，但应补充“仅因状态引用保留，不再是任务主入口”。
- `docs/planning/workbench-mvp/MASTER_IMPLEMENTATION_PLAN.md` 的作用应是阶段实施子计划和 R0/R1/R2 交付治理，不应压过 `PLAN_LATEST.md`。
- `docs/planning/workbench-mvp/2026-04-25-workbench-mvp-backlog-roadmap.md` 是 backlog / roadmap 维护入口，不应成为 Daily Check 的替代主计划。
- `archive/governance/2026-05-02-doc-convergence-audit/01-historical-p1-coverage-matrix.md` 写到“当前计划入口仍是 `PLAN_LATEST.md` 与 `MASTER_IMPLEMENTATION_PLAN.md`”，作为 archive 审计证据可保留，但若后续被复制到 active docs 会造成双主计划语言。

## Old-stage terminology findings

| path | pattern | classification | recommended action |
| ---- | ------- | -------------- | ------------------ |
| `TECHNICAL_STANDARDS.md` | 标题 `AI 模拟面试 P1 技术标准` | invalid-current-plan-language | 后续 root terminology repair 中改为 current MVP / Workbench MVP 语言 |
| `EXECUTION_LOG.md` | 标题 `AI 模拟面试 P1 执行日志` 和历史 W13 entries | allowed-history-mapping | 过程日志可保留历史标签；标题可后续降噪 |
| `AGENTS.md` | 文档索引中多处 `P1` 标题 | invalid-current-plan-language | 保留链接但改显示名，避免 P1 作为当前阶段 |
| `TASK_INDEX.md` | `ST13_20`、`ST13_21`、`ST13_24`、`ST13_25` | allowed-task-id | `ST13_` 保留为任务 ID，不按旧阶段词清理 |
| `TASK_INDEX.md` | 规则说明 `P0/P1/P2`、`W13-*` 仅历史追溯 | allowed-history-mapping | 保留，作为清理标准 |
| `docs/planning/workbench-mvp/2026-05-01-r-stage-mapping.md` | `P0/P1/P2`、`W13-*`、`ST13_*` 映射表 | allowed-history-mapping | 保留，作为 terminology repair 输入 |
| `docs/planning/workbench-mvp/2026-04-25-workbench-mvp-backlog-roadmap.md` | backlog 表中大量 W13 source/owner/window 字段 | allowed-history-mapping | 不清空；逐步压缩到 source/trace 字段 |
| `docs/tasks/workbench-mvp/st13-task-packages/**` | `ST13_` 文件名和正文任务 ID | allowed-task-id | 保留任务 ID；仅修正文中过时阶段语义 |
| `docs/governance/previews/**` | W13 preview 文件名和字段 | generated-or-preview | 不作为 current plan 语言；后续按 preview artifact 处理 |
| `docs/governance/DOC_STATE.yaml` | `ST13_01~ST13_25` official state keys | allowed-task-id | official state key 不在本轮重命名 |

## Archive-reference findings

| path | reference | classification | recommended action |
| ---- | --------- | -------------- | ------------------ |
| `README.md` | “归档材料不作为当前需求、设计、规划或任务依据” | allowed-historical-evidence | 保留 |
| `AGENTS.md` | `archive/`: 历史材料，不作为当前事实源 | allowed-historical-evidence | 保留 |
| `PLAN_LATEST.md` | `archive/governance/archive-ledger.md` 与 backlog history snapshot | allowed-archive-ledger | 保留；避免把 archive snapshot 作为 current planning |
| `TASK_INDEX.md` | `archive/governance/archive-ledger.md` 与 W13 history snapshot | allowed-archive-ledger | 保留；补“不替代 task index”说明即可 |
| `docs/planning/workbench-mvp/2026-04-25-workbench-mvp-backlog-roadmap.md` | history snapshot 与 archive ledger | allowed-archive-ledger | 保留 |
| `docs/governance/ACTIVE_DOC_CANON.md` | `archive/ARCHIVE_INDEX.md` | allowed-archive-ledger | 保留；后续补 state-bound 例外 |
| `EXECUTION_LOG.md` | 多处旧 `archive/docs/superpowers/**` 迁移记录 | allowed-historical-evidence | 保留为过程记录 |
| `archive/governance/2026-05-02-doc-convergence-audit/01-historical-p1-coverage-matrix.md` | 历史 P1 设计稿与当前承接矩阵 | allowed-historical-evidence | 保留在 archive audit pack；不要复制为 active facts |
| `docs/governance/DOC_QUALITY_GATE_REPORT.md` | generated gate failure snapshot | generated-or-preview | 不作为 current fact source；后续重生或删除 |
| `docs/governance/DOC_STATE_W13_E13_8_CANDIDATE_FACTS_PREVIEW.yaml` | root-level preview YAML | generated-or-preview | 评估是否重复于 `docs/governance/previews/**`；后续处理 |

## Generated-report findings

- `docs/governance/DOC_AUTOMATION.md` 已明确定义：`BOOTSTRAP_REPORT.md`、`DOC_GOVERNOR_REPORT.md` 是解释性生成报告，不是 official state。
- `docs/governance/DOC_GOVERNOR_REPORT.md` 当前仍可被误读为 gate 真值。它的解释边界虽然写明不是真值来源，但报告中 gate 摘要可能与 `DOC_STATE.yaml` 不同步；例如 official state 已将 `ST13_20 / ST13_21.formal_window_status` 写为 `open`，而 generated report 仍可能展示 formal-window 关闭阻断。
- `docs/governance/DOC_QUALITY_GATE_REPORT.md` 是 `doc-quality-gate` 输出快照；本窗口禁止运行该命令，因此不能把当前失败列表当作最新事实。
- `docs/governance/BOOTSTRAP_REPORT.md` 标题仍为英文 `Bootstrap Report`，且作为 generated report 被质量门禁扫描；后续应优先修生成器或决定不跟踪该报告，而不是手工维护快照。
- `docs/governance/previews/**` 与 `docs/governance/packets/**` 属于 preview / packet artifact。它们可以是历史证据，但不能作为 Daily Check、canon、plan 或 task 的事实源。

## State-bound movement risks

- `docs/planning/2026-04-25-current-repo-execution-plan.md`：虽然已标记 superseded 并登记 `archive/ARCHIVE_INDEX.md`，但 `DOC_STATE.yaml.documents.DOC-PLAN-CURRENT-REPO-2026-04-25.meta.path` 仍指向该文件，且 state status 为 `active`。后续删除或移动会直接破坏 evaluate/document scan。
- `docs/tasks/workbench-mvp/2026-04-25-workbench-mvp-task-remap.md`：`DOC_STATE.yaml` 中 `ST13_01~ST13_25.meta.path` 和 `w13_preview.source_doc` 多处仍指向该文件。后续必须先设计批量 source_doc migration。
- `docs/tasks/workbench-mvp/st13-task-packages/**`：多个 required doc slot 已登记到 official state；后续清理不得按“ST13 是旧阶段词”误移动这些目录。
- `docs/governance/packets/**`：packet 可能被 implementation docs 引用，删除前需检查 `DOC_STATE.yaml`、transition history 与 task implementation docs。
- `docs/governance/previews/**`：preview 可能作为 transition evidence refs 或 backlog 证据存在；删除前需确认是否已有 archive ledger 或 transition history 可追溯。

## Active cleanup candidates

| path | current location | proposed final state | action type | prerequisite | risk |
| ---- | ---------------- | -------------------- | ----------- | ------------ | ---- |
| `README.md` | root | active root navigation | keep-active | 后续小措辞修补 | low |
| `AGENTS.md` | root | active execution rule entry | keep-active | 后续补 Daily Check 读取层级说明 | medium |
| `PLAN_LATEST.md` | root | planning 唯一主入口 | keep-active | 修补 delegated/state-bound reference wording | low |
| `TASK_INDEX.md` | root | task 唯一主入口 | keep-active | 修补 task-remap state-bound wording | medium |
| `docs/governance/ACTIVE_DOC_CANON.md` | docs/governance | active canon | keep-active | 增补 state-bound movement guard | medium |
| `docs/governance/DOC_STATE.yaml` | docs/governance | official state truth | keep-active | 不在 cleanup 窗口直接编辑，除非 state migration window | high |
| `docs/planning/2026-04-25-current-repo-execution-plan.md` | docs/planning | state-bound delegated historical doc 或迁移后 archive | state-migration-required | 先更新 `DOC_STATE.yaml.documents` 并验证 evaluate | high |
| `docs/tasks/workbench-mvp/2026-04-25-workbench-mvp-task-remap.md` | docs/tasks/workbench-mvp | state-bound source_doc 或迁移后 archive | state-migration-required | 先更新 ST13 source_doc / meta.path 并验证 evaluate | high |
| `docs/planning/workbench-mvp/MASTER_IMPLEMENTATION_PLAN.md` | docs/planning/workbench-mvp | R0/R1/R2 subordinate implementation plan | keep-active | 去除“唯一主计划入口”冲突措辞 | medium |
| `docs/planning/workbench-mvp/2026-05-01-r-stage-mapping.md` | docs/planning/workbench-mvp | active terminology mapping | keep-active | 无 | low |
| `docs/planning/workbench-mvp/2026-04-25-workbench-mvp-backlog-roadmap.md` | docs/planning/workbench-mvp | active backlog / roadmap | keep-active | 压缩旧 W13 字段展示，保留 history refs | medium |
| `docs/governance/DOC_STATE.bootstrap.yaml` | docs/governance | generated bootstrap artifact removed or archived | delete-generated | 确认无命令、测试、文档将其作为 required input | medium |
| `docs/governance/BOOTSTRAP_REPORT.md` | docs/governance | generated bootstrap report removed or regenerated on demand | delete-generated | 确认 bootstrap workflow 不要求 tracked report | medium |
| `docs/governance/DOC_GOVERNOR_REPORT.md` | docs/governance | generated report regenerated on demand or removed | delete-generated | 先确认 report 是否仍需作为审计快照；若保留需重生 | high |
| `docs/governance/DOC_QUALITY_GATE_REPORT.md` | docs/governance | generated quality-gate report regenerated on demand or removed | delete-generated | 后续允许运行 doc-quality-gate 后再处理 | medium |
| `docs/governance/DOC_STATE_W13_E13_8_CANDIDATE_FACTS_PREVIEW.yaml` | docs/governance root | archive or delete duplicate preview | needs-human-decision | 比对 `docs/governance/previews/DOC_STATE_W13_E13_8_CANDIDATE_FACTS_PREVIEW.yaml` 和 transition refs | medium |
| `docs/governance/previews/**` | docs/governance/previews | historical preview evidence or archive | needs-human-decision | 检查 transition history / backlog refs | medium |
| `docs/governance/packets/**` | docs/governance/packets | packet evidence retained or archived | needs-human-decision | 检查 implementation docs 和 state refs | high |
| `archive/governance/2026-05-02-doc-convergence-audit/**` | archive/governance | audit evidence pack | keep-active | 后续 merge window 汇总 | low |

## Recommended repair plan

| priority | target path | repair action | depends on | risk |
| -------- | ----------- | ------------- | ---------- | ---- |
| P0 | `docs/governance/ACTIVE_DOC_CANON.md` | 增补 state-bound movement guard：superseded 不等于可删除/可移动 | 串行修复窗口授权 | medium |
| P0 | `PLAN_LATEST.md` | 将 execution plan / task remap 改为 state-bound delegated references，不写成并行 current entries | canon guard 确认 | medium |
| P0 | `TASK_INDEX.md` | 明确 task-remap 仅因 official state source_doc 保留，不再是任务主入口 | canon guard 确认 | medium |
| P1 | `docs/planning/workbench-mvp/MASTER_IMPLEMENTATION_PLAN.md` | 降级“唯一主计划入口”为“R0/R1/R2 阶段实施子计划” | 用户确认其继续 active | medium |
| P1 | `README.md` | current facts 表中区分 root main entry 与 subordinate/state-bound docs | PLAN/TASK 修复后 | low |
| P1 | `AGENTS.md` | Daily Check 读取清单补充“读取不等于主入口或可清理判定” | PLAN/TASK 修复后 | medium |
| P1 | `docs/governance/DOC_GOVERNOR_REPORT.md`、`DOC_QUALITY_GATE_REPORT.md`、`BOOTSTRAP_REPORT.md` | 确认 generated report 的保留策略：删除、归档或允许后续重生 | 需要单独 generated cleanup window | high |
| P2 | `docs/planning/2026-04-25-current-repo-execution-plan.md` | 仅在 state migration 后考虑 archive-with-git-mv | state migration green | high |
| P2 | `docs/tasks/workbench-mvp/2026-04-25-workbench-mvp-task-remap.md` | 仅在 ST13 source_doc migration 后考虑 archive-with-git-mv | state migration green | high |
| P2 | `TECHNICAL_STANDARDS.md`、root index display names | 清理 `P1` 标题和显示名，统一 current MVP / R0-R2 语言 | canon/root repair 后 | low |

## Proposed follow-up windows

| window | goal | allowed write scope | stop condition |
| --- | --- | --- | --- |
| `R0-W03-CANON-ROOT-REPAIR` | 修补 canon、root entry、PLAN/TASK 主入口措辞，不移动 state-bound 文件 | `README.md`、`AGENTS.md`、`PLAN_LATEST.md`、`TASK_INDEX.md`、`docs/governance/ACTIVE_DOC_CANON.md` | 出现 state file 修改需求即停止 |
| `R0-W04-GENERATED-ARTIFACT-DECISION` | 决定 generated reports / previews / packets 的保留、删除或归档策略 | 先只读；确认后再给 cleanup card | 发现 transition refs 未覆盖即停止 |
| `R0-W05-STATE-BOUND-MIGRATION-PLAN` | 为 superseded execution plan 与 task-remap 设计 state/source_doc migration 方案 | 只读或 preview artifact，按窗口授权 | 需要正式 `DOC_STATE.yaml` 写入时停止等确认 |
| `R0-W06-ROOT-TERMINOLOGY-REPAIR` | 清理 root docs 中 `P1` 作为当前阶段语言的残留 | 根文档指定白名单 | 任何任务 ID 或历史日志被误改即停止 |

## Validation notes

- 已执行 Phase A preflight：HEAD `04b94b1`，branch `main`，初始 tracked 修改仅为两份已接受 frontmatter 格式化文件；审计包目录存在。
- Basic Memory MCP 检查没有发现真实 `basic-memory mcp --project AiForInterviewer` 或 `basic_memory mcp --project AiForInterviewer` 进程；输出只命中本次 `ps|rg` 命令自身。
- 本窗口只新增本文件，未修改 active docs、root docs、`docs/**`、`apps/**`、`tools/**`、`tests/**`、归档台账或 Basic Memory。
- 本窗口未运行 doc-quality-gate、pytest、npm test/build。
- 本文件是 archive audit evidence，不是 current requirement、design、planning、task 或 official state truth。

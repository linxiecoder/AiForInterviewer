---
title: DOC_GOVERNOR_RUNBOOK
type: note
permalink: ai-for-interviewer/docs/governance/doc-governor-runbook
---

# 文档治理命令与轮次运行手册

## 1. 定位与范围

本文档是当前仓库中 `doc-governor` 的整体 CLI 运行手册，用于说明：

- 主要命令族的用途与进入方式
- 当前已落地的两条核心流程：
  - 文档轮次（`document round`）完善流程
  - `open-window` / 审批队列规划流程
- 各命令之间的衔接关系与当前边界

边界说明：

- 本文档是操作手册，不是 schema / gate / confirmed state 的最终实现真值。
- 自动化边界与命令契约以 `docs/governance/DOC_AUTOMATION.md` 为准。
- 实际命令参数、输出字段、默认值与行为以 `tools/doc_governor/cli.py` 及相关实现为准。

## 2. 入口约定

统一 CLI 入口：

```powershell
python -m tools.doc_governor.cli --help
```

统一 Codex CLI 入口：

```powershell
C:\Users\Administrator\AppData\Roaming\npm\codex.cmd exec
```

## 3. 当前命令族总览

### 3.1 主链命令

当前最小闭环直接依赖的主链命令包括：

- 状态治理：`bootstrap-state`、`validate-state`、`init-official-state`、`evaluate-state`、`render-report`、`confirm-transition`
- 历史与上下文回收：`show-history`、`summarize-history`
- readiness / 开窗：`preflight-open-window`、`plan-open-window`、`open-window`
- round / 多窗口协作：`plan-round`、`generate-round-template`、`apply-round`、`update-round-status`、`generate-codex-packet`

### 3.2 生成类命令

以下命令都属于“生成产物或生成规划”的命令，但不应被误写成“已经自动完成后续审批或写回”：

- `generate-round-template`
- `generate-codex-packet`
- `generate-implementation-packet`

当前边界：

- `generate-round-template` 生成 round 模板并登记 round 跟踪信息，不替代 `confirm-transition`。
- `generate-codex-packet` 生成文档轮次交接包，当前主要服务 document round。
- `generate-implementation-packet` 只面向已满足 `implementation_ready` 的 task；若 task 仍 blocked，会直接拒绝生成 packet。

### 3.3 扩展分析与建议命令

以下命令已在 CLI 中存在，但当前定位是扩展分析、建议输出或任务治理辅助，不应被描述成默认主链：

- `plan-task-adaptation`
- `suggest-requirement-links`
- `plan-task-remediation`
- `plan-task-readiness`
- `summarize-task-apply-result`
- `plan-task-window-candidates`

这些命令大多支持 `json/markdown` 输出，更适合作为讨论输入、窗口规划输入或实施前审阅材料。

### 3.4 `preview/apply/sync/seed` 命令族

以下命令主要服务于 requirement / task 的 seed、preview、state writeback 与 state sync：

- requirement 相关：`apply-requirement-container-seed`、`apply-requirement-seed`、`apply-requirement-entity-sync`
- task 骨架 / 文档 / 实施状态相关：`apply-task-skeleton-seed`、`apply-task-doc-state-sync`、`apply-task-implementation-state-sync`
- readiness 修复相关：`preview-task-readiness-fix`、`preview-task-patches`、`apply-task-readiness-fix`
- task state writeback 相关：`preview-task-state-writeback`、`preview-task-state-dependency-map`、`apply-task-state-writeback`
- readiness state sync 相关：`preview-task-readiness-state-sync`、`apply-task-readiness-state-sync`
- formal window sync 相关：`preview-task-formal-window-sync`、`apply-task-formal-window-sync`

### 3.5 当前需要谨慎使用的命令

以下命令虽然已经暴露在 CLI 中，但默认都不应被写成“主链自动执行”的既成事实：

- 所有带 `--apply` 的 requirement/task seed、writeback、sync 命令
- `generate-implementation-packet`
- `apply-round`

谨慎使用原则：

- 先 `validate-state` / `evaluate-state`，再 preview / plan，最后才考虑 apply。
- 优先保留 dry-run、preview、plan 输出，避免直接把扩展命令当成正式审批替代品。
- `apply-round` 是“批量消费审批计划”的执行器，不是完整 round 生命周期。
- `generate-implementation-packet` 只在 task 已满足 `implementation_ready` 时成立，不能把命令存在误读成“任意 task 都已可生成实施包”。

### 3.6 按工作目标选择命令

| 工作目标 | 推荐命令 | 当前说明 |
| --- | --- | --- |
| 讨论 | `evaluate-state`、`render-report`、`plan-open-window`、`plan-round`、`plan-task-adaptation`、`plan-task-readiness` | 先生成讨论输入，不直接写回状态 |
| 状态校验 | `validate-state` | 校验 bootstrap / official state 的 schema 与规则约束 |
| 状态评估 | `evaluate-state` | 生成只读 evaluate payload，供报告、开窗、task 规划与 packet 消费 |
| readiness | `preflight-open-window`、`plan-open-window`、`open-window`、`plan-task-readiness`、`preview-task-readiness-fix`、`preview-task-readiness-state-sync` | 区分 ready 检查、排优先级、正式开窗与修复预演 |
| packet | `generate-codex-packet`、`generate-implementation-packet` | 前者服务 document round，后者只服务 implementation-ready task |
| Codex 多窗口实施 | `plan-round`、`generate-round-template`、`generate-codex-packet`、`plan-task-window-candidates` | 用于明确窗口边界、交接包与候选桥接结果 |
| 验证 | `validate-state`、`evaluate-state`、`show-history`、`summarize-history`、`preview-task-state-dependency-map`、`summarize-task-apply-result` | 用于回归核对、历史审计与写回结果复盘 |
| 上下文回收 | `render-report`、`show-history`、`summarize-history`、支持 Markdown 输出的 task 规划命令 | 用于把讨论、历史和 task 规划重新压回可复用文本产物 |

### 3.7 Official / Preview / Dry-run 操作分层

- official state 固定为 `docs/governance/DOC_STATE.yaml`，是唯一正式状态真值。
- preview state 可以用 `validate-state --input <preview.yaml>` 与 `evaluate-state --input <preview.yaml>` 做结构、规则和 document path 验证；preview 文件不是 governance truth。
- preview state 可放在 `docs/governance/previews/`、`docs/governance/` 或 repo 内其他受支持的 preview 路径；其中 `documents.*.meta.path` 按仓库根解析，不按 preview 文件所在目录解析。
- dry-run 只做影响分析，不写正式状态；apply / official write 必须在用户确认后的单独窗口执行。
- `candidate_status` 只支持 `none` / `observe` / `candidate`，`readiness` 只支持 `blocked` / `not_ready` / `downstream_ready` / `implementation_ready`；`near_ready` 不是状态层正式值。
- `formal_window_open=false` 时不得把 `candidate_status=candidate` 作为正式状态；`readiness=downstream_ready` 要求 confirmed `maturity` 已设置。
- facts-only candidate preview 只表示事实记录或候选观察，不等于 formal window open，也不等于 implementation packet 可生成。
- 文档层 formal-window candidate 推荐统一写入 `facts.formal_window_candidate_recommended=true`、`facts.formal_window_candidate_source`、`facts.formal_window_candidate_review_status=pending_confirmation`、`facts.formal_window_candidate_state=document_layer_recommended` 与 `facts.formal_window_candidate_notes`。
- near-ready 统一写入 `facts.near_ready_for_formal_window_candidate=true`、`facts.near_ready_reason`、`facts.near_ready_blockers` 与 `facts.near_ready_state=document_layer_only`；不要写成 `readiness=near_ready`。
- `design_doc.exists=true` / `implementation_doc.exists=true` 只是 required doc slot 存在，不是 readiness；`implementation_doc` 也不是 implementation packet。
- formal window open 只是 packet / implementation-ready 的必要条件，不是充分条件；`implementation_doc_state`、acceptance criteria、required tests、implementation scope、allowed paths、forbidden paths 与 blocker diagnostics 仍必须全部闭合。
- `render-report` 的子任务 gate 摘要、`preview-task-state-dependency-map` 与 `preview-task-readiness-state-sync` 会展示 `gate_result`、`can_open_formal_window`、`can_generate_implementation_packet`、`can_mark_implementation_ready`；这些字段是只读判断摘要，不是正式开窗或 packet 授权。

## 4. 常用只读命令

### 4.1 评估官方状态并渲染报告

```powershell
python -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml > tmp_eval.json
python -m tools.doc_governor.cli render-report --evaluate-json tmp_eval.json
```

若直接从 state 进入渲染：

```powershell
python -m tools.doc_governor.cli render-report --state docs/governance/DOC_STATE.yaml
```

报告中的“子任务 gate 摘要”用于快速查看 top blockers 与 next actions。若摘要显示 `can_generate_implementation_packet=false` 或 `can_mark_implementation_ready=false`，不得生成 implementation packet，也不得把 facts-only candidate 当成 formal window open。

### 4.2 查询 transition history

查看原始历史记录：

```powershell
python -m tools.doc_governor.cli show-history --history docs/governance/transition_history.jsonl --limit 20
```

按对象筛选：

```powershell
python -m tools.doc_governor.cli show-history --entity-type module --entity-id M01
```

查看聚合摘要：

```powershell
python -m tools.doc_governor.cli summarize-history --history docs/governance/transition_history.jsonl --top-rejected 10
```

当前 history 命令的用途分工：

- `show-history`：查看按时间倒序返回的原始 transition 记录，支持 `entity_type`、`entity_id`、`actor`、`result`、`since/until`、`limit` 过滤。
- `summarize-history`：查看聚合统计、`latest_attempt_by_entity`、`top_rejected_entities` 等摘要。
- 两者都只读，不修改 `DOC_STATE.yaml`、`DOC_STATE.bootstrap.yaml` 或 history 文件本身。

### 4.3 开窗预检与规划

预检：

```powershell
python -m tools.doc_governor.cli preflight-open-window --state docs/governance/DOC_STATE.yaml
```

按子任务预检：

```powershell
python -m tools.doc_governor.cli preflight-open-window --input docs/governance/DOC_STATE.yaml --subtask ST13_24
```

规划：

```powershell
python -m tools.doc_governor.cli plan-open-window --state docs/governance/DOC_STATE.yaml
```

当前输出边界：

- `preflight-open-window` 返回：
  - `eligible_entities`
  - `blocked_entities`
  - `review_required_before_open`
  - `blocker_reasons`
  - `missing_requirements`
  - `history_signals`
  - `summary`
- 当使用 `--subtask <ID>` 时，还会返回目标子任务 gate 摘要：
  - `gate_result`
  - `can_open_formal_window`
  - `can_generate_implementation_packet`
  - `can_mark_implementation_ready`
  - `required_doc_slots`
  - `design_doc`
  - `implementation_doc`
  - `acceptance_criteria`
  - `required_tests`
  - `implementation_scope`
  - `formal_window_open`
  - `candidate`
  - `near_ready`
  - `blockers`
  - `next_required_actions`
- `plan-open-window` 在 preflight 基础上进一步整理为：
  - `eligible_to_apply`
  - `near_open_but_blocked`
  - `hard_blocked`
  - `would_change_by_entity`
  - `summary`
  - `missing_requirements`
  - `history_signals`

不要把这两个命令混成一件事：

- `preflight-open-window` 是“是否能开窗”的只读预检。
- `plan-open-window` 是“如果要开窗 / 排优先级 / 讨论下一轮”的分类规划。
- `preflight-open-window` 不打开 formal window，不写 `DOC_STATE.yaml`，不生成 packet。

## 5. open-window 执行

### 5.1 dry-run

```powershell
python -m tools.doc_governor.cli open-window --state docs/governance/DOC_STATE.yaml --entity-type module --entity-id M01 --mode dry-run
```

### 5.2 apply

```powershell
python -m tools.doc_governor.cli open-window --state docs/governance/DOC_STATE.yaml --entity-type module --entity-id M01 --mode apply --actor alice --reason "Decision: open module window"
```

当前执行约束：

- `open-window` 只接受 `module` 或 `subtask`。
- `--mode` 只允许 `dry-run` 或 `apply`。
- `apply` 模式必须提供 `--actor` 与 `--reason`。
- 执行前会先跑 `preflight-open-window`；若目标对象不在 `eligible_entities` 中，或仍处于 `blocked_entities` / `review_required_before_open`，则 apply 会直接失败。

## 6. 文档轮次流程

这是当前最完整的轮次驱动文档流程。

### 6.1 生成文档轮次计划

单文档：

```powershell
python -m tools.doc_governor.cli plan-round --state docs/governance/DOC_STATE.yaml --entity-type document --entity-id DOC-SPEC-P1 --round-id R-SPEC-01
```

多文档：

```powershell
python -m tools.doc_governor.cli plan-round --state docs/governance/DOC_STATE.yaml --entity-type document --round-id R-SPECPLAN-01
```

当前文档轮次计划重点字段包括：

- `workflow`
- `round_id`
- `topic`
- `scope`
- `target_documents`
- `required_evidence_refs`
- `exit_criteria`
- `writeback_items`
- `summary`

### 6.2 生成 round 模板并登记 `open`

```powershell
python -m tools.doc_governor.cli generate-round-template --round-id R-SPECPLAN-01 --state docs/governance/DOC_STATE.yaml --entity-type document
```

也可以先把计划保存成文件，再用：

```powershell
python -m tools.doc_governor.cli generate-round-template --round-id R-SPECPLAN-01 --state docs/governance/DOC_STATE.yaml --from-plan round-plan.json
```

### 6.3 生成 Codex 交接包

```powershell
python -m tools.doc_governor.cli generate-codex-packet --round-id R-SPECPLAN-01 --state docs/governance/DOC_STATE.yaml
```

### 6.4 执行本地 Codex CLI

直接执行交接包产物中的命令：

```powershell
Get-Content -LiteralPath docs\governance\packets\R-SPECPLAN-01.exec.txt -Encoding UTF8
```

### 6.5 进入 `review`

```powershell
python -m tools.doc_governor.cli update-round-status --round-id R-SPECPLAN-01 --state docs/governance/DOC_STATE.yaml --status review --actor alice
```

### 6.6 执行 document 对象的 `confirm-transition`

```powershell
python -m tools.doc_governor.cli confirm-transition --input docs/governance/DOC_STATE.yaml --entity-type document --entity-id DOC-SPEC-P1 --proposed-changes "{\"status\":\"active\",\"review_status\":\"approved\",\"blocker_refs\":[],\"active_round_id\":\"R-SPECPLAN-01\"}" --mode approve --actor alice --reason "Decision: spec refined" --round-id R-SPECPLAN-01
```

### 6.7 关闭 round

```powershell
python -m tools.doc_governor.cli update-round-status --round-id R-SPECPLAN-01 --state docs/governance/DOC_STATE.yaml --status closed --actor alice --close-reason completed --decision-ref decision:DR-SPECPLAN-01 --result-summary "spec/plan refined"
```

## 7. 审批队列规划与批量 apply

这条流程服务于 module / subtask 的开窗与审批队列整理，当前不是文档轮次流程的替代品。

### 7.1 生成审批队列计划

```powershell
python -m tools.doc_governor.cli plan-round --state docs/governance/DOC_STATE.yaml --history docs/governance/transition_history.jsonl --round-id round-batch-01
```

当前非 document `plan-round` 输出重点字段：

- `round_id`
- `scope`
- `queues.must_review`
- `queues.can_approve_now`
- `queues.blocked_hard`
- `summary`
- `parse_errors`

每个队列项当前至少包含：

- `entity_type`
- `entity_id`
- `recommended_action`
- `proposed_changes`
- `evidence_refs`

并会保留规划阶段已有的 blocker / history / proximity 等上下文信息。

### 7.2 批量 apply 计划

```powershell
python -m tools.doc_governor.cli apply-round --round-id round-batch-01 --from-plan round-plan.json --state docs/governance/DOC_STATE.yaml --actor alice --reason "Decision: batch apply"
```

当前 `apply-round` 的真实边界：

- 必须且只能提供一个计划输入：`--plan-json` 或 `--from-plan`
- `--round-id` 必须与计划中的 `round_id` 一致
- `recommended_action=approve|reject` 会转成对 `confirm-transition` 的调用
- `recommended_action=defer` 不会写状态，只计入 `skipped`
- 若 `--reason` 未包含 `Decision:`，命令会自动补上 `Decision: batch apply`
- 输出会返回：
  - `summary.total`
  - `summary.applied`
  - `summary.skipped`
  - `summary.failed`
  - `results`

说明：

- `apply-round` 当前是“批量消费审批计划”的执行器，不会自动替你生成 round 模板或 Codex 交接包。
- 需要正式 round 记录时，仍应结合 `generate-round-template` / `update-round-status` 使用；不要把 `apply-round` 误解为完整轮次生命周期。

## 8. `generate-round-template` 的当前边界

当前命令存在两种主要用法：

### 8.1 文档轮次模板

- 通过 `--entity-type document` 或 `--from-plan <document-plan>` 生成
- 模板会预填 `target_documents`、`required_evidence_refs`、`writeback_items`
- 同时会向 `governance_rounds` 登记 round，并为目标 document 写入 `active_round_id`

### 8.2 开窗评审模板

- 未显式提供文档计划时，命令会回退到 `plan-open-window`
- 模板当前只会预填：
  - `near_open_but_blocked`
  - `hard_blocked`
- 这更适合讨论“下一轮怎么处理开窗阻塞”，不是批量审批队列的完整模板

不要误判当前能力：

- `generate-round-template` 目前不会把 `plan-round` 的 `queues.can_approve_now / must_review / blocked_hard` 自动展开成一套更丰富的模板区块。
- `generate-codex-packet` 当前仍以文档轮次为主要使用场景。

## 9. 子任务实施与状态回写扩展命令

### 9.1 implementation packet 与 task 规划

- `generate-implementation-packet`：可从 `--input` 或 `--evaluate-json` 读取数据，但会基于 official state 重新执行 validate/evaluate gate，并检查目标 task 的 `derived.implementation_ready`、`formal_window_open=true`、`implementation_doc_state=active_working_doc`、非模板双文档、acceptance criteria、required tests、implementation scope、allowed/forbidden paths 与 blocking diagnostics；未满足时直接拒绝生成。
- `plan-task-adaptation`：基于 official state / evaluate payload 生成 task adaptation plan，支持 `json/markdown` 输出。
- `plan-task-remediation`：生成 task 修复规划，用于讨论“先补什么、怎么补”。
- `plan-task-readiness`：生成 task readiness 规划，适合在 implementation window 前做收敛。
- `suggest-requirement-links`：生成 requirement link 建议；它是建议输出，不会直接改状态。
- `plan-task-window-candidates`：生成 task window 候选桥接结果，用于多窗口实施前的边界收敛。

### 9.2 requirement / task seed、preview、sync

这一组命令当前已经存在，但应理解为“辅助 writeback / sync 工具”，而不是默认主链：

- requirement：`apply-requirement-container-seed`、`apply-requirement-seed`、`apply-requirement-entity-sync`
- task seed / state：`apply-task-skeleton-seed`、`apply-task-doc-state-sync`、`apply-task-implementation-state-sync`
- readiness 修复：`preview-task-readiness-fix`、`preview-task-patches`、`apply-task-readiness-fix`
- task state writeback：`preview-task-state-writeback`、`preview-task-state-dependency-map`、`apply-task-state-writeback`
- readiness state sync：`preview-task-readiness-state-sync`、`apply-task-readiness-state-sync`
- formal window sync：`preview-task-formal-window-sync`、`apply-task-formal-window-sync`
- 回写结果汇总：`summarize-task-apply-result`

使用这些命令时，建议固定遵守：

1. 先保留 `preview` / `plan` 输出，再决定是否 `--apply`。
2. 对 state writeback / state sync / formal-window sync 类命令，优先显式保留 `actor`、`reason` 和 evaluate 证据来源。
3. 不要把这些命令生成的 patch / plan / sync 结果直接视为 confirmed state；正式真值仍回到 `DOC_STATE.yaml` 与 `confirm-transition` / round 生命周期。
4. `preview-task-state-dependency-map` 与 `preview-task-readiness-state-sync` 的 `gate_result/can_*` 字段只用于只读对齐 preflight 语义；其他 wrapper 若暂未显示同字段，应记录为 P1 工具债，不得因此扩大写状态行为。

## 10. 关键文件

- 官方状态：`docs/governance/DOC_STATE.yaml`
- bootstrap 输出：`docs/governance/DOC_STATE.bootstrap.yaml`
- 报告：`docs/governance/DOC_GOVERNOR_REPORT.md`
- 工具债：`docs/governance/DOC_GOVERNOR_TOOL_DEBT.md`
- rounds：`docs/governance/rounds/*.md`
- packets：`docs/governance/packets/*`
- 历史：`docs/governance/transition_history.jsonl`

## 11. 常见故障

### 11.1 `codex.ps1` 被执行策略拦截

不要切到 `codex.ps1`，统一使用 `codex.cmd`。

### 11.2 `confirm-transition` 提示缺少 `Decision:`

如果传入了 `--round-id`，则 `--reason` 必须包含 `Decision:` 锚点。

### 11.3 `open-window` 无法 apply

优先检查：

- `preflight-open-window` 是否 `ok=true`
- 目标对象是否在 `eligible_entities` 中
- 是否仍位于 `review_required_before_open`
- `apply` 模式下是否提供了 `--actor` 与 `--reason`

### 11.4 `apply-round` 报计划输入错误

检查：

- 是否同时传了 `--plan-json` 与 `--from-plan`
- 是否两个都没传
- `--round-id` 是否与计划中的 `round_id` 一致

### 11.5 设计稿或计划文档没有被 evaluate 到

检查：

- `DOC_STATE.yaml` 中是否已登记 `documents`
- `meta.path` 是否为仓库相对路径
- heading 是否与 `required_sections.heading` 精确一致
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

### 3.1 状态与报告

- `bootstrap-state`
- `validate-state`
- `evaluate-state`
- `render-report`
- `init-official-state`
- `confirm-transition`

### 3.2 历史查询

- `show-history`
- `summarize-history`

### 3.3 开窗预检与执行

- `preflight-open-window`
- `plan-open-window`
- `open-window`

### 3.4 轮次与批量审批

- `plan-round`
- `generate-round-template`
- `generate-codex-packet`
- `apply-round`
- `update-round-status`

说明：

- `generate-codex-packet` 当前主要服务于文档轮次流程。
- `apply-round` 当前用于消费 `plan-round` 产出的审批队列计划，不会替代 `confirm-transition` 的字段校验与写回规则。

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

## 9. 关键文件

- 官方状态：`docs/governance/DOC_STATE.yaml`
- bootstrap 输出：`docs/governance/DOC_STATE.bootstrap.yaml`
- 报告：`docs/governance/DOC_GOVERNOR_REPORT.md`
- rounds：`docs/governance/rounds/*.md`
- packets：`docs/governance/packets/*`
- 历史：`docs/governance/transition_history.jsonl`

## 10. 常见故障

### 10.1 `codex.ps1` 被执行策略拦截

不要切到 `codex.ps1`，统一使用 `codex.cmd`。

### 10.2 `confirm-transition` 提示缺少 `Decision:`

如果传入了 `--round-id`，则 `--reason` 必须包含 `Decision:` 锚点。

### 10.3 `open-window` 无法 apply

优先检查：

- `preflight-open-window` 是否 `ok=true`
- 目标对象是否在 `eligible_entities` 中
- 是否仍位于 `review_required_before_open`
- `apply` 模式下是否提供了 `--actor` 与 `--reason`

### 10.4 `apply-round` 报计划输入错误

检查：

- 是否同时传了 `--plan-json` 与 `--from-plan`
- 是否两个都没传
- `--round-id` 是否与计划中的 `round_id` 一致

### 10.5 设计稿或计划文档没有被 evaluate 到

检查：

- `DOC_STATE.yaml` 中是否已登记 `documents`
- `meta.path` 是否为仓库相对路径
- heading 是否与 `required_sections.heading` 精确一致

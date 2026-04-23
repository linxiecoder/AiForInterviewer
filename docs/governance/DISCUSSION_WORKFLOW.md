# 讨论轮次工作流

本文档定义当前轮次驱动协作与规划输出负载的最小契约，并约束它们与 `doc-governor`、本地 Codex CLI 的联动方式。

边界说明：

- 本文档覆盖的是“如何组织讨论、规划、round 模板与批量审批输入”。
- 它不是 schema / gate / confirmed state 的最终实现真值。
- 当前命令参数、输出字段与默认行为仍以 `tools/doc_governor/cli.py` 及相关实现为准。

## 1. 当前覆盖范围

当前工作流主要覆盖三类输出：

1. 文档轮次（`document round`）计划与收口
2. open-window 预检与开窗讨论输入
3. module / subtask 的审批队列计划与批量 apply 输入

不要把这三类内容混为一种自动化流程：

- 文档轮次当前有最完整的 `governance_rounds` 生命周期。
- open-window 讨论输入当前可以生成 round 模板，但更偏讨论记录，不等于自动审批。
- 审批队列计划当前主要是 `plan-round` / `apply-round` 的 JSON 契约，不自动等价于完整轮次模板生命周期。

## 2. 文档轮次生命周期

文档轮次当前固定按以下阶段推进：

1. `plan-round --entity-type document`
2. `generate-round-template`
3. `generate-codex-packet`
4. 人工执行 `codex.cmd exec`
5. `update-round-status --status review`
6. `confirm-transition`
7. `update-round-status --status closed`

固定 round 状态：

- `open`
- `in_progress`
- `review`
- `closed`

当前文档轮次计划的最小字段包括：

- `workflow`
- `round_id`
- `topic`
- `scope`
- `target_documents`
- `required_evidence_refs`
- `exit_criteria`
- `writeback_items`
- `summary`

其中 `target_documents[*]` 当前至少应包含：

- `document_id`
- `target_sections`

## 3. `governance_rounds[*]` 的当前登记字段

已登记 round 当前至少应包含：

- `round_id`
- `workflow`
- `topic`
- `scope`
- `status`
- `opened_at`
- `opened_by`
- `decision_refs`
- `target_documents`
- `required_evidence_refs`
- `exit_criteria`
- `writeback_items`

当前实现还会维护以下补充字段：

- `started_at`
- `review_at`
- `closed_at`
- `closed_by`
- `close_reason`
- `packet_paths`
- `result_summary`

说明：

- 文档轮次在登记 `open` 时，会为目标 document 写入 `active_round_id`。
- round 关闭时，会清空对应 document 的 `active_round_id`，并更新 `last_round_id`。

## 4. `preflight-open-window` 的当前输出边界

`preflight-open-window` 是只读预检命令，用于回答“哪些对象当前可开窗、哪些被挡住、挡在什么地方”。

当前输出重点包括：

- `ok`
- `state_path`
- `history_path`
- `evaluation_source`
- `scope`
- `eligible_entities`
- `blocked_entities`
- `blocker_reasons`
- `missing_requirements`
- `review_required_before_open`
- `summary`
- `history_recent`
- `history_signals`
- `parse_errors`

当前分类逻辑：

- `eligible_entities`：当前可进入开窗 apply 的对象
- `blocked_entities`：当前被 hard blocker 或 review-required 挡住的对象
- `review_required_before_open`：属于“接近可开窗，但还需要人工确认”的对象

`blocked_entities[*]` 当前至少会带出：

- `entity_type`
- `entity_id`
- `proximity`
- `hard_blockers`
- `blockers`
- `sources`
- `history_recent`
- `history_signals`
- `missing_requirements`

其中 `proximity` 当前会出现：

- `openable`
- `near-open`
- `blocked`

## 5. `plan-open-window` 的当前输出边界

`plan-open-window` 在 `preflight-open-window` 基础上，把结果整理成更适合讨论和排队的三类分类结果。

当前输出重点包括：

- `eligible_to_apply`
- `near_open_but_blocked`
- `hard_blocked`
- `blocker_reasons`
- `would_change_by_entity`
- `summary`
- `missing_requirements`
- `history_signals`
- `parse_errors`

当前三类分类结果的含义：

- `eligible_to_apply`：当前可直接进入 `open-window --mode apply`
- `near_open_but_blocked`：离开窗很近，但仍需要 review / confirm 的对象
- `hard_blocked`：当前明确不能开窗的对象

当前 `summary` 至少包括：

- `entities_scanned`
- `eligible_to_apply_count`
- `near_open_but_blocked_count`
- `hard_blocked_count`
- `preflight_eligible_count`
- `preflight_blocked_count`
- `evaluation_source`

当前 `would_change_by_entity[*]` 只表达如果 apply 时准备写入的窗口字段，不表示已经写回状态：

- `entity_type`
- `entity_id`
- `window_status`
- `window_opened_at`
- `window_opened_by`
- `window_reason`

## 6. `plan-round` 的当前双轨行为

`plan-round` 当前不是单一输出，而是两种不同契约：

### 6.1 `--entity-type document`

这条路径会生成文档轮次计划，服务于文档完善与 Codex 交接包工作流。

输出重点：

- `workflow=document_refinement`
- `round_id`
- `topic`
- `scope`
- `target_documents`
- `required_evidence_refs`
- `exit_criteria`
- `writeback_items`
- `summary`
- `diagnostics`

### 6.2 非 document 路径

这条路径会先跑：

1. `preflight-open-window`
2. `plan-open-window`

然后再生成审批队列计划，而不是文档轮次计划。

当前输出重点：

- `round_id`
- `state_path`
- `history_path`
- `evaluation_source`
- `scope`
- `queues.must_review`
- `queues.can_approve_now`
- `queues.blocked_hard`
- `summary`
- `parse_errors`

当前队列含义：

- `must_review`：建议 `recommended_action=defer`
- `can_approve_now`：建议 `recommended_action=approve`
- `blocked_hard`：建议 `recommended_action=reject`

队列项当前至少包含：

- `entity_type`
- `entity_id`
- `recommended_action`
- `proposed_changes`
- `evidence_refs`

并会保留规划阶段的 blocker / history / proximity 等上下文信息。

## 7. `generate-round-template` 的当前边界

当前模板生成有两种主要模式：

### 7.1 文档轮次模板

适用场景：

- 通过 `--entity-type document` 直接生成
- 或通过 `--from-plan <document-plan.json>` 生成

当前会自动预填：

- `target_documents`
- `required_evidence_refs`
- `writeback_items`

### 7.2 开窗评审模板

当没有提供显式文档轮次计划时，当前实现会回退到 `plan-open-window`，并把讨论模板预填为：

- `near_open_but_blocked`
- `hard_blocked`

当前这类模板更适合记录“哪些对象为何还不能开窗”，而不是表达批量审批队列。

### 7.3 当前未完全自动化的边界

当前代码不会自动把 `plan-round` 非 document 路径下的：

- `queues.can_approve_now`
- `queues.must_review`
- `queues.blocked_hard`

直接展开成更丰富的模板章节。因此，审批队列计划目前主要是 `plan-round` / `apply-round` 的 JSON 契约，而不是完整 Markdown 讨论模板体系。

## 8. `apply-round` 的当前作用

`apply-round` 当前用于消费审批队列计划，而不是生成计划。

真实边界如下：

- 必须且只能提供一个计划输入：`--plan-json` 或 `--from-plan`
- `--round-id` 必须与计划中的 `round_id` 一致
- `approve` / `reject` 动作会转为调用 `confirm-transition`
- `defer` 动作只会记为 `skipped`，不会写回状态
- 若 `--reason` 不含 `Decision:`，命令会自动补成批量 apply 理由

当前输出重点：

- `ok`
- `round_id`
- `state_path`
- `summary.total`
- `summary.applied`
- `summary.skipped`
- `summary.failed`
- `results`

因此，`apply-round` 当前应被视为“批量执行审批计划”的命令，而不是“完整轮次生命周期自动收口器”。

## 9. evidence refs / decision refs 格式

推荐继续使用以下格式：

- `oq:OQ-004`
- `module:M03`
- `subtask:ST03_01`
- `doc:DOC-SPEC-P1#architecture`
- `doc:DOC-PLAN-P1#milestones`
- `round:R-2026-04-22-SPECPLAN-01`
- `decision:DR-2026-04-22-SPECPLAN-01`

说明：

- `Decision:` 仍是 round 模板中的决策摘要锚点。
- 当 `confirm-transition` 传入 `--round-id` 时，`--reason` 仍必须与 `Decision:` 锚点对齐。

## 10. 收口规则

已登记 round 进入 `closed` 前，必须至少满足以下之一：

- 已完成对应 document 的 `confirm-transition`
- 已明确记录 `close_reason=blocked|cancelled|superseded|completed`

当 round 关闭时：

- 目标 document 的 `active_round_id` 应清空
- 目标 document 的 `last_round_id` 应更新为当前 round
- 若仍有未解决事项，应通过 `writeback_items` 或下一轮 agenda 继续承接

## 11. 下一轮 agenda 的当前来源

下一轮 agenda 当前优先从以下来源收集：

1. evaluate 输出中的 OQ gate blocker
2. document blocker / missing relation refs / missing required sections
3. `plan-open-window` 与 `plan-round` 里仍需 review 的对象
4. 未关闭 round 的 `writeback_items`

`render-report` 中的 `## Next Round Agenda` 仍然只是建议层，不是审批命令，也不等于状态写回。

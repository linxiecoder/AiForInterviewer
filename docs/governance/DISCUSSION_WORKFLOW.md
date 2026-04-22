# 讨论轮次工作流（Discussion Workflow）

本文档定义每轮讨论（round）的最小输入契约，并约束与 `doc-governor`、本地 Codex CLI 的联动方式。

## 1. 轮次生命周期

每个 round 固定按以下阶段推进：

1. `plan-round`
2. `generate-round-template`
3. `generate-codex-packet`
4. 人工执行 `codex.cmd exec`
5. `update-round-status --status review`
6. `confirm-transition`
7. `update-round-status --status closed`

固定状态枚举：
- `open`
- `in_progress`
- `review`
- `closed`

## 2. 每轮讨论最小输入

每轮讨论必须至少包含以下字段：

- `round_goal`
- `entities_in_scope`
- `decision_criteria`
- `required_evidence_refs`
- `exit_criteria`

对于 document round，必须再补齐：
- `target_documents`
- `target_sections`
- `writeback_items`

## 3. 状态登记字段

`governance_rounds[*]` 当前至少应包含：

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

建议补充字段：
- `started_at`
- `review_at`
- `closed_at`
- `closed_by`
- `close_reason`
- `packet_paths`
- `result_summary`

## 4. scope 与 target_documents

- `scope` 保留为人类可读摘要，例如 `documents:DOC-SPEC-P1,DOC-PLAN-P1`。
- `target_documents` 是结构化范围定义，至少包含：
  - `document_id`
  - `target_sections`
- `target_sections` 只允许 section id，不直接使用自由文本段落描述。

## 5. evidence refs / decision refs 格式

推荐使用以下格式：

- `oq:OQ-004`
- `module:M03`
- `subtask:ST03_01`
- `doc:DOC-SPEC-P1#architecture`
- `doc:DOC-PLAN-P1#milestones`
- `round:R-2026-04-22-SPECPLAN-01`
- `decision:DR-2026-04-22-SPECPLAN-01`

## 6. 轮次模板与决策摘要锚点

- 统一通过 `python -m tools.doc_governor.cli generate-round-template --round-id <round_id>` 生成模板。
- 默认输出路径：`docs/governance/rounds/<round_id>.md`。
- 模板中必须保留决策摘要锚点前缀：`Decision:`。
- 在 `confirm-transition` 传入 `--round-id` 时，`--reason` 必须包含 `Decision:` 前缀，用于将确认动作与轮次结论对齐。

## 7. Codex Packet 交接

document round 生成 packet 后，固定交接产物为：

- `docs/governance/packets/<round_id>.packet.json`
- `docs/governance/packets/<round_id>.prompt.md`
- `docs/governance/packets/<round_id>.exec.txt`

Windows 本地执行入口固定为：

```powershell
C:\Users\Administrator\AppData\Roaming\npm\codex.cmd exec
```

packet 至少包含：
- 本轮目标
- 目标文档
- 允许修改范围
- 禁止修改范围
- 必须保留的治理约束
- 必须引用的 evidence / decision
- exit criteria
- 回写建议

## 8. 自动预填

对于 legacy open-window 轮次，模板仍可自动预填：

- `near_open_but_blocked`
- `hard_blocked`

> 这两类列表来自 `plan-open-window`，仅作讨论输入参考，不直接写回状态层。

对于 document round，模板自动预填：

- `target_documents`
- `required_evidence_refs`
- `writeback_items`

## 9. 收口规则

round 进入 `closed` 前，必须至少满足以下之一：

- 已完成对应 document 的 `confirm-transition`
- 已明确记录 `close_reason=blocked|cancelled|superseded`

当 round 关闭时：
- 目标 document 的 `active_round_id` 应清空
- 目标 document 的 `last_round_id` 应更新为当前 round
- 若仍有未解决事项，必须写入 `writeback_items`

## 10. 下一轮 agenda 生成

下一轮 agenda 优先从以下来源收集：

1. evaluate 输出中的 OQ gate blocker
2. document blocker / missing relation refs / missing required sections
3. `review_required` 的 near-open module / subtask
4. 未关闭 round 的 `writeback_items`

`render-report` 中的 `## Next Round Agenda` 仍然只是建议层，不是审批命令。

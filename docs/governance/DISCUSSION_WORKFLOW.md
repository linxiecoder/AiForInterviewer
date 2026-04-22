# 讨论轮次工作流（Discussion Workflow）

本文档定义每轮讨论（round）的最小输入契约，并约束与 `doc-governor` 的联动方式。

## 1. 每轮讨论最小输入

每轮讨论必须至少包含以下字段：

- `round_goal`
- `entities_in_scope`
- `decision_criteria`
- `required_evidence_refs`
- `exit_criteria`

## 2. 轮次模板与决策摘要锚点

- 统一通过 `doc-governor generate-round-template --round-id <round_id>` 生成模板。
- 默认输出路径：`docs/governance/rounds/<round_id>.md`。
- 模板中必须保留决策摘要锚点前缀：`Decision:`。
- 在 `confirm-transition` 传入 `--round-id` 时，`--reason` 必须包含 `Decision:` 前缀，用于将确认动作与轮次结论对齐。

## 3. 自动预填（来自 plan-open-window）

轮次模板会自动预填以下两类实体，减少人工整理：

- `near_open_but_blocked`
- `hard_blocked`

> 两类列表均由 `plan-open-window` 输出读取并写入模板，仅作讨论输入参考，不直接写回状态层。

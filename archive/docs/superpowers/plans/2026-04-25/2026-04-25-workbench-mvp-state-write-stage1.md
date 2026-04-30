---
title: 2026-04-25-workbench-mvp-state-write-stage1
type: note
permalink: ai-for-interviewer/archive/docs/superpowers/plans/2026-04-25/2026-04-25-workbench-mvp-state-write-stage1
---

# AI 模拟面试一期工作台 MVP State Write 阶段 1 变更与回退说明

## 1. 背景

本文件记录 `W13-E4-B` 的阶段 1 正式状态层写入结果。阶段 1 按用户确认的 C-Phased 策略执行，只把 `ST13_01~ST13_25` 写入正式 `docs/governance/DOC_STATE.yaml`，并保留旧 `STxx_*` 不动。

本轮用户确认结果：

- `OQ-094=B`：执行 `W13-E4-B`，只写入 `ST13_01~ST13_25`，保留旧 `STxx_*`。
- `OQ-095`：阶段 1 按方案 C，只并存新旧任务，暂不表达旧 `STxx_*` superseded；阶段 2 再按方案 B 使用现有 `facts` 字段表达 `superseded / historical-reference`。
- `OQ-096=B`：创建 State Write 变更说明和回退说明，不复制正式 `DOC_STATE.yaml`。

## 2. 本阶段写入范围

- 修改 `docs/governance/DOC_STATE.yaml`。
- 在 `subtasks` 容器新增 `ST13_01~ST13_25`。
- 保留每个 `ST13_*` 的 `WT13-xx` alias，位置为 `facts.w13_preview.wt13_id`。
- 保留每个 `ST13_*` 的 W13 事实源指向，位置为 `facts.w13_preview.source_doc`。
- 将 `facts.w13_preview.formal_doc_state_write` 设为 `true`，表示这些条目已从 Preview 进入正式状态层。
- 将 `ST13_01~ST13_25` 追加到 `requirements.RQ01.facts.task_ids`。

## 3. 本阶段明确不做的事项

- 不移除旧 `STxx_*`。
- 不把旧 `STxx_*` 标记为 `superseded` 或 `historical-reference`。
- 不迁移任何旧任务到 `archive/`。
- 不修改 `tools/**`、`tests/**`、`docs/modules/**`、`apps/**`、`infra/**`。
- 不生成 implementation packet。
- 不标记任何任务为 `implementation-ready`。
- 不打开 formal implementation window。
- 不执行 Git 提交或推送。
- 不写 Basic Memory。

## 4. `ST13_01~ST13_25` 写入摘要

| 正式状态层 ID | WT13 alias | 主模块 | 当前状态 |
| --- | --- | --- | --- |
| `ST13_01` | `WT13-01` | M01 | blocked，不具备实施条件 |
| `ST13_02` | `WT13-02` | M01 | blocked，不具备实施条件 |
| `ST13_03` | `WT13-03` | M03 | blocked，不具备实施条件 |
| `ST13_04` | `WT13-04` | M03 | blocked，不具备实施条件 |
| `ST13_05` | `WT13-05` | M02 | blocked，不具备实施条件 |
| `ST13_06` | `WT13-06` | M03 | blocked，不具备实施条件 |
| `ST13_07` | `WT13-07` | M05 | blocked，不具备实施条件 |
| `ST13_08` | `WT13-08` | M06 | blocked，不具备实施条件 |
| `ST13_09` | `WT13-09` | M06 | blocked，不具备实施条件 |
| `ST13_10` | `WT13-10` | M05 | blocked，不具备实施条件 |
| `ST13_11` | `WT13-11` | M04 | blocked，不具备实施条件 |
| `ST13_12` | `WT13-12` | M06 | blocked，不具备实施条件 |
| `ST13_13` | `WT13-13` | M04 | blocked，不具备实施条件 |
| `ST13_14` | `WT13-14` | M08 | blocked，不具备实施条件 |
| `ST13_15` | `WT13-15` | M06 | blocked，不具备实施条件 |
| `ST13_16` | `WT13-16` | M04 | blocked，不具备实施条件 |
| `ST13_17` | `WT13-17` | M03 | blocked，不具备实施条件 |
| `ST13_18` | `WT13-18` | M05 | blocked，不具备实施条件 |
| `ST13_19` | `WT13-19` | M03 | blocked，不具备实施条件 |
| `ST13_20` | `WT13-20` | M01 | blocked，不具备实施条件 |
| `ST13_21` | `WT13-21` | M01 | blocked，不具备实施条件 |
| `ST13_22` | `WT13-22` | M01 | blocked，不具备实施条件 |
| `ST13_23` | `WT13-23` | M01 | blocked，不具备实施条件 |
| `ST13_24` | `WT13-24` | M01 | blocked，不具备实施条件 |
| `ST13_25` | `WT13-25` | M01 | blocked，不具备实施条件 |

## 5. `RQ01.facts.task_ids` 更新摘要

阶段 1 只追加 `ST13_01~ST13_25`，不删除旧引用。当前 `RQ01.facts.task_ids` 同时保留：

- 旧引用：`ST01_01`、`ST09_03`。
- 新写入：`ST13_01~ST13_25`。

该并存状态是阶段 1 的预期结果，不表示旧 `STxx_*` 已被 superseded，也不表示新 `ST13_*` 已具备 implementation-ready。

## 6. 旧 `STxx_*` 保留说明

阶段 1 没有改写、删除、移动或标记旧 `STxx_*`。旧任务仍留在正式 `subtasks` 容器中，继续作为 state-bound 历史结构与追溯入口。旧任务的 superseded / historical-reference 表达留给阶段 2。

## 7. 预期 blocker

阶段 1 写入后，新增 `ST13_*` 的 blocker 是预期可解释 blocker，原因包括：

- `global_policy.formal_window_open=false`。
- `ST13_*` 尚无正式 `SUBTASK_DESIGN.md` 与 `SUBTASK_IMPLEMENTATION.md`。
- `implementation_doc_state=missing`。
- `allowed_modify_paths`、`required_tests`、`acceptance_criteria` 尚未形成 implementation packet 输入。

这些 blocker 只说明新任务还不能实施，不属于 schema error、missing reference 或 formal window 误开。

## 8. 实际验证结果

写入前：

- 正式 `DOC_STATE.yaml`：`validate-state ok=true, error=0, warning=0`。
- 正式 `DOC_STATE.yaml`：`evaluate-state ok=true, error=0, warning=0`，`documents_blocked_count=0`、`modules_blocked_count=1`、`subtasks_blocked_count=30`。
- Preview YAML：`validate-state ok=true, error=0, warning=0`。
- Preview YAML：`evaluate-state ok=true, error=0, warning=0`，`documents_blocked_count=0`、`modules_blocked_count=1`、`subtasks_blocked_count=55`。

写入后：

- 正式 `DOC_STATE.yaml`：`validate-state ok=true, error=0, warning=0`。
- 正式 `DOC_STATE.yaml`：`evaluate-state ok=true, error=0, warning=0`，`documents_blocked_count=0`、`modules_blocked_count=1`、`subtasks_blocked_count=55`。
- 未发现 implementation-ready 误判。
- 未发现 formal window 误开。
- 未发现 schema error、missing reference 或 stale target。

## 9. 回退步骤

如需回退阶段 1，应只撤销本阶段写入，不回滚 W13-E / W13-E2 / W13-E3 / W13-E4-A 的既有文档成果。

1. 在 `docs/governance/DOC_STATE.yaml` 中删除 `subtasks.ST13_01~subtasks.ST13_25`。
2. 在 `requirements.RQ01.facts.task_ids` 中删除 `ST13_01~ST13_25`，保留原有 `ST01_01` 与 `ST09_03`。
3. 撤销 `TASK_INDEX.md` 中关于 `ST13_*` 已正式写入的阶段 1 表述，保留 `WT13-xx` 候选任务域历史记录。
4. 撤销 `MODULE_INDEX.md` 中关于 `ST13_*` 已正式写入的阶段 1 表述，保留 W13 候选模块映射。
5. 撤销 `PLAN_LATEST.md`、`DOCUMENT_PROGRESS.md`、`DOCUMENT_MATURITY.md`、`OPEN_QUESTIONS.md`、`DESIGN_DECISIONS.md`、`EXECUTION_LOG.md` 中“阶段 1 已执行”的表述，恢复为“等待阶段 1 确认 / 执行”。
6. 保留 Preview YAML 与 State Write 分阶段计划，作为回退后的复盘依据。

## 10. 回退成功判断

回退后必须满足：

- `DOC_STATE.yaml` 不再包含 `ST13_01~ST13_25`。
- `RQ01.facts.task_ids` 不再包含 `ST13_01~ST13_25`。
- 旧 `STxx_*` 仍存在，且未被标记 superseded。
- `validate-state` 结果为 `ok=true, error=0, warning=0`。
- `evaluate-state` 结果为 `ok=true, error=0, warning=0`。
- `subtasks_blocked_count` 回到阶段 1 前的 30。
- 没有“阶段 1 已正式写入”的残留误导。

## 11. 后续阶段 2 输入

阶段 2 的输入是：在阶段 1 验证全部通过后，另开窗口处理旧 `STxx_*` 的 `superseded / historical-reference` 表达。阶段 2 不应由本文件自动触发，仍需用户明确确认。

## 12. 当前仍不能实现说明

阶段 1 只是正式状态层入口写入，不是实施放行。当前仍不能实现，原因是：

- formal window 仍关闭。
- `ST13_*` 尚无子任务双文档。
- `implementation_ready=false`。
- implementation packet 未生成，且本窗口明确禁止生成。
- `apps/**`、`infra/**`、`tools/**`、`tests/**` 均未进入本阶段修改范围。
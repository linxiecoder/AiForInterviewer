---
title: 2026-04-25-workbench-mvp-state-write-stage3
type: note
permalink: ai-for-interviewer/archive/docs/superpowers/plans/2026-04-25/2026-04-25-workbench-mvp-state-write-stage3
---

# AI 模拟面试一期工作台 MVP State Write 阶段 3 变更与回退说明

## 1. 背景

本文件记录 `W13-E4-F` 的阶段 3 正式状态层写入结果。阶段 3 基于 `W13-E4-E` 已通过的 Stage3 Preview 执行，只处理正式 `docs/governance/DOC_STATE.yaml` 中当前任务容器和 `RQ01.facts.task_ids` 的收敛，不进入实现。

## 2. 用户确认方案 B

用户已确认方案 B：进入正式 Stage 3 写入窗口，从正式 `DOC_STATE.yaml.subtasks` 移出旧 `STxx_*`，并从 `RQ01.facts.task_ids` 移除旧 `ST01_01`、`ST09_03`。

该确认不表示 archive 迁移完成，不表示旧 `STxx_*` 文档删除，不表示 implementation-ready，也不表示 formal window 已打开。

## 3. Stage3 Preview 结果摘要

- Preview `validate-state`：`ok=true, error=0, warning=0`。
- Preview `evaluate-state`：`ok=true, error=0, warning=0`。
- Preview `documents_blocked_count=0`。
- Preview `modules_blocked_count=1`。
- Preview `subtasks_blocked_count=25`。
- Preview `subtasks` 中旧 `STxx_*` 数量为 `0`。
- Preview `subtasks` 中 `ST13_*` 数量为 `25`。
- Preview `RQ01.facts.task_ids` 只保留 `ST13_01~ST13_25`。
- Preview 未出现 schema error、missing reference、stale target、implementation-ready 误判或 formal window 误开。

## 4. 本阶段正式修改范围

- 修改 `docs/governance/DOC_STATE.yaml`。
- 同步 `TASK_INDEX.md`、`MODULE_INDEX.md`、`PLAN_LATEST.md`、`EXECUTION_LOG.md`、`DOCUMENT_PROGRESS.md`、`DOCUMENT_MATURITY.md`、`OPEN_QUESTIONS.md`、`DESIGN_DECISIONS.md`。
- 同步 `docs/superpowers/plans/2026-04-25-workbench-mvp-state-write-plan.md`、`2026-04-25-workbench-mvp-state-write-stage3-dry-run.md`、`2026-04-25-workbench-mvp-task-remap.md`、`2026-04-25-workbench-mvp-backlog-roadmap.md`。
- 新增本阶段正式写入说明与回退说明文档。

## 5. 本阶段明确不做

- 不删除旧 `STxx_*` 文档。
- 不迁移旧 `STxx_*` 到 `archive/`。
- 不修改 `docs/modules/**`。
- 不修改 closed round 历史引用。
- 不修改 `transition_history`。
- 不生成 implementation packet。
- 不设置 implementation-ready。
- 不打开 formal window。
- 不创建 `apps/**`、`infra/**`。
- 不修改 `tools/**`、`tests/**` 或 schema / evaluate / validate 代码。

## 6. DOC_STATE.yaml 修改摘要

正式 `docs/governance/DOC_STATE.yaml` 已完成以下变更：

- `subtasks` 容器从 `55` 个任务收敛为 `25` 个任务。
- `subtasks` 容器只保留 `ST13_01~ST13_25`。
- 旧 `ST01_01~ST10_03` 不再位于正式 `subtasks` 容器。
- `global_policy.formal_window_open` 保持 `false`。
- `documents` 分支未回退旧 `DOC-SPEC-P1 / DOC-PLAN-P1`。
- closed round 历史引用未修改。
- `ST13_01~ST13_25` 的 blocked / 非 implementation-ready 状态未改变。

## 7. 移出的旧 STxx_* 清单

- `ST01_01`、`ST01_02`、`ST01_03`
- `ST02_01`、`ST02_02`、`ST02_03`
- `ST03_01`、`ST03_02`、`ST03_03`
- `ST04_01`、`ST04_02`、`ST04_03`
- `ST05_01`、`ST05_02`、`ST05_03`
- `ST06_01`、`ST06_02`、`ST06_03`
- `ST07_01`、`ST07_02`、`ST07_03`
- `ST08_01`、`ST08_02`、`ST08_03`
- `ST09_01`、`ST09_02`、`ST09_03`
- `ST10_01`、`ST10_02`、`ST10_03`

## 8. RQ01.facts.task_ids 修改摘要

`RQ01.facts.task_ids` 已从阶段 2 的 `27` 项收敛为 `25` 项，最终只保留：

`ST13_01`、`ST13_02`、`ST13_03`、`ST13_04`、`ST13_05`、`ST13_06`、`ST13_07`、`ST13_08`、`ST13_09`、`ST13_10`、`ST13_11`、`ST13_12`、`ST13_13`、`ST13_14`、`ST13_15`、`ST13_16`、`ST13_17`、`ST13_18`、`ST13_19`、`ST13_20`、`ST13_21`、`ST13_22`、`ST13_23`、`ST13_24`、`ST13_25`。

旧 `ST01_01`、`ST09_03` 已从正式 `RQ01.facts.task_ids` 移除。

## 9. TASK_INDEX.md 同步摘要

`TASK_INDEX.md` 已同步阶段 3 口径：

- `ST13_01~ST13_25` 是当前 W13 工作台级正式状态层任务入口。
- `WT13-01~WT13-25` 是业务 alias。
- 旧 `STxx_*` 已从正式状态层 current `subtasks` 容器移出。
- 旧 `STxx_*` 仍保留为历史参考、reusable evidence 和 archive candidate。
- 旧 `STxx_*` 不再作为 current implementation entry。
- 当前仍不得标记 implementation-ready。

## 10. MODULE_INDEX.md 同步摘要

`MODULE_INDEX.md` 已同步阶段 3 口径：

- 各模块当前任务入口指向 `ST13 / WT13`。
- 旧 `STxx_*` 仅作为历史参考和映射证据。
- 旧 `STxx_*` 不被重新激活。
- 模块范围和成熟度不因阶段 3 自动升级。

## 11. 历史可追溯性说明

阶段 3 只解除旧任务在正式状态层 current `subtasks` 容器中的当前位置，不删除历史说明。旧 `STxx_*` 的追溯信息仍保留在：

- `TASK_INDEX.md`
- `MODULE_INDEX.md`
- `docs/superpowers/plans/2026-04-25-workbench-mvp-task-remap.md`
- `docs/superpowers/plans/2026-04-25-workbench-mvp-state-write-stage2.md`
- `docs/superpowers/plans/2026-04-25-workbench-mvp-state-write-stage3-dry-run.md`
- 本文件
- 历史执行日志与 Git 历史

## 12. validate-state 结果

正式写入后：

```text
ok=true
error=0
warning=0
```

## 13. evaluate-state 结果

正式写入后：

```text
ok=true
error=0
warning=0
documents_blocked_count=0
modules_blocked_count=1
subtasks_blocked_count=25
```

## 14. blocked count 对比

| 状态 | documents_blocked_count | modules_blocked_count | subtasks_blocked_count |
| --- | ---: | ---: | ---: |
| Stage 2 正式状态 | 0 | 1 | 55 |
| Stage3 Preview | 0 | 1 | 25 |
| Stage 3 正式写入后 | 0 | 1 | 25 |

`subtasks_blocked_count=25` 是预期结果，来源是 `ST13_01~ST13_25` 尚缺实施级子任务双文档、验收、测试要求，且 formal window 仍关闭。

## 15. 不可接受 blocker 检查

未发现以下不可接受 blocker：

- schema error
- missing reference
- stale target
- parse error
- implementation-ready 误判
- formal window 误开
- requirement relation 丢失
- module relation 丢失
- `ST13_01~ST13_25` 缺失
- archive 被误作为当前事实源

## 16. 回退步骤

如需回退阶段 3，应只撤销本阶段写入，不回滚 W13-A 至 W13-E4-E 的既有成果。

1. 在 `docs/governance/DOC_STATE.yaml` 中恢复旧 `ST01_01~ST10_03` 到 `subtasks` 容器，内容可从 Git 历史或阶段 2 状态中取回。
2. 保持 `ST13_01~ST13_25` 不变。
3. 在 `requirements.RQ01.facts.task_ids` 中恢复旧 `ST01_01`、`ST09_03`，并保留 `ST13_01~ST13_25`。
4. 撤销 `TASK_INDEX.md` 中“旧 `STxx_*` 已从正式状态层 current `subtasks` 容器移出”的阶段 3 表述，恢复为“旧任务仍保留在正式容器”。
5. 撤销 `MODULE_INDEX.md` 中“正式状态层入口已切换到 `ST13 / WT13`，旧 `STxx_*` 不再是 current state entity”的阶段 3 表述。
6. 撤销 `PLAN_LATEST.md`、`DOCUMENT_PROGRESS.md`、`DOCUMENT_MATURITY.md`、`OPEN_QUESTIONS.md`、`DESIGN_DECISIONS.md`、`EXECUTION_LOG.md`、state-write 计划与 backlog 中的阶段 3 已完成表述。
7. 确认 `ST13_01~ST13_25` 未被删除、改名或设置为 implementation-ready。
8. 重新运行正式 `validate-state / evaluate-state`。

## 17. 回退成功判断

回退后必须满足：

- `DOC_STATE.yaml.subtasks` 同时包含旧 `ST01_01~ST10_03` 和 `ST13_01~ST13_25`。
- `RQ01.facts.task_ids` 包含 `ST01_01`、`ST09_03` 和 `ST13_01~ST13_25`。
- `validate-state` 为 `ok=true, error=0`。
- `evaluate-state` 为 `ok=true, error=0`。
- `ST13_01~ST13_25` 仍不具备 implementation-ready。
- `formal_window_open` 仍为 `false`。

## 18. 后续 archive 迁移条件

阶段 3 完成后，可以进入 archive 迁移评估，但不能直接迁移。进入 archive 迁移评估前至少需要：

- 旧 `STxx_*` 的全局索引引用已确认只作历史说明。
- 模块级 `MODULE_TASK_INDEX.md` 的历史引用处理方案已确认。
- archive 迁移不会破坏可追溯性或 closed round 解释。
- 用户另行确认 archive 迁移窗口。

## 19. 当前仍不能实现说明

阶段 3 是状态层 current task 容器收敛，不是实施准备完成。当前仍不能实现，原因包括：

- `ST13_01~ST13_25` 尚无正式子任务双文档。
- `ST13_01~ST13_25` 尚缺明确允许修改范围、验收标准和 required tests。
- `formal_window_open=false`。
- 未生成 implementation packet。
- 未打开 formal window。
- 模块级设计仍需按 W13 唯一事实源继续同步。
---
title: 2026-04-25-workbench-mvp-backlog-roadmap
type: note
permalink: ai-for-interviewer/docs/planning/workbench-mvp/2026-04-25-workbench-mvp-backlog-roadmap
---

# AI 模拟面试一期工作台 MVP 待办与路线图清单

> 本文档保留“当前可执行 backlog 入口”和“字段规范”。W13 历史过程、确认卡逐条记录与阶段性明细已归档，避免正文继续膨胀。

## 1. 文档定位

- 维护范围：当前待办、状态层后续事项、实现前置条件与后续候选能力。
- 正式状态真值：`docs/governance/DOC_STATE.yaml`。
- 历史过程明细入口：`archive/planning/workbench-mvp/2026-04-25-workbench-mvp-backlog-roadmap.history-2026-05-01.md`。
- 归档总台账入口：`archive/governance/archive-ledger.md`。

## 2. 跟踪字段规范

每个待办项必须至少包含以下字段：

- ID
- 标题
- 类别
- 状态
- 优先级
- 来源
- 负责人或处理窗口
- 阻断关系
- 目标解决窗口
- 最近更新时间
- 备注

状态建议：`open`、`in_review`、`blocked`、`confirmed`、`done`、`superseded`、`backlog`。

优先级建议：`P0`、`P1`、`P2`、`P3`。

## 3. 当前活跃待办（精简）

| ID | 标题 | 类别 | 状态 | 优先级 | 目标窗口 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| BR-BLK-004 | implementation-ready 尚未形成 | 当前 MVP 阻断项 | blocked | P0 | W13-E3+ | 当前不能生成 implementation packet。 |
| BR-STATE-005 | archive-candidate 解除引用条件 | 状态层后续事项 | open | P1 | W13-E4+ | 解除 `DOC_STATE.yaml` / 索引引用前不得迁移历史任务文档。 |
| BR-STATE-011 | 评估旧 `STxx_*` archive 迁移 | 状态层后续事项 | open | P1 | 后续窗口 | 只可评估，不得在未确认窗口中迁移 archive 或删除旧文档。 |
| BR-REMAP-002 | `TASK_INDEX.md` 后续正式化 | Task Remap 后续事项 | open | P0 | W13-E3+ | 需补 allowed/forbidden paths、Validation 与 DoD。 |
| BR-REMAP-003 | `MODULE_INDEX.md` 后续正式化 | Task Remap 后续事项 | open | P1 | W13-E3+ | 不得误激活旧 `STxx_*` 或模块 L5 候选。 |
| BR-REMAP-004 | 任务开窗顺序确认 | Task Remap 后续事项 | open | P1 | W13-E3+ | 当前仍停留在设计/contract 前置阶段。 |
| BR-REMAP-019 | `ST13_24` formal window open 执行窗口确认 | Task Remap 后续事项 | open | P0 | formal window 执行窗口 | 推荐只打开 `ST13_24` 作为保守试点。 |
| BR-PRE-001 | API contract | 实现前置条件 | open | P0 | W13-E3+ | 阻断后端和前端联调。 |
| BR-PRE-004 | LLM provider 确认 | 实现前置条件 | open | P0 | W13-E3+ | 阻断真实 LLM 接入。 |
| BR-PRE-005 | RAG 检索路线确认 | 实现前置条件 | open | P0 | W13-E3+ | 阻断面试证据和评分证据。 |
| BR-ARCH-001 | `STxx_*` 历史任务目录处理 | 历史材料后续事项 | open | P1 | W13-E3+ | 需先完成状态层解除引用与用户确认。 |
| UC-W13-E15-001 | 是否允许后续窗口打开 `ST13_24/25` formal window | 用户确认待办 | proposed-default | P0 | 后续 State Update | `OQ-125` 未确认前不得写 `formal_window_open=true`。 |

## 4. 历史明细归档入口

以下内容已迁出本文正文，统一在归档中维护：

- W13 各阶段完成项（含 `done` 的阻断项、State Write 分阶段、Task Remap 已完成批次）。
- 全量用户确认卡（UC-W13-*）逐条历史。
- 二期/三期候选能力全量历史快照。

请从以下入口追溯：

1. `archive/planning/workbench-mvp/2026-04-25-workbench-mvp-backlog-roadmap.history-2026-05-01.md`
2. `archive/governance/archive-ledger.md`

## 5. 更新规则

1. 新增待办时必须补齐第 2 节字段。
2. 状态变化后同步更新最近更新时间和备注。
3. 任何 `confirmed` 状态必须可追溯到用户确认、`DESIGN_DECISIONS.md` 或正式文档事实源。
4. 任何会影响 `DOC_STATE.yaml` 的事项必须先进入 preview / dry-run 或用户确认卡。
5. 本文件不得被用来绕过 `validate-state`、`evaluate-state`、`confirm-transition` 或 formal window gate。

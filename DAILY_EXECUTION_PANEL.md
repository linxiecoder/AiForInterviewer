---
title: DAILY_EXECUTION_PANEL
type: note
permalink: ai-for-interviewer/daily-execution-panel
---

# 每日执行面板（会话默认起点）

> 目的：作为每次 Codex 会话的默认起点，记录“今天只做什么、在哪个窗口做、被什么阻断、完成到什么证据、明天从哪里接力”。
>
> 维护要求：每次开发结束必须更新本页（至少更新日期、唯一目标、窗口卡、完成证据、次日接力入口）。

## 0. 今日信息

- 日期：2026-05-01
- 当前分支：`main`
- 当前主推进迭代：R0

## 1. 今日唯一目标（只能 1 个）

- 建立并启用根目录轻量“每日执行面板”机制，作为后续会话固定起点。

## 2. 当前窗口卡

| 字段 | 内容 |
| --- | --- |
| Window ID | `R0-W-DAILY-PANEL-01` |
| Allowed Paths | `DAILY_EXECUTION_PANEL.md`、`PLAN_LATEST.md` |
| Forbidden Paths | `docs/governance/DOC_STATE.yaml`、`tools/doc_governor/**`、业务代码目录 |
| DoD | 1) 根目录存在可复用模板化面板；2) 覆盖“唯一目标/窗口卡/阻断项/证据/次日接力”；3) 明确“每次开发结束必须更新”。 |
| Validation | `test -f DAILY_EXECUTION_PANEL.md`；`rg "每次开发结束必须更新" DAILY_EXECUTION_PANEL.md`；`git status --short` |

## 3. 阻断项与负责人

| 阻断项 | 负责人 | 状态 | 说明 |
| --- | --- | --- | --- |
| 当前无阻断 | - | open | 若出现 gate/依赖阻断，按新增行维护。 |

## 4. 当日完成证据链接（提交 / 文档 / 测试结果）

- 提交：待本次会话提交后补充 commit hash。
- 文档：`DAILY_EXECUTION_PANEL.md`（本文件）。
- 测试结果：待执行验证命令后回填。

## 5. 次日接力入口

- 下一步第一条命令：`sed -n '1,220p' DAILY_EXECUTION_PANEL.md`
- 下一步第一份文档：`PLAN_LATEST.md`

## 6. 结束前更新清单（每次必做）

- [ ] 回填“今日信息”（日期、分支、主迭代）。
- [ ] 校验“今日唯一目标”仍为 1 条且已完成或明确未完成原因。
- [ ] 更新窗口卡中的 Allowed/Forbidden Paths、DoD、Validation。
- [ ] 更新阻断项与负责人（无阻断也要显式写“当前无阻断”）。
- [ ] 补齐当日证据（commit hash、文档路径、测试命令结果）。
- [ ] 写明“次日第一条命令 + 第一份文档”。

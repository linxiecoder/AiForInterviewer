---
title: GOALS_README
type: execution-evidence-index
status: evidence-only
owner: 文档治理
permalink: ai-for-interviewer/docs/goals
---

# docs/goals

`docs/goals/` 是受控窗口的 execution evidence / close-out records 目录，用于保存窗口完成报告、审计或 backfill delta、验证证据和剩余缺口。

## 边界

- 本目录不是 active requirement、active design、delivery plan、ADR、Project source 或代码事实源。
- 本目录不得替代 `docs/01-product/PRD.md`、`docs/02-design/*.md`、`docs/03-delivery/BACKLOG.md`、`docs/03-delivery/DELIVERY_PLAN.md`、`docs/04-decisions/ADR-*.md` 或当前代码。
- 本目录中的 proposed delta 只表示执行后建议回填内容；除非后续授权窗口已经修改对应 active source docs，否则不得视为当前事实。
- 本目录不得绕过 `BACKLOG.md`、`DELIVERY_PLAN.md`、active docs 或 ADR 流程启动任务、关闭阶段、改变需求、改变设计或改变实现事实。

## Source hierarchy

当 goal records 与当前事实冲突时，优先级如下：

1. GitHub main 当前代码和当前仓库文档事实。
2. `docs/00-governance/DOCS_INDEX.md` 登记的 active docs、`BACKLOG.md`、`DELIVERY_PLAN.md`、ADR 和 Project source。
3. `docs/goals/` 中的 execution evidence、final report、audit/backfill delta、validation evidence 和 remaining gaps。

## Required shape

未来 goal records 必须按日期和 window 建目录，建议形态为：

- `docs/goals/YYYY-MM-DD/<WINDOW-ID>/`
- final report：记录 root cause、what changed、files changed、validation commands/results 和 remaining risks。
- audit/backfill delta：记录 proposed matrix / risk / decision delta，并明确是否尚未回写 active source docs。
- validation evidence：记录实际执行命令、结果和失败或跳过原因。
- remaining gaps：记录未完成项、后续窗口边界和不得自动视为完成的事项。

## Index

### 2026-06-03 / P1-W1

- [P1_W1_FINAL_REPORT.md](2026-06-03/P1-W1/P1_W1_FINAL_REPORT.md)：P1-W1 close-out final report，只作为执行证据。
- [P1_W1_BACKFILL_DELTA.md](2026-06-03/P1-W1/P1_W1_BACKFILL_DELTA.md)：P1-W1 proposed backfill delta；除非后续授权窗口回写 active source docs，否则保持 proposed delta 状态。

### 2026-06-03 / P1-W2

- [P1_W2_FINAL_REPORT.md](2026-06-03/P1-W2/P1_W2_FINAL_REPORT.md)：P1-W2 close-out final report，只作为执行证据；implementation commit `fca4dd2fceed030f1fa7c102892945d71d6f7e2a`。
- [P1_W2_BACKFILL_DELTA.md](2026-06-03/P1-W2/P1_W2_BACKFILL_DELTA.md)：P1-W2 proposed backfill delta；DDD-001 / DDD-002 仍为 advanced / partial，Phase 1 仍保持 open。

### 2026-06-03 / P1-W3

- [P1_W3_FINAL_REPORT.md](2026-06-03/P1-W3/P1_W3_FINAL_REPORT.md)：P1-W3 architecture / boundary tests final report，只作为执行证据；Phase 1 仍保持 open。
- [P1_W3_BACKFILL_DELTA.md](2026-06-03/P1-W3/P1_W3_BACKFILL_DELTA.md)：P1-W3 proposed backfill delta；记录 provider forbidden-key test/gate 和 `developer_prompt` / `full_asset_body` remaining gap。

### 2026-06-03 / Phase 1 Close-out

- [PHASE_1_CLOSEOUT_ASSESSMENT.md](2026-06-03/PHASE_1_CLOSEOUT_ASSESSMENT.md)：Phase 1 close-out assessment；推荐 `close_with_deferred_gaps`，需 owner 确认；不启动后续阶段。
- [PHASE_1_CLOSEOUT_GAP_REGISTER.md](2026-06-03/PHASE_1_CLOSEOUT_GAP_REGISTER.md)：Phase 1 deferred gap register；登记 provider、Agent C0 catalog、runtime wiring、Canonical Evidence / SourceSupportSummary 和剩余 Polish ownership gap。

### 2026-06-03 / Phase 3 P3-W0 Scope Lock

- [PHASE_3_SCOPE_LOCK.md](2026-06-03/PHASE_3_SCOPE_LOCK.md)：P3-W0 Domain Policies scope-lock / recon 记录；docs-only，未启动实现。
- [PHASE_3_WINDOW_CATALOG.md](2026-06-03/PHASE_3_WINDOW_CATALOG.md)：Phase 3 window catalog 和当前 P3-W1..P3-W6 状态图；只作为执行建议。
- [PHASE_3_ENTRY_GAP_REGISTER.md](2026-06-03/PHASE_3_ENTRY_GAP_REGISTER.md)：Phase 3 entry gap register；登记 Phase 2 closeout evidence、SRC-001、CTX-002、P3-W1 sequence 和剩余 Domain Policy gap。
- [PHASE_3_DECISION_OPTIONS.md](2026-06-03/PHASE_3_DECISION_OPTIONS.md)：Phase 3 后续执行顺序选项和推荐 next prompt；需 controller 确认后才能进入实现。


### 2026-06-03 / P3-W2

- [P3_W2_FINAL_REPORT.md](2026-06-03/P3-W2/P3_W2_FINAL_REPORT.md)：P3-W2 question grounding / follow-up coverage domain policy final report；Phase 2 / SRC-001 / CTX-002 仍为 deferred gap，P3-W1 仍为 `partial_with_deferred_gap`。


### 2026-06-03 / P3-W3

- [P3_W3_FINAL_REPORT.md](2026-06-03/P3-W3/P3_W3_FINAL_REPORT.md)：P3-W3 feedback review domain policies final report；FAG-002 / FAG-003 / FAG-004 已抽为 domain policy，P3-W4 和 Phase 2 / SRC-001 / CTX-002 deferred gaps 仍保持 open。


### 2026-06-03 / P3-W4

- [P3_W4_FINAL_REPORT.md](2026-06-03/P3-W4/P3_W4_FINAL_REPORT.md)：P3-W4 feedback next-action domain policy final report；FAG-005 已抽为 domain policy，P3-W5 和 Phase 2 / SRC-001 / CTX-002 deferred gaps 仍保持 open。

### 2026-06-03 / Phase 3 P3-W1 Evidence

- [PHASE_3_CLOSEOUT_ASSESSMENT.md](2026-06-03/PHASE_3_CLOSEOUT_ASSESSMENT.md)：既有 P3-W1 source support closeout evidence；只记录 source support partial，不关闭 Phase 3。
- [PHASE_3_CLOSEOUT_GAP_REGISTER.md](2026-06-03/PHASE_3_CLOSEOUT_GAP_REGISTER.md)：既有 P3-W1 gap register；保留 CTX-002 / SourceSupportSummary deferred gap 和其他 Domain Policy 未完成项。

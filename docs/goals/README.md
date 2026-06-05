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

- [P3_W4_FINAL_REPORT.md](2026-06-03/P3-W4/P3_W4_FINAL_REPORT.md)：P3-W4 feedback next-action domain policy final report；FAG-005 已抽为 domain policy；后续 PRE-P4 evidence 显示 CTX-002 已修复，SRC-001 已回填，Phase 2 closeout evidence 已恢复并对账。

### 2026-06-03 / P3-W5

- [P3_W5_FINAL_REPORT.md](2026-06-03/P3-W5/P3_W5_FINAL_REPORT.md)：P3-W5 application bridge / boundary hardening final report；bridge / adapter architecture gate 已加固；后续 PRE-P4 evidence 显示 CTX-002 已修复，SRC-001 已回填，Phase 2 closeout evidence 已恢复并对账。

### 2026-06-03 / P3-W6

- [P3_W6_FINAL_REPORT.md](2026-06-03/P3-W6/P3_W6_FINAL_REPORT.md)：P3-W6 closeout / source backfill assessment；Phase 3 implementation evidence 已汇总；后续 PRE-P4 evidence 显示 CTX-002 已修复，SRC-001 已回填，Phase 2 closeout evidence 已恢复并对账。

### 2026-06-03 / Phase 3 Closeout Assessment

- [PHASE_3_CLOSEOUT_ASSESSMENT.md](2026-06-03/PHASE_3_CLOSEOUT_ASSESSMENT.md)：post-P3-W5 Phase 3 closeout assessment；记录 Domain Policy implementation evidence、PRE-P4-W1 CTX-002 repair evidence、PRE-P4-W4 SRC-001 repo backfill 和 PRE-P4-W5 recovered Phase 2 evidence reconciliation；Phase 3 为 `closed_with_recovered_phase2_evidence`。
- [PHASE_3_CLOSEOUT_GAP_REGISTER.md](2026-06-03/PHASE_3_CLOSEOUT_GAP_REGISTER.md)：post-P3-W5 / P3-W6 gap register；登记 CTX-002 / SourceSupportSummary 已由 PRE-P4-W1 修复、SRC-001 已由 PRE-P4-W4 回填，Phase 2 closeout evidence 已由 PRE-P4-W5 恢复并对账。
- [PHASE_3_AUDIT_AND_RESIDUAL_LOCK.md](2026-06-03/PHASE_3_AUDIT_AND_RESIDUAL_LOCK.md)：P3-AUDIT-AND-RESIDUAL-LOCK controller audit；接受 P3-W2 到 P3-W5 为 locally audited evidence，确认 P3-W6 是 blocked closeout，Phase 4 未启动。
- [PRE_P4_REMOTE_VERIFICATION_BACKFILL.md](2026-06-03/PRE_P4_REMOTE_VERIFICATION_BACKFILL.md)：PRE-P4-W0 remote verification backfill；登记 P3-W0 / P3-W2 / P3-W3 / P3-W4 / P3-W5 / P3-W6 / P3-AUDIT 为 `GITHUB_REMOTE_VERIFIED_COMMITS`，同时明确 `NO_REMOTE_CI_RUNS_FOUND`、Phase 3 仍被 residual gaps 阻断、Phase 4 未启动。
- [PRE_P4_CTX_002_SOURCE_SUPPORT_SUMMARY.md](2026-06-03/PRE_P4_CTX_002_SOURCE_SUPPORT_SUMMARY.md)：PRE-P4-W1 CTX-002 SourceSupportSummary repair evidence；登记 domain value object、legacy `source_support_level` 兼容和 provider / prompt / API / DB / runtime non-change 边界。
- [PRE_P4_PHASE2_SRC_BACKFILL.md](2026-06-03/PRE_P4_PHASE2_SRC_BACKFILL.md)：PRE-P4-W2 Phase 2 / SRC backfill evidence；记录当时证据不可用和 SRC-001 尚待回填的历史状态；后续 W4 / W5 已分别完成 source pack repo backfill 和 Phase 2 evidence reconciliation。
- [PRE_P4_PROJECT_SOURCE_PACK_BACKFILL.md](2026-06-03/PRE_P4_PROJECT_SOURCE_PACK_BACKFILL.md)：PRE-P4-W4 Project source pack repo backfill evidence；登记 `docs/project-sources/**` 已成为 repo-readable Project source anchors，SRC-001 为 `repo_backfilled_from_project_sources`。
- [PRE_P4_PHASE2_EVIDENCE_RECONCILIATION.md](2026-06-03/PRE_P4_PHASE2_EVIDENCE_RECONCILIATION.md)：PRE-P4-W5 recovered Phase 2 evidence reconciliation；登记 Phase 2 closeout evidence 为 `recovered_and_reconciled`，Phase 2 historical status 为 `close_with_deferred_source_pack_gap` / `partial_deferred`，Phase 3 为 `closed_with_recovered_phase2_evidence`。
- [PHASE_2_CLOSEOUT_ASSESSMENT.md](2026-06-03/PHASE_2_CLOSEOUT_ASSESSMENT.md)：Phase 2 closeout evidence assessment；记录 current mainline 0dbfdb90 evidence、48af513 recovered branch evidence、original P2-W6 source pack deferment 和 PRE-P4-W4 SRC-001 repair。
- [PHASE_2_CLOSEOUT_GAP_REGISTER.md](2026-06-03/PHASE_2_CLOSEOUT_GAP_REGISTER.md)：Phase 2 closeout gap register；关闭 / supersede missing evidence gaps，保留 provider sanitizer、runtime、later-phase gaps。
- [PHASE_2_SOURCE_BACKFILL_STATUS.md](2026-06-03/PHASE_2_SOURCE_BACKFILL_STATUS.md)：Phase 2 source backfill status；登记 required Project source-pack anchors 已在 `docs/project-sources/**` 回填，original P2-W6 source pack deferment 已由 PRE-P4-W4 repair。
- [PHASE_3_FINAL_CLOSEOUT_ASSESSMENT.md](2026-06-03/PHASE_3_FINAL_CLOSEOUT_ASSESSMENT.md)：PRE-P4-W5 final closeout update；记录 Phase 3 `closed_with_recovered_phase2_evidence`，Phase 4 `entry_scope_lock_created` / `implementation_not_started`。
- [PHASE_4_ENTRY_SCOPE_LOCK.md](2026-06-03/PHASE_4_ENTRY_SCOPE_LOCK.md)：Phase 4 entry scope-lock artifact；只授权未来 Agent Contracts / Skills / Tools planning，不启动 implementation。

### 2026-06-03 / P4-W0

- [P4_W0_SCOPE_LOCK.md](2026-06-03/P4_W0_SCOPE_LOCK.md)：P4-W0 docs-only scope lock；锁定 Phase 4 Agent Contracts / Skills / Tools planning 边界，不授权实现。
- [P4_W0_DECISION_OPTIONS.md](2026-06-03/P4_W0_DECISION_OPTIONS.md)：P4-W0 decision options；提供 Option A / B / C，进入 P4-W1 前必须由 Controller / user 选择。
- [P4_W0_WINDOW_CATALOG.md](2026-06-03/P4_W0_WINDOW_CATALOG.md)：P4-W0 proposed next-window catalog；定义 P4-W1 到 P4-W5 的目标、能力 ID、文件边界、验证和 stop conditions。
- [P4_W0_ACCEPTANCE_GATES.md](2026-06-03/P4_W0_ACCEPTANCE_GATES.md)：P4-W0 acceptance gates；登记 candidate-only、no formal write、Tool no repository exposure、no provider/prompt leakage、no runtime wiring 等后续硬闸门。
- [P4_W0_FINAL_REPORT.md](2026-06-03/P4_W0_FINAL_REPORT.md)：P4-W0 final report；记录 docs-only 变更、验证结果、推荐下一决策和剩余风险。

### 2026-06-05 / P4-W1

- [P4_W1_AGENT_CONTRACTS_SKILLS_TOOLS_C1_EXECUTION_REPORT.md](2026-06-05/P4_W1_AGENT_CONTRACTS_SKILLS_TOOLS_C1_EXECUTION_REPORT.md)：P4-W1 Agent Contracts / Skills / Tools C1 execution report；记录 RED/GREEN、C1 catalog、registry validation、forbidden-scope audit 和 source backfill。
- [P4_W1_FIX01_AGENT_CATALOG_HYGIENE_EXECUTION_REPORT.md](2026-06-05/P4_W1_FIX01_AGENT_CATALOG_HYGIENE_EXECUTION_REPORT.md)：P4-W1.fix.01 Agent Catalog Hygiene execution report；记录 catalog decomposition、version separation、SkillDefinition contract hygiene、验证和 forbidden-scope audit。
- [PHASE_4_CLOSEOUT_ASSESSMENT.md](2026-06-05/PHASE_4_CLOSEOUT_ASSESSMENT.md)：Phase 4 closeout assessment；状态为 `complete_with_deferred_gaps`，runtime/eval gates 仍 deferred。
- [PHASE_4_GAP_REGISTER.md](2026-06-05/PHASE_4_GAP_REGISTER.md)：Phase 4 deferred gap register；记录 Phase 5/6/8/9 后续边界和既有 provider xfail gap。

### 2026-06-05 / P5P6-W1

- [P5P6_W1_SCOPE_LOCK.md](2026-06-05/P5P6-W1-C2-C3-PLANNED-WORKFLOW-L5-FOUNDATION/P5P6_W1_SCOPE_LOCK.md)：P5P6-W1 Controller scope lock；授权 Phase 5 / Phase 6 C2 / C3 L2 planned guarded workflow，禁止 Phase 8 / Phase 11 / Phase 12 和 prompt/provider/API/DB 行为改动。
- [P5P6_W1_CLOSEOUT_REPORT.md](2026-06-05/P5P6-W1-C2-C3-PLANNED-WORKFLOW-L5-FOUNDATION/P5P6_W1_CLOSEOUT_REPORT.md)：P5P6-W1 closeout report；记录 question_candidate / feedback_candidate planned handoff、验证证据、source backfill 和 deferred gaps。

### 2026-06-05 / P5-W1.fix.01

- [P5_W1_FIX01_CLOSEOUT_REPORT.md](2026-06-05/P5-W1.fix.01-QUESTION-PLANNED-WORKFLOW-REMEDIATION/P5_W1_FIX01_CLOSEOUT_REPORT.md)：Question planned workflow remediation closeout；记录 dedicated Question planned workflow component、normal path wiring、验证结果和 deferred blockers。

### 2026-06-05 / P5P6-W1.fix.02

- [P5P6_W1_FIX02_CLOSEOUT_REPORT.md](2026-06-05/P5P6-W1.fix.02-VALIDATION-BLOCKER-REMEDIATION/P5P6_W1_FIX02_CLOSEOUT_REPORT.md)：P5/P6 validation blocker remediation closeout；记录 canonical-evidence legacy test alignment、repo-root `tmp` 处理、验证结果、source backfill 和 L5 non-claim。

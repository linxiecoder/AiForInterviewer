# AI 模拟面试系统当前推进计划

## 1. 文档定位

- 本文档用于说明当前仓库的推进目标、当前阶段、已完成项、阻断项和下一步。
- 本文档是当前执行入口，不再继续以阶段 3 白名单治理叙事作为主导入口。
- 历史治理轮次仍保留在 `EXECUTION_LOG.md`、`DOCUMENT_PROGRESS.md`、`DOCUMENT_MATURITY.md` 等文档中，本文件只保留“当前推进计划”所需信息。

## 2. 当前总目标

- 围绕“AI 模拟面试系统”继续推进设计开发与治理工具链建设。
- 保持“项目目标”和“当前仓库现实”分层表达，避免把未来产品蓝图误写成当前仓库落地计划。
- 让当前主入口能够正确指导后续窗口先做状态校验、再做评估、再决定是否开启新一轮协作。

## 3. 当前仓库阶段

- 当前阶段：`W13` 产品范围重估与一期工作台 MVP 重新定义阶段。
- 当前仓库现实：仓库当前承载设计文档、治理状态、`doc_governor` / `doc_governance` 工具、测试与验证机制，并保留 `apps/web/**` 首切片最小原型作为探索证据。
- 当前仓库限制：`apps/web/**` 不再作为一期 MVP 的直接开发起点；当前仓库尚不是完整 `apps/web`、`apps/api`、`infra` monorepo 实现仓库。
- 当前活动窗口：`W13-A` 用户确认结果写回与一期工作台 MVP 范围冻结草案；当前暂停代码开发，回到设计文档补齐。

## 4. 当前执行入口与历史叙事边界

### 4.1 当前执行入口

当前应以以下入口理解和推进仓库：

1. `README.md`
2. `AGENTS.md`
3. `PLAN_LATEST.md`
4. `docs/superpowers/plans/2026-04-25-current-repo-execution-plan.md`
5. `docs/superpowers/plans/2026-04-25-workbench-mvp-scope.md`
6. `docs/DOC_GOVERNANCE.md`
7. `docs/governance/DOC_AUTOMATION.md`
8. `docs/governance/DOC_GOVERNOR_RUNBOOK.md`
9. `python -m tools.doc_governor.cli validate-state --input docs/governance/DOC_STATE.yaml`
10. `python -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml`

### 4.2 上游产品蓝图

- `docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md` 继续作为上游产品设计输入。
- `docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md` 继续保留，但当前已明确降级为未来 monorepo 蓝图，不再充当当前仓库可直接执行计划。
- 当前仓库执行计划入口改为 `docs/superpowers/plans/2026-04-25-current-repo-execution-plan.md`。
- `W9` 已完成状态层同步：`DOC_STATE.yaml` 的当前受管 plan 入口已切换到 `docs/superpowers/plans/2026-04-25-current-repo-execution-plan.md`，`DOC-PLAN-P1` 不再作为当前仓库受管 execution plan 参与 document evaluate。

### 4.3 历史治理记录

- 阶段 3、白名单、formal window、`M01-M03` 等叙事应视为历史治理背景与阶段记录。
- 这些记录仍有审计价值，但当前不再作为本文件的主叙事。
- 若需要查看历史治理收口链路，应转到 `EXECUTION_LOG.md` 与相关治理状态文档，而不是从本文件继续展开旧轮次。

### 4.4 当前 `doc_governor` 工具链定位

- `doc_governor` 当前是协同 Codex 推进设计开发、文档治理、任务拆分、状态评估、执行交接和验证收口的宽 CLI 工具链。
- 按 W2 已确认结论，命令面应区分：
  - 主链命令
  - 扩展命令
  - 生成类命令
  - preview/apply/sync/seed 类命令
  - 实验性或需谨慎使用命令
- preview/apply/sync/seed 类命令、`generate-implementation-packet`、`apply-round` 不应被写成默认主链 SOP。
- `render-report` 和生成报告属于解释性治理产物，不是 confirmed state 真值。

## 5. 本轮已完成

### 5.1 W2 工具文档对齐

- `docs/DOC_GOVERNANCE.md`、`docs/governance/DOC_AUTOMATION.md`、`docs/governance/DOC_GOVERNOR_RUNBOOK.md` 已完成命令面对齐。
- `DOC_AUTOMATION.md` 与 `DOC_GOVERNOR_RUNBOOK.md` 已覆盖 CLI 全量 39 个顶层子命令。
- 命令角色分层已明确，默认主链与谨慎使用命令的边界已明确。

### 5.2 W3 工具代码 P0

- `validate-state` 当前结果为 `ok=true, error=0, warning=0`。
- `evaluate-state` 当前结果为 `ok=true, error=0, warning=0`。
- 定向 pytest 当前结果为 `43 passed`。
- 已补入 `repo_truth.referenced_paths`、`repo_truth.existing_paths`、`repo_truth.missing_paths`。
- 已补入 `direction_drift.future_blueprint_terms`、`direction_drift.governance_term_count`。
- 已新增 `document_repo_truth_mismatch` blocker，用于识别“未来蓝图路径”和“当前仓库现实”不一致。

### 5.3 W4 测试规则统一

- `docs/governance/TEST_POLICY.md` 与 `tests/test_temp_artifact_policy.py` 已完成统一。
- 当前仓库测试临时产物规则已经收敛到 `ManagedTempArtifacts` / `ManagedTempArtifactsTestCase` + `tools.test_runner.run_tests` + pytest 会话级残留守卫。

### 5.4 W1 主入口收口

- 新建 `README.md`，补上当前项目、当前仓库、当前限制、推荐工作流与测试规则入口说明。
- 重写 `PLAN_LATEST.md`，切换为“当前推进计划”文档。
- 在 `EXECUTION_LOG.md` 追加本轮 W1 收口记录，并列出 W5 与后续窗口事项。

### 5.5 W5-W7 验证、清理与中文化收口

- `W5` 已完成主入口只读复核，通过当前仓库真相与执行入口口径检查。
- `W6-A` 已清理 4 个基线未跟踪项。
- `W6-B` 已完成本轮结论收口保存。
- `W7` 已完成 `render.py` / `bootstrap.py` 生成报告中文化。

### 5.6 W8 计划分层决策

- 已选择方案 `C`：拆分未来蓝图与当前仓库执行计划。
- `DOC-PLAN-P1` 现明确定位为未来 monorepo / 产品落地蓝图。
- 已新增 `docs/superpowers/plans/2026-04-25-current-repo-execution-plan.md`，作为当前仓库执行计划入口。

### 5.7 W10 首切片冻结与关系补齐

- `W10-A` 已冻结“最小功能切片优先”的推进路线，并明确当前不创建业务代码目录。
- `W10-B` 已压实首切片的输入、处理、输出、排除项、验收标准与未来蓝图边界。
- `W10-C` 已补齐 `RQ01 -> M03 / M04 / M06 / M07 (+ 条件性 M01)` 关系层，写清 `MT03_01 / MT03_03` 仅为观察蓝本、`ST04_01 / ST04_02 / ST06_01 / ST06_02 / ST07_03` 仅为后续承接对象，且正式开窗层仍为空。

### 5.8 W10-D-Gate 用户确认完成

- 用户已确认 `Q1=B Q2=A Q3=A Q4=A Q5=A Q6=A Q7=B Q8=B`。
- 当前允许进入的只是不代表正式实施完成的“首切片最小原型探索”复核路径。
- 若下一窗口复核通过，只允许创建 `apps/web/**` 最小原型骨架；`apps/api/**`、`infra/**` 继续禁止。
- 当前明确采用：mock LLM、无登录、会话内临时数据、文字反馈、Markdown 兼容文本、不做导出，并继续排除 RAG / 资产库 / 管理台 / 多轮面试 / 完整权限体系 / 完整 CI/CD。
- `W10-D` 前仍需保持 `git status` 干净，并再次通过 `validate-state` / `evaluate-state`；`W10-D` 后必须进入 `W10-E / W10-F`。

### 5.9 W10-D/W10-E 首切片原型与 UI 核验

- `W10-D` 已以 commit `0c1f4c8` 实现 `apps/web/**` 最小原型：mock LLM、单用户临时会话、会话内临时数据、文字反馈与 Markdown 兼容文本。
- `W10-E` 已以 commit `b3c66d3` 完成 UI 规范核验与最小修复，核验入口包括 P1 设计稿第 16 节、第 19 节、第 19.12 节、第 19.13 节与第 19.21 节。
- `web:test` 与 `web:build` 均已通过，浏览器真实测试已覆盖无 console error、390px 移动宽度无横向溢出与 UI 状态完整性。
- 当前仍未进入正式实施完成；`apps/web/**` 仅表示首切片最小原型探索，后续真实 LLM、登录、持久化、评分、导出、`apps/api/**`、`infra/**` 必须重新走用户确认模式。

### 5.10 W13-A 工作台级 MVP 范围重新冻结

- 用户已确认组合 `1B2C3C4C5C6C7B8A9B`。
- 一期 MVP 不再是 W10 首切片“JD + 简历 Markdown -> 3 条问题 -> 第 1 题问答 -> 简版反馈”，而是工作台级 MVP。
- 一期范围已确认包含：服务端历史记录 / 复盘记录、真实 LLM、完整登录 / 权限、简历和面试记录服务端保存、完整 `0-100` 多维评分，以及复制 / Markdown 下载导出。
- 当前 `apps/web/**` 原型降级为原型探索参考证据，不直接扩展为正式一期开发起点。
- 当前暂停代码开发；在 `W13-B / W13-C / W13-D` 完成并经用户再次确认前，不继续 `W11-B` 代码布局重构，不扩展 `apps/web/**`，不创建 `apps/api/**`，不接真实 LLM，不做数据库、登录、评分或后端实现。

## 6. 当前阻断与风险

- `DOC-PLAN-P1` 已从当前受管 `documents` 集合移出，保留为未来 monorepo / 产品落地蓝图文件与历史 round 引用。
- `evaluate-state` 已不再报告 `DOC-PLAN-P1 -> document_repo_truth_mismatch`；已关闭 round 中保留的 `DOC-PLAN-P1` target / evidence 仅作为历史记录。
- 当前状态层、主入口层与当前仓库执行计划入口已重新对齐，不再存在由旧 plan 造成的 document blocker。
- W10 首切片与 `apps/web/**` mock 原型只表示原型探索成果，不再代表当前一期 MVP 范围。
- 当前一期 MVP 已冻结到工作台级范围，但仍停留在范围草案与设计补齐层，不具备实施开工条件。
- 具体 LLM provider、数据库类型、登录方案、权限模型细节、评分维度和权重、API / 后端框架、导出细节、运维 / 部署边界仍未确认，不能由 Codex 在本轮自行决定。
- 当前暂停代码开发；继续扩展 `apps/web/**`、创建 `apps/api/**`、接真实 LLM、做数据库、登录、评分或后端实现都属于越界。

## 7. 当前推荐推进路径

1. 当前主入口统一以 `PLAN_LATEST.md`、`docs/superpowers/plans/2026-04-25-current-repo-execution-plan.md` 与 `docs/superpowers/plans/2026-04-25-workbench-mvp-scope.md` 为准。
2. `W13-A` 只完成用户确认结果写回与一期工作台 MVP 范围冻结草案，不进入代码实施。
3. `W13-B` 建议补工作台 IA、核心用户旅程、页面对象关系和一期工作台信息架构。
4. `W13-C` 建议补对象模型、服务端保存边界、登录 / 权限方案确认卡、真实 LLM provider / API / 后端框架确认卡。
5. `W13-D` 建议补 `0-100` 多维评分体系、复盘记录、导出范围细节和 MVP DoD。
6. `W13-B / W13-C / W13-D` 完成并经用户再次确认前，不继续 `W11-B` 代码布局重构，不扩展 `apps/web/**`，不创建 `apps/api/**`，不接真实 LLM，不做数据库、登录、评分或后端实现。

## 8. 当前不作为默认主链的内容

以下内容当前不应在主入口中被写成默认闭环：

- preview/apply/sync/seed 类命令
- `generate-implementation-packet`
- `apply-round`
- 任何把 generated report 直接等同于 confirmed state 的叙述

## 9. 维护要求

- 若后续“当前仓库真相”发生变化，应优先更新 `README.md`、`PLAN_LATEST.md` 与 `EXECUTION_LOG.md` 的主入口叙事。
- 若后续处理计划入口，必须同时维护 `DOC-PLAN-P1` 的未来蓝图定位与 `docs/superpowers/plans/2026-04-25-current-repo-execution-plan.md` 的当前执行计划定位。
- 若后续新增正式入口文档，应先补入 `AGENTS.md` 索引，再继续扩展。

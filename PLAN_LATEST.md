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

- 当前阶段：`W10` 首切片最小原型探索收口阶段。
- 当前仓库现实：仓库当前承载设计文档、治理状态、`doc_governor` / `doc_governance` 工具、测试与验证机制，并已出现 `apps/web/**` 首切片最小原型。
- 当前仓库限制：`apps/web/**` 仅代表首切片 mock 原型探索，当前仓库尚不是完整 `apps/web`、`apps/api`、`infra` monorepo 实现仓库。
- 当前活动窗口：`W10-F` 首切片原型收口、状态复核与 Basic Memory 回收；尚未进入正式实施完成。

## 4. 当前执行入口与历史叙事边界

### 4.1 当前执行入口

当前应以以下入口理解和推进仓库：

1. `README.md`
2. `AGENTS.md`
3. `PLAN_LATEST.md`
4. `docs/superpowers/plans/2026-04-25-current-repo-execution-plan.md`
5. `docs/DOC_GOVERNANCE.md`
6. `docs/governance/DOC_AUTOMATION.md`
7. `docs/governance/DOC_GOVERNOR_RUNBOOK.md`
8. `python -m tools.doc_governor.cli validate-state --input docs/governance/DOC_STATE.yaml`
9. `python -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml`

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

## 6. 当前阻断与风险

- `DOC-PLAN-P1` 已从当前受管 `documents` 集合移出，保留为未来 monorepo / 产品落地蓝图文件与历史 round 引用。
- `evaluate-state` 已不再报告 `DOC-PLAN-P1 -> document_repo_truth_mismatch`；已关闭 round 中保留的 `DOC-PLAN-P1` target / evidence 仅作为历史记录。
- 当前状态层、主入口层与当前仓库执行计划入口已重新对齐，不再存在由旧 plan 造成的 document blocker。
- `W10-A` 已冻结当前优先级：先收敛首个 MVP 切片与关系层，不横向铺开完整业务仓库。
- `W10-B` 已把首切片输入边界压实为“岗位 JD 文本 + 简历 Markdown + 可选面试方向”，并明确岗位等级、公司类型、面试轮次不是本轮必需参数；关键字段缺失时只能返回补全提示，不进入问题生成。
- `W10-B` 已把最小处理链压实为“JD 提取 -> 简历提取 -> 最小对齐 -> 首轮问题生成 -> 1 轮问答记录 -> 简版反馈摘要”，并固定排除多轮会话、长期记忆、检索增强、资产归档、训练中心、管理台与未来业务目录全量落地。
- `W10-C` 已完成关系补齐：当前已把 `RQ01 -> M03 / M04 / M06 / M07 (+ 条件性 M01)`、`MT03_01 / MT03_03` 观察蓝本、`ST04_01 / ST04_02 / ST06_01 / ST06_02 / ST07_03` 后续承接对象与“正式开窗层为空”写成当前主口径。
- `W10-D-Gate` 已完成用户确认写回，`W10-D / W10-E` 已完成 `apps/web/**` 最小原型与 UI 核验。
- 当前 W10 仍只是最小原型探索，不代表正式实施完成；`apps/api/**`、`infra/**`、真实 LLM、登录、持久化、评分与导出仍未放行。

## 7. 当前推荐推进路径

1. 当前主入口统一以 `PLAN_LATEST.md` + `docs/superpowers/plans/2026-04-25-current-repo-execution-plan.md` 为准。
2. `W10-A` 已确认下一轮采用“最小功能切片优先”，首切片固定为“岗位 JD 手工输入 + 简历 Markdown 粘贴/编辑 -> 首轮问题 -> 1 轮问答 -> 简版反馈摘要”。
3. `W10-B` 已完成主项目文档细化：当前执行计划中已写死输入、处理、输出、排除项、验收标准、未来蓝图边界与 `W10-C` 交接输入。
4. `W10-C` 已完成关系补齐：`RQ01 -> M03 / M04 / M06 / M07 (+ 条件性 M01)`、`MT03_01 / MT03_03` 观察蓝本、`ST04_01 / ST04_02 / ST06_01 / ST06_02 / ST07_03` 后续承接对象与“正式开窗层为空”已同步到全局入口。
5. `W10-D-Gate` 已完成用户确认写回，确认组合为 `Q1=B Q2=A Q3=A Q4=A Q5=A Q6=A Q7=B Q8=B`。
6. `W10-D / W10-E` 已完成 `apps/web/**` 最小原型与 UI 核验；该结果仍只属于首切片最小原型探索。
7. `W10-F` 负责本轮收口、状态复核与 Basic Memory 回收，不继续扩大业务范围。
8. W10 后续路线必须回到用户确认模式，在原型体验审查、真实 LLM、轻量持久化或后端边界之间重新选择。

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

# AI 模拟面试系统当前仓库执行计划

## 1. 文档定位

- 本文档是当前仓库现实执行计划入口，用于指导下一阶段主项目设计开发与仓库结构决策。
- 本文档不替代 `DOC-PLAN-P1` 的产品蓝图价值，但优先级高于把 `DOC-PLAN-P1` 直接当作当前仓库实施计划的做法。
- 当前主入口仍包括 `README.md`、`AGENTS.md`、`PLAN_LATEST.md`；本文档负责补足“当前仓库执行计划”这一专用入口。

## 2. 当前仓库定位

- 当前仓库主要承载 `AI 模拟面试系统` 的设计文档、治理状态、`doc_governor` / `doc_governance` 工具链，以及对应测试与验证工具。
- 当前仓库真实可核验的主结构仍是根目录治理文档、`docs/`、`tools/doc_governor/`、`tests/` 与 `requirements.txt`。
- 当前仓库不是已经落地完成的“Web 端目录 / API 端目录 / 基础设施目录”一体化业务实现仓库。

## 3. W0-W7 已完成事项

- `W0`：冻结本轮 P0 对齐范围与窗口边界，明确本轮先做治理链路和主入口收口。
- `W1`：新建 `README.md`，重写 `PLAN_LATEST.md`，补记 `EXECUTION_LOG.md`，把主入口切回“当前仓库真相 + 当前推进计划”。
- `W2`：完成 `doc_governor` 治理文档与 CLI 命令面对齐。
- `W3`：补入 `direction_drift`、`repo_truth`、`document_repo_truth_mismatch` 检查，并修复 requirement relation warning。
- `W4`：统一 `TEST_POLICY` 与测试守卫规则。
- `W5`：完成主入口的只读复核，确认当前仓库真相与工具链主入口口径可用。
- `W6-A`：清理 4 个基线未跟踪项。
- `W6-B`：完成本轮结论收口保存。
- `W7`：完成 `render.py` / `bootstrap.py` 生成报告中文化。

## 4. 当前主项目设计开发的真实前置条件

- 需要先明确当前仓库是否真的要创建未来 Web 端目录、API 端目录与基础设施目录结构，而不是继续把未来蓝图当成已生效目录。
- 需要把上游产品蓝图映射成符合当前仓库现实的推进路径，避免从“未来目录规划”直接跳到“当前仓库代码脚手架”。
- 需要补足状态层回写，使 `DOC-PLAN-P1` 不再继续被 `DOC_STATE.yaml` 误当作当前仓库受管 implementation plan。
- 需要确定下一阶段的首批落地单元：是先做模块设计收口、关系补齐，还是先做新的代码目录初始化。

## 5. 当前不直接落未来业务目录结构的原因

- 当前仓库现实并不包含这些目录，直接创建会把未来蓝图伪装成当前事实。
- 当前 `doc_governor` 状态层与主入口层尚未完全同步，如果先落代码目录，会继续放大“蓝图 / 现实 / 状态”三层不一致。
- 当前更缺的是落地路径决策与首批开发边界，而不是先把未来多应用仓库目录一次性铺开。

## 6. 下一步建议

- `是否创建未来多应用仓库结构`：暂不默认创建，建议交给后续总控 / 状态回写窗口做明确决策。
- `是否先完善模块设计`：建议是，先把产品蓝图映射到当前模块与任务链路，再决定首批代码落点。
- `是否先补齐需求到模块到子任务关系`：建议是，避免直接从未来目录蓝图跳到代码实施。
- `是否进入主项目功能设计开发`：可以进入，但应以本文档和 `PLAN_LATEST.md` 为入口，先做设计开发与落地路径决策，不直接宣告未来业务目录开工。

## 7. 验证命令

```powershell
git status --short
python -m tools.doc_governor.cli validate-state --input docs/governance/DOC_STATE.yaml
python -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml
rg -n "未来蓝图|多应用仓库|当前仓库执行计划|DOC-PLAN-P1|document_repo_truth_mismatch" docs/superpowers/plans PLAN_LATEST.md EXECUTION_LOG.md README.md
```

## 8. 与 `DOC-PLAN-P1` 的关系

- `DOC-PLAN-P1` 保留为未来多应用仓库 / 产品落地蓝图。
- 本文档负责描述当前仓库现实下的执行计划与下一阶段入口。
- 若未来正式决定创建新的业务目录结构，应由后续总控窗口基于 `DOC-PLAN-P1` 与本文档共同生成新的正式实施计划或状态回写，而不是把旧蓝图直接继续当作当前仓库真相。

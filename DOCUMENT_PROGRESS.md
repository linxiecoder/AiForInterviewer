# AI 模拟面试项目文档进展

## 1. 文档定位

本文档只记录文档体系进展、当前阶段和阻断摘要，不承载需求正文、设计正文、任务正文或执行日志。

## 2. 当前进展摘要

| area | status | notes |
| --- | --- | --- |
| requirements | active | Workbench MVP 需求层已独立到 `docs/requirements/workbench-mvp/**` |
| design | active | Workbench MVP 设计层继续由 `docs/design/workbench-mvp/**` 承载 |
| planning | active | 当前规划入口为 `PLAN_LATEST.md` 与 `docs/planning/**` |
| task | blocked by implementation gate | ST13 任务文档已迁入 `docs/tasks/**`，不自动进入 implementation-ready |
| process | active | 过程记录进入 `EXECUTION_LOG.md` |
| governance | active | 规则入口保持 `AGENTS.md`、`docs/DOC_GOVERNANCE.md`、`docs/governance/**` |
| archive | separated | 归档材料不作为当前事实来源 |

## 3. 当前阻断

| blocker | impact | next action |
| --- | --- | --- |
| formal window not open | 不能生成 implementation packet 或进入实现 | 先完成文档与状态 gate |

## 4. 验证入口

```powershell
python -m tools.doc_governor.cli validate-state --input docs/governance/DOC_STATE.yaml
python -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml
git diff --check
```

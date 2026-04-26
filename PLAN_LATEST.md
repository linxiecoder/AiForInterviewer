# AI 模拟面试系统当前仓库执行计划

## 1. 文档定位

本文档是当前规划入口，只回答“当前怎么推进”。本文档不承载需求正文、设计正文、任务正文、执行日志或状态写回。

## 2. 当前规划事实

| domain | current entry | planning role |
| --- | --- | --- |
| requirements | `docs/requirements/workbench-mvp/**` | 输入范围、边界和验收口径 |
| design | `docs/design/workbench-mvp/**` | 输入设计约束和设计分解依据 |
| state truth | `docs/governance/DOC_STATE.yaml` | 判断正式状态、required docs 和 gate |
| execution plan | `docs/superpowers/plans/2026-04-25-current-repo-execution-plan.md` | 当前仓库执行顺序；路径被状态层引用，保持原位 |
| task remap | `docs/superpowers/plans/2026-04-25-workbench-mvp-task-remap.md` | Workbench MVP 任务重映射；路径被状态层引用，保持原位 |
| task docs | `docs/superpowers/plans/st13-task-packages/**` | ST13 当前任务双文档；路径被状态层引用，保持原位 |
| backlog | `docs/superpowers/plans/2026-04-25-workbench-mvp-backlog-roadmap.md` | 后续 backlog 与路线图 |

## 3. 当前阶段

当前仓库处于文档体系重构与任务开窗前置治理阶段。

当前阶段允许：

- 清理需求、设计、规划、任务、过程、治理、索引、归档职责边界。
- 创建或校准 Workbench MVP 需求层。
- 原地清理被状态层引用文档的过时措辞。
- 归档已完成且不再作为当前入口的过程文档。
- 运行只读状态验证和引用扫描。

当前阶段不允许：

- 修改 `docs/governance/DOC_STATE.yaml`。
- 打开 formal window。
- 生成 implementation packet。
- 进入业务代码实现。
- 提升 implementation readiness。

## 4. 下一步推进顺序

1. 完成文档体系重构和引用清理。
2. 人工 review 本轮 diff，确认职责分离没有误删事实。
3. 另开状态窗口处理仍被状态层锁定但目录职责不理想的任务文档。
4. 状态层允许后，再进入 formal window / implementation packet 的独立流程。

## 5. 验证入口

```powershell
python -m tools.doc_governor.cli validate-state --input docs/governance/DOC_STATE.yaml
python -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml
git diff --check
git status --short
```

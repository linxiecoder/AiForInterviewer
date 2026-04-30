---
title: 2026-04-25-workbench-mvp-state-write-stage2
type: note
permalink: ai-for-interviewer/archive/docs/superpowers/plans/2026-04-25/2026-04-25-workbench-mvp-state-write-stage2
---

# AI 模拟面试一期工作台 MVP State Write 阶段 2 变更与回退说明

> 本文档记录 `W13-E4-C / State Write 阶段 2` 的正式变更、验证结果与回退步骤。本阶段只表达旧 `STxx_*` 的 `historical-reference / superseded` 关系，不移出旧任务，不迁移 archive，不生成 implementation packet，不进入实现。

## 1. 背景

`W13-E4-B` 阶段 1 已将 `ST13_01~ST13_25` 写入正式 `docs/governance/DOC_STATE.yaml`，并将这些任务补入 `RQ01.facts.task_ids`。阶段 1 明确保留旧 `STxx_*`，不表达旧任务 superseded。

阶段 2 的输入来自：

- `docs/superpowers/plans/2026-04-25-workbench-mvp-task-remap.md`
- `docs/superpowers/plans/2026-04-25-workbench-mvp-doc-state-preview.yaml`
- `docs/superpowers/plans/2026-04-25-workbench-mvp-state-write-plan.md`
- `docs/superpowers/plans/2026-04-25-workbench-mvp-state-write-stage1.md`

## 2. 用户确认

用户已确认进入 `W13-E4-C`，采用方案 B：用 `DOC_STATE.yaml` 现有 `facts` 字段表达旧 `STxx_*` 已被 W13 新任务体系覆盖，标记为 `superseded / historical-reference`，不移出旧任务。

该确认不包含：

1. 移出旧 `STxx_*`。
2. 迁移旧 `STxx_*` 到 archive。
3. 删除旧 `STxx_*`。
4. 修改 schema。
5. 修改 `validate.py / evaluate.py`。
6. 生成 implementation packet。
7. 标记 implementation-ready。
8. 进入阶段 3。

## 3. 本阶段目标

1. 保留 30 个旧 `STxx_*` 在正式 `subtasks` 容器中。
2. 在每个旧 `STxx_*` 的 `facts` 下写入 `w13_status: superseded`。
3. 在每个旧 `STxx_*` 的 `facts` 下写入 `w13_role: historical-reference`。
4. 用 `w13_superseded_by` 指向对应 `ST13_*`。
5. 用 `w13_alias_target` 保留对应 `WT13-*` 任务域 alias。
6. 用 `w13_archive_candidate` 表达后续可作为 archive 候选，但本阶段不迁移。
7. 用 `w13_current_implementation_entry: false` 明确旧任务不是 W13 当前实施入口。

本阶段未使用 `covered_by` 字段；覆盖关系统一通过 `w13_superseded_by` 和 `w13_alias_target` 表达。

## 4. 本阶段明确不做

1. 不从 `DOC_STATE.yaml.subtasks` 删除旧 `STxx_*`。
2. 不修改旧 `STxx_*` 的路径。
3. 不移动 `docs/modules/**`。
4. 不写 archive。
5. 不修改 `tools/**`、`tests/**`、`apps/**`、`infra/**`。
6. 不新增 schema 字段或容器。
7. 不修改 closed round 历史引用。
8. 不打开 formal window。
9. 不生成 implementation packet。
10. 不进入代码实现。

## 5. facts 表达方式

每个旧 `STxx_*` 均写入以下字段：

```yaml
w13_status: superseded
w13_role: historical-reference
w13_superseded_by:
- ST13_xx
w13_alias_target:
- WT13-xx
w13_archive_candidate: true
w13_mapping_review_required: false
w13_current_implementation_entry: false
w13_retention_reason: 保留旧任务的状态层路径和历史证据，避免断开早期模块骨架追溯。
w13_notes: 旧任务仅作历史参考，当前 W13 任务以 ST13 / WT13 为准；本阶段不移出正式 subtasks 容器，不迁移 archive。
```

## 6. 旧 STxx 到 ST13 / WT13 映射清单

| 旧 ST ID | 旧 ST 所属模块 | 旧 ST 当前角色 | 历史信息价值 | 映射到 ST13 | 对应 WT13 alias | 映射理由 | 是否完整覆盖 | 是否 archive-candidate | 是否需要后续复核 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `ST01_01` | M01 | historical-reference / superseded | 运行环境与仓库基线历史骨架 | `ST13_20`、`ST13_21`、`ST13_24`、`ST13_25` | `WT13-20`、`WT13-21`、`WT13-24`、`WT13-25` | 被服务端保存、API 边界、测试验收和文档治理任务域覆盖 | 是 | 是 | 否 |
| `ST01_02` | M01 | historical-reference / superseded | 工作台壳层与 i18n 历史骨架 | `ST13_02`、`ST13_23` | `WT13-02`、`WT13-23` | 被工作台首页 / 导航与前端工作台页面集合覆盖 | 是 | 是 | 否 |
| `ST01_03` | M01 | historical-reference / superseded | 测试、日志与文档治理历史骨架 | `ST13_22`、`ST13_24`、`ST13_25` | `WT13-22`、`WT13-24`、`WT13-25` | 被日志观测、测试验收和文档治理收口覆盖 | 是 | 是 | 否 |
| `ST02_01` | M02 | historical-reference / superseded | 鉴权机制与会话边界历史入口 | `ST13_01`、`ST13_21` | `WT13-01`、`WT13-21` | 被账号登录权限与 API 后端服务边界覆盖 | 是 | 是 | 否 |
| `ST02_02` | M02 | historical-reference / superseded | 团队、用户与成员目录历史入口 | `ST13_01`、`ST13_21` | `WT13-01`、`WT13-21` | 被账号登录权限与 API 后端服务边界覆盖 | 是 | 是 | 否 |
| `ST02_03` | M02 | historical-reference / superseded | 授权矩阵与管理员 / 成员边界历史入口 | `ST13_01`、`ST13_22` | `WT13-01`、`WT13-22` | 被账号权限与日志审计 / 运维任务域覆盖 | 是 | 是 | 否 |
| `ST03_01` | M03 | historical-reference / superseded | 岗位域与页面历史入口 | `ST13_03`、`ST13_06`、`ST13_23` | `WT13-03`、`WT13-06`、`WT13-23` | 被岗位管理、发起模拟面试和前端页面集合覆盖 | 是 | 是 | 否 |
| `ST03_02` | M03 | historical-reference / superseded | 简历域、版本与编辑器历史入口 | `ST13_04`、`ST13_06`、`ST13_23` | `WT13-04`、`WT13-06`、`WT13-23` | 被简历管理、发起模拟面试和前端页面集合覆盖 | 是 | 是 | 否 |
| `ST03_03` | M03 | historical-reference / superseded | 上传、转换与导出链路历史入口 | `ST13_04`、`ST13_19`、`ST13_20` | `WT13-04`、`WT13-19`、`WT13-20` | 被简历管理、Markdown 导出和服务端保存覆盖 | 是 | 是 | 否 |
| `ST04_01` | M04 | historical-reference / superseded | 岗位-简历绑定与输入契约历史骨架 | `ST13_06`、`ST13_13`、`ST13_21` | `WT13-06`、`WT13-13`、`WT13-21` | 被发起模拟面试、评分体系和 API 边界覆盖 | 是 | 是 | 否 |
| `ST04_02` | M04 | historical-reference / superseded | 匹配分析、评分与证据历史骨架 | `ST13_13`、`ST13_16` | `WT13-13`、`WT13-16` | 被评分体系和薄弱项证据聚合覆盖 | 是 | 是 | 否 |
| `ST04_03` | M04 | historical-reference / superseded | 分析展示与训练入口历史骨架 | `ST13_17`、`ST13_23` | `WT13-17`、`WT13-23` | 被训练抽屉和前端工作台页面集合覆盖 | 是 | 是 | 否 |
| `ST05_01` | M05 | historical-reference / superseded | 资产类型与资产域历史骨架 | `ST13_18` | `WT13-18` | 被资产归档任务域覆盖 | 是 | 是 | 否 |
| `ST05_02` | M05 | historical-reference / superseded | 归档记录与来源追踪历史骨架 | `ST13_18`、`ST13_20` | `WT13-18`、`WT13-20` | 被资产归档和服务端保存覆盖 | 是 | 是 | 否 |
| `ST05_03` | M05 | historical-reference / superseded | 检索分块与索引入库历史骨架 | `ST13_10`、`ST13_20` | `WT13-10`、`WT13-20` | 被 RAG / 知识库和服务端保存覆盖 | 是 | 是 | 否 |
| `ST06_01` | M06 | historical-reference / superseded | 面试会话创建与列表历史骨架 | `ST13_05`、`ST13_06`、`ST13_07` | `WT13-05`、`WT13-06`、`WT13-07` | 被模拟记录列表、发起模拟面试和面试台覆盖 | 是 | 是 | 否 |
| `ST06_02` | M06 | historical-reference / superseded | 上下文包与问题来源规则历史骨架 | `ST13_06`、`ST13_07`、`ST13_10`、`ST13_11`、`ST13_12` | `WT13-06`、`WT13-07`、`WT13-10`、`WT13-11`、`WT13-12` | 被发起、面试台、RAG、LLM provider 和多轮状态机覆盖 | 是 | 是 | 否 |
| `ST06_03` | M06 | historical-reference / superseded | 消息 Trace、报告与导出历史骨架 | `ST13_12`、`ST13_15`、`ST13_19`、`ST13_22` | `WT13-12`、`WT13-15`、`WT13-19`、`WT13-22` | 被多轮状态机、模拟复盘、导出和日志观测覆盖 | 是 | 是 | 否 |
| `ST07_01` | M07 | historical-reference / superseded | 打磨主题推荐与启动历史骨架 | `ST13_08`、`ST13_16`、`ST13_17` | `WT13-08`、`WT13-16`、`WT13-17` | 被打磨模式、薄弱项和训练抽屉覆盖 | 是 | 是 | 否 |
| `ST07_02` | M07 | historical-reference / superseded | 能力树蓝图与节点状态历史骨架 | `ST13_08`、`ST13_16` | `WT13-08`、`WT13-16` | 被打磨模式和薄弱项覆盖 | 是 | 是 | 否 |
| `ST07_03` | M07 | historical-reference / superseded | 逐题评估与进度快照历史骨架 | `ST13_08`、`ST13_13`、`ST13_16`、`ST13_17` | `WT13-08`、`WT13-13`、`WT13-16`、`WT13-17` | 被打磨模式、评分体系、薄弱项和训练抽屉覆盖 | 是 | 是 | 否 |
| `ST08_01` | M08 | historical-reference / superseded | 复盘总对象与列表 / 详情历史骨架 | `ST13_14`、`ST13_15`、`ST13_18`、`ST13_19` | `WT13-14`、`WT13-15`、`WT13-18`、`WT13-19` | 被真实复盘、模拟复盘、资产归档和导出覆盖 | 是 | 是 | 否 |
| `ST08_02` | M08 | historical-reference / superseded | 真实面试导入与逐题分析历史骨架 | `ST13_14`、`ST13_16` | `WT13-14`、`WT13-16` | 被真实面试复盘和薄弱项覆盖 | 是 | 是 | 否 |
| `ST08_03` | M08 | historical-reference / superseded | 模拟面试复盘回放与导出历史骨架 | `ST13_15`、`ST13_18`、`ST13_19` | `WT13-15`、`WT13-18`、`WT13-19` | 被模拟面试复盘、资产归档和导出覆盖 | 是 | 是 | 否 |
| `ST09_01` | M09 | historical-reference / superseded | 薄弱项聚合与训练中心历史骨架 | `ST13_16` | `WT13-16` | 被薄弱项 `WeaknessItem` 覆盖 | 是 | 是 | 否 |
| `ST09_02` | M09 | historical-reference / superseded | 训练抽屉与待打磨入列历史骨架 | `ST13_17` | `WT13-17` | 被训练抽屉 / 待打磨清单覆盖 | 是 | 是 | 否 |
| `ST09_03` | M09 | historical-reference / superseded | 生命周期、消减与停练规则历史骨架 | `ST13_16`、`ST13_17` | `WT13-16`、`WT13-17` | 被薄弱项生命周期和训练抽屉覆盖 | 是 | 是 | 否 |
| `ST10_01` | M10 | historical-reference / superseded | 成员治理与角色操作历史骨架 | `ST13_01`、`ST13_22` | `WT13-01`、`WT13-22` | 被账号权限和日志 / 运维治理覆盖 | 是 | 是 | 否 |
| `ST10_02` | M10 | historical-reference / superseded | 模型目录、评分规则与系统设置历史骨架 | `ST13_11`、`ST13_13`、`ST13_22` | `WT13-11`、`WT13-13`、`WT13-22` | 被 LLM provider、评分体系和日志 / 运维覆盖 | 是 | 是 | 否 |
| `ST10_03` | M10 | historical-reference / superseded | 可观测性、CI/E2E 与 snapshot 运维历史骨架 | `ST13_22`、`ST13_24`、`ST13_25` | `WT13-22`、`WT13-24`、`WT13-25` | 被日志观测、测试验收和文档治理收口覆盖 | 是 | 是 | 否 |

本阶段没有无法明确映射到 `ST13_*` 的旧任务；因此没有新增人工复核清单。

## 7. DOC_STATE.yaml facts 写入摘要

已修改 `docs/governance/DOC_STATE.yaml` 中 30 个旧 `STxx_*` 的 `facts`：

- `w13_status=superseded`：标记旧任务已被 W13 新任务覆盖。
- `w13_role=historical-reference`：标记旧任务只保留历史参考角色。
- `w13_superseded_by`：记录对应 `ST13_*`。
- `w13_alias_target`：记录对应 `WT13-*`。
- `w13_archive_candidate=true`：记录后续可作为 archive 候选。
- `w13_current_implementation_entry=false`：明确旧任务不是当前 W13 实施入口。

未修改：

- `meta.path`
- `state.confirmed`
- `legacy_locked`
- `design_doc`
- `implementation_doc`
- closed round 历史记录
- `ST13_01~ST13_25`
- `RQ01.facts.task_ids`

## 8. TASK_INDEX.md 同步摘要

`TASK_INDEX.md` 应同步表达：

1. 旧 `STxx_*` 仍在索引和正式状态层中保留。
2. 旧 `STxx_*` 已通过 `DOC_STATE.yaml.facts` 表达 historical / superseded。
3. 当前 W13 正式状态层入口仍是 `ST13_01~ST13_25`，文档层任务域 alias 仍是 `WT13-01~WT13-25`。
4. 旧 `STxx_*` 不再作为 W13 当前实现入口。
5. 仍不能进入 implementation-ready。

## 9. MODULE_INDEX.md 同步摘要

`MODULE_INDEX.md` 应同步表达：

1. 各模块旧 `STxx_*` 仍保留历史参考角色。
2. 模块成熟度不因旧任务 historical / superseded 写入而升级。
3. 后续模块窗口仍应以 W13 四份事实源和 `WT13 / ST13` 映射为输入。
4. 不得把旧 `STxx_*` 重新激活为模块实施入口。

## 10. 预期 blocker

阶段 2 不应新增 schema error、missing reference、stale target、formal window 误开或 implementation-ready 误判。

可接受 blocker：

- `formal_window_closed`
- `implementation_doc_not_active`
- `missing_required_doc_slot`
- `implementation_scope_unclear`
- `acceptance_criteria_missing`
- `required_tests_missing`
- `template_like_required_doc_slot`
- `upstream_module_not_ready`
- `language_non_compliant`

这些 blocker 仍表示任务尚未进入实施准备，不代表阶段 2 失败。

## 11. 实际验证结果

写入后正式状态层验证结果：

| 命令 | 结果 |
| --- | --- |
| `python -m tools.doc_governor.cli validate-state --input docs/governance/DOC_STATE.yaml` | `ok=true, error=0, warning=0` |
| `python -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml` | `ok=true, error=0, warning=0` |

`evaluate-state` 摘要：

| 指标 | 结果 |
| --- | ---: |
| `documents_blocked_count` | 0 |
| `modules_blocked_count` | 1 |
| `subtasks_blocked_count` | 55 |

结构检查：

- `ST13_01~ST13_25` 仍存在。
- 30 个旧 `STxx_*` 仍存在。
- 30 个旧 `STxx_*` 均写入 `w13_status=superseded`。
- 30 个旧 `STxx_*` 均写入 `w13_role=historical-reference`。
- 30 个旧 `STxx_*` 均写入 `w13_superseded_by` 与 `w13_alias_target`。
- 未发生回退。

## 12. 不可接受 blocker 检查

本阶段未发现：

1. schema error。
2. missing reference。
3. stale target。
4. 旧任务路径被改写。
5. `ST13_*` 被破坏。
6. `RQ01.facts.task_ids` 被破坏。
7. 任一任务被误判 `implementation_ready=true`。
8. formal window 被误开。
9. archive 路径被误作当前事实源。

## 13. 回退步骤

如需回退阶段 2，只撤销本阶段写入，不影响阶段 1 的 `ST13_01~ST13_25`：

1. 在 `docs/governance/DOC_STATE.yaml` 中删除 30 个旧 `STxx_*` 的以下 facts：
   - `w13_status`
   - `w13_role`
   - `w13_superseded_by`
   - `w13_alias_target`
   - `w13_archive_candidate`
   - `w13_mapping_review_required`
   - `w13_current_implementation_entry`
   - `w13_retention_reason`
   - `w13_notes`
2. 保留 `ST13_01~ST13_25`。
3. 保留 `RQ01.facts.task_ids` 中的 `ST13_01~ST13_25`。
4. 将 `TASK_INDEX.md` 中“阶段 2 已完成 / 旧 ST 已 facts historical / superseded”文字恢复为“阶段 2 待执行”。
5. 将 `MODULE_INDEX.md` 中“旧 ST 已 facts historical / superseded”文字恢复为“旧 ST 仍待状态层窗口处理”。
6. 将 `PLAN_LATEST.md`、`DOCUMENT_PROGRESS.md`、`DOCUMENT_MATURITY.md`、`OPEN_QUESTIONS.md`、`DESIGN_DECISIONS.md` 和 `EXECUTION_LOG.md` 中阶段 2 完成描述恢复为待执行描述。
7. 不删除 W13 四份事实源、task-remap、Preview YAML、State Write 分阶段计划或 Stage 1 说明。

## 14. 回退成功判断

回退后必须满足：

1. `ST13_01~ST13_25` 仍存在。
2. 30 个旧 `STxx_*` 仍存在。
3. 旧 `STxx_*` 不再包含阶段 2 写入的 `w13_*` facts。
4. `RQ01.facts.task_ids` 未破坏。
5. `TASK_INDEX.md` 和 `MODULE_INDEX.md` 不再宣称阶段 2 已完成。
6. 正式验证命令仍为：
   - `validate-state ok=true, error=0, warning=0`
   - `evaluate-state ok=true, error=0, warning=0`
   - `documents_blocked_count=0`
   - `modules_blocked_count=1`
   - `subtasks_blocked_count=55`

## 15. 后续阶段 3 输入

阶段 3 只能在用户另行确认后进入。阶段 3 的输入是：

1. 阶段 1 已写入 `ST13_01~ST13_25`。
2. 阶段 2 已表达旧 `STxx_*` historical / superseded。
3. `TASK_INDEX.md` 与 `MODULE_INDEX.md` 已同步旧任务历史参考角色。
4. `validate-state / evaluate-state` 均为 `ok=true, error=0, warning=0`。
5. 无 implementation-ready 误判。
6. 无 formal window 误开。

阶段 3 仍不是 archive 迁移；它只讨论是否将旧 `STxx_*` 移出正式任务容器并保留历史引用。

## 16. 当前仍不能实现说明

阶段 2 完成后仍不能进入实现，原因是：

1. `ST13_01~ST13_25` 仍缺少实施级子任务双文档和 implementation packet 输入。
2. `formal_window_open=false`。
3. `evaluate-state` 仍显示 `subtasks_blocked_count=55`。
4. 旧 `STxx_*` 虽已 historical / superseded，但仍留在正式 `subtasks` 容器中。
5. 阶段 3 尚未执行。
6. archive 迁移尚未执行。
7. 未明确任何允许修改代码路径、验证命令或 DoD 的实施包。

结论：本阶段最多允许进入 `W13-E4-D / 阶段 3` 的确认或审计窗口；不能进入业务代码实现窗口。

后续注记：`W13-E4-D` 已完成阶段 3 dry-run / 影响分析，并新增 `docs/superpowers/plans/2026-04-25-workbench-mvp-state-write-stage3-dry-run.md`。正式阶段 3 仍未执行，旧 `STxx_*` 仍未移出正式 `subtasks` 容器，下一步建议先创建 Stage3 Preview YAML。
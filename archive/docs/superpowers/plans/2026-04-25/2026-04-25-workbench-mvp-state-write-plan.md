---
title: 2026-04-25-workbench-mvp-state-write-plan
type: note
permalink: ai-for-interviewer/archive/docs/superpowers/plans/2026-04-25/2026-04-25-workbench-mvp-state-write-plan
---

# AI 模拟面试一期工作台 MVP State Write 分阶段计划

> 本文档是 `W13-E4-A / State Write 分阶段计划、测试矩阵与回退方案` 的正式计划产物。`W13-E4-B` 已按本计划执行阶段 1：写入 `ST13_01~ST13_25`，保留旧 `STxx_*`；`W13-E4-C` 已执行阶段 2：用旧任务 facts 表达 `historical-reference / superseded`；`W13-E4-D` 已完成阶段 3 dry-run / 影响分析；`W13-E4-E` 已创建并验证 Stage3 Preview YAML；`W13-E4-F` 已执行正式 Stage 3，将旧 `STxx_*` 从 formal current `subtasks` 容器移出，并将 `RQ01.facts.task_ids` 收敛为 `ST13_01~ST13_25`。本文档仍不生成 implementation packet，不放行实现。

## 1. 背景

用户已确认采用方案 C 的分阶段版本：最终要把 `ST13_01~ST13_25` 写入正式 `DOC_STATE.yaml`，并把旧 `STxx_*` 标记为 `superseded` 或移出正式任务容器，但不能一次性粗暴切换。

本窗口边界固定为：

1. `W13-E4-A` 默认不修改 `docs/governance/DOC_STATE.yaml`；`W13-E4-B` 阶段 1 已按用户确认修改正式状态层。
2. 不写代码，不修改 `tools/**`、`tests/**`，不创建 `apps/**` 或 `infra/**`。
3. 不执行 Git 提交、推送或任何破坏性 Git 操作。
4. 不生成 implementation packet。
5. 阶段 3 已由 `W13-E4-F` 按用户确认执行；阶段 4 仍必须等待后续窗口再次确认。

`W13-E4-B` 执行注记：用户已确认 `OQ-094=B`、`OQ-095` 阶段 1 方案 C / 阶段 2 方案 B、`OQ-096=B`。阶段 1 已新增 `docs/superpowers/plans/2026-04-25-workbench-mvp-state-write-stage1.md` 记录变更与回退说明，旧 `STxx_*` 未移除、未改写、未标记 superseded。

`W13-E4-C` 执行注记：用户已确认进入阶段 2 并采用方案 B。阶段 2 已新增 `docs/superpowers/plans/2026-04-25-workbench-mvp-state-write-stage2.md`，并在 30 个旧 `STxx_*` 的 `facts` 中写入 `w13_status=superseded`、`w13_role=historical-reference`、`w13_superseded_by` 与 `w13_alias_target`。阶段 2 完成时旧任务仍未移出正式容器，未迁移 archive；后续 `W13-E4-F` 已执行正式移出。

`W13-E4-E` 执行注记：已新增 `docs/superpowers/plans/2026-04-25-workbench-mvp-doc-state-stage3-preview.yaml`，并在 preview 中验证 `subtasks` 只保留 `ST13_01~ST13_25`、`RQ01.facts.task_ids` 只保留 `ST13_01~ST13_25` 后仍保持 `validate-state / evaluate-state` 绿灯。正式 `DOC_STATE.yaml` 未修改；是否执行正式 Stage 3 仍需用户确认。

`W13-E4-F` 执行注记：用户已确认 `OQ-100` 方案 B。正式 Stage 3 已将 `DOC_STATE.yaml.subtasks` 收敛为 `ST13_01~ST13_25`，并从正式 `RQ01.facts.task_ids` 移除旧 `ST01_01`、`ST09_03`。新增 `docs/superpowers/plans/2026-04-25-workbench-mvp-state-write-stage3.md` 记录变更与回退说明；未迁移 archive，未生成 implementation packet，未放行实现。

## 2. W13-E3 Preview 结果摘要

本轮开始前已验证：

```powershell
python -m tools.doc_governor.cli validate-state --input docs/governance/DOC_STATE.yaml
python -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml
python -m tools.doc_governor.cli validate-state --input docs/superpowers/plans/2026-04-25-workbench-mvp-doc-state-preview.yaml
python -m tools.doc_governor.cli evaluate-state --input docs/superpowers/plans/2026-04-25-workbench-mvp-doc-state-preview.yaml
```

结果摘要：

1. 正式 `DOC_STATE.yaml`：`ok=true, error=0, warning=0`。
2. 正式 `DOC_STATE.yaml`：`requirements=1, modules=10, subtasks=30, documents=1`。
3. 正式 `evaluate-state`：`documents_blocked_count=0, modules_blocked_count=1, subtasks_blocked_count=30`。
4. Preview YAML：`ok=true, error=0, warning=0`。
5. Preview YAML：`requirements=1, modules=10, subtasks=55`。
6. Preview YAML：`ST13_01~ST13_25` 作为 `WT13-01~WT13-25` 的状态层兼容 alias。
7. Preview YAML：30 个旧 `STxx_*` 在各自 `facts.w13_superseded_preview` 中保留 superseded preview 信息，`formal_doc_state_write=false, archive_move=false`。
8. Preview YAML：`subtasks_blocked_count=55` 是预期结构预览结果，不代表失败，也不代表 implementation-ready。
9. 正式 `global_policy.formal_window_open=false`，后续不得绕过 formal window gate。

## 3. C-Phased 策略

用户已确认的高层策略是 `C-Phased`：

1. 最终目标是正式状态层承载 W13 新任务。
2. 旧 `STxx_*` 不直接删除，不直接迁移 archive。
3. 先建立新任务入口，再表达旧任务历史化，再解除正式任务容器引用，最后设计 archive 迁移。
4. 每阶段必须保持 `validate-state / evaluate-state` 为 `ok=true, error=0, warning=0`。
5. 每阶段不得新增无法解释的 blocker，不得破坏已关闭 round、`TASK_INDEX.md`、`MODULE_INDEX.md` 或模块索引追溯链。

## 4. 分阶段 State Write 计划

### 4.1 阶段 1：写入 `ST13_01~ST13_25`，不移除旧 `STxx_*`

1. 修改目标：
   - 将 Preview 中的 `ST13_01~ST13_25` 写入正式 `DOC_STATE.yaml.subtasks`。
   - 将 `ST13_01~ST13_25` 加入 `requirements.RQ01.facts.task_ids`。
   - 保留旧 `STxx_*`，避免任务索引、模块索引和历史 round 断链。
2. 修改文件：
   - 后续 `W13-E4-B` 只应修改 `docs/governance/DOC_STATE.yaml`。
   - 如需同步说明，可只更新计划类文档，不触碰模块目录。
3. 不修改文件：
   - 不修改 `TASK_INDEX.md`、`MODULE_INDEX.md`、`docs/modules/**`、`archive/**`、`tools/**`、`tests/**`、`apps/**`、`infra/**`。
4. 预期 `validate-state`：
   - `ok=true, error=0, warning=0`。
   - `subtasks` 计数从 30 增加到 55。
   - 不出现 schema error、unknown enum、missing relation、typed blocker ref 错误。
5. 预期 `evaluate-state`：
   - `ok=true, error=0, warning=0`。
   - `subtasks_blocked_count` 预计从 30 增加到 55。
   - `implementation_ready` 仍全部为 `false`。
   - `formal_window_open` 仍不得误判为打开。
6. 可能新增 blocker：
   - `missing_required_doc_slot`
   - `acceptance_criteria_missing`
   - `required_tests_missing`
   - `implementation_scope_unclear`
   - `implementation_doc_not_active`
   - `formal_window_closed`
   这些 blocker 只表示尚未进入实施，不是 schema 失败。
7. 可接受 blocker：
   - 因 `ST13_*` 只有状态层入口、尚无子任务双文档和 implementation packet 输入而产生的 blocker。
   - 因 `formal_window_open=false` 产生的 blocker。
8. 不可接受 blocker：
   - `SCHEMA_*` error。
   - `missing reference`。
   - stale target 指向 archive 或不存在路径。
   - 任一 `ST13_*` 被推成 `implementation_ready=true`。
   - 任一 `ST13_*` 被误判为 `formal_window_open=true`。
9. 回退方案：
   - 从 `DOC_STATE.yaml.subtasks` 删除本阶段新增的 `ST13_01~ST13_25`。
   - 从 `requirements.RQ01.facts.task_ids` 删除 `ST13_01~ST13_25`。
   - 保留 Preview YAML 和 W13 四份事实源不变。
   - 回退后重新运行正式 `validate-state / evaluate-state`，期望恢复到 `subtasks=30`、`subtasks_blocked_count=30`。
10. 是否需要用户确认：
   - 需要。推荐由确认卡 1 选择方案 B 后执行。
11. 是否可进入下一阶段：
   - 只有当正式状态和索引链验证全部通过，且无 implementation-ready 误判时，才可进入阶段 2。

### 4.2 阶段 2：旧 `STxx_*` 标记为 `superseded / historical-reference`

执行状态：`W13-E4-C` 已完成。阶段 2 只写入旧任务 facts 和同步索引文档；未进入阶段 3，未移动旧任务，未迁移 archive。

1. 修改目标：
   - 在正式状态层表达旧 `STxx_*` 已被 W13 新任务覆盖。
   - 仍不移出旧 `STxx_*`，不移动文件，不迁移 archive。
2. 修改文件：
   - 优先只修改 `docs/governance/DOC_STATE.yaml` 中旧 `STxx_*` 的 `facts`。
   - 可选同步 `TASK_INDEX.md / MODULE_INDEX.md / task-remap` 的文字状态，但需另行确认允许范围。
3. 不修改文件：
   - 不修改 `docs/modules/**` 和 `archive/**`。
   - 不修改 `tools/**`、`tests/**`。
4. 预期 `validate-state`：
   - `ok=true, error=0, warning=0`。
   - 旧任务仍是合法 `STxx_yy` key。
5. 预期 `evaluate-state`：
   - `ok=true, error=0, warning=0`。
   - 旧任务不应被误读为当前 W13 实现任务。
   - blocker 数量可能仍包含旧任务，因为旧任务仍在正式容器中。
6. 可能新增 blocker：
   - 不应新增新的实现 blocker；若 evaluate 忽略 facts 中的 `w13_superseded_preview`，blocked count 可能不变。
7. 可接受 blocker：
   - 旧任务仍因正式容器存在而保留原有 blocker。
   - `formal_window_closed` 继续存在。
8. 不可接受 blocker：
   - 因新增字段导致 schema error。
   - 因 superseded 表达导致旧任务 requirement relation 断裂。
   - 旧任务被误判为 ready 或可开窗。
9. 回退方案：
   - 删除旧 `STxx_*` 中本阶段新增或修改的 superseded / historical-reference 字段。
   - 保留 `ST13_*` 阶段 1 写入结果不变。
   - 重新运行正式 `validate-state / evaluate-state`。
10. 是否需要用户确认：
   - 需要。推荐阶段 1 绿灯后再确认阶段 2。
11. 是否可进入下一阶段：
   - 只有当旧任务 superseded 表达不引入 schema error、不破坏索引追溯时，才可进入阶段 3。

### 4.3 阶段 3：旧 `STxx_*` 移出正式任务容器

当前执行状态：`W13-E4-F` 已完成正式 Stage 3。正式 `DOC_STATE.yaml.subtasks` 当前只保留 `ST13_01~ST13_25`，正式 `RQ01.facts.task_ids` 当前只保留 `ST13_01~ST13_25`。旧 `STxx_*` 仍保留为历史参考、reusable evidence 和 archive candidate，不得误读为 archive 迁移完成或 implementation-ready。

1. 修改目标：
   - 让正式 `subtasks` 容器只承载 W13 新任务。
   - 旧 `STxx_*` 进入历史引用、closed 记录或 superseded 容器表达，但不丢失追溯性。
2. 修改文件：
   - `DOC_STATE.yaml` 是核心改动对象。
   - 可能需要同步 `TASK_INDEX.md`、`MODULE_INDEX.md` 和 task-remap，但必须另开允许这些文件的状态清理窗口。
3. 不修改文件：
   - 不移动 `docs/modules/**`。
   - 不迁移 `archive/**`。
4. 预期 `validate-state`：
   - `ok=true, error=0, warning=0`。
   - 不出现 missing relation，尤其是 `requirements.RQ01.facts.task_ids` 不得继续引用已移出的旧 `STxx_*`。
5. 预期 `evaluate-state`：
   - `ok=true, error=0, warning=0`。
   - `subtasks_blocked_count` 不再被旧 `STxx_*` 主导。
   - W13 新任务仍因未开窗、未补双文档而 blocked。
6. 可能新增 blocker：
   - 若 relation 清理不完整，可能出现 missing reference；这是不可接受 blocker，应立即回退。
7. 可接受 blocker：
   - W13 新任务的 missing docs / formal window closed 等 blocker。
8. 不可接受 blocker：
   - closed round 目标文档或 evidence ref 断裂。
   - `TASK_INDEX.md / MODULE_INDEX.md` 仍把移出的旧任务写成当前正式任务。
   - archive 路径被误作为当前事实源。
9. 回退方案：
   - 把旧 `STxx_*` 原样恢复到 `DOC_STATE.yaml.subtasks`。
   - 恢复 `requirements.RQ01.facts.task_ids` 到阶段 2 的安全状态。
   - 恢复 `TASK_INDEX.md / MODULE_INDEX.md / task-remap` 中本阶段涉及旧任务移出语义的文字。
   - 重新运行正式 `validate-state / evaluate-state`，并复查 closed round。
10. 是否需要用户确认：
   - 已由 `OQ-100` 确认方案 B，并由 `W13-E4-F` 执行完成；后续 archive 迁移仍需另行确认。
11. 是否可进入下一阶段：
   - 只有旧任务引用解除后仍可追溯，且 `subtasks_blocked_count` 可解释，才可进入阶段 4。

### 4.4 阶段 4：旧 `STxx_*` archive 迁移准备

1. 修改目标：
   - 在状态层和索引引用解除后，评估旧 `STxx_*` 是否迁入 `archive/docs/modules/**`。
   - 本阶段只设计，不迁移。
2. 修改文件：
   - 计划上只更新 archive 迁移方案、引用清单和风险清单。
3. 不修改文件：
   - 不移动 `docs/modules/**`。
   - 不创建或修改 `archive/**`。
4. 预期 `validate-state`：
   - 不应因 archive 迁移准备发生变化。
5. 预期 `evaluate-state`：
   - 不应因 archive 迁移准备发生变化。
6. 可能新增 blocker：
   - 无。若出现 blocker，说明阶段 4 错误地触碰了正式状态或索引。
7. 可接受 blocker：
   - 仅保留 W13 新任务尚未 implementation-ready 的既有 blocker。
8. 不可接受 blocker：
   - archive 路径被视为当前事实源。
   - 旧 `STxx_*` 历史引用丢失。
9. 回退方案：
   - 删除或撤销本阶段新增的 archive 迁移计划文字。
   - 不触碰 W13 四份事实源、Preview YAML 或正式状态。
10. 是否需要用户确认：
   - 需要。archive 迁移必须单独确认。
11. 是否可进入下一阶段：
   - 本阶段之后才能另开 Archive Cleanup 窗口；仍不能自动进入实现。

## 5. 验证矩阵

每一阶段均按以下矩阵验证，不使用复杂表格：

### 5.1 阶段 1 验证

1. 运行正式 `validate-state`，结果必须 `ok=true, error=0, warning=0`。
2. 运行正式 `evaluate-state`，结果必须 `ok=true, error=0, warning=0`。
3. 记录 `documents_blocked_count`，预期仍为 `0`。
4. 记录 `modules_blocked_count`，预期仍可解释，当前基线为 `1`。
5. 记录 `subtasks_blocked_count`，预期从 `30` 增至 `55`，且新增 25 个 blocker 都来自 `ST13_*` 未开窗 / 未补双文档。
6. 检查无 schema error。
7. 检查无 missing reference。
8. 检查无 stale target。
9. 检查没有 `implementation_ready=true`。
10. 检查没有 `formal_window_open=true` 误判。
11. 检查 `TASK_INDEX.md` 仍能定位 `WT13-01~WT13-25` 候选任务域。
12. 检查 `MODULE_INDEX.md` 仍能定位模块到 `WT13` 的候选映射。
13. 检查模块索引仍能追溯旧 `STxx_*` 为 state-bound 历史结构。
14. 检查 `ST13_01~ST13_25` 均存在于正式 `DOC_STATE.yaml.subtasks`。
15. 检查每个 `ST13_*` 的 `facts.w13_preview.wt13_id` 均存在。
16. 检查旧 `STxx_*` 尚未要求 superseded 映射写入。
17. 检查 archive 路径未被误作为当前事实源。
18. 检查 closed round `R-2026-04-22-SPECPLAN-01` 未被破坏。

### 5.2 阶段 2 验证

1. 运行正式 `validate-state`。
2. 运行正式 `evaluate-state`。
3. 记录 `documents_blocked_count`，不得新增 document blocker。
4. 记录 `modules_blocked_count`，不得出现无法解释变化。
5. 记录 `subtasks_blocked_count`，允许不下降，但必须能解释旧任务仍在容器中。
6. 检查无 schema error。
7. 检查无 missing reference。
8. 检查无 stale target。
9. 检查没有旧 `STxx_*` 进入 `implementation_ready=true`。
10. 检查没有旧 `STxx_*` 进入 formal window open。
11. 检查 `TASK_INDEX.md` 仍引用正确。
12. 检查 `MODULE_INDEX.md` 仍引用正确。
13. 检查模块索引仍能追溯旧 `STxx_*`。
14. 检查 `ST13_01~ST13_25` 仍能定位。
15. 检查 `WT13` alias 仍保留。
16. 检查 30 个旧 `STxx_*` 均具备 superseded 或 historical-reference 映射。
17. 检查 archive 路径未被误作为当前事实源。
18. 检查 closed round 历史引用未被破坏。

### 5.3 阶段 3 验证

1. 运行正式 `validate-state`。
2. 运行正式 `evaluate-state`。
3. 记录 `documents_blocked_count`。
4. 记录 `modules_blocked_count`。
5. 记录 `subtasks_blocked_count`，预期不再由旧 `STxx_*` 主导。
6. 检查无 schema error。
7. 检查无 missing reference，尤其是 requirement `task_ids`。
8. 检查无 stale target。
9. 检查没有 W13 新任务进入 `implementation_ready=true`。
10. 检查没有 formal window open 误判。
11. 检查 `TASK_INDEX.md` 不把已移出的旧任务写作当前正式任务。
12. 检查 `MODULE_INDEX.md` 不把已移出的旧任务写作当前正式任务。
13. 检查模块索引仍能通过历史段落追溯旧 `STxx_*`。
14. 检查 `ST13_01~ST13_25` 均能定位。
15. 检查 `WT13` alias 仍保留。
16. 检查旧 `STxx_*` superseded 映射仍可读。
17. 检查 archive 路径未被误作为当前事实源。
18. 检查 closed round 历史引用未被破坏。

### 5.4 阶段 4 验证

1. 运行正式 `validate-state`，确认 archive 准备文档未改变正式状态。
2. 运行正式 `evaluate-state`，确认没有新增 blocker。
3. 记录 `documents_blocked_count`。
4. 记录 `modules_blocked_count`。
5. 记录 `subtasks_blocked_count`。
6. 检查无 schema error。
7. 检查无 missing reference。
8. 检查无 stale target。
9. 检查没有 implementation-ready 误判。
10. 检查没有 formal_window_open 误判。
11. 检查 `TASK_INDEX.md` 引用正确。
12. 检查 `MODULE_INDEX.md` 引用正确。
13. 检查模块索引仍能追溯旧 `STxx_*`。
14. 检查 `ST13_01~ST13_25` 仍能定位。
15. 检查 `WT13` alias 仍保留。
16. 检查旧 `STxx_*` superseded 映射仍保留。
17. 检查 archive 路径仍未被误作为当前事实源。
18. 检查 closed round 历史引用未被破坏。

## 6. 验证命令清单

基础命令：

```powershell
python -m tools.doc_governor.cli validate-state --input docs/governance/DOC_STATE.yaml
python -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml
```

Preview 对照命令：

```powershell
python -m tools.doc_governor.cli validate-state --input docs/superpowers/plans/2026-04-25-workbench-mvp-doc-state-preview.yaml
python -m tools.doc_governor.cli evaluate-state --input docs/superpowers/plans/2026-04-25-workbench-mvp-doc-state-preview.yaml
```

关键词回归命令：

```powershell
rg -n "W13-E4|State Write|C-Phased|ST13_01|ST13_25|WT13|superseded|historical-reference|DOC_STATE|preview|dry-run|回退|验证矩阵|implementation-ready|确认卡|自定义方案" PLAN_LATEST.md EXECUTION_LOG.md DOCUMENT_PROGRESS.md DOCUMENT_MATURITY.md OPEN_QUESTIONS.md DESIGN_DECISIONS.md AGENTS.md docs/superpowers/plans
```

建议用于后续 State Write 窗口的结构检查命令：

```powershell
rg -n "ST13_01|ST13_25|w13_preview|wt13_id|w13_superseded_preview|formal_doc_state_write|archive_move" docs/governance/DOC_STATE.yaml docs/superpowers/plans/2026-04-25-workbench-mvp-doc-state-preview.yaml
rg -n "WT13-01|WT13-25|ST13_01|ST13_25|superseded|historical-reference" TASK_INDEX.md MODULE_INDEX.md docs/superpowers/plans/2026-04-25-workbench-mvp-task-remap.md
```

## 7. 回退方案

### 7.1 阶段 1 回退

1. 撤销 `DOC_STATE.yaml` 改动：
   - 删除 `subtasks.ST13_01~subtasks.ST13_25`。
   - 删除 `requirements.RQ01.facts.task_ids` 中的 `ST13_01~ST13_25`。
2. 恢复 `TASK_INDEX.md`：
   - 阶段 1 原则上不改 `TASK_INDEX.md`；若后续窗口实际改动，只撤销与阶段 1 正式写入状态直接相关的状态描述，不撤销 W13 候选任务树历史记录。
3. 恢复 `MODULE_INDEX.md`：
   - 阶段 1 原则上不改 `MODULE_INDEX.md`；若后续窗口实际改动，只撤销与阶段 1 正式写入状态直接相关的状态描述。
4. 恢复 task-remap 文档：
   - 保留 W13-E / W13-E2 / W13-E3 草案与 Preview 结论；只撤销“已正式写入”的阶段 1 表述。
5. 保留 W13 事实源不受影响：
   - 四份 W13 唯一事实源不回退。
6. 处理 preview 文件：
   - Preview YAML 保留，继续作为阶段 1 复盘证据。
7. 判断回退成功：
   - 正式 `DOC_STATE.yaml` 回到 `subtasks=30`。
   - `evaluate-state` 回到 `subtasks_blocked_count=30`，且 `error=0, warning=0`。
8. 回退后验证：
   - 运行正式 `validate-state`。
   - 运行正式 `evaluate-state`。
   - 运行关键词回归，确认没有“阶段 1 已正式写入”的残留误导。

### 7.2 阶段 2 回退

1. 撤销 `DOC_STATE.yaml` 改动：
   - 删除旧 `STxx_*` 中本阶段新增的 superseded / historical-reference 字段。
   - 保留阶段 1 的 `ST13_*` 正式写入结果。
2. 恢复 `TASK_INDEX.md`：
   - 若阶段 2 同步索引，只撤销“状态层已正式 superseded”的文字，不撤销候选映射草案。
3. 恢复 `MODULE_INDEX.md`：
   - 只撤销“状态层已正式 superseded”的文字。
4. 恢复 task-remap 文档：
   - 保留旧 `STxx_* -> WT13` 映射草案；撤销“正式状态层已完成 superseded”的表述。
5. 保留 W13 事实源不受影响。
6. 处理 preview 文件：
   - Preview YAML 保留，不改。
7. 判断回退成功：
   - 旧 `STxx_*` 回到阶段 1 状态。
   - `validate-state / evaluate-state` 仍为绿灯。
8. 回退后验证：
   - 运行正式 `validate-state`。
   - 运行正式 `evaluate-state`。
   - 复查 30 个旧 `STxx_*` 仍可定位。

### 7.3 阶段 3 回退

1. 撤销 `DOC_STATE.yaml` 改动：
   - 恢复旧 `STxx_*` 到 `subtasks` 容器。
   - 恢复 requirement relation 到阶段 2 的一致状态。
2. 恢复 `TASK_INDEX.md`：
   - 恢复旧 `STxx_*` 的历史 / state-bound 追溯段落，不把它们误写为当前正式任务。
3. 恢复 `MODULE_INDEX.md`：
   - 恢复旧 `STxx_*` 的模块追溯说明。
4. 恢复 task-remap 文档：
   - 撤销“旧 `STxx_*` 已移出正式容器”的表述，保留“计划移出”的设计。
5. 保留 W13 事实源不受影响。
6. 处理 preview 文件：
   - Preview YAML 保留。
7. 判断回退成功：
   - 旧任务容器与关系重新一致。
   - closed round 仍可在 evaluate 输出中完整读取。
8. 回退后验证：
   - 运行正式 `validate-state`。
   - 运行正式 `evaluate-state`。
   - 复查 `TASK_INDEX.md / MODULE_INDEX.md`。

### 7.4 阶段 4 回退

1. 撤销本阶段计划文字或 archive 准备清单。
2. 不撤销 W13 四份事实源。
3. 不撤销 `ST13_*` 状态层结果。
4. 不改 Preview YAML。
5. 判断回退成功：
   - 正式状态无变化。
   - archive 路径未被写成当前事实源。
6. 回退后验证：
   - 运行正式 `validate-state`。
   - 运行正式 `evaluate-state`。
   - 关键词复扫 archive / current fact source 表述。

## 8. `ST13_01~ST13_25` 正式写入草案

正式写入位置：

1. `DOC_STATE.yaml.subtasks.ST13_01~ST13_25`。
2. `DOC_STATE.yaml.requirements.RQ01.facts.task_ids`。
3. 不写入 `documents`。
4. 不直接打开 `global_policy.formal_window_open`。

初始状态建议：

1. `state.confirmed.candidate_status=none`。
2. `state.confirmed.review_status=unreviewed`。
3. `state.confirmed.readiness=blocked`。
4. `state.confirmed.implementation_doc_state=missing`。
5. `state.confirmed.blocker_refs=[]`，除非后续 confirm 工具要求显式 blocker ref。
6. `facts.w13_preview.implementation_ready=false`。
7. `facts.w13_preview.formal_doc_state_write=true` 仅在实际写入正式 `DOC_STATE.yaml` 的后续窗口中设置；Preview 文件保持 `false`。

为什么不能直接 implementation-ready：

1. `formal_window_open=false`。
2. `ST13_*` 尚无子任务双文档目录和 `SUBTASK_DESIGN.md / SUBTASK_IMPLEMENTATION.md`。
3. `allowed_modify_paths`、`required_tests`、`acceptance_criteria` 尚未形成可执行任务包。
4. W13 四份事实源可作为下游设计输入，但不等于单个子任务的实施说明。
5. 正式 implementation packet 只能在 evaluate 判定 `implementation_ready=true` 后生成。

逐项草案：

1. `ST13_01` -> `WT13-01`，模块 `M01`，上游模块 `M01 / M02 / M10`，主题：账号 / 登录 / 权限，事实源：范围、IA、对象模型、task-remap，初始状态：blocked，不 implementation-ready。
2. `ST13_02` -> `WT13-02`，模块 `M01`，上游模块 `M01 / M02 / M10`，主题：工作台首页 / 导航 / 权限入口，事实源：范围、IA、task-remap，初始状态：blocked。
3. `ST13_03` -> `WT13-03`，模块 `M03`，上游模块 `M03 / M04`，主题：岗位管理，事实源：范围、IA、对象模型、task-remap，初始状态：blocked。
4. `ST13_04` -> `WT13-04`，模块 `M03`，上游模块 `M03 / M10`，主题：简历管理，事实源：范围、IA、对象模型、task-remap，初始状态：blocked。
5. `ST13_05` -> `WT13-05`，模块 `M02`，上游模块 `M02 / M06 / M08`，主题：模拟记录列表，事实源：范围、IA、对象模型、评分复盘 DoD、task-remap，初始状态：blocked。
6. `ST13_06` -> `WT13-06`，模块 `M03`，上游模块 `M03 / M04 / M05 / M06 / M07`，主题：发起模拟面试，事实源：范围、IA、对象模型、task-remap，初始状态：blocked。
7. `ST13_07` -> `WT13-07`，模块 `M05`，上游模块 `M05 / M06 / M07 / M08`，主题：面试台，事实源：IA、对象模型、评分复盘 DoD、task-remap，初始状态：blocked。
8. `ST13_08` -> `WT13-08`，模块 `M06`，上游模块 `M06 / M07 / M09`，主题：打磨模式，事实源：对象模型、评分复盘 DoD、task-remap，初始状态：blocked。
9. `ST13_09` -> `WT13-09`，模块 `M06`，上游模块 `M06 / M07 / M08`，主题：压力面模式，事实源：对象模型、评分复盘 DoD、task-remap，初始状态：blocked。
10. `ST13_10` -> `WT13-10`，模块 `M05`，上游模块 `M05 / M06 / M08 / M10`，主题：RAG / 知识库，事实源：范围、IA、对象模型、评分复盘 DoD、task-remap，初始状态：blocked。
11. `ST13_11` -> `WT13-11`，模块 `M04`，上游模块 `M04 / M06 / M08 / M10`，主题：真实 LLM provider / adapter，事实源：范围、对象模型、task-remap，初始状态：blocked。
12. `ST13_12` -> `WT13-12`，模块 `M06`，上游模块 `M06 / M07 / M08`，主题：多轮上下文 / 状态机，事实源：IA、对象模型、评分复盘 DoD、task-remap，初始状态：blocked。
13. `ST13_13` -> `WT13-13`，模块 `M04`，上游模块 `M04 / M07 / M08 / M10`，主题：评分体系，事实源：对象模型、评分复盘 DoD、task-remap，初始状态：blocked。
14. `ST13_14` -> `WT13-14`，模块 `M08`，上游模块 `M08 / M09 / M10`，主题：真实面试复盘，事实源：对象模型、评分复盘 DoD、task-remap，初始状态：blocked。
15. `ST13_15` -> `WT13-15`，模块 `M06`，上游模块 `M06 / M07 / M08 / M09`，主题：模拟面试复盘，事实源：IA、对象模型、评分复盘 DoD、task-remap，初始状态：blocked。
16. `ST13_16` -> `WT13-16`，模块 `M04`，上游模块 `M04 / M07 / M08 / M09`，主题：薄弱项 `WeaknessItem`，事实源：对象模型、评分复盘 DoD、task-remap，初始状态：blocked。
17. `ST13_17` -> `WT13-17`，模块 `M03`，上游模块 `M03 / M07 / M08 / M09`，主题：训练抽屉 / 待打磨清单，事实源：对象模型、评分复盘 DoD、task-remap，初始状态：blocked。
18. `ST13_18` -> `WT13-18`，模块 `M05`，上游模块 `M05 / M08 / M10`，主题：资产归档，事实源：对象模型、评分复盘 DoD、task-remap，初始状态：blocked。
19. `ST13_19` -> `WT13-19`，模块 `M03`，上游模块 `M03 / M07 / M08 / M10`，主题：Markdown 导出 / 复制，事实源：范围、评分复盘 DoD、task-remap，初始状态：blocked。
20. `ST13_20` -> `WT13-20`，模块 `M01`，上游模块 `M01~M10`，主题：服务端保存 / 数据库，事实源：范围、对象模型、task-remap，初始状态：blocked。
21. `ST13_21` -> `WT13-21`，模块 `M01`，上游模块 `M01~M10`，主题：API / 后端服务边界，事实源：对象模型、task-remap，初始状态：blocked。
22. `ST13_22` -> `WT13-22`，模块 `M01`，上游模块 `M01 / M10`，主题：日志 / 观测 / 运维，事实源：对象模型、task-remap，初始状态：blocked。
23. `ST13_23` -> `WT13-23`，模块 `M01`，上游模块 `M01~M10`，主题：前端工作台 UI / 页面集合，事实源：IA、评分复盘 DoD、task-remap，初始状态：blocked。
24. `ST13_24` -> `WT13-24`，模块 `M01`，上游模块 `M01 / M10`，主题：测试 / 验收 / DoD，事实源：评分复盘 DoD、AGENTS、TEST_POLICY、task-remap，初始状态：blocked。
25. `ST13_25` -> `WT13-25`，模块 `M01`，上游模块 `M01 / M10`，主题：文档治理 / 收口 / Basic Memory，事实源：AGENTS、DOC_GOVERNANCE、task-remap、backlog-roadmap，初始状态：blocked。

## 9. 旧 `STxx_*` superseded / 移出策略

旧任务处理草案：

1. 阶段 1：旧 `STxx_*` 继续保留在 `subtasks` 容器，不新增正式 superseded 字段。
2. 阶段 2：旧 `STxx_*` 在各自 `facts` 下表达 `w13_superseded_preview` 或后续等价字段，标明：
   - `source_decision=W13-E-Q2`
   - `source_decision_status=confirmed`
   - `state_layer_role=state-bound historical reference; not reactivated`
   - `suggested_classification` 包含 `historical-reference / reusable-evidence / state-bound / superseded-candidate / archive-candidate`
   - `mapped_wt13_task_domains`
   - `formal_doc_state_write=true`
   - `archive_move=false`
3. 阶段 3：旧 `STxx_*` 从正式 `subtasks` 容器移出，但必须保留历史映射、closed round 追溯和索引说明。
4. 阶段 4：只设计 archive 迁移，仍不直接迁移。

是否需要新增 `w13_superseded` 或类似容器：

1. 不推荐新增顶层 `w13_superseded` 容器。
2. 当前 `validate.py` 对未知顶层字段未必立即报错，但 `DOC_AUTOMATION.md` 没有把该容器列为主链 contract，`evaluate.py` 也不会消费它。
3. 因此从治理语义上看，现有 schema 不正式支持一个可被 evaluate 消费的顶层 superseded 容器。
4. 在不修改 `validate.py / evaluate.py` 的约束下，应使用现有 `facts` 扩展字段表达，例如 `facts.w13_superseded_preview`，并通过 `TASK_INDEX.md / MODULE_INDEX.md / task-remap` 保留人类可读映射。
5. 后续若要求 evaluate 主链真正识别 superseded 并降低 blocked count，需要单独修改 schema / validate / evaluate / tests；这不属于本窗口，也不属于 W13-E4-B 阶段 1。

## 10. 用户确认卡

### 10.1 确认卡 1：是否允许 W13-E4-B 写入 `ST13_01~ST13_25`，但不移除旧 `STxx_*`？

方案 A：不写正式 `DOC_STATE.yaml`，继续只保留 Preview。

- 解决：风险最低。
- 限制：无法进入正式任务开窗治理。
- 风险：状态层仍旧。
- 后续影响：继续停留设计治理。

方案 B：写入 `ST13_01~ST13_25`，不移除旧 `STxx_*`。

- 解决：开始建立 W13 正式状态层。
- 限制：新旧并存。
- 风险：evaluate 可能增加可解释 blocker。
- 后续影响：推荐作为下一步。

方案 C：写入 `ST13_01~ST13_25`，并同时标记旧 `STxx_*` superseded，但不移出容器。

- 解决：新旧关系更清楚。
- 限制：需确认 schema 如何表达 superseded。
- 风险：状态复杂度增加。
- 后续影响：可作为第二阶段。

方案 D：自定义方案 / 其他，由用户补充。

推荐方案：B。

推荐理由：先建立 W13 新任务状态层入口，再处理旧 `STxx_*`，风险最低且符合分阶段原则。

### 10.2 确认卡 2：旧 `STxx_*` superseded 表达方式

方案 A：只在 `TASK_INDEX / MODULE_INDEX / task-remap` 中表达 superseded，不写 `DOC_STATE`。

- 解决：风险低。
- 限制：状态层看不见 superseded。
- 风险：旧 `STxx_*` blocker 仍存在。
- 后续影响：适合短期。

方案 B：在 `DOC_STATE.yaml` 中用现有字段表达 superseded / historical-reference。

- 解决：状态层能感知旧任务历史化。
- 限制：受 schema 限制。
- 风险：字段不兼容会失败。
- 后续影响：需要 preview 验证。

方案 C：先不表达 superseded，只并存新旧任务，下一阶段再处理。

- 解决：最稳。
- 限制：旧 blocker 继续存在。
- 风险：状态层噪音不变。
- 后续影响：适合第一阶段。

方案 D：自定义方案 / 其他，由用户补充。

推荐方案：C 用于第一阶段，B 用于第二阶段。

推荐理由：先写入新任务，再处理旧任务，避免一次引入太多变量。

### 10.3 确认卡 3：是否创建正式 State Write 备份文件

方案 A：不创建备份，只依赖人工 diff。

- 解决：简单。
- 限制：回退不够稳。
- 风险：状态层窗口高风险。
- 后续影响：不推荐。

方案 B：在 `docs/superpowers/plans` 下创建 State Write 变更说明和回退说明，不复制 `DOC_STATE`。

- 解决：文档化回退。
- 限制：不是完整状态备份。
- 风险：回退仍依赖后续窗口的精确 diff 或人工 patch。
- 后续影响：可接受。

方案 C：创建 `DOC_STATE` 写入前快照副本到 preview / backup 目录，但不作为正式状态。

- 解决：回退证据充分。
- 限制：多一个状态副本需要标明非正式。
- 风险：被误用为正式状态。
- 后续影响：适合高风险窗口。

方案 D：自定义方案 / 其他，由用户补充。

推荐方案：B。

推荐理由：避免复制正式状态造成混乱，同时保留足够回退说明。若用户更重视可回滚证据，可选 C。

## 11. W13-E4-B 阶段 1 执行结果

`W13-E4-B` 已按阶段 1 执行：

1. 开始前已重新运行正式和 Preview 的 `validate-state / evaluate-state`。
2. 已只把 `ST13_01~ST13_25` 写入正式 `DOC_STATE.yaml`。
3. 已同步 `requirements.RQ01.facts.task_ids`。
4. 未移除旧 `STxx_*`。
5. 未写旧 `STxx_*` superseded。
6. 未修改 `tools/**`、`tests/**`、`apps/**`、`infra/**`。
7. 未生成 implementation packet。
8. 已在阶段 1 变更说明中记录 `documents_blocked_count / modules_blocked_count / subtasks_blocked_count` 差异。
9. 写入后验证仍为 `ok=true, error=0, warning=0`，未触发回退。

## 12. 当前不进入实现说明

当前仍不能进入实现：

1. 正式 `DOC_STATE.yaml` 已写入 W13 新任务，但 `ST13_*` 仍是 blocked / review-required 状态。
2. 旧 `STxx_*` 仍在正式状态容器中。
3. `formal_window_open=false`。
4. `ST13_*` 即使写入，也只是状态层入口，不是实施任务包。
5. `TASK_INDEX.md / MODULE_INDEX.md` 已同步入口摘要，但仍未形成开窗资格。
6. `M01-M10` 仍未因 W13 产品事实 confirmed 自动升级为可实施。
7. `apps/**`、`infra/**`、业务代码、测试和工具链均不是本窗口对象。
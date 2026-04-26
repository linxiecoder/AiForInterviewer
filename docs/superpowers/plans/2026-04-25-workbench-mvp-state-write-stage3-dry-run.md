# AI 模拟面试一期工作台 MVP State Write 阶段 3 dry-run 与影响分析

> 本文档是 `W13-E4-D` 的 dry-run / 影响分析产物。本文档不修改正式 `docs/governance/DOC_STATE.yaml`，不移出旧 `STxx_*`，不迁移 archive，不生成 implementation packet，不标记 implementation-ready。
>
> 用户后续已确认 `OQ-097=B`、`OQ-098=先做方案B的Preview，不正式移出旧STxx_*`、`OQ-099=先做方案B的Preview，在Preview中移除旧ST01_01、ST09_03`。该确认只放行下一窗口创建并验证 Stage3 Preview YAML，不改变本文档的 dry-run 边界。
>
> 后续 `W13-E4-E` 已创建并验证 `docs/superpowers/plans/2026-04-25-workbench-mvp-doc-state-stage3-preview.yaml`：preview `validate-state / evaluate-state` 全绿，preview `subtasks` 只保留 `ST13_01~ST13_25`，preview `RQ01.facts.task_ids` 只保留 `ST13_01~ST13_25`。正式 `DOC_STATE.yaml` 仍未修改。
>
> 后续 `W13-E4-F` 已基于用户确认方案 B 执行正式 Stage 3：正式 `DOC_STATE.yaml.subtasks` 已只保留 `ST13_01~ST13_25`，正式 `RQ01.facts.task_ids` 已只保留 `ST13_01~ST13_25`。旧 `STxx_*` 仍保留为历史参考 / reusable evidence / archive candidate，未迁移 archive，未放行实现。

## 1. 背景

`W13-E4-B` 已完成阶段 1：正式 `DOC_STATE.yaml.subtasks` 已写入 `ST13_01~ST13_25`，并将这些新任务加入 `requirements.RQ01.facts.task_ids`。

`W13-E4-C` 已完成阶段 2：30 个旧 `STxx_*` 仍保留在正式 `subtasks` 容器中，但已在各自 `facts` 中表达：

```yaml
w13_status: superseded
w13_role: historical-reference
w13_superseded_by:
- ST13_xx
w13_alias_target:
- WT13-xx
w13_archive_candidate: true
w13_current_implementation_entry: false
```

本阶段只分析阶段 3 是否可以安全执行：将旧 `STxx_*` 从正式 `subtasks` 容器移出，同时保留历史追溯链。

## 2. 当前状态摘要

本轮开始前验证：

```powershell
python -m tools.doc_governor.cli validate-state --input docs/governance/DOC_STATE.yaml
python -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml
```

结果摘要：

1. `validate-state`：`ok=true, error=0, warning=0`。
2. `evaluate-state`：`ok=true, error=0, warning=0`。
3. `documents_blocked_count=0`。
4. `modules_blocked_count=1`。
5. `subtasks_blocked_count=55`。
6. 正式状态层当前有 `requirements=1`、`modules=10`、`subtasks=55`、`documents=1`。
7. `subtasks=55` 由 30 个旧 `STxx_*` 与 25 个新 `ST13_*` 共同构成。
8. `ST13_01~ST13_25` 均不是 implementation-ready。
9. 旧 `STxx_*` 均不是 W13 当前 implementation entry。
10. 当前仍不能进入实现。

## 3. 旧 `STxx_*` 引用链分析

### 3.1 全量旧 ST 清单

30 个旧任务如下：

`ST01_01`、`ST01_02`、`ST01_03`、`ST02_01`、`ST02_02`、`ST02_03`、`ST03_01`、`ST03_02`、`ST03_03`、`ST04_01`、`ST04_02`、`ST04_03`、`ST05_01`、`ST05_02`、`ST05_03`、`ST06_01`、`ST06_02`、`ST06_03`、`ST07_01`、`ST07_02`、`ST07_03`、`ST08_01`、`ST08_02`、`ST08_03`、`ST09_01`、`ST09_02`、`ST09_03`、`ST10_01`、`ST10_02`、`ST10_03`。

### 3.2 引用链矩阵

| 旧 ST | DOC_STATE.subtasks | TASK_INDEX | MODULE_INDEX | 模块任务索引 | 模块需求 | 进展/成熟度 | 执行日志 | closed round target/evidence | archive 文档 | facts historical/superseded | 映射到 ST13/WT13 | 阶段 3 候选 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `ST01_01` | 是 | 是 | 是 | 是 | 否 | 否 | 是 | 否 | 否 | 是 | `ST13_20/ST13_21/ST13_24/ST13_25` / `WT13-20/WT13-21/WT13-24/WT13-25` | 可进入 preview |
| `ST01_02` | 是 | 是 | 是 | 是 | 否 | 否 | 否 | 否 | 否 | 是 | `ST13_02/ST13_23` / `WT13-02/WT13-23` | 可进入 preview |
| `ST01_03` | 是 | 是 | 是 | 是 | 否 | 否 | 否 | 否 | 否 | 是 | `ST13_22/ST13_24/ST13_25` / `WT13-22/WT13-24/WT13-25` | 可进入 preview |
| `ST02_01` | 是 | 是 | 是 | 是 | 是 | 否 | 否 | 否 | 否 | 是 | `ST13_01/ST13_21` / `WT13-01/WT13-21` | 可进入 preview |
| `ST02_02` | 是 | 是 | 是 | 是 | 是 | 否 | 否 | 否 | 否 | 是 | `ST13_01/ST13_21` / `WT13-01/WT13-21` | 可进入 preview |
| `ST02_03` | 是 | 是 | 是 | 是 | 是 | 否 | 是 | 否 | 否 | 是 | `ST13_01/ST13_22` / `WT13-01/WT13-22` | 可进入 preview |
| `ST03_01` | 是 | 是 | 是 | 是 | 否 | 否 | 否 | 否 | 否 | 是 | `ST13_03/ST13_06/ST13_23` / `WT13-03/WT13-06/WT13-23` | 可进入 preview |
| `ST03_02` | 是 | 是 | 是 | 是 | 否 | 否 | 否 | 否 | 否 | 是 | `ST13_04/ST13_06/ST13_23` / `WT13-04/WT13-06/WT13-23` | 可进入 preview |
| `ST03_03` | 是 | 是 | 是 | 是 | 否 | 否 | 否 | 否 | 否 | 是 | `ST13_04/ST13_19/ST13_20` / `WT13-04/WT13-19/WT13-20` | 可进入 preview |
| `ST04_01` | 是 | 是 | 是 | 是 | 否 | 否 | 是 | 否 | 否 | 是 | `ST13_06/ST13_13/ST13_21` / `WT13-06/WT13-13/WT13-21` | 可进入 preview |
| `ST04_02` | 是 | 是 | 是 | 是 | 否 | 否 | 是 | 否 | 否 | 是 | `ST13_13/ST13_16` / `WT13-13/WT13-16` | 可进入 preview |
| `ST04_03` | 是 | 是 | 是 | 是 | 否 | 否 | 否 | 否 | 否 | 是 | `ST13_17/ST13_23` / `WT13-17/WT13-23` | 可进入 preview |
| `ST05_01` | 是 | 是 | 是 | 是 | 否 | 否 | 否 | 否 | 否 | 是 | `ST13_18` / `WT13-18` | 可进入 preview |
| `ST05_02` | 是 | 是 | 是 | 是 | 否 | 否 | 否 | 否 | 否 | 是 | `ST13_18/ST13_20` / `WT13-18/WT13-20` | 可进入 preview |
| `ST05_03` | 是 | 是 | 是 | 是 | 否 | 否 | 否 | 否 | 否 | 是 | `ST13_10/ST13_20` / `WT13-10/WT13-20` | 可进入 preview |
| `ST06_01` | 是 | 是 | 是 | 是 | 否 | 否 | 是 | 否 | 否 | 是 | `ST13_05/ST13_06/ST13_07` / `WT13-05/WT13-06/WT13-07` | 可进入 preview |
| `ST06_02` | 是 | 是 | 是 | 是 | 否 | 否 | 是 | 否 | 否 | 是 | `ST13_06/ST13_07/ST13_10/ST13_11/ST13_12` / `WT13-06/WT13-07/WT13-10/WT13-11/WT13-12` | 可进入 preview |
| `ST06_03` | 是 | 是 | 是 | 是 | 否 | 否 | 否 | 否 | 否 | 是 | `ST13_12/ST13_15/ST13_19/ST13_22` / `WT13-12/WT13-15/WT13-19/WT13-22` | 可进入 preview |
| `ST07_01` | 是 | 是 | 是 | 是 | 否 | 否 | 否 | 否 | 否 | 是 | `ST13_08/ST13_16/ST13_17` / `WT13-08/WT13-16/WT13-17` | 可进入 preview |
| `ST07_02` | 是 | 是 | 是 | 是 | 否 | 否 | 否 | 否 | 否 | 是 | `ST13_08/ST13_16` / `WT13-08/WT13-16` | 可进入 preview |
| `ST07_03` | 是 | 是 | 是 | 是 | 否 | 否 | 是 | 否 | 否 | 是 | `ST13_08/ST13_13/ST13_16/ST13_17` / `WT13-08/WT13-13/WT13-16/WT13-17` | 可进入 preview |
| `ST08_01` | 是 | 是 | 是 | 是 | 否 | 否 | 否 | 否 | 否 | 是 | `ST13_14/ST13_15/ST13_18/ST13_19` / `WT13-14/WT13-15/WT13-18/WT13-19` | 可进入 preview |
| `ST08_02` | 是 | 是 | 是 | 是 | 否 | 否 | 否 | 否 | 否 | 是 | `ST13_14/ST13_16` / `WT13-14/WT13-16` | 可进入 preview |
| `ST08_03` | 是 | 是 | 是 | 是 | 否 | 否 | 否 | 否 | 否 | 是 | `ST13_15/ST13_18/ST13_19` / `WT13-15/WT13-18/WT13-19` | 可进入 preview |
| `ST09_01` | 是 | 是 | 是 | 是 | 否 | 否 | 否 | 否 | 否 | 是 | `ST13_16` / `WT13-16` | 可进入 preview |
| `ST09_02` | 是 | 是 | 是 | 是 | 否 | 否 | 否 | 否 | 否 | 是 | `ST13_17` / `WT13-17` | 可进入 preview |
| `ST09_03` | 是 | 是 | 是 | 是 | 否 | 否 | 是 | 否 | 否 | 是 | `ST13_16/ST13_17` / `WT13-16/WT13-17` | 可进入 preview |
| `ST10_01` | 是 | 是 | 是 | 是 | 否 | 否 | 否 | 否 | 否 | 是 | `ST13_01/ST13_22` / `WT13-01/WT13-22` | 可进入 preview |
| `ST10_02` | 是 | 是 | 是 | 是 | 否 | 否 | 否 | 否 | 否 | 是 | `ST13_11/ST13_13/ST13_22` / `WT13-11/WT13-13/WT13-22` | 可进入 preview |
| `ST10_03` | 是 | 是 | 是 | 是 | 否 | 否 | 是 | 否 | 否 | 是 | `ST13_22/ST13_24/ST13_25` / `WT13-22/WT13-24/WT13-25` | 可进入 preview |

### 3.3 引用链结论

1. 全部 30 个旧 `STxx_*` 都存在于正式 `DOC_STATE.yaml.subtasks` 容器。
2. 全部 30 个旧 `STxx_*` 都存在于 `TASK_INDEX.md`、`MODULE_INDEX.md` 和模块级 `MODULE_TASK_INDEX.md`。
3. 仅 `ST02_01~ST02_03` 在模块级 `MODULE_REQUIREMENTS.md` 中直接命中；其他模块需求文档未直接命中旧 ST ID。
4. `DOCUMENT_PROGRESS.md` 与 `DOCUMENT_MATURITY.md` 当前没有逐项直接引用旧 ST ID，但有阶段性摘要引用旧 `STxx_*` 族群。
5. `EXECUTION_LOG.md` 中直接命中 9 个旧 ST：`ST01_01`、`ST02_03`、`ST04_01`、`ST04_02`、`ST06_01`、`ST06_02`、`ST07_03`、`ST09_03`、`ST10_03`。这些命中属于历史执行记录，不应被阶段 3 删除。
6. `DOC_STATE.yaml.governance_rounds` 中 closed round 的 `target_documents` / `required_evidence_refs` 未直接引用旧 ST。
7. `docs/governance/transition_history.jsonl` 未直接引用旧 ST。
8. `archive/docs/**` 当前未直接引用旧 ST。
9. 生成型治理报告或 bootstrap 输出可能仍含旧 ST 路径或 blocker 说明；这些文件不是 confirmed state，本窗口不修改。
10. 如果旧 `STxx_*` 从 `subtasks` 容器移出，文本引用不会自然断链，但 `TASK_INDEX.md`、`MODULE_INDEX.md` 和模块索引必须明确这些旧 ID 只保留为历史引用，不再是当前正式 state entity。
11. 当前可进入阶段 3 preview 候选的是全部 30 个旧 ST；不建议跳过 preview 直接正式移出。

## 4. `RQ01.facts.task_ids` 影响分析

当前 `RQ01.facts.task_ids` 包含：

1. 旧任务：`ST01_01`、`ST09_03`。
2. 新任务：`ST13_01~ST13_25`。

分析结论：

1. 本窗口不得移除 `ST01_01`、`ST09_03`。
2. 如果正式阶段 3 从 `subtasks` 容器移出旧任务，则 `RQ01.facts.task_ids` 不应继续把 `ST01_01`、`ST09_03` 当作当前任务关系；否则会形成语义上的 stale relation。
3. 当前 validate/evaluate 主链按 `requirements.RQ01.facts.task_ids` 参与 requirement-task fallback relation。旧任务移出后若仍保留在 `task_ids` 中，即使不一定触发当前代码层 error，也会让 requirement relation 继续携带非当前正式任务，容易误导审计。
4. 推荐在 Stage3 Preview 中测试方案 B：从 `RQ01.facts.task_ids` 移除 `ST01_01`、`ST09_03`，只保留 `ST13_01~ST13_25`。
5. 如需保留旧任务追溯，可在 preview 中评估 `facts.w13_legacy_task_ids` 或等价说明字段；但当前 `DOC_AUTOMATION.md` 没有把该字段列为 evaluate 主链 contract，因此它只能是说明性历史事实，不应作为关系真值。
6. 若 schema / validate / evaluate 后续需要正式消费历史 task relation，应另开工具链窗口修改 `schema.py`、`validate.py`、`evaluate.py` 和测试；这不属于本阶段。

推荐方案：Stage3 Preview 中先移除 `RQ01.facts.task_ids` 的 `ST01_01`、`ST09_03`，保留索引和 dry-run 文档中的历史说明；正式阶段 3 是否采用该结果，等待 preview 验证和用户确认。

## 5. `subtasks` 容器移出候选策略

### 方案 A：暂不移出，仅保持 facts historical / superseded

- 解决：风险最低，当前状态已经验证通过。
- 限制：`subtasks_blocked_count` 继续包含 30 个旧任务。
- 风险：状态层仍然嘈杂，后续审计持续看到 55 个 blocked subtask。
- 后续影响：可以先继续模块设计或再次收口，但不能清理状态层噪音。

### 方案 B：移出旧 `STxx_*`，并在 `DOC_STATE.yaml` 中保留合法历史引用

- 解决：正式 `subtasks` 容器更干净，同时保留状态层内历史追溯。
- 限制：当前 `DOC_AUTOMATION.md` 没有定义可被 evaluate 主链消费的 `legacy / historical` 顶层容器。
- 风险：若新增容器虽不报 schema error 但 evaluate 不消费，会造成“看似进状态层、实际不参与主链”的误读。
- 后续影响：必须先创建 Stage3 Preview YAML 验证，不得直接正式写入。

### 方案 C：移出旧 `STxx_*`，只保留 closed round / 索引历史引用

- 解决：正式状态层最简洁，`subtasks` 仅保留 `ST13_01~ST13_25`。
- 限制：历史追溯主要落在 `TASK_INDEX.md`、`MODULE_INDEX.md`、模块索引、阶段 2 / 阶段 3 文档和执行日志中。
- 风险：若 `RQ01.facts.task_ids`、索引说明或生成报告未同步，可能出现 stale target 或人工误读。
- 后续影响：需要强引用扫描和明确回退方案。

### 方案 D：自定义方案 / 其他

由用户补充。

推荐策略：先通过 Stage3 Preview 验证方案 B 的可行性；如果 preview 证明顶层历史容器不具备主链意义，则转向方案 A 或方案 C。当前不正式执行任何方案。

## 6. Stage3 Preview 方案

本窗口不创建 Preview YAML。后续 `W13-E4-E` 已创建并验证：

```text
docs/superpowers/plans/2026-04-25-workbench-mvp-doc-state-stage3-preview.yaml
```

Preview 方案与实际验证结果：

1. 基于正式 `docs/governance/DOC_STATE.yaml` 复制生成 preview。
2. 从 preview 的 `subtasks` 容器中移出 30 个旧 `STxx_*`。
3. 保留 `ST13_01~ST13_25` 不变。
4. 在 preview 中处理 `RQ01.facts.task_ids`：移除 `ST01_01`、`ST09_03`，只保留 `ST13_01~ST13_25`。
5. 如测试方案 B，可在 preview 中临时加入说明性历史字段或容器，但必须标明它不是当前 evaluate 主链 contract。
6. 不修改 `TASK_INDEX.md`、`MODULE_INDEX.md` 和模块目录，只在 dry-run 文档中记录预期同步。
7. 运行 preview 验证：

```powershell
python -m tools.doc_governor.cli validate-state --input docs/superpowers/plans/2026-04-25-workbench-mvp-doc-state-stage3-preview.yaml
python -m tools.doc_governor.cli evaluate-state --input docs/superpowers/plans/2026-04-25-workbench-mvp-doc-state-stage3-preview.yaml
```

8. 实际验证结果：preview `validate-state / evaluate-state` 均为 `ok=true,error=0,warning=0`，`subtasks_blocked_count` 从正式状态的 `55` 降为 preview 的 `25`。这只表示旧任务不再参与 preview 当前 `subtasks` 评估，不表示 W13 新任务 ready。
9. 本轮未出现的不可接受结果：
   - `validate-state` 出现 error / warning。
   - `evaluate-state` 出现 error / warning。
   - 出现 missing reference、stale target 或 schema error。
   - 任一 `ST13_*` 被误判为 `implementation_ready=true`。
   - `formal_window_open` 被误判为打开。
10. 回退方式：删除 preview 文件或弃用 preview 结果；正式 `DOC_STATE.yaml` 不受影响。

## 7. 正式阶段 3 执行计划草案

建议窗口名：`W13-E4-F` 或 `W13-StateWrite-Stage3`。

当前执行状态：已由 `W13-E4-F` 执行完成；正式变更与回退说明见 [`2026-04-25-workbench-mvp-state-write-stage3.md`](2026-04-25-workbench-mvp-state-write-stage3.md)。

### 7.1 执行目标

1. 将旧 `STxx_*` 从正式 `DOC_STATE.yaml.subtasks` 容器移出。
2. 保留旧 `STxx_*` 的历史追溯和 W13 映射说明。
3. 让正式 `subtasks` 容器只承载 `ST13_01~ST13_25`。
4. 继续保持所有 `ST13_*` blocked / 非 implementation-ready。

### 7.2 前置条件

1. 用户确认 Stage3 Preview YAML 创建方案。
2. Preview YAML 已通过 `validate-state / evaluate-state`。
3. 已确认 `RQ01.facts.task_ids` 对旧 `ST01_01`、`ST09_03` 的处理方式。
4. 已确认不迁移 archive。
5. 已确认不进入实现。

### 7.3 修改文件

正式阶段 3 预计修改：

1. `docs/governance/DOC_STATE.yaml`。
2. `TASK_INDEX.md`。
3. `MODULE_INDEX.md`。
4. `PLAN_LATEST.md`。
5. `DOCUMENT_PROGRESS.md`。
6. `DOCUMENT_MATURITY.md`。
7. `OPEN_QUESTIONS.md`。
8. `DESIGN_DECISIONS.md`。
9. `EXECUTION_LOG.md`。
10. `docs/superpowers/plans/2026-04-25-workbench-mvp-state-write-plan.md`。
11. 必要时新增正式阶段 3 变更与回退说明。

### 7.4 不修改文件

正式阶段 3 不应修改：

1. `apps/**`。
2. `infra/**`。
3. `tools/**`。
4. `tests/**`。
5. `archive/**`。
6. `docs/modules/**`，除非用户单独确认模块索引同步窗口。
7. `package.json`、`package-lock.json`、`pnpm-lock.yaml`。

### 7.5 移出步骤

1. 开始前运行正式 `validate-state / evaluate-state`。
2. 对照通过的 Stage3 Preview。
3. 从正式 `DOC_STATE.yaml.subtasks` 移出 30 个旧 `STxx_*`。
4. 保留 `ST13_01~ST13_25`。
5. 同步 `RQ01.facts.task_ids`，按 preview 结果移除旧 `ST01_01`、`ST09_03` 或采用用户确认的历史字段方案。
6. 不修改 `formal_window_open`。
7. 不修改 `implementation_doc_state` 为 active。
8. 不生成 implementation packet。
9. 更新 `TASK_INDEX.md` 和 `MODULE_INDEX.md` 的历史说明：旧 `STxx_*` 已不再是当前正式 state subtask，仅保留历史索引和映射。
10. 保护 closed round，不改 `governance_rounds`。
11. 不迁移 archive。

### 7.6 验证矩阵

正式阶段 3 完成后必须运行：

```powershell
python -m tools.doc_governor.cli validate-state --input docs/governance/DOC_STATE.yaml
python -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml
```

必须满足：

1. `validate-state ok=true, error=0, warning=0`。
2. `evaluate-state ok=true, error=0, warning=0`。
3. `documents_blocked_count=0`。
4. `ST13_01~ST13_25` 全部存在。
5. 旧 `STxx_*` 不再存在于正式 `DOC_STATE.yaml.subtasks`。
6. `RQ01.facts.task_ids` 不再把旧任务误当当前任务关系。
7. 无 missing reference。
8. 无 stale target。
9. 无 schema error。
10. 无 implementation-ready 误判。
11. 无 formal window 误开。
12. `TASK_INDEX.md` / `MODULE_INDEX.md` 仍能追溯旧任务历史。

### 7.7 失败回退步骤

1. 恢复旧 `STxx_*` 到 `DOC_STATE.yaml.subtasks`。
2. 恢复 `RQ01.facts.task_ids` 到阶段 2 安全状态。
3. 恢复 `TASK_INDEX.md` / `MODULE_INDEX.md` / 计划文档中本阶段新增的“已移出”语义。
4. 重新运行正式 `validate-state / evaluate-state`。
5. 记录失败原因，不进入实现。

## 8. 验证矩阵

本 dry-run 文档完成后仍只验证正式状态未被改动：

```powershell
python -m tools.doc_governor.cli validate-state --input docs/governance/DOC_STATE.yaml
python -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml
```

关键词扫描：

```powershell
rg -n "W13-E4-D|阶段 3|Stage3|dry-run|旧 STxx|ST01_|ST02_|ST03_|ST04_|ST05_|ST06_|ST07_|ST08_|ST09_|ST10_|ST13_01|ST13_25|WT13|superseded|historical-reference|archive-candidate|RQ01.facts.task_ids|subtasks 容器|Preview YAML|implementation-ready|formal_window_open" docs/governance/DOC_STATE.yaml PLAN_LATEST.md EXECUTION_LOG.md DOCUMENT_PROGRESS.md DOCUMENT_MATURITY.md OPEN_QUESTIONS.md DESIGN_DECISIONS.md TASK_INDEX.md MODULE_INDEX.md AGENTS.md docs/superpowers/plans
```

## 9. 回退方案

本窗口只新增 dry-run 分析文档和同步说明，不修改正式状态。若需要回退本窗口文档层写入：

1. 删除或撤销本文档。
2. 撤销 `PLAN_LATEST.md`、`EXECUTION_LOG.md`、`DOCUMENT_PROGRESS.md`、`DOCUMENT_MATURITY.md`、`OPEN_QUESTIONS.md`、`DESIGN_DECISIONS.md`、`TASK_INDEX.md`、`MODULE_INDEX.md`、`AGENTS.md` 中与 `W13-E4-D` 相关的新增说明。
3. 不触碰 `DOC_STATE.yaml`。
4. 重新运行正式 `validate-state / evaluate-state`，确认状态层未变化。

## 10. 用户确认卡

### 确认卡 1：是否创建 Stage3 Preview YAML？

方案 A：不创建 Preview YAML，只保留 dry-run 分析文档。

- 解决：风险最低。
- 限制：没有实际 validate/evaluate 对照。
- 风险：阶段 3 正式执行前仍需再验证。
- 后续影响：适合继续人工确认。

方案 B：下一窗口创建 Stage3 Preview YAML，不修改正式 `DOC_STATE.yaml`。

- 解决：可以验证旧 `STxx_*` 移出后的状态变化。
- 限制：多一个 preview 文件。
- 风险：preview 与正式状态可能存在差异。
- 后续影响：推荐。

方案 C：跳过 preview，直接正式移出旧 `STxx_*`。

- 解决：最快。
- 限制：风险最高。
- 风险：可能产生 missing reference / stale target。
- 后续影响：不推荐。

方案 D：自定义方案 / 其他，由用户补充。

推荐方案：B。

推荐理由：阶段 3 风险高，先创建 Preview YAML 验证最稳。

用户确认结果：`OQ-097=B`。后续 `W13-E4-E` 已创建并验证 Stage3 Preview YAML；正式 `DOC_STATE.yaml` 未修改。

### 确认卡 2：旧 `STxx_*` 移出策略

方案 A：暂不移出，只保留 facts historical / superseded。

方案 B：正式阶段 3 移出旧 `STxx_*`，同时保留合法历史引用。

方案 C：只移出确认无引用风险的旧 `STxx_*`。

方案 D：自定义方案 / 其他，由用户补充。

推荐方案：先做 B 的 preview，不直接正式执行。如果 preview 通过，再确认是否正式执行 B。

用户确认结果：`OQ-098=先做方案B的Preview，不正式移出旧STxx_*`。后续 `W13-E4-E` 已验证方案 B 的 preview，不正式移出旧任务。

### 确认卡 3：`RQ01.facts.task_ids` 旧任务处理

方案 A：暂时保留 `ST01_01`、`ST09_03`。

方案 B：阶段 3 preview 中移除 `ST01_01`、`ST09_03`，只保留 `ST13_01~ST13_25`。

方案 C：把 `ST01_01`、`ST09_03` 移到历史说明字段，如果 schema 支持。

方案 D：自定义方案 / 其他，由用户补充。

推荐方案：B 作为 preview 候选。

推荐理由：若旧 `STxx_*` 从 `subtasks` 容器移出，`RQ01.facts.task_ids` 也应在 preview 中验证只保留 `ST13_*` 是否可行。

用户确认结果：`OQ-099=先做方案B的Preview，在Preview中移除旧ST01_01、ST09_03`。后续 `W13-E4-E` 已在 preview 中完成验证；该确认不修改正式 `RQ01.facts.task_ids`。

## 11. 当前不执行正式移出说明

本窗口不执行：

1. 不从正式 `DOC_STATE.yaml.subtasks` 移出旧 `STxx_*`。
2. 不删除旧 `STxx_*`。
3. 不迁移 archive。
4. 本窗口当时不创建 Stage3 Preview YAML；后续 `W13-E4-E` 的 preview 文件不是正式状态真值。
5. 不修改 `RQ01.facts.task_ids`。
6. 不修改 `formal_window_open`。
7. 不生成 implementation packet。

## 12. 当前不进入实现说明

当前仍不能进入实现：

1. `formal_window_open=false`。
2. `ST13_01~ST13_25` 仍缺少实施级子任务双文档和 implementation packet 输入。
3. 阶段 3 只是状态层清理，不是实施开窗。
4. 旧 `STxx_*` 即使移出正式容器，也只会降低状态层噪音，不会让 `ST13_*` ready。
5. 业务代码目录、后端、真实 LLM、数据库、登录、评分、RAG、多轮、复盘、导出和训练能力仍必须等待正式任务包。

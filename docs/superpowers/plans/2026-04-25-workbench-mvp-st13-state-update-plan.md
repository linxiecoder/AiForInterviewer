# AI 模拟面试一期工作台 MVP ST13 State Update 准备方案

## 1. 背景

本文档记录 `W13-E12 / State Update 准备与确认窗口` 的分析结果。

本窗口基于 `W13-E11` 第一批 ST13 formal window candidate 文档层评估，准备后续 `DOC_STATE.yaml` State Update 方案、字段影响分析、验证矩阵、回退方案和用户确认卡。

本窗口不修改 `docs/governance/DOC_STATE.yaml`，不创建 preview YAML，不写代码，不创建 `apps/**`、`infra/**`、`tools/**`、`tests/**`，不生成 implementation packet，不打开 formal window，不标记 implementation-ready。

## 2. W13-E11 结论

W13-E11 已形成以下文档层结论：

| ST13 | WT13 alias | W13-E11 文档层结论 | 状态层处理原则 |
| --- | --- | --- | --- |
| `ST13_24` | `WT13-24` | `formal_window_candidate_recommended` | 可进入后续 candidate State Update preview。 |
| `ST13_25` | `WT13-25` | `formal_window_candidate_recommended` | 可进入后续 candidate State Update preview。 |
| `ST13_21` | `WT13-21` | `near_ready_for_formal_window_candidate_confirmed` | 暂不建议写入状态层 candidate。 |
| `ST13_20` | `WT13-20` | `near_ready_for_formal_window_candidate_confirmed` | 暂不建议写入状态层 candidate。 |

上述结论不等于正式状态层已写入 `candidate_status=candidate`，不等于 formal window 已打开，不等于 implementation-ready。

## 3. 基线验证

W13-E12 开始前已执行：

- `python -m tools.doc_governor.cli validate-state --input docs/governance/DOC_STATE.yaml`
- `python -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml`

基线结果：

| 命令 | 结果 |
| --- | --- |
| `validate-state` | `ok=true,error=0,warning=0` |
| `evaluate-state` | `ok=true,error=0,warning=0` |
| `documents_blocked_count` | `0` |
| `modules_blocked_count` | `1` |
| `subtasks_blocked_count` | `25` |

当前状态层仍保持可校验，但全部 ST13 仍未进入 implementation-ready。

## 4. 当前 DOC_STATE 字段分析

当前 `DOC_STATE.yaml` 中 `ST13_20 / ST13_21 / ST13_24 / ST13_25` 均位于 `subtasks` 容器，核心结构一致：

- `meta.module_id=M01`
- `meta.requirement_id=RQ01`
- `meta.path=docs/superpowers/plans/2026-04-25-workbench-mvp-task-remap.md`
- `facts.design_doc.exists=true`
- `facts.design_doc.template_like=false`
- `facts.implementation_doc.exists=true`
- `facts.implementation_doc.template_like=false`
- `facts.w13_preview.implementation_ready=false`
- `state.confirmed.implementation_doc_state=missing`
- `state.confirmed.candidate_status=none`
- `state.confirmed.review_status=unreviewed`
- `state.confirmed.readiness=blocked`
- `state.confirmed.blocker_refs=[]`

### 4.1 字段可写性判断

| 字段 | 当前存在位置 | 当前值 / 形态 | W13-E13 可否考虑 | 风险判断 |
| --- | --- | --- | --- | --- |
| `readiness` | `state.confirmed.readiness` | `blocked` | 可在 preview 中评估 `ST13_24 / ST13_25 -> downstream_ready`；`ST13_21 / ST13_20` 暂不建议更新 | readiness 提升需要证据；不得写成 `implementation_ready`。 |
| `candidate_status` | `state.confirmed.candidate_status` | `none` | 可在 preview 中评估 `ST13_24 / ST13_25 -> candidate` | `candidate` 必须配套 `review_status=pending_confirmation`，且至少一条 `--evidence-ref`。 |
| `implementation_doc_state` | `state.confirmed.implementation_doc_state` | `missing` | 本轮建议不更新 | 改为 `active_working_doc` 会减少 implementation blocker，容易被误读为进入实施准备。 |
| `facts.design_doc` | `facts.design_doc` | 已登记真实路径，`template_like=false` | 不需要更新 | 已由 W13-E8.5 完成，重复写入风险高。 |
| `facts.implementation_doc` | `facts.implementation_doc` | 已登记真实路径，`template_like=false` | 不需要更新 | 已由 W13-E8.5 完成，重复写入风险高。 |
| `facts.task_ids` | `requirements.RQ01.facts.task_ids` | 已只保留 `ST13_01~ST13_25` | 不更新 | 改动会影响 requirement 到 subtask 关系，超出本轮。 |
| `blocked_by` | 无同名字段 | 当前使用 `blocker_refs` / `declared_blocker_refs` / derived blockers | 不新增同名字段 | 随意新增可能无效或造成语义漂移。 |
| `review_required` | derived 输出 | 非 confirmed state 字段 | 不直接写 | 由 evaluate 派生，不应手工写入。 |
| `formal_window_open` | `global_policy.formal_window_open` | `false` | 不更新 | 这是全局 policy；不得在 candidate State Update 中打开。 |
| `implementation_ready` | derived 输出与 `facts.w13_preview` | `false` | 不更新 | implementation-ready 只能由 gate 派生，不应手工写。 |
| acceptance criteria | 非直接 state 字段 | evaluate 从 implementation packet inputs 派生 | 不在 W13-E12 更新 | 当前 `meta.path` 仍指向 task-remap，高级实施输入仍为空，需后续专门处理。 |
| required tests | 非直接 state 字段 | evaluate 从 implementation packet inputs 派生 | 不在 W13-E12 更新 | 不能用 candidate update 替代测试矩阵落地。 |
| implementation scope | 非直接 state 字段 | evaluate 从 implementation packet inputs 派生 | 不在 W13-E12 更新 | 不能用 candidate update 替代 allowed paths / goal / scope。 |
| notes / facts / metadata 扩展 | `facts` 可扩展，但需 preview 验证 | 现有 `facts.w13_preview` | 可仅在 preview 中测试 | 若用于 near-ready 说明，必须先验证 schema 和 evaluate 影响。 |

### 4.2 可安全更新字段

后续 W13-E13 preview 中可优先测试：

1. `ST13_24.state.confirmed.candidate_status: candidate`
2. `ST13_24.state.confirmed.review_status: pending_confirmation`
3. `ST13_24.state.confirmed.readiness: downstream_ready`
4. `ST13_25.state.confirmed.candidate_status: candidate`
5. `ST13_25.state.confirmed.review_status: pending_confirmation`
6. `ST13_25.state.confirmed.readiness: downstream_ready`

这些字段只应进入 preview，且必须保留 `global_policy.formal_window_open=false`、`implementation_doc_state=missing`，不得写成 implementation-ready。

### 4.3 不应更新字段

本阶段不建议更新：

1. `global_policy.formal_window_open`
2. `state.confirmed.implementation_doc_state`
3. `state.confirmed.readiness=implementation_ready`
4. `requirements.RQ01.facts.task_ids`
5. `facts.design_doc` / `facts.implementation_doc`
6. `meta.path`
7. acceptance criteria / required tests / implementation scope 的派生输入

### 4.4 需要 preview 或 dry-run 的字段

必须通过 preview 验证后才能考虑正式写入：

1. `candidate_status`
2. `review_status`
3. `readiness`
4. 可选的 `facts.w13_e12_candidate_note` 或等价 facts 扩展字段
5. 可选的 `facts.w13_e12_near_ready_note` 或等价 facts 扩展字段

### 4.5 可能触发 validate / evaluate blocker 的字段

| 字段 | 可能问题 |
| --- | --- |
| `candidate_status` | 仅允许 `none / observe / candidate`；写入 `candidate` 时必须配套 `review_status=pending_confirmation` 和 evidence。 |
| `readiness` | 仅允许 `blocked / not_ready / downstream_ready / implementation_ready`；near-ready 不是合法枚举。 |
| `implementation_doc_state` | 仅允许 `missing / inactive_template / active_working_doc`；当前不宜提前 active。 |
| `blocker_refs` | 只能写合法 typed ref；自由文本会失败。 |
| `formal_window_open` | 只能在 global policy 写布尔值；本轮不得改为 true。 |

### 4.6 留给 W13-E13 的字段

W13-E12 不写正式状态；以下内容只能留给 W13-E13 preview：

1. `ST13_24 / ST13_25` 的 candidate 状态 preview。
2. `ST13_24 / ST13_25` 的 readiness preview。
3. 是否用 facts 表达 `formal_window_candidate_recommended`。
4. 是否让 `ST13_21 / ST13_20` 的 near-ready 仅停留文档层，或写入 facts。
5. preview 与正式 `DOC_STATE.yaml` 的字段级 diff。

## 5. ST13_24 State Update 方案

`ST13_24 / WT13-24` 是测试 / 验收 / DoD 横向任务。W13-E11 已推荐为 `formal_window_candidate_recommended`。

| 项 | W13-E12 建议 |
| --- | --- |
| 是否更新 `candidate_status` | 后续 W13-E13 preview 中可测试 `candidate_status=candidate`。 |
| 是否更新 `readiness` | 后续 W13-E13 preview 中可测试 `readiness=downstream_ready`；不得写 `implementation_ready`。 |
| 是否更新 `implementation_doc_state` | 不更新，继续保持 `missing`，直到 formal window / active doc 条件另窗确认。 |
| 是否更新 blocker explanation | 不直接写自由文本 blocker；可在 preview facts 中记录候选依据，需验证。 |
| 是否记录 `formal_window_candidate_recommended` | 建议先在 preview facts 中记录，例如 `w13_e12_state_update.candidate_recommendation`。 |
| 是否保持 implementation-ready=false | 是。 |
| 是否保持 formal window closed | 是，`formal_window_open` 保持 false。 |
| 是否保持 implementation packet forbidden | 是。 |
| 是否需要新增 facts 字段 | 可选；建议只在 preview 中测试。 |
| 是否需要 preview 验证 | 必须。 |
| 更新后预期 blocker | 仍保留 `formal_window_closed`、`implementation_doc_not_active`、`implementation_scope_unclear`、`required_tests_missing`、`acceptance_criteria_missing`。 |
| 更新后 validate/evaluate 预期 | 目标为 `ok=true,error=0,warning=0`；不应新增不可解释 blocker。 |

推荐 W13-E13 preview 草案：

```yaml
state:
  confirmed:
    candidate_status: candidate
    review_status: pending_confirmation
    readiness: downstream_ready
    implementation_doc_state: missing
```

候选证据建议使用合法 typed refs，例如 `subtask:ST13_24`、`doc:design_doc`、`doc:implementation_doc`，并在 preview 说明中引用 W13-E11 评估文档。

## 6. ST13_25 State Update 方案

`ST13_25 / WT13-25` 是文档治理 / 收口 / Basic Memory 横向任务。W13-E11 已推荐为 `formal_window_candidate_recommended`。

| 项 | W13-E12 建议 |
| --- | --- |
| 是否更新 `candidate_status` | 后续 W13-E13 preview 中可测试 `candidate_status=candidate`。 |
| 是否更新 `readiness` | 后续 W13-E13 preview 中可测试 `readiness=downstream_ready`；不得写 `implementation_ready`。 |
| 是否更新 `implementation_doc_state` | 不更新，继续保持 `missing`。 |
| 是否更新 blocker explanation | 不直接写自由文本 blocker；可在 preview facts 中记录候选依据，需验证。 |
| 是否记录 `formal_window_candidate_recommended` | 建议先在 preview facts 中记录。 |
| 是否保持 implementation-ready=false | 是。 |
| 是否保持 formal window closed | 是，`formal_window_open` 保持 false。 |
| 是否保持 implementation packet forbidden | 是。 |
| 是否需要新增 facts 字段 | 可选；建议只在 preview 中测试。 |
| 是否需要 preview 验证 | 必须。 |
| 更新后预期 blocker | 仍保留 `formal_window_closed`、`implementation_doc_not_active`、`implementation_scope_unclear`、`required_tests_missing`、`acceptance_criteria_missing`。 |
| 更新后 validate/evaluate 预期 | 目标为 `ok=true,error=0,warning=0`；不应新增不可解释 blocker。 |

推荐 W13-E13 preview 草案：

```yaml
state:
  confirmed:
    candidate_status: candidate
    review_status: pending_confirmation
    readiness: downstream_ready
    implementation_doc_state: missing
```

候选证据建议使用合法 typed refs，例如 `subtask:ST13_25`、`doc:design_doc`、`doc:implementation_doc`，并在 preview 说明中引用 W13-E11 评估文档。

## 7. ST13_21 / ST13_20 near-ready 策略

`ST13_21 / WT13-21` 与 `ST13_20 / WT13-20` 仍保持文档层 near-ready，不建议在当前状态层写为 candidate。

| 项 | ST13_21 策略 | ST13_20 策略 |
| --- | --- | --- |
| 是否保持文档层 near-ready | 是 | 是 |
| 是否写入 `candidate_status` | 否 | 否 |
| 是否只在 TASK_INDEX / MODULE_INDEX / readiness review 文档保留 near-ready | 默认推荐是 | 默认推荐是 |
| 是否等待 M02 blocker 闭合 | 是 | 是 |
| 是否等待 OpenAPI / schema / apps 授权 | 等待 OpenAPI / `apps/api/**` 授权 | 等待 schema / migration / ORM / apps 授权 |
| 是否需要额外 contract 细化 | 可后续补 API contract 与 M02 权限消费关系 | 可后续补 schema / migration / rollback 细节 |
| 是否需要用户确认 | 是，若要写 facts near-ready，需要用户确认 | 是，若要写 facts near-ready，需要用户确认 |
| 是否需要后续 State Update | 可选；默认不写状态层 near-ready | 可选；默认不写状态层 near-ready |
| 是否保持 implementation-ready=false | 是 | 是 |
| 是否保持 formal window closed | 是 | 是 |

near-ready 不是当前 schema 中的 `readiness` 合法枚举。若用户选择状态层可追踪方案，只能考虑写入 facts 扩展字段，并且必须先 preview。

## 8. State Update 确认卡

### OQ-118：是否允许 W13-E13 更新 ST13_24 / ST13_25 的 candidate_status

问题：
是否允许后续 W13-E13 在 `DOC_STATE.yaml` preview 中为 `ST13_24 / ST13_25` 写入 formal window candidate 相关状态？

背景：
W13-E11 已将 `ST13_24 / ST13_25` 评估为 `formal_window_candidate_recommended`，但正式 `DOC_STATE.yaml` 尚未更新 `candidate_status`。W13-E12 只准备方案，不执行写入。

| 方案 | 内容 | 解决 | 限制 | 风险 | 后续影响 |
| --- | --- | --- | --- | --- | --- |
| 方案 A | 暂不更新 `DOC_STATE.yaml`，只保留文档层 recommended | 风险最低 | 状态层仍不反映 candidate | 后续 formal window 判断仍依赖文档 | 可继续文档准备，但状态层不收敛 |
| 方案 B | 下一窗口 W13-E13 preview 更新 `ST13_24 / ST13_25` 的 candidate 相关字段，但保持 formal window closed、implementation-ready=false | 状态层可反映 candidate 推荐 | 需要严格 validate/evaluate | 可能新增 blocker 或字段不兼容 | 推荐 |
| 方案 C | 下一窗口同时更新 candidate 并准备 formal window open | 推进最快 | 风险最高 | 容易越过 formal window 确认条件 | 不推荐 |
| 方案 D | 自定义方案 | 由用户补充 | 由用户补充 | 由用户补充 | 由用户补充 |

推荐方案：B。

推荐理由：
W13-E11 已有文档层 candidate 结论，下一步应先以 preview 同步状态层候选表达，但仍不能打开 formal window 或进入实现。

### OQ-119：ST13_21 / ST13_20 是否写入状态层 near-ready

问题：
是否允许后续 W13-E13 在 `DOC_STATE.yaml` preview 中为 `ST13_21 / ST13_20` 写入 near-ready 状态？

背景：
`ST13_21 / ST13_20` 仍受 M02 blocker、OpenAPI / schema / apps 授权限制，不建议写成 candidate。

| 方案 | 内容 | 解决 | 限制 | 风险 | 后续影响 |
| --- | --- | --- | --- | --- | --- |
| 方案 A | 暂不写入状态层 near-ready，只保留文档层 near-ready | 风险最低 | 状态层不表达 near-ready | 后续追踪需依赖索引和评审文档 | 默认推荐 |
| 方案 B | 下一窗口用 facts 字段表达 near_ready_for_formal_window_candidate，但不写 `candidate_status` | 状态层可追踪 near-ready | 受 schema 字段兼容影响 | 字段表达不当可能增加 blocker | 可作为中间态 |
| 方案 C | 直接写 `candidate_status`，但标记 near-ready | 表达看似清楚 | 当前 schema 不支持 near-ready candidate | 可能被 evaluate 或开窗工具误用 | 不推荐 |
| 方案 D | 自定义方案 | 由用户补充 | 由用户补充 | 由用户补充 | 由用户补充 |

推荐方案：A 或 B。默认推荐 A。

推荐理由：
如果用户想降低风险，选 A；如果用户想状态层可追踪，选 B。默认 A 可以避免状态层语义过早复杂化。

### OQ-120：W13-E13 是否先做 Preview 再写正式 DOC_STATE.yaml

问题：
后续 State Update 是否需要先创建 preview YAML？

背景：
`candidate_status` / `readiness` 写入会影响 `evaluate-state`，且当前字段组合需要验证。

| 方案 | 内容 | 解决 | 限制 | 风险 | 后续影响 |
| --- | --- | --- | --- | --- | --- |
| 方案 A | 不做 preview，直接写正式 `DOC_STATE.yaml` | 最快 | 风险较高 | 可能新增 blocker | 不推荐 |
| 方案 B | 先创建 State Update preview YAML，不修改正式 `DOC_STATE.yaml` | 风险最低 | 多一个窗口 | preview 与正式状态可能有差异 | 推荐 |
| 方案 C | 同一窗口先 preview，preview 通过后再正式写入 | 效率较高 | 窗口复杂度较高 | 容易在同窗扩大范围 | 谨慎使用 |
| 方案 D | 自定义方案 | 由用户补充 | 由用户补充 | 由用户补充 | 由用户补充 |

推荐方案：B。

推荐理由：
状态层 candidate 写入不应直接上正式状态，先 preview 更安全。

## 9. State Update Preview 方案

建议后续 W13-E13 创建 preview 文件：

`docs/superpowers/plans/2026-04-25-workbench-mvp-st13-candidate-state-preview.yaml`

Preview 应只做状态层候选预演，不修改正式 `DOC_STATE.yaml`。

### 9.1 Preview 内容

1. 基于正式 `DOC_STATE.yaml` 复制生成 preview。
2. 对 `ST13_24` preview：
   - `candidate_status=candidate`
   - `review_status=pending_confirmation`
   - `readiness=downstream_ready`
   - `implementation_doc_state=missing`
3. 对 `ST13_25` preview：
   - `candidate_status=candidate`
   - `review_status=pending_confirmation`
   - `readiness=downstream_ready`
   - `implementation_doc_state=missing`
4. 对 `ST13_21 / ST13_20`：
   - 默认保持不变；若用户选择 OQ-119 方案 B，仅在 facts 中测试 near-ready 说明。
5. `global_policy.formal_window_open` 保持 false。
6. 不写 implementation-ready。
7. 不生成 implementation packet。
8. 不打开 formal window。

### 9.2 Preview 验证矩阵

| 验证项 | 命令 / 检查 | 预期 |
| --- | --- | --- |
| 正式状态基线 | `validate-state --input docs/governance/DOC_STATE.yaml` | `ok=true,error=0,warning=0` |
| 正式状态评估 | `evaluate-state --input docs/governance/DOC_STATE.yaml` | `ok=true,error=0,warning=0` |
| preview 校验 | `validate-state --input docs/superpowers/plans/2026-04-25-workbench-mvp-st13-candidate-state-preview.yaml` | `ok=true,error=0,warning=0` |
| preview 评估 | `evaluate-state --input docs/superpowers/plans/2026-04-25-workbench-mvp-st13-candidate-state-preview.yaml` | `ok=true,error=0,warning=0` |
| 字段 diff | 对比 `ST13_20/21/24/25` 与 global policy | 只出现用户确认允许的字段变化 |
| blocker 检查 | 对比 blocker 增减 | 不新增不可解释 blocker |
| 禁止范围检查 | 检查 `docs/governance/**`、`apps/**`、`infra/**`、`tools/**`、`tests/**`、`archive/**`、`docs/modules/**` | 未修改 |

### 9.3 回退方案

W13-E13 preview 失败时：

1. 删除或弃用 preview 文件。
2. 不修改正式 `DOC_STATE.yaml`。
3. 将失败原因写回 State Update plan / execution log。
4. 若失败来自 enum 或字段组合，回退到 OQ-118 方案 A 或 OQ-119 方案 A。
5. 若失败来自 unexpected blocker，先记录 blocker，再开单独分析窗口。

## 10. 后续窗口建议

| 窗口 | 目标 | 禁止事项 |
| --- | --- | --- |
| W13-E13 | State Update Preview 窗口：创建 candidate state preview，不改正式 `DOC_STATE.yaml` | 不打开 formal window，不生成 packet，不实现 |
| W13-E14 | State Update 正式写入窗口：preview 通过后，将 `ST13_24 / ST13_25` candidate 相关字段写入正式 `DOC_STATE.yaml` | 不打开 formal window，不生成 packet，不实现 |
| W13-E15 | formal window open 前置确认窗口：决定是否允许打开某个 ST13 formal window | 不自动实现 |
| W13-E16 | implementation packet 准备确认窗口：只有 formal window 打开后才考虑 packet | 不越过 gate |

不建议直接进入实现。

## 11. 当前不进入实现说明

W13-E12 不放行以下事项：

- 不修改 `DOC_STATE.yaml`。
- 不创建 preview YAML。
- 不打开 formal window。
- 不生成 implementation packet。
- 不标记 implementation-ready。
- 不创建 `apps/**`、`infra/**`、`tools/**`、`tests/**`。
- 不创建 OpenAPI、schema、migration、ORM、测试文件或应用目录。
- 不写 Basic Memory。
- 不写代码。

## 12. 完成标准

W13-E12 完成后应满足：

1. 已分析 `DOC_STATE.yaml` 中四个目标 ST13 的可写字段。
2. 已提出 `ST13_24 / ST13_25` State Update 方案。
3. 已提出 `ST13_21 / ST13_20` near-ready 保持策略。
4. 已输出 `OQ-118~OQ-120` 确认卡。
5. 已设计 W13-E13 Preview 方案。
6. 未修改正式 `DOC_STATE.yaml`。
7. 未打开 formal window。
8. 未生成 implementation packet。
9. 未进入实现。
10. 未创建 `apps/**`、`infra/**`。
11. 未修改 `tools/**`、`tests/**`。
12. `validate-state / evaluate-state` 仍为 `ok=true,error=0,warning=0`。

结论：满足用户确认后，可以进入 W13-E13 Preview；进入前必须确认 `OQ-118~OQ-120`。

## 13. W13-E13 Preview 验证结果

用户已确认：

1. `OQ-118=B`：W13-E13 只在 preview 中测试 `ST13_24 / ST13_25` candidate 相关字段，保持 `formal_window_open=false`、`implementation-ready=false`，不修改正式 `DOC_STATE.yaml`。
2. `OQ-119=A`：`ST13_21 / ST13_20` 不写状态层 near-ready，只保留文档层 near-ready。
3. `OQ-120=B`：先创建 State Update preview YAML。

W13-E13 已创建：

`docs/superpowers/plans/2026-04-25-workbench-mvp-st13-candidate-state-preview.yaml`

Preview 中仅尝试：

1. `ST13_24`：`candidate_status=candidate`、`review_status=pending_confirmation`、`readiness=downstream_ready`。
2. `ST13_25`：`candidate_status=candidate`、`review_status=pending_confirmation`、`readiness=downstream_ready`。
3. `ST13_21 / ST13_20`：保持正式状态原样，不写 candidate，不写 near-ready。

验证结果：

| 输入 | 命令 | 结果 |
| --- | --- | --- |
| 正式 `DOC_STATE.yaml` | `validate-state` | `ok=true,error=0,warning=0` |
| 正式 `DOC_STATE.yaml` | `evaluate-state` | `ok=true,error=0,warning=0,documents_blocked_count=0,modules_blocked_count=1,subtasks_blocked_count=25` |
| Preview YAML | `validate-state` | `ok=false,error=4,warning=0` |
| Preview YAML | `evaluate-state` | `ok=false,error=4,warning=0` |

失败原因：

1. `ST13_24 / ST13_25` 均触发 `RULE_FORMAL_WINDOW_CLOSED_CANDIDATE_FORBIDDEN`：当前 `global_policy.formal_window_open=false` 时不允许 `candidate_status=candidate`。
2. `ST13_24 / ST13_25` 均触发 `RULE_ILLEGAL_STATE_COMBINATION`：`readiness=downstream_ready` 要求对应 `maturity` 非空。

结论：

1. W13-E13 Preview 未通过。
2. 不建议进入 W13-E14 正式 State Update。
3. 正式 `DOC_STATE.yaml` 未修改。
4. formal window 仍关闭。
5. implementation packet 仍禁止。
6. implementation-ready 未形成。
7. 后续应先确认 `OQ-121`：是否暂不执行正式 State Update，并修正 candidate 状态表达策略。

## 14. W13-E13.5 策略修正

用户已确认 `OQ-121=A`：暂不执行正式 State Update，只保留失败 Preview，并先修正后续状态表达策略。

因此，本文件第 4 节和第 6 节中原本建议的 `candidate_status=candidate` + `readiness=downstream_ready` Preview 组合已被 W13-E13 验证为不可直接采用，后续不得将其作为正式写入方案。

修正后的状态表达策略为：

1. `ST13_24 / ST13_25` 继续只保留文档层 `formal_window_candidate_recommended`。
2. 正式 `DOC_STATE.yaml` 暂不写 `candidate_status=candidate`。
3. 下一轮 Candidate Preview 优先验证 facts-only 表达，例如 `facts.formal_window_candidate_recommended=true` 或等价现有 facts 字段。
4. 备选方案是验证 `candidate_status=observe` 是否可作为状态层轻量观察态。
5. 不直接写 `readiness=downstream_ready`，除非 maturity 合法字段和值已明确。
6. `ST13_21 / ST13_20` 继续只保留文档层 `near_ready_for_formal_window_candidate_confirmed`，不写 candidate，不写 `downstream_ready`。
7. `formal_window_open` 继续保持 `false`，implementation-ready 继续保持 `false`，implementation packet 继续 forbidden。

新的后续窗口建议：

| 窗口 | 目标 | 边界 |
| --- | --- | --- |
| W13-E14-pre 或下一 Candidate Preview 窗口 | 创建修正后的 facts-only Candidate Preview，验证 `ST13_24 / ST13_25` 的 facts 表达 | 不修改正式 `DOC_STATE.yaml`，不打开 formal window，不生成 packet |
| 后续备选 Preview | 验证 `candidate_status=observe` 是否合法 | 只作为备选，不等同正式 candidate |
| W13-E14 | 只有新的 Preview 全绿且用户另行确认后，才可讨论正式 State Update | 不得由 W13-E13 失败 Preview 直接跳入 |

W13-E13.5 新增确认卡见 `OPEN_QUESTIONS.md` 的 `OQ-122 / OQ-123`。确认前，不进入 `W13-E14`。

## 15. W13-E13.6 facts-only Preview 回写

用户已确认：

1. `OQ-122=A`：下一轮 Candidate Preview 采用 facts-only 方案。
2. `OQ-123=A`：继续禁止 `W13-E14` 正式 State Update，直到新的 Preview validate/evaluate 全绿。

W13-E13.6 已新增：

`docs/superpowers/plans/2026-04-25-workbench-mvp-st13-candidate-state-facts-preview.yaml`

Preview 写入范围：

1. `ST13_24 / ST13_25`：仅在 `facts` 下写入 `formal_window_candidate_recommended=true`、来源、review status、document layer state 和禁止 packet/实现说明。
2. `ST13_21 / ST13_20`：保持正式状态原样，不写 candidate，不写 near-ready facts。
3. 未写 `candidate_status=candidate`。
4. 未写 `readiness=downstream_ready`。
5. 未打开 `formal_window_open`。
6. 未形成 implementation-ready。

验证结果：

| 输入 | 命令 | 结果 |
| --- | --- | --- |
| 正式 `DOC_STATE.yaml` | `validate-state` | `ok=true,error=0,warning=0` |
| 正式 `DOC_STATE.yaml` | `evaluate-state` | `ok=true,error=0,warning=0,documents_blocked_count=0,modules_blocked_count=1,subtasks_blocked_count=25` |
| facts-only Preview YAML | `validate-state` | `ok=true,error=0,warning=0` |
| facts-only Preview YAML | `evaluate-state` | `ok=true,error=0,warning=0,documents_blocked_count=1,modules_blocked_count=1,subtasks_blocked_count=25` |

结论：

1. facts-only 字段被 schema / validate 接受。
2. W13-E13 的 `formal_window_open=false` + `candidate_status=candidate` 错误未复现。
3. W13-E13 的 `readiness=downstream_ready` + `maturity=null` 错误未复现。
4. `documents_blocked_count=1` 来自 plan-path Preview 对 `documents` 路径的扫描根目录副作用，不来自 ST13 facts-only 字段。
5. 按 `OQ-123=A` 的严格全绿口径，当前仍不直接进入 `W13-E14`，需先由用户确认 `OQ-124`。

## 16. W13-E13.8 facts-only 正式 State Update 执行结果

用户已确认 `OQ-124` 方案 A：将 Preview 放到 `docs/governance/previews/` 下重新验证；Preview 严格全绿后，再执行 facts-only 正式 State Update。

本轮已新增：

- `docs/governance/previews/DOC_STATE_W13_E13_8_CANDIDATE_FACTS_PREVIEW.yaml`

本轮正式写入：

1. `ST13_24 / ST13_25`：仅在 `facts` 下写入 `formal_window_candidate_recommended=true`、来源、review status、document layer state 和禁止 packet/实现说明。
2. `ST13_21 / ST13_20`：保持正式状态原样；不写 candidate facts，不写 near-ready 状态，不写 `candidate_status=candidate`。
3. 不写 `readiness=downstream_ready`，不打开 formal window，不标记 implementation-ready，不生成 implementation packet。

验证结果：

| 对象 | 命令 | 结果 |
| --- | --- | --- |
| 正式 `DOC_STATE.yaml` 基线 | `validate-state` | `ok=true,error=0,warning=0` |
| 正式 `DOC_STATE.yaml` 基线 | `evaluate-state` | `ok=true,error=0,warning=0,documents_blocked_count=0,modules_blocked_count=1,subtasks_blocked_count=25` |
| docs/governance/previews 路径 Preview | `validate-state` | `ok=true,error=0,warning=0` |
| docs/governance/previews 路径 Preview | `evaluate-state` | `ok=true,error=0,warning=0,documents_blocked_count=0,modules_blocked_count=1,subtasks_blocked_count=25` |
| 正式 `DOC_STATE.yaml` 写入后 | `validate-state` | `ok=true,error=0,warning=0` |
| 正式 `DOC_STATE.yaml` 写入后 | `evaluate-state` | `ok=true,error=0,warning=0,documents_blocked_count=0,modules_blocked_count=1,subtasks_blocked_count=25` |

结论：W13-E13.8 已完成 facts-only 正式 State Update，但不放行 formal window open、implementation packet 或代码实现。

后续若进入正式 State Update，只能写入 `ST13_24 / ST13_25.facts` 的 candidate 推荐事实，并继续保持 `candidate_status=none`、`readiness=blocked`、`formal_window_open=false`、implementation-ready=false。

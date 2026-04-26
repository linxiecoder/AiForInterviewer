# AI 模拟面试一期工作台 MVP ST13 candidate 状态表达策略修正

## 1. 背景

本文件记录 `W13-E13.5 / Candidate State 表达策略修正窗口` 的策略复盘与后续建议。该窗口基于 `W13-E13` candidate State Preview 的失败结果，只修正后续状态表达策略，不修改正式 `docs/governance/DOC_STATE.yaml`，不创建新的正式 State Update，不进入 `W13-E14`，不打开 formal window，不生成 implementation packet，不标记 implementation-ready，也不进入代码实现。

用户已确认 `OQ-121=A`：暂不执行正式 State Update，只保留失败 Preview，并先修正后续状态表达策略。

## 2. W13-E13 Preview 失败摘要

`W13-E13` Preview 原计划只在 preview 文件中测试 `ST13_24 / ST13_25` 的 candidate 相关字段：

- `candidate_status=candidate`
- `review_status=pending_confirmation`
- `readiness=downstream_ready`
- `formal_window_open=false`
- `implementation-ready=false`

正式 `DOC_STATE.yaml` 的基线验证仍为安全状态：

- `validate-state`：`ok=true,error=0,warning=0`
- `evaluate-state`：`ok=true,error=0,warning=0`
- `documents_blocked_count=0`

Preview 验证失败：

- `validate-state`：`ok=false,error=4,warning=0`
- `evaluate-state`：`ok=false,error=4,warning=0`
- 无 schema error。
- 无 parse error。
- 无 missing reference。
- 无 stale target。
- 无 implementation-ready 误判。
- 无 formal_window_open 误开。

失败字段为：

| 对象 | 字段组合 | 失败原因 |
| --- | --- | --- |
| `ST13_24` | `candidate_status=candidate` + `formal_window_open=false` | 当前规则禁止 formal window 关闭时写入 candidate。 |
| `ST13_24` | `readiness=downstream_ready` + `maturity=null` | 当前规则要求 readiness 为 downstream_ready 时 maturity 非空。 |
| `ST13_25` | `candidate_status=candidate` + `formal_window_open=false` | 当前规则禁止 formal window 关闭时写入 candidate。 |
| `ST13_25` | `readiness=downstream_ready` + `maturity=null` | 当前规则要求 readiness 为 downstream_ready 时 maturity 非空。 |

## 3. 状态规则分析

### 3.1 `formal_window_open=false` 与 `candidate_status=candidate`

当前 `doc_governor` 规则把 `candidate_status=candidate` 视为 formal window 相关状态。只要全局 `formal_window_open=false`，就禁止任何目标写入 `candidate_status=candidate`。因此，`candidate_status=candidate` 不能作为“formal window 尚未打开但已推荐候选”的中间态。

这意味着：

- 文档层的 `formal_window_candidate_recommended` 可以继续存在。
- 正式状态层不能在 formal window 关闭时写入 `candidate_status=candidate`。
- 若后续确需正式状态层 candidate，必须先处理 formal window 前置确认，或改用不触发 candidate 规则的中间表达。

### 3.2 `readiness=downstream_ready` 与 `maturity`

当前规则要求 `readiness=downstream_ready` 时目标 `maturity` 不得为空。`W13-E13` Preview 中 `ST13_24 / ST13_25` 的 maturity 仍为空，因此同时触发非法状态组合。

这意味着：

- 不能单独用 `readiness=downstream_ready` 表达文档层候选推荐。
- 若尝试写 `downstream_ready`，必须先明确 maturity 合法字段和值。
- 在 maturity 语义未澄清前，直接补 maturity 可能被误读为实施成熟度提升，因此不宜作为优先策略。

### 3.3 为什么不是 schema error

Preview 使用的字段和值本身位于 schema 支持范围内：

- `candidate_status` 支持 `none / observe / candidate`。
- `review_status` 支持 `pending_confirmation`。
- `readiness` 支持 `blocked / not_ready / downstream_ready / implementation_ready`。

失败来自字段之间的组合规则，而不是 YAML 结构、字段名、枚举值或引用解析错误。

### 3.4 为什么正式 `DOC_STATE.yaml` 仍然安全

`W13-E13` 只创建并验证 preview 文件，没有修改正式 `docs/governance/DOC_STATE.yaml`。正式状态层仍通过 `validate-state / evaluate-state`，且 `documents_blocked_count=0`。失败 Preview 只是验证证据，不是 confirmed state，也不会驱动 `confirm-transition`、formal window open 或 implementation packet。

### 3.5 为什么不能进入 W13-E14

`W13-E14` 原本意味着基于 Preview 进入正式 State Update。当前 Preview 已被规则拒绝，若直接进入正式写入，会把已知非法组合写入正式状态层，破坏 `validate-state / evaluate-state` gate。因此必须先设计新的 Preview 方案并验证全绿。

### 3.6 为什么不能打开 formal window

本窗口没有用户确认 formal window open，且 `ST13_24 / ST13_25` 仍缺 implementation scope、required tests 和正式状态层候选验证闭环。`ST13_21 / ST13_20` 还受 M02 blocker、OpenAPI / schema / apps 授权等前置条件影响。因此 formal window 必须继续关闭。

### 3.7 为什么不能生成 implementation packet

当前 25 个 `ST13_*` 均未形成 implementation-ready。`ST13_24 / ST13_25` 只具备文档层 candidate 推荐，不具备正式状态层 candidate、formal window open、required tests 落盘或 implementation scope 闭合。因此 implementation packet 仍 forbidden。

## 4. 候选状态表达策略比较

| 策略 | 表达方式 | 适用性 | 限制 | 风险 | 后续影响 |
| --- | --- | --- | --- | --- | --- |
| 策略 A | 只在文档层表达 `formal_window_candidate_recommended`；状态层保持 `candidate_status=none` 或原状态 | 风险最低 | 状态层不表达 candidate | evaluate 不会将其视为 candidate | 可继续文档治理，不能推动状态层 candidate |
| 策略 B | 用 `candidate_status=observe` 表达候选观察态；`formal_window_open=false`；`readiness` 保持 `blocked` 或 `not_ready` | 若规则允许 observe，可作为轻量状态表达 | 需要 Preview 验证 | observe 语义不等同 candidate，可能仍受组合规则限制 | 可作为备选中间态 |
| 策略 C | 使用 `facts.formal_window_candidate_recommended=true` 或等价现有 facts 字段；`candidate_status` 保持 `none / observe`；`readiness` 保持当前状态 | 不触发 `candidate_status=candidate` 限制 | evaluate 可能不会识别为 candidate | 状态层可见性弱 | 适合记录候选推荐但不驱动 formal window |
| 策略 D | 先补 maturity，再尝试 `readiness=downstream_ready`，但不写 `candidate_status=candidate` | 仅在 maturity 语义清晰时适用 | 需要明确合法字段和值 | 易误导为成熟度提升 | 需谨慎，不建议优先 |
| 策略 E | 等 formal window open 前置确认后，再写 `candidate_status=candidate` | 与现有规则最一致 | candidate 状态和 formal window open 绑定过紧 | 缺少中间候选状态 | 可能需要把 candidate 推荐长期放在文档层 |
| 策略 F | 自定义方案 / 其他 | 由用户补充 | 需另行 Preview 验证 | 取决于字段组合 | 不得在本窗口执行正式写入 |

当前推荐：优先采用策略 A + 策略 C 的 facts-only Preview，即状态层只记录事实型候选推荐，不写 `candidate_status=candidate`，不写 `readiness=downstream_ready`。备选策略为 B，用 `candidate_status=observe` 做验证。

## 5. `ST13_24 / ST13_25` 修正策略

`ST13_24 / ST13_25` 的表达策略修正为：

1. 文档层继续保留 `formal_window_candidate_recommended`。
2. 正式 `DOC_STATE.yaml` 暂不写 `candidate_status=candidate`。
3. 下一轮 Preview 优先验证 facts-only 表达，例如 `facts.formal_window_candidate_recommended=true` 或等价现有 facts 字段。
4. 如需状态层轻量状态，优先另行验证 `candidate_status=observe`。
5. 不直接写 `readiness=downstream_ready`，除非 maturity 合法字段和值已明确。
6. `formal_window_open` 必须保持 `false`。
7. implementation-ready 必须保持 `false`。
8. implementation packet 仍 forbidden。

## 6. `ST13_21 / ST13_20` 保持策略

`ST13_21 / ST13_20` 的表达策略保持为：

1. 继续保留文档层 `near_ready_for_formal_window_candidate_confirmed`。
2. 不写 `candidate_status`。
3. 不写 `readiness=downstream_ready`。
4. 不写 formal window candidate。
5. 不写 implementation-ready。
6. 等 M02 blocker、OpenAPI / schema / apps 授权闭合后再重新评估。

## 7. 新 Candidate Preview 候选方案

| 方案 | Preview 内容 | 优点 | 限制 / 风险 | 推荐级别 |
| --- | --- | --- | --- | --- |
| 方案 A | `ST13_24 / ST13_25` 仅写 `facts.formal_window_candidate_recommended=true` 或等价现有 facts 字段；不写 `candidate_status=candidate`；不写 `readiness=downstream_ready`；`formal_window_open=false`；implementation-ready=false | 最不容易触发现有组合规则 | evaluate 可能不识别为 candidate | 优先推荐 |
| 方案 B | `ST13_24 / ST13_25` 写 `candidate_status=observe`、`review_status=pending_confirmation`，`readiness` 保持 `blocked` 或 `not_ready`；`formal_window_open=false`；implementation-ready=false | 可验证 observe 是否可作为状态层候选观察态 | observe 语义可能不等同 candidate，也可能仍受规则限制 | 备选 |
| 方案 C | 只补 maturity 相关字段，不写 `candidate_status=candidate`，再尝试 `readiness=downstream_ready`；`formal_window_open=false`；implementation-ready=false | 可测试 downstream_ready 的必要条件 | maturity 语义不清，容易被误读为成熟度提升 | 不推荐优先 |
| 方案 D | 自定义方案 / 其他 | 由用户补充 | 必须另行 Preview 验证 | 待用户确认 |

推荐方案：A。备选方案：B。

## 8. 是否适合并行窗口

当前默认不建议基于 main 开启并行窗口。

原因：

1. 当前 main 工作区已有前置文档改动和未跟踪的 W13-E13 产物，基线不属于干净状态。
2. 本轮需要同步多个总控文档，若并行窗口同时修改总控文档，冲突风险较高。
3. candidate 状态表达策略尚未通过新的 Preview 验证，先并行推进容易把失败策略扩散到 ST13 文档和 backlog。
4. 并行窗口不得修改 `DOC_STATE.yaml`、不得打开 formal window、不得生成 implementation packet，这些边界需要先在串行策略窗口中稳定下来。

后续建议：

- 先用一个串行窗口创建修正后的 Candidate State Preview。
- 若新 Preview 全绿，再考虑并行处理 `ST13_24 / ST13_25` 文档同步和 backlog 维护。
- 并行完成后必须有 Merge 总控窗口负责总结、方向把控、冲突检查、验证和提交。

## 9. 用户确认卡

### 确认卡 1：W13-E13.5 后是否创建新的 Candidate State Preview？

问题：是否允许下一窗口创建修正后的 Candidate State Preview？

| 方案 | 内容 | 解决 | 限制 | 风险 | 后续影响 |
| --- | --- | --- | --- | --- | --- |
| 方案 A | 创建 facts-only Candidate Preview。`ST13_24 / ST13_25` 只用 facts 字段表达 `formal_window_candidate_recommended`，`candidate_status` 不写 candidate，`readiness` 不写 downstream_ready。 | 最稳。 | evaluate 可能不识别为 candidate。 | 状态层仍以事实字段记录，不驱动 formal window。 | 推荐。 |
| 方案 B | 创建 `candidate_status=observe` Preview。 | 验证 observe 是否可作为状态层候选观察态。 | 语义可能不等同 candidate。 | 可能仍有规则限制。 | 可作为备选。 |
| 方案 C | 创建 maturity + downstream_ready Preview。 | 测试 `readiness=downstream_ready` 的必要条件。 | maturity 语义不清。 | 可能误导为成熟度提升。 | 不推荐优先。 |
| 方案 D | 自定义方案 / 其他 | 由用户补充。 | 需重新设计验证矩阵。 | 取决于字段组合。 | 待确认。 |

推荐方案：A。

### 确认卡 2：是否继续禁止 W13-E14 正式 State Update？

| 方案 | 内容 | 解决 | 限制 | 风险 | 后续影响 |
| --- | --- | --- | --- | --- | --- |
| 方案 A | 继续禁止，直到新的 Preview 全绿。 | 风险最低。 | 状态层 candidate 暂不正式写入。 | 推进速度慢。 | 推荐。 |
| 方案 B | 允许在 facts-only 方案下直接正式写入。 | 推进快。 | 未验证前风险高。 | 可能新增 blocker。 | 不推荐。 |
| 方案 C | 允许 formal window open 前置确认后再写 `candidate_status=candidate`。 | 符合现有规则。 | 把 candidate 与 formal window 绑定。 | 中间态缺失。 | 可后续再议。 |
| 方案 D | 自定义方案 / 其他 | 由用户补充。 | 需重新设计验证矩阵。 | 取决于字段组合。 | 待确认。 |

推荐方案：A。

## 10. 当前不进入实现说明

本窗口完成后仍保持以下边界：

- 不修改正式 `docs/governance/DOC_STATE.yaml`。
- 不执行正式 State Update。
- 不进入 `W13-E14`。
- 不打开 formal window。
- 不生成 implementation packet。
- 不标记 implementation-ready。
- 不创建 `apps/**`、`infra/**`、`tests/**`、`tools/**`。
- 不创建 OpenAPI 文件、schema 文件、测试代码或业务代码。
- 不写 Basic Memory。
- 不执行 Git 提交或推送。

## 11. 下一步建议

1. 用户已确认确认卡 1 的方案 A（`OQ-122=A`）和确认卡 2 的方案 A（`OQ-123=A`）。
2. W13-E13.6 已创建 facts-only Candidate Preview，并只验证 `ST13_24 / ST13_25` 的 facts 表达。
3. facts-only 字段已被 `validate-state` 接受，且未复现 W13-E13 的 candidate/downstream 两类规则错误。
4. 完整 Preview 仍有 `documents_blocked_count=1` 的 path-scan blocker；因此在用户确认 `OQ-124` 前，继续禁止 `W13-E14`、formal window open、implementation packet 和代码实现。

## 12. W13-E13.6 执行结果

新增 Preview：

`docs/superpowers/plans/2026-04-25-workbench-mvp-st13-candidate-state-facts-preview.yaml`

Preview 只在 `ST13_24 / ST13_25.facts` 下写入：

- `formal_window_candidate_recommended=true`
- `formal_window_candidate_source=W13-E11 candidate evaluation`
- `formal_window_candidate_review_status=pending_confirmation`
- `formal_window_candidate_state=document_layer_recommended`
- `formal_window_candidate_notes=formal window closed; implementation-ready false; implementation packet forbidden`

验证结果：

- Preview `validate-state`：`ok=true,error=0,warning=0`
- Preview `evaluate-state`：`ok=true,error=0,warning=0,documents_blocked_count=1,modules_blocked_count=1,subtasks_blocked_count=25`

当前结论：

- facts-only 表达可作为后续正式 State Update 的候选事实字段。
- `ST13_21 / ST13_20` 仍不写 candidate 或 near-ready facts。
- 当前仍不建议并行窗口。
- 当前仍不进入 `W13-E14`，除非用户先确认 `OQ-124`。

## 13. W13-E13.8 执行结果回写

用户已确认 `OQ-124` 方案 A：把 facts-only Candidate Preview 放到 `docs/governance/` 直下重新验证；Preview 严格全绿后，再执行 facts-only 正式 State Update。

W13-E13.8 已创建：

- `docs/governance/DOC_STATE_W13_E13_8_CANDIDATE_FACTS_PREVIEW.yaml`

执行结果：

1. docs/governance 直下 Preview `validate-state / evaluate-state` 均为 `ok=true,error=0,warning=0`，`documents_blocked_count=0`。
2. 正式 `DOC_STATE.yaml` 已仅为 `ST13_24 / ST13_25.facts` 写入 `formal_window_candidate_*` 推荐事实。
3. 正式写入后 `validate-state / evaluate-state` 仍为 `ok=true,error=0,warning=0`，`documents_blocked_count=0`。
4. `ST13_21 / ST13_20` 保持正式状态原样，不写 candidate facts，不写 near-ready 状态。
5. 仍不写 `candidate_status=candidate`，不写 `readiness=downstream_ready`，不打开 formal window，不生成 implementation packet，不标记 implementation-ready，不进入实现。

该结果确认 facts-only 策略可用于记录候选推荐事实，但不改变 formal window 和 implementation-ready 门禁。

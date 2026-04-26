# AI 模拟面试一期工作台 MVP ST13 required doc slot State Update

## 1. 背景

本文档记录 `W13-E8.5 / 第一批 ST13 required doc slot State Update` 的状态层写入结果。

W13-E8 已根据用户确认创建第一批正式双文档：

- `OQ-111=A`：ST13 双文档路径采用集中任务包目录。
- `OQ-112=A`：允许创建 `ST13_21 / ST13_20 / ST13_24 / ST13_25` 的正式双文档。
- `OQ-113=B`：创建双文档后，在后续单独 State Update 窗口更新 `DOC_STATE.yaml` required doc slot。

本窗口承接 `OQ-113=B`，只登记 required doc slot，不进入实现。

## 2. 更新范围

本窗口只处理以下四个正式状态层入口：

1. `ST13_21`
2. `ST13_20`
3. `ST13_24`
4. `ST13_25`

本窗口未处理 `ST13_01~ST13_19`、`ST13_22`、`ST13_23`，未恢复旧 `STxx_*`，未修改 `RQ01.facts.task_ids`。

## 3. 双文档路径

| ST13 | DESIGN 文档 | IMPLEMENTATION 文档 |
| --- | --- | --- |
| `ST13_21` | `docs/superpowers/plans/st13-task-packages/ST13_21/ST13_21_DESIGN.md` | `docs/superpowers/plans/st13-task-packages/ST13_21/ST13_21_IMPLEMENTATION.md` |
| `ST13_20` | `docs/superpowers/plans/st13-task-packages/ST13_20/ST13_20_DESIGN.md` | `docs/superpowers/plans/st13-task-packages/ST13_20/ST13_20_IMPLEMENTATION.md` |
| `ST13_24` | `docs/superpowers/plans/st13-task-packages/ST13_24/ST13_24_DESIGN.md` | `docs/superpowers/plans/st13-task-packages/ST13_24/ST13_24_IMPLEMENTATION.md` |
| `ST13_25` | `docs/superpowers/plans/st13-task-packages/ST13_25/ST13_25_DESIGN.md` | `docs/superpowers/plans/st13-task-packages/ST13_25/ST13_25_IMPLEMENTATION.md` |

## 4. DOC_STATE.yaml 更新方式

`docs/governance/DOC_STATE.yaml` 的目标 ST13 已存在 `facts.design_doc` 与 `facts.implementation_doc` slot。本窗口沿用既有 slot 结构，在 slot 内补充路径元数据，不新增新的 slot 类型、顶层结构或工具校验规则，不修改 `tools/**`。

每个目标 ST13 仅做以下状态层登记：

- `facts.design_doc.exists: true`
- `facts.design_doc.path: <DESIGN 文档路径>`
- `facts.design_doc.template_like: false`
- `facts.implementation_doc.exists: true`
- `facts.implementation_doc.path: <IMPLEMENTATION 文档路径>`
- `facts.implementation_doc.template_like: false`

本窗口未修改：

- `state.confirmed.implementation_doc_state`
- `state.confirmed.readiness`
- `state.confirmed.candidate_status`
- `state.confirmed.review_status`
- `policy.global_policy.formal_window_open`

## 5. 不做事项

- 不写代码。
- 不创建 `apps/**`、`infra/**`。
- 不修改 `tools/**`、`tests/**`。
- 不修改 `docs/modules/**`。
- 不生成 implementation packet。
- 不打开 formal window。
- 不标记 implementation-ready。
- 不创建新的 ST13 双文档。
- 不扩大第一批 ST13 范围。
- 不写 Basic Memory。
- 不执行 Git 提交或推送。

## 6. 验证结果

开始前验证：

- `python -m tools.doc_governor.cli validate-state --input docs/governance/DOC_STATE.yaml`：`ok=true,error=0,warning=0`
- `python -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml`：`ok=true,error=0,warning=0`
- `documents_blocked_count=0`
- `modules_blocked_count=1`
- `subtasks_blocked_count=25`
- `missing_required_doc_slot=50`

更新后即时验证：

- `python -m tools.doc_governor.cli validate-state --input docs/governance/DOC_STATE.yaml`：`ok=true,error=0,warning=0`
- `python -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml`：`ok=true,error=0,warning=0`
- `documents_blocked_count=0`
- `modules_blocked_count=1`
- `subtasks_blocked_count=25`
- `missing_required_doc_slot=42`

最终验证以执行日志和本轮最终输出为准。

## 7. blocked count 变化

本窗口只补齐 4 个 ST13 的 8 个 required doc slot，因此：

- `documents_blocked_count` 保持 `0`。
- `modules_blocked_count` 保持 `1`，因为本窗口不处理模块 required doc slot。
- `subtasks_blocked_count` 保持 `25`，因为 formal window、implementation doc activation、acceptance criteria、required tests 和 implementation scope 仍未闭合。
- `missing_required_doc_slot` 从 `50` 降为 `42`。

该 blocker 减少只表示文档路径登记完成，不表示 implementation-ready。

## 8. 后续 contract 细化输入

`ST13_21 / ST13_20 / ST13_24 / ST13_25` 的双文档已登记到状态层 required doc slot，可作为后续 W13-E9 contract 细化的状态层输入。

W13-E9 仍只能细化 contract，不得实现，不得生成 implementation packet，不得打开 formal window。

## 9. 回退说明

如需回退本窗口 `DOC_STATE.yaml` required doc slot 更新，应仅撤销四个目标 ST13 的 slot 登记：

1. 在 `ST13_21.facts.design_doc` 中移除 `path`，并把 `exists` 改回 `false`。
2. 在 `ST13_21.facts.implementation_doc` 中移除 `path`，并把 `exists` 改回 `false`。
3. 在 `ST13_20.facts.design_doc` 中移除 `path`，并把 `exists` 改回 `false`。
4. 在 `ST13_20.facts.implementation_doc` 中移除 `path`，并把 `exists` 改回 `false`。
5. 在 `ST13_24.facts.design_doc` 中移除 `path`，并把 `exists` 改回 `false`。
6. 在 `ST13_24.facts.implementation_doc` 中移除 `path`，并把 `exists` 改回 `false`。
7. 在 `ST13_25.facts.design_doc` 中移除 `path`，并把 `exists` 改回 `false`。
8. 在 `ST13_25.facts.implementation_doc` 中移除 `path`，并把 `exists` 改回 `false`。
9. 撤销 `TASK_INDEX.md`、`MODULE_INDEX.md` 和总控文档中关于 `double_doc_registered` / W13-E8.5 的同步描述。
10. 如需撤销本说明文档，应同步从 `AGENTS.md` 索引移除本文件。
11. 回退后必须执行：

```bash
python -m tools.doc_governor.cli validate-state --input docs/governance/DOC_STATE.yaml
python -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml
```

回退后预期仍为 `ok=true,error=0,warning=0`，且 `missing_required_doc_slot` 回到本窗口前的 `50`。

## 10. 当前不进入实现说明

本窗口只完成 required doc slot 登记。以下状态仍保持：

- `implementation_doc_state=missing`
- `readiness=blocked`
- `candidate_status=none`
- `review_status=unreviewed`
- `formal_window_open=false`

因此当前仍不能进入实现，不能生成 implementation packet，不能打开 formal window。

## 11. 后续建议

1. 进入 W13-E9：只细化 `ST13_21 / ST13_20 / ST13_24 / ST13_25` 的 API、数据、测试和治理 contract。
2. 后续 W13-E10 再复核 readiness、acceptance criteria、required tests、implementation scope 和模块 blocker。
3. 后续 W13-E11 才能评估 formal window 候选；是否打开 formal window 仍需用户另窗确认。

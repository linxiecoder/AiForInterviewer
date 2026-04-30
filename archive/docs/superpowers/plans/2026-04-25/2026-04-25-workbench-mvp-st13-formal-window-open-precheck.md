---
title: 2026-04-25-workbench-mvp-st13-formal-window-open-precheck
type: note
permalink: ai-for-interviewer/archive/docs/superpowers/plans/2026-04-25/2026-04-25-workbench-mvp-st13-formal-window-open-precheck
---

# AI 模拟面试一期工作台 MVP ST13 formal window open 前置确认

## 1. 背景

本文件记录 `W13-E15` formal window open 前置确认结果，输入来自 `W13-E14-Merge` 已合并的 formal window 前置材料补齐结果，以及正式 `docs/governance/DOC_STATE.yaml` 的当前工具预检输出。

本窗口只做前置确认、候选范围判断、风险复核、状态写入方案设计和用户确认卡输出；不直接打开 formal window，不修改 `DOC_STATE.yaml`，不生成 implementation packet，不标记 implementation-ready，不进入代码实现，不写 Basic Memory。

## 2. 当前状态摘要

### 2.1 Git 与状态验证

| 检查项 | 结果 |
| --- | --- |
| `git status --short` | 空 |
| `git status -sb` | `## main...origin/main` |
| `origin/main...HEAD` | `0 0` |
| `validate-state` | `ok=true,error=0,warning=0` |
| `evaluate-state` | `ok=true,error=0,warning=0,documents_blocked_count=0` |

### 2.2 preflight 摘要

| ST13 | gate_result | can_open_formal_window | can_generate_implementation_packet | can_mark_implementation_ready | 主要 blockers |
| --- | --- | --- | --- | --- | --- |
| `ST13_24` | `blocked` | `false` | `false` | `false` | `formal_window_closed`、`official_readiness_blocked`、`acceptance_criteria_missing`、`implementation_doc_not_active`、`implementation_scope_unclear`、`required_tests_missing` |
| `ST13_25` | `blocked` | `false` | `false` | `false` | `formal_window_closed`、`official_readiness_blocked`、`acceptance_criteria_missing`、`implementation_doc_not_active`、`implementation_scope_unclear`、`required_tests_missing` |

说明：

- `required_doc_slots.all_present=true` 且 `all_non_template=true`，说明 `ST13_24 / ST13_25` 的 DESIGN / IMPLEMENTATION 双文档路径已登记且非模板。
- `candidate.formal_window_candidate_recommended=true`，说明 facts-only candidate 推荐事实已写入正式状态层。
- 工具层仍将 `acceptance_criteria`、`required_tests`、`implementation_scope` 判定为未进入 implementation packet inputs；这不否认双文档正文已经补齐材料，但表示正式状态 / packet gate 尚未识别为可开窗或可生成 packet。
- `implementation_doc_state=missing`、`candidate_status=none`、`readiness=blocked`、`formal_window_open=false` 仍是正式状态层事实。

## 3. ST13_24 前置复核

| 复核项 | 结论 |
| --- | --- |
| facts-only candidate 推荐 | 存在，正式状态层 `facts.formal_window_candidate_recommended=true` |
| DESIGN / IMPLEMENTATION 双文档 | 存在，且 required doc slot 非模板 |
| required doc slot | 已登记，但只是必要非充分条件 |
| acceptance criteria | 文档层已明确，工具层 preflight 尚未识别为 packet input |
| required tests | 文档层已明确，工具层 preflight 尚未识别为 packet input |
| implementation scope | 文档层已明确，工具层 preflight 尚未识别为 packet input |
| allowed paths | 文档层已明确，未来涉及 `tests/**` 必须另窗授权 |
| forbidden paths | 文档层已明确，当前禁止 `tests/**`、`apps/**`、`infra/**`、`tools/**`、`docs/governance/**`、Basic Memory 等 |
| formal window 前置条件 | 已明确，但仍需用户另窗确认和状态治理执行 |
| implementation packet 前置条件 | 已明确，formal window 未打开前禁止生成 |
| 回退策略 | 已明确，状态回退必须另开 State Update 或治理窗口 |
| preflight 当前 gate_result | `blocked` |
| 当前 blockers | `formal_window_closed`、`official_readiness_blocked`、`acceptance_criteria_missing`、`implementation_doc_not_active`、`implementation_scope_unclear`、`required_tests_missing` |
| 是否可进入 formal window open 用户确认窗口 | 可以 |
| 是否可直接打开 formal window | 不可以，本窗口不执行开窗 |
| 是否可生成 implementation packet | 不可以 |
| 是否可进入实现 | 不可以 |

结论：`ST13_24 / WT13-24` 适合作为后续 formal window open 执行窗口的保守试点候选，但本轮只能输出用户确认卡和状态写入方案草案。

## 4. ST13_25 前置复核

| 复核项 | 结论 |
| --- | --- |
| facts-only candidate 推荐 | 存在，正式状态层 `facts.formal_window_candidate_recommended=true` |
| DESIGN / IMPLEMENTATION 双文档 | 存在，且 required doc slot 非模板 |
| required doc slot | 已登记，但只是必要非充分条件 |
| 收口标准 | 文档层已明确 |
| Basic Memory 授权边界 | 已明确，当前默认不写 Basic Memory，未来必须另窗授权 |
| fallback 包 | 已明确，写回失败或不可用时必须输出可复制 fallback 包 |
| Superpowers 更新规则 | 已明确，不得替代 `DOC_STATE.yaml` 或 gate 结果 |
| 文档治理 DoD | 已明确，覆盖唯一事实源、OQ/DD/backlog、状态验证、过时表述、孤立文档和中文规则检查 |
| allowed paths | 文档层已明确，未来治理收口文件和 Basic Memory 必须另窗授权 |
| forbidden paths | 文档层已明确，当前禁止 `DOC_STATE.yaml`、Basic Memory、实现目录和测试目录 |
| formal window 前置条件 | 已明确，但仍需用户另窗确认和状态治理执行 |
| implementation packet 前置条件 | 已明确，治理任务通常不应生成业务 implementation packet |
| preflight 当前 gate_result | `blocked` |
| 当前 blockers | `formal_window_closed`、`official_readiness_blocked`、`acceptance_criteria_missing`、`implementation_doc_not_active`、`implementation_scope_unclear`、`required_tests_missing` |
| 是否可进入 formal window open 用户确认窗口 | 可以 |
| 是否可直接打开 formal window | 不可以，本窗口不执行开窗 |
| 是否可生成 implementation packet | 不可以 |
| 是否可进入实现 | 不可以 |
| 是否可直接写 Basic Memory | 不可以 |

结论：`ST13_25 / WT13-25` 可作为后续 formal window open 候选，但 Basic Memory / Superpowers 写回边界更容易被误读，默认不作为第一试点。

## 5. ST13_21 / ST13_20 near-ready 保持说明

| ST13 | 当前保持结论 | 不进入本轮 open 的原因 |
| --- | --- | --- |
| `ST13_21 / WT13-21` | 继续保持文档层 `near_ready_for_formal_window_candidate_confirmed` | M02 blocker、OpenAPI、`apps/api/**`、schema / DTO / shared contract 授权、`ST13_20` 数据 contract 联动仍未闭合 |
| `ST13_20 / WT13-20` | 继续保持文档层 `near_ready_for_formal_window_candidate_confirmed` | M02 blocker、schema / migration / ORM、PostgreSQL 连接 / 配置 / rollback、`ST13_21` API contract 联动仍未闭合 |

本窗口不为 `ST13_21 / ST13_20` 写 `candidate_status`，不写 facts-only formal window candidate，不进入 formal window open，不生成 packet，不创建 OpenAPI、schema、`apps/api/**`、migration、ORM 或测试文件。

## 6. formal window open 方案

### 6.1 推荐方案

推荐方案：后续单独开 formal window open 执行窗口，只打开 `ST13_24`。

推荐理由：

- `ST13_24` 是测试 / 验收 / DoD，适合作为第一个 formal window open 试点。
- 它不需要写 Basic Memory，不直接创建业务实现目录，也能验证 formal window gate 到 packet gate 的后续链路。
- 后续仍需严格拆分 open window、packet、实现三段式门禁。

### 6.2 方案选项

| 方案 | 内容 | 影响 |
| --- | --- | --- |
| A | 暂不进入 formal window open，继续保留 candidate facts | 风险最低，但 `ST13_24 / ST13_25` 继续停留候选事实层 |
| B | 后续单独窗口只打开 `ST13_24` | 推荐；测试 / 验收 / DoD 作为保守试点 |
| C | 后续单独窗口只打开 `ST13_25` | 可选；需严格避免误写 Basic Memory |
| D | 后续单独窗口同时打开 `ST13_24` 和 `ST13_25` | 推进最快但范围更大，不推荐作为第一步 |
| E | 自定义方案 | 由用户补充 |

## 7. packet 与实现继续禁止说明

- formal window open 与 implementation packet 必须拆窗。
- 即使后续 formal window open 成功，也不等于 `implementation_doc_state=active_working_doc`，不等于 packet inputs 已完整，不等于 implementation-ready。
- 本窗口不生成 packet；后续 open-window 执行窗口也不应同窗生成 packet。
- 本窗口不进入实现；后续 formal window open 成功后，仍需 packet 准备和用户确认。

## 8. State Update 执行方案草案

后续 formal window open 执行窗口建议流程：

1. 重新执行 `git status --short`、`git status -sb`、`git rev-list --left-right --count origin/main...HEAD`。
2. 重新执行 `validate-state` 与 `evaluate-state`，要求 `ok=true,error=0,warning=0`，且 `documents_blocked_count=0`。
3. 重新运行 `preflight-open-window --subtask <ST13>`，记录 gate 结果。
4. 根据用户确认只选择一个目标，默认建议 `ST13_24`。
5. 通过当前工具认可的正式流程修改 `DOC_STATE.yaml` 中目标 ST13 的 formal window 相关字段；如果工具语义不清，先输出确认卡，不执行。
6. 不修改 `candidate_status=candidate`，除非工具规则明确要求且通过预检。
7. 不生成 implementation packet，不标记 implementation-ready，不进入实现。
8. 修改后重新执行 `validate-state`、`evaluate-state` 和目标 preflight。
9. 输出 formal window 状态变化、剩余 blockers、是否可以进入 packet 准备窗口。

## 9. 用户确认卡

### 确认卡 1 / OQ-125：是否允许进入 formal window open 执行窗口？

问题：是否允许后续单独窗口打开 `ST13_24 / ST13_25` 的 formal window？

背景：`ST13_24 / ST13_25` 已具备文档层 candidate 推荐和 facts-only 状态记录，且前置材料已补齐。但 preflight 当前仍 blocked，因为 formal window 仍关闭、implementation packet 仍 forbidden、implementation-ready 仍 false。本窗口只做前置确认，不直接开窗。

| 方案 | 内容 | 风险 / 限制 |
| --- | --- | --- |
| A | 暂不进入 formal window open，继续保留 candidate facts | 风险最低，但无法推进到 packet 前置 |
| B | 后续单独开 formal window open 窗口，只打开 `ST13_24` | 推荐；试点风险相对可控 |
| C | 后续单独开 formal window open 窗口，只打开 `ST13_25` | 可选；需严防误写 Basic Memory |
| D | 后续单独开 formal window open 窗口，同时打开 `ST13_24` 和 `ST13_25` | 不推荐作为第一步，后续 gate 更复杂 |
| E | 自定义方案 | 由用户补充 |

推荐方案：B。

状态：`proposed-default`，等待用户确认。

### 确认卡 2 / OQ-126：formal window open 后是否允许立即生成 implementation packet？

问题：如果后续打开 `ST13_24` 或 `ST13_25` formal window，是否允许同一窗口生成 implementation packet？

| 方案 | 内容 |
| --- | --- |
| A | 不允许。同一窗口只打开 formal window，packet 必须另开窗口并通过 preflight / packet gate。推荐 |
| B | 允许在 formal window open 成功后，同一窗口尝试生成 packet dry-run。不推荐 |
| C | 允许直接生成正式 implementation packet。禁止推荐 |
| D | 自定义方案 |

推荐方案：A。

状态：`proposed-default`，等待用户确认。

### 确认卡 3 / OQ-127：formal window open 后是否允许进入实现？

问题：如果后续 formal window open 成功，是否允许立刻进入代码实现？

| 方案 | 内容 |
| --- | --- |
| A | 不允许。formal window open 后仍需 packet 准备和用户确认。推荐 |
| B | 允许同一窗口进入实现。不推荐 |
| C | 允许只做文档实现，不做代码。不推荐作为默认，因为容易混淆 |
| D | 自定义方案 |

推荐方案：A。

状态：`proposed-default`，等待用户确认。

## 10. 下一步建议

1. 等待用户确认 `OQ-125~OQ-127`。
2. 若用户确认推荐组合，下一窗口只执行 `ST13_24` formal window open 状态治理动作。
3. 下一窗口不得同窗生成 implementation packet，不得进入实现，不得创建 `tests/**`、`apps/**`、`infra/**`、`tools/**`。
4. `ST13_25` 可作为第二个治理任务候选，但应在 Basic Memory / Superpowers 授权边界再次确认后再进入 open。
5. `ST13_21 / ST13_20` 继续保持 near-ready，不进入本轮 formal window open。
---
title: 2026-04-25-workbench-mvp-st13-first-contract-formal-window-candidate-evaluation
type: note
permalink: ai-for-interviewer/archive/docs/superpowers/plans/2026-04-25/2026-04-25-workbench-mvp-st13-first-contract-formal-window-candidate-evaluation
---

# AI 模拟面试一期工作台 MVP ST13 第一批 formal window candidate 评估

## 1. 背景

本文档记录 `W13-E11 / 第一批 ST13 formal window candidate 评估窗口` 的评估结果。

输入来自：

- `W13-E8` 创建的 `ST13_21 / ST13_20 / ST13_24 / ST13_25` 正式双文档。
- `W13-E8.5` 完成的 `facts.design_doc` / `facts.implementation_doc` required doc slot 登记。
- `W13-E9` 完成的四个 ST13 contract 细化。
- `W13-E10` 完成的 readiness review。
- 用户已确认 `OQ-114=A`、`OQ-115=B`、`OQ-116=A`、`OQ-117=A`。

本窗口只做文档层 formal window candidate 评估和后续 State Update 建议；不修改 `DOC_STATE.yaml`，不打开 formal window，不生成 implementation packet，不标记 implementation-ready，不写代码。

## 2. 基线验证

W13-E11 开始前已执行：

- `python -m tools.doc_governor.cli validate-state --input docs/governance/DOC_STATE.yaml`
- `python -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml`

基线结果：

- `validate-state`：`ok=true,error=0,warning=0`
- `evaluate-state`：`ok=true,error=0,warning=0`
- `documents_blocked_count=0`
- `modules_blocked_count=1`
- `subtasks_blocked_count=25`

该结果说明状态层仍未放行 implementation-ready；W13-E11 只能给出文档层 candidate 建议。

## 3. 用户确认吸收

| OQ | 用户确认 | W13-E11 吸收结果 |
| --- | --- | --- |
| `OQ-114` | 方案 A | 接受 W13-E10 分级：`ST13_24 / ST13_25 = ready_for_formal_window_candidate`，`ST13_21 / ST13_20 = near_ready_for_formal_window_candidate`。 |
| `OQ-115` | 方案 B | W13-E11 后再开 State Update；本窗口不修改 `DOC_STATE.yaml`。 |
| `OQ-116` | 方案 A | 不新增 W13-E10.5，直接完成 W13-E11 candidate 评估。 |
| `OQ-117` | 方案 A | 继续禁止 OpenAPI、schema、`tests/**`、`apps/**`、implementation packet、formal window open 和代码实现，直到后续另窗确认。 |

## 4. formal window candidate 评估标准

本窗口采用以下文档层标准：

1. 双文档存在，且已登记到 `DOC_STATE.yaml` 的 `facts.design_doc` / `facts.implementation_doc`。
2. 双文档 `template_like=false`，且完成 contract_refined 级细化。
3. acceptance criteria、required tests、implementation scope、allowed / forbidden paths、formal window 前置条件、implementation packet 前置条件可被后续 State Update 或 formal window 使用。
4. 不存在 required doc slot 旧表述。
5. 不存在把 readiness review 写成 implementation-ready、formal window open 或 packet-ready 的误写。
6. 仍明确禁止当前窗口实现、创建目录、创建测试、生成 packet 或打开 formal window。

## 5. ST13_21 评估

| 项 | 结论 |
| --- | --- |
| 任务 | `ST13_21 / WT13-21`：API / 后端服务边界 |
| W13-E10 分级 | `near_ready_for_formal_window_candidate` |
| W13-E11 评估结论 | 接受 near-ready 分级；暂不建议直接写为状态层 `candidate_status=candidate` |
| 可用输入 | API 分组、Auth、Account / Role / Permission、Job、Resume、KnowledgeBase、Retrieval、Interview、Question / Follow-up、Answer、Feedback / Score、SessionRecord、Markdown Export、Admin、Health / Config / Observability、错误 contract 已细化 |
| 仍未闭合 | M02 权限文档 blocker、未来 OpenAPI 文件授权、`apps/api/**` 授权、State Update、formal window 用户确认 |
| 后续 State Update 建议 | 可记录为 API contract near-ready，但不建议在 M02 blocker 未处理前写成 formal window candidate |
| 当前禁止 | 不创建 OpenAPI，不创建 `apps/api/**`，不生成 packet，不实现 |

## 6. ST13_20 评估

| 项 | 结论 |
| --- | --- |
| 任务 | `ST13_20 / WT13-20`：服务端保存 / 数据库 |
| W13-E10 分级 | `near_ready_for_formal_window_candidate` |
| W13-E11 评估结论 | 接受 near-ready 分级；暂不建议直接写为状态层 `candidate_status=candidate` |
| 可用输入 | User / Account / Role / Permission、Job、Resume、KnowledgeBase、KnowledgeDocument / Chunk、Retrieval、Interview、Answer、Feedback、Score、Weakness、Asset、Export、LLM 生成、脱敏、归档、审计、schema version contract 已细化 |
| 仍未闭合 | M02 权限文档 blocker、未来 schema / migration / ORM 授权、State Update、formal window 用户确认 |
| 后续 State Update 建议 | 可记录为数据 contract near-ready，但不建议在 M02 blocker 和 schema 授权未处理前写成 formal window candidate |
| 当前禁止 | 不创建数据库，不创建 migration，不创建 ORM，不写 SQL 或代码 |

## 7. ST13_24 评估

| 项 | 结论 |
| --- | --- |
| 任务 | `ST13_24 / WT13-24`：测试 / 验收 / DoD |
| W13-E10 分级 | `ready_for_formal_window_candidate` |
| W13-E11 评估结论 | 接受 ready 分级；建议后续 State Update 评估是否写入 `candidate_status=candidate` 或等价候选字段 |
| 可用输入 | 产品、数据、UI、工程、收口 DoD，API / 数据库 / RAG / LLM / 多轮 / 打磨 / 压力面 / 评分 / 导出 / 错误态 / 权限 / 安全 / 隐私测试 contract 已细化 |
| 仍未闭合 | 状态层 candidate 写入、formal window 用户确认、测试文件创建授权 |
| 后续 State Update 建议 | 可作为第一批优先 candidate 更新对象 |
| 当前禁止 | 不创建 `tests/**`，不写测试代码，不生成 packet |

## 8. ST13_25 评估

| 项 | 结论 |
| --- | --- |
| 任务 | `ST13_25 / WT13-25`：文档治理 / 收口 / Basic Memory |
| W13-E10 分级 | `ready_for_formal_window_candidate` |
| W13-E11 评估结论 | 接受 ready 分级；建议后续 State Update 评估是否写入 `candidate_status=candidate` 或等价候选字段 |
| 可用输入 | 唯一事实源、OQ / DD / backlog-roadmap、State Write、archive、Basic Memory 检索与回读、fallback 包、Superpowers、确认闭环、收口报告、过时检查、引用检查 contract 已细化 |
| 仍未闭合 | 状态层 candidate 写入、formal window 用户确认、Basic Memory / Superpowers 写回授权 |
| 后续 State Update 建议 | 可作为第一批优先 candidate 更新对象 |
| 当前禁止 | 不写 Basic Memory，不做 Superpowers 外部写回，不生成 packet |

## 9. 候选分级结论

| ST13 | W13-E11 文档层结论 | 是否建议后续 State Update 写 candidate | 是否可进入实现 |
| --- | --- | --- | --- |
| `ST13_21` | `near_ready_for_formal_window_candidate_confirmed` | 否，先保留 near-ready 解释 | 否 |
| `ST13_20` | `near_ready_for_formal_window_candidate_confirmed` | 否，先保留 near-ready 解释 | 否 |
| `ST13_24` | `formal_window_candidate_recommended` | 是，建议后续 State Update 评估写入 | 否 |
| `ST13_25` | `formal_window_candidate_recommended` | 是，建议后续 State Update 评估写入 | 否 |

本表不等于正式 `DOC_STATE.yaml.candidate_status=candidate`，不等于 formal window open，不等于 implementation-ready。

## 10. 后续 State Update 建议

根据 `OQ-115=B`，建议 W13-E11 后另开 State Update 窗口，且至少评估：

1. 将 `OQ-114~OQ-117` 的确认结果作为状态更新依据之一，但不直接等同于实现放行。
2. 对 `ST13_24 / ST13_25` 评估是否写入 `candidate_status=candidate` 或当前 schema 支持的等价候选表达。
3. 对 `ST13_21 / ST13_20` 保留 near-ready 解释，不直接写为 `candidate_status=candidate`，除非先处理 M02 blocker 或用户另行确认。
4. 不修改 `formal_window_open` 为 true。
5. 不修改 implementation-ready。
6. 不生成 implementation packet。
7. 若状态 schema 不支持 near-ready 字段，near-ready 仅保留在文档层，不强行写入结构化状态。

### 10.1 W13-E12 State Update 准备承接

W13-E12 已新增 `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-state-update-plan.md`，用于承接本节建议并输出字段影响分析、写入方案、验证矩阵、回退方案和 `OQ-118~OQ-120` 确认卡。

W13-E12 结论只表示后续可进入 State Update Preview 的准备状态：

1. `ST13_24 / ST13_25` 建议在 W13-E13 preview 中测试 candidate 相关字段，但仍保持 `formal_window_open=false` 和 `implementation-ready=false`。
2. `ST13_21 / ST13_20` 默认只保留文档层 near-ready，不写 `candidate_status=candidate`。
3. W13-E12 未修改正式 `DOC_STATE.yaml`，未打开 formal window，未生成 implementation packet，未进入实现。

## 11. 下一窗口建议

W13-E12 已完成 State Update 准备。推荐下一窗口为 `W13-E13 / 第一批 ST13 candidate State Update Preview 窗口`，只创建 preview YAML，不修改正式 `DOC_STATE.yaml`。

备选后续：

1. `W13-E13`：基于 W13-E12 确认卡创建 candidate state preview，不直接实现。
2. `M02 blocker` 专项窗口：补权限 / open_questions 模块 blocker，使 `ST13_21 / ST13_20` 从 near-ready 进入 ready。
3. `W13-F2`：在用户授权后做 Basic Memory / Superpowers 写回。

不建议下一步直接进入实现。

## 12. 当前不进入实现说明

W13-E11 不放行以下事项：

- 不修改 `DOC_STATE.yaml`。
- 不打开 formal window。
- 不生成 implementation packet。
- 不标记 implementation-ready。
- 不创建 `apps/**`、`infra/**`、`tools/**`、`tests/**`。
- 不创建 OpenAPI、schema、migration、ORM、测试文件或应用目录。
- 不写 Basic Memory。
- 不写代码。

## 13. 完成标准

W13-E11 完成后应满足：

1. `OQ-114~OQ-117` 已从 proposed-default 回写为 confirmed。
2. `ST13_24 / ST13_25` 已形成文档层 `formal_window_candidate_recommended`。
3. `ST13_21 / ST13_20` 已形成文档层 `near_ready_for_formal_window_candidate_confirmed`。
4. 已明确后续 State Update 需求。
5. 未修改 `DOC_STATE.yaml`。
6. 未进入实现，未生成 packet，未打开 formal window。
7. `validate-state / evaluate-state` 仍为 `ok=true,error=0,warning=0`。

## 14. W13-E13 Preview 回写

W13-E13 已按用户确认 `OQ-118=B`、`OQ-119=A`、`OQ-120=B` 创建 candidate state preview：

`docs/superpowers/plans/2026-04-25-workbench-mvp-st13-candidate-state-preview.yaml`

Preview 中 `ST13_24 / ST13_25` 尝试写入 `candidate_status=candidate`、`review_status=pending_confirmation`、`readiness=downstream_ready`；`ST13_21 / ST13_20` 保持正式状态原样，只保留文档层 near-ready。

验证结论：Preview 未通过。失败原因为当前规则禁止在 `formal_window_open=false` 时写入 `candidate_status=candidate`，且 `readiness=downstream_ready` 要求目标 `maturity` 非空。

因此，本评估文档中的 `formal_window_candidate_recommended` 仍只表示文档层推荐，不等于正式 `DOC_STATE.yaml` candidate 已写入，不等于 formal window 已打开，不等于 implementation-ready。后续不建议直接进入 W13-E14 正式 State Update，需先确认 `OQ-121`。

## 15. W13-E13.5 策略修正回写

用户已确认 `OQ-121=A`：暂不执行正式 State Update，只保留失败 Preview，并先修正后续状态表达策略。

基于 W13-E13 的验证结果，本评估文档中的候选分级需要按以下口径理解：

| ST13 | 文档层结论 | 状态层修正口径 |
| --- | --- | --- |
| `ST13_21` | `near_ready_for_formal_window_candidate_confirmed` | 继续只保留文档层 near-ready；不写 `candidate_status`，不写 `readiness=downstream_ready`。 |
| `ST13_20` | `near_ready_for_formal_window_candidate_confirmed` | 继续只保留文档层 near-ready；不写 `candidate_status`，不写 `readiness=downstream_ready`。 |
| `ST13_24` | `formal_window_candidate_recommended` | 正式状态层暂不写 `candidate_status=candidate`；下一轮优先验证 facts-only 表达，备选验证 `candidate_status=observe`。 |
| `ST13_25` | `formal_window_candidate_recommended` | 正式状态层暂不写 `candidate_status=candidate`；下一轮优先验证 facts-only 表达，备选验证 `candidate_status=observe`。 |

该修正不撤回 W13-E11 的文档层候选推荐，但明确其不能直接映射为正式 `DOC_STATE.yaml.candidate_status=candidate`。在新的 Candidate Preview 全绿并经用户确认前，不进入 `W13-E14`，不打开 formal window，不生成 implementation packet，不进入实现。

## 16. W13-E13.6 facts-only Preview 回写

用户已确认 `OQ-122=A`、`OQ-123=A`。W13-E13.6 已创建 facts-only Candidate Preview：

`docs/superpowers/plans/2026-04-25-workbench-mvp-st13-candidate-state-facts-preview.yaml`

本评估文档中的候选分级继续按以下口径理解：

| ST13 | 文档层结论 | W13-E13.6 Preview 表达 | 状态层边界 |
| --- | --- | --- | --- |
| `ST13_21` | `near_ready_for_formal_window_candidate_confirmed` | 不写 candidate facts | 不写 `candidate_status`，不写 `readiness=downstream_ready`。 |
| `ST13_20` | `near_ready_for_formal_window_candidate_confirmed` | 不写 candidate facts | 不写 `candidate_status`，不写 `readiness=downstream_ready`。 |
| `ST13_24` | `formal_window_candidate_recommended` | 仅在 `facts` 下写入 `formal_window_candidate_recommended=true` 等推荐事实 | 不写 `candidate_status=candidate`，不写 `readiness=downstream_ready`。 |
| `ST13_25` | `formal_window_candidate_recommended` | 仅在 `facts` 下写入 `formal_window_candidate_recommended=true` 等推荐事实 | 不写 `candidate_status=candidate`，不写 `readiness=downstream_ready`。 |

Preview `validate-state / evaluate-state` 均为 `ok=true,error=0,warning=0`，但完整 Preview `documents_blocked_count=1` 来自 plan-path Preview 的 document 扫描根目录副作用。该结果不撤回 `ST13_24 / ST13_25` 的文档层 candidate 推荐，但在用户确认 `OQ-124` 前，不进入正式 State Update，不打开 formal window，不生成 implementation packet，不进入实现。

## 17. W13-E13.8 facts-only 正式 State Update 回写

用户已确认 `OQ-124` 方案 A：把 facts-only Preview 放到 `docs/governance/previews/` 下重新验证；Preview 严格全绿后，再执行 facts-only 正式 State Update。

W13-E13.8 已新增：

- `docs/governance/previews/DOC_STATE_W13_E13_8_CANDIDATE_FACTS_PREVIEW.yaml`

验证结果：

| 对象 | validate-state | evaluate-state |
| --- | --- | --- |
| docs/governance/previews 路径 Preview | `ok=true,error=0,warning=0` | `ok=true,error=0,warning=0,documents_blocked_count=0,modules_blocked_count=1,subtasks_blocked_count=25` |
| 正式 `DOC_STATE.yaml` 写入后 | `ok=true,error=0,warning=0` | `ok=true,error=0,warning=0,documents_blocked_count=0,modules_blocked_count=1,subtasks_blocked_count=25` |

| ST13 | 文档层结论 | W13-E13.8 正式状态层表达 | 状态层边界 |
| --- | --- | --- | --- |
| `ST13_20` | `near_ready_for_formal_window_candidate_confirmed` | 不写 candidate facts；保持正式状态原样 | 不升级为 candidate。 |
| `ST13_21` | `near_ready_for_formal_window_candidate_confirmed` | 不写 candidate facts；保持正式状态原样 | 不升级为 candidate。 |
| `ST13_24` | `formal_window_candidate_recommended` | 在 `facts` 下写入 `formal_window_candidate_recommended=true` 等推荐事实 | 不写 `candidate_status=candidate`，不写 `readiness=downstream_ready`。 |
| `ST13_25` | `formal_window_candidate_recommended` | 在 `facts` 下写入 `formal_window_candidate_recommended=true` 等推荐事实 | 不写 `candidate_status=candidate`，不写 `readiness=downstream_ready`。 |

该回写只表示 candidate 推荐事实已进入正式状态层；formal window 仍关闭，implementation-ready 仍为 false，implementation packet 仍禁止生成，仍不得进入实现。
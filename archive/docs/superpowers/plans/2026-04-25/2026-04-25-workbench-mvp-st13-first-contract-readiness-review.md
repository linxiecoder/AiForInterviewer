---
title: 2026-04-25-workbench-mvp-st13-first-contract-readiness-review
type: note
permalink: ai-for-interviewer/archive/docs/superpowers/plans/2026-04-25/2026-04-25-workbench-mvp-st13-first-contract-readiness-review
---

# AI 模拟面试一期工作台 MVP ST13 第一批 contract readiness 复核

## 1. 背景

本文档记录 `W13-E10 / 第一批 ST13 readiness 复核窗口` 的复核结果。

W13-E11 更新：用户已确认 `OQ-114=A`、`OQ-115=B`、`OQ-116=A`、`OQ-117=A`；确认后的 formal window candidate 评估记录见 `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-first-contract-formal-window-candidate-evaluation.md`。

本窗口承接以下已完成事实：

1. W13-E8 已创建 `ST13_21 / ST13_20 / ST13_24 / ST13_25` 的正式 DESIGN / IMPLEMENTATION 双文档。
2. W13-E8.5 已将上述 8 个双文档登记到 `DOC_STATE.yaml` 既有 `facts.design_doc` / `facts.implementation_doc` slot，且 `exists=true`、`template_like=false`。
3. W13-E9 已清理 required doc slot 过时表述，并将四个目标 ST13 推进到 `contract_refined`。

本窗口只做 readiness review、缺口审计、formal window candidate 判断和下一步确认卡输出；不写代码，不创建实现目录，不修改 `DOC_STATE.yaml`，不生成 implementation packet，不打开 formal window，不标记 implementation-ready。

## 2. 复核范围

| ST13 | WT13 alias | 主题 | 本轮动作 |
| --- | --- | --- | --- |
| `ST13_21` | `WT13-21` | API / 后端服务边界 | readiness review |
| `ST13_20` | `WT13-20` | 服务端保存 / 数据库 | readiness review |
| `ST13_24` | `WT13-24` | 测试 / 验收 / DoD | readiness review |
| `ST13_25` | `WT13-25` | 文档治理 / 收口 / Basic Memory | readiness review |

不得扩大到其他 ST13；不得创建新的 ST13 双文档；不得创建 `apps/**`、`infra/**`、`tools/**`、`tests/**`；不得写 Basic Memory。

## 3. 基线验证

W13-E10 开始前已执行：

| 命令 | 结果 |
| --- | --- |
| `python -m tools.doc_governor.cli validate-state --input docs/governance/DOC_STATE.yaml` | `ok=true`，`error=0`，`warning=0` |
| `python -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml` | `ok=true`，`error=0`，`warning=0`，`documents_blocked_count=0` |

基线 `evaluate-state` 仍显示 `subtasks_blocked_count=25`，并保留 `formal_window_closed`、`implementation_doc_not_active`、`acceptance_criteria_missing`、`required_tests_missing`、`implementation_scope_unclear` 等实现层 blocker。这些 blocker 说明当前只能做候选复核，不能进入实现。

## 4. ST13_21 readiness 复核

| 检查项 | 结论 |
| --- | --- |
| 双文档是否存在 | 是 |
| `facts.design_doc` 是否已登记 | 是，W13-E8.5 已登记 |
| `facts.implementation_doc` 是否已登记 | 是，W13-E8.5 已登记 |
| DESIGN 文档是否非模板 | 是，`template_like=false` |
| IMPLEMENTATION 文档是否非模板 | 是，`template_like=false` |
| contract 是否已细化 | 是，API / Auth / Account / Job / Resume / Knowledge / Retrieval / Interview / Score / Export / Error / LLM-RAG failure 已细化 |
| acceptance criteria 是否明确 | 文档层明确；状态层尚未写入 implementation packet inputs |
| required tests 是否明确 | 文档层明确；状态层尚未写入 implementation packet inputs |
| implementation scope 是否明确 | 文档层明确；状态层 `allowed_modify_paths` 仍未激活 |
| allowed paths 是否明确 | 文档层明确；当前窗口仍不得创建 `apps/api/**` |
| forbidden paths 是否明确 | 明确，禁止 `DOC_STATE.yaml`、`apps/**`、`infra/**`、`tools/**`、`tests/**` 等 |
| formal window 前置条件是否明确 | 明确，需用户另窗确认并经状态层处理 |
| implementation packet 前置条件是否明确 | 明确，当前禁止生成 |
| 是否仍有用户确认项 | 有：是否列为 formal window candidate、是否允许后续 State Update、是否允许未来 OpenAPI / `apps/api/**` |
| 是否仍缺 contract | 文档层不缺第一轮 contract；后续 OpenAPI/schema 仍需确认 |
| 是否仍缺测试要求 | 文档层不缺；状态层仍未闭合 |
| 是否仍缺验收标准 | 文档层不缺；状态层仍未闭合 |
| 是否仍存在 required doc slot 旧表述 | 未发现与 W13-E8.5 事实冲突的旧表述 |
| 是否存在 implementation-ready 误写 | 未发现；均为 `not implementation-ready` |
| 是否存在 formal window 误写 | 未发现；均为 `formal window closed` |
| 是否存在 implementation packet 误写 | 未发现；均为 `implementation packet forbidden` |
| 是否可作为 formal window candidate | `near_ready_for_formal_window_candidate` |
| 是否可进入实现 | 否 |
| 是否可生成 implementation packet | 否 |
| 结论 | API contract 已达到候选复核输入质量，但 `ST13_21` 仍受 M02 权限边界、状态层未激活和用户确认项约束；建议进入 W13-E11 候选评估，不直接标记 candidate |

## 5. ST13_20 readiness 复核

| 检查项 | 结论 |
| --- | --- |
| 双文档是否存在 | 是 |
| `facts.design_doc` 是否已登记 | 是，W13-E8.5 已登记 |
| `facts.implementation_doc` 是否已登记 | 是，W13-E8.5 已登记 |
| DESIGN 文档是否非模板 | 是，`template_like=false` |
| IMPLEMENTATION 文档是否非模板 | 是，`template_like=false` |
| contract 是否已细化 | 是，User / Account / Role / Permission、Job、Resume、Knowledge、Retrieval、Interview、Score、Asset、Export、LLM generation、审计、脱敏、schema version 已细化 |
| acceptance criteria 是否明确 | 文档层明确；状态层尚未写入 implementation packet inputs |
| required tests 是否明确 | 文档层明确；状态层尚未写入 implementation packet inputs |
| implementation scope 是否明确 | 文档层明确；状态层 `allowed_modify_paths` 仍未激活 |
| allowed paths 是否明确 | 文档层明确；当前窗口仍不得创建数据库、migration、ORM 或 SQL |
| forbidden paths 是否明确 | 明确，禁止 `DOC_STATE.yaml`、`apps/**`、`infra/**`、`tools/**`、`tests/**` 等 |
| formal window 前置条件是否明确 | 明确，需用户另窗确认并经状态层处理 |
| implementation packet 前置条件是否明确 | 明确，当前禁止生成 |
| 是否仍有用户确认项 | 有：是否列为 formal window candidate、是否允许后续 State Update、是否允许未来 schema / migration / ORM |
| 是否仍缺 contract | 文档层不缺第一轮数据 contract；后续实体 schema 文件仍需确认 |
| 是否仍缺测试要求 | 文档层不缺；状态层仍未闭合 |
| 是否仍缺验收标准 | 文档层不缺；状态层仍未闭合 |
| 是否仍存在 required doc slot 旧表述 | 未发现与 W13-E8.5 事实冲突的旧表述 |
| 是否存在 implementation-ready 误写 | 未发现；均为 `not implementation-ready` |
| 是否存在 formal window 误写 | 未发现；均为 `formal window closed` |
| 是否存在 implementation packet 误写 | 未发现；均为 `implementation packet forbidden` |
| 是否可作为 formal window candidate | `near_ready_for_formal_window_candidate` |
| 是否可进入实现 | 否 |
| 是否可生成 implementation packet | 否 |
| 结论 | 数据 contract 已达到候选复核输入质量，但仍受 M02 权限边界、schema/migration 授权、状态层未激活和用户确认项约束；建议进入 W13-E11 候选评估，不直接标记 candidate |

## 6. ST13_24 readiness 复核

| 检查项 | 结论 |
| --- | --- |
| 双文档是否存在 | 是 |
| `facts.design_doc` 是否已登记 | 是，W13-E8.5 已登记 |
| `facts.implementation_doc` 是否已登记 | 是，W13-E8.5 已登记 |
| DESIGN 文档是否非模板 | 是，`template_like=false` |
| IMPLEMENTATION 文档是否非模板 | 是，`template_like=false` |
| contract 是否已细化 | 是，产品、数据、UI、工程、收口、API、数据库、RAG、LLM、多轮、评分、导出、错误态、权限、安全、临时产物、浏览器验证与测试分层已细化 |
| acceptance criteria 是否明确 | 文档层明确；状态层尚未写入 implementation packet inputs |
| required tests 是否明确 | 文档层明确；状态层尚未写入 implementation packet inputs |
| implementation scope 是否明确 | 文档层明确；当前窗口不创建 `tests/**` |
| allowed paths 是否明确 | 文档层明确；未来需 formal window 另行授权 |
| forbidden paths 是否明确 | 明确，当前禁止 `tests/**`、`tools/**`、`DOC_STATE.yaml` 等 |
| formal window 前置条件是否明确 | 明确，需用户另窗确认并经状态层处理 |
| implementation packet 前置条件是否明确 | 明确，当前禁止生成 |
| 是否仍有用户确认项 | 有：是否列为 formal window candidate、是否允许后续 State Update、是否允许未来测试文件 |
| 是否仍缺 contract | 文档层不缺第一轮测试 / DoD contract |
| 是否仍缺测试要求 | 文档层不缺；状态层仍未闭合 |
| 是否仍缺验收标准 | 文档层不缺；状态层仍未闭合 |
| 是否仍存在 required doc slot 旧表述 | 未发现与 W13-E8.5 事实冲突的旧表述 |
| 是否存在 implementation-ready 误写 | 未发现；均为 `not implementation-ready` |
| 是否存在 formal window 误写 | 未发现；均为 `formal window closed` |
| 是否存在 implementation packet 误写 | 未发现；均为 `implementation packet forbidden` |
| 是否可作为 formal window candidate | `ready_for_formal_window_candidate` |
| 是否可进入实现 | 否 |
| 是否可生成 implementation packet | 否 |
| 结论 | 测试 / 验收 / DoD contract 已具备进入 W13-E11 candidate 评估的文档条件；但本窗口不打开 formal window，不创建 `tests/**`，不标记 implementation-ready |

## 7. ST13_25 readiness 复核

| 检查项 | 结论 |
| --- | --- |
| 双文档是否存在 | 是 |
| `facts.design_doc` 是否已登记 | 是，W13-E8.5 已登记 |
| `facts.implementation_doc` 是否已登记 | 是，W13-E8.5 已登记 |
| DESIGN 文档是否非模板 | 是，`template_like=false` |
| IMPLEMENTATION 文档是否非模板 | 是，`template_like=false` |
| contract 是否已细化 | 是，唯一事实源、OQ/DD/backlog、State Write、archive、Basic Memory、fallback、Superpowers、确认项闭环、收口报告、过时检查、引用检查和未来写回窗口已细化 |
| acceptance criteria 是否明确 | 文档层明确；状态层尚未写入 implementation packet inputs |
| required tests 是否明确 | 文档层明确；状态层尚未写入 implementation packet inputs |
| implementation scope 是否明确 | 文档层明确；当前窗口不写 Basic Memory |
| allowed paths 是否明确 | 文档层明确；未来需 formal window 另行授权 |
| forbidden paths 是否明确 | 明确，当前禁止 `DOC_STATE.yaml`、Basic Memory、实现目录和测试目录 |
| formal window 前置条件是否明确 | 明确，需用户另窗确认并经状态层处理 |
| implementation packet 前置条件是否明确 | 明确，当前禁止生成 |
| 是否仍有用户确认项 | 有：是否列为 formal window candidate、是否允许后续 State Update、是否允许未来 Basic Memory / Superpowers 写回 |
| 是否仍缺 contract | 文档层不缺第一轮治理 contract |
| 是否仍缺测试要求 | 文档层不缺；状态层仍未闭合 |
| 是否仍缺验收标准 | 文档层不缺；状态层仍未闭合 |
| 是否仍存在 required doc slot 旧表述 | 未发现与 W13-E8.5 事实冲突的旧表述 |
| 是否存在 implementation-ready 误写 | 未发现；均为 `not implementation-ready` |
| 是否存在 formal window 误写 | 未发现；均为 `formal window closed` |
| 是否存在 implementation packet 误写 | 未发现；均为 `implementation packet forbidden` |
| 是否可作为 formal window candidate | `ready_for_formal_window_candidate` |
| 是否可进入实现 | 否 |
| 是否可生成 implementation packet | 否 |
| 结论 | 文档治理 / 收口 contract 已具备进入 W13-E11 candidate 评估的文档条件；但本窗口不写 Basic Memory，不打开 formal window，不标记 implementation-ready |

## 8. acceptance criteria 复核

四个 ST13 的 DESIGN / IMPLEMENTATION 双文档均已包含验收标准，并满足以下文档层要求：

1. 与任务目标一致。
2. 可由后续 formal window 或 State Update 转换为 implementation packet input。
3. 不依赖当前窗口写代码。
4. 包含不做事项。
5. 包含失败条件或回退边界。
6. 包含治理验证命令或交接输出要求。

不足仍在状态层：`evaluate-state` 当前仍把 25 个 ST13 的 `acceptance_criteria` 判定为空，因为本窗口未修改 `DOC_STATE.yaml`，也未激活 implementation doc。

## 9. required tests 复核

四个 ST13 的双文档均已包含测试要求：

| ST13 | 文档层测试要求 | 当前限制 |
| --- | --- | --- |
| `ST13_21` | API schema、权限、错误态、LLM / RAG 降级、异步状态、导出 contract | 当前不创建 API 测试代码 |
| `ST13_20` | 数据一致性、schema relation、权限过滤、审计、脱敏、删除 / 归档、导出快照 | 当前不创建数据库、migration、ORM 或 SQL |
| `ST13_24` | 产品 / 数据 / UI / 工程 / 收口 DoD，手工与自动化测试分层，浏览器真实验证，临时产物治理 | 当前不创建 `tests/**` |
| `ST13_25` | 关键字扫描、索引同步、状态验证、Basic Memory fallback、回读验证、过时表述检查 | 当前不写 Basic Memory，不修改外部记忆 |

不足仍在状态层：`required_tests` 尚未写入 implementation packet inputs；后续需要 State Update 或 formal window 前置窗口处理。

## 10. implementation scope 复核

四个 ST13 的 implementation scope 文档层已明确：

1. 当前窗口只允许文档复核和允许范围内索引同步。
2. 当前窗口禁止创建 `apps/**`、`infra/**`、`tools/**`、`tests/**`。
3. 当前窗口禁止修改 `DOC_STATE.yaml`。
4. 当前窗口禁止生成 implementation packet。
5. 当前窗口禁止打开 formal window。
6. 当前窗口禁止标记 implementation-ready。
7. 未来实现窗口必须另行确认 allowed paths、forbidden paths、required tests、acceptance criteria、rollback 和 handoff output。

不足仍在状态层：`implementation_packet_inputs.goal` 与 `allowed_modify_paths` 仍为空，`implementation_doc_state` 仍为 `missing`。

## 11. formal window candidate 判断

| ST13 | 状态建议 | 还缺什么 | 是否需要用户确认 | 是否需要 State Update | 是否可进入 W13-E11 |
| --- | --- | --- | --- | --- | --- |
| `ST13_21` | `near_ready_for_formal_window_candidate` | M02 权限 blocker、State Update、是否允许未来 OpenAPI / `apps/api/**` | 是 | 是 | 是，作为候选评估对象 |
| `ST13_20` | `near_ready_for_formal_window_candidate` | M02 权限 blocker、State Update、schema / migration / ORM 授权 | 是 | 是 | 是，作为候选评估对象 |
| `ST13_24` | `ready_for_formal_window_candidate` | State Update、是否允许未来 `tests/**` | 是 | 是 | 是 |
| `ST13_25` | `ready_for_formal_window_candidate` | State Update、是否允许未来 Basic Memory / Superpowers 写回 | 是 | 是 | 是 |

本表只表达 W13-E10 文档层 readiness review 结论，不等于 `candidate_status=candidate`，不等于 formal window open，不等于 implementation-ready。

## 12. 后续 State Update 需求

如用户接受本轮候选判断，后续应另开 State Update 或 W13-E11 之后的状态窗口，评估是否写入：

1. `readiness`
2. `candidate_status`
3. `implementation_doc_state`
4. acceptance criteria completion
5. required tests completion
6. formal window candidate 标记
7. blocker 解释字段
8. required doc slot 完成状态说明

本窗口不修改 `DOC_STATE.yaml`。

## 13. 下一窗口建议

推荐下一步为 `W13-E11 / formal window candidate 评估窗口`，输入为本文件与四个 ST13 双文档。

可选路径：

1. 若用户接受本轮分级：进入 `W13-E11`，只评估 formal window candidate，不打开 formal window。
2. 若用户希望先压实状态层字段：先开 `State Update` 或 `W13-E10.5`，但仍不得实现。
3. 若用户认为 `ST13_21 / ST13_20` 仍需更细 contract：开 `W13-E9B`，只补 API / 数据 contract。
4. Basic Memory / Superpowers 写回只能放到后续授权窗口，例如 `W13-F2`。

不得直接建议进入实现。

## 14. 用户确认卡

W13-E11 已吸收本节四张确认卡：`OQ-114=A`、`OQ-115=B`、`OQ-116=A`、`OQ-117=A`。以下卡片保留 W13-E10 输出结构，并补充确认状态。

### 14.1 确认卡 A：是否接受 W13-E10 formal window candidate 分级

问题：是否接受本轮把 `ST13_24 / ST13_25` 判定为 `ready_for_formal_window_candidate`，把 `ST13_21 / ST13_20` 判定为 `near_ready_for_formal_window_candidate`？

背景：四个 ST13 均已完成双文档、required doc slot 登记和第一轮 contract 细化；但状态层仍未激活 implementation doc，也未打开 formal window。

方案 A：接受本轮分级，进入 W13-E11 candidate 评估。

方案 B：四个 ST13 全部降级为 `near_ready_for_formal_window_candidate`。

方案 C：四个 ST13 全部保持 `not_ready_for_formal_window_candidate`，先开 W13-E10.5 补文档。

方案 D：自定义方案 / 其他：由用户补充。

每个方案解决什么：A 解决下一窗口候选评估输入；B 保守处理所有状态层未闭合项；C 解决对文档层 completeness 的疑虑；D 保留用户自定义分级。

限制：任一方案都不打开 formal window，不生成 implementation packet，不进入实现。

风险：若过早把 `near_ready` 写成正式 candidate，可能掩盖 M02 权限 blocker 和状态层空字段。

后续影响：A 可进入 W13-E11；B/C 可能需要 W13-E10.5 或 W13-E9B。

推荐方案：A。

推荐理由：文档层已经足以支撑候选评估，但状态层仍需单独处理。

W13-E11 确认：用户已确认方案 A。

等待用户确认：否，已确认。

### 14.2 确认卡 B：是否允许后续 State Update 处理 readiness / candidate_status

问题：是否允许后续单独 State Update 窗口评估并写入 readiness / candidate_status / implementation_doc_state 等字段？

背景：W13-E10 不修改 `DOC_STATE.yaml`；当前状态层仍显示 `readiness=blocked`、`candidate_status=none`、`implementation_doc_state=missing`。

方案 A：暂不 State Update，先做 W13-E11 candidate 评估。

方案 B：W13-E11 后再开 State Update。

方案 C：先开 State Update，再做 W13-E11。

方案 D：自定义方案 / 其他：由用户补充。

每个方案解决什么：A 保持复核与状态写入拆窗；B 先拿到候选评估结论再写状态；C 优先压实结构化状态；D 保留自定义节奏。

限制：本窗口不写 `DOC_STATE.yaml`。

风险：若没有 State Update，`evaluate-state` 仍会保留实现层 blocker；若过早 State Update，可能把文档层候选误读成实现放行。

后续影响：需要单独 validate/evaluate 并记录回退方案。

推荐方案：B。

推荐理由：先完成 W13-E11 人工候选评估，再写结构化状态，风险最低。

W13-E11 确认：用户已确认方案 B。

等待用户确认：否，已确认。

### 14.3 确认卡 C：是否需要 W13-E10.5 补齐 acceptance criteria / required tests / implementation scope

问题：是否需要在 W13-E11 前再开 W13-E10.5，只补四个 ST13 的验收、测试和 scope 文档细节？

背景：本轮认为四个 ST13 的文档层验收、测试和 scope 已足以支撑候选评估；不足主要在状态层。

方案 A：不新增 W13-E10.5，直接进入 W13-E11 candidate 评估。

方案 B：只对 `ST13_21 / ST13_20` 开 W13-E10.5，因为二者仍涉及 M02 权限 blocker。

方案 C：对四个 ST13 全部开 W13-E10.5。

方案 D：自定义方案 / 其他：由用户补充。

每个方案解决什么：A 保持推进效率；B 针对高风险 API/数据边界加固；C 最大化文档稳态；D 保留自定义补齐范围。

限制：W13-E10.5 仍不得写代码、不得创建测试文件、不得修改 `DOC_STATE.yaml`。

风险：A 可能把少量细节留给 W13-E11；B/C 会增加一轮文档成本。

后续影响：A 进入 W13-E11；B/C 先补文档再复核。

推荐方案：A。

推荐理由：当前文档层已经满足 candidate 评估输入，状态层问题更适合 W13-E11 / State Update 处理。

W13-E11 确认：用户已确认方案 A。

等待用户确认：否，已确认。

### 14.4 确认卡 D：是否保持实现类动作继续禁止

问题：是否继续禁止 OpenAPI 文件、schema 文件、`tests/**`、`apps/**`、implementation packet、formal window open 和代码实现？

背景：W13-E10 只做 readiness review；任何实现类动作都会越过当前窗口边界。

方案 A：继续全部禁止，直到用户另窗确认 formal window 和 implementation packet 条件。

方案 B：允许后续仅创建 OpenAPI / schema 文档，但不创建实现目录。

方案 C：允许后续创建测试文件或应用目录骨架。

方案 D：自定义方案 / 其他：由用户补充。

每个方案解决什么：A 保持治理边界；B 为 API/数据 contract 产物预留空间；C 提前准备实现骨架；D 保留自定义授权。

限制：本窗口不执行任何实现类动作。

风险：B/C 可能被误读为 implementation-ready 或 formal window 已打开。

后续影响：A 进入候选评估；B/C 需要新的确认卡和新的窗口边界。

推荐方案：A。

推荐理由：当前状态层仍 blocked，且用户明确禁止实现类动作。

W13-E11 确认：用户已确认方案 A。

等待用户确认：否，已确认。

## 15. 当前不进入实现说明

W13-E10 结论不放行实现：

1. 不修改 `DOC_STATE.yaml`。
2. 不打开 formal window。
3. 不生成 implementation packet。
4. 不标记 implementation-ready。
5. 不创建 `apps/**`、`infra/**`、`tools/**`、`tests/**`。
6. 不写代码。
7. 不写 Basic Memory。

`ready_for_formal_window_candidate` 仅表示文档层可进入后续 candidate 评估，不表示可以进入实现。
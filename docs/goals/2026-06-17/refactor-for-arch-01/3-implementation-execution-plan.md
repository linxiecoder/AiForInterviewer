---
title: 3-implementation-execution-plan
type: execution-plan-draft
status: draft
permalink: ai-for-interviewer/docs/goals/2026-06-17/refactor-for-arch-01/3-implementation-execution-plan
source_report: docs/goals/2026-06-17/refactor-for-arch-01/1-audit-report.md
source_plan: docs/goals/2026-06-17/refactor-for-arch-01/2-implementation-plan.md
---

# Execution Plan Draft

本文档是 `refactor-for-arch-01` 的分阶段实施计划清单，用于后续 Goal pack 拆分。

输入边界：

- 仅基于 `docs/goals/2026-06-17/refactor-for-arch-01/1-audit-report.md`。
- 仅基于 `docs/goals/2026-06-17/refactor-for-arch-01/2-implementation-plan.md`。
- 不引入外部 issue 模型、外部 issue 清单或额外架构推断。

输出边界：

- 本文件只做 execution plan decomposition。
- 本文件不替代 `BACKLOG.md`、`DELIVERY_PLAN.md`、active design docs、ADR 或代码事实。
- 后续实现必须在授权窗口内回写唯一入口。
- 所有任务保持工程实施粒度，不做架构重设计，不引入新的编译器、图谱或运行时模型，不做图化任务拆分。

## Phase 1: Control-plane Isolation

### 1. Objective

收敛 execution authority 的来源。审计报告指出，下一题生成权、执行目标、授权 refs 和 grant snapshot 分散在 frontend selection、API route、command fields、feedback payload、runtime policy、handoff/repository 等位置；现有方案要求 authority 成为 backend-only 的唯一决策层，并统一输出 `allowed`、`rejected`、`execution_target`、`reason_codes`、`decision_ref`。

### 2. Scope

- `apps/api/app/application/polish/commands.py`
- `apps/api/app/application/polish/use_cases.py`
- `apps/api/app/api/v1/polish.py`
- `CreatePolishQuestionTaskCommand`
- `NextQuestionExecutionGrant`
- `QuestionAuthority` / `FeedbackAuthority` / `ProgressAuthority` 的模块级输出边界
- `SourceSupportPolicy`、`QuestionGroundingPolicy`、`AssetConsistencyPolicy` 等 policy result 的消费位置

本阶段只处理 authority 收敛，不处理 executor 合并、snapshot 冻结、frontend UI 改造或 legacy cleanup。

### 3. Tasks

#### Task 1.1: 统一 authority decision 输出

- Task Name: 统一 authority decision 输出
- Target Area: `apps/api/app/application/polish/commands.py` 与 `apps/api/app/application/polish/use_cases.py`
- Steps:
  1. 梳理 `CreatePolishQuestionTaskCommand` 中同时承载 selection、execution source、authorized refs、grant snapshot 的字段。
  2. 梳理 `NextQuestionExecutionGrant` 当前即时生成、校验、消费的位置。
  3. 将 question / feedback / progress 的授权判断输出对齐到 `AuthorityDecisionResult` 字段：`allowed`、`rejected`、`execution_target`、`reason_codes`、`decision_ref`。
  4. 将 rejected decision 固定为 fail closed：不创建 snapshot、不调用 executor、不持久化业务结果。
  5. 将 `execution_target` 的生成位置限制在 backend authority 输出处。
- Checkpoints:
  - `allowed=true` 时 `rejected=false`，且 `execution_target` 非空。
  - `allowed=false` 时 `rejected=true`，且 `reason_codes` 至少包含一个拒绝原因。
  - `allowed` 与 `rejected` 不会同时为 `true` 或同时为 `false`。
  - `decision_ref` 能贯穿后续 response、幂等和持久化计划。
- Test Points:
  - 覆盖 allowed question intent，断言输出包含 `execution_target=generate_question` 或 `retry_question_generation`。
  - 覆盖 rejected question intent，断言不进入后续执行入口。
  - 覆盖 feedback / progress 的 rejected decision，断言 `reason_codes` 可解释拒绝。
  - 覆盖非法 authority 状态组合，断言 fail closed。
- Risk Notes:
  - 如果仅新增字段而不移除旧字段消费，authority 仍会分叉。
  - 如果 `reason_codes` 被复用为 executor 结果状态，会继续混淆解释信号和执行结果。
  - 如果 `decision_ref` 只出现在 response，不进入持久化计划，后续幂等无法闭合。

#### Task 1.2: 移除非 backend 的执行目标派生

- Task Name: 移除非 backend 的执行目标派生
- Target Area: `apps/api/app/api/v1/polish.py` 与 `apps/api/app/application/polish/use_cases.py`
- Steps:
  1. 检查 `/questions` 与 `/feedback/{feedback_id}/next-question` 两个入口传入 `create_question_task` 的 command 组装逻辑。
  2. 将 frontend local state、UI selection、display status、optimistic state 从 execution target 决策来源中移出。
  3. 将 LLM recommendation、candidate text、graph/fallback availability、provider transport success 标记为非授权来源。
  4. 保留 route 层的请求适配职责，但不允许 route 层直接生成执行授权或执行目标。
  5. 对仍需保留的 compatibility signal，仅作为 adapter output 或 safe response metadata 处理。
- Checkpoints:
  - API route 不直接生成 `execution_target`。
  - frontend 传入的 selection 类字段不会被解释为授权目标。
  - LLM / graph / provider 输出不能直接触发 persistence。
  - rejected authority path 不会因 compatibility fallback 继续执行。
- Test Points:
  - 通过 direct question path 与 feedback next-question path 传入相同 intent，断言执行目标只来自 authority。
  - 模拟 frontend selection 变化，断言 backend `execution_target` 不被 UI focus 改写。
  - 模拟 provider success 但 authority rejected，断言不持久化业务结果。
  - 模拟 graph disabled / fallback available，断言不产生授权。
- Risk Notes:
  - route 文件当前同时承担 dependency wiring、response contract、compat shape、payload filtering，改动时容易把 response 兼容误当 authority。
  - feedback payload 中 evaluation-shaped fields 可能继续越界成 orchestration signal。
  - 保留 legacy mapper 时必须确认其输出不是目标选择器。

#### Task 1.3: 分离 policy reason 与执行控制

- Task Name: 分离 policy reason 与执行控制
- Target Area: `SourceSupportPolicy`、`QuestionGroundingPolicy`、`AssetConsistencyPolicy` 与 feedback rules 的消费位置
- Steps:
  1. 梳理 policy result 当前被写入 metadata、legacy dict 或 block/allow 分支的位置。
  2. 将 authority 使用的 `reason_codes` 限定为决策原因。
  3. 将 executor failure reason 与 artifact lifecycle status 放到后续 execution result 语义中，不在 authority 阶段提前混用。
  4. 对需要展示的 policy 解释信息保留 safe metadata，但不得赋予执行授权。
  5. 补充 rejected decision 的 fail-closed 测试覆盖。
- Checkpoints:
  - policy result 不再同时承担解释和执行目标选择。
  - `reason_codes` 不承载 persisted artifact 的最终状态。
  - metadata / legacy dict 中的解释字段不能反向触发执行。
  - authority output 对 question / feedback / progress 保持同一字段集。
- Test Points:
  - 覆盖 policy 返回阻断原因时 authority rejected。
  - 覆盖 policy 返回非阻断说明时 authority allowed 且 `execution_target` 来自 authority。
  - 覆盖 legacy metadata 存在但不触发 executor 的路径。
  - 覆盖 response 中 safe metadata 不改变 backend decision。
- Risk Notes:
  - 现有测试可能断言 reason-coded decision 被跨层消费，需要同步调整为 authority-only 语义。
  - 如果 metadata 命名与 authority 字段过近，后续实现容易误用。
  - 不能在本阶段顺手改 artifact lifecycle 终态；该项留给 Phase 5。

### 4. Validation Plan

- 验证修复有效：用 focused tests 覆盖 allowed / rejected authority path，断言 rejected decision 不创建 snapshot、不调用 executor、不写业务结果；断言 allowed decision 必须携带非空 `execution_target`。
- 确认没有 regression：保留现有 API safe response 和 compatibility shape 的只读展示语义，覆盖 direct question path、feedback next-question path、feedback evaluation path 的基本响应。
- 确认 control-plane 没新增分叉：扫描 route、command、use case、policy result 消费点，确认只有 backend authority 输出 `execution_target`，frontend、LLM、graph/fallback、provider、legacy mapper 不再生成执行授权。

## Phase 2: Execution Flow Stabilization

### 1. Objective

收敛执行路径。审计报告指出 question / feedback / progress tree 不是单向链路，而是循环影响；出题有多入口；question 可走 `AiOrchestrationFacade`，feedback 又要求 `FeedbackGenerationService.generate_feedback_v1()`；prompt/runtime/workflow 多套并存。现有方案要求所有链路统一为 `intent → authority → snapshot → executor → persist result`，executor 是唯一执行入口。

### 2. Scope

- `apps/api/app/application/polish/use_cases.py`
- `apps/api/app/api/v1/polish.py`
- `AiOrchestrationFacade`
- `FeedbackGenerationService.generate_feedback_v1()`
- `AgentPersistenceHandoff.write_question_result()`
- question direct workflow、feedback service workflow、progress projection update path
- persisted result 中的 `decision_ref` 与 `execution_target`

本阶段只处理执行路径收敛，不新增 snapshot 字段，不处理 frontend payload 隔离，不清理 placeholder / skeleton 路由。

### 3. Tasks

#### Task 2.1: 收敛 question 执行入口

- Task Name: 收敛 question 执行入口
- Target Area: `apps/api/app/application/polish/use_cases.py` 与 `apps/api/app/api/v1/polish.py`
- Steps:
  1. 将 `/questions` 与 `/feedback/{feedback_id}/next-question` 两个入口统一为 intent 进入 authority 后的同一 question execution path。
  2. 让 question execution path 只消费 authority 之后的执行输入，不再从 route 或 feedback payload 重建目标。
  3. 将 `AgentPersistenceHandoff.write_question_result()` 的调用限制在 executor handler 内。
  4. 移除 route、feedback payload、LLM result、graph/fallback adapter 直接触发 formal question write 的路径。
  5. 保留 rejected path 的 safe response，不进入 question executor。
- Checkpoints:
  - 两个 question 入口进入同一 executor boundary。
  - executor 不调用 authority。
  - executor 不重建 progress target。
  - formal question write 只从 executor handler 发生。
- Test Points:
  - direct question path 通过 executor 持久化 question result。
  - feedback next-question path 通过同一 executor boundary 持久化 question result。
  - authority rejected 时 `AgentPersistenceHandoff.write_question_result()` 不被调用。
  - graph disabled / fallback available 时不会绕过 executor。
- Risk Notes:
  - 当前 API 层承担 contract composer 职责，迁移时不能破坏既有 safe response 字段。
  - planned workflow candidate 与 formal write 之间存在语义差异，不能在本阶段把 candidate-only 直接升级为 implemented。
  - 如果只合并函数入口但保留 route-level write，执行路径仍未收敛。

#### Task 2.2: 收敛 feedback evaluation 执行路径

- Task Name: 收敛 feedback evaluation 执行路径
- Target Area: `FeedbackGenerationService.generate_feedback_v1()` 与 feedback use case
- Steps:
  1. 将 answer-submit / feedback-retry intent 统一进入 `FeedbackAuthority` 后的 feedback executor path。
  2. 保留 `generate_feedback_v1()` 作为 executor handler 内部调用点或 service dependency，不允许其绕过 authority。
  3. 将 feedback payload 中的 answer coverage、answer change analysis、asset consistency check 等 evaluation-shaped fields 限定为 evaluation result 或 metadata。
  4. 将 feedback failure response 收敛为 safe response 和 reason code，不暴露 raw runtime detail。
  5. 确认 feedback retry 使用同一 `decision_ref` / `execution_target` 规则。
- Checkpoints:
  - feedback evaluation 的执行入口只有 executor boundary。
  - `generate_feedback_v1()` 不直接决定是否执行。
  - feedback payload 不授权下一题。
  - retry 与首次 evaluation 共享同一执行流规则。
- Test Points:
  - answer-submit allowed 时执行 `evaluate_feedback` 并持久化 feedback result。
  - feedback-retry allowed 时执行 `retry_feedback_evaluation`。
  - feedback authority rejected 时不调用 feedback service。
  - feedback payload 中 recommendation 存在时不触发 next-question persistence。
- Risk Notes:
  - feedback path 当前仍有 v1 命名和 legacy 兼容字段，不能把命名清理扩成执行语义改造。
  - evaluation-shaped fields 继续被下游当 orchestration signal 会复发 authority 分裂。
  - safe response 不应泄露 provider exception stack、transport detail 或 secret。

#### Task 2.3: 收敛 progress projection 执行路径

- Task Name: 收敛 progress projection 执行路径
- Target Area: progress tree update / refresh use case
- Steps:
  1. 将 progress update 限定为 backend execution result 触发的 intent。
  2. 通过 `ProgressAuthority` 校验 projection 更新依附于已完成 backend execution result。
  3. 将 progress projection 更新纳入 executor target：`update_progress_projection` 或 `refresh_progress_projection`。
  4. 禁止 progress projection 更新改写 question / answer / feedback canonical state。
  5. 对 progress failed / refresh_failed response 保持 safe failure 语义。
- Checkpoints:
  - progress update 不由 frontend display status 触发。
  - progress projection 不成为隐式 execution target 来源。
  - progress update 只能跟随 backend execution result。
  - projection failure 不改写 canonical state。
- Test Points:
  - question result persisted 后触发 progress projection update。
  - feedback result persisted 后触发 progress projection update。
  - 缺失 backend execution result 时 `ProgressAuthority` rejected。
  - projection stale 或 state version conflict 时返回 safe rejection / failure。
- Risk Notes:
  - 审计报告指出 progress tree 读 turns / feedback / question completion，容易继续成为隐式状态汇聚点。
  - frontend 将 progress tree 当 action target 时，会与 Phase 4 产生边界依赖。
  - 不能在本阶段调整 progress 文案或 UI fallback；只处理执行路径。

#### Task 2.4: 持久化绑定 `decision_ref` 与 `execution_target`

- Task Name: 持久化绑定 `decision_ref` 与 `execution_target`
- Target Area: question / feedback / progress persistence handoff
- Steps:
  1. 为 question result persistence 写入 `decision_ref` 与 `execution_target`。
  2. 为 feedback result persistence 写入 `decision_ref` 与 `execution_target`。
  3. 为 progress projection result 写入 `decision_ref` 与 `execution_target`。
  4. 以 `decision_ref` 和目标状态实现重复执行的返回已有结果或 no-op。
  5. 将写入失败统一为 safe failure response。
- Checkpoints:
  - 每个 persisted result 都能追溯到 authority decision。
  - 同一 `decision_ref` 不产生重复业务结果。
  - rejected decision 没有业务写入。
  - failure response 不包含 raw provider payload。
- Test Points:
  - 重放同一 `decision_ref` 的 question execution，断言无重复 question result。
  - 重放同一 `decision_ref` 的 feedback execution，断言无重复 feedback result。
  - 持久化失败时返回 safe response。
  - rejected decision 后检查 repository 没有新增业务结果。
- Risk Notes:
  - 如果旧 persistence path 没有同步关闭，idempotency 会只保护新路径。
  - 如果 `execution_target` 只写日志不写结果，后续排查无法确认执行来源。
  - 不能把 provider transport success 当 persisted success。

### 4. Validation Plan

- 验证修复有效：用 flow-level tests 覆盖 question、feedback、progress 三条链路，断言都符合 `intent → authority → snapshot → executor → persist result`，且 executor 不调用 authority、不重建 context。
- 确认没有 regression：覆盖现有 direct question、feedback next-question、answer-submit、feedback retry、progress refresh 的 safe response 和持久化结果，确认用户可见响应不因入口收敛丢字段。
- 确认 control-plane 没新增分叉：扫描 route、service、facade、handoff、provider callback，确认没有新的 direct persistence、direct execution target、route-level write 或 provider-triggered write。

## Phase 3: Snapshot Introduction

### 1. Objective

引入执行上下文冻结。审计报告指出 question / feedback / progress tree 会循环读取和再解释状态，runtime flags / provider boundary 只是能力 gate 而不是业务 execution authority，frontend selection 与 backend target 重复派生。现有方案要求在 authority allowed 后创建 immutable `ExecutionSnapshot`，executor 只能消费 snapshot，不能重建 context 或改写目标。

### 2. Scope

- `apps/api/app/application/polish/entities.py`
- `apps/api/app/application/polish/use_cases.py`
- `ExecutionSnapshot` 字段：`authority_decision_result`、`session_state`、`progress_state`、`input_payload`、`execution_target`、`runtime_flags`、`decision_ref`
- 可选 `asset_snapshot`
- snapshot 创建点与 executor 入参

本阶段只做上下文冻结，不新增 authority domain，不合并 executor handler，不处理 frontend 权限隔离。

### 3. Tasks

#### Task 3.1: 定义 snapshot 数据边界

- Task Name: 定义 snapshot 数据边界
- Target Area: `apps/api/app/application/polish/entities.py`
- Steps:
  1. 在 application polish entity 边界定义 `ExecutionSnapshot` 的字段集合。
  2. 将 `authority_decision_result` 完整保存到 snapshot。
  3. 将 `execution_target` 约束为等于 `authority_decision_result.execution_target`。
  4. 将 `decision_ref` 作为 snapshot、日志、幂等、持久化的贯穿引用。
  5. 将 `asset_snapshot` 保持为可选冻结引用，不作为决策来源。
- Checkpoints:
  - snapshot 字段集合与现有方案一致。
  - snapshot 中不存在 frontend local state、UI selection、LLM recommendation、graph availability、provider success。
  - `asset_snapshot` 只记录 prompt / rubric / asset 版本引用。
  - snapshot 定义不引入新的执行模型。
- Test Points:
  - 构造 allowed authority result 后创建 snapshot，断言字段完整。
  - 构造 rejected authority result，断言不能创建 snapshot。
  - 构造 execution_target 不一致的 snapshot，断言失败。
  - 构造含 `asset_snapshot` 的 snapshot，断言不改变 authority decision。
- Risk Notes:
  - 如果 snapshot 携带 mutable repository 对象，executor 仍可重建 context。
  - 如果 snapshot 允许缺省 `execution_target`，会把目标选择推迟到 executor。
  - 如果 `asset_snapshot` 被用作授权依据，会形成新的 control-plane 分叉。

#### Task 3.2: 在 authority allowed 后创建 snapshot

- Task Name: 在 authority allowed 后创建 snapshot
- Target Area: `apps/api/app/application/polish/use_cases.py`
- Steps:
  1. 在 question authority allowed path 后创建 snapshot。
  2. 在 feedback authority allowed path 后创建 snapshot。
  3. 在 progress authority allowed path 后创建 snapshot。
  4. 将 current backend canonical state、validated input payload、runtime flags 写入 snapshot。
  5. 将 rejected path 固定为 `authority_decision_result → safe rejection response`。
- Checkpoints:
  - snapshot 只在 `allowed=true` 时创建。
  - rejected path 没有 snapshot side effect。
  - snapshot 创建点位于 authority 与 executor 之间。
  - snapshot 包含 authority 决策时看到的 canonical state。
- Test Points:
  - allowed question intent 创建 snapshot 后进入 executor。
  - rejected question intent 不创建 snapshot。
  - allowed feedback intent 创建 snapshot 后进入 executor。
  - progress authority rejected 时返回 safe rejection response。
- Risk Notes:
  - 如果 route 层创建 snapshot，会把 request adapter 变成执行边界。
  - 如果 snapshot 创建后继续读取 mutable state 派生新目标，冻结无效。
  - 如果 rejected path 仍保留 legacy fallback，fail closed 会被绕过。

#### Task 3.3: 冻结 runtime flags 与 asset refs

- Task Name: 冻结 runtime flags 与 asset refs
- Target Area: runtime flags、prompt / rubric / asset 版本引用消费位置
- Steps:
  1. 在 snapshot 创建时读取并冻结本次执行所需 `runtime_flags`。
  2. 对依赖 prompt / rubric / asset 版本的执行，冻结为 `asset_snapshot` 引用。
  3. 禁止 executor 在执行中重新读取 runtime flags 并改变执行路径。
  4. 禁止 graph/fallback availability 在 snapshot 创建后改写 `execution_target`。
  5. 将 provider transport result 限定为 executor 内部调用结果，不影响 snapshot target。
- Checkpoints:
  - snapshot 创建后 runtime flag 变化不影响本次执行。
  - `asset_snapshot` 没有授权含义。
  - graph/fallback 只返回可用性、调用结果或兼容信号。
  - provider success 不会改写 `execution_target`。
- Test Points:
  - 创建 snapshot 后切换 runtime flag，断言 executor 仍按 snapshot 执行。
  - 缺少 provider 时返回 safe failure，不改变 execution target。
  - graph disabled 时不改变 snapshot target。
  - asset version 变化不影响已创建 snapshot 的重放。
- Risk Notes:
  - runtime fallback 语义当前不等价，容易把安全边界、可用性边界、兼容边界混成一个 status。
  - prompt / runtime 多套并存时，asset ref 必须是版本引用，不是重新决策入口。
  - provider boundary 通过不等于 execution 安全通过。

#### Task 3.4: 阻止 executor 重建 context

- Task Name: 阻止 executor 重建 context
- Target Area: executor handler 与 service dependency 调用点
- Steps:
  1. 将 executor 入参限制为 `ExecutionSnapshot`。
  2. 删除或改造 executor 中为了选择目标而读取 repository、frontend state、LLM output、graph/fallback adapter、provider response 的逻辑。
  3. 保留 executor 为执行动作所需的 service dependency，但不得用 dependency 输出重新决策。
  4. 对 snapshot 中没有的输入，禁止参与 execution。
  5. 为同一 snapshot 的幂等重放补充断言。
- Checkpoints:
  - executor 不接收 frontend intent。
  - executor 不接收 authority input。
  - executor 不读取 mutable context 来改变路径。
  - executor 只执行 `snapshot.execution_target`。
- Test Points:
  - executor 入参缺少 snapshot 时失败。
  - snapshot 中没有的 field 不参与 service call。
  - 同一 snapshot 重放返回已有结果或 no-op。
  - provider / graph output 变化不改变 execution target。
- Risk Notes:
  - 如果 executor 仍读取 progress tree 当前状态来选目标，Phase 1 authority 收敛会被破坏。
  - 如果 service dependency 内部仍 direct write，需要在 Phase 2 / Phase 5 同步关闭。
  - 不能把 context rebuild 移到 helper 中规避检查。

### 4. Validation Plan

- 验证修复有效：覆盖 allowed 创建 snapshot、rejected 不创建 snapshot、snapshot target 等于 authority target、runtime flag 变化不影响已创建 snapshot、同一 snapshot 可幂等重放。
- 确认没有 regression：覆盖 question / feedback / progress 的 happy path 与 safe failure path，确认响应仍能返回用户需要的 safe response，不泄露 raw provider payload、exception stack、transport detail 或 secret。
- 确认 control-plane 没新增分叉：扫描 executor 和 service dependency 调用点，确认没有从 repository、frontend state、LLM output、graph/fallback adapter、provider response 重建 execution target。

## Phase 4: Frontend Isolation

### 1. Objective

隔离 UI 权限。审计报告指出 frontend 不是纯展示层，`InterviewPage.tsx` 会计算 `selected_progress_node_ref` 和 `completed_focus_refs`，并用 task refs 回写本地焦点；frontend selection 与 backend target 重复派生，UI fallback mapper 会掩盖 backend 语义差异。现有方案要求 frontend 只能提交 intent 和展示上下文，不能参与 execution decision。

### 2. Scope

- `apps/web/src/pages/interview/InterviewPage.tsx`
- frontend next-question / answer-submit / feedback-retry request construction
- frontend task refs 与 local focus reconciliation
- UI fallback mapper 与 safe response rendering

本阶段只做 UI 权限隔离，不改 backend authority 规则，不合并 executor，不清理 backend legacy route。

### 3. Tasks

#### Task 4.1: 将 frontend action payload 收敛为 intent-only

- Task Name: 将 frontend action payload 收敛为 intent-only
- Target Area: `apps/web/src/pages/interview/InterviewPage.tsx` action request construction
- Steps:
  1. 梳理 next-question、answer-submit、feedback-retry 的请求构造位置。
  2. 移除或降级 `selected_progress_node_ref`、`completed_focus_refs` 等 UI focus 字段的 execution target 语义。
  3. 将用户动作表达为显式 intent，不从 UI selection 生成授权目标。
  4. 仅保留 backend contract 允许的展示上下文或输入 payload。
  5. 对 optimistic state 只保留 UI 展示作用，不参与 backend target selection。
- Checkpoints:
  - frontend payload 不携带授权目标。
  - frontend local state 不参与 execution decision。
  - UI focus 变化不会改写 backend execution target。
  - optimistic state 只影响渲染，不影响执行。
- Test Points:
  - 切换 UI focus 后触发 next-question，断言 request 不含授权目标语义。
  - answer-submit 只提交 answer intent 与必要 input payload。
  - feedback-retry 不从本地 task refs 派生 execution target。
  - backend rejected safe response 能被前端正常展示。
- Risk Notes:
  - 不能把字段简单改名后继续作为 target 使用。
  - 若 backend 尚未完成 Phase 1/2，frontend intent-only 改动需要与后端兼容窗口同步。
  - optimistic UI 不能提前展示 persisted 成功状态。

#### Task 4.2: 移除 task refs 对本地焦点的执行授权作用

- Task Name: 移除 task refs 对本地焦点的执行授权作用
- Target Area: `InterviewPage.tsx` task refs 与 local focus reconciliation
- Steps:
  1. 梳理 task candidate refs、API command refs、grant validation refs 回写本地焦点的位置。
  2. 将 task refs 的用途限定为展示、定位或结果关联。
  3. 禁止 task refs 被再次用于生成下一次 execution target。
  4. 将 backend response 中的 `decision_ref` / `execution_target` 作为只读展示或调试引用处理。
  5. 覆盖 local focus 更新与下一次 action request 的隔离关系。
- Checkpoints:
  - task refs 不再形成 UI side authority。
  - local focus 不会成为 backend target。
  - `decision_ref` 不被 frontend 用来授权新 execution。
  - frontend 不重建 selected / authorized target。
- Test Points:
  - 收到 question result 后更新 UI focus，下一次 intent 不继承 focus 为执行目标。
  - 收到 feedback result 后 task refs 仅用于展示关联。
  - local focus stale 时 backend decision 不受影响。
  - grant validation refs 只读展示，不生成新 grant。
- Risk Notes:
  - 审计报告指出 frontend selection 与 backend target 重复派生，本任务必须避免把重复派生移到新的 helper。
  - 如果 task refs 同时用于滚动定位和执行目标，拆分时要保留 UX 展示能力。
  - 不能让 frontend 通过 fallback mapper 重新解释 backend authority。

#### Task 4.3: 收敛 UI fallback mapper 的展示语义

- Task Name: 收敛 UI fallback mapper 的展示语义
- Target Area: `InterviewPage.tsx` status mapping 与 response rendering
- Steps:
  1. 梳理 pending / failed / display fallback 的 mapper 逻辑。
  2. 将 unknown backend status 显示为 safe display state，不映射为可执行授权。
  3. 区分 authority rejection、executor failure、provider unavailable、validation failed 的用户可见展示。
  4. 保留 candidate / formal / fallback / partial / skeleton / validation_failed 的原始 non-claim 语义。
  5. 为 rejected safe response、executor safe failure、pending payload 分别补充 UI 断言。
- Checkpoints:
  - UI fallback 不掩盖 backend 语义差异。
  - unknown status 不触发 retry / next-question 授权。
  - `partial`、`skeleton`、`default-off`、`candidate-only` 不被展示为 implemented。
  - frontend display state 不回写 backend authority。
- Test Points:
  - authority rejected response 展示拒绝原因，不触发 executor action。
  - executor failure response 展示安全失败状态，不暴露 raw runtime detail。
  - unknown status 进入 safe display fallback。
  - candidate-only 结果不展示为 formal persisted success。
- Risk Notes:
  - UI fallback mapper 当前可能把未知状态压成 pending/failed，容易掩盖后端 contract drift。
  - 若展示文案过度承诺，会把 partial / skeleton 误升格。
  - 不能在 UI 层修正 backend 生命周期状态，只能安全展示。

### 4. Validation Plan

- 验证修复有效：用 frontend-focused tests 覆盖 next-question、answer-submit、feedback-retry payload，断言 frontend 只提交 intent / input payload，不提交授权目标；覆盖 UI focus 变化不影响 backend target。
- 确认没有 regression：覆盖 question、feedback、progress 的用户可见状态渲染，确认 pending、safe rejection、safe failure、candidate-only、formal persisted success 都能正常展示。
- 确认 control-plane 没新增分叉：扫描 `InterviewPage.tsx` 中 request construction、local focus reconciliation、status mapper，确认没有从 UI selection、task refs、fallback mapper 生成 execution authorization 或 target selection。

## Phase 5: Cleanup & Risk Removal

### 1. Objective

清理遗留路径和风险。审计报告指出 active、placeholder、skeleton、default-off、legacy_direct_path_retained 同时是运行事实；placeholder route 和 skeleton use case 已挂入 v1 API；status 语义在 candidate、formal、fallback、partial、skeleton、validation_failed 等模块间扩散；tests 会固化当前分裂结构。现有方案要求任何绕过 authority、snapshot 或 executor 的执行都必须删除或改为 adapter / intent / persistence response。

### 2. Scope

- `apps/api/app/api/v1/polish.py`
- `pressure_skeleton`、`review_skeleton`、`ai_task_skeleton`
- `domain/*/services.py` 中的 pass 壳
- graph facade、direct fallback、fake transport gate、provider boundary
- candidate workflow、formal write、pending payload、progress failed artifact、frontend fallback mapper 的状态边界
- 现有 contract tests 与 flow tests

本阶段只做遗留路径清理和风险移除，不新增业务能力，不新增执行目标，不重构阶段计划。

### 3. Tasks

#### Task 5.1: 下线或隔离 placeholder / skeleton 运行入口

- Task Name: 下线或隔离 placeholder / skeleton 运行入口
- Target Area: `apps/api/app/api/v1/polish.py` 中的 placeholder route 与 skeleton use case
- Steps:
  1. 梳理 `pressure_skeleton`、`review_skeleton`、`ai_task_skeleton` 是否仍挂入 v1 API。
  2. 将不会进入真实 execution flow 的 route 标记为 unavailable safe response，或移出运行入口。
  3. 防止 skeleton success 被前端或调用方解释为真实业务 capability。
  4. 保留必要的历史来源说明，但不作为 active execution path。
  5. 补充 false capability 防回归测试。
- Checkpoints:
  - placeholder / skeleton route 不产生业务执行。
  - skeleton response 不声明 implemented。
  - default-off capability 不被 route existence 升格为 available。
  - API inventory 与实际可执行能力一致。
- Test Points:
  - 调用 skeleton route 时返回 safe unavailable / skeleton response。
  - skeleton route 不调用 authority、snapshot、executor 或 persistence。
  - frontend 不把 skeleton response 渲染为真实成功。
  - route inventory 不把 placeholder 计入 active capability。
- Risk Notes:
  - 删除 route 可能破坏兼容调用方；隔离时必须保证不会形成 false capability。
  - skeleton_succeeded 这类状态名容易被误解为业务成功。
  - 不能把 placeholder cleanup 扩成新功能实现。

#### Task 5.2: 将 graph / fallback / provider legacy 分支降级为 adapter-only

- Task Name: 将 graph / fallback / provider legacy 分支降级为 adapter-only
- Target Area: `AiOrchestrationFacade`、graph facade、direct fallback、fake transport gate、provider boundary
- Steps:
  1. 梳理 graph default-off、legacy direct path、fake runtime、provider boundary 的调用分支。
  2. 将 graph/fallback 输出限制为可用性、调用结果或兼容信号。
  3. 删除或改造绕过 authority / snapshot / executor 的 legacy direct execution path。
  4. 将 fake provider 配置错误与 provider missing、graph disabled 区分为不同 safe failure / adapter status。
  5. 覆盖 graph disabled、fake provider、provider missing 的路径差异。
- Checkpoints:
  - graph/fallback 不能 authorization。
  - graph/fallback 不能 target selection。
  - graph/fallback 不能 persistence。
  - provider success 不等于 execution allowed。
- Test Points:
  - graph disabled path 不 fallback 成 direct execution write。
  - fake provider 配置错误返回 safe failure。
  - provider missing 返回 failed artifact 或 safe failure，但不改写 authority。
  - legacy direct path 不再保留为执行入口。
- Risk Notes:
  - 审计报告指出 runtime fallback 语义不等价，清理时不能用一个泛化 status 覆盖所有原因。
  - 如果 legacy path 只改名为 adapter 但仍写业务结果，风险未移除。
  - provider boundary 通过不等于 business grant 通过。

#### Task 5.3: 收敛 lifecycle / status 运行语义

- Task Name: 收敛 lifecycle / status 运行语义
- Target Area: question candidate workflow、feedback payload、progress artifact、API pending payload、frontend mapper
- Steps:
  1. 梳理 candidate、formal、fallback、partial、skeleton、validation_failed、refresh_failed 等状态的运行消费位置。
  2. 将 artifact lifecycle 终态限定在各自模块边界，不跨层当执行授权。
  3. 将 safe response status 与 persisted result status 区分。
  4. 保留 `partial`、`skeleton`、`default-off`、`candidate-only` 的 non-claim 语义。
  5. 更新或新增状态语义防回归测试。
- Checkpoints:
  - candidate-only 不会触发 formal persistence。
  - pending payload 不会被前端解释为授权成功。
  - progress failed / refresh_failed 不改写 question / feedback canonical state。
  - frontend mapper 不把未知状态压成执行授权。
- Test Points:
  - planned workflow candidate 校验失败时进入 validation failed path，不写 formal question。
  - feedback failed payload 不触发 next-question execution。
  - progress refresh_failed 保持 safe display，不改写 canonical state。
  - partial / skeleton / default-off 在 UI 和 API 中不展示为 implemented。
- Risk Notes:
  - 状态词改动容易破坏现有 contract tests，需要按模块逐步更新断言。
  - 不能用统一文案掩盖不同 failure cause。
  - lifecycle cleanup 不等于新增统一状态机。

#### Task 5.4: 清理固化旧分裂结构的测试断言

- Task Name: 清理固化旧分裂结构的测试断言
- Target Area: polish API / application / frontend 相关 contract tests 与 flow tests
- Steps:
  1. 梳理直接断言多入口、多 fallback、多 UI focus 行为的测试。
  2. 将断言目标改为 authority-only、snapshot-only、executor-only 的边界行为。
  3. 保留 response compatibility 的测试，但不再要求旧 direct path 存活。
  4. 增加 forbidden path 回归断言，覆盖 bypass authority、bypass snapshot、bypass executor。
  5. 将 placeholder / skeleton / default-off 的 non-claim 语义纳入测试。
- Checkpoints:
  - 测试不再要求 frontend selection 参与 backend target。
  - 测试不再要求 graph/fallback direct path retained。
  - 测试仍覆盖 safe response 与 compatibility shape。
  - forbidden path 断言覆盖主要 bypass。
- Test Points:
  - 旧 direct path 测试改为断言 safe adapter / unavailable / executor-only。
  - UI focus 测试改为断言 intent-only payload。
  - provider / graph 测试改为断言 adapter-only。
  - skeleton / placeholder 测试断言 false capability 不成立。
- Risk Notes:
  - 如果测试只跟随实现删除断言，可能漏掉 regression。
  - 如果保留旧测试但改 expected 为新 success，会固化新的分叉。
  - 测试调整必须区分 response compatibility 与 execution authority。

### 4. Validation Plan

- 验证修复有效：运行 focused regression 覆盖 placeholder / skeleton route、graph disabled、fake provider、provider missing、candidate-only、formal write、progress failed / refresh_failed，确认绕过 authority、snapshot 或 executor 的路径被删除或降级。
- 确认没有 regression：运行 polish API / application / frontend 相关测试，确认 safe response、compatibility shape、用户可见状态、持久化结果、幂等行为仍符合前四个 Phase 的 contract。
- 确认 control-plane 没新增分叉：做 forbidden path scan，确认不存在 route-level direct write、frontend target selection、LLM-triggered execution、graph/fallback authorization、provider-triggered persistence、legacy mapper target selection、skeleton false capability。

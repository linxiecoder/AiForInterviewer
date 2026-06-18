---
title: 2-implementation-plan
type: implementation-plan
status: final-execution-freeze
permalink: ai-for-interviewer/docs/goals/2026-06-17/refactor-for-arch-01/2-implementation-plan
source_report: docs/goals/2026-06-17/refactor-for-arch-01/1-audit-report.md
---

# Execution Minimal Model v1.0

本文件是 `refactor-for-arch-01` 的最终收敛版实现方案。`docs/goals/` 只保存 execution evidence，本文件不替代 `BACKLOG.md`、`DELIVERY_PLAN.md`、active design docs、ADR 或代码事实；后续实现必须在授权窗口内回写唯一入口。

## 1. Summary

Execution Minimal Model v1.0 固定为三层结构：

1. Execution Authority：按 domain 判断 intent 是否允许执行。
2. Execution Snapshot：冻结 authority 决策后的执行输入。
3. Execution Executor：唯一执行入口，只消费 snapshot 并持久化结果。

统一执行流固定为：

```text
intent → authority → snapshot → executor → persist result
```

全局角色固定为：

| Role | Final rule |
| --- | --- |
| backend | backend-only decision；唯一产生 execution decision |
| frontend | intent only；只提交用户意图和展示上下文 |
| LLM | recommendation only；只返回建议内容或候选文本 |
| graph/fallback | adapter only；只返回可用性、调用结果或兼容信号 |

任何非 backend authority 的输出都不能直接生成执行授权、执行目标或持久化写入。所有执行必须先得到 authority 输出，再冻结为 snapshot，再交给 executor。

## 2. Execution Minimal Model

### 2.1 Three-Layer Contract

| Layer | Responsibility | Output | Prohibited |
| --- | --- | --- | --- |
| Execution Authority | 按 domain 判断 intent 是否允许执行 | `allowed` / `rejected`、`execution_target`、`reason_codes` | 执行业务动作、写入状态、调用 provider 生成业务结果 |
| Execution Snapshot | 冻结 authority 决策和执行输入 | immutable snapshot | 重新决策、重建 context、读取 runtime mutable state 派生新目标 |
| Execution Executor | 消费 snapshot 并执行唯一业务动作 | persisted result、safe response | 决策、重建 context、选择另一条执行路径 |

### 2.2 Minimal Runtime Contract

每一次 execution attempt 必须拥有以下 contract：

```text
ExecutionIntent
  → AuthorityDecisionResult
  → ExecutionSnapshot
  → ExecutionResult
```

`AuthorityDecisionResult` 是唯一决策结果：

```text
allowed: boolean
rejected: boolean
execution_target: string | null
reason_codes: string[]
decision_ref: string
```

约束：

- `allowed=true` 时，`rejected=false`，`execution_target` 必须存在，`reason_codes` 可以为空或记录非阻断说明。
- `allowed=false` 时，`rejected=true`，`execution_target=null`，`reason_codes` 必须至少包含一个拒绝原因。
- `allowed` 与 `rejected` 不得同时为 `true`，不得同时为 `false`。
- `execution_target` 只能由 authority 产生，executor 不得改写。
- `reason_codes` 只能描述 authority 决策原因，不得承载 executor 结果。

## 3. Authority Layer

Execution Authority 是唯一决策层，按 domain 拆分为：

| Authority | Domain | Allowed targets |
| --- | --- | --- |
| `QuestionAuthority` | 下一题生成、题目刷新、题目重试 | `generate_question`、`retry_question_generation` |
| `FeedbackAuthority` | 答案提交后的反馈评价、反馈重试 | `evaluate_feedback`、`retry_feedback_evaluation` |
| `ProgressAuthority` | 进度状态刷新、进度读模型更新 | `update_progress_projection`、`refresh_progress_projection` |

### 3.1 Shared Decision Inputs

Authority 只能使用以下输入：

- `intent`：frontend 提交的显式用户意图。
- `session_state`：后端持有的 session canonical state。
- `progress_state`：后端持有的 progress canonical state。
- `input_payload`：当前请求 payload。
- `runtime_flags`：后端配置的运行标记。
- `decision_ref`：本次决策引用。

禁止作为决策来源：

- frontend local state。
- UI selection、display status、optimistic state。
- LLM recommendation、suggestion、candidate text。
- graph/fallback availability 或 compatibility signal。
- provider transport success。
- legacy mapper output。

### 3.2 Domain Rules

`QuestionAuthority`：

- 只允许处理显式 next-question / retry-question intent。
- 必须校验 `session_state` 是否允许进入题目生成。
- 必须校验当前 answer / feedback 状态不会被跳过。
- 输出 `execution_target=generate_question` 或 `retry_question_generation`。
- 拒绝时必须返回 `reason_codes`，例如 `session_not_ready`、`feedback_not_closed`、`duplicate_intent`、`stale_session_state`。

`FeedbackAuthority`：

- 只允许处理显式 answer-submit / feedback-retry intent。
- 必须校验 answer payload 已通过后端输入校验。
- 必须校验 question 与 answer 属于同一 session state。
- 输出 `execution_target=evaluate_feedback` 或 `retry_feedback_evaluation`。
- 拒绝时必须返回 `reason_codes`，例如 `answer_missing`、`question_not_ready`、`payload_invalid`、`duplicate_intent`。

`ProgressAuthority`：

- 只允许处理 backend execution result 触发的 progress projection 更新 intent。
- 必须校验 progress update 依附于已完成的 backend execution result。
- 必须校验 projection 更新不会改写 question / answer / feedback canonical state。
- 输出 `execution_target=update_progress_projection` 或 `refresh_progress_projection`。
- 拒绝时必须返回 `reason_codes`，例如 `execution_result_missing`、`projection_stale`、`state_version_conflict`。

### 3.3 Authority Output Contract

每个 authority 必须返回同一结构：

```text
AuthorityDecisionResult
  allowed
  rejected
  execution_target
  reason_codes
  decision_ref
```

所有 rejected decision 必须 fail closed：

- 不创建 snapshot。
- 不调用 executor。
- 不持久化业务结果。
- 只返回 safe rejection response。

## 4. Snapshot Layer

Execution Snapshot 是 authority 决策后的冻结层。Snapshot 创建后不可变，execution 只能消费 snapshot。

### 4.1 Snapshot Fields

Snapshot 必须包含：

```text
authority_decision_result
session_state
progress_state
input_payload
execution_target
runtime_flags
decision_ref
```

Snapshot 可以包含：

```text
asset_snapshot
```

字段规则：

| Field | Rule |
| --- | --- |
| `authority_decision_result` | 完整保存 authority 输出，包含 `allowed` / `rejected` / `execution_target` / `reason_codes` / `decision_ref` |
| `session_state` | 冻结 authority 决策时看到的 session canonical state |
| `progress_state` | 冻结 authority 决策时看到的 progress canonical state |
| `input_payload` | 冻结已校验或待 executor 消费的请求输入 |
| `execution_target` | 必须等于 `authority_decision_result.execution_target` |
| `runtime_flags` | 冻结后端运行标记，不允许 executor 重新读取并改变执行路径 |
| `asset_snapshot` | 可选；只保存本次执行需要的 prompt / rubric / asset 版本引用 |
| `decision_ref` | 决策引用，贯穿日志、幂等和结果持久化 |

### 4.2 Immutability Rules

- Snapshot 一经创建，不得修改字段。
- Executor 不得从 repository、frontend state、LLM output、graph/fallback adapter 或 provider response 重建 context。
- Executor 不得在执行中重新调用 authority。
- Executor 不得因为 runtime availability 改写 `execution_target`。
- Snapshot 中没有的输入不得参与 execution。
- Snapshot 必须能支持幂等重放同一 execution attempt。

### 4.3 Snapshot Creation Rules

Snapshot 只能在 `AuthorityDecisionResult.allowed=true` 时创建。

创建过程固定为：

```text
authority_decision_result
  + current backend canonical state
  + validated input payload
  + runtime flags
  + optional asset snapshot
  → immutable execution snapshot
```

如果 authority 返回 rejected：

```text
authority_decision_result
  → safe rejection response
```

## 5. Executor Layer

Execution Executor 是唯一执行入口。Executor 只接收 immutable snapshot，不接收 frontend intent、authority 输入或 mutable context。

### 5.1 Executor Contract

Executor 输入：

```text
ExecutionSnapshot
```

Executor 输出：

```text
ExecutionResult
  persisted: boolean
  execution_target
  decision_ref
  result_status
  reason_codes
  safe_response
```

Executor 规则：

- 只执行 `snapshot.execution_target` 指定的动作。
- 不做 authority decision。
- 不做 context rebuild。
- 不允许分叉 execution path。
- 不允许根据 LLM、graph/fallback、provider 或 UI 状态改写目标。
- 不允许调用非 snapshot 声明的业务输入。
- 只通过后端 canonical persistence 写入结果。

### 5.2 Allowed Execution Targets

| `execution_target` | Executor behavior |
| --- | --- |
| `generate_question` | 基于 snapshot 生成下一题并持久化 question result |
| `retry_question_generation` | 基于同一 retry intent 重新执行题目生成并持久化结果 |
| `evaluate_feedback` | 基于 snapshot 评价 answer 并持久化 feedback result |
| `retry_feedback_evaluation` | 基于同一 retry intent 重新执行反馈评价并持久化结果 |
| `update_progress_projection` | 基于 backend execution result 更新 progress projection |
| `refresh_progress_projection` | 基于 snapshot 刷新 progress projection |

### 5.3 Persistence Rules

- persist result 必须记录 `decision_ref`。
- persist result 必须记录 `execution_target`。
- persist result 必须保留 authority 的 `reason_codes` 或追加 executor failure reason codes。
- 写入失败时返回 safe failure response，不暴露 raw provider payload、exception stack、transport detail 或 secret。
- 同一 `decision_ref` 的重复执行必须返回已有结果或幂等 no-op。

## 6. Execution Flow

所有链路统一为：

```text
intent → authority → snapshot → executor → persist result
```

### 6.1 Question Flow

```text
frontend question intent
→ QuestionAuthority
→ ExecutionSnapshot(execution_target=generate_question | retry_question_generation)
→ ExecutionExecutor
→ persist question result
```

拒绝路径：

```text
frontend question intent
→ QuestionAuthority(rejected, reason_codes)
→ safe rejection response
```

### 6.2 Feedback Flow

```text
frontend answer-submit or feedback-retry intent
→ FeedbackAuthority
→ ExecutionSnapshot(execution_target=evaluate_feedback | retry_feedback_evaluation)
→ ExecutionExecutor
→ persist feedback result
```

拒绝路径：

```text
frontend answer-submit or feedback-retry intent
→ FeedbackAuthority(rejected, reason_codes)
→ safe rejection response
```

### 6.3 Progress Flow

```text
backend progress-update intent
→ ProgressAuthority
→ ExecutionSnapshot(execution_target=update_progress_projection | refresh_progress_projection)
→ ExecutionExecutor
→ persist progress result
```

拒绝路径：

```text
backend progress-update intent
→ ProgressAuthority(rejected, reason_codes)
→ safe rejection response
```

### 6.4 Cross-Flow Rule

Question、Feedback、Progress 三条链路只共享同一五段 flow，不共享执行入口以外的隐式授权。任何 flow 都必须先经过对应 authority，再创建 snapshot，再进入 executor。

## 7. Migration Strategy

迁移目标是把现有实现收敛到三层模型，不引入新执行体系。

### 7.1 Step 1: Normalize Authority Results

- 为 `QuestionAuthority`、`FeedbackAuthority`、`ProgressAuthority` 建立统一 `AuthorityDecisionResult`。
- 所有 domain authority 输出必须包含 `allowed`、`rejected`、`execution_target`、`reason_codes`、`decision_ref`。
- 移除由 frontend、LLM、graph/fallback、provider、legacy mapper 派生执行目标的逻辑。

验收：

- rejected decision 不创建 snapshot。
- allowed decision 必须携带非空 `execution_target`。
- reason code 能解释每个拒绝结果。

### 7.2 Step 2: Introduce Immutable Snapshot

- 在 authority 后创建 `ExecutionSnapshot`。
- 将 `session_state`、`progress_state`、`input_payload`、`runtime_flags`、`execution_target`、`decision_ref` 冻结进 snapshot。
- 如执行依赖 prompt / rubric / asset 版本，写入 `asset_snapshot`。
- 禁止 executor 再读取 mutable context 来改变本次执行。

验收：

- executor 入参只有 snapshot。
- snapshot 中的 `execution_target` 与 authority result 一致。
- runtime flag 变化不影响已经创建的 snapshot。

### 7.3 Step 3: Collapse Execution Entrypoints

- 所有 question / feedback / progress 执行动作统一进入 `ExecutionExecutor`。
- executor 根据 `snapshot.execution_target` 分发到唯一内部 handler。
- 移除 route、frontend handler、LLM result、graph/fallback adapter、provider callback 直接触发执行的路径。

验收：

- question、feedback、progress 都符合 `intent → authority → snapshot → executor → persist result`。
- executor 不调用 authority。
- executor 不重建 context。

### 7.4 Step 4: Persist With Decision Reference

- 所有持久化结果写入 `decision_ref`。
- 所有持久化结果写入 `execution_target`。
- 幂等逻辑以 `decision_ref` 和目标状态为准。
- failure response 只返回 safe response 和 reason code。

验收：

- 同一 `decision_ref` 重放不产生重复业务结果。
- rejected decision 无业务写入。
- failure 不泄露 raw runtime detail。

## 8. Hard Rules

1. 系统只允许三层结构：Execution Authority、Execution Snapshot、Execution Executor。
2. 所有执行必须使用 `intent → authority → snapshot → executor → persist result`。
3. Authority 是唯一决策层，且必须 backend-only。
4. Authority 必须按 domain 分为 `QuestionAuthority`、`FeedbackAuthority`、`ProgressAuthority`。
5. Authority 输出必须包含 `allowed`、`rejected`、`execution_target`、`reason_codes`。
6. `allowed=false` 必须 fail closed，不创建 snapshot，不调用 executor，不写业务结果。
7. Frontend 只能提交 intent，不能参与 execution decision。
8. LLM 只能提供 recommendation，不能触发 execution。
9. graph/fallback 只能作为 adapter，不能参与 authorization、target selection 或 persistence。
10. Snapshot 是冻结层，创建后不可变。
11. Snapshot 必须包含 `authority_decision_result`、`session_state`、`progress_state`、`input_payload`、`execution_target`、`runtime_flags`、`decision_ref`。
12. `asset_snapshot` 只作为可选冻结引用，不能成为新的决策来源。
13. Executor 是唯一执行入口。
14. Executor 不做决策。
15. Executor 不做 context rebuild。
16. Executor 不允许分叉 execution path。
17. Executor 只能消费 snapshot。
18. Executor 只能执行 `snapshot.execution_target`。
19. Persist result 必须绑定 `decision_ref` 和 `execution_target`。
20. 任何绕过 authority、snapshot 或 executor 的执行都必须删除或改为 adapter / intent / persistence response。

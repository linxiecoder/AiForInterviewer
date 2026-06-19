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
- 承接用户确认的 breaking-change decisions：ADR-0005 addendum 后置落库、统一入口 + domain handler、暂不优先 durable idempotency、旧 direct path 默认删除、旧 API compat 默认破坏式替换、Progress 拆分 canonical write / projection refresh、旧测试按新契约重写。
- 不引入外部 issue 模型、外部 issue 清单或额外架构推断。

输出边界：

- 本文件只做 execution plan decomposition。
- 本文件不替代 `BACKLOG.md`、`DELIVERY_PLAN.md`、active design docs、ADR 或代码事实。
- 后续实现必须在授权窗口内回写唯一入口。
- 所有任务保持工程实施粒度，不做架构重设计，不引入新的编译器、图谱或运行时模型，不做图化任务拆分。

## Preflight: Breaking-change Scope And ADR Delta

### 1. Objective

在实施前锁定破坏式清理边界，避免后续继续保留旧兼容层。本 Preflight 不创建新 active docs，不替代 ADR / BACKLOG / DELIVERY_PLAN；它只整理后续回写 ADR-0005 addendum 和 active docs 所需的 delta。

### 2. Tasks

1. 列出旧 direct path、旧 API compat fields / mirror payload、legacy mapper、placeholder / skeleton route、旧测试断言。
2. 为每一项标记处理方式：`delete`、`replace`、`rewrite`、`temporary_exception`。
3. 默认不保留旧 direct path、不保留旧 compat payload、不保留旧 contract test expected。
4. 明确本轮不实现 durable idempotency / running task lifecycle；`decision_ref` 只作为追踪引用。
5. 整理 expected ADR-0005 addendum delta，待重构完成后回写最终决策。
6. 任何 `temporary_exception` 必须使用固定字段记录：`reason`、`allowed_scope`、`blocking_condition`、`delete_condition`、`cleanup_phase_or_task`、`owner_check`；不得只写“暂时保留”。
7. 开发前必须用 `rg` 做定向现状复核，并把结果回填到 legacy cleanup inventory 后才能进入 Phase 1：
   - route / API endpoint：`apps/api/app/api/v1/polish.py`。
   - use case / application service：`apps/api/app/application/polish/use_cases.py`。
   - repository / persistence：`apps/api/app/infrastructure/db/repositories/polish.py`。
   - frontend request construction：`apps/web/src/pages/interview/InterviewPage.tsx`。
   - frontend types / API client：`apps/web/src/entities/polish/model/types.ts` 及实际 API client 文件。
   - tests / contract tests：`tests/api/*polish*`、frontend 相关 tests。
   - legacy direct / fallback / compat payload 残留：定向扫描 `direct`、`fallback`、`compat`、`mirror`、`selected_progress_node_ref`、`completed_focus_refs`、`candidate_refs`、`legacy_direct_path_retained`。

### 3. Validation Plan

- 形成 legacy cleanup inventory，且每一项只有 `delete`、`replace`、`rewrite` 或 `temporary_exception` 四类处理方式。
- 确认没有把 temporary exception 写成长期 fallback、长期 compat 或长期测试保护。
- 确认每个 `temporary_exception` 都包含 blocking condition、删除条件和后续清理任务位置。
- 确认开发前 `rg` 复核已覆盖 route、use case、repository、frontend request、frontend types / API client、tests 和 legacy direct / fallback / compat payload 残留。
- 确认后续 Phase 的任务描述不再要求保留旧 direct path、旧 compat shape 或旧 fallback success。

## Phase 1: Control-plane Isolation

### 1. Objective

收敛 execution authority 的来源。审计报告指出，下一题生成权、执行目标、授权 refs 和 grant snapshot 分散在 frontend selection、API route、command fields、feedback payload、runtime policy、handoff/repository 等位置；现有方案要求 authority 成为 backend-only 的唯一决策层，并统一输出 `allowed`、`rejected`、`execution_target`、`reason_codes`、`decision_ref`。

### 2. Scope

- `apps/api/app/application/polish/commands.py`
- `apps/api/app/application/polish/use_cases.py`
- `apps/api/app/api/v1/polish.py`
- `CreatePolishQuestionTaskCommand`
- `NextQuestionExecutionGrant`
- `QuestionAuthority` / `FeedbackAuthority` / `ProgressCanonicalAuthority` / `ProgressProjectionPolicy` 的模块级输出边界
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
  - `decision_ref` 能贯穿后续 response、结果关联和持久化追踪计划，但不声明 durable idempotency。
- Test Points:
  - 覆盖 allowed question intent，断言输出包含 `execution_target=generate_question` 或 `retry_question_generation`。
  - 覆盖 rejected question intent，断言不进入后续执行入口。
  - 覆盖 feedback / progress 的 rejected decision，断言 `reason_codes` 可解释拒绝。
  - 覆盖非法 authority 状态组合，断言 fail closed。
- Risk Notes:
  - 如果仅新增字段而不移除旧字段消费，authority 仍会分叉。
  - 如果 `reason_codes` 被复用为 executor 结果状态，会继续混淆解释信号和执行结果。
  - 如果 `decision_ref` 只出现在 response，不进入持久化追踪，后续排查无法关联 authority decision 与结果。

#### Task 1.2: 移除非 backend 的执行目标派生

- Task Name: 移除非 backend 的执行目标派生
- Target Area: `apps/api/app/api/v1/polish.py` 与 `apps/api/app/application/polish/use_cases.py`
- Steps:
  1. 检查 `/questions` 与 `/feedback/{feedback_id}/next-question` 两个入口传入 `create_question_task` 的 command 组装逻辑。
  2. 将 frontend local state、UI selection、display status、optimistic state 从 execution target 决策来源中移出。
  3. 将 LLM recommendation、candidate text、graph/fallback availability、provider transport success 标记为非授权来源。
  4. 保留 route 层的请求适配职责，但不允许 route 层直接生成执行授权或执行目标。
  5. 默认删除旧适配信号；如确实无法立刻删除，只能登记为 `temporary_exception`，并限定为 adapter output 或 safe response metadata。
- Checkpoints:
  - API route 不直接生成 `execution_target`。
  - frontend 传入的 selection 类字段不会被解释为授权目标。
  - LLM / graph / provider 输出不能直接触发 persistence。
  - rejected authority path 不会因 legacy fallback 或 temporary exception 继续执行。
- Test Points:
  - 通过 direct question path 与 feedback next-question path 传入相同 intent，断言执行目标只来自 authority。
  - 模拟 frontend selection 变化，断言 backend `execution_target` 不被 UI focus 改写。
  - 模拟 provider success 但 authority rejected，断言不持久化业务结果。
  - 模拟 graph disabled / fallback available，断言不产生授权。
- Risk Notes:
  - route 文件当前同时承担 dependency wiring、response contract、compat shape、payload filtering；本轮默认删除旧 compat shape，改动时不得把旧响应兼容误当 authority。
  - feedback payload 中 evaluation-shaped fields 可能继续越界成 orchestration signal。
  - legacy mapper 默认删除；若登记为 temporary exception，必须确认其输出不是目标选择器，并写明删除条件。

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

#### Task 1.4: 修复 repository / application entity 依赖方向

- Task Name: 修复 repository / application entity 依赖方向
- Target Area: `apps/api/app/infrastructure/db/repositories/polish.py`、`apps/api/app/application/polish/ports.py`、`apps/api/app/application/polish/entities.py`
- Steps:
  1. 梳理 repository 当前是否直接 import 或返回 application entity。
  2. 明确 repository 只能消费 persistence model、repository DTO、primitive persistence shape 或 port 定义的出入参；不得反向依赖 application entity。
  3. 将 application 层通过 port 接口消费 repository，application entity 的组装留在 application boundary 内。
  4. 若需要跨层数据承载，定义 repository DTO / persistence DTO，并保证其不携带 authority、snapshot 或 executor 语义。
  5. 增加 import boundary test 或 contract test，防止 `infrastructure/db/repositories/*` 重新 import `application/polish/entities.py`。
- Checkpoints:
  - repository 不再反向 import application entity。
  - persistence DTO 与 application entity 的边界清晰。
  - repository 不成为新的 domain decision 或 execution authority 来源。
  - import boundary test 能防止依赖方向回归。
- Test Points:
  - import boundary test 覆盖 repository 到 application entity 的禁止依赖。
  - repository contract test 覆盖 DTO / persistence shape 与 port 约定。
  - application use case 能在 port 边界内组装 application entity。
  - rejected authority path 不因 repository helper 产生业务写入。
- Risk Notes:
  - 如果只移动 import 但保留 application entity 在 repository 内组装，依赖方向仍未修复。
  - 如果 repository DTO 命名过像 domain entity，后续实现容易把 persistence shape 当业务事实源。
  - 本任务不新增数据库 schema，不引入 migration；只修复依赖方向和边界测试。

#### Task 1.5: 定义 `use_cases.py` 最小模块拆分落点

- Task Name: 定义 `use_cases.py` 最小模块拆分落点
- Target Area: `apps/api/app/application/polish/use_cases.py` 与同目录新增或既有 application 模块
- Steps:
  1. 先给出最小模块拆分图，再移动代码；不得只按行数切文件。
  2. 将 `AuthorityDecisionResult`、`ExecutionSnapshot`、`ExecutionResult` 等纯 contract / entity 放在 `entities.py` 或明确的 contract 模块。
  3. 将 `QuestionAuthority`、`FeedbackAuthority`、`ProgressCanonicalAuthority` 放在 authority 模块。
  4. 将 `ProgressProjectionPolicy` 放在 policy / projection 模块，避免被误用为业务 execution authority。
  5. 将 `ExecutionExecutor` 放在 executor 模块；executor 只做 snapshot 边界校验和 domain handler dispatch。
  6. 将 `QuestionExecutionHandler`、`FeedbackExecutionHandler`、`ProgressCanonicalHandler`、`ProgressProjectionHandler` 放在 handler 模块或按 domain 拆分的 handler 模块。
  7. 将 `use_cases.py` 收敛为 route-facing application orchestration，不再同时持有 repository、LLM、progress、runtime facade、policy resolver 和 persistence handoff 的全部细节。
- Checkpoints:
  - 拆分图能说明每个 use case / handler / authority / policy 的文件落点。
  - `use_cases.py` 不再是单体业务事实 owner。
  - executor 不是单体大 executor；domain 细节落到 handler。
  - 拆分后责任边界可由 focused tests 或 import boundary tests 验证。
- Test Points:
  - authority tests 只覆盖 decision output，不调用 provider 或 persistence。
  - executor tests 只断言 snapshot dispatch，不重建 context。
  - handler tests 覆盖各 domain 持久化行为，不互相隐式授权。
  - import / contract tests 覆盖 use case、authority、executor、handler 的依赖方向。
- Risk Notes:
  - 不能把 `use_cases.py` 的单体复杂度搬到 `executor.py`。
  - 不能为了拆文件新增未授权抽象或新的运行时模型。
  - done condition 是职责边界可测，而不是文件数量增加或单个文件变小。

### 4. Validation Plan

- 验证修复有效：用 focused tests 覆盖 allowed / rejected authority path，断言 rejected decision 不创建 snapshot、不调用 executor、不写业务结果；断言 allowed decision 必须携带非空 `execution_target`。
- 确认没有 regression：按新 API response contract 覆盖 direct question path、feedback next-question path、feedback evaluation path 的用户主路径；不保留旧 compatibility shape 作为断言目标。
- 确认 control-plane 没新增分叉：扫描 route、command、use case、policy result 消费点，确认只有 backend authority 输出 `execution_target`，frontend、LLM、graph/fallback、provider、legacy mapper 不再生成执行授权。
- 确认 repository 边界没有反向依赖：扫描 `infrastructure/db/repositories/*`，确认不存在对 application entity 的反向 import，且 import boundary test 已覆盖。
- 确认 `use_cases.py` 拆分不是形式拆分：每个 authority、policy、executor、handler 的责任边界与文件落点均可被测试或 import rule 区分。

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
  - feedback path 当前仍有 v1 命名和 legacy 兼容字段；本轮默认删除旧 compat 字段，但不能把命名清理扩成未授权的新业务语义。
  - evaluation-shaped fields 继续被下游当 orchestration signal 会复发 authority 分裂。
  - safe response 不应泄露 provider exception stack、transport detail 或 secret。

#### Task 2.3A: 收敛 canonical progress write

- Task Name: 收敛 canonical progress write
- Target Area: canonical progress update use case、`ProgressCanonicalAuthority`、`ProgressCanonicalHandler`
- Steps:
  1. 将 canonical progress write 限定为 backend execution result 触发的 intent。
  2. 通过 `ProgressCanonicalAuthority` 校验 canonical progress write 依附于已完成 backend execution result。
  3. 将 canonical progress write 纳入 executor target：`update_progress_canonical`。
  4. 让 `ProgressCanonicalHandler` 只消费 snapshot 与已完成 execution result，不读取 frontend display status 或 projection state 来选择目标。
  5. 对 progress canonical write 失败返回 safe failure / rejection，不改写 question / answer / feedback canonical state。
- Checkpoints:
  - canonical progress write 不由 frontend display status 触发。
  - canonical progress write 只能跟随 backend execution result。
  - `ProgressCanonicalAuthority` rejected 时不创建 snapshot、不调用 handler、不写 canonical state。
  - canonical write 与 projection refresh 的入口、handler 和测试断言分开。
- Test Points:
  - question result persisted 后触发 canonical progress write。
  - feedback result persisted 后触发 canonical progress write。
  - 缺失 backend execution result 时 `ProgressCanonicalAuthority` rejected。
  - canonical write state version conflict 时返回 safe rejection / failure。
- Risk Notes:
  - 审计报告指出 progress tree 读 turns / feedback / question completion，容易继续成为隐式状态汇聚点。
  - 如果 canonical write 从 projection state 派生目标，Progress authority 会再次分裂。
  - 不能在本任务调整 progress 文案或 UI fallback；只处理 canonical write。

#### Task 2.3B: 收敛 progress projection refresh

- Task Name: 收敛 progress projection refresh
- Target Area: progress projection refresh use case、`ProgressProjectionPolicy`、`ProgressProjectionHandler`
- Steps:
  1. 将 projection refresh 限定为 `ProgressProjectionPolicy` + `ProgressProjectionHandler` 的派生读模型更新。
  2. 明确 projection refresh 不产生业务授权，不创建新的 question / feedback execution decision。
  3. 禁止 progress projection 更新改写 question / answer / feedback canonical state。
  4. 禁止 projection refresh 结果反向成为 `execution_target`、frontend target selection 或 retry authorization。
  5. 对 progress failed / refresh_failed response 保持 safe display / safe failure 语义。
- Checkpoints:
  - projection refresh 不成为隐式 execution target 来源。
  - projection failure 不改写 canonical state。
  - `ProgressProjectionPolicy` 与 `ProgressCanonicalAuthority` 的返回语义可测试区分。
  - projection handler 不调用 canonical write handler，也不绕过 executor 写业务结果。
- Test Points:
  - projection stale 时返回 safe display / failure，不改写 canonical state。
  - refresh_failed 只影响 projection / display state，不影响 question / feedback canonical state。
  - frontend 将 progress tree 当 action target 时，不会通过 projection refresh 派生 backend target。
  - projection refresh 测试断言 adapter / read-model 语义，而不是业务 execution authority。
- Risk Notes:
  - frontend 将 progress tree 当 action target 时，会与 Phase 4 产生边界依赖。
  - projection refresh 不能因为返回 `execution_target=refresh_progress_projection` 而被误升格为 question / feedback 同级业务执行。
  - 不能用一个泛化 progress status 同时覆盖 canonical write failure 和 projection refresh failure。

#### Task 2.4: 持久化绑定 `decision_ref` 与 `execution_target`（非幂等）

- Task Name: 持久化绑定 `decision_ref` 与 `execution_target`（非幂等）
- Target Area: question / feedback / progress persistence handoff
- Steps:
  1. 为 question result persistence 写入 `decision_ref` 与 `execution_target`。
  2. 为 feedback result persistence 写入 `decision_ref` 与 `execution_target`。
  3. 为 canonical progress result / projection refresh result 写入 `decision_ref` 与 `execution_target`，或在派生刷新响应中保留可追踪引用。
  4. 将写入失败统一为 safe failure response。
  5. 明确本轮不实现 durable duplicate suppression、running task recovery、resume / cancel / deadline lifecycle。
- Checkpoints:
  - 每个 persisted result 都能追溯到 authority decision。
  - `decision_ref` 只承担追踪与排查，不作为 durable idempotency contract。
  - rejected decision 没有业务写入。
  - failure response 不包含 raw provider payload。
- Test Points:
  - question execution 写入结果时携带 `decision_ref` 与 `execution_target`。
  - feedback execution 写入结果时携带 `decision_ref` 与 `execution_target`。
  - 持久化失败时返回 safe response。
  - rejected decision 后检查 repository 没有新增业务结果。
- Risk Notes:
  - 如果旧 persistence path 没有同步关闭，旧路径仍可能绕过追踪字段。
  - 如果 `execution_target` 只写日志不写结果，后续排查无法确认执行来源。
  - 不能把 provider transport success 当 persisted success。

### 4. Validation Plan

- 验证修复有效：用 flow-level tests 覆盖 question、feedback、progress 三条链路，断言都符合 `intent → authority → snapshot → executor → persist result`，且 executor 不调用 authority、不重建 context。
- 确认没有 regression：覆盖现有 direct question、feedback next-question、answer-submit、feedback retry、progress refresh 的用户主路径和新 response contract；旧 compat 字段不作为保留目标。
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
  4. 将 `decision_ref` 作为 snapshot、日志、结果关联和持久化追踪的贯穿引用，不声明 durable idempotency。
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
  - graph/fallback 只返回可用性、调用结果或 adapter status。
  - provider success 不会改写 `execution_target`。
- Test Points:
  - 创建 snapshot 后切换 runtime flag，断言 executor 仍按 snapshot 执行。
  - 缺少 provider 时返回 safe failure，不改变 execution target。
  - graph disabled 时不改变 snapshot target。
  - asset version 变化不影响已创建 snapshot 的确定性检查和调试复盘。
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
  5. 为同一 snapshot 的目标不可变和输入不可扩展补充断言；不要求幂等重放。
- Checkpoints:
  - executor 不接收 frontend intent。
  - executor 不接收 authority input。
  - executor 不读取 mutable context 来改变路径。
  - executor 只执行 `snapshot.execution_target`。
- Test Points:
  - executor 入参缺少 snapshot 时失败。
  - snapshot 中没有的 field 不参与 service call。
  - 同一 snapshot 的检查结果保持目标不可变，不要求返回已有结果或 no-op。
  - provider / graph output 变化不改变 execution target。
- Risk Notes:
  - 如果 executor 仍读取 progress tree 当前状态来选目标，Phase 1 authority 收敛会被破坏。
  - 如果 service dependency 内部仍 direct write，需要在 Phase 2 / Phase 5 同步关闭。
  - 不能把 context rebuild 移到 helper 中规避检查。

### 4. Validation Plan

- 验证修复有效：覆盖 allowed 创建 snapshot、rejected 不创建 snapshot、snapshot target 等于 authority target、runtime flag 变化不影响已创建 snapshot、同一 snapshot 的目标不可变。
- 确认没有 regression：覆盖 question / feedback / progress 的 happy path 与 safe failure path，确认响应仍能返回用户需要的 safe response，不泄露 raw provider payload、exception stack、transport detail 或 secret。
- 确认 control-plane 没新增分叉：扫描 executor 和 service dependency 调用点，确认没有从 repository、frontend state、LLM output、graph/fallback adapter、provider response 重建 execution target。

## Phase 4: Frontend Isolation

### 1. Objective

隔离 UI 权限。审计报告指出 frontend 不是纯展示层，`InterviewPage.tsx` 会计算 `selected_progress_node_ref` 和 `completed_focus_refs`，并用 task refs 回写本地焦点；frontend selection 与 backend target 重复派生，UI fallback mapper 会掩盖 backend 语义差异。现有方案要求 frontend 只能提交 intent 和展示上下文，不能参与 execution decision。

### 2. Scope

- `apps/web/src/pages/interview/InterviewPage.tsx`
- `apps/api/app/schemas/polish.py`
- `apps/web/src/entities/polish/model/types.ts`
- frontend API client / request adapter
- frontend next-question / answer-submit / feedback-retry request construction
- frontend task refs 与 local focus reconciliation
- UI fallback mapper 与 safe response rendering
- API / contract tests

本阶段只做 UI 权限隔离，不改 backend authority 规则，不合并 executor，不清理 backend legacy route。

### 3. Tasks

#### Task 4.0: 同步破坏式 API contract 替换

- Task Name: 同步破坏式 API contract 替换
- Target Area: backend schema、frontend model/types、API client、API / contract tests
- Steps:
  1. 梳理新 response / request contract 对 backend Pydantic schema 的影响，更新 `apps/api/app/schemas/polish.py` 中与 question、feedback、progress、task response 相关的字段。
  2. 同步更新 frontend model/types，至少覆盖 `apps/web/src/entities/polish/model/types.ts` 中对应 request / response 类型。
  3. 同步更新 frontend API client / request adapter，确保 request construction 不再发送旧 compat fields、mirror payload 或 execution target 类 UI selection 字段。
  4. 同步更新 API tests / contract tests，断言目标改为新 authority / snapshot / executor-handler contract。
  5. 明确删除旧 compat shape、mirror payload、fallback success shape 的断言；不得通过双 shape 或 optional compat fields 保持旧契约。
- Checkpoints:
  - backend schema、frontend types、API client 和 tests 在同一切片内同步。
  - API response 不再输出旧 compat mirror payload。
  - frontend request 不再携带旧 execution target 类 UI selection 字段。
  - contract tests 不再以旧 compat shape 作为 expected。
- Test Points:
  - backend API tests 覆盖新 response contract。
  - frontend request payload tests 覆盖 intent-only request。
  - frontend type checks 或 focused tests 覆盖新 response shape 的消费。
  - forbidden contract tests 覆盖 compat payload reintroduction。
- Risk Notes:
  - 只改 backend schema 会造成 frontend contract drift。
  - 只改 frontend types 但保留 API client 旧字段，会继续把 UI selection 发送给后端。
  - 不能用 optional fields 暗中保留旧 compat shape；本轮接受破坏式替换。

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
  - 若 backend 尚未完成 Phase 1/2，frontend intent-only 改动必须与后端破坏式契约更新在同一切片同步完成，不保留长期兼容窗口。
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
- 验证 contract 同步有效：backend schema、frontend model/types、API client、API / contract tests 均已按新契约更新，且旧 compat shape / mirror payload 不再作为断言目标。
- 确认没有 regression：覆盖 question、feedback、progress 的用户可见状态渲染，确认 pending、safe rejection、safe failure、candidate-only、formal persisted success 都能正常展示。
- 确认 control-plane 没新增分叉：扫描 `InterviewPage.tsx` 中 request construction、local focus reconciliation、status mapper，确认没有从 UI selection、task refs、fallback mapper 生成 execution authorization 或 target selection。

## Phase 5: Cleanup & Risk Removal

### 1. Objective

清理遗留路径和风险。审计报告指出 active、placeholder、skeleton、default-off、legacy_direct_path_retained 同时是运行事实；placeholder route 和 skeleton use case 已挂入 v1 API；status 语义在 candidate、formal、fallback、partial、skeleton、validation_failed 等模块间扩散；tests 会固化当前分裂结构。本轮要求任何绕过 authority、snapshot 或 executor 的旧执行路径默认删除；只有已登记的 `temporary_exception` 可以短期隔离为 unavailable / adapter-only，并必须写明删除条件。

### 2. Scope

- `apps/api/app/api/v1/polish.py`
- `pressure_skeleton`、`review_skeleton`、`ai_task_skeleton`
- `domain/*/services.py` 中的 pass 壳
- graph facade、direct fallback、fake transport gate、provider boundary
- candidate workflow、formal write、pending payload、progress failed artifact、frontend fallback mapper 的状态边界
- 现有 contract tests 与 flow tests

本阶段只做遗留路径清理和风险移除，不新增业务能力，不新增执行目标，不重构阶段计划。

### 3. Tasks

#### Task 5.1: 删除 placeholder / skeleton 运行入口

- Task Name: 删除 placeholder / skeleton 运行入口
- Target Area: `apps/api/app/api/v1/polish.py` 中的 placeholder route 与 skeleton use case
- Steps:
  1. 梳理 `pressure_skeleton`、`review_skeleton`、`ai_task_skeleton` 是否仍挂入 v1 API。
  2. 默认将不会进入真实 execution flow 的 route 移出运行入口；无法立即移除时登记为 `temporary_exception` 并返回 unavailable safe response。
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
  - 删除 route 可能破坏旧调用方；本轮接受破坏式清理，只有 temporary exception 可短期隔离，且必须保证不会形成 false capability。
  - skeleton_succeeded 这类状态名容易被误解为业务成功。
  - 不能把 placeholder cleanup 扩成新功能实现。

#### Task 5.2: 删除 graph / fallback / provider legacy direct 分支

- Task Name: 删除 graph / fallback / provider legacy direct 分支
- Target Area: `AiOrchestrationFacade`、graph facade、direct fallback、fake transport gate、provider boundary
- Steps:
  1. 梳理 graph default-off、legacy direct path、fake runtime、provider boundary 的调用分支。
  2. 将 graph/fallback 输出限制为可用性、调用结果或 safe adapter status。
  3. 删除绕过 authority / snapshot / executor 的 legacy direct execution path；无法立即删除时必须登记为 `temporary_exception` 并降级为 adapter-only。
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

#### Task 5.4: 重写固化旧结构的测试断言

- Task Name: 重写固化旧结构的测试断言
- Target Area: polish API / application / frontend 相关 contract tests 与 flow tests
- Steps:
  1. 梳理直接断言多入口、多 fallback、多 UI focus、旧 compat payload 的测试。
  2. 先判断测试保护的是用户主路径还是旧实现细节。
  3. 用户主路径测试按新 authority / snapshot / executor-handler 契约重写。
  4. 旧 compat / direct path / fallback success 行为测试默认删除。
  5. 增加 forbidden path 回归断言，覆盖 bypass authority、bypass snapshot、bypass executor、legacy mapper target selection 和 compat payload reintroduction。
- Checkpoints:
  - 测试不再要求 frontend selection 参与 backend target。
  - 测试不再要求 graph/fallback direct path retained。
  - 测试不再覆盖旧 response compatibility shape。
  - forbidden path 断言覆盖主要 bypass。
- Test Points:
  - 用户主路径测试按新 response contract 重写。
  - UI focus 测试改为断言 intent-only payload。
  - provider / graph 测试改为断言 adapter-only 或 no direct execution。
  - skeleton / placeholder 测试断言不存在、不可用或不声明 implemented。
- Risk Notes:
  - 如果测试只跟随实现删除断言，可能漏掉 regression。
  - 如果保留旧测试但改 expected 为新 success，会固化新的分叉。
  - 测试调整必须区分用户主路径、新执行契约和旧实现细节。

### 4. Validation Plan

- 验证修复有效：运行 focused regression 覆盖 placeholder / skeleton route、graph disabled、fake provider、provider missing、candidate-only、formal write、progress failed / refresh_failed，确认绕过 authority、snapshot 或 executor 的路径被删除；temporary exception 必须可清点。
- 确认没有 regression：运行 polish API / application / frontend 相关测试，确认用户主路径、新 response contract、用户可见状态和持久化结果符合前四个 Phase 的 contract；不要求旧 compatibility shape 或 durable idempotency 行为。
- 确认 control-plane 没新增分叉：做 forbidden path scan，确认不存在 route-level direct write、frontend target selection、LLM-triggered execution、graph/fallback authorization、provider-triggered persistence、legacy mapper target selection、skeleton false capability。

## Final Cleanup Gate

完成条件：

- route / use case 中不存在旧 direct execution path。
- API response 不再输出旧 compat mirror payload。
- frontend 不再发送 execution target 类 UI selection 字段。
- tests 不再断言旧 direct path、旧 compat shape、旧 fallback success。
- 仅保留新 authority / snapshot / executor-handler 契约测试。
- `ProgressCanonicalAuthority` 与 `ProgressProjectionPolicy` 的边界可被测试区分。
- `decision_ref` 只作为追踪引用，不被描述为 durable idempotency contract。
- repository / persistence 层不存在反向 import application entity，且 import boundary test 或 contract test 已覆盖。
- backend schema、frontend model/types、API client、contract tests 已同步到新 API contract。
- `use_cases.py` 不再作为 repository、LLM、progress、runtime facade、policy resolver 和 persistence handoff 的单体事实 owner。
- ADR-0005 addendum delta 已整理，可进入后续 active docs 回写窗口。

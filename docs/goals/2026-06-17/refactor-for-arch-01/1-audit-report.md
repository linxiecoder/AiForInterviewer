---
title: 1-audit-report
type: note
permalink: ai-for-interviewer/docs/goals/2026-06-17/refactor-for-arch-01/1-audit-report-1
---

• 1. Agent Reports (1-5)

  Agent 1: Architecture Analyst

  - DDD 主要是目录形状，不是运行事实。Polish 核心实体在 apps/api/app/application/polish/entities.py:1，而多个 domain/*/services.py 是 pass 壳。
  - 实际业务重心集中在 apps/api/app/application/polish/use_cases.py:168：repository、LLM、progress tree、question、feedback、runtime facade、policy resolver 同时被一个 operations
    对象持有。

  - API 层也不是薄 adapter。apps/api/app/api/v1/polish.py:273 同时承担 route、dependency wiring、response contract、compat shape、payload filtering。
  - 分层破坏模式：domain 是命名空间，application 是事实 owner，API 是 contract composer，repository 反向依赖 application entity。

  Agent 2: AI Flow Analyst

  - Question / feedback / progress tree 不是单向链路，而是循环影响：progress tree 读 turns/feedback，question 读 progress/evaluation history，complete_question() 又写 progress
    state。

  - 出题有多入口：apps/api/app/api/v1/polish.py:273 与 apps/api/app/api/v1/polish.py:501 都进入 create_question_task。
  - Graph / service / facade 分裂：question 可走 AiOrchestrationFacade，feedback facade 明确拒绝并要求 FeedbackGenerationService.generate_feedback_v1()。
  - Prompt/runtime 多套并存：progress prompt、question prompt、feedback prompt、planned workflow、graph workflow、direct service workflow 同时存在。

  Agent 3: Control Plane Analyst

  - Intent / grant / execution 只是字段级分离，不是执行边界分离。apps/api/app/application/polish/commands.py:32 同时承载 selection、execution source、authorized refs、grant
    snapshot。

  - Frontend 不是纯展示层。apps/web/src/pages/interview/InterviewPage.tsx:5020 会计算 selected_progress_node_ref 和 completed_focus_refs，并用 task refs 回写本地焦点。
  - NextQuestionExecutionGrant 存在，但嵌在 apps/api/app/application/polish/use_cases.py:410 内即时生成、校验、消费。
  - Runtime flags / provider boundary 只是运行能力 gate，不是业务 execution authority。

  Agent 4: Legacy & Version Drift Analyst

  - active、placeholder、skeleton、default-off、legacy_direct_path_retained 同时是运行事实。
  - Question graph 是 pr9-agent-orchestration，feedback graph 仍有 pr5-skeleton / pr6-fake-runtime / pr7-readonly-parity 痕迹。
  - v2 主要出现在 progress tree metadata；主流程仍大量是 .v1、generate_feedback_v1、invoke_provider_v1。
  - Placeholder route 和 skeleton use case 已挂入 v1 API，例如 pressure_skeleton、review_skeleton、ai_task_skeleton。

  Agent 5: Pattern Miner

  - 重复模式不是单点 bug，而是跨模块同构：authority 附加、artifact lifecycle 多终态、policy result 双重角色、runtime fallback 语义不等价、frontend selection 参与 execution
    target。

  - 最关键重复结构：每个新 AI 能力都增加一组 endpoint/schema/frontend path、metadata、status、candidate refs、fallback，而不是替换旧执行事实。

  2. Systemic Root Cause

  唯一核心根因：

  系统复杂性是由“叠加式控制面演进”生成的。

  每次新增能力时，系统没有淘汰旧的 direct path、旧 endpoint、旧 status、旧 payload shape、旧 frontend selection 语义；而是把新的 grant、candidate、policy、graph、runtime flag、
  planned workflow 作为 metadata、adapter、fallback branch 或兼容字段叠加到原路径上。

  所以复杂性不是自然来自 AI 业务难，而是来自同一决策对象被多层重复表达：

  - “下一题生成权”同时存在于 frontend selection、API route、command fields、feedback payload、grant snapshot、runtime policy。
  - “AI 结果状态”同时存在于 candidate payload、formal write、task status、feedback payload、progress state、frontend fallback mapper。
  - “安全/可用/降级”同时由 provider boundary、runtime flag、graph disabled、fake gate、fallback reason、本地 deterministic path 表达。

  系统每加一层保护或能力，就横向复制一套 authority / lifecycle / status / contract；旧层没有消失，因此复杂性持续生成。

  3. Agreement Map

  - 所有 Agent 都观察到：application/API 是真实运行 owner，domain 层不是主要行为 owner。
  - 所有 Agent 都观察到：question / feedback / progress tree 没有单一 AI flow，而是多条可进入、可回退、可再解释的流程。
  - 所有 Agent 都观察到：control authority 分散在 frontend、API command、feedback grant、runtime facade、handoff/repository。
  - 所有 Agent 都观察到：candidate / formal / fallback / partial / skeleton / validation_failed 这些状态在不同模块语义不完全等价。
  - 所有 Agent 都观察到：frontend 参与 execution target 选择，不只是被动 renderer。
  - 所有 Agent 都观察到：legacy/default-off/placeholder 不是死文档，而是仍影响运行路径。

  4. Conflict Map

  - “Domain policy 是规则来源” vs “Application service 是执行来源”：policy 输出 reason codes，但是否执行、如何写入仍由 application 决定。
  - “Graph 是 active runtime” vs “Graph default-off 且 direct path retained”：代码同时声明 graph active 和 legacy fallback 有效。
  - “Feedback next action 是建议” vs “Feedback payload 可授权下一题”：next_recommended_actions 是 display/suggestion，但同一 feedback payload 又被 runtime grant gate 读取。
  - “Candidate-only 语义” vs “Question path 最终可 formal write”：planned workflow 生成 candidate，但 AgentPersistenceHandoff.write_question_result() 仍可写 formal question。
  - “API 是适配层” vs “API 是 contract composer”：route 文件实际组装 dependency、命令、response shape、compat fields。
  - “v2 存在” vs “主执行仍 v1”：v2 metadata 与 v1 runtime/schema/prompt 并存，系统认知不稳定。

  5. Repeated Patterns

  Pattern 1: Authority 附加到共享 command

  - 出现模块：API /questions、API /feedback/{feedback_id}/next-question、CreatePolishQuestionTaskCommand、NextQuestionExecutionGrant、frontend selection。
  - 表现差异：direct path 用 selected_progress_node_ref；feedback path 用 authorized_feedback_id + grant；frontend 用当前 UI focus。
  - 本质结构一致性：都在决定同一个问题，即“是否生成下一题，生成到哪个 progress node”。
  - 根因抽象：execution authority 没有成为单一对象，而是被追加到共享 envelope。

  Pattern 2: Artifact lifecycle 重复但终态不统一

  - 出现模块：question candidate workflow、feedback planned handoff、progress tree artifact、API pending payload。
  - 表现差异：question 失败成 validation task；feedback 失败写 failed payload；progress 失败写 failed/refresh_failed state。
  - 本质结构一致性：都是生成候选 artifact -> 校验 -> metadata -> 写入或响应。
  - 根因抽象：AI artifact 生命周期没有统一状态机，各模块本地定义终态。

  Pattern 3: Policy result 同时是解释和控制信号

  - 出现模块：SourceSupportPolicy、QuestionGroundingPolicy、AssetConsistencyPolicy、feedback rules、next-question gate。
  - 表现差异：有的写 metadata，有的写 legacy dict，有的直接影响 block/allow。
  - 本质结构一致性：reason-coded decision 被跨层消费。
  - 根因抽象：解释性证据和执行选择器没有分离。

  Pattern 4: Runtime fallback 语义不等价

  - 出现模块：runtime flags、graph facade、provider boundary、fake transport gate、question direct fallback、progress failed artifact。
  - 表现差异：graph disabled 可 fallback；fake provider 是配置错误；provider missing 可变成 failed artifact。
  - 本质结构一致性：都是“能力不可用或不可可信”的非 happy path。
  - 根因抽象：安全边界、可用性边界、兼容边界共用局部 status vocabulary。

  Pattern 5: Frontend selection 与 backend target 重复派生

  - 出现模块：InterviewPage.tsx selection state、task candidate_refs、API command refs、grant validation refs。
  - 表现差异：frontend 服务 UI focus，backend 服务 execution validation。
  - 本质结构一致性：都在维护 current / selected / authorized target。
  - 根因抽象：目标身份不是单一事实，而是在多层由重叠 ID 重建。

  6. Hidden Failures

  - 新 endpoint/schema/frontend path 会继续产生 contract drift，因为 contract 事实被 Python route、Pydantic schema、TS API、React handler 多点复制。
  - Placeholder route 和 skeleton use case 会制造 false capability：API 看起来可用，但业务链路只是 skeleton。
  - Status 语义会继续扩散：partial、generated、validation_failed、refresh_failed、skeleton_succeeded 在不同模块含义不同。
  - Feedback 字段会继续越界成 orchestration signal，尤其 answer_coverage、answer_change_analysis、asset_consistency_check 这类 evaluation-shaped fields。
  - Provider 安全通过不等于 execution 安全通过；provider boundary 不持有 business grant。
  - Progress tree 会成为隐式状态汇聚点，因为它读 turns/feedback/question completion，又被 frontend 当作 action target。
  - UI fallback mapper 会掩盖 backend 语义差异，把未知状态压成 pending/failed/display fallback。
  - Tests 会固化当前分裂结构，因为大量 contract test 直接断言多入口、多 fallback、多 UI focus 行为。
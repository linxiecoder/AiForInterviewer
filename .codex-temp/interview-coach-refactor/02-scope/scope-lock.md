---
title: Round 3 范围锁定
type: temporary-scope-lock
status: scope-locked
---

# Round 3 范围锁定

## 1. 本轮边界

- 本轮阶段: Scope Lock
- 本轮性质: docs-only capability mapping，不实现功能，不创建 Goal 文件。
- 允许写入: `capability-map.md`、`scope-lock.md`、`requirements-index.md`、`functional-spec-index.md`、`CONTROL.md`。
- 禁止写入: 生产代码、`AGENTS.md`、active docs、`docs/goals/**`、`archive/**`、`/tmp/interview-coach-skill`。
- 当前 mapping 只服务 Round 4 Goal 包与技术设计创建；不自动升级为 BACKLOG、DELIVERY_PLAN、ADR 或实现事实。

## 2. 已批准进入 Round 4 设计候选的范围

以下能力只批准进入 Round 4 Goal 包与技术设计候选，不批准本轮实现。

| Capability ID | 范围 | 处理策略 | 已锁 landing point | Round 4 最小输出 |
| --- | --- | --- | --- | --- |
| `R3-CAP-002` | 长期 coaching state 连贯性 | Adapt | `InterviewSession`、`PolishSessionDetail.progress_tree_*`、`PolishUseCases._build_session_detail`、`SqlAlchemyPolishRepository.update_progress_tree` | 状态字段/兼容策略/验证计划，不复制 flat `coaching_state.md`。 |
| `R3-CAP-003` | 输入 capture 与 analysis 分离 | Adapt | `createPolishAnswer` -> `createPolishFeedbackTask`、`create_polish_answer`、`create_polish_feedback_task`、`add_answer`、`add_feedback` | 已收敛为 `G-002` Draft：`R-003` / `R-004`、`FS-003` / `FS-004`；Round 4 仍需审计 answer-save 事实与 feedback-generation 结果边界，external feedback 另行审计。 |
| `R3-CAP-005` | evidence / confidence / source availability | Adapt | `QuestionGenerationService.generate`、`build_question_provider_request`、`build_feedback_prompt_asset`、`validate_final_feedback_payload`、`PolishFeedbackPayload` | 证据字段、低置信、trace、validation、UI 可见状态和不可输出 claim 边界。 |
| `R3-CAP-006` | scoring + root-cause alignment | Adapt | `ScoringPolicy.evaluate`、`PolishFeedbackPayload.loss_points`、`ScoreResult`、`SCORING_SPEC.md` | 0-100 score、loss point evidence、root-cause candidate 语义和 non-probability guard。 |
| `R3-CAP-009` | state-aware next action | Adapt | `PolishFeedbackPayload.next_recommended_actions`、`validate_final_feedback_payload`、`POLISH_CONTRACTS.md` next action 枚举、`InterviewWorkbenchPage` view models | next action 来源、枚举、用户确认边界和 progress node/current answer 关系。 |
| `R3-CAP-010` | long-context hygiene | Adapt | `build_question_provider_request` compact canonical evidence、`build_feedback_prompt_asset` bounded answer/recent turns、`APPLICATION_FLOW_SPEC.md` `SessionSummary` | context limit、summary/dropped context、raw payload 禁止和测试计划。 |

## 3. 暂缓范围

| Capability ID | 能力 | 暂缓原因 | 重新进入条件 |
| --- | --- | --- | --- |
| `R3-CAP-004` | transcript ingestion pipeline | 当前代码未发现 transcript 一级对象、normalization pipeline、quality gate、upload/API/UI/tests。 | 单独授权 transcript discovery；完成 data/API/privacy/threat-model landing audit。 |
| `R3-CAP-007` | storybank as reusable memory | 当前没有 `Storybank` / `Story` 模型、repository、API 或 UI；Asset/Weakness 只是相邻概念。 | 单独审计 Asset/Weakness/Training 与 story memory 的关系，并确认 active docs 需要该对象。 |
| `R3-CAP-008` | progress calibration / outcome drift | 当前没有 outcome log、external feedback store、self-assessment delta、real outcome correlation 或 drift lifecycle。 | 先定义 outcome input、score history query、privacy boundary 和 drift tests。 |

## 4. Research-only 范围

| Capability ID | 能力 | Research-only 边界 |
| --- | --- | --- |
| `R3-CAP-001` | source-backed command routing pattern | 只保留“入口轻、细节下沉到 contract/service”的结构启发；不得复制 command list、command names、directory layout 或 workflow wording。 |

## 5. Reject 范围

- 直接复制 interview-coach command names、menus、workflow wording、output wording。
- 直接复制 flat `coaching_state.md`。
- 直接复制 interview-coach scoring dimensions、1-5 anchors、seniority bands、hire-signal wording。
- 直接复制 company/interviewer claim examples、prompt prose 或 coaching voice。
- 在没有 AIForInterviewer landing point 时，把 transcript、storybank、outcome calibration 写成 Adopt / Adapt。

## 6. 风险说明

- Polish-specific coupling: 当前可工作主线集中在 `polish` route、application service、frontend workbench；Round 4 不应假设通用 `application/interviews` skeleton 已可承接。
- Design-code drift: active design docs 登记了 Pressure、Report、Review、Training 等更大范围；本轮只按当前代码和已读 docs 双证据确认，不把 design-only 写成 implemented。
- Evidence inflation: `trace_refs`、`low_confidence_flags`、`next_recommended_actions` 已存在，但不等于完整 company research、transcript analysis、outcome calibration 或 storybank。
- Prompt copying risk: interview-coach source 是 MIT，但本轮不复制 prompt/prose/output schema；后续如需使用结构性思想，必须用 AIForInterviewer 自己的 contract/schema 重写。
- Goal inflation: 本轮不创建 Goal 文件；Round 4 才能在 scope-lock 基础上创建 Goal 包与技术设计。

## 7. Round 4 建议

下一轮建议执行: Round 4: Goal 包与技术设计创建。

Round 4 最小建议顺序:

1. 创建一个受控 Goal 包，覆盖 `R3-CAP-002`、`R3-CAP-003`、`R3-CAP-005`、`R3-CAP-006`、`R3-CAP-009`、`R3-CAP-010` 的 design-only 输出。
2. 明确不纳入 `R3-CAP-004`、`R3-CAP-007`、`R3-CAP-008`，除非用户另行授权。
3. 在设计中逐条列出 API、application service、repository/model、frontend type/UI、tests 和 docs 回写计划。
4. 继续禁止生产代码实现，直到 Goal/design 被确认。

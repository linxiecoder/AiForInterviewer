---
title: G-002：Capture / Analysis Separation
type: temporary-goal-draft
status: draft
---

# G-002：Capture / Analysis Separation

## 1. Status

Draft。

本文件是 Round 3.5-B 的需求/功能规格收敛包，只处理 `R3-CAP-003`。它不是完整技术设计，不表示可以实现、已实现、已验证或已批准进入 Round 4。

## 2. 覆盖范围

| 项 | 覆盖关系 |
| --- | --- |
| `R3-CAP-003` | capture-versus-analysis separation pattern |
| `R-003` | 回答 capture 必须先于 feedback analysis 独立完成 |
| `R-004` | analysis 结果必须附着到已 capture 输入，并保留失败/降级边界 |
| `FS-003` | 回答 capture 边界功能规格 |
| `FS-004` | feedback analysis 边界功能规格 |

## 3. Source Inspiration

真实 interview-coach evidence：

- G-002 的主要 source inspiration 是 `/tmp/interview-coach-skill/references/commands/feedback.md`，尤其是 `# feedback — Capture Feedback, Outcomes, and Corrections`、`### Input Type Detection`、`### Type A: Recruiter/Interviewer Feedback`、`### Type C: Coaching Correction`、`### Design Principles`。
- `/tmp/interview-coach-skill/references/commands/progress.md` 仅作为“后续 analysis 消费 capture 信号”的背景来源，提供 data-threshold、trend review 和 drift review 背景，不进入 G-002 当前范围。
- `/tmp/interview-coach-skill/references/calibration-engine.md` 仅作为“后续 analysis 消费 capture 信号”的背景来源，提供 feedback contradiction / drift signal 背景，不进入 G-002 当前范围。

来源模式说明：

- source 把 between-session 输入先作为 facts capture，不在 capture 时直接做完整 analysis。
- source 把更重的 analysis 留给后续 workflow 消费 capture data。
- source 将 feedback contradiction、correction 和 outcome 类信息作为后续分析信号，而不是在 capture 步骤直接变成最终评分或长期策略。
- G-002 不新增其他 interview-coach source，不扩大到 progress、calibration 或 outcome tracking。

不复制内容说明：

- G-002 只吸收“先保存输入事实，再由分析流程消费”的能力模式。
- 不复制 interview-coach command、menu、长文案、目录结构、output schema、coaching voice 或 prompt prose。
- 不复制 outcome calibration、progress calibration、outcome tracking、transcript ingestion、storybank、company / interviewer examples 或 source scoring vocabulary。
- source-backed command routing 不进入 G-002 当前范围。
- 不把 source 的 external feedback taxonomy 直接实现为 AIForInterviewer 产品对象；本轮仅使用其 separation pattern 解释现有 answer / feedback 边界。

## 4. AIForInterviewer Landing Point

| 范围 | 真实落点 | 当前行为 | 当前缺口 | 为什么存在真实落点 |
| --- | --- | --- | --- | --- |
| 前端提交顺序 | `apps/web/src/pages/interview/InterviewPage.tsx::InterviewWorkbenchPage` 内部 `sendAnswer`；`apps/web/src/entities/polish/api/polishApi.ts::createPolishAnswer`；`apps/web/src/entities/polish/api/polishApi.ts::createPolishFeedbackTask` | `sendAnswer` 先调用 `createPolishAnswer` 保存回答，再调用 `createPolishFeedbackTask` 生成反馈；反馈失败时设置 `feedbackFailedAnswerSaved`，提示“回答已保存”。 | separation 是已有行为，但未形成 G-002 级需求、FS、回归验收和失败/降级定义。 | 用户可见 workflow 已明确区分 answer capture 与 feedback generation。 |
| API 边界 | `apps/api/app/api/v1/polish.py::create_polish_answer`；`apps/api/app/api/v1/polish.py::create_polish_feedback_task`；`apps/api/app/schemas/polish.py::CreateAnswerRequest`；`apps/api/app/schemas/polish.py::CreateFeedbackTaskRequest` | answer route 接收 `question_id` / `answer_text` 并返回 `polish_answer`；feedback route 接收 `answer_id` / optional scoring context 并返回 `ai_task` / feedback response。 | 需要明确反馈生成失败、validation failed、重复生成、answer 不存在等情况不能破坏 capture 结果。 | 两个 route 与两个 request schema 已天然分离 capture input 和 analysis request。 |
| Application 边界 | `apps/api/app/application/polish/use_cases.py::PolishUseCases.create_answer`；`apps/api/app/application/polish/feedback_application_service.py::PolishFeedbackApplicationService.create_feedback_task`；`apps/api/app/application/polish/answer_application_service.py::AnswerSubmissionBoundaryBuilder` | `create_answer` 校验 session/question、处理 idempotency、计算 answer round 并调用 `add_answer`；`create_feedback_task` 读取已保存 answer / question / session detail 后构造 feedback generation context。 | 需要把“analysis 只能消费已保存 answer”的约束写成 Draft FS，避免后续绕过 answer capture 直接生成 feedback。 | Application 层已有独立 answer submission boundary 与 feedback generation service。 |
| Persistence 边界 | `apps/api/app/infrastructure/db/repositories/polish.py::add_answer`；`apps/api/app/infrastructure/db/repositories/polish.py::add_feedback`；`apps/api/app/application/polish/ports.py::add_answer`；`apps/api/app/application/polish/ports.py::add_feedback` | answer 与 feedback 分别持久化；feedback generation 失败时可写 failed feedback / task，而不撤销 answer。 | 需要明确 failed analysis 的持久化/展示语义，不得伪装为 generated feedback 或正式 score。 | repository port 和 SQLAlchemy repository 已把 answer 与 feedback 写入操作拆开。 |
| 现有测试落点 | `tests/api/test_polish_application_service_split.py`；`tests/api/test_polish_feedback_generation_service.py`；`tests/api/test_polish_api.py` | 已存在 application split、feedback service、API 兼容相关测试文件；本轮未运行。 | G-002 未来需要补充或调整针对 capture-first、analysis-failure、idempotency 和 retry 的 focused tests。 | 测试树已有可承接 split / feedback generation 行为的文件边界。 |

## 5. Requirement：R-003 回答 Capture 优先

### 用户可见行为

用户在工作台提交回答时，系统应先保存回答事实。即使后续反馈生成失败、LLM 输出无效、provider 不可用或进度刷新失败，用户仍应能看到已保存回答，并获得可理解的“回答已保存但分析未完成/失败”的状态。

### 验收标准

- 提交非空回答后，answer capture 成功应返回可展示的 `answer_id`、回答内容摘要和轮次信息。
- feedback generation 失败时，不得删除、覆盖或隐藏已保存 answer。
- 失败状态必须与 feedback generated 状态可区分，不能把 analysis failure 包装为普通成功。
- answer idempotency 冲突必须阻断重复/矛盾 capture，不得生成基于错误 answer 的 feedback。
- session 不存在、owner 不匹配、session ended/deleted、question 不属于 session 或 answer 为空时，不得写入 answer。

### 与 G-002 的关联

`R-003` 是 G-002 的 capture-side requirement，负责定义“输入事实保存”在用户体验、API 和 persistence 上必须独立成立。

### 与 source evidence / landing point 的关联

- Source evidence：`/tmp/interview-coach-skill/references/commands/feedback.md` 的 capture-first design principle。
- AIForInterviewer landing point：`sendAnswer`、`createPolishAnswer`、`create_polish_answer`、`PolishUseCases.create_answer`、`AnswerSubmissionBoundaryBuilder`、`SqlAlchemyPolishRepository.add_answer`。

## 6. Requirement：R-004 Analysis 附着与失败边界

### 用户可见行为

系统生成反馈、评分、下一步建议或相关分析时，必须基于已保存 answer 运行。analysis 成功、失败、validation failed、retryable 或已有 generated feedback 复用必须对用户可见且可区分；失败或低置信 analysis 不得覆盖 capture 事实，也不得自动写成正式反馈、正式评分或确定性下一步。

### 验收标准

- feedback analysis request 必须引用已存在且属于当前 session / owner 的 `answer_id`。
- analysis 成功时，feedback/task 应附着到对应 answer，并可追踪 session、question、answer、feedback/task refs。
- analysis 失败或 validation failed 时，应产生可重试或可查看的失败/降级状态；不得伪造成 `generated` feedback。
- 已存在 generated feedback 且 payload 有效时，可复用已有结果，但必须保持与原 answer 的关联。
- analysis 失败不得触发 Weakness、Asset、Training、Report、progress calibration、outcome calibration 或其他正式对象写入。

### 与 G-002 的关联

`R-004` 是 G-002 的 analysis-side requirement，负责定义“分析结果如何消费已 capture 输入，以及失败时如何保持边界”。

### 与 source evidence / landing point 的关联

- Source evidence：`/tmp/interview-coach-skill/references/commands/feedback.md` 的 capture now / analyze later 模式；`/tmp/interview-coach-skill/references/commands/progress.md` 和 `calibration-engine.md` 仅作为“后续 analysis 消费信号”的来源模式，不进入本轮实现范围。
- AIForInterviewer landing point：`createPolishFeedbackTask`、`create_polish_feedback_task`、`PolishFeedbackApplicationService.create_feedback_task`、`FeedbackGenerationService.generate`、`SqlAlchemyPolishRepository.add_feedback`、`get_latest_feedback_for_answer`。

## 7. Functional Spec：FS-003 回答 Capture 边界

### Inputs

- authenticated actor / owner scope。
- `session_id`。
- `question_id`。
- `answer_text`。
- optional `base_question_version_ref`。
- optional `Idempotency-Key`。
- 当前 `InterviewSession` / `PolishSessionDetail` / `Question` 状态。

### Outputs

- `PolishAnswer` / API `polish_answer` response。
- `answer_id`、`question_id`、`session_id`、`answer_round`、`created_at`。
- 用户可见 capture success 状态。
- 若后续 analysis 失败，用户可见“回答已保存，反馈生成失败/可重试”的等价状态。

### State Changes

- 成功 capture 写入 Answer record。
- answer round 基于同 question 已有 answers 计算。
- idempotent retry 在 payload 一致时返回已有 answer；payload 不一致时返回 validation error。
- capture 成功不得依赖 feedback generation 成功。

### Error / Fallback Behavior

- session not found、owner mismatch、session not running、question not found、empty answer 或 idempotency conflict：不写 answer。
- feedback generation 失败不是 capture rollback 条件。
- progress refresh failure 不是 answer rollback 条件。
- provider unavailable / LLM validation failed 不应影响已保存 answer。

### Compatibility Expectations

- 保持现有 `POST /polish-sessions/{session_id}/answers` 行为和 frontend `createPolishAnswer` contract。
- 不改变 existing answer records、turn rendering、answer round 或 idempotency semantics。
- 不新增 transcript ingestion、external feedback object、storybank、outcome calibration 或 source command routing。

## 8. Functional Spec：FS-004 Feedback Analysis 边界

### Inputs

- authenticated actor / owner scope。
- `session_id`。
- captured `answer_id`。
- optional internal scoring context。
- existing `InterviewSession`、`Question`、`Answer`、session detail turns。
- feedback generation context 与 validation result。

### Outputs

- `PolishTaskStatus` / API `ai_task` response。
- 成功时的 generated feedback payload、`feedback_id`、task refs、candidate refs。
- 失败时的 generation failed task、validation errors、retryable status 和用户可见失败状态。
- 与 answer 绑定的 feedback / task / trace refs。

### State Changes

- analysis 成功时写入 generated `PolishFeedback` 和 succeeded task。
- analysis 失败时可写入 failed feedback payload 与 generation failed task，但不得改变 answer capture 事实。
- 已存在 generated feedback 可复用为 existing generated task，不重复生成。
- analysis 不得自动写入 Weakness、Asset、Training、Report、outcome calibration 或 source-like coaching state。

### Error / Fallback Behavior

- answer 不存在、answer 不属于 session、question 不存在或 session 不存在：不生成 feedback。
- LLM/provider/output validation failure：进入 failed / retryable / validation-result 路径，不伪装成功。
- duplicate request 命中已有 generated feedback 时，应返回已存在结果，而不是创建冲突 feedback。
- fallback 或 failed payload 必须保留可追踪错误原因，不扩大输入范围补救。

### Compatibility Expectations

- 保持现有 `POST /polish-sessions/{session_id}/feedback` 行为和 frontend `createPolishFeedbackTask` contract。
- 保持 feedback payload validation、candidate refs、trace refs、low confidence / validation failure 语义。
- 与 G-001 的 session continuity / context hygiene 兼容：已保存 turns 可继续展示，analysis context 仍受 bounded input 约束。

## 9. Technical Design（Draft / Candidate）

本节只是 Round 4 技术设计审计的候选输入，不是完整设计，不是已批准实现路径，也不表示本轮进入 Round 4。

### Candidate Modified Files

- `apps/web/src/pages/interview/InterviewPage.tsx`
- `apps/web/src/entities/polish/api/polishApi.ts`
- `apps/web/src/entities/polish/model/types.ts`
- `apps/api/app/api/v1/polish.py`
- `apps/api/app/schemas/polish.py`
- `apps/api/app/application/polish/use_cases.py`
- `apps/api/app/application/polish/answer_application_service.py`
- `apps/api/app/application/polish/feedback_application_service.py`
- `apps/api/app/application/polish/feedback_generation_service.py`
- `apps/api/app/application/polish/feedback_validation.py`
- `apps/api/app/infrastructure/db/repositories/polish.py`
- `tests/api/test_polish_application_service_split.py`
- `tests/api/test_polish_feedback_generation_service.py`
- `tests/api/test_polish_api.py`
- 可能的 frontend contract / smoke tests，具体文件待 Round 4 审计确认。

### Candidate Module Boundary

- Answer capture 候选边界：前端 `createPolishAnswer` / API `create_polish_answer` / application `create_answer` / repository `add_answer`。
- Feedback analysis 候选边界：前端 `createPolishFeedbackTask` / API `create_polish_feedback_task` / application `create_feedback_task` / feedback generation and validation services / repository `add_feedback`。
- Frontend display 候选边界：`InterviewWorkbenchPage` 中 answer saved、feedback generated、feedback failed 的既有展示与后续可见状态。
- Tests 候选边界仅作为未来 validation plan 输入；本轮不新增、不修改、不运行测试。

### Candidate Data / API / Service Questions

- 是否需要新增显式 `analysis_status` / `capture_status` response metadata，还是继续复用现有 answer / feedback / task 字段。
- 失败 feedback payload 是否应继续持久化为 `PolishFeedback`，以及前端如何展示 failed payload 与 retry 入口。
- retry 行为是否需要稳定 idempotency key 或 answer-level feedback generation key。
- 是否需要把 analysis failure 与 progress tree refresh failure 拆成不同 UI 状态。
- 是否需要为 existing generated feedback reuse 增加更明确的 API / frontend 表达。

### Round 4 待确认项

- Round 4 是否只需要 tests/docs guard，还是需要最小 API/frontend metadata 调整。
- Round 4 是否接受上述 candidate modified files，需以当轮只读审计结果为准。
- Round 4 是否需要补充 active docs 迁移计划，必须等实现和验证后再决定。
- 是否需要将 G-002 结论迁入 active API / application flow / frontend contract docs，必须等实现和验证后再决定。

## 10. Implementation Plan（Draft Checklist）

以下只是未来 Draft checklist，不表示已执行、已实现、已验证、已批准或本轮将实现：

- [ ] 未来 Round 4 审计现有 answer / feedback route、application service、repository、frontend state 和 tests。
- [ ] 未来 Round 4 确认 `R-003` / `FS-003` 是否只需要 tests/docs guard，还是需要最小 API/frontend metadata 调整。
- [ ] 未来 Round 4 确认 `R-004` / `FS-004` 对 failed feedback payload、retry、existing generated reuse 的最小设计。
- [ ] 未来设计 focused backend tests：capture success、idempotency conflict、analysis answer-not-found、analysis validation failure、existing generated reuse。
- [ ] 未来设计 focused frontend tests：answer saved / feedback failed 可见、retry 入口、generated 状态和 failed 状态可区分。
- [ ] 未来审查是否需要 active doc 迁移；未实现和未验证前不回写 active docs。

## 11. Acceptance Criteria

以下验收标准仅用于未来 Round 4/后续实现与验证，不表示本轮已验证。

- AC-001：回答提交成功但 feedback generation 抛错时，用户可见 answer saved 状态，且已保存 answer 仍存在于 session turns。
- AC-002：feedback analysis request 只能接受当前 owner/session 下已存在的 `answer_id`；不存在或跨 session 的 answer 必须失败且不写 feedback。
- AC-003：analysis failed / validation failed 与 generated feedback 在 API payload、task status 或 frontend state 上可区分。
- AC-004：analysis failed 不得撤销 answer、不得生成正式 score、不得创建正式 next action，也不得写 Weakness / Asset / Training / Report / outcome calibration。
- AC-005：重复 feedback request 命中已有 generated feedback 时，应保持同一 answer 关联，不产生冲突或重复正式反馈。
- AC-006：empty answer、ended session、owner mismatch、idempotency conflict 均不得写入 answer，也不得触发 analysis。
- AC-007：G-002 不引入 transcript ingestion、storybank、outcome calibration、source command routing、flat `coaching_state.md`、source scoring vocabulary 或 company/interviewer examples。

## 12. Validation Plan（Future Only）

本轮不运行测试、不创建 `test-results.md`。

未来可验证项：

- 后端 focused tests：`tests/api/test_polish_application_service_split.py` 覆盖 answer capture 与 feedback analysis 分离。
- 后端 feedback tests：`tests/api/test_polish_feedback_generation_service.py` 覆盖 generation failed、validation errors、existing generated reuse。
- API tests：`tests/api/test_polish_api.py` 覆盖 answer route 与 feedback route 的响应边界。
- Frontend tests：覆盖 `sendAnswer` 中 answer saved / feedback failed / retry 或状态展示路径。
- Contract scan：确认 `CreateAnswerRequest` 与 `CreateFeedbackTaskRequest` 不被合并，feedback request 不接受 raw answer text 直接绕过 capture。
- Regression scan：确认未新增 transcript/storybank/outcome calibration/source command objects。

## 13. Risks

- scope creep 风险：capture / analysis separation 容易扩展到 external feedback、outcome tracking、progress calibration、storybank 或 transcript ingestion；G-002 只覆盖现有 answer / feedback 边界。
- LLM output / parser 风险：feedback analysis 可能因 provider failure、JSON parse failure、schema validation failure 或 low-confidence payload 失败；这些失败必须保留为 analysis failure，不能污染 capture。
- 现有 flow 兼容风险：调整状态词、API payload 或 frontend state 可能破坏现有 `polish` answer / feedback / progress refresh flow。
- 用户体验风险：用户可能误以为“回答已保存”也意味着“反馈已生成”；需要在 UI 状态中清楚区分 capture success 与 analysis success/failure。

## 14. Migration Notes for Active Doc

若未来实现并通过验证，G-002 的长期结论可考虑迁入 active API / application flow / frontend contract 文档，重点说明 answer capture 与 feedback analysis 的边界、失败状态、retry 语义和非目标。未实现、未验证或未完成 Round 4 审计前，不应迁入 active docs 或 BACKLOG。

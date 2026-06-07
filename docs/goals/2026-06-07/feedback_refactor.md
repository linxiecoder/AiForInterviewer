---
title: '1'
type: note
permalink: ai-for-interviewer/docs/goals/2026-06-07/1-2
---

<!-- PROMPT_START -->

# AiForInterviewer Feedback 链路收缩式重构 Goal

## 0. Goal 模式触发说明

本文件用于 Codex / Claude Code / 其它代码执行 Agent 的 goal 模式。

推荐保存路径：

- `/tmp/goal-feedback/GOAL.md`
- 或 `docs/goals/2026-06-07/FEEDBACK_CONTRACT_PRUNE_GOAL.md`

执行方式：

1. 第一轮只执行 Recon，不修改代码。
2. Recon 输出确认后，再按 A→I 批次 Patch。
3. 每个批次必须通过 gate 后才能进入下一批。
4. 最终状态必须是收缩式重构完成，而不是在旧系统上继续加兼容层。

如果执行器不支持真正的 goal 模式，也可以把本文件作为单次任务提示词执行，但仍必须遵守“先 Recon、后 Patch”的 gate。

---

## 1. 项目背景

项目：`AiForInterviewer`

仓库目标：AI 模拟面试工作台级 MVP。

当前需要重构的是模拟面试 feedback 功能。问题不是单个 prompt，而是 feedback 链路中多套历史契约和兼容代码并存，导致维护困难、验证脆弱、功能边界不清。

当前已确认事实：

1. feedback agent 当前 max_tokens 是 1600。
2. Phase4 字段当前已经由 `apply_feedback_core_rules()` 规则层生成或覆盖。
3. Transport 层已有基础 LLM request start / success / failed 日志。
4. validator 已兼容 `deduction` 与 `deducted_points`。
5. generated feedback 顶层字段当前约 26 个。
6. HTTP trace 基建已存在，request_id / trace_id 由 middleware 注入。
7. 测试已经证明 Phase4 规则层对部分脆弱点有缓解。
8. reserved feedback、legacy compatibility、old generated schema、quick prompt、final payload 作为 LLM 输出契约等历史设计仍在代码和测试中残留。

---

## 2. 核心目标

本任务不是给现有系统继续做加法，而是做收缩式重构。

最终目标：

1. 删除 reserved feedback。
2. 删除 legacy compatibility。
3. 删除重复字段。
4. 删除旧 validator 兼容接口。
5. 删除无业务价值的旧测试。
6. LLM 只输出语义 candidate。
7. Phase4 字段只由服务端 deterministic rules 生成。
8. score_result 只由服务端 scoring policy 生成。
9. final feedback payload 只有一套 shape。
10. `PolishUseCases` 不再承载完整 feedback 主流程。
11. 前端类型与 API payload 同步收敛。
12. Alembic migration 处理历史 reserved 数据。
13. 只保留最小必要日志。
14. 最终净删除代码量明显大于新增代码量。

---

## 3. 强制原则

1. 以删减为优先。
2. 默认不保留内部兼容。
3. 可以同步修改前端和测试。
4. 不为了旧测试通过而保留旧代码。
5. 不为了“未来可能用”保留字段、函数、常量或文件。
6. 不新增 wrapper / adapter 来包住旧实现。
7. 不新增复杂 ValidationReport 系统。
8. 不新增新的 debug dump 格式。
9. 不引入新依赖。
10. 不扩散修改 question / progress tree 主链路。
11. 不在生产代码中引入新的多 Agent Runtime。
12. 多 Agent 只作为执行分工，不是项目运行时架构。
13. 如果发现旧逻辑无真实调用，应删除而不是包一层继续保留。
14. 如果两个字段表达同一概念，只保留一个。
15. 如果两个函数只是为了支持旧 shape，删除旧 shape 后删除函数。

---

## 4. 禁止事项

禁止：

1. 不要引入 structlog 或其它日志依赖。
2. 不要新增 LangGraph / planner / workflow runtime。
3. 不要新增兼容 adapter。
4. 不要保留 reserved fallback。
5. 不要保留 `legacy_compatibility`。
6. 不要把旧 validator deprecated 接口作为最终状态保留。
7. 不要让 LLM 输出最终 Phase4 字段。
8. 不要让 LLM 输出可信 `score_result`。
9. 不要让 LLM 输出可信 deduction。
10. 不要把 raw prompt、raw completion、provider payload 写入 DB 或 API 响应。
11. 不要为了旧测试通过而保留旧契约。
12. 不要在同一批次中同时大改后端、前端、migration 和测试而没有 gate。
13. 不要让多个 Agent 同时修改同一文件。
14. 不要保留新旧两套互调实现。
15. 不要把“多 Agent 协作记录”写入业务代码。

---

## 5. 必须先执行 Recon

第一阶段只分析，不修改代码。

执行前必须运行：

- `git status --short`
- 确认当前 worktree 是否有非本任务改动
- 如果存在非本任务改动，不得覆盖，必须先报告

Recon 必须扫描以下路径：

- `apps/api/app/api/v1/polish.py`
- `apps/api/app/schemas/polish.py`
- `apps/api/app/application/polish/use_cases.py`
- `apps/api/app/application/polish/feedback_application_service.py`
- `apps/api/app/application/polish/feedback_generation_service.py`
- `apps/api/app/application/polish/feedback_agent.py`
- `apps/api/app/application/polish/feedback_prompt_assets.py`
- `apps/api/app/application/polish/feedback_validation.py`
- `apps/api/app/application/polish/feedback_rules.py`
- `apps/api/app/application/polish/feedback_schema.py`
- `apps/api/app/application/polish/feedback_reserved.py`
- `apps/api/app/domain/polish/policies/`
- `apps/api/migrations/versions/`
- `apps/api/app/infrastructure/db/repositories/polish.py`
- `apps/web/src/entities/polish/model/types.ts`
- `apps/web/src/pages/interview/**`
- `tests/api/test_polish_feedback_generation_service.py`
- `tests/api/test_polish_feedback_generation_schema.py`
- `tests/api/test_polish_feedback_agent_io_alignment.py`
- `tests/api/test_polish_feedback_runtime.py`
- `tests/api/test_polish_api.py`

Recon 必须搜索：

- `reserved`
- `RESERVED_FEEDBACK`
- `RESERVED_FEEDBACK_TEXT`
- `LEGACY_PENDING_FEEDBACK_TEXT`
- `legacy_compatibility`
- `validate_generated_feedback_payload`
- `project_asset_consistency_check`
- `explicit_score`
- `implicit_score`
- `score_loss_deduction_mismatch`
- `POLISH_FEEDBACK_QUICK`
- `feedback_payload`
- `feedback_summary`
- `contract_id`
- `should_continue_same_question`
- `should_generate_next_question`

Recon 输出必须包含：

1. reserved 引用清单。
2. legacy 引用清单。
3. validator 调用方清单。
4. prompt 旧字段清单。
5. frontend feedback 字段消费清单。
6. 数据库 feedback 表实际表名、status 字段、feedback_summary 存储方式。
7. 是否存在历史 `status = "reserved"` 数据迁移需求。
8. 可以删除的文件。
9. 可以删除的函数。
10. 可以删除的字段。
11. 可以删除或重写的测试。
12. 新 candidate schema。
13. 新 final feedback payload schema。
14. 分批 patch 拓扑顺序。
15. 预计净删除行数。
16. 风险点。
17. 每批次建议验证命令。

Recon 阶段禁止修改任何文件。

---

## 6. 多 Agent 执行协议

本任务允许使用多 Agent / 多工作流协作，但只用于分析、拆分执行和交叉审查。

### Agent A：Recon / 删除清单 Agent

职责：

1. 扫描 reserved / legacy / validator / prompt / frontend / tests / DB migration 引用。
2. 输出删除清单。
3. 输出新 candidate schema。
4. 输出新 final payload schema。
5. 输出改动拓扑顺序。
6. 标记高风险文件。

禁止修改代码。

输出：

- reserved 引用清单
- legacy 引用清单
- validator 调用方清单
- frontend 消费字段清单
- 数据库表名和迁移方案
- 删除文件 / 函数 / 字段 / 测试清单
- 分批 patch 计划

### Agent B：Contract Pruner Agent

职责：

1. 删除 reserved feedback。
2. 删除 legacy compatibility。
3. 收敛 `feedback_schema.py`。
4. 收敛 API DTO feedback payload 类型。
5. 同步删除无用常量。

允许修改：

- `feedback_schema.py`
- `feedback_reserved.py`
- `polish.py`
- `schemas/polish.py`
- 相关测试

完成标准：

- 不再存在 runtime reserved feedback 分支。
- API 不再返回 `legacy_compatibility`。
- final feedback payload 字段唯一。

### Agent C：Prompt / Candidate Agent

职责：

1. 将 LLM 输出契约改为 candidate。
2. 删除 Phase4 required fields。
3. 删除 LLM score_result / deduction 要求。
4. 更新 prompt tests。

允许修改：

- `feedback_prompt_assets.py`
- `feedback_agent.py`
- prompt/schema 相关测试

完成标准：

- provider prompt 只要求 candidate JSON。
- candidate 不包含 Phase4、next actions、final score。

### Agent D：Rules / Scoring Agent

职责：

1. 新增 `ScoringPolicy`。
2. 服务端生成 `loss_points[].deduction`。
3. 服务端生成 `score_result`。
4. 保持 Phase4 由 deterministic rules 生成。

允许修改：

- `apps/api/app/domain/polish/policies/scoring_policy.py`
- `feedback_rules.py`
- 相关测试

完成标准：

- LLM 不再提供可信 score。
- final payload 的 score 由服务端计算。
- 删除 `score_loss_deduction_mismatch` 作为 provider validation failed 条件。

### Agent E：Validator / Service Flow Agent

职责：

1. 新增 candidate validator。
2. 新增 final validator。
3. 重写 `FeedbackGenerationService.generate()` 主流程。
4. 迁移生产调用方。
5. 删除旧 `validate_generated_feedback_payload(...)`。

允许中间步骤短暂保留旧接口，但最终提交状态必须删除。

允许修改：

- `feedback_validation.py`
- `feedback_generation_service.py`
- `feedback_agent.py`
- feedback generation tests

完成标准：

- 生产代码不再调用旧 validator。
- LLM candidate validator 与 final payload validator 分离。
- final payload 由服务端组装并验证。

### Agent F：Application / Transaction Agent

职责：

1. 将 feedback 主流程从 `PolishUseCases` 迁移到 `PolishFeedbackApplicationService`。
2. 保持现有锁语义。
3. 保持 repository / transaction 模式不扩散。
4. 删除重复主流程。

允许修改：

- `use_cases.py`
- `feedback_application_service.py`
- repository 相关最小代码
- 并发 / runtime tests

完成标准：

- `PolishUseCases.create_feedback_task()` 只委托。
- 不存在 use_cases 和 feedback_application_service 两套互调实现。
- 并发重复生成测试通过。

### Agent G：Frontend / API Sync Agent

职责：

1. 同步前端 feedback payload 类型。
2. 删除前端对 legacy / reserved 字段依赖。
3. 确保页面读取新 final payload。
4. 更新页面测试。

允许修改：

- `apps/web/src/entities/polish/model/types.ts`
- `apps/web/src/pages/interview/**`
- 前端相关测试

完成标准：

- 前端不读取 `legacy_compatibility`。
- 前端不依赖 `reserved`。
- 页面反馈展示仍正常。

### Agent H：Migration Agent

职责：

1. 确认实际 feedback 表名。
2. 新增 Alembic 迁移处理历史 reserved 数据。
3. 迁移 feedback_summary JSON 中的 reserved payload。
4. 保证 migration 幂等。

允许修改：

- `apps/api/migrations/versions/**`
- migration tests

完成标准：

- 历史 `reserved` 数据迁移为 `pending` 或 `failed`。
- generated / failed 数据不被破坏。
- 迁移不猜测表名，必须基于现有 migration / model / repository 确认。

### Agent I：Test Cleanup / Final Review Agent

职责：

1. 删除只保护旧契约的测试。
2. 补齐新 candidate / final payload / scoring / logs 测试。
3. 跑后端和前端最小验证。
4. 检查净删除情况。
5. 检查是否残留旧接口、旧字段、旧文件。

必须执行搜索：

- `reserved`
- `legacy_compatibility`
- `validate_generated_feedback_payload`
- `project_asset_consistency_check`
- `explicit_score`
- `implicit_score`
- `score_loss_deduction_mismatch`
- `POLISH_FEEDBACK_QUICK`
- `RESERVED_FEEDBACK`

完成标准：

- 不存在 runtime reserved feedback。
- 不存在 legacy compatibility。
- 不存在旧 validator 生产调用。
- 不存在 LLM 输出 Phase4 的 prompt 要求。
- 删除代码量明显大于新增代码量。

---

## 7. 执行顺序

必须串行通过 gate，不允许并行乱改。

推荐顺序：

1. Agent A：Recon，只分析，不改代码。
2. Agent B：Contract Pruner。
3. Agent C：Prompt / Candidate。
4. Agent D：Rules / Scoring。
5. Agent E：Validator / Service Flow。
6. Agent F：Application / Transaction。
7. Agent H：Migration。
8. Agent G：Frontend / API Sync。
9. Agent I：Test Cleanup / Final Review。

如果某个 Agent 发现上游方案错误，必须停止并返回修正建议，不要继续叠加补丁。

---

## 8. Gate 输出规则

每个 Agent 完成后必须输出：

1. 本 Agent 删除了什么。
2. 本 Agent 新增了什么。
3. 是否引入兼容层。
4. 是否修改了禁止修改的范围。
5. 运行了什么测试。
6. 剩余风险。
7. 下一 Agent 的输入摘要。
8. `git diff --stat`。
9. `git status --short`。

如果验证失败：

1. 不得继续下一 Agent。
2. 必须说明失败测试、失败原因、相关文件。
3. 必须给出最小修复方案。
4. 不得通过降低测试标准来绕过失败。

---

## 9. 文件锁规则

为了避免多 Agent 冲突：

- Agent B 独占：`feedback_schema.py`、`feedback_reserved.py`、`schemas/polish.py`
- Agent C 独占：`feedback_prompt_assets.py`、`feedback_agent.py`
- Agent D 独占：`feedback_rules.py`、`domain/polish/policies/scoring_policy.py`
- Agent E 独占：`feedback_validation.py`、`feedback_generation_service.py`
- Agent F 独占：`use_cases.py`、`feedback_application_service.py`
- Agent G 独占：`apps/web/**`
- Agent H 独占：`apps/api/migrations/**`
- Agent I 只做测试和清理，修改前必须重新检查 `git status --short`

如果必须跨 Agent 修改同一文件，后一个 Agent 必须先重新读取当前文件，不得基于旧上下文 patch。

---

## 10. 删除目标一：删除 reserved feedback

删除或废弃：

- `feedback_reserved.py`
- `RESERVED_FEEDBACK_SCHEMA_ID`
- `RESERVED_FEEDBACK_SCHEMA_VERSION`
- `RESERVED_FEEDBACK_TEXT`
- `ReservedFeedbackArtifacts`
- `build_reserved_feedback_artifacts`
- `build_reserved_feedback_payload`
- API 层 reserved fallback
- reserved metadata
- reserved response shape
- 测试中只保护 reserved shape 的用例

统一状态：

- 未生成：`pending`
- 生成成功：`generated`
- 生成失败：`failed`

数据库迁移要求：

1. Recon 阶段先确认实际表名，禁止猜测表名。
2. 如果存在历史 `status = "reserved"` 记录，新增 Alembic 迁移将其更新为 `pending` 或 `failed`。
3. 迁移必须同时处理 feedback_summary JSON 中的 reserved payload，避免前端继续读出 reserved 状态。
4. 迁移应幂等，不影响 generated / failed 记录。

---

## 11. 删除目标二：删除 legacy compatibility

删除：

- `legacy_compatibility`
- 单数 `contract_id`
- reserved-specific metadata
- placeholder / reserved 文案分支
- `should_continue_same_question`
- `should_generate_next_question`
- `score_result_ref`
- `validation_result_ref`
- `candidate_refs`，除非 Recon 证明前端或业务明确仍消费
- 失败 payload 里的 `generate_next_question`

如果前端依赖旧字段，同步改前端，不保留后端兼容字段。

---

## 12. 删除目标三：收敛 final feedback schema

最终 feedback payload 只保留以下字段：

- `schema_id`
- `schema_version`
- `status`
- `contract_ids`
- `feedback_id`
- `feedback_text`
- `answer_summary`
- `score_result`
- `loss_points`
- `reference_answer`
- `asset_consistency_check`
- `answer_coverage`
- `answer_change_analysis`
- `feedback_cards`
- `next_recommended_actions`
- `low_confidence_flags`
- `trace_refs`
- `feedback_metadata`

删除以下字段，除非 Recon 证明仍被真实业务消费：

- `explicit_score`
- `implicit_score`
- `scoring_dimensions`
- `knowledge_points`
- `technical_principles`
- `same_question_effect`
- `project_asset_consistency_check`
- `session_similarity_check`
- `project_asset_update_candidates`
- `feedback_summary`
- `polish_session_ref`
- `question_ref`
- `answer_ref`
- `user_confirmation_required`

注意：

- `feedback_id` 是存储和响应主键，必须保留。
- `contract_ids` 用于契约识别，必须保留。
- `trace_refs` 用于 LLM trace / evidence trace 关联，建议保留。

---

## 13. 删除目标四：LLM 只输出 candidate

定义唯一 LLM candidate schema：

- `feedback_text`
- `answer_summary`
- `score_reasoning`
- `loss_points`
- `reference_answer`
- `same_question_effect`
- `project_asset_update_candidates`
- `low_confidence_flags`
- `evidence_refs`

字段要求：

- `score_reasoning` 是对象数组，每项包含 `dimension` 和 `rationale`。
- `loss_points` 每项包含 `loss_point_id`、`severity`、`reason`、`evidence_refs`。
- `reference_answer.sections` 每项包含 `section_id`、`title`、`content`、`addresses_loss_point_ids`。
- `same_question_effect` 可选。
- `project_asset_update_candidates` 可选，但不得直接写正式资产。
- `evidence_refs` 只能引用 provider prompt 中存在的 evidence ref。

LLM candidate 禁止输出：

- `schema_id`
- `schema_version`
- `contract_ids`
- `feedback_id`
- `score_result`
- `deduction`
- `deducted_points`
- `asset_consistency_check`
- `answer_coverage`
- `answer_change_analysis`
- `feedback_cards`
- `next_recommended_actions`
- `project_asset_consistency_check`
- `session_similarity_check`
- `legacy_compatibility`
- `raw_prompt`
- `raw_completion`
- `provider_payload`
- `raw_provider_payload`
- `full_resume`
- `full_jd`
- `full_answer`
- `token`
- `secret`
- `cookie`

---

## 14. 删除目标五：Prompt 降噪

修改 `feedback_prompt_assets.py`：

1. provider prompt 改为 candidate prompt。
2. `output_schema` 只描述 candidate 结构。
3. `required_json_schema.required_fields` 删除所有 Phase4 和 final payload 字段：
   - `asset_consistency_check`
   - `answer_coverage`
   - `answer_change_analysis`
   - `feedback_cards`
   - `next_recommended_actions`
   - `score_result`
   - `explicit_score`
   - `implicit_score`
4. `output_requirements` 改成“返回 candidate JSON”。
5. `refusal_and_low_confidence_policy` 保留，但改成 candidate 级别规则。
6. Prompt 不再要求 LLM 生成最终评分、卡片顺序或下一步动作。

---

## 15. 删除目标六：validator 重写为两层

新增两个明确 validator：

- `validate_feedback_candidate_payload(payload: object)`
- `validate_final_feedback_payload(payload: object)`

要求：

1. candidate validator 只验证 LLM candidate 的最小语义结构。
2. final validator 只验证服务端最终 payload。
3. 不再让 LLM 承担 Phase4、next actions、最终 score 的硬校验。
4. 删除 `score_loss_deduction_mismatch` 作为 LLM 输出失败条件。
5. final validator 可以检查服务端生成的 score / deduction 一致性，但这是服务端 bug，不是 provider validation failed。

旧接口处理原则：

- 允许在重构中间批次短暂保留 `validate_generated_feedback_payload(...)` 以迁移调用方。
- 最终合并状态必须删除旧接口。
- 不允许把 deprecated 旧接口作为最终兼容层保留下来。
- 所有生产代码和测试必须迁移到新 validator。

---

## 16. 删除目标七：Score / deduction 改为服务端策略生成

新增领域策略：

路径建议：

- `apps/api/app/domain/polish/policies/scoring_policy.py`

策略要求：

- LLM 不再输出可信 deduction。
- LLM 不再输出最终 `score_result`。
- LLM 只给 loss point severity / reason。
- 服务端根据 severity 生成 deduction。
- 服务端计算最终 score_result。

建议初始策略：

- `critical`: 20
- `major`: 12
- `minor`: 6

最终实现应允许后续结合 polish theme、题目类型、expected dimensions 扩展，但本轮不要过度设计。

`apply_feedback_core_rules()` 或 final payload builder 应调用 scoring policy，生成：

- `loss_points[].deduction`
- `score_result.score_value`
- `score_result.score_type`
- `score_result.scoring_basis`

---

## 17. 删除目标八：FeedbackGenerationService 收敛

`FeedbackGenerationService.generate()` 新流程：

1. normalize context
2. build candidate prompt
3. call agent
4. extract candidate
5. validate candidate
6. apply deterministic rules
7. compute score
8. build final payload
9. validate final payload
10. return result

注意：

- Phase4 字段由 deterministic rules 生成。
- next actions 由 deterministic rules 生成。
- score_result 由 scoring policy 生成。
- final payload 由服务端组装。
- 不再拿 LLM generated final payload 覆盖后再校验。

---

## 18. 删除目标九：Application 主流程拆瘦

把 feedback 主流程迁移到 `PolishFeedbackApplicationService`。

目标：

- `PolishUseCases.create_feedback_task()` 只负责同步服务、委托、保持现有外部入口。
- `PolishFeedbackApplicationService.create_feedback_task()` 承担 feedback task 主业务流程。
- 不保留 use_cases 和 feedback_application_service 两套互调实现。

事务与锁边界：

1. 保持现有 feedback lock 语义。
2. 不要在 service 内另开一套不受控事务。
3. 如果 repository 已管理 session factory，则沿用现有 repository 模式。
4. 拆分后不得引入锁失效、重复生成或死锁。
5. 并发重复请求测试必须保留并通过。

---

## 19. 删除目标十：最小必要日志

只新增或保留三类 feedback 事件：

- `feedback_generation_started`
- `feedback_generation_failed`
- `feedback_generation_succeeded`

字段：

- `session_id`
- `question_id`
- `answer_id`
- `llm_called`
- `provider_status`
- `error_code`
- `validation_stage`
- `candidate_valid`
- `prompt_char_count`
- `evidence_item_count`
- `duration_ms`

日志规则：

1. 不新增复杂 ValidationReport。
2. 不新增新的 debug dump 格式。
3. 不记录 raw prompt、raw completion、provider_payload、raw_provider_payload。
4. raw LLM I/O 继续沿用现有 transport `.local/llm-raw` 能力。
5. 日志必须复用现有 LogUtil，不引入新依赖。

---

## 20. 分批落地顺序

### A 批：删除 reserved / legacy 基础分支

任务：

1. 扫描 reserved / legacy 引用。
2. 删除 reserved feedback 文件和分支。
3. 删除 legacy fields。
4. 新增必要 Alembic 迁移。
5. 同步前端类型和消费字段。

验证：

- API 不再返回 reserved。
- API 不再返回 legacy_compatibility。
- 历史 reserved 数据能被迁移为 pending 或 failed。

### B 批：收敛 schema 与 candidate schema

任务：

1. 收敛 final feedback schema。
2. 定义 candidate payload fields。
3. 删除 generated-as-LLM-output 旧契约常量。
4. 保留 final contract ids。

验证：

- schema 文件不再同时维护 reserved / generated / quick 多套概念。
- final payload 字段唯一。

### C 批：Prompt 降噪与 ScoringPolicy

任务：

1. Prompt 改为 candidate 输出。
2. 删除 Phase4 required fields。
3. 新增 ScoringPolicy。
4. 删除 LLM deduction / score_result 信任路径。

验证：

- LLM candidate 不含 Phase4 也能进入后续流程。
- score_result 由服务端生成。

### D 批：validator 两层改造

任务：

1. 新增 candidate validator。
2. 新增 final validator。
3. 迁移 service 和测试。
4. 中间允许短暂保留旧 validator 接口。

约束：

- D 批结束后，生产代码不得依赖旧 validator。
- G 批之前必须删除旧 validator 接口。

### E 批：FeedbackGenerationService 与 Application Service 收敛

任务：

1. 重写 FeedbackGenerationService 新流程。
2. 把 use_cases 中 feedback 主流程迁移到 PolishFeedbackApplicationService。
3. 保持锁和事务语义。
4. 删除重复流程。

验证：

- 并发重复生成测试通过。
- failed payload 不包含 generate_next_question。
- final payload 由服务端生成完整结构。

### F 批：最小日志

任务：

1. LogUtil 增加 3 个 feedback 事件。
2. service 在 started / failed / succeeded 打点。
3. 日志字段包含 validation_stage 和 candidate_valid。

验证：

- 日志 JSON 字段齐全。
- 不泄露 raw prompt / raw completion / provider payload。

### G 批：最终删除旧接口与旧测试

任务：

1. 删除旧 `validate_generated_feedback_payload(...)`。
2. 删除 reserved / legacy / Phase4 LLM 输出相关旧测试。
3. 删除无调用函数和常量。
4. 清理文档中明显过时的 feedback 契约描述。

最终要求：

- 不保留 deprecated validator。
- 不保留 reserved fallback。
- 不保留 legacy_compatibility。
- 不保留 generated final payload 作为 LLM 输出契约。
- 净删除代码量大于新增代码量。

---

## 21. 必须补齐或改写的测试

新增或改写以下测试：

1. candidate validator 通过。
2. candidate validator 失败。
3. final validator 通过。
4. final validator 失败。
5. LLM candidate 不含 Phase4 字段也能生成 final feedback。
6. final payload 包含服务端生成的 Phase4 字段。
7. score_result 由服务端算出，不依赖 LLM。
8. failed payload 不包含 `generate_next_question`。
9. API 返回不包含 `reserved`。
10. API 返回不包含 `legacy_compatibility`。
11. 并发生成、锁、去重仍正常。
12. 日志事件包含 `validation_stage` 和 `candidate_valid`。
13. 前端类型与页面消费新 payload shape 正常。

删除或重写以下测试：

- 只保护 reserved shape 的测试
- 只保护 legacy_compatibility 的测试
- 要求 LLM 返回 Phase4 字段的测试
- 要求旧 `validate_generated_feedback_payload(...)` 长期兼容的测试
- 只验证旧错误码但无业务价值的测试

---

## 22. 推荐验证命令

后端：

- `PYTHONPATH=.:apps/api .venv/bin/pytest tests/api/test_polish_feedback_generation_service.py -q`
- `PYTHONPATH=.:apps/api .venv/bin/pytest tests/api/test_polish_feedback_generation_schema.py -q`
- `PYTHONPATH=.:apps/api .venv/bin/pytest tests/api/test_polish_feedback_agent_io_alignment.py -q`
- `PYTHONPATH=.:apps/api .venv/bin/pytest tests/api/test_polish_feedback_runtime.py -q`
- `PYTHONPATH=.:apps/api .venv/bin/pytest tests/api/test_polish_api.py -q`

前端：

- 先检查 `package.json` 中实际脚本。
- 运行对应 typecheck / test。
- 如果没有独立 typecheck，则运行最小相关 web 测试。

数据库：

- 执行 Alembic upgrade。
- 验证 reserved 历史数据迁移。
- 验证 generated / failed 数据不被破坏。

---

## 23. 最终验收标准

最终状态必须满足：

1. reserved feedback 已删除。
2. legacy compatibility 已删除。
3. LLM 只输出 candidate。
4. Phase4 只由服务端规则层生成。
5. score_result 只由服务端 scoring policy 生成。
6. validator 分为 candidate / final 两层。
7. `PolishUseCases` 不再承载完整 feedback 主流程。
8. 前端类型与 API payload 一致。
9. Alembic migration 处理历史 reserved 数据。
10. 旧 validator 兼容接口最终删除。
11. 净删除代码量大于新增代码量。
12. 后端相关测试通过。
13. 前端相关测试或 typecheck 通过。
14. `git status --short` 中只存在本任务相关改动。

---

## 24. 最终输出要求

最终回复必须包含：

1. Root Cause
2. Scope
3. Deleted files
4. Deleted functions
5. Deleted fields
6. Deleted or rewritten tests
7. New feedback candidate shape
8. New final feedback payload shape
9. New feedback generation flow
10. Migration summary
11. Files changed
12. Validation results
13. Net reduction summary
14. Remaining risks

Net reduction summary 必须列出：

- 删除文件数
- 删除函数数
- 删除字段数
- 删除测试数
- 新增文件数
- 新增函数数
- 新增测试数
- 大致新增/删除行数

---

## 25. Recon 阶段输出模板

Recon 阶段必须按以下格式输出：

# Recon Result

## Current Worktree

- git status:
- non-task changes:
- risk:

## Reserved References

- file:
- symbol:
- usage:
- delete / migrate decision:

## Legacy References

- file:
- symbol:
- usage:
- delete / migrate decision:

## Validator Callers

- file:
- caller:
- migration target:

## Frontend Consumers

- file:
- field:
- usage:
- replacement:

## Database Findings

- feedback table:
- status column:
- payload column:
- reserved data migration needed:
- migration strategy:

## Delete Plan

### Files to delete

### Functions to delete

### Fields to delete

### Tests to delete or rewrite

## New Candidate Shape

## New Final Payload Shape

## Patch Batches

- A:
- B:
- C:
- D:
- E:
- F:
- G:

## Risks

## Next Step

Do not patch until this Recon is reviewed.

<!-- PROMPT_END -->
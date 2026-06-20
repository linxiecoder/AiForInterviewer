---
title: Polish Question Generation AI Task Result Fix Plan
type: refactor-implementation-plan
status: draft-evidence
owner: backend-frontend
created_at: 2026-06-20
source_task: AIFI-BE-008
source_evidence: local-debug-polish-question-generation-no-visible-question
---

# Polish 题目生成失败可见性与 LLM 输出契约修复方案

## 0. 文档边界

本文档记录 2026-06-20 本地排查形成的实现方案，只用于指导当前修复窗口的开发执行。

本文档不替代以下 active 入口：

- `docs/00-governance/DOCS_INDEX.md`
- `docs/03-implementation/BACKLOG.md`
- `docs/03-implementation/DELIVERY_PLAN.md`
- `docs/02-design/PROMPT_SPEC.md`
- `docs/02-design/PROMPT_ASSET_SPEC.md`
- `docs/02-design/PROMPT_EVALUATION_SPEC.md`
- `docs/02-design/API_SPEC.md`
- `docs/02-design/DATA_MODEL.md`
- `docs/02-design/APPLICATION_FLOW_SPEC.md`
- `docs/02-design/SECURITY_PRIVACY.md`

本方案不得被理解为新的 roadmap、长期计划入口或任务体系。正式开发仍需以当前授权窗口和 `BACKLOG.md` 中已登记任务边界为准。

本轮建议挂靠 `AIFI-BE-008`，并在进入代码实现前建立当轮 scope lock。本文档只作为该 scope lock 的实现证据和审计修订材料，不成为长期事实源；若后续发现需要变更 active contract，应回写 `API_SPEC.md` / `DATA_MODEL.md` / `PROMPT_*` 或 `BACKLOG.md` 的对应入口。

### 0.1 已确认推荐范围

本方案方向成立。基于复审结论，本轮采用以下收敛选择：

1. API result 本轮正式新增 `validation_errors`，并同步 `API_SPEC.md`、`AiTaskResultResponse`、前端类型和 contract 测试；本轮不新增通用 `result_payload` 给 question generation 使用。
2. 前端不使用 `result_payload` 承接题目生成失败；失败态只使用 `status`、`validation_errors`、`candidate_refs`、`validation_result_ref` 和安全文案展示。现有 `result_payload` 保持 feedback payload 兼容语义。
3. `AiTaskResult` 扩展采用 additive nullable 字段，并说明旧 task、旧 feedback payload、空 result row 的兼容读取和回滚方式；不得无授权新增独立 migration 体系。
4. 本轮验收范围限定为“提交任务后的当前页面轮询能显示失败原因”。刷新页面后仍展示最近一次失败原因不纳入本轮；如需实现，应另行补 session detail 最近 question generation task ref 或前端受控 task id 持久化。
5. `validation_failed` 的 LLM 输出只能作为失败摘要和校验证据展示，不得被 repair 成正式 `Question`。

## 1. 当前已确认问题

页面刷新后没有题目，不是单一前端问题。当前链路存在两个确定缺口：

1. 题目生成实际发送给 LLM 的 compact provider request 丢失了关键输出字段形状。
2. 题目生成校验失败后，后端没有把可展示的失败结果完整写入 AI Task result 读模型，前端轮询终态后无法展示失败原因。

这两个缺口叠加后，表现为：

- LLM raw log 中可以看到 provider 返回 JSON。
- 后端解析或业务 grounding 校验失败。
- `questions` 正式业务表没有新增题目。
- 前端刷新 session 只能查询正式题目，因此页面仍然没有题目。
- AI Task 查询结果缺少足够的 `validation_errors` / `candidate_refs` / `validation_result_ref` 展示信息。

## 2. 代码事实

### 2.1 LLM 实际输入不是完整 Prompt Asset

题目生成链路：

```text
QuestionGenerationService.generate
  -> build_question_provider_request
  -> build_validated_transport_request
  -> OpenAICompatibleLlmTransport.generate
  -> /chat/completions
```

相关文件：

- `apps/api/app/application/polish/question_generation_service.py`
- `apps/api/app/application/polish/question_generation_prompts.py`
- `apps/api/app/infrastructure/llm/openai_compatible.py`

`OpenAICompatibleLlmTransport` 实际发送的是：

- `system` message：通用结构化 JSON 执行器提示。
- `user` message：JSON，根字段包含 `task_type`、`input_refs`、`evidence_bundle`。
- `response_format={"type": "json_object"}`。

当前问题是通用 `system` prompt 要求模型遵守 `evidence_bundle.prompt` 和 `output_schema`，但题目生成的 `evidence_bundle` 实际来自 `build_question_provider_request()`，并不携带完整 `prompt` 和完整 `output_schema`。

### 2.2 provider request 只带 required fields，不带字段形状

`build_question_provider_request()` 当前会构造：

```text
expected_output_contract.required_fields
expected_output_contract.evidence_refs_must_match
expected_output_contract.generation_policy
safety_rules_summary
```

但当前没有把以下字段形状完整传给 LLM：

- `scoring_rubric` 必须是数组。
- `scoring_rubric[]` 每项必须包含 `dimension` 和 `signals[]`。
- `confidence` 必须是字符串枚举：`high` / `medium` / `low`。
- `evidence_refs` 必须来自允许的 evidence refs。
- `clarification_needed` 必须是 boolean。
- `missing_context` 必须是字符串数组。

字段形状的直接事实依据来自当前代码中的 full prompt asset `output_schema` 与 parser 校验逻辑；active prompt docs 支持“输出必须可校验、失败必须 rejected / validation failed”的原则，但 `P-POLISH-002` 子文档并未逐字段登记 `scoring_rubric` / `confidence` / `evidence_refs` 的完整形状。开发时应以当前代码中的 `output_schema`、parser 和 grounding policy 为实现依据；如需把字段形状升格为长期事实源，必须在另一个授权窗口回写 active prompt asset / API contract 文档。

因此 provider 返回如下形态时，raw log 看似成功，但后端应当拒绝：

```json
{
  "scoring_rubric": {
    "excellent": "...",
    "good": "..."
  },
  "confidence": 0.85
}
```

这是 schema invalid，不是业务题目生成成功。

### 2.3 校验失败不得写正式 Question

`QuestionGenerationService.generate()` 中，LLM 返回结果先经过 `_parse_llm_question_payload()`，再经过 grounding 校验。失败时返回：

```text
QuestionGenerationResult(
  succeeded=False,
  draft=None,
  validation_errors=...
)
```

这个行为是正确的。根据 `DATA_MODEL.md`、`API_SPEC.md`、`PROMPT_EVALUATION_SPEC.md`：

- `validation_failed` 不得写 formal object。
- 不可信输出不得通过 repair 伪装成成功。
- counterexample 的预期只能是 rejected / validation failed / fallback / low confidence / manual review。
- 不得把 raw prompt、raw completion、provider payload 暴露给前端或普通日志。

因此本修复不能把非法 LLM 输出自动转换成正式题目。

### 2.4 当前 AiTaskResult 物理模型不支持结构化结果摘要

当前 ORM：

```python
class AiTaskResult(...):
    ai_task_id
    result_sequence
    validation_result_ref_id
    trace_ref_id
    result_ref_id
```

当前没有以下字段：

- `candidate_refs`
- `suggestion_refs`
- `validation_errors`
- `low_confidence_flags`
- `source_availability`
- `evidence_refs`

这是当前 ORM 与 `DATA_MODEL.md` 通用 AI Task result 语义之间的明确缺口。需要注意：`API_SPEC.md` 当前 result response 尚未登记 `validation_errors`，而 `result_payload` 也不是当前 `AiTaskResultResponse` contract 字段。本轮选择只把 `validation_errors` 纳入正式 API contract；`result_payload` 不作为 question generation 失败摘要的对外字段。

### 2.5 当前 AI Task result 投影偏 feedback 专用

`apps/api/app/infrastructure/db/repositories/ai_tasks.py` 当前在 `_status_projection()` 和 `_result_projection()` 中读取：

- `candidate_refs`
- `suggestion_refs`
- `validation_errors`
- `result_payload`

但这些字段主要从 `_feedback_payload_for_task()` 读取。题目生成失败没有 feedback payload，因此 `/api/v1/ai-tasks/{id}/result` 无法给前端返回足够可展示信息。

### 2.6 adjacent evidence 规则已经存在，但 provider-facing 表达不够强

当前 full prompt asset 和 grounding policy 已有 adjacent evidence 约束：

- 邻近项目证据不能被写成候选人已经完成目标能力。
- `adjacent_project_evidence` 必须使用假设式或澄清式表达。
- 问题文案应使用“如果要引入 / 改造 / 你会如何设计”这类表达。

当前缺口是：provider request 只传了摘要布尔值，LLM 很容易忽略具体措辞边界。

## 3. 修复目标

本次修复目标：

1. LLM 输入契约足够明确，减少 provider 按常识猜字段形状。
2. LLM 输出不合格时，后端继续拒绝正式写题目。
3. 题目生成失败要形成可查询的 AI Task result。
4. 前端轮询到终态后能显示失败原因，不再静默刷新为空。
5. API response、日志、task result 不暴露 raw prompt、raw completion、provider payload、system prompt 或 hidden rubric。

非目标：

- 不新增 AI 功能入口。
- 不让前端直接接触 LLM/provider。
- 不把 validation failed 的 LLM 输出修成正式题目。
- 不恢复旧 direct path、legacy fallback-as-authority 或 provider direct formal write。
- 不新增独立 roadmap、阶段、任务体系。

## 4. 实现方案

### 4.1 第一优先级：补齐 LLM compact 输出契约

修改文件：

- `apps/api/app/application/polish/question_generation_prompts.py`
- `apps/api/app/infrastructure/llm/openai_compatible.py`

#### 4.1.1 provider request 增加 field contracts

在 `build_question_provider_request()` 的现有 `expected_output_contract` 内增加 compact field contract。

建议结构：

```json
{
  "expected_output_contract": {
    "schema_id": "polish_question_generation_v1",
    "schema_version": "1",
    "required_fields": ["question_text"],
    "evidence_refs_must_match": ["..."],
    "field_contracts": {
      "question_text": {
        "type": "string",
        "required": true,
        "description": "single interview question, no answer leak"
      },
      "follow_ups": {
        "type": "array<string>",
        "required": true
      },
      "scoring_rubric": {
        "type": "array<object>",
        "required": true,
        "item_required_fields": ["dimension", "signals"],
        "signals_type": "array<string>"
      },
      "confidence": {
        "type": "enum<string>",
        "allowed_values": ["high", "medium", "low"]
      },
      "clarification_needed": {
        "type": "boolean"
      },
      "missing_context": {
        "type": "array<string>"
      },
      "evidence_refs": {
        "type": "array<string>",
        "allowed_values_from": "evidence_refs_must_match"
      }
    }
  }
}
```

实现要求：

- 保持 provider request 顶层 key 不变，避免破坏 `_QUESTION_PROVIDER_REQUEST_TOP_LEVEL_KEYS`。
- 不传完整 raw prompt。
- 不传 raw resume / raw JD / provider payload。
- 只传输出结构和必要安全语义。

#### 4.1.2 provider request 增强 adjacent evidence 规则

在现有 `safety_rules_summary` 或 `expected_output_contract.generation_policy` 中增加明确规则：

```json
{
  "adjacent_project_evidence_rule": {
    "must_use_hypothetical_wording": true,
    "must_not_claim_completed_target_capability": true,
    "allowed_wording_examples": [
      "如果要引入...",
      "假设要改造...",
      "你会如何设计..."
    ],
    "forbidden_meaning": "candidate already completed the target capability"
  }
}
```

注意：这里不是新增业务规则，而是把已经存在于 prompt asset 和 grounding policy 的规则传给真实 provider request。

#### 4.1.3 修正通用 system prompt

当前 system prompt 不应继续要求所有任务遵守不存在的 `evidence_bundle.prompt` 和 `output_schema`。

改为：

```text
必须严格遵守 user message 中 evidence_bundle.expected_output_contract、safety_rules_summary、schema_id 和 prompt_version。
```

对仍然传完整 `prompt` / `output_schema` 的其他任务，需要检查测试。如果存在依赖旧 wording 的任务，可以在 system prompt 中兼容表达：

```text
必须严格遵守 user message 中 evidence_bundle.expected_output_contract 或 output_schema，以及 safety_rules_summary、schema_id 和 prompt_version。
```

不得在 system prompt 中要求模型输出 provider payload、内部推理过程或额外说明。

### 4.2 第二优先级：补齐 AI Task result 安全摘要能力

修改文件：

- `apps/api/app/infrastructure/db/models/ai_task.py`
- `apps/api/app/infrastructure/db/repositories/polish.py`
- `apps/api/app/infrastructure/db/repositories/ai_tasks.py`
- `apps/api/app/schemas/ai_tasks.py`
- 相关测试文件

#### 4.2.1 明确当前缺口

当前 `AiTaskResult` 只有 ref 字段，不能保存结构化结果摘要。要满足 `DATA_MODEL.md` 的安全结果摘要语义，并让实现与 `API_SPEC.md` 保持一致，本轮只补齐 question generation 失败可见性所需的安全摘要字段，并把 `validation_errors` 纳入正式 result response contract。

建议在 `AiTaskResult` 增加 JSON 字段：

```python
candidate_refs_json
suggestion_refs_json
validation_errors_json
low_confidence_flags_json
evidence_ref_ids
```

字段命名可按当前仓库 ORM 命名习惯调整，但必须满足以下语义：

- 只能保存 sanitized refs / status / validation summary。
- 不保存 raw prompt。
- 不保存 raw completion。
- 不保存 provider request / response payload。
- 不保存完整简历、完整 JD、回答正文或系统提示。

新增字段必须是 additive nullable JSON / ref 字段，旧 task、旧 feedback payload 和没有 result row 的历史数据必须继续可读。读取逻辑应优先使用通用 `AiTaskResult` 字段，再 fallback 到现有 feedback payload；写入逻辑应避免重复插入导致唯一键或序列冲突。回滚策略是停止读取或返回新字段、保留旧 fallback，不通过删除字段来恢复旧行为。

当前仓库本地 schema 初始化由 SQLAlchemy `Base.metadata.create_all()` 承接，没有独立 Alembic 目录。本次实现不要无授权新增 migration 体系；测试环境按当前 ORM 初始化路径验证。若后续需要生产数据迁移，必须另行进入授权任务和 active docs / backlog 边界。

注意：`Base.metadata.create_all()` 不会给已经存在的本地数据库表自动补列。本轮实现若新增 ORM 字段，测试应使用 fresh schema；已有本地开发库需要明确 reset / recreate / 受控升级步骤。生产数据迁移仍需另行授权，不在本文档中创建独立 migration 体系。

#### 4.2.2 add_task 写入 AiTaskResult

当前 `SqlAlchemyPolishRepository.add_task()` 只插入 `AiTask`。需要调整为：

- 写入或更新 `AiTask`。
- 对终态任务同步写入 `AiTaskResult`。
- `validation_failed` / `generation_failed` / `source_unavailable` 也必须有 result row。

终态包括：

- `succeeded`
- `partial`
- `low_confidence`
- `validation_failed`
- `source_unavailable`
- `generation_failed`
- `timed_out`
- `cancelled`

题目生成 validation failed 时，至少写入：

```json
{
  "status": "validation_failed",
  "validation_errors": ["..."],
  "candidate_refs": [],
  "evidence_refs": ["..."],
  "result_ref": {
    "trace_type": "validation_result",
    "trace_ref_id": "..."
  },
  "provider_payload": null
}
```

当前 application 层 task status 已有 `validation_errors`、`candidate_refs`、`suggestion_refs` 等结果字段。实现时需要确认是否还要补充 `evidence_refs`；本轮不新增 question generation 通用 `result_payload`。新增语义应优先在 domain/application 层表达，而不是在 repository 里硬编码业务含义。

#### 4.2.3 ai_tasks repository 改成通用 result projection

`SqlAlchemyAiTaskRepository.get_status()` 和 `get_result()` 应优先从 `AiTaskResult` 通用字段投影：

- `status`
- `result_ref`
- `candidate_refs`
- `suggestion_refs`
- `validation_result_ref`
- `validation_errors`
- `provider_payload: null`

API contract gate：

- `GET /api/v1/ai-tasks/{id}/result` 本轮正式返回 `validation_errors`，必须同步更新 `API_SPEC.md`、`AiTaskResultResponse`、前端 `PolishAiTaskResult` 类型和 contract 测试。
- 本轮不为 question generation 返回通用 `result_payload`。现有 feedback task 的 `result_payload` 兼容逻辑可保留，但不得把 question generation 失败摘要塞进 `PolishFeedbackPayload`。

兼容逻辑：

1. 优先使用 `AiTaskResult` 的通用 JSON 字段。
2. 对历史 feedback task，保留 `_feedback_payload_for_task()` fallback。
3. 不允许把 provider payload 从任何路径返回给前端。

用户可见状态建议：

| task status | user_visible_status |
| --- | --- |
| `succeeded` | 题目已生成 |
| `validation_failed` | 题目未生成，AI 输出未通过校验 |
| `generation_failed` | 题目生成失败，可重试 |
| `source_unavailable` | 缺少可用材料，无法生成题目 |
| `timed_out` | 任务已超时，可重试 |

注意：如果 task_type 是 feedback，仍可沿用反馈文案；不要把所有任务都写成“反馈生成中”。

### 4.3 第三优先级：前端轮询终态分支

修改文件：

- `apps/web/src/pages/interview/InterviewPage.tsx`
- `apps/web/src/entities/polish/model/types.ts`

#### 4.3.1 类型补齐

当前前端 `PolishAiTaskResult.result_payload` 是 feedback payload 兼容字段，不适合承接 question generation 失败摘要。本轮前端不使用 `result_payload` 展示题目生成失败，只补齐以下字段：

- `validation_errors`
- `candidate_refs`
- `suggestion_refs`
- `validation_result_ref`

`provider_payload` 不应被使用；保留类型只用于断言其为 `null`。现有 feedback `result_payload` 兼容逻辑不得被复用为 question generation failure payload。

#### 4.3.2 轮询后按终态处理

当前问题不是简单 reload session。应按 task result status 分支：

| result status | 前端行为 |
| --- | --- |
| `succeeded` | reload session，找到 `candidate_refs` 中的 `question` ref 并 focus |
| `validation_failed` | 展示“题目未生成，AI 输出未通过校验”，展示安全错误码 |
| `generation_failed` | 展示“题目生成失败，可重试” |
| `source_unavailable` | 展示“缺少可用材料，无法生成题目” |
| `timed_out` | 展示超时并允许重试 |

关键点：

- `validation_failed` 不应继续调用 focus generated question。
- 没有新 question ref 时，不要假装成功。
- reload session 只能刷新正式题目，不负责解释失败原因。

#### 4.3.3 刷新页面后的可见性

刷新页面后，如果前端没有保存最近的 `ai_task_id`，只能从 session detail 读取正式题目。由于 validation failed 不写 `questions`，页面仍然不会出现题目，这是正确业务结果。

要让刷新后仍能看到失败原因，需要后端 session detail 暴露最近一次 question generation task ref，或前端受控持久化当前 task id。推荐后端提供最近 task ref，因为它符合 owner-scoped backend authority，且不要求前端推断 provider 或 LLM 状态。

本轮明确不实现刷新页面后的失败可见性，只保证提交任务后的当前页面轮询能显示失败原因。若后续要支持刷新后展示最近失败状态，应另行扩展 session detail 的最近 question generation task ref，并同步后端 schema、前端类型和测试。

## 5. adjacent evidence 约束处理

当前约束是合理的，不能删除：

- 邻近项目证据只能说明候选人有可迁移背景。
- 不能把邻近项目证据写成候选人已完成目标能力。
- 对目标能力必须使用假设式、设计式或澄清式题目。

需要改的是表达方式：

### 5.1 LLM 输入层

把 adjacent evidence 规则明确写入 provider request：

```text
当 source_support_level=adjacent_project_evidence 时：
1. 只能把已验证项目作为背景。
2. 不得声称候选人已经完成目标能力。
3. 主问题必须使用“如果/假设/你会如何设计”表达。
```

### 5.2 rewrite 层

检查并修改 `_rewrite_project_clarification_question()`。

避免生成：

```text
基于你在 X 中 Y 的经历，...
```

推荐改为：

```text
参考已有项目中可验证的工程背景，如果要扩展到 <target_capability>，你会如何设计？
```

这样既利用 adjacent evidence，又不会把目标能力写成已完成事实。

### 5.3 grounding policy 层

保留 `QuestionGroundingPolicy` 的 blocking 行为。

可做微调：

- 对明显假设式表达放行。
- 对“你已经实现/完成/主导/落地了目标能力”继续阻断。
- 不要为了提高生成率删除 `adjacent_project_evidence_forbidden_completed_experience_claim`。

## 6. 禁止实现方式

以下实现方式禁止：

- 前端直接调用 LLM 或 provider。
- 前端根据 raw log 自己构造题目。
- 后端把 schema invalid 的 LLM 输出 repair 成正式 question。
- validation failed 后仍写 `questions`。
- 在 API response 返回 raw prompt、raw completion、provider payload、system prompt、hidden rubric。
- 新增独立 AI 功能入口绕过 `QuestionGenerationService`。
- 恢复旧 direct path、legacy fallback-as-authority、provider direct formal write。
- 为了调试把完整 provider request / response 写入普通日志或 task result。

## 7. 测试方案

### 7.1 后端单元测试

新增或更新题目生成 prompt builder 测试：

- `build_question_provider_request()` 包含 `expected_output_contract.field_contracts.scoring_rubric`。
- `build_question_provider_request()` 包含 `expected_output_contract.field_contracts.confidence.allowed_values`。
- adjacent evidence provider request 包含 `must_not_claim_completed_target_capability`。
- provider request 顶层 key 仍符合 `_QUESTION_PROVIDER_REQUEST_TOP_LEVEL_KEYS`。

新增或更新 transport prompt 测试：

- 通用 system prompt 不再只引用不存在的 `evidence_bundle.prompt` / `output_schema`。
- system prompt 要求遵守 `expected_output_contract` 和 `safety_rules_summary`。

### 7.2 后端集成测试

新增或更新 polish question generation 测试：

1. provider 返回 `scoring_rubric` object、`confidence` number。
   - task status 为 `validation_failed`。
   - `questions` 表不新增记录。
   - `/api/v1/ai-tasks/{id}/result` 返回 `validation_errors`。
   - `provider_payload` 为 `null`。
   - 不返回 question generation 通用 `result_payload`。

2. provider 返回合法 schema。
   - task status 为 `succeeded`。
   - `questions` 表新增正式题目。
   - task result 返回 question ref。

3. adjacent evidence 返回完成事实口吻。
   - grounding policy 阻断。
   - task status 为 `validation_failed`。
   - 不写 `questions`。

4. adjacent evidence 返回假设式题目。
   - grounding policy 放行或 warning。
   - 符合条件时写入正式题目。

5. 历史 feedback task 与旧 result row。
   - 旧 feedback payload fallback 仍可读。
   - 旧 task 没有通用 JSON 字段或字段为 `null` 时不报错。
   - feedback 任务的 result projection 不因 question generation 改造而回归。

### 7.3 API contract 测试

覆盖：

- `GET /api/v1/ai-tasks/{id}` owner scoped。
- `GET /api/v1/ai-tasks/{id}/result` 对 `validation_failed` 返回可见状态。
- `GET /api/v1/ai-tasks/{id}/result` 对 question generation `validation_failed` 返回 `validation_errors`。
- `provider_payload` 永远为 `null`。
- cross-user 查询仍被拒绝或不可见。
- `API_SPEC.md`、`AiTaskResultResponse`、前端 `PolishAiTaskResult` 类型和测试必须对 `validation_errors` 保持一致。
- 本轮不新增 question generation 通用 `result_payload`；现有 feedback `result_payload` 兼容路径不回归。
- 对 legacy / null `AiTaskResult` 字段保持兼容。

### 7.4 前端测试

覆盖：

- `succeeded` 后 reload 并展示新题。
- `validation_failed` 后展示失败状态，不再 focus question。
- `generation_failed` / `source_unavailable` 有明确文案。
- 没有 `question` candidate ref 时不报成功。
- 刷新页面后失败可见性不属于本轮验收；本轮只断言当前页面轮询期间失败可见。

## 8. 验收标准

本修复完成后，必须满足：

- DeepSeek 返回 schema invalid JSON 时，页面能显示题目未生成原因。
- schema invalid 不写 `questions`。
- schema valid 且 grounding 通过时，页面能展示新题。
- `/api/v1/ai-tasks/{id}/result` 对 question generation `validation_failed` 返回 `validation_errors`。
- `AiTaskResult` 能承接 sanitized result summary。
- API response 不包含 provider payload，且 `provider_payload` 始终为 `null`。
- question generation 失败不通过 `result_payload` 对外表达；现有 feedback `result_payload` 兼容读取不回归。
- 日志不保存 raw prompt、raw completion、provider payload。
- adjacent evidence 不会被写成候选人已完成目标能力。
- 现有反馈生成任务不因通用 AI Task result 投影改造而回归。
- 刷新页面后的失败可见性明确不属于本轮；后续如需支持，另行补 session detail 最近 task ref。

## 9. 建议开发顺序

1. 修改 `build_question_provider_request()`，补 compact field contracts 和 adjacent evidence rule。
2. 修改 `_system_prompt()`，让 system prompt 与真实 provider request 对齐。
3. 补 prompt builder / transport 单元测试。
4. 同步扩展 `API_SPEC.md`、`AiTaskResultResponse`、前端 `PolishAiTaskResult` 和 contract 测试，正式新增 `validation_errors`；不新增 question generation 通用 `result_payload`。
5. 扩展 `AiTaskResult` ORM 的安全结果摘要字段，保持 additive nullable 和旧数据兼容。
6. 修改 `add_task()`，让终态任务幂等写入或更新 `AiTaskResult`。
7. 修改 `SqlAlchemyAiTaskRepository`，优先从通用 `AiTaskResult` 投影 status/result。
8. 补 `/api/v1/ai-tasks/{id}/result` 相关测试。
9. 修改前端 task result 类型和轮询终态分支。
10. 补前端失败态展示测试。
11. 跑后端题目生成、反馈生成、AI task result 相关回归测试。

## 10. 最小验证命令建议

后端建议至少覆盖：

```bash
PYTHONPATH=.:apps/api PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -p no:cacheprovider \
  tests/api/test_polish_question_graph_integration.py \
  tests/api/test_openai_compatible_llm_transport.py \
  tests/api/test_polish_api.py \
  tests/api/test_llm_runtime.py \
  -q
```

前端建议至少覆盖：

```bash
npm run typecheck --workspace apps/web
```

如果项目已有更具体的 frontend test command，应优先使用当前仓库脚本，而不是新增测试入口。

## 11. 已确认决策与实现落点

以下决策已经按本轮推荐路线收敛，开发时按这些落点执行：

1. API 本轮正式返回 `validation_errors`，必须同步 `API_SPEC.md`、schema、前端类型和 contract 测试。
2. API 本轮不新增 question generation 通用 `result_payload`；现有 feedback `result_payload` 只保持兼容读取。
3. 当前 application 层 `PolishTaskStatus` 已有 `validation_errors`、`candidate_refs`、`suggestion_refs`；如需 `evidence_refs`，应在 application/domain 层补齐表达，不在 repository 硬编码业务含义。
4. `AiTaskResult` JSON 字段命名需和仓库现有 ORM / schema 风格一致，且必须 additive nullable。
5. 当前本地 schema 初始化没有 Alembic 目录；不要无授权新增 migration 体系。如需生产迁移，另走授权任务。
6. 已有本地数据库不会因 `create_all()` 自动补列；本轮测试使用 fresh schema，开发环境需要 reset / recreate / 受控升级说明。
7. 刷新后失败状态不属于本轮；后续如需支持，另行在 session detail 暴露最近 question generation task ref。

## 12. 最终判断

本问题的正确修复不是让失败的 LLM 输出也生成题目，而是：

```text
让 LLM 更清楚地知道要返回什么；
让后端继续严格拒绝非法输出；
让 AI Task result 正确承接失败结果；
让前端把失败状态展示给用户。
```

这条路径不破坏“各个 AI 功能只有后端统一入口”的约束，也不破坏 candidate / formal object 边界。本轮开发范围已收敛为：挂靠 `AIFI-BE-008`，正式新增 AI Task result `validation_errors`，不新增 question generation 通用 `result_payload`，只保证当前页面轮询失败可见，`AiTaskResult` 扩展保持 additive nullable 与旧数据兼容。

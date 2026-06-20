---
title: Polish 题目生成失败可见性与 LLM 输出契约修复实施清单
type: refactor-implementation-checklist
status: draft-evidence
owner: backend-frontend
created_at: 2026-06-20
source_task: AIFI-BE-008
source_plan: docs/refactor/20260620/polish-question-generation-ai-task-result-fix-plan.md
permalink: ai-for-interviewer/refactor/20260620/polish-question-generation-ai-task-implementation-checklist
---

# Polish 题目生成失败可见性与 LLM 输出契约修复实施清单

本文是 `AIFI-BE-008` 下的实施准备清单，只用于后续实现窗口的 scope lock、代码事实复核和验收拆分。它不是新的 roadmap、plan-v2、latest-plan、codex-plan、长期任务入口或 active design source；当前执行依据仍以 `docs/00-governance/DOCS_INDEX.md` 登记的 active docs、`docs/03-implementation/BACKLOG.md` 和 `docs/03-implementation/DELIVERY_PLAN.md` 为准。

## 1. 边界声明

### 1.1 当前文档生成边界

- 本轮只允许创建或更新本文件：`docs/refactor/20260620/polish-question-generation-ai-task-implementation-checklist.md`。
- 本轮不得修改生产代码、测试、配置、数据库、migration、active docs、原始 fix plan、`.env`、证书、密钥或依赖。
- 本轮不得启动服务、安装依赖、访问真实数据库、执行 migration、调用真实 LLM provider、生成 goal package、提交或推送。
- 本轮读取的 `docs/refactor/**` 与 `docs/goals/**` 只能作为 evidence，不得替代 active docs。

### 1.2 后续实现边界

- 后续实现必须挂靠 `docs/03-implementation/BACKLOG.md` 中的 `AIFI-BE-008`，不得绕过 BACKLOG 直接开启任务。
- 后续若需要更新 active API / data / prompt / security contract，必须在授权窗口内直接修改对应 active docs；本文件不能替代 contract 更新。
- 题目生成失败可见性只覆盖当前页面 polling 后的终态失败提示；刷新后恢复失败可见性不进入本轮范围。
- 题目生成不得引入通用 `result_payload` 作为失败可见性载体；`result_payload` 仍只能按现有兼容边界服务 feedback。
- `validation_failed` 输出不得被修复、补齐或降级写入正式 `Question`。
- 不建立 Alembic 或独立 migration 体系；当前仓库 schema 初始化仍由 SQLAlchemy `Base.metadata.create_all()` 承担。对已有本地数据库列缺失问题，只能通过 fresh schema、reset/recreate 或另行授权的受控升级处理。

## 2. 读取与事实快照

### 2.1 必读入口

| 文件 | 用途 | 本轮结论 |
| --- | --- | --- |
| `AGENTS.md` | 协作、文档治理、Markdown 和本地启动边界 | 本文件遵守中文、active docs、BACKLOG、Markdown 安全和完成报告要求 |
| `docs/00-governance/DOCS_INDEX.md` | 当前有效文档体系 | active docs 仍是唯一当前执行依据 |
| `docs/refactor/20260620/polish-question-generation-ai-task-result-fix-plan.md` | 本清单的来源 evidence | 采用其决策：新增 `validation_errors`、不新增题目生成 `result_payload`、当前页失败可见性、nullable additive result 字段、无 migration 系统 |
| `docs/03-implementation/BACKLOG.md` | 当前任务入口 | `AIFI-BE-008` 存在，状态为 `NOT_STARTED` |
| `docs/03-implementation/DELIVERY_PLAN.md` | 当前阶段入口 | F5 后端处于 `READY_TO_START`，F6/F7 后续承接 |

### 2.2 Active contract 摘要

| 文档 | 与本修复相关的约束 |
| --- | --- |
| `docs/02-design/PROMPT_SPEC.md` | Prompt 输出结构校验失败必须进入失败/校验失败路径，不得写入正常业务事实；不能把 raw prompt/completion/provider payload 写入日志、API 或 checkpoint |
| `docs/02-design/PROMPT_ASSET_SPEC.md` | Prompt builder 必须保持 `task_type`、`prompt_version`、`schema_id` 与 registry 一致；可以动态组装 compact evidence，但不能改变契约目标、输出 schema 和脱敏边界 |
| `docs/02-design/PROMPT_EVALUATION_SPEC.md` | negative fixtures 期望 validation failed 或 rejected，不得把不合格输出修复成 success；真实 provider eval 默认关闭 |
| `docs/02-design/API_SPEC.md` | API response 不得包含 raw prompt/completion/provider payload；AI task result 当前登记了 `provider_payload: null`，但尚未登记 `validation_errors` |
| `docs/02-design/DATA_MODEL.md` | `AiTaskResult` 逻辑对象可承载 result/candidate/suggestion/validation/low confidence/source availability/evidence/trace，但不得保存 provider response text |
| `docs/02-design/PERSISTENCE_MODEL.md` | `AiTask`/`AiTaskResult` 映射到 `ai_tasks`/`ai_task_results`；trace 与 API 不保存 provider payload、system prompt、completion 或 request body |
| `docs/02-design/APPLICATION_FLOW_SPEC.md` | frontend 只能发起 intent，不直接执行 LLM/DB；`validation_failed`、`source_unavailable`、`generation_failed` 不得被隐藏成 success |
| `docs/02-design/SECURITY_PRIVACY.md` | raw prompt、completion、provider request/response、system prompt、hidden rubric、secrets 不得进入普通 runtime row、log、API、timeline、copy 或 checkpoint |

### 2.3 当前代码事实

| 区域 | 当前事实 | 后续影响 |
| --- | --- | --- |
| `question_generation_prompts.py` | `build_question_provider_request()` 已输出 compact `expected_output_contract`、`generation_policy` 和 `safety_rules_summary`，但缺少 `scoring_rubric`、`confidence`、`clarification_needed`、`missing_context`、`evidence_refs` 的明确 field contract | Phase 2 需要补 compact 输出契约，不发送完整 prompt asset |
| `openai_compatible.py` | generic system prompt 仍要求遵守 `evidence_bundle.prompt`、`output_schema`、`schema_id`、`prompt_version` | Phase 2 需要让 provider 指令匹配 compact request，避免模型看不到字段契约 |
| `question_generation_service.py` | parser 已校验 required fields、rubric list、confidence enum、bool、missing_context、evidence_refs；失败会返回 `succeeded=False`、`draft=None` 和 `validation_errors` | Phase 3/4 应持久化和投影失败摘要，而不是修复成正式题目 |
| `question_grounding_policy.py` | adjacent project evidence 会阻断事实性完成经历宣称，要求假设式或澄清式措辞 | Phase 2/6 必须保持该 safety behavior |
| `models/ai_task.py` | `AiTaskResult` 只有 result/ref/validation/trace 基础字段，没有 candidate/suggestion/validation_errors/low confidence/source availability/evidence summary JSON 字段 | Phase 3 需要 additive nullable 字段，并说明本地 schema fresh/reset 边界 |
| `repositories/polish.py` | `add_task()` 只写 `AiTask`；feedback 已有 `_task_result_to_model()` 路径 | Phase 3 应扩展现有 result writer/upsert，避免新增并行 writer |
| `repositories/ai_tasks.py` | result projection 当前从 feedback payload 派生 `candidate_refs`、`suggestion_refs` 和 `validation_errors`，`provider_payload` 固定为 `None`；`AiTaskResultResponse` 尚无顶层 `validation_errors` | Phase 4 需要 result summary 优先、feedback fallback 兼容、question failure 不依赖 feedback payload |
| `schemas/ai_tasks.py` | `AiTaskResultResponse` 没有 `validation_errors`，也没有通用 `result_payload` | Phase 1/4 需要 additive nullable `validation_errors` |
| `schemas/polish.py` | `PolishTaskStatusResponse` 与 `PolishFeedbackPayload` 已有 `validation_errors` | Phase 4 禁止把 question failure 塞进 `PolishFeedbackPayload` |
| `types.ts` | `PolishAiTaskResult` 没有 `validation_errors`，`result_payload` 类型是 `PolishFeedbackPayload | null` | Phase 1/5 需要同步 frontend type，且不扩大 question generation 的 `result_payload` |
| `InterviewPage.tsx` | `waitForPolishAiTaskFinalStatus()` 会返回终态；`createCurrentNodeQuestion()` 和 `createFeedbackNextQuestion()` 在终态后直接调用 `focusGeneratedQuestionTask()` | Phase 5 需要在 focus 之前识别失败终态并展示当前页错误 |
| `tests/api/**` | 已有 prompt、provider boundary、question graph、persistence handoff、sensitive payload、AI task contract、feedback compatibility 等测试入口 | Phase 6 应用 focused tests 覆盖新增 contract |
| `tests/web/test_interview_actions.py` | 当前 source-scan 断言轮询后会调用 focus | Phase 5/6 需要改为验证失败终态不 focus、显示用户可见错误 |

## 3. 决策快照

| 决策 | 结论 |
| --- | --- |
| 任务挂靠 | 后续实现挂靠 `AIFI-BE-008` |
| API 结果字段 | `AiTaskResultResponse` 正式新增 `validation_errors: string[] | null` 或等价 nullable list |
| 题目生成 `result_payload` | 不新增、不复用、不作为失败可见性载体 |
| 前端可见性 | 只做当前页面 polling 后失败可见性；刷新后恢复失败状态 deferred |
| DB 字段策略 | `AiTaskResult` 只做 additive nullable summary 字段；兼容旧空字段/旧 feedback payload |
| migration 策略 | 不新增 Alembic/migration；本地旧库需 fresh schema、reset/recreate 或另行授权的受控升级 |
| 校验失败行为 | `validation_failed` 不得生成正式 `Question`，不得调用 focus generated question |
| Provider 安全 | 不保存、不返回、不测试输出 raw prompt/completion/provider payload；真实 provider eval 默认不执行 |
| 轻量安全检查 | 本轮优先关闭失败不可见问题，执行轻量敏感信息检查，重点防止 `provider_payload`、`raw_provider_payload`、`raw_prompt`、`raw_completion`、`api_key`、`secret` 泄漏；更完整的 system prompt、provider request/response、完整简历/JD 扫描后置到 release/security gate |
| Graph/authority | frontend 只发 intent；backend application/runtime 决定 execution 与持久化 |

## 4. 阶段总览

| Phase | 名称 | 主责 | 主要输出 | 进入下一阶段条件 |
| --- | --- | --- | --- | --- |
| 0 | Scope Lock 与代码事实复核 | 全栈/治理 | 当轮 scope lock、dirty tree 基线、contract/code/test 事实复核 | 确认只改授权文件、`AIFI-BE-008` 仍可用 |
| 1 | API/schema/frontend types 契约同步 | API/Web | `validation_errors` contract 与类型同步 | Contract tests 证明 additive 且 `provider_payload` 仍为 `null` |
| 2 | LLM compact provider request 输出契约修复 | Backend/Prompt | compact field contracts 与 provider system prompt 对齐 | fake/provider-boundary tests 证明不发送 raw payload 且 invalid 输出失败 |
| 3 | `AiTaskResult` safe summary 持久化与兼容读取 | Backend/Persistence | nullable summary fields、question failure result write、旧数据兼容 | fresh schema tests 和旧 payload fallback tests 通过 |
| 4 | AI task result projection 与 feedback 回归保护 | Backend/API | result projection 顶层 `validation_errors`、feedback 兼容 | API contract tests 覆盖 question/feedback 双路径 |
| 5 | 前端当前页 polling 失败状态 | Frontend | 失败终态用户可见、成功路径仍 focus | web source/type tests 证明失败不 focus |
| 6 | 联调测试、回归与轻量 forbidden scan | QA/Full stack | focused regression suite、轻量 forbidden scan、验收证据 | 全部最小验证命令通过或记录阻断 |

## 5. Phase 0 - Scope Lock 与代码事实复核

### Goal

在任何实现前重新确认授权范围、当前 dirty worktree、active contract、CodeGraph/代码事实、测试入口和 DB schema 策略，防止在已有未提交改动上误改非目标文件。

### Scope

- 读取 governance、active docs、原始 fix plan、目标代码和测试。
- 确认 `.codegraph/` 存在时优先使用 CodeGraph 理解相关 symbols，再用 `rg`/`Select-String` 精读具体位置。
- 记录当轮 branch、HEAD、status、diff stat 和 pre-existing dirty files。

### Allowed Changes

- 无代码变更。
- 如实现窗口要求保存 scope lock evidence，只能写入当轮授权的 evidence 文件；不得把本文件自动升级为 active contract。

### Forbidden Changes

- 禁止修改 `apps/**`、`tests/**`、active docs、config、DB、migration、依赖和原始 fix plan。
- 禁止清理、回滚或格式化与本任务无关的已有 dirty files。
- 禁止启动服务、调用 provider、安装依赖或访问真实 DB。

### Checklist

- [ ] 运行 `git branch --show-current`，确认当前分支。
- [ ] 运行 `git rev-parse HEAD`，记录 HEAD。
- [ ] 运行 `git status --short --untracked-files=all`，标注 pre-existing dirty files。
- [ ] 运行 `git diff --stat`，记录当前 diff 基线。
- [ ] 读取 `AGENTS.md`、`DOCS_INDEX.md`、`BACKLOG.md`、`DELIVERY_PLAN.md` 和原始 fix plan。
- [ ] 确认 `AIFI-BE-008` 仍存在且状态允许进入后续工作。
- [ ] 读取 `API_SPEC.md`、`DATA_MODEL.md`、`PERSISTENCE_MODEL.md`、`PROMPT_SPEC.md`、`PROMPT_ASSET_SPEC.md`、`PROMPT_EVALUATION_SPEC.md`、`APPLICATION_FLOW_SPEC.md`、`SECURITY_PRIVACY.md` 中相关段落。
- [ ] 使用 CodeGraph 或 `rg` 复核 question generation、provider transport、AiTaskResult、AI task projection、frontend polling 和 tests 的现状。
- [ ] 明确当轮 allowed write list，默认不要超过当前 phase 的文件。
- [ ] 明确 DB 策略：fresh schema/reset/recreate/受控升级；不得默认已有本地库会自动获得新增列。

### Tests to Add / Update

| 测试文件 | 操作 | 断言 |
| --- | --- | --- |
| 无 | 不新增 | Phase 0 是 read-only gate |

### Verification Commands

- `git branch --show-current`
- `git rev-parse HEAD`
- `git status --short --untracked-files=all`
- `git diff --stat`
- `rg -n "AIFI-BE-008|AiTaskResultResponse|validation_errors|result_payload|provider_payload" docs apps tests`

### Done When

- 已形成当轮 scope lock，列出允许修改文件、禁止修改文件、验证命令和阻断条件。
- 已确认 `AIFI-BE-008` 是唯一任务挂靠入口。
- 已确认后续 phase 不依赖未授权 active docs 或 migration 改动。

### Rollback Strategy

Phase 0 不写代码；如发现范围不匹配，直接停止并更新 scope lock 结论，不做实现。

### Risks

- 当前工作区已有大量 unrelated dirty files，容易误把既有修改纳入本任务。
- 如果 active docs 已在其他窗口变化，后续字段和验收可能需要重新对齐。

### Future Goal Boundary

后续 goal 可以只包含 Phase 1，或将 Phase 1+2 合并为 contract/prompt slice；不得一次性把 Phase 1-6 全部无门禁执行。

## 6. Phase 1 - API/schema/frontend types 契约同步 `validation_errors`

### Goal

让 AI task result contract 明确暴露顶层 `validation_errors`，同时保持 additive nullable、`provider_payload: null` 和无题目生成 `result_payload` 的边界。

### Scope

- API active contract：`docs/02-design/API_SPEC.md`。
- Backend schema：`apps/api/app/schemas/ai_tasks.py`。
- Frontend type：`apps/web/src/entities/polish/model/types.ts`。
- Contract tests：优先覆盖 `AiTaskResultResponse` additive 字段与 forbidden payload。

### Allowed Changes

- 在授权实现窗口内修改 `API_SPEC.md`，登记 `AiTaskResultResponse.validation_errors`。
- 在 `AiTaskResultResponse` schema 中新增 nullable list 字段，默认 `None` 或空 list 需与现有序列化约定一致。
- 在 `PolishAiTaskResult` 中新增 `validation_errors?: string[] | null`。
- 更新 API/web contract tests。

### Forbidden Changes

- 禁止为 question generation 新增通用 `result_payload`。
- 禁止把 `validation_errors` 放进 `PolishFeedbackPayload` 作为题目生成失败的主要出口。
- 禁止让 `provider_payload` 从 `null` 变成 provider/raw/debug 对象。
- 禁止将 API_SPEC 之外的 inactive/refactor 文档当作合同来源。

### Checklist

- [ ] 在 `API_SPEC.md` 中为 `AiTaskResultResponse` 增加 `validation_errors` 字段，标明仅为用户安全错误摘要，不包含 raw provider 内容。
- [ ] 在 `apps/api/app/schemas/ai_tasks.py` 中增加同名 nullable 字段。
- [ ] 在 `apps/web/src/entities/polish/model/types.ts` 中同步 `PolishAiTaskResult`。
- [ ] 保持 `candidate_refs`、`suggestion_refs`、`validation_result_ref` 和 `provider_payload` 的现有兼容语义。
- [ ] 增加 contract test：缺省时兼容旧响应，失败时返回 `validation_errors`。
- [ ] 增加 forbidden test：响应中不出现 raw prompt/completion/provider payload。

### Tests to Add / Update

| 测试文件 | 操作 | 断言 |
| --- | --- | --- |
| `tests/api/test_ai_task_contracts.py` | 更新或新增 | `AiTaskResultResponse` 包含 `validation_errors`，字段 nullable/additive，`provider_payload` 仍为 `None` |
| `tests/api/test_polish_api.py` | 更新 | question task validation failure 的 result endpoint 返回 `validation_errors` |
| `tests/web/test_interview_actions.py` | 更新 source/type assertion | `PolishAiTaskResult` 类型包含 `validation_errors`，不要求 question `result_payload` |

### Verification Commands

- `PYTHONPATH=.:apps/api PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -p no:cacheprovider tests/api/test_ai_task_contracts.py tests/api/test_polish_api.py -q`
- `python3 -m pytest -p no:cacheprovider tests/web/test_interview_actions.py -q`
- `rg -n "AiTaskResultResponse|PolishAiTaskResult|validation_errors|result_payload|provider_payload" apps docs tests`

### Done When

- active API contract、backend schema 和 frontend type 对 `validation_errors` 达成一致。
- question generation failure 不依赖 `result_payload`。
- `provider_payload` 在 API response 中仍稳定为 `null`。

### Rollback Strategy

回滚 `API_SPEC.md`、`schemas/ai_tasks.py`、`types.ts` 与对应 tests 的字段改动；不触碰 DB 或 runtime 逻辑。

### Risks

- 若只改 schema 不改 projection，字段会一直为空，Phase 4 必须补齐。
- 若 frontend 过早依赖该字段而 API 未部署，会出现 undefined；类型应允许 nullable/optional。

### Future Goal Boundary

可单独作为 contract slice 提交；完成后再进入 provider request 修复，避免同时改 API、LLM、DB、UI 导致回归面过大。

## 7. Phase 2 - LLM compact provider request 输出契约修复

### Goal

让 compact provider request 明确告诉 LLM 每个关键输出字段的形状、取值和 evidence 约束，避免模型只看到 required fields 却不知道 `scoring_rubric` 等字段的详细契约。

### Scope

- `apps/api/app/application/polish/question_generation_prompts.py`
- `apps/api/app/infrastructure/llm/openai_compatible.py`
- prompt/provider boundary tests

### Allowed Changes

- 在 `build_question_provider_request()` 的 `expected_output_contract` 中加入 compact `field_contracts`。
- 明确字段契约：`question_text`、`question_kind`、`target_competency`、`scoring_rubric`、`evidence_refs`、`confidence`、`clarification_needed`、`missing_context`。
- 明确 `confidence` allowed values、`scoring_rubric` item shape、`clarification_needed` boolean、`missing_context` string array、`evidence_refs` 只能来自列出的 refs。
- 调整 generic provider system prompt，使其同时承认 `expected_output_contract`、`generation_policy` 和 `safety_rules_summary`，不再只要求不存在的 compact `evidence_bundle.prompt`/`output_schema`。

### Forbidden Changes

- 禁止发送完整 prompt asset、hidden rubric、raw resume、raw JD 或 provider debug payload。
- 禁止降低 `question_grounding_policy.py` 对 adjacent evidence 的阻断要求。
- 禁止在 provider 层把 invalid JSON 或 invalid schema 自动修复为 success。
- 禁止调用真实 provider 作为本 phase 验收条件。

### Checklist

- [ ] 设计 compact `field_contracts`，保持体积小、字段明确、可测试。
- [ ] `scoring_rubric` 要求 list，每项至少包含可评分标准和高质量回答信号；不得要求 raw hidden rubric。
- [ ] `evidence_refs` 明确只能引用 compact evidence bundle 中列出的 ref。
- [ ] adjacent/gap evidence 需要假设式或澄清式措辞，不能宣称候选人已完成相关经历。
- [ ] provider system prompt 与 compact request 字段名一致。
- [ ] 保持 `_QUESTION_PROVIDER_REQUEST_TOP_LEVEL_KEYS` 与测试同步。
- [ ] 增加 fake transport 或 source-scan 测试，证明 request 中包含 field contract 且不包含 forbidden raw payload。

### Tests to Add / Update

| 测试文件 | 操作 | 断言 |
| --- | --- | --- |
| `tests/api/test_polish_rag_non_claim.py` | 更新 | adjacent/gap evidence 仍要求假设式/澄清式输出，field contract 不削弱 grounding |
| `tests/api/test_openai_compatible_llm_transport.py` | 更新 | generic system prompt 引导模型遵守 compact `expected_output_contract` |
| `tests/api/test_provider_boundary.py` | 更新 | provider request 不包含 raw prompt/completion/provider payload 或敏感字段 |
| `tests/api/test_sensitive_payload_redaction.py` | 更新 | 新增 field contract 后 forbidden markers 仍不会泄漏 |

### Verification Commands

- `PYTHONPATH=.:apps/api PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -p no:cacheprovider tests/api/test_polish_rag_non_claim.py tests/api/test_openai_compatible_llm_transport.py tests/api/test_provider_boundary.py tests/api/test_sensitive_payload_redaction.py -q`
- `rg -n "expected_output_contract|field_contracts|scoring_rubric|confidence|clarification_needed|missing_context|evidence_refs" apps/api/app/application/polish apps/api/app/infrastructure/llm tests/api`
- `rg -n "provider_payload|raw_provider_payload|raw_prompt|raw_completion|api_key|secret" apps/api/app/application/polish apps/api/app/infrastructure/llm tests/api`

### Done When

- compact request 中的关键输出字段都有明确契约。
- provider system prompt 不再要求 compact request 中不存在的 `prompt` 或 `output_schema`。
- negative/fake provider tests 证明 invalid shape 仍走 validation failure，不写正式题目。

### Rollback Strategy

回滚 `question_generation_prompts.py` 与 `openai_compatible.py` 的 prompt/request 变更；保留 Phase 1 API contract 不受影响。

### Risks

- field contract 过长会增加 token 消耗；应使用 compact wording。
- provider prompt 改动可能影响 feedback 或其他 generic LLM task；测试必须覆盖 task_type 分支或确认 shared behavior 安全。

### Future Goal Boundary

可作为独立 prompt/provider slice；若 provider prompt 是 shared 入口，建议单独做 provider boundary review。

## 8. Phase 3 - `AiTaskResult` safe summary 持久化与兼容读取

### Goal

为 question generation 的 terminal failure status 持久化安全摘要，使 `validation_failed`、`source_unavailable`、`generation_failed`、`timed_out`、`cancelled` 都能被 result endpoint 查询到，同时兼容旧数据和 feedback 现有路径。

### Scope

- `apps/api/app/infrastructure/db/models/ai_task.py`
- `apps/api/app/infrastructure/db/repositories/polish.py`
- 必要时涉及 application use case 或 runtime handoff，但只允许在 AIFI-BE-008 scope 内。
- DB/tests 必须使用 fresh schema 或受控 test DB，不访问真实本地数据。

### Allowed Changes

- 为 `AiTaskResult` 增加 nullable safe summary 字段，例如 candidate refs、suggestion refs、validation errors、low confidence flags、source availability、evidence refs。
- 扩展既有 `_task_result_to_model()` 或同一 repository 内的 result upsert 路径；优先复用现有 helper，不创建并行 writer。
- 在 question task terminal failure 时写入 `AiTaskResult`，覆盖 `validation_failed`、`source_unavailable`、`generation_failed`、`timed_out`、`cancelled`，并确保正式 `Question` 不被创建。
- `succeeded`、`partial`、`low_confidence` 若已有正式/candidate result path，必须保持兼容，不得被伪造成 failure summary。
- 对旧 `AiTaskResult` 空字段和旧 feedback payload fallback 保持兼容。

### Forbidden Changes

- 禁止新增 Alembic/migration 系统。
- 禁止假设 `Base.metadata.create_all()` 会给已有本地 DB 表自动补列。
- 禁止把 raw provider payload、prompt、completion、system prompt、hidden rubric 写入新字段。
- 禁止把 validation failure 的 draft 修复成正式 question。
- 禁止让 frontend 或 provider 直接写 `AiTaskResult`。

### Checklist

- [ ] 选定 nullable JSON 字段命名，遵循现有 SQLAlchemy model 风格。
- [ ] 确认 SQLite/PostgreSQL test 环境下 JSON/text 字段行为一致。
- [ ] 为 question generation terminal failure result 增加 write path，覆盖 `validation_failed`、`source_unavailable`、`generation_failed`、`timed_out`、`cancelled`。
- [ ] 确认 `succeeded`、`partial`、`low_confidence` 的既有 result/candidate/formal 路径不被 failure summary 逻辑误伤。
- [ ] 复用 owner check 与 task authority；不得新增绕过 application service 的 direct path。
- [ ] `validation_errors` 只保存用户安全摘要，不保存 provider 原文。
- [ ] fresh schema tests 覆盖新增列。
- [ ] 旧数据 tests 覆盖 nullable 字段缺省读取。
- [ ] 文档或 release notes 记录：已有本地 DB 需要 reset/recreate 或另行受控升级。

### Tests to Add / Update

| 测试文件 | 操作 | 断言 |
| --- | --- | --- |
| `tests/api/test_polish_question_graph_persistence_handoff.py` | 更新 | validation failure 写 `AiTaskResult` safe summary，不写正式 `Question`；超时/取消 failure status 有安全摘要 |
| `tests/api/test_polish_question_graph_integration.py` | 更新 | terminal failure result 可被查询，candidate/formal 边界保持；`succeeded` / `partial` / `low_confidence` 不被 failure summary 误伤 |
| `tests/api/test_polish_api.py` | 更新 | result endpoint 对 question failure 返回 `validation_errors` 或 null-safe summary，覆盖 `validation_failed`、`source_unavailable`、`generation_failed`、`timed_out`、`cancelled` |
| `tests/api/test_db_schema_bootstrap.py` 或相邻 schema test | 新增/更新 | fresh schema 包含新增 nullable 字段；不声明 migration 自动补列 |

### Verification Commands

- `PYTHONPATH=.:apps/api PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -p no:cacheprovider tests/api/test_polish_question_graph_persistence_handoff.py tests/api/test_polish_question_graph_integration.py tests/api/test_polish_api.py -q`
- `rg -n "AiTaskResult|validation_errors|candidate_refs|suggestion_refs|source_availability|low_confidence|provider_payload|raw_prompt|raw_completion" apps/api/app/infrastructure apps/api/app/application tests/api`

### Done When

- question generation terminal failures 有持久化 safe summary，覆盖 `validation_failed`、`source_unavailable`、`generation_failed`、`timed_out`、`cancelled`。
- 旧 feedback result 读取不回归。
- 新字段为空时读取兼容。
- 任何失败路径都不创建正式 `Question`。

### Rollback Strategy

回滚 `AiTaskResult` model 字段、repository result writer 和相关 tests；若本地 test DB 已由 fresh schema 创建，可直接丢弃 test DB。生产/本地持久库升级需另行受控，不由 rollback 自动处理。

### Risks

- 对已有本地 DB，新增 model 字段不会自动出现，运行时可能报缺列；必须在实施说明中显式要求 fresh schema/reset/recreate 或受控升级。
- result writer 与 task status 更新如果非原子，可能出现 status terminal 但 result 缺失；repository tests 需要覆盖。

### Future Goal Boundary

建议单独作为 persistence slice；不要和 frontend 失败提示混在一个无门禁大改里。

## 9. Phase 4 - AI task result projection 与 feedback 回归保护

### Goal

让 result endpoint 从 `AiTaskResult` safe summary 投影 `validation_errors`，同时保留 feedback payload 的旧兼容读取，避免破坏 feedback 反馈卡片与现有 API 消费。

### Scope

- `apps/api/app/infrastructure/db/repositories/ai_tasks.py`
- `apps/api/app/schemas/ai_tasks.py`
- 必要时只做与 contract 一致的 `apps/api/app/schemas/polish.py` 兼容调整。

### Allowed Changes

- `_result_projection()` 新增顶层 `validation_errors`。
- projection 优先使用 `AiTaskResult` safe summary；仅对 feedback task 兼容 fallback 到 `Feedback.feedback_summary`。
- `_status_projection()` 和 `_result_projection()` 保持 `provider_payload: None`。
- `user_visible_status` 可按 task type 做更准确文案，但必须保持用户安全。

### Forbidden Changes

- 禁止让 question generation failure 依赖 `PolishFeedbackPayload`。
- 禁止将 `result_payload` 扩大为通用 AI task result 容器。
- 禁止把 feedback payload 的业务字段错误投影到 question generation task。
- 禁止通过 API 暴露 raw provider payload、trace raw body、prompt 或 completion。

### Checklist

- [ ] 梳理 `_status_projection()` 与 `_result_projection()` 字段来源优先级。
- [ ] 新增 safe summary extraction helper，处理 null/invalid legacy JSON。
- [ ] question generation result：对 `validation_failed`、`source_unavailable`、`generation_failed`、`timed_out`、`cancelled` 返回 `validation_errors` 或 null-safe summary、refs、`provider_payload: null`，不返回 question `result_payload`。
- [ ] feedback result：保留现有 `result_payload` 与 `feedback_payload` 兼容。
- [ ] user-visible copy 覆盖 `validation_failed`、`source_unavailable`、`generation_failed`、`timed_out`、`cancelled`。
- [ ] contract tests 同时覆盖 question failure 与 feedback success/failure；若 `tests/api/test_ai_task_contracts.py` 只覆盖 task contract/parser/transport request，则必须新增或更新真实 result route/projection 测试。

### Tests to Add / Update

| 测试文件 | 操作 | 断言 |
| --- | --- | --- |
| `tests/api/test_ai_task_contracts.py` 或专门 result API contract test | 更新/新增 | `GET /api/v1/ai-tasks/{ai_task_id}/result` 真实响应含顶层 `validation_errors`，`provider_payload` 为 `None`，question generation 不返回通用 `result_payload` |
| `tests/api/test_polish_feedback_payload_compatibility.py` | 更新 | feedback `result_payload` 兼容不被 question 改动破坏 |
| `tests/api/test_polish_api.py` | 更新 | question generation failure 不返回 feedback-shaped payload，覆盖 `validation_failed`、`source_unavailable`、`generation_failed`、`timed_out`、`cancelled` |
| `tests/api/test_sensitive_payload_redaction.py` | 更新 | projection 继续过滤 forbidden keys |

### Verification Commands

- `PYTHONPATH=.:apps/api PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -p no:cacheprovider tests/api/test_ai_task_contracts.py tests/api/test_polish_feedback_payload_compatibility.py tests/api/test_polish_api.py tests/api/test_sensitive_payload_redaction.py -q`
- `rg -n "result_payload|feedback_payload|validation_errors|provider_payload|_result_projection|_status_projection" apps/api/app/infrastructure/db/repositories apps/api/app/schemas tests/api`

### Done When

- question task result endpoint 可见 `validation_errors`。
- question task result endpoint 对 `validation_failed`、`source_unavailable`、`generation_failed`、`timed_out`、`cancelled` 的失败终态行为一致。
- feedback result payload 完整兼容。
- API response 无 provider/raw payload。

### Rollback Strategy

回滚 `ai_tasks.py` projection 和 schema/test 调整；Phase 3 的持久化 safe summary 可暂时保留但不对外投影，直到 contract 恢复。

### Risks

- 旧 feedback tests 可能依赖 `result_payload` shape；必须先锁定兼容断言。
- 如果 status endpoint 和 result endpoint 字段不一致，frontend 会出现分支判断差异；建议统一 helper。

### Future Goal Boundary

可与 Phase 1 合并为 API contract slice，也可在 Phase 3 之后单独执行；不得跳过 Phase 3 直接用 feedback payload 伪造 question failure。

## 10. Phase 5 - 前端当前页 polling 失败状态

### Goal

当前页面发起题目生成后，如果 polling 得到 `validation_failed`、`generation_failed`、`source_unavailable`、`timed_out` 或 `cancelled` 等失败终态，用户应看到明确错误；页面不得继续 focus 一个不存在的生成题目。

### Scope

- `apps/web/src/pages/interview/InterviewPage.tsx`
- `apps/web/src/entities/polish/model/types.ts`
- 必要时涉及 polish API client 的返回类型，但不得新增 persistent task recovery UI。

### Allowed Changes

- 在 `PolishAiTaskResult` 中读取 `validation_errors`。
- 在 `createCurrentNodeQuestion()` 和 `createFeedbackNextQuestion()` 中，polling 后先判断 terminal result 是否可生成 question。
- 对失败终态设置 `answerError` 或已有工作台失败状态，展示用户安全文案。
- 成功终态仍调用 `focusGeneratedQuestionTask()`，并刷新 session/candidate records。

### Forbidden Changes

- 禁止实现刷新后恢复失败提示。
- 禁止让 frontend 解析或使用 `provider_payload`。
- 禁止通过 `result_payload` 承载 question generation failure。
- 禁止新增 frontend execution target override。
- 禁止绕过 backend task authority 在前端生成或写入 question。

### Checklist

- [ ] 定义 helper，例如 `isPolishAiTaskFailedStatus()` 或复用现有状态映射，覆盖 `validation_failed`、`generation_failed`、`source_unavailable`、`timed_out`、`cancelled`。
- [ ] 定义用户安全错误文案，优先展示 `validation_errors` 的摘要，避免 raw provider 内容。
- [ ] `createCurrentNodeQuestion()` polling 返回失败时不调用 `focusGeneratedQuestionTask()`。
- [ ] `createFeedbackNextQuestion()` polling 返回失败时不调用 `focusGeneratedQuestionTask()`。
- [ ] success/partial/low_confidence 可继续按现有 candidate refs focus，但需确认 `candidate_refs` 存在。
- [ ] 保持 `loadSession()`/`loadCandidateRecords()` 的调用时机合理，避免失败后 UI stale。
- [ ] 更新 web tests，不再只断言 polling 后必定 focus。

### Tests to Add / Update

| 测试文件 | 操作 | 断言 |
| --- | --- | --- |
| `tests/web/test_interview_actions.py` | 更新 | question task polling 失败终态会设置错误文案，不调用 `focusGeneratedQuestionTask()` |
| `tests/web/test_interview_actions.py` | 更新 | success 终态仍调用 focus 并刷新 session/candidate records |
| `tests/web/test_interview_actions.py` | 更新 | frontend 不读取 `provider_payload`，不要求 question `result_payload` |

### Verification Commands

- `python3 -m pytest -p no:cacheprovider tests/web/test_interview_actions.py -q`
- `npm run typecheck --workspace apps/web`
- `rg -n "waitForPolishAiTaskFinalStatus|focusGeneratedQuestionTask|validation_failed|generation_failed|source_unavailable|provider_payload|result_payload" apps/web/src tests/web`

### Done When

- 当前页面能区分成功和失败终态。
- 失败终态用户可见，且不 focus 生成题目。
- success path 没有回归。

### Rollback Strategy

回滚 `InterviewPage.tsx` 与 frontend type/test 变更；backend API 字段可保留，不影响旧成功路径。

### Risks

- 当前 web tests 多为 source-scan，可能无法覆盖真实 DOM 行为；若后续 Playwright 环境可用，应补 UI flow test。
- 如果 backend result endpoint 暂时不返回 `validation_errors`，frontend 只能展示 status-based fallback copy。

### Future Goal Boundary

只做当前页面 polling failure；刷新后恢复、跨页面 task notification、persistent failed-task banner 应另开 goal。

## 11. Phase 6 - 联调测试、回归与 forbidden scan

### Goal

在不调用真实 provider、不启动服务、不访问真实 DB 的前提下，用 focused tests 和轻量 source scan 证明本修复满足 contract、最低敏感信息边界、持久化、前端可见性和回归要求。更严格的 system prompt、provider request/response、完整简历/JD 扫描后置到 release/security gate。

### Scope

- backend focused pytest
- web source/type tests
- lightweight forbidden payload source scan
- diff/status closeout

### Allowed Changes

- 补充或调整本任务范围内的 tests。
- 如发现 Phase 1-5 的实现缺口，只能回到对应 phase 修复授权文件。

### Forbidden Changes

- 禁止把真实 provider eval 作为必要验收。
- 禁止启动 `npm run dev`、`npm run dev:debug` 或本地服务。
- 禁止访问真实 DB 或执行 migration。
- 禁止把 unrelated dirty files 纳入提交。

### Checklist

- [ ] 运行 backend focused tests。
- [ ] 运行 web source/type tests。
- [ ] 执行轻量 forbidden scan：`provider_payload`、`raw_provider_payload`、`raw_prompt`、`raw_completion`、`api_key`、`secret` 不得出现在 API projection、持久化 summary 或 frontend usage 的新增路径中。
- [ ] 记录后置安全边界：`system_prompt`、provider request/response、完整简历/完整 JD/岗位全文等更完整扫描不阻塞本轮，但实现不得主动新增这些敏感内容的持久化、API 返回或前端展示。
- [ ] 执行 compatibility scan：`result_payload` 只服务 feedback 兼容，不服务 question generation failure。
- [ ] 执行 `git diff --stat` 和 `git status --short --untracked-files=all`。
- [ ] 输出新增/修改清单、未执行命令原因、残余风险和 rollback note。

### Tests to Add / Update

| 测试文件 | 操作 | 断言 |
| --- | --- | --- |
| `tests/api/test_ai_task_contracts.py` 或专门 result API contract test | 更新/新增 | 真实 result API contract、轻量 forbidden payload、validation errors |
| `tests/api/test_polish_api.py` | 更新 | question task result failure 可见，feedback 不回归；覆盖 `timed_out`、`cancelled` |
| `tests/api/test_polish_feedback_payload_compatibility.py` | 更新 | feedback `result_payload` 兼容 |
| `tests/api/test_polish_question_graph_integration.py` | 更新 | validation failure 不写正式 question |
| `tests/api/test_polish_question_graph_persistence_handoff.py` | 更新 | AiTaskResult safe summary 持久化 |
| `tests/api/test_openai_compatible_llm_transport.py` | 更新 | provider prompt 与 compact contract 一致 |
| `tests/domain/polish/test_question_grounding_policy.py` | 更新/保留 | domain grounding policy 不被 provider request 改动削弱 |
| `tests/api/test_polish_rag_non_claim.py` | 更新/保留 | 若该文件仍是真实 API 层回归入口，则 adjacent evidence safety 不回归 |
| `tests/web/test_interview_actions.py` | 更新 | frontend 当前页 failure visible、不 focus |

### Verification Commands

- `PYTHONPATH=.:apps/api PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -p no:cacheprovider tests/api/test_ai_task_contracts.py tests/api/test_polish_api.py tests/api/test_polish_feedback_payload_compatibility.py tests/api/test_polish_question_graph_integration.py tests/api/test_polish_question_graph_persistence_handoff.py tests/api/test_openai_compatible_llm_transport.py tests/domain/polish/test_question_grounding_policy.py tests/api/test_polish_rag_non_claim.py tests/api/test_provider_boundary.py tests/api/test_sensitive_payload_redaction.py -q`
- `python3 -m pytest -p no:cacheprovider tests/web/test_interview_actions.py -q`
- `npm run typecheck --workspace apps/web`
- `rg -n "provider_payload|raw_provider_payload|raw_prompt|raw_completion|api_key|secret" apps docs tests`
- `rg -n "result_payload|validation_errors|AiTaskResultResponse|PolishAiTaskResult|PolishFeedbackPayload" apps docs tests`
- `git diff --stat`
- `git status --short --untracked-files=all`

### Done When

- Focused backend tests、web tests/typecheck 和轻量 forbidden scans 通过，或阻断原因被明确记录。
- 只包含本任务授权文件变更。
- 用户可见失败、API contract、persistence summary、provider compact contract 与轻量 no raw payload 边界均有测试证据。

### Rollback Strategy

按 phase 逆序回滚：frontend failure branch、API projection、persistence fields/writer、provider contract、schema/types/API_SPEC。若 DB fresh schema 曾被创建，只丢弃测试 DB；已有本地库升级另行处理。

### Risks

- `npm run typecheck --workspace apps/web` 可能受当前 workspace 依赖状态和已有 unrelated package changes 影响。
- Source-scan tests 无法替代真实浏览器交互；后续 F7 应补 Playwright 或等价 E2E。

### Future Goal Boundary

Phase 6 应只做 verification 与最小修复，不再新增功能范围；若发现 refresh-after-reload 或 generic result payload 需求，应创建新任务并回写 BACKLOG。

## 12. 跨阶段验收矩阵

| 验收项 | Phase 1 | Phase 2 | Phase 3 | Phase 4 | Phase 5 | Phase 6 |
| --- | --- | --- | --- | --- | --- | --- |
| `validation_errors` 成为正式 API result 字段 | 必须 | 关联 | 关联 | 必须 | 消费 | 验证 |
| 不为 question generation 新增 `result_payload` | 必须 | 无关 | 关联 | 必须 | 必须 | 验证 |
| provider request 具备 compact field contract | 无关 | 必须 | 无关 | 无关 | 无关 | 验证 |
| `validation_failed` 不写正式 `Question` | 关联 | 必须 | 必须 | 关联 | 关联 | 验证 |
| `AiTaskResult` safe summary 可持久化 | 无关 | 无关 | 必须 | 消费 | 消费 | 验证 |
| feedback payload 兼容不回归 | 关联 | 无关 | 必须 | 必须 | 关联 | 验证 |
| 当前页 polling failure 可见 | 关联 | 无关 | 必须 | 必须 | 必须 | 验证 |
| 轻量敏感信息不泄漏 | 必须 | 必须 | 必须 | 必须 | 必须 | 验证 |
| 无 migration 系统新增 | 无关 | 无关 | 必须 | 关联 | 无关 | 验证 |
| 不启动服务/不调用真实 provider | 无关 | 必须 | 必须 | 必须 | 必须 | 必须 |

## 13. Deferred / Out of Scope

- 刷新页面后恢复题目生成失败可见性。
- 通用 AI task `result_payload` 平台化。
- 新增 Alembic、独立 migration 目录或生产 DB migration 流程。
- 真实 provider evaluation、线上模型质量评测或 prompt tuning。
- session detail 持久暴露 latest question generation task ref。
- frontend 全局 task notification、跨页面 task recovery 或历史失败任务中心。
- 将 `docs/refactor/**` 或 `docs/goals/**` 升级为 active source。
- 提交、推送、部署、启动服务或联调真实 provider。

## 14. 推荐执行顺序

1. Phase 0：重新建立 scope lock 和 dirty tree 基线。
2. Phase 1：先落 active API contract、backend schema 和 frontend type 的 `validation_errors`。
3. Phase 2：修复 compact provider request 与 generic system prompt 的字段契约错位。
4. Phase 3：增加 `AiTaskResult` safe summary 持久化，明确 fresh schema/reset 边界。
5. Phase 4：更新 result projection，并用 feedback compatibility tests 锁住旧行为。
6. Phase 5：实现当前页 polling failure UI，不处理 refresh-after-reload。
7. Phase 6：执行 focused tests、typecheck、轻量 forbidden scan 和 closeout。

## 15. 最小验证命令集合

后续实现完成后，至少执行以下命令；如某条命令因环境限制无法执行，必须在 closeout 中写明原因。

- `PYTHONPATH=.:apps/api PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -p no:cacheprovider tests/api/test_ai_task_contracts.py tests/api/test_polish_api.py tests/api/test_polish_feedback_payload_compatibility.py tests/api/test_polish_question_graph_integration.py tests/api/test_polish_question_graph_persistence_handoff.py tests/api/test_openai_compatible_llm_transport.py tests/domain/polish/test_question_grounding_policy.py tests/api/test_polish_rag_non_claim.py tests/api/test_provider_boundary.py tests/api/test_sensitive_payload_redaction.py -q`
- `python3 -m pytest -p no:cacheprovider tests/web/test_interview_actions.py -q`
- `npm run typecheck --workspace apps/web`
- `rg -n "provider_payload|raw_provider_payload|raw_prompt|raw_completion|api_key|secret" apps docs tests`
- `rg -n "result_payload|validation_errors|AiTaskResultResponse|PolishAiTaskResult|PolishFeedbackPayload" apps docs tests`
- `git diff --stat`
- `git status --short --untracked-files=all`

## 16. 风险与回滚总表

| 风险 | 影响 | 缓解 | 回滚 |
| --- | --- | --- | --- |
| Active API contract 未先更新 | 实现与文档不一致 | Phase 1 先改 `API_SPEC.md` 并加 contract tests | 回滚 API_SPEC/schema/type |
| compact provider request 字段契约仍不完整 | LLM 输出 invalid，失败频繁 | Phase 2 加 field contracts 和 fake provider tests | 回滚 prompt/request 变更 |
| 新增 DB 字段对旧本地库缺列 | 本地运行报错 | 明确 fresh schema/reset/recreate；不声称 migration 自动处理 | 回滚 model/repository；丢弃 test DB |
| projection 破坏 feedback `result_payload` | 反馈卡片或 API 兼容回归 | Phase 4 加 feedback compatibility tests | 回滚 projection helper |
| frontend failure branch 误伤 success focus | 成功生成后无法定位题目 | Phase 5 同时测 success 与 failure | 回滚 UI branch |
| 核心敏感内容泄漏 | 安全/隐私 blocker | 每 phase 做轻量 forbidden scan 和 redaction tests；更完整 security scan 后置 release/security gate | 立即回滚泄漏字段与投影 |
| unrelated dirty files 混入 | 提交不可审计 | Phase 0/6 status 与 diff stat，提交前只 stage 授权文件 | 不 stage unrelated files |

## 17. Goal 边界建议

| Goal | 建议范围 | 不包含 |
| --- | --- | --- |
| Goal A | Phase 1 contract/type 同步 | DB、provider、UI |
| Goal B | Phase 2 compact provider request 与 provider prompt 对齐 | API projection、frontend |
| Goal C | Phase 3 persistence safe summary | frontend failure UI、real provider |
| Goal D | Phase 4 API result projection 与 feedback 回归 | DB schema 设计、UI |
| Goal E | Phase 5 当前页 polling failure UI | refresh-after-reload、全局 task center |
| Goal F | Phase 6 tests/轻量 forbidden scan/closeout | 新功能 |

## 18. 最终门禁结论

结论：CONDITIONAL GO。

允许进入后续实现的条件：

1. 实现窗口重新执行 Phase 0，确认 `AIFI-BE-008`、branch/HEAD、dirty tree 和 allowed write list。
2. Phase 1 先同步 active API contract；本文件不能替代 `API_SPEC.md`。
3. Phase 3/4 必须覆盖全部失败终态：`validation_failed`、`source_unavailable`、`generation_failed`、`timed_out`、`cancelled`。
4. Phase 3 明确 fresh schema/reset/recreate 或受控升级策略；不得假设 `create_all()` 自动补齐已有表列。
5. Phase 4 必须用真实 result endpoint / projection contract tests 验证 question failure 与 feedback compatibility。
6. Phase 6 必须纳入 domain grounding policy 回归，证明 provider request 改动不削弱 adjacent evidence safety。
7. Phase 6 执行轻量 forbidden scan，至少覆盖 `provider_payload`、`raw_provider_payload`、`raw_prompt`、`raw_completion`、`api_key`、`secret`；更完整的 security scan 后置到 release/security gate。
8. 每个 phase 只改授权文件，且禁止引入 question generation 通用 `result_payload`。
9. Phase 6 focused tests、typecheck 和轻量 forbidden scans 通过，或将阻断原因记录为 NOT READY。

在以上条件满足前，不建议直接进入一口气实现；在条件满足后，可以按 Phase 1 到 Phase 6 小步推进。

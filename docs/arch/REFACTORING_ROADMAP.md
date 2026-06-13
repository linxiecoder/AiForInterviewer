---
title: REFACTORING_ROADMAP
type: refactoring-roadmap
status: draft-input
permalink: ai-for-interviewer/docs/arch/refactoring-roadmap
---

# AiForInterviewer 机制优先重构路线

本文是机制优先的重构输入，不是新的阶段计划或任务入口。正式执行必须拆成 `AIFI-*` 并登记到 `docs/03-delivery/BACKLOG.md`。

## 1. 路线结论

下一阶段不应按模块优先级推进，而应按控制能力优先级推进：

```text
Priority 1: 缺 control loop 的地方先补
Priority 2: prompt 结构和上下文边界重构
Priority 3: DDD / module cleanup
```

原因：当前系统真正的风险不是“模块不够多”，而是 LLM execution 的控制权分散。继续先拆模块，可能只会得到更漂亮的结构和同样分散的控制面。

## 2. 重构目标

目标不是“一次性 Agent 平台化”，而是让每次 LLM execution 都可解释、可追踪、可校验、可写回、可校准。

TO-BE 控制架构：

```text
User Action / API Command
  -> IntentController
  -> SkillInvocation
  -> ContextAssembler
  -> PromptAssetRuntime
  -> ToolGateway
  -> LlmTransport or DeterministicAnalyzer
  -> OutputValidator
  -> SkillResult
  -> StateUpdatePolicy
  -> NextActionPolicy
  -> Eval / Trace / Calibration
```

## 3. Priority 1：必须补 control loop

### 3.1 缺陷：Skill contract 没有成为执行入口

当前现象：

- `SkillDefinition` 有 `skill_id`、schema、tool refs、eval refs、failure semantics。
- catalog builder 能构造 registries。
- 但主路径不是统一从 `SkillInvocation` 进入。

应补控制能力：

- `SkillInvocation`
- `SkillResult`
- `SkillExecutor`
- `SkillRuntime`

成功口径：

- 至少 `skill.transcript.observe.v1` 和 `skill.polish.feedback.evaluate.v1` 通过同一 runtime 执行。
- SkillResult 必须包含 `status`、`trace_refs`、`validation_refs`、`low_confidence_flags`、`next_actions`。

### 3.2 缺陷：Tool side effect 只在 registry 层控制

当前现象：

- `ToolRegistry` 可阻止 direct repository / DB / raw prompt exposure。
- runtime 中还没有统一 ToolGateway 成为主路径。

应补控制能力：

- Tool call request/response；
- owner scope；
- redaction；
- side-effect policy；
- formal-write handoff guard；
- trace emission。

成功口径：

- SkillExecutor 不直接访问 repository/provider。
- 所有 read/external-call/candidate-write 都通过 ToolGateway。
- formal write 只能由 UseCase 授权后的 handoff 完成。

### 3.3 缺陷：State update 没有 Skill-level policy

当前现象：

- Polish feedback 会写 task / feedback。
- eval 会写 report。
- 前端会改变 UI 状态。
- 但没有统一规定每个 Skill 输出如何写回长期状态。

应补控制能力：

- `StateUpdatePolicy`；
- `SkillSessionState`；
- `CalibrationSnapshot`；
- `OutcomeFeedback`；
- writeback trace refs。

成功口径：

- 每个 Skill 定义 `state_update_policy`。
- `feedback.capture` 能写外部反馈 candidate。
- `calibration.detect_drift` 只输出 candidate，不自动改历史 score。

### 3.4 缺陷：Next action 不是 typed output

当前现象：

- `interview-coach-skill` 每个 workflow 都给 state-aware recommended next。
- 本地系统更多依赖前端按钮和局部 disabled reason。

应补控制能力：

- `NextActionPolicy`；
- typed `next_actions`；
- blocked reason；
- required refs；
- confidence。

成功口径：

- 后端 response 提供可渲染 next action。
- 前端不重新推断业务下一步，只呈现和触发。

## 4. Priority 2：prompt 结构重构

### 4.1 缺陷：Prompt shaping 局部强，全局弱

当前强点：

- `feedback_prompt_assets.py` 已做 context compression、forbidden data policy、output schema、provider compact prompt。

当前弱点：

- 这不是所有 LLM path 的公共机制。
- Prompt asset 与 Skill/eval/trace 的绑定不统一。

应补控制能力：

- `PromptAssetRuntime`；
- `ContextAssembler`；
- prompt asset registry；
- prompt_version trace；
- evidence policy；
- forbidden data scanner。

成功口径：

- feedback、question、transcript observation 至少三条路径都能暴露 prompt/context 控制元数据。
- `no full_resume/full_jd/provider_payload` 变成通用 guard。

### 4.2 缺陷：Reasoning boundary 分散

当前现象：

- rubric 在 docs；
- validation 在 Python；
- fallback 在 service；
- non-claim 在 tests；
- next step 在前端/文案。

应补控制能力：

- 每个 Skill 有 reasoning boundary spec；
- 每个 Skill 有 output validator；
- 每个 Skill 有 failure semantics；
- 每个 Skill 有 state update rules。

成功口径：

- `validation_failed`、`generation_failed`、`low_confidence` 语义一致。
- `partial` 不是 success。
- replay/fake/deterministic 不变成 provider quality。

### 4.3 缺陷：缺 feedback capture loop

当前现象：

- 系统能生成 feedback。
- 但 recruiter/interviewer feedback、real outcome、candidate correction 还没有成为统一输入回路。

应补控制能力：

- `skill.feedback.capture.v1`；
- external feedback evidence refs；
- outcome log；
- correction handling；
- meta-feedback handling；
- calibration trigger。

成功口径：

- external feedback 不直接变成 score；
- outcome 足够后触发 calibration candidate；
- user correction 可成为下一次评估上下文。

## 5. Priority 3：DDD / module cleanup

### 5.1 `PolishUseCases.create_question_task`

这不是因为文件长就必须拆，而是因为它承担太多 control flow：

- request validation；
- progress readiness；
- runtime policy resolution；
- follow-up context；
- completed focus refs；
- fallback；
- task persistence。

应拆出的不是“模块”，而是控制职责：

- progress selection control；
- runtime orchestration control；
- persistence handoff control；
- result mapping control。

### 5.2 Use case namespace 收敛

`app.usecases.polish` 与 `app.application.polish` 并存，会让执行入口不清楚。重构目的不是整理目录，而是让团队知道：

```text
用户命令从哪个 UseCase 进，
LLM execution 从哪个 SkillRuntime 进，
formal write 从哪个 handoff 进。
```

### 5.3 `InterviewPage.tsx`

前端拆分目标不是 UI 重做，而是降低 frontend 对 execution control 的占有：

- page container；
- API action hooks；
- derived view-model；
- panels；
- typed next action renderer。

后端能返回 next_actions 后，前端应减少业务推断。

## 6. 建议推进顺序

### Slice A：Skill runtime 最小闭环

控制目标：

- 定义 `SkillInvocation` / `SkillResult`。
- 建立 `SkillRuntime`。
- 包装 `skill.transcript.observe.v1`。
- 验证 deterministic Skill 不依赖 provider。

验证重点：

- `trace_refs` 存在；
- forbidden fields 不出现；
- no score / weakness / coaching in observation；
- existing transcript tests 不退化。

### Slice B：Feedback Skill 化

控制目标：

- 将 Polish feedback 迁入 `skill.polish.feedback.evaluate.v1`。
- 复用现有 prompt asset 和 validators。
- SkillResult 输出 `candidate_refs`、`low_confidence_flags`、`validation_refs`、`next_actions`。

验证重点：

- fake transport 仍失败；
- validation_failed 不成功；
- `score_result_id=None` 保留；
- provider prompt 不含 forbidden data。

### Slice C：Feedback capture loop

控制目标：

- 建立 `skill.feedback.capture.v1`。
- 区分 recruiter feedback、outcome、correction、post-session memory、meta-feedback。
- capture first, analyze later。

验证重点：

- external feedback 只成为 evidence/candidate；
- correction 不自动覆盖历史 score；
- outcome threshold 只触发 calibration recommendation。

### Slice D：Question path 控制拆分

控制目标：

- 拆 `create_question_task` 的控制职责。
- 形成 `skill.polish.question.generate.v1` 的入口。
- 保留 default-off / fallback 行为。

验证重点：

- existing polish question tests 不退化；
- runtime policy failure 仍是 validation failure；
- fallback path 可追踪；
- candidate/formal boundary 不变。

### Slice E：Next action 前后端收敛

控制目标：

- 后端 SkillResult 输出 typed `next_actions`。
- 前端增加通用 renderer。
- `InterviewPage.tsx` 减少业务推断。

验证重点：

- 按钮 disabled reason 与后端 blocked reason 一致；
- follow-up/regenerate/complete 仍可用；
- UI 不展示 hidden prompt/provider data。

### Slice F：Calibration candidate

控制目标：

- 建立 outcome-backed calibration candidate。
- 只在数据充分时 default-off 运行。
- 输出 drift candidate，不改正式分。

验证重点：

- replay eval 不宣称 outcome quality；
- drift 结论必须有 evidence refs；
- 不足数据返回 low confidence 或 policy_blocked。

## 7. 验证策略

每个 Slice 必须验证控制能力，而不是只验证功能可跑：

| 控制能力 | 验证方式 |
| --- | --- |
| intent routing | explicit API action -> expected skill_id |
| context control | forbidden data scanner + prompt asset snapshot |
| reasoning boundary | invalid input / insufficient context / no-score field tests |
| execution control | SkillRuntime contract tests |
| side-effect control | ToolGateway policy tests |
| validation | candidate/final schema tests |
| feedback loop | state update policy tests |
| non-claim | skeleton guard / eval non-claim tests |
| next action | typed response + frontend render tests |
| calibration | outcome threshold + drift candidate tests |

建议命令按实际 Slice 缩小，不在本文固化为任务。通常会涉及：

```bash
PYTHONPATH=.:apps/api .venv/bin/python -m pytest tests/api/test_architecture_boundaries.py
PYTHONPATH=.:apps/api .venv/bin/python -m pytest tests/api/test_skeleton_guard.py tests/api/test_capability_preservation_inventory.py
PYTHONPATH=.:apps/api .venv/bin/python -m pytest tests/api/test_composition_layer.py tests/api/test_transcript_analysis.py
PYTHONPATH=.:apps/api .venv/bin/python -m pytest tests/api/test_polish_feedback_generation_service.py tests/api/test_polish_feedback_pipeline_contract.py
npm run web:test
npm run eval:gate
npm run eval:gate:negative
```

## 8. 不应立即做

- 不做自由规划 Agent。
- 不一次性迁移全部参考 command。
- 不把 `coaching_state.md` 复制为产品状态。
- 不把 G-004 observation 升级成 scoring / weakness / coaching。
- 不把 replay / fixture / fake eval 写成真实模型质量。
- 不为整理结构而先大拆前端视觉。
- 不绕过 `BACKLOG.md` 新建执行任务体系。

## 9. Top 10 控制缺陷关闭口径

| 控制缺陷 | 关闭口径 |
| --- | --- |
| Execution controller 缺位 | 所有首批 Skill 经统一 SkillRuntime |
| Prompt context controller 不统一 | ContextAssembler 覆盖 feedback/question/transcript |
| Reasoning boundary 分散 | 每个 Skill 有 workflow / schema / failure semantics |
| Skill contract 与 runtime 脱节 | catalog definition 能映射 executor_ref |
| Tool side-effect control 停留 registry | runtime ToolGateway 执行 policy |
| Next action 不是一等输出 | SkillResult 返回 typed next_actions |
| Outcome calibration 缺失 | calibration candidate 有 outcome threshold |
| Long-term coaching state 缺标准模型 | SkillSessionState / CalibrationSnapshot 建立 |
| Partial capability 被复杂度掩盖 | skeleton / capability / eval non-claim guard 保留 |
| Frontend 承担过多 execution control | 后端 next_actions 驱动 UI |

## 10. 路线结论

机制优先重构的核心判断：

```text
先补 LLM execution control loop，
再收敛 prompt structure，
最后整理 DDD / module shape。
```

如果顺序反过来，系统会继续拥有复杂结构，却仍然无法回答最关键的问题：

```text
谁控制这次 LLM 执行？
谁控制上下文？
谁控制推理边界？
谁控制反馈闭环？
```

本路线的最终目标是让 AiForInterviewer 从“局部可用的复杂系统”变成“可控的 LLM execution system”。

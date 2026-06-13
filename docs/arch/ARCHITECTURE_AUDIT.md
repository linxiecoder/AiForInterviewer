---
title: ARCHITECTURE_AUDIT
type: architecture-audit
status: draft-input
permalink: ai-for-interviewer/docs/arch/architecture-audit
---

# AiForInterviewer 控制能力架构审计

本文是机制级架构输入，不是新的计划、任务入口或实现事实。正式执行必须进入 `docs/03-implementation/BACKLOG.md`、`docs/03-implementation/DELIVERY_PLAN.md` 或 ADR。

## 1. 审计结论

当前系统不是“失败的复杂系统”。它是一个具备强工程边界、强局部路径、弱统一 LLM execution control 的半完成系统。

它仍然有效，原因是 Polish 主路径形成了足够多的局部闭环：

- API route 能把用户操作映射到 Polish session / question / answer / feedback。
- `PolishFeedbackApplicationService` 有 answer/session/question 校验、幂等锁、失败落库和 candidate handoff。
- `FeedbackGenerationService` 有 context normalize、prompt asset、provider gate、candidate validation、final validation、trace / low confidence metadata。
- `feedback_prompt_assets.py` 压缩上下文，禁止 full resume / full JD / provider payload，并要求 evidence refs。
- `CompositionService` 能按 mode 隔离 G-003 feedback 与 G-004 analysis。
- skeleton guard、capability inventory、eval gate 阻止把 skeleton / replay / fake / partial 宣称为 implemented。

它的薄弱点不是模块名，而是控制能力分散：

```text
UseCase 控制一部分 execution flow
Service 控制一部分 prompt shaping
Runtime facade 控制一部分 trace / replay
Tests 控制 non-claim
Frontend 控制大量 next action
Docs 控制设计意图
```

这导致系统看起来工程化，但 LLM 的核心执行控制面没有统一。

## 2. 本地系统的有效性机制

### 2.1 局部闭环足以支撑主路径

当前用户可见主路径集中在 Polish workbench，而不是 skeleton 状态的通用 Interview / Pressure / Reviews。

Polish feedback 的局部闭环如下：

```text
create_feedback_task
  -> owner/session/answer/question validation
  -> existing generated feedback reuse
  -> FeedbackGenerationContext
  -> FeedbackGenerationService.generate
  -> prompt asset + provider boundary
  -> candidate payload validation
  -> final payload validation
  -> planned handoff
  -> PolishPersistResultUseCase
  -> task status + feedback storage
```

这个 loop 不完美，但足够完整：失败会变成 `generation_failed` / `validation_failed`，成功会带 `candidate_refs`、`trace_refs`、`score_result_id=None` 等边界信息。

### 2.2 失败被显式表达，而不是伪装成功

系统里的 robustness 不是来自“什么都能成功”，而是来自 fail-closed：

- no transport -> `llm_transport_unavailable`
- fake transport -> `fake_transport_not_runtime_provider`
- candidate invalid -> validation errors
- final payload invalid -> validation errors
- replay / fixture -> non-claim
- skeleton route prefix -> 不登记为 implemented route

这些机制让半成品系统在不完美情况下仍然可控。

### 2.3 Prompt shaping 局部有效

`build_feedback_prompt_asset()` 不是普通字符串拼接。它把 context 压缩为：

- current question；
- structured answer；
- same-question / recent turns；
- evidence items；
- focus target；
- compact job/resume/progress snapshot；
- output schema；
- safety / validation rules；
- provider compact prompt。

这解释了为什么 feedback path 比纯 LLM wrapper 更稳定：prompt context 被裁剪、命名、约束和验证。

### 2.4 测试守卫承担了系统自我认知

`test_skeleton_guard.py` 和 `test_capability_preservation_inventory.py` 不只是测试。它们在控制系统里承担“能力事实校准器”：

- route prefix 不等于能力实现；
- DB model 不等于产品流程；
- fake / replay / deterministic eval 不等于 real provider quality；
- partial / skeleton / default-off 不能升级成 implemented；
- Polish aggregate 仍保持 partial，直到 API + UseCase + repository/model + tests + frontend/user path + runtime quality evidence 全部独立证明。

这类 guard 是当前系统没崩的重要原因。

## 3. 控制能力地图

| 控制面 | 当前位置 | 成熟度 | 判断 |
| --- | --- | --- | --- |
| Intent routing | API route + frontend actions +部分 runtime policy | 中 | 显式操作可控，自然语言 intent router 不统一 |
| Execution flow | `PolishUseCases`、focused application services、runtime facade | 中低 | feedback 较强，question 入口过重 |
| Prompt context | `feedback_prompt_assets.py`、question prompt builders | 中 | 局部强，缺通用 ContextAssembler |
| Reasoning boundary | prompt rules、validators、forbidden fields、tests | 中 | 多点分散，未上升为 Skill primitive |
| Tool side effect | `ToolRegistry` contract、runtime side-effect guard | 中低 | registry 强，runtime ToolGateway 不完整 |
| Feedback loop | task status、feedback payload、trace、eval report | 中 | 缺 outcome calibration / long-term Skill state |
| Non-claim control | skeleton guard、capability inventory、eval non-claims | 高 | 是系统可信度核心 |
| Next action | frontend state +局部后端字段 | 低 | 缺 typed state-aware `next_actions` |

## 4. DDD 结构的真实价值与局限

### 4.1 真实价值

DDD 分层没有白做。它提供了：

- domain 不依赖 FastAPI / SQLAlchemy / infrastructure；
- API 不直接依赖 provider payload；
- application 层能集中 owner-scope、idempotency、transaction handoff；
- repository / DB model 与业务用例隔离；
- architecture boundary tests 可持续阻止层间侵蚀。

这些是 `interview-coach-skill` 不具备的产品化硬边界。

### 4.2 局限

DDD 解决“业务规则和技术实现怎么分层”，不自动解决“LLM 如何被控制”。

当前的主要问题：

- `PolishUseCases.create_question_task` 仍把 progress selection、runtime policy、follow-up context、fallback、candidate persistence 混在一条大路径里。
- `SkillDefinition` 是 catalog contract，不是统一执行入口。
- `ToolRegistry` 能描述 side-effect policy，但主路径还没有统一 ToolGateway。
- `InterviewPage.tsx` 仍承担大量 execution state 和 next-action 判断。
- docs 中的 Prompt / Skill / Agent 设计比 runtime 更理想，容易形成 design-time / runtime mismatch。

## 5. 半完成模块为什么不是立即失败

半完成模块包括：

- `apps/api/app/application/interviews/use_cases.py` 返回 `interview_skeleton`。
- `apps/api/app/domain/interviews/services.py` 为空服务。
- `apps/api/app/application/pressure/use_cases.py` 为 skeleton。
- Agent/Skill catalog 有大量 contract-only / default-off / replay 语义。

它们没有导致主路径崩溃，因为：

- 用户当前主路径不依赖这些 skeleton；
- route snapshot 和 skeleton guard 阻止它们被展示为 implemented；
- active docs 与 capability registry 保留 non-claim 状态；
- fallback / validation 把不可用能力转为可解释失败。

半完成不是失败，误宣称半完成才是失败。

## 6. Over-engineering vs Under-engineering

### 6.1 Over-engineering

这些区域存在“结构领先于控制闭环”的风险：

- Agent catalog / Skill catalog：定义丰富，但不是所有业务路径默认通过其执行。
- LangGraph / multi-agent design：有 runtime foundation 和 replay gate，但不能等同于产品级多智能体。
- 部分 F4/F5 文档：契约完整，但与 runtime execution 之间仍有落差。
- Frontend workbench：单文件吸收太多状态，扩大控制面而非收敛控制面。

### 6.2 Under-engineering

这些区域反而工程化不足：

- 缺统一 `SkillInvocation` / `SkillResult`。
- 缺全局 `ContextAssembler`。
- 缺运行时 `ToolGateway`。
- 缺 outcome calibration / `SkillSessionState`。
- 缺 typed `next_actions`。

也就是说，系统不是“工程太多”或“工程太少”，而是工程投放点错位：结构治理强于执行控制。

## 7. 看起来复杂但闭环不足的结构

| 结构 | 看起来像什么 | 实际闭环状态 | 风险 |
| --- | --- | --- | --- |
| `SkillDefinition` | Skill 系统 | contract metadata | 被误当成可执行 Skill runtime |
| Agent L5 registries | 多智能体平台 | contract-only / no runtime execution | 被误当成 product agent |
| Phase9 eval | 质量认证 | replay / fixture regression gate | 被误当成真实 provider quality |
| `CompositionService` | orchestration layer | 轻量 mode router | 被误当成完整 Skill composition |
| `Pressure` / `Reviews` | 产品模块 | skeleton / prefix-only | 被误当成已实现能力 |

## 8. 当前系统为什么没崩

系统没崩的机制解释：

1. 主用户路径集中，不需要所有设计模块同时完成。
2. Polish feedback 的 prompt/validation/persistence 闭环足够强。
3. LLM 的 probabilistic robustness 能在 prompt 足够明确时补齐小缺口。
4. 错误状态明确，不把 provider/fake/validation failure 包装成成功。
5. 测试和文档 guard 持续压制 capability overclaim。
6. 前端虽然重，但给用户提供了可操作路径，减少自由对话漂移。
7. DDD 边界阻止了底层依赖污染 domain / application。

## 9. 当前系统真正需要的 TO-BE

不是新的 module architecture，而是 control architecture：

```text
IntentController
  -> SkillInvocation
  -> ContextAssembler
  -> PromptAssetRuntime
  -> ToolGateway
  -> LlmTransport / DeterministicAnalyzer
  -> OutputValidator
  -> SkillResult
  -> StateUpdatePolicy
  -> NextActionPolicy
  -> Eval / Trace / Calibration
```

DDD 仍保留，但它服务于控制架构：

- UseCase 负责权限、状态、事务、formal write。
- SkillRuntime 负责 LLM execution。
- ToolGateway 负责副作用和授权上下文。
- PromptAssetRuntime 负责版本化 prompt shaping。
- Eval / Trace / Calibration 负责质量闭环。

## 10. 架构审计结论

本地系统并不应该“抛弃 DDD 学 Skill”。正确方向是：

```text
保留 DDD 的安全边界，
把 Skill 作为 LLM execution control primitive，
让所有 prompt / tool / validation / trace / feedback loop 通过 SkillRuntime 汇聚。
```

复杂工程系统弱于轻量 Skill 的地方，不是代码质量，而是 LLM 控制权被稀释。下一阶段必须优先补 control loop，再做模块 cleanup。

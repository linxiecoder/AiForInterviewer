---
title: AI_SKILL_ADOPTION_PLAN
type: architecture-plan
status: draft-input
permalink: ai-for-interviewer/docs/arch/ai-skill-adoption-plan
---

# AI Skill 控制架构采用方案

本文是机制优先的采用方案，不是新的阶段计划或任务入口。正式实施必须拆成 `AIFI-*` 并登记到 `docs/03-implementation/BACKLOG.md`。

## 1. 采用目标

目标不是把 `interview-coach-skill` 的 Markdown 文件搬进仓库，也不是再增加一层抽象。目标是把当前分散在 UseCase、Service、PromptBuilder、Runtime、Tests、Frontend 中的 LLM 控制权，收敛成统一 Skill-first execution control loop。

目标形态：

```text
User / API Command
  -> IntentController
  -> SkillInvocation
  -> SkillRuntime
  -> ContextAssembler
  -> PromptAssetRuntime
  -> ToolGateway
  -> OutputValidator
  -> SkillResult
  -> StateUpdatePolicy
  -> NextActionPolicy
```

DDD 不被替代。DDD 负责安全边界、事务、权限、formal write；SkillRuntime 负责 LLM execution 的意图、上下文、推理、验证和反馈。

## 2. Skill 的本质定义

Skill 不是模块，不是 service，也不是 agent catalog row。Skill 是：

```text
Context transformer
  + Intent-to-execution bridge
  + Prompt execution primitive
```

它必须回答：

- 当前用户意图是什么？
- 执行这个意图需要哪些上下文？
- 哪些上下文禁止进入 prompt？
- 哪个 prompt asset / reference 应该加载？
- 模型可推理到哪里，哪里必须停？
- 输出 schema 是什么？
- 失败状态怎么表达？
- trace 和 evidence 怎么记录？
- 结果如何写回 state？
- 下一步怎么推荐？

如果一个“Skill”只描述 `skill_id`、schema 和 tool refs，却不控制这些问题，它只是 contract metadata。

## 3. Skill vs UseCase vs Service

| 对象 | 核心职责 | 不该承担 |
| --- | --- | --- |
| UseCase | 权限、idempotency、业务状态转换、事务、formal write handoff | 拼大 prompt、决定 rubric、直接调用 provider |
| Service | 封装稳定业务规则或技术能力 | 维护跨轮 coaching state、决定全局 next action |
| Skill | 控制 LLM execution：intent、context、prompt、reasoning boundary、validation、feedback loop | 直接访问 repository、绕过 UseCase 写 formal 对象 |
| Tool | 受权限和 side-effect policy 约束的原子能力 | 自行决定业务目标或输出解释 |
| Agent | 在受控范围内选择 / 排序 Skill | 自由访问 DB、provider、filesystem 或隐藏 prompt |

这一区分的核心是：UseCase 是 application boundary；Skill 是 cognition boundary。

## 4. TO-BE Control Architecture

### 4.1 IntentController

负责把用户操作或自然语言输入映射为 Skill：

```text
explicit API action
  -> explicit Skill
natural-language command
  -> shadow mode routing
multi-step intent
  -> controlled sequence
```

第一阶段只允许显式 API action，不做自由自然语言规划。自然语言 routing 可先 shadow 记录，不影响用户结果。

### 4.2 ContextAssembler

负责压缩和净化上下文：

- owner scoped；
- evidence refs only；
- bounded answer text / structured answer；
- compact resume/job/progress snapshot；
- no full resume；
- no full JD；
- no raw prompt；
- no provider payload；
- no secrets；
- no hidden scoring rule exposure。

它要把 `feedback_prompt_assets.py` 的局部经验升级为通用机制。

### 4.3 PromptAssetRuntime

负责加载版本化 prompt asset：

- `prompt_asset_id`；
- `prompt_version`；
- `schema_id` / `schema_version`；
- `developer_constraints`；
- `output_schema`；
- `evidence_policy`；
- `refusal_and_low_confidence_policy`；
- `eval_suite_refs`。

Prompt 不再是 service 内部字符串，而是 Skill 可追踪资产。

### 4.4 ToolGateway

ToolGateway 是运行时 side-effect controller：

| side effect | 允许场景 |
| --- | --- |
| `read_only` | 读取受控上下文、evidence、state snapshot |
| `external_call` | LLM / embedding / search 等外部调用 |
| `candidate_write` | 写 candidate / trace / validation result |
| `formal_write_handoff_only` | 只在 UseCase 授权后正式写入 |
| `forbidden` | 任何 runtime 都不能调用 |

`ToolRegistry` 已能描述很多 policy，但 ToolGateway 必须在 runtime 执行这些 policy。

### 4.5 OutputValidator

每个 SkillResult 必须区分：

- `succeeded`
- `partial`
- `low_confidence`
- `validation_failed`
- `generation_failed`
- `policy_blocked`
- `cancelled`

不得把 `validation_failed_partial_result` 报成 success；不得把 fake/replay 证据报成 live provider quality。

### 4.6 StateUpdatePolicy

Skill 输出必须定义写回策略：

- 什么写入 session；
- 什么写入 progress state；
- 什么写入 feedback candidate；
- 什么写入 calibration snapshot；
- 什么只写 trace；
- 什么需要 HITL confirmation；
- 什么禁止写 formal。

这对应 `interview-coach-skill` 的 state update triggers，但在本地系统中要 typed / owner scoped / transactional。

### 4.7 NextActionPolicy

每个 SkillResult 应产生 typed `next_actions`：

```text
next_actions:
  - action_id
  - label
  - reason
  - required_refs
  - confidence
  - blocked_reason
```

前端只负责渲染，不应重新推断 coaching next step。

## 5. 最小契约

建议引入以下最小概念。路径可在正式任务中确认，本文只定义机制边界：

```python
from dataclasses import dataclass
from typing import Any, Mapping, Protocol

@dataclass(frozen=True)
class SkillInvocation:
    skill_id: str
    skill_version: str
    owner_id: str
    actor_id: str
    input_refs: tuple[str, ...]
    context_refs: tuple[str, ...]
    idempotency_key: str
    runtime_policy: Mapping[str, Any]

@dataclass(frozen=True)
class SkillResult:
    status: str
    output_refs: tuple[str, ...]
    candidate_refs: tuple[str, ...]
    trace_refs: tuple[str, ...]
    validation_refs: tuple[str, ...]
    low_confidence_flags: tuple[str, ...]
    next_actions: tuple[Mapping[str, Any], ...]
    state_update_refs: tuple[str, ...]
    metadata: Mapping[str, Any]

class SkillExecutor(Protocol):
    def execute(self, invocation: SkillInvocation) -> SkillResult:
        ...
```

这不是为了引入更多类，而是为了把控制权显式化。

## 6. 第一批 Skill 选择

### 6.1 `skill.transcript.observe.v1`

原因：

- deterministic；
- G-004 observation boundary 清晰；
- 不依赖 LLM provider；
- 已有 composition tests；
- 适合作为 SkillRuntime 的低风险试点。

控制要求：

- 只输出 observation；
- 不输出 `score`、`weakness`、`ranking`、`coaching`；
- 保留 `schema_id=transcript_analysis_v1`；
- 失败必须显式 `validation_failed` 或 `partial`。

### 6.2 `skill.polish.feedback.evaluate.v1`

原因：

- 用户可见主路径；
- 当前已有 prompt asset、provider gate、candidate validation、final validation；
- 可以把局部强闭环升级为通用 Skill primitive；
- 适合验证 `trace_refs`、`low_confidence_flags`、`score_result_id=None`、candidate/formal boundary。

控制要求：

- UseCase 创建 `SkillInvocation`；
- SkillRuntime 构造 prompt asset；
- OutputValidator 校验 candidate 和 final payload；
- StateUpdatePolicy 只写 candidate / feedback summary，不写 formal score；
- NextActionPolicy 输出可渲染下一步。

### 6.3 `skill.feedback.capture.v1`

原因：

- 参考系统里 `feedback` 的高价值是 capture-vs-analysis separation；
- 本地系统需要外部 recruiter/interviewer feedback 与 outcome 入口；
- 这能防止把用户反馈直接升级成评分事实。

控制要求：

- classify input as recruiter feedback / outcome / correction / memory / meta-feedback；
- record evidence and confidence；
- 不做深度 scoring；
- 只触发后续 `analyze` / `progress` / calibration recommendation。

### 6.4 `skill.calibration.detect_drift.v1`

原因：

- 当前 eval gate 强在 replay / contract regression，不证明 coaching outcome quality；
- 参考系统 calibration engine 提供真实 outcome-backed control loop；
- 适合 default-off / candidate-only。

控制要求：

- 只有足够 outcome data 才运行；
- 输出 drift candidate；
- 不自动改历史 score；
- 所有结论必须有 outcome / feedback evidence refs。

## 7. 为什么不先做自由 Agent

自由 Agent 最大风险是夺走 control flow：

```text
Agent decides skills
Agent decides tools
Agent decides context
Agent decides writeback
Agent decides next action
```

在没有统一 SkillRuntime / ToolGateway / StateUpdatePolicy 前，自由 Agent 会放大 context dilution 和 side-effect 风险。第一阶段必须走显式 Skill pipeline；自然语言 routing 只能 shadow。

## 8. Prompt 重构原则

Prompt 不是文案，而是 execution control surface。

每个 prompt asset 必须满足：

- 输入上下文有 schema；
- 上下文经过压缩；
- forbidden data 明确；
- evidence refs 可追溯；
- output schema 明确；
- validation policy 明确；
- low confidence policy 明确；
- eval suite refs 明确；
- prompt_version 进入 trace；
- provider payload 不落用户可见输出。

这比“优化提示词”更重要。目标是 prompt 结构可控。

## 9. Feedback loop 设计

本地系统需要三层反馈：

### 9.1 Runtime feedback

- validation errors；
- generation failures；
- provider status；
- trace refs；
- low confidence flags。

### 9.2 User workflow feedback

- user correction；
- recruiter/interviewer feedback；
- outcome update；
- remembered interview detail；
- coaching meta-feedback。

### 9.3 Outcome calibration

- internal score vs real outcome；
- external feedback contradiction；
- scoring drift；
- stale intelligence decay；
- success pattern extraction。

没有第 2、3 层，系统只能证明“能生成”，不能证明“越用越准”。

## 10. 与现有设计文档的关系

现有文档不是废弃，而是重新定位：

| 现有对象 | 新定位 |
| --- | --- |
| `PROMPT_SPEC.md` | Prompt / AI contract registry 的上游 |
| `PROMPT_ASSET_SPEC.md` | PromptAssetRuntime 的治理来源 |
| `PROMPT_EVALUATION_SPEC.md` | Skill eval / regression / negative control 来源 |
| `SKILL_MODEL_SPEC.md` | Skill taxonomy 来源，不等于 executable runtime |
| `APPLICATION_FLOW_SPEC.md` | UseCase 与 SkillRuntime 协作边界来源 |
| Agent contracts | 可复用 metadata，但需执行协议承接 |
| Phase9 eval | regression gate，不等于 live provider quality |

## 11. Skill-first vs DDD-first 采用结论

### DDD-first 的失败模式

```text
先建模块
  -> 再写 service
  -> 再塞 prompt
  -> 再补 tests
  -> 最后发现用户意图和 feedback loop 没被统一控制
```

### Skill-first 的失败模式

```text
先写 prompt skill
  -> 用户体验强
  -> 但没有 owner scope / schema / audit / transaction
  -> 难以产品化
```

### 本地正确路线

```text
Skill-first control loop
  + DDD application boundary
  + ToolGateway side-effect control
  + typed persistence
  + eval / trace / calibration
```

## 12. 采用优先级

### Priority 1：补 control loop

- `SkillInvocation` / `SkillResult`
- `SkillRuntime`
- `ToolGateway`
- `StateUpdatePolicy`
- `NextActionPolicy`

### Priority 2：重构 prompt 结构

- 通用 PromptAssetRuntime；
- prompt asset 与 schema / eval / trace 绑定；
- ContextAssembler 统一上下文压缩；
- feedback / transcript / question 三条路径逐步迁入。

### Priority 3：清理 DDD / module

- 拆 `PolishUseCases.create_question_task`；
- 收敛 use case namespace；
- 拆前端 controller / hooks / view-model；
- 保留 skeleton / partial / contract-only guard。

## 13. 采用完成口径

不能只看“有 Skill 文件”或“有 registry”。至少满足：

- 至少两个用户可见路径通过 `SkillRuntime` 执行；
- 每个 SkillResult 都有 trace、validation、low confidence、next action；
- Tool side effect 在 runtime 被执行；
- prompt asset version 可追溯；
- eval gate 能按 `skill_id` 定位 regression；
- external feedback / outcome 能进入 calibration candidate；
- front-end 不再重新推断后端已经知道的 next action；
- docs 不把 shadow/default-off/contract-only 写成 implemented。

## 14. 最终判断

Skill-first architecture 不是轻量玩具；它是 LLM 系统的控制优先架构。DDD-first architecture 不是错误；它是产品化保护层。

AiForInterviewer 应该采用：

```text
Skill-first execution control
  guarded by DDD-first system boundaries
```

这样才能从“复杂但局部有效”演进为“复杂且可控”。

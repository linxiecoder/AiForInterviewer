---
title: MECHANISM_ANALYSIS
type: architecture-mechanism-analysis
status: draft-input
permalink: ai-for-interviewer/docs/arch/mechanism-analysis
---

# AiForInterviewer LLM 执行机制分析

本文是架构机制分析输入，不是新的阶段计划、任务入口或 ADR。正式执行必须回写到 `docs/03-implementation/BACKLOG.md`、`docs/03-implementation/DELIVERY_PLAN.md` 或 ADR。

## 1. 核心结论

轻量 `interview-coach-skill` 之所以有效，不是因为它有更好的模块结构，而是因为它把 LLM 系统最关键的控制变量直接放在 prompt 执行面：

- 它控制 intent routing：用户输入被压缩成命令或命令序列。
- 它控制 context loading：顶层规则只保留稳定约束，深度 reference 按需读取。
- 它控制 reasoning boundary：每个 command 有明确步骤、rubric、质量门和输出蓝图。
- 它控制 feedback loop：`coaching_state.md`、state update triggers、outcome calibration 和 recommended next step 构成闭环。

本地系统更工程化，具备 DDD 分层、API、repository、LLM boundary、Agent contract、eval gate 和 trace 机制。它在当前不完美状态下仍然有效，是因为 Polish 主路径、feedback generation、prompt asset、validation、persistence handoff 和 replay/negative gate 形成了局部闭环。它的问题不是“没有架构”，而是很多控制能力没有被统一成公共 LLM execution primitive。

一句话：

```text
Skill-first 系统赢在控制面短、上下文密度高、反馈闭环贴近用户目标；
DDD-first 系统赢在边界、持久化、安全和可维护性，但若没有统一 execution control loop，会把 LLM 的关键控制权散落到多个层。
```

## 2. 证据范围

本轮读取范围：

- 本地仓库：`/home/administrator/code/AiForInterviewer`
- 当前分支：`feature/composition-layer`
- 当前 HEAD：`68fb489f289faff8f5e271fd63e6b5b22be090a6`
- 本地参考副本：`/tmp/interview-coach-skill-phase2-20260611`
- 参考 commit：`634a8dd8689e0420c21e5f0c8ae3cfa9e1a7ab7e`
- 参考远端：<https://github.com/noamseg/interview-coach-skill>

关键本地证据：

- `apps/api/app/application/polish/use_cases.py`
- `apps/api/app/application/polish/feedback_application_service.py`
- `apps/api/app/application/polish/feedback_generation_service.py`
- `apps/api/app/application/polish/feedback_prompt_assets.py`
- `apps/api/app/application/composition/service.py`
- `apps/api/app/application/agents/contracts/__init__.py`
- `apps/api/app/application/agents/registry/__init__.py`
- `apps/api/app/application/agents/runtime/__init__.py`
- `tests/api/test_skeleton_guard.py`
- `tests/api/test_capability_preservation_inventory.py`
- `tests/api/test_composition_layer.py`
- `scripts/evals/run_eval_gate.py`
- `evals/suites/phase9.json`
- `apps/web/src/pages/interview/InterviewPage.tsx`

关键参考证据：

- `SKILL.md`
- `references/mode-detection.md`
- `references/coaching-state-schema.md`
- `references/state-update-triggers.md`
- `references/commands/analyze.md`
- `references/commands/feedback.md`
- `references/calibration-engine.md`

## 3. 系统动力学解释

LLM execution system 的有效性主要由四个变量决定：

| 控制变量 | 作用 | 缺失后的典型症状 |
| --- | --- | --- |
| Intent control | 把用户输入映射到可执行模式 | 对话看似智能，但下一步漂移 |
| Context control | 决定哪些信息进入模型上下文 | context dilution、prompt pollution、遗漏关键约束 |
| Reasoning boundary | 决定模型在何处推理、何处停止 | 过度分析、越权写入、把猜测写成事实 |
| Feedback control | 把输出、用户反馈和 outcome 写回状态 | 每次都像新会话，无法校准 |

传统工程系统倾向先设计 module boundary；LLM 系统还必须设计 control boundary。前者解决“代码放哪里”，后者解决“模型在什么约束下推理、执行、校准”。

本地系统的 DDD 分层保护了很多安全边界，例如 domain 不直接依赖 framework / infrastructure，API 不暴露 provider payload，candidate/formal 边界被测试守住。但 LLM 的真正执行控制仍分散在 `PolishUseCases`、`FeedbackGenerationService`、prompt asset、runtime facade、eval gate 和前端交互状态中。

`interview-coach-skill` 没有这些工程层，却把 control boundary 直接写成操作协议。对单用户、本地 agent host 来说，这反而减少了控制路径长度。

## 4. Q1：为什么 `interview-coach-skill` 能 work？

### 4.1 它如何压缩复杂性

它把复杂系统压缩成三层：

```text
SKILL.md
  -> command routing
  -> command/reference files loaded on demand
  -> coaching_state.md state update
```

这相当于把 Product、Workflow、Prompt、Memory、Feedback 都放进一个可被 LLM 直接执行的控制面。它不需要在 API、UseCase、Service、Repository、Graph、Frontend 状态之间传递意图，因此意图损耗低。

复杂度没有消失，而是被转移成：

- priority hierarchy；
- command registry；
- mode detection；
- per-command step sequence；
- state update triggers；
- calibration rules；
- output blueprint。

这些都是 LLM 可以直接遵守的 prompt-level control primitives。

### 4.2 它如何避免工程系统常见失败点

它避开了这些失败点：

- 没有多层 DTO / entity / schema 映射，所以不会在层间丢失 coaching intent。
- 没有异步 task / graph / repository 装配，所以不会出现 task succeeded 但用户目标未闭环。
- 没有分散 prompt builder，所以核心控制词不会散落到多个 service。
- 没有过早平台化 Skill registry，所以不会出现 catalog 很完整但 executor 不存在。
- 没有前端状态机，所以 recommended next step 直接由 coaching state 决定。

代价也明确：缺少权限、并发、审计、schema enforcement、multi-user isolation、可复现测试和正式数据治理。因此它适合个人 agent skill，不适合直接作为多用户产品后端。

### 4.3 核心控制面是什么

核心控制面是 `SKILL.md`，不是目录结构。

它控制：

- Session start：先读状态，再给 prescriptive recommendation。
- Session end / mid-session save：重大 workflow 后写回状态。
- Command execution：显式命令优先，未显式时按 mode detection 路由。
- File routing：每个 command 只加载必要 reference。
- Output：用固定 blueprint 和 command schema 控制输出。
- Evidence：要求 evidence-tagged claims 和 confidence labels。
- Feedback：每个产生数据的 command 都必须更新状态。

这是一种 prompt-native control plane。

### 4.4 它依赖结构还是 prompt shaping

它主要依赖 prompt shaping。文件结构只是让 prompt shaping 可维护：

- `references/commands/*.md` 是 command-local reasoning boundary。
- `references/cross-cutting.md` 是共享策略。
- `references/calibration-engine.md` 是反馈控制规则。
- `coaching_state.md` 是长期状态。

结构服务于 prompt 执行，不是反过来。

## 5. Q2：为什么复杂 DDD / Agent 系统可能反而更弱？

### 5.1 Context dilution

DDD / Agent 系统常把同一个用户目标拆进多层：

```text
router -> command schema -> use case -> service -> prompt builder -> runtime -> validator -> persistence -> frontend
```

每一层都可能只看到局部字段，不再看到完整用户意图。对普通业务系统这是解耦；对 LLM 系统可能变成 context dilution。模型最终看到的是被切碎后的上下文，缺少用户真正目标、历史状态和当前 coaching strategy。

### 5.2 Tool / Skill fragmentation

如果 Skill 只是 catalog metadata，Tool 只是 contract definition，Agent 只是 future runtime，那么系统看起来完整，但控制流仍由散落的 use case 和服务函数承担。

本地证据里 `SkillDefinition` 明确是 “no runtime execution” 的 catalog contract，Agent L5 registry 也标注为 “without runtime execution”。这类结构有治理价值，但不能替代执行闭环。

### 5.3 Control flow loss

多层系统容易让“谁决定下一步”变得不清楚：

- API 决定 endpoint；
- UseCase 决定业务状态；
- Service 决定 prompt；
- Runtime 决定 graph；
- Frontend 决定按钮和 next action；
- Eval 决定是否 gate。

如果没有统一 controller，execution flow 就会由多个局部 if/else 拼出来。系统可运行，但难以解释“为什么这一步是现在最该做的事”。

### 5.4 Prompt context pollution

复杂系统常把 prompt 作为 service 内部实现细节。这样会带来两个问题：

- 业务状态、provider hygiene、schema、rubric、fallback 混在一个 builder 里。
- 为了“保险”塞入越来越多上下文，导致模型注意力被稀释。

本地 feedback prompt asset 已经开始压缩上下文，例如限定 answer text、禁止 full resume / full JD / provider payload、要求 evidence refs。但这还没有成为统一 Skill runtime 的默认行为。

## 6. Q3：为什么半成品系统仍然能工作？

### 6.1 LLM system 的 probabilistic robustness

LLM 不是传统确定性函数。只要输入目标、上下文、约束和输出格式大体正确，它有概率在不完美链路中补齐缺口：

- prompt 不完美时，模型可根据语义惯性生成合理结果；
- context 有缺口时，模型可用领域常识填空；
- schema 宽松时，validator / fallback 可拦截部分错误；
- UI 没有完美状态机时，用户仍可通过下一次交互修正。

这叫 probabilistic robustness。它能让系统在半完成状态下有用，但也会掩盖控制缺陷。

### 6.2 Partial completeness 不等于 failure

本地系统的很多能力是局部完整：

- Polish session / question / answer / feedback / report 路径可用；
- feedback generation 有 provider gate、candidate validation、final validation、trace refs；
- composition layer 能按 mode 隔离 G-003 feedback 与 G-004 analysis；
- eval gate 有 replay / fixture / negative control；
- skeleton guard 阻止把 prefix-only 或 placeholder 误报成 implemented。

这些局部闭环足以支撑产品主路径。它们不是“完整 Agent 系统”，但可以形成可用体验。

### 6.3 Runtime vs design-time mismatch

设计文档里的 Agent runtime、Prompt contract、Skill model 比当前 runtime 更理想化。代码里的真实控制面集中在 Polish path 和 feedback path。这个 mismatch 不会立刻导致失败，因为用户实际走的是已闭合的 Polish 路径，而不是所有 design-time 架构。

失败风险在于：如果文档把 design-time 架构当成 runtime fact，后续改造会围绕不存在的控制点展开。

### 6.4 Implicit fallback mechanisms

本地系统存在大量隐式 fallback：

- 无 LLM transport 时返回 `llm_transport_unavailable`，不伪装成功。
- fake transport 被拒绝为 runtime provider。
- candidate payload 校验失败会落 `validation_failed` / `generation_failed`。
- replay / fixture eval 明确 non-claim。
- skeleton guard 防止把 route prefix、DB model、disabled nav 当成实现。

这些 fallback 让系统“不完美但不崩”。它们是控制系统里的阻尼器。

## 7. 结构 vs 机制对比

| 维度 | `interview-coach-skill` | 本地系统 |
| --- | --- | --- |
| 架构复杂度 | 低：instruction package + reference files + state file | 高：DDD / Application / Domain / Infrastructure / Agent contracts / eval / frontend |
| 控制方式 | `SKILL.md` 直接控制 session、command、context、output、feedback | 控制分散在 UseCase、Service、runtime facade、prompt builder、tests、frontend |
| prompt shaping | 强：priority hierarchy、file routing、command schema、rubric、next step 都是 prompt-native | 局部强：feedback prompt asset 已压缩上下文；全局未统一 |
| execution loop | 明确但软：输入 -> mode/command -> reference -> response -> state update | 局部硬：Polish feedback 有 validation/persistence；Agent/Skill 全局 loop 未统一 |
| feedback loop | 强：state update triggers、Outcome Log、Calibration State、Meta-Check | 局部：feedback、trace、eval、candidate refs；缺统一 outcome calibration |
| 控制能力位置 | LLM host 的 prompt 执行面 | Python service / tests / docs / frontend 多点分散 |
| 成功条件 | 用户意图被正确路由，状态持续更新 | 局部路径闭环，guard 不误报，fallback fail closed |
| 主要风险 | 无强权限、无并发控制、无 typed persistence | context dilution、control flow loss、contract-only 误宣称 |

## 8. Skill 本质分析

Skill 本质不是传统模块。它更接近：

```text
Context transformer
  + Intent-to-execution bridge
  + Prompt execution primitive
```

### 8.1 Skill vs UseCase

UseCase 关注应用命令：

- 权限；
- idempotency；
- 状态转换；
- transaction boundary；
- repository handoff。

Skill 关注 LLM 执行：

- 当前意图如何转成任务；
- 哪些上下文进入 prompt；
- 哪些 reference 必须读取；
- 推理边界在哪里；
- 输出如何校验；
- 失败如何表达；
- 下一步如何推荐；
- 哪些状态要写回。

UseCase 是 application boundary；Skill 是 cognition boundary。

### 8.2 Skill vs Service

Service 封装业务或技术操作。Skill 封装的是“面向模型的执行协议”。一个 Skill 可以使用多个 Service，但不能退化成 Service。否则它会失去 prompt shaping 和 feedback control。

### 8.3 Skill 为什么更适合 LLM 系统

LLM 的主要失败不是函数调用失败，而是意图漂移、上下文污染、推理越界和反馈缺失。Skill 正好控制这些变量：

- 它减少模型要同时处理的上下文；
- 它把 workflow 和 rubric 放在模型能看到的位置；
- 它用输出蓝图约束生成；
- 它把用户反馈和 outcome 写回长期状态。

工程系统若只提供 module boundary，容易在层间丢失“为什么现在要这样回答用户”。

## 9. 控制能力差距分析

| 控制问题 | `interview-coach-skill` | 本地系统当前状态 | 差距 |
| --- | --- | --- | --- |
| 谁控制 execution flow | `SKILL.md` + mode detection + command sequence | UseCase / service / frontend / runtime 多点控制 | 缺统一 Skill controller |
| 谁控制 prompt context | command file routing + state schema | prompt asset 局部控制，其他路径分散 | 缺全局 context assembler |
| 谁控制 reasoning boundary | per-command workflow 和 rubric | validator / service / docs 局部控制 | 缺 Skill-level reasoning boundary |
| 谁控制 feedback loop | state update triggers + calibration engine | task status / feedback payload / eval report | 缺 outcome calibration 与 state update policy |
| 谁控制 next step | state-aware recommended next | 前端按钮 + 后端 task response 局部推断 | 缺 typed `next_actions` |
| 谁控制 non-claim | prompt rules + confidence labels | skeleton guard / capability inventory / eval non-claims | 本地更强，但未统一到 Skill result |

## 10. Top 10 控制缺陷

这不是任务清单，而是控制缺陷清单：

1. **Execution controller 缺位**：没有统一对象决定一次 LLM run 从 intent 到 result 的完整闭环。
2. **Prompt context controller 不统一**：feedback path 有 context compression，其他路径没有统一 ContextAssembler。
3. **Reasoning boundary 分散**：rubric、schema、fallback、validation 分布在 service、docs、tests 中。
4. **Skill contract 与 runtime 脱节**：`SkillDefinition` 有治理信息，但不是默认执行入口。
5. **Tool side-effect control 停留在 registry 层**：`ToolRegistry` 会阻止 direct exposure，但 runtime ToolGateway 尚未成为主路径。
6. **Next action 不是一等输出**：用户下一步仍由前端状态和局部文案推导，缺 typed state-aware recommendation。
7. **Outcome calibration 缺失**：eval gate 能证明 regression，不证明真实 coaching quality 或 outcome predictive accuracy。
8. **Long-term coaching state 缺标准模型**：session/progress/feedback 有状态，但没有统一 SkillSessionState / CalibrationSnapshot。
9. **Partial capability 容易被结构复杂度掩盖**：Agent/Pressure/Reviews/Scoring 等 skeleton 或 contract-only 容易被误读成实现。
10. **Frontend 承担过多 execution control**：`InterviewPage.tsx` 超大，按钮、API 调用、状态解释和视图耦合，削弱后端控制闭环。

## 11. TO-BE：Control Architecture

目标不是先画更多模块，而是建立控制架构：

```text
User Input
  -> Intent Controller
      - explicit command
      - mode detection
      - multi-step sequence
  -> Context Controller
      - state snapshot
      - evidence refs
      - prompt asset refs
      - redaction policy
  -> Reasoning Controller
      - skill workflow
      - rubric
      - stop rules
      - confidence policy
  -> Execution Controller
      - deterministic analyzer
      - LLM transport
      - ToolGateway
      - retry / timeout
  -> Validation Controller
      - candidate schema
      - final schema
      - forbidden field scanner
      - failure semantics
  -> Feedback Controller
      - trace refs
      - low_confidence_flags
      - next_actions
      - state update triggers
      - calibration update
```

这套架构可落地为 `SkillRuntime`，但核心不是类名，而是每一层都有明确控制权。

## 12. 机制优先级

### Priority 1：必须补 control loop

- 统一 `SkillInvocation` / `SkillResult`，让每次 LLM execution 都产生 trace、validation、low confidence、next action。
- 建立 `SkillRuntime` 作为 execution controller，而不是让 UseCase 直接拼 prompt 或调 provider。
- 建立 `ToolGateway`，把 read-only、external-call、candidate-write、formal-write-handoff-only 变成运行时策略。
- 建立 `SkillStateUpdatePolicy`，规定哪些输出写回 session/progress/calibration/candidate。

### Priority 2：关键 prompt 结构重构

- 把 feedback path 的 prompt asset 模式升级为通用 PromptAssetRuntime。
- 每个 Skill 只加载必要 reference/context，避免全局 prompt 污染。
- 每个 prompt asset 必须绑定 schema、eval refs、forbidden data policy、evidence policy。
- 把 `next_actions` 从文案升级为 typed output。

### Priority 3：DDD / module cleanup

- 拆 `PolishUseCases.create_question_task`，降低单点控制复杂度。
- 收敛 `app.usecases.polish` 与 `app.application.polish` 双命名空间。
- 拆 `InterviewPage.tsx` 的 controller/hook/view-model。
- 保留 skeleton / partial / contract-only 守卫，不把结构 cleanup 写成能力完成。

## 13. Skill-first vs DDD-first 结论

Skill-first 不是反工程化。它的优势是先抓住 LLM 系统的控制变量，然后再用工程边界固化这些变量。

DDD-first 如果先追求层次完整，容易得到：

```text
好看的模块边界 + 分散的 prompt 控制 + 不完整的反馈闭环
```

Skill-first 如果缺少工程治理，容易得到：

```text
强体验闭环 + 弱权限/审计/并发/复现
```

AiForInterviewer 的正确方向不是二选一，而是：

```text
Skill-first control architecture
  protected by DDD boundaries
  executed through typed UseCase / ToolGateway / Repository / Eval gates
```

即：先让 Skill 成为 LLM execution 的控制原语，再让 DDD 负责把这个原语安全、可测、可持久化地产品化。

---
title: INTERVIEW_COACH_INSIGHTS
type: reference-analysis
status: draft-input
permalink: ai-for-interviewer/docs/arch/interview-coach-insights
---

# `interview-coach-skill` 机制分析

本文分析参考项目 <https://github.com/noamseg/interview-coach-skill>。本地只读副本为 `/tmp/interview-coach-skill-phase2-20260611`，当前读取 commit 为 `634a8dd8689e0420c21e5f0c8ae3cfa9e1a7ab7e`。本文不是要求复制该仓库结构，而是提取它为什么有效的执行机制。

## 1. 结论

`interview-coach-skill` 不是传统工程系统，但它像产品，因为它直接控制了产品体验最关键的闭环：

```text
用户输入
  -> mode / command detection
  -> command-specific reference loading
  -> rubric / workflow guided reasoning
  -> schema-like output
  -> coaching_state.md update
  -> state-aware recommended next step
```

它没有后端、数据库、CI、typed validator、权限模型，也没有真正 Tool runtime。它能 outperform 复杂系统，是因为它在 LLM host 内部保持了高密度控制面：所有让模型“知道现在该干什么、用什么上下文、输出什么、写回什么”的信息，都离模型推理非常近。

## 2. 它如何被执行

执行方式不是启动服务，而是把 `SKILL.md` 放到 agent 宿主可读的高优先级指令位置：

- Claude Code：按 README 指引可将 `SKILL.md` 改名为 `CLAUDE.md`。
- OpenAI Codex：按 README 指引可将 `SKILL.md` 改名为 `AGENTS.md`。
- 用户说 `kickoff` 或其他自然语言请求后，宿主 LLM 按 `SKILL.md` 执行。

因此它的 runtime 是宿主 agent；它的 control plane 是 instruction files；它的 persistence 是 `coaching_state.md`。

这解释了它为什么轻：它不实现运行时，而是劫持宿主 LLM 的运行时。

## 3. 核心控制面

### 3.1 `SKILL.md` 是操作系统，不是 README

`SKILL.md` 控制：

- priority hierarchy；
- session start protocol；
- session end / mid-session save；
- state migration and staleness check；
- command registry；
- file routing；
- mode detection；
- global rubric；
- evidence sourcing；
- response blueprints；
- coaching voice。

这不是普通说明文档，而是 LLM execution policy。

### 3.2 Mode detection 是 intent router

`references/mode-detection.md` 用优先级把输入映射到 command：

- explicit command 优先；
- transcript -> `analyze`；
- feedback / outcome / correction -> `feedback`；
- post-interview -> `debrief`；
- company + JD -> `prep`；
- JD analysis -> `decode`；
- offer -> `negotiate`；
- otherwise ask `kickoff` or `help`。

它还定义 multi-step intent，例如“prepare me for interview at company”会走 research -> prep -> concerns -> hype 的序列。

这就是轻量 Skill 的 execution flow controller。

### 3.3 File routing 是 context controller

`SKILL.md` 没有要求每次加载全量知识。它规定：

- all commands 读取当前 command file 和 cross-cutting；
- `analyze` 额外读取 transcript、rubrics、examples、calibration；
- `practice` / `mock` 额外读取 role drills；
- `progress` 额外读取 calibration；
- Level 5 额外读取 challenge protocol。

这避免了复杂工程系统常见的 context pollution。它让上下文按任务进入，而不是把所有产品规则塞进一次 prompt。

### 3.4 Command files 是 reasoning boundary

`references/commands/analyze.md` 定义了完整推理边界：

```text
cold start
  -> minimal missing context
  -> self-assessment first
  -> independent scoring
  -> transcript format detection
  -> quality gate
  -> format-aware parsing
  -> score
  -> compare self-assessment
  -> signal reading
  -> triage decision tree
  -> active coaching strategy update
  -> interview intelligence update
  -> output schema
  -> recommended next step
```

这比“调用一个分析服务”更贴合 LLM，因为模型在推理时能直接看到过程约束。

### 3.5 `coaching_state.md` 是 feedback loop

`references/coaching-state-schema.md` 定义了长期状态：

- Profile；
- Resume Analysis；
- Storybank；
- Score History；
- Outcome Log；
- Interview Intelligence；
- Drill Progression；
- Active Coaching Strategy；
- Calibration State；
- Interview Loops；
- Meta-Check Log；
- Session Log；
- Coaching Notes。

`references/state-update-triggers.md` 定义每个 command 完成后写回什么。也就是说，每次输出都不是孤立 response，而是对未来执行上下文的更新。

## 4. 输入 -> 推理 -> 输出 -> 反馈闭环

### 4.1 输入

输入不是简单文本，而是被 mode detection 转成 intent：

- 明确 command；
- transcript；
- feedback；
- outcome；
- company/JD；
- practice intent；
- progress intent。

这一步减少了模型“猜用户到底要什么”的自由度。

### 4.2 推理

推理由 command file 限制：

- step sequence；
- scoring dimensions；
- quality gate；
- triage priority；
- exception handling；
- confidence labels；
- directness level。

这比“给一个大 prompt 让模型自由分析”稳定。

### 4.3 输出

输出用 blueprints / schemas 约束：

- `Scorecard`；
- `Triage Decision`；
- `What Is Working`；
- `Top 3 Gaps To Close`；
- `Priority Move`；
- `Confidence`；
- `Recommended Next Step`。

它把回答变成可预测的产品界面，即使没有真正 UI。

### 4.4 反馈

反馈通过三条路径写回：

- explicit feedback command：捕获 recruiter/interviewer feedback、outcome、correction、post-session memory、meta-feedback；
- state update triggers：每个 command 更新相关 state section；
- calibration engine：真实 outcome 与 internal score 对比，识别 scoring drift。

这就是它像产品的关键。

## 5. 为什么简单结构可以 outperform 复杂系统

### 5.1 控制面更短

复杂系统中一次回答可能穿过 API、UseCase、Service、PromptBuilder、Runtime、Validator、Repository、Frontend。每层都可能丢失 intent。`interview-coach-skill` 的路径短：

```text
user intent -> command protocol -> reference context -> answer -> state update
```

控制面短，意图损耗少。

### 5.2 Context 密度更高

它只加载当前 command 需要的 reference。上下文里每段信息都直接影响当前推理。复杂系统如果把长期文档、schema、runtime metadata、历史状态混在一起，context density 会下降。

### 5.3 它把 feedback 当成系统核心

`feedback.md` 明确 capture first, analyze later。它不把用户提供的外部反馈立刻升级成评分事实，而是保存成高信号输入，后续在 `progress` / calibration 中使用。这是一种非常强的 reasoning boundary。

### 5.4 它的产品循环非常明确

每个 command 都回答：

- 当前用户处在什么状态？
- 这次该做什么？
- 输出后状态怎么变？
- 下一步是什么？

很多复杂系统只回答“这个 endpoint 返回什么”。

## 6. 它依赖 prompt shaping，而不是结构

目录结构只是维护 prompt shaping 的方式。真正有用的是这些原语：

| Prompt primitive | 作用 |
| --- | --- |
| Priority hierarchy | 决定冲突时保什么 |
| Mode detection | 把自然语言压成命令 |
| File routing | 控制上下文预算 |
| Command workflow | 限定推理步骤 |
| Quality gate | 降低坏输入造成的误判 |
| Rubric anchors | 稳定评分尺度 |
| Confidence labels | 控制不确定性表达 |
| State update triggers | 形成长期记忆 |
| Recommended next | 把输出连接到下一次执行 |
| Calibration engine | 用 outcome 修正内部评估 |

如果只复制 `references/` 目录，而不复制这些控制原语，迁移就会失败。

## 7. 参考系统的局限

它的成功边界必须说清楚：

| 局限 | 为什么重要 | 在 AiForInterviewer 中的替代 |
| --- | --- | --- |
| 无 typed schema enforcement | 输出靠 LLM 自律 | `OutputValidator` + final schema |
| 无权限和 owner scope | 单用户本地可接受，产品不可接受 | UseCase + ToolGateway |
| 无并发控制 | `coaching_state.md` 易冲突 | DB-backed state + transaction |
| 无 provider boundary | 宿主模型就是 runtime | LLM transport boundary |
| 无 test / CI | 难以回归验证 | pytest + eval gate + negative control |
| 无 formal/candidate boundary | 状态文件可直接变事实 | candidate/formal handoff |
| 无 observability | 难以复盘运行 | trace refs + eval report |

所以它不能被直接产品化。可迁移的是机制，不是运行方式。

## 8. 可迁移机制

| Reference mechanism | 本地落点 | 迁移原则 |
| --- | --- | --- |
| `SKILL.md` priority hierarchy | `SkillRuntimePolicy` | 放进 runtime policy，不散落到 service |
| mode detection | `IntentController` / `SkillRouter` | 先显式模式，后 shadow natural-language |
| file routing | `PromptAssetRuntime` | 按 Skill 加载 prompt assets |
| command workflows | `SkillDefinition.executor_ref` + workflow spec | 不止 catalog，要可执行 |
| `coaching_state.md` | `SkillSessionState` | typed DB/read model，不复制 Markdown |
| state update triggers | `SkillStateUpdatePolicy` | 所有 SkillResult 都有写回策略 |
| evidence/confidence discipline | `evidence_refs` + `low_confidence_flags` | 结构化输出，不只文案 |
| calibration engine | `SkillCalibrationSnapshot` / eval suite | outcome-backed，不等于 replay gate |
| recommended next | typed `next_actions` | 前端只渲染，不重新推断 |
| feedback capture vs analysis | G-003/G-004 separation | capture 不自动升级为 score/weakness |

## 9. 不能迁移的东西

不建议直接迁移：

- `coaching_state.md` 作为产品状态源；
- Markdown command 作为后端 runtime；
- 全量 23 个 command 一次性导入；
- 自由规划 Agent 自动选择任意 Skill；
- 把 reference 的 scoring / weakness / coaching 字段直接塞进 G-004 observation；
- 把 README 的产品承诺当成本地实现事实。

## 10. 对本地系统的启发

本地系统最应该吸收的不是“更多 Agent”，而是“更短控制面”：

```text
Intent -> Skill -> Context -> Prompt -> Validate -> Result -> State Update -> Next Action
```

第一批可迁移对象：

- `skill.transcript.observe.v1`：从 G-004 deterministic observation 开始。
- `skill.polish.feedback.evaluate.v1`：吸收 evidence/confidence/next action。
- `skill.feedback.capture.v1`：专门捕获 external feedback / correction / outcome，避免过早分析。
- `skill.calibration.detect_drift.v1`：等 outcome 数据足够时 default-off / candidate-only。

## 11. 为什么它“不是工程系统但却像产品”

产品感不来自微服务、数据库或 UI，而来自连续体验：

- 你回来时，它知道上次做了什么。
- 你输入自然语言，它能路由到正确工作流。
- 它输出的不只是答案，还有下一步。
- 它吸收反馈并改变之后的建议。
- 它承认不确定性，并用 outcome 校准自己。

这就是 LLM 产品的最小闭环。复杂工程系统如果没有这条闭环，即使模块更多，也会显得像一组功能而不是一个教练。

## 12. 结论

`interview-coach-skill` 的成功不是反架构，而是提示我们：LLM 系统的第一架构是控制架构。

本地系统要超越它，不能只补更多 DDD 模块。必须把 `interview-coach-skill` 的 prompt-native control primitives 产品化：

```text
Skill-first control loop
  + typed schema
  + owner scope
  + ToolGateway
  + persistence
  + eval / trace / calibration
```

这样才能同时得到轻量 Skill 的高意图对齐，以及工程系统的安全、可测和可维护。

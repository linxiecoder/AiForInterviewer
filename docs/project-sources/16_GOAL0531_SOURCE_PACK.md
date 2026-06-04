---
title: 16_GOAL0531_SOURCE_PACK
type: note
permalink: ai-for-interviewer/docs/project-sources/16-goal0531-source-pack
---

# 16 GOAL0531 Source Pack

## Purpose

保存 GOAL0531 的核心意图摘要。

注意：

GOAL0531 不是唯一可信源。
它是重构目标和阶段意图源。
当前实现事实必须以 GitHub main 代码为准。

## Source of Truth Placement

GOAL0531 的优先级：

1. 用户明确确认。
2. GitHub main 当前代码。
3. 当前测试 / Eval 结果。
4. Project source 文档。
5. GOAL0531。
6. 历史聊天。
7. 子窗口输出，必须经总控审计。

如果 GOAL 与 GitHub 当前代码冲突：

- GitHub 描述当前实现。
- GOAL 描述历史目标和阶段意图。
- 差异记录为 gap。
- 不得把 GOAL 目标当作代码已完成事实。

## Core Intent

GOAL0531 的核心意图是重构 AI 模拟面试项目中的：

- 出题 Agent
- 系统反馈 Agent
- 资产库事实复用
- DDD 应用层边界
- AI 测试体系

## Original Problems

1. 出题 Agent、反馈 Agent、资产库、进展树、评分、训练闭环之间没有统一事实契约。
2. PolishUseCases 承载过多职责。
3. 反馈接口主链路曾使用 reserved placeholder。
4. 资产库没有成为最高优先级事实源。
5. Fake LLM 曾作为 runtime provider。
6. provider-facing payload 不清晰。
7. 测试主要验证工程路径和 fake 行为，不足以验证 AI 能力质量。

## Current Interpretation After Phase 0.1

GOAL0531 的阶段意图按当前 Project sources 解释如下：

### DDD Split

历史意图：

- 拆分过重的 PolishUseCases。
- 建立 DDD 应用层边界。

当前解释：

- Phase 1 = DDD Rails + Agent Platform C0 + Polish Facade Convergence。
- Phase 1 是项目级 DDD 起点，不是全仓库一次性 DDD 迁移。
- Phase 1 也不是仅 Polish 局部文件拆分。
- Polish 是第一条纵切面。
- 项目级 DDD rails 和 Agent Platform C0 必须同步建立。

### Agent Platform

历史意图：

- 将出题 / 反馈从单次 LLM workflow 演进为 Agent。

当前解释：

- Agent Platform 目标态是 C：
  - AgentExecutor
  - AgentDefinitionRegistry
  - SkillRegistry
  - ToolRegistry
  - HandoffContract
  - EvalContract
- B，即只有 contracts + registry skeleton，不是最终目标。
- Phase 1 只实现 C0 skeleton，后续 Phase 4/5/6/8 逐步接入 Question / Feedback。

### Canonical Assets

历史意图：

- 资产库事实复用。
- 资产库成为重要事实来源。

当前解释：

- Phase 2 先统一 CanonicalEvidencePack / SourceSupportSummary。
- Question / Feedback 不得各自解释 source support。
- asset_confirmed 才是 canonical evidence。
- asset conflict 必须 HITL。

### Feedback Rules

历史意图：

- 反馈接口走真实主链路。
- 反馈要有资产一致性、覆盖度、变化分析。

当前解释：

- Phase 3 拆 Domain Policies。
- Phase 6 接 Feedback Agent planned workflow。
- asset conflict 禁止 generate_next_question。
- asset update 只能 candidate，必须 user_confirmation_required=true。

### Question Agent Rules

历史意图：

- 出题要事实可追踪、可评分、可追问。

当前解释：

- Phase 3 拆 source support / grounding / follow-up coverage policies。
- Phase 5 接 Question Agent planned workflow。
- job_gap_only 不得声称候选人做过。
- adjacent_project_evidence 必须假设性表达。
- deterministic fallback 不等于 generated success。

### AI Evals and Fake Cleanup

历史意图：

- 清理 fake runtime 污染。
- 建立 AI 质量测试。

当前解释：

- Phase 7 做 provider request fail-closed 和 fake cleanup。
- Phase 9 建 Eval / CI / Regression gate。
- 单测不替代 Eval。

## Mapping to New Phases

| GOAL0531 Topic | New Phase |
|---|---|
| ddd-split | Phase 1 DDD Rails + Agent Platform C0 + Polish Facade Convergence |
| feedback-realpath | Feedback Agent spec + Phase 6 planned workflow |
| canonical-assets | Phase 2 Canonical Evidence / Interview Context |
| feedback-rules | Phase 3 Domain Policy + Phase 6 Feedback Agent |
| question-agent-rules | Phase 3 Domain Policy + Phase 5 Question Agent |
| ai-evals-and-fake-cleanup | Phase 7 Provider/Fake + Phase 9 Eval gate |

## Known Gaps

GOAL0531 不提供：

- 当前代码逐文件事实。
- 当前测试结果。
- 当前 Eval 结果。
- 完整 Agent Definition Registry。
- 完整 Skill / Tool Registry。
- 完整 DDD import boundary rules。
- 每个 capability 的 done evidence。

这些必须由 GitHub recon、Project sources、测试/Eval 结果补足。

## Usage Rules

允许使用 GOAL0531 判断：

- 为什么要重构。
- 哪些历史问题必须覆盖。
- 阶段意图是否丢失。
- 是否存在方向性偏移。

禁止使用 GOAL0531 断言：

- 当前代码已经完成某能力。
- 某测试已经通过。
- 某 Agent 已达到 L3/L4。
- 某 prompt/provider/DB 行为已满足目标态。
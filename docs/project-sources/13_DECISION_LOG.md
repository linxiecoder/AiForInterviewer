---
title: 13_DECISION_LOG
type: note
permalink: ai-for-interviewer/docs/project-sources/13-decision-log
---

# 13 Decision Log

## Status

允许状态：

- proposed
- confirmed
- superseded
- deferred
- rejected

## DEC-001 Source of Truth Hierarchy

Status: confirmed

Decision:

GOAL0531 不作为唯一可信源。采用分层可信源：

1. 用户明确确认。
2. GitHub main 当前代码。
3. 当前测试 / Eval 结果。
4. Project source 文档。
5. GOAL0531 历史目标和阶段意图。
6. 历史聊天。
7. 子窗口输出，必须经总控审计。

If conflict:

- GitHub describes current implementation.
- Project source describes target architecture and rules.
- GOAL0531 describes historical intent.
- Difference must be recorded as gap.

Recommendation:

分层可信源。

## DEC-002 First Phase

Status: confirmed

Decision:

第一阶段先做 Phase 0 Project source pack / Agent Definition / Traceability Matrix，不改代码。

Recommendation:

Phase 0 first.

## DEC-003 Agent Maturity Target

Status: confirmed

Decision:

短期目标是 L2 planned guarded workflow，不直接追求 L4 autonomous agent。

Question Agent 当前默认判断：

- L1.5-L2，不是成熟 autonomous Agent。

Feedback Agent 当前默认判断：

- L1.5-L2，不是成熟 autonomous Agent。

Recommendation:

L2 first, but on Agent Platform C path.

## DEC-004 Domain Policy Migration Order

Status: confirmed

Decision:

Domain Policy 迁移顺序采用 C：

CanonicalEvidencePack / SourceSupportSummary first -> Question Policy -> Feedback Policy

Rationale:

Question / Feedback 都依赖 source support。
若先迁单侧 policy，会继续造成 evidence support 语义双轨。

Recommendation:

Phase 2 先统一 Canonical Evidence / Interview Context。
Phase 3 再迁 Domain Policies。

## DEC-005 Agent Platform Target

Status: confirmed

Decision:

Agent Platform 目标态采用 C：

- AgentExecutor
- AgentDefinitionRegistry
- SkillRegistry
- ToolRegistry
- AgentExecutionPlan
- AgentExecutionTrace
- HandoffContract
- EvalContract
- Question / Feedback 最终接入该平台

B，即只建 contracts + registry skeleton，不是最终目标。
B 只能作为 C 的过渡切片。

Recommendation:

锁定 C target。
Phase 1 执行 C0，不把 B 当 done。

## DEC-006 Phase 1 Agent Platform Slice

Status: confirmed

Decision:

Phase 1 只执行 C0：

- 项目级 Agent contracts / registry / executor port skeleton。
- DDD rails。
- PolishUseCases facade 收敛。
- boundary tests。

Phase 1 不做：

- Question / Feedback runtime 全量接入 AgentExecutor。
- prompt rewrite。
- provider behavior refactor。
- DB schema change。
- API behavior change。
- Domain Policy migration。

Recommendation:

Phase 1 = DDD Rails + Agent Platform C0 + Polish Facade Convergence.

## DEC-007 Provider Boundary Timing

Status: confirmed

Decision:

Provider Boundary 采用 B：

Phase 1 可加 provider boundary tests / gate，但不直接重构 provider 行为。

Provider request 行为重构留到 Phase 7。

Recommendation:

Phase 1 锁 provider direction；Phase 7 实施 CompactProviderRequestBuilder fail-closed。

## DEC-008 Phase 1 Scope Interpretation

Status: confirmed

Decision:

Phase 1 第一窗口是项目级 DDD 起点，但不是一次性全项目 DDD 迁移。

定义：

Project-level DDD rails + Polish vertical slice facade convergence + Agent Platform C0.

Recommendation:

避免两个偏移：

1. 把 Phase 1 降级为仅 Polish 局部拆文件。
2. 把 Phase 1 膨胀为全仓库 DDD 大迁移。

## DEC-009 Candidate / Formal Boundary

Status: confirmed

Decision:

Agent 只能产出 candidate / suggestion。
Formal write 必须经过 Application Service + Domain Policy + Handoff。

Principle:

AI propose, Domain dispose.

Recommendation:

所有 Agent Definition / Skill / Tool / Handoff 以 candidate-only 为硬约束。

## DEC-010 Source Backfill Requirement

Status: confirmed

Decision:

关键决策不能只留在聊天中。
每次总控确认后，必须回填 Project sources：

- Decision Log
- Traceability Matrix
- Risk Register
- Acceptance Gates
- Phase Roadmap when applicable

Recommendation:

执行 Phase 0.1 Source Backfill 后再进入 Phase 1。
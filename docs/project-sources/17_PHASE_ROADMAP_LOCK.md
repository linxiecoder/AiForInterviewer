---
title: 17_PHASE_ROADMAP_LOCK
type: note
permalink: ai-for-interviewer/docs/project-sources/17-phase-roadmap-lock
---

# 17 Phase Roadmap Lock

## Purpose

锁定 Phase 0-10 的当前解释，防止后续窗口目标偏移。

本文件是 Phase 0.1 Source Backfill 的核心输出之一。

## Global Rules

1. GOAL0531 是历史意图源，不是当前代码事实源。
2. GitHub main 当前代码是当前实现事实源。
3. 测试 / Eval 是行为证据源。
4. Project source 是目标架构和总控规则源。
5. 子窗口输出必须经总控审计。
6. 关键决策必须回填 Project sources。
7. Agent 只能输出 candidate / suggestion。
8. Formal write 必须经过 Application Service + Domain Policy + Handoff。
9. Prompt Builder 只渲染已确定 context / policy / contract，不做业务决策。
10. Provider request 必须 compact and fail-closed。
11. Fake 只能用于 tests / evals / replay。

## Phase 0

Name:

Project source pack / Agent Definition / Traceability Matrix

Goal:

- 审核 GOAL0531 是否足以作为重构意图证据。
- 建立 Agent Definition Standard。
- 建立 Agent Platform Architecture。
- 建立 DDD Target Architecture。
- 建立 Refactor Traceability Matrix。
- 标出风险和偏移点。
- 输出 Phase 1 候选范围。

Allowed:

- 文档审计。
- GitHub recon。
- Project source 输出。
- Matrix / Risk / Decision 初稿。

Forbidden:

- 改代码。
- 写 Codex 实施补丁。
- 修改业务行为。

Status:

completed by conversation, pending source backfill.

## Phase 0.1

Name:

Source Backfill

Goal:

- 回填已确认决策。
- 锁定 DEC-Q2=C。
- 锁定 DEC-Q3=C target / Phase 1 C0。
- 锁定 DEC-Q4=B。
- 更新 Phase 1 定义。
- 防止后续目标从 C 降级为 B。

Allowed:

- 更新 Project sources。
- 新增 roadmap / Agent Platform C target / Phase 1 catalog。
- 不改业务代码。

Forbidden:

- 改业务代码。
- 生成 Codex 实施补丁。
- 改 prompt / provider / DB / API。

Done Criteria:

- Decision Log 更新。
- Agent Platform Architecture 更新。
- DDD Target Architecture 更新。
- Matrix 更新。
- Risk Register 更新。
- Acceptance Gates 更新。
- Phase Roadmap Lock 新增。
- Agent Platform C Target 新增。
- Phase 1 Window Catalog 新增。

## Phase 1

Name:

DDD Rails + Agent Platform C0 + Polish Facade Convergence

Goal:

- 建立项目级 DDD rails。
- 建立 Agent Platform C0 skeleton。
- 收敛 PolishUseCases facade。
- 让 focused application services 开始真实承载 application orchestration。
- 加 architecture / boundary tests。

Allowed:

- application/agents contracts / definitions / registry / runtime port skeleton。
- tests/architecture boundary tests。
- PolishUseCases facade 收敛。
- Focused services ownership extraction。
- Provider boundary tests only。

Forbidden:

- Prompt rewrite。
- Provider behavior refactor。
- DB schema change。
- API contract change。
- Question / Feedback Domain Policy migration。
- Full Agent runtime migration。
- LangGraph behavior change。
- Eval gate finalization。

Non-goals:

- 不完成全项目 DDD。
- 不完成 Agent Platform C。
- 不完成 Question / Feedback Agent 接入。
- 不完成 provider fail-closed 重构。

Done Criteria:

- C0 skeleton 存在或明确实现。
- PolishUseCases 只保留 facade / wiring / backward-compatible exports。
- Focused services 不再只是空 wrapper，至少 P1 选中服务真实承载 orchestration。
- Boundary tests 通过。
- No prompt/provider/DB/API behavior diff。
- Matrix / Decision / Risk 回填。

## Phase 2

Name:

Canonical Evidence / Interview Context

Goal:

- CanonicalEvidencePack 成为共享事实入口。
- SourceSupportSummary 统一。
- Interview Context 统一。
- Question / Feedback 不再各自解释 evidence support。

Allowed:

- context services。
- source_support_summary。
- context digest。
- evidence refs。
- reason codes。
- confidence。

Forbidden:

- 大规模 Agent runtime 改造。
- Provider behavior rewrite。
- Formal asset update behavior change。

Done Criteria:

- CanonicalEvidencePack shape 与 contract 对齐。
- source_support_summary 包含 level / refs / reason_codes / confidence。
- Question / Feedback context 使用统一入口。
- Tests / eval seeds 覆盖 direct / adjacent / job_gap / insufficient。

## Phase 3

Name:

Domain Policies

Goal:

- 将 source support、grounding、follow-up coverage、asset consistency、answer coverage、answer change、next action 等业务规则迁入 Domain Policy。
- Domain 不访问 DB、不调用 LLM、不依赖 FastAPI/infrastructure。

Allowed:

- domain/polish/policies/*
- policy tests
- application services 调用 policies

Forbidden:

- Prompt 承载业务规则。
- Infrastructure 承载业务规则。
- Agent 直接写 formal fact。

Done Criteria:

- Domain policies pure。
- Application services orchestrate policies。
- Existing application-level rules 不再承载核心职责。
- Boundary tests 通过。

## Phase 4

Name:

Agent Contracts / Skills / Tools

Goal:

- Question / Feedback Agent Definition 注册。
- Skills 注册。
- Tools 注册。
- Handoff contracts 对齐。
- Trace contracts 对齐。

Allowed:

- AgentDefinitionRegistry entries。
- SkillRegistry entries。
- ToolRegistry entries。
- Agent contracts。
- Tool contracts。

Forbidden:

- Full runtime replacement unless explicitly scoped。
- Provider behavior rewrite。
- DB schema change。

Done Criteria:

- Question / Feedback definitions complete。
- Skills and tools registered with schemas。
- Candidate-only rules enforced。
- Tool no repository exposure gate。

P4-W1 Status:

- `polish_question_agent` / `polish_feedback_agent` definitions validated in project-level C1 catalog。

P4-W1.fix.01 Status:

- C1 catalog hygiene complete: `catalog.py` is an aggregator, concrete Question / Feedback definitions live under `definitions/polish/`, and public C1 registry builder imports are preserved.
- Agent / Skill versioning separated from execution window marker: semantic definition versions and schema versions are stable, while `catalog_revision` records `2026-06-05.p4-w1.fix01`.
- No runtime behavior change: AgentExecutor wiring, LangGraph runtime, provider requests, prompt assets, API, DB schema, and domain policy behavior remain out of scope.
- Question 8 skills / 8 tools and Feedback 10 skills / 9 tools validated by architecture tests。
- Trace and handoff contract fields validated; Feedback asset update requires user confirmation。
- Runtime workflow remains deferred to Phase 5 / Phase 6。
- LangGraph / multi-agent runtime remains deferred to Phase 8。
- Eval / CI gate remains deferred to Phase 9。

## Phase 5

Name:

Question Agent Planned Workflow

Goal:

- Question Agent 接入 planned guarded workflow。
- 使用统一 CanonicalEvidencePack / SourceSupportSummary。
- 使用 Domain Policies。
- 输出 question_candidate。

Allowed:

- question agent planner。
- question skills。
- question tools。
- question handoff。
- question eval cases。

Forbidden:

- Agent 直接写 formal question。
- job_gap_only factual claim。
- adjacent_project_evidence as completed fact。
- deterministic fallback as success。

Done Criteria:

- Source support reason codes。
- Grounding blocking。
- Follow-up anti-repetition。
- Candidate handoff。
- Tests / Eval passed。

## Phase 6

Name:

Feedback Agent Planned Workflow

Goal:

- Feedback Agent 接入 planned guarded workflow。
- 使用统一 CanonicalEvidencePack / SourceSupportSummary。
- 使用 Domain Policies。
- 输出 feedback_candidate / asset_update_candidate。

Allowed:

- feedback agent planner。
- feedback skills。
- feedback tools。
- feedback handoff。
- feedback eval cases。

Forbidden:

- Asset conflict 时 generate_next_question。
- Asset update candidate 直接写正式资产。
- Provider unavailable / validation failed as success。

Done Criteria:

- asset_consistency_check。
- answer_coverage。
- answer_change_analysis。
- feedback_cards。
- next action policy。
- HITL asset candidate。
- Tests / Eval passed。

## Phase 7

Name:

Provider request fail-closed

Goal:

- CompactProviderRequestBuilder。
- No full prompt asset fallback。
- Forbidden keys rejected。
- Provider fail-closed。
- Fake cleanup。

Allowed:

- provider boundary。
- compact request builder。
- parser。
- redaction。
- tests.

Forbidden:

- Prompt business rule expansion。
- Domain policy in provider layer。
- Fake runtime provider。

Done Criteria:

- Compact builder required。
- Forbidden keys blocked。
- Provider unavailable not success。
- Fake only tests/evals/replay。

## Phase 8

Name:

LangGraph / 多 Agent runtime

Goal:

- Agent runtime 接入。
- Controlled tool loop。
- Resume / replay / interrupt。
- Multi-agent handoff。

Allowed:

- infrastructure/ai_runtime。
- application agent executor adapter。
- runtime flags。
- checkpointer。
- replay。

Forbidden:

- Runtime direct formal write。
- Infrastructure business policy。
- Unbounded autonomous loops。

Done Criteria:

- Runtime controlled。
- Formal write blocked unless handoff。
- Trace complete。
- Replay read-only default。
- HITL works。

## Phase 9

Name:

Eval / CI / Regression gate

Goal:

- AI Eval datasets。
- Graders。
- Runners。
- Reports。
- Regression gate。
- CI integration。

Allowed:

- tests/evals。
- eval runners。
- datasets。
- reports。
- CI gates。

Forbidden:

- Claim AI quality with only unit tests。
- Fake-only eval as real provider quality。

Done Criteria:

- Every Capability ID has regression case。
- Eval failure blocks done。
- CI gate documented。
- Reports generated。

## Phase 10

Name:

Stage closure and Project sources backfill

Goal:

- 收口阶段。
- 更新 source pack。
- Matrix closure。
- Decision/Risk cleanup。
- Remaining gaps explicit。

Allowed:

- docs。
- audit。
- source backfill。
- final matrix。

Forbidden:

- 新功能混入收口。
- 未验证即 done。

Done Criteria:

- All completed capability done evidence present。
- Deferred gaps documented。
- Next roadmap updated。

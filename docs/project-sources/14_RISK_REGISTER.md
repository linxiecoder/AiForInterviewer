---
title: 14_RISK_REGISTER
type: note
permalink: ai-for-interviewer/docs/project-sources/14-risk-register
---

# 14 Risk Register

## RISK-001 文档与代码事实混淆

Severity: high

Description:

GOAL0531、Project source、历史聊天、子窗口输出可能被误当作当前代码事实。

Mitigation:

- Source of Truth Policy。
- 实现判断必须读 GitHub 当前代码。
- GOAL 只作为历史意图源。
- 冲突必须记录 gap。

## RISK-002 Agent 名称掩盖单次 workflow

Severity: high

Description:

Question / Feedback 可能被称为 Agent，但实际仍是单次 LLM workflow 或 guarded workflow。

Mitigation:

- Agent Definition Standard。
- 成熟度未达标时不得称 autonomous agent。
- 当前默认 L1.5-L2。
- 目标短期 L2 planned guarded workflow。

## RISK-003 DDD 文件移动但职责未迁移

Severity: high

Description:

只移动文件或创建 wrapper service，但旧位置仍承载真实职责。

Mitigation:

- Matrix done criteria 要求旧位置不再承载职责。
- wrapper split 不得标记 capability done。
- Phase 1 必须验证 PolishUseCases facade 收敛。

## RISK-004 Prompt 承载业务规则

Severity: high

Description:

Prompt builder 继续承载 source support、asset conflict、next action、score range 等业务规则。

Mitigation:

- 抽 Domain Policy。
- Prompt Builder 只渲染已确定 context / policy / contract。
- 加 architecture boundary tests。
- Phase 3 迁移 policy。

## RISK-005 Provider request fail-open

Severity: high

Description:

Provider request 在 compact payload 不存在时 fallback 到 full prompt asset，或携带 forbidden keys。

Mitigation:

- CompactProviderRequestBuilder fail-closed。
- No full prompt asset fallback。
- Forbidden keys rejected。
- Phase 1 先加 provider boundary tests / gate。
- Phase 7 实施 provider boundary 重构。

## RISK-006 Fake 污染 runtime

Severity: medium

Description:

Fake LLM 或 fake transport 被 runtime provider 使用，导致测试成功掩盖真实 provider 行为。

Mitigation:

- Fake 下沉 tests/evals/replay。
- Runtime env 禁止 fake provider。
- import boundary scan。
- Fake output trace visible。

## RISK-007 Eval 只覆盖 seed 样本

Severity: medium

Description:

Eval 只覆盖少量 seed 或 fake 行为，不能证明 AI 质量。

Mitigation:

- 每个 Capability ID 绑定 regression case。
- Eval gate 进入 CI。
- Phase 9 建立 graders / datasets / reports。

## RISK-008 多 Agent 扩展复制混乱

Severity: high

Description:

每个 Agent 自己定义 Skill / Tool / Trace / Handoff，导致平台不可演进。

Mitigation:

- Agent Platform Architecture。
- AgentDefinitionRegistry。
- SkillRegistry。
- ToolRegistry。
- AgentExecutor。
- Phase 1 C0 skeleton。
- Phase 4 C1 project-level catalog and architecture tests validate Question / Feedback definitions, skills, tools, trace, and handoff refs.

## RISK-009 DEC-Q3 目标被降级为 B

Severity: high

Description:

只建立 contracts + registry skeleton 后，被误认为 Agent Platform 已完成，导致后续离 C 越来越远。

Mitigation:

- DEC-005 confirmed：目标态是 C。
- DEC-006 confirmed：Phase 1 是 C0。
- Acceptance Gates 增加 Agent Platform C0 Gate。
- Matrix 增加 AGT-005 AgentExecutor port。
- DEC-007 confirmed：Phase 4 C1 只是 contract catalog slice，runtime/eval gates 仍 deferred。

## RISK-016 Phase 4 C1 被误当 runtime 接入完成

Severity: high

Description:

C1 已注册 AgentDefinition / SkillDefinition / ToolDefinition，但若被误读为 Question / Feedback runtime 已经接入 AgentExecutor，会掩盖 Phase 5 / Phase 6 / Phase 8 的真实工作。

Mitigation:

- P4-W1 execution report 标明 no runtime wiring。
- Matrix 只标 C1 contract capabilities validated，不标 Phase 5/6/8/9 done。
- Acceptance Gates 增加 Agent Platform C1 Gate。
- Phase 5 / Phase 6 / Phase 8 / Phase 9 必须单独 scope lock 和验证。

## RISK-010 Phase 1 被误解为仅 Polish 局部拆文件

Severity: high

Description:

Phase 1 如果只做 Polish 文件拆分，会缺失项目级 DDD rails 和 Agent Platform C0，后续多 Agent 继续复制混乱。

Mitigation:

- Phase 1 定义为 DDD Rails + Agent Platform C0 + Polish Facade Convergence。
- Phase 1 Window Catalog 锁定 allowed / forbidden。
- 必须包含 architecture / boundary tests。

## RISK-011 Phase 1 膨胀为全仓库 DDD 大迁移

Severity: high

Description:

Phase 1 若试图一次性迁移全项目 DDD，会导致范围失控、测试爆炸、prompt/provider/DB 被误改。

Mitigation:

- Phase 1 是项目级 DDD 起点，不是全仓库完成。
- 禁止 prompt/provider/DB/API 行为变化。
- 只做 Polish vertical slice 和 C0 rails。

## RISK-012 Source support 语义双轨

Severity: high

Description:

CanonicalEvidencePack、QuestionGenerationService、Feedback rules 各自维护 evidence support 语义，导致题目和反馈判断不一致。

Mitigation:

- DEC-004 confirmed：CanonicalEvidencePack / SourceSupportSummary first。
- Phase 2 统一 source_support_summary。
- Phase 3 迁移 Domain Policies。

## RISK-013 Candidate / formal boundary 不统一

Severity: high

Description:

Graph path 使用 candidate handoff，但 direct fallback path 可能直接写 generated business object，造成 Agent 边界不一致。

Mitigation:

- Agent candidate only。
- Formal write through Application Service + Domain Policy + Handoff。
- Phase 4/5/6 统一 Question / Feedback Agent handoff。

## RISK-014 Feedback rules 与 expected points 耦合

Severity: medium

Description:

Expected points、asset consistency、answer coverage、answer change、next action 混在 feedback_rules 中，难以复用和测试。

Mitigation:

- Phase 2 拆 expected point builder / context。
- Phase 3 拆 Domain Policies。
- Phase 6 接 Feedback Agent planned workflow。

## RISK-015 Provider boundary tests 误改 provider 行为

Severity: medium

Description:

Phase 1 只允许加 tests / gate，但可能被误执行为 provider 行为重构。

Mitigation:

- DEC-007 confirmed：Phase 1 only tests / gate。
- Provider behavior refactor deferred to Phase 7。
- Execution Window Protocol 设置 forbidden scope。

## RISK-016 Project source 不回填导致目标漂移

Severity: high

Description:

关键决策只停留在聊天里，后续窗口按旧文档执行。

Mitigation:

- Phase 0.1 Source Backfill。
- 每个窗口 Done Criteria 要求 Backfill。
- Decision Log / Matrix / Risk Register 必须同步。

---
title: 09_REFACTOR_TRACEABILITY_MATRIX
type: note
permalink: ai-for-interviewer/docs/project-sources/09-refactor-traceability-matrix
---

# 09 Refactor Traceability Matrix

## 状态

允许状态：

- not_started
- recon_done
- design_done
- implementation_planned
- implemented
- validated
- blocked
- deferred
- done

## 关闭规则

只有同时满足以下条件，才能标记 done：

1. 设计更新。
2. 代码迁移。
3. 旧位置不再承载职责。
4. 单测通过。
5. 必要 eval 通过。
6. 验证命令运行并记录结果。
7. 无 forbidden scope 修改。
8. Project source 回填。
9. gap 已关闭或显式 deferred。
10. 用户确认需要确认的关键决策。

文件移动但职责未迁移，不得标记 done。
wrapper split 不等于 capability done。

## Phase 0.1 决策回填

已确认：

- DEC-Q2 = C：先统一 CanonicalEvidencePack / SourceSupportSummary，再迁 Question / Feedback policy。
- DEC-Q3 = C target：AgentExecutor + SkillRegistry + ToolRegistry 是目标态；Phase 1 只做 C0。
- DEC-Q4 = B：Phase 1 加 provider boundary tests / gate，不重构 provider 行为。

## Matrix

| ID | Capability | Current | Target | Layer | Status | Phase |
|---|---|---|---|---|---|---|
| DDD-001 | PolishUseCases facade 收敛 | use_cases.py 承载大量 orchestration；focused services 已有但多为 wrapper | facade.py + services/*，PolishUseCases 只保留 facade / wiring / backward compatibility | Application | recon_done | Phase 1 |
| DDD-002 | Application services 真实落位 | *_application_service wrapper | services/* 真实承载 application orchestration | Application | recon_done | Phase 1 |
| DDD-003 | Project-level DDD rails | 分层目标存在于文档，代码 boundary tests 不完整 | tests/architecture + import allow/deny matrix | Architecture | design_done | Phase 1 |
| DDD-004 | Domain Policy target directory | domain/polish/policies 目标存在 | Question / Feedback policies 最终迁入 domain/polish/policies | Domain | not_started | Phase 3 |
| CTX-001 | CanonicalEvidencePack | canonical_evidence.py 已存在，shape 与目标契约不完全一致 | context/canonical_evidence_service.py + source_support_summary | Context | recon_done | Phase 2 |
| CTX-002 | SourceSupportSummary | source_support_level 单字段/多处推导 | source_support_summary with reason_codes / confidence / refs | Context / Domain Policy | design_done | Phase 2 |
| CTX-003 | Interview Context | scattered dicts | unified interview context builder | Context | not_started | Phase 2 |
| QAG-001 | Source support classification | 多处散落 | source_support_policy.py 使用 SourceSupportSummary | Domain Policy | recon_done | Phase 3 |
| QAG-002 | Question grounding | question_grounding.py in application | question_grounding_policy.py in domain | Domain Policy | recon_done | Phase 3 |
| QAG-003 | Follow-up coverage | metadata/use_cases | follow_up_coverage_policy.py | Domain Policy | recon_done | Phase 3 |
| QAG-004 | Question Agent planner | implicit + graph phases | question_agent_planner.py under Agent Platform | Agent | recon_done | Phase 5 |
| QAG-005 | Question Agent Definition | partial spec | AgentDefinition registered | Agent Platform | design_done | Phase 4 |
| QAG-006 | Question Skills | listed in spec | registered skills with contracts | Agent Platform | design_done | Phase 4/5 |
| QAG-007 | Question Tools | local graph TOOL_SCHEMAS | registered tools with contracts | Agent Platform | recon_done | Phase 4/5 |
| FAG-001 | Expected points builder | feedback_rules/question_metadata | expected_point_builder.py in context | Context | recon_done | Phase 2 |
| FAG-002 | Asset consistency | feedback_rules.py | asset_consistency_policy.py | Domain Policy | recon_done | Phase 3 |
| FAG-003 | Answer coverage | feedback_rules.py | answer_coverage_policy.py | Domain Policy | recon_done | Phase 3 |
| FAG-004 | Answer change | feedback_rules.py | answer_change_policy.py | Domain Policy | recon_done | Phase 3 |
| FAG-005 | Feedback next action | scattered / feedback_rules | feedback_next_action_policy.py | Domain Policy | recon_done | Phase 3/6 |
| FAG-006 | Feedback Agent Definition | partial spec | AgentDefinition registered | Agent Platform | design_done | Phase 4 |
| FAG-007 | Feedback Skills | listed in spec | registered skills with contracts | Agent Platform | design_done | Phase 4/6 |
| FAG-008 | Feedback Tools | implicit functions | registered tools with contracts | Agent Platform | not_started | Phase 4/6 |
| AGT-001 | Agent contracts | ai_runtime contracts partial | application/agents/contracts/* | Agent Platform | recon_done | Phase 1 |
| AGT-002 | AgentDefinitionRegistry | none / graph registry only | agent_definition_registry.py | Agent Platform | design_done | Phase 1 |
| AGT-003 | SkillRegistry | none | skill_registry.py | Agent Platform | design_done | Phase 1 |
| AGT-004 | ToolRegistry | graph-local tool schemas | tool_registry.py | Agent Platform | design_done | Phase 1 |
| AGT-005 | AgentExecutor port | AgentGraphRunner exists for graph runtime | AgentExecutor protocol / port independent from LangGraph | Agent Platform | design_done | Phase 1 |
| AGT-006 | Handoff contract | ai_runtime handoff partial | shared agent handoff contract | Agent Platform | recon_done | Phase 1/4 |
| AGT-007 | Agent Trace Contract | ai_runtime trace refs partial | unified AgentExecutionTrace | Agent Platform | recon_done | Phase 1/4 |
| PRO-001 | Compact provider request | scattered Question/Feedback builders | CompactProviderRequestBuilder | Provider Boundary | recon_done | Phase 7 |
| PRO-002 | Provider boundary tests | partial tests | forbidden keys + no full prompt asset fallback gate | Provider Boundary | design_done | Phase 1/7 |
| FAKE-001 | Fake cleanup | runtime fake rejected; fake transport still exists for tests | tests/fakes + evals/replay only | Test/Eval | recon_done | Phase 7/9 |
| EVAL-001 | AI Eval gate | seed evals / descriptors | evals + CI regression gate | Eval | recon_done | Phase 9 |
| WIN-001 | Execution Window Protocol | protocol exists | every window has scope / forbidden / tests / rollback / backfill | Governance | design_done | Phase 0.1 |
| SRC-001 | Source Backfill | sources partially stale after DEC confirmations | updated Project sources | Governance | implementation_planned | Phase 0.1 |

## Gap Register

| Gap ID | Description | Source | Target |
|---|---|---|---|
| GAP-001 | GOAL0531 是意图源，不是当前代码事实源 | Source Policy | 每次实施先 GitHub recon |
| GAP-002 | focused services 已存在但多为 wrapper | GitHub code recon | Application service 真实落位 |
| GAP-003 | Source support 语义双轨 | GitHub code recon | SourceSupportSummary |
| GAP-004 | feedback_rules 承载 domain policy | GitHub code recon | domain/polish/policies |
| GAP-005 | question_grounding 承载 domain policy | GitHub code recon | domain/polish/policies |
| GAP-006 | provider compact builder 分散 | GitHub code recon | CompactProviderRequestBuilder |
| GAP-007 | graph-local tool schema 不等于 ToolRegistry | GitHub code recon | project-level ToolRegistry |
| GAP-008 | B 可能被误当 Agent Platform 目标态 | User confirmed concern | C target / C0 slice |
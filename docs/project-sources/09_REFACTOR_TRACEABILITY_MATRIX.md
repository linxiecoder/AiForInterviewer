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
- implemented_with_validation_blockers
- validated_with_deferred_l5_runtime
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
| QAG-004 | Question Agent planner | implicit + graph phases | dedicated Question planned workflow component + application-service handoff bridge | Agent | validated_with_deferred_l5_runtime | Phase 5 |
| QAG-005 | Question Agent Definition | partial spec | AgentDefinition registered | Agent Platform | validated | Phase 4 |
| QAG-006 | Question Skills | listed in spec | registered skills with contracts | Agent Platform | validated | Phase 4/5 |
| QAG-007 | Question Tools | local graph TOOL_SCHEMAS | registered tools with contracts | Agent Platform | validated | Phase 4/5 |
| FAG-001 | Expected points builder | feedback_rules/question_metadata | expected_point_builder.py in context | Context | recon_done | Phase 2 |
| FAG-002 | Asset consistency | feedback_rules.py | asset_consistency_policy.py | Domain Policy | recon_done | Phase 3 |
| FAG-003 | Answer coverage | feedback_rules.py | answer_coverage_policy.py | Domain Policy | recon_done | Phase 3 |
| FAG-004 | Answer change | feedback_rules.py | answer_change_policy.py | Domain Policy | recon_done | Phase 3 |
| FAG-005 | Feedback next action | scattered / feedback_rules | feedback_next_action_policy.py | Domain Policy | implemented | Phase 3/6 |
| FAG-006 | Feedback Agent Definition | partial spec | AgentDefinition registered | Agent Platform | validated | Phase 4 |
| FAG-007 | Feedback Skills | listed in spec | registered skills with contracts | Agent Platform | validated | Phase 4/6 |
| FAG-008 | Feedback Tools | implicit functions | registered tools with contracts | Agent Platform | validated | Phase 4/6 |
| AGT-001 | Agent contracts | ai_runtime contracts partial | application/agents/contracts/* | Agent Platform | recon_done | Phase 1 |
| AGT-002 | AgentDefinitionRegistry | none / graph registry only | agent_definition_registry.py | Agent Platform | design_done | Phase 1 |
| AGT-003 | SkillRegistry | none | skill_registry.py | Agent Platform | design_done | Phase 1 |
| AGT-004 | ToolRegistry | graph-local tool schemas | tool_registry.py | Agent Platform | design_done | Phase 1 |
| AGT-005 | AgentExecutor port | AgentGraphRunner exists for graph runtime | AgentExecutor protocol / port independent from LangGraph | Agent Platform | design_done | Phase 1 |
| AGT-006 | Handoff contract | ai_runtime handoff partial | shared agent handoff contract | Agent Platform | validated | Phase 1/4 |
| AGT-007 | Agent Trace Contract | ai_runtime trace refs partial | unified AgentExecutionTrace | Agent Platform | validated | Phase 1/4 |
| PRO-001 | Compact provider request | scattered Question/Feedback builders | CompactProviderRequestBuilder | Provider Boundary | recon_done | Phase 7 |
| PRO-002 | Provider boundary tests | partial tests | forbidden keys + no full prompt asset fallback gate | Provider Boundary | design_done | Phase 1/7 |
| FAKE-001 | Fake cleanup | runtime fake rejected; fake transport still exists for tests | tests/fakes + evals/replay only | Test/Eval | recon_done | Phase 7/9 |
| EVAL-001 | AI Eval gate | seed evals / descriptors | evals + CI regression gate | Eval | recon_done | Phase 9 |
| WIN-001 | Execution Window Protocol | protocol exists | every window has scope / forbidden / tests / rollback / backfill | Governance | validated | Phase 0.1 |
| SRC-001 | Source Backfill | sources partially stale after DEC confirmations | updated Project sources | Governance | implemented | Phase 0.1 |

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

## P4-W1 Backfill Evidence

- `apps/api/app/application/agents/definitions/catalog.py` registers `polish_question_agent` and `polish_feedback_agent` through a project-level C1 catalog aggregator.
- P4-W1.fix.01 split concrete Question / Feedback skill and tool definitions into `apps/api/app/application/agents/definitions/polish/` while preserving the public C1 registry builder.
- Agent definition versions are stable semantic versions (`1.0.0`); `catalog_revision` records `2026-06-05.p4-w1.fix01`.
- Registered `SkillDefinition` records include purpose, contract-only implementation ref, preconditions, postconditions, fail-closed fallback policy, stable definition/schema version, and architecture test refs.
- Question Agent C1 contract has 8 skill refs, 8 tool refs, and only `question_candidate` output.
- Feedback Agent C1 contract has 10 skill refs, 9 tool refs, and only `feedback_candidate` / `asset_update_candidate` outputs.
- `ToolRegistry` validates allowed `side_effect_policy`, required forbidden data, and no direct repository / DB / SQLAlchemy exposure.
- `AgentDefinitionRegistry.validate_references` fails closed for unknown skill refs, unknown tool refs, duplicate IDs, invalid candidate outputs, and unresolved skill tool refs.
- Validation evidence: `tests/architecture/test_agent_platform_c1_boundary.py` and `tests/architecture` passed in the P4-W1 window; P4-W1.fix.01 adds catalog hygiene and version-separation assertions to the same C1 boundary suite.
- Runtime workflow, LangGraph execution, and eval CI gates remain deferred to Phase 5 / Phase 6 / Phase 8 / Phase 9.

## P5P6-W1 Backfill Evidence

- Window `P5P6-W1-C2-C3-PLANNED-WORKFLOW-L5-FOUNDATION` implemented Phase 5 / Phase 6 as C2 / C3 L2 planned guarded workflow only.
- `QAG-004` now has an application-service planned workflow bridge: provider / graph output is normalized to `question_candidate`, enriched with source-support / policy / validation / handoff refs, and fallback or graph-disabled candidates return `validation_failed` instead of persisting a formal question.
- `QAG-006` / `QAG-007` continue to rely on the Phase 4 C1 project-level Skill / Tool contracts; this window used those contracts as trace metadata and did not add Phase 8 runtime tool loops.
- `FAG-005` is integrated into the Feedback planned handoff metadata through existing feedback policy outputs and explicit next-action / asset-update candidate refs.
- `FAG-007` / `FAG-008` continue to rely on Phase 4 C1 project-level Skill / Tool contracts; this window added a local planned handoff bridge for `feedback_candidate` / `asset_update_candidate`, not autonomous runtime execution.
- `AGT-006` / `AGT-007` were exercised through candidate refs, validation refs, policy refs and planned handoff metadata. Formal writes remain owned by Application Service paths.
- `EVAL-001` has P5/P6 scoped local eval runner evidence for this window, but the Phase 9 CI regression gate remains deferred and must not be marked done.
- `SRC-001` is backfilled for this window by the Project source updates and `docs/goals/2026-06-05/P5P6-W1-C2-C3-PLANNED-WORKFLOW-L5-FOUNDATION/` evidence.
- Phase 11 / Phase 12 Supervisor / Orchestrator and final L5 release gate were not implemented by this window.
- Broad API tests still contain legacy expectations that fake / default / graph-disabled question fallback persists a formal question; those tests are a deferred alignment gap, not evidence that fallback success is allowed.

## P5-W1.fix.01 Question Planned Workflow Remediation

- Manual / Codex audit found the previous `QAG-004` wording overstrong because Question had candidate metadata and fallback behavior in `use_cases.py`, but no dedicated production `apps/api/app/application/polish/agents/question/planned_workflow.py`.
- `P5-W1.fix.01-QUESTION-PLANNED-WORKFLOW-REMEDIATION` corrects that by adding a real Phase 5 Question planned workflow component and wiring normal graph/direct question paths through it before handoff.
- `QAG-004` remains `implemented_with_validation_blockers`, not `done`: focused Question business assertions pass, but pytest process exit is still blocked by the pre-existing repo-root `tmp` temp leak checker and `tests/api/test_polish_canonical_evidence.py::test_polish_question_and_feedback_context_include_canonical_assets` remains a deferred legacy alignment gap outside this remediation write scope.
- Phase 5 remains C2 / L2 planned guarded workflow only. Phase 8 runtime, Phase 11 Supervisor / Orchestrator, and Phase 12 L5 release gate are not implemented by this remediation.

## P5P6-W1.fix.02 Validation Blocker Remediation

- `P5P6-W1.fix.02-VALIDATION-BLOCKER-REMEDIATION` resolves the two remaining validation blockers for this window without prompt, provider, DB, API, frontend, Phase 8 runtime, or Phase 11 / Phase 12 changes.
- The legacy canonical-evidence test now asserts provider-unavailable Question fallback as a `VALIDATION_FAILED` `question_candidate` task, while still proving canonical asset refs, source support level, validation refs, context digest, and fallback-not-success metadata are present on the candidate.
- The same test keeps Feedback coverage by using the recorded `question_candidate` payload as test context and confirming Feedback context includes canonical assets plus `feedback_candidate` fallback-not-success metadata.
- Repo-root `tmp/` was identified as local goal/source-pack scratch material and moved out of the repository to `/tmp/aifi-repo-root-tmp-P5P6-W1.fix.02-20260605`; the temp leak checker was not weakened.
- Current broad selector evidence is `300 passed, 323 deselected`; no business assertion failure remains for the scoped Question / Feedback / Agent / Handoff / Canonical / SourceSupport selector.
- `QAG-004` status is now `validated_with_deferred_l5_runtime`: Phase 5 remains C2 / L2 planned guarded workflow, and L5 runtime / release completion remains deferred.

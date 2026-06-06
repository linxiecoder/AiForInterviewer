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
- contract_slice_complete_with_deferred_runtime_gaps
- runtime_hardening_slice_complete_with_deferred_product_workflow
- candidate_product_slice_complete_with_deferred_formal_write_and_release_gate
- eval_contract_slice_complete_with_deferred_runner_ci_release
- validated_with_deferred_gaps
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
| RTE-001 | LangGraph runtime adapter / AgentExecutor integration | AgentGraphRunner / AiOrchestrationFacade active; AgentExecutor protocol existed but was not concrete wiring | AgentGraphRunnerExecutorAdapter exposes AgentGraphRunner through AgentExecutor-compatible boundary; all current facade start surfaces route through that adapter context; facade-created status / timeline / cancel route through adapter read/cancel for known runs with owner-scope preservation; descriptor-unsupported facade-created timeline/cancel fail closed before runner access while Question/Feedback descriptors declare implemented timeline/cancel entrypoints; unknown runs keep runner fallback | Agent Platform / Runtime | validated_with_deferred_gaps | Phase 8 |
| RTE-002 | Controlled tool loop bounds | Polish question graph had local bounded loop; ToolRegistry / SideEffectGuard existed; facade-created runtime commands did not carry shared loop policy metadata; direct Question runtime policy initially lacked the `interrupt_required` stop condition; Feedback direct in-memory runner initially accepted missing loop-policy metadata | AgentRuntimeLoopPolicy required by AgentExecutor adapter and rejects incomplete P8 required stop-condition sets (`max_steps_exceeded`, `timeout`, `validation_failed`, `tool_not_allowed`, `formal_write_requested`, `interrupt_required`, `provider_failed`); GraphDescriptor policy fields feed all current facade start surfaces plus facade-created resume/replay command `runtime_loop_policy` metadata and fail closed on missing bounds; generic direct in-memory runtime start requires valid `runtime_loop_policy` metadata before graph invocation; runtime tool authorization fails closed without registered ToolDefinition and consumes ToolDefinition.forbidden_data; Polish question concrete tool calls require registered runtime ToolDefinition lookup and enforce runtime loop policy `allowed_callers` / `side_effect_policy` plus tool-declared forbidden-data payload blocking; Feedback PR8 provider trace gate requires registered runtime ToolDefinition lookup and now has caller / permission / owner / side-effect / tool-declared forbidden-data negative coverage; Feedback direct in-memory runner start requires descriptor-matching `runtime_loop_policy` metadata and rejects missing or mismatched fields before fake payload construction; Polish question direct runtime policy includes `interrupt_required`; ToolDefinition caller / permission / owner-scope / side-effect / forbidden-payload checks fail closed; architecture gate verifies current direct production `authorize_tool_call()` call sites pass non-`None` `tool=` | Runtime | validated_with_deferred_gaps | Phase 8 |
| RTE-003 | Interrupt / resume / checkpoint / replay | interrupt service and replay/checkpoint tests existed; facade lacked replay method and P8 HITL trigger matrix | facade replay returns read-only / formal-write-blocked AgentReplayResult; facade resume requires checkpoint/strict-base/idempotency control fields and fails closed on unsupported actions before runner invocation; interrupt service supports P8 HITL triggers and checkpoint-bound resume validation; generic in-memory user-confirmation interrupts and Feedback in-memory five-trigger HITL paths use service-backed checkpoint/base/action/idempotency validation before graph continuation, and Feedback service-backed resume timeline preserves candidate / validation refs | Runtime | validated_with_deferred_gaps | Phase 8 |
| RTE-004 | Replay read-only by default | runner replay was read-only in existing paths; replay failure-status / trace-comparison metadata was not preserved before P8 remediation; positive replay side-effect counters were not rejected | adapter and facade fail closed if replay is not read-only / formal-write-blocked; generic in-memory, Question and Feedback runtime replay preserve original failed / blocked / interrupted / cancelled status category as `replayed_*`, original status, failure/fallback reasons, refs-only trace comparison including Feedback validation refs, nested refs-only trace metadata, and zero provider/tool/repository/DB/formal-write counters through `AgentReplayResult.metadata`; `AgentReplayResult` rejects positive/unparseable provider/tool/repository/DB/formal-write side-effect counters | Runtime | validated_with_deferred_gaps | Phase 8 |
| RTE-005 | Runtime trace / timeline completeness | AgentExecutionTrace lacked P8 agent_version / ai_task / low-confidence / failure / fallback fields and adapter did not map full P8 ref categories; runtime DTO and metadata event status strings were not canonicalized | AgentExecutionTrace supports P8 refs and adapter maps graph version / ai_task_id plus validation / handoff / tool / policy / provider / low-confidence / failure / fallback refs when supplied by command/runtime metadata; command metadata and nested runtime `metadata.trace_refs` `tool_refs` / `policy_refs` / `provider_refs` / `validation_refs` / `handoff_refs` / `low_confidence_refs` are merged with runtime result / timeline event refs; runtime replay metadata preserves nested status `metadata.trace_refs` as refs-only replay metadata and promotes validation / handoff / tool / policy / provider / low-confidence refs for adapter trace mapping; runtime result/status/timeline metadata fails closed if it exposes non-empty `formal_refs`, non-zero formal-write counters or non-zero repository / DB business write counters, including common counter key variants; Feedback status trace refs include validation refs for replay comparison while resume/cancel control metadata remains checkpoint-only; adapter timeline events merge event metadata refs and command `handoff_envelope` refs, expose event candidate refs and keep validation / handoff refs separate from output refs; generic runtime start/resume/cancel events, Feedback service-backed resume/cancel events and Polish question / Feedback concrete runtime start plus Polish question cancel events emit refs-only checkpoint / validation / candidate / interrupt / output metadata where applicable, with generic direct `run_started` / `run_resumed` / `run_succeeded` preserving the P8 command ref matrix and Question cancel checkpoint refs separated from validation refs; cancel events preserve candidate/validation/output/checkpoint refs where applicable with zero provider/formal-write counters; adapter status snapshots expose handoff refs from status metadata / trace refs; runtime DTOs classify canonical status categories and reject unknown status or success-like status with `failure_reason`; Polish question application task status mapping reuses the shared runtime status taxonomy to map pending/running/interrupted/blocked/failed/replayed/cancelled statuses onto existing `AiTaskStatus` values without DB/API status expansion; `AgentTraceBridge` and adapter metadata phase/tool event statuses reject unknown non-DTO status values before trace write/event emission | Runtime / Trace | validated_with_deferred_gaps | Phase 8 |
| RTE-006 | Typed multi-agent handoff | HandoffContract metadata existed; typed handoff envelope instance was missing | AgentHandoffEnvelope carries candidate_ref / candidate_type / payload_schema_id / trace_refs / validation_refs / side_effect_key / idempotency_key plus refs-only asset update descriptor fields; adapter execution result/status surfaces expose mapped handoff refs; source result candidate descriptors can be converted into target AgentExecutionPlan input refs through HandoffContract / AgentHandoffEnvelope without raw payload sharing; `execute_agent_handoff()` starts the target AgentExecutor from that typed handoff plan; target executor timeline events surface handoff envelope refs without raw candidate payload sharing | Agent Platform / Handoff | validated_with_deferred_gaps | Phase 8 |
| RTE-007 | Runtime flags / provider-fake isolation | runtime flags default false; LangGraph flag existed in code but not `.env.example` | `.env.example` documents `AIFI_AI_RUNTIME_LANGGRAPH_ENABLED=false`; runtime result metadata fails closed when it reports fake-provider use or fallback-as-generated-success; existing fake/provider gates remain green | Runtime / Provider Boundary | validated_with_deferred_gaps | Phase 8 |
| PRO-001 | Compact provider request | 当前 active production `LlmTransportRequest` caller paths 已在 transport 前使用 compact provider boundary；DTO-level forbidden-key backstop 已存在；P7-W3 已将 Feedback `current_answer.answer_text` formalized as bounded primary input；P7-W4.fix.01 full validation passed | CompactProviderRequestBuilder / equivalent with schema-bound redacted request and fail-closed validation | Provider Boundary | done | Phase 7 |
| PRO-002 | Provider boundary tests | P7 provider boundary tests 覆盖 catalog、recursive reject、redaction、schema gate、Q/F fail-closed paths、global DTO backstop、static no-direct-constructor gate、progress tree、job match、bounded current answer policy metadata、historical answer no raw fallback、nested `full_answer` fail-closed paths；P7-W4.fix.01 full-repo pytest / web validation passed | forbidden keys + no full prompt asset fallback gate | Provider Boundary | done | Phase 1/7 |
| FAKE-001 | Fake cleanup | runtime fake rejected; Feedback direct fake transport now returns fake-visible non-success; fake fixture remains for tests; auth smoke no longer sets `LLM_PROVIDER=fake` | tests/fakes + evals/replay only | Test/Eval | done | Phase 7/9 |
| EVAL-001 | AI Eval gate | seed evals / descriptors；P9 suite manifest、capability-bound replay datasets、deterministic graders、JSON/Markdown reports、negative-control gate、package script and no-secret GitHub Actions job exist；P10 accepts Phase 9 as `complete_with_deferred_remote_ci_gap` with remote CI deferred and stale committed report metadata risk recorded | evals + CI regression gate | Eval | validated | Phase 9 |
| WIN-001 | Execution Window Protocol | P7-W4.fix.01 完成 A/B read-only recon、C single-writer implementation、D full validation、E audit、source backfill sequence | every window has scope / forbidden / tests / rollback / backfill | Governance | done | Phase 0.1/7 |
| SRC-001 | Source Backfill | Project sources 已回填 P7-W4.fix.01 full validation evidence；P8 foundation partial source backfill 已追加，但 P8 final status 仍有 deferred gaps | updated Project sources | Governance | validated_with_deferred_gaps | Phase 0.1/7/8 |
| L5-001 | Final L5 target lock | Phase 0-10 foundation is `closed_with_deferred_gaps`; Phase 11 / Phase 12 were entry/future conditions and not implementation facts | Phase 11 L5 Controlled Multi-Agent Orchestration and Phase 12 L5 Eval, Hardening, and Release Gate are explicitly scoped with non-claims | Governance / Agent Platform | design_done | P11-W0 |
| L5-002 | Supervisor / Orchestrator Agent | P11-W1 contract slice registers `interview_orchestrator_agent` as contract-only in the L5 contract catalog; P11-W5 integration/boundary tests now cover registration, non-release wording, no runtime/provider/API/DB/domain wiring and Orchestrator participation in the refs-only evidence package | Registered Supervisor / Orchestrator Agent with goal decomposition, plan, bounded loop and HITL scope; full runtime execution, product release and Phase 12 release gate remain separately scoped | Agent Platform | validated_with_deferred_gaps | Phase 11 |
| L5-003 | Cross-agent handoff / state / trace | P11-W1 contract slice adds `CrossAgentPlan`, `CrossAgentPlanStep`, `CrossAgentHandoffRoute`, `CrossAgentStateContract` and `CrossAgentTraceContract`; P11-W5 tests backfill trace / validation / handoff separation and typed handoff evidence into the architecture validation command | Typed cross-agent plan, handoff, state, checkpoint, replay and trace timeline contracts; full runtime execution and Phase 12 release gate remain separately scoped | Agent Platform / Runtime | validated_with_deferred_gaps | Phase 11 |
| L5-004 | Multi-agent product workflow | P11-W3 adds a deterministic refs-only minimal candidate product slice with `polish_feedback_agent`, `asset_candidate_agent` and `training_plan_agent`; P11-W5 architecture tests now prove three-business-agent candidate refs, typed feedback -> asset -> training handoffs, trace-visible low confidence, asset-conflict block and formal-write block under the window validation scope | At least one end-to-end workflow with Supervisor / Orchestrator plus three or more business agents; formal write completion, real-provider quality and Phase 12 eval/replay/release gate remain separately scoped | Product Orchestration | validated_with_deferred_gaps | Phase 11 |
| L5-005 | Controlled tool loop hardening | P11-W4 accepted controlled runtime-boundary hardening: `AgentRuntimeLoopPolicy` carries `max_steps`, `max_retries`, `timeout_seconds`, `stop_conditions`, `repair_strategy` and `fallback_semantics`; adapter/facade command metadata carries validated policy; runtime-reported step/retry/timeout exhaustion, `hitl_required` success-like results, fallback/generated-success markers and repository/DB/tool exposure markers fail closed; P11-W5 source backfill records this as validated boundary evidence, not release evidence | Bounded cross-agent tool loop and HITL boundary evidence for Phase 11; product release, formal write completion, real-provider quality and Phase 12 release gate remain separately scoped | Runtime / Tooling | validated | Phase 11 |
| L5-006 | L5 eval / replay / release gate | P12-W1 implemented executable L5 eval suite foundation: runner, Phase 12 datasets, eval gate tests, deterministic mode, negative control, and CI binding exist; P12-W2 replay/resume/failure fixtures, P12-W3 observability/trace report, and P12-W4 human release decision remain open | multi-agent eval, replay, CI, failure triage, rollback policy, trace report, and human release decision | Eval / Release | implemented | Phase 12 |

### P12-W1 Backfill — Executable L5 Eval Suite Foundation

Status:

- P12-W1 implementation slice is complete.
- L5-006 moves from blocked to implemented.
- This does not close L5-006.
- This is not L5 release and not Phase 12 release gate closure.

Code / eval evidence:

- Executable runner:
  - scripts/evals/run_l5_eval_suite.py
- Executable Phase 12 suite / datasets:
  - tests/evals/phase12/suite.json
  - tests/evals/phase12/datasets/*.jsonl
- Phase 12 eval gate test:
  - tests/evals/test_phase12_l5_eval_gate.py
- CI binding:
  - .github/workflows/eval-gate.yml

Validation evidence:

- PYTHONPATH=.:apps/api .venv/bin/python -m pytest tests/evals/test_phase12_l5_eval_gate.py -q -> 6 passed.
- PYTHONPATH=.:apps/api .venv/bin/python -m pytest tests/evals -q -> 41 passed.
- PYTHONPATH=.:apps/api .venv/bin/python -m pytest tests/architecture -q -> 33 passed.
- PYTHONPATH=.:apps/api .venv/bin/python scripts/evals/run_l5_eval_suite.py --mode deterministic -> blocking_failures=0, total_cases=9.
- Phase 12 negative control -> observed_expected_failure=true.
- Phase 9 runner and negative control passed.
- git diff --check -> passed.

Remaining gap:

- P12-W2 replay / resume / failure fixtures remain open.
- P12-W3 observability / trace report remains open.
- P12-W4 release readiness audit and human release decision remain open.
- Real-provider quality certification is not claimed.

### P11-W4 Backfill — Controlled Tool Loop / HITL

Status: `runtime_bounds_hitl_slice_complete_with_deferred_release_gate` for controlled runtime-boundary hardening only. This is not `done` for `L5-005`, not L5 release, not real-provider quality certification, not remote CI success and not Phase 12 release gate completion.

- P11-W4 validates bounded runtime metadata for `max_steps`, `max_retries`, `timeout_seconds`, `stop_conditions`, `repair_strategy` and `fallback_semantics`.
- Runtime-reported bound exhaustion cannot be reported as success; accepted exhaustion must be non-success with a matching stop condition or failure reason.
- HITL trigger metadata is validated for formal write, asset conflict, low confidence, ambiguous ownership and validation-failed partial result; `hitl_required=true` cannot be reported as success.
- Runtime tool-call metadata must stay scoped to allowed tool refs and must not expose repository, DB, SQLAlchemy session, unit-of-work or formal writer handles.
- Candidate/formal and fallback boundaries remain enforced: fallback, validation failure or provider-unavailable markers cannot be reported as generated success or formal write success.
- `L5-006` remains release-blocking Phase 12 scope; executable eval/replay/CI/report/human decision evidence is still required before any L5 release claim.

### P11-W5 Integration / Boundary Tests Backfill

Status: `validated_with_deferred_gaps` for `L5-002` through `L5-004`; `validated` for `L5-005` controlled runtime-boundary hardening only. No L5 capability is marked `done`.

- P11-W5 adds architecture validation coverage for Supervisor / Orchestrator registration, non-release wording, no runtime/provider/API/DB/domain wiring, three-business-agent candidate workflow evidence, typed feedback -> asset -> training handoff refs and trace / validation / handoff separation.
- P11-W5 validates candidate-only and formal-write boundaries in the window validation scope: happy path emits `feedback_candidate`, `asset_update_candidate` and `training_plan_candidate` refs only; formal-write request blocks before candidate or handoff success; asset conflict blocks before asset/training candidates.
- P11-W5 carries P11-W4 controlled-loop / HITL evidence as `L5-005` validated boundary evidence after Matrix and Risk Register backfill; this does not implement Phase 12 eval/replay/CI/report/human decision evidence.
- Required validation commands for this window are `pytest tests/architecture`, `pytest tests/evals` and `pytest tests/api`; local command output must be recorded in the final window report before any closure claim.
- `L5-006` remains release-blocking. P11-W5 does not claim L5 release, real-provider quality certification, remote CI success, formal F8/M8 release or Phase 12 release gate completion.

## P10 Stage Closeout / Source Backfill Evidence

Status: `closed_with_deferred_gaps` for Phase 0-10 L5 Foundation closeout；`complete_with_deferred_remote_ci_gap` for the accepted Phase 9 final state。

- `EVAL-001` remains `validated`, not `done`: deterministic replay / fixture regression foundation is locally validated, but remote GitHub Actions execution is unavailable/deferred and committed eval report metadata still embeds short SHA `f86adea`.
- Current implementation fact: `HEAD` and `origin/main` both resolve to `76c670c859d3f7d32d13e604b3d0edffeefd2048` in the Phase 10 recon.
- Non-mutating current rerun evidence: `python3 scripts/evals/run_eval_gate.py --suite phase9 --mode replay --report-dir /tmp/aifi-p10-closeout-eval-reports` passed with `30 passed`, `0 blocking_failures`, `2 deferred`, and report metadata for current behavior showed short SHA `76c670c`.
- Required eval test evidence: `PYTHONPATH=.:apps/api .venv/bin/pytest tests/evals -q` passed with `27 passed`.
- Negative-control evidence: `python3 scripts/evals/run_eval_gate.py --suite phase9 --mode replay --expect-fail-fixture` observed the expected `must_not_have_present` blocking failure.
- `deferred_remote_ci_gap` is explicit: no GitHub Actions run/artifact is claimed by Phase 10.
- Phase 8 runtime gaps remain `validated_with_deferred_gaps` / `partial_with_deferred_gaps`; Phase 10 does not close them.
- At Phase 10 closeout time, Phase 11 Supervisor / Orchestrator and Phase 12 L5 release were `not_started` / deferred and could not be inferred from Phase 0-10 foundation closure. Later P11 rows above carry the current Phase 11 evidence status.
- Committed report metadata risk is residual only: Phase 10 does not rewrite `evals/reports/**`.

## P11-W0 Scope Lock / Gap Reconciliation Evidence

Status: `scope_lock_complete_with_deferred_gaps` for docs-only P11-W0 reconciliation. This status does not apply to L5 implementation capabilities.

- `L5-001` is `design_done` because P11-W0 locks the L5 target and source wording.
- At P11-W0 scope-lock time, `L5-002` through `L5-006` were not implemented, validated or done; current capability rows above supersede this historical window status.
- `deferred_remote_ci_gap`, Phase 8 runtime gaps, stale committed eval report metadata short SHA `f86adea`, Supervisor / Orchestrator not started, Phase 12 release gate not started and real-provider quality certification non-claim are carried forward.
- P11-W0 code recon found C1 Question / Feedback catalog and P8 foundation contracts/runtime/handoff surfaces, but no registered Supervisor / Orchestrator and no three-or-more-business-agent product workflow at that time.
- Decision options for the next window remain `proposed`; no option is confirmed by this matrix.

## P11-W1 Contract-first Orchestrator Evidence

Status: `contract_slice_complete_with_deferred_runtime_gaps` for Option A contract-first implementation. This status applies only to contract/catalog/test evidence and does not close runtime, product workflow, remote CI, stale eval report, real-provider quality or release gaps.

- `L5-002`: `interview_orchestrator_agent` exists as a contract-only AgentDefinition with candidate outputs only, no formal outputs, no direct DB/repository write, no runtime execution and no L5 release claim.
- `L5-003`: cross-agent plan / step / handoff route / state / trace contracts exist, normalize tuple/list inputs, fail closed on required IDs/refs and filter forbidden metadata keys.
- P11-W1 contract slice is implemented and locally validated for contract/catalog/test evidence only; full L5 capability validation, runtime execution, product workflow and release gate remain deferred.
- Registry / catalog evidence: `build_default_agent_platform_l5_contract_registries()` composes the existing Question / Feedback C1 contracts with the Orchestrator contract and validates agent->skill/tool references without replacing `build_default_agent_platform_c1_registries()`.
- Tool evidence: Orchestrator ToolDefinition records are contract-only, `read_only` or `forbidden`, and ToolRegistry still rejects repository / DB / SQLAlchemy / session / formal writer exposure.
- Validation evidence: P11-W1 architecture and contract tests cover no runtime wiring, candidate-only outputs, non-claims, required trace/validation refs and forbidden data.
- P11-W1 does not implement product multi-agent workflow.
- P11-W1 does not execute Supervisor / Orchestrator at runtime.
- P11-W1 does not close Phase 8 runtime gaps.
- P11-W1 does not close `deferred_remote_ci_gap`.
- P11-W1 does not rewrite stale eval reports.
- P11-W1 does not certify real-provider quality.
- P11-W1 does not claim L5 release.
- P11-W1 does not implement Phase 12 release gate.

## P11-W2 Runtime-hardening Slice Evidence

Status: `runtime_hardening_slice_complete_with_deferred_product_workflow` for a narrow runtime-hardening slice. This status applies only to internal Agent Platform runtime-facing primitives and focused local tests. It is not product multi-agent workflow completion, not Orchestrator runtime execution, not full Phase 8 runtime gap closure and not L5 release.

- `L5-005`: cross-agent runtime-hardening helpers now fail closed for route-bound handoff source/target mismatch, invalid candidate type, missing required trace refs, missing required validation refs, formal refs, unsafe metadata, missing checkpoint/base_version/idempotency, owner mismatch, unsupported resume action, non-read-only replay, formal-write-enabled replay, collapsed trace/timeline refs, unsafe trace metadata and HITL success-like failure semantics.
- `L5-003`: contract and handoff surfaces are hardened only where this window directly touches cross-agent handoff validation; full runtime execution and product workflow validation remain deferred.
- `L5-004`: remains `not_started`; no three-or-more-business-agent product workflow is implemented.
- `L5-006`: remains `not_started`; no Phase 12 eval/replay/release gate is implemented.
- P11-W2 adds `tests/application/agents/test_phase11_runtime_hardening.py` and updates focused P8/API/architecture gates.
- P11-W2 does not execute `interview_orchestrator_agent` as a runtime agent.
- P11-W2 does not wire Orchestrator into `AgentExecutor`, LangGraph, `AiOrchestrationFacade`, API routes, Question workflow, Feedback workflow, provider, prompt, DB, frontend or domain policies.
- P11-W2 does not close `deferred_remote_ci_gap`.
- P11-W2 does not rewrite stale eval reports.
- P11-W2 does not certify real-provider quality.
- P11-W2 does not claim L5 release.
- P11-W2 does not implement Phase 12 release gate.

## P11-W3 Minimal Three-Agent Candidate Product Slice Evidence

Status: `candidate_product_slice_complete_with_deferred_formal_write_and_release_gate` for a minimal refs-only product vertical slice. This status applies only to L5-004 candidate workflow evidence. It is not formal write completion, not L5 release, not real-provider quality certification, not remote CI success and not Phase 12 release gate completion.

- `L5-004`: deterministic refs-only product slice exists under `app.application.agents.orchestration.minimal_three_agent_slice`.
- The participant business agents are `polish_feedback_agent`, `asset_candidate_agent` and `training_plan_agent`.
- The L5 contract catalog registers `asset_candidate_agent` and `training_plan_agent` through the project-level AgentDefinition / Skill / Tool registries while the C1 catalog remains Question / Feedback only.
- Happy path emits candidate refs only: `feedback_candidate`, `asset_update_candidate` and `training_plan_candidate`.
- Handoff refs connect `feedback_candidate` to `asset_update_candidate`, then `asset_update_candidate` to `training_plan_candidate`.
- Asset update candidates require user confirmation and keep `formal_write_blocked`.
- Missing required refs fail closed; asset conflict and formal write request block the workflow; low confidence remains trace-visible.
- Trace refs and validation refs remain separated in the result and timeline metadata.
- P11-W3 does not call LLM or provider.
- P11-W3 does not render prompts.
- P11-W3 does not read or write DB.
- P11-W3 does not call repositories.
- P11-W3 does not modify provider, prompt, API, DB, frontend, domain policy, application polish behavior, eval datasets, eval graders, eval suites, eval reports, scripts or workflow files.
- P11-W3 does not write formal assets, feedback, progress, scores, reports or training plans.
- P11-W3 does not certify real-provider quality.
- P11-W3 does not claim L5 release.
- P11-W3 does not implement Phase 12 release gate.
- `L5-006`: remains `not_started`; no Phase 12 eval/replay/release gate is implemented.

## P11-W4 Phase 11 Closeout / Source Sanity Evidence

Status: `phase11_closed_with_deferred_release_gate` for Phase 11 closeout summary only. This is not a Matrix capability status upgrade, not L5 release, not Phase 12 release gate completion and not a `done` status for any L5 capability.

- P11-W4 reconciles P11-W0 through P11-W3 evidence and accepts the controller decision that P11-W3 post-push audit is `post_push_audit_passed`.
- Phase 11 is closed as controlled multi-agent foundation plus a minimal candidate-only product slice.
- At P11-W4 closeout time, `L5-001` remained `design_done`.
- At P11-W4 closeout time, `L5-002` remained `contract_slice_complete_with_deferred_runtime_gaps`.
- At P11-W4 closeout time, `L5-003` remained `contract_slice_complete_with_deferred_runtime_gaps`.
- At P11-W4 closeout time, `L5-004` remained `candidate_product_slice_complete_with_deferred_formal_write_and_release_gate`; candidate product slice only, not release.
- At P11-W4 closeout time, `L5-005` remained `runtime_hardening_slice_complete_with_deferred_product_workflow`; runtime-hardening slice only, not full runtime closure.
- `L5-006` remained `not_started` at P11-W4 closeout time and remains release-blocking in the current Matrix row.
- `EVAL-001` remains `validated`; P11-W4 does not upgrade eval / replay / release gate status.
- No L5 capability is marked `done`.
- Phase 12 release gate remains open.
- Remote CI artifact evidence remains open.
- Real-provider quality certification remains open.
- Formal write remains open and must go through Application Service -> Domain Policy -> Handoff.
- L5 release remains open.
- Multi-agent eval / replay / release evidence remains open.

P11-W4 non-claims:

- P11-W4 does not modify code, tests, eval datasets, eval suites, eval graders, eval reports, scripts, workflows, provider, prompt, API, DB, frontend or domain policy files.
- P11-W4 does not claim real-provider quality certification.
- P11-W4 does not claim remote CI success.
- P11-W4 does not claim formal write completion.
- P11-W4 does not claim product workflow release.
- P11-W4 does not claim full L5 validation complete.
- P11-W4 does not mark `L5-006` implemented, validated or done.

## P12-W0 Release Gate Scope Lock Evidence

Status: `release_gate_scope_locked_with_deferred_implementation` for docs-only scope lock. This is not an implementation status for `L5-006`, not a release gate completion status and not a `done` status for any L5 capability.

- P12-W0 creates release-gate scope, release evidence contract, decision options and source-backfill report under `docs/goals/2026-06-06/`.
- `L5-006` remains `not_started` in the Matrix row; no multi-agent eval/replay/release gate implementation is claimed.
- `EVAL-001` remains `validated`; P12-W0 does not upgrade replay / fixture evidence into Phase 12 release evidence.
- Required Phase 12 evidence is defined for eval, replay, CI, observability and human release decision, but implementation remains pending Controller/user option choice.
- Remote CI gap remains open unless a visible passing CI run and uploaded artifact are cited.
- Real-provider quality certification remains a non-claim unless a separately scoped provider evidence window records provider config, redaction, human review and non-fake results.
- Formal write remains Application Service -> Domain Policy -> Handoff and is not changed by P12-W0.

P12-W0 non-claims:

- P12-W0 does not modify code, tests, eval datasets, eval suites, eval graders, eval reports, scripts, workflows, provider, prompt, API, DB, frontend, runtime or domain policy files.
- P12-W0 does not claim L5 release.
- P12-W0 does not claim real-provider quality certification.
- P12-W0 does not claim remote CI success.
- P12-W0 does not claim formal write completion.
- P12-W0 does not claim product workflow release.
- P12-W0 does not claim full L5 validation complete.
- P12-W0 does not mark `L5-006` implemented, validated or done.

## P12-W1 Eval-contract-first Evidence

Status: `eval_contract_slice_complete_with_deferred_runner_ci_release` for contract-only eval artifacts and static contract tests. This status is not an implementation status, not a validation status, not a release gate completion status and not a `done` status for `L5-006` or any L5 capability.

- Controller selected P12-W0 Option A Eval-contract-first for P12-W1.
- P12-W1 creates `evals/suites/phase12.json`, `evals/datasets/phase12/*.jsonl`, `evals/graders/phase12_contract.json`, `evals/schemas/phase12_release_report_schema.json` and `tests/evals/test_phase12_eval_contracts.py`.
- The Phase 12 suite manifest, dataset skeletons, grader contract and release report schema are contract-only artifacts.
- Static contract validation passed locally: `PYTHONPATH=.:apps/api .venv/bin/pytest tests/evals/test_phase12_eval_contracts.py -q` reported `8 passed`; `PYTHONPATH=.:apps/api .venv/bin/pytest tests/evals -q` reported `35 passed`.
- `EVAL-001` remains `validated`; P12-W1 does not upgrade Phase 9 replay / fixture evidence into Phase 12 release evidence or remote CI evidence.
- Runner behavior, CI workflow binding, replay execution, report generation, remote CI artifact evidence, real-provider quality certification and human release decision remain deferred.

P12-W1 non-claims:

- P12-W1 does not implement eval runner behavior.
- P12-W1 does not run or complete a Phase 12 release gate.
- P12-W1 does not modify CI workflows.
- P12-W1 does not generate or rewrite eval reports.
- P12-W1 does not claim L5 release.
- P12-W1 does not claim real-provider quality certification.
- P12-W1 does not claim remote CI success.
- P12-W1 does not mark `L5-006` implemented, validated or done.
- P11-W4 does not mark any L5 capability done.

## P12-W2 Preflight Stop Backfill Evidence

Status: `complete_preflight_stop` for P12-W2 preflight only. Blocker: `blocked_by_missing_executable_phase12_eval_suite`.

- 总控 accepted P12-W2 preflight stop for `P12-W2-REPLAY-RESUME-FAILURE-FIXTURES`.
- P12-W2 replay / resume / failure fixtures were not implemented.
- `evals/suites/phase12.json` is `contract_only`; its Phase 12 suite flags keep `eval_runner_required=false` and `release_gate_pass_required=false`.
- `evals/graders/phase12_contract.json` is a data contract, not an executable Python grader; its deferred implementation block still records no Python grader, runner integration, CI binding, report generation or negative-control execution created in P12-W1.
- `.github/workflows/eval-gate.yml` remains bound to the Phase 9 eval gate only.
- Existing Phase 12 eval artifacts cannot support P12-W2 replay fixture validation; `P12-W1-MULTI-AGENT-EVAL-SUITE` must be inserted before retrying P12-W2.
- Preservation evidence: `PYTHONPATH=.:apps/api .venv/bin/python -m pytest tests/evals -q` reported `35 passed`; `PYTHONPATH=.:apps/api .venv/bin/python -m pytest tests/architecture -q` reported `33 passed`.
- `L5-006` remains release-blocking and is not marked implemented, validated, done or released by this preflight stop.

P12-W2 preflight non-claims:

- P12-W2 does not implement replay fixtures.
- P12-W2 does not implement resume fixtures.
- P12-W2 does not implement failure fixtures.
- P12-W2 does not modify code, tests, CI, provider, prompt, DB, API, frontend, eval runners, eval graders, eval reports or workflow behavior.
- P12-W2 does not claim L5 release, real-provider quality certification, remote CI success or Phase 12 release gate closure.

## P9 Eval / CI Regression Gate Backfill Evidence

Status: `validated` for `EVAL-001` replay/fixture regression foundation；post-push accepted status is `complete_with_deferred_remote_ci_gap` because remote GitHub Actions evidence remains deferred；不得解读为 real-provider quality、P8 runtime closure 或 L5 release。

- `EVAL-001`: `evals/suites/phase9.json` binds the Phase 9 suite to capability IDs, dataset refs, grader refs, minimum pass criteria and CI blocking behavior. `scripts/evals/run_eval_gate.py` runs deterministic `replay` / `fixture` suites, emits JSON + Markdown reports, scans generated reports before write, and returns non-zero on blocking eval failures.
- `CTX-001` / `CTX-002` / `CTX-003`: `evals/datasets/phase9/canonical_evidence.jsonl` adds direct project evidence, adjacent hypothetical, job-gap no-fact-claim and insufficient-context deferred cases.
- `QAG-004` / `QAG-006` / `QAG-007`: `evals/datasets/phase9/question_agent.jsonl` adds grounding-blocked, follow-up anti-repetition, deterministic fallback-not-success and `question_candidate` trace/validation/handoff-ref cases.
- `FAG-006` / `FAG-007` / `FAG-008`: `evals/datasets/phase9/feedback_agent.jsonl` adds asset-conflict next-action blocking, asset candidate confirmation, answer coverage, same-question answer change, provider-unavailable and validation-failed non-success cases.
- `PRO-001` / `PRO-002`: `evals/datasets/phase9/provider_boundary.jsonl` plus `evals/graders/code_rules.py` add report/provider forbidden-data, no full prompt asset fallback and fail-closed reason-code coverage. The production provider boundary was not modified.
- `FAKE-001`: `evals/datasets/phase9/fake_gate.jsonl` records fake/replay visible non-claims and runtime fake rejection as regression evidence only. Runtime fake rejection was not weakened.
- `AGT-006` / `AGT-007`: `evals/datasets/phase9/handoff_trace.jsonl` adds refs-only `question_candidate`, `feedback_candidate` and `asset_update_candidate` handoff/trace coverage without formal refs.
- P8 / L5 guard: `evals/datasets/phase9/runtime_foundation_contract.jsonl` only protects existing P8 partial foundation surfaces and records future/product runtime surfaces as `deferred_with_reason`.
- Report evidence: `docs/goals/2026-06-06/P9_EVAL_REPORT.md` and `evals/reports/phase9_eval_report.json` record 30 passed cases, 0 failed, 0 blocking failures, 2 explicit deferred cases and replay/fake/L5 non-claims.
- Negative control: `python scripts/evals/run_eval_gate.py --suite phase9 --mode replay --expect-fail-fixture` observes `p9_nc_job_gap_claims_completed_work` failing for `must_not_have_present`, proving blocking eval failures can make the gate non-zero.
- CI evidence: `.github/workflows/eval-gate.yml` runs `python -m pytest tests/evals -q`, the Phase 9 replay gate and the negative-control gate without live provider credentials; `package.json` registers `eval:gate` and `eval:gate:negative`.

Non-claims:

- Replay/fixture eval pass is not real-provider quality evidence.
- P9 does not implement or close Phase 8 runtime deferred gaps.
- P9 is L5 Foundation regression evidence only, not L5 release.
- No prompt/provider/API/DB/frontend/domain-policy production behavior changed in this Phase 9 backfill.

## P7-W1 Provider Fail-Closed Backfill Evidence

Status: `validated_with_deferred_gaps`，不得标记 `done`。

- `PRO-001`: `apps/api/app/application/llm/provider_boundary.py` adds the P7 forbidden-key catalog and validator. Question and Feedback active provider paths call `build_validated_transport_request()` before `transport.generate()` and fail closed with `provider_request_validation_failed` / `provider_request_invalid` when validation fails.
- `PRO-002`: Validation evidence recorded in `docs/goals/2026-06-05/P7_D_IMPLEMENTATION_REPORT.md` and independently audited in `docs/goals/2026-06-05/P7_E_AUDIT_REPORT.md`: provider boundary static tests `2 passed`; provider / fake / runtime selector `15 passed`; Question regression `65 passed`; Feedback service / agent / runtime selector `44 passed`; provider selector `19 passed`; Feedback selector `63 passed`; architecture selector `22 passed`; `git diff --check` clean.
- `FAKE-001`: `FeedbackGenerationService(FakeLlmTransport())` returns fake-visible non-success with `fake_transport_not_runtime_provider`, `provider_status=fake_transport`, and `llm_called=False`; runtime fake rejection and fixture isolation remain covered by focused tests. Fake fixture availability for tests/evals/replay is preserved.
- `WIN-001`: Agent A/B/C read-only recon, Controller scope lock, Agent D implementation report, and Agent E audit report exist under `docs/goals/2026-06-05/`. Agent E returned `WARN`, allowing source backfill but not a `done` claim.
- `SRC-001`: This section plus the Phase 7 updates in `14_RISK_REGISTER.md` and `17_PHASE_ROADMAP_LOCK.md` are the P7 Project source backfill.

Remaining gaps:

- Only Q/F active provider paths are proven protected; the new boundary is not a global transport backstop for all `LlmTransportRequest` call sites.
- Feedback compact prompt still includes a bounded `current_answer` excerpt; a short answer could equal the complete answer text.
- Single-writer identity is `UNKNOWN` from current worktree evidence; only scope conformance is proven.
- Full-repo pytest, web tests, and e2e tests were not run.

## P7-W2 Provider Global Backstop Evidence

Status: `validated_with_deferred_gaps`，不得标记 `done`。

- `PRO-001`: `apps/api/app/application/llm/types.py` 为 `LlmTransportRequest` 增加 DTO-level recursive forbidden-key backstop，覆盖 `dataclasses.replace(...)` mutation paths。`apps/api/app/application/polish/progress_tree.py`、`apps/api/app/infrastructure/llm/job_match.py`、`apps/api/app/application/ai_runtime/business_graphs/polish_feedback_graph.py` 已在 transport 前使用 `build_validated_transport_request()`。
- `PRO-002`: `tests/architecture/test_provider_boundary_static.py` 拒绝 `provider_boundary.py` 之外的 production direct `LlmTransportRequest(...)` constructors。`tests/api/test_provider_global_backstop.py` 证明 direct DTO bypass、replace injection、progress tree unsafe prompt、job match unsafe payload 均在 transport 前失败。
- `FAKE-001`: existing fake runtime rejection 与 feedback direct fake non-success 行为仍由 required narrow suite 覆盖；本窗口未新增 fake runtime provider path。
- `WIN-001`: A/B/C recon、D implementation report、E audit report、F source backfill report 已落在 `docs/goals/2026-06-05/`。
- `SRC-001`: This section plus the P7-W2 updates in `14_RISK_REGISTER.md` and `17_PHASE_ROADMAP_LOCK.md` are the P7-W2 Project source backfill.

P7-W2 gap classification:

- `P7-GAP-001`: 当前 production `LlmTransportRequest` call sites 为 `validated`；static gate 防止新增 production direct constructors。
- `P7-GAP-002`: `partially_mitigated`；DTO-level forbidden-key backstop 已存在，但 per-task schema compactness 仍由 builder / static gate 证明，而不是 universal runtime schema registry。
- `P7-GAP-003`: `deferred`；bounded `current_answer.answer_text` 可能等于完整短回答，需要 product/security policy decision。
- `P7-GAP-004`: `partially_mitigated`；D/E reports 已记录 single-writer sequence，但 worktree identity proof 无法由机器独立验证。
- `P7-GAP-005`: `deferred`；full-repo pytest、web tests、e2e tests 未运行。

## P7-W3 Answer Excerpt Policy Backfill Evidence

Status: `validated_with_deferred_gaps`，不得标记 `done`。

- Controller Decision B is now the active answer excerpt policy for Feedback provider requests: `current_answer.answer_text` is allowed only as bounded current-answer primary task input and must not be represented as `full_answer`.
- `PRO-001`: `apps/api/app/application/polish/feedback_prompt_assets.py` records `answer_text_policy=current_answer_bounded_primary_input`, `answer_text_max_chars=1200`, `answer_text_is_bounded=true`, and `full_answer_forbidden=true` under both prompt asset / provider prompt `current_answer` and `input_contract`.
- `PRO-002`: `tests/api/test_polish_feedback_generation_service.py` proves a short current answer may equal submitted text while carrying bounded policy metadata, provider prompt excludes forbidden keys, and historical same-question answers do not fallback to raw `answer_text`. `tests/api/test_polish_feedback_agent_io_alignment.py` proves nested `full_answer` fails closed before transport.
- `SRC-001`: This section plus the P7-W3 updates in `14_RISK_REGISTER.md`, `17_PHASE_ROADMAP_LOCK.md`, and `20_PHASE7_CLOSEOUT.md` are the P7-W3 Project source backfill.

P7-W3 gap classification:

- `P7-GAP-001`: `validated` from P7-W2；production direct constructor static gate remains in place.
- `P7-GAP-002`: `partially_mitigated`；per-task schema compactness remains builder / static-gate based, not universal runtime schema registry.
- `P7-GAP-003`: `closed_by_policy_and_tests`；Controller Decision B is formalized in provider request metadata and focused tests.
- `P7-GAP-004`: `partially_mitigated`；single-writer scope conformance is recorded, worktree identity proof remains machine-UNKNOWN.
- `P7-GAP-005`: `deferred`；full-repo pytest、web tests、e2e tests remain out of scope for P7-W3 / deferred to P7-W4.

## P7-W4.fix.01 Full Validation Blocker Remediation Backfill Evidence

Status: `done`。

- `PRO-001`: P7 compact provider request fail-closed behavior remains unchanged. Full validation did not modify provider runtime, application provider builders, API routes, DB, domain policies, Phase 8 runtime, or Phase 9 eval / CI gates.
- `PRO-002`: Full-repo pytest passed with `1067 passed in 86.00s`; focused temp / fake policy selector passed with `21 passed`; `git diff --check` passed.
- `FAKE-001`: `scripts/qa/authenticated-frontend-smoke.mjs` no longer sets `LLM_PROVIDER=fake`; runtime fake rejection remains covered by `tests/api/test_llm_runtime.py` and `tests/api/test_fake_llm_boundary.py`.
- `WIN-001`: Required execution board artifacts exist under `docs/goals/2026-06-05/P7_W4_FIX01_*.md`: A/B recon, C implementation, D validation, E audit.
- `SRC-001`: This section plus the P7-W4.fix.01 updates in `14_RISK_REGISTER.md`, `17_PHASE_ROADMAP_LOCK.md`, and `20_PHASE7_CLOSEOUT.md` are the P7-W4.fix.01 Project source backfill.

P7-W4.fix.01 gap classification:

- `P7-GAP-001`: `validated` from P7-W2 / P7-W4 full validation.
- `P7-GAP-002`: `partially_mitigated` by DTO-level forbidden-key backstop and builder / static gates; no Phase 7 done blocker remains.
- `P7-GAP-003`: `closed_by_policy_and_tests`.
- `P7-GAP-004`: `partially_mitigated`; execution sequence and diff audit are recorded, machine proof of human worktree identity remains outside code evidence.
- `P7-GAP-005`: `closed_by_full_validation`; full-repo pytest, `npm run web:test`, `npm run web:smoke:auth`, focused temp policy tests, runtime fake rejection tests, and required grep interpretation passed.

Phase result:

- Phase 7: `done`.
- Phase 8: `eligible_for_controller_decision`, not started.

## P8 Runtime Foundation Backfill Evidence

Status: `validated_with_deferred_gaps`，不得标记 `done`。

- `RTE-001`: `AgentGraphRunnerExecutorAdapter` exposes the current `AgentGraphRunner` through the `AgentExecutor` protocol surface. It maps start / resume / replay / status / timeline / cancel to project-owned AgentExecution DTOs, blocks non-empty formal refs, preserves runner output / interrupt / typed candidate payload refs, and `AiOrchestrationFacade` now routes all current facade start surfaces plus facade-created status / timeline / cancel for known runs through the adapter. Facade keeps a run owner guard before adapter read/cancel access, fails closed before runner timeline/cancel access when the known run descriptor lacks the requested entrypoint, Question/Feedback descriptors declare implemented `timeline` / `cancel` entrypoints, and the existing runner fallback remains for unknown runs.
- `RTE-002`: `AgentRuntimeLoopPolicy` records required max_steps / max_retries / timeout_seconds / stop_conditions / allowed_tools / allowed_callers / side_effect_policy, is required by the adapter, and rejects incomplete P8 required stop-condition sets (`max_steps_exceeded`, `timeout`, `validation_failed`, `tool_not_allowed`, `formal_write_requested`, `interrupt_required`, `provider_failed`). `GraphDescriptor` now carries runtime policy primitives; `AiOrchestrationFacade` injects validated `runtime_loop_policy` metadata into all current start surfaces plus resume/replay commands and fails closed before runner invocation when descriptor bounds are missing. Generic direct in-memory runtime start also requires valid `runtime_loop_policy` metadata before graph invocation. `AgentSideEffectGuard.authorize_tool_call()` now requires registered `ToolDefinition`, validates caller, permission scope, owner scope, side-effect policy and forbidden payload, and consumes `ToolDefinition.forbidden_data` keys recursively. Polish question concrete phase tools require registered runtime `ToolDefinition` lookup and fail closed when the runtime loop policy disallows the agent caller, candidate-write side effect, or a tool-declared forbidden-data payload; the Feedback PR8 provider trace gate also requires registered runtime `ToolDefinition` lookup before execution and fails closed on unregistered tool, caller mismatch, permission-scope mismatch, owner-scope mismatch, side-effect mismatch and tool-declared forbidden-data payloads. Feedback direct in-memory runner start now requires descriptor-matching `runtime_loop_policy` metadata, rejects missing or mismatched fields before fake payload construction, and strips that control-plane metadata before PR6 refs/digest payload validation. Polish question direct runtime policy includes the P8 `interrupt_required` stop condition. Architecture gate verifies current direct production `authorize_tool_call()` call sites pass non-`None` `tool=`. Full closure remains deferred for future / indirect graph tool-loop expansion outside the covered facade start surfaces and Question/Feedback direct paths.
- `RTE-003` / `RTE-004`: `AiOrchestrationFacade.replay_agent_run()` exposes replay without API contract change and fails closed unless replay is read-only and formal-write-blocked. `AgentReplayResult.metadata` now carries sanitized replay metadata; generic in-memory, Question and Feedback runtime replay preserve original failed / blocked / interrupted / cancelled status category as `replayed_*`, original status, failure/fallback reasons, refs-only trace comparison including Feedback validation refs, nested refs-only trace metadata, and zero provider/tool/repository/DB/formal-write counters through the facade and AgentExecutor adapter. `AgentReplayResult` rejects positive or unparseable provider/tool/repository/DB/formal-write side-effect counters, so replay outputs that report provider calls, external tool calls, repository access, DB business writes or formal business writes fail closed before adapter/facade success. `AiOrchestrationFacade.resume_interrupted_run()` now requires `checkpoint_ref`, strict non-negative integer `base_version` and `idempotency_key`, carries checkpoint/base/idempotency control fields into runner resume payload, fails closed on unsupported resume actions or descriptor-unsupported `resume` before runner invocation, and routes runner results through the AgentExecutor adapter formal-ref guard. Facade replay also rejects descriptor-unsupported `replay` before runner invocation, and `polish_question_graph` now declares the already-implemented `resume` entrypoint. `AgentInterruptService.create_hitl_interrupt()` now represents the P8 HITL matrix (`formal_write_attempt`, `asset_conflict`, `low_confidence_formal_update`, `ambiguous_ownership`, `validation_failed_partial_result`) with required checkpoint refs and `formal_refs=()`. HITL resume validates checkpoint ref, base version and allowed action. Generic in-memory runtime start now registers its user-confirmation interrupt through `AgentInterruptService` with checkpoint/base-version state, so generic runtime resume also validates checkpoint ref / base version / idempotency / allowed action before graph continuation and strips resume control fields from event metadata. Polish question concrete runtime and Feedback in-memory runtime now open checkpoint-bound runner HITL for refs-only P8 trigger metadata and do not report those paths as succeeded; low-confidence Feedback trigger refs populate trace/drawer flags; service-backed Question and Feedback runtime resume validates checkpoint ref / base version / idempotency / allowed action before graph continuation, and Feedback resume timeline preserves candidate / validation refs from the interrupted run.
- `RTE-005`: `AgentExecutionTrace` now carries `agent_version`, `ai_task_id`, `low_confidence_flags`, `failure_reason`, and `fallback_reason`, and `AgentExecutionTrace` / `AgentHandoffEnvelope` metadata recursively filters nested forbidden keys such as `raw_prompt`, `provider_payload`, `full_asset_body`, `full_resume`, `api_key` and `token`. Feedback status trace refs include validation refs for replay comparison while resume/cancel control metadata remains checkpoint-only. Runtime replay metadata preserves nested status `metadata.trace_refs` as refs-only metadata and promotes validation / handoff / tool / policy / provider / low-confidence refs for adapter trace mapping. Adapter traces map graph version, AI task id, validation refs, handoff refs, tool refs, policy refs, provider refs, low-confidence flags, failure reason, fallback reason and runtime event names when the runner provides those refs, and merge command metadata plus nested runtime `metadata.trace_refs` `tool_refs` / `policy_refs` / `provider_refs` / `validation_refs` / `handoff_refs` / `low_confidence_refs` with runtime result / timeline event refs. Runtime result/status/timeline metadata fails closed if it exposes non-empty `formal_refs`, non-zero formal-write counters or non-zero repository / DB business write counters, including common `formal_write_count` / `formal_writes` and repository / DB counter variants. Adapter timeline events merge event metadata refs and command `handoff_envelope` refs, expose event candidate refs and keep validation / handoff refs separate from output refs. Generic runtime start/resume/cancel events, Feedback service-backed resume/cancel events and Polish question / Feedback concrete runtime start plus Polish question cancel events emit refs-only checkpoint / validation / candidate / interrupt / output metadata where applicable; generic direct `run_started` / `run_resumed` / `run_succeeded`, Feedback direct `run_started` / `run_succeeded`, and Question direct `run_started` / `interrupt_opened` / `run_resumed` / resumed `run_succeeded` timeline events preserve P8 command `plan_refs` / `skill_refs` / `tool_refs` / `policy_refs` / `provider_refs` / `validation_refs` / `handoff_refs` / `low_confidence_flags` / failure / fallback metadata while filtering raw/provider/full payload. Question cancel checkpoint/validation refs remain separated. Cancel events preserve candidate/validation/output/checkpoint refs where applicable with zero provider/formal-write counters. Adapter status snapshots expose handoff refs from status metadata / trace refs and nested runtime `metadata.trace_refs`. Runtime DTO status taxonomy now covers run result/status/replay/task/interrupt refs and fails closed on unknown status or success-like status with `failure_reason`; Polish question application task status mapping now reuses the shared runtime status taxonomy for existing `AiTaskStatus` projection while preserving candidate-only success as `queued`; `AgentTraceBridge` and adapter metadata phase/tool event statuses reject unknown non-DTO status values before trace write/event emission.
- `RTE-006`: `AgentHandoffEnvelope` provides a typed candidate handoff envelope with candidate, schema, trace, validation, side-effect and idempotency refs plus refs-only asset update descriptor fields. Adapter execution result/status surfaces expose mapped handoff refs; source result candidate descriptors can be converted into target `AgentExecutionPlan` input refs through `HandoffContract` / `AgentHandoffEnvelope` without raw payload sharing; `execute_agent_handoff()` starts the target `AgentExecutor` from that typed handoff plan. Target executor timeline events surface handoff envelope candidate / validation / handoff refs without raw candidate payload sharing. Feedback in-memory runtime now emits typed refs-only `feedback_candidate` and `asset_update_candidate` payloads with validation refs, checkpoint-backed trace refs, `asset_body_ref` / `asset_schema_id` descriptors and no formal refs. Product-level Supervisor / L5 orchestration, raw asset body transfer and formal asset composition/write semantics remain deferred and must not be claimed as Phase 11 / L5 workflow.
- `RTE-007`: `.env.example` now documents `AIFI_AI_RUNTIME_LANGGRAPH_ENABLED=false`; `AgentGraphRunnerExecutorAdapter` fails closed when runtime result metadata reports fake-provider use or fail-open fallback reported as generated success; no dependency, prompt, provider, DB, API, frontend or domain policy behavior was changed.
- Validation evidence: latest facade start surface coverage `5 passed, 18 deselected in 0.15s`; latest facade-created status/timeline/cancel adapter routing coverage `1 passed, 22 deselected in 0.16s`; latest descriptor-supported resume/replay facade gate `2 passed, 23 deselected in 0.19s` after expected red failures; latest descriptor-supported timeline/cancel facade guard `2 passed, 25 deselected in 0.11s` after expected red failures and full facade regression `27 passed in 0.34s`; latest generic direct runtime start timeline ref-matrix gate `1 passed, 9 deselected in 0.44s` after expected red failure; latest generic direct runtime missing-policy gate `1 passed, 9 deselected in 0.41s` after expected red failure; latest generic direct runtime resume/succeeded ref-matrix gate `1 passed, 10 deselected in 0.56s` after expected red `KeyError: 'plan_refs'`; PR4 runtime regression `12 passed in 0.64s`; latest generic replay nested trace metadata gate `1 passed, 11 deselected in 0.61s` after expected red `KeyError: 'trace_refs'`; latest Feedback direct runtime start/succeeded ref-matrix gate `1 passed, 15 deselected in 0.52s` after expected red `RuntimeValidationError`; PR6 runtime regression `17 passed in 0.70s`; latest Feedback replay trace refs metadata gate `1 passed, 16 deselected in 0.59s` after expected red `KeyError: 'trace_refs'`; latest Question direct runtime start/resume/succeeded ref-matrix gate `1 passed, 13 deselected in 0.58s` after expected red `KeyError: 'plan_refs'`; Question graph integration regression `15 passed in 1.71s`, including application status taxonomy mapping; latest P8 application-layer AgentExecutor adapter gate `tests/application` `1 passed in 0.08s`; latest typed handoff execution gate `1 passed, 16 deselected in 0.09s`; latest Question cancel checkpoint/validation ref separation remediation `1 passed, 12 deselected in 0.68s` after expected red failure; latest adapter command metadata `validation_refs` / `handoff_refs` / `low_confidence_flags` trace/timeline merge remediation `2 passed in 0.16s` after expected red failures; latest nested runtime trace metadata extraction gate `1 passed, 17 deselected in 0.20s` after expected red failure; latest runtime formal-ref metadata guard `1 passed, 18 deselected in 0.12s` after expected red failure; latest runtime formal-write counter variant guard `1 passed, 19 deselected in 0.14s` after expected red failure; latest runtime repository / DB business-write counter guard `1 passed, 20 deselected in 0.13s` after expected red failure; latest runtime fake-provider / fail-open fallback metadata guard `2 passed, 21 deselected in 0.12s` after expected red failures; latest `test_agent_graph_runner.py` `23 passed in 0.27s`; earlier command metadata `tool_refs` / `policy_refs` / `provider_refs` remediation also passed. Latest Feedback direct runtime loop-policy gate remediation `2 passed in 0.51s` after expected red failures; latest Feedback status/replay validation-ref trace comparison remediation `1 passed in 0.65s`; latest nested metadata contract remediation `1 passed in 0.15s`; latest required P8 stop-condition contract remediation `1 passed, 14 deselected in 0.17s` after expected red failure; `tests/api/test_agent_contracts.py` passed `15 passed in 0.23s`; latest replay-status remediation focused tests `2 passed in 0.53s`; replay side-effect fail-closed focused tests `2 passed in 0.20s`; impacted runtime / replay / resume regression `43 passed in 1.93s`; focused core tests `157 passed in 3.63s`; architecture gate `24 passed in 1.49s` with `PYTHONPATH=.:apps/api`; latest `tests/api/test_agent*` `108 passed in 2.18s`; latest `tests/api` gate `719 passed in 64.71s (0:01:04)`; latest PR4-PR8 runtime/graph gate `97 passed in 6.01s`; latest full test-suite gate `1151 passed in 89.38s (0:01:29)`; latest P8 broad polish gate `tests/api/test_polish*` `286 passed in 19.28s`; `git diff --check` passed.

P8 deferred gaps:

- `P8-GAP-001`: all current facade start surfaces and facade-created status/timeline/cancel now route through `AgentGraphRunnerExecutorAdapter` for known runs, descriptor-unsupported timeline/cancel fail closed before runner invocation, and facade resume uses adapter result validation, but the adapter remains a compatibility foundation, not product-level Supervisor / L5 orchestration.
- `P8-GAP-002`: Feedback in-memory runtime emits typed refs-only `feedback_candidate` and `asset_update_candidate` payloads with refs-only asset body descriptors; raw asset body transfer and formal asset composition/write semantics remain deferred.
- `P8-GAP-003`: P8 HITL trigger matrix and checkpoint-bound resume validation exist at the interrupt service boundary; facade resume carries checkpoint/strict-base/idempotency control fields, validates allowed action and descriptor-supported `resume` before runner invocation, and blocks returned runtime formal refs through the adapter; facade replay rejects descriptor-unsupported `replay`; generic in-memory user-confirmation resume, Polish question concrete P8 trigger refs and Feedback in-memory five-trigger metadata refs use service-backed checkpoint/base/action/idempotency validation, and Feedback resume timeline preserves candidate / validation refs, but remaining product-level runtime wiring and concrete graph coverage outside the facade/generic/Question/Feedback paths remain deferred.
- `P8-GAP-004`: AgentExecutor-bound source result to target plan handoff foundation, `execute_agent_handoff()` target AgentExecutor start and target timeline ref visibility are implemented, but product-level Supervisor / L5 orchestration is not implemented; Phase 11 Supervisor / Orchestrator remains out of scope.
- `P8-GAP-005`: runtime trace/timeline DTO shape, recursive trace/handoff metadata filtering, Feedback status/replay validation-ref trace comparison, adapter mapping including command metadata and nested runtime `metadata.trace_refs` `tool_refs` / `policy_refs` / `provider_refs` / `validation_refs` / `handoff_refs` / `low_confidence_refs` plus command handoff envelope refs, generic runtime start/resume/cancel refs metadata including direct `run_started` / `run_resumed` / `run_succeeded` P8 command ref matrix preservation, Feedback direct `run_started` / `run_succeeded` P8 command ref matrix preservation, Feedback service-backed resume/start/cancel refs metadata, concrete Question start/resume/cancel-event refs metadata including Question cancel checkpoint/validation ref separation, and target handoff refs metadata are expanded, but remaining product/future runtime events do not yet prove the complete P8 reference set.
- `P8-GAP-006`: runtime DTO canonical status taxonomy exists for run result/status/replay/task/interrupt refs, Polish question application task status mapping reuses the shared runtime taxonomy for existing `AiTaskStatus` projection, `AgentTraceBridge` rejects unknown node/run-finished trace statuses, and adapter metadata phase/tool event statuses reject unknown values before trace event emission; DB persistence/API status taxonomy remains deferred.

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

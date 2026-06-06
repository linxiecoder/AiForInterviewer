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

## DEC-011 Phase 4 C1 Agent Contract Catalog

Status: confirmed

Decision:

Phase 4 P4-W1 采用项目级 C1 contract catalog 作为 C target 的下一步过渡切片：

- `polish_question_agent` 和 `polish_feedback_agent` 必须注册在项目级 `AgentDefinitionRegistry`。
- Question / Feedback skills 和 tools 必须注册在项目级 `SkillRegistry` / `ToolRegistry`。
- `ToolRegistry` 必须 fail-closed 校验 side-effect policy、required forbidden data 和 repository / DB / SQLAlchemy 直接暴露。
- Trace / Handoff / Eval refs 只作为 contract metadata 绑定，不执行 runtime。

Phase 4 C1 不做：

- Question / Feedback planned workflow runtime wiring。
- LangGraph / multi-agent runtime migration。
- Provider request builder / transport / prompt rewrite。
- API / DB schema / domain policy 行为改动。

Recommendation:

进入 Phase 5 / Phase 6 前必须重新 scope lock；不得把 C1 catalog 当作 runtime 接入完成。

## DEC-012 Agent Catalog Hygiene / Versioning Strategy

Status: confirmed

Decision:

P4-W1.fix.01 将 C1 catalog 从单文件 God Catalog 调整为聚合器：

- `catalog.py` 只保留 public C1 registry builder 和 project-level registry aggregation。
- Question / Feedback 的具体 AgentDefinition、SkillDefinition、ToolDefinition 定义下沉到 `definitions/polish/` 子模块。
- `agent.version` 使用稳定语义版本；定义结构使用 `schema_version`；执行窗口标记只进入 `catalog_revision`。
- `SkillDefinition` 保持 contract-only，但必须携带 purpose、implementation_ref、preconditions、postconditions、fallback_policy、definition_version、schema_version 和 test_refs。

P4-W1.fix.01 不做：

- Question / Feedback runtime wiring。
- LangGraph / multi-agent runtime migration。
- Provider request builder / transport / prompt rewrite。
- API / DB schema / domain policy 行为改动。

Recommendation:

后续 Phase 5 / Phase 6 可以复用 C1 catalog contract shape，但必须单独 scope lock runtime 行为；不得把 catalog revision 当作 runtime version。

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

## DEC-013 P5/P6 Planned Workflow Maturity Boundary

Status: confirmed

Decision:

`P5P6-W1-C2-C3-PLANNED-WORKFLOW-L5-FOUNDATION` 只实现 Phase 5 / Phase 6 的 C2 / C3 L2 planned guarded workflow：

- `polish_question_agent` 输出 `question_candidate`；fallback、fake、graph-disabled 或 validation failed 不持久化正式题目。
- `polish_feedback_agent` 输出 `feedback_candidate` / `asset_update_candidate`；资产更新候选必须 `user_confirmation_required=true`，且不直接写正式资产。
- Formal write 仍只能经 Application Service + Domain Policy + Handoff。
- 本窗口只推进 L5 Foundation，不实现 Phase 8 runtime、Phase 11 Supervisor / Orchestrator 或 Phase 12 L5 release gate。

Recommendation:

后续若要接入 AgentExecutor runtime、跨 Agent orchestration、CI eval gate 或 L5 release gate，必须分别进入 Phase 8 / Phase 9 / Phase 11 / Phase 12 的独立 scope lock。

## DEC-014 P8 Runtime Foundation Boundary

Status: Accepted for C4 foundation partial; not accepted as Phase 8 done.

Decision:

`P8-GOAL-ONE-SHOT-C4-RUNTIME` implements a C4 runtime foundation slice, not a product-level L5 workflow or release gate.

Accepted:

- LangGraph dependency decision is `existing`; no dependency or lock-file change is needed.
- `AgentGraphRunnerExecutorAdapter` is the compatibility bridge from current `AgentGraphRunner` runtime to the AgentExecutor-compatible boundary; facade-created starts now route through that adapter and adapter execution results preserve runner output / interrupt / typed candidate payload refs.
- Runtime loop bounds are represented by `AgentRuntimeLoopPolicy`; missing bounds fail closed at the AgentExecutor adapter boundary and at the facade-created command boundary through descriptor runtime policy metadata.
- Runtime tool authorization must fail closed without a registered `ToolDefinition`.
- Polish question concrete runtime phase tools must resolve registered runtime `ToolDefinition` entries before execution and fail closed on unregistered tools.
- Polish question direct runtime policy must include `interrupt_required` as a stop condition.
- Feedback PR8 provider trace gate must resolve a registered runtime `ToolDefinition` before execution and fail closed on unregistered trace-gate nodes.
- Replay through `AiOrchestrationFacade.replay_agent_run()` must be read-only and formal-write-blocked.
- P8 HITL interrupt types are represented at the interrupt service boundary and checkpoint-bound resume validation is required for those HITL interrupts.
- Feedback in-memory runtime must open checkpoint-bound runner HITL for refs-only `formal_write_attempt_ref`, `asset_conflict_ref`, `low_confidence_formal_update_ref`, `ambiguous_ownership_ref` and `validation_failed_partial_result_ref` metadata and keep those paths non-success / formal-write-blocked.
- Polish question concrete runtime must open checkpoint-bound runner HITL for refs-only P8 trigger metadata and keep those paths non-success / formal-write-blocked.
- Low-confidence Feedback HITL refs must populate trace and drawer flags.
- Feedback service-backed HITL resume timeline metadata must preserve candidate refs and validation refs from the interrupted run.
- Facade resume must require checkpoint/strict-base/idempotency control fields, fail closed on unsupported actions before runner invocation, and block returned runtime formal refs through the AgentExecutor adapter boundary.
- Generic in-memory runtime user-confirmation interrupts must be registered through `AgentInterruptService` so resume validates checkpoint ref / base version / idempotency / allowed action before graph continuation.
- Polish question concrete HITL resume must validate checkpoint ref / base version / idempotency / allowed action before graph continuation.
- Service-backed in-memory runner resume must validate checkpoint ref / base version / allowed action before graph continuation.
- Adapter traces may carry P8 validation / handoff / tool / policy / provider / low-confidence / failure / fallback refs when runtime metadata provides them.
- Generic runtime start/resume events and Polish question / Feedback concrete runtime start timeline events may carry refs-only checkpoint / validation / candidate / interrupt / output metadata where applicable.
- Adapter execution result/status surfaces may expose mapped handoff refs when runtime metadata or trace refs provide them.
- Source result candidate descriptors may be converted into target `AgentExecutionPlan` input refs only through `HandoffContract` / `AgentHandoffEnvelope`; raw candidate payload body, raw asset body, raw prompt and `formal_refs` must not cross this handoff metadata boundary.
- Asset update candidate handoff may expose refs-only `asset_body_ref` / `asset_schema_id`, user-confirmation and formal-write-blocked metadata as foundation evidence; it must not be read as formal asset composition/write or product-level Agent A -> Agent B orchestration.
- Target executor timelines may merge command handoff envelope candidate / validation / handoff refs for trace visibility, but must still exclude raw prompt, raw provider payload, raw asset body and raw candidate payload body.
- Runtime DTO status taxonomy must classify run result/status/replay/task/interrupt refs and fail closed on unknown status or success-like status with `failure_reason`; adapter result/status mapping must reuse that shared guard, and adapter metadata phase/tool event statuses must reject unknown non-DTO values before trace event emission.
- Feedback in-memory runtime emits typed refs-only `feedback_candidate` and `asset_update_candidate` payloads with validation refs, checkpoint-backed trace refs, refs-only asset body descriptors and no formal refs.
- Typed handoff is represented by `AgentHandoffEnvelope`; formal writes remain Application Service -> Domain Policy / validation -> Handoff -> Repository / Transaction.

Not accepted as done:

- Raw asset body transfer, formal asset composition/write semantics and product-level Supervisor / L5 orchestration.
- Future / indirect graph tool-loop expansion and full product runtime migration without shared loop-policy / registry consumption evidence.
- Remaining product-level runtime/orchestration wiring and runner-bound HITL emission / resume validation outside the already covered facade/generic/Question/Feedback paths.
- Complete trace population for remaining product/future runtime events outside current generic runtime plus Feedback service-backed resume, Question/Feedback start/resume-event and target handoff timeline coverage.
- Non-DTO persistence/API status taxonomy beyond the runtime DTO, trace bridge and adapter metadata event status guards.
- Phase 11 Supervisor / Orchestrator, Phase 12 L5 release gate, or formal F8/M8 release.

## DEC-015 Phase 9 Default Replay Eval Gate

Status: accepted

Decision:

Phase 9 introduces a deterministic offline replay/fixture eval gate as the default CI regression gate.

Accepted:

- The default gate is `python scripts/evals/run_eval_gate.py --suite phase9 --mode replay`.
- The suite registry lives at `evals/suites/phase9.json` and binds suite ID, capability IDs, dataset refs, grader refs, pass criteria, CI behavior, negative-control refs and non-claims.
- Phase 9 datasets live under `evals/datasets/phase9/` and are intentionally refs/reason-code based; they must not store raw prompt, raw completion, provider payload, full resume, full JD, full answer, full asset body, secrets, tokens, cookies or API keys.
- The gate writes a machine JSON report under `evals/reports/` and a Markdown evidence report under the requested docs/goals report directory.
- The gate must return non-zero on blocking eval failures and must provide a negative-control mode proving this behavior.
- The GitHub Actions job in `.github/workflows/eval-gate.yml` runs eval tests, replay gate and negative-control gate without live provider credentials.

Not accepted:

- Replay/fixture/fake-visible eval pass as real-provider quality evidence.
- Unit tests alone as AI quality proof.
- Phase 8 runtime gap closure.
- Phase 11 Supervisor / Orchestrator or Phase 12 L5 release gate.
- L5 release, formal F8/M8 release readiness, prompt/provider/API/DB/frontend/domain-policy behavior changes.

Recommendation:

Future real-provider or advisory eval modes must be separate, skipped by default unless explicit environment configuration exists, and must preserve the same report redaction and non-claim rules.

## DEC-016 Phase 9 Accepted with Deferred Remote CI Gap

Status: confirmed

Decision:

Accept Phase 9 as `complete_with_deferred_remote_ci_gap` during Phase 10 closeout/source-backfill.

Accepted:

- User-confirmed post-push audit verdict is `PASS_WITH_RISK`.
- Current implementation fact is `HEAD` / `origin/main` at `76c670c859d3f7d32d13e604b3d0edffeefd2048`.
- Local validation evidence includes `tests/evals` passing, deterministic replay eval gate passing with `30 passed`, `0 blocking_failures`, `2 deferred`, and negative-control expected failure observed.
- Non-mutating Phase 10 rerun to `/tmp/aifi-p10-closeout-eval-reports` proves current `76c670c` behavior without rewriting committed reports.
- Phase 9 deterministic replay/fixture gate remains L5 Foundation regression evidence only.

Not accepted:

- No remote GitHub Actions evidence is claimed.
- No committed eval report rewrite is authorized in Phase 10.
- Existing committed eval report metadata short SHA `f86adea` is not silently normalized; it is recorded as residual metadata risk.
- Phase 8 runtime gaps remain deferred.
- Phase 11 Supervisor / Orchestrator is not started.
- Phase 0-10 are L5 Foundation only, not L5 release or formal F8/M8 release.

Recommendation:

Enter Phase 11 only under a new scope lock that explicitly carries or resolves `deferred_remote_ci_gap`, preserves Phase 8 runtime gaps unless directly authorized for implementation, and keeps L5 release out of scope until a separate release gate.

## DEC-017 Phase 11 Scope Lock Target

Status: proposed

Decision:

Phase 11 target should be L5 Controlled Multi-Agent Orchestration.

Proposed scope:

- registered Supervisor / Orchestrator Agent
- typed cross-agent goal decomposition
- cross-agent plan contract
- typed cross-agent handoff contract
- cross-agent state / checkpoint / replay contract
- cross-agent trace timeline
- bounded tool loop with `max_steps` / `max_retries` / `timeout` / `stop_conditions`
- HITL triggers for asset conflict, formal write, low confidence, ambiguous ownership and validation failed with partial result
- at least one end-to-end product workflow with three or more business agents
- candidate-only output boundary
- formal write remains Application Service -> Domain Policy -> Handoff

Not accepted:

- L5 release claim
- unbounded autonomous swarm
- Agent direct DB / repository write
- Tool direct repository exposure
- provider full prompt / full resume / full JD fallback
- prompt/provider/API/DB/frontend/domain behavior changes unless separately scoped
- committed eval report rewrite
- remote CI claim without visible run/artifact

Recommendation:

Controller/user must choose a next-window option before implementation. P11-W0 does not choose an option and does not implement Supervisor / Orchestrator.

## DEC-018 Phase 12 Release Gate Target

Status: proposed

Decision:

Phase 12 target should be L5 Eval, Hardening, and Release Gate.

Proposed scope:

- multi-agent regression suite
- cross-agent replay fixtures
- failure-mode regression cases
- L5 CI gate
- observability / trace report
- rollback policy
- failure triage policy
- remote CI artifact evidence
- human release decision

Not accepted:

- claiming L5 with unit tests only
- claiming L5 with fake-only or replay-only eval
- skipping replay / trace evidence
- release with unresolved candidate/formal boundary gaps
- release with unresolved provider fail-open gaps
- release without human/controller decision

Recommendation:

Do not start Phase 12 until Phase 11 implementation evidence, carried Phase 8 gap treatment, remote CI artifact policy and human/controller release criteria are explicit.

## DEC-019 P11-W1 Contract-first Orchestrator Option A

Status: accepted_for_p11_w1_contract_slice

Decision:

P11-W1 selects Option A: Contract-first Orchestrator.

Accepted scope:

- add contract-only `interview_orchestrator_agent` AgentDefinition.
- add cross-agent plan / step / handoff route / state / trace contracts.
- add contract-only Orchestrator SkillDefinition and ToolDefinition records.
- add `build_default_agent_platform_l5_contract_registries()` as a separate L5 contract catalog builder.
- keep Phase 4 C1 Question / Feedback catalog behavior backward-compatible.
- add architecture and API contract gates for candidate-only, no direct repository exposure, no runtime wiring and no release claim.

Not accepted:

- product multi-agent workflow.
- Supervisor / Orchestrator runtime execution.
- Orchestrator wiring into `AgentExecutor`, LangGraph, `AiOrchestrationFacade`, Question workflow, Feedback workflow, API routes or persistence.
- prompt/provider/API/DB/frontend/domain behavior changes.
- eval dataset, grader, suite, report, script or workflow changes.
- L5 release, real-provider quality certification, remote CI success, Phase 12 release gate completion or Phase 8 runtime gap closure.

Result:

P11-W1 may report `contract_slice_complete_with_deferred_runtime_gaps` only if code/tests/source-backfill validation passes and all forbidden paths remain untouched.

P11-W1 non-claims:

- P11-W1 does not implement product multi-agent workflow.
- P11-W1 does not execute Supervisor / Orchestrator at runtime.
- P11-W1 does not close Phase 8 runtime gaps.
- P11-W1 does not close `deferred_remote_ci_gap`.
- P11-W1 does not rewrite stale eval reports.
- P11-W1 does not certify real-provider quality.
- P11-W1 does not claim L5 release.
- P11-W1 does not implement Phase 12 release gate.

## DEC-020 P11-W2 Runtime-hardening Slice

Status: accepted_for_p11_w2_runtime_hardening_slice

Decision:

P11-W2 selects a narrow runtime-hardening slice for future controlled cross-agent orchestration.

Accepted scope:

- harden route-bound cross-agent handoff validation.
- add cross-agent resume/checkpoint validation helper and strict adapter opt-in.
- add cross-agent replay read-only / formal-write-blocked validation.
- add refs-only cross-agent trace/timeline mapping validation.
- add HITL trigger validation for `formal_write_requested`, `asset_conflict`, `low_confidence`, `ambiguous_ownership` and `validation_failed_partial_result`.
- update focused local tests and source backfill for the runtime-hardening slice only.

Not accepted:

- product multi-agent workflow.
- executing `interview_orchestrator_agent` as a runtime agent.
- Orchestrator wiring into `AgentExecutor`, LangGraph, `AiOrchestrationFacade`, Question workflow, Feedback workflow, API routes or persistence.
- prompt/provider/API/DB/frontend/domain behavior changes.
- eval dataset, grader, suite, report, script or workflow changes.
- L5 release, real-provider quality certification, remote CI success, Phase 12 release gate completion or full Phase 8 runtime gap closure.

Result:

P11-W2 may report `runtime_hardening_slice_complete_with_deferred_product_workflow` only if code/tests/source-backfill validation passes and all forbidden paths remain untouched.

P11-W2 non-claims:

- P11-W2 does not implement product multi-agent workflow.
- P11-W2 does not execute `interview_orchestrator_agent` as a runtime agent.
- P11-W2 does not close all Phase 8 runtime gaps.
- P11-W2 does not close `deferred_remote_ci_gap`.
- P11-W2 does not rewrite stale eval reports.
- P11-W2 does not certify real-provider quality.
- P11-W2 does not claim L5 release.
- P11-W2 does not implement Phase 12 release gate.

## DEC-021 P11-W3 Minimal Three-Agent Candidate Product Slice

Status: accepted_for_p11_w3_candidate_product_slice

Decision:

P11-W3 selects a minimal candidate-only three-business-agent product vertical slice.

Accepted scope:

- register `asset_candidate_agent` and `training_plan_agent` in the L5 contract catalog.
- keep C1 catalog behavior unchanged.
- add a deterministic refs-only product slice with `polish_feedback_agent`, `asset_candidate_agent` and `training_plan_agent`.
- emit candidate refs only: `feedback_candidate`, `asset_update_candidate` and `training_plan_candidate`.
- connect handoff refs from feedback to asset candidate and from asset candidate to training plan.
- require user confirmation for asset update candidates and keep formal writes blocked.
- fail closed on missing required refs and unsafe metadata.
- block or interrupt on asset conflict and formal write request.
- preserve trace refs and validation refs as separate metadata buckets.
- update focused local tests and source backfill for L5-004 only.

Not accepted:

- calling LLM or provider.
- rendering prompts.
- reading or writing DB.
- calling repositories.
- writing formal assets, feedback, progress, scores, reports or training plans.
- wiring `interview_orchestrator_agent` into API, ai_runtime, polish, domain or infrastructure.
- provider, prompt, API, DB, frontend, domain policy, application polish behavior, eval dataset, grader, suite, report, script or workflow changes.
- L5 release, real-provider quality certification, remote CI success, Phase 12 release gate completion or formal write completion.

Result:

P11-W3 may report `candidate_product_slice_complete_with_deferred_formal_write_and_release_gate` only if code/tests/source-backfill validation passes and all forbidden paths remain untouched.

P11-W3 non-claims:

- P11-W3 implements only a minimal candidate-only product slice.
- P11-W3 does not write formal assets, progress, scores, feedback, reports or training plans.
- P11-W3 does not call LLM or provider.
- P11-W3 does not modify provider, prompt, API, DB, frontend, domain policy or persistence behavior.
- P11-W3 does not certify real-provider quality.
- P11-W3 does not close Phase 12 release gate.
- P11-W3 does not claim L5 release.
- P11-W3 does not close remote CI gap.
- P11-W3 does not replace Phase 12 multi-agent eval.

## DEC-022 P12-W0 Release Gate Scope Lock

Status: accepted_for_p12_w0_scope_lock_only

Decision:

P12-W0 starts Phase 12 as a docs-only release-gate scope lock. It defines evidence requirements and proposed next-window options, but it does not implement Phase 12 eval / replay / CI / observability / release decision behavior.

Accepted scope:

- create release gate scope report.
- create release evidence contract.
- create proposed Phase 12 decision options.
- create source backfill report.
- update allowed Project sources and `docs/goals/README.md` only as needed.
- define eval, replay, CI, observability and release decision evidence requirements.
- define Phase 12 gate and stop conditions.
- keep next-window options proposed.

Not accepted:

- code, test, eval dataset, eval suite, eval grader, eval runner, eval report, script or workflow changes.
- provider, prompt, API, DB, frontend, runtime or domain policy behavior changes.
- eval runner behavior implementation.
- CI behavior implementation.
- L5 release, real-provider quality certification, remote CI success, Phase 12 release gate completion or formal write completion claims.
- marking `L5-006` implemented, validated or done.
- marking any L5 capability done.

Result:

P12-W0 may report `release_gate_scope_locked_with_deferred_implementation` if all created reports and source backfill stay inside the docs-only allowlist and final validation shows no implementation/eval/workflow files changed.

Next-window options:

- Option A Eval-contract-first: proposed.
- Option B Replay-gate-first: proposed.
- Option C CI-artifact-first: proposed.
- Option D Full Phase 12 eval gate slice: proposed.

No option is confirmed by this decision. Controller/user confirmation is required before implementation starts.

## DEC-023 P12-W1 Eval-contract-first Option A

Status: confirmed

Decision:

Controller selected P12-W0 Option A, Eval-contract-first, for P12-W1. This confirmation applies only to option selection and the contract-first slice. It is not a release completion decision.

Accepted scope:

- create `evals/suites/phase12.json`.
- create Phase 12 dataset skeletons under `evals/datasets/phase12/`.
- create `evals/graders/phase12_contract.json` as a data contract only.
- create `evals/schemas/phase12_release_report_schema.json` as a schema contract only.
- create static tests in `tests/evals/test_phase12_eval_contracts.py`.
- update allowed Project sources and `docs/goals/README.md` only as needed to record the contract-first slice.

Not accepted:

- eval runner behavior implementation or modification.
- CI workflow modification.
- release report generation or eval report rewrite.
- Phase 9 suite, dataset, grader or report modification.
- provider, prompt, API, DB, frontend, runtime or domain policy behavior changes.
- L5 release, real-provider quality certification, remote CI success, Phase 12 release gate completion or formal write completion claims.
- marking `L5-006` implemented, validated or done.

Result:

P12-W1 may report `eval_contract_slice_complete_with_deferred_runner_ci_release` only if contract artifacts and static tests pass, forbidden paths remain untouched and all non-claims are preserved. Runner behavior, replay execution, CI binding, report generation, remote CI artifact evidence and release decision remain deferred to separately scoped windows.

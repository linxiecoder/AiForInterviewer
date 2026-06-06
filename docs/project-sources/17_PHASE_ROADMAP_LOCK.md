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

P5P6-W1 Status:

- `P5P6-W1-C2-C3-PLANNED-WORKFLOW-L5-FOUNDATION` implemented a Phase 5 C2 / L2 planned guarded workflow bridge.
- `P5-W1.fix.01-QUESTION-PLANNED-WORKFLOW-REMEDIATION` added the dedicated production `apps/api/app/application/polish/agents/question/planned_workflow.py` component after audit found the earlier Question planned workflow claim overstrong.
- Question output is normalized to `question_candidate` before any formal write decision.
- graph-disabled、fake transport、deterministic fallback 和 validation failed path 不再持久化正式题目，也不报告 generated success。
- `P5P6-W1.fix.02-VALIDATION-BLOCKER-REMEDIATION` aligned the legacy canonical-evidence test to candidate-only semantics and cleared the broad API business failure.
- Current Question validation evidence: canonical evidence focused test `1 passed`, Question graph integration `12 passed`, Question persistence handoff `15 passed`, Question phase1 refactor `64 passed`, broad selector `300 passed, 323 deselected`, and local question eval `3 passed / 0 failed`.
- Phase 8 runtime、Phase 11 Supervisor / Orchestrator 和 Phase 12 L5 release gate 未实现。

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

P5P6-W1 Status:

- `P5P6-W1-C2-C3-PLANNED-WORKFLOW-L5-FOUNDATION` implemented a Phase 6 C3 / L2 planned guarded workflow handoff bridge.
- Feedback success path records `feedback_candidate` refs and policy / validation / handoff metadata.
- Asset update proposals are candidate-only and require `user_confirmation_required=true`; formal asset write remains blocked until user confirmation.
- Current Feedback validation evidence: Feedback runtime `7 passed`, local feedback eval `5 passed / 0 failed`, broad selector `300 passed, 323 deselected`; Phase 9 CI eval gate remains deferred.
- Phase 8 runtime、Phase 11 Supervisor / Orchestrator 和 Phase 12 L5 release gate 未实现。

## P5P6-W1 L5 Foundation Scope Lock

Status:

- `polish_question_agent`: C2 / L2 planned guarded workflow。
- `polish_feedback_agent`: C3 / L2 planned guarded workflow。
- Project: `validated_with_deferred_l5_runtime` for P5/P6 L2 planned guarded workflow; L5 Foundation progress only, not L5 release。

Non-claims:

- 不声明 autonomous Agent。
- 不声明 L5 done。
- 不声明 Phase 8 runtime complete。
- 不声明 Phase 9 CI eval gate complete。
- 不声明 Phase 11 / Phase 12 implemented。

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

P7-W1 Status:

- Phase 7 Status: `validated_with_deferred_gaps`。
- Implementation evidence: `apps/api/app/application/llm/provider_boundary.py`, `apps/api/app/application/polish/question_generation_service.py`, `apps/api/app/application/polish/feedback_agent.py`, `apps/api/app/application/polish/feedback_generation_service.py`, `apps/api/app/application/ai_runtime/contracts.py`, `apps/api/app/application/llm/agent_io.py`.
- Test evidence: provider boundary static tests `2 passed`; provider / fake / runtime selector `15 passed`; Question regression `65 passed`; Feedback service / agent / runtime selector `44 passed`; provider selector `19 passed`; Feedback selector `63 passed`; architecture selector `22 passed`; `git diff --check` clean.
- Audit evidence: `docs/goals/2026-06-05/P7_E_AUDIT_REPORT.md` returned `WARN`, not `FAIL`, and allowed source backfill.
- Source backfill evidence: `docs/project-sources/09_REFACTOR_TRACEABILITY_MATRIX.md`, `docs/project-sources/14_RISK_REGISTER.md`, `docs/project-sources/17_PHASE_ROADMAP_LOCK.md`, and `docs/goals/2026-06-05/P7_F_SOURCE_BACKFILL_REPORT.md`.
- Remaining gaps: only Q/F active provider paths are proven; no global provider backstop; bounded `current_answer` excerpt may equal a complete short answer; single-writer identity is `UNKNOWN`; full-repo pytest, web tests, and e2e tests were not run.
- Non-claim: Phase 7 is not `done`; Phase 8 / Phase 9 work must not start from this record alone.

P7-W2 Status:

- Phase 7 Status: `validated_with_deferred_gaps`。
- Implementation evidence: `apps/api/app/application/llm/types.py`、`apps/api/app/application/llm/provider_boundary.py`、`apps/api/app/application/polish/progress_tree.py`、`apps/api/app/infrastructure/llm/job_match.py`、`apps/api/app/application/ai_runtime/business_graphs/polish_feedback_graph.py`。
- Test evidence: static + global provider backstop `7 passed`；PR8 trace gate `10 passed`；job match `11 passed`；provider boundary `4 passed`；required narrow suite plus global backstop `144 passed`；global backstop standalone `4 passed`。
- Provider call-site result: 当前 production `LlmTransportRequest(...)` construction 仅限 `provider_boundary.py`；progress tree、job match、Question、Feedback、feedback trace requests 均使用 `build_validated_transport_request()`。
- Global backstop result: `LlmTransportRequest` 拒绝 recursive P7 forbidden keys，覆盖 direct construction 与 `dataclasses.replace(...)` injection。Per-task required / allowed top-level schema 仍由 validated builder 与 static gate 证明，而不是 universal runtime schema registry。
- Remaining gaps: bounded `current_answer.answer_text` 可能等于完整短回答；full-repo pytest、web tests、e2e tests 未运行。
- Non-claim: Phase 7 不是 `done`；不得仅凭本记录启动 Phase 8 / Phase 9。

P7-W3 Status:

- Phase 7 Status: `validated_with_deferred_gaps`。
- Controller Decision B: Feedback `current_answer.answer_text` is allowed as bounded current-answer primary task input and must not be represented as `full_answer`.
- Implementation evidence: `apps/api/app/application/polish/feedback_prompt_assets.py` adds answer text policy metadata under `current_answer` and `input_contract`, keeps the 1200 char bound, removes historical same-question `answer_text` evidence fallback, and expands Feedback prompt asset unsafe key filtering for `full_answer` / `full_asset_body`.
- Test evidence: `tests/api/test_polish_feedback_generation_service.py` covers bounded current answer policy metadata, short current answer equality, provider prompt forbidden-key absence, and historical no-raw-answer fallback. `tests/api/test_polish_feedback_agent_io_alignment.py` covers provider request policy metadata and nested `full_answer` fail-closed before transport.
- Gap result: `P7-GAP-003` is `closed_by_policy_and_tests`。
- Remaining gaps: `P7-GAP-005` full-repo pytest、web tests、e2e tests 未运行，deferred to P7-W4。
- Non-claim: Phase 7 不是 `done`；不得仅凭本记录启动 Phase 8 / Phase 9。

P7-W4.fix.01 Status:

- Phase 7 Status: `done`。
- Controller Decision B: pytest-managed temp fixtures such as `tmp_path` / `tmp_path_factory` / `pytester` are allowed only when managed by pytest outside repo-root; repo-root scratch artifacts, leaked tmp directories, and untracked execution artifacts remain forbidden.
- Controller Decision A: authenticated frontend smoke must not depend on fake LLM provider; runtime fake rejection must not be weakened.
- Implementation evidence: `tests/test_temp_artifact_policy.py` allows pytest-managed fixture names while preserving repo-root `tmp*` rejection; `docs/00-governance/TEST_POLICY.md` reflects the same test artifact boundary; `scripts/qa/authenticated-frontend-smoke.mjs` sets `LLM_PROVIDER` to blank instead of fake.
- Validation evidence: full-repo pytest `1067 passed in 86.00s`; `npm run web:test` passed; `npm run web:smoke:auth` passed; focused temp / fake policy tests `21 passed`; `git diff --check` clean.
- Audit evidence: `docs/goals/2026-06-05/P7_W4_FIX01_E_AUDIT_REPORT.md` returned `PASS` with no provider / fake policy weakening and no API route, DB, frontend feature, domain policy, Phase 8 runtime, or Phase 9 eval / CI scope drift.
- Gap result: `P7-GAP-005` is `closed_by_full_validation`。
- Phase 8 handoff: `eligible_for_controller_decision`, not started。

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

Current Status:

- `partial_with_deferred_gaps` after `P8-GOAL-ONE-SHOT-C4-RUNTIME`.
- Implemented and validated C4 foundation evidence: AgentExecutor-compatible adapter, facade-created start routed through the adapter, facade-created status/timeline/cancel adapter routing with owner-scope preservation, descriptor-supported timeline/cancel fail-closed guard and Question/Feedback timeline/cancel descriptor declarations, adapter result preservation for output / interrupt / typed candidate payload refs, runtime formal-ref, formal-write-counter and repository/DB business-write metadata fail-closed guards, runtime fake-provider / fail-open fallback metadata fail-closed guard, runtime loop policy contract with complete P8 required stop-condition fail-closed validation, facade-created start/resume/replay command `runtime_loop_policy` metadata, generic direct runtime missing-policy fail-closed gate, descriptor-supported resume/replay fail-closed guard, Feedback direct in-memory runner descriptor policy metadata fail-closed gate, Polish question direct runtime `interrupt_required` stop-condition coverage, Polish question concrete loop-policy caller/side-effect/tool-declared-forbidden-data enforcement, facade checkpoint-bound strict-base resume control-field/action/formal-ref gate, mandatory registered ToolDefinition authorization, Polish question concrete runtime ToolDefinition lookup, Polish question concrete checkpoint-bound HITL resume validation, Feedback PR8 provider trace gate runtime ToolDefinition lookup plus caller/permission/owner/side-effect/forbidden-data negative coverage, direct `authorize_tool_call()` architecture gate, ToolDefinition side-effect guard checks, read-only facade replay with original failure/interruption status metadata, refs-only trace comparison preservation including Feedback validation refs and replay side-effect counter fail-closed validation, P8 HITL service trigger matrix with checkpoint-bound resume validation, generic in-memory checkpoint-bound user-confirmation resume validation, generic direct `run_started` / `run_resumed` / `run_succeeded`, Feedback direct `run_started` / `run_succeeded`, and Question direct `run_started` / `interrupt_opened` / `run_resumed` / resumed `run_succeeded` P8 command ref matrix preservation, Feedback in-memory runner-bound five-trigger HITL emission with low-confidence trace refs, service-backed in-memory runner resume validation plus candidate/validation resume timeline refs, typed handoff envelope, AgentExecutor-bound source-result to target-plan handoff foundation, `execute_agent_handoff()` target AgentExecutor start, refs-only asset body descriptor handoff, target timeline handoff envelope ref visibility, adapter result/status handoff ref propagation, Feedback in-memory typed `feedback_candidate` and `asset_update_candidate` payloads, expanded trace DTO plus recursive nested metadata filtering, Feedback status validation-ref trace surface and adapter P8 trace/timeline ref mapping including command metadata `tool_refs` / `policy_refs` / `provider_refs` / `validation_refs` / `handoff_refs` / `low_confidence_flags`, generic runtime start/resume/cancel refs metadata, concrete Question start/resume/cancel-event refs metadata including Question cancel checkpoint/validation ref separation, Feedback start/resume/cancel-event refs metadata, cancel zero-provider/formal-write counters, runtime DTO status taxonomy guard, Polish question application status taxonomy mapping, `AgentTraceBridge` non-DTO status guard, adapter metadata event status taxonomy guard, default-off LangGraph runtime flag documentation, architecture gate, focused runtime gates, Q/F regression gate and full backend pytest.
- Deferred gaps: raw asset body transfer and formal asset composition/write semantics, future / indirect graph tool-loop expansion outside the covered facade start surfaces and Question/Feedback direct paths, remaining product-level runtime/orchestration wiring and runner-bound HITL emission / resume validation outside the already covered facade/generic/Question/Feedback paths, DB persistence/API status taxonomy beyond the runtime DTO and Polish question application status mapping, product-level Supervisor / L5 orchestration and proving complete trace population for remaining product/future runtime events outside current generic start/resume/cancel plus Feedback service-backed resume/start/cancel, Question start/resume/cancel and target handoff timeline coverage.
- Non-claim: no Phase 11 Supervisor / Orchestrator, no Phase 12 L5 release gate, no formal F8/M8 release, no prompt/provider/API/DB/frontend/domain-policy behavior change.

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

Current Status:

- `complete_with_deferred_remote_ci_gap` for deterministic replay/fixture eval regression foundation after Phase 10 closeout acceptance.
- `evals/suites/phase9.json` registers Phase 9 suite, capability IDs, dataset refs, grader refs, CI behavior, negative-control refs and non-claims.
- `evals/datasets/phase9/*.jsonl` covers canonical evidence/source support, Question Agent, Feedback Agent, provider boundary, fake gate, handoff/trace and runtime-foundation deferred cases.
- `scripts/evals/run_eval_gate.py` runs the default replay gate, writes JSON/Markdown reports, scans report output and exits non-zero on blocking failures.
- `docs/goals/2026-06-06/P9_EVAL_REPORT.md` records 30 total cases, 30 passed, 0 blocking failures and 2 explicit deferred cases.
- `.github/workflows/eval-gate.yml` integrates the replay gate and negative-control gate without live provider credentials.
- `package.json` registers `eval:gate` and `eval:gate:negative`.
- Phase 10 recon confirms `HEAD` and `origin/main` at `76c670c859d3f7d32d13e604b3d0edffeefd2048`.
- Remote GitHub Actions evidence remains `deferred_remote_ci_gap`; no remote run/artifact is claimed.
- Committed eval reports still embed short SHA `f86adea`; Phase 10 treats this as residual report-metadata risk and does not rewrite reports.
- Non-claim: Phase 9 evidence is deterministic regression evidence only; it is not real-provider quality certification, P8 closure, Phase 11 / Phase 12 implementation or L5 release.

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

Current Status:

- `closeout_source_backfill_complete_with_deferred_gaps` for Phase 10 docs/source-backfill.
- Phase 0-10 L5 Foundation stage is closed as `closed_with_deferred_gaps`, not as L5 release.
- Phase 9 accepted state is `complete_with_deferred_remote_ci_gap`.
- `deferred_remote_ci_gap` remains open until a visible passing GitHub Actions run and artifact are cited or the gap is explicitly carried again.
- Phase 8 runtime gaps remain deferred and are not closed by Phase 10 source backfill.
- Phase 11 Supervisor / Orchestrator implementation has not started.
- Phase 12 L5 release gate has not started.
- No prompt/provider/API/DB/domain/runtime/frontend behavior changed in Phase 10.

Phase 10 Evidence:

- `docs/goals/2026-06-06/P10_CLOSEOUT_REPORT.md`
- `docs/goals/2026-06-06/P10_DEFERRED_GAP_REGISTER.md`
- `docs/goals/2026-06-06/P10_SOURCE_BACKFILL_AUDIT.md`
- `PYTHONPATH=.:apps/api .venv/bin/pytest tests/evals -q` passed with `27 passed`.
- `python3 scripts/evals/run_eval_gate.py --suite phase9 --mode replay --report-dir /tmp/aifi-p10-closeout-eval-reports` passed with `30 passed`, `0 blocking_failures`, `2 deferred`, current short SHA `76c670c`.
- `python3 scripts/evals/run_eval_gate.py --suite phase9 --mode replay --expect-fail-fixture` observed expected failure `must_not_have_present:你负责过`.

## Phase 11

Name:

L5 Controlled Multi-Agent Orchestration

Current Status:

- `scope_lock_complete_with_deferred_gaps` for P11-W0 docs-only reconciliation.
- `contract_slice_complete_with_deferred_runtime_gaps` for P11-W1 Option A contract-first Orchestrator.
- `runtime_hardening_slice_complete_with_deferred_product_workflow` for P11-W2 narrow runtime-hardening slice.
- `candidate_product_slice_complete_with_deferred_formal_write_and_release_gate` for P11-W3 minimal candidate-only three-business-agent product slice.
- `L5-002` Supervisor / Orchestrator is contract-only validated with deferred runtime/product workflow gaps.
- `L5-003` cross-agent handoff / state / trace contracts are validated with deferred runtime execution gaps.
- `L5-004` multi-agent product workflow has a minimal candidate-only product slice with deferred formal write and release gate.
- `L5-005` controlled tool loop hardening has a locally validated runtime-hardening slice, with deferred product workflow.

Goal:

- Register a Supervisor / Orchestrator Agent.
- Define typed cross-agent goal decomposition.
- Define cross-agent plan, handoff, state, checkpoint, replay and trace contracts.
- Enforce bounded tool loop with `max_steps`, `max_retries`, `timeout` and `stop_conditions`.
- Add HITL triggers for asset conflict, formal write, low confidence, ambiguous ownership and validation failed with partial result.
- Prove at least one end-to-end product workflow with three or more business agents.
- Preserve candidate-only outputs and formal write through Application Service -> Domain Policy -> Handoff.

Allowed only in a separately scoped Phase 11 implementation window:

- Supervisor / Orchestrator runtime wiring.
- Product multi-agent workflow implementation.
- Scoped runtime/orchestration behavior explicitly authorized by the selected option.
- Source backfill for implemented/verified capability only.

Forbidden:

- L5 release claim.
- Unbounded autonomous swarm.
- Agent direct DB / repository write.
- Tool direct repository exposure.
- Infrastructure business policy.
- Provider full prompt / full resume / full JD fallback.
- Prompt/provider/API/DB/frontend/domain behavior changes unless separately scoped.
- Committed eval report rewrite.
- Remote CI claim without visible run/artifact.

P11-W0 Evidence:

- `docs/goals/2026-06-06/P11_W0_SCOPE_LOCK_AND_GAP_RECONCILIATION.md`
- `docs/goals/2026-06-06/P11_W0_GAP_RECONCILIATION.md`
- `docs/goals/2026-06-06/P11_W0_DECISION_OPTIONS.md`
- `docs/goals/2026-06-06/P11_W0_SOURCE_BACKFILL_AUDIT.md`

P11-W1 Evidence:

- `docs/goals/2026-06-06/P11_W1_CONTRACT_FIRST_ORCHESTRATOR.md`
- `docs/goals/2026-06-06/P11_W1_IMPLEMENTATION_REPORT.md`
- `docs/goals/2026-06-06/P11_W1_VALIDATION_REPORT.md`
- `docs/goals/2026-06-06/P11_W1_SOURCE_BACKFILL_REPORT.md`

P11-W2 Evidence:

- `docs/goals/2026-06-06/P11_W2_RUNTIME_HARDENING_SLICE.md`
- `docs/goals/2026-06-06/P11_W2_IMPLEMENTATION_REPORT.md`
- `docs/goals/2026-06-06/P11_W2_VALIDATION_REPORT.md`
- `docs/goals/2026-06-06/P11_W2_SOURCE_BACKFILL_REPORT.md`

P11-W3 Evidence:

- `docs/goals/2026-06-06/P11_W3_MINIMAL_THREE_AGENT_PRODUCT_SLICE.md`
- `docs/goals/2026-06-06/P11_W3_IMPLEMENTATION_REPORT.md`
- `docs/goals/2026-06-06/P11_W3_VALIDATION_REPORT.md`
- `docs/goals/2026-06-06/P11_W3_SOURCE_BACKFILL_REPORT.md`

P11-W1 non-claims:

- P11-W1 does not implement product multi-agent workflow.
- P11-W1 does not execute Supervisor / Orchestrator at runtime.
- P11-W1 does not close Phase 8 runtime gaps.
- P11-W1 does not close `deferred_remote_ci_gap`.
- P11-W1 does not rewrite stale eval reports.
- P11-W1 does not certify real-provider quality.
- P11-W1 does not claim L5 release.
- P11-W1 does not implement Phase 12 release gate.

P11-W2 non-claims:

- P11-W2 does not implement product multi-agent workflow.
- P11-W2 does not execute `interview_orchestrator_agent` as a runtime agent.
- P11-W2 does not close all Phase 8 runtime gaps.
- P11-W2 does not close `deferred_remote_ci_gap`.
- P11-W2 does not rewrite stale eval reports.
- P11-W2 does not certify real-provider quality.
- P11-W2 does not claim L5 release.
- P11-W2 does not implement Phase 12 release gate.

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

## Phase 12

Name:

L5 Eval, Hardening, and Release Gate

Current Status:

- Release gate scope locked by P12-W0.
- P12-W1 Eval-contract-first creates contract-only eval artifacts and static tests.
- `L5-006` current status is `eval_contract_slice_complete_with_deferred_runner_ci_release`, not implemented, not validated and not done.
- Runner behavior, replay execution, CI binding, report generation, real-provider quality certification, remote CI artifact evidence and release decision remain deferred.
- No L5 release, real-provider quality certification, formal F8/M8 release, Phase 12 release gate completion or remote CI success is claimed by P12-W0 or P12-W1.

Goal:

- Multi-agent regression suite.
- Cross-agent replay fixtures.
- Failure-mode regression cases.
- L5 CI gate.
- Observability / trace report.
- Rollback policy.
- Failure triage policy.
- Remote CI artifact evidence.
- Human/controller release decision.

P12-W0 Evidence:

- `docs/goals/2026-06-06/P12_W0_RELEASE_GATE_SCOPE_LOCK.md`
- `docs/goals/2026-06-06/P12_W0_RELEASE_GATE_SCOPE_REPORT.md`
- `docs/goals/2026-06-06/P12_W0_RELEASE_EVIDENCE_CONTRACT.md`
- `docs/goals/2026-06-06/P12_W0_DECISION_OPTIONS.md`
- `docs/goals/2026-06-06/P12_W0_SOURCE_BACKFILL_REPORT.md`

P12-W0 treatment:

- Scope lock only.
- Phase 12 implementation remains pending scoped execution after the contract-first slice.
- Next-window options remain open after P12-W1 audit.
- Phase 12 is release evidence and hardening, not new product feature scope.

P12-W1 Evidence:

- `docs/goals/2026-06-06/P12_W1_EVAL_CONTRACT_FIRST.md`
- `docs/goals/2026-06-06/P12_W1_IMPLEMENTATION_REPORT.md`
- `docs/goals/2026-06-06/P12_W1_VALIDATION_REPORT.md`
- `docs/goals/2026-06-06/P12_W1_SOURCE_BACKFILL_REPORT.md`
- `evals/suites/phase12.json`
- `evals/datasets/phase12/multi_agent_product_slice.jsonl`
- `evals/datasets/phase12/replay_and_failure_modes.jsonl`
- `evals/datasets/phase12/release_non_claims.jsonl`
- `evals/graders/phase12_contract.json`
- `evals/schemas/phase12_release_report_schema.json`
- `tests/evals/test_phase12_eval_contracts.py`

P12-W1 treatment:

- Eval-contract-first only.
- Contract artifacts are not executable eval gate evidence.
- Dataset skeletons are not eval pass evidence.
- Grader contract is not grader implementation.
- Release report schema is not a generated report artifact.
- P12-W2 or later must be separately selected for runner, replay, CI, report generation, remote CI artifacts or release decision work.

Forbidden:

- Claiming L5 with unit tests only.
- Claiming L5 with fake-only or replay-only eval.
- Skipping replay / trace evidence.
- Release with unresolved candidate/formal boundary gaps unless explicitly accepted by release controller.
- Release with unresolved provider fail-open gaps.
- Release without human/controller decision.
- Claiming remote CI success without visible run/artifact.
- Treating P12-W0 scope lock as release gate completion.
- Treating P12-W1 eval contract artifacts as release gate completion.
- Marking `L5-006` implemented, validated or done before evidence exists.

## Phase 11 Entry Conditions

Phase 11 may start only after these conditions are explicit in the next scope lock:

1. Phase 0-10 foundation is treated as closed with deferred gaps, not clean release.
2. Remaining gaps are explicitly carried: `deferred_remote_ci_gap`, Phase 8 runtime gaps, stale committed report metadata risk and L5 release non-claim.
3. Remote CI gap is either resolved by visible passing GitHub Actions run/artifact or explicitly accepted as deferred for the Phase 11 window.
4. No L5 release, formal F8/M8 release or real-provider quality certification is claimed.
5. Supervisor / Orchestrator implementation is not assumed to exist and must be separately scoped.
6. Committed eval reports are not rewritten unless a separate report refresh window authorizes it.

Phase 11 must stop and return to Controller if it requires:

- claiming remote CI without visible evidence;
- closing Phase 8 runtime gaps by wording only;
- marking L5 release or formal F8/M8 release;
- changing prompt/provider/API/DB/domain/runtime/frontend behavior outside the Phase 11 scope;
- rewriting committed eval reports without explicit authorization.

---
title: CAPABILITY_IMPLEMENTATION_REGISTRY
type: delivery-registry
status: active-f0
updated: 2026-06-13
permalink: ai-for-interviewer/docs/03-delivery/capability-implementation-registry
source_migrated_from:
  - .codex-temp/interview-coach-refactor/
  - docs/active/
  - docs/project-sources/
---

# Capability Implementation Registry

本文登记从 `.codex-temp/interview-coach-refactor/`、`docs/active/`、`docs/project-sources/` 迁入 active docs 的 confirmed implemented capability。它只记录已有实现事实、真实代码路径、验证证据和当前行为影响，不创建新 architecture、新 feature 或新 task system。

## Migration Rule

迁入条件：

- 来源状态为 `implemented`、`validated`、`done`，或明确记录为已实现并本地验证的受限切片。
- 能指出真实实现文件路径。
- 能指出 tests、eval、execution result 或 source-recorded validation evidence。
- 能保留 non-claim / deferred gap，不把 `partial`、`design_done`、`not_started`、`contract-only`、`deferred` 升级为 implemented。

未迁入为 implemented 的状态：

- `design_done`
- `not_started`
- `implementation_planned`
- `recon_done`
- `skeleton`
- `partial` without implemented-and-validated slice evidence
- `deferred`
- `deferred_out_of_scope_for_option_d`
- 只存在于目标架构或旧 prompt 的设计叙事

## Current Active Mapping

| Source area | Permanent active location |
| --- | --- |
| `.codex-temp/interview-coach-refactor/**` G-003 implementation evidence | 本文件 §G-003；`docs/02-design/INTERVIEW_COACH_REFACTOR_SPEC.md` |
| `docs/active/interview-coach-refactor.md` final system boundary | `docs/02-design/INTERVIEW_COACH_REFACTOR_SPEC.md` |
| `docs/project-sources/**` implemented project capability evidence | 本文件 §Agent Platform / Provider / Eval / L5 / Governance |
| Existing baseline product capability matrix | `docs/03-delivery/refactor/CAPABILITY_PRESERVATION_MATRIX.md` |

## Interview Coach Refactor

### G-003 Transcript Structured Signal Extraction

What it does:

- 在 G-003 feedback evaluation 前解析 raw `answer_text`，生成 bounded `structured_answer`。
- `structured_answer` 包含 `claims`、`topics`、`sentiment`、`confidence_indicators`、`experience_signals`。
- prompt asset 和 core rules 消费结构化输入；parser failure 使用 fallback wrapper。

Where implemented:

- `apps/api/app/application/polish/transcript_signal_parser.py`
- `apps/api/app/application/polish/feedback_generation_service.py`
- `apps/api/app/application/polish/feedback_prompt_assets.py`

Validation evidence:

- Migrated temp evidence: GREEN command reported `67 passed in 0.96s` with `AI_FOR_INTERVIEWER_ALLOW_TEST_DIR_LEAKS=1`。
- Test paths: `tests/api/test_polish_transcript_signal_parser.py`、`tests/api/test_polish_feedback_generation_service.py`、`tests/api/test_polish_feedback_pipeline_contract.py`、`tests/api/test_polish_feedback_agent_io_alignment.py`。

Current system behavior impact:

- Current answer enters G-003 as structured, bounded evaluation input.
- G-003 still remains evaluation / feedback only; it does not become G-004 understanding, scoring, taxonomy or coaching.

### G-004 Transcript Understanding

What it does:

- 解析 transcript 并输出 structure / behavioral signals。
- 保持 understanding-only，不生成 feedback、score、rubric verdict 或 coaching plan。

Where implemented:

- `apps/api/app/application/transcript_analysis/models.py`
- `apps/api/app/application/transcript_analysis/parser.py`
- `apps/api/app/application/transcript_analysis/analyzer.py`
- `apps/api/app/application/transcript_analysis/service.py`

Validation evidence:

- Test paths: `tests/api/test_transcript_analysis.py`、`tests/api/test_transcript_analysis_contract_lock.py`。
- Migrated temp evidence 的 GREEN command 覆盖上述 G-004 tests。

Current system behavior impact:

- G-004 owns `transcript_analysis_v1` and does not depend on G-003 / Polish feedback services.

### Composition Layer

What it does:

- 按 `interview`、`training`、`analysis` mode 决定是否调用 G-003 / G-004。
- 只进行 envelope-level routing / packaging。

Where implemented:

- `apps/api/app/application/composition/service.py`

Validation evidence:

- Test path: `tests/api/test_composition_layer.py`。

Current system behavior impact:

- `analysis` mode 不调用 G-003。
- `interview` / `training` mode 可返回 G-004 与可选 G-003 输出，但不得跨层改写语义。

## Provider Boundary And Fake Isolation

### PRO-001 Compact Provider Request Boundary

What it does:

- 在 active provider paths 中构造 compact、schema-bound、redacted、traceable 的 provider request。
- forbidden keys fail closed，包括 raw prompt、provider payload、full resume、full JD、full answer、full asset body、secret/token/cookie/api key。
- Feedback current answer policy 允许 bounded `current_answer.answer_text` 作为 primary task input，但不得表示为 `full_answer`。

Where implemented:

- `apps/api/app/application/llm/provider_boundary.py`
- `apps/api/app/application/llm/types.py`
- `apps/api/app/application/polish/question_generation_service.py`
- `apps/api/app/application/polish/feedback_agent.py`
- `apps/api/app/application/polish/feedback_generation_service.py`
- `apps/api/app/application/polish/feedback_prompt_assets.py`
- `apps/api/app/application/polish/progress_tree.py`
- `apps/api/app/infrastructure/llm/job_match.py`
- `apps/api/app/application/ai_runtime/business_graphs/polish_feedback_graph.py`

Validation evidence:

- Migrated P7-W4.fix.01 source evidence records `Status: done` with full-repo pytest `1067 passed in 86.00s`、`npm run web:test` passed、`npm run web:smoke:auth` passed、focused temp / fake policy selector `21 passed`、`git diff --check` passed。
- Test paths include `tests/api/test_provider_boundary.py`、`tests/api/test_provider_global_backstop.py`、`tests/architecture/test_provider_boundary_static.py`、`tests/api/test_polish_feedback_generation_service.py`、`tests/api/test_polish_feedback_agent_io_alignment.py`。

Current system behavior impact:

- Provider request construction is guarded by builder / DTO backstop / static gate.
- Provider unavailable, provider validation failure and forbidden payload are non-success paths.
- No real-provider quality certification is claimed by these tests alone.

### PRO-002 Provider Boundary Tests And Static Gate

What it does:

- Prevents production direct `LlmTransportRequest(...)` constructors outside the provider boundary.
- Locks recursive forbidden-key rejection and per-task schema validation.

Where implemented:

- `tests/architecture/test_provider_boundary_static.py`
- `tests/api/test_provider_boundary.py`
- `tests/api/test_provider_global_backstop.py`

Validation evidence:

- P7-W2 / P7-W4 source records cite static + global provider backstop coverage and full validation.

Current system behavior impact:

- New production transport call sites must use validated boundary paths instead of direct DTO construction.

### FAKE-001 Runtime Fake Provider Isolation

What it does:

- Keeps fake LLM behavior limited to tests / evals / replay.
- Runtime fake provider usage is rejected or made trace-visible non-success.
- Auth frontend smoke no longer depends on `LLM_PROVIDER=fake`.

Where implemented:

- `apps/api/app/infrastructure/llm/runtime.py`
- `apps/api/app/application/polish/feedback_generation_service.py`
- `scripts/qa/authenticated-frontend-smoke.mjs`
- `.github/workflows/eval-gate.yml`

Validation evidence:

- P7-W4.fix.01 records `npm run web:smoke:auth` passed, focused runtime fake rejection tests passed, and grep showed no auth smoke `LLM_PROVIDER.*fake` hit.
- Test paths include `tests/api/test_llm_runtime.py`、`tests/api/test_fake_llm_boundary.py`、`tests/api/test_fake_llm_transport.py`。

Current system behavior impact:

- Fake paths cannot be mistaken for runtime provider success.
- Eval/replay fake evidence remains regression evidence only, not real-provider quality.

## Agent Platform Contracts And Planned Workflows

### QAG-005 / QAG-006 / QAG-007 Question Agent Definition, Skills And Tools

What it does:

- Registers `polish_question_agent` in the project-level AgentDefinition registry.
- Registers Question skills and tools with candidate-only contract metadata.
- Enforces no formal output and no direct repository / DB tool exposure.

Where implemented:

- `apps/api/app/application/agents/definitions/catalog.py`
- `apps/api/app/application/agents/definitions/polish/question.py`
- `apps/api/app/application/agents/definitions/common.py`
- `apps/api/app/application/agents/registry/__init__.py`

Validation evidence:

- Migrated source evidence marks QAG-005, QAG-006 and QAG-007 as `validated`。
- Test path: `tests/architecture/test_agent_platform_c1_boundary.py`。

Current system behavior impact:

- Question Agent contract exists as project-level C1 catalog evidence.
- It does not by itself prove autonomous runtime execution or L5 release.

### FAG-006 / FAG-007 / FAG-008 Feedback Agent Definition, Skills And Tools

What it does:

- Registers `polish_feedback_agent` in the project-level AgentDefinition registry.
- Registers Feedback skills and tools.
- Keeps outputs limited to `feedback_candidate` / `asset_update_candidate` and user-confirmed asset handoff.

Where implemented:

- `apps/api/app/application/agents/definitions/catalog.py`
- `apps/api/app/application/agents/definitions/polish/feedback.py`
- `apps/api/app/application/agents/definitions/common.py`
- `apps/api/app/application/agents/registry/__init__.py`

Validation evidence:

- Migrated source evidence marks FAG-006, FAG-007 and FAG-008 as `validated`。
- Test path: `tests/architecture/test_agent_platform_c1_boundary.py`。

Current system behavior impact:

- Feedback Agent contract exists as project-level C1 catalog evidence.
- It does not directly write formal Asset / Feedback / Training objects.

### AGT-006 / AGT-007 Handoff And Trace Contracts

What it does:

- Provides shared handoff and trace metadata contracts for candidate refs, validation refs, handoff refs and output refs.
- Filters unsafe metadata and blocks formal refs in Agent-owned outputs.

Where implemented:

- `apps/api/app/application/agents/contracts/__init__.py`
- `apps/api/app/application/agents/handoff/__init__.py`
- `apps/api/app/application/agents/runtime/__init__.py`

Validation evidence:

- Migrated source evidence marks AGT-006 and AGT-007 as `validated`。
- Test paths include `tests/api/test_agent_contracts.py` and `tests/architecture/test_agent_platform_c1_boundary.py`。

Current system behavior impact:

- Agent output remains candidate / suggestion / validation / trace.
- Formal writes remain Application Service -> Domain Policy -> Handoff.

### QAG-004 Question Planned Guarded Workflow

What it does:

- Normalizes provider / graph output into `question_candidate` before formal write decisions.
- Ensures graph-disabled, fake transport, deterministic fallback and validation failed paths do not persist formal generated questions or report generated success.

Where implemented:

- `apps/api/app/application/polish/agents/question/planned_workflow.py`
- `apps/api/app/application/polish/question_application_service.py`
- `apps/api/app/application/polish/question_generation_service.py`
- `apps/api/app/application/polish/use_cases.py`

Validation evidence:

- Migrated source evidence records QAG-004 current status as `validated_with_deferred_l5_runtime` after P5P6-W1.fix.02。
- Recorded validation: canonical evidence focused test `1 passed`, Question graph integration `12 passed`, Question persistence handoff `15 passed`, Question phase1 refactor `64 passed`, broad selector `300 passed, 323 deselected`, local question eval `3 passed / 0 failed`。
- Test paths: `tests/api/test_polish_question_graph_integration.py`、`tests/api/test_pr5_polish_question_graph_persistence_handoff.py`、`tests/api/test_polish_question_refactor_phase1.py`、`tests/api/test_polish_canonical_evidence.py`。

Current system behavior impact:

- Question fallback / validation failure remains candidate-only and non-success.
- Phase 8 runtime, Phase 11 Supervisor / Orchestrator and Phase 12 L5 release are not implied.

### FAG-005 Feedback Next Action And Feedback Planned Workflow

What it does:

- Integrates feedback policy outputs into planned handoff metadata.
- Emits `feedback_candidate` refs and optional `asset_update_candidate` refs.
- Requires user confirmation for asset update candidates.

Where implemented:

- `apps/api/app/application/polish/agents/feedback/planned_workflow.py`
- `apps/api/app/application/polish/feedback_application_service.py`
- `apps/api/app/application/polish/feedback_generation_service.py`
- `apps/api/app/application/polish/feedback_rules.py`

Validation evidence:

- Migrated source evidence marks FAG-005 as `implemented` and P5/P6 planned workflow as `validated_with_deferred_l5_runtime`。
- Recorded validation includes Feedback runtime `7 passed`, local feedback eval `5 passed / 0 failed`, broad selector `300 passed, 323 deselected`。
- Test paths include `tests/api/test_polish_feedback_runtime.py`、`tests/api/test_polish_feedback_generation_service.py`、`tests/api/test_polish_feedback_validation.py`。

Current system behavior impact:

- Feedback success path carries candidate / validation / handoff refs.
- Asset update candidates remain candidate-only and do not perform formal asset writes.

## Agent Runtime And L5 Local Multi-Agent Capability

### RTE-001 AgentExecutor Adapter Integration

What it does:

- Exposes `AgentGraphRunner` through `AgentExecutor` compatible boundaries.
- Routes current facade-created start/status/timeline/cancel surfaces through adapter for known runs.
- Preserves owner scope and blocks descriptor-unsupported timeline/cancel before runner access.

Where implemented:

- `apps/api/app/application/ai_runtime/facade.py`
- `apps/api/app/application/agents/runtime/__init__.py`
- `apps/api/app/infrastructure/ai_runtime/langgraph/in_memory_runtime.py`

Validation evidence:

- Migrated source evidence records RTE-001 as `validated_with_deferred_gaps`。
- P8 records cite facade start coverage, status/timeline/cancel adapter routing, full facade regression, P8 application-layer AgentExecutor adapter gate and broader backend gates.
- Test paths include `tests/api/test_ai_orchestration_facade.py`、`tests/api/test_agent_contracts.py`、`tests/application/agents/test_option_d_local_multi_agent_runtime_wiring.py`。

Current system behavior impact:

- Current known facade-created runs use the project AgentExecutor boundary while preserving candidate-only and formal-ref guards.
- Product-level Supervisor / L5 release remains separately scoped.

### RTE-002 Controlled Tool Loop Bounds

What it does:

- Requires `AgentRuntimeLoopPolicy` metadata with max steps, retries, timeout and stop conditions.
- Fails closed on missing/invalid loop policy, unregistered tools, caller mismatch, permission mismatch, owner mismatch, side-effect mismatch and tool-declared forbidden payloads.

Where implemented:

- `apps/api/app/application/agents/runtime/__init__.py`
- `apps/api/app/application/ai_runtime/facade.py`
- `apps/api/app/infrastructure/ai_runtime/langgraph/in_memory_runtime.py`
- `apps/api/app/application/ai_runtime/business_graphs/polish_feedback_graph.py`

Validation evidence:

- RTE-002 is `validated_with_deferred_gaps` in the migrated project-source matrix.
- P8 records cite required stop-condition remediation, Feedback direct runtime loop-policy gates and direct `authorize_tool_call()` architecture gate.
- Test paths include `tests/application/agents/test_phase11_runtime_hardening.py`、`tests/api/test_agent_contracts.py`、`tests/api/test_ai_orchestration_facade.py`。

Current system behavior impact:

- Runtime cannot report unbounded or fail-open execution as success in the covered facade/generic/Question/Feedback paths.

### RTE-003 / RTE-004 Interrupt, Resume, Checkpoint And Replay

What it does:

- Provides read-only / formal-write-blocked replay.
- Requires checkpoint refs, base versions, idempotency keys and allowed resume actions.
- Preserves original failure/interruption status and refs-only replay trace metadata.
- Rejects replay side-effect counters for provider/tool/repository/DB/formal writes.

Where implemented:

- `apps/api/app/application/ai_runtime/facade.py`
- `apps/api/app/application/agents/runtime/__init__.py`
- `apps/api/app/infrastructure/ai_runtime/langgraph/in_memory_runtime.py`

Validation evidence:

- RTE-003 and RTE-004 are `validated_with_deferred_gaps` in migrated source evidence.
- Test paths include `tests/api/test_pr4_fake_runtime_replay_resume.py`、`tests/api/test_ai_orchestration_facade.py`、`tests/application/agents/test_phase11_runtime_hardening.py`、`tests/evals/test_phase12_l5_eval_gate.py`。

Current system behavior impact:

- Covered runtime replay / resume paths preserve refs and fail closed on formal-write or side-effect leakage.

### RTE-005 Runtime Trace And Status Taxonomy

What it does:

- Expands `AgentExecutionTrace` with agent version, AI task, low-confidence flags, failure reason and fallback reason.
- Recursively filters forbidden metadata.
- Rejects unknown runtime statuses and success-like status with failure reason.

Where implemented:

- `apps/api/app/application/agents/runtime/__init__.py`
- `apps/api/app/application/ai_runtime/facade.py`
- `apps/api/app/infrastructure/ai_runtime/langgraph/in_memory_runtime.py`

Validation evidence:

- RTE-005 is `validated_with_deferred_gaps`。
- P8 records cite trace/timeline metadata gates, Question/Feedback direct runtime ref-matrix gates, replay trace comparison gates and `AgentTraceBridge` non-DTO status guard.

Current system behavior impact:

- Runtime metadata remains refs-only and status taxonomy guarded in covered paths.
- DB persistence/API status taxonomy beyond runtime DTO remains deferred.

### RTE-006 Typed Multi-Agent Handoff

What it does:

- Uses `AgentHandoffEnvelope` to carry candidate, schema, trace, validation, side-effect and idempotency refs.
- Starts target AgentExecutor from typed handoff plan without raw payload sharing.
- Surfaces handoff refs in target timeline metadata.

Where implemented:

- `apps/api/app/application/agents/handoff/__init__.py`
- `apps/api/app/application/agents/runtime/__init__.py`
- `apps/api/app/application/agents/orchestration/minimal_three_agent_slice.py`

Validation evidence:

- RTE-006 is `validated_with_deferred_gaps`。
- Test paths include `tests/application/agents/test_phase11_three_agent_product_slice.py`、`tests/api/test_agent_contracts.py`。

Current system behavior impact:

- Cross-agent handoff uses refs-only candidate descriptors.
- Raw asset body transfer and formal asset composition/write semantics remain deferred.

### RTE-007 Runtime Flags And Provider-Fake Isolation

What it does:

- Keeps LangGraph / runtime paths default-off unless flags enable them.
- Fails closed on runtime metadata that reports fake-provider use or fail-open fallback as generated success.

Where implemented:

- `.env.example`
- `apps/api/app/application/agents/runtime/__init__.py`
- `apps/api/app/application/ai_runtime/facade.py`
- `apps/api/app/infrastructure/ai_runtime/langgraph/in_memory_runtime.py`

Validation evidence:

- RTE-007 is `validated_with_deferred_gaps`。
- P8 records cite runtime fake-provider / fail-open fallback metadata guard and full backend validation.

Current system behavior impact:

- Runtime productization remains guarded and default-off; fake provider use cannot be hidden as success.

### L5-002 Supervisor / Orchestrator Agent

What it does:

- Registers `interview_orchestrator_agent` for local multi-agent orchestration.
- Provides goal decomposition, bounded loop and HITL scope as local capability evidence.

Where implemented:

- `apps/api/app/application/agents/definitions/orchestrator.py`
- `apps/api/app/application/agents/definitions/catalog.py`
- `apps/api/app/application/ai_runtime/facade.py`
- `apps/api/app/application/ai_runtime/business_graphs/local_multi_agent_orchestrator.py`
- `apps/api/app/infrastructure/ai_runtime/langgraph/in_memory_runtime.py`

Validation evidence:

- Migrated source evidence records L5-002 as `validated` for Phase 11/12 Option D local evidence.
- Test paths include `tests/architecture/test_agent_platform_l5_orchestrator_contract.py`、`tests/application/agents/test_option_d_local_multi_agent_runtime_wiring.py`。

Current system behavior impact:

- Local Orchestrator path exists behind default-off flags.
- Production release, remote CI hard claim and real-provider certification remain deferred.

### L5-003 Cross-Agent Handoff / State / Trace

What it does:

- Provides typed cross-agent plan, handoff, state, checkpoint, replay and trace timeline contracts.
- Emits typed handoff refs, checkpoint refs, trace refs and read-only replay evidence with zero provider / repository / DB / formal-write counters.

Where implemented:

- `apps/api/app/application/agents/contracts/__init__.py`
- `apps/api/app/application/agents/handoff/__init__.py`
- `apps/api/app/application/agents/runtime/__init__.py`
- `apps/api/app/infrastructure/ai_runtime/langgraph/in_memory_runtime.py`

Validation evidence:

- L5-003 is `validated` in migrated Option D source evidence.
- Test paths include `tests/api/test_agent_contracts.py`、`tests/application/agents/test_phase11_runtime_hardening.py`、`tests/application/agents/test_option_d_local_multi_agent_runtime_wiring.py`。

Current system behavior impact:

- Cross-agent metadata is refs-only and side-effect guarded in local Option D paths.

### L5-004 Multi-Agent Product Workflow

What it does:

- Provides at least one local candidate-only workflow using `polish_feedback_agent`, `asset_candidate_agent` and `training_plan_agent`.
- Emits `feedback_candidate`, `asset_update_candidate` and `training_plan_candidate` refs.
- Blocks formal write request and asset conflict paths.

Where implemented:

- `apps/api/app/application/agents/orchestration/minimal_three_agent_slice.py`
- `apps/api/app/application/agents/definitions/asset_candidate.py`
- `apps/api/app/application/agents/definitions/training_plan.py`
- `apps/api/app/application/ai_runtime/business_graphs/local_multi_agent_orchestrator.py`
- `apps/api/app/infrastructure/ai_runtime/langgraph/in_memory_runtime.py`

Validation evidence:

- L5-004 is `validated` in migrated Option D source evidence.
- Test paths include `tests/application/agents/test_phase11_three_agent_product_slice.py`、`tests/application/agents/test_option_d_local_multi_agent_runtime_wiring.py`、`tests/evals/test_phase12_l5_eval_gate.py`。

Current system behavior impact:

- Local workflow can produce candidate refs across three business agents.
- It does not write formal assets, feedback, progress, scores, reports or training plans.

### L5-005 Controlled Tool Loop Hardening

What it does:

- Validates runtime loop bounds, stop conditions and HITL triggers.
- Blocks success-like statuses for bound exhaustion, HITL required, provider unavailable, validation failure and fallback/generated-success markers.

Where implemented:

- `apps/api/app/application/agents/runtime/__init__.py`
- `apps/api/app/application/ai_runtime/facade.py`
- `apps/api/app/infrastructure/ai_runtime/langgraph/in_memory_runtime.py`

Validation evidence:

- L5-005 is `validated` for controlled runtime-boundary evidence.
- Test path: `tests/application/agents/test_phase11_runtime_hardening.py`。

Current system behavior impact:

- Local multi-agent runtime cannot hide controlled-loop or HITL boundary failures as success.

### L5-006A Local Multi-Agent Eval / Replay / Failure Hardening

What it does:

- Provides deterministic local multi-agent eval, replay/resume fixtures, failure fixtures, local trace report and fake-safe negative controls.
- Covers happy path, insufficient context, asset conflict, low confidence, formal write request, ownership ambiguity, provider unavailable, validation failed partial result, cross-agent handoff failure, replay, replay mismatch and bounded-loop stop.

Where implemented:

- `scripts/evals/run_l5_eval_suite.py`
- `tests/evals/phase12/suite.json`
- `tests/evals/phase12/datasets/multi_agent_core.jsonl`
- `tests/evals/phase12/datasets/failure_and_replay.jsonl`
- `tests/evals/phase12/datasets/quality_lanes.jsonl`
- `tests/evals/phase12/datasets/negative_control.jsonl`
- `tests/evals/test_phase12_l5_eval_gate.py`

Validation evidence:

- D-W4 source evidence records `PYTHONPATH=.:apps/api .venv/bin/python scripts/evals/run_l5_eval_suite.py --mode deterministic --report-dir /tmp/aifi-phase12-l5-option-d` -> 13 total, 13 passed, 0 failed, 0 blocking failures。
- Phase 12 and Phase 9 negative controls observed expected failures.
- Additional recorded validation: `tests/application/agents tests/architecture` -> 58 passed; `tests/architecture tests/evals` -> 74 passed; `tests/evals` -> 41 passed.

Current system behavior impact:

- Option D local complete controlled multi-agent capability is locally validated.
- `L5-006B` production release gate / remote CI hard claim / real-provider production certification / production observability / release decision remains deferred and out of scope.

## Eval And Governance

### EVAL-001 AI Eval Regression Gate

What it does:

- Provides deterministic replay / fixture eval regression foundation.
- Runs default replay gate, writes JSON / Markdown reports, scans reports for forbidden payloads and returns non-zero on blocking failures.
- Includes negative-control proof fixture.

Where implemented:

- `evals/suites/phase9.json`
- `evals/datasets/phase9/*.jsonl`
- `evals/graders/code_rules.py`
- `scripts/evals/run_eval_gate.py`
- `tests/evals/test_phase9_eval_gate.py`
- `.github/workflows/eval-gate.yml`
- `package.json`

Validation evidence:

- Migrated P9/P10 evidence records local replay gate `30 passed`, `0 blocking_failures`, `2 deferred`; `tests/evals` passed; negative-control gate observed expected failure.
- Matrix status: `validated`, not `done`, because remote GitHub Actions evidence remains deferred.

Current system behavior impact:

- Local deterministic regression gate protects capability IDs and non-claims.
- It is not real-provider quality certification and not a remote CI hard claim.

### WIN-001 Execution Window Protocol

What it does:

- Requires each controlled window to define scope, allowed files, forbidden files, tests, rollback, backfill and final evidence.
- Prevents implementation claims without validation and source migration.

Where implemented:

- `AGENTS.md`
- `docs/00-governance/AI_WORKFLOW.md`
- `docs/00-governance/DOCS_INDEX.md`
- `docs/00-governance/TEST_POLICY.md`

Validation evidence:

- P7-W4.fix.01 source evidence records A/B read-only recon, C single-writer implementation, D full validation, E audit and source backfill sequence.
- Current active workflow rules require `git status --short`, `git diff --stat`, changed-file lists, residual checks and scope-out reporting after governance migrations.

Current system behavior impact:

- AI / Codex work must stay within allowed files and preserve non-claim wording.
- Temporary source packs are no longer active truth once migrated to this registry and `DOCS_INDEX.md`。

### SRC-001 Source Backfill And Capability Migration

What it does:

- Converts verified implementation evidence into active docs without promoting unverified target architecture.
- Records deferred gaps and non-claims alongside implemented slices.

Where implemented:

- `docs/00-governance/DOCS_INDEX.md`
- `docs/02-design/INTERVIEW_COACH_REFACTOR_SPEC.md`
- `docs/03-delivery/CAPABILITY_IMPLEMENTATION_REGISTRY.md`
- `docs/03-delivery/refactor/CAPABILITY_PRESERVATION_MATRIX.md`

Validation evidence:

- This migration is verified by readback / keyword scans / Markdown diff checks in the cleanup closeout.

Current system behavior impact:

- `.codex-temp/interview-coach-refactor/`、`docs/active/`、`docs/project-sources/` are no longer active capability sources after cleanup.
- Implemented capabilities remain discoverable under permanent `docs/00-04` paths.

## Explicit Non-Claims

- No production L5 release is claimed.
- No real-provider production quality certification is claimed.
- No remote CI hard claim is made without visible passing GitHub Actions artifact evidence.
- No A/B testing, traffic split, canary rollout or online experiment framework is required or claimed by Option D.
- P8 Runtime remains `validated_with_deferred_gaps` / partial foundation, not full product runtime completion.
- `L5-006B` remains deferred and out of scope.
- Design-only target architecture from `docs/project-sources/**` is not upgraded by this migration.

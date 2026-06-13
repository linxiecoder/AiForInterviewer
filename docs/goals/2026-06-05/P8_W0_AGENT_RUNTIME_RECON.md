---
title: P8_W0_AGENT_RUNTIME_RECON
type: goal-evidence
status: warn
date: 2026-06-05
permalink: ai-for-interviewer/docs/goals/2026-06-05/p8-w0-agent-runtime-recon
---

# P8-W0 Agent Runtime Recon

Status: warn

本报告仅记录 Runtime Surface Recon 结果。未修改代码、依赖、配置或测试；不声称 Phase 8 done。

## Scope Lock

- task_id: P8-W0 Runtime Surface Recon（无新增 `AIFI-*` 任务编号）
- allowed_ops: READ_ONLY；唯一写入本报告
- final_artifact: `docs/goals/2026-06-05/P8_W0_AGENT_RUNTIME_RECON.md`
- done_condition: 识别 LangGraph 安装状态、当前 executor / runner / checkpointer / status / timeline surface、安全集成点、依赖风险和 stop conditions
- forbidden_ops: 修改代码、依赖、配置、测试；运行会产生缓存或副作用的 pytest / build；声称 Phase 8 完成

## Files Read

- Governance / goal docs:
  - `AGENTS.md`
  - `docs/00-governance/DOCS_INDEX.md`
  - `docs/03-implementation/BACKLOG.md`
  - `docs/03-implementation/DELIVERY_PLAN.md`
  - `docs/tmp/goal0605/phase8_codex_goal_pack/docs/P8_MASTER_GOAL.md`
  - `docs/tmp/goal0605/phase8_codex_goal_pack/agents/A_RUNTIME_SURFACE_RECON.md`
  - `docs/04-decisions/ADR-0005-langgraph-agentic-workflow-runtime.md`
  - historical refactor planning docs, now de-layered and deleted; confirmed implementation evidence is retained in active design docs and `docs/03-implementation/F5_BACKEND_IMPLEMENTATION_NOTES.md`
  - `docs/02-design/SECURITY_PRIVACY.md`
- Runtime application code:
  - `apps/api/app/application/agents/runtime/__init__.py`
  - `apps/api/app/application/ai_runtime/contracts.py`
  - `apps/api/app/application/ai_runtime/facade.py`
  - `apps/api/app/application/ai_runtime/handoff.py`
  - `apps/api/app/application/ai_runtime/interrupts.py`
  - `apps/api/app/application/ai_runtime/llm_trace.py`
  - `apps/api/app/application/ai_runtime/registry.py`
  - `apps/api/app/application/ai_runtime/runtime_flags.py`
  - `apps/api/app/application/ai_runtime/side_effect_guard.py`
  - `apps/api/app/application/ai_runtime/trace_bridge.py`
  - `apps/api/app/application/ai_runtime/business_graphs/polish_question_graph.py`
  - `apps/api/app/application/ai_runtime/business_graphs/polish_feedback_graph.py`
- Runtime infrastructure code:
  - `apps/api/app/infrastructure/ai_runtime/langgraph/__init__.py`
  - `apps/api/app/infrastructure/ai_runtime/langgraph/checkpointer.py`
  - `apps/api/app/infrastructure/ai_runtime/langgraph/dependency_spike.py`
  - `apps/api/app/infrastructure/ai_runtime/langgraph/in_memory_runtime.py`
  - `apps/api/app/infrastructure/ai_runtime/langgraph/polish_question_runtime.py`
  - `apps/api/app/infrastructure/ai_runtime/langgraph/serializer.py`
  - `apps/api/app/infrastructure/ai_runtime/llm_trace/persisted_transport.py`
- Ancillary runtime persistence / wiring:
  - `apps/api/app/main.py`
  - `apps/api/app/api/deps.py`
  - `apps/api/app/api/v1/polish.py`
  - `apps/api/app/application/polish/use_cases.py`
  - `apps/api/app/infrastructure/db/models/ai_runtime.py`
  - `apps/api/app/infrastructure/db/repositories/ai_runtime/__init__.py`
- Dependency / runtime config:
  - `requirements.txt`
  - `package.json`
  - `apps/web/package.json`
  - `.env.example`
- Test files inspected but not run:
  - `tests/api/test_langgraph_dependency_spike.py`
  - `tests/api/test_pr4_fake_runtime_replay_resume.py`
  - `tests/api/test_agent_contracts.py`
  - `tests/api/test_agent_runtime_flags.py`
  - plus path-scoped `rg` over runtime-related `tests/api/*` and `tests/architecture/*`

## Findings

- [GITHUB_CODE] LangGraph is declared in `requirements.txt` as `langgraph==1.2.1`. Project `.venv` can import `langgraph` and reports version `1.2.1`; system `/usr/bin/python3` cannot find the package. Runtime validation must use `./.venv/bin/python` or an environment installed from `requirements.txt`.
- [GITHUB_CODE] Concrete LangGraph imports are restricted to `apps/api/app/infrastructure/ai_runtime/langgraph/dependency_spike.py`, `in_memory_runtime.py`, and `polish_question_runtime.py`. No `langgraph` / `langchain` imports were found in application, API, or domain layers.
- [GITHUB_CODE] `apps/api/app/application/agents/runtime/__init__.py` defines an `AgentExecutor` protocol with `start`, `resume`, `replay`, `get_status`, `get_timeline`, and `cancel`, but the current runtime wiring primarily uses `application.ai_runtime.contracts.AgentGraphRunner` plus `AiOrchestrationFacade`; `AgentExecutor` is not the active adapter boundary.
- [GITHUB_CODE] `AgentGraphRunner` exposes the P8 method surface: `start`, `resume`, `replay`, `get_status`, `get_timeline`, and `cancel`. `AiOrchestrationFacade` exposes start methods, resume, status, timeline, and cancel, but no public facade method for replay was found in the inspected code.
- [GITHUB_CODE] `apps/api/app/main.py` builds `AiOrchestrationFacade` at startup with `InMemoryLangGraphRuntime`, `PolishQuestionGraphRuntime`, `AgentGraphRegistry.default()`, and `RuntimeFlagResolver`.
- [GITHUB_CODE] Runtime flags are fail-closed by default. `RuntimeFlagResolver` checks test overrides, environment, settings overrides, authorized persisted config, then hardcoded default false. Graph flags can only be resolved by `facade`, `registry`, or `runner_entry`.
- [GITHUB_CODE] The concrete runner additionally requires `AIFI_AI_RUNTIME_ENABLED` and `AIFI_AI_RUNTIME_LANGGRAPH_ENABLED`. `.env.example` only lists `AIFI_AI_RUNTIME_ENABLED`, `AIFI_GRAPH_POLISH_QUESTION_ENABLED`, and `AIFI_REAL_PROVIDER_ENABLED`; it does not list `AIFI_AI_RUNTIME_LANGGRAPH_ENABLED` or feedback/report/review graph flags.
- [GITHUB_CODE] `InMemoryLangGraphRuntime` implements start/resume/replay/status/timeline/cancel. It records refs-only checkpoints and sanitized timeline events in process memory. Replay returns `read_only=True` and `formal_write_blocked=True`, and does not mutate the checkpointer in the inspected implementation.
- [GITHUB_CODE] `PolishQuestionGraphRuntime` is the most complete concrete business runtime. It compiles a LangGraph `StateGraph`, calls `run_polish_question_agent`, emits candidate payloads, checkpoint refs, validation refs, sanitized metadata, and timeline events. Provider path is gated by `AIFI_REAL_PROVIDER_ENABLED`.
- [GITHUB_CODE] `polish_question_graph.py` has a bounded local tool loop: `MAX_AGENT_STEPS=7`, `MAX_RETRIES=2`, `QUESTION_AGENT_TIMEOUT_SECONDS=20`, retry logging, timeout handling, and validator/finalize phases. This is a polish-question-specific loop, not a general AgentExecutor-level tool loop across all graphs.
- [GITHUB_CODE] `polish_feedback_graph.py` remains placeholder / skeleton / fake-runtime oriented. Its descriptor has `lifecycle_status="placeholder"`, `provider_enabled=False`, no formal write targets, and status names such as `fake_runtime_succeeded` / `skeleton_replayed`.
- [GITHUB_CODE] Runtime persistence tables and repositories exist for `agent_runs`, `agent_node_runs`, `agent_interrupts`, `agent_checkpoint_refs`, `llm_calls`, and `llm_call_payloads`. These repository surfaces provide owner scope, record version checks, idempotency, refs-only checkpoint metadata, and payload redaction.
- [GITHUB_CODE] The current concrete runner uses in-memory `_statuses`, `_timelines`, and `RefsOnlyLangGraphCheckpointer`. The inspected runtime does not yet wire `AgentRunRepository`, `AgentCheckpointRefRepository`, `AgentInterruptRepository`, or persistent timeline repositories into the active runner path.
- [GITHUB_CODE] Safety surfaces exist but are not all integrated into the runner. `AgentSideEffectGuard`, `AgentInterruptService`, `AgentTraceBridge`, and `FailClosedPersistedLlmTransport` are defined; path-scoped search found these classes mostly at definition sites or tests, not as active dependencies inside `InMemoryLangGraphRuntime` / `PolishQuestionGraphRuntime`.
- [GITHUB_CODE] Formal business writes are not performed directly by the runtime runner. Polish question graph output is consumed by `PolishUseCases`, then routed through `build_question_result_write_plan` and `AgentPersistenceHandoff.write_question_result`. Feedback/report/review formal write methods in `AgentPersistenceHandoff` fail closed.
- [GITHUB_CODE] Security / privacy protections are present at multiple runtime boundaries: candidate payloads reject sensitive payloads, checkpoint refs reject raw state and sensitive metadata, serializer blocks raw graph state, persisted LLM transport plans a sanitized call then fails closed before provider invocation if provider is disabled or unavailable.
- [PROJECT_SOURCE] `P8_MASTER_GOAL.md` requires LangGraph / multi-agent runtime integration through the AgentExecutor boundary; controlled tool loop bounds; interrupt / resume / checkpoint / replay; complete trace / timeline; typed handoff; default-off flags; no fake provider runtime path; and candidate-only runtime boundary.
- [PROJECT_SOURCE] `ADR-0005` is still `Proposed`. It constrains the target directory shape to `application/ai_runtime/**` + `infrastructure/ai_runtime/langgraph/**`, keeps Core Business free of LangGraph imports, treats checkpoint as runtime recovery/debug state, and forbids raw payload persistence and runtime direct formal writes.
- [PROJECT_SOURCE] The refactor implementation package lists `AIFI_AI_RUNTIME_LANGGRAPH_ENABLED` as a PR4+ default-off flag and says disabling it must prevent concrete adapter / fake graph execution while keeping DTOs importable.
- [TEST_RESULT] No pytest, build, or smoke command was run in this recon because the user requested read-only recon and prohibited test modifications; running pytest can create `.pytest_cache` or other artifacts. Current evidence from tests is read-only file inspection only.
- [TEST_RESULT] Read-only import checks: `/usr/bin/python3` cannot resolve `langgraph`; `./.venv/bin/python` resolves `langgraph==1.2.1` and can import `StateGraph`, `START`, and `END`.
- [TEST_RESULT] Read-only `git diff --stat` before writing this report was empty.

## Gaps

- `AgentExecutor` protocol exists but is not the active runtime integration boundary. P8 requires explicit AgentExecutor / AgentGraphRunner compatibility or a controller decision that `AgentGraphRunner` is the accepted concrete equivalent.
- `AiOrchestrationFacade` does not expose a public replay method, even though the runner implements replay.
- `AIFI_AI_RUNTIME_LANGGRAPH_ENABLED` is required by runtime code and project source, but missing from `.env.example`.
- Current runtime status, timeline, and checkpoint surfaces are in-memory for active runner execution. Persistent AI Runtime repositories exist but are not wired into the concrete runner.
- `polish_feedback_graph` is still placeholder / fake-runtime oriented and not a complete P8 controlled runtime.
- The controlled tool loop is implemented for Polish question only. It is not yet a reusable runtime-level policy with `allowed tools`, `allowed callers`, `side_effect_policy`, and unified stop conditions across all graphs.
- HITL interrupt semantics are available as a service and DTO surface, but not visibly wired into the concrete Polish question / feedback runtime flows inspected here.
- `AgentSideEffectGuard`, `AgentTraceBridge`, and `FailClosedPersistedLlmTransport` exist, but active runner integration is incomplete.
- Runtime API exposure for replay / status / timeline appears partial. Status and timeline exist through facade methods, but no dedicated Agent Runtime API endpoint was inspected as active current behavior.
- Environment consistency risk: system Python lacks LangGraph while project `.venv` has it. Validation commands must pin to the intended Python environment.

## Recommended Patch Scope

- Controller should first create `docs/goals/2026-06-05/P8_W0_SCOPE_LOCK.md` before any code patch.
- Recommended allowed files for the next implementation scope:
  - `apps/api/app/application/agents/runtime/__init__.py`
  - `apps/api/app/application/ai_runtime/contracts.py`
  - `apps/api/app/application/ai_runtime/facade.py`
  - `apps/api/app/application/ai_runtime/registry.py`
  - `apps/api/app/application/ai_runtime/runtime_flags.py`
  - `apps/api/app/application/ai_runtime/interrupts.py`
  - `apps/api/app/application/ai_runtime/side_effect_guard.py`
  - `apps/api/app/application/ai_runtime/trace_bridge.py`
  - `apps/api/app/application/ai_runtime/handoff.py`
  - `apps/api/app/application/ai_runtime/business_graphs/polish_question_graph.py`
  - `apps/api/app/application/ai_runtime/business_graphs/polish_feedback_graph.py`
  - `apps/api/app/infrastructure/ai_runtime/langgraph/checkpointer.py`
  - `apps/api/app/infrastructure/ai_runtime/langgraph/in_memory_runtime.py`
  - `apps/api/app/infrastructure/ai_runtime/langgraph/polish_question_runtime.py`
  - `apps/api/app/infrastructure/ai_runtime/langgraph/serializer.py`
  - `apps/api/app/infrastructure/ai_runtime/llm_trace/persisted_transport.py`
  - `.env.example` only for additive default-off runtime flags
  - focused tests under `tests/api/test_agent*`, `tests/api/test_pr4*`, `tests/api/test_pr5*`, `tests/api/test_pr6*`, `tests/api/test_pr8*`, `tests/api/test_polish_question_graph_integration.py`, and `tests/architecture/*` as selected by controller
  - `docs/goals/2026-06-05/**` for evidence-only reports
- Patch order recommendation:
  1. Align executor boundary decision: either adapt `AgentExecutor` to the active runtime or document why `AgentGraphRunner` is the accepted equivalent.
  2. Add facade replay surface if Phase 8 requires replay at facade/API-adjacent boundary.
  3. Add `.env.example` default-off `AIFI_AI_RUNTIME_LANGGRAPH_ENABLED` and any graph flags selected by scope lock.
  4. Wire runtime-level guard/trace/interrupt/checkpoint abstractions into the active runner path before expanding business graph behavior.
  5. Only then expand feedback graph from placeholder/fake-runtime semantics, preserving direct path fallback.

## Recommended Forbidden Files

- `apps/api/app/application/polish/question_generation_prompts.py`
- `apps/api/app/application/polish/feedback_prompt_assets.py`
- `apps/api/app/application/polish/*prompt*`
- `apps/api/app/application/ai_provider/**`
- `apps/api/app/infrastructure/llm/**` except read-only recon
- `apps/api/app/infrastructure/db/**` except read-only recon, unless controller explicitly authorizes persistent runtime wiring and migration impact
- `apps/api/migrations/**`
- `apps/api/app/api/v1/**` unless controller explicitly confirms existing runtime endpoints require compatible no-contract-change wiring
- `apps/web/**`
- `domain/polish/policies/**`
- production fake provider wiring
- `requirements.txt` / dependency lock files, because LangGraph is already declared and installed in project `.venv`; only modify if controller records a dependency decision
- `.env` or any secret-bearing local configuration

## Stop-Condition Findings

- No immediate stop condition for dependency addition: LangGraph is already declared in `requirements.txt` and available in project `.venv`.
- Stop before patch if validation must use system `/usr/bin/python3` without project `.venv`, because that environment cannot import LangGraph.
- Stop before patch if controller requires runtime work through `AgentExecutor` but rejects `AgentGraphRunner` as the current equivalent; the boundary mismatch needs a controller decision.
- Stop before patch if P8 implementation requires DB schema or migration changes. Current DB runtime models already exist; expanding them is outside this recon and P8 forbidden scope unless explicitly re-authorized.
- Stop before patch if implementation needs prompt/provider/API/frontend changes. Recon did not identify a need for those changes for runtime surface alignment.
- Stop before patch if feedback graph must be treated as complete runtime while still using `fake_runtime_succeeded` / skeleton semantics.
- Stop before patch if replay must be exposed through API/product behavior without an explicit API contract decision.
- Stop before patch if any implementation would let runtime or tool code write formal business facts directly rather than routing through Application Service -> Domain Policy / validation -> Handoff -> Repository.
- Stop before patch if source backfill would mark C4 as L5 release or Phase 8 done without full P8 validation.

## Confidence

Confidence: high

Confidence is high for the inspected code and dependency/config facts. It is medium for runtime behavior under full test execution because tests were not run in this read-only recon.

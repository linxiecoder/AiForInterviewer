---
title: 12_ACCEPTANCE_GATES
type: note
permalink: ai-for-interviewer/docs/project-sources/12-acceptance-gates
---

# 12 Acceptance Gates

## 通用 Gate

每个窗口必须通过：

- Scope
- Behavior
- Test
- Architecture
- Security
- Fake
- Traceability
- Decision
- Backfill

## Scope Gate

必须满足：

- Window ID 明确。
- Phase 明确。
- Capability IDs 明确。
- Allowed files 明确。
- Forbidden files 明确。
- Behavior change allowed 明确。
- Prompt/schema/provider/DB change allowed 明确。

禁止：

- 混入下个 Phase。
- 修改 forbidden files。
- 无 recon 直接 patch。

## Behavior Gate

必须满足：

- 行为变化被授权。
- API contract 不变，除非明确授权。
- DB schema 不变，除非明确授权。
- fallback 不伪装 success。
- validation failed 不伪装 success。
- provider unavailable 不伪装 success。

## Test Gate

必须满足：

- 指定测试运行。
- 结果记录。
- 无法运行时说明原因。
- 新能力必须有 regression test。
- 行为质量能力必须绑定 Eval 或明确 deferred。

## Architecture Gate

必须满足：

- Domain 不 import infrastructure/api/application.llm。
- Application 不含 prompt/provider/复杂 domain policy。
- Agent candidate only。
- Infrastructure 不含 business policy。
- Tool 不直接暴露 repository。
- Provider request compact and fail-closed。

## DDD Gate

Domain：

- 不访问 DB。
- 不调用 LLM。
- 不依赖 FastAPI。
- 不依赖 infrastructure。
- 只承载 entities / value objects / policies / invariants。

Application：

- 只做 command/query、repository port、context、domain policy、agent executor、transaction、DTO。
- 不承载 prompt/provider。
- 不承载复杂 domain policy。
- 不直接调用 LLM transport。

Agent：

- 只能输出 candidate / suggestion / validation / plan / trace。
- 不写正式状态。
- 不绕过 Application Service。
- 不直接确认资产、进展、评分。

Infrastructure：

- 不承载 business policy。
- 不决定 source support。
- 不决定 asset conflict。
- 不决定 next action。

## Agent Platform C0 Gate

适用于 Phase 1。

必须满足：

- Agent Platform 目标态 C 被文档锁定。
- Phase 1 只实现 C0，不把 B 当终态。
- AgentDefinition contract 存在或被明确规划。
- AgentDefinitionRegistry 存在或被明确规划。
- SkillRegistry 存在或被明确规划。
- ToolRegistry 存在或被明确规划。
- AgentExecutor port 存在或被明确规划。
- Handoff contract 存在或被明确规划。
- Agent output candidate-only 规则被测试或文档 gate 覆盖。
- Tool 不直接暴露 repository 的规则被测试或文档 gate 覆盖。
- Formal write 必须经 Application Service + Domain Policy + Handoff。

禁止：

- 只建 contracts/registry skeleton 后将 Agent Platform 标记 done。
- 局部 Question/Feedback tool schema 替代项目级 ToolRegistry。
- Agent 直接写业务对象。
- Candidate 被持久化为正式事实而无 handoff。

## Agent Platform C1 Gate

适用于 Phase 4 P4-W1。

必须满足：

- `polish_question_agent` 和 `polish_feedback_agent` 在项目级 `AgentDefinitionRegistry` 中注册。
- 两个 Agent 引用的所有 SkillDefinition 都能在 `SkillRegistry` 中解析。
- 两个 Agent 引用的所有 ToolDefinition 都能在 `ToolRegistry` 中解析。
- `SkillRegistry` 和 `ToolRegistry` 支持按 `agent_id` 列出定义。
- Question Agent 只能产出 `question_candidate`。
- Feedback Agent 只能产出 `feedback_candidate` 和 `asset_update_candidate`。
- AgentDefinition 不包含 formal output / formal write result 字段；正式写入只能经 Application Service + Domain Policy + Handoff。
- Feedback `asset_update_candidate` 的 handoff 必须 `user_confirmation_required=true`。
- ToolDefinition 必须声明 allowed `side_effect_policy`，并禁止 raw prompt、raw provider payload、full resume、full JD、secrets、tokens、cookies、api keys。
- ToolRegistry 必须拒绝 repository / DB / SQLAlchemy / session / unit-of-work 直接暴露。
- Trace contract 必须引用 input / plan / skill / tool / policy / provider / candidate / validation / handoff / output / events，并禁止敏感 raw payload。

禁止：

- 将 graph-local `TOOL_SCHEMAS` 当作项目级 `ToolRegistry` 的替代。
- 在 Phase 4 C1 中接入 AgentExecutor runtime。
- 在 Phase 4 C1 中修改 prompt/provider/API/DB/domain policy 行为。
- 因 C1 catalog 已存在而将 Phase 5/6/8/9 runtime/eval gates 标记完成。

## Agent Platform C1 Hygiene Gate

适用于 P4-W1.fix.01。

必须满足：

- `catalog.py` 仅作为 C1 registry builder / aggregator，不承载完整 Question / Feedback skill 和 tool 清单。
- Question / Feedback 具体 AgentDefinition、SkillDefinition 和 ToolDefinition 定义位于 agent definitions 子模块，且仍注册到项目级 registry。
- `agent.version` 使用稳定语义版本，不使用执行阶段标记。
- `schema_version` 表示定义结构版本，`catalog_revision` 是唯一允许记录 P4-W1.fix.01 窗口标记的位置。
- 每个 `SkillDefinition` 必须包含非空 purpose、preconditions、postconditions、fallback_policy、definition_version、schema_version 和 test_refs。
- C1 candidate-only、handoff、trace、Tool no repository exposure 和 forbidden data gate 继续通过。

禁止：

- 新增 Question-only 或 Feedback-only registry 绕过项目级 registry。
- 把 catalog hygiene 解释为 Phase 5 / Phase 6 runtime wiring 已完成。
- 因版本策略修正而修改 prompt/provider/API/DB/domain policy 行为。

## Question Agent Gate

必须满足：

- source_support_level / source_support_summary 有 reason codes 和 evidence refs。
- grounding blocking 不持久化正常题目。
- job_gap_only 不声称候选人做过。
- adjacent_project_evidence 必须是假设。
- follow-up 不重复 completed focus。
- deterministic fallback 不等于 generated success。
- Question Agent 只能产出 question_candidate。
- Formal question write 必须走 Application Service + Domain Policy + Handoff。

## Feedback Agent Gate

必须满足：

- asset_consistency_check 存在。
- answer_coverage 存在。
- answer_change_analysis 存在。
- feedback_cards 存在。
- asset conflict 使 asset_consistency card 排第一。
- asset conflict 禁止 generate_next_question。
- asset candidate 必须 user_confirmation_required=true。
- provider unavailable / validation failed 不伪装成功。
- Feedback Agent 只能产出 feedback_candidate / asset_update_candidate。
- Asset update formal write 必须用户确认。

## P5P6-W1 Planned Workflow Gate

适用于 `P5P6-W1-C2-C3-PLANNED-WORKFLOW-L5-FOUNDATION`。

必须满足：

- Phase 5 / Phase 6 只声明为 C2 / C3 L2 planned guarded workflow。
- Question provider / graph output 必须先形成 `question_candidate`，再由 Application Service + Domain Policy + Handoff 路径决定是否正式写入。
- graph disabled、fake transport、deterministic fallback 或 validation failed 不得持久化正常题目，也不得报告为 generated success。
- Feedback 成功路径必须暴露 `feedback_candidate` refs；存在资产更新建议时必须暴露 `asset_update_candidate` refs 且 `user_confirmation_required=true`。
- Feedback asset update candidate 不得直接写正式资产。
- Trace / metadata 只能记录 input refs、policy refs、validation refs、candidate refs、handoff refs，不得写入 raw prompt、raw provider payload、full resume、full JD 或 secrets。
- Phase 8 LangGraph / multi-agent runtime、Phase 11 Supervisor / Orchestrator、Phase 12 L5 release gate 必须保持未实现。

本窗口验证记录：

| Gate | Evidence | Result |
|---|---|---|
| Question candidate-only | `test_polish_question_graph_integration.py` reported `12 passed`; `test_pr5_polish_question_graph_persistence_handoff.py` reported `15 passed`; `test_polish_question_refactor_phase1.py` reported `64 passed`; pytest processes exited `1` because repo root had a pre-existing `tmp` temp-like directory | behavior evidence present; temp checker gap deferred |
| Feedback candidate handoff | `test_polish_feedback_runtime.py` reported `7 passed`; pytest process exited `1` because repo root had a pre-existing `tmp` temp-like directory | behavior evidence present; temp checker gap deferred |
| Architecture / platform | raw `tests/architecture -q` exited `2` because `app` was not on `PYTHONPATH`; supplemental `PYTHONPATH=.:apps/api .venv/bin/python -m pytest tests/architecture -q` reported `33 passed, 2 xfailed`, then exited `1` because of the same repo-root `tmp` temp-like directory | architecture evidence present; environment/PYTHONPATH and temp checker gaps deferred |
| P5/P6 eval runners | `tests/evals -q` reported `19 passed` then exited `1` because of repo-root `tmp`; `evals.runners.run_question_eval` exited `0` with 3 total / 0 failed; `evals.runners.run_feedback_eval` exited `0` with 5 total / 0 failed | scoped eval evidence passed; temp checker gap deferred |
| Broad API compatibility | `tests/api -k "question or feedback or agent or handoff or canonical or source_support"` reported `299 passed / 1 failed / 323 deselected`; the remaining failure is `tests/api/test_polish_canonical_evidence.py::test_polish_question_and_feedback_context_include_canonical_assets`, which still expects provider-unavailable Question fallback to persist a formal question and is outside this remediation write scope | legacy canonical-evidence alignment deferred; not a done gate |

P5P6-W1.fix.02 current validation record:

| Gate | Evidence | Result |
|---|---|---|
| Canonical evidence legacy alignment | `.venv/bin/python -m pytest tests/api/test_polish_canonical_evidence.py::test_polish_question_and_feedback_context_include_canonical_assets -q` | `1 passed`; provider-unavailable Question fallback remains `VALIDATION_FAILED` `question_candidate`, canonical asset refs remain asserted on candidate metadata, and Feedback canonical context remains asserted |
| Question candidate-only | `test_polish_question_graph_integration.py` = `12 passed`; `test_pr5_polish_question_graph_persistence_handoff.py` = `15 passed`; `test_polish_question_refactor_phase1.py` = `64 passed` | passed; no formal generated success restored for fallback |
| Feedback candidate handoff | `test_polish_feedback_runtime.py` = `7 passed` | passed; `feedback_candidate` bridge remains wired |
| Architecture / platform | Raw `.venv/bin/python -m pytest tests/architecture -q` still requires application import path and exits collection with `ModuleNotFoundError: No module named 'app'`; `PYTHONPATH=.:apps/api .venv/bin/python -m pytest tests/architecture -q` = `33 passed, 2 xfailed` | behavior gate passed with existing path precondition; not a Phase 5/6 business assertion failure |
| P5/P6 eval runners | `tests/evals -q` = `19 passed`; `evals.runners.run_question_eval` = 3 total / 0 failed; `evals.runners.run_feedback_eval` = 5 total / 0 failed | passed |
| Broad API compatibility | `.venv/bin/python -m pytest tests/api -k "question or feedback or agent or handoff or canonical or source_support" -q` = `300 passed, 323 deselected` | passed; previous `299 passed / 1 failed` blocker cleared |
| Temp leak checker | repo-root `tmp/` moved to `/tmp/aifi-repo-root-tmp-P5P6-W1.fix.02-20260605`; `find . -maxdepth 3 -type d -name "tmp" -print` now reports only `./docs/tmp` | repo-root temp blocker cleared without disabling leak detection |

Current P5/P6 source status: `validated_with_deferred_l5_runtime`. This does not close Phase 8 runtime, Phase 9 CI eval gate, Phase 11 Supervisor / Orchestrator, Phase 12 L5 release gate, or provider/prompt/API/DB work.

禁止：

- 将本窗口写成 L5 done、autonomous Agent、Phase 11 / Phase 12 完成或 Phase 9 CI gate 完成。
- 为了满足旧测试而恢复 fake / default / graph-disabled fallback formal write。
- 修改 prompt/provider/API/DB 行为来扩大本窗口。

## Provider Gate

必须满足：

- CompactProviderRequestBuilder required。
- No full prompt asset fallback。
- Forbidden keys rejected。
- Provider request schema-bound。
- Provider request redacted。
- Provider request traceable。
- Provider unavailable fail-closed。
- Validation failed fail-closed。

Forbidden keys：

- raw_prompt
- system_prompt
- developer_prompt
- raw_completion
- provider_payload
- raw_provider_payload
- full_resume
- full_jd
- full_answer
- full_asset_body
- token
- secret
- cookie
- api_key

## Canonical Evidence Gate

必须满足：

- CanonicalEvidencePack 是 Question / Feedback / Progress / Scoring / Training loop 的共享事实契约。
- source_support_summary 包含 level / refs / reason_codes / confidence。
- asset_confirmed 是 canonical asset 正常事实来源。
- asset_archived 不作为默认事实源。
- 当前回答新事实不能直接成为正式资产。
- asset conflict 必须 HITL。
- context_digest 稳定。

## Fake Gate

必须满足：

- Fake 只能用于 tests / evals / replay。
- Runtime env 不允许 fake provider。
- Fake path 不得伪装真实 provider success。
- Fake output 必须 trace visible。
- Fake imports 不得污染 production runtime wiring。

## Agent Platform C4 Gate

Current status: `partial_with_deferred_gaps`。

Accepted evidence in P8-GOAL-ONE-SHOT-C4-RUNTIME:

- Five read-only recon reports and `P8_W0_SCOPE_LOCK.md` exist under `docs/goals/2026-06-05/`.
- `AgentGraphRunnerExecutorAdapter` provides an AgentExecutor-compatible boundary, blocks runtime formal refs from result fields and result/status/timeline metadata including formal-write counter variants and repository / DB business write counters, rejects runtime result metadata that reports fake-provider use or fail-open fallback as generated success, preserves runner output / interrupt / typed candidate payload refs, all current facade start surfaces now route through the adapter, and facade-created status / timeline / cancel route through adapter read/cancel for known runs with owner-scope preservation while descriptor-unsupported facade-created timeline/cancel fail closed before runner access.
- `AgentRuntimeLoopPolicy` is required by the adapter and rejects incomplete P8 required stop-condition sets (`max_steps_exceeded`, `timeout`, `validation_failed`, `tool_not_allowed`, `formal_write_requested`, `interrupt_required`, `provider_failed`); `AiOrchestrationFacade` now injects validated `runtime_loop_policy` metadata into all current facade start surfaces plus facade-created resume/replay commands and fails closed when descriptor bounds are missing; generic direct in-memory runtime start also rejects missing or invalid `runtime_loop_policy` before graph invocation.
- Tool calls must provide a registered `ToolDefinition`; caller, permission scope, owner scope, side-effect policy and tool-declared forbidden payload are fail-closed.
- Polish question concrete runtime phase tools require registered runtime `ToolDefinition` lookup and fail closed when the tool is not registered, the runtime loop policy disallows the caller / side-effect policy, or the payload contains a `ToolDefinition.forbidden_data` key.
- Polish question direct runtime policy includes the P8 `interrupt_required` stop condition.
- Feedback PR8 provider trace gate requires registered runtime `ToolDefinition` lookup and fails closed on unregistered trace gate node, caller mismatch, permission-scope mismatch, owner-scope mismatch, side-effect mismatch and tool-declared forbidden-data payloads.
- Feedback direct in-memory runner start requires descriptor-matching `runtime_loop_policy` metadata and rejects missing or mismatched fields before fake payload construction.
- `AiOrchestrationFacade.replay_agent_run()` returns read-only / formal-write-blocked replay without API contract change.
- Replay now preserves original failed / blocked / interrupted / cancelled status category as `replayed_*`, original status, failure/fallback reasons, refs-only trace comparison, nested refs-only trace metadata, trace-match flag and zero provider/tool/repository/DB/formal-write counters through `AgentReplayResult.metadata`, `AgentGraphRunnerExecutorAdapter` and `AiOrchestrationFacade.replay_agent_run()` for the covered generic/Question/Feedback runtime replay paths; Feedback replay comparison includes validation refs from status trace refs.
- `AgentReplayResult` rejects replay metadata with positive or unparseable provider/tool/repository/DB/formal-write side-effect counters, so replay outputs that report provider calls, external tool calls, repository access, DB business writes or formal business writes fail closed.
- `AiOrchestrationFacade.resume_interrupted_run()` requires `checkpoint_ref`, strict non-negative integer `base_version` and `idempotency_key`, carries checkpoint/base/idempotency control fields into runner resume payload, fails closed on unsupported actions before runner invocation, and blocks returned runtime formal refs through the AgentExecutor adapter boundary.
- P8 HITL interrupt types are represented at the interrupt service boundary, require checkpoint refs, and resume validates checkpoint ref / base version / allowed action.
- Generic in-memory runtime start registers checkpoint-bound user-confirmation interrupts through `AgentInterruptService`, and generic runtime resume validates checkpoint ref / base version / idempotency / allowed action before graph continuation.
- Polish question concrete runtime opens checkpoint-bound runner HITL interrupts for refs-only P8 trigger metadata, keeps those paths non-success / formal-write-blocked, and resumes through service-backed checkpoint ref / base version / idempotency / allowed action validation.
- Feedback in-memory runtime opens checkpoint-bound runner HITL interrupts for refs-only `formal_write_attempt_ref`, `asset_conflict_ref`, `low_confidence_formal_update_ref`, `ambiguous_ownership_ref` and `validation_failed_partial_result_ref` metadata and does not report those paths as succeeded.
- Low-confidence Feedback HITL refs populate `trace_refs.low_confidence_refs` and drawer `low_confidence_flags`.
- Feedback service-backed HITL resume timeline metadata preserves candidate refs and validation refs from the interrupted run.
- Service-backed in-memory runner resume validates checkpoint ref / base version / allowed action before graph continuation.
- `AgentHandoffEnvelope` provides typed candidate handoff fields.
- Source result candidate descriptors can be converted into target `AgentExecutionPlan` input refs through `HandoffContract` / `AgentHandoffEnvelope` without raw payload sharing.
- `execute_agent_handoff()` starts the target `AgentExecutor` from a typed handoff plan and preserves refs-only metadata.
- Asset update candidate descriptors carry only `asset_body_ref` / `asset_schema_id`, confirmation and formal-write-blocked metadata; raw asset body and `formal_refs` do not cross the handoff metadata boundary.
- Target executor timelines can surface command handoff envelope candidate / validation / handoff refs without raw prompt, raw asset body or candidate payload body.
- `AgentExecutionTrace` includes P8 agent version, AI task, low-confidence, failure and fallback fields; `AgentExecutionTrace` and `AgentHandoffEnvelope` recursively filter nested forbidden metadata keys; Feedback status trace refs include validation refs for replay comparison while resume/cancel control metadata remains checkpoint-only; runtime replay metadata preserves nested status `metadata.trace_refs` as refs-only metadata and promotes validation / handoff / tool / policy / provider / low-confidence refs for adapter trace mapping; adapter traces map validation / handoff / tool / policy / provider refs when supplied by command/runtime metadata and merge command metadata `tool_refs` / `policy_refs` / `provider_refs` / `validation_refs` / `handoff_refs` / `low_confidence_flags` with runtime result / timeline event refs; runtime result/status/timeline metadata fails closed on non-empty `formal_refs`, non-zero formal-write counter variants and non-zero repository / DB business write counter variants; adapter timeline mapping includes event metadata refs and command handoff envelope refs; generic runtime start/resume/cancel events, Feedback service-backed resume/cancel events and concrete Question start/resume/cancel plus Feedback runtime start/service-backed cancel timeline events emit refs-only metadata, including generic direct `run_started` / `run_resumed` / `run_succeeded`, Feedback direct `run_started` / `run_succeeded`, and Question direct `run_started` / `interrupt_opened` / `run_resumed` / resumed `run_succeeded` P8 command ref matrix preservation plus Question cancel checkpoint/validation ref separation; cancel events preserve candidate/validation/output/checkpoint refs where applicable with zero provider/formal-write counters; and adapter result/status surfaces expose mapped handoff refs.
- Runtime DTOs classify canonical status categories for run result/status/replay/task/interrupt refs and reject unknown status or success-like status with `failure_reason`; adapter result/status mapping and Polish question application task status mapping reuse the shared guard while keeping candidate-only success projected to existing queued task semantics.
- `AgentTraceBridge` rejects unknown non-DTO node/run-finished trace statuses before trace write, and adapter metadata phase/tool event status mapping rejects unknown values before trace event emission.
- Feedback in-memory runtime emits typed refs-only `feedback_candidate` and `asset_update_candidate` payloads with validation refs, checkpoint-backed trace refs, refs-only asset body descriptors and no formal refs.
- `.env.example` documents `AIFI_AI_RUNTIME_LANGGRAPH_ENABLED=false`, and runtime result metadata now fails closed when it reports fake-provider use or fail-open fallback as generated success.
- Latest facade start surface coverage passed: `5 passed, 18 deselected in 0.15s`; facade-created status/timeline/cancel adapter routing coverage passed: `1 passed, 22 deselected in 0.16s`; descriptor-supported resume/replay facade guard passed: `2 passed, 23 deselected in 0.19s` after expected red failures; descriptor-supported timeline/cancel facade guard passed: `2 passed, 25 deselected in 0.11s` after expected red failures and full facade regression passed `27 passed in 0.34s`; generic direct runtime start timeline ref-matrix gate passed: `1 passed, 9 deselected in 0.44s` after expected red failure; generic direct runtime missing-policy gate passed: `1 passed, 9 deselected in 0.41s` after expected red failure; generic direct runtime resume/succeeded ref-matrix gate passed: `1 passed, 10 deselected in 0.56s` after expected red `KeyError: 'plan_refs'`; PR4 runtime regression passed `12 passed in 0.64s`; generic replay nested trace metadata gate passed `1 passed, 11 deselected in 0.61s` after expected red `KeyError: 'trace_refs'`; Feedback direct runtime start/succeeded ref-matrix gate passed: `1 passed, 15 deselected in 0.52s` after expected red `RuntimeValidationError`; PR6 runtime regression passed `17 passed in 0.70s`; Feedback replay trace refs metadata gate passed `1 passed, 16 deselected in 0.59s` after expected red `KeyError: 'trace_refs'`; Question direct runtime start/resume/succeeded ref-matrix gate passed: `1 passed, 13 deselected in 0.58s` after expected red `KeyError: 'plan_refs'`; Question graph integration regression passed `15 passed in 1.71s`, including application status taxonomy mapping; P8 application-layer AgentExecutor adapter gate passed: `tests/application` `1 passed in 0.08s`; typed handoff execution gate passed: `1 passed, 16 deselected in 0.09s`; Question cancel checkpoint/validation ref separation remediation passed: `1 passed, 12 deselected in 0.68s` after expected red failure; adapter command metadata `validation_refs` / `handoff_refs` / `low_confidence_flags` trace/timeline remediation passed: `2 passed in 0.16s` after expected red failures; nested runtime trace metadata extraction gate passed: `1 passed, 17 deselected in 0.20s` after expected red failure; runtime formal-ref metadata guard passed: `1 passed, 18 deselected in 0.12s` after expected red failure; runtime formal-write counter variant guard passed: `1 passed, 19 deselected in 0.14s` after expected red failure; runtime repository / DB business-write counter guard passed: `1 passed, 20 deselected in 0.13s` after expected red failure; runtime fake-provider / fail-open fallback metadata guard passed: `2 passed, 21 deselected in 0.12s` after expected red failures; `test_agent_graph_runner.py` passed `23 passed in 0.27s`; earlier command metadata `tool_refs` / `policy_refs` / `provider_refs` remediation also passed. Feedback direct runtime loop-policy gate remediation passed: `2 passed in 0.51s` after expected red failures; Feedback status/replay validation-ref trace comparison remediation passed: `1 passed in 0.65s`; nested metadata contract remediation passed: `1 passed in 0.15s`; required P8 stop-condition contract remediation passed: `1 passed, 14 deselected in 0.17s` after expected red failure; `tests/api/test_agent_contracts.py` passed `15 passed in 0.23s`; replay-status focused remediation passed: `2 passed in 0.53s`; replay side-effect fail-closed focused tests passed: `2 passed in 0.20s`; impacted runtime / replay / resume regression passed: `43 passed in 1.93s`; focused P8 core passed: `157 passed in 3.63s`; architecture gate passed: `24 passed in 1.49s`; latest agent API gate passed: `108 passed in 2.18s`; latest API gate passed: `719 passed in 64.71s (0:01:04)`; latest PR4-PR8 runtime/graph gate passed: `97 passed in 6.01s`; full test-suite passed: `1151 passed in 89.38s (0:01:29)`; latest P8 Q/F regression passed: `286 passed in 19.28s`.

Still not accepted as full `done`:

- Raw asset body transfer and formal asset composition/write semantics remain deferred.
- Future / indirect graph tool-loop expansion outside the covered facade start surfaces and Question/Feedback direct paths still needs shared loop-policy and registry lookup evidence.
- Remaining product-level runtime/orchestration wiring and runner-bound HITL emission / resume validation outside the already covered facade/generic/Question/Feedback paths remains deferred.
- Complete trace population for remaining product/future runtime events outside current generic start/resume/cancel plus Feedback service-backed resume/start/cancel, Question start/resume/cancel and target handoff timeline coverage remains deferred.
- DB persistence/API status taxonomy beyond the runtime DTO, Polish question application task status mapping, `AgentTraceBridge` and adapter metadata event status guards remains deferred.
- Product-level Supervisor / L5 orchestration is not implemented; Phase 11 Supervisor / Orchestrator and Phase 12 L5 release gate remain out of scope.
- No L5 release, formal F8/M8 release, prompt/provider/API/DB/frontend/domain-policy change is claimed.

## Phase 9 Eval / CI Regression Gate

Current status: `complete_with_deferred_remote_ci_gap` for deterministic replay/fixture regression gate after Phase 10 closeout acceptance. `EVAL-001` remains `validated` in the traceability matrix; it is not `done` while remote GitHub Actions evidence is deferred and stale committed report metadata risk remains.

Accepted evidence in P9-W0-W4-EVAL-CI-REGRESSION-GATE:

- Five read-only recon reports exist under `docs/goals/2026-06-06/P9_AGENT_*.md`, and the controller merge exists at `docs/goals/2026-06-06/P9_CONTROLLER_RECON_MERGE.md`.
- `evals/suites/phase9.json` binds suite ID, capability IDs, dataset refs, grader refs, minimum pass criteria, CI behavior, negative-control refs and non-claims.
- `evals/datasets/phase9/*.jsonl` covers canonical evidence/source support, Question Agent, Feedback Agent, provider boundary, fake gate, handoff/trace and runtime-foundation deferred cases.
- `evals/graders/code_rules.py` adds deterministic task types for answer coverage, provider boundary, fake gate, handoff/trace, runtime deferred gap and source-support contracts; scanner coverage includes normalized forbidden keys and secret-like value patterns.
- `scripts/evals/run_eval_gate.py` runs the default `replay` gate, writes `evals/reports/phase9_eval_report.json`, writes Markdown reports such as `docs/goals/2026-06-06/P9_EVAL_REPORT.md`, scans JSON/Markdown report content before write and exits non-zero on blocking failures.
- Negative control passed: `--expect-fail-fixture` observes the intentionally failing job-gap completed-work claim fixture and returns success only because the expected blocking failure is detected.
- CI integration exists in `.github/workflows/eval-gate.yml`; default job runs eval tests, replay gate and negative-control gate without live provider credentials.
- Local validation evidence recorded in `docs/goals/2026-06-06/P9_FINAL_REPORT.md`: `tests/evals` passed, replay gate passed with 30 total / 30 passed / 0 blocking failures / 2 deferred cases, and negative-control gate passed.

Gate rules:

- Blocking eval failure must return non-zero.
- Default CI mode must not require provider credentials.
- Reports must not store raw prompt, raw completion, provider payload, full resume, full JD, full answer, full asset body, secrets, tokens, cookies or API keys.
- Skips/deferred cases must be explicit and categorized.
- Replay/fixture/fake-visible evidence must not be represented as real-provider quality evidence.

Still not accepted as broader `done`:

- No real-provider quality is certified.
- No P8 runtime deferred gap is implemented or closed.
- No Phase 11 Supervisor / Orchestrator or Phase 12 L5 release gate is implemented.
- No formal F8/M8 release readiness is claimed.
- No remote GitHub Actions success is claimed unless a visible passing run and artifact are cited.

## Phase 10 Closeout / Source Backfill Gate

适用于 `P10-W1-STAGE-CLOSEOUT-SOURCE-BACKFILL`。

必须满足：

- Phase 10 只做 docs/source-backfill，不修改业务代码、prompt/provider/API/DB/domain/runtime/frontend、eval runner、grader、suite、dataset、workflow 或 committed eval reports。
- Phase 9 post-push accepted status 可写为 `complete_with_deferred_remote_ci_gap` only if `deferred_remote_ci_gap` is explicitly recorded.
- `EVAL-001` 只能按 matrix 语义保持 `validated`，不得在 remote CI gap 和 stale metadata risk 未关闭时升级为 `done`。
- Remote CI 只有在 GitHub Actions run/artifact 可见且通过时才能作为 evidence；local validation 不能替代 remote CI claim。
- Committed reports with stale metadata short SHA `f86adea` are residual report-metadata risk unless remediated by a separate authorized report refresh window.
- Non-mutating eval reruns must use an external report dir such as `/tmp/...` and must not rewrite `evals/reports/**` or `docs/goals/2026-06-06/P9_EVAL_REPORT.md` in this window.
- Phase 8 runtime gaps remain deferred.
- Phase 11 Supervisor / Orchestrator remains not started.
- Phase 12 / L5 release remains not started and no formal F8/M8 release readiness is claimed.

Phase 10 accepted evidence:

| Gate | Evidence | Result |
|---|---|---|
| Scope / forbidden paths | `git status --short --untracked-files=all` clean before patch; edits limited to allowed docs/source files | pass pending final diff audit |
| HEAD / origin | `git rev-parse HEAD` and `git rev-parse origin/main` both `76c670c859d3f7d32d13e604b3d0edffeefd2048` | pass |
| Local eval tests | `PYTHONPATH=.:apps/api .venv/bin/pytest tests/evals -q` | `27 passed` |
| Non-mutating current eval rerun | `python3 scripts/evals/run_eval_gate.py --suite phase9 --mode replay --report-dir /tmp/aifi-p10-closeout-eval-reports` | `30 passed`, `0 blocking_failures`, `2 deferred`, current short SHA `76c670c` |
| Negative control | `python3 scripts/evals/run_eval_gate.py --suite phase9 --mode replay --expect-fail-fixture` | expected failure observed |

禁止：

- 把 `complete_with_deferred_remote_ci_gap` 改写为 remote CI passed。
- 把 stale committed report metadata 当成行为 blocker 并在本窗口重写 reports。
- 关闭 Phase 8 runtime gaps。
- 标记 L5 release、Phase 11 Supervisor / Orchestrator done 或 Phase 12 release gate done。

## L5 Multi-Agent Gate

适用于 Phase 11 / Phase 12 的 L5 能力声明。

必须满足：

- Phase 0-10 明确保持 L5 Foundation `closed_with_deferred_gaps`，不得作为 L5 release。
- `deferred_remote_ci_gap`、Phase 8 runtime gaps、stale committed report metadata risk、Supervisor / Orchestrator not started、Phase 12 release gate not started 和 real-provider quality certification non-claim 必须显式处理。
- L5-002 到未拆分的 L5-006 不得在 P11-W0 标记 implemented、validated 或 done；D-W0 后使用 `L5-006A` / `L5-006B` 拆分状态，禁止继续用未拆分 `L5-006` 作为完成口径。
- replay / fake / fixture evidence 不得当作 real-provider quality certification。
- remote CI claim 必须引用 visible passing GitHub Actions run 和 artifact。
- 每个跨 Agent 输出仍为 candidate / suggestion / validation / plan / trace。
- formal write 只能经 Application Service -> Domain Policy -> Handoff。

禁止：

- 以 unit tests alone 声称 L5 release。
- 以 serial service calls disguised as MultiAgent 声称 L5 orchestration。
- 以 contracts-only documentation 声称 Supervisor / Orchestrator implemented。
- 以 Phase 8 foundation partial 声称 Phase 11/12 done。

## P12-W1 Executable Eval Suite Foundation Gate

P12-W1 may be accepted only as an eval-suite foundation when:

- executable runner exists under scripts/evals/run_l5_eval_suite.py;
- executable Phase 12 suite / datasets exist under tests/evals/phase12/**;
- Phase 12 gate test exists and passes;
- deterministic run passes with zero blocking failures;
- negative control fails as expected;
- CI workflow binding may exist, but visible remote CI artifact evidence remains a separate production-release claim;
- no product behavior, provider, prompt, DB, API contract, frontend, or production runtime behavior changes are introduced;
- no raw prompt / raw provider payload / raw completion / full resume / full JD / full asset body is persisted.

Non-claims:

- P12-W1 does not complete replay / resume / failure fixtures.
- P12-W1 does not close `L5-006A` local hardening.
- P12-W1 does not start or close `L5-006B` production release.
- P12-W1 does not claim L5 release.
- P12-W1 does not claim real-provider quality certification.
- P12-W1 does not record human release decision.

## Phase 11 Scope Gate

适用于 Phase 11 L5 Controlled Multi-Agent Orchestration。

必须满足：

- fresh scope lock 选择一个已确认的 next-window option。
- registered Supervisor / Orchestrator Agent scope 明确。
- typed cross-agent goal decomposition、plan、handoff、state、checkpoint、replay 和 trace contracts 明确。
- bounded tool loop 包含 `max_steps`、`max_retries`、`timeout` 和 `stop_conditions`。
- HITL triggers 覆盖 asset conflict、formal write、low confidence、ambiguous ownership、validation failed with partial result。
- 至少一个三业务 Agent 产品 workflow 的实现和验证边界明确。
- candidate-only 和 formal-write handoff 边界保持。
- Phase 8 runtime gaps 是被实现、被验证还是继续 deferred 必须逐项说明。

禁止：

- unbounded autonomous swarm。
- Agent direct DB / repository write。
- Tool direct repository exposure。
- infrastructure business policy。
- prompt/provider/API/DB/frontend/domain behavior changes unless separately scoped。
- committed eval report rewrite。
- remote CI claim without visible run/artifact。

## P11-W1 Contract-first Orchestrator Gate

适用于 `P11-W1-CONTRACT-FIRST-ORCHESTRATOR` / Option A。

Status:

- `contract_slice_complete_with_deferred_runtime_gaps` is allowed only for the contract-first slice.
- This status is not L5 release, not product workflow completion and not Phase 8 runtime gap closure.

必须满足：

- `interview_orchestrator_agent` is registered only in the L5 contract catalog.
- Existing Phase 4 C1 builder continues to register Question / Feedback only.
- Cross-agent plan, plan step, handoff route, state/checkpoint/replay and trace/timeline contracts exist as immutable contract-only dataclasses.
- Cross-agent contracts require non-empty IDs, trace refs, validation refs, state refs and stop conditions where applicable.
- Cross-agent contracts normalize tuple/list inputs and filter forbidden metadata keys.
- Orchestrator skills are `contract_only`, do not call LLM, do not execute runtime logic, do not access DB/repository and include eval refs or deferred eval refs.
- Orchestrator tools are `read_only` or `forbidden`, do not expose repository, DB, SQLAlchemy session, unit of work or formal writer, and include required forbidden data keys.
- L5 contract catalog validates AgentDefinition -> SkillDefinition / ToolDefinition references.
- Architecture gates prove candidate-only outputs, no formal outputs, no product workflow execution, no runtime wiring and no L5 release claim.

禁止：

- wiring Orchestrator into `AgentExecutor`, LangGraph, `AiOrchestrationFacade`, Question workflow, Feedback workflow, API routes or persistence.
- executing Supervisor / Orchestrator at runtime.
- modifying provider, prompt, API, DB, frontend, domain policy, eval datasets, eval graders, eval suites, eval reports, scripts or workflow files.
- claiming L5 release, real-provider quality certification, remote CI success, Phase 12 release gate completion or Phase 8 runtime gap closure.

P11-W1 non-claims:

- P11-W1 does not implement product multi-agent workflow.
- P11-W1 does not execute Supervisor / Orchestrator at runtime.
- P11-W1 does not close Phase 8 runtime gaps.
- P11-W1 does not close `deferred_remote_ci_gap`.
- P11-W1 does not rewrite stale eval reports.
- P11-W1 does not certify real-provider quality.
- P11-W1 does not claim L5 release.
- P11-W1 does not implement Phase 12 release gate.

## P11-W2 Runtime-hardening Slice Gate

适用于 `P11-W2-RUNTIME-HARDENING-SLICE`。

Status:

- `runtime_hardening_slice_complete_with_deferred_product_workflow` is allowed only for the narrow runtime-hardening slice.
- This status is not L5 release, not product workflow completion, not remote CI success and not Phase 12 release gate completion.

必须满足：

- Cross-agent handoff route validation fails closed on source/target mismatch, invalid candidate type, missing trace refs, missing validation refs, formal refs and unsafe metadata.
- Cross-agent resume validation requires `checkpoint_ref`, non-negative integer `base_version`, `idempotency_key`, owner scope, `interrupt_ref` and supported action.
- Cross-agent replay metadata remains `read_only`, `formal_write_blocked` and zero-provider/tool/repository/DB/formal-write.
- Cross-agent trace/timeline mapping preserves plan, handoff, validation and candidate refs separately and rejects collapsed output refs.
- HITL trigger validation covers `formal_write_requested`, `asset_conflict`, `low_confidence`, `ambiguous_ownership` and `validation_failed_partial_result`, and rejects success-like statuses when a failure reason is present.
- Focused tests cover negative handoff, resume, replay, trace/timeline and HITL cases.

禁止：

- wiring Orchestrator into `AgentExecutor`, LangGraph, `AiOrchestrationFacade`, Question workflow, Feedback workflow, API routes or persistence.
- executing `interview_orchestrator_agent` as a runtime agent.
- product multi-agent workflow implementation.
- prompt/provider/API/DB/frontend/domain behavior changes.
- eval dataset, grader, suite, report, script or workflow changes.
- claiming L5 release, real-provider quality certification, remote CI success, Phase 12 release gate completion or full Phase 8 runtime gap closure.

P11-W2 non-claims:

- P11-W2 does not implement product multi-agent workflow.
- P11-W2 does not execute `interview_orchestrator_agent` as a runtime agent.
- P11-W2 does not close all Phase 8 runtime gaps.
- P11-W2 does not close `deferred_remote_ci_gap`.
- P11-W2 does not rewrite stale eval reports.
- P11-W2 does not certify real-provider quality.
- P11-W2 does not claim L5 release.
- P11-W2 does not implement Phase 12 release gate.
- P11-W2 does not change provider, prompt, API, DB, frontend, domain policy or business persistence behavior.

## P11-W3 Minimal Three-Agent Candidate Product Slice Gate

适用于 `P11-W3-MINIMAL-THREE-AGENT-PRODUCT-SLICE`。

Status:

- `candidate_product_slice_complete_with_deferred_formal_write_and_release_gate` is allowed only for the minimal candidate-only product slice.
- This status is not formal write completion, not L5 release, not real-provider quality certification, not remote CI success and not Phase 12 release gate completion.

必须满足：

- L5 contract catalog registers `asset_candidate_agent` and `training_plan_agent` through project-level AgentDefinition / Skill / Tool registries.
- Existing C1 catalog continues to register only `polish_question_agent` and `polish_feedback_agent`.
- Minimal product slice includes the three business agents `polish_feedback_agent`, `asset_candidate_agent` and `training_plan_agent`.
- Happy path emits candidate refs only: `feedback_candidate`, `asset_update_candidate` and `training_plan_candidate`.
- Handoff refs connect feedback -> asset candidate -> training plan candidate.
- Asset update candidate requires user confirmation and keeps `formal_write_blocked`.
- Missing required refs fail closed.
- Asset conflict and formal write request block or interrupt and are trace-visible.
- Low confidence is trace-visible and does not enable formal writes.
- Trace refs and validation refs remain separated.
- Unsafe metadata is rejected or sanitized.
- Focused tests cover happy path, candidate refs, handoff refs, confirmation, fail-closed refs, blocked HITL cases, low confidence, metadata safety and no forbidden wiring.

禁止：

- calling LLM or provider.
- rendering prompts.
- reading or writing DB.
- calling repositories.
- writing formal assets, feedback, progress, scores, reports or training plans.
- wiring `interview_orchestrator_agent` into API, ai_runtime, polish, domain or infrastructure.
- modifying provider, prompt, API, DB, frontend, domain policy, application polish behavior, eval datasets, eval graders, eval suites, eval reports, scripts or workflow files.
- claiming L5 release, real-provider quality certification, remote CI success, Phase 12 release gate completion or formal write completion.

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

## P11-W4 Controlled Tool Loop / HITL Gate

适用于 `P11-W4-CONTROLLED-TOOL-LOOP-HITL`。

Status:

- `runtime_bounds_hitl_slice_complete_with_deferred_release_gate` is allowed only for controlled runtime-boundary hardening.
- This status is not L5 release, not real-provider quality certification, not remote CI success and not Phase 12 release gate completion.

必须满足：

- `AgentRuntimeLoopPolicy` 明确 `max_steps`、`max_retries`、`timeout_seconds`、`stop_conditions`、`repair_strategy` 和 `fallback_semantics`。
- Facade / adapter command metadata must carry the validated runtime loop policy.
- Runtime-reported max step, retry and timeout exhaustion must fail closed when reported as success.
- Bound exhaustion may be accepted only as non-success with matching stop condition or failure reason.
- HITL trigger validation covers `formal_write_requested`, `asset_conflict`, `low_confidence`, `ambiguous_ownership` and `validation_failed_partial_result`。
- `hitl_required=true` cannot be reported as success.
- Validation failed, provider unavailable and fallback markers cannot be reported as generated success or formal write success.
- Runtime tool-call metadata must be scoped to allowed tool refs and must not expose repository, DB, SQLAlchemy session, unit-of-work or formal writer handles.
- Candidate-only and formal-write handoff boundaries remain enforced.
- Focused tests cover loop-bound exhaustion, HITL interrupt, resume owner/action validation, fallback generated-success rejection and forbidden direct tool/repository exposure.

禁止：

- unbounded autonomous swarm。
- Agent direct DB / repository write。
- Tool direct repository exposure。
- prompt/provider/API/DB/frontend/domain behavior changes。
- formal business writes outside Application Service -> Domain Policy -> Handoff。
- claiming L5 release, real-provider quality certification, remote CI success or Phase 12 release gate completion。

P11-W4 non-claims:

- P11-W4 hardens runtime bounds and HITL/tool permissions only.
- P11-W4 does not call real provider or change prompt/provider behavior.
- P11-W4 does not change DB schema, API contract, frontend or domain policy.
- P11-W4 does not authorize direct formal writes.
- P11-W4 does not close Phase 12 release gate or claim L5 release.

## P11-W5 Integration / Boundary Tests Backfill Gate

适用于 `P11-W5-L5-INTEGRATION-BOUNDARY-TESTS-BACKFILL`。

Status:

- `validated_with_deferred_gaps` is allowed for `L5-002` through `L5-004` when integration/boundary tests and source backfill prove the scoped evidence.
- `validated` is allowed for `L5-005` controlled runtime-boundary hardening after Traceability Matrix and Risk Register backfill.
- No L5 capability may be marked `done` in this window.

必须满足：

- Supervisor / Orchestrator registration evidence exists and does not replace the C1 Question / Feedback catalog.
- Cross-agent handoff / state / trace contracts remain typed, refs-only and validated for required refs.
- At least one evidence-backed workflow includes three or more business agents and uses typed handoff refs.
- Controlled loop evidence covers `max_steps`, `max_retries`, `timeout`, `stop_conditions`, HITL and forbidden repository / DB / formal writer exposure boundaries.
- Candidate outputs remain candidate/suggestion only.
- Formal-write request blocks before candidate or handoff success unless a separately authorized Application Service -> Domain Policy -> Handoff path exists.
- HITL triggers remain explicit for asset conflict, formal write, low confidence, ambiguous ownership and validation-failed partial result.
- Project source backfill updates Matrix, Decision Log, Risk Register, Acceptance Gates and Phase Roadmap.
- Required validation commands are run or blockers recorded: `pytest tests/architecture`, `pytest tests/evals`, `pytest tests/api`.

禁止：

- provider behavior change。
- prompt rewrite。
- DB schema or migration。
- frontend/API contract change。
- Phase 12 eval runner, replay execution, CI binding, report generation, observability report or release decision implementation。
- L5 release, real-provider quality certification, remote CI success, formal F8/M8 release or Phase 12 release gate completion claim。
- marking pre-split `L5-006`, `L5-006A` or `L5-006B` implemented, validated or done without the required scoped evidence。

P11-W5 non-claims:

- P11-W5 backfills integration/boundary evidence only.
- P11-W5 does not implement Phase 12 release gate.
- P11-W5 does not certify real-provider quality or remote CI success.
- P11-W5 does not authorize direct formal writes.
- P11-W5 does not mark any L5 capability `done`.

## Phase 12 Release Gate

适用于 Phase 12 L5 Eval, Hardening, and Release Gate。

Option D split:

- `L5-006A` is the local multi-agent eval / replay / failure hardening track.
- `L5-006B` is the production release gate / remote CI hard claim / real-provider production certification / production observability / release decision track.
- USER_CONFIRMED Option D includes `L5-006A` and excludes `L5-006B`.
- A/B testing, traffic split, canary rollout, online experiment metrics and production rollout governance are out of scope for Option D.
- Production release readiness remains deferred until a separate release scope records visible remote CI artifact evidence, real-provider production certification, production observability/SLO, rollback evidence and human/controller release decision.

Option D Local Hardening Gate:

- Option D may only claim local complete multi-agent capability when default-off local product/runtime wiring, local replay, local trace, HITL, bounded-loop and failure hardening evidence all pass.
- `L5-006A` may not be marked `done` unless local code, tests/evals, old-duty removal, no forbidden scope, source backfill and every gap closure/deferred reason are proven.
- Local deterministic/fake-safe eval evidence is not real-provider production quality certification.
- Local pytest/eval success is not remote CI hard claim.

P12-W0 status:

- `release_gate_scope_locked_with_deferred_implementation` is allowed only for docs-only release-gate scope lock.
- This status is not L5 release, not remote CI success, not real-provider quality certification and not Phase 12 release gate completion.
- Pre-split `L5-006` remains not done; after D-W0, `L5-006A` and `L5-006B` must be evaluated separately.

P12-W1 Eval Contract Gate:

- `eval_contract_slice_complete_with_deferred_runner_ci_release` is allowed only for the contract-first eval slice: Phase 12 suite manifest, dataset skeletons, grader contract, release report schema and static contract tests.
- This status is contract evidence only. It is not executable eval evidence, not replay evidence, not CI evidence, not release report evidence, not real-provider quality certification and not Phase 12 release gate completion.
- `L5-006A` must not be marked validated or done from P12-W1 evidence alone; `L5-006B` remains deferred / out of scope.
- Contract artifacts must state that dataset skeletons are not eval pass evidence, grader contract is not grader implementation, report schema is not a generated report and local pytest is not remote CI success.
- P12-W2 or later must be separately scoped before runner behavior, replay execution, CI workflow binding, report generation, remote CI artifacts or release decision evidence can be implemented or claimed.

必须满足：

- multi-agent regression suite。
- suite manifest includes capability IDs, case IDs, input refs, expected candidate refs, expected handoff refs, expected validation refs, expected HITL refs, expected failure mode, expected non-claims, grader refs and minimum pass criteria。
- required eval cases cover happy path candidate product slice, insufficient context, asset conflict, formal write requested, low confidence, provider failure, validation failure, cross-agent handoff failure, replay mismatch, forbidden data, fake/replay non-claim and release non-claim。
- cross-agent replay fixtures。
- replay evidence proves `read_only=true`, `formal_write_blocked=true`, zero provider calls, zero repository / DB business writes, zero formal writes, trace comparison, candidate refs preserved, validation refs preserved and handoff refs preserved。
- failure-mode regression cases。
- local L5 eval gate with command list, blocking failure behavior and negative-control behavior for `L5-006A`。
- production L5 CI gate with workflow name, visible artifact evidence, artifact retention expectation and remote run link only for separately scoped `L5-006B`。
- default CI gate does not require live provider credentials。
- optional real-provider advisory mode is explicit, non-default and separately scoped。
- observability / trace report。
- trace report contains agent_id, run_id, plan refs, skill refs, tool refs, policy refs, candidate refs, handoff refs, validation refs, HITL refs, failure reason, fallback reason and forbidden-data scan result。
- rollback policy。
- failure triage policy。
- human/controller release decision with accepted risks, deferred gaps, rollback plan, version/tag ref, date/actor, evidence links and non-claims。

禁止：

- claiming L5 with unit tests only。
- claiming L5 with fake-only or replay-only eval。
- skipping replay / trace evidence。
- release with unresolved candidate/formal boundary gaps unless explicitly accepted by release controller。
- release with unresolved provider fail-open gaps。
- release without human/controller decision。
- claiming remote CI success without visible passing run and uploaded artifact。
- treating a workflow file as artifact evidence。
- treating local eval pass as remote CI pass。
- treating Option D local capability as production release readiness。
- requiring or claiming A/B testing inside Option D。
- storing forbidden payloads in reports。
- release without rollback plan。
- omitting negative-control evidence。
- weakening formal write boundary during release work。
- marking `L5-006A` done without local replay/trace/failure evidence。
- marking `L5-006B` implemented, validated or done inside Option D。

## Traceability Gate

必须满足：

- Capability ID 更新。
- Matrix 状态更新。
- Decision Log 更新。
- Risk Register 更新。
- Acceptance Gate 更新。
- Project source backfill。
- Gap closed 或 deferred。

## Done Gate

Capability 标记 done 必须同时满足：

- 设计更新。
- 代码迁移。
- 旧位置不再承载职责。
- 单测通过。
- 必要 eval 通过。
- 验证运行。
- 无 forbidden scope 修改。
- Project source 回填。
- 用户确认需要确认的关键决策。

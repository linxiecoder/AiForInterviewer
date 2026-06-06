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

Current Phase 7 evidence:

- Compact provider request boundary exists in `apps/api/app/application/llm/provider_boundary.py`.
- Question and Feedback active provider paths validate before `transport.generate()` and fail closed on forbidden-key / schema validation errors.
- Forbidden-key recursive rejection, schema top-level gate, redaction, no full prompt fallback, and provider validation failure are covered by focused tests recorded in `docs/goals/2026-06-05/P7_D_IMPLEMENTATION_REPORT.md` and audited in `docs/goals/2026-06-05/P7_E_AUDIT_REPORT.md`.
- P7-W2 增加 DTO-level `LlmTransportRequest` forbidden-key backstop，将 progress tree / job match / feedback trace request construction 迁入 `build_validated_transport_request()`，并增加 static architecture gate，禁止 `provider_boundary.py` 之外的 production direct request constructors。
- P7-W3 formalizes Controller Decision B for Feedback answer text handling: `current_answer.answer_text` is allowed only as bounded current-answer primary input, provider request includes auditable policy metadata, historical answer raw `answer_text` fallback is removed, and nested `full_answer` remains fail-closed.
- P7-W4.fix.01 full validation passed: full-repo pytest `1067 passed`, `npm run web:test` passed, `npm run web:smoke:auth` passed, focused temp / fake policy selector `21 passed`, and `git diff --check` passed.
- Status: `mitigated_for_phase_7`。当前 production provider request construction 已被 forbidden keys 与 per-task schema gates 覆盖；bounded answer excerpt semantics 已由 policy / tests 关闭；`P7-GAP-005` 已由 full validation 关闭。

## RISK-006 Fake 污染 runtime

Severity: medium

Description:

Fake LLM 或 fake transport 被 runtime provider 使用，导致测试成功掩盖真实 provider 行为。

Mitigation:

- Fake 下沉 tests/evals/replay。
- Runtime env 禁止 fake provider。
- import boundary scan。
- Fake output trace visible。

Current Phase 7 evidence:

- `FeedbackGenerationService(FakeLlmTransport())` now returns fake-visible non-success with `fake_transport_not_runtime_provider`, `provider_status=fake_transport`, and `llm_called=False`.
- Runtime fake rejection and fake fixture isolation are covered by focused tests recorded in `docs/goals/2026-06-05/P7_D_IMPLEMENTATION_REPORT.md` and audited in `docs/goals/2026-06-05/P7_E_AUDIT_REPORT.md`.
- Agent E audit found no production app code newly importing `FakeLlmTransport`; production grep hits were runtime rejection text and fake module boundaries.
- P7-W4.fix.01 removed the auth smoke dependency on runtime fake provider by changing the smoke env from `LLM_PROVIDER=fake` to blank while preserving runtime fake rejection.
- Full validation evidence: `npm run web:smoke:auth` passed; focused runtime fake rejection tests passed; grep shows no auth smoke script `LLM_PROVIDER.*fake` hit.
- Status: `mitigated_for_phase_7`. Phase 9 CI eval gates remain separate Phase 9 work and are not marked done.

## RISK-P7-FALSE-SUCCESS

Severity: high

Description:

Provider / fake boundary work may be partially implemented while reports mark Phase 7 `done` without proving all active paths, grep interpretation, tests, audit, and source backfill.

Mitigation:

- Use claim ledger labels and read-only Audit / Diff review before source fact backfill.
- Treat child-agent output as evidence candidates until audited.
- Record `validated_with_deferred_gaps` when WARN gaps remain.
- Keep unsupported claims visible: non-global provider backstop, bounded answer excerpt, single-writer identity `UNKNOWN`, and unrun full-repo / web / e2e tests.

Status: `partially_mitigated`.

P7-W2 update:

- global provider static gate 与 DTO forbidden-key backstop 降低了 false-success risk，但 final project status 仍是 `validated_with_deferred_gaps`。
- Remaining non-claims: 不声明 answer excerpt leakage elimination；不声明 full-repo pytest / web / e2e 已通过；不声明 Phase 7 `done`。

P7-W3 update:

- Controller Decision B 将 bounded `current_answer.answer_text` 明确为 allowed current primary task input，并由 policy metadata 与 focused tests 验证。
- `P7-GAP-003` status: `closed_by_policy_and_tests`。
- Remaining non-claims: 不声明 full-repo pytest / web / e2e 已通过；不声明 Phase 7 `done`；不启动 Phase 8 / Phase 9。

P7-W4.fix.01 update:

- Controller Decision B for temp artifact policy is implemented: pytest-managed temp fixtures are allowed only when managed outside repo-root; repo-root scratch artifacts remain forbidden.
- Controller Decision A for auth smoke is implemented: auth smoke no longer sets `LLM_PROVIDER=fake`; runtime fake rejection remains intact.
- Full validation passed: full-repo pytest `1067 passed`, `npm run web:test` passed, `npm run web:smoke:auth` passed.
- `P7-GAP-005` status: `closed_by_full_validation`。
- Phase 7 status: `done`。
- Phase 8 status: `eligible_for_controller_decision`, not started。

## RISK-007 Eval 只覆盖 seed 样本

Severity: medium

Description:

Eval 只覆盖少量 seed 或 fake 行为，不能证明 AI 质量。

Mitigation:

- 每个 Capability ID 绑定 regression case。
- Eval gate 进入 CI。
- Phase 9 建立 graders / datasets / reports。

P9 update:

- `evals/suites/phase9.json` now binds Phase 9 dataset refs, grader refs, capability IDs, pass criteria, CI behavior and non-claims.
- `evals/datasets/phase9/*.jsonl` adds deterministic regression cases for canonical evidence/source support, Question Agent, Feedback Agent, provider boundary, fake gate, handoff/trace and runtime deferred-gap non-claims.
- `scripts/evals/run_eval_gate.py` produces JSON + Markdown reports, scans report output, exits non-zero on blocking failures and supports a negative-control proof fixture.
- `.github/workflows/eval-gate.yml` runs the replay gate and negative-control gate without live provider credentials.
- Remaining non-claim: replay/fixture/fake-visible evals are not real-provider quality evidence.

P12-W1 mitigation evidence:

- Executable L5 eval runner added: scripts/evals/run_l5_eval_suite.py.
- Phase 12 datasets added under tests/evals/phase12/datasets/.
- Phase 12 gate test added: tests/evals/test_phase12_l5_eval_gate.py.
- Deterministic run passed with blocking_failures=0, total_cases=9.
- Negative control produced expected failure.
- CI workflow binding exists for Phase 12 L5 gate, but visible remote CI artifact evidence remains a separate production-release claim.

Residual risk:

- Real-provider quality certification is not claimed.
- `L5-006A` local replay / resume / failure fixtures remain P12-W2.
- `L5-006A` local observability / trace report remains P12-W3.
- `L5-006B` production release readiness, remote CI hard claim, production observability/SLO, real-provider production certification and human production release decision remain deferred / out of scope for Option D.

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

## RISK-017 Project source 不回填导致目标漂移

Severity: high

Description:

关键决策只停留在聊天里，后续窗口按旧文档执行。

Mitigation:

- Phase 0.1 Source Backfill。
- 每个窗口 Done Criteria 要求 Backfill。
- Decision Log / Matrix / Risk Register 必须同步。

P12-W1 mitigation evidence:

- P12-W1 adds executable eval gate foundation, but does not claim L5 release.
- Pre-split L5-006 is now separated: `L5-006A` remains open for local replay / trace / failure hardening evidence, and `L5-006B` remains deferred for production CI/release evidence and human production release decision.

Residual risk:

- Do not treat executable eval foundation alone as L5 release.
- Do not treat fake-only / deterministic-only evidence as real-provider quality certification.

## RISK-018 P5/P6 planned workflow 被误读为 L5 完成

Severity: high

Description:

Phase 5 / Phase 6 的 C2 / C3 L2 planned guarded workflow 可能被误读为 autonomous Agent、Phase 11 / Phase 12 或 L5 release 完成。

Mitigation:

- `P5P6-W1-C2-C3-PLANNED-WORKFLOW-L5-FOUNDATION` 只记录为 L5 Foundation progress。
- Phase Roadmap Lock 明确 Phase 8 / Phase 9 / Phase 11 / Phase 12 仍 deferred。
- Final report 和 matrix 禁止使用 L5 done / autonomous done 表述。

P11-W4 mitigation evidence:

- P11-W4 accepted status is `runtime_bounds_hitl_slice_complete_with_deferred_release_gate`, limited to controlled runtime-boundary hardening.
- Controlled loop metadata covers `max_steps`, `max_retries`, `timeout_seconds`, `stop_conditions`, `repair_strategy` and `fallback_semantics`.
- Bound exhaustion, `hitl_required=true`, fallback/generated-success markers and forbidden repository/DB/tool exposure markers fail closed instead of being reported as success.
- HITL trigger metadata covers formal write, asset conflict, low confidence, ambiguous ownership and validation-failed partial result.

P11-W5 mitigation evidence:

- P11-W5 backfills integration/boundary tests and Project sources for `L5-002` through `L5-005`; this is evidence backfill, not Phase 12 release-gate work.
- `L5-005` may be recorded as `validated` for controlled runtime-boundary hardening after Matrix and Risk Register backfill, but it remains not `done` and does not certify release readiness.
- P11-W5 architecture tests cover three-business-agent candidate refs, typed handoff refs, trace / validation / handoff separation, asset-conflict block and formal-write block under the window validation scope.

Residual risk:

- `L5-005` is not `done`; evidence remains controlled runtime-boundary hardening plus integration/boundary tests, not L5 release.
- Pre-split `L5-006` remains release-blocking in this historical P11-W5 context; D-W0 splits current tracking into `L5-006A` local hardening and `L5-006B` deferred production release.
- Real-provider quality certification, remote CI success, formal write completion and Phase 12 release gate completion remain non-claims.

## RISK-019 legacy fallback 测试与 candidate-only 语义冲突

Severity: medium

Description:

P5P6-W1.fix.02 前，部分旧 API 测试仍期待 fake / default / graph-disabled question fallback 持久化正式题目，这与 Phase 5 candidate-only / fallback-not-success gate 冲突。

Mitigation:

- 本窗口不恢复旧 fallback formal write。
- `P5P6-W1.fix.02-VALIDATION-BLOCKER-REMEDIATION` 已将 `test_polish_question_and_feedback_context_include_canonical_assets` 对齐为 candidate-only / provider-unavailable-not-success 语义。
- 更新后的测试仍断言 canonical asset refs、source support level、validation refs、context digest、`question_candidate` 输出和 fallback-not-success metadata。
- Broad selector 当前为 `300 passed, 323 deselected`，不再有该 legacy business assertion failure。

## RISK-020 repo root temp-like 目录导致 pytest 命令非零退出

Severity: medium

Description:

P5P6-W1.fix.02 前，聚焦 pytest 用例主体报告通过，但测试结束阶段因 repo root 预存 `tmp` 目录触发 temp leak checker，命令以 exit code `1` 退出。

Mitigation:

- `P5P6-W1.fix.02-VALIDATION-BLOCKER-REMEDIATION` 确认 repo-root `tmp/` 仅包含 local goal / source-pack scratch material，不是测试即时产物。
- 已将该目录移出仓库到 `/tmp/aifi-repo-root-tmp-P5P6-W1.fix.02-20260605`，未修改或弱化 temp leak checker。
- 当前聚焦 pytest、eval pytest 和 broad selector 不再因 repo-root `tmp` 退出 `1`。

## RISK-021 Phase 9 eval CI gate 尚未建立

Severity: medium

Description:

P5/P6 scoped eval runners 可以本地运行，但仓库仍没有 Phase 9 CI regression gate，因此本地 eval 通过不能证明 AI 质量门禁已完成。

Mitigation:

- `EVAL-001` 不标记 done。
- Source backfill 只记录本地 P5/P6 scoped eval evidence。
- Phase 9 另行 scope lock CI gate、grader、dataset 和报告。

P9 update:

- Status: `mitigated_by_phase9_replay_gate`。
- Phase 9 CI integration now exists in `.github/workflows/eval-gate.yml`.
- Local Phase 9 replay gate evidence is recorded in `docs/goals/2026-06-06/P9_EVAL_REPORT.md` and `evals/reports/phase9_eval_report.json`: 30 total cases, 30 passed, 0 blocking failures and 2 explicit deferred cases.
- Negative-control gate evidence proves the gate detects a blocking job-gap completed-work claim failure.
- The risk is not closed as real-provider quality certification; replay/fake non-claims remain required.

## RISK-022 P8 C4 runtime foundation 被误读为 L5 完成

Severity: high

Status: open_mitigated_by_partial_backfill

Description:

Phase 8 C4 runtime foundation may be misread as full multi-agent product workflow, Phase 11 Supervisor / Orchestrator, Phase 12 L5 release gate, or formal F8/M8 MVP release.

Mitigation:

- `P8_W0_SCOPE_LOCK.md` records C4-only scope and explicitly forbids prompt/provider/API/DB/frontend/domain-policy changes, Phase 11, Phase 12 and L5 claims.
- P8 source backfill uses `partial_with_deferred_gaps` / `validated_with_deferred_gaps`, not `done`.
- P8 source backfill distinguishes AgentExecutor-bound handoff plan, `execute_agent_handoff()` target AgentExecutor start and target timeline ref visibility from product-level Supervisor / L5 orchestration.
- Final reports must list deferred gaps for raw asset body transfer and formal asset composition/write semantics, product-level Supervisor / L5 orchestration beyond the AgentExecutor-bound handoff plan / execution primitive and target timeline ref visibility, shared loop-policy and registry consumption by concrete graph tool calls outside the facade command boundary, remediated Polish question path and Feedback PR8 trace gate path, remaining product-level runtime/orchestration wiring and runner-bound HITL emission / resume validation outside the already covered facade/generic/Question/Feedback paths, DB persistence/API status taxonomy beyond the runtime DTO and Polish question application status mapping, `AgentTraceBridge` and adapter metadata event status guards, and full trace population for remaining product/future runtime events outside current generic runtime plus Feedback service-backed resume, Question/Feedback start/resume-event and target handoff timeline coverage.
- Validation evidence is allowed to prove the implemented foundation slice only; it does not prove L5 release or Supervisor / Orchestrator completion.

## RISK-023 Replay / fake eval evidence 被误读为真实 provider 质量证明

Severity: high

Status: open_mitigated_by_phase9_non_claims

Description:

Phase 9 replay / fixture / fake-visible evals can regress deterministic contracts, but they do not prove live provider output quality. If reports or source backfill omit this distinction, a local replay gate could be falsely treated as AI quality certification.

Mitigation:

- Phase 9 manifest and reports include non-claims: replay mode is not real-provider quality evidence; fake-visible eval is not production provider quality evidence; Phase 9 is L5 Foundation regression evidence only, not L5 release.
- `scripts/evals/run_eval_gate.py` records `mode`, `provider_evidence_type` and CI credential metadata in the JSON report.
- `.github/workflows/eval-gate.yml` uses default replay mode and does not require provider credentials.
- Future real-provider/advisory eval modes must be explicitly configured, skipped by default, and separately reported.

## RISK-024 deferred_remote_ci_gap 被误读为 remote CI 已通过

Severity: high

Status: open_deferred

Description:

Phase 9 has local validation and a GitHub Actions workflow file, but no visible passing GitHub Actions run/artifact is claimed in Phase 10. If `complete_with_deferred_remote_ci_gap` is shortened to `complete` or `done`, later windows may incorrectly assume remote CI passed.

Mitigation:

- Phase 10 source backfill records `deferred_remote_ci_gap` in closeout report, gap register, acceptance gate, decision log and roadmap lock.
- Remote CI may only be claimed when a passing GitHub Actions run and uploaded artifact are visible and cited.
- Local `tests/evals`, replay gate and negative-control results remain local behavior evidence only.

Closure condition:

- A later authorized CI verification window cites a passing GitHub Actions `Eval Gate` run and `phase9-eval-reports` artifact, or explicitly carries the gap forward again.

## RISK-025 stale committed eval report metadata short SHA f86adea

Severity: medium

Status: open_residual_metadata_risk

Description:

Committed Phase 9 eval reports embed short SHA `f86adea`, while Phase 10 accepted current implementation fact is `76c670c859d3f7d32d13e604b3d0edffeefd2048`. This can confuse report readers even though a non-mutating rerun proves current behavior.

Mitigation:

- Phase 10 records the mismatch as residual report-metadata risk, not behavior blocker.
- Non-mutating rerun to `/tmp/aifi-p10-closeout-eval-reports` produced current `76c670c` report evidence with `30 passed`, `0 blocking_failures`, `2 deferred`.
- Phase 10 does not rewrite `evals/reports/**` or committed P9 reports.

Closure condition:

- Either leave the risk documented, or run a separate authorized report refresh window that rewrites committed reports without changing runner, grader, suite, dataset or implementation behavior.

## RISK-026 eval report churn from committed report-dir reruns

Severity: medium

Status: open_mitigated_by_phase10_gate

Description:

Running the eval gate with a committed report directory can rewrite `evals/reports/**` or `docs/goals/2026-06-06/P9_EVAL_REPORT.md`, causing report churn and obscuring whether behavior changed.

Mitigation:

- Phase 10 validation uses `/tmp/aifi-p10-closeout-eval-reports`.
- Phase 10 acceptance gate requires non-mutating report dirs unless a separate report refresh window is authorized.
- Committed report rewrite remains forbidden in this closeout/source-backfill window.

Closure condition:

- Future report refresh work must be separately scoped, reviewed as report metadata refresh, and must not mix with runner/grader/suite or implementation behavior changes.

## RISK-027 Phase 0-10 foundation closeout 被误读为 L5 release

Severity: high

Status: open_mitigated_by_phase10_non_claims

Description:

Closing Phase 0-10 foundation could be misread as L5 release, formal F8/M8 release readiness, real-provider quality certification, or Phase 12 release gate completion.

Mitigation:

- Phase 10 closeout uses `closed_with_deferred_gaps` and explicitly states L5 Foundation only.
- Phase 10 roadmap lock keeps Phase 11 Supervisor / Orchestrator and Phase 12 L5 release not started.
- Acceptance gates and decision log explicitly forbid L5 release claims from Phase 10 evidence.

Closure condition:

- Only a future release-gate window with explicit release criteria, remote CI evidence, rollout/rollback evidence and user/controller approval can close this risk.

## RISK-028 Phase 8 runtime gap false-closure

Severity: high

Status: open_deferred

Description:

Phase 8 runtime foundation has extensive validation evidence, but still carries deferred runtime gaps. A Phase 10 source-backfill closeout could accidentally normalize those gaps into done if it focuses only on foundation closure.

Mitigation:

- Phase 10 records Phase 8 runtime gaps as deferred in closeout report, gap register, acceptance gate, decision log and roadmap lock.
- P8 source status remains `validated_with_deferred_gaps` / `partial_with_deferred_gaps`.
- Phase 11 entry conditions require remaining gaps to be explicitly carried or resolved under a new scope lock.

Closure condition:

- A scoped Phase 8 follow-up or Phase 11 runtime/orchestration window implements or verifies the specific runtime gaps with tests, source backfill and no false L5 release claim.

## RISK-029 fake Supervisor / Orchestrator

Severity: high

Status: open

Description:

Phase 11 could create a named Supervisor / Orchestrator that only calls existing services serially without typed goal decomposition, plan, handoff, state, trace, bounded tool loop or HITL semantics.

Mitigation:

- Phase 11 Scope Gate requires registered definition, typed cross-agent contracts, trace timeline and tests.
- Decision options remain proposed until controller/user confirms next-window scope.
- Matrix keeps `L5-002` as `not_started` in P11-W0.

Closure condition:

- Phase 11 implementation evidence proves orchestration behavior and negative tests reject fake/shell orchestration.

## RISK-030 contract-only L5 false claim

Severity: high

Status: open

Description:

P11-W0 or a contract-first Phase 11 window could be misread as L5 implementation or release because target contracts are documented.

Mitigation:

- P11-W0 records source status as scope lock / design only.
- `L5-002` to `L5-006` cannot be marked implemented, validated or done in P11-W0.
- P11-W1 may only claim `contract_slice_complete_with_deferred_runtime_gaps`; its Orchestrator definition, contracts, skills and tools are contract-only and architecture-gated for no runtime wiring.
- Phase 12 release gate remains not started.

Closure condition:

- Later implementation and release windows provide code, tests, eval/replay, CI artifact and human/controller decision evidence.

## RISK-031 serial service calls disguised as MultiAgent

Severity: high

Status: open

Description:

A product vertical slice could chain existing Question / Feedback / asset logic without true cross-agent plan, handoff, state, checkpoint/replay and trace semantics.

Mitigation:

- Phase 11 requires typed cross-agent plan/handoff/state/trace contracts.
- At least one workflow must involve three or more business agents and keep candidate/formal boundaries.
- Trace timeline must show cross-agent refs, not only sequential service calls.
- P11-W3 adds a deterministic candidate-only slice with three business agents and typed handoff refs, but keeps formal write and release gates deferred.

Closure condition:

- End-to-end tests and trace evidence prove multi-agent orchestration semantics.

## RISK-032 replay/fake eval mistaken for provider quality

Severity: high

Status: open

Description:

Phase 9 replay/fake-visible evidence can be mistaken for real-provider quality certification or Phase 12 release evidence.

Mitigation:

- P11-W0 carries real-provider quality certification non-claim.
- Phase 12 Release Gate forbids L5 release with fake-only or replay-only eval.
- Any real-provider quality evidence must be separately scoped.

Closure condition:

- Separate real-provider/advisory eval window or release gate records provider evidence, redaction, human review and non-fake certification.

## RISK-033 Phase 8 gaps normalized by wording

Severity: high

Status: open

Description:

Phase 8 foundation evidence is extensive and could be shortened into done wording, hiding deferred runtime gaps needed by Phase 11.

Mitigation:

- Gap reconciliation table carries raw asset body, formal asset write, future tool-loop, product wiring, HITL, DB/API taxonomy and trace gaps.
- Phase 11 Scope Gate requires per-gap treatment.
- Phase 0-10 remains `closed_with_deferred_gaps`.

Closure condition:

- Each runtime gap is implemented/verified or explicitly accepted as deferred in a later authorized window.

## RISK-034 missing cross-agent state durability

Severity: high

Status: open

Description:

Supervisor / Orchestrator could coordinate transient calls without durable checkpoint/replay semantics, making cross-agent recovery and audit unreliable.

Mitigation:

- Phase 11 target requires cross-agent state / checkpoint / replay contract.
- State is control state, not business fact persistence.
- Replay must remain read-only and formal-write-blocked unless separately authorized.
- P11-W2 adds focused runtime-hardening validation for cross-agent resume `checkpoint_ref` / `base_version` / `idempotency_key` / owner / interrupt / action and read-only / formal-write-blocked replay metadata, without persisting cross-agent state.

Closure condition:

- Phase 11 product/runtime tests prove checkpoint/base/idempotency validation and replay trace behavior for cross-agent state in the selected product workflow.

## RISK-035 missing HITL for formal write / asset conflict

Severity: high

Status: open

Description:

L5 workflow could bypass user confirmation or HITL when asset conflict, formal write, low confidence, ambiguous ownership or validation-failed partial result occurs.

Mitigation:

- Phase 11 requires these HITL triggers.
- Formal writes remain Application Service -> Domain Policy -> Handoff.
- Asset update candidates require user confirmation.
- P11-W2 adds focused HITL trigger validation for `formal_write_requested`, `asset_conflict`, `low_confidence`, `ambiguous_ownership` and `validation_failed_partial_result`, including non-success semantics for formal write / asset conflict and success-like failure rejection.
- P11-W3 keeps asset update candidates `formal_write_blocked`, requires user confirmation and blocks the minimal product slice on asset conflict or formal write request.

Closure condition:

- HITL trigger and resume tests cover all required cases in the selected product workflow.

## RISK-036 Phase 12 release gate skipped

Severity: high

Status: open

Description:

After Phase 11 implementation, a team could claim L5 release without multi-agent eval/replay, remote CI artifact, observability report, rollback policy or human/controller decision.

Mitigation:

- Phase 12 is explicit and not started.
- Phase 12 Release Gate forbids unit-test-only, fake-only or replay-only release claims.
- Remote CI artifact evidence and human release decision are required.

Closure condition:

- Phase 12 completes with release evidence and controller/user approval.

## RISK-037 P11-W1 contract Orchestrator 被误读为 runtime Orchestrator

Severity: high

Status: open

Description:

P11-W1 adds a real contract-only `interview_orchestrator_agent`, cross-agent contracts and L5 contract catalog builder. Without explicit wording, later readers could treat that as product multi-agent workflow, Supervisor / Orchestrator runtime execution, Phase 8 runtime gap closure or L5 release evidence.

Mitigation:

- P11-W1 source backfill and reports use `contract_slice_complete_with_deferred_runtime_gaps`.
- Architecture gates assert `interview_orchestrator_agent` is absent from runtime, handoff, ai_runtime, polish, API, domain and infrastructure Python paths.
- L5 catalog builder is separate from the Phase 4 C1 builder and only validates contract references.
- P11-W1 non-claims are repeated in implementation and source-backfill records.

Closure condition:

- A later Phase 11 product/runtime window explicitly wires and verifies Supervisor / Orchestrator behavior with focused runtime, HITL, trace, replay and source-backfill evidence, or the release controller explicitly accepts the remaining runtime gaps.

P11-W1 non-claims:

- P11-W1 does not implement product multi-agent workflow.
- P11-W1 does not execute Supervisor / Orchestrator at runtime.
- P11-W1 does not close Phase 8 runtime gaps.
- P11-W1 does not close `deferred_remote_ci_gap`.
- P11-W1 does not rewrite stale eval reports.
- P11-W1 does not certify real-provider quality.
- P11-W1 does not claim L5 release.
- P11-W1 does not implement Phase 12 release gate.

## RISK-038 P11-W2 runtime hardening 被误读为 product workflow

Severity: high

Status: open

Description:

P11-W2 adds real runtime-facing validation helpers and stricter handoff guards. Without explicit wording, later readers could treat this as Orchestrator runtime execution, product multi-agent workflow, full Phase 8 runtime gap closure or L5 release evidence.

Mitigation:

- Matrix status is `runtime_hardening_slice_complete_with_deferred_product_workflow`.
- P11-W2 source backfill repeats that product workflow, Orchestrator runtime execution, remote CI, stale eval report rewrite, real-provider quality certification, L5 release and Phase 12 release gate remain out of scope.
- Architecture gate still verifies `interview_orchestrator_agent` is absent from runtime, handoff, ai_runtime, polish, API, domain and infrastructure Python paths.

Closure condition:

- A later Phase 11 product workflow window explicitly wires and verifies Supervisor / Orchestrator behavior with three or more business agents, focused runtime/HITL/trace/replay evidence and source backfill, or the controller explicitly accepts remaining workflow gaps.

P11-W2 non-claims:

- P11-W2 does not implement product multi-agent workflow.
- P11-W2 does not execute `interview_orchestrator_agent` as a runtime agent.
- P11-W2 does not close all Phase 8 runtime gaps.
- P11-W2 does not close `deferred_remote_ci_gap`.
- P11-W2 does not rewrite stale eval reports.
- P11-W2 does not certify real-provider quality.
- P11-W2 does not claim L5 release.
- P11-W2 does not implement Phase 12 release gate.

## RISK-039 P11-W3 candidate slice 被误读为 formal product completion

Severity: high

Status: open

Description:

P11-W3 adds a real product-facing candidate workflow with three business agents. Without explicit wording, later readers could treat this as formal asset / feedback / training-plan write completion, real-provider quality certification, remote CI success, Phase 12 release gate completion or L5 release.

Mitigation:

- Matrix status is `candidate_product_slice_complete_with_deferred_formal_write_and_release_gate`.
- Source backfill repeats that P11-W3 is candidate-only, refs-only and formal-write-blocked.
- L5-006 remains `not_started`.
- Validation keeps provider, prompt, API, DB, frontend, domain policy, eval dataset, grader, suite, report, script and workflow files out of scope.

Closure condition:

- A later authorized window implements and validates formal write handoff and Phase 12 eval/replay/release evidence, or the controller explicitly accepts remaining formal-write/release gaps.

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

## RISK-040 Phase 12 release overclaim

Severity: critical

Status: open

Description:

P12-W0 scope lock or a later partial Phase 12 slice could be shortened into a release claim before eval, replay, CI artifact, observability, rollback and human decision evidence exist.

Mitigation:

- P12-W0 status is `release_gate_scope_locked_with_deferred_implementation`.
- `L5-006` remains not implemented, not validated and not done.
- Phase 12 Release Gate requires eval, replay, CI artifact, observability and release decision evidence before release wording.

Closure condition:

- Controller/user accepts a release decision package with all required Phase 12 evidence links.

## RISK-041 fake/replay eval mistaken as real-provider quality

Severity: high

Status: open

Description:

Phase 9 fake/replay evidence and future Phase 12 replay fixtures can prove deterministic regression behavior, but they can be mistaken for real-provider quality certification.

Mitigation:

- Fake-only and replay-only evidence must carry non-claims.
- Optional real-provider advisory mode must be explicit, non-default and separately scoped.
- Real-provider quality needs provider config, redaction, human review and non-fake results.

Closure condition:

- A separately authorized real-provider evidence window records the required provider evidence, or release decision explicitly keeps this as a non-claim.

## RISK-042 CI workflow existence mistaken as passing artifact evidence

Severity: high

Status: open

Description:

A workflow file can exist without a visible passing run or uploaded artifact. Treating workflow presence as remote CI success would close the release gate by wording only.

Mitigation:

- Remote CI success may only be claimed with a visible passing run and uploaded artifact.
- P12 evidence contract requires workflow name, command list, artifact name, retention expectation and artifact link.

Closure condition:

- A Phase 12 or successor CI verification window cites visible passing CI run and artifact evidence.

## RISK-043 local eval pass mistaken as remote CI pass

Severity: high

Status: open

Description:

Local eval, replay or pytest success can be useful regression evidence but does not prove remote CI behavior.

Mitigation:

- Local command output and remote CI artifact evidence are separate evidence categories.
- Release decision must list local evidence and remote artifact evidence separately.

Closure condition:

- Remote CI artifact evidence is cited or the release decision explicitly carries remote CI as deferred.

## RISK-044 trace report stores forbidden payloads

Severity: high

Status: open

Description:

Phase 12 observability reports could accidentally store raw prompt, provider payload, full resume, full JD, full answer, full asset body or secrets.

Mitigation:

- Observability contract requires refs-only report schema and forbidden-data scan result.
- Forbidden keys include raw prompt, provider payload, full resume, full JD, full answer, full asset body, token, secret, cookie and API key.

Closure condition:

- Phase 12 trace report generation includes a passing forbidden-data scan.

## RISK-045 release without rollback plan

Severity: high

Status: open

Description:

Release could be approved from eval/CI evidence without a rollback trigger, owner and procedure.

Mitigation:

- Release decision evidence requires rollback plan.
- Phase 12 gate blocks release decision when rollback plan is missing.

Closure condition:

- Controller/user accepts a rollback plan linked from the release decision package.

## RISK-046 release without human decision

Severity: critical

Status: open

Description:

Automated eval/replay/CI evidence could be misread as automatic release approval.

Mitigation:

- Human/controller release decision is a required evidence category.
- No release claim is valid from automation alone.

Closure condition:

- Human/controller decision is recorded with date, actor, accepted risks, deferred gaps and evidence links.

## RISK-047 formal write boundary weakened during release

Severity: critical

Status: open

Description:

Release pressure could weaken candidate-only and formal-write handoff boundaries, allowing Agents or Tools to write formal business facts directly.

Mitigation:

- Formal writes remain Application Service -> Domain Policy -> Handoff.
- Phase 12 gate forbids formal write claims unless a separately scoped window implements and validates the handoff path.
- P12-W0 modifies no provider, prompt, API, DB, frontend, runtime or domain policy behavior.

Closure condition:

- Formal write remains blocked, or a later authorized formal-write window provides implementation and validation evidence.

## RISK-048 negative-control omitted

Severity: high

Status: open

Description:

An eval gate that only passes positive cases may not prove that blocking failures actually fail the gate.

Mitigation:

- Phase 12 evidence contract requires negative-control behavior.
- CI evidence must show that expected negative-control failure is observed.

Closure condition:

- Phase 12 report includes negative-control evidence and blocking failure behavior.

## RISK-049 multi-agent eval coverage too narrow

Severity: high

Status: open

Description:

Phase 12 eval could cover only the happy path and miss insufficient context, asset conflict, formal write request, low confidence, provider failure, validation failure, handoff failure, replay mismatch, forbidden data and release non-claim cases.

Mitigation:

- P12 evidence contract lists required case categories.
- Suite manifest must map capability IDs to case IDs and minimum pass criteria.

Closure condition:

- Phase 12 suite manifest and report show required case coverage or explicit Controller-accepted deferred gaps.

## RISK-050 P12-W1 contract-only eval mistaken for executable gate

Severity: critical

Status: open

Description:

P12-W1 creates Phase 12 eval contract artifacts and static tests only. If `eval_contract_slice_complete_with_deferred_runner_ci_release` is shortened into executable eval gate evidence, Phase 12 could be treated as closed before runner, replay, CI, report and release decision evidence exist.

Mitigation:

- P12-W1 status includes `deferred_runner_ci_release`.
- Suite manifest states `contract_only_not_executable_release_gate`.
- Acceptance Gate requires P12-W2 or later for runner, replay, CI, report generation and release decision evidence.

Closure condition:

- A later scoped Phase 12 window implements and validates executable eval/replay/CI/report behavior, or release decision explicitly carries the gap as deferred.

## RISK-051 dataset skeleton mistaken for eval pass

Severity: high

Status: open

Description:

Phase 12 JSONL files created in P12-W1 are refs-only skeletons. They can define required cases but do not prove case execution or pass/fail behavior.

Mitigation:

- Dataset cases set `deferred_if_not_executable=true`.
- Suite manifest labels dataset refs as `dataset_skeleton_not_eval_pass`.
- Static tests validate shape and case coverage only.

Closure condition:

- Executable Phase 12 runner or successor evaluation records case results, blocking failures, deferred cases and negative-control behavior.

## RISK-052 report schema mistaken for generated report artifact

Severity: high

Status: open

Description:

`evals/schemas/phase12_release_report_schema.json` can be misread as an actual Phase 12 release report or release decision artifact.

Mitigation:

- Report schema labels itself `schema_contract_only_no_report_generation`.
- P12-W1 does not write `evals/reports/**`.
- Source backfill keeps release report generation deferred.

Closure condition:

- A later authorized report-generation window writes report artifacts with forbidden-data scans, artifact refs, rollback policy refs and explicit non-claims.

## RISK-053 grader contract mistaken for grader implementation

Severity: high

Status: open

Description:

`evals/graders/phase12_contract.json` defines assertion types and required fields, but it is not Python grader behavior and is not imported by the runner in P12-W1.

Mitigation:

- Grader contract labels itself `data_contract_only_not_python_grader`.
- P12-W1 does not modify `evals/graders/code_rules.py` or runner files.
- Static tests assert grader implementation and runner integration remain deferred.

Closure condition:

- A later scoped implementation window creates or updates deterministic grader behavior and validates it without weakening existing Phase 9 gates.

## RISK-054 L5-006 overclaim from P12-W1 source backfill

Severity: critical

Status: open

Description:

Updating the older unsplit `L5-006` from `not_started` to a P12-W1 or Option D status could be misread as local hardening complete, production release-ready, validated or done.

Mitigation:

- Matrix now splits `L5-006` into `L5-006A` local hardening and `L5-006B` production release.
- `L5-006A` status is `partial_local_eval_foundation_with_deferred_replay_failure_trace_gaps`, not done.
- `L5-006B` status is `deferred_out_of_scope_for_option_d`.
- P12-W1 and D-W0 reports repeat that replay/resume/failure fixtures, trace report, real-provider quality certification, remote CI success, production observability/SLO and release decision remain deferred where applicable.

Closure condition:

- `L5-006A` can move beyond partial local hardening only after a separately scoped Option D window provides local replay/trace/failure evidence and source backfill without forbidden-scope changes.
- `L5-006B` can move beyond deferred only after a separately scoped production release window provides visible remote CI artifact evidence, real-provider production certification, production observability/SLO, rollback evidence and human/controller release decision.

## RISK-055 Phase 9 report rewrite during Phase 12 contract work

Severity: high

Status: open

Description:

Phase 12 contract work could accidentally rewrite existing Phase 9 reports or suite assets, hiding stale report metadata or mixing Phase 9 replay evidence with Phase 12 release evidence.

Mitigation:

- P12-W1 forbids `evals/reports/**`, `evals/suites/phase9.json`, `evals/datasets/phase9/**` and `evals/graders/code_rules.py` changes.
- Static tests inspect git status for Phase 9 and report path changes.
- Validation requires `git diff --name-only` and contextual report-path grep interpretation.

Closure condition:

- Future report refresh or Phase 9 remediation is separately scoped and does not use Phase 12 contract work as implicit authorization.

## RISK-056 P11-W5 validated evidence mistaken for L5 release

Severity: high

Status: open

Description:

P11-W5 backfills integration and boundary tests for `L5-002` through `L5-005`. The resulting `validated` / `validated_with_deferred_gaps` wording can be misread as L5 release readiness, Phase 12 release gate completion or `L5-006` closure.

Mitigation:

- Matrix splits `L5-006A` local hardening from deferred `L5-006B` production release and does not mark any L5 capability `done`.
- P11-W5 Decision Log, Acceptance Gate and Phase Roadmap repeat that this window does not implement eval runner, replay execution, CI binding, observability report, release report generation or human/controller release decision.
- P11-W5 validation is local `pytest tests/architecture`, `pytest tests/evals` and `pytest tests/api`; it is not remote CI artifact evidence and not real-provider quality certification.

Closure condition:

- Phase 12 separately provides executable eval/replay/CI/report/human-decision evidence and controller/user accepts a release decision package.

## RISK-057 Option D local capability mistaken for production release

Severity: critical

Status: open

Description:

USER_CONFIRMED Option D is Local Complete Multi-Agent Capability. It combines default-off local product/runtime wiring with local replay/trace/HITL/bounded-loop/failure hardening. If this is shortened to "L5 release" or treated as production rollout readiness, the project could falsely claim production release, A/B readiness, remote CI success or real-provider production certification.

Mitigation:

- DEC-L5-015 records Option D as a local capability target, not a production release target.
- Matrix splits `L5-006A` local hardening from `L5-006B` production release.
- Acceptance Gates state that A/B testing, traffic split, canary rollout, online experiment metrics, production observability/SLO, remote CI hard claim and real-provider production certification are out of scope for Option D.
- Canonical goal path is `docs/03-delivery/refactor-multiagent-langgraph-implementation/option_d_local_complete_multi_agent_goal.md`.

Closure condition:

- Option D closeout uses local capability wording only, leaves `L5-006B` deferred, and records any production release decision in a separately authorized release scope.

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

## RISK-018 P5/P6 planned workflow 被误读为 L5 完成

Severity: high

Description:

Phase 5 / Phase 6 的 C2 / C3 L2 planned guarded workflow 可能被误读为 autonomous Agent、Phase 11 / Phase 12 或 L5 release 完成。

Mitigation:

- `P5P6-W1-C2-C3-PLANNED-WORKFLOW-L5-FOUNDATION` 只记录为 L5 Foundation progress。
- Phase Roadmap Lock 明确 Phase 8 / Phase 9 / Phase 11 / Phase 12 仍 deferred。
- Final report 和 matrix 禁止使用 L5 done / autonomous done 表述。

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

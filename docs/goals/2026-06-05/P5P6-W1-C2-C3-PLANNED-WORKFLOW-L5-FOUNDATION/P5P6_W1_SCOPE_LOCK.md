---
title: P5P6_W1_SCOPE_LOCK
type: scope-lock
status: evidence-only
owner: P5P6-W1-C2-C3-PLANNED-WORKFLOW-L5-FOUNDATION
permalink: ai-for-interviewer/docs/goals/2026-06-05/p5p6-w1-c2-c3-planned-workflow-l5-foundation/scope-lock
---

# P5P6-W1 Scope Lock

本文件记录 `P5P6-W1-C2-C3-PLANNED-WORKFLOW-L5-FOUNDATION` 的 Controller Scope Lock。它只授权 Phase 5 Question Agent 与 Phase 6 Feedback Agent 的 C2/C3 L2 planned guarded workflow 窗口，不授权 Phase 11 / Phase 12、Supervisor / Orchestrator 或 L5 release gate 实现。

## 1. Scope Lock

```text
task_id: N/A - 本窗口使用 Project source capability IDs，不新建 AIFI-* 任务入口
window_id: P5P6-W1-C2-C3-PLANNED-WORKFLOW-L5-FOUNDATION
capability_ids: QAG-004, QAG-006, QAG-007, AGT-006, AGT-007, FAG-005, FAG-007, FAG-008, EVAL-001, WIN-001, SRC-001, L5-001
files: 见第 5 节 allowed files；如需范围外写入立即停止
figma_nodes: N/A
allowed_ops: EDIT_LISTED_FILES
forbidden_ops: prompt rewrite, provider behavior refactor, DB schema change, API contract change, Phase7/8/11/12 implementation, direct formal business fact write by agent, repository exposure by tool, L5/autonomous done claim
final_artifact: code/tests/eval/source backfill/final report for P5/P6 C2/C3 L2 planned guarded workflow
done_condition: 第 11 节全部满足，且验证和 forbidden-scope audit 通过
```

## 2. Sequencing Lock

| Step | Owner | Operation | Status |
| --- | --- | --- | --- |
| 1 | Platform / Question / Feedback / Policy+Context / Test+Eval Recon Agents | parallel read-only recon | done |
| 2 | Controller Agent | merge recon and write this Scope Lock | done |
| 3 | Single Writer Agent | Phase5 Question planned workflow patch | pending |
| 4 | Single Writer Agent | Phase5 focused validation | pending |
| 5 | Single Writer Agent | Phase6 Feedback planned workflow patch | pending |
| 6 | Single Writer Agent | integrated validation | pending |
| 7 | Single Writer Agent | source backfill | pending |
| 8 | Audit/Diff Agent | forbidden scope, test/eval, backfill, L5 lock audit | pending |

Question 和 Feedback 不得并行写 shared Agent Platform 文件。所有 implementation patch 由单一 writer 顺序执行。

## 3. Recon Summary

| Source category | Current fact | Target / gap |
| --- | --- | --- |
| Project source | Phase 5 / Phase 6 是 Question / Feedback planned workflow，短期成熟度是 L2 planned guarded workflow。 | 本窗口只能登记 C2/C3 L2 progress，不得宣称 L5 done。 |
| L5 lock | Refreshed goal 明确 Phase 11 / Phase 12 才是 L5 controlled multi-agent system completion path。 | 本窗口不得实现 Supervisor / Orchestrator / L5 release gate。 |
| Agent Platform | C1 `AgentDefinition` / `SkillDefinition` / `ToolDefinition` / trace / handoff / registry 存在，支持 candidate-only contract。 | `apps/api/app/application/agents/eval/**` 不存在；eval CI gate 不得标 done。 |
| Phase2/3 prerequisite | `CanonicalEvidencePack` / `SourceSupportSummary` 兼容 bridge 可用；domain policies 已存在并由 application adapter 使用。 | `apps/api/app/application/polish/context/**` 不存在，完整 Interview Context 统一入口 deferred。 |
| Question | 图路径已有 candidate/handoff；service path 有 source support / grounding / fallback metadata。 | `apps/api/app/application/polish/agents/question/**` 不存在；direct fallback 仍会正式写题；fallback 可被写成 generated success。 |
| Feedback | service/schema/rules 已有 asset consistency、answer coverage、answer change、next action、asset update candidate confirmation。 | `apps/api/app/application/polish/agents/feedback/**` 不存在；成功路径尚未通过 feedback/asset_update candidate handoff refs。 |
| Tests/evals | Focused API / architecture tests 和 eval runners 存在。 | 缺 P5/P6 scoped regression descriptor；Phase9 eval CI gate deferred。 |

## 4. Prerequisite Gate

| Gate | Decision | Evidence interpretation |
| --- | --- | --- |
| Phase2 CanonicalEvidencePack / SourceSupportSummary usable | pass_with_bridge_gap | `SourceSupportSummary` has level / evidence refs / reason codes / confidence; full `context/**` absent remains deferred. |
| Phase3 Question / Feedback domain policies present | pass | Source support, grounding, follow-up coverage, asset consistency, answer coverage, answer change, and next action policies exist. |
| Phase4 AgentDefinition / SkillRegistry / ToolRegistry / Trace / Handoff present | pass_with_eval_gap | C1 catalog and registries exist; `agents/eval/**` runtime package absent, eval gate deferred. |
| Stop condition triggered before patch | no | No prerequisite requires prompt/provider/API/DB/Phase8/11/12 work. |

## 5. Allowed Files

Implementation and tests may modify only these current-window paths:

- `apps/api/app/application/polish/agents/question/**`
- `apps/api/app/application/polish/agents/feedback/**`
- `apps/api/app/application/polish/question_application_service.py`
- `apps/api/app/application/polish/question_generation_service.py`
- `apps/api/app/application/polish/feedback_application_service.py`
- `apps/api/app/application/polish/feedback_generation_service.py`
- `apps/api/app/application/polish/use_cases.py`
- `apps/api/app/application/agents/contracts/**`
- `apps/api/app/application/agents/definitions/**`
- `apps/api/app/application/agents/registry/**`
- `apps/api/app/application/agents/runtime/**`
- `apps/api/app/application/agents/handoff/**`
- `tests/api/**`
- `tests/architecture/**`
- `tests/evals/**`
- `evals/**`
- `docs/goals/2026-06-05/**`
- `docs/project-sources/09_REFACTOR_TRACEABILITY_MATRIX.md`
- `docs/project-sources/12_ACCEPTANCE_GATES.md`
- `docs/project-sources/13_DECISION_LOG.md`
- `docs/project-sources/14_RISK_REGISTER.md`
- `docs/project-sources/17_PHASE_ROADMAP_LOCK.md`

Shared Agent Platform files may be changed only if the change is backward-compatible, generic, and required for both C2/C3 use. Domain policy files are read-only unless a small adapter/import fix is proven necessary; current recon does not require domain policy writes.

## 6. Forbidden Files

No writes are allowed to:

- `apps/api/app/application/polish/question_generation_prompts.py`
- `apps/api/app/application/polish/feedback_prompt_assets.py`
- `apps/api/app/infrastructure/llm/**`
- `apps/api/app/infrastructure/db/**`
- `apps/api/app/api/v1/**`
- database migrations
- provider SDK / transport wiring
- production runtime environment provider selection
- `.github/workflows/**`
- `pyproject.toml`
- archive files

If any implementation requires these files, stop and produce a blocker report instead of patching.

## 7. Forbidden Behavior

- No prompt rewrite.
- No provider request behavior refactor.
- No DB schema change.
- No public API contract change.
- No Phase7 CompactProviderRequestBuilder implementation.
- No Phase8 runtime migration.
- No Phase11 Supervisor / Orchestrator implementation.
- No Phase12 L5 release gate implementation.
- No agent direct formal write.
- No tool direct repository exposure.
- No asset update formal write without user confirmation.
- No fallback / provider unavailable / validation failed reported as generated success.
- No claim that Question / Feedback are autonomous or L5.

## 8. Required Patch Shape

| Phase | Required direction |
| --- | --- |
| Phase5 | Ensure Question planned workflow produces `question_candidate` before formal write, keeps source support / grounding / follow-up / fallback semantics traceable, and prevents fallback/generated-success ambiguity. |
| Phase5 validation | Add or update focused Question tests before Phase6 implementation. |
| Phase6 | Add thin Feedback planned workflow wrapper/candidate refs using existing generation service and domain-policy bridge; preserve existing Application Service formal feedback write path while exposing `feedback_candidate` / `asset_update_candidate` handoff evidence. |
| Integrated validation | Run focused API / architecture / eval commands selected by Test/Eval recon. |
| Source backfill | Update only factual completion evidence and deferred gaps; keep Phase5/6 as C2/C3 L2 planned guarded workflow and L5 Foundation progress only. |
| Audit report | Record changed files, validation results, forbidden-scope audit, L5 scope lock result, and remaining gaps. |

## 9. Validation Plan

Focused commands to run after implementation:

```bash
PYTHONPATH=.:apps/api python -m pytest -q tests/api/test_polish_question_refactor_phase1.py -k "source_support_policy_classifies or phase1_question_service_keeps_job_gap_probe or next_question_agent_direct_project_evidence or next_question_agent_adjacent_project_evidence or next_question_agent_job_gap_only or next_question_agent_clarifies_when_materials_missing or next_question_agent_post_check_blocks or question_service_blocks_grounding_failure or follow_up_question_task_grounding_blocking or follow_up_question_task_does_not_repeat_existing_focus_key or follow_up_question_service_marks_fake_transport or follow_up_question_service_marks_missing_transport or question_task_persists_validation_failed"
PYTHONPATH=.:apps/api python -m pytest -q tests/api/test_polish_feedback_generation_service.py tests/api/test_polish_feedback_generation_schema.py tests/api/test_polish_feedback_runtime.py -k "confirmed_asset_conflict or same_question_regression or missing_points_remove_generate_next_question or next_action_regression or validator_rejects_generate_next_question or asset_update_candidates_are_forced or required_fields or provider_unavailable or validator_failed or unsafe_raw_prompt_or_provider_payload"
PYTHONPATH=.:apps/api python -m pytest -q tests/api/test_agent_candidate_payload_runtime_mapping.py tests/api/test_agent_contracts.py tests/architecture/test_agent_platform_c1_boundary.py tests/architecture/test_domain_polish_policy_boundary.py tests/evals
PYTHONPATH=.:apps/api python -m evals.runners.run_question_eval
PYTHONPATH=.:apps/api python -m evals.runners.run_feedback_eval
```

Audit commands:

```bash
git diff --check
git diff --name-only
git status --short --untracked-files=all
```

## 10. Stop Conditions

Stop immediately if:

- required recon files cannot be mapped;
- current code materially contradicts Project sources;
- implementation requires prompt rewrite;
- implementation requires provider behavior refactor;
- implementation requires DB schema or API contract change;
- implementation requires Phase7 / Phase8 / Phase11 / Phase12 work;
- agent would directly write formal business facts;
- tool would directly expose repository;
- existing tests require forbidden behavior changes;
- candidate-only semantics cannot be preserved;
- forbidden trace/provider data cannot be avoided;
- any file outside this Scope Lock must be edited.

## 11. Done Criteria

This window is done only when:

- recon report exists and source categories are cited in final report;
- this Scope Lock exists before implementation patch;
- Phase5 Question planned workflow exists or is clearly integrated;
- Phase6 Feedback planned workflow exists or is clearly integrated;
- Question / Feedback emit candidates before formal write;
- formal write path remains Application Service plus authorized handoff / domain-policy path;
- no prompt/provider/DB/API behavior diff is introduced;
- no Phase11/12 L5 implementation is introduced;
- focused tests/evals run and results are recorded;
- project source backfill records completion evidence and gaps;
- final report uses the required 14-section format.

## 12. Non-Claims

- This window does not mark Phase 11 or Phase 12 implemented.
- This window does not mark project L5 release done.
- This window does not mark Question or Feedback autonomous.
- This window does not complete Phase9 eval CI gates.
- This window does not complete the full Phase2 Interview Context service gap.

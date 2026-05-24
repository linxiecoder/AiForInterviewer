---
title: PR2 Runtime Data Model Preflight Readiness Report
type: delivery-planning
status: draft-pr2-preflight
owner: 项目交付
permalink: ai-for-interviewer/docs/03-delivery/refactor-multiagent-langgraph/pr2-preflight-readiness-report
---

# PR2 Runtime Data Model Preflight Readiness Report

## 1. Purpose

本文执行 `AIFI-BE-005`，只做 PR2 启动前 readiness gate，判断 PR2 runtime data model / repository / tests 是否可以开始代码实现。

本报告不实现 PR2，不修改 `apps/**`、`tests/**`、依赖、migration 或 CI。PR2 code implementation 是否允许，以本文 Decision 为准。

## 2. Inputs

| Input | Evidence Used | Notes |
|---|---|---|
| Governance | `AGENTS.md`; `docs/00-governance/DOCS_INDEX.md`; `docs/03-delivery/BACKLOG.md`; `docs/03-delivery/DELIVERY_PLAN.md` | active docs 和 Backlog 是当前执行依据；`archive/` 不作为当前事实源。 |
| Goal file | `docs/tmp/GOAL_AIFI_BE_005_PR2_PREFLIGHT_READINESS.md` | 只作为本轮目标输入；不提升为长期事实源。 |
| PR1.6 blocker plan | `19_AI_PRODUCT_PROMPT_SKILL_PRESSURE_REMEDIATION_PLAN.md` | 记录 PR2 blocked、P0 gates、AIFI-BE-004 / AIFI-PROMPT-002 / AIFI-ARCH-007 closure evidence。 |
| PR2 data / migration plan | `10_DATA_MODEL_AND_MIGRATION_PLAN.md` | 提供 runtime tables、字段级定义、repository methods、migration / rollback、retention 和 tests。 |
| Validation plan | `15_VALIDATION_PLAN.md` | 提供 PR2 preflight、static scans、pytest subset、real-provider gate。 |
| PR sequence | `17_PR_BREAKDOWN_AND_IMPLEMENTATION_SEQUENCE.md` | 定义 PR2 blocked 状态、allowed / forbidden files、启动门槛。 |
| ADR | `docs/04-decisions/ADR-0005-langgraph-agentic-workflow-runtime.md` | Option C 仍是 `Proposed`；AIFI-ARCH-008 directory caveat 已写入；PR2 仍需 blockers closed 或 accepted risk。 |
| Active design docs | `SKILL_MODEL_SPEC.md`; `PROMPT_ASSET_SPEC.md`; `PROMPT_EVALUATION_SPEC.md`; `PRESSURE_MODE_SPEC.md`; `DATA_MODEL.md`; `PERSISTENCE_MODEL.md`; `SECURITY_PRIVACY.md` | 用于确认 Skill / Prompt / Pressure / raw-off / rollback 边界。 |
| Current code / tests | `apps/api/app/infrastructure/db/models/**`; `apps/api/app/infrastructure/db/repositories/**`; `tests/api/test_db_schema_bootstrap.py`; `tests/api/test_model_imports.py`; `tests/api/test_architecture_boundaries.py` | 只读盘点现有 model style、repository base、bootstrap/import tests 和 architecture boundary tests。 |

## 3. Gate Checklist

| Gate | Status | Evidence | Impact | Required Action | Owner Task |
|---|---|---|---|---|---|
| AIFI-ARCH-008 closed or risk accepted | BLOCKER | `19_AI_PRODUCT_PROMPT_SKILL_PRESSURE_REMEDIATION_PLAN.md` says AIFI-ARCH-008 closed; ADR-0005 caveat says directory open issue closed; but `BACKLOG.md` still lists `AIFI-ARCH-008` as `READY_TO_PLAN` and the PR1.6 blocker note says PR2 depends on AIFI-ARCH-008 and AIFI-BE-005 closing or explicit accepted risk. | Backlog is the active task entry; the closure evidence is not fully synchronized into task status. PR2 code implementation cannot be authorized from conflicting state. | Close / accept AIFI-ARCH-008 in the active task entry, or record explicit accepted risk in `BACKLOG.md`, ADR, or authorized PR scope. | AIFI-ARCH-008 |
| AIFI-ARCH-007 closed or risk accepted | PASS | `BACKLOG.md` marks `AIFI-ARCH-007` `ACCEPTED`; `SKILL_MODEL_SPEC.md` states AIFI-ARCH-007 is the active design doc and PR2 must not create `Skill*` formal objects. | Skill Model blocker is closed for PR2 preflight, but it does not independently authorize PR2. | Preserve PR2 rule: no `Skill*` formal object and no temporary skill key. | AIFI-ARCH-007 |
| AIFI-PROMPT-002 closed or risk accepted | PASS | `BACKLOG.md` marks `AIFI-PROMPT-002` `ACCEPTED`; `PROMPT_ASSET_SPEC.md` and `PROMPT_EVALUATION_SPEC.md` say Prompt Asset / Evaluation design is implementation-ready but not PR2 authorization. | Prompt Asset / Evaluation blocker is closed for design; PR2 must not implement business graph prompt migration. | Keep PR2 independent from production prompt assets; PR5-PR8 use the asset / evaluation specs. | AIFI-PROMPT-002 |
| AIFI-BE-004 closed or risk accepted | PASS | `BACKLOG.md` marks `AIFI-BE-004` `ACCEPTED`; `PRESSURE_MODE_SPEC.md` freezes Pressure Mode and says Pressure graph does not enter PR2. | Pressure mode-level design no longer blocks PR2 data preflight; Pressure graph remains forbidden in PR2. | Keep Pressure business graph in PR8 or separately authorized Pressure PR. | AIFI-BE-004 |
| AI/Core directory shape finalized | PASS WITH TASK-STATUS CAVEAT | `03_TARGET_DIRECTORY_STRUCTURE.md` and `04_BACKEND_AGENT_RUNTIME_PLAN.md` freeze `application/ai_runtime/**` and `infrastructure/ai_runtime/langgraph/**`; ADR-0005 repeats this. | Directory design is ready, but AIFI-ARCH-008 task status conflict still blocks GO. | Synchronize AIFI-ARCH-008 closure / risk acceptance before PR2 code. | AIFI-ARCH-008 |
| ADR-0005 status / caveat supports PR2 | BLOCKER | ADR-0005 status is `Proposed`; it allows PR2 only after PR1.6 blockers are closed or main Agent explicitly accepts risk. | ADR supports the target architecture but explicitly does not permit immediate PR2 implementation. | Either accept ADR / relevant risk explicitly, or keep PR2 blocked until remaining blockers close. | AIFI-ARCH-008 / AIFI-BE-005 |
| Runtime data model field-level spec complete | PASS | `10_DATA_MODEL_AND_MIGRATION_PLAN.md` defines `agent_runs`, `agent_node_runs`, `agent_interrupts`, `agent_checkpoint_refs`, `llm_calls`, `llm_call_payloads` with SQLAlchemy type, nullable, default, indexes, unique constraints, owner scope, retention, API visibility and sensitivity. | The planning package is implementation-ready for model fields. Active `DATA_MODEL.md` still does not list these runtime objects as canonical business model facts. | If PR2 is later authorized, either keep runtime table truth in PR2 scope or backfill active docs as authorized. | AIFI-BE-005 |
| SQLAlchemy model-level spec complete | PASS | `10_DATA_MODEL_AND_MIGRATION_PLAN.md` aligns to `OwnedRecordMixin`, `id`, `String(80)`, `DateTime(timezone=True)`, `JSON`, indexes and unique constraints; model style scan found current models use these patterns. | PR2 has enough model-level constraints to implement `models/ai_runtime.py` after authorization. | Keep runtime models separate from Core Business formal objects; do not import LangGraph in ORM models. | AIFI-BE-005 |
| Repository method contract complete | PASS | `10_DATA_MODEL_AND_MIGRATION_PLAN.md` lists `AgentRunRepository`, `AgentNodeRunRepository`, `AgentInterruptRepository`, `AgentCheckpointRefRepository`, `LlmCallRepository`, `LlmCallPayloadRepository` and side-effect wrapper methods with owner/idempotency contracts. | Repository surface is implementable after authorization. | Implement only after PR2 GO; every method must be owner scoped and raw-off. | AIFI-BE-005 |
| Migration / rollback scope complete | PASS | `10_DATA_MODEL_AND_MIGRATION_PLAN.md` defines migration order and rollback order; `PERSISTENCE_MODEL.md` covers migration / rollback / backup restore handoff and in-flight `AiTask` rollback. Current repo has no Alembic directory; schema init uses SQLAlchemy bootstrap. | PR2 can use SQLAlchemy bootstrap/backfill tests rather than Alembic, but code implementation remains blocked by governance gates. | PR2 implementation must update bootstrap/import tests and avoid silent formal writes during rollback. | AIFI-BE-005 |
| Retention / security / raw-off policy complete | PASS | `10_DATA_MODEL_AND_MIGRATION_PLAN.md`, ADR-0005 and `SECURITY_PRIVACY.md` all forbid raw prompt, raw completion, provider payload, system prompt, token, cookie, secret and hidden scoring rules in normal logs/checkpoint/API/trace. | Security policy is defined enough for PR2 negative tests. | PR2 must add redaction tests before or with repository implementation. | AIFI-BE-005 |
| Architecture boundary tests specified | PASS | `03_TARGET_DIRECTORY_STRUCTURE.md`, `13_TEST_PLAN_BACKEND.md`, and `15_VALIDATION_PLAN.md` specify AST/import boundary tests and forbidden LangGraph import scans. Existing `test_architecture_boundaries.py` covers current layer boundaries but not yet the future LangGraph-specific cases. | Tests are specified; implementation must add/extend them in PR2/PR3 as scoped. | Add PR2 boundary coverage only after PR2 code authorization. | AIFI-BE-005 |
| Existing model import/bootstrap tests impact known | PASS | `tests/api/test_model_imports.py` currently imports existing model modules and asserts table subset; `tests/api/test_db_schema_bootstrap.py` verifies current schema bootstrap/backfill. `10_DATA_MODEL_AND_MIGRATION_PLAN.md` says PR2 must update these for six runtime tables. | Impact is known and directly testable. | PR2 must update imports and bootstrap assertions with runtime tables after authorization. | AIFI-BE-005 |
| PR2 allowed files and forbidden files clear | PASS | `17_PR_BREAKDOWN_AND_IMPLEMENTATION_SEQUENCE.md` states blocked-state allowed ops are repo-state preflight, read-only recon and authorized docs writeback. After new authorization, PR2 allowed files are runtime model/repository/sanitized LLM persistence/backend tests; forbidden files include business graph, LangGraph dependency, real provider and `application/ai_runtime/graphs/**`. | Scope is clear. Current PR2 code implementation remains blocked. | Re-lock scope before any PR2 code implementation. | AIFI-BE-005 |
| PR2 validation commands clear | PASS | `15_VALIDATION_PLAN.md` gives PR2 preflight and pytest subset; this report also records validation commands below. | Validation surface is clear. | Re-run validation after any status synchronization and again after implementation. | AIFI-BE-005 |
| Runtime feature flags / default-off policy | BLOCKER | `03_TARGET_DIRECTORY_STRUCTURE.md` and `04_BACKEND_AGENT_RUNTIME_PLAN.md` mention `runtime_flags.py`, default-off, per-graph flag and real-provider gate, but PR2 code is still blocked and no accepted risk records bypassing this gate were found. | PR2 runtime tables should not be created under a path that can accidentally activate graph/provider behavior. | Freeze or explicitly accept runtime flag/default-off behavior before implementation. | AIFI-BE-005 / PR3 |
| Source-of-truth backfill / active docs sync decision | BLOCKER | ADR-0005 follow-up table says `DATA_MODEL.md`, `PERSISTENCE_MODEL.md`, `SECURITY_PRIVACY.md`, `APPLICATION_FLOW_SPEC.md` and `API_SPEC.md` require backfill in later PRs; `16_DESIGN_DOCS_REFACTOR_PLAN.md` says conflicts must be resolved in active docs, BACKLOG or ADR before implementation. No accepted risk record was found for skipping this. | Planning package is detailed, but active canonical docs are not fully synchronized for PR2 runtime objects. | Either complete authorized active-docs backfill / sync decision or record accepted risk before PR2 code. | AIFI-BE-005 / main Agent |

## 4. Blocker Table

| Gate | Status | Evidence | Impact | Required Action | Owner Task |
|---|---|---|---|---|---|
| AIFI-ARCH-008 active task state | BLOCKER | `BACKLOG.md` has `AIFI-ARCH-008` status `READY_TO_PLAN`; PR1.6 note says PR2 still depends on AIFI-ARCH-008 and AIFI-BE-005 closure. | AIFI-ARCH-008 cannot be treated as fully closed from AIFI-BE-005 alone. | Close / accept AIFI-ARCH-008 in active task state or record accepted risk. | AIFI-ARCH-008 |
| ADR-0005 proposed / conditional caveat | BLOCKER | ADR-0005 is `Proposed` and states PR2 remains blocked until remaining PR1.6 blockers are resolved or explicitly accepted. | Architecture decision does not currently authorize implementation. | Accept the relevant ADR/risk or keep PR2 blocked. | AIFI-ARCH-008 / main Agent |
| Source-of-truth backfill / accepted risk missing | BLOCKER | ADR-0005 lists follow-up active-docs backfill; `16_DESIGN_DOCS_REFACTOR_PLAN.md` says implementation cannot resolve active-doc conflicts first. | PR2 implementation could rely on planning package instead of canonical active docs. | Decide and register active-docs sync scope or accepted risk. | AIFI-BE-005 / main Agent |
| Runtime flags default-off gate | BLOCKER | Runtime flag/default-off concepts are planned but not closed as an implementation authorization gate. | Runtime foundation could be merged without a stable disable / rollback guard. | Freeze runtime enablement / default-off / real-provider gate before code. | AIFI-BE-005 / PR3 |

## 5. PR2 Scope Lock

```text
task_id: AIFI-BE-005
allowed_ops_current: READ_ONLY_RECON + DOCS_ONLY_REPORT
forbidden_ops_current: PR2 code implementation; apps/** edits; tests/** edits; dependency edits; migrations; CI edits; real provider calls; commit; push
final_artifact: docs/03-delivery/refactor-multiagent-langgraph/20_PR2_PREFLIGHT_READINESS_REPORT.md
done_condition: readiness verdict recorded; blockers listed; final response states whether PR2 code implementation is allowed
```

If a future turn explicitly re-authorizes PR2 code implementation, the scope must be re-locked. This report does not grant that authorization.

## 6. Allowed Files

Current AIFI-BE-005 allowed files:

- `docs/03-delivery/refactor-multiagent-langgraph/20_PR2_PREFLIGHT_READINESS_REPORT.md`
- `docs/03-delivery/refactor-multiagent-langgraph/17_PR_BREAKDOWN_AND_IMPLEMENTATION_SEQUENCE.md`, only if updating PR2 readiness status is necessary
- `docs/03-delivery/BACKLOG.md`, only if updating AIFI-BE-005 status is necessary
- `docs/00-governance/DOCS_INDEX.md`, only if registering this report is necessary

No update to `17_PR_BREAKDOWN_AND_IMPLEMENTATION_SEQUENCE.md`, `BACKLOG.md`, or `DOCS_INDEX.md` is required by this NO-GO verdict; existing entries already state PR2 is blocked and the directory package is already registered.

Future PR2 implementation files, only after new explicit authorization:

- `apps/api/app/infrastructure/db/models/ai_runtime.py`
- `apps/api/app/infrastructure/db/repositories/ai_runtime/**`
- sanitized LLM persistence files explicitly included in the new Scope Lock
- backend tests explicitly included in the new Scope Lock
- authorized active-docs sync files, if the main Agent includes them in scope

## 7. Forbidden Files

Forbidden in this AIFI-BE-005 readiness turn:

- `apps/**`
- `tests/**`
- dependency files / lockfiles
- migrations / Alembic or schema migration directories
- CI config
- real provider / real LLM calls
- business graph implementation
- `application/ai_runtime/graphs/**`
- LangGraph dependency or concrete adapter implementation
- commit / push

## 8. Required Tests

Read-only / current-state checks run or inspected for AIFI-BE-005:

- model style scan over current DB models and bootstrap/import tests
- forbidden LangGraph / AgentState import scan over current DB models and application layer
- `.venv/bin/python -m pytest tests/api/test_model_imports.py tests/api/test_db_schema_bootstrap.py -q`

Future PR2 implementation tests, after explicit re-authorization:

- `tests/api/test_model_imports.py`
- `tests/api/test_db_schema_bootstrap.py`
- `tests/api/test_agent_run_repository.py`
- `tests/api/test_agent_interrupt_repository.py`
- `tests/api/test_llm_call_repository.py`
- `tests/api/test_sensitive_payload_redaction.py`
- `tests/api/test_agent_side_effect_idempotency.py`
- `tests/api/test_agent_replay_resume_policy.py`
- architecture/import boundary tests scoped to runtime models/repositories and forbidden LangGraph imports

## 9. Required Validation Commands

Required by the goal file:

```bash
git status --short --untracked-files=all
git diff --stat
git diff --check
.venv/bin/python -m tools.doc_governor.cli doc-quality-gate --repo-root .
```

Additional PR2 preflight commands from `15_VALIDATION_PLAN.md`:

```bash
git branch --show-current
git rev-parse HEAD
git rev-list --left-right --count origin/main...HEAD
rg -n "class .*\\(OwnedRecordMixin, Base\\)|__tablename__|mapped_column\\(|JSON|DateTime\\(timezone=True\\)|String\\(80\\)" apps/api/app/infrastructure/db/models tests/api/test_db_schema_bootstrap.py tests/api/test_model_imports.py
rg -n "LangGraph|langgraph|AgentState|application/agents|from app.application.agents|import langgraph" apps/api/app/infrastructure/db/models apps/api/app/application
.venv/bin/python -m pytest tests/api/test_model_imports.py tests/api/test_db_schema_bootstrap.py -q
rg -n "LLM_OPENAI_API_KEY|AIFI_.*REAL_PROVIDER|REAL_PROVIDER|provider manual" tests apps/api
```

Observed preflight evidence before report creation:

| Command | Result | Notes |
|---|---|---|
| `git status --short --untracked-files=all` | PASS | clean before creating this report |
| `git branch --show-current` | PASS | `main` |
| `git rev-parse HEAD` | PASS | `02620a30b51fc36bf523d7965dc75d342af57e2b` |
| `git rev-list --left-right --count origin/main...HEAD` | PASS | `0 0` |
| model style scan | PASS | Current models use `OwnedRecordMixin`, `mapped_column`, `String(80)`, `JSON`, `DateTime(timezone=True)` patterns expected by PR2. |
| forbidden dependency scan | PASS | No current match for LangGraph / AgentState imports in `models` or `application` paths. |
| schema bootstrap preflight | PASS | `3 passed in 1.67s` for `test_model_imports.py` and `test_db_schema_bootstrap.py`. |
| provider gate scan | WARN | Existing Polish/OpenAI-compatible tests and services define real-provider env gates; PR2 must not use those paths or require real provider. |

Observed validation evidence after report creation:

| Command | Result | Notes |
|---|---|---|
| `git status --short --untracked-files=all` | PASS WITH EXPECTED DOC OUTPUT | Shows only this new report as untracked after removing the transient doc-quality report artifact. |
| `git diff --stat` | PASS | No tracked diff; the new report is untracked until explicitly staged by a later authorized step. |
| `git diff --check` | PASS | No whitespace errors in tracked diff. |
| `.venv/bin/python -m tools.doc_governor.cli doc-quality-gate --repo-root .` | PASS | `ok=true`, `error=0`, `warning=0`. The command generated `docs/governance/DOC_QUALITY_GATE_REPORT.md`; that transient untracked artifact was removed because it is outside this task's required output. |
| Markdown mojibake scan | PASS | No replacement character or common mojibake markers found in this report. |

## 10. Decision

**NO-GO. PR2 code implementation is not allowed.**

The implementation package is substantially more mature than the previous PR1.6 state: runtime table fields, repository methods, rollback order, raw-off policy, tests, import scans and scope boundaries are mostly defined. However, the active governance state still contains unresolved blockers:

- `BACKLOG.md` does not mark `AIFI-ARCH-008` closed or accepted.
- ADR-0005 remains `Proposed` and explicitly conditions PR2 on blocker closure or accepted risk.
- source-of-truth backfill / active-docs sync is not fully closed or risk accepted.
- runtime enablement / default-off / real-provider gate is not closed as an implementation authorization gate.

Because the goal file's strict rule requires NO-GO when a required gate is missing without explicit accepted risk, this report cannot authorize PR2 code implementation.

## 11. GO Implementation Prompt Summary

Not provided because the decision is NO-GO.

## 12. NO-GO Blockers

1. Close or explicitly risk-accept `AIFI-ARCH-008` in the active task state.
2. Record whether ADR-0005 / Option C is accepted for PR2, or explicitly accept the risk of implementing under `Proposed` status.
3. Decide source-of-truth backfill scope for `DATA_MODEL.md`, `PERSISTENCE_MODEL.md`, `SECURITY_PRIVACY.md`, `APPLICATION_FLOW_SPEC.md`, `API_SPEC.md`, `BACKLOG.md`, and `DOCS_INDEX.md`, or record accepted risk.
4. Freeze runtime enablement / default-off / per-graph / real-provider gate behavior before runtime code is allowed.
5. Re-run this AIFI-BE-005 gate after those items are closed or risk accepted.

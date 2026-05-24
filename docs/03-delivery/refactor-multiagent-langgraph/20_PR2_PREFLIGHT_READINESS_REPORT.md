---
title: PR2 Runtime Data Model Preflight Readiness Report
type: delivery-planning
status: conditional-go-pr2-runtime-foundation
owner: 项目交付
permalink: ai-for-interviewer/docs/03-delivery/refactor-multiagent-langgraph/pr2-preflight-readiness-report
---

# PR2 Runtime Data Model Preflight Readiness Report

## 1. Purpose

本文执行 `AIFI-BE-005`，并由 `AIFI-BE-006` 做 governance closure，只判断 PR2 runtime data model / repository / tests 是否可以开始代码实现。

本报告不实现 PR2，不修改 `apps/**`、`tests/**`、依赖、migration 或 CI。PR2 code implementation 是否允许，以本文 Decision 和 exact Scope Lock 为准。

## 2. Inputs

| Input | Evidence Used | Notes |
|---|---|---|
| Governance | `AGENTS.md`; `docs/00-governance/DOCS_INDEX.md`; `docs/03-delivery/BACKLOG.md`; `docs/03-delivery/DELIVERY_PLAN.md` | active docs 和 Backlog 是当前执行依据；`archive/` 不作为当前事实源。 |
| Goal file | `docs/tmp/GOAL_AIFI_BE_005_PR2_PREFLIGHT_READINESS.md` | 只作为前序目标输入；不提升为长期事实源。 |
| PR1.6 blocker plan | `19_AI_PRODUCT_PROMPT_SKILL_PRESSURE_REMEDIATION_PLAN.md` | 记录 PR2 blocked、P0 gates、AIFI-BE-004 / AIFI-PROMPT-002 / AIFI-ARCH-007 / AIFI-ARCH-008 closure evidence。 |
| PR2 data / migration plan | `10_DATA_MODEL_AND_MIGRATION_PLAN.md` | 提供 runtime tables、字段级定义、repository methods、migration / rollback、retention 和 tests。 |
| Validation plan | `15_VALIDATION_PLAN.md` | 提供 PR2 preflight、static scans、pytest subset、real-provider gate。 |
| PR sequence | `17_PR_BREAKDOWN_AND_IMPLEMENTATION_SEQUENCE.md` | 定义 PR2 scope、allowed / forbidden files、启动门槛。 |
| ADR | `docs/04-decisions/ADR-0005-langgraph-agentic-workflow-runtime.md` | Option C 仍是 `Proposed`；PR2-only accepted risk 已登记，只授权 inert runtime foundation。 |
| Active design docs | `SKILL_MODEL_SPEC.md`; `PROMPT_ASSET_SPEC.md`; `PROMPT_EVALUATION_SPEC.md`; `PRESSURE_MODE_SPEC.md`; `DATA_MODEL.md`; `PERSISTENCE_MODEL.md`; `SECURITY_PRIVACY.md` | 用于确认 Skill / Prompt / Pressure / raw-off / rollback 边界。 |
| Current code / tests | `apps/api/app/infrastructure/db/models/**`; `apps/api/app/infrastructure/db/repositories/**`; `tests/api/test_db_schema_bootstrap.py`; `tests/api/test_model_imports.py`; `tests/api/test_architecture_boundaries.py` | 前序报告只读盘点现有 model style、repository base、bootstrap/import tests 和 architecture boundary tests。 |

## 3. Gate Checklist

| Gate | Status | Evidence | Impact | Required Action | Owner Task |
|---|---|---|---|---|---|
| AIFI-ARCH-008 closed or risk accepted | PASS | `BACKLOG.md` marks `AIFI-ARCH-008` as `ACCEPTED`; `19_AI_PRODUCT_PROMPT_SKILL_PRESSURE_REMEDIATION_PLAN.md` and ADR-0005 already say the AI/Core directory issue is closed. | Directory blocker no longer blocks PR2. | Preserve final directory shape: `application/ai_runtime/**` + `infrastructure/ai_runtime/langgraph/**`; PR2 still must not create business graph directories. | AIFI-ARCH-008 |
| AIFI-ARCH-007 closed or risk accepted | PASS | `BACKLOG.md` marks `AIFI-ARCH-007` `ACCEPTED`; `SKILL_MODEL_SPEC.md` states AIFI-ARCH-007 is the active design doc and PR2 must not create `Skill*` formal objects. | Skill Model blocker is closed for PR2 preflight, but it does not independently authorize business graph work. | Preserve PR2 rule: no `Skill*` formal object and no temporary skill key. | AIFI-ARCH-007 |
| AIFI-PROMPT-002 closed or risk accepted | PASS | `BACKLOG.md` marks `AIFI-PROMPT-002` `ACCEPTED`; `PROMPT_ASSET_SPEC.md` and `PROMPT_EVALUATION_SPEC.md` say Prompt Asset / Evaluation design is implementation-ready but not PR2 authorization. | Prompt Asset / Evaluation blocker is closed for design; PR2 must not implement production prompt asset or business graph prompt migration. | Keep PR2 independent from production prompt assets; PR5-PR8 use the asset / evaluation specs. | AIFI-PROMPT-002 |
| AIFI-BE-004 closed or risk accepted | PASS | `BACKLOG.md` marks `AIFI-BE-004` `ACCEPTED`; `PRESSURE_MODE_SPEC.md` freezes Pressure Mode and says Pressure graph does not enter PR2. | Pressure mode-level design no longer blocks PR2 data preflight; Pressure graph remains forbidden in PR2. | Keep Pressure business graph in PR8 or separately authorized Pressure PR. | AIFI-BE-004 |
| AI/Core directory shape finalized | PASS | `03_TARGET_DIRECTORY_STRUCTURE.md`, `04_BACKEND_AGENT_RUNTIME_PLAN.md`, `17_PR_BREAKDOWN_AND_IMPLEMENTATION_SEQUENCE.md`, ADR-0005 and `BACKLOG.md` freeze `application/ai_runtime/**` and `infrastructure/ai_runtime/langgraph/**`. | Directory design is ready for PR2 repository/model work and later PR3/PR4 runtime layers. | Do not reintroduce `application/ai/**`, `application/agents/**`, `infrastructure/agent_runtime/**` or application-level `langgraph_adapters/**`. | AIFI-ARCH-008 |
| ADR-0005 status / caveat supports PR2 | CONDITIONAL PASS | ADR-0005 remains `Proposed`, but now records PR2-only accepted risk for inert AI Runtime data model / repository / backend tests under this report's exact scope lock. | The full Option C architecture is not accepted for PR3-PR8 or business graphs; PR2 runtime foundation can proceed under a constrained accepted-risk path. | Before PR3/PR4 runtime exposure or PR5-PR8 business graph migration, revisit ADR status or record a new accepted risk. | AIFI-BE-006 / main Agent |
| Runtime data model field-level spec complete | PASS | `10_DATA_MODEL_AND_MIGRATION_PLAN.md` defines `agent_runs`, `agent_node_runs`, `agent_interrupts`, `agent_checkpoint_refs`, `llm_calls`, `llm_call_payloads` with SQLAlchemy type, nullable, default, indexes, unique constraints, owner scope, retention, API visibility and sensitivity. | The planning package is implementation-ready for model fields. | PR2 may implement only these inert runtime fields and tests; no business model canonicalization is implied. | AIFI-BE-005 |
| SQLAlchemy model-level spec complete | PASS | `10_DATA_MODEL_AND_MIGRATION_PLAN.md` aligns to `OwnedRecordMixin`, `id`, `String(80)`, `DateTime(timezone=True)`, `JSON`, indexes and unique constraints; model style scan found current models use these patterns. | PR2 has enough model-level constraints to implement `models/ai_runtime.py`. | Keep runtime models separate from Core Business formal objects; do not import LangGraph in ORM models. | AIFI-BE-005 |
| Repository method contract complete | PASS | `10_DATA_MODEL_AND_MIGRATION_PLAN.md` lists `AgentRunRepository`, `AgentNodeRunRepository`, `AgentInterruptRepository`, `AgentCheckpointRefRepository`, `LlmCallRepository`, `LlmCallPayloadRepository` and side-effect wrapper methods with owner/idempotency contracts. | Repository surface is implementable under PR2 scope. | Every method must be owner scoped, raw-off, idempotency-aware and unable to write formal business objects. | AIFI-BE-005 |
| Migration / rollback scope complete | PASS | `10_DATA_MODEL_AND_MIGRATION_PLAN.md` defines migration order and rollback order; `PERSISTENCE_MODEL.md` covers migration / rollback / backup restore handoff and in-flight `AiTask` rollback. Current repo has no Alembic directory; schema init uses SQLAlchemy bootstrap. | PR2 can use SQLAlchemy bootstrap/backfill tests rather than Alembic. | PR2 must update bootstrap/import tests and avoid silent formal writes during rollback. | AIFI-BE-005 |
| Retention / security / raw-off policy complete | PASS | `10_DATA_MODEL_AND_MIGRATION_PLAN.md`, ADR-0005 and `SECURITY_PRIVACY.md` all forbid raw prompt, raw completion, provider payload, system prompt, token, cookie, secret and hidden scoring rules in normal logs/checkpoint/API/trace. | Security policy is defined enough for PR2 negative tests. | PR2 must add redaction tests before or with repository implementation. | AIFI-BE-005 |
| Architecture boundary tests specified | PASS | `03_TARGET_DIRECTORY_STRUCTURE.md`, `13_TEST_PLAN_BACKEND.md`, and `15_VALIDATION_PLAN.md` specify AST/import boundary tests and forbidden LangGraph import scans. Existing `test_architecture_boundaries.py` covers current layer boundaries but not yet the future LangGraph-specific cases. | Tests are specified; PR2 may add only PR2-scoped boundary cases. | Add PR2 boundary coverage for runtime models/repositories and forbidden LangGraph imports; do not add PR3/PR4 graph adapter tests. | AIFI-BE-005 |
| Existing model import/bootstrap tests impact known | PASS | `tests/api/test_model_imports.py` currently imports existing model modules and asserts table subset; `tests/api/test_db_schema_bootstrap.py` verifies current schema bootstrap/backfill. `10_DATA_MODEL_AND_MIGRATION_PLAN.md` says PR2 must update these for runtime tables. | Impact is known and directly testable. | PR2 must update imports and bootstrap assertions with runtime tables. | AIFI-BE-005 |
| PR2 allowed files and forbidden files clear | PASS | `17_PR_BREAKDOWN_AND_IMPLEMENTATION_SEQUENCE.md` and this report list the exact PR2 scope lock. | Scope is clear and narrow. | Any implementation window must re-lock scope to this report before editing code/tests. | AIFI-BE-005 |
| PR2 validation commands clear | PASS | `15_VALIDATION_PLAN.md` gives PR2 preflight and pytest subset; this report also records validation commands below. | Validation surface is clear. | Re-run validation after implementation. | AIFI-BE-005 |
| Runtime feature flags / default-off policy | PASS | ADR-0005 now freezes `PR2 Default-Off Rule`; `17_PR_BREAKDOWN_AND_IMPLEMENTATION_SEQUENCE.md` G6 says PR2 does not create / modify runtime enablement flag, per-graph flag, real-provider gate or `runtime_flags.py`. | PR2 runtime foundation cannot activate graph/provider behavior by itself. | Runtime flag implementation is deferred to PR3; PR2 tests must prove no LangGraph/provider dependency is introduced. | AIFI-BE-005 / AIFI-BE-006 |
| Source-of-truth backfill / active docs sync decision | CONDITIONAL PASS | ADR-0005 follow-up table records accepted-risk deferral for `DATA_MODEL.md`, `PERSISTENCE_MODEL.md` and `SECURITY_PRIVACY.md`; `17_PR_BREAKDOWN_AND_IMPLEMENTATION_SEQUENCE.md` G7 repeats that full backfill is required before PR3/PR4 runtime exposure. | PR2 may implement inert runtime tables from the planning package without pretending active design docs are fully backfilled. | Before PR3/PR4 runtime exposure, backfill active docs or record a new accepted risk. | AIFI-BE-006 / main Agent |

## 4. Governance Closure Table

| Previous NO-GO blocker | Closure decision | Evidence | Residual constraint |
|---|---|---|---|
| AIFI-ARCH-008 active task state | CLOSED | `BACKLOG.md` status changed to `ACCEPTED`; directory shape already frozen in `03_TARGET_DIRECTORY_STRUCTURE.md`, `04_BACKEND_AGENT_RUNTIME_PLAN.md`, `17_PR_BREAKDOWN_AND_IMPLEMENTATION_SEQUENCE.md` and ADR-0005. | Closed only for directory/import boundary; no runtime symbol or business graph is authorized by AIFI-ARCH-008. |
| ADR-0005 proposed / conditional caveat | CLOSED BY PR2-ONLY ACCEPTED RISK | ADR-0005 remains `Proposed`, but records accepted risk for PR2 inert data model / repository / backend tests under this report's exact scope lock. | Full Option C acceptance remains open before PR3/PR4 runtime exposure or PR5-PR8 business graph migration. |
| Source-of-truth backfill / accepted risk missing | CLOSED BY DEFERRAL + ACCEPTED RISK | ADR-0005 and `17_PR_BREAKDOWN_AND_IMPLEMENTATION_SEQUENCE.md` say PR2 may use planning package + ADR + readiness report for inert foundation; active design doc backfill is deferred before PR3/PR4 runtime exposure. | PR2 must not claim `DATA_MODEL.md`, `PERSISTENCE_MODEL.md`, `SECURITY_PRIVACY.md`, `APPLICATION_FLOW_SPEC.md` or `API_SPEC.md` are fully synchronized. |
| Runtime flags default-off gate | CLOSED | ADR-0005 `PR2 Default-Off Rule` and `17_PR_BREAKDOWN_AND_IMPLEMENTATION_SEQUENCE.md` G6 freeze PR2 as default-off: no runtime flag implementation, no graph execution, no real provider, no business graph migration. | Runtime enablement remains PR3+ scope and requires separate authorization. |

## 5. PR2 Exact Scope Lock

```text
task_id: AIFI-BE-005
governance_closure_task: AIFI-BE-006
decision: CONDITIONAL GO
files:
  - apps/api/app/infrastructure/db/models/ai_runtime.py
  - apps/api/app/infrastructure/db/repositories/ai_runtime/**
  - tests/api/test_model_imports.py
  - tests/api/test_db_schema_bootstrap.py
  - tests/api/test_agent_run_repository.py
  - tests/api/test_agent_interrupt_repository.py
  - tests/api/test_llm_call_repository.py
  - tests/api/test_sensitive_payload_redaction.py
  - tests/api/test_agent_side_effect_idempotency.py
  - tests/api/test_agent_replay_resume_policy.py
  - tests/api/test_architecture_boundaries.py (PR2 import-boundary assertions only)
allowed_ops: EDIT_LISTED_FILES only after a new PR2 implementation turn re-locks this exact scope
forbidden_ops: LangGraph runtime enablement; graph execution; real provider calls; business graph migration; runtime facade / runner / adapter / checkpointer / serializer implementation; runtime_flags.py creation or edits; apps/api/app/application/ai_runtime/graphs/**; frontend edits; dependency / lockfile edits; migration / Alembic edits; CI edits; unrelated backend/business code edits; commit; push
default_off_rule: PR2 may create inert data models, repositories and tests only; no code path may start, resume, replay or execute a graph, invoke a provider, or write a formal business object from runtime data.
final_artifact: PR2 implementation diff limited to the listed files plus verification evidence
done_condition: schema/import/bootstrap/repository/redaction/idempotency/boundary tests pass; forbidden LangGraph/provider scans pass; git diff contains no files outside this scope
```

This docs-only AIFI-BE-006 closure does not itself edit PR2 code. It authorizes a later PR2 implementation window only if that window adopts this exact Scope Lock before touching code.

## 6. Current Docs-Only Allowed Files

Current AIFI-BE-006 closure files:

- `docs/03-delivery/BACKLOG.md`
- `docs/04-decisions/ADR-0005-langgraph-agentic-workflow-runtime.md`
- `docs/03-delivery/refactor-multiagent-langgraph/17_PR_BREAKDOWN_AND_IMPLEMENTATION_SEQUENCE.md`
- `docs/03-delivery/refactor-multiagent-langgraph/20_PR2_PREFLIGHT_READINESS_REPORT.md`
- `docs/03-delivery/refactor-multiagent-langgraph/15_VALIDATION_PLAN.md`, only if validation gates need clarification

## 7. Forbidden Files

Forbidden in this AIFI-BE-006 governance closure turn:

- `apps/**`
- `tests/**`
- dependency files / lockfiles
- migrations / Alembic or schema migration directories
- CI config
- backend code, frontend code or business code
- real provider / real LLM calls
- commit / push

Forbidden in the later PR2 implementation unless explicitly re-authorized:

- `apps/api/app/application/**`
- `apps/api/app/infrastructure/ai_runtime/langgraph/**`
- `apps/api/app/application/ai_runtime/graphs/**`
- LangGraph / LangChain dependency or concrete adapter implementation
- runtime flag enablement
- business graph implementation or migration
- real provider / real LLM calls

## 8. Required Tests

Required for this docs-only governance closure:

- `git status --short --untracked-files=all`
- `git diff --stat`
- `git diff --check`
- `.venv/bin/python -m tools.doc_governor.cli doc-quality-gate --repo-root .`

Required for the later PR2 implementation:

- `tests/api/test_model_imports.py`
- `tests/api/test_db_schema_bootstrap.py`
- `tests/api/test_agent_run_repository.py`
- `tests/api/test_agent_interrupt_repository.py`
- `tests/api/test_llm_call_repository.py`
- `tests/api/test_sensitive_payload_redaction.py`
- `tests/api/test_agent_side_effect_idempotency.py`
- `tests/api/test_agent_replay_resume_policy.py`
- architecture/import boundary tests scoped to runtime models/repositories and forbidden LangGraph imports
- forbidden real-provider / LangGraph scans from `15_VALIDATION_PLAN.md`

## 9. Required Validation Commands

Required by this goal:

```bash
git status --short --untracked-files=all
git diff --stat
git diff --check
.venv/bin/python -m tools.doc_governor.cli doc-quality-gate --repo-root .
```

Additional PR2 implementation preflight commands from `15_VALIDATION_PLAN.md`:

```bash
git branch --show-current
git rev-parse HEAD
git rev-list --left-right --count origin/main...HEAD
rg -n "class .*\\(OwnedRecordMixin, Base\\)|__tablename__|mapped_column\\(|JSON|DateTime\\(timezone=True\\)|String\\(80\\)" apps/api/app/infrastructure/db/models tests/api/test_db_schema_bootstrap.py tests/api/test_model_imports.py
rg -n "LangGraph|langgraph|AgentState|application/agents|from app.application.agents|import langgraph" apps/api/app/infrastructure/db/models apps/api/app/application
.venv/bin/python -m pytest tests/api/test_model_imports.py tests/api/test_db_schema_bootstrap.py -q
rg -n "LLM_OPENAI_API_KEY|AIFI_.*REAL_PROVIDER|REAL_PROVIDER|provider manual" tests apps/api
```

Observed validation evidence after AIFI-BE-006 governance closure:

| Command | Result | Notes |
|---|---|---|
| `git status --short --untracked-files=all` | PASS WITH EXPECTED DOC DIFF | Shows only allowed docs changes for this closure. |
| `git diff --stat` | PASS | Diff is limited to allowed docs. |
| `git diff --check` | PASS | No whitespace errors. |
| `.venv/bin/python -m tools.doc_governor.cli doc-quality-gate --repo-root .` | PASS | `ok=true`, `error=0`, `warning=0`. |
| Markdown mojibake scan | PASS | No replacement character or common mojibake markers found in edited files. |

## 10. Decision

**CONDITIONAL GO. PR2 code implementation is allowed only under the exact Scope Lock in §5.**

The remaining NO-GO blockers are closed or accepted as bounded risk:

- `AIFI-ARCH-008` is `ACCEPTED` in `BACKLOG.md`; directory/import boundary is closed.
- ADR-0005 remains `Proposed`, but records a PR2-only accepted risk for inert runtime foundation.
- source-of-truth active docs backfill is accepted-risk deferred for PR2 only and must be revisited before PR3/PR4 runtime exposure.
- runtime enablement / default-off / real-provider behavior is frozen by prohibition: PR2 does not implement or enable runtime flags, graph execution or real provider calls.

This is not a full GO for LangGraph runtime, graph execution, provider integration, application facade / adapter, frontend UI, or business graph migration.

## 11. PR2 Implementation Prompt Summary

Implement PR2 Runtime Data Model only under `AIFI-BE-005`:

1. Re-lock the exact Scope Lock from §5 before editing.
2. Create only the AI Runtime ORM model file, AI Runtime repositories and listed backend tests.
3. Keep PR2 default-off: no LangGraph dependency/import, no graph execution, no real provider, no runtime flag enablement, no business graph migration.
4. Prove owner scope, raw-off, checkpoint-ref-only, idempotency replay and no formal business write through tests.
5. Run the PR2 pytest subset, forbidden import/provider scans, `git diff --check` and doc-quality gate if docs are touched.

## 12. Remaining Blockers

No blocker remains for PR2 runtime data model / repository / tests inside §5.

Remaining blockers for later PRs:

1. Before PR3 / PR4 runtime exposure, backfill `DATA_MODEL.md`, `PERSISTENCE_MODEL.md`, `SECURITY_PRIVACY.md`, `APPLICATION_FLOW_SPEC.md` and `API_SPEC.md`, or record a new accepted risk.
2. Before PR3 / PR4 runtime exposure, decide whether ADR-0005 becomes `Accepted` or stays `Proposed` with a new bounded risk.
3. Before PR4 or any business graph migration, implement and test runtime flags, per-graph enablement, fake-provider default, real-provider gate and rollback disable behavior.

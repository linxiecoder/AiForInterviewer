---
title: PHASE_3_WINDOW_CATALOG
type: window-catalog
status: evidence-only
owner: P3-W0-DOMAIN-POLICY-SCOPE-LOCK
permalink: ai-for-interviewer/docs/goals/2026-06-03/phase-3-window-catalog
---

# Phase 3 Window Catalog

本文件是 `P3-W0-DOMAIN-POLICY-SCOPE-LOCK` 产出的 Phase 3 window catalog。它只记录下一步执行建议和 scope-lock，不授权实现。

## 1. Global Rules

| Rule | Value |
| --- | --- |
| Phase | Phase 3 - Domain Policies |
| Domain policy purity | Must not access DB, call LLM, import FastAPI, import infrastructure, import provider SDKs, render prompts, or perform formal writes |
| Application role | Orchestrate policy calls, repositories, context, transactions, DTO mapping, and handoff |
| Prompt builder role | Render already-decided context / policy / contract only |
| Agent role | Output candidate / suggestion only |
| Formal write rule | Formal business writes require Application Service + Domain Policy + Handoff |
| Global forbidden changes | Prompt assets, provider behavior, DB schema / migrations, API routes / contracts, LangGraph / Agent runtime wiring, frontend |

## 2. Window Status Map

| Window | Status | Evidence | Next action |
| --- | --- | --- | --- |
| P3-W0 | `scope_locked_docs_only` | This record creates scope lock, catalog, entry gaps, and decision options under `docs/goals/2026-06-03/`. | Commit docs-only P3-W0 artifacts; wait for controller decision. |
| P3-W1 | `partial_with_deferred_gap` | `SourceSupportPolicy` exists under `app.domain.polish.policies`; existing Phase 3 closeout records source support as implemented with deferred summary gap; no full `SourceSupportSummary` symbol or payload was found. | Audit/repair only if controller chooses; do not duplicate source support implementation. |
| P3-W2 | `implemented_with_residual_gap` | `question_grounding_policy.py` and `follow_up_coverage_policy.py` exist with domain tests; `question_grounding.py` and `use_cases.py` call domain policies. `question_metadata.py` legacy helper remains residual because it was not in the allowed write set. | Keep residual helper / `next_question_agent.py` guardrail explicit; proceed to P3-W3 only under controller authorization. |
| P3-W3 | `implemented_p3_w3` | `asset_consistency_policy.py`, `answer_coverage_policy.py`, and `answer_change_policy.py` exist with domain tests; `feedback_rules.py` calls them as adapter / legacy payload bridge. | Proceed to P3-W4 next-action policy; keep Phase 2 / SRC-001 / CTX-002 deferred gaps open. |
| P3-W4 | `implemented_p3_w4` | `feedback_next_action_policy.py` exists with domain tests; `feedback_rules.py` calls it as next-action adapter while `feedback_validation.py` keeps schema guardrails. | Proceed to P3-W5 bridge / boundary hardening; keep Phase 2 / SRC-001 / CTX-002 deferred gaps open. |
| P3-W5 | `implemented_p3_w5` | `tests/architecture/test_domain_polish_policy_boundary.py` now locks Phase 3 policy file list, application bridge imports, policy entrypoint calls, and thin adapter runtime boundary. | Proceed only to P3-W6 assessment/backfill with Phase 2 / SRC-001 / CTX-002 still open; do not claim final closeout. |
| P3-W6 | `blocked_requires_controller_decision` | P3-W6 assessment updated closeout / gap evidence after P3-W5, but Phase 2 closeout evidence, SRC-001, and CTX-002 / `SourceSupportSummary` remain deferred gaps. | Open CTX-002 / SourceSupportSummary repair or Phase 2 / SRC-001 backfill, or obtain explicit final-residual acceptance before final closeout. |

## 3. P3-W1 - Source Support Policy Bridge

| Field | Value |
| --- | --- |
| Capability IDs | QAG-001, DDD-004, CTX-002 as gap-sensitive dependency |
| Goal | Ensure source support classification lives in pure domain policy and is consumed through compatibility bridge. |
| Current evidence | `SourceSupportPolicy` defines `SourceSupportLevel`, `SourceSupportDecision`, and deterministic classification. `canonical_evidence.py` and `question_generation_service.py` call it. |
| Allowed files | `apps/api/app/domain/polish/policies/source_support_policy.py`, `apps/api/app/domain/polish/policies/__init__.py`, `apps/api/app/domain/polish/__init__.py`, `apps/api/app/application/polish/canonical_evidence.py`, `apps/api/app/application/polish/question_generation_service.py`, `tests/domain/polish/test_source_support_policy.py`, `tests/api/test_polish_question_refactor_phase1.py`, `tests/architecture/**`, `docs/goals/**` |
| Forbidden files | Prompt assets, provider / infrastructure, DB, API routes, Agent runtime, frontend |
| Behavior change allowed | Minimal deterministic preservation only |
| Prompt/schema/provider change allowed | No |
| DB schema change allowed | No |
| Validation commands | `python -m compileall apps/api/app/domain/polish apps/api/app/application/polish`; `pytest tests/api/test_polish_question_refactor_phase1.py -q`; `pytest tests/architecture -q`; add/run `tests/domain/polish/test_source_support_policy.py` only if a repair window is authorized |
| Done criteria | Pure policy exists; direct / adjacent / job gap / insufficient cases covered; CTX-002 status remains honest |
| Rollback | Revert P3-W1 repair files only; keep existing P3-W1 evidence if no code repair is performed |
| Stop conditions | Full `SourceSupportSummary` requires API / prompt / provider / DB changes; controller has not authorized CTX-002 repair |

## 4. P3-W2 - Question Grounding and Follow-up Policies

| Field | Value |
| --- | --- |
| Capability IDs | QAG-002, QAG-003, DDD-004 |
| Goal | Move question grounding and follow-up coverage decisions into pure domain policies. |
| Current evidence | `QuestionGroundingPolicy` and `FollowUpCoveragePolicy` now own main grounding and follow-up focus decisions; `question_grounding.py` and `use_cases.py` act as adapters for the main generation path. `question_metadata.py` still contains a legacy helper because it was not in the allowed write set. |
| Allowed files | `apps/api/app/domain/polish/policies/question_grounding_policy.py`, `apps/api/app/domain/polish/policies/follow_up_coverage_policy.py`, `apps/api/app/domain/polish/policies/__init__.py`, adapters in `question_grounding.py`, `question_generation_service.py`, `question_application_service.py`, `use_cases.py`, domain/API/architecture tests, `docs/goals/**` |
| Forbidden files | `question_generation_prompts.py`, provider / infrastructure, DB, API routes, Agent runtime, frontend |
| Behavior change allowed | Only documented guardrails that prevent unsafe factual claims or repeated follow-up focus |
| Prompt/schema/provider change allowed | No |
| DB schema change allowed | No |
| Validation commands | `python -m compileall apps/api/app/domain/polish apps/api/app/application/polish`; `pytest tests/domain/polish/test_question_grounding_policy.py -q`; `pytest tests/domain/polish/test_follow_up_coverage_policy.py -q`; `pytest tests/api/test_polish_question_refactor_phase1.py -q`; `pytest tests/architecture -q` |
| Done criteria | Met for main generation path with explicit residuals: policies are pure, `question_grounding.py` is a thin adapter, `use_cases.py` maps follow-up payload into domain input, and tests cover direct / adjacent / job gap / insufficient plus follow-up repetition / completed-focus blocking. |
| Rollback | Revert new policy files and adapters; restore old application-level behavior |
| Stop conditions | Prompt rewrite, provider payload change, API contract change, DB change, or Agent runtime change is needed |

## 5. P3-W3 - Feedback Review Policies

| Field | Value |
| --- | --- |
| Capability IDs | FAG-002, FAG-003, FAG-004, DDD-004 |
| Goal | Move asset consistency, answer coverage, and answer change review rules into pure domain policies. |
| Current evidence | P3-W3 now adds pure `AssetConsistencyPolicy`, `AnswerCoveragePolicy`, and `AnswerChangePolicy`; `feedback_rules.py` owns context extraction, legacy payload mapping, feedback cards, and P3-W4 next-action bridge only. |
| Allowed files | `asset_consistency_policy.py`, `answer_coverage_policy.py`, `answer_change_policy.py`, `policies/__init__.py`, adapter use in `feedback_rules.py`, `feedback_generation_service.py`, `feedback_application_service.py`, domain/API/architecture tests, `docs/goals/**` |
| Forbidden files | `feedback_prompt_assets.py`, `question_generation_prompts.py`, provider / infrastructure, DB, API routes, Agent runtime, frontend |
| Behavior change allowed | Only to preserve or make explicit existing deterministic guardrails |
| Prompt/schema/provider change allowed | No |
| DB schema change allowed | No |
| Validation commands | `python -m compileall apps/api/app/domain/polish apps/api/app/application/polish`; `pytest tests/domain/polish/test_asset_consistency_policy.py -q`; `pytest tests/domain/polish/test_answer_coverage_policy.py -q`; `pytest tests/domain/polish/test_answer_change_policy.py -q`; `pytest tests/api -k "feedback and polish" -q`; `pytest tests/architecture -q` |
| Done criteria | Met for P3-W3: three pure policies exist; domain tests cover conflict / new fact / insufficient asset context, full / partial / missing coverage, and first-attempt / mixed / regressed history; feedback API regression preserves legacy payload behavior. |
| Rollback | Revert new policies and feedback adapter changes |
| Stop conditions | Provider prompt output, generated schema, storage, task status, or API shape must change |

## 6. P3-W4 - Feedback Next Action Policy

| Field | Value |
| --- | --- |
| Capability IDs | FAG-005, DDD-004 |
| Goal | Move feedback next-action decisions into pure domain policy. |
| Current evidence | P3-W4 now adds pure `FeedbackNextActionPolicy`; `feedback_rules.py` owns legacy payload mapping and calls the policy; `feedback_validation.py` still rejects unsafe next question with unresolved feedback. |
| Allowed files | `feedback_next_action_policy.py`, `policies/__init__.py`, adapter use in `feedback_rules.py`, `feedback_generation_service.py`, `feedback_application_service.py`, domain/API/architecture tests, `docs/goals/**` |
| Forbidden files | Prompt assets, provider / infrastructure, DB, API routes, Agent runtime, frontend |
| Behavior change allowed | Only existing documented blocking / HITL semantics |
| Prompt/schema/provider change allowed | No |
| DB schema change allowed | No |
| Validation commands | `python -m compileall apps/api/app/domain/polish apps/api/app/application/polish`; `pytest tests/domain/polish/test_feedback_next_action_policy.py -q`; `pytest tests/api -k "feedback and next_action" -q`; `pytest tests/api -k "asset_consistency or asset conflict" -q`; `pytest tests/architecture -q` |
| Done criteria | Met for generated feedback payloads: asset conflict blocks next question; asset update candidates require confirmation; provider / validation failure is covered as fail-closed in policy-level tests and remains fail-closed in service/runtime tests; `feedback_rules.py` is the adapter. |
| Rollback | Revert next-action policy and adapter changes |
| Stop conditions | API action enum / schema changes or formal asset / weakness / training writes are required |

## 7. P3-W5 - Application Bridge and Boundary Tests

| Field | Value |
| --- | --- |
| Capability IDs | DDD-004, QAG-001, QAG-002, QAG-003, FAG-002, FAG-003, FAG-004, FAG-005 |
| Goal | Ensure application services orchestrate policies and boundary tests prevent drift. |
| Current evidence | P3-W5 enhanced `tests/architecture/test_domain_polish_policy_boundary.py` to assert Phase 3 policy files, application bridge imports, policy entrypoint calls, and thin adapter forbidden imports. |
| Allowed files | Application adapters in polish modules, `apps/api/app/domain/polish/policies/**`, `tests/architecture/**`, `tests/domain/polish/**`, targeted API tests, `docs/goals/**` |
| Forbidden files | Prompt assets, provider / infrastructure, DB, API routes, Agent runtime, frontend |
| Behavior change allowed | No external behavior change |
| Prompt/schema/provider change allowed | No |
| DB schema change allowed | No |
| Validation commands | `python -m compileall apps/api/app/domain/polish apps/api/app/application/polish`; `pytest tests/domain/polish -q`; `pytest tests/architecture -q`; `pytest tests/api/test_polish_question_refactor_phase1.py -q`; `pytest tests/api -k "feedback and polish" -q`; `rg -n "from app\\.infrastructure|import app\\.infrastructure|FastAPI|sqlalchemy|openai|anthropic|Prompt|prompt" apps/api/app/domain/polish || true` |
| Done criteria | Met for bridge / boundary hardening: architecture tests pass, application bridges import and call domain policies, thin adapters are guarded from prompt/provider/DB/API/runtime drift, and CTX-002 remains explicit deferred gap. |
| Rollback | Revert bridge / test changes from this window only |
| Stop conditions | Broad cleanup or unrelated refactor is needed to pass |

## 8. P3-W6 - Closeout and Backfill

| Field | Value |
| --- | --- |
| Capability IDs | DDD-004, QAG-001, QAG-002, QAG-003, FAG-002, FAG-003, FAG-004, FAG-005, WIN-001, SRC-001 |
| Goal | Produce final Phase 3 status, validation evidence, scope audit, and deferred gap register. |
| Current evidence | P3-W6 closeout assessment and gap register are updated post-P3-W5; P3-W1 source support remains partial with deferred gap; Phase 2 closeout evidence, SRC-001, and CTX-002 / `SourceSupportSummary` remain open and block final closeout unless backfilled or explicitly accepted as final residual. |
| Allowed files | `docs/goals/**`, registered docs / markdown backfill only if authorized |
| Forbidden files | Implementation files unless controller explicitly opens a repair window |
| Behavior change allowed | No |
| Prompt/schema/provider change allowed | No |
| DB schema change allowed | No |
| Validation commands | `git diff --name-only`; `git diff --stat`; `python -m compileall apps/api/app/domain/polish apps/api/app/application/polish`; `pytest tests/domain/polish -q`; `pytest tests/architecture -q`; `pytest tests/api/test_polish_question_refactor_phase1.py -q`; `pytest tests/api -k "feedback and polish" -q` |
| Done criteria | Met for blocked closeout assessment: capability statuses are honest, deferred gaps are explicit, and impossible / blocked source backfill files are listed. Final closeout remains blocked. |
| Rollback | Revert docs closeout/backfill changes |
| Stop conditions | Any capability is claimed done without code + tests + source evidence |

## 9. Global Stop Conditions

Stop and return to controller if:

- A window requires modifying prompt assets, provider behavior, DB schema, API contract, Agent runtime, LangGraph runtime, or frontend.
- A domain policy would need DB, LLM, FastAPI, infrastructure, provider SDKs, or prompt builders.
- A candidate / suggestion would need to become a formal business fact without Application Service + Domain Policy + Handoff.
- SourceSupportSummary or CTX-002 would be falsely closed without full object, payload propagation, and tests.
- Existing Phase 2 missing closeout evidence blocks the controller's desired sequencing.

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
| P3-W3 | `not_started_for_domain_policy` | Feedback asset consistency, answer coverage, and answer change logic remain in `feedback_rules.py`; API tests and deterministic evals exist. | Extract three feedback review policies while preserving behavior. |
| P3-W4 | `not_started_for_domain_policy` | Feedback next-action rewrite remains in `feedback_rules.py`; validation gate rejects unsafe next question in `feedback_validation.py`. | Extract next-action policy and candidate confirmation semantics. |
| P3-W5 | `partial_boundary_support` | `tests/architecture/test_domain_polish_policy_boundary.py` exists; `tests/domain/polish/` now contains P3-W2 question policy tests; feedback policy domain tests remain future-window work. | Strengthen boundary / adapter tests as P3-W3 and P3-W4 policies are extracted. |
| P3-W6 | `not_started` | Phase 3 final closeout cannot run while feedback policies remain unextracted and Phase 2 / SRC-001 / CTX-002 deferred gaps remain open; QAG-002 / QAG-003 are implemented for the main path with explicit residuals. | Produce closeout only after implementation windows and validations pass, or record explicit deferred gaps. |

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
| Current evidence | `feedback_rules.py` owns confirmed-only asset checks, archived exclusion, technology / metric / timeline / responsibility conflicts, expected point coverage, prior answer comparison, and feedback card generation. |
| Allowed files | `asset_consistency_policy.py`, `answer_coverage_policy.py`, `answer_change_policy.py`, `policies/__init__.py`, adapter use in `feedback_rules.py`, `feedback_generation_service.py`, `feedback_application_service.py`, domain/API/architecture tests, `docs/goals/**` |
| Forbidden files | `feedback_prompt_assets.py`, `question_generation_prompts.py`, provider / infrastructure, DB, API routes, Agent runtime, frontend |
| Behavior change allowed | Only to preserve or make explicit existing deterministic guardrails |
| Prompt/schema/provider change allowed | No |
| DB schema change allowed | No |
| Validation commands | `python -m compileall apps/api/app/domain/polish apps/api/app/application/polish`; `pytest tests/domain/polish/test_asset_consistency_policy.py -q`; `pytest tests/domain/polish/test_answer_coverage_policy.py -q`; `pytest tests/domain/polish/test_answer_change_policy.py -q`; `pytest tests/api -k "feedback and polish" -q`; `pytest tests/architecture -q` |
| Done criteria | Three pure policies exist; tests cover conflict / new fact / archived exclusion, full / partial / missing coverage, and improved / regressed / unchanged / insufficient history |
| Rollback | Revert new policies and feedback adapter changes |
| Stop conditions | Provider prompt output, generated schema, storage, task status, or API shape must change |

## 6. P3-W4 - Feedback Next Action Policy

| Field | Value |
| --- | --- |
| Capability IDs | FAG-005, DDD-004 |
| Goal | Move feedback next-action decisions into pure domain policy. |
| Current evidence | `feedback_rules.py` removes `generate_next_question` on asset conflict or unresolved coverage and adds deterministic alternatives. `feedback_validation.py` rejects unsafe next question with unresolved feedback. |
| Allowed files | `feedback_next_action_policy.py`, `policies/__init__.py`, adapter use in `feedback_rules.py`, `feedback_generation_service.py`, `feedback_application_service.py`, domain/API/architecture tests, `docs/goals/**` |
| Forbidden files | Prompt assets, provider / infrastructure, DB, API routes, Agent runtime, frontend |
| Behavior change allowed | Only existing documented blocking / HITL semantics |
| Prompt/schema/provider change allowed | No |
| DB schema change allowed | No |
| Validation commands | `python -m compileall apps/api/app/domain/polish apps/api/app/application/polish`; `pytest tests/domain/polish/test_feedback_next_action_policy.py -q`; `pytest tests/api -k "feedback and next_action" -q`; `pytest tests/api -k "asset_consistency or asset conflict" -q`; `pytest tests/architecture -q` |
| Done criteria | Asset conflict blocks next question; asset update candidates require confirmation; provider / validation failure is not represented as success; old module is adapter or explicit gap |
| Rollback | Revert next-action policy and adapter changes |
| Stop conditions | API action enum / schema changes or formal asset / weakness / training writes are required |

## 7. P3-W5 - Application Bridge and Boundary Tests

| Field | Value |
| --- | --- |
| Capability IDs | DDD-004, QAG-001, QAG-002, QAG-003, FAG-002, FAG-003, FAG-004, FAG-005 |
| Goal | Ensure application services orchestrate policies and boundary tests prevent drift. |
| Current evidence | Domain policy boundary test exists; domain policy test directory is missing; application modules still carry policy-like logic before W2-W4. |
| Allowed files | Application adapters in polish modules, `apps/api/app/domain/polish/policies/**`, `tests/architecture/**`, `tests/domain/polish/**`, targeted API tests, `docs/goals/**` |
| Forbidden files | Prompt assets, provider / infrastructure, DB, API routes, Agent runtime, frontend |
| Behavior change allowed | No external behavior change |
| Prompt/schema/provider change allowed | No |
| DB schema change allowed | No |
| Validation commands | `python -m compileall apps/api/app/domain/polish apps/api/app/application/polish`; `pytest tests/domain/polish -q`; `pytest tests/architecture -q`; `pytest tests/api/test_polish_question_refactor_phase1.py -q`; `pytest tests/api -k "feedback and polish" -q`; `rg -n "from app\\.infrastructure|import app\\.infrastructure|FastAPI|sqlalchemy|openai|anthropic|Prompt|prompt" apps/api/app/domain/polish || true` |
| Done criteria | Boundary tests pass; application modules call policies; remaining legacy policy logic is explicitly deferred |
| Rollback | Revert bridge / test changes from this window only |
| Stop conditions | Broad cleanup or unrelated refactor is needed to pass |

## 8. P3-W6 - Closeout and Backfill

| Field | Value |
| --- | --- |
| Capability IDs | DDD-004, QAG-001, QAG-002, QAG-003, FAG-002, FAG-003, FAG-004, FAG-005, WIN-001, SRC-001 |
| Goal | Produce final Phase 3 status, validation evidence, scope audit, and deferred gap register. |
| Current evidence | Not ready: only P3-W1 source support is partial; other policy windows remain open. |
| Allowed files | `docs/goals/**`, registered docs / markdown backfill only if authorized |
| Forbidden files | Implementation files unless controller explicitly opens a repair window |
| Behavior change allowed | No |
| Prompt/schema/provider change allowed | No |
| DB schema change allowed | No |
| Validation commands | `git diff --name-only`; `git diff --stat`; `python -m compileall apps/api/app/domain/polish apps/api/app/application/polish`; `pytest tests/domain/polish -q`; `pytest tests/architecture -q`; `pytest tests/api/test_polish_question_refactor_phase1.py -q`; `pytest tests/api -k "feedback and polish" -q` |
| Done criteria | Capability statuses are honest; deferred gaps explicit; source backfill complete or impossible files listed |
| Rollback | Revert docs closeout/backfill changes |
| Stop conditions | Any capability is claimed done without code + tests + source evidence |

## 9. Global Stop Conditions

Stop and return to controller if:

- A window requires modifying prompt assets, provider behavior, DB schema, API contract, Agent runtime, LangGraph runtime, or frontend.
- A domain policy would need DB, LLM, FastAPI, infrastructure, provider SDKs, or prompt builders.
- A candidate / suggestion would need to become a formal business fact without Application Service + Domain Policy + Handoff.
- SourceSupportSummary or CTX-002 would be marked complete without full object, payload propagation, and tests.
- Existing Phase 2 missing closeout evidence blocks the controller's desired sequencing.

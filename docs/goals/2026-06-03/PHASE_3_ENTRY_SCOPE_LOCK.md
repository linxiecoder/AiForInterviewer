---
title: PHASE_3_ENTRY_SCOPE_LOCK
type: scope-lock-candidate
status: proposed
owner: P2-W6-SOURCE-BACKFILL-CLOSEOUT
permalink: ai-for-interviewer/docs/goals/2026-06-03/phase-3-entry-scope-lock
---

# Phase 3 Entry Scope Lock Candidate

本文件只是 Phase 3 entry candidate，不授权启动 Phase 3。Phase 3 必须由 owner 明确确认后才能执行。

## 1. Candidate Scope

| Item | Value |
| --- | --- |
| Candidate phase | Phase 3 - Domain Policies |
| Source label | `GOAL_SOURCE` / `INFERENCE` |
| Required owner action | Confirm Phase 3 start and allowed files before any patch. |
| Behavior change | Policy extraction / compatibility only after explicit approval. |
| Prompt/provider/DB/API change | Forbidden unless owner grants a separate scope. |
| Runtime migration | Forbidden in Phase 3 candidate. |

## 2. Candidate Policy Areas

- Source support policy.
- Grounding policy.
- Follow-up coverage policy.
- Asset consistency policy.
- Answer coverage policy.
- Answer change policy.
- Next action policy.

## 3. Candidate Allowed Scope

Exact files must be re-locked before work starts. Candidate areas:

- `apps/api/app/application/polish/context/**`
- `apps/api/app/application/polish/question_grounding.py`
- `apps/api/app/application/polish/feedback_rules.py`
- `apps/api/app/application/polish/question_metadata.py`
- focused tests under `tests/api/**`
- architecture tests under `tests/architecture/**`
- Phase 3 evidence docs under `docs/goals/2026-06-03/**`

## 4. Candidate Forbidden Scope

- `apps/api/app/application/polish/question_generation_prompts.py`
- `apps/api/app/application/polish/feedback_prompt_assets.py`
- `apps/api/app/infrastructure/llm/**`
- `apps/api/app/infrastructure/db/**`
- `apps/api/app/api/v1/**`
- DB migrations
- LangGraph / Agent runtime migration
- direct formal writes from Agent or context layer
- treating current answer facts as confirmed canonical assets

## 5. Entry Gates

- Phase 2 code/test windows remain validated.
- Phase 2 source pack backfill gap is either resolved or explicitly accepted as deferred by owner.
- Phase 3 policy boundaries are scoped before editing.
- Existing prompt/provider behavior is protected by tests or explicit no-touch audit.

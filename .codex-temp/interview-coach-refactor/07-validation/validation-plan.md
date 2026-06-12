---
title: Validation Plan
type: validation-plan
status: active
round: Round 3.5-E
updated: 2026-06-12
---

# Validation Plan

Round 3.5-E 是 documentation-only deep gap analysis correction。本轮不运行自动化测试，也不声称测试通过。自动化验证必须等 GPT Project 审计批准进入未来实现轮后执行。

## Current Round Validation

| Validation | Status | Evidence |
|---|---|---|
| Governance/doc read | Done | `AGENTS.md`, `docs/00-governance/DOCS_INDEX.md`, `.codex-temp/interview-coach-refactor/**` required docs read-only inspected |
| Production code inspection | Done, read-only | G-001 `As-Is Code Behavior` lists API/use case/repository/model/prompt/provider/frontend evidence |
| Production code changed | No | Documentation-only round |
| Production tests changed | No | Documentation-only round |
| Automated tests run | No | Not run by design in Round 3.5-E |

## G-001 Test Matrix Summary

| Test ID | Gap ID | 行为 | 测试类型 | 测试文件 | 断言 | 未来命令 |
|---|---|---|---|---|---|---|
| T-001 | GAP-001 | reopen restores continuity status | backend API test | `tests/api/test_polish_api.py` | response includes optional continuity status/summary/restored refs and old fields remain | `.venv/bin/python -m pytest tests/api/test_polish_api.py -k "session_detail or continuity"` |
| T-002 | GAP-002 | legacy missing metadata readable | backend API test | `tests/api/test_polish_api.py` | missing progress/question metadata does not crash and falls back to `partial`/`unknown` | `.venv/bin/python -m pytest tests/api/test_polish_api.py -k "legacy or malformed or continuity"` |
| T-003 | GAP-003 | progress refresh fallback distinguishable | backend service/API test | `tests/api/test_polish_api.py` | `refresh_failed`/insufficient context maps to non-ready continuity and does not silently overwrite readable state | `.venv/bin/python -m pytest tests/api/test_polish_api.py -k "progress_tree_refresh"` |
| T-004 | GAP-004 | bounded context used | backend service test | `tests/api/test_polish_feedback_generation_service.py`, `tests/api/test_polish_api.py` | provider request receives bounded safe context only | `.venv/bin/python -m pytest tests/api/test_polish_feedback_generation_service.py tests/api/test_polish_api.py -k "bounded or provider_request or prompt"` |
| T-005 | GAP-005 | safe metadata exposed only as allowed | backend/schema test | `tests/api/test_polish_feedback_generation_service.py`, `tests/api/test_polish_feedback_validation.py` | safe metadata present, raw prompt absent | `.venv/bin/python -m pytest tests/api/test_polish_feedback_generation_service.py tests/api/test_polish_feedback_validation.py -k "metadata or unsafe or provider"` |
| T-006 | GAP-006 | provider payload not exposed | backend/frontend test | `tests/api/test_polish_api.py`, `apps/web/src/pages/interview/InterviewPage.test.ts` | no provider payload in API/frontend serialized data | `.venv/bin/python -m pytest tests/api/test_polish_api.py -k "provider_payload or raw_prompt"` and `npm run web:test` |
| T-007 | GAP-007 | frontend handles optional fields | frontend test/build | `apps/web/src/pages/interview/InterviewPage.test.ts`, `apps/web/src/entities/polish/model/types.ts` | missing optional fields do not break UI | `npm run web:test` and `npm run web:build` |

## Existing Tests To Extend

| Area | Existing files/tests | Needed in future approved implementation round |
|---|---|---|
| Session detail / legacy | `tests/api/test_polish_api.py::test_create_and_get_polish_session_persists_owner_scoped_context`, `test_get_polish_session_does_not_regenerate_progress_tree`, `test_polish_session_detail_returns_empty_metadata_for_legacy_or_malformed_questions`, `test_polish_session_keeps_old_feedback_payload_compatible` | Add optional continuity field assertions and legacy partial/unknown assertions |
| Progress refresh | `tests/api/test_polish_api.py` progress refresh tests | Add stale/partial/unknown continuity mapping assertions |
| Feedback context safety | `tests/api/test_polish_feedback_generation_service.py`, `tests/api/test_polish_feedback_validation.py` | Add safe metadata and no raw/provider payload assertions |
| Frontend optional rendering | `apps/web/src/pages/interview/InterviewPage.test.ts` | Add missing-field fallback and optional metadata rendering/type assertions |

## Commands Required In Future Implementation Round

```bash
.venv/bin/python -m pytest tests/api/test_polish_api.py -k "session_detail or continuity or legacy or progress_tree_refresh"
.venv/bin/python -m pytest tests/api/test_polish_feedback_generation_service.py tests/api/test_polish_feedback_validation.py -k "metadata or unsafe or provider or bounded"
npm run web:test
npm run web:build
git status --short --untracked-files=all
git diff --stat
git diff --name-only
git status -- AGENTS.md
git diff -- AGENTS.md
```

## Readiness Gate

| Gate | Decision |
|---|---|
| G-001 design package | Ready for GPT Project audit |
| Implementation approval | Not approved in Round 3.5-E |
| Automated verification | Pending future implementation round |

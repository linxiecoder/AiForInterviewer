---
title: Design Decisions
type: decisions
status: active
round: Round 3.5-E
updated: 2026-06-12
---

# Design Decisions

本文件记录 Round 3.5-E 对 G-001 的关键边界决策。完整证据和 Gap Matrix 留在 G-001 目标文件。

## G-001 Decisions

| Decision ID | Decision | Reason | Impacted files/functions | Status |
|---|---|---|---|---|
| G001-D-001 | No DB migration | Session continuity 可从现有 `PolishSessionDetail`, turns, progress plan/state 和 refs 推导；context hygiene 可落到现有 question metadata / feedback payload metadata | `apps/api/app/infrastructure/db/models/interview.py::PolishSessionDetail`, `apps/api/app/infrastructure/db/models/polish.py::Question`, `Feedback`; `apps/api/app/api/v1/polish.py::_session_response` | Confirmed for design audit |
| G001-D-002 | No new endpoint | Reopen 已有 `GET /polish-sessions/{session_id}`；progress refresh 已有 `/progress-tree/state`；G-001 只扩展 backward-compatible optional response metadata | `apps/api/app/api/v1/polish.py::get_polish_session`, `refresh_polish_progress_tree_state` | Confirmed for design audit |
| G001-D-003 | No provider-facing output schema change | Context hygiene 是 API/internal safe metadata；provider request builders 已有 bounded context，provider-facing output schema 不变 | `apps/api/app/application/polish/question_generation_prompts.py::build_question_provider_request`, `apps/api/app/application/polish/feedback_prompt_assets.py::_provider_compact_prompt` | Confirmed for design audit |
| G001-D-004 | No raw prompt exposure | Existing LLM boundary forbids raw prompt/system/developer/completion/full source keys；G-001 new metadata must keep same forbidden content boundary | `apps/api/app/application/llm/types.py::P7_PROVIDER_FORBIDDEN_KEYS`, `apps/api/app/application/llm/provider_boundary.py::ProviderRequestValidator`, `apps/api/app/api/v1/polish.py::FORBIDDEN_FEEDBACK_PAYLOAD_RESPONSE_KEYS` | Confirmed for design audit |
| G001-D-005 | No provider payload exposure | Provider payload remains blocked by transport/request validator and API sanitizer; frontend receives only safe response metadata | `apps/api/app/application/llm/types.py::LlmTransportRequest`, `apps/api/app/api/v1/polish.py::_drop_forbidden_feedback_payload_response_keys`, `apps/web/src/entities/polish/model/types.ts` | Confirmed for design audit |
| G001-D-006 | Optional backward-compatible metadata only | Legacy sessions and current frontend rendering must remain readable; missing new fields fall back to existing progress/turn/current-ref behavior | `apps/api/app/api/v1/polish.py::_session_response`, `apps/api/app/schemas/polish.py::PolishSessionResponse`, `apps/web/src/entities/polish/model/types.ts::PolishSessionDetail`, `apps/web/src/pages/interview/InterviewPage.tsx` | Confirmed for design audit |

## Non-Decisions

| Item | Result |
|---|---|
| G-002 implementation | Not in Round 3.5-E |
| Storybank | Not in G-001 |
| Transcript ingestion | Not in G-001 |
| Command routing | Research-only/Reject source pattern; not implemented |
| Active doc migration | Not in this round |

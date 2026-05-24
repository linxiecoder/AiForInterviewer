---
title: Frontend LangGraph UI Plan
type: delivery-planning
status: draft-f5-langgraph-implementation-consolidation
owner: 前端架构 / 产品设计
permalink: ai-for-interviewer/docs/03-delivery/refactor-multiagent-langgraph-implementation/frontend-langgraph-ui-plan
---

# Frontend LangGraph UI Plan

## 1. 文档目的

本文是前端 LangGraph / AI Runtime UI 计划的唯一位置。它覆盖 route、API client、DTO、polling、timeline、interrupt resume、candidate confirmation、report/review states、copy boundary 和前端测试。

## 2. Frontend boundaries

| Boundary | Rule |
|---|---|
| no debug page | 不新增普通用户 Agent debug page |
| sanitized only | UI 只展示 sanitized task status、timeline、interrupt summary、candidate refs、LLM summary |
| no raw internals | 不展示 AgentState、checkpoint payload、raw prompt、raw completion、provider payload |
| no export | 报告/复盘只提供 copy boundary，不提供文件导出/下载 |
| candidate/formal | candidate confirmation requires explicit user action |
| default polling | PR7 默认 polling；streaming 需要独立受权和测试 |

## 3. Route and surface plan

| Surface | Route | Files | Entry | Rule |
|---|---|---|---|---|
| AI task status | no standalone route | `features/ai-task-status/**`, `widgets/task-status-panel/**` | embedded in report/review/job match/interview surfaces | no Agent debug page |
| Agent timeline | no standalone route | `widgets/agent-run-timeline/**` | task status panel expands timeline | sanitized timeline only |
| Report detail | `/interview/:session_id` drawer; review can open associated report drawer | `widgets/report-viewer/**`, `widgets/copy-boundary/**` | interview list/detail/workbench/pressure completed state | no first-level report list |
| Review list | `/review` | `pages/review/ReviewPage.tsx` | AppShell navigation | adds route when PR7/PR8 authorized |
| Review detail | `/review` drawer or route state | `widgets/review-viewer/**` | review row, generation completion, report entry | drawer, not standalone detail page |
| Real review input | `/review` drawer | `features/review-generation/RealReviewInputDrawer.tsx` | review list add action | saving input does not create AI task |
| Candidate confirmation | no standalone route | `features/candidate-confirmation/**` | report/review/feedback/training surfaces | no silent formal write |
| Interrupt resume | no standalone route | `features/agent-interrupt-resume/**` | task panel or interrupt timeline event | approve/edit/reject via resume API |

## 4. API client / DTO plan

| File | Symbol | API | Assertions |
|---|---|---|---|
| `entities/ai-task/model/types.ts` | `AiTaskStatus`, `AiTaskStatusResponse` | `GET /api/v1/ai-tasks/{ai_task_id}` | covers queued/running/succeeded/partial/low_confidence/validation_failed/source_unavailable/generation_failed/timed_out/cancelled |
| `entities/ai-task/api/aiTaskApi.ts` | `getAiTask`, `retryAiTask`, `cancelAiTask` | AI task endpoints | uses shared envelope and propagates `ApiHttpError` |
| `entities/agent-run/model/types.ts` | `AgentRunSummaryResponse`, `AgentTimelineEvent` | Agent runtime API | excludes AgentState, checkpoint, Prompt, completion, provider payload |
| `entities/agent-run/api/agentRunApi.ts` | `getAgentRun`, `getAgentRunTimeline`, `resumeInterrupt` | status/timeline/resume endpoints | path encode, idempotency header, 422/409 mapping |
| `entities/report/api/reportApi.ts` | `createReportTask`, `getReport`, `getReportCopyContent`, `recordReportCopyEvent` | report endpoints | copy only; no export artifact |
| `entities/review/api/reviewApi.ts` | `listReviews`, `createMockReviewTask`, `createRealReviewInput`, `createRealReviewTask`, `getReview`, `getReviewCopyContent` | review endpoints | real input save no LLM task |
| `entities/candidate/api/candidateApi.ts` | `saveCandidateCorrection`, `confirmDepositTarget` | candidate / deposit endpoints | confirmation required |

## 5. Common AI task state machine

| State | Enter condition | API action | UI | Exit |
|---|---|---|---|---|
| `idle` | no `ai_task_id` | none | show generate entry or empty state | user creates task |
| `accepted` | create returns 202 | start polling | accepted badge | queued/running |
| `queued` | task queued | polling | skeleton; no fake result | running or terminal |
| `running` | task running | polling | generation in progress | terminal or interrupted |
| `interrupted` | task/run has interrupt ref | stop task polling; fetch timeline | interrupt panel | resume -> accepted |
| `partial` | terminal partial | stop polling | partial banner and available sections | retry or accept partial read |
| `low_confidence` | terminal low confidence | stop polling | low confidence banner and review entry | correction / retry / manual review |
| `validation_failed` | terminal validation failed or 422 | stop polling | validation panel; preserve input | edit / retry |
| `failed` | generation failed / timeout / provider unavailable | stop polling | error panel, retry if safe | retry -> accepted |
| `succeeded` | result ref available | stop polling | load business result and open detail | detail loaded |
| `cancelled` | cancel success | stop polling | cancelled state | restart if user chooses |

默认 polling 间隔为 `2000ms`。进入 terminal status、页面隐藏、组件卸载或路由离开时必须停止 polling。

## 6. Report / review UI states

| Surface | User action | API | State transition | UI assertion |
|---|---|---|---|---|
| report generation | click generate report | `POST /api/v1/reports` then task polling | idle -> accepted -> queued/running -> terminal | opens report drawer only after result ref |
| report copy | click copy | `GET /copy-content`, `POST /copy-events` | copy_idle -> copying -> copied/failed | no file name, download URL or export artifact |
| review list | enter `/review` | `GET /api/v1/reviews` | loading -> list_loaded/empty/error | row status covers generating/available/partial/low_confidence/failed/source_unavailable |
| mock review | select system session/report | `POST /api/v1/reviews/mock` then task polling | idle -> accepted -> terminal | candidate refs are pending confirmation |
| real input save | submit real interview input | `POST /api/v1/reviews/real-inputs` | editing -> saving -> saved/validation_failed/failed | saving does not create `ai_task_id` |
| real review generation | generate from saved input | `POST /api/v1/reviews/real` then task polling | saved -> accepted -> terminal | no real interview outcome prediction |
| review detail | click review row or generation completion | `GET /api/v1/reviews/{review_id}` | detail_loading -> detail_loaded/partial/low_confidence/failed | content deposit is confirmation, not automatic formal write |

## 7. Interrupt resume UI

| Field | Control | Source | Rule |
|---|---|---|---|
| `action` | segmented control | interrupt schema | approve/edit/reject required |
| `resume_payload` | form object | timeline interrupt summary | edit requires payload; approve/reject may use empty object |
| `base_interrupt_version_ref` | hidden field | interrupt event | stale returns 409 and preserves input |
| `user_message` | textarea | user input | submitted to API; not logged/displayed as raw trace |
| `correction_refs[]` | selected refs | candidate/correction UI | owner scoped |

## 8. Candidate confirmation UI

| Source | Candidate data | Confirmation action | UI rule |
|---|---|---|---|
| AI task result | `candidate_refs[]` / `suggestion_refs[]` | domain confirmation or deposit API | not displayed as formal object |
| Polish feedback | existing polish candidate API | legacy confirm/dismiss until canonical API lands | preserve compatibility |
| Report / Review | report/review candidate refs | candidate / deposit endpoints | confirm/edit/reject/merge are explicit user actions |
| Low confidence correction | correction response | candidate correction + confirmation | correction still requires confirmation |

## 9. Component and hook plan

| File | Name | Inputs | Outputs | States | Tests |
|---|---|---|---|---|---|
| `features/ai-task-status/useAgentTaskStatus.ts` | `useAgentTaskStatus` | `aiTaskId`, `enabled`, `pollIntervalMs` | task/loading/error/refresh/retry/cancel | queued/running/terminal | polling stops terminal |
| `widgets/agent-run-timeline/useAgentRunTimeline.ts` | `useAgentRunTimeline` | `agentRunId`, cursor | events/loading/error/refresh | skeleton/empty/error | no raw payload |
| `features/report-generation/useReportGeneration.ts` | `useReportGeneration` | session/report type | start/task/reportRef | accepted/running/partial/failed | result ref load |
| `features/review-generation/useReviewGeneration.ts` | `useReviewGeneration` | source ref/review type | start/task/reviewRef | mock/real states | low confidence visible |
| `features/agent-interrupt-resume/useAgentInterruptResume.ts` | `useAgentInterruptResume` | run/interrupt refs | approve/edit/reject | submitting/validation/stale | idempotency and stale |
| `features/ai-task-status/AgentTaskStatusBadge.tsx` | status badge | status/retryable/actions | compact status | all statuses | text fits and status clear |
| `widgets/agent-run-timeline/AgentRunTimeline.tsx` | timeline | events/loading/error | sanitized timeline | skeleton/error | forbidden markers absent |
| `shared/ui/LowConfidenceBanner.tsx` | low confidence banner | flags/source availability | warning | visible low confidence | flags visible |
| `shared/ui/ValidationFailedPanel.tsx` | validation panel | validation result/message | repair panel | visible validation | input preserved |
| `widgets/report-viewer/ReportSectionList.tsx` | report sections | sections/score refs/copy state | report view | skeleton/partial | no export UI |
| `widgets/review-viewer/ReviewInsightPanel.tsx` | review insights | review/candidate refs | insight panel | skeleton/low confidence | candidate-only |
| `features/candidate-confirmation/CandidateConfirmationDrawer.tsx` | candidate drawer | candidates/actions | confirmation result | submitting/failed | confirm/edit/reject/merge |
| `features/agent-interrupt-resume/AgentInterruptPanel.tsx` | interrupt panel | interrupt/actions | resume action | submitting/stale | user action audited |
| `widgets/copy-boundary/CopyBoundaryPanel.tsx` | copy boundary | copy content/redaction | copy action | copying/failed | no file export wording |

## 10. Test plan

| Test file | Assertions |
|---|---|
| `entities/ai-task/api/aiTaskApi.test.ts` | envelope handling, path, status enum |
| `entities/agent-run/model/types.test.ts` | no raw runtime fields in timeline event |
| `features/ai-task-status/useAgentTaskStatus.test.tsx` | polling interval, terminal stop, retry |
| `widgets/agent-run-timeline/AgentRunTimeline.test.tsx` | loading/empty/error/events, forbidden markers absent |
| `features/report-generation/useReportGeneration.test.tsx` | accepted -> running -> succeeded with report ref |
| `widgets/report-viewer/ReportSectionList.test.tsx` | partial/low confidence/no export |
| `features/review-generation/useReviewGeneration.test.tsx` | mock and real flows; real input save no AI task |
| `widgets/review-viewer/ReviewInsightPanel.test.tsx` | candidate-only and no outcome prediction |
| `features/agent-interrupt-resume/AgentInterruptPanel.test.tsx` | approve/edit/reject, stale conflict preserves input |
| `features/candidate-confirmation/CandidateConfirmationDrawer.test.tsx` | confirm/edit/reject/merge explicit actions; failure does not mark formal |
| optional E2E smoke | login -> review/task timeline/candidate/copy; no raw payload or export |

## 11. Frontend PR gates

| Gate | Rule |
|---|---|
| PR7 route changes | Only add `/review` if backend/API contract and navigation scope are authorized |
| test dependencies | Vitest/Testing Library/MSW/Playwright changes require explicit PR7 scope |
| streaming | EventSource/SSE requires backend endpoint, shared client wrapper and tests; otherwise polling |
| design | Follow `UX_SPEC.md` / `UI_DESIGN_SYSTEM.md`; no Agent debug UI |
| copy | No export/download UI or wording |

## 12. Non-goals

- 不实现后端逻辑。
- No LangGraph internals in frontend DTOs.
- 不展示 raw prompt、raw completion、provider payload 或 checkpoint payload。
- No file export or download.
- No exact probability or hidden scoring display.

---
title: 前端测试脚本实施计划
type: delivery-planning
status: draft-pr1
owner: 项目交付
permalink: ai-for-interviewer/docs/03-delivery/refactor-multiagent-langgraph/test-plan-frontend
---

# 前端测试脚本实施计划

## 1. 文档目的

本文规划前端 unit、component、hook、API client、page、mocked server 和 optional E2E smoke 测试方法级计划，覆盖 AI Runtime UI、report / review 页面、interrupt resume、candidate confirmation、copy boundary 和所有 AI task 可见状态。

## 2. 输入来源

- `12_FRONTEND_IMPLEMENTATION_PLAN.md`
- active docs：`UX_SPEC.md`、`UI_DESIGN_SYSTEM.md`、`API_SPEC.md`、`APPLICATION_FLOW_SPEC.md`、`SECURITY_PRIVACY.md`
- 当前 `apps/web/src` 测试风格只读盘点
- 当前代码映射：现有测试包括 `InterviewPage.test.ts`、`JobMatchPanel.test.tsx`、`AppShell.test.ts`、`navigation.test.ts`；`shared/api/client.ts` 已校验 `request_id` / `trace_id`；当前测试依赖以 TypeScript / 局部组件测试为主。

## 3. 当前状态

当前前端测试主要依赖 TypeScript 编译与局部 `.test.ts(x)` 契约骨架。PR1 不新增测试依赖；PR7 若引入 Vitest/Testing Library/MSW/Playwright，必须单独授权。

## 4. 目标输出

为 PR7/PR8 提供目标测试文件骨架，覆盖：

- task status polling。
- graph run timeline。
- report generation pending / success / partial / failed。
- review generation pending / success / low_confidence。
- interrupt approval / edit / reject。
- candidate confirmation。
- low confidence display。
- validation failed display。
- copy boundary behavior。

## 5. 必须覆盖范围

### 5.1 API client / DTO tests

| Target file | Test method | Mocked API response | Act | Expected assertions | PR |
|---|---|---|---|---|---|
| `apps/web/src/entities/ai-task/model/types.test.ts` | `testAiTaskStatusTerminalHelpersCoverAllApiStates` | no network; statuses array includes `queued/running/succeeded/partial/low_confidence/validation_failed/source_unavailable/generation_failed/timed_out/cancelled` | call helpers `isTerminalAiTaskStatus`, `isRetryableAiTaskStatus` | terminal excludes `queued/running`; `partial/low_confidence/validation_failed/failed` are not treated as success | PR7 |
| `apps/web/src/entities/ai-task/model/types.test.ts` | `testAiTaskStatusResponseTypeDoesNotContainRawRuntimeFields` | object with legal fields | serialize keys | no `prompt`, `completion`, `provider_payload`, `checkpoint`, `agent_state` keys in exported type fixture | PR7 |
| `apps/web/src/entities/ai-task/api/aiTaskApi.test.ts` | `testGetAiTaskUsesEnvelopeAndAiTaskPath` | 200 envelope `{request_id, trace_id, status:"running", resource_type:"ai_task", data:{ai_task_id:"ait_1", status:"running"}}` | call `getAiTask("ait_1")` with fetch mock | requested `/ai-tasks/ait_1`; returns data; preserves `request_id` / `trace_id` through shared client contract | PR7 |
| `apps/web/src/entities/ai-task/api/aiTaskApi.test.ts` | `testGetAiTaskMapsValidationAndOwnerErrors` | 422 `validation_failed`; 404 `not_found_or_inaccessible` error envelopes | call `getAiTask` | thrown `ApiHttpError.code` matches envelope; no fallback success state | PR7 |
| `apps/web/src/entities/agent-run/model/types.test.ts` | `testAgentTimelineEventAllowsOnlySanitizedFields` | event fixture with `node_key`, `summary`, `safe_trace_refs`, `low_confidence_flags` | serialize fixture | forbidden raw runtime fields absent | PR7 |
| `apps/web/src/entities/agent-run/api/agentRunApi.test.ts` | `testResumeInterruptSendsIdempotencyKeyAndSchemaBody` | 202 envelope with `AiTaskStatusResponse` | call `resumeInterrupt(runId, interruptId, body, {idempotencyKey})` | path is `/agent-runs/{run}/interrupts/{interrupt}/resume`; header `Idempotency-Key` set; body has `action`, `resume_payload`, `base_interrupt_version_ref` | PR7 |

### 5.2 Polling / timeline hook tests

| Target file | Test method | Mocked API response | Act | Expected assertions | PR |
|---|---|---|---|---|---|
| `apps/web/src/features/ai-task-status/useAgentTaskStatus.test.tsx` | `testPollingStartsForQueuedAndStopsOnSucceeded` | sequence: `queued`, `running`, `succeeded` with `result_ref` | render hook with fake timers | calls `getAiTask` until succeeded; clears timer; exposes terminal task | PR7 |
| `apps/web/src/features/ai-task-status/useAgentTaskStatus.test.tsx` | `testPollingStopsAndShowsLowConfidencePartialFailedValidationInterrupted` | terminal fixtures for `low_confidence`, `partial`, `generation_failed`, `validation_failed`; interrupted response has `interrupt_refs` | render hook per state | no state is normalized to success; exposed `uiState` is `low_confidence/partial/failed/validation_failed/interrupted` | PR7 |
| `apps/web/src/features/ai-task-status/useAgentTaskStatus.test.tsx` | `testRetryOnlyCallsApiWhenTaskRetryable` | failed task `retryable=true`, validation failed `retryable=false` | click retry action from hook | retry API called only for retryable task; non-retryable exposes disabled reason | PR7 |
| `apps/web/src/widgets/agent-run-timeline/useAgentRunTimeline.test.ts` | `testTimelineFetchesCursorAndAppendsSanitizedEvents` | first page `events=[node_started]`, `meta.next_cursor="c2"`; second page `node_completed` | call hook refresh and load more | events appended; next cursor stored; forbidden fields ignored | PR7 |
| `apps/web/src/widgets/agent-run-timeline/AgentRunTimeline.test.tsx` | `testTimelineRendersLoadingEmptyErrorAndSanitizedEvents` | component props for loading, empty, error, events | render component states | skeleton visible; empty state visible; retry button visible; event summary visible; no raw payload text visible | PR7 |

### 5.3 Report page / widget tests

| Target file | Test method | Mocked API response | Act | Expected assertions | PR |
|---|---|---|---|---|---|
| `apps/web/src/features/report-generation/useReportGeneration.test.tsx` | `testCreateReportTaskEntersAcceptedThenPollsToReportRef` | `POST /reports` returns 202 `ait_report_1`; polling returns `succeeded` with `result_ref=rep_1` | call `start({report_type:"polish_summary"})` | state transitions `idle -> accepted -> running -> succeeded`; returned report ref stored | PR7/PR8 |
| `apps/web/src/features/report-generation/useReportGeneration.test.tsx` | `testReportGenerationSurfacesPartialFailedValidationFailedLowConfidence` | terminal fixtures for `partial`, `generation_failed`, `validation_failed`, `low_confidence` | start generation per fixture | UI state matches exact terminal; no detail fetch on failed / validation_failed | PR7/PR8 |
| `apps/web/src/widgets/report-viewer/ReportSectionList.test.tsx` | `testReportSectionsRenderPartialAndLowConfidenceWithoutExactProbability` | `ReportResponse` with `report_status="partial"`, low confidence flags, score refs, no exact probability | render report sections | partial banner visible; low confidence banner visible; no text matching `%通过率|offer 概率|录取概率` | PR8 |
| `apps/web/src/widgets/copy-boundary/CopyBoundaryPanel.test.tsx` | `testReportCopyBoundaryAllowsClipboardOnlyAndRecordsAudit` | `ReportCopyContentResponse` with `clipboard_blocks`, `redaction_applied=true`, `export_artifact=null`; copy event response has audit ref | click copy | calls `navigator.clipboard.writeText`; calls copy event API; shows redaction marker; no filename/download URL/file id rendered | PR8 |
| `apps/web/src/widgets/copy-boundary/CopyBoundaryPanel.test.tsx` | `testCopyFailureKeepsRetryAndDoesNotDropContent` | clipboard write rejects; copy content loaded | click copy | failed state visible; retry action visible; content still present; no audit body text included in request fixture | PR8 |

### 5.4 Review route / page tests

| Target file | Test method | Mocked API response | Act | Expected assertions | PR |
|---|---|---|---|---|---|
| `apps/web/src/app/routes/router.test.tsx` | `testReviewRouteRendersReviewPageAndRequiresAuth` | auth user present / absent | navigate `/review` | authenticated renders `ReviewPage`; unauthenticated redirects `/login`; route type includes `/review` | PR8 |
| `apps/web/src/pages/review/ReviewPage.test.tsx` | `testReviewListRendersLoadingEmptyErrorAndRows` | list loading; empty list; error; success list with `available/partial/low_confidence/failed/source_unavailable` rows | render page with API mocks | page state matches fixtures; row statuses visible; low confidence not styled as success | PR8 |
| `apps/web/src/features/review-generation/useReviewGeneration.test.tsx` | `testMockReviewGenerationPollsAndOpensReviewDetail` | `POST /reviews/mock` 202 task; polling succeeded `rev_1`; `GET /reviews/rev_1` available | call start mock review | state transitions to detail loaded; candidate refs shown as pending confirmation | PR8 |
| `apps/web/src/features/review-generation/useReviewGeneration.test.tsx` | `testRealReviewInputSaveDoesNotCreateAiTaskUntilGenerateClicked` | `POST /reviews/real-inputs` returns 201 `real_input_1`; no `ai_task_id`; `POST /reviews/real` returns 202 | save input then generate | save state has no polling; generation starts polling only after user action | PR8 |
| `apps/web/src/widgets/review-viewer/ReviewInsightPanel.test.tsx` | `testReviewInsightPanelShowsCandidateOnlyAndNoOutcomePrediction` | `ReviewResponse` with `candidate_refs`, low confidence flags | render panel | candidate confirmation entry visible; no formal write success; no exact real interview outcome prediction wording | PR8 |
| `apps/web/src/widgets/copy-boundary/CopyBoundaryPanel.test.tsx` | `testReviewCopyRedactsThirdPartyAndProviderPayload` | review copy blocks include redaction markers; fixture intentionally includes forbidden provider key in ignored field | render and copy | redaction marker visible; forbidden field not rendered or copied | PR8 |

### 5.5 Interrupt resume tests

| Target file | Test method | Mocked API response | Act | Expected assertions | PR |
|---|---|---|---|---|---|
| `apps/web/src/features/agent-interrupt-resume/AgentInterruptPanel.test.tsx` | `testInterruptPanelApproveEditRejectSubmitSchema` | 202 `AiTaskStatusResponse` for each action | fill approve/edit/reject and submit | API body uses `action`, `resume_payload`, `base_interrupt_version_ref`; edit requires user payload; approve/reject submit object payload | PR7 |
| `apps/web/src/features/agent-interrupt-resume/AgentInterruptPanel.test.tsx` | `testInterruptPanelHandlesStaleVersionAndValidationFailedPreservingInput` | 409 `stale_version_conflict`; 422 `validation_failed` | submit edited payload | error panel visible; form input preserved; retry remains available after edit | PR7 |
| `apps/web/src/features/agent-interrupt-resume/useAgentInterruptResume.test.tsx` | `testResumeIdempotencyConflictIsNotRetriedAutomatically` | 409 `idempotency_conflict` | call resume twice with changed body fixture | hook exposes conflict; does not auto-resubmit changed body | PR7 |

### 5.6 Candidate confirmation and status boundary tests

| Target file | Test method | Mocked API response | Act | Expected assertions | PR |
|---|---|---|---|---|---|
| `apps/web/src/features/candidate-confirmation/CandidateConfirmationDrawer.test.tsx` | `testCandidateDrawerConfirmEditRejectMergeRequiresUserAction` | candidate refs for asset, weakness, training; confirmation success responses | render drawer and click each action | no API call before click; confirm/edit/reject/merge call expected endpoint; success updates local candidate status | PR7/PR8 |
| `apps/web/src/features/candidate-confirmation/CandidateConfirmationDrawer.test.tsx` | `testCandidateDrawerFailureKeepsEditsAndDoesNotMarkFormal` | 422 validation failed and 409 stale version | submit edited candidate | input preserved; formal success tag absent; retry/edit visible | PR7/PR8 |
| `apps/web/src/shared/ui/LowConfidenceBanner.test.tsx` | `testLowConfidenceBannerShowsReasonSourceAndActions` | flags include `evidence_missing`, `source_unavailable` | render banner | reason text and actions visible; no success icon-only state | PR7 |
| `apps/web/src/shared/ui/ValidationFailedPanel.test.tsx` | `testValidationFailedPanelPreservesRepairContext` | validation ref, message, field errors | render panel | field errors visible; edit/retry actions visible; user input prop rendered | PR7 |
| `apps/web/src/pages/interview/InterviewPage.test.ts` | `testExistingPolishCandidatePanelRemainsCandidateOnly` | existing polish candidate fixture | call view model builder or render current candidate panel | pending and settled counts correct; candidate not shown as formal asset/weakness | PR7 |
| `apps/web/src/pages/job/JobMatchPanel.test.tsx` | `testJobMatchCopyBoundaryDoesNotIntroduceFileExport` | existing job match analysis fixture | render and copy | copy button remains clipboard action; no download/export wording added by AI Runtime UI | PR7 |

### 5.7 Optional E2E smoke

E2E smoke 只在 PR8 明确授权 Playwright 或现有 smoke runner 后执行。目标文件和方法：

| Target file | Test method | Mocked API response | Act | Expected assertions | PR |
|---|---|---|---|---|---|
| `apps/web/tests/ai-runtime-smoke.spec.ts` | `testLoginReviewTaskTimelineCandidateCopySmoke` | route mocks for login, `/reviews`, task polling, timeline, candidate confirmation, copy content | login -> `/review` -> create mock review -> see timeline -> confirm candidate -> copy | no raw payload visible; no export/download visible; candidate formalization only after click | PR8 |

## 6. 与 active docs 的关系

UI 状态继承 `UI_DESIGN_SYSTEM.md`；API 状态继承 `API_SPEC.md`；安全展示继承 `SECURITY_PRIVACY.md`。本测试计划不替代 active UX/API 文档。

## 7. 非目标

- 不验证后端真实 graph 质量。
- 不做像素级 Figma 验收。
- 不默认增加 Playwright、Vitest、Testing Library 或 MSW。
- 不创建测试文件。

## 8. 目标 PR 使用方式

PR7 实现类型、hook、component、API client 测试；PR8 追加 report/review/candidate closure 和 optional E2E smoke。

## 9. Definition of Done

- 每个目标测试文件都有 test method、mocked response、act 和 assertions。
- task polling、timeline、report/review states、interrupt、candidate、low confidence、validation failed、copy boundary 全覆盖。
- 测试计划明确不暴露 raw payload、checkpoint 或 export/download。

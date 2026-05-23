---
title: 前端实施计划
type: delivery-planning
status: draft-pr1
owner: 项目交付
permalink: ai-for-interviewer/docs/03-delivery/refactor-multiagent-langgraph/frontend-implementation-plan
---

# 前端实施计划

## 1. 文档目的

本文规划 LangGraph / AI Runtime 接入后的前端页面级状态机、route / page 路径、API 调用、polling 策略、interrupt resume、candidate confirmation 和异常 UI。目标是让 PR7 / PR8 可按现有 React + Vite + TypeScript + antd 结构落地，而不是只停留在组件清单。

## 2. 输入来源

- `docs/tmp/CODEX_LANGGRAPH_AI_NON_AI_BOUNDARY.md`：只作为 PR1 输入，不作为 UI 文案或接口事实源。
- active docs：`UX_SPEC.md`、`UI_DESIGN_SYSTEM.md`、`API_SPEC.md`、`APPLICATION_FLOW_SPEC.md`、`PERSISTENCE_MODEL.md`、`SECURITY_PRIVACY.md`
- 当前 `apps/web/src` 结构只读盘点
- `11_BACKEND_API_AND_SCHEMA_PLAN.md`
- 当前代码映射：`router.tsx` 已有 `/dashboard`、`/resume`、`/job`、`/interview`、`/interview/:session_id`；`shared/api` 已校验 `request_id` / `trace_id` envelope；`InterviewPage.tsx` 已有 question / feedback / candidate / copy 局部状态；`JobMatchPanel.tsx` 已有 job match 和 copy 状态。

## 3. 当前状态

当前前端采用 React + Vite + TypeScript + antd，并已有 `entities`、`features`、`widgets`、`pages`、`shared` 分层。PR1 不修改前端代码。当前 route 尚无 `/review`，报告没有一级 route；UX 明确报告详情从模拟面试列表、模拟面试详情、工作台或压力面工作台进入并以右侧抽屉展示。PR7 / PR8 必须保持这个页面边界。

## 4. 目标输出

PR7 可执行前端切片：

- AI task status polling。
- Agent run timeline。
- Report / review generation states。
- Interrupt approve/edit/reject/resume。
- Candidate confirmation drawer。
- Low confidence / validation failed 展示。
- Copy boundary panel。

## 5. 必须覆盖范围

### 5.1 Route 与页面路径

| Surface | Route | 页面 / widget 文件 | 入口 | 规则 |
|---|---|---|
| AI task status surface | no standalone route | `features/ai-task-status/**`, `widgets/task-status-panel/**` | report/review/job match/interview workbench 内嵌 | 不新增普通用户 Agent debug 页 |
| Agent timeline | no standalone route | `widgets/agent-run-timeline/AgentRunTimeline.tsx` | task status panel 展开 | 只显示 sanitized timeline |
| 报告详情 | `/interview/:session_id` 内右侧抽屉；`/review` 可从复盘来源打开关联报告抽屉 | `widgets/report-viewer/ReportSectionList.tsx`, `widgets/copy-boundary/CopyBoundaryPanel.tsx` | 模拟面试列表、会话详情、工作台、压力面完成态 | 不新增一级报告列表；不展示下载/导出 |
| 面试复盘列表 | `/review` | `pages/review/ReviewPage.tsx` | App Shell 左侧导航“面试复盘” | 新增 route 需更新 `router.tsx` 与 AppShell navigation |
| 复盘详情 | `/review` 内右侧抽屉；可选 path state `reviewId` | `widgets/review-viewer/ReviewInsightPanel.tsx` | 复盘列表名称、复盘生成完成、报告详情入口 | detail 仍是抽屉，不独立一级详情页 |
| 真实面试输入 | `/review` 内新增真实面试复盘抽屉 | `features/review-generation/RealReviewInputDrawer.tsx` | 复盘列表新增入口 | 保存输入同步；生成复盘另起 async task |
| Candidate confirmation | no standalone route | `features/candidate-confirmation/CandidateConfirmationDrawer.tsx` | 报告、复盘、feedback、training suggestion surface | candidate / suggestion 未确认不得进入正式列表 |
| Interrupt resume | no standalone route | `features/agent-interrupt-resume/AgentInterruptPanel.tsx` | task status panel 或 timeline interrupt event | approve/edit/reject 调 `resume` API |

### 5.2 API client 与 DTO 文件

| File | Symbol | API | Response source | 必须断言 |
|---|---|---|---|---|
| `entities/ai-task/model/types.ts` | `AiTaskStatus`, `AiTaskStatusResponse` | `GET /api/v1/ai-tasks/{ai_task_id}` | `API_SPEC.md` / `11` | 覆盖 `queued/running/succeeded/partial/low_confidence/validation_failed/source_unavailable/generation_failed/timed_out/cancelled` |
| `entities/ai-task/api/aiTaskApi.ts` | `getAiTask`, `retryAiTask`, `cancelAiTask` | `API-AITASK-002/004/005` | `shared/api/request` envelope | error 透传 `ApiHttpError` |
| `entities/agent-run/model/types.ts` | `AgentRunSummaryResponse`, `AgentTimelineEvent` | `11` | sanitized DTO | 不含 `AgentState`、checkpoint、Prompt、completion、provider payload |
| `entities/agent-run/api/agentRunApi.ts` | `getAgentRun`, `getAgentRunTimeline`, `resumeInterrupt` | `11` endpoint | `shared/api/request` envelope | path encode、idempotency header、422/409 映射 |
| `entities/report/api/reportApi.ts` | `createReportTask`, `getReport`, `getReportCopyContent`, `recordReportCopyEvent` | `API-REPORT-*` | `API_SPEC.md` | copy only, no export artifact |
| `entities/review/api/reviewApi.ts` | `listReviews`, `createMockReviewTask`, `createRealReviewInput`, `createRealReviewTask`, `getReview`, `getReviewCopyContent` | `API-REVIEW-*` | `API_SPEC.md` | real input save no LLM task |
| `entities/candidate/api/candidateApi.ts` | `saveCandidateCorrection`, `confirmDepositTarget` | `API-CANDIDATE-001`, `API-DEPOSIT-001` | `API_SPEC.md` | confirmation required |

### 5.3 页面级状态机

#### 5.3.1 通用 AI task 状态机

| State | Enter condition | API action | UI | Exit |
|---|---|---|---|---|
| `idle` | 无 `ai_task_id` | none | 显示生成入口或空态 | 用户触发 create |
| `accepted` | create 返回 202 | `getAiTask` start polling | 状态 badge 显示已受理 | `queued/running` |
| `queued` | task status queued | polling | loading skeleton，不伪造结果 | `running/failed terminal` |
| `running` | task status running | polling | 可返回列表；显示生成中 | terminal or interrupt |
| `interrupted` | task/run has interrupt ref | stop polling task; fetch timeline | 展示 `AgentInterruptPanel` 表单 | approve/edit/reject resume -> `accepted` |
| `partial` | task terminal partial | stop polling | 展示 partial banner、可用 section、retry/copy boundary | retry or user accepts partial read |
| `low_confidence` | task terminal low_confidence | stop polling | 展示 `LowConfidenceBanner` 和校对入口 | correction / retry / manual review |
| `validation_failed` | task terminal validation_failed or API 422 | stop polling | 展示 `ValidationFailedPanel`，保留用户输入 | edit / retry |
| `failed` | generation_failed/timed_out/provider unavailable | stop polling | 错误 Frame + retry if `retryable` | retry -> `accepted` |
| `succeeded` | succeeded with result_ref | stop polling | 读取业务结果并打开详情/抽屉 | detail loaded |
| `cancelled` | cancel success | stop polling | 显示已取消，不 late formal write | user restart |

Polling 默认值：PR7 使用 `setInterval` 或现有 hook timer；默认间隔 `2000ms`，页面隐藏或 terminal state 停止。Streaming 不进入 PR7 默认实现。Streaming 的冻结边界是 PR7 决策点：仅当后端新增已登记 SSE endpoint、`shared/api` 增加 EventSource wrapper、`14_TEST_PLAN_FRONTEND.md` 增加 streaming mock tests 三项同时满足，才允许以独立 PR 改为 streaming；否则一律 polling。

#### 5.3.2 报告生成与详情

| Step | User action | API | State transition | UI assertion |
|---|---|---|---|---|
| 1 | 在会话 / 工作台点击生成报告 | `POST /api/v1/reports` | `idle -> accepted` | 按钮 loading；返回 `ai_task_id` |
| 2 | 等待生成 | `GET /api/v1/ai-tasks/{id}` polling | `queued/running -> terminal` | `partial/low_confidence/failed/validation_failed` 独立显示 |
| 3 | 成功读取报告 | `GET /api/v1/reports/{report_id}` | `succeeded -> detail_loaded` | 打开报告抽屉，展示 sections / score refs / risk |
| 4 | 复制报告 | `GET /copy-content` then `POST /copy-events` | `copy_idle -> copying -> copied/failed` | `CopyBoundaryPanel` 不出现文件名、download URL 或 export artifact |

#### 5.3.3 复盘列表、模拟复盘和真实复盘

| Surface | User action | API | State transition | UI assertion |
|---|---|---|---|---|
| 复盘列表 | 进入 `/review` | `GET /api/v1/reviews` | `loading -> list_loaded/empty/error` | 行级 status 覆盖 `generating/available/partial/low_confidence/failed/source_unavailable` |
| 模拟复盘 | 选择系统内会话或报告并确认 | `POST /api/v1/reviews/mock` | `idle -> accepted -> queued/running -> terminal` | candidate refs 仅展示待确认入口 |
| 真实输入保存 | 填写真实面试输入并保存 | `POST /api/v1/reviews/real-inputs` | `editing -> saving -> saved/validation_failed/failed` | 保存不创建 `ai_task_id`，材料短缺展示 low confidence |
| 真实复盘生成 | 对已保存输入点击生成 | `POST /api/v1/reviews/real` | `saved -> accepted -> queued/running -> terminal` | 不预测真实面试结果 |
| 复盘详情 | 点击列表名称或生成完成 | `GET /api/v1/reviews/{review_id}` | `detail_loading -> detail_loaded/partial/low_confidence/failed` | 内容沉淀入口必须是 confirmation，不自动 formal write |
| 复盘复制 | 点击复制 | `GET /copy-content` then `POST /copy-events` | `copying -> copied/failed` | 第三方隐私 redaction marker 可见 |

#### 5.3.4 Interrupt resume

Interrupt resume 表单 schema 来源于 `11_BACKEND_API_AND_SCHEMA_PLAN.md` 的 `AgentInterruptResumeRequest`，PR7 前端只使用字段子集：

| Field | Control | Source | UI rule |
|---|---|---|---|
| `action` | segmented control | `approve/edit/reject` | 必选 |
| `resume_payload` | form object | interrupt schema summary from timeline event | edit 时必填，approve/reject 可为空对象 |
| `base_interrupt_version_ref` | hidden field | interrupt event | stale 时返回 `stale_version_conflict` 并保留输入 |
| `user_message` | textarea | user input | 不写入日志正文，只提交 API |
| `correction_refs[]` | selected refs | candidate/correction UI | owner scoped |

### 5.4 Candidate confirmation 数据来源

| Source | Candidate data | Confirmation API | UI rule |
|---|---|---|---|
| AI task result | `AiTaskResultResponse.candidate_refs[]` / `suggestion_refs[]` | domain confirmation endpoint or `API-DEPOSIT-001` | 只作为入口，不展示为正式对象 |
| Polish feedback | `feedback_payload.candidate_refs` and current `polish-candidates` API | existing polish candidate confirm/dismiss until canonical candidate API lands | 保留 legacy compatibility，不扩大到 report/review |
| Report / Review | `ReportResponse` / `ReviewResponse` candidate refs | `API-CANDIDATE-001`, `API-DEPOSIT-001`, domain confirmation endpoints | confirm/edit/reject/merge 必须显式用户动作 |
| Low confidence correction | `CandidateCorrectionResponse` | `API-CANDIDATE-001` | 保存校对后仍需 confirmation |

### 5.5 组件 / hook / API 骨架

| File | Name | Props / input | Return / output | Loading state | Error state | Retry behavior | Tests |
|---|---|---|---|---|---|---|---|
| `features/ai-task-status/useAgentTaskStatus.ts` | `useAgentTaskStatus` | `aiTaskId`, `enabled`, `pollIntervalMs=2000` | task/loading/error/refresh/retry/cancel | queued/running polling | envelope error | terminal stop, retryable only | hook test |
| `widgets/agent-run-timeline/useAgentRunTimeline.ts` | `useAgentRunTimeline` | `agentRunId`, `enabled`, cursor | events/loading/error/refresh | skeleton timeline | visible empty/error | manual refresh | hook test |
| `features/report-generation/useReportGeneration.ts` | `useReportGeneration` | session/report type | start/task/reportRef | accepted/running | partial/failed visible | retry if task retryable | pending/success/partial/failed |
| `features/review-generation/useReviewGeneration.ts` | `useReviewGeneration` | sourceRef/reviewType | start/task/reviewRef | accepted/running | low_confidence/failed visible | retry if allowed | mock/real states |
| `features/agent-interrupt-resume/useAgentInterruptResume.ts` | `useAgentInterruptResume` | agentRunId/interruptId | approve/edit/reject | submitting | validation/owner/stale | retry after edit | approve/edit/reject |
| `features/ai-task-status/AgentTaskStatusBadge.tsx` | `AgentTaskStatusBadge` | status/retryable/nextActions | compact status | queued/running | failed/validation_failed | onRetry | all statuses |
| `widgets/agent-run-timeline/AgentRunTimeline.tsx` | `AgentRunTimeline` | events/loading/error/onRetry | sanitized timeline | skeleton rows | retry panel | onRetry | no raw payload |
| `shared/ui/LowConfidenceBanner.tsx` | `LowConfidenceBanner` | flags/sourceAvailability | warning banner | none | visible low confidence | onReview/onRetry | low confidence display |
| `shared/ui/ValidationFailedPanel.tsx` | `ValidationFailedPanel` | validationResultRef/message | repair panel | none | validation details | edit/retry | validation failed display |
| `widgets/report-viewer/ReportSectionList.tsx` | `ReportSectionList` | sections/scoreRefs/copyState | report sections | section skeleton | partial/failed | regenerate section if allowed | no export UI |
| `widgets/review-viewer/ReviewInsightPanel.tsx` | `ReviewInsightPanel` | review/candidateRefs | review insights | skeleton | low confidence | confirm candidate | candidate-only |
| `features/candidate-confirmation/CandidateConfirmationDrawer.tsx` | `CandidateConfirmationDrawer` | candidates/open/actions | confirmation result | submitting | failed preserves edits | retry submit | confirm/edit/reject/merge |
| `features/agent-interrupt-resume/AgentInterruptPanel.tsx` | `AgentInterruptPanel` | interrupt/actions | resume action | submitting | stale/validation | retry/edit | user action audited |
| `widgets/copy-boundary/CopyBoundaryPanel.tsx` | `CopyBoundaryPanel` | copyContent/redactionApplied | copy action | copying | copy failed | retry copy | no file export wording |

## 6. 与 active docs 的关系

前端只消费 active `API_SPEC.md`、`APPLICATION_FLOW_SPEC.md`、`SECURITY_PRIVACY.md`、`UX_SPEC.md` 和 `UI_DESIGN_SYSTEM.md` 中的稳定字段。`docs/tmp` 与本专题包不直接成为 UI 文案或接口事实源。

## 7. 非目标

- 不新增普通用户可见 Agent debug 页面。
- 不展示 LangGraph checkpoint、AgentState、raw prompt、raw completion、provider payload。
- 不实现后端 PR2-PR8 逻辑。
- 不设计文件导出/下载。
- 不在 PR1 引入 frontend dependency。

## 8. 目标 PR 使用方式

PR7 执行 AI task status、timeline、interrupt、基础 candidate confirmation 和 polling。PR8 执行 report / review / candidate closure。若 PR7 引入 Vitest、Testing Library、MSW 或 Playwright，必须在 PR7 scope 中单独授权、更新 `package.json`、补测试命令并由 `17_PR_BREAKDOWN_AND_IMPLEMENTATION_SEQUENCE.md` 的 PR7 DoD 关闭。

## 9. Definition of Done

- 页面 route、页面路径、用户动作、API 调用和状态迁移已覆盖。
- 默认 polling、streaming 启动条件和 terminal stop 规则已冻结。
- loading、error、retry、low confidence、validation failed、candidate confirmation、copy boundary 都有测试计划。
- UI 不暴露 raw payload、checkpoint 或 exact probability。

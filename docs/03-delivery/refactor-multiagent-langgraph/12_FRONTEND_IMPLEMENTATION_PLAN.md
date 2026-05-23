---
title: 前端实施计划
type: delivery-planning
status: draft-pr1
owner: 项目交付
permalink: ai-for-interviewer/docs/03-delivery/refactor-multiagent-langgraph/frontend-implementation-plan
---

# 前端实施计划

## 1. 文档目的

本文规划 LangGraph / AI Runtime 接入后的前端实现骨架，覆盖 routes/pages、entities/model types、shared API client、features、widgets、hooks、components、tests 和 QA scripts。

## 2. 输入来源

- `docs/tmp/CODEX_LANGGRAPH_AI_NON_AI_BOUNDARY.md`
- active docs：`UX_SPEC.md`、`UI_DESIGN_SYSTEM.md`、`API_SPEC.md`、`APPLICATION_FLOW_SPEC.md`、`PERSISTENCE_MODEL.md`、`SECURITY_PRIVACY.md`
- 当前 `apps/web/src` 结构只读盘点
- `11_BACKEND_API_AND_SCHEMA_PLAN.md`

## 3. 当前状态

当前前端采用 React + Vite + TypeScript + antd，并已有 `entities`、`features`、`widgets`、`pages`、`shared` 分层。PR1 不修改前端代码；PR7 才进入 AI Runtime UI 实现。

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

### 5.1 前端分层骨架

| Layer | 目标目录 | 职责 |
|---|---|---|
| routes / pages | existing page routes + report/review entry points | 发起业务动作，不展示 raw runtime internals |
| entities / model types | `entities/ai-task/**`, `entities/agent-run/**` | 类型、API DTO、status helpers |
| shared API client | `shared/api` | 复用统一 request/envelope/error |
| features | `ai-task-status`, `agent-interrupt-resume`, `candidate-confirmation` | 用户可操作状态 |
| widgets | `task-status-panel`, `agent-run-timeline` | 复用 UI 组合 |
| hooks | feature-local hooks | polling、resume、generation action |
| components | shared/status/report/review components | 低置信度、validation failed、copy boundary |
| tests | colocated `.test.ts(x)` | 先按当前风格做类型/逻辑测试骨架 |
| QA scripts | `npm run web:test`, `npm run web:build` | PR7 最小验证 |

### 5.2 组件 / hook / API 骨架

| File | Name | Props / input | Return / output | Loading state | Error state | Retry behavior | Tests |
|---|---|---|---|---|---|---|---|
| `entities/ai-task/api/aiTaskApi.ts` | `getAiTask` | `taskId` | `AiTaskStatusResponse` | request pending | envelope error | caller refresh | API path/shape test |
| `entities/agent-run/api/agentRunApi.ts` | `getAgentRunTimeline` | `agentRunId`, cursor | sanitized events | request pending | owner/not found | caller refresh | no raw fields test |
| `features/ai-task-status/useAgentTaskStatus.ts` | `useAgentTaskStatus` | `aiTaskId`, enabled, pollIntervalMs | task/loading/error/refresh/retry/cancel | queued/running polling | visible error | terminal stop, retryable only | hook test |
| `widgets/agent-run-timeline/useAgentRunTimeline.ts` | `useAgentRunTimeline` | `agentRunId`, enabled | events/loading/error/refresh | skeleton timeline | visible empty/error | manual refresh | hook test |
| `features/report-generation/useReportGeneration.ts` | `useReportGeneration` | session/report type | start/task/reportRef | accepted/running | failed/partial visible | retry if task retryable | pending/success/partial/failed |
| `features/review-generation/useReviewGeneration.ts` | `useReviewGeneration` | sourceRef/reviewType | start/task/reviewRef | accepted/running | low_confidence/failed visible | retry if allowed | mock/real states |
| `features/agent-interrupt-resume/useAgentInterruptResume.ts` | `useAgentInterruptResume` | agentRunId/interruptId | approve/edit/reject | submitting | validation/owner/stale | retry after edit | approve/edit/reject |
| `features/ai-task-status/AgentTaskStatusBadge.tsx` | `AgentTaskStatusBadge` | status/retryable/nextActions | compact status | queued/running | failed/validation failed | onRetry | all statuses |
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

## 8. 后续 PR 使用方式

PR7 执行本文。若 PR7 需要 Vitest、Testing Library、MSW 或 Playwright，必须在 PR7 scope 中单独授权并更新验证命令。

## 9. Definition of Done

- 前端分层和组件/hook/API 骨架已覆盖。
- loading、error、retry、low confidence、validation failed、candidate confirmation、copy boundary 都有测试计划。
- UI 不暴露 raw payload、checkpoint 或 exact probability。


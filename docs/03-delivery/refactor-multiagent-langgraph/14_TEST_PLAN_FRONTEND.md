---
title: 前端测试脚本实施计划
type: delivery-planning
status: draft-pr1
owner: 项目交付
permalink: ai-for-interviewer/docs/03-delivery/refactor-multiagent-langgraph/test-plan-frontend
---

# 前端测试脚本实施计划

## 1. 文档目的

本文规划前端 unit、component、hook、API client、page、mocked server 和 optional E2E smoke 测试骨架，覆盖 AI Runtime UI 和 report/review/candidate closure。

## 2. 输入来源

- `12_FRONTEND_IMPLEMENTATION_PLAN.md`
- active docs：`UX_SPEC.md`、`UI_DESIGN_SYSTEM.md`、`API_SPEC.md`、`APPLICATION_FLOW_SPEC.md`、`SECURITY_PRIVACY.md`
- 当前 `apps/web/src` 测试风格只读盘点

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

| Target file | 类型 | 覆盖点 | 当前 PR1 冻结 | 后续 PR |
|---|---|---|---|---|
| `apps/web/src/entities/ai-task/model/types.test.ts` | unit/type | status enum、terminal state、result refs | 不含 raw fields | PR7 |
| `apps/web/src/entities/agent-run/model/types.test.ts` | unit/type | timeline event、interrupt action、sanitized summary | no checkpoint/AgentState/raw | PR7 |
| `apps/web/src/entities/ai-task/api/aiTaskApi.test.ts` | API client | `/ai-tasks/{task_id}` path、response guard | envelope/error mapping | PR7 |
| `apps/web/src/entities/agent-run/api/agentRunApi.test.ts` | API client | agent runs、timeline、interrupt resume path | sanitized DTO | PR7 |
| `apps/web/src/features/ai-task-status/useAgentTaskStatus.test.tsx` | hook | polling、terminal stop、retry/cancel/error | runner 是否引入 by PR7 | PR7 |
| `apps/web/src/widgets/agent-run-timeline/AgentRunTimeline.test.tsx` | component/widget | loading/empty/error/events/no raw debug payload | no raw fields | PR7 |
| `apps/web/src/features/report-generation/useReportGeneration.test.tsx` | hook/feature | pending/success/partial/failed | no export action | PR7/PR8 |
| `apps/web/src/features/review-generation/useReviewGeneration.test.tsx` | hook/feature | mock/real pending/success/low_confidence | no outcome prediction | PR8 |
| `apps/web/src/features/agent-interrupt-resume/AgentInterruptPanel.test.tsx` | component | approve/edit/reject/stale version | audit action visible | PR7 |
| `apps/web/src/features/candidate-confirmation/CandidateConfirmationDrawer.test.tsx` | component | confirm/edit/reject/merge/failure keeps input | no silent formal write | PR7/PR8 |
| `apps/web/src/shared/ui/LowConfidenceBanner.test.tsx` | component | flags/source availability/action | not shown as success | PR7 |
| `apps/web/src/shared/ui/ValidationFailedPanel.test.tsx` | component | repair/retry/edit | preserves user input | PR7 |
| `apps/web/src/widgets/report-viewer/ReportSectionList.test.tsx` | component/page | report section partial/failed/copy-only | no export/download | PR8 |
| `apps/web/src/widgets/review-viewer/ReviewInsightPanel.test.tsx` | component/page | candidate refs visible, confirmation entry | candidate-only | PR8 |
| `apps/web/src/widgets/copy-boundary/CopyBoundaryPanel.test.tsx` | component | copy success/failure/redaction marker | no file export | PR8 |
| optional E2E smoke | E2E | login -> mocked task -> timeline -> candidate -> copy | only if tooling authorized | PR8 |

## 6. 与 active docs 的关系

UI 状态继承 `UI_DESIGN_SYSTEM.md`；API 状态继承 `API_SPEC.md`；安全展示继承 `SECURITY_PRIVACY.md`。本测试计划不替代 active UX/API 文档。

## 7. 非目标

- 不验证后端真实 graph 质量。
- 不做像素级 Figma 验收。
- 不默认增加 Playwright、Vitest、Testing Library 或 MSW。
- 不创建测试文件。

## 8. 后续 PR 使用方式

PR7 实现类型、hook、component、API client 测试；PR8 追加 report/review/candidate closure 和 optional E2E smoke。

## 9. Definition of Done

- unit/component/hook/API client/page/mocked server/optional E2E smoke 覆盖已列明。
- task polling、timeline、report/review states、interrupt、candidate、low confidence、validation failed、copy boundary 全覆盖。
- 测试计划明确不暴露 raw payload、checkpoint 或 export/download。


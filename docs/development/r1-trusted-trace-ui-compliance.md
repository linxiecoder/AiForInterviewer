---
title: R1 可信 trace UI 规范审计
type: report
permalink: ai-for-interviewer/development/r1-trusted-trace-ui-compliance
---

# R1 可信 trace UI 规范审计

本文档记录 `apps/web/src/components/TrustedTracePage.tsx` 在 R1-DEV-07 完成后的 UI compliance 审计结果。本文档只记录当前判断，不授权 UI 重构。

## 审计结论

当前可信 trace 页面符合 R1 最小可见面的功能目标，但不完全符合“大型项目成熟组件优先”的长期方向。

具体结论：

- 页面已通过真实浏览器 E2E 保护，可展示 `trace_summary`、RAG citation、evidence gap、degraded / failed / retryable、review / export trace reference 和 empty trace 空态。
- 页面当前只使用 React、HTML 结构和项目自定义 CSS，没有使用 Ant Design、ProComponents 或统一 UI 组件库。
- 当前项目没有既有 Ant Design 依赖。
- 当前项目没有既有 ProComponents 依赖。
- 当前项目没有可复用的统一 UI 组件库，只有局部组件和全局 CSS。
- 本任务不建议引入 Ant Design，因为这会引入较大依赖、样式基线变化、bundle 变化和 E2E 回归风险。
- 本任务不建议引入 ProComponents，因为当前页面以只读摘要展示为主，不是复杂中后台表单或表格场景。

## 检查依据

检查范围：

- `apps/web/package.json`
- `package-lock.json`
- `apps/web/src/components/TrustedTracePage.tsx`
- `apps/web/src/styles.css`
- `apps/web/e2e/trusted-trace.spec.ts`

检查结果：

- 未发现 `antd`、`@ant-design/*`、`@ant-design/pro-*`、`ProComponents`。
- `TrustedTracePage` 中的卡片、标签、列表、空态和提示由 `TraceCard`、`TagList`、`ReferenceGroup` 与 CSS 实现。
- 页面没有引入新的状态管理库。
- 页面没有迁移 Umi。
- 页面没有全站视觉重构。

## 是否需要立即改代码

本任务不建议立即改代码。

原因：

- R1-DEV-07 的目标是让可信数据在真实页面中可见，当前已满足。
- 当前页面已有 Playwright E2E smoke tests，贸然替换 UI 基础组件会增加测试和视觉回归面。
- 项目还没有全局 UI 组件选型，单页引入大型组件库会形成局部孤岛。
- 当前缺口更适合先记录为 UI 选型债，再在统一工作台 UI slice 中收敛。

## 后续 UI 选型建议

若后续进入 R1 工作台 UI 收敛 slice，建议采用以下顺序：

1. 先确定 `apps/web` 是否继续保持 Vite + React，或是否需要中后台框架。
2. 如果仍是 React 且需要成熟组件库，优先评估 Ant Design。
3. 只在复杂表单、表格、筛选、详情页密集场景中评估 ProComponents。
4. 先做一个页面的最小替换实验，覆盖 `Card`、`Alert`、`Tag`、`List`、`Descriptions`、`Empty`、`Typography`、`Spin`。
5. 替换前后必须跑 `npm --workspace apps/web run build`、`npm --workspace apps/web run test`、`npm --workspace apps/web run e2e`。

## 当前保留风险

- 自定义 `TraceCard` / `TagList` 后续可能与全局设计系统重复。
- 页面密度、状态色和列表语义还没有统一组件规范背书。
- 如果 R1 后续增加筛选、折叠、表格或复杂 review/export 操作，应优先使用成熟组件库，而不是继续扩展自研基础组件。

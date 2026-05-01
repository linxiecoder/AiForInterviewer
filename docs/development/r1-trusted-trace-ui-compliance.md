---
title: R1 可信 trace UI 规范审计
type: report
permalink: ai-for-interviewer/development/r1-trusted-trace-ui-compliance
---

# R1 可信 trace UI 规范审计

本文档记录 `apps/web/src/components/TrustedTracePage.tsx` 的 UI compliance 审计和 R1-DEV-07c Ant Design 试点结果。本文档只记录当前判断，不授权全站 UI 重构。

## 审计结论

当前可信 trace 页面已经完成 Ant Design 最小落地试点，功能上保持 R1 最小可信展示面，组件选型上比纯自定义 CSS 更接近“大型项目成熟组件优先”的长期方向。

2026-05-01 补充：根路径 `/` 已从旧 W10 mock 原型切换为 R1 工作台首页，旧 mock 迁移到 `/legacy-mock` 和 `/mock`。首页只做工作台级入口、真实 history contract 最近记录、可信能力摘要和风险空态，不新增后端能力，不改变可信详情页 API 读取逻辑。

具体结论：

- 页面已通过真实浏览器 E2E 保护，可展示 `trace_summary`、RAG citation、evidence gap、degraded / failed / retryable、review / export trace reference 和 empty trace 空态。
- 根路径 `/` 已通过真实浏览器 E2E 保护，可展示 R1 工作台首页，读取 `/api/v1/interviews` history contract，并能从最近记录进入 `/interviews/:sessionId`。
- Markdown export 区域已展示 `status`、`failure_reason`、`retryable`、`content_version` 和可用 snapshot ref。
- 旧 W10 mock 原型仍可通过 `/legacy-mock` 或 `/mock` 访问，避免删除已有 prototype 验证价值。
- 页面当前使用 Ant Design 的 `Card`、`Alert`、`Tag`、`Descriptions`、`Collapse`、`Empty`、`Typography`、`List`、`Spin` 承接基础展示。
- 当前项目已新增 `antd` 依赖。
- 当前项目没有既有 ProComponents 依赖。
- 当前项目还没有全局封装的统一 UI 组件库，Ant Design 仍停留在单页试点层。
- 本试点不引入 ProComponents，因为当前页面以只读摘要展示为主，不是复杂中后台表单或表格场景。
- 本试点不迁移 Umi，不引入新状态管理库，不做全站 layout 重构。

## 检查依据

检查范围：

- `apps/web/package.json`
- `package-lock.json`
- `apps/web/src/App.tsx`
- `apps/web/src/components/WorkbenchHomePage.tsx`
- `apps/web/src/components/LegacyMockPage.tsx`
- `apps/web/src/components/TrustedTracePage.tsx`
- `apps/web/src/styles.css`
- `apps/web/e2e/trusted-trace.spec.ts`

检查结果：

- 已发现 `antd`，未发现 `@ant-design/pro-*`、`ProComponents`。
- `App.tsx` 只做轻量 route 分发，并已使用 route-level lazy loading：`/` 指向 R1 工作台首页，`/interviews/:sessionId` 指向可信详情页，`/legacy-mock` 和 `/mock` 指向旧 mock 原型。
- `WorkbenchHomePage` 使用 Ant Design 的 `Card`、`Alert`、`Tag`、`Descriptions`、`Empty`、`Typography`、`List`、`Button`、`Space`、`Row`、`Col` 承接首页布局。
- `TrustedTracePage` 中的卡片、提示、标签、描述列表、折叠面板、空态、文本和列表已由 Ant Design 组件承接。
- 项目仍保留少量页面级 CSS，用于 grid、间距、长 ref 换行和 Ant Design 组件之间的局部布局适配。
- 页面没有引入新的状态管理库。
- 页面没有迁移 Umi。
- 页面没有全站视觉重构。

## 试点结论

Ant Design 适合继续作为 R1 后续评分、复盘、历史、导出页面的候选统一 UI 基础，但需要先处理 bundle 和局部封装策略。

正向结果：

- `TrustedTracePage` 可以在不改 route、不改 API 字段、不改 view model 核心逻辑的前提下切到 Ant Design。
- `Card`、`Descriptions`、`Tag`、`Alert`、`Collapse`、`Empty`、`List` 能覆盖当前可信 trace 详情展示。
- Playwright E2E 可继续断言用户真实可见能力，并额外覆盖 Ant Design `Card` / `Collapse` / `Empty` 形态。

代价和风险：

- 引入 `antd` 且新增 R1 首页后曾导致主 JS chunk 约 `740 kB`；本轮通过 route-level lazy loading 拆分到页面级 chunk，Node `v22.22.2` 下 `npm --workspace apps/web run build` 最大 chunk 约 `465.54 kB`，不再触发 500 kB chunk warning。
- 前端 runtime baseline 已声明为 Node `20.19+` 或 `22.12+`，仓库 `.nvmrc` / `.node-version` 固定到 `22.12.0`；Node 18 下的 Vite warning 不再视为可长期忽略。
- 如果后续多页面直接散用 Ant Design，可能出现样式和交互不一致；建议建立轻量页面级 pattern，而不是继续随页复制。

## 后续 UI 选型建议

若后续进入 R1 工作台 UI 收敛 slice，建议采用以下顺序：

1. 先确定 `apps/web` 是否继续保持 Vite + React，或是否需要中后台框架。
2. 如果仍是 React 且需要成熟组件库，可基于本试点继续使用 Ant Design。
3. 只在复杂表单、表格、筛选、详情页密集场景中评估 ProComponents。
4. 为评分、复盘、历史、导出页面沉淀一组轻量 pattern，例如详情页 header、状态区、ref 摘要、引用列表、降级提示。
5. 评估 Vite code-splitting 或按 route 懒加载，避免 Ant Design 让首屏主 chunk 持续增大。
6. 替换前后必须跑 `npm --workspace apps/web run build`、`npm --workspace apps/web run test`、`npm --workspace apps/web run e2e`。

## 当前保留风险

- Ant Design 当前只在 `TrustedTracePage` 试点，尚未形成全站统一 UI 规范。
- Ant Design 相关 chunk 已通过 route-level lazy loading 降到当前 Vite warning 阈值以内；如果后续页面继续膨胀，再评估更细的页面拆分或 `manualChunks`。
- 页面密度、状态色和列表语义仍需在评分、复盘、历史、导出页面中继续验证。
- R1 首页当前已读取真实 history contract；发起表单、岗位 / 简历 / RAG 管理仍是入口级展示，需后续 R1 slice 接入后端数据。
- 如果 R1 后续增加复杂表格和筛选，再评估 ProComponents；当前不应提前引入。

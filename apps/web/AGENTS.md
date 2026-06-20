# apps/web 局部规则

本文件只补充根目录 `AGENTS.md`。冲突时以根规则、`docs/00-governance/DOCS_INDEX.md`、active design docs 和当前前端代码为准。

## 入口与栈

- `apps/web` 是唯一 npm workspace，包名是 `@ai-for-interviewer/web`。
- 当前栈是 Vite + React 19 + TypeScript + Ant Design 6。
- 页面入口是 `apps/web/src/main.tsx`，应用入口是 `apps/web/src/app/App.tsx`。
- 本地前端 dev 固定 `127.0.0.1:5173 --strictPort --open`。

## 路由与状态

- 路由是自建 `RouteProvider` / `AppRouter`，位置在 `apps/web/src/app/routes/router.tsx`；不要按 React Router 方式新增页面。
- 新页面要登记 `RoutePath`、导航状态和必要的类型断言测试。
- `AppProviders` 当前承载全局 provider；新增 provider 前先确认是否影响登录态初始化和路由重定向。

## API 调用

- 前端 API 请求应走 `apps/web/src/shared/api/client.ts`，不要在页面里散落裸 `fetch`。
- 默认 API base 是 `/api/v1`，Vite 代理到 `VITE_API_PROXY_TARGET`，默认 `http://127.0.0.1:8001`。
- 请求默认需要 `credentials: "include"`；后端成功 envelope 应保留 `request_id` 和 `trace_id`。
- 不得渲染 provider payload、raw prompt、raw completion、secret、token 或完整敏感输入。

## 结构

- `app/` 放 providers、routes 和 app 壳层。
- `entities/` 放领域类型和实体 API。
- `features/` 放用户动作能力。
- `pages/` 放页面级组合。
- `widgets/` 放跨页面 UI 区块。
- `shared/` 放 API client、配置、通用 UI 和通用工具。

## 测试与验证

- `npm --workspace apps/web run test` 当前只是 `tsc -p tsconfig.json --noEmit`，不等于组件运行测试。
- 当前未发现 Vitest、Jest、Testing Library 或 Playwright 配置；不要把这些写成已有门禁。
- 前端行为变更至少跑 `npm run web:test`；路由、导航和类型契约改动要补充或更新 `*.test.ts(x)` 类型断言。
- UI 行为或页面流变更还需要本地页面验证，不能只用 TypeScript 编译通过替代。

## UI 边界

- Polish 当前创建入口不要新增 Pressure、Review、Training 模式；废弃 `training` 导航保持移除。
- 不使用原生 `alert`、`confirm`、`prompt` 承载业务交互。
- 不在界面声明“已检索知识库”，除非当前 API contract 明确返回了可展示证据。
- 页面错误文案应使用 safe message；不要把服务端内部异常或 provider 原文直接显示给用户。

# M01 基础平台与工作台壳层 - API 设计

## 1. 文档定位

- 本文档用于沉淀本模块的接口清单与契约方向。
- 当前状态：可评审草案。

## 2. 接口分类

| 接口 | 类型 | 消费方 | 作用 | 当前成熟度 |
| --- | --- | --- | --- | --- |
| `GET /api/v1/health` | HTTP API | 本地开发、CI、后续模块联调 | 返回最小存活确认 | L4 |
| `getMessages()` + locale seed | 前端文案入口 | Web 页面、共享组件 | 统一读取可见文案，禁止硬编码 | L4 |
| `AppShell` / `PageHeader` | 前端组合接口 | `/(dashboard)` 页面与后续业务页 | 统一工作台壳层与页面头部 | L4 |
| `DataTable` / `FilterBar` / `Pagination` | 前端组合接口 | 列表型页面 | 统一表格、筛选、分页与状态骨架 | L4 |

## 3. HTTP API：`GET /api/v1/health`

- 路径：`/api/v1/health`
- 方法：`GET`
- 认证要求：无
- 作用：只做轻量存活确认，用于本地启动、CI 和最小联调入口，不承担数据库、Redis、对象存储、异步任务的真实探活。

### 3.1 请求契约

- 请求参数：无
- 请求体：无
- Header 约束：无额外业务 Header 要求

### 3.2 成功响应

| HTTP 状态码 | 响应体 | 语义 |
| --- | --- | --- |
| `200` | `{ "status": "ok" }` | API 入口已启动，且最小路由可达 |

### 3.3 错误语义

- 本接口不定义业务错误码。
- 若应用未启动、路由未注册或框架异常，按默认 HTTP 错误语义返回，并通过结构化日志记录。
- 健康检查失败意味着运行时基线未建立，应先修复 M01，不应继续推进下游模块实现。

## 4. 前端文案入口接口

- 统一入口：`apps/web/src/i18n/**`
- 当前口径：页面标题、导航、按钮、表头、空态、提示语都必须通过集中消息入口读取。
- 首轮 locale seed：`zh-CN`、`en-US`
- 当前约束：
  - 组件内部禁止直接写死可见文案。
  - 后续模块若新增页面或组件，必须先补消息键，再写 UI。
  - locale 切换由 layout / App Shell 统一解析 active locale，下游页面和组件只消费，不自行定义切换策略。
  - locale fallback 固定为“请求 locale -> `zh-CN` -> 记录缺失 key”。
  - 消息命名空间只冻结“共享壳层一层、业务页面一层”的最小边界。

## 5. 壳层接口

### 5.1 `AppShell`

- 消费方：`/(dashboard)` layout 与后续工作台页面。
- 固定职责：
  - 渲染一级导航。
  - 提供主内容区骨架。
  - 承载当前页面标题上下文。
- 当前冻结范围：
  - 一级导航项至少覆盖 `dashboard`、`jobs`、`resumes`、`interviews`、`reviews`、`assets`、`admin`。
  - `training` 页面不是一级导航常驻项。
  - 鉴权信息、成员菜单与角色差异展示不在 M01 冻结。

### 5.2 `PageHeader`

- 消费方：Dashboard 以及后续列表页、详情页、报告页。
- 当前冻结职责：
  - 标题区。
  - 可选说明文案。
  - 可选主动作 / 次动作区域。
- 配套默认冻结口径：
  - 摘要区独立于 `PageHeader`，只承载 `status_badge`、`updated_at`、`summary_items` 与最小状态表达。
  - `PageHeader` 与摘要区共同构成“最小共享页面原语”，但不扩张为完整设计系统 props catalog。
- 未冻结项：
  - 精确 props / slot 结构。
  - 文案采用 message key 还是 resolved copy 的代码级承载形式。

## 6. 列表原语接口

### 6.1 `DataTable`

- 负责：渲染列头、数据行、图标式操作列。
- 共享规则：
  - 支持排序、筛选、分页的展示骨架。
  - 操作列采用图标 + tooltip / aria-label 的方向。
  - 加载态、空态、错误态必须可组合，不应由业务模块绕开基础容器。
- 不负责：数据获取、鉴权、业务字段解释。

### 6.2 `FilterBar`

- 负责：承载列表筛选控件布局与响应式折行。
- 不负责：具体筛选字段、请求序列化和业务查询语义。

### 6.3 `Pagination`

- 负责：展示当前页、总页数和翻页入口。
- 当前至少需要消费：当前页、总页数。
- 未冻结项：翻页回调具体签名、完整 props catalog 与高级筛选序列化规则。

## 7. 跨接口规则

- HTTP API 统一挂在 `/api/v1` 前缀下。
- 页面壳层与列表原语统一复用 i18n 入口，不允许自行维护独立文案来源。
- 列表页优先遵循 `16.1 表格规范`：排序、筛选、服务端分页、图标操作列。
- 列表查询默认采用共享 `ListQueryState`，并使用最小映射：
  - `page -> page`
  - `pageSize -> page_size`
  - `sortBy -> sort`
  - `sortDirection -> order`
  - `filters.q -> q`
  - `filters.status -> status`
- 服务端列表接口默认复用统一分页骨架：`items`、`page`、`page_size`、`total`、`total_pages`。
- 页面容器负责 state / URL / request adapter；`DataTable` / `FilterBar` / `Pagination` 不直接依赖 router。
- M01 只冻结平台级接口方向，不在本轮定义业务模块的请求 DTO、鉴权头或错误码字典。

## 8. 当前缺口

- 共享页面原语已形成默认冻结口径；列表查询状态也已形成最小共享映射，但 `PageHeader` 与列表原语的实现级 props / callback catalog 仍未冻结。
- 根目录脚本与 CI 入口虽已有方向，但未收敛成可供子任务直接照搬的接口清单。
- 完整的 URL locale、持久化偏好、formatter 规则与分包加载策略仍未冻结。

## 9. 进入可作为下游输入前需要补充

- 将 `PageHeader` 与 Dashboard 摘要区的最小接口边界固化为模块级默认共享页面原语口径。
- 将列表查询状态的默认冻结口径继续吸收到实现级 prop / callback contract。
- 冻结根目录最小验证命令矩阵与调用入口。

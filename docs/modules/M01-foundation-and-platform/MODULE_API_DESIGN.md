# M01 基础平台与工作台壳层 - API 设计

## 1. 文档定位

- 本文档用于沉淀本模块的接口清单与契约方向。
- 当前状态：可评审草案。

## 2. 接口分类

| 接口 | 类型 | 消费方 | 作用 | 当前成熟度 |
| --- | --- | --- | --- | --- |
| `GET /api/v1/health` | HTTP API | 本地开发、CI、后续模块联调 | 返回最小存活确认 | L4 |
| `GET /api/v1/storage-objects/{object_id}/download` | HTTP API | M03、M05、M06、M08 等业务模块 | 统一实际文件下载入口 | L4 / L5 候选 |
| `StorageObjectWritePort` | 平台内部接口 | M03 上传 / 导出、M05 归档、M08 导出 | 统一对象写入与元数据回填边界 | L4 / L5 候选 |
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

## 4. HTTP API：`GET /api/v1/storage-objects/{object_id}/download`

- 路径：`/api/v1/storage-objects/{object_id}/download`
- 方法：`GET`
- 认证要求：是
- 作用：作为真实文件字节输出的唯一共享入口，统一承接原始 PDF、导出产物、搜索快照等对象下载；业务模块可以保留自己的资源定位入口，但不能再复制第二套实际下载逻辑。

### 4.1 请求契约

- Path 参数：
  - `object_id`：共享 `storage_objects` 元数据对象 ID
- 请求体：无
- Query：本轮不冻结额外 query 语义
- Header 约束：
  - 继承调用方的当前成员身份与团队上下文
- 共享边界：
  - 本接口只接受共享 `object_id`，不直接接受 `resume_id`、`review_id`、`report_id` 等业务资源 ID。
  - 业务模块若保留 `original-pdf`、`export-report` 等业务入口，只负责把业务资源定位到 `object_id`，不负责直接回传对象字节。

### 4.2 成功响应

| HTTP 状态码 | 响应体 / Header | 语义 |
| --- | --- | --- |
| `200` | 二进制流 + `Content-Type` / `Content-Disposition` | 共享下载网关直接代理对象内容 |
| `307` | `Location` 指向短期有效的签名 URL | 共享下载网关选择重定向到对象存储下载地址 |

- 调用方只能依赖“下载成功且返回正确文件内容”这一语义，不能把“代理流”或“签名 URL”当作业务契约的一部分。
- 下载文件名默认由 `storage_objects.original_filename` 派生，不要求业务模块重复维护一份下载文件名规则。

### 4.3 错误语义

- `401`：当前请求没有有效身份上下文。
- `403`：当前成员不在对象所属团队作用域内，或业务 owner/source pointer 校验失败。
- `404`：`object_id` 不存在，或对应元数据已进入不可下载状态。
- 本接口不负责解释业务资源为什么不可见，只负责在共享层阻止对象字节泄漏。

## 5. 平台对象写入接口：`StorageObjectWritePort`

- 这是平台内部服务边界，不要求本轮冻结具体 SDK、同步 / 异步函数签名或框架注入方式。
- 作用：为上传、导出、快照归档等流程提供统一的对象写入顺序和元数据回填约束。

### 5.1 输入契约

- 调用方至少需要提供：
  - `team_id`
  - `bucket`
  - `source_type`
  - `source_id`
  - `original_filename`
  - `content_type`
  - `size_bytes`
  - `checksum_sha256`
  - 对象二进制流
- 当前冻结的 bucket 范围：
  - `resume-originals`
  - `export-artifacts`
  - `search-snapshots`
- 当前冻结的 object key 规则：
  - `team/{team_id}/{domain}/{entity_id}/{yyyy}/{mm}/{uuid}_{filename}`

### 5.2 输出契约

- 平台写入成功后，至少返回：
  - `object_id`
  - `bucket`
  - `object_key`
  - `storage_provider`
  - `status`
- 调用方必须先拿到稳定的 `object_id`，再把它关联到自己的业务记录。
- 调用方不直接把 bucket / key 暴露给前端或其他模块，而是统一暴露共享 `object_id`。

### 5.3 当前不冻结的内容

- 具体 SDK 封装方式
- 分块上传 / 断点续传
- 代理流与签名 URL 的切换策略
- 签名 URL TTL
- 加密、对象生命周期、跨 bucket 迁移策略

## 6. 前端文案入口接口

- 统一入口：`apps/web/src/i18n/**`
- 当前口径：页面标题、导航、按钮、表头、空态、提示语都必须通过集中消息入口读取。
- 首轮 locale seed：`zh-CN`、`en-US`
- 当前约束：
  - 组件内部禁止直接写死可见文案。
  - 后续模块若新增页面或组件，必须先补消息键，再写 UI。
  - locale 切换由 layout / App Shell 统一解析 active locale，下游页面和组件只消费，不自行定义切换策略。
  - locale fallback 固定为“请求 locale -> `zh-CN` -> 记录缺失 key”。
  - 消息命名空间只冻结“共享壳层一层、业务页面一层”的最小边界。

## 7. 壳层接口

### 7.1 `AppShell`

- 消费方：`/(dashboard)` layout 与后续工作台页面。
- 固定职责：
  - 渲染一级导航。
  - 提供主内容区骨架。
  - 承载当前页面标题上下文。
- 当前冻结范围：
  - 一级导航项至少覆盖 `dashboard`、`jobs`、`resumes`、`interviews`、`reviews`、`assets`、`admin`。
  - `training` 页面不是一级导航常驻项。
  - 鉴权信息、成员菜单与角色差异展示不在 M01 冻结。

### 7.2 `PageHeader`

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

## 8. 列表原语接口

### 8.1 `DataTable`

- 负责：渲染列头、数据行、图标式操作列。
- 共享规则：
  - 支持排序、筛选、分页的展示骨架。
  - 操作列采用图标 + tooltip / aria-label 的方向。
  - 加载态、空态、错误态必须可组合，不应由业务模块绕开基础容器。
- 不负责：数据获取、鉴权、业务字段解释。

### 8.2 `FilterBar`

- 负责：承载列表筛选控件布局与响应式折行。
- 不负责：具体筛选字段、请求序列化和业务查询语义。

### 8.3 `Pagination`

- 负责：展示当前页、总页数和翻页入口。
- 当前至少需要消费：当前页、总页数。
- 未冻结项：翻页回调具体签名、完整 props catalog 与高级筛选序列化规则。

## 9. 跨接口规则

- HTTP API 统一挂在 `/api/v1` 前缀下。
- 业务模块允许保留业务级资源定位入口，但真实文件下载统一走 `GET /api/v1/storage-objects/{object_id}/download`。
- 共享对象写入必须遵循“先写对象 -> 落 `storage_objects` 元数据 -> 返回 `object_id` -> 业务模块关联”的顺序；业务模块不得只保存 bucket / key 而绕过共享元数据层。
- `source_type` / `source_id` 与 `team_id` 是共享下载网关做 owner scope 校验的最小指针，但不在 M01 扩张为完整权限矩阵。
- 页面壳层与列表原语统一复用 i18n 入口，不允许自行维护独立文案来源。
- 列表页优先遵循 `16.1 表格规范`：排序、筛选、服务端分页、图标操作列。
- 列表查询默认采用共享 `ListQueryState`，并使用最小映射：
  - `page -> page`
  - `pageSize -> page_size`
  - `sortBy -> sort`
  - `sortDirection -> order`
  - `filters.q -> q`
  - `filters.status -> status`
- `updated_after` / `updated_before` 当前不属于 M01 冻结的共享最小映射；若业务模块需要时间筛选，只能在各自模块层单独登记扩展，不得反向要求 M01 升级共享白名单。
- 服务端列表接口默认复用统一分页骨架：`items`、`page`、`page_size`、`total`、`total_pages`。
- 页面容器负责 state / URL / request adapter；`DataTable` / `FilterBar` / `Pagination` 不直接依赖 router。
- M01 只冻结平台级接口方向，不在本轮定义业务模块的请求 DTO、鉴权头或错误码字典。

## 10. 当前缺口

- 共享下载网关与对象写入的最小口径已可供下游模块引用；当前仍未冻结的只剩代理流 / 签名 URL 切换策略、签名 TTL、分块上传与对象生命周期策略。
- 共享页面原语已形成默认冻结口径；列表查询状态也已与全局 `OQ-021` 对齐到最小共享映射，但 `PageHeader` 与列表原语的实现级 props / callback catalog 仍未冻结。
- 根目录脚本与 CI 入口虽已有方向，但未收敛成可供子任务直接照搬的接口清单。
- 完整的 URL locale、持久化偏好、formatter 规则与分包加载策略仍未冻结。

## 11. 进入可作为下游输入前需要补充

- 共享下载 / 对象存储主题已补到可供 M03 / M05 引用；若继续推进这一主题，下一层只应细化 transport mode、生命周期与实现级适配，而不是回退最小共享边界。
- 将 `PageHeader` 与 Dashboard 摘要区的最小接口边界固化为模块级默认共享页面原语口径。
- 将列表查询状态的默认冻结口径继续吸收到实现级 prop / callback contract，并保持共享最小映射只覆盖 `page / page_size / q / status / sort / order`。
- 冻结根目录最小验证命令矩阵与调用入口。

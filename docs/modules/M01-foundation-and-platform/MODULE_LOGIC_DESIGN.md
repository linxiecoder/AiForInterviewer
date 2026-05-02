---
title: MODULE_LOGIC_DESIGN
type: note
permalink: ai-for-interviewer/docs/modules/m01-foundation-and-platform/module-logic-design
---

# M01 基础平台与工作台壳层 - Logic 设计

## 1. 文档定位

- 本文档用于沉淀本模块的核心流程、业务规则、状态变化和异常路径。
- 当前状态：状态层已确认为 `maturity=L5`、`readiness=downstream_ready`、`review_status=pending_confirmation`；该状态只支撑下游设计与 formal window preparation，不授权实现。

## 2. 核心状态定义

| 状态域 | 状态 | 说明 |
| --- | --- | --- |
| `workspace` | `uninitialized` | 尚未准备 `.env` 与基础设施 |
| `workspace` | `configured` | 环境模板已补全、本地占位值已准备 |
| `workspace` | `services-ready` | Web / API 最小入口已可启动 |
| `workspace` | `verified` | 最小测试或 CI 入口已通过 |
| `storage-object` | `write-prepared` | 对象元数据、bucket 与 owner/source pointer 已校验完成 |
| `storage-object` | `stored` | 对象字节与 `storage_objects` 元数据已稳定写入 |
| `storage-object` | `download-authorized` | 共享下载网关已通过团队与 owner/source pointer 校验 |
| `storage-object` | `download-blocked` | 对象不存在、不可下载或超出当前作用域 |
| `shell` | `route-resolved` | 当前页面路由已确定 |
| `shell` | `messages-loaded` | 页面所需消息资源已可读取 |
| `shell` | `layout-rendered` | App Shell 与 Page Header 已渲染 |
| `list-view` | `loading` | 列表数据加载中 |
| `list-view` | `empty` | 列表加载成功但无数据 |
| `list-view` | `ready` | 列表数据已展示 |
| `list-view` | `error` | 列表请求或渲染失败 |

## 3. 主流程

### 3.1 本地开发环境启动顺序

1. 从 `.env.example` 派生本地 `.env`，只使用安全占位值。
2. 启动 `infra` 中的最小依赖服务。
3. 安装并同步 `apps/web`、`apps/api` 依赖。
4. 通过根目录 `dev:api` / `dev:web` 启动 FastAPI 最小入口和 Vite + React 最小入口。
5. 运行 `test:api` / `test:web` 或等价 API / Web 双 lane 验证，进入 `verified`。

### 3.2 健康检查逻辑

1. 请求命中 `/api/v1/health`。
2. 应用完成最小日志初始化。
3. 路由返回 `{ "status": "ok" }`。
4. 结果用于确认 API 入口存活，不用于判断外部依赖是否健康。

### 3.2.1 ST13_21 API runtime 边界逻辑

1. `apps/api/app/main.py` 创建 FastAPI app。
2. `get_settings()` 读取 `API_TITLE`、`API_VERSION`、`ENVIRONMENT`、`API_PREFIX`、`API_HOST`、`API_PORT` 等最小运行配置。
3. `main.py` 通过 `build_api_v1_router(settings.api_prefix)` 注册 `/api/v1` router。
4. 历史最小骨架保证 `GET /api/v1/health` 返回 `{ "status": "ok" }`；当前 `apps/api` 已存在 interviews、records、review、export 等读写面，当前事实以 `apps/api/**` 和 `docs/development/**` 为准。
5. HTTPException 进入 minimal error envelope，返回 `{"error": {"code": "HTTP_<status>", "message": "<detail>"}}`。
6. future route placeholders 仅作为未注册常量保留，不创建业务 endpoint。
7. 该历史骨架流程不访问 DB、Redis、MinIO、LLM、RAG、对象存储或外部网络；当前数据库事实为 PostgreSQL runtime + SQLite fallback，Redis、MinIO 和对象存储不作为 R0 必需 runtime。

### 3.3 工作台壳层渲染逻辑

1. 解析当前 Dashboard 路由。
2. 由 layout / App Shell 统一解析 active locale。
3. 读取对应 locale bundle；若请求 locale 缺失，则 fallback 到 `zh-CN` 并记录缺失 key。
4. 渲染 App Shell 的导航、主内容容器和页面头部。
5. 在壳层内加载 Dashboard 摘要区或后续业务页面内容。

### 3.4 列表原语复用逻辑

1. 页面层传入列定义、数据、筛选条件和分页状态。
2. `FilterBar` 渲染筛选控件容器。
3. `DataTable` 渲染表头、数据行和图标操作列。
4. `Pagination` 渲染页码信息与翻页入口。
5. 页面层根据数据结果切换 `loading / empty / ready / error` 状态。

### 3.5 文档治理逻辑

1. 若平台边界发生变化，先回写 M01 模块文档。
2. 若变化影响全局规则或共享契约，再由总控更新全局状态文档。
3. 在模块文档未达到 `L5` 前，不允许把缺口下放到子任务文档中伪装解决。

### 3.6 对象写入与业务关联逻辑

1. 业务模块先完成自己的输入校验，明确 `team_id`、bucket、`source_type`、`source_id`、`content_type`、`size_bytes` 和 `checksum_sha256`。
2. 调用共享 `StorageObjectWritePort` 写入对象二进制流。
3. 平台层先写对象存储，再落 `storage_objects` 元数据，并返回稳定的 `object_id`。
4. 业务模块在拿到 `object_id` 后，再把它关联到自己的业务记录，例如 `original_pdf_object_id`、`output_object_id`。
5. 在业务关联成功前，不允许把 bucket / key 或下载地址直接暴露给前端。

### 3.7 共享下载网关逻辑

1. 业务模块详情页或业务入口先定位到共享 `object_id`。
2. 请求进入 `GET /api/v1/storage-objects/{object_id}/download`。
3. 共享下载网关读取 `storage_objects` 元数据，并校验：
   - 当前成员身份是否存在
   - `team_id` 是否在当前作用域内
   - `source_type` / `source_id` 对应的业务 owner/source pointer 是否允许访问
4. 校验通过后，网关根据平台策略返回代理流或签名 URL。
5. 网关记录下载事件，但不在 M01 冻结完整审计字段字典。

## 4. 分支流程

### 4.1 环境缺失分支

- 若环境变量未准备或本地基础设施不可用，流程停留在 `configured` 之前。
- 此时允许修复运行时与配置，但不允许继续细化业务模块实现。

### 4.2 locale 资源缺失分支

- 若页面或组件找不到消息键，应回补 locale bundle。
- 不允许在组件中直接写死替代文案来规避 i18n 入口。

### 4.3 列表无数据或失败分支

- 无数据时进入统一空态。
- 请求失败时进入统一错误态并保留重试入口。
- 业务模块可补业务说明，但不能绕开基础状态语义。
- 当筛选条件变化、排序变化或 `pageSize` 变化时，页面必须重置到第一页。
- 当仅发生翻页时，不应清空既有筛选与排序状态。
- 页面容器负责 `ListQueryState` 与 URL / request 之间的同步；共享列表原语不直接操作 router。
- request adapter 只写回共享最小键集 `page / page_size / q / status / sort / order`；业务扩展查询键必须在各自模块文档单独登记。
- shared adapter 负责把服务响应、页面态与 i18n 消费边界投影为共享原语稳定输入；resolved copy 承载方式不在 M01 冻结。
- 时间筛选、复杂组合筛选以及 formatter / locale 级持久化策略当前只允许作为业务模块扩展，不属于 M01 共享列表状态的默认白名单。

### 4.4 对象写入或业务关联失败分支

- 若对象字节写入成功，但 `storage_objects` 元数据落库失败：
  - 不允许返回可用 `object_id`
  - 必须记录补偿 / 清理日志，避免形成下游不可见的悬空对象
- 若 `storage_objects` 已创建，但业务记录关联失败：
  - 不允许把下载入口暴露给前端
  - 由业务模块或后续治理流程负责补偿清理，而不是让业务模块绕过共享元数据层直接回放 bucket / key

### 4.5 下载授权失败分支

- 若 `object_id` 不存在、对象已不可下载或团队 / owner/source pointer 校验失败：
  - 进入 `download-blocked`
  - 返回 `403` 或 `404`
  - 不暴露 bucket、key、provider 等底层细节

## 5. 异常路径与回退策略

- 健康检查失败：先修复最小入口，再继续任何下游工作。
- 对象写入成功但共享元数据或业务关联失败：必须保留补偿记录，不允许让业务模块继续携带裸 bucket / key 工作。
- 下载授权失败：共享下载网关直接拦截，不允许把失败原因转化为对象存储地址泄漏。
- Web 壳层渲染失败：先确认路由、消息资源和共享组件边界，禁止在业务页面私自复制壳层。
- 测试 / CI 基线失败：视为平台基线未完成，阻塞模块合并与下游实现准备。
- 文档边界发生冲突：记录到 `MODULE_OPEN_QUESTIONS.md`，不要在模块内临时补一套新契约。

## 6. 幂等性、一致性与约束

- `GET /api/v1/health` 必须保持幂等。
- 环境模板与根目录脚本应支持重复执行，不依赖真实生产凭据。
- 共享下载网关是实际对象字节输出的唯一平台入口；业务模块可以保留自己的资源定位入口，但不能旁路共享下载能力。
- `storage_objects` 的 `team_id` 与 `source_type` / `source_id` 必须在对象可被下游引用前稳定落库。
- 共享下载网关只冻结最小团队与 owner/source pointer 校验职责，不在 M01 扩张为完整权限矩阵或签名 URL 策略。
- i18n 取词是单一事实来源；同一条文案不应在多个组件中重复维护。
- 列表原语只负责展示与交互骨架，避免和业务请求 / 权限语义耦合。

## 7. 当前缺口

- `MQ-001`、`MQ-003`、`MQ-005` 已压缩到共享最小层；当前正式状态层已确认 M01 为 `maturity=L5`、`readiness=downstream_ready`、`review_status=pending_confirmation`，但 `implementation_ready=false`，不得据此推导为可创建或修改 `apps/**`、`infra/**`、`.github/**`、`tests/**`、`tools/**` 或运行时代码。
- 根目录脚本命名、health check 与 API / Web 双 lane 已收敛为最小共享验证顺序；当前未冻结的只剩完整 workflow、lint / format gate、E2E 与多平台矩阵。
- 对象写入顺序、共享下载网关和最小 owner/source pointer 已形成稳定输入；当前未冻结的只剩签名 URL TTL、对象生命周期与清理策略。
- Dashboard 摘要区和 `PageHeader` 的详细状态流仍停留在方向级。
- 列表查询状态已与全局 `OQ-021` 对齐到最小共享行为口径，且当前白名单只覆盖 `page / page_size / q / status / sort / order`；完整实现级 route / callback、时间筛选扩展与 URL / 持久化 / formatter 级 locale 策略仍未冻结。

## 8. L5 / downstream_ready 后仍后置的实现级条件

- 共享下载 / 对象存储主题已足以支撑 M03 的对象引用与下载投影继续推进；后续若继续细化，应留在实现级适配与治理策略，不应回退共享边界。
- 若继续推进 MQ-001，只应补完整 workflow、lint / format gate、E2E 与多平台矩阵，不再回退根目录最小命名与 API / Web 双 lane。
- 冻结壳层头部与摘要区的精确交互状态。
- 将列表查询状态与 URL / callback 的默认行为口径继续吸收到页面样例与组件测试，并保持时间筛选等扩展不被误升格为共享前置。

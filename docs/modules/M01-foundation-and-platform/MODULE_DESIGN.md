# M01 基础平台与工作台壳层 - 模块设计

## 1. 文档定位

- 本文档用于把模块需求转为模块级结构设计。
- 当前状态：可评审草案。

## 2. 设计目标

- 在不擅自补关键共享契约的前提下，为仓库结构、运行时、工作台壳层、i18n、列表原语和验证入口建立统一边界。
- 让 M02、M03 以及后续模块能够明确“应复用什么平台能力、暂时不能依赖什么未冻结契约”。
- 把 M01 从“需求初稿 + 设计骨架”推进到“设计可评审”，但不把模块误判为可直接支撑子任务设计。

## 3. 模块职责边界

- 模块职责：建立全新项目的仓库结构、运行时基线、工作台壳层、i18n 入口、列表原语、测试与文档治理规则。
- 上游依赖：无
- 下游承接：ST01_01、ST01_02、ST01_03

### 3.1 M01 明确负责

- `Workspace Baseline`：monorepo 根目录、应用目录、基础设施目录和环境模板的边界。
- `API Runtime Baseline`：FastAPI 最小入口、`/api/v1/health`、结构化日志初始化。
- `Web Shell Baseline`：Next.js 入口、`/(dashboard)` 壳层、一级导航、页面头部、Dashboard 基础摘要区。
- `Shared Primitive / Adapter Baseline`：页面头部、Dashboard 摘要区、表格、筛选条、分页容器与 shared adapter 的职责边界。
- `Governance Baseline`：i18n 集中取词入口、最小测试入口、CI 方向与文档回写约束。

### 3.2 M01 不负责

- 鉴权会话、成员权限矩阵、团队隔离。
- 业务对象建模、业务路由、领域 API 和持久化表设计。
- 业务模块专属页面 adapter、模块私有 query / DTO 协议和页面级 service 组合规则。
- Markdown 渲染链、上传/导出、异步任务编排的最终实施契约。
- 完整设计系统、完整可观测性与完整 E2E 策略。

## 4. 内部结构拆分

### 4.1 Workspace / Runtime 基线层

- 根目录维护统一脚本入口、`.env.example` 和 `infra/**` 占位。
- `apps/api` 承载 Python 运行时、健康检查和后续领域服务入口。
- `apps/web` 承载 Next.js App Router、共享 layout、i18n 与前端测试入口。
- 本层解决的是“项目怎样被启动和验证”，不解决业务功能本身。

### 4.2 API 最小入口层

- 以 `/api/v1` 作为统一前缀。
- 仅冻结最小健康检查接口：用于本地启动、CI 验证和后续模块联调前的存活确认。
- 结构化日志从最小入口开始统一初始化，但日志字段字典、trace 贯穿和审计规则留给后续模块。

### 4.3 Web 壳层与页面原语层

- `AppShell` 负责左侧导航、主内容区和顶层布局骨架。
- `PageHeader` 负责标题、描述与操作区的统一头部结构。
- 默认冻结口径采用方案 B：`PageHeader` 只承载标题、可选说明、主动作与次动作；摘要区独立承载 `status_badge`、`updated_at` 与 `summary_items`，不并入正文卡片体系。
- Dashboard 页面只提供首个可复用的“摘要区 + 主内容区”基线，不沉淀业务卡片细节，也不在本轮扩张为完整设计系统 props catalog。
- `DataTable`、`FilterBar`、`Pagination` 负责列表页的统一交互骨架，业务模块只补字段和数据来源。
- 训练中心不进入一级导航，但保留被工作台和详情页引出的能力入口约束。

### 4.4 Shared adapter 边界层

- `shared adapter` 位于页面容器与共享页面原语 / 服务层之间，是 Web 侧的编排边界，不是新的领域服务层。
- M01 本轮只冻结 shared adapter 的职责切分，不冻结实现级 props / callback / DTO：
  - 页面容器：持有当前 route、active locale、`ListQueryState` 与 `loading / empty / ready / error` 页面态，决定何时触发 adapter。
  - request adapter：负责 `ListQueryState <-> URL <-> request` 的最小映射，沿用统一 query / pagination 骨架，不引入模块私有 query 编码。
  - shared primitive：`AppShell`、`PageHeader`、摘要区、`FilterBar`、`DataTable`、`Pagination` 只消费稳定输入，不直接访问 router、fetch client 或模块私有 service。
  - i18n 消费边界：layout / App Shell 负责 locale 解析与 fallback；页面容器或 shared adapter 只能从集中消息入口取词，并将稳定 message key 或按同一入口解析后的文案投影给共享原语，不维护第二套消息源。
  - 服务层：只输出领域数据、统一分页骨架和错误语义，不感知 `PageHeader`、摘要区、locale fallback 或共享组件树。
- 因此 shared adapter 的职责是“编排与投影”，不是“重写业务协议”：它可以整理页面输入与服务响应，但不能改写领域字段含义、权限语义或模块私有校验规则。
- 按最低位压缩口径，shared adapter 继续分三层处理：
  - 共享最小层：冻结页面容器职责、`ListQueryState` 最小映射、共享页面原语稳定输入和集中 i18n 入口。
  - 模块投影层：业务模块可在自身文档登记扩展查询键、摘要字段与页面投影规则，但不得回写成 M01 共享前置。
  - 实现细节层：精确 props / callback / hook 组织与 resolved copy 承载形态继续留在后续模块或子任务设计，不作为本轮 M01 共享契约。

### 4.5 验证与治理层

- 后端最小 pytest 用例验证健康检查。
- 前端最小 vitest 用例验证 App Shell 与 DataTable 的可渲染性。
- CI 只冻结 API lane / Web lane 两类最小校验入口，不在 M01 冻结完整流水线矩阵、lint / format gate、E2E 或多平台矩阵。
- 文档治理遵循 `global -> module -> subtask` 分层，不允许在子任务文档中倒填模块缺口。

## 5. 核心对象模型

| 对象 | 作用 | 所属层 | 说明 |
| --- | --- | --- | --- |
| `WorkspaceTopology` | 表达 monorepo 目录边界 | Workspace | 固定为 `apps/web`、`apps/api`、`infra` |
| `EnvTemplateEntry` | 表达安全占位环境变量模板 | Workspace | 只承载键名、说明和本地占位值 |
| `HealthCheckResponse` | 表达最小存活确认 | API | 当前只冻结 `status: ok` |
| `ShellNavigationItem` | 表达一级导航项 | Web | 对齐页面信息架构中的一级导航 |
| `PageHeaderModel` | 表达统一页面头部 | Web | 默认冻结到标题、说明和动作区语义；摘要区作为独立对象承接，精确 props 命名仍待后续收敛 |
| `ListViewState` | 表达筛选、排序、分页和状态容器 | Web | 为后续业务列表页复用 |
| `LocaleMessageBundle` | 表达统一文案资源 | Governance | 页面与组件均通过集中入口取词 |
| `VerificationEntry` | 表达最小测试 / CI 入口 | Governance | 用于定义“现在至少如何验证” |

## 6. 核心数据流与协作路径

### 6.1 开发者启动链路

1. 读取 `WorkspaceTopology` 和 `EnvTemplateEntry`，准备本地配置。
2. 启动 `infra` 中的最小基础设施。
3. 启动 `apps/api`、`apps/web` 的最小入口。
4. 运行 `VerificationEntry` 中定义的最小验证。

### 6.2 HTTP 健康检查链路

1. 客户端或 CI 请求 `GET /api/v1/health`。
2. FastAPI 入口完成日志初始化后转发到健康检查路由。
3. 健康检查只返回轻量存活确认，不读取外部依赖状态。

### 6.3 Dashboard 壳层渲染链路

1. Web 入口装载 locale seed 与根 layout。
2. `/(dashboard)` layout 复用 `AppShell` 建立导航和内容骨架。
3. Dashboard 页面容器读取当前 route / locale 上下文，并通过 shared adapter 组装 `PageHeaderModel`、摘要区输入与页面态。
4. `PageHeader` 与摘要区模板只负责渲染，不直接拉取模块私有服务。
5. 后续模块页面在相同壳层中挂载自己的主内容，并复用同一职责切分。

### 6.4 列表原语复用链路

1. 页面容器持有 `ListQueryState`、active locale 和 `loading / empty / ready / error` 页面态。
2. request adapter 负责把 `ListQueryState` 同步到 URL 与服务请求参数。
3. 服务层返回领域数据、统一分页骨架和错误语义。
4. shared adapter 把服务响应与文案消费边界投影为 `FilterBar`、`DataTable`、`Pagination` 可消费的稳定输入。
5. `FilterBar`、`DataTable`、`Pagination` 只负责通用展示和交互框架，不直接读取 router、locale 策略或模块私有 service。

## 7. 跨模块协作点

- M02 直接复用 `/(dashboard)` 路由骨架、`/api/v1` 前缀、i18n 取词入口和 shared adapter 边界；`MT02_05`、`MT02_06` 只能消费该边界，不得自行定义模块私有 page adapter 协议。
- M03 直接复用列表页、页面头部与 shared adapter 边界；`MT03_02`、`MT03_05` 只能在模块内做字段投影与渲染承接，不重写列表 / 页面原语协议。
- M04-M10 间接复用仓库结构、日志初始化、最小测试入口和页面状态规范。
- 若后续模块需要改变一级导航、页面头部或列表原语的共享行为，应先回写 M01，而不是在业务模块私自分叉。

## 8. 风险点与设计限制

- 如果把 M01 过早扩大为“完整设计系统”或“完整平台治理”，会拖慢整个文档链路，不符合 `OQ-002`、`OQ-003` 的冻结口径。
- 鉴权、会话和权限尚未由 M02 冻结，M01 只能保留“登录后工作台”的壳层前提，不补认证逻辑。
- M01 不拥有业务数据库表；若在本模块提前引入持久化契约，会和 M02-M03 的真实对象设计冲突。
- 最小 CI 与测试入口需要与 M10 的后续治理范围区分，避免把“首轮基线”误写成“最终治理标准”。

## 9. 测试策略

- 后端：通过 `GET /api/v1/health` 的 pytest 验证最小 API 入口。
- 前端：通过 App Shell 与 DataTable 的 vitest 验证壳层和列表原语可渲染。
- 页面设计：统一要求后续页面显式覆盖 loading / empty / error 其中至少一种处理策略。
- 文档治理：任何影响共享壳层、i18n 或目录结构的变化，都必须先更新模块文档，再下放到子任务。

## 10. 维持高 L4 时仍缺的最小条件

- `MQ-001`、`MQ-003`、`MQ-005` 虽已压缩到共享最小层，但这只说明共享边界更稳定；当前 M01 仍只是高 `L4`、接近整体 `L5` 候选但未接受，不构成子任务设计前置条件。
- `PageHeaderModel`、Dashboard 摘要区与 `ListQueryState` 的 shared adapter 三层边界已补齐；当前未冻结的只剩精确 props、request adapter 签名与 resolved copy 承载方式等实现级细节。
- 根目录脚本命名、health check 与 API / Web 双 lane 已收敛为共享最小层；当前未冻结的只剩完整 workflow、lint / format gate、E2E 与多平台矩阵。
- locale fallback、切换策略和消息命名空间已形成最小共享默认口径，但完整 i18n 架构仍未定稿，不足以直接安全拆子任务设计。

## 11. 关联文档

- MODULE_REQUIREMENTS.md。
- MODULE_API_DESIGN.md。
- MODULE_SCHEMA_DESIGN.md。
- MODULE_LOGIC_DESIGN.md。

# M01 基础平台与工作台壳层 - 模块需求

## 1. 文档定位

- 本文档用于把原始需求和原始实施计划中与“基础平台与工作台壳层”相关的内容提炼成模块级需求。
- 当前状态：可评审草案。
- 下游输入目标：MODULE_DESIGN.md、MODULE_API_DESIGN.md、MODULE_SCHEMA_DESIGN.md、MODULE_LOGIC_DESIGN.md。

## 2. 上游输入

### 2.1 原始需求与计划引用
- docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md：4 推荐技术方案
- docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md：5.1 前端 Web 层
- docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md：5.2 前端 UI 组件层
- docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md：14 页面信息架构
- docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md：16 全局交互规范
- docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md：19 视觉风格规范

### 2.2 原始实施计划引用
- docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md：22-282 目标仓库结构与完整仓库目录规划
- docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md：282-303 环境基线
- docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md：303-310 跨任务约束
- docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md：1003-1391 任务 1
- docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md：1392-1644 任务 2

### 2.3 全局治理与冻结口径

- `AGENTS.md`：文档主体默认使用中文；本轮只允许修改 M01 模块级文档。
- `docs/DOC_GOVERNANCE.md`：模块文档达到 `L5` 前，不应进入子任务设计。
- `PLAN_LATEST.md`：M01 是整个项目的依赖根部模块，负责仓库结构、运行时、i18n、测试与文档治理基线。
- `TASK_INDEX.md`：M02、M03 直接依赖 M01，后续模块间接依赖 M01 的仓库、页面壳层和验证约束。
- `TECHNICAL_STANDARDS.md`：默认技术口径为 monorepo、Next.js、FastAPI、PostgreSQL、Redis；工作台壳层和列表原语需先沉淀为全局复用能力。
- `DESIGN_DECISIONS.md`：`DD-004`、`DD-005` 目前仍是 `proposed`，本轮按默认口径推进，不擅自升级为 confirmed。
- `OPEN_QUESTIONS.md`：本轮默认冻结 `OQ-001` monorepo、`OQ-002` 首轮只做最小运行时/测试/CI 基线、`OQ-003` 首轮只沉淀壳层/头部/列表原语/基础页面样式。

## 3. 模块目标与用户价值

- 建立全新项目的仓库结构、运行时基线、工作台壳层、i18n 入口、列表原语、测试与文档治理规则。
- 为 M02-M10 提供统一的仓库边界、路由分层、页面壳层、国际化入口和最小验证入口。
- 为后续代码实施提供“最小可运行、可验证、可继续收敛”的平台基线，而不是一次性做完整平台建设。

## 4. 服务对象

- 开发者 / 维护者：需要统一仓库结构、环境模板、本地运行命令和基础验证入口。
- 已登录工作台用户：后续会通过本模块提供的 Dashboard 壳层、导航、头部和列表原语访问业务页面；具体角色隔离由 M02 定义。
- 后续模块设计者：需要复用统一的 i18n 入口、页面结构、列表能力和最小 HTTP 前缀约束。

## 5. 模块范围内

- 仓库目录、环境模板、基础设施占位
- FastAPI 健康检查与日志初始化
- Next.js 最小入口、Dashboard App Shell、页面头部、列表原语与基础页面样式
- `apps/web/src/i18n/**` 统一文案入口与 locale seed
- 根目录脚本命名、最小测试入口与 API / Web 双 lane CI 基线
- 模块级文档治理约束与对下游模块的共享约束说明

## 6. 不在本模块范围内

- 业务领域对象
- 正式鉴权与权限矩阵
- AI 推理与检索能力
- Markdown 转换 / 预览 / 导出链路的最终契约
- 完整设计系统、完整视觉 token 体系和业务页高保真实现
- 生产级可观测性、权限审计和完整 E2E 加固

## 7. 关键角色与对象

### 7.1 关键角色

- 平台维护者：创建 `.env`、安装依赖、启动本地基础设施、运行测试和 CI 入口。
- 前端模块开发者：复用 App Shell、Page Header、DataTable、FilterBar、Pagination 与 `getMessages()`。
- 后端模块开发者：复用 `/api/v1` 前缀、最小 FastAPI 入口和结构化日志初始化方式。

### 7.2 关键对象

- `WorkspaceTopology`：`apps/web`、`apps/api`、`infra` 的单仓布局。
- `EnvTemplateEntry`：安全占位的环境变量模板条目。
- `HealthCheckResponse`：最小存活确认响应。
- `ShellNavigationItem`：一级导航项定义。
- `PageHeaderModel`：页面头部标题、说明和动作区的展示模型。
- `ListViewState`：筛选、排序、分页、空态、错误态等列表原语共享状态。
- `LocaleMessageBundle`：统一文案命名空间与 locale seed。
- `VerificationEntry`：根目录 `dev:web` / `dev:api` / `test:web` / `test:api` 与 API / Web 双 lane 的最小验证入口。

## 8. 关键流程

### 8.1 本地开发环境启动

1. 开发者从 `.env.example` 派生本地 `.env`，只填本地安全占位值。
2. 启动 `infra` 中的最小基础设施，并安装 `apps/web`、`apps/api` 依赖。
3. 启动 FastAPI 最小入口与 Next.js 最小入口，确保健康检查与首页可用。
4. 通过 `test:api` / `test:web` 或等价 API / Web 双 lane 入口验证“仓库结构可运行、服务可存活、页面壳层可渲染”。

### 8.2 工作台壳层加载

1. Web 入口装载统一 layout 与 locale seed。
2. `/(dashboard)` 路由组复用 App Shell，渲染一级导航、页面头部和主内容区。
3. Dashboard 页面在壳层内渲染首个摘要区，作为后续模块页面模板基线。

### 8.3 列表原语复用

1. 后续业务页面通过统一的 `DataTable`、`FilterBar`、`Pagination` 组合生成列表页骨架。
2. 排序、筛选、分页属于共享能力，但具体字段、业务请求与权限判定由业务模块负责。
3. 列表页必须覆盖加载态、空态、错误态与可重试入口，不允许在业务模块重新发明另一套基础交互。

### 8.4 文档与验证治理

1. M01 在模块级文档中明确仓库、壳层、i18n 和验证边界。
2. 后续模块引用 M01 文档时，优先复用约束，不重复定义平台基线。
3. 若新增需求会改变仓库结构或共享页面原语，应先回写 M01 模块文档，再进入下游设计或实现。

## 9. 分支流程与异常流程

- 环境变量缺失或基础设施未启动时，M01 只能停留在基线修复，不允许继续拆解业务模块设计。
- 健康检查只负责存活确认；若连最小健康检查都失败，应先修复运行时入口，不应把问题下放到 M02-M10。
- locale key 缺失时，应视为 i18n 资源缺口并补齐消息源，而不是在组件中直接硬编码文案。
- 列表页无数据或加载失败时，应复用统一空态 / 错误态容器，不允许每个业务模块自行定义基础状态语义。

## 10. 业务规则与约束

- 首轮仓库结构按 monorepo 冻结，目录边界以 `apps/web`、`apps/api`、`infra` 为准。
- 首轮只建立最小运行时、测试和 CI 基线，不要求在 M01 完成完整生产化设施。
- 根目录统一脚本最小命名冻结为：`dev:web`、`dev:api`、`test:web`、`test:api`。
- 最小验证入口类型冻结为：API=`pytest`、Web=`vitest`；CI 只冻结 API lane / Web lane，不扩张为完整 workflow、lint / format gate、E2E 或多平台矩阵。
- 首轮视觉范围只沉淀壳层、头部、列表原语与基础页面样式，不负责完整业务页视觉定稿。
- 所有页面可见文案都必须通过 `apps/web/src/i18n/**` 或等价集中入口读取。
- 首轮 i18n 最小共享口径固定为：统一 `getMessages(locale)` 入口、locale seed=`zh-CN` / `en-US`、默认 locale=`zh-CN`、切换由 layout / App Shell 统一解析、fallback=`请求 locale -> zh-CN -> 记录缺失 key`。
- 首轮消息命名空间只冻结“共享壳层一层、业务页面一层”的最小边界；共享壳层使用稳定共享 namespace，业务页面按稳定路由或领域根命名。
- `GET /api/v1/health` 只做轻量存活确认，不访问数据库、Redis、对象存储等外部依赖。
- 结构化日志从最小 FastAPI 入口开始统一使用 `structlog` 方向，不在本模块定义完整日志字段字典。
- M01 可以为对象存储、异步任务和数据库迁移保留目录或占位，但不在本轮冻结这些能力的完整实施契约。

## 11. 对下游文档的输出要求

- MODULE_DESIGN.md 需要基于本文件明确组件拆分与职责边界。
- MODULE_API_DESIGN.md 需要基于本文件明确最小 HTTP 入口、前端组合接口与错误语义边界。
- MODULE_SCHEMA_DESIGN.md 需要基于本文件明确数据对象、关系、状态和约束。
- MODULE_LOGIC_DESIGN.md 需要基于本文件明确流程、规则、状态机与异常路径。

## 12. 验收标准

- 仓库结构、目录职责和最小运行时基线边界可评审。
- 健康检查、日志初始化、Web 入口、App Shell、Page Header、列表原语和 i18n 入口的职责分工可评审。
- `OQ-001~003` 对 M01 的影响已被显式映射到需求、设计、API、schema、logic、依赖和任务索引文档。
- 模块当前为什么还不能进入子任务设计，原因被写清且可追踪。

## 13. 当前缺口

- `MQ-001`、`MQ-003`、`MQ-005` 虽已压缩到共享最小层，但当前整体口径仍只能视为高 `L4`、接近整体 `L5` 候选但未接受；不得据此推导为已具备整体接受条件或可开启子任务设计。
- 根目录统一脚本命名、health check 与 API / Web 双 lane 已按 `OQ-019` 吸收；当前未冻结的只剩完整 workflow、lint / format gate、E2E 与多平台矩阵。
- `PageHeader`、Dashboard 摘要区和列表查询状态的共享最小层已冻结；当前未冻结的只剩精确 props 命名、callback catalog 与 resolved copy 承载形态等实现级细节。
- locale fallback、切换策略和命名空间约束已冻结到最小共享规则级别，但完整的 URL / 持久化 / formatter 级 i18n 架构仍未定稿，尚不能据此直接开放子任务设计。

## 14. 待确认问题

- OQ-001 仓库结构是否最终固定为 monorepo（本轮按 `apps/web` + `apps/api` + `infra` 冻结推进）
- OQ-019 / M10：完整 workflow、lint / format gate、E2E 与多平台矩阵是否继续后置到治理模块，不作为 M01 共享前置
- OQ-003 首轮视觉范围是否维持在壳层、头部、列表原语与基础页面样式，不进一步扩张到完整业务页组件库

## 15. 关联文档

- MODULE_DESIGN.md。
- MODULE_API_DESIGN.md。
- MODULE_SCHEMA_DESIGN.md。
- MODULE_LOGIC_DESIGN.md。
- MODULE_TASK_INDEX.md。
- MODULE_DEPENDENCIES.md。
- MODULE_OPEN_QUESTIONS.md。

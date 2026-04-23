# AI 模拟面试 P1 技术标准

## 1. 文档定位

- 本文档沉淀当前项目的全局技术标准与默认口径。
- 对于尚未最终确认的内容，使用“默认建议”或“待确认”表述，不把未决项伪装成最终结论。

## 2. 已确认标准

- 文档主体默认使用中文，代码与技术标识保持英文。
- 正式文档新增后，必须同步更新 `AGENTS.md` 索引。
- 文档体系采用 `global -> module -> subtask` 分层。
- 子任务设计文档与实施文档必须分离。
- 单次执行单位必须是一个子任务目录中的 `SUBTASK_IMPLEMENTATION.md`。

## 3. 默认技术口径

### 3.1 仓库结构

- 当前仓库实现布局：以文档治理与 `doc_governor` 工具链为主，而不是已经落地的业务 monorepo。
- 当前目录真值：根目录全局文档、`docs/governance/`、`docs/modules/`、`docs/superpowers/`、`tools/doc_governor/`、`tests/doc_governor/`、`requirements.txt`。
- 当前不把 `node_modules/`、`.serena/`、`.worktrees/`、`__pycache__/`、临时缓存目录计入正式项目结构。
- 目标产品代码结构默认建议：monorepo。
- 目标产品代码目录建议：`apps/web`、`apps/api`、`infra`。
- 待确认：OQ-001、OQ-002。

### 3.2 Web

- 默认建议：Next.js + TypeScript。
- 工作台壳层、列表原语和页面模板应先沉淀为全局可复用能力，再进入具体业务模块。
- 共享页面原语默认采用方案 B：`PageHeader` 只冻结标题、可选说明、主动作与次动作四类语义区，不冻结精确 props 命名。
- Dashboard 摘要区默认独立于 `PageHeader`，只冻结 `status_badge`、`updated_at`、`summary_items` 与最小状态表达，不并入正文卡片体系。
- 页面原语最小状态表达默认冻结为 `loading` / `ready` / `empty` / `error`，动作可见性仅冻结到 `enabled` / `disabled` / `hidden`。
- 不在当前轮冻结完整设计系统 props catalog、slot tree、视觉 token 与业务专属摘要卡 schema。
- Web 可见文案统一从 `apps/web/src/i18n/**` 读取，并通过 `getMessages(locale)` 作为集中取词入口。
- 首轮 locale seed 默认冻结为 `zh-CN`、`en-US`，默认 locale 为 `zh-CN`。
- locale 切换默认由 layout / App Shell 统一解析 active locale，下游页面和组件只消费，不自行定义切换策略。
- locale fallback 默认冻结为“请求 locale -> `zh-CN` -> 记录缺失 key”，缺失 key 视为消息资源缺口，不允许组件硬编码兜底。
- 消息命名空间默认只冻结“共享壳层一层、业务页面一层”的最小边界；共享壳层使用稳定共享 namespace，业务页面按稳定路由或领域根命名，不在当前轮扩张为完整 i18n 架构。
- 列表查询与分页默认采用方案 B：
  - 共享 `ListQueryState` 作为 canonical state，字段为 `page`、`pageSize`、`sortBy`、`sortDirection`、`filters`。
  - 页面容器负责 state / URL / request adapter，共享列表原语不直接耦合 router。
  - URL / request 默认最小映射为：`page -> page`、`pageSize -> page_size`、`sortBy -> sort`、`sortDirection -> order`、`filters.q -> q`、`filters.status -> status`，时间筛选统一使用 `updated_after`、`updated_before`。
  - 多值筛选首轮默认使用重复 query key 表达，不引入模块私有编码格式。
  - 服务端分页响应默认复用统一骨架：`items`、`page`、`page_size`、`total`、`total_pages`。
  - 当筛选条件变化、排序变化或 `pageSize` 变化时，页面必须重置到第一页；仅翻页时不清空既有筛选与排序。
  - 本轮不冻结完整 props / callback catalog、高级筛选 DSL、cursor pagination 或 infinite scroll。
- 已形成 `proposed-default` 但仍待实现级细化：OQ-003、OQ-020、OQ-021、OQ-022。

### 3.3 API

- 默认建议：FastAPI + Python。
- API、Schema、Service、Task 的分层需要在 M01-M03 中先稳定下来。
- 待确认：OQ-004。

### 3.4 数据与存储

- 默认建议：结构化数据使用 PostgreSQL。
- 默认建议：缓存与异步协调使用 Redis。
- 默认建议：对象存储走 S3-compatible 抽象，本地以 MinIO 模拟。
- 待确认：OQ-007、OQ-009、OQ-010。

### 3.5 内容与渲染

- Markdown 预览与导出默认共用同一渲染链。
- Search snapshot 默认仅消费导入数据，不做在线抓取。
- 打磨主题推荐默认先采用规则推荐。
- 待确认：OQ-006、OQ-011、OQ-013。

### 3.6 治理与可观测性

- 需要保留管理员与普通成员的权限矩阵验证入口。
- 需要保留模块级和子任务级验证入口。
- 根目录统一脚本最小命名默认冻结为：`dev:web`、`dev:api`、`test:web`、`test:api`。
- 最小存活检查默认冻结为 `GET /api/v1/health` 返回 `200` 与 `{ "status": "ok" }`，仅用于服务存活确认，不探测数据库、Redis、对象存储等外部依赖。
- 最小验证入口类型默认冻结为：API 使用 `pytest`，Web 使用 `vitest`。
- 最小 CI 校验矩阵默认只冻结 `API lane` 与 `Web lane` 两类入口，不在当前轮冻结完整 workflow、E2E、lint / format gate、多平台矩阵与缓存策略。
- 文档建设阶段也必须维护成熟度、进展和执行日志，而不是只维护任务状态。
- 待确认：OQ-005、OQ-014、OQ-016、OQ-017、OQ-018、OQ-019。

## 4. 标准变更后需要同步回写

- `DESIGN_DECISIONS.md`
- `OPEN_QUESTIONS.md`
- `MODULE_INDEX.md`
- 受影响的模块文档

# M01 基础平台与工作台壳层 - Schema 设计

## 1. 文档定位

- 本文档用于沉淀本模块涉及的领域对象、关系、约束和生命周期字段。
- 当前状态：可评审草案。

## 2. Schema 范围说明

- M01 不引入业务数据库表，也不冻结后续模块的持久化 schema。
- 本文档只定义 M01 自身需要稳定的配置对象、传输对象和视图模型。
- Alembic、业务模型文件和对象存储抽象在 M01 只保留目录与职责方向，不在本轮落字段级实体设计。

## 3. 对象清单

### 3.1 `EnvTemplateEntry`

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `key` | `string` | 是 | 环境变量键名 |
| `scope` | `root \| web \| api \| infra` | 是 | 所属运行范围 |
| `required` | `boolean` | 是 | 本地运行是否必填 |
| `placeholderValue` | `string` | 是 | 仅允许本地安全占位值 |
| `description` | `string` | 是 | 变量用途说明 |

### 3.2 `HealthCheckResponse`

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `status` | `string` | 是 | 当前固定值为 `ok` |

### 3.3 `ShellNavigationItem`

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `key` | `string` | 是 | 导航项唯一键，例如 `dashboard` |
| `labelKey` | `string` | 是 | i18n 消息键 |
| `href` | `string` | 是 | 对应路由 |
| `primaryNav` | `boolean` | 是 | 是否属于一级导航 |

### 3.4 `PageHeaderModel`

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `titleKey` | `string` | 是 | 标题文案 key |
| `descriptionKey` | `string` | 否 | 描述文案 key |
| `primaryActionKey` | `string` | 否 | 主动作文案 key |
| `secondaryActionKeys` | `string[]` | 否 | 次动作文案 key 集合 |
| `summarySlot` | `string` | 否 | 预留给摘要区的槽位标识 |

### 3.5 `ListColumnSpec`

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `key` | `string` | 是 | 列唯一键 |
| `header` | `string` | 是 | 当前列标题或标题 key |
| `sortable` | `boolean` | 否 | 是否支持排序 |
| `align` | `left \| center \| right` | 否 | 展示对齐方式 |

### 3.6 `ListActionSpec`

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `labelKey` | `string` | 是 | 动作文案 key |
| `icon` | `string` | 是 | 图标标识 |
| `disabled` | `boolean` | 否 | 是否禁用 |

### 3.7 `ListQueryState`

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `page` | `number` | 是 | 当前页码 |
| `pageSize` | `number` | 否 | 每页数量 |
| `sortBy` | `string` | 否 | 排序字段 |
| `sortDirection` | `asc \| desc` | 否 | 排序方向 |
| `filters` | `Record<string, string \| string[]>` | 否 | 筛选值集合 |

### 3.8 `LocaleMessageBundle`

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `locale` | `string` | 是 | locale 标识 |
| `namespace` | `string` | 是 | 文案命名空间 |
| `messages` | `Record<string, string>` | 是 | 文案键值对 |

### 3.9 `VerificationEntry`

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | `string` | 是 | 验证项 ID |
| `layer` | `api \| web \| ci \| docs` | 是 | 所属层 |
| `target` | `string` | 是 | 对应文件或命令目标 |
| `successCondition` | `string` | 是 | 通过标准描述 |

## 4. 关系与引用规则

- `ShellNavigationItem.labelKey`、`PageHeaderModel.*Key`、`ListActionSpec.labelKey` 都必须引用 `LocaleMessageBundle` 中的消息键。
- `ShellNavigationItem.href` 需对齐页面信息架构中的工作台一级导航与 Dashboard 路由组。
- `ListQueryState` 是页面与列表原语之间的共享视图状态，不是后端数据库实体。
- `VerificationEntry` 可引用测试命令、CI job 或文档检查项，但不等于真实 CI 配置文件结构。

## 5. 约束与生命周期

- M01 不定义业务数据库表，因此不存在本模块自有的主键 / 外键 / 软删除策略。
- `HealthCheckResponse.status` 当前仅允许返回 `ok`，不扩展额外探活字段。
- 一级导航默认包含 `dashboard`、`jobs`、`resumes`、`interviews`、`reviews`、`assets`、`admin`；`training` 不作为一级导航常驻项。
- 环境变量模板必须使用安全占位值，不允许把真实口令、token 或 DSN 写入模板。
- 列表原语需要支持统一的 loading / empty / error 容器语义，但具体状态枚举仍由页面层组合。

## 6. 迁移影响

- 当前 M01 对数据库迁移的要求为“目录和职责预留”，不要求生成首轮迁移脚本。
- 后续模块若引入业务实体，不应回写到 M01 的配置 / 视图模型对象中。

## 7. 当前缺口

- `PageHeaderModel.summarySlot`、动作区结构和 Dashboard 摘要对象尚未冻结到可直接复用。
- `ListQueryState` 与 URL、服务端查询参数的精确映射仍未冻结。
- `VerificationEntry` 尚未细化到最终命令级矩阵。

## 8. 进入可作为下游输入前需要补充

- 冻结页面头部与摘要区对象模型。
- 冻结列表查询状态与 URL / callback 的映射规则。
- 冻结根目录验证矩阵对象与 CI job 的一一对应关系。

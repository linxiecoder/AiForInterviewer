# M01 基础平台与工作台壳层 - Schema 设计

## 1. 文档定位

- 本文档用于沉淀本模块涉及的领域对象、关系、约束和生命周期字段。
- 当前状态：可评审草案。

## 2. Schema 范围说明

- M01 不引入业务数据库表，也不冻结后续模块的持久化 schema。
- 本文档只定义 M01 自身需要稳定的配置对象、传输对象和视图模型。
- Alembic、业务模型文件和对象存储抽象在 M01 只保留目录与职责方向，不在本轮落字段级实体设计。
- 例外：共享 `storage_objects` 属于平台级基础设施元数据对象；本轮需要冻结其最小字段面、bucket / key 规则与 owner/source 指针，供 M03、M05、M08 等模块引用。

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

- `PageHeaderModel` 只表达头部语义，不承载摘要区实体本身。
- 摘要区在默认冻结口径下作为独立概念对象承接 `status_badge`、`updated_at`、`summary_items` 与最小状态表达；精确字段命名和代码级结构继续留给后续实现收敛。
- `titleKey` / `descriptionKey` / action key 目前仍按 `LocaleMessageBundle` 引用建模；是否下沉为 resolved copy 继续受 `OQ-022` 约束。

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

- 默认最小映射规则：
  - `page -> page`
  - `pageSize -> page_size`
  - `sortBy -> sort`
  - `sortDirection -> order`
  - `filters.q -> q`
  - `filters.status -> status`
  - 时间筛选统一映射为 `updated_after`、`updated_before`
- 多值筛选首轮默认使用重复 query key 表达，不引入模块私有编码格式。

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

### 3.10 `StorageObjectRecord`

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | `string` | 是 | 共享对象元数据 ID |
| `team_id` | `string` | 是 | 所属团队，用于团队隔离 |
| `bucket` | `resume-originals \| export-artifacts \| search-snapshots` | 是 | 当前冻结的 bucket 名称 |
| `object_key` | `string` | 是 | 对象存储内的实际 key |
| `original_filename` | `string` | 是 | 原始文件名 |
| `content_type` | `string` | 是 | MIME 类型 |
| `size_bytes` | `number` | 是 | 对象字节大小 |
| `checksum_sha256` | `string` | 是 | 写入前计算的 SHA-256 |
| `storage_provider` | `minio \| s3-compatible` | 是 | 存储提供方抽象 |
| `source_type` | `string` | 是 | 业务来源类型，例如原始 PDF、导出产物、搜索快照 |
| `source_id` | `string` | 是 | 对应的业务资源 ID |
| `status` | `string` | 是 | 只冻结“可下载 / 不可下载”的最小语义，不在本轮展开完整枚举 |
| `created_at` | `string` | 是 | 创建时间 |
| `updated_at` | `string` | 是 | 最后更新时间 |
| `created_by` | `string` | 否 | 创建人 |
| `updated_by` | `string` | 否 | 最后更新人 |
| `deleted_at` | `string` | 否 | 软删除时间 |
| `deleted_by` | `string` | 否 | 软删除执行人 |

- `StorageObjectRecord` 对应共享 `storage_objects` 元数据对象；业务模块只应持有 `object_id` 引用，不应复制 bucket / key 到自己的领域对象中。
- M01 在本轮只冻结最小字段面，不扩张为完整对象生命周期、ACL、版本化或冷热分层策略。

## 4. 关系与引用规则

- `ShellNavigationItem.labelKey`、`PageHeaderModel.*Key`、`ListActionSpec.labelKey` 都必须引用 `LocaleMessageBundle` 中的消息键。
- `ShellNavigationItem.href` 需对齐页面信息架构中的工作台一级导航与 Dashboard 路由组。
- `ListQueryState` 是页面与列表原语之间的共享视图状态，不是后端数据库实体。
- `StorageObjectRecord.source_type` / `source_id` 表达对象与业务资源的最小 owner/source pointer；它们为共享下载网关提供定位线索，但不单独构成完整权限来源。
- 业务模块若需要保留 `original-pdf`、`export-report` 等业务入口，应通过业务资源定位到 `storage_objects.id`，而不是复制 bucket / key 规则。
- 服务端列表响应默认复用统一分页骨架：`items`、`page`、`page_size`、`total`、`total_pages`。
- `VerificationEntry` 可引用测试命令、CI job 或文档检查项，但不等于真实 CI 配置文件结构。

## 5. 约束与生命周期

- M01 不定义业务数据库表，因此不存在本模块自有的主键 / 外键 / 软删除策略。
- `HealthCheckResponse.status` 当前仅允许返回 `ok`，不扩展额外探活字段。
- `StorageObjectRecord.bucket` 当前只允许 `resume-originals`、`export-artifacts`、`search-snapshots` 三类值；后续新增 bucket 必须先回写 M01。
- `StorageObjectRecord.object_key` 统一遵循 `team/{team_id}/{domain}/{entity_id}/{yyyy}/{mm}/{uuid}_{filename}` 模式。
- `StorageObjectRecord.status` 当前只冻结“可下载 / 不可下载”的最小语义；精确枚举、生命周期策略与保留期规则不在本轮收口。
- 一级导航默认包含 `dashboard`、`jobs`、`resumes`、`interviews`、`reviews`、`assets`、`admin`；`training` 不作为一级导航常驻项。
- 环境变量模板必须使用安全占位值，不允许把真实口令、token 或 DSN 写入模板。
- 列表原语需要支持统一的 loading / empty / error 容器语义，但具体状态枚举仍由页面层组合。

## 6. 迁移影响

- 当前 M01 对数据库迁移的要求为“目录和职责预留”，不要求生成首轮迁移脚本。
- `storage_objects` 作为共享基础设施元数据对象，可以在后续模块落到真实模型 / 迁移文件，但字段面应以当前 M01 冻结口径为准，不在各业务模块重复发明一份。
- 后续模块若引入业务实体，不应回写到 M01 的配置 / 视图模型对象中。

## 7. 当前缺口

- 页面头部与摘要区对象模型已形成默认冻结候选，但 `PageHeaderModel.summarySlot`、动作区代码级结构和摘要区精确字段命名尚未冻结到可直接实现复用。
- `ListQueryState` 与 URL、服务端查询参数的最小映射已形成 `proposed-default`；但高级筛选序列化和完整实现级交互细节仍未冻结。
- `StorageObjectRecord` 的最小字段面、bucket / key 规则和 owner/source pointer 已冻结；当前仍未冻结的是对象生命周期、版本化、保留策略与 provider failover。
- `VerificationEntry` 尚未细化到最终命令级矩阵。

## 8. 进入可作为下游输入前需要补充

- `storage_objects` 的最小字段面已经足以供 M03 / M05 / M08 建立对象引用与下载投影，不应继续在下游模块重定义 bucket / key / source pointer。
- 将页面头部与摘要区对象模型提升为模块级稳定默认口径，并保持不扩张为完整 props catalog。
- 将列表查询状态与 URL / callback 的默认冻结口径继续吸收到组件接口与页面样例。
- 冻结根目录验证矩阵对象与 CI job 的一一对应关系。

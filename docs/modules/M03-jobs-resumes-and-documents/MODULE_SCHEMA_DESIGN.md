---
title: MODULE_SCHEMA_DESIGN
type: note
permalink: ai-for-interviewer/docs/modules/m03-jobs-resumes-and-documents/module-schema-design
---

# M03 岗位、简历与文档处理 - Schema 设计

## 1. 文档定位

- 本文档用于沉淀本模块涉及的领域对象、关系、约束和生命周期字段。
- 当前状态：高 `L4`，字段面以源计划中的最低字段面为基础，已能支撑模块级评审与白名单观察，但当前不登记为正式子任务设计候选输入。
- 本模块只定义 M03 自有对象；`job_resume_bindings`、`job_resume_match_analyses` 等对象属于 M04。

## 2. 核心对象

### 2.1 `storage_objects`
- 来源：共享文件元数据对象，M03 只消费与原始 PDF / 导出 PDF 相关的引用。
- 最低字段面：
  - `id`
  - `team_id`
  - `bucket`
  - `object_key`
  - `original_filename`
  - `content_type`
  - `size_bytes`
  - `checksum_sha256`
  - `storage_provider`
  - `source_type`
  - `source_id`
  - `status`
  - `created_at`
  - `updated_at`
  - `created_by`
  - `updated_by`
  - `deleted_at`
  - `deleted_by`
- M03 使用方式：
  - `resumes.original_pdf_object_id`
  - `resume_export_records.output_object_id`

### 2.2 `jobs`
- 最低字段面：
  - `id`
  - `team_id`
  - `company`
  - `title`
  - `jd_markdown`
  - `requirement_items_json`
  - `source_url`
  - `status`
  - `owner_user_id`
  - `latest_match_analysis_id`
  - `created_at`
  - `updated_at`
  - `created_by`
  - `updated_by`
  - `deleted_at`
  - `deleted_by`
- 说明：
  - `requirement_items_json` 被 M04 / M06 直接消费；本轮已在模块层形成 `proposed-default` 最小契约，用于约束最小 item 结构、空值语义、排序规则与写入责任。
  - `latest_match_analysis_id` 只是跨模块引用，不代表 M03 管理分析对象本身。

### 2.2.1 `jobs.requirement_items_json` 最小 item 契约
- 物理形态：
  - `jsonb`
  - 允许为 `null` 或 JSON array
- 空值语义：
  - `null`：岗位结构化要求尚未完成整理，不能作为 M04 / M06 稳定输入。
  - `[]`：岗位结构化要求已完成整理，但当前没有可独立消费的要求项。
- 非空数组中的每个 item 至少包含：
  - `item_key`
    - string
    - 在同一 `job` 内唯一，用于下游稳定引用。
  - `text`
    - string
    - `trim` 后不能为空，承载最小人类可读要求正文。
- 排序规则：
  - 数组顺序是唯一排序事实来源。
  - 下游详情展示、上下文装配与匹配分析必须保持原序，不得自行重排。
- 写入责任：
  - 仅 `POST/PATCH jobs` 可以整体替换该数组。
  - 列表 / 详情读模型与 M04 / M06 不得局部 patch、反向回写或重写 item schema。
- 未冻结扩展区：
  - 分类、权重、来源区段、证据提示等扩展字段仍未冻结。
  - 在总控收口 `OQ-025` 前，下游模块不得依赖扩展字段存在。

### 2.3 `resumes`
- 最低字段面：
  - `id`
  - `team_id`
  - `owner_user_id`
  - `name`
  - `source_type`
  - `original_pdf_object_id`
  - `current_document_id`
  - `status`
  - `created_at`
  - `updated_at`
  - `created_by`
  - `updated_by`
  - `deleted_at`
  - `deleted_by`
- 说明：
  - Markdown 新建简历时，`original_pdf_object_id` 允许为空。
  - PDF 导入简历时，`current_document_id` 在转换成功前允许为空。

### 2.4 `resume_documents`
- 最低字段面：
  - `id`
  - `team_id`
  - `resume_id`
  - `version_no`
  - `markdown_content`
  - `summary_json`
  - `save_reason`
  - `created_at`
  - `updated_at`
  - `created_by`
  - `updated_by`
  - `deleted_at`
  - `deleted_by`
- 说明：
  - `markdown_content` 是当前简历正文的事实来源。
  - `summary_json` 仅作为本模块内部扩展区，下游暂不应依赖其结构。
  - `save_reason` 需要区分初始导入、手动保存、版本恢复等语义，但本轮不冻结枚举值。

### 2.5 `resume_conversion_logs`
- 最低字段面：
  - `id`
  - `team_id`
  - `resume_id`
  - `source_object_id`
  - `target_document_id`
  - `parser_name`
  - `parser_version`
  - `status`
  - `duration_ms`
  - `error_message`
  - `created_at`
  - `updated_at`
  - `created_by`
  - `updated_by`
  - `deleted_at`
  - `deleted_by`
- 说明：
  - `target_document_id` 在失败前允许为空。
  - `parser_name` / `parser_version` 用于回溯转换质量，不直接暴露为跨模块稳定契约。

### 2.6 `resume_export_records`
- 最低字段面：
  - `id`
  - `team_id`
  - `resume_id`
  - `document_id`
  - `format`
  - `trigger_mode`
  - `status`
  - `output_object_id`
  - `render_duration_ms`
  - `requested_by`
  - `created_at`
  - `updated_at`
  - `created_by`
  - `updated_by`
  - `deleted_at`
  - `deleted_by`
- 说明：
  - `document_id` 指向导出所基于的版本快照。
  - `output_object_id` 在导出完成前允许为空。

## 3. 关系与引用规则

- `resumes` 与 `resume_documents`
  - `1:N`
  - `resumes.current_document_id` 指向其中一个当前生效版本
- `resumes` 与 `storage_objects`
  - `0:1`
  - `original_pdf_object_id` 只指向原始 PDF，不指向导出文件
- `resume_conversion_logs` 与 `storage_objects`
  - `source_object_id -> storage_objects.id`
- `resume_conversion_logs` 与 `resume_documents`
  - `target_document_id -> resume_documents.id`
- `resume_export_records` 与 `resume_documents`
  - `document_id -> resume_documents.id`
- `resume_export_records` 与 `storage_objects`
  - `output_object_id -> storage_objects.id`
- `jobs` 与 `resumes`
  - 本模块不直接建关系表
  - 多对多绑定由 M04 的 `job_resume_bindings` 定义

## 4. 约束与查询策略

### 4.1 通用约束
- 所有热点表至少具备 `(team_id, deleted_at)` 组合索引。
- 列表页常用筛选字段建立复合索引，例如：
  - `status`
  - `updated_at`
  - `job_id`
  - `resume_id`
  - `source_type`

### 4.2 M03 专属约束
- `resume_documents`
  - 同一 `resume_id` 下的 `version_no` 必须唯一。
  - 不允许修改历史版本内容。
- `resumes`
  - `current_document_id` 只能指向属于本 `resume_id` 的未删除文档。
- `resume_conversion_logs`
  - 一个日志只对应一次转换任务。
  - 成功时必须留下 `target_document_id`；失败时必须留下 `error_message`。
- `resume_export_records`
  - 一个导出记录只对应一次导出任务。
  - 成功时必须留下 `output_object_id`。

## 5. 生命周期语义

- `jobs`
  - 已确认本轮必须有可筛选的 `status` 字段。
  - 精确枚举留待 `ST03_01` 子任务评审细化。
- `resumes`
  - 需要区分至少四类语义：
    - 已创建但无当前文档
    - 可编辑 / 可引用
    - 转换失败待人工处理
    - 已删除或归档
  - 已确认本轮先冻结生命周期语义，精确枚举留待 `ST03_02` 子任务评审细化。
- `resume_documents`
  - 创建即生效于历史视图，是否成为当前版本由 `current_document_id` 决定。
- `resume_conversion_logs`
  - 反映上传后异步转换的真实状态，不允许把失败吞掉。
- `resume_export_records`
  - 反映导出任务的真实状态，不允许“前端认为成功但无产物对象”。

### 5.1 模块级冻结字段与延后细化字段

| 对象 | 模块级已冻结 | 延后到子任务级细化 |
| --- | --- | --- |
| `jobs` | 最小字段面、`requirement_items_json` 的 `item_key` / `text` / 数组顺序候选契约、必须存在可筛选 `status` | `status` 精确枚举值、`requirement_items_json` 扩展字段与页面侧 badge 映射 |
| `resumes` | `source_type`、`original_pdf_object_id` / `current_document_id` 的可空语义、当前版本指针规则 | `status` 精确枚举值、列表摘要字段投影 |
| `resume_documents` | `version_no` 唯一、`markdown_content` 为事实正文、历史版本不可变 | `summary_json` 结构、`save_reason` 枚举值 |
| `resume_conversion_logs` | 状态日志是上传后异步转换事实来源、失败必须有 `error_message` | 错误分类细粒度、前端展示文案映射 |
| `resume_export_records` | 导出基于具体 `document_id` 快照、成功必须有 `output_object_id` | 导出类型扩展与重试 UI 投影 |

## 6. 对下游模块的稳定输出

- 面向 M04：
  - `jobs.id`
  - `jobs.jd_markdown`
  - `jobs.requirement_items_json[*].item_key`
  - `jobs.requirement_items_json[*].text`
  - `jobs.requirement_items_json` 的数组顺序
  - `resumes.id`
  - `resumes.current_document_id`
  - `resume_documents.markdown_content`
- 面向 M05：
  - `storage_objects` 上的原始 PDF / 导出 PDF 引用
  - `resume_conversion_logs` 与 `resume_export_records` 的来源链路
  - `resume_documents` 不进入共享 `retrieval_chunks`
- 面向 M06：
  - 岗位结构化要求的 `item_key` / `text` 与数组顺序
  - 当前简历正文

## 7. 当前缺口

- `summary_json`、`save_reason` 与状态字段的细化枚举留待子任务评审，不再阻塞本轮模块推进。
- `jobs.requirement_items_json` 已按 `OQ-025` 吸收为 `proposed-default` 最小 item 契约，但扩展字段区、下游共识回写与模块措辞收紧尚未完成；当前不得把扩展字段当稳定依赖，也不得据此宣布岗位链已 ready。
- 历史版本恢复是否需要单独字段或复用新增版本语义，留待 `ST03_02` 继续细化。
- 文件清理与过期策略依赖基础设施与治理模块，本轮不在 M03 内单独发明。
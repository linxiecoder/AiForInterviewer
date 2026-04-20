# M03 岗位、简历与文档处理 - API 设计

## 1. 文档定位

- 本文档用于沉淀本模块的接口清单与契约方向。
- 当前状态：可评审草案，重点明确接口边界、同步/异步职责和跨模块归属。
- 鉴权基线引用 M02：
  - 所有接口默认要求已登录用户。
  - 访问控制遵循 `401 / 403 / 404` 与 `team_id` 隔离规则。
- 本文档不重新定义 M04 的绑定 / 匹配分析接口，也不重写共享文件下载网关契约。

## 2. M03 自有接口清单

| 接口 | 作用 | 同步 / 异步 | 说明 |
| --- | --- | --- | --- |
| `GET /api/v1/jobs` | 岗位列表 | 同步 | 支持分页、筛选、排序 |
| `POST /api/v1/jobs` | 创建岗位 | 同步 | 创建岗位基础记录 |
| `GET /api/v1/jobs/{job_id}` | 岗位详情 | 同步 | 只返回 M03 自有数据面 |
| `PATCH /api/v1/jobs/{job_id}` | 更新岗位 | 同步 | 更新岗位正文和结构化要求 |
| `GET /api/v1/resumes` | 简历列表 | 同步 | 返回简历摘要与当前状态 |
| `POST /api/v1/resumes` | 以 Markdown 创建简历 | 同步 | 同步创建 `resumes` 与首个 `resume_documents` |
| `GET /api/v1/resumes/{resume_id}` | 简历详情 | 同步 | 返回当前文档、原始文件引用、日志摘要 |
| `PATCH /api/v1/resumes/{resume_id}` | 更新简历基础信息 | 同步 | 仅更新聚合根元数据，不直接写正文快照 |
| `POST /api/v1/resumes/upload-pdf` | 上传 PDF 并创建简历 | 同步受理 + 异步转换 | 同步完成文件入库与受理，转换走任务链路 |
| `GET /api/v1/resumes/{resume_id}/documents` | 读取版本列表 | 同步 | 返回历史版本摘要 |
| `POST /api/v1/resumes/{resume_id}/documents` | 保存新版本 | 同步 | 新增不可变快照并切换 `current_document_id` |
| `GET /api/v1/resumes/{resume_id}/conversion-logs` | 查询转换日志 | 同步 | 返回异步转换状态与失败原因 |
| `GET /api/v1/resumes/{resume_id}/export-records` | 查询导出记录 | 同步 | 返回导出状态与产物引用 |
| `POST /api/v1/resumes/{resume_id}/export-pdf` | 发起导出 | 同步受理 + 异步导出 | 返回受理结果和导出记录 ID |
| `GET /api/v1/resumes/{resume_id}/original-pdf` | 访问原始 PDF | 同步 | 业务定位入口，实际下载复用共享文件能力 |

## 3. 明确不属于 M03 的接口

- `GET /api/v1/jobs/{job_id}/resume-bindings`
- `POST /api/v1/jobs/{job_id}/resume-bindings`
- `DELETE /api/v1/jobs/{job_id}/resume-bindings/{resume_id}`
- `POST /api/v1/jobs/{job_id}/match-analyses`
- `GET /api/v1/jobs/{job_id}/match-analyses/{analysis_id}`
- `GET /api/v1/storage-objects/{object_id}/download`

> 上述接口分别属于 M04 或共享基础设施。M03 只能提供输入对象或对象引用，不能在本模块内重复定义。

## 4. 关键请求与响应语义

### 4.1 岗位接口
- 创建 / 更新岗位时，语义上至少包含：
  - `company`
  - `title`
  - `jd_markdown`
  - `requirement_items_json`
  - `source_url`
  - `status`
- 岗位详情可返回：
  - M03 自有字段
  - `latest_match_analysis_id` 这类跨模块引用字段
- 岗位详情不内联返回完整匹配分析对象，避免把 M04 契约写回 M03。

### 4.2 简历接口
- `POST /api/v1/resumes`
  - 用于 Markdown 直建简历。
  - 成功后同步返回：
    - `resume_id`
    - `current_document_id`
    - 当前 Markdown 摘要
- `POST /api/v1/resumes/{resume_id}/documents`
  - 语义是“保存新版本”，不是“覆盖旧版本”。
  - 成功后返回新建版本和新的 `current_document_id`。
- `GET /api/v1/resumes/{resume_id}`
  - 至少需要带出：
    - 简历基础信息
    - `original_pdf_object_id`
    - 当前版本摘要
    - 最近转换状态
    - 最近导出状态

### 4.3 上传 / 转换 / 导出接口
- `POST /api/v1/resumes/upload-pdf`
  - 只接受 `PDF` 文件。
  - 同步完成：
    - 文件校验
    - 原始文件落对象存储
    - `storage_objects` 初始记录落库
    - `resumes` 初始记录落库
    - `resume_conversion_logs` 初始记录落库
  - 返回 `202 Accepted`，并携带：
    - `resume_id`
    - `conversion_log_id`
    - 当前状态摘要
- `GET /api/v1/resumes/{resume_id}/conversion-logs`
  - 以日志状态暴露转换结果，而不是要求上传接口阻塞等待。
- `POST /api/v1/resumes/{resume_id}/export-pdf`
  - 返回 `202 Accepted`
  - 至少返回：
    - `export_record_id`
    - 导出的目标文档引用
    - 当前状态摘要
- `GET /api/v1/resumes/{resume_id}/original-pdf`
  - 是业务资源入口。
  - 真实文件下载仍复用共享 `storage_objects` 下载能力，避免复制一套权限校验逻辑。

## 5. 跨接口统一规则

- 分页 / 筛选 / 排序
  - 岗位和简历列表都需要支持服务端分页。
  - 过滤字段至少覆盖 `status`、`updated_at`、关键关键词搜索。
- 鉴权与团队隔离
  - 所有列表与详情接口都只返回当前团队可见数据。
  - 软删除对象不应出现在列表；详情访问返回 `404`。
- 版本语义
  - “当前版本”是 `resumes.current_document_id` 指向的快照。
  - 历史版本接口只读，不提供原地覆盖。
- 渲染链语义
  - 预览与导出消费同一 Markdown 规则集。
  - 导出请求默认基于当前生效文档快照，而不是前端未保存草稿。
- 异步语义
  - 上传同步受理、转换异步。
  - 导出同步受理、生成异步。
  - 异步结果通过日志 / 记录接口查询，不通过长轮询阻塞创建接口。

## 6. 错误语义

- 鉴权失败：遵循 M02 的 `401 / 403 / 404` 基线。
- 资源不存在或已软删除：返回 `404`。
- 文件校验失败：
  - 非 PDF
  - 超出大小限制
  - 缺少必要字段
  - 在同步请求内直接失败，不创建异步任务。
- 转换失败：
  - 由 `resume_conversion_logs` 暴露失败状态和 `error_message`
  - 保留原始 PDF，不伪造成功文档。
- 导出失败：
  - 由 `resume_export_records` 暴露失败状态
  - 不影响当前 Markdown 版本。
- 保存冲突：
  - 已确认本轮不把 `base_version_no` 设为模块级必填。
  - 若后续需要显式冲突校验，再由 `ST03_02` 细化 `409 Conflict` 等契约。

## 7. 当前缺口

- DTO 字段命名的 camelCase / snake_case 细节尚未在模块内冻结。
- 版本保存的精确冲突返回契约留待 `ST03_02` 细化，但不再阻塞本轮模块推进。
- 原始 PDF / 导出 PDF 下载入口已确认复用共享下载能力，剩余只需在 `ST03_03` 落具体接口投影。

# M03 岗位、简历与文档处理 - API 设计

## 1. 文档定位

- 本文档用于沉淀本模块的接口清单与契约方向。
- 当前状态：高 `L4`，重点明确接口边界、同步/异步职责、最小查询键和跨模块归属；本轮按 `MR-27` 做上传 / 导出链依赖与开窗前置条件复核，并把结构性主阻塞继续收紧为“正式开窗层为空 + 当前阶段关窗 + 上传 / 导出链依赖未变”；高 `L4` 只作为这三项未解时的结果态，不作为额外独立问题；`OQ-021` / `OQ-025` 的最低位吸收口径保持不变。
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
- `requirement_items_json` 的写入责任按 `OQ-025` 的 `proposed-default` 口径吸收：
  - 最小 item 只要求 `item_key` / `text`
  - `null` 表示尚未完成结构化，`[]` 表示已结构化但当前无项
  - 仅岗位写模型允许整体替换；读模型与下游模块只消费，不反向补写
- 若岗位读取接口返回 `requirement_items_json`，当前最低位稳定口径也只覆盖同一最小集合：
  - `item_key`
  - `text`
  - `null / []` 语义
  - 数组顺序即消费顺序
- 任何扩展字段、派生摘要或页面展示专用结构都只属于未冻结附加信息：
  - 不得被 M04 / M06 当成稳定输入
  - 不得被 `MT03_01` / `MT03_03` 的 readiness 判断当成“岗位链已收口”的证据
- `OQ-025` 在 M03 最低位文档中允许冻结的最小共享输入只限下表：

| 最小共享输入项 | 当前最低位冻结口径 | 稳定边界 |
| --- | --- | --- |
| `jd_markdown` | 岗位正文 Markdown | 可作为下游只读输入引用，但不附带页面投影语义 |
| `requirement_items_json[*].item_key` | item 稳定标识 | 只承诺最小 item 键，不承诺扩展字段 |
| `requirement_items_json[*].text` | item 展示文本 | 只承诺文本本身，不承诺派生摘要 |
| `requirement_items_json = null` | 尚未完成结构化 | 不得被解释为“空要求” |
| `requirement_items_json = []` | 已结构化但当前无项 | 与 `null` 明确区分 |
| 数组顺序 | 即消费顺序 | M04 / M06 只可按当前顺序消费，不得反向定义排序规则 |
| 写入责任 | 仅岗位写模型可整体替换 | 下游读模型、页面投影与后续模块不得反向补写 |

- 上表是当前允许吸收到 M03 最低位文档的全部 `OQ-025` 最小共享输入；这里的“稳定”只表示接口最小载荷语义稳定，不等于岗位链整体 ready，也不放宽 `MT03_01` / `MT03_03` 的正式候选判断。
- 该口径当前只够支撑 M03 本模块设计、以及 M04 / M06 对岗位输入的最小设计引用；它不改变上传 / 转换 / 导出链的依赖判断，`MT03_06` / `MT03_07` / `MT03_08` 仍继续受 `OQ-007` 与 M01 共享下载 / 对象存储口径约束。
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

### 5.1 已吸收的共享最小查询键、URL / request 映射与模块级扩展
- 已与 `OQ-021` 的 `proposed-default` 口径对齐；M03 当前吸收的共享最小查询键集合为：
  - `page`
  - `page_size`
  - `q`
  - `status`
  - `sort`
  - `order`
- 本最低位文档对 `OQ-021` 只按三层状态吸收，边界如下：

| 层级 | 当前允许写入本最低位文档的内容 | M03 当前结论 |
| --- | --- | --- |
| 共享最小层 | query key、同名 request 字段、统一分页响应骨架 | 已冻结到 `page` / `page_size` / `q` / `status` / `sort` / `order` |
| 模块扩展层 | 仅 M03 自己消费的扩展查询键 | 只登记 `updated_after` / `updated_before`，且不得上升为共享前提 |
| 实现细节层 | route 段、callback 参数、alias、复杂筛选编码、adapter 双向序列化 | 不在模块最低位冻结，继续留给后续微任务 |

- 本节所说的“URL / request 映射”只指列表 query string key 到 request 字段的最小一一对应，不包含 route path 命名、前端 callback 参数签名或页面 adapter 内部状态映射。
- M03 在最低位文档内冻结的共享最小 URL / request 映射仅限下表：

| 共享 query key | 最小 request 字段 | 适用列表接口 | 层级 | 说明 |
| --- | --- | --- | --- | --- |
| `page` | `page` | `GET /api/v1/jobs`、`GET /api/v1/resumes` | 共享最小层 | 页码 |
| `page_size` | `page_size` | `GET /api/v1/jobs`、`GET /api/v1/resumes` | 共享最小层 | 每页条数 |
| `q` | `q` | `GET /api/v1/jobs`、`GET /api/v1/resumes` | 共享最小层 | 关键字搜索 |
| `status` | `status` | `GET /api/v1/jobs`、`GET /api/v1/resumes` | 共享最小层 | 生命周期状态筛选 |
| `sort` | `sort` | `GET /api/v1/jobs`、`GET /api/v1/resumes` | 共享最小层 | 排序字段 |
| `order` | `order` | `GET /api/v1/jobs`、`GET /api/v1/resumes` | 共享最小层 | 排序方向 |

- M03 可单独登记、但不属于共享最小映射的模块级扩展查询键为：
  - `updated_after`
  - `updated_before`
- 上表是当前允许写入模块共享契约的全部 `OQ-021` 最小映射；最低位文档不再为共享最小层登记别名、复合 query、路由派生值或 callback 参数签名。
- 共享最小 URL / request 映射只覆盖 `page / page_size / q / status / sort / order` 与统一分页骨架。
- `updated_after / updated_before` 当前只可作为 M03 模块级扩展，不得回写为共享最小映射，也不得被当成 `MT03_01 / MT03_03` 白名单 readiness 的共享前提。
- 若实现层需要别名兼容、复杂筛选编码或 route / callback / request adapter 细节，只能留在子任务级实现文档，不得反向写回本模块共享最小层。
- 模块级当前冻结“共享最小查询键”“模块扩展查询键”“分页响应骨架”以及与全局默认口径一致的最小 URL / request 映射；不冻结前端实现级 callback 签名与高级筛选双向序列化细节。

### 5.2 已冻结的最小响应骨架
- 列表集合统一复用分页骨架：`items`、`page`、`page_size`、`total`、`total_pages`。
- `GET /api/v1/jobs`
  - 每个列表项至少返回：`id`、`company`、`title`、`status`、`updated_at`
- `GET /api/v1/jobs/{job_id}`
  - 至少返回：岗位基础信息、`jd_markdown`、`requirement_items_json`、必要的跨模块引用字段
- `GET /api/v1/resumes`
  - 每个列表项至少返回：`id`、`name`、`source_type`、`status`、`current_document_id`、`updated_at`
- `GET /api/v1/resumes/{resume_id}`
  - 至少返回：简历基础信息、当前版本摘要、`original_pdf_object_id`、最近转换状态、最近导出状态
- `POST /api/v1/resumes/upload-pdf`
  - 至少返回：`resume_id`、`conversion_log_id` 与当前受理状态摘要
- `POST /api/v1/resumes/{resume_id}/export-pdf`
  - 至少返回：`export_record_id`、目标文档引用与当前受理状态摘要

### 5.3 已冻结的下载入口职责
- `GET /api/v1/resumes/{resume_id}/original-pdf`
  - 保留业务语义定位入口，用于从“简历”上下文访问原始 PDF。
- `GET /api/v1/storage-objects/{object_id}/download`
  - 仍是实际文件下载能力的唯一共享入口。
- 模块级冻结原则：
  - M03 不重复发明第二套下载权限逻辑。
  - `ST03_03` 只需把业务入口正确投影到共享下载能力，而不是重写共享网关。

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
- 原始 PDF / 导出 PDF 下载入口已确认复用共享下载能力，剩余只需在后续上传 / 导出相关微任务中落具体接口投影。
- `OQ-021` 的共享最小映射已在本最低位文档稳定吸收；剩余未冻结项只包括列表页实现级 callback 签名、复杂筛选编码与路由细节，这些仍属于子任务级待确认项。
- `OQ-025` 的最小共享输入已在岗位接口输入 / 输出语义中稳定吸收；剩余未冻结项只包括扩展字段、派生摘要与页面专用投影，这些仍不得被 API 文档写成稳定下游输入。
- `OQ-024` 的三层映射引用已按全局口径吸收到模块内：旧 `ST03_*` 只保留为历史容器、`MT03_01` / `MT03_03` 只保留为白名单观察蓝本、正式开窗层当前为空；这里的“为空”不是缺少命名入口，而是当前所有 `MT03_*` 要么仍只满足观察面输入、要么仍受共享契约和跨模块依赖约束，尚无任何一项同时满足“可作为正式候选输入 + 当前阶段允许开窗”这两个条件。
- 当前阶段仍关窗；关窗不是背景状态，而是直接阻塞项。按当前治理口径，在关窗状态解除前，即使 `MT03_01` / `MT03_03` 已具备局部可拆输入，也只能继续停留在白名单观察面，不得据此升级为正式候选。
- 上传 / 导出链依赖之所以仍未发生实质变化，是因为 `OQ-007` 当前仍只提供“上传同步受理、转换 / 导出异步”的共享最小语义，M01 的共享下载 / 对象存储口径也仍不足以支撑上传 / 导出链正式放行；`MQ-303` 只确认“业务入口映射到共享下载”，并没有把 `upload-pdf`、`export-pdf`、`original-pdf` 的放行前提在 M03 内单独闭合。
- 当前模块最低成熟度文档仍是高 `L4` 的 `MODULE_API_DESIGN.md`；但这不是独立第四问题，而是“正式开窗层为空 + 当前阶段关窗 + 上传 / 导出链依赖未变”共同回压后的结果态。只要本文件仍覆盖 `upload-pdf`、`export-pdf`、`original-pdf` 等接口，而上述三项未变，这份最低位文档就不能跨过正式候选门槛。
- `OQ-025` 的吸收当前只够支撑岗位域模块设计输入对齐，不足以放宽上传 / 导出相关微任务的依赖门槛；`MT03_06` / `MT03_07` / `MT03_08` 仍需等待 `OQ-007` 与 M01 共享下载 / 对象存储口径继续收口，因此上传 / 导出链依赖未变仍会回压整个 API 文档的放行判断。

### 7.1 当前为什么仍停在高 `L4`

- 共享最小层的吸收已基本完成：
  - `OQ-021` 已收敛到最小 query / request 映射与分页骨架
  - `OQ-025` 已收敛到最小岗位输入 / 输出语义
- 这些吸收只消除了局部共享契约缺口，不会单独产生正式候选资格。
- 本文档仍停在高 `L4` 的结构性主阻塞只剩三项：
  - 正式开窗层当前为空：没有任何 `MT03_*` 被提升为正式候选入口，因此 API 文档还不能从“观察蓝本”转为“正式子任务设计输入”
  - 当前阶段仍关窗：即使 `MT03_01` / `MT03_03` 局部输入已可复核，也只能维持观察面，不允许据此放行
  - 上传 / 导出链依赖未变：本 API 文档覆盖的上传、导出与业务下载入口仍受 `OQ-007` 与 M01 共享下载 / 对象存储口径约束；这部分未收口前，整份 API 文档不能被视为正式候选输入
- 因此，高 `L4` 只是上述三项未解时的结果态，不是独立第四阻塞。

### 7.2 离正式候选还差的最小条件

- 总控把正式开窗层从“当前为空”推进到至少一个明确的正式候选入口；观察蓝本不计入正式开窗层。
- 总控明确结束当前阶段关窗状态，允许把模块层观察输入重新评估为正式子任务设计候选输入。
- 上传 / 导出链依赖判断发生实质收口，至少不再让 `upload-pdf`、`export-pdf`、`original-pdf` 这些接口继续作为整份 API 文档的结构性阻塞；单独润色 API 文案不构成收口。

# M03 岗位、简历与文档处理 - 模块设计

## 1. 文档定位

- 本文档用于把模块需求转为模块级结构设计。
- 当前状态：可评审草案，仍未达到可直接作为子任务输入的 `L5`。
- 本文档重点解决三类边界：
  - 岗位域与简历域的对象边界
  - Markdown 渲染链与导出链路边界
  - M03 与 M04-M06 的模块协作边界

## 2. 模块职责边界

### 2.1 M03 负责
- 岗位基础对象与岗位页面基础数据面。
- 简历聚合根、当前文档指针、版本快照与编辑页主流程。
- 原始 PDF 上传、对象存储引用、转换日志和导出记录。
- 对下游暴露“当前岗位输入”和“当前简历正文输入”的稳定数据面。

### 2.2 M03 不负责
- `job_resume_bindings`、`job_resume_match_analyses`、`weakness_evidences`，由 M04 承接。
- 资产归档、检索分块与向量化，由 M05 承接。
- 模拟面试上下文包组装、会话导出和 search snapshot，由 M06 承接。
- 对象存储 SDK、任务调度器、统一下载网关本身的技术实现，由 M01 / 基础设施承接。

### 2.3 设计前提
- 鉴权默认使用 M02 冻结的 Bearer token 方案。
- 所有 M03 对象都遵守团队隔离与软删除基线。
- `OQ-006`、`OQ-007` 已视为当前设计输入，而不是待决前提。

## 3. 模块内组件拆分

| 组件 | 主要职责 | 直接产物 | 下游使用方 |
| --- | --- | --- | --- |
| 岗位域 | 管理 `jobs`，沉淀 JD 正文与结构化要求 | 岗位列表/详情基础数据 | M04、M06 |
| 简历聚合根 | 管理 `resumes` 与 `current_document_id` | 当前简历摘要、编辑入口 | M04、M06 |
| 版本快照层 | 管理不可变 `resume_documents` | 当前正文、历史版本 | M04、M06 |
| 文件接入层 | 管理原始 PDF 上传、对象元数据入库、转换日志创建 | `storage_objects` 引用、`resume_conversion_logs` | M05 |
| 渲染链 | 统一 Markdown 预览与导出所依赖的渲染规则 | 预览结果、导出输入 | M03 内部，M06 可复用理念 |
| 导出链路 | 管理导出请求、记录、产物对象引用 | `resume_export_records`、导出文件引用 | M05 |

## 4. 跨模块协作点

| 协作方 | M03 依赖 / 输出 | 当前口径 | 风险说明 |
| --- | --- | --- | --- |
| M01 | 依赖对象存储抽象、任务调度、统一下载能力、工作台壳层与测试基线 | 已有全局默认方案，但模块文档仍低成熟度 | 影响 ST03_03 的技术实现，但不阻止本轮评审 |
| M02 | 依赖 Bearer token、`team_id` 隔离、权限矩阵与软删除访问规则 | 已有全局默认方案与计划基线 | 影响鉴权与 401/403/404 细节，不应在 M03 重写 |
| M04 | 向下游输出岗位正文、结构化要求、当前简历正文、版本关系 | `job_resume_bindings` 与匹配分析明确不属于 M03 | M04 可稳定依赖输入面，但不能反向要求 M03 提供分析对象 |
| M05 | 向下游输出原始 PDF / 导出 PDF 的对象引用和来源链路 | `resume_documents` 不进入共享向量库 | M05 可消费产物与来源，不应把简历正文当长期资产切块 |
| M06 | 向下游输出岗位结构化要求与当前简历正文 | 上下文包固定装配顺序中包含岗位要求和当前简历正文 | M06 可稳定依赖正文输入，但不应依赖转换日志内部 JSON 细节 |

## 5. 核心对象关系与数据流

### 5.1 对象关系
- `jobs`
  - 保存岗位基础信息、JD 正文和结构化要求。
- `resumes`
  - 通过 `original_pdf_object_id` 指向原始 PDF。
  - 通过 `current_document_id` 指向当前生效的 `resume_documents`。
- `resume_documents`
  - 与 `resumes` 是 `1:N` 关系。
  - 每次保存或转换成功都新增快照。
- `resume_conversion_logs`
  - `source_object_id -> storage_objects.id`
  - `target_document_id -> resume_documents.id`
- `resume_export_records`
  - `document_id -> resume_documents.id`
  - `output_object_id -> storage_objects.id`

### 5.2 数据流
1. 岗位创建或编辑后，`jobs` 直接成为 M04/M06 的上游输入。
2. 简历创建或保存后，`resume_documents.markdown_content` 成为当前唯一正文来源。
3. PDF 上传先形成 `storage_objects` 与 `resume_conversion_logs`，再异步产出 `resume_documents`。
4. 导出请求先形成 `resume_export_records`，再异步产出导出文件和 `storage_objects` 引用。
5. M03 不创建岗位-简历绑定；绑定关系由 M04 在消费 `jobs` 与 `resumes` 后建立。

## 6. 关键状态变化

### 6.1 简历生命周期语义
- Markdown 新建简历：
  - 创建 `resumes`
  - 同步创建首个 `resume_documents`
  - `current_document_id` 立即可用
- PDF 导入简历：
  - 创建 `storage_objects`
  - 创建 `resumes`
  - 创建一条待处理 `resume_conversion_logs`
  - 转换成功后才生成首个 `resume_documents`

### 6.2 版本语义
- `resume_documents` 一旦创建即不可变。
- “当前版本”由 `resumes.current_document_id` 表示。
- 恢复历史版本不修改旧记录，而是新增一个新版本快照并切换指针。

### 6.3 异步记录语义
- `resume_conversion_logs`
  - 至少需要区分：已受理、处理中、成功、失败。
- `resume_export_records`
  - 至少需要区分：已受理、处理中、成功、失败。
- 异步记录是任务状态的事实来源，不应把状态只塞在前端本地内存里。

## 7. 风险点与评审关注点

- 共用渲染链是否真正做到“同一规则集”，而不是两套实现碰巧看起来相近。
- M03 与 M04 的边界是否足够清晰，尤其是 `job_resume_bindings` 不能被 M03 抢占。
- M03 与 M05 的边界是否足够清晰，尤其是 `resume_documents` 不得直接进入共享资产向量库。
- M01/M02 文档成熟度仍低，意味着 M03 只能把依赖写清，不能把未冻结的上游契约硬写成实现事实。
- 简历编辑保存冲突策略未冻结，会影响 ST03_02 的接口设计深度。

## 8. 测试策略

- API 层：
  - 岗位与简历 CRUD 的基础成功路径。
  - 未登录、跨团队、软删除资源访问的鉴权矩阵用例。
  - PDF 上传同步受理、导出同步受理的状态码断言。
- 服务层：
  - 上传落库与转换日志创建的原子性。
  - 转换成功后切换 `current_document_id` 的一致性。
  - 导出记录与产物对象引用更新的一致性。
- 前端 / 浏览器层：
  - 简历编辑页双栏或移动端切换布局。
  - 预览与导出在标题、列表、表格、代码块等规则上的一致性。
  - 版本历史、转换日志、导出记录不打断主编辑流。

## 9. 当前设计缺口

- `jobs.status` / `resumes.status` 的精确枚举尚未冻结。
- 版本保存的并发冲突策略尚未冻结。
- 业务下载入口与共享下载入口的职责分工尚待评审确认。

## 10. 关联文档

- `MODULE_REQUIREMENTS.md`
- `MODULE_API_DESIGN.md`
- `MODULE_SCHEMA_DESIGN.md`
- `MODULE_LOGIC_DESIGN.md`
- `MODULE_DEPENDENCIES.md`
- `MODULE_OPEN_QUESTIONS.md`

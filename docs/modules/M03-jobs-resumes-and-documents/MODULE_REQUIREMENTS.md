# M03 岗位、简历与文档处理 - 模块需求

## 1. 文档定位

- 本文档用于把原始需求和原始实施计划中与“岗位、简历与文档处理”相关的内容提炼成模块级需求。
- 当前状态：稳定候选，建议按 `L5` 候选看待，并由总控 Codex 决定是否正式登记。
- 本轮判断：
  - 模块级边界、最小字段面、同步/异步职责和下游输出面已经收口到可作为子任务设计输入的程度。
  - 仍存在少量共享 UI / 列表交互口径待总控继续收口，但不再阻塞模块级核心契约进入 `L5` 候选。
- 下游输入目标：`MODULE_DESIGN.md`、`MODULE_API_DESIGN.md`、`MODULE_SCHEMA_DESIGN.md`、`MODULE_LOGIC_DESIGN.md`。
- 本轮冻结口径：
  - `OQ-006`：Markdown 预览与导出共用同一渲染链。
  - `OQ-007`：上传同步入库，转换与导出异步执行。

## 2. 来源文档

### 2.1 原始需求引用
- `docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md`：3.3 简历处理边界
- `docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md`：7.2 岗位与简历
- `docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md`：9.1 简历导入与编辑
- `docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md`：9.2 岗位创建与简历绑定
- `docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md`：15.2 岗位模块
- `docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md`：15.3 简历模块

### 2.2 原始实施计划引用
- `docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md`：326-334 岗位与简历域
- `docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md`：389-411 岗位与简历 API
- `docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md`：479-505 页面与路由总表
- `docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md`：506-576 通用模型字段与核心表字段设计
- `docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md`：722-778 对象存储、Markdown 预览与导出约束
- `docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md`：1937-2334 任务 4

### 2.3 全局与上游约束引用
- `PLAN_LATEST.md`：M03 在 `M01 -> M02 -> M03` 顺序中承接岗位、简历与文档链路。
- `TECHNICAL_STANDARDS.md`：默认技术口径为 Next.js + FastAPI + PostgreSQL + Redis + S3-compatible 对象存储。
- `DESIGN_DECISIONS.md`：文档体系分层、单次实施单位、Markdown 渲染链共享等全局口径。
- `OPEN_QUESTIONS.md`：`OQ-006`、`OQ-007` 已按默认方案冻结，可作为本轮 M03 设计输入。
- `docs/modules/M01-foundation-and-platform/**`：提供 monorepo、对象存储、工作台壳层、日志与测试基线。
- `docs/modules/M02-identity-and-team/**`：提供 Bearer token、`team_id` 隔离与权限矩阵基线。

## 3. 模块目标

- 定义岗位、简历、文档版本、上传、转换、预览与导出的模块边界。
- 明确同步链路与异步链路的分界，避免把耗时任务塞进请求线程。
- 为 M04-M06 提供稳定的岗位正文、结构化要求、当前简历正文、版本记录和文件产物引用。

## 4. 模块范围内

- 岗位对象与岗位列表/详情页的基础数据面。
- 简历对象、当前文档指针、版本快照与 Markdown 编辑/预览。
- 原始 PDF 上传、对象存储入库、转换日志、导出记录。
- 原始 PDF 与导出 PDF 的业务级访问入口，以及它们与共享 `storage_objects` 的映射关系。
- 面向下游模块的稳定输入面：
  - `jobs.jd_markdown`
  - `jobs.requirement_items_json`
  - `resumes.current_document_id`
  - `resume_documents.markdown_content`
  - `resume_conversion_logs`
  - `resume_export_records`

## 5. 不在本模块范围内

- 岗位与简历绑定关系、匹配分析、缺口项与训练证据输出，由 M04 承接。
- 资产归档、检索分块、向量化入库，由 M05 承接。
- 模拟面试上下文包装配、会话导出、search snapshot，由 M06 承接。
- 多格式解析矩阵、复杂协同编辑、语音/视频简历处理，不纳入 P1 本轮。

## 6. 关键角色与对象

### 6.1 关键角色
- 当前登录用户：来自 M02 的鉴权上下文，所有读写请求必须带 `team_id` 作用域。
- 团队管理员 / 普通成员：权限矩阵由 M02 提供，M03 只消费“本团队可访问”的基线，不在本文件内重新定义角色契约。

### 6.2 核心对象
- `jobs`
  - 团队级岗位对象，保存 JD 正文、结构化要求和列表筛选所需状态。
- `resumes`
  - 简历聚合根，负责连接原始 PDF、当前 Markdown 文档和对外状态摘要。
- `resume_documents`
  - 简历 Markdown 的不可变版本快照，是当前编辑结果与下游引用的正文来源。
- `storage_objects`
  - 共享文件元数据对象，M03 通过 `original_pdf_object_id` 和 `output_object_id` 建立原件/导出件引用。
- `resume_conversion_logs`
  - PDF 转 Markdown 的异步执行日志，记录输入原件、解析器版本、耗时和失败原因。
- `resume_export_records`
  - 导出请求的异步执行日志，记录导出来源文档、状态和产物对象。

## 7. 关键流程

### 7.1 岗位创建与编辑
1. 当前用户在岗位页创建岗位，提交公司、岗位名、JD 正文及结构化要求。
2. 服务端在团队作用域内创建 `jobs` 记录，并返回岗位详情基础数据。
3. 岗位详情页后续可展示与 M04 关联的绑定、匹配分析和训练入口，但这些对象不由 M03 创建。

### 7.2 Markdown 简历创建、保存与版本快照
1. 当前用户以 Markdown 直接新建简历，生成 `resumes` 记录和首个 `resume_documents` 快照。
2. 用户在编辑页修改 Markdown，保存时新增一条不可变 `resume_documents` 记录。
3. `resumes.current_document_id` 指向最新成功保存的版本。
4. 版本历史、导出记录、转换日志为编辑页的辅助区，不打断主编辑流。

### 7.3 PDF 上传、转换与预览
1. 用户上传 PDF。
2. 服务端同步完成文件校验、对象存储写入和 `storage_objects` / `resumes` / `resume_conversion_logs` 的初始落库。
3. 上传接口返回已受理状态，转换任务异步执行 `PDF -> Markdown`。
4. 转换成功后生成新的 `resume_documents` 快照，并更新 `resumes.current_document_id`；失败时保留原始 PDF 和失败日志。

### 7.4 导出
1. 用户基于当前 Markdown 发起 PDF 导出请求。
2. 服务端同步创建 `resume_export_records` 并返回受理结果。
3. 导出任务异步读取指定文档快照，通过与预览一致的渲染链生成 PDF。
4. 产物写入 `storage_objects`，导出记录更新为完成状态，并暴露业务级下载入口。

## 8. 业务规则与验收边界

- 所有正式领域对象必须带 `team_id`，并遵守统一软删除字段与访问过滤规则。
- `jobs` 与 `resumes` 均是团队级对象；`owner_user_id` 用于归属与审计，不作为跨团队之外的唯一访问边界。
- `resume_documents` 必须保持不可变；“保存”表示新增版本，而不是原地覆盖旧版本。
- `OQ-006` 的影响必须显式落到设计上：
  - 预览与导出共享同一渲染规则集。
  - 不能分别维护两套 Markdown 语义并期待结果一致。
- `OQ-007` 的影响必须显式落到链路上：
  - 上传必须同步完成文件落库和业务受理。
  - 转换与导出必须以任务记录驱动，不在请求线程内完成。
- `resume_documents` 不进入共享资产向量库；M05/M06 只消费它的正文结果，不把它当长期知识资产存入 `retrieval_chunks`。

## 9. 对下游文档的输出要求

- `MODULE_DESIGN.md` 需要把“岗位域 / 简历域 / 渲染链 / 上传转换 / 导出”拆成稳定职责图。
- `MODULE_API_DESIGN.md` 需要明确哪些接口是同步创建，哪些接口只做异步受理，以及哪些接口不属于 M03。
- `MODULE_SCHEMA_DESIGN.md` 需要明确对象关系、字段约束、版本不可变规则和文件引用关系。
- `MODULE_LOGIC_DESIGN.md` 需要明确保存、转换、导出、失败补偿和状态更新顺序。
- `MODULE_DEPENDENCIES.md` 需要明确 M04-M06 可以稳定依赖哪些输出，以及仍不能依赖哪些未冻结细节。

## 10. L5 候选判定基线

### 10.1 已冻结且可作为子任务设计输入

- 模块边界已稳定：
  - M03 只负责岗位、简历、版本快照、上传/转换/导出链路以及对应的文件对象引用。
  - 岗位-简历绑定、匹配分析、资产归档与面试上下文组装明确留给 M04-M06。
- 领域对象最小字段面已稳定：
  - `jobs`、`resumes`、`resume_documents`、`resume_conversion_logs`、`resume_export_records` 与共享 `storage_objects` 的最小字段面已对齐源计划。
  - `resume_documents.markdown_content` 与 `resumes.current_document_id` 已明确为下游稳定输入。
  - `jobs.requirement_items_json` 已形成模块层 `proposed-default` 最小契约候选：JSON array item 至少含 `item_key` / `text`，`null` 表示未完成结构化，`[]` 表示已结构化但无项，数组顺序即消费顺序；是否升级为全局稳定输入仍待 `MQ-307` / `OQ-025` 收口。
- 关键业务规则已稳定：
  - 预览与导出共用同一 Markdown 渲染链。
  - 上传同步入库并受理，转换与导出异步执行。
  - 简历保存始终新增不可变快照，不原地覆盖旧版本。
  - 原始 PDF / 导出 PDF 保留业务级入口，但真实文件下载复用共享下载能力。
- 面向下游模块的输出面已稳定：
  - 面向 M04：岗位正文、结构化要求、当前简历正文与版本指针。
  - 面向 M05：原始 PDF / 导出 PDF 的对象引用与转换/导出记录。
  - 面向 M06：岗位结构化要求、岗位正文与当前简历正文。

### 10.2 仍留给后续微任务级细化，但不阻塞模块进入 L5 候选

- `jobs.status`、`resumes.status` 的精确枚举值留待岗位 / 简历相关微任务细化；模块级只冻结“必须存在可筛选状态字段与生命周期语义”。
- 简历编辑保存的精确冲突返回契约留待简历版本相关微任务细化；模块级只冻结“保存会新增不可变快照，`base_version_no` 不是模块级必填”。
- 原始 PDF / 导出 PDF 的业务入口到共享下载能力的具体投影方式留待上传 / 导出相关微任务细化；模块级只冻结“业务入口保留、下载能力复用”。

### 10.3 当前剩余阻塞与待确认

- `OQ-021`：列表查询状态、分页交互与 URL / callback 的统一映射已形成全局 `proposed-default`，但实现级 URL / callback 细节仍未定稿，继续影响 `jobs` / `resumes` 列表页和相关 API 的最终页面态设计。
- `OQ-020`：共享页面头部与摘要区的最小接口边界已形成全局 `proposed-default`，但实现级 props / slot 细节仍未定稿，继续影响岗位页与简历页的共享 UI 口径收口。
- M01 共享下载能力与对象存储实现细节成熟度仍偏低，影响上传 / 导出相关微任务的实施级方案深度，但不阻塞模块级任务重切继续推进。
- `jobs.requirement_items_json` 虽已形成模块层候选口径，但总控尚未把它升级为全局默认冻结；在 `OQ-025` 收口前，下游只可依赖 `item_key` / `text` 与数组顺序，不得依赖扩展字段。

## 11. 当前已确认口径

- 全局默认冻结候选并可直接使用：
  - `OQ-006`：Markdown 预览与导出共用同一渲染链。
  - `OQ-007`：上传同步入库，转换与导出异步执行。
- 本轮模块内已确认：
  - `MQ-301`：保存会新增不可变版本快照，`base_version_no` 不设为模块级必填。
  - `MQ-302`：本轮必须存在可筛选状态字段与生命周期语义，但不在模块级冻结最终枚举表。
  - `MQ-303`：保留业务入口定位资源，真实文件下载统一复用共享下载能力。

## 12. 关联文档

- `MODULE_DESIGN.md`
- `MODULE_API_DESIGN.md`
- `MODULE_SCHEMA_DESIGN.md`
- `MODULE_LOGIC_DESIGN.md`
- `MODULE_TASK_INDEX.md`
- `MODULE_DEPENDENCIES.md`
- `MODULE_OPEN_QUESTIONS.md`

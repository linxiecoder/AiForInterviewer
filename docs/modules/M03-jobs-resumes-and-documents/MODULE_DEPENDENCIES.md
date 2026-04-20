# M03 岗位、简历与文档处理 - 模块依赖

## 1. 上游输入

| 来源 | 当前可引用输入 | 当前状态判断 | 对 M03 的影响 |
| --- | --- | --- | --- |
| `PLAN_LATEST.md` / `TECHNICAL_STANDARDS.md` / `DESIGN_DECISIONS.md` | monorepo、Next.js + FastAPI、PostgreSQL、Redis、S3-compatible 存储、文档分层规则 | 可引用 | 作为架构与文档治理总口径 |
| `OPEN_QUESTIONS.md` | `OQ-006`、`OQ-007` 的默认冻结方案 | 可引用 | 允许把渲染链共享、上传同步/转换导出异步写入 M03 设计 |
| M01 | 对象存储默认形态、统一下载能力、工作台壳层、日志与测试基线 | 部分可引用，模块文档本身仍低成熟度 | 可用于描述依赖方向，暂不应把实现细节写死 |
| M02 | Bearer token、`team_id` 隔离、权限矩阵与软删除访问规则 | 部分可引用，模块文档本身仍低成熟度 | 可用于约束鉴权与访问语义，暂不应在 M03 重写权限细节 |

## 2. 下游承接子任务

- `ST03_01` 岗位域与页面
- `ST03_02` 简历域、版本与编辑器
- `ST03_03` 上传、转换与导出链路

## 3. 面向 M04-M06 的稳定输出

### 3.1 面向 M04
- 可稳定引用：
  - `jobs.id`
  - `jobs.jd_markdown`
  - `jobs.requirement_items_json`
  - `resumes.id`
  - `resumes.current_document_id`
  - `resume_documents.markdown_content`
- 不应从 M03 引用：
  - `job_resume_bindings`
  - `job_resume_match_analyses`
  - 训练证据对象

### 3.2 面向 M05
- 可稳定引用：
  - 原始 PDF 的 `storage_objects` 引用
  - 导出 PDF 的 `storage_objects` 引用
  - `resume_conversion_logs`
  - `resume_export_records`
- 需要显式遵守：
  - `resume_documents` 不进入共享 `retrieval_chunks`
  - M05 若要归档简历相关内容，应基于业务选择的导出产物或显式归档流程，而不是直接把当前简历正文当共享知识资产

### 3.3 面向 M06
- 可稳定引用：
  - `jobs.requirement_items_json`
  - `jobs.jd_markdown`
  - `resumes.current_document_id`
  - `resume_documents.markdown_content`
- 需要显式遵守：
  - M06 消费的是“当前简历正文”，不是转换日志内部细节
  - M06 不应依赖 `summary_json` 这类未冻结内部 JSON 结构

## 4. 依赖门槛判断

- 进入 M03 模块评审：
  - 当前已满足
  - 因为全局默认口径和源计划已足以支撑 reviewable 文档
- 进入 M03 子任务设计：
  - 当前未满足
  - 原因：
    - 本轮 M03 目标只到 `L4` 可评审，尚未到 `L5`
    - M01 / M02 的模块级文档仍未达到可稳定下游输入
    - `MQ-301`、`MQ-302`、`MQ-303` 已确认默认方案，但相关子任务级细化尚未完成
- 进入 M03 子任务实施：
  - 当前不满足
  - 原因：
    - 子任务双文档仍为骨架
    - 上游模块设计和共享契约尚未全部稳定

## 5. 当前依赖风险

- M01 只给出了方向性基础设施约束，尚未提供高成熟度模块级实施输入。
- M02 已给出权限矩阵基线，但接口级和对象级细节仍未在模块文档中沉淀。
- 共享文件下载投影面仍依赖 M01 / 基础设施评审结果。
- 如果后续 `OQ-006` 或 `OQ-007` 被全局改写，M03 设计包需要整体回看。

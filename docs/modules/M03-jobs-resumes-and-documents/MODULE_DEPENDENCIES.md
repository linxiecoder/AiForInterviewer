# M03 岗位、简历与文档处理 - 模块依赖

## 1. 上游输入

| 来源 | 当前可引用输入 | 当前状态判断 | 对 M03 的影响 |
| --- | --- | --- | --- |
| `PLAN_LATEST.md` / `TECHNICAL_STANDARDS.md` / `DESIGN_DECISIONS.md` | monorepo、Next.js + FastAPI、PostgreSQL、Redis、S3-compatible 存储、文档分层规则 | 可引用 | 作为架构与文档治理总口径 |
| `OPEN_QUESTIONS.md` | `OQ-006`、`OQ-007` 的默认冻结方案 | 可引用 | 允许把“共享渲染链”“上传同步受理、转换/导出异步”写入模块层设计 |
| `OPEN_QUESTIONS.md` | `OQ-020`：共享页面头部与摘要区的最小接口边界 | 已形成全局 `proposed-default`，但仍不应扩写成实现级 props catalog | 影响 `jobs` / `resumes` 页面微任务，当前不适合下放到旧 `ST03_01` / `ST03_02` |
| `OPEN_QUESTIONS.md` | `OQ-021`：列表查询状态、分页交互与 URL / callback 的统一映射规则 | 已形成全局 `proposed-default`，但仍只覆盖最小 shared contract | 影响 `jobs` / `resumes` 列表 API 与页面微任务，当前不适合下放到旧 `ST03_01` / `ST03_02` |
| M01 | 对象存储默认形态、统一下载能力、工作台壳层、日志与测试基线 | 方向可引用，但共享下载 / 对象存储实现口径成熟度仍不足 | 直接限制上传、导出与下载投影相关微任务是否能并行推进 |
| M02 | Bearer token、`team_id` 隔离、权限矩阵与软删除访问规则 | 方向可引用，但接口级和页面级细节仍未全部成熟 | 影响岗位 / 简历页面的数据可见性与错误语义，但不应在 M03 重写权限契约 |

## 2. 旧切分入口的依赖问题

| 旧入口 | 被混在一起的依赖 | 为什么会导致错误进入子任务阶段 |
| --- | --- | --- |
| `ST03_01` | `jobs` 领域契约 + `OQ-020` + `OQ-021` + M02 页面可见性语义 + 页面实施骨架 | 一个入口同时吃掉领域、列表、详情页和共享 UI / list 契约，无法形成可验证、可并行的子任务边界 |
| `ST03_02` | 简历聚合根 + 版本不变量 + `OQ-006` + `OQ-020` + `OQ-021` + 编辑器页面交互 | 一个入口同时承担领域不变量和页面交互，导致“只看标题像子任务，实际仍是模块层设计包” |
| `ST03_03` | `OQ-007` + M01 对象存储 / 共享下载 + 转换 / 导出状态机 + 业务下载入口投影 | 一个入口跨越上传、转换、导出三条链路，既不能并行，也无法在上游不稳定时形成独立验证点 |

## 3. 模块层必须先冻结的前置依赖

| 前置项 | 当前状态 | 影响微任务 | 当前判断 |
| --- | --- | --- | --- |
| `jobs.requirement_items_json` 最小结构与字段责任 | `proposed-default`（模块层候选） | `MT03_01`、`MT03_02A`、`MT03_02B`，以及 M04 / M06 下游消费 | 已上提到模块层，可作为岗位链首开输入；仍待总控决定是否升格为 `OQ-025` 默认口径 |
| `jobs.status` / `resumes.status` 生命周期语义 | 已冻结到语义层，未冻结到枚举层 | `MT03_01`、`MT03_02A`、`MT03_02B`、`MT03_03`、`MT03_04` | 允许继续做微任务设计，但不允许各微任务自行发明最终枚举 |
| `current_document_id` / `version_no` / 保存新增快照规则 | 已冻结到模块层 | `MT03_03`、`MT03_04`、`MT03_05` | 可以作为后续微任务设计输入 |
| `OQ-020` 共享页面原语最小边界 | `proposed-default` | `MT03_02B`、`MT03_05` | 作为候选输入可引用，但不适合本轮直接开页面微任务 |
| `OQ-021` 列表 shared contract | `proposed-default` | `MT03_02A`、`MT03_05` | 作为候选输入可引用，但仍需保留实现级风险位 |
| M01 共享下载 / 对象存储口径 | 成熟度不足 | `MT03_06`、`MT03_07`、`MT03_08` | 仍是上传/导出相关微任务的主要阻塞 |

## 4. 重切后的微任务依赖矩阵

| 微任务 ID | 直接依赖 | 当前主要阻塞 | 并行组 | 当前判断 |
| --- | --- | --- | --- | --- |
| `MT03_01` | `MODULE_REQUIREMENTS.md`、`MODULE_DESIGN.md`、`MODULE_SCHEMA_DESIGN.md` | `OQ-025` 尚未全局冻结，但模块层已给出最小候选契约 | A | 可先按模块候选口径开设计，不得新增 item schema 义务 |
| `MT03_02A` | `MT03_01`、`MQ-302`、`OQ-021`、M02 页面可见性基线 | 列表 shared contract 仍只有默认候选 | B | `OQ-021` 进一步收敛后可单独启动 |
| `MT03_02B` | `MT03_01`、`OQ-020`、M02 页面可见性基线 | 详情页摘要 / 页面原语仍只有默认候选 | B | `OQ-020` 进一步收敛后可单独启动 |
| `MT03_03` | `MODULE_DESIGN.md`、`MODULE_SCHEMA_DESIGN.md`、`MODULE_LOGIC_DESIGN.md` | 仅剩状态精确枚举未细化 | A | 模块层补齐后可优先启动 |
| `MT03_04` | `MT03_03`、`MQ-301` | 依赖聚合根与版本不变量先稳定 | 串行 | 不建议与 `MT03_03` 同时开启 |
| `MT03_05` | `MT03_03`、`MT03_04`、`OQ-006`、`OQ-020`、`OQ-021` | 页面共享契约与版本接口仍未同时稳定 | B | 共享契约冻结后可并行 |
| `MT03_06` | `OQ-007`、M01 对象存储基线 | M01 成熟度不足 | D | 等待 M01 |
| `MT03_07` | `MT03_06`、`OQ-007` | 上传受理契约未稳定 | E | `MT03_06` 稳定后再开 |
| `MT03_08` | `MT03_03`、`OQ-006`、`OQ-007`、M01 共享下载口径 | M01 共享下载口径未成熟 | E | 等待 M01 后与 `MT03_07` 并行 |

## 5. 面向 M04-M06 的输出 readiness

### 5.1 面向 M04
- 当前可稳定引用：
  - `jobs.id`
  - `jobs.jd_markdown`
  - `jobs.requirement_items_json[*].item_key`
  - `jobs.requirement_items_json[*].text`
  - `jobs.requirement_items_json` 的数组顺序
  - `resumes.id`
  - `resumes.current_document_id`
  - `resume_documents.markdown_content`
- 当前仍不能宣称完全稳定：
  - `jobs.requirement_items_json` 的扩展字段
  - 原因：模块层已形成 `proposed-default` 最小契约，但 `OQ-025` 尚未在总控层完成默认冻结
- 不应从 M03 引用：
  - `job_resume_bindings`
  - `job_resume_match_analyses`
  - 训练证据对象

### 5.2 面向 M05
- 当前可稳定引用：
  - 原始 PDF / 导出 PDF 对应的对象引用关系
  - `resume_conversion_logs`
  - `resume_export_records`
- 当前仍需保留风险位：
  - 上传、导出与共享下载网关的实现投影细节
- 需要显式遵守：
  - `resume_documents` 不进入共享 `retrieval_chunks`
  - M05 若要归档简历相关内容，应基于业务显式选择的导出产物或归档流程，而不是直接把当前简历正文当共享知识资产

### 5.3 面向 M06
- 当前可稳定引用：
  - `jobs.jd_markdown`
  - `jobs.requirement_items_json[*].item_key`
  - `jobs.requirement_items_json[*].text`
  - `jobs.requirement_items_json` 的数组顺序
  - `resumes.current_document_id`
  - `resume_documents.markdown_content`
- 当前仍不能宣称完全稳定：
  - `jobs.requirement_items_json` 的扩展字段
  - 原因：与 M04 一致，模块层只有最小候选契约，`OQ-025` 尚未全局冻结
- 需要显式遵守：
  - M06 消费的是“当前简历正文”，不是转换日志内部细节
  - M06 不应依赖 `summary_json` 这类未冻结内部 JSON 结构

## 6. 依赖门槛判断

- 进入 M03 模块评审：
  - 当前已满足
  - 原因：全局默认口径与当前模块文档已足以支撑 reviewable 级评审
- 进入 M03 微任务设计：
  - 当前仍不满足“批量开启”
  - 主要原因：
    - 旧 `ST03_*` 入口已经被判定为错误切分，必须先完成任务重切后的全局索引同步
    - `OQ-020`、`OQ-021` 和 M01 共享下载口径仍会直接影响页面 / 下载相关微任务
  - 但局部判断：
    - `MT03_01` 已具备岗位链首开候选条件，只能按模块层 `proposed-default` 契约推进，不得再改 item schema
- 进入 M03 微任务实施：
  - 当前不满足
  - 原因：
    - 还没有新的微任务双文档
    - 上游共享契约尚未全部稳定
    - 当前子任务骨架仍存在模板与成熟度问题

## 7. 当前依赖风险

- M01 仍只给出了方向性基础设施约束，尚未提供足以支撑上传 / 导出微任务的高成熟度下载与对象存储口径。
- M02 已给出权限矩阵基线，但页面级和接口级的最终细节仍不适合在 M03 内部重写。
- `jobs.requirement_items_json` 已形成模块层最小候选契约，但 `OQ-025` 尚未全局冻结，扩展字段仍不可依赖；若总控改写默认口径，岗位链 `MT03_01` / `MT03_02A` / `MT03_02B` 需同步回看。
- `OQ-021` 与 `OQ-020` 当前都只应被视为 shared contract 候选输入，仍不足以让旧 `ST03_01` / `ST03_02` 直接开窗。
- 如果后续 `OQ-006`、`OQ-007` 或 M01 共享下载口径被改写，M03 的上传 / 导出 / 预览相关微任务切分需要整体回看。

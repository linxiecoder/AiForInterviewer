# AI 模拟面试 P1 文档进展

## 1. 文档定位

- 本文档用于跨轮次跟踪文档体系建设进度，而不是只跟踪代码实施进度。
- 每轮工作结束后，应同步更新本文件以及 `DOCUMENT_MATURITY.md`、`OPEN_QUESTIONS.md`。
- 本文档由总控 Codex 主责维护，用于明确当前阶段、当前阻塞、当前并行任务包和下一轮优先级。

## 2. 阶段定义

| 阶段 | 名称 | 目标 | 完成标志 |
| --- | --- | --- | --- |
| 阶段 1 | 建立全局文档骨架 | 建立总控、索引、规则、成熟度和开放问题入口 | 全局文档可评审 |
| 阶段 2 | 建立模块目录与基础需求 | 建立模块目录、需求、依赖、任务与问题入口 | 模块目录齐全，模块需求进入初稿 |
| 阶段 3 | 细化模块设计 | 完成模块设计、API、Schema、Logic 首轮草稿 | 优先模块进入可评审 |
| 阶段 4 | 细化子任务设计 | 让优先子任务 `SUBTASK_DESIGN.md` 达到可作为下游输入 | 可支撑实施准备 |
| 阶段 5 | 生成实施文档 | 把优先子任务 `SUBTASK_IMPLEMENTATION.md` 细化到可执行 | 至少一批子任务达到可直接实施 |
| 阶段 6 | 代码实施与持续回写 | 进入子任务级实施，并持续维护索引、成熟度和日志 | 文档与实施双向闭环 |

## 3. 当前状态

- 当前阶段：阶段 2
- 阶段目标：从“模块目录与基础需求”推进到“基础模块设计可评审”
- 已完成事项：
  - 修复全局入口和总控文档乱码。
  - 建立根目录全局文档体系。
  - 建立 `docs/modules/` 模块目录与模块骨架。
  - 建立模块级待确认问题与子任务目录。
  - 建立成熟度与进展跟踪入口。
  - 完成本轮首次真实模块成熟度盘点，并把 `M01-M03` 回写为 `L2`、`M04-M10` 回写为 `L1`。
  - 明确当前没有任何模块达到子任务设计准入条件。
- 当前未完成事项：
  - `MODULE_DESIGN.md`、`MODULE_API_DESIGN.md`、`MODULE_SCHEMA_DESIGN.md`、`MODULE_LOGIC_DESIGN.md` 普遍仍以骨架为主。
  - 子任务设计与实施文档普遍尚未达到下游输入门槛，且多份 `SUBTASK_DESIGN.md` 仍残留父模块模板占位符。
  - 大部分高影响待确认问题尚未关闭。
  - 当前仍没有任何子任务可进入实施准备。

## 4. 当前阻塞项

- OQ-001 仓库结构是否固定为 monorepo。
- OQ-004 鉴权机制采用固定 Bearer token、JWT 还是 session cookie。
- OQ-006 Markdown 预览与导出是否共用同一渲染链。
- OQ-007 上传、转换、导出在 P1 中哪些必须异步。
- OQ-008 匹配分析与评估规则是否需要版本化。
- OQ-011 Search snapshot 是否只做导入。
- OQ-012 上下文包中的 source priority 与引用摘要规则如何固定。
- OQ-014 模拟面试、打磨模式和复盘是否共用同一评估口径。
- OQ-016 薄弱项聚合 key、消减规则和停练规则如何定稿。
- OQ-017 模型推荐来源是本地 catalog 还是在线同步。
- OQ-018 管理台是否负责 search snapshot 导入与运维。

## 5. 当前并行文档完善计划

> 本节由总控 Codex 每轮更新。任何“第一轮 / 当前轮”的并行计划都必须写在这里，而不能只停留在聊天中。

### 5.1 本轮总目标
- 将 `M01-M03` 从“需求初稿 + 设计骨架”推进到“模块设计可评审”
- 用评审 Codex 收敛 `M04-M10` 的共享阻塞与下游推进顺序
- 在不擅自补关键契约的前提下，明确下一批允许启动的模块窗口

### 5.2 本轮任务包
#### 任务包 A：M01 基础平台与工作台壳层设计收敛
- 负责角色：模块 Codex
- 负责范围：M01 的模块级需求、设计、API、schema、logic、依赖关系、任务索引与模块开放问题。
- 允许修改的文档：
  - `docs/modules/M01-foundation-and-platform/MODULE_REQUIREMENTS.md`
  - `docs/modules/M01-foundation-and-platform/MODULE_DESIGN.md`
  - `docs/modules/M01-foundation-and-platform/MODULE_API_DESIGN.md`
  - `docs/modules/M01-foundation-and-platform/MODULE_SCHEMA_DESIGN.md`
  - `docs/modules/M01-foundation-and-platform/MODULE_LOGIC_DESIGN.md`
  - `docs/modules/M01-foundation-and-platform/MODULE_DEPENDENCIES.md`
  - `docs/modules/M01-foundation-and-platform/MODULE_TASK_INDEX.md`
  - `docs/modules/M01-foundation-and-platform/MODULE_OPEN_QUESTIONS.md`
- 禁止修改的文档：
  - 所有根目录全局状态文档
  - `docs/modules/M01-foundation-and-platform/sub_modules/**`
  - 其他模块目录
- 依赖的上游文档：
  - `AGENTS.md`
  - `docs/DOC_GOVERNANCE.md`
  - `PLAN_LATEST.md`
  - `TASK_INDEX.md`
  - `TECHNICAL_STANDARDS.md`
  - `DESIGN_DECISIONS.md`
  - `OPEN_QUESTIONS.md`
- 目标成熟度：
  - `MODULE_REQUIREMENTS.md >= L3`
  - `MODULE_DESIGN.md / MODULE_API_DESIGN.md / MODULE_SCHEMA_DESIGN.md / MODULE_LOGIC_DESIGN.md >= L4`
  - `MODULE_TASK_INDEX.md / MODULE_OPEN_QUESTIONS.md / MODULE_DEPENDENCIES.md >= L3`
- 完成标准：
  - 仓库结构、运行时基线、壳层职责、i18n 与测试/文档治理边界可评审。
  - 关键 OQ 与对应文档映射清晰。
  - 模块仍不能进入子任务设计的原因被显式记录。
- 若发现需求不清时的处理规则：
  - 不补关键契约。
  - 先写入 `MODULE_OPEN_QUESTIONS.md`，再向总控回报。

#### 任务包 B：M02 鉴权、团队与成员设计收敛
- 负责角色：模块 Codex
- 负责范围：M02 的模块级需求、设计、API、schema、logic、依赖关系、任务索引与模块开放问题。
- 允许修改的文档：
  - `docs/modules/M02-identity-and-team/MODULE_REQUIREMENTS.md`
  - `docs/modules/M02-identity-and-team/MODULE_DESIGN.md`
  - `docs/modules/M02-identity-and-team/MODULE_API_DESIGN.md`
  - `docs/modules/M02-identity-and-team/MODULE_SCHEMA_DESIGN.md`
  - `docs/modules/M02-identity-and-team/MODULE_LOGIC_DESIGN.md`
  - `docs/modules/M02-identity-and-team/MODULE_DEPENDENCIES.md`
  - `docs/modules/M02-identity-and-team/MODULE_TASK_INDEX.md`
  - `docs/modules/M02-identity-and-team/MODULE_OPEN_QUESTIONS.md`
- 禁止修改的文档：
  - 所有根目录全局状态文档
  - `docs/modules/M02-identity-and-team/sub_modules/**`
  - 其他模块目录
- 依赖的上游文档：
  - `AGENTS.md`
  - `docs/DOC_GOVERNANCE.md`
  - `PLAN_LATEST.md`
  - `TECHNICAL_STANDARDS.md`
  - `DESIGN_DECISIONS.md`
  - `OPEN_QUESTIONS.md`
  - `docs/modules/M01-foundation-and-platform/**`
- 目标成熟度：
  - `MODULE_REQUIREMENTS.md >= L3`
  - `MODULE_DESIGN.md / MODULE_API_DESIGN.md / MODULE_SCHEMA_DESIGN.md / MODULE_LOGIC_DESIGN.md >= L4`
  - `MODULE_TASK_INDEX.md / MODULE_OPEN_QUESTIONS.md / MODULE_DEPENDENCIES.md >= L3`
- 完成标准：
  - 鉴权方式、会话边界、成员目录、权限矩阵与跨团队访问规则达到可评审。
  - 模块内 OQ 与共享契约依赖关系被显式记录。
  - 是否允许下一轮继续进入子任务设计有明确判断。
- 若发现需求不清时的处理规则：
  - 不补关键契约。
  - 先写入 `MODULE_OPEN_QUESTIONS.md`，再向总控回报。

#### 任务包 C：M03 岗位、简历与文档处理设计收敛
- 负责角色：模块 Codex
- 负责范围：M03 的模块级需求、设计、API、schema、logic、依赖关系、任务索引与模块开放问题。
- 允许修改的文档：
  - `docs/modules/M03-jobs-resumes-and-documents/MODULE_REQUIREMENTS.md`
  - `docs/modules/M03-jobs-resumes-and-documents/MODULE_DESIGN.md`
  - `docs/modules/M03-jobs-resumes-and-documents/MODULE_API_DESIGN.md`
  - `docs/modules/M03-jobs-resumes-and-documents/MODULE_SCHEMA_DESIGN.md`
  - `docs/modules/M03-jobs-resumes-and-documents/MODULE_LOGIC_DESIGN.md`
  - `docs/modules/M03-jobs-resumes-and-documents/MODULE_DEPENDENCIES.md`
  - `docs/modules/M03-jobs-resumes-and-documents/MODULE_TASK_INDEX.md`
  - `docs/modules/M03-jobs-resumes-and-documents/MODULE_OPEN_QUESTIONS.md`
- 禁止修改的文档：
  - 所有根目录全局状态文档
  - `docs/modules/M03-jobs-resumes-and-documents/sub_modules/**`
  - 其他模块目录
- 依赖的上游文档：
  - `AGENTS.md`
  - `docs/DOC_GOVERNANCE.md`
  - `PLAN_LATEST.md`
  - `TECHNICAL_STANDARDS.md`
  - `DESIGN_DECISIONS.md`
  - `OPEN_QUESTIONS.md`
  - `docs/modules/M01-foundation-and-platform/**`
  - `docs/modules/M02-identity-and-team/**`
- 目标成熟度：
  - `MODULE_REQUIREMENTS.md >= L3`
  - `MODULE_DESIGN.md / MODULE_API_DESIGN.md / MODULE_SCHEMA_DESIGN.md / MODULE_LOGIC_DESIGN.md >= L4`
  - `MODULE_TASK_INDEX.md / MODULE_OPEN_QUESTIONS.md / MODULE_DEPENDENCIES.md >= L3`
- 完成标准：
  - 岗位、简历、版本、上传、转换、导出链路的对象边界、接口方向和异步约束达到可评审。
  - `OQ-006 / OQ-007` 对设计包的影响被显式记录。
  - 下游 `M04-M06` 可引用的稳定输入被明确列出。
- 若发现需求不清时的处理规则：
  - 不补关键契约。
  - 先写入 `MODULE_OPEN_QUESTIONS.md`，再向总控回报。

#### 任务包 D：M04-M10 共享阻塞评审与推进顺序校准
- 负责角色：评审 Codex
- 负责范围：只读评审 `M04-M10` 的 `MODULE_OPEN_QUESTIONS.md`、`MODULE_DEPENDENCIES.md`、`MODULE_TASK_INDEX.md` 与关键设计骨架，输出共享阻塞分层和下一批模块顺序建议。
- 允许修改的文档：
  - 无。本任务包只读评审，产出直接回报总控。
- 禁止修改的文档：
  - 所有全局状态文档
  - 所有模块与子任务文档
- 依赖的上游文档：
  - `AGENTS.md`
  - `docs/DOC_GOVERNANCE.md`
  - `OPEN_QUESTIONS.md`
  - `TECHNICAL_STANDARDS.md`
  - `DESIGN_DECISIONS.md`
  - `docs/modules/M04-match-analysis-and-evidence/**`
  - `docs/modules/M05-assets-and-retrieval/**`
  - `docs/modules/M06-simulated-interview-and-context/**`
  - `docs/modules/M07-polish-assessment-and-progress/**`
  - `docs/modules/M08-review-and-replay/**`
  - `docs/modules/M09-training-and-weakness-lifecycle/**`
  - `docs/modules/M10-admin-governance-and-observability/**`
- 目标成熟度：
  - 不直接提升模块成熟度，目标是形成一份可执行的阻塞分层与顺序建议。
- 完成标准：
  - 明确 `M04-M10` 的共享契约阻塞如何分组。
  - 明确 `M03` 之后应先推进哪一批模块。
  - 明确哪些问题必须先由总控冻结默认口径。
- 若发现需求不清时的处理规则：
  - 不补关键契约。
  - 只记录到评审回报，由总控决定是否升级到全局 `OPEN_QUESTIONS.md`。

## 6. 当前模块推进判断

> 本节用于让你一眼看到：哪个模块在什么阶段、是否能继续拆到子任务。

| 模块 | 当前主阶段 | 当前判断 | 是否可进入子任务设计 | 主要原因 |
| --- | --- | --- | --- | --- |
| M01 | 需求初稿 + 设计骨架 | 整体 L2，优先推进模块设计可评审 | 否 | `OQ-001~003` 未收敛，设计包四件套仍为 L1 |
| M02 | 需求初稿 + 设计骨架 | 整体 L2，优先推进鉴权与权限矩阵设计 | 否 | `OQ-004~005` 未收敛，设计包四件套仍为 L1 |
| M03 | 需求初稿 + 设计骨架 | 整体 L2，优先推进文档处理与异步边界设计 | 否 | `OQ-006~007` 未收敛，设计包四件套仍为 L1 |
| M04 | 需求初稿 + 模块骨架 | 整体 L1，等待上游输入更稳定后再推进 | 否 | 评分/versioning 契约未固化，设计包与子任务文档均为骨架 |
| M05 | 需求初稿 + 模块骨架 | 整体 L1，等待上游输入更稳定后再推进 | 否 | provider、归档粒度与检索入库链路未固化 |
| M06 | 需求初稿 + 模块骨架 | 整体 L1，等待 `M03-M05` 与共享契约收敛 | 否 | 上下文包、trace、snapshot/admin 边界均未固化 |
| M07 | 需求初稿 + 模块骨架 | 整体 L1，当前不应开启子任务设计 | 否 | 评估口径、推荐机制与能力树状态未固化 |
| M08 | 需求初稿 + 模块骨架 | 整体 L1，当前不应开启子任务设计 | 否 | review 输入模型、复盘对象与导出边界未固化 |
| M09 | 需求初稿 + 模块骨架 | 整体 L1，当前不应开启子任务设计 | 否 | 弱项聚合 key、生命周期规则与共享评估口径未固化 |
| M10 | 需求初稿 + 模块骨架 | 整体 L1，当前不应开启子任务设计 | 否 | 管理台治理边界、模型来源、snapshot 运维职责未固化 |

## 7. 下一轮建议

- 先开 `M01`、`M02`、`M03` 三个模块 Codex 窗口，把模块设计包推进到 `L4`。
- 另开一个评审 Codex 窗口，只读收敛 `M04-M10` 的共享阻塞和下一批顺序，不直接改文档。
- 本轮不要开启任何子模块 Codex；所有 `SUBTASK_DESIGN.md` / `SUBTASK_IMPLEMENTATION.md` 目前都还不具备细化条件。
- 对 `OQ-001`、`OQ-004`、`OQ-006`、`OQ-007`、`OQ-014` 优先给出冻结默认口径或确认结果。
- 在进入下一批模块前，先统一清理 `SUBTASK_DESIGN.md` 中残留的父模块模板占位符。

## 8. 本轮收口要求

每轮结束后，总控 Codex 至少要回写：
1. 当前低成熟度重点模块
2. 当前并行文档完善计划
3. 当前模块推进判断
4. 当前阻塞项是否变化
5. 下一轮建议是否变化
6. 与 `DOCUMENT_MATURITY.md` 是否一致

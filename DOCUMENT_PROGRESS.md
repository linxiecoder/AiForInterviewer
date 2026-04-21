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

- 当前阶段：阶段 3 / 计划重构执行轮 `R-Refactor-01`
- 阶段目标：从“优先模块设计可评审”切换到“共享契约冻结 + `M01/M02/M03` 任务重切”
- 本轮轮次定位：
  - 本轮不是普通推进轮，而是针对既有文档体系的计划重构执行轮。
  - 当前实施计划不再继续按 11 个源任务直接执行，而是按“共享契约窗口 + 模块重切窗口 + 评审窗口”重新组织。
  - 本轮不调整项目目录结构，不开启任何子任务实施窗口，也不开放子任务 Codex。
- 本轮总控判断：
  - `M01/M02/M03` 已整体从 `L2` 提升到 `L4`
  - 当前最低成熟度模块仍为 `M04-M10`
  - 当前最接近“可进入子任务设计候选”的顺序为：`M03` > `M02` > `M01`
  - 本轮仍应优先推进 `M01/M02/M03`，但方式已从“普通模块推进”改为“共享契约冻结 + 模块重切”
- 已完成事项：
  - 修复全局入口和总控文档乱码。
  - 建立根目录全局文档体系。
  - 建立 `docs/modules/` 模块目录与模块骨架。
  - 建立模块级待确认问题与子任务目录。
  - 建立成熟度与进展跟踪入口。
  - 完成 `M01`、`M02`、`M03` 首轮模块设计收敛，并把三者统一推进到可评审层级。
  - 明确 `M01` 的剩余缺口集中在平台共享契约，`M02` 的剩余缺口集中在对齐 M01 契约和清理命名漂移，`M03` 的剩余缺口集中在状态/冲突/下载映射等收口项。
  - 识别出需要上升为全局治理的问题：最小 CI 验证矩阵、共享页面原语、列表查询状态映射、locale 策略，以及 admin 成员管理归属。
  - 将 `OQ-023` 维持为 `proposed-default`，作为 `M02/M10` 职责重切输入，而不是继续保持模块间摇摆状态。
  - 明确当前仍没有任何模块达到正式子任务设计准入条件。
- 当前未完成事项：
  - `M01` 的共享平台契约虽已完成本轮总控回写：`OQ-019`、`OQ-020`、`OQ-021`、`OQ-022` 已形成默认冻结候选并可作为继续推进输入；其中 `OQ-021` 已完成 `M01-M03` 的模块级默认口径吸收，但完整实现级细节与 `OQ-022` 的模块边界收口仍未定稿。
  - `M02` 仍需完成与 `M01` 共享契约的最终对齐，吸收 `OQ-020` 的共享页面原语口径与 `OQ-022` 的默认 i18n 口径，并把 `OQ-023` 的职责重切稳定回写到模块边界。
  - `M03` 虽已形成完整可评审草案，但仍未完成“候选面收缩”，尚不能由总控正式登记为稳定下游输入。
  - `M04-M10` 当前仍停留在需求初稿 / 设计骨架阶段，不适合作为本轮主写对象。
  - 子任务设计与实施文档普遍尚未达到下游输入门槛，且多份 `SUBTASK_DESIGN.md` 仍残留父模块模板占位符。
  - 当前仍没有任何子任务可进入实施准备。

## 4. 当前阻塞项

- 已冻结且可继续作为模块设计输入的全局口径：
  - `OQ-001`、`OQ-002`、`OQ-003`
  - `OQ-004`、`OQ-005`
  - `OQ-006`、`OQ-007`
  - `OQ-008`、`OQ-011`
  - `OQ-014`
  - `OQ-017`、`OQ-018`
- 当前仍阻塞 `M01/M02/M03` 正式升入 `L5` 的问题：
  - `OQ-021` 已形成 `proposed-default`，并已完成 `M01-M03` 的模块级默认口径吸收，但仍需继续保留实现级细节风险位。
- 本轮已具备默认冻结并可直接作为任务重切输入的问题：
  - `OQ-019` 保持 `proposed-default`：冻结根目录脚本命名、最小 health check、验证入口类型与 API/Web 两类最小校验 lane，不扩张为完整流水线设计。
  - `OQ-020` 保持 `proposed-default`：冻结最小共享页面原语边界；`PageHeader` 只承载标题/说明/主次动作，摘要区独立承载 `status_badge` / `updated_at` / `summary_items` 与最小状态表达，可作为 `M01` 收口、`M03` 页面设计收缩与 `M02` 页面承接口径对齐输入。
  - `OQ-021` 保持 `proposed-default`：冻结共享 `ListQueryState`、query 映射、分页响应骨架与页面容器 adapter 职责；可作为 `M01-M03` 继续推进输入，但不扩张为完整实现级交互定稿。
  - `OQ-022` 保持 `proposed-default`：冻结统一取词入口、locale seed、最小 fallback 规则与 namespace 边界，可作为 `M01` 共享 i18n 收口与 `M02` 模块重切输入，但不扩张为完整 i18n 架构定稿。
  - `OQ-023` 保持 `proposed-default`，作为 `M02` 与后续治理模块的职责切分口径，不再单独占用共享契约冻结窗口。
- 当前仍阻塞下一批模块深化设计的问题：
  - `OQ-012` 上下文包中的 source priority 与引用摘要规则仍未完整冻结，`M06` 只能先停留在评审准备。
  - `OQ-016` 薄弱项聚合 key、消减规则和停练规则仍未完整冻结，`M09` 仍不宜进入主写深化。
- 当前过程性风险：
  - 两个模块 `MODULE_EXECUTION_LOG.md` 仍保留模板化收口，不适合作为正式成熟度提升的唯一依据。
  - `M02` 已把部分模块级问题清空，但全局共享契约依赖尚未真正消失；若总控不先统一口径，会出现“模块自评 L5、全局仍判 L4”的双重叙事。

## 5. 当前并行文档完善计划

> 本节由总控 Codex 每轮更新。任何“第一轮 / 当前轮”的并行计划都必须写在这里，而不能只停留在聊天中。
>
> 本轮（`R-Refactor-01` / 计划重构执行轮）收口结论：
> - `OQ-019~OQ-022` 已全部完成 `proposed-default` 回写，且不再回退为 `open`
> - `M02` 已完成第一轮职责重切，`M03` 已完成第一轮旧入口清理与微任务重切
> - 下一轮不再重复讨论“是否冻结 `OQ-019~OQ-022`”，而是转向“补齐残留共享契约 + 同步全局索引 + 收紧模块 readiness”
> - 下一轮建议保持 6 个窗口并行：总控 / 全局问题升级 x1，`M01` 共享契约收口 x2，`M02 / M03` 模块收紧 x2，评审 x1
> - 下一轮仍不开放任何子任务 Codex

### 5.1 当前阻塞项变化

- 已不再构成本轮主阻塞：
  - `OQ-019`
  - `OQ-020`
  - `OQ-021`
  - `OQ-022`
- 仍需下一轮继续处理的阻塞：
  - `OQ-024`：旧 `ST02_* / ST03_*` 目录的全局映射与退役口径
  - `OQ-025`：`jobs.requirement_items_json` 的最小输入契约
  - `M01` 共享下载 / 对象存储口径与 shared adapter 实现级边界
  - `M02` 页面 adapter readiness 与 `MODULE_API_DESIGN.md` 的最后收口
  - `M03` 岗位链输入契约与上传 / 导出链的上游依赖

### 5.2 下一轮任务包

#### 任务包 GC-01：旧入口退役与全局问题升级
- 任务包名称：旧入口退役与全局问题升级
- 负责角色：总控 Codex
- 负责范围：把 `MQ-207` + `MQ-306` 合并升级为 `OQ-024`，把 `MQ-307` 升级为 `OQ-025`，并同步全局索引与 readiness 口径。
- 允许修改的文档：
  - `OPEN_QUESTIONS.md`
  - `TASK_INDEX.md`
  - `MODULE_INDEX.md`
  - `DOCUMENT_PROGRESS.md`
  - `DOCUMENT_MATURITY.md`
  - `EXECUTION_LOG.md`
- 禁止修改的文档：
  - `docs/modules/**`
  - 所有 `sub_modules/**`
- 依赖的上游文档：
  - `AGENTS.md`
  - `docs/DOC_GOVERNANCE.md`
  - `docs/modules/M02-identity-and-team/MODULE_OPEN_QUESTIONS.md`
  - `docs/modules/M02-identity-and-team/MODULE_TASK_INDEX.md`
  - `docs/modules/M03-jobs-resumes-and-documents/MODULE_OPEN_QUESTIONS.md`
  - `docs/modules/M03-jobs-resumes-and-documents/MODULE_TASK_INDEX.md`
  - 评审窗口回报
- 目标成熟度：
  - 让全局状态文档与模块重切结果重新对齐，避免下一轮继续按错误入口开窗。
- 完成标准：
  - `OQ-024`、`OQ-025` 在根目录问题表完成登记。
  - `TASK_INDEX.md` 不再把旧 `ST02_* / ST03_*` 作为可直开入口。
  - 下一轮窗口编排与 readiness 口径完成同步。
- 若发现需求不清时的处理规则：
  - 不在总控层直接新建或重命名子任务目录。
  - 只登记保守映射策略与未决点。

#### 任务包 SC-05：`M01` 共享下载 / 对象存储口径收口
- 任务包名称：`M01` 共享下载 / 对象存储口径收口
- 负责角色：模块 Codex
- 负责范围：冻结业务下载入口到共享下载网关、对象引用面与最小对象存储边界，给 `M03` 上传 / 导出链提供稳定上游输入。
- 允许修改的文档：
  - `docs/modules/M01-foundation-and-platform/MODULE_REQUIREMENTS.md`
  - `docs/modules/M01-foundation-and-platform/MODULE_DESIGN.md`
  - `docs/modules/M01-foundation-and-platform/MODULE_API_DESIGN.md`
  - `docs/modules/M01-foundation-and-platform/MODULE_SCHEMA_DESIGN.md`
  - `docs/modules/M01-foundation-and-platform/MODULE_LOGIC_DESIGN.md`
  - `docs/modules/M01-foundation-and-platform/MODULE_DEPENDENCIES.md`
  - `docs/modules/M01-foundation-and-platform/MODULE_TASK_INDEX.md`
  - `docs/modules/M01-foundation-and-platform/MODULE_OPEN_QUESTIONS.md`
  - `docs/modules/M01-foundation-and-platform/MODULE_EXECUTION_LOG.md`
- 禁止修改的文档：
  - 所有根目录全局状态文档
  - `docs/modules/M01-foundation-and-platform/sub_modules/**`
  - 其他模块目录
- 依赖的上游文档：
  - `AGENTS.md`
  - `docs/DOC_GOVERNANCE.md`
  - `OPEN_QUESTIONS.md`
  - `TECHNICAL_STANDARDS.md`
  - `docs/modules/M03-jobs-resumes-and-documents/**`
- 目标成熟度：
  - 维持 `M01` 为高 `L4`，但把“共享下载 / 对象存储”补到可供 `M03` 引用的上游输入程度。
- 完成标准：
  - 业务下载入口与共享下载网关的映射被写清。
  - 对象引用面、受理边界与明确不做的部分被写清。
  - `M03` 依赖文档可直接引用该口径，而不是继续口头引用。
- 若发现需求不清时的处理规则：
  - 不扩张为完整存储平台设计。
  - 只冻结最小共享边界与未决风险。

#### 任务包 SC-06：`M01` shared adapter 边界补写
- 任务包名称：`M01` shared adapter 边界补写
- 负责角色：模块 Codex
- 负责范围：在 `OQ-020~OQ-022` 已完成默认冻结的前提下，把页面原语、列表 adapter、i18n 消费边界补写到 `M01` 模块文档。
- 允许修改的文档：
  - `docs/modules/M01-foundation-and-platform/MODULE_REQUIREMENTS.md`
  - `docs/modules/M01-foundation-and-platform/MODULE_DESIGN.md`
  - `docs/modules/M01-foundation-and-platform/MODULE_API_DESIGN.md`
  - `docs/modules/M01-foundation-and-platform/MODULE_LOGIC_DESIGN.md`
  - `docs/modules/M01-foundation-and-platform/MODULE_DEPENDENCIES.md`
  - `docs/modules/M01-foundation-and-platform/MODULE_TASK_INDEX.md`
  - `docs/modules/M01-foundation-and-platform/MODULE_OPEN_QUESTIONS.md`
  - `docs/modules/M01-foundation-and-platform/MODULE_EXECUTION_LOG.md`
- 禁止修改的文档：
  - 所有根目录全局状态文档
  - `docs/modules/M01-foundation-and-platform/sub_modules/**`
  - 其他模块目录
- 依赖的上游文档：
  - `AGENTS.md`
  - `docs/DOC_GOVERNANCE.md`
  - `OPEN_QUESTIONS.md`
  - `TECHNICAL_STANDARDS.md`
  - `DESIGN_DECISIONS.md`
  - `docs/modules/M02-identity-and-team/**`
  - `docs/modules/M03-jobs-resumes-and-documents/**`
- 目标成熟度：
  - 维持 `M01` 高 `L4`，并把默认冻结口径补成可审计、可被模块下游复用的 shared adapter 输入。
- 完成标准：
  - 页面容器、request adapter、shared primitive 与 i18n 消费边界被写清。
  - 不再把 `OQ-020~OQ-022` 的实现级细节停留在总控口径。
  - 仍明确本轮不开放 `M01` 子任务窗口。
- 若发现需求不清时的处理规则：
  - 不扩张为完整设计系统或完整 i18n 架构。
  - 只补共享边界，不补具体实现。

#### 任务包 MR-03：`M02` readiness 收紧与入口映射同步
- 任务包名称：`M02` readiness 收紧与入口映射同步
- 负责角色：模块 Codex
- 负责范围：继续收紧 `M02` 的 `MODULE_API_DESIGN.md`、同步 `OQ-024` 的旧入口映射口径，并把页面类微任务与可先开的非页面微任务明确分离。
- 允许修改的文档：
  - `docs/modules/M02-identity-and-team/MODULE_DESIGN.md`
  - `docs/modules/M02-identity-and-team/MODULE_API_DESIGN.md`
  - `docs/modules/M02-identity-and-team/MODULE_DEPENDENCIES.md`
  - `docs/modules/M02-identity-and-team/MODULE_TASK_INDEX.md`
  - `docs/modules/M02-identity-and-team/MODULE_OPEN_QUESTIONS.md`
  - `docs/modules/M02-identity-and-team/MODULE_EXECUTION_LOG.md`
- 禁止修改的文档：
  - 所有根目录全局状态文档
  - `docs/modules/M02-identity-and-team/sub_modules/**`
  - 其他模块目录
- 依赖的上游文档：
  - `AGENTS.md`
  - `docs/DOC_GOVERNANCE.md`
  - `OPEN_QUESTIONS.md`
  - `MODULE_INDEX.md`
  - `docs/modules/M01-foundation-and-platform/**`
- 目标成熟度：
  - 把 `M02` 从“高 `L4` 可评审”推进到“接近 `L5` 候选但仍未放行页面面”的清晰状态。
- 完成标准：
  - `MODULE_API_DESIGN.md` 的最低位原因被进一步缩小到可审计范围。
  - `MT02_05/MT02_06` 被明确保留在后置页面队列，不被误判为可直开。
  - 旧 `ST02_*` 入口的历史容器口径与新微任务蓝本映射被写清。
- 若发现需求不清时的处理规则：
  - 不直接去补写子任务双文档。
  - 不把页面范围重新并回 backend / policy 任务。

#### 任务包 MR-04：`M03` 岗位链再切分与输入契约上提
- 任务包名称：`M03` 岗位链再切分与输入契约上提
- 负责角色：模块 Codex
- 负责范围：进一步拆细 `MT03_02`、`MT03_05`，并把 `jobs.requirement_items_json` 的最小输入契约上提为可供总控冻结的问题输入。
- 允许修改的文档：
  - `docs/modules/M03-jobs-resumes-and-documents/MODULE_REQUIREMENTS.md`
  - `docs/modules/M03-jobs-resumes-and-documents/MODULE_DESIGN.md`
  - `docs/modules/M03-jobs-resumes-and-documents/MODULE_SCHEMA_DESIGN.md`
  - `docs/modules/M03-jobs-resumes-and-documents/MODULE_DEPENDENCIES.md`
  - `docs/modules/M03-jobs-resumes-and-documents/MODULE_TASK_INDEX.md`
  - `docs/modules/M03-jobs-resumes-and-documents/MODULE_OPEN_QUESTIONS.md`
  - `docs/modules/M03-jobs-resumes-and-documents/MODULE_EXECUTION_LOG.md`
- 禁止修改的文档：
  - 所有根目录全局状态文档
  - `docs/modules/M03-jobs-resumes-and-documents/sub_modules/**`
  - 其他模块目录
- 依赖的上游文档：
  - `AGENTS.md`
  - `docs/DOC_GOVERNANCE.md`
  - `OPEN_QUESTIONS.md`
  - `MODULE_INDEX.md`
  - `docs/modules/M01-foundation-and-platform/**`
  - `docs/modules/M04-match-analysis-and-evidence/**`
  - `docs/modules/M06-simulated-interview-and-context/**`
- 目标成熟度：
  - 维持 `M03` 为 `L4`，但把“只有简历聚合根链局部接近候选”的判断写实，并为 `OQ-025` 提供可冻结输入。
- 完成标准：
  - `jobs.requirement_items_json` 的最小结构候选、空值语义、排序规则与写入责任被整理成可升级输入。
  - `MT03_02`、`MT03_05` 的边界继续收紧，不再混合读模型与页面 adapter。
  - 上传 / 导出链仍明确受 `M01` 共享下载口径约束，不被误判为可并行直开。
- 若发现需求不清时的处理规则：
  - 不允许下游模块先发明 JSON 契约再回填上游。
  - 不直接开放任何 `ST03_*` 或新微任务设计窗口。

#### 任务包 RV-02：下一轮 readiness 交叉复核
- 任务包名称：下一轮 readiness 交叉复核
- 负责角色：评审 Codex
- 负责范围：交叉复核 `GC-01`、`SC-05`、`SC-06`、`MR-03`、`MR-04` 的输出，确认 `M01/M02/M03` 的真实 readiness 与下一轮是否仍应关闭子任务窗口。
- 允许修改的文档：
  - 无。本任务包只读评审，产出直接回报总控。
- 禁止修改的文档：
  - 所有全局状态文档
  - 所有模块与子任务文档
- 依赖的上游文档：
  - `AGENTS.md`
  - `docs/DOC_GOVERNANCE.md`
  - `DOCUMENT_MATURITY.md`
  - `DOCUMENT_PROGRESS.md`
  - `MODULE_INDEX.md`
  - `OPEN_QUESTIONS.md`
  - `docs/modules/M01-foundation-and-platform/**`
  - `docs/modules/M02-identity-and-team/**`
  - `docs/modules/M03-jobs-resumes-and-documents/**`
- 目标成熟度：
  - 不直接提升成熟度，目标是防止模块自评与总控登记再次分叉。
- 完成标准：
  - 明确 `M02` 是否已进入真正的 `L5` 候选区间。
  - 明确 `M03` 是否仍只能登记为“局部接近候选”。
  - 明确下一轮是否依然不得开启第一批子任务窗口。
- 若发现需求不清时的处理规则：
  - 不补关键契约。
  - 只记录风险点、保守结论和建议总控动作。

## 6. 当前模块推进判断

> 本节用于让你一眼看到：哪个模块在什么阶段、是否能继续拆到子任务。

| 模块 | 当前主阶段 | 当前判断 | 是否可进入子任务设计 | 主要原因 |
| --- | --- | --- | --- | --- |
| M01 | 共享契约收口 / 上游稳定化 | 整体高 `L4`，但当前仍不是 `L5` 候选优先项 | 否 | `OQ-019~OQ-022` 已全部形成 `proposed-default`，下一步瓶颈转为共享下载 / 对象存储口径与 shared adapter 实现级边界 |
| M02 | 模块重切 / `L5` 候选前复核 | 整体高 `L4`，是当前最接近整体 `L5` 候选的模块，但页面面仍未 ready | 否 | `MODULE_API_DESIGN.md` 仍是最低位；`MT02_05/MT02_06` 继续受 `OQ-020/OQ-021/OQ-022` 吸收完成度与 `OQ-024` 入口映射约束 |
| M03 | 模块重切 / 局部候选收紧 | 整体 `L4`，只有简历聚合根链局部接近候选，模块整体不 ready | 否 | `jobs.requirement_items_json` 仍缺最小输入契约；岗位链受 `OQ-025` 阻塞，上传 / 导出链仍依赖 `M01` 共享下载口径 |
| M04 | 需求初稿 + 模块骨架 | 整体 L1，下一轮不建议作为主写窗口 | 否 | `M03` 尚未正式形成稳定输入，且 `OQ-008` 之外仍缺上游边界 |
| M05 | 需求初稿 + 模块骨架 | 整体 L1，下一轮不建议作为主写窗口 | 否 | `OQ-009/OQ-010` 仍 open，且依赖 `M03/M04` |
| M06 | 需求初稿 + 模块骨架 | 整体 L1，下一轮不建议作为主写窗口 | 否 | `OQ-012` 仍 open，且依赖 `M03-M05` 设计输入 |
| M07 | 需求初稿 + 模块骨架 | 整体 L1，本轮纳入共享阻塞评审，不进入主写 | 否 | 评估口径虽可先按默认框架评审，但仍缺 `M06` 输入 |
| M08 | 需求初稿 + 模块骨架 | 整体 L1，本轮纳入共享阻塞评审，不进入主写 | 否 | review 输入模型与复盘对象仍未得到上游设计支撑 |
| M09 | 需求初稿 + 模块骨架 | 整体 L1，本轮纳入共享阻塞评审，不进入主写 | 否 | `OQ-016` 仍 open，且共享评估口径尚未完成模块级回写 |
| M10 | 需求初稿 + 模块骨架 | 整体 L1，本轮纳入共享阻塞评审，不进入主写 | 否 | 治理边界虽有默认口径，但仍依赖 `M02/M03/M06/M09` 的稳定输入 |

## 7. 下一轮建议

- 下一轮建议直接按 6 个窗口执行：`GC-01`、`SC-05`、`SC-06`、`MR-03`、`MR-04`、`RV-02`。
- `OQ-019~OQ-022` 已完成默认冻结回写，下一轮不再重复开单问题冻结窗口；优先级转移到 `OQ-024`、`OQ-025` 与 `M01` 共享下载 / 对象存储口径。
- `M02` 可以继续按“接近 `L5` 候选但页面面未 ready”推进；`M03` 只能按“局部接近候选”推进，不能再用“模块整体最接近候选”的说法放宽判断。
- 暂不建议把主写窗口切到 `M04/M05/M06`；这些模块仍应以准备性阅读或只读评审为主。
- 下一轮仍不建议开启任何子任务 Codex；至少要等 `OQ-024` 完成全局映射、`OQ-025` 至少形成可下发口径、`M01` 共享下载 / 对象存储口径稳定并通过 `RV-02` 复核后再判断。

## 8. 本轮收口要求

每轮结束后，总控 Codex 至少要回写：
1. 当前低成熟度重点模块
2. 当前并行文档完善计划
3. 当前模块推进判断
4. 当前阻塞项是否变化
5. 下一轮建议是否变化
6. 与 `DOCUMENT_MATURITY.md` 是否一致

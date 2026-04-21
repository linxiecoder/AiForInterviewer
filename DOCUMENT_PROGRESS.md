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

- 当前阶段：阶段 3 / 计划重构执行轮 `R-Refactor-02`
- 阶段目标：从“共享契约冻结 + `M01/M02/M03` 任务重切”切换到“总控澄清 + 模块候选白名单准备”
- 本轮轮次定位：
  - 本轮不是普通推进轮，而是上一轮计划重构结果的总控收口轮。
  - 当前实施计划不再继续按 11 个源任务直接执行，而是按“总控澄清窗口 + 模块收口窗口 + 评审窗口”重新组织。
  - 本轮不调整项目目录结构，不开启任何子任务实施窗口，也不开放子任务 Codex。
- 本轮总控判断：
  - `M01/M02/M03` 仍整体维持 `L4`，但 readiness 比上一轮更接近。
  - 当前最低成熟度模块仍为 `M04-M10`，本轮无变化。
  - 当前最接近“可进入子任务设计候选”的观察顺序调整为：`M02` > `M03`（仅局部链路） > `M01`。
  - 下一轮仍继续模块轮，但主题已切换为“总控澄清 + 模块候选白名单准备”。
- 已完成事项：
  - `GC-01` 已固化“旧 `ST02_* / ST03_*` 只保留为历史容器、禁止直开”的全局口径。
  - `SC-05` 已把 `M01` 的共享下载 / 对象存储主题收口到可供 `M03/M05/M06/M08` 继续引用的程度。
  - `SC-06` 已把 shared adapter 明确为页面容器与共享页面原语 / 服务层之间的编排边界。
  - `MR-03` 已把 `M02` 收紧为“无正式可开微任务，只有极小候选白名单观察面”的状态。
  - `MR-04` 已把 `jobs.requirement_items_json` 的最小契约上提到模块层，并把岗位链拆为 `MT03_02A / MT03_02B`。
  - `RV-02` 已确认本轮仍不开放任何子任务 Codex，但可为后续极小白名单准备观察位。
- 当前未完成事项：
  - `OQ-024` 仍只收口到“旧入口退役为历史容器”，正式编号 / 映射策略尚未定稿。
  - `OQ-025` 已升为 `proposed-default`，但仍需总控吸收并同步约束 `M03 -> M04/M06` 的下游措辞。
  - `OQ-021` 的共享最小映射虽已澄清，但模块层仍需继续吸收，避免把 `updated_after / updated_before` 误写成共享最小契约。
  - `M01` 仍需处理 `MQ-001`、`MQ-003`、`MQ-005` 的整体 `L5` 收口。
  - `M02`、`M03` 仍未达到正式开放子任务设计窗口的程度。

## 4. 当前阻塞项

- 已冻结且可继续作为模块设计输入的全局口径：
  - `OQ-001`、`OQ-002`、`OQ-003`
  - `OQ-004`、`OQ-005`
  - `OQ-006`、`OQ-007`
  - `OQ-008`、`OQ-011`
  - `OQ-014`
  - `OQ-017`、`OQ-018`
- 当前仍阻塞 `M01/M02/M03` 正式升入 `L5` 的问题：
  - `OQ-021` 已形成 `proposed-default`，共享最小映射已澄清为 `page/page_size/q/status/sort/order`，但模块层仍需继续吸收，避免把 `updated_after / updated_before` 漂移成共享最小契约。
  - `OQ-024` 已把旧入口退役为历史容器，但正式编号 / 映射策略仍未定稿。
  - `OQ-025` 已升为 `proposed-default`，但仍需完成总控吸收并收紧对下游稳定性的表述。
  - `M01` 的整体主阻塞已切换为 `MQ-001`、`MQ-003`、`MQ-005`，而不是继续重复讨论 `SC-05`。
- 本轮已具备默认冻结并可直接作为任务重切输入的问题：
  - `OQ-019` 保持 `proposed-default`：冻结根目录脚本命名、最小 health check、验证入口类型与 API/Web 两类最小校验 lane，不扩张为完整流水线设计。
  - `OQ-020` 保持 `proposed-default`：冻结最小共享页面原语边界；`PageHeader` 只承载标题/说明/主次动作，摘要区独立承载 `status_badge` / `updated_at` / `summary_items` 与最小状态表达，可作为 `M01` 收口、`M03` 页面设计收缩与 `M02` 页面承接口径对齐输入。
  - `OQ-021` 保持 `proposed-default`：冻结共享 `ListQueryState`、最小 query 映射、分页响应骨架与页面容器 adapter 职责；`updated_after / updated_before` 当前只作为模块扩展，不进入共享最小映射。
  - `OQ-022` 保持 `proposed-default`：冻结统一取词入口、locale seed、最小 fallback 规则与 namespace 边界，可作为 `M01` 共享 i18n 收口与 `M02` 模块重切输入，但不扩张为完整 i18n 架构定稿。
  - `OQ-023` 保持 `proposed-default`，作为 `M02` 与后续治理模块的职责切分口径，不再单独占用共享契约冻结窗口。
  - `OQ-025` 保持 `proposed-default`：冻结 `jobs.requirement_items_json` 的最小 item 子集、`null / []` 语义、数组顺序与写入责任，作为 `M03 -> M04/M06` 的最小共享输入。
- 当前仍阻塞下一批模块深化设计的问题：
  - `OQ-012` 上下文包中的 source priority 与引用摘要规则仍未完整冻结，`M06` 只能先停留在评审准备。
  - `OQ-016` 薄弱项聚合 key、消减规则和停练规则仍未完整冻结，`M09` 仍不宜进入主写深化。
- 当前过程性风险：
  - 两个模块 `MODULE_EXECUTION_LOG.md` 仍保留模板化收口，不适合作为正式成熟度提升的唯一依据。
  - `M02` 已把部分模块级问题清空，但全局共享契约依赖尚未真正消失；若总控不先统一口径，会出现“模块自评 L5、全局仍判 L4”的双重叙事。

## 5. 当前并行文档完善计划

> 本节由总控 Codex 每轮更新。任何“第一轮 / 当前轮”的并行计划都必须写在这里，而不能只停留在聊天中。
>
> 本轮（`R-Refactor-02` / 计划重构执行轮）收口结论：
> - `GC-01` 已把“旧入口退役为历史容器、禁止直开”固化为全局映射，`OQ-024` 保留剩余“正式编号 / 映射策略”问题
> - `SC-05`、`SC-06`、`MR-03`、`MR-04`、`RV-02` 已完成回写，不再按原任务包重复开窗
> - `M01/M02/M03` 比上一轮更接近 readiness，但当前仍不开放任何子任务 Codex
> - 下一轮仍继续模块轮，但从“共享契约冻结 + 任务重切”切换为“总控澄清 + 模块候选白名单准备”

### 5.1 当前阻塞项变化

- 已不再构成本轮主阻塞：
  - `SC-05` 作为独立主题的收口
  - `SC-06` 作为独立主题的收口
  - 旧 `ST02_* / ST03_*` 继续被误判为可直开入口
- 仍需下一轮继续处理的阻塞：
  - `OQ-021`：需要补一次总控澄清，明确 `updated_after / updated_before` 不属于共享最小映射
  - `OQ-024`：仍需保留“是否复用旧编号、如何把 `MT02_* / MT03_*` 正式映射成入口”的残余问题
  - `OQ-025`：已可按默认口径继续推进，但仍需完成总控吸收与下游口径统一
  - `M01`：整体仍受 `MQ-001`、`MQ-003`、`MQ-005` 约束，不能把 `SC-05` 重复当成主阻塞
  - `M02`：仍没有任何正式可开窗微任务，页面类与验证类任务继续阻塞
  - `M03`：岗位链仍需吸收 `OQ-025`、修正 `OQ-021` 漂移，并收紧“面向下游已稳定”的措辞

### 5.2 下一轮任务包

#### 任务包 GC-02：`OQ-021/OQ-024/OQ-025` 总控澄清与全局回写
- 任务包名称：`OQ-021/OQ-024/OQ-025` 总控澄清与全局回写
- 负责角色：总控 Codex
- 负责范围：统一澄清共享最小列表映射、`OQ-024` 的剩余正式映射问题，以及 `OQ-025` 的默认冻结口径，并同步全局状态文档。
- 允许修改的文档：
  - `OPEN_QUESTIONS.md`
  - `DOCUMENT_PROGRESS.md`
  - `DOCUMENT_MATURITY.md`
  - `MODULE_INDEX.md`
  - 必要时 `TASK_INDEX.md`
  - `EXECUTION_LOG.md`
- 禁止修改的文档：
  - `docs/modules/**`
  - 所有 `sub_modules/**`
- 依赖的上游文档：
  - `AGENTS.md`
  - `docs/DOC_GOVERNANCE.md`
  - `docs/modules/M01-foundation-and-platform/**`
  - `docs/modules/M02-identity-and-team/**`
  - `docs/modules/M03-jobs-resumes-and-documents/**`
  - `RV-02` 评审回报
- 目标成熟度：
  - 让总控口径与模块吸收口径重新一致，避免下一轮“共享最小映射”和“模块级扩展”继续漂移。
- 完成标准：
  - `OQ-021` 的共享最小映射与模块级扩展边界被写死。
  - `OQ-024` 的剩余问题范围被收窄到“正式编号 / 映射策略”。
  - `OQ-025` 的默认冻结口径被稳定登记为总控输入。
- 若发现需求不清时的处理规则：
  - 不新建新的全局 OQ。
  - 只做保守澄清，不直接放行子任务窗口。

#### 任务包 MR-05：`M01` 非 `SC-05` 的整体 `L5` 收口
- 任务包名称：`M01` 非 `SC-05` 的整体 `L5` 收口
- 负责角色：模块 Codex
- 负责范围：继续处理 `M01` 在脚本 / CI、列表实现级接口、shared adapter 实现级 contract 上的剩余缺口，不重复讨论共享下载 / 对象存储主题本身。
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
  - `DESIGN_DECISIONS.md`
- 目标成熟度：
  - 维持高 `L4`，并把模块整体缺口收缩到是否具备 `L5` 候选判定所需的最后一组问题。
- 完成标准：
  - `SC-05` 不再被当作独立主写主题重复展开。
  - `MQ-001`、`MQ-003`、`MQ-005` 的剩余影响面被写清。
  - 下游模块可继续引用 `MQ-006`，但不把这件事误写成“模块整体 ready”。
- 若发现需求不清时的处理规则：
  - 不把实现级细节直接下放到 `ST01_*`。
  - 不新增新的平台级共享问题，除非明确跨模块漂移。

#### 任务包 MR-06：`M02` 候选白名单准备
- 任务包名称：`M02` 候选白名单准备
- 负责角色：模块 Codex
- 负责范围：把非页面候选与正式放行判断继续分离，明确 `MT02_01 / MT02_02 / (MT02_03 / MT02_07)` 的条件性白名单位置，并保持页面类微任务后置。
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
  - 把 `M02` 从“最接近 `L5` 候选”推进到“具备极小白名单准备条件，但仍未正式放行”的清晰状态。
- 完成标准：
  - `MT02_01 / MT02_02` 的候选前置条件被写清。
  - `MT02_04 / MT02_05 / MT02_06 / MT02_08` 继续保持阻塞且原因可审计。
  - 不把“候选顺序”误写成“正式可开子任务”。
- 若发现需求不清时的处理规则：
  - 不直接补写子任务双文档。
  - 不把页面 / 验证面重新并回非页面任务。

#### 任务包 MR-07：`M03` 吸收 `OQ-025` 与口径收紧
- 任务包名称：`M03` 吸收 `OQ-025` 与口径收紧
- 负责角色：模块 Codex
- 负责范围：吸收 `OQ-025` 的默认口径、修正 `OQ-021` 的模块扩展漂移，并下调“面向下游已稳定”的表述强度。
- 允许修改的文档：
  - `docs/modules/M03-jobs-resumes-and-documents/MODULE_REQUIREMENTS.md`
  - `docs/modules/M03-jobs-resumes-and-documents/MODULE_DESIGN.md`
  - `docs/modules/M03-jobs-resumes-and-documents/MODULE_API_DESIGN.md`
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
  - 维持 `L4`，但把模块剩余漂移点收缩到可复核范围，并为下一次“局部候选复评”准备干净输入。
- 完成标准：
  - `updated_after / updated_before` 被明确为模块扩展，而不是共享最小映射。
  - 面向 M04 / M06 的输出面表述从“已稳定”收紧为“可依赖最小子集”。
  - `MT03_01 / MT03_03` 的条件性候选前提被写清，其余链路继续保持后置。
- 若发现需求不清时的处理规则：
  - 不在模块内擅自扩张 `OQ-021` 共享口径。
  - 不把 `OQ-025` 的扩展字段提前写成稳定输入。

#### 任务包 RV-03：候选白名单交叉复核
- 任务包名称：候选白名单交叉复核
- 负责角色：评审 Codex
- 负责范围：交叉复核 `GC-02`、`MR-05`、`MR-06`、`MR-07` 的输出，判断是否已满足“极小白名单候选”条件，以及是否仍继续关闭子任务窗口。
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
  - 不直接提升成熟度，目标是为下一轮是否允许“极小白名单候选”提供可靠依据。
- 完成标准：
  - 明确是否仍应继续模块轮。
  - 明确是否已有模块达到“可进入子任务设计候选”。
  - 明确若继续关闭子任务窗口，具体还差哪两三条总控口径。
- 若发现需求不清时的处理规则：
  - 不补关键契约。
  - 只记录保守结论与建议总控动作。

## 6. 当前模块推进判断

> 本节用于让你一眼看到：哪个模块在什么阶段、是否能继续拆到子任务。

| 模块 | 当前主阶段 | 当前判断 | 是否可进入子任务设计 | 主要原因 |
| --- | --- | --- | --- | --- |
| M01 | 模块整体 `L5` 收口前复核 | 整体高 `L4`，但当前仍不是正式候选 | 否 | `SC-05` 主题本身已足够作为下游输入，当前瓶颈已切换为 `MQ-001`、`MQ-003`、`MQ-005`，不应再把共享下载口径重复当作主阻塞 |
| M02 | 候选白名单准备 | 整体高 `L4`，仍是当前最接近整体 `L5` 候选的模块 | 否 | `MODULE_API_DESIGN.md` 仍是最低位；当前只有非页面链路进入候选白名单观察，页面 / 验证面继续受 `OQ-020/OQ-021/OQ-022/OQ-024` 约束 |
| M03 | 局部候选吸收 / 口径收紧 | 整体 `L4`，只有少量链路接近候选，模块整体不 ready | 否 | `OQ-025` 虽已可按默认口径推进，但仍需完成总控吸收；`OQ-021` 的共享最小映射与模块扩展边界也需澄清 |
| M04 | 需求初稿 + 模块骨架 | 整体 L1，下一轮不建议作为主写窗口 | 否 | `M03` 尚未正式形成稳定输入，且 `OQ-008` 之外仍缺上游边界 |
| M05 | 需求初稿 + 模块骨架 | 整体 L1，下一轮不建议作为主写窗口 | 否 | `OQ-009/OQ-010` 仍 open，且依赖 `M03/M04` |
| M06 | 需求初稿 + 模块骨架 | 整体 L1，下一轮不建议作为主写窗口 | 否 | `OQ-012` 仍 open，且依赖 `M03-M05` 设计输入 |
| M07 | 需求初稿 + 模块骨架 | 整体 L1，本轮纳入共享阻塞评审，不进入主写 | 否 | 评估口径虽可先按默认框架评审，但仍缺 `M06` 输入 |
| M08 | 需求初稿 + 模块骨架 | 整体 L1，本轮纳入共享阻塞评审，不进入主写 | 否 | review 输入模型与复盘对象仍未得到上游设计支撑 |
| M09 | 需求初稿 + 模块骨架 | 整体 L1，本轮纳入共享阻塞评审，不进入主写 | 否 | `OQ-016` 仍 open，且共享评估口径尚未完成模块级回写 |
| M10 | 需求初稿 + 模块骨架 | 整体 L1，本轮纳入共享阻塞评审，不进入主写 | 否 | 治理边界虽有默认口径，但仍依赖 `M02/M03/M06/M09` 的稳定输入 |

## 7. 下一轮建议

- 下一轮仍继续模块轮，但不再是“共享契约冻结 + 任务重切轮”，而是“总控澄清 + 模块候选白名单准备轮”。
- 下一轮建议按 5 个窗口执行：`GC-02`、`MR-05`、`MR-06`、`MR-07`、`RV-03`。
- `SC-05` 不应再作为下一轮独立主写主题；它只保留为 `M01` 的残余实现级风险备注。
- `M02` 仍是最值得优先推进的模块窗口；`M03` 次之；`M01` 仍需继续做整体 `L5` 收口，但重点已从下载口径转向其余残留主题。
- 下一轮仍不建议开启任何子任务 Codex；若要准备后续“极小白名单”，当前最合理的观察面是 `M02: MT02_01 / MT02_02`、`M03: MT03_01 / MT03_03`，但本轮不正式放行。

## 8. 本轮收口要求

每轮结束后，总控 Codex 至少要回写：
1. 当前低成熟度重点模块
2. 当前并行文档完善计划
3. 当前模块推进判断
4. 当前阻塞项是否变化
5. 下一轮建议是否变化
6. 与 `DOCUMENT_MATURITY.md` 是否一致

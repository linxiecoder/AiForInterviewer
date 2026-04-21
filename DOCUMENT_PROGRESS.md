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

- 当前阶段：阶段 3 / 最低位压缩轮
- 阶段目标：统一 `OQ-021 / OQ-024 / OQ-025` 的正式映射与状态分层，并把 `M01 / M02 / M03` 的窗口作用域压缩到“最低位文档 / 最小阻塞集合”。
- 本轮轮次定位：
  - 本轮不是普通模块推进轮，也不是子任务推进轮，而是“最低位压缩轮”。
  - 当前实施计划不再按 11 个源任务直接执行；本轮固定为 5 个窗口：总控 x1、`M01` x1、`M02` x1、`M03` x1、评审 x1。
  - 本轮不调整项目目录结构，不开启任何子任务实施窗口，也不开放任何子任务 Codex。
- 本轮总控判断：
  - `M01/M02/M03` 仍整体维持 `L4`，但本轮目标不再是泛化收口，而是把最低位文档中的关键歧义压缩到最小集合。
  - 当前最低成熟度模块仍为 `M04-M10`，本轮无变化。
  - 当前最接近“可进入子任务设计候选”的观察顺序仍为：`M02` > `M03`（仅局部链路） > `M01`。
  - 当前阶段仍继续模块轮；本轮只做最低位压缩，不做正式候选放行，更不做子任务开窗。
- 已吸收的上轮结论：
  - `GC-02` 已统一 `OQ-021 / OQ-024 / OQ-025` 的总控口径：`OQ-021` 的共享最小映射不含 `updated_after / updated_before`，`OQ-024` 明确“白名单观察面 != 正式子任务开窗条件”，`OQ-025` 只代表最小共享输入而不代表完整岗位链 ready。
  - `MR-05` 已确认：`SC-05` 相关共享下载 / `storage_objects` 主题已足够作为 `M03/M05` 的模块设计输入，但 `M01` 整体仍被 `MQ-001`、`MQ-003`、`MQ-005` 阻塞。
  - `MR-06` 已确认：`M02` 当前仍只有 `MT02_01 / MT02_02` 属于条件性白名单观察面；`MQ-209` 已被总控吸收到 `OQ-024` 叙事中。
  - `MR-07` 已确认：`M03` 已吸收 `OQ-025` 并修正 `OQ-021` 漂移；`MT03_01 / MT03_03` 仍只是条件性白名单观察面。
  - `RV-03` 已确认：上一轮仍不能开放任何子任务窗口，关键剩余条件是 `OQ-024` 正式映射未定、`OQ-021` 模块吸收未闭合，以及 `M01/M02/M03` 最低位文档仍未统一跨过 `L5`。
- 本轮待处理事项：
  - 把 `OQ-021 / OQ-024 / OQ-025` 的三层状态写死到全局文档：共享最小层 / 模块扩展层 / 正式候选或开窗层。
  - 把 `M01 / M02 / M03` 的窗口作用域压缩到最低位文档及其最小阻塞集合。
  - 继续明确：本轮仍不允许开启任何子任务窗口。

## 4. 当前阻塞项

- 已冻结且可继续作为模块设计输入的全局口径：
  - `OQ-001`、`OQ-002`、`OQ-003`
  - `OQ-004`、`OQ-005`
  - `OQ-006`、`OQ-007`
  - `OQ-008`、`OQ-011`
  - `OQ-014`
  - `OQ-017`、`OQ-018`
  - `OQ-019`、`OQ-020`、`OQ-022`、`OQ-023`
- 当前仍阻塞本轮最低位压缩的关键问题：
  - `OQ-021`：共享最小映射已澄清为 `page/page_size/q/status/sort/order`，但其“共享最小层 / 模块扩展层 / 实现细节层”仍需在三个模块的最低位文档中完全吸收。
  - `OQ-024`：旧入口的状态分层已基本清晰，但“历史容器 / 观察蓝本 / 正式子任务 ID”之间的正式映射规则仍需由总控写死。
  - `OQ-025`：最小共享输入已形成默认口径，但“最小输入层 / 扩展字段层 / 完整岗位链语义层”仍需继续收紧。
  - `M01`：只剩 `MQ-001`、`MQ-003`、`MQ-005` 属于本轮允许处理的最小阻塞集合。
  - `M02`：只剩 `/members` 共享契约、`OQ-024` 映射引用、`MT02_02` 的权限消费边界属于本轮允许处理的最小阻塞集合。
  - `M03`：只剩共享最小映射与模块扩展查询键的边界、`OQ-025` 的最小输入表述、以及最低位 API 中的 route / callback 边界属于本轮允许处理的最小阻塞集合。
- 当前仍阻塞下一批模块深化设计的问题：
  - `OQ-012` 上下文包中的 source priority 与引用摘要规则仍未完整冻结，`M06` 只能先停留在评审准备。
  - `OQ-016` 薄弱项聚合 key、消减规则和停练规则仍未完整冻结，`M09` 仍不宜进入主写深化。
- 当前过程性风险：
  - 若总控不把 `OQ-021 / OQ-024 / OQ-025` 的状态分层写死，模块最低位文档会再次回流到“重复讨论共享契约”的状态。
  - 若总控不继续把“白名单观察面”与“正式可进入子任务设计候选”分开登记，后续仍可能按错误入口开窗。
  - 若模块窗口超出最低位文档与最小阻塞集合，本轮会重新退化成普通收口轮。

## 5. 当前并行文档完善计划

> 本节由总控 Codex 每轮更新。任何“当前轮 / 下一轮”的并行计划都必须写在这里，而不能只停留在聊天中。
>
> 当前轮次（最低位压缩轮）的极窄并行计划：
> - 上一轮 `GC-02`、`MR-05`、`MR-06`、`MR-07`、`RV-03` 的结论已全部吸收为本轮输入，不再按旧任务包重复开窗。
> - 本轮固定为 5 个窗口：总控 x1、`M01` x1、`M02` x1、`M03` x1、评审 x1。
> - 本轮目标不是提升模块整体等级，也不是开放子任务窗口，而是把当前最关键的最低位文档和最小阻塞集合压缩到可复评范围。

### 5.1 当前阻塞项变化

- 已不再构成本轮主阻塞：
  - `SC-05` 作为独立主题的收口
  - 旧 `ST02_* / ST03_*` 被误判为可直开入口
  - `OQ-025` 被误写成“完整岗位链 ready”的表述
- 本轮仍需继续处理的阻塞：
  - `OQ-021`：需要把共享最小层、模块扩展层和实现细节层的分界彻底写死
  - `OQ-024`：需要把历史容器、观察蓝本、正式子任务 ID 三种状态的映射关系写死
  - `OQ-025`：需要把最小共享输入层与完整链路语义层继续分开
  - `M01`：只允许继续处理 `MQ-001`、`MQ-003`、`MQ-005`
  - `M02`：只允许继续处理 `/members` 共享契约、正式入口映射引用、`MT02_02` 权限消费边界
  - `M03`：只允许继续处理共享最小映射与模块扩展查询键边界、`OQ-025` 最小输入表述、route / callback 边界

### 5.2 本轮任务包

#### 任务包 GC-03：`OQ-021 / OQ-024 / OQ-025` 状态分层与正式映射定稿
- 任务包名称：`OQ-021 / OQ-024 / OQ-025` 状态分层与正式映射定稿
- 负责角色：总控 Codex
- 负责范围：统一 `OQ-021 / OQ-024 / OQ-025` 的正式映射与状态分层；其中 `OQ-024` 只处理旧入口退役后的正式编号 / 映射策略，并把“白名单观察面 / 正式候选 / 可开窗子任务”三种状态的全局登记方式写死。
- 允许修改的文档：
  - `OPEN_QUESTIONS.md`
  - `DOCUMENT_PROGRESS.md`
  - `DOCUMENT_MATURITY.md`
  - `MODULE_INDEX.md`
  - `TASK_INDEX.md`
  - `PLAN_LATEST.md`
  - `EXECUTION_LOG.md`
- 禁止修改的文档：
  - `docs/modules/**`
  - 所有 `sub_modules/**`
- 依赖的上游文档：
  - `AGENTS.md`
  - `docs/DOC_GOVERNANCE.md`
  - `RV-03` 评审回报
- 目标成熟度：
  - 让总控状态机足以支持“最低位压缩 -> 正式候选复评”的后续判断，但仍不直接放行子任务窗口。
- 完成标准：
  - `OQ-021` 的共享最小层、模块扩展层、实现细节层被明确分开。
  - `OQ-024` 的历史容器、观察蓝本、正式子任务 ID 三层状态被明确分开。
  - `OQ-025` 的最小共享输入层、扩展字段层、完整链路语义层被明确分开。
  - `TASK_INDEX.md` 与 `MODULE_INDEX.md` 对三种状态的表述完全一致。
  - 仍不开放任何子任务窗口。
- 若发现需求不清时的处理规则：
  - 只做保守映射，不创建新的全局 OQ。

#### 任务包 MR-08：`M01` 剩余 `L5` 候选前压缩
- 任务包名称：`M01` 剩余 `L5` 候选前压缩
- 负责角色：模块 Codex
- 负责范围：只收口 `MQ-001`、`MQ-003`、`MQ-005`，明确脚本 / CI 最小验证矩阵、共享列表实现级 contract 与 shared adapter 实现级承接方式；不再回到 `SC-05`、i18n、共享页面原语等其他主题。
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
  - `OPEN_QUESTIONS.md`
  - `TECHNICAL_STANDARDS.md`
  - `DESIGN_DECISIONS.md`
- 目标成熟度：
  - 只压缩 `M01` 最低位文档周围的最小阻塞集合，不追求本轮内整体升格。
- 完成标准：
  - `MQ-001`、`MQ-003`、`MQ-005` 的实现级残余边界被写清。
  - 最低位文档不再以开放问题集合的方式承载主阻塞。
  - 不新增新的跨模块共享问题。
- 若发现需求不清时的处理规则：
  - 不把实现级细节直接下放到 `ST01_*`。

#### 任务包 MR-09：`M02` 最低位 API 收口与观察面复评准备
- 任务包名称：`M02` 最低位 API 收口与观察面复评准备
- 负责角色：模块 Codex
- 负责范围：继续压实 `MODULE_API_DESIGN.md` 的 `/members` 列表共享契约、`OQ-024` 入口映射引用与 `MT02_02` 权限消费边界，并复核 `MT02_01 / MT02_02` 是否仍只停留在观察面；不扩写页面、i18n 与验证面。
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
  - `OPEN_QUESTIONS.md`
  - `MODULE_INDEX.md`
  - `TASK_INDEX.md`
  - `docs/modules/M01-foundation-and-platform/**`
- 目标成熟度：
  - 在不开放子任务窗口的前提下，为 `M02` 的正式候选复评准备更干净的最低位 API 文档。
- 完成标准：
  - `MT02_01 / MT02_02` 继续被明确记录为观察面，而非正式候选。
  - `MT02_03 / MT02_07` 继续保持后续顺位。
  - `MODULE_API_DESIGN.md` 中剩余歧义收敛到可复评范围。
- 若发现需求不清时的处理规则：
  - 不补写任何子任务双文档。

#### 任务包 MR-10：`M03` 最低位 API 收口与最小输入稳定化
- 任务包名称：`M03` 最低位 API 收口与最小输入稳定化
- 负责角色：模块 Codex
- 负责范围：继续压实 `MODULE_API_DESIGN.md` 中共享最小映射、模块扩展查询键和 route / callback 细节的边界，并稳定 `OQ-025` 的最小共享输入表述；不扩写上传 / 导出链和完整岗位链 ready 叙事。
- 允许修改的文档：
  - `docs/modules/M03-jobs-resumes-and-documents/MODULE_REQUIREMENTS.md`
  - `docs/modules/M03-jobs-resumes-and-documents/MODULE_DESIGN.md`
  - `docs/modules/M03-jobs-resumes-and-documents/MODULE_API_DESIGN.md`
  - `docs/modules/M03-jobs-resumes-and-documents/MODULE_SCHEMA_DESIGN.md`
  - `docs/modules/M03-jobs-resumes-and-documents/MODULE_LOGIC_DESIGN.md`
  - `docs/modules/M03-jobs-resumes-and-documents/MODULE_DEPENDENCIES.md`
  - `docs/modules/M03-jobs-resumes-and-documents/MODULE_TASK_INDEX.md`
  - `docs/modules/M03-jobs-resumes-and-documents/MODULE_OPEN_QUESTIONS.md`
  - `docs/modules/M03-jobs-resumes-and-documents/MODULE_EXECUTION_LOG.md`
- 禁止修改的文档：
  - 所有根目录全局状态文档
  - `docs/modules/M03-jobs-resumes-and-documents/sub_modules/**`
  - 其他模块目录
- 依赖的上游文档：
  - `OPEN_QUESTIONS.md`
  - `MODULE_INDEX.md`
  - `TASK_INDEX.md`
  - `docs/modules/M01-foundation-and-platform/**`
- 目标成熟度：
  - 继续维持 `L4`，但为岗位链局部候选复评准备更稳定的最低位 API 文档。
- 完成标准：
  - `updated_after / updated_before` 不再在最低位文档中被写成共享最小映射。
  - `OQ-025` 的最小输入表述不再外溢成“完整岗位链 ready”。
  - `MT03_01 / MT03_03` 继续保持为观察面，而非正式候选。
- 若发现需求不清时的处理规则：
  - 不提前放行上传 / 导出链。

#### 任务包 RV-04：正式候选前交叉复核
- 任务包名称：正式候选前交叉复核
- 负责角色：评审 Codex
- 负责范围：交叉复核 `GC-03`、`MR-08`、`MR-09`、`MR-10` 的输出，判断是否已具备“正式候选复评”条件，而不是直接判断是否允许开子任务窗口。
- 允许修改的文档：
  - 无。本任务包只读评审，产出直接回报总控。
- 禁止修改的文档：
  - 所有全局状态文档
  - 所有模块与子任务文档
- 依赖的上游文档：
  - `DOCUMENT_MATURITY.md`
  - `DOCUMENT_PROGRESS.md`
  - `MODULE_INDEX.md`
  - `OPEN_QUESTIONS.md`
  - `docs/modules/M01-foundation-and-platform/**`
  - `docs/modules/M02-identity-and-team/**`
  - `docs/modules/M03-jobs-resumes-and-documents/**`
- 目标成熟度：
  - 不直接提升成熟度，目标是为“是否进入正式候选复评”提供可靠依据。
- 完成标准：
  - 明确是否仍应继续模块轮。
  - 明确是否已有模块达到“可进入子任务设计候选”的前置条件。
  - 明确若继续关闭子任务窗口，还差哪两三条总控口径或最低位文档条件。
- 若发现需求不清时的处理规则：
  - 只记录保守结论，不补关键契约。

## 6. 当前模块推进判断

> 本节用于让你一眼看到：哪个模块在什么阶段、是否能继续拆到子任务。

| 模块 | 当前主阶段 | 当前判断 | 是否可进入子任务设计 | 主要原因 |
| --- | --- | --- | --- | --- |
| M01 | 最低位压缩 | 整体高 `L4`，接近 `L5` 候选但未到整体候选 | 否 | 本轮只允许处理 `MQ-001`、`MQ-003`、`MQ-005`；`SC-05` 相关主题已足够作为 `M03/M05` 的局部设计输入，不再回流为当前主阻塞 |
| M02 | 最低位 API 压缩 | 整体高 `L4`，仍是当前最接近整体 `L5` 候选的模块，但本轮后仍只有观察面 | 否 | 本轮只允许处理 `/members` 共享契约、`OQ-024` 入口映射引用、`MT02_02` 权限消费边界；页面 / i18n / 验证面继续后置 |
| M03 | 最低位 API 压缩 | 整体 `L4`，只有少量链路接近候选，模块整体不 ready | 否 | 本轮只允许处理共享最小映射与模块扩展查询键边界、`OQ-025` 最小输入表述、以及 route / callback 边界；上传 / 导出链继续后置 |
| M04 | 需求初稿 + 模块骨架 | 整体 L1，下一轮不建议作为主写窗口 | 否 | `M03` 尚未正式形成稳定输入，且 `OQ-008` 之外仍缺上游边界 |
| M05 | 需求初稿 + 模块骨架 | 整体 L1，下一轮不建议作为主写窗口 | 否 | `OQ-009/OQ-010` 仍 open，且依赖 `M03/M04` |
| M06 | 需求初稿 + 模块骨架 | 整体 L1，下一轮不建议作为主写窗口 | 否 | `OQ-012` 仍 open，且依赖 `M03-M05` 设计输入 |
| M07 | 需求初稿 + 模块骨架 | 整体 L1，本轮纳入共享阻塞评审，不进入主写 | 否 | 评估口径虽可先按默认框架评审，但仍缺 `M06` 输入 |
| M08 | 需求初稿 + 模块骨架 | 整体 L1，本轮纳入共享阻塞评审，不进入主写 | 否 | review 输入模型与复盘对象仍未得到上游设计支撑 |
| M09 | 需求初稿 + 模块骨架 | 整体 L1，本轮纳入共享阻塞评审，不进入主写 | 否 | `OQ-016` 仍 open，且共享评估口径尚未完成模块级回写 |
| M10 | 需求初稿 + 模块骨架 | 整体 L1，本轮纳入共享阻塞评审，不进入主写 | 否 | 治理边界虽有默认口径，但仍依赖 `M02/M03/M06/M09` 的稳定输入 |

## 7. 下一轮建议

- 若本轮 `GC-03 / MR-08 / MR-09 / MR-10 / RV-04` 收包后仍存在口径漂移，则继续维持阶段 3 的模块轮，不转入子任务推进轮。
- 若本轮能把 `OQ-024` 的状态分层写死，并把 `M01/M02/M03` 的最低位文档压缩到可复评范围，则下一步才考虑“正式候选复评”，而不是直接开子任务窗口。
- 即使 `M02: MT02_01 / MT02_02`、`M03: MT03_01 / MT03_03` 继续保留观察面，也仍不等于正式开放子任务设计窗口。
- 在 `OQ-024` 映射定稿、`OQ-021` 在三个模块最低位文档上的吸收闭合、且评审确认至少一个模块达到正式候选前，不允许开启任何子任务 Codex。

## 8. 本轮收口要求

每轮结束后，总控 Codex 至少要回写：
1. 当前低成熟度重点模块
2. 当前并行文档完善计划
3. 当前模块推进判断
4. 当前阻塞项是否变化
5. 下一轮建议是否变化
6. 与 `DOCUMENT_MATURITY.md` 是否一致

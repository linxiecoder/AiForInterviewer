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

- 当前阶段：阶段 3
- 阶段目标：从“优先模块设计可评审”推进到“优先模块形成稳定下游输入”
- 本轮总控判断：
  - `M01/M02/M03` 已整体从 `L2` 提升到 `L4`
  - 当前最低成熟度模块仍为 `M04-M10`
  - 下一轮仍应优先推进 `M01/M02/M03`，暂不切换到 `M04/M05/M06` 全面主写
- 已完成事项：
  - 修复全局入口和总控文档乱码。
  - 建立根目录全局文档体系。
  - 建立 `docs/modules/` 模块目录与模块骨架。
  - 建立模块级待确认问题与子任务目录。
  - 建立成熟度与进展跟踪入口。
  - 完成 `M01`、`M02`、`M03` 首轮模块设计收敛，并把三者统一推进到可评审层级。
  - 明确 `M01` 的剩余缺口集中在平台共享契约，`M02` 的剩余缺口集中在对齐 M01 契约和清理命名漂移，`M03` 的剩余缺口集中在状态/冲突/下载映射等收口项。
  - 识别出需要上升为全局治理的问题：最小 CI 验证矩阵、共享页面原语、列表查询状态映射、locale 策略，以及 admin 成员管理归属。
  - 明确当前仍没有任何模块达到正式子任务设计准入条件。
- 当前未完成事项：
  - `M01` 的共享平台契约尚未总控收口到全局：根目录脚本/最小 CI、页面头部/摘要区、列表查询状态与 locale 策略仍未完全冻结。
  - `M02` 仍需完成与 `M01` 共享契约的最终对齐，并修正 `display_name/displayName`、`teams.id/team_id`、`logout` 响应体与 `/members` envelope 的口径漂移。
  - `M03` 虽已形成完整可评审草案，但仍未正式达到稳定下游输入。
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
  - `OQ-019` 根目录统一脚本与最小 CI 校验矩阵的冻结粒度仍未明确。
  - `OQ-020` 共享页面原语（`PageHeader` / Dashboard 摘要区）的最小接口边界仍未明确。
  - `OQ-021` 列表查询状态、分页交互与 URL / callback 映射仍未明确。
  - `OQ-022` locale fallback、切换策略与消息命名空间仍未明确。
- 当前仍阻塞下一批模块深化设计的问题：
  - `OQ-012` 上下文包中的 source priority 与引用摘要规则仍未完整冻结，`M06` 只能先停留在评审准备。
  - `OQ-016` 薄弱项聚合 key、消减规则和停练规则仍未完整冻结，`M09` 仍不宜进入主写深化。
- 当前过程性风险：
  - 两个模块 `MODULE_EXECUTION_LOG.md` 仍保留模板化收口，不适合作为正式成熟度提升的唯一依据。
  - `M02` 已把部分模块级问题清空，但全局共享契约依赖尚未真正消失；若总控不先统一口径，会出现“模块自评 L5、全局仍判 L4”的双重叙事。

## 5. 当前并行文档完善计划

> 本节由总控 Codex 每轮更新。任何“第一轮 / 当前轮”的并行计划都必须写在这里，而不能只停留在聊天中。

### 5.1 本轮总目标
- 已完成：
  - 将 `M01/M02/M03` 从“需求初稿 + 设计骨架”推进到“模块设计可评审”
  - 收到 `M01`、`M02` 模块回报与评审回报，并据此识别出应上升为全局的问题
- 本轮未完成：
  - `M01/M02/M03` 尚未正式形成稳定下游输入
  - `M04/M05/M06` 仍不具备全面主写条件
- 下一轮目标：
  - 先收口 `M01/M02/M03` 的共享契约与全局对齐问题，再决定是否开放 `M04/M05/M06`

### 5.2 本轮任务包
#### 任务包 A：M01 平台共享契约全局化收口
- 负责角色：模块 Codex
- 负责范围：继续收口 `M01` 的模块级共享平台契约，并把影响多模块的剩余缺口与总控口径对齐。
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
- 本轮已冻结输入：
  - `OQ-001` monorepo：`apps/web` + `apps/api` + `infra`
  - `OQ-002` 首轮只建立最小运行时、测试和 CI 基线
  - `OQ-003` 视觉规范首轮只沉淀壳层、头部、列表原语与基础页面样式
- 目标成熟度：
  - 模块核心文档从高 `L4` 收口到可判定是否升入 `L5`
- 完成标准：
  - `OQ-019~OQ-022` 对应的模块级表达与全局口径一致。
  - 页面头部/摘要区、列表查询状态与 locale 策略不再只停留在方向级描述。
  - 是否具备 `L5` 候选条件可以由总控用统一尺子判断。
- 若发现需求不清时的处理规则：
  - 不补关键契约。
  - 先写入 `MODULE_OPEN_QUESTIONS.md`，再向总控回报。

#### 任务包 B：M02 鉴权与成员目录契约对齐收口
- 负责角色：模块 Codex
- 负责范围：在不扩大模块边界的前提下，修复 `M02` 与 `M01`、`M10` 相关的共享契约漂移。
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
- 本轮已冻结输入：
  - `OQ-004` P1 鉴权默认采用固定 Bearer token
  - `OQ-005` 权限矩阵首轮只覆盖 P1 页面与 API，不扩展未来多租户治理
- 本轮必须显式处理的对齐项：
  - `/members` 列表 envelope / 分页参数与 `M01` 列表原语的关系
  - `display_name / displayName` 命名一致性
  - `teams.id / team_id` 主键与外键表述一致性
  - `logout` 成功响应语义
- 目标成熟度：
  - 模块核心文档从高 `L4` 收口到可判定是否升入 `L5`
- 完成标准：
  - 模块内不再同时存在“已完全 L5”与“仍依赖 M01 未冻结契约”两套叙事。
  - `MQ-203` 的跨模块职责边界与全局 `OPEN_QUESTIONS.md` 对齐。
  - 模块是否可进入 `L5` 候选有清晰、可审计的依据。
- 若发现需求不清时的处理规则：
  - 不补关键契约。
  - 先写入 `MODULE_OPEN_QUESTIONS.md`，再向总控回报。

#### 任务包 C：M03 从可评审草案收口到稳定候选
- 负责角色：模块 Codex
- 负责范围：在不回退既有设计的前提下，把 `M03` 的剩余缺口压缩到可由总控判断是否进入 `L5` 候选。
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
- 本轮已冻结输入：
  - `OQ-006` Markdown 预览与导出共用同一渲染链
  - `OQ-007` 上传可同步入库，转换与导出走异步任务
- 目标成熟度：
  - 模块核心文档从 `L4` 收口到可判定是否升入 `L5`
- 完成标准：
  - 状态枚举、版本冲突策略、下载入口映射仍未冻结的部分被清楚隔离到子任务层或后续模块，而不是继续悬在模块层。
  - 输出给 `M04/M05/M06` 的可依赖内容与不可依赖内容被显式列出。
- 若发现需求不清时的处理规则：
  - 不补关键契约。
  - 先写入 `MODULE_OPEN_QUESTIONS.md`，再向总控回报。

#### 任务包 D：评审 / 总控共享契约校准
- 负责角色：评审 Codex
- 负责范围：只读评审 `M01-M03` 与根目录状态文档之间的共享契约一致性，输出“哪些问题必须先全局收口”。
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
  - `docs/modules/M01-foundation-and-platform/**`
  - `docs/modules/M02-identity-and-team/**`
  - `docs/modules/M03-jobs-resumes-and-documents/**`
- 目标成熟度：
  - 不直接提升模块成熟度，目标是降低“模块自评”和“总控登记”之间的口径差。
- 完成标准：
  - 明确哪些模块级问题必须上升到根目录 `OPEN_QUESTIONS.md`。
  - 明确 `M01/M02/M03` 哪些剩余缺口属于总控收口、哪些仍应由模块继续写清。
- 若发现需求不清时的处理规则：
  - 不补关键契约。
  - 只记录到评审回报，由总控决定是否升级到全局 `OPEN_QUESTIONS.md`。

## 6. 当前模块推进判断

> 本节用于让你一眼看到：哪个模块在什么阶段、是否能继续拆到子任务。

| 模块 | 当前主阶段 | 当前判断 | 是否可进入子任务设计 | 主要原因 |
| --- | --- | --- | --- | --- |
| M01 | 模块设计可评审 | 整体高 `L4`，下一轮仍应优先推进收口 | 否 | 根目录脚本/最小 CI、共享页面原语、列表查询状态与 locale 契约未全局冻结 |
| M02 | 模块设计可评审 | 整体高 `L4`，下一轮仍应优先推进收口 | 否 | 仍依赖 `M01` 未冻结的列表/i18n 契约，且存在 DTO / schema / 响应语义漂移 |
| M03 | 模块设计可评审 | 整体 `L4`，下一轮仍应优先推进收口 | 否 | 状态枚举、版本冲突策略与下载入口映射仍待收口；尚未正式形成稳定下游输入 |
| M04 | 需求初稿 + 模块骨架 | 整体 L1，下一轮不建议作为主写窗口 | 否 | `M03` 尚未正式形成稳定输入，且 `OQ-008` 之外仍缺上游边界 |
| M05 | 需求初稿 + 模块骨架 | 整体 L1，下一轮不建议作为主写窗口 | 否 | `OQ-009/OQ-010` 仍 open，且依赖 `M03/M04` |
| M06 | 需求初稿 + 模块骨架 | 整体 L1，下一轮不建议作为主写窗口 | 否 | `OQ-012` 仍 open，且依赖 `M03-M05` 设计输入 |
| M07 | 需求初稿 + 模块骨架 | 整体 L1，本轮纳入共享阻塞评审，不进入主写 | 否 | 评估口径虽可先按默认框架评审，但仍缺 `M06` 输入 |
| M08 | 需求初稿 + 模块骨架 | 整体 L1，本轮纳入共享阻塞评审，不进入主写 | 否 | review 输入模型与复盘对象仍未得到上游设计支撑 |
| M09 | 需求初稿 + 模块骨架 | 整体 L1，本轮纳入共享阻塞评审，不进入主写 | 否 | `OQ-016` 仍 open，且共享评估口径尚未完成模块级回写 |
| M10 | 需求初稿 + 模块骨架 | 整体 L1，本轮纳入共享阻塞评审，不进入主写 | 否 | 治理边界虽有默认口径，但仍依赖 `M02/M03/M06/M09` 的稳定输入 |

## 7. 下一轮建议

- 仍优先开启 `M01`、`M02`、`M03` 三个模块窗口，但目标从“脱离骨架”改为“收口共享契约、争取进入 L5 候选”。
- 另开 1 个评审 / 总控校准窗口，专门处理共享契约上升全局的问题，不再继续做宽泛的 `M04-M10` 只读评审。
- 暂不建议把主写窗口切到 `M04/M05/M06`；最多只允许做准备性阅读，不建议全面改写。
- 本轮仍不要开启任何子模块 Codex；所有 `SUBTASK_DESIGN.md` / `SUBTASK_IMPLEMENTATION.md` 目前都还不具备细化条件。
- 在 `M01/M02/M03` 正式升入 `L5` 前，先统一清理 `SUBTASK_DESIGN.md` 中残留的父模块模板占位符，并补真实模块执行日志。

## 8. 本轮收口要求

每轮结束后，总控 Codex 至少要回写：
1. 当前低成熟度重点模块
2. 当前并行文档完善计划
3. 当前模块推进判断
4. 当前阻塞项是否变化
5. 下一轮建议是否变化
6. 与 `DOCUMENT_MATURITY.md` 是否一致

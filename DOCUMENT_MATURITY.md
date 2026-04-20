# AI 模拟面试 P1 文档成熟度

## 1. 文档定位

- 本文档用于统一定义文档成熟度等级，并登记当前全局、模块和子任务文档的成熟状态。
- 成熟度用于判断文档是否可以作为下游输入，或是否已经具备直接实施条件。
- 本文档由总控 Codex 主责维护；模块 Codex 和子模块 Codex 可以提出成熟度建议，但不应各自维护独立标准。
- 每轮工作结束后，必须结合实际文档变化同步更新本文件，并与 `DOCUMENT_PROGRESS.md`、`OPEN_QUESTIONS.md` 保持一致。

## 2. 成熟度等级定义

| 等级 | 名称 | 说明 | 可作为下游输入 | 可直接用于实施 |
| --- | --- | --- | --- | --- |
| L0 | 未创建 | 文档不存在或仅在索引中占位 | 否 | 否 |
| L1 | 仅有骨架 | 只有标题、章节或极少量提示信息 | 否 | 否 |
| L2 | 初稿 | 已有初步内容，但边界、输入输出、依赖和问题仍不稳定 | 否 | 否 |
| L3 | 待澄清 | 结构基本完整，但仍有会阻塞下游的关键问题 | 否 | 否 |
| L4 | 可评审 | 已具备稳定结构，可用于组织评审，但尚未细化到实施粒度 | 部分 | 否 |
| L5 | 可作为下游输入 | 已能稳定支撑下游设计或拆分 | 是 | 否 |
| L6 | 可直接用于实施 | 已明确目标、范围、文件边界、实施步骤、验证方式和 DoD | 是 | 是 |
| L7 | 稳定维护 | 已经过多轮使用和回写，只做增量维护 | 是 | 是 |

## 3. 各类文档门槛

| 文档类型 | 达到“可评审”需要具备 | 达到“可作为下游输入”需要具备 | 达到“可直接用于实施”需要具备 |
| --- | --- | --- | --- |
| 全局文档 | 目标、范围、索引、规则稳定 | 能稳定指导模块拆分、成熟度更新与回写 | 不直接用于代码实施 |
| 模块文档 | 模块职责、依赖、边界明确 | 可稳定拆分为子任务并指导下游设计 | 不直接用于代码实施 |
| 子任务设计文档 | 目标、范围、依赖、输入输出明确 | 能稳定指导 `SUBTASK_IMPLEMENTATION.md` | 不直接用于代码实施 |
| 子任务实施文档 | 实施目标、目标区域和前置条件明确 | 上游设计稳定，且修改范围与验证方式清晰 | 具备修改范围、步骤、验证、DoD、回滚方案 |

## 4. 当前登记

### 4.1 全局文档

| 文档路径 | 文档类型 | 当前等级 | 当前缺失项 | 下一等级所需补充 | 是否可作为下游输入 | 是否可直接用于实施 |
| --- | --- | --- | --- | --- | --- | --- |
| `AGENTS.md` | global-governance-entry | L5 | 需随新文档与新协作方式持续补充索引 | 补充新规则入口并稳定维护 | 是 | 否 |
| `docs/DOC_GOVERNANCE.md` | global-governance-rules | L5 | 需结合真实并行协作继续校正细则 | 增补并行冲突样例与回写细则 | 是 | 否 |
| `PLAN_LATEST.md` | global-plan | L4 | 模块优先级、阶段目标、任务节奏仍需随轮次收敛 | 补充阶段推进依据与模块进入标准 | 部分 | 否 |
| `TASK_INDEX.md` | global-task-index | L3 | 状态、成熟度、模块/子任务映射仍是首轮登记 | 建立稳定的状态回写和优先级排序 | 否 | 否 |
| `EXECUTION_LOG.md` | global-execution-log | L2 | 执行样本仍少，尚未形成跨轮次复盘习惯 | 累积至少数轮真实更新记录 | 否 | 否 |
| `TECHNICAL_STANDARDS.md` | global-standard | L3 | 多项默认技术口径仍待确认 | 收敛高影响技术口径并形成稳定规范 | 否 | 否 |
| `DESIGN_DECISIONS.md` | global-decision-log | L3 | 多项 proposed 决策仍待收敛 | 关闭关键 proposed 决策并建立引用关系 | 否 | 否 |
| `MODULE_INDEX.md` | global-module-index | L3 | 模块成熟度、最低成熟度文档、阶段状态需持续回写 | 建立模块级稳定总览表 | 否 | 否 |
| `OPEN_QUESTIONS.md` | global-open-questions | L3 | 待确认项仍未逐轮关闭，优先级未收敛 | 完成高优问题分层与关闭规则 | 否 | 否 |
| `DOCUMENT_MATURITY.md` | global-maturity | L4 | 需结合后续真实推进持续校正登记 | 加强模块和子任务的真实成熟度变化记录 | 部分 | 否 |
| `DOCUMENT_PROGRESS.md` | global-progress | L4 | 当前仍以文档建设进度为主，缺少任务包沉淀 | 固定记录并行任务包与阶段推进标准 | 部分 | 否 |

### 4.2 模块文档模板成熟度

> 说明：本节描述“模块文档模板”的当前成熟度，不等同于某个具体模块已经达到该等级。

| 文档模板 | 当前等级 | 当前缺失项 | 下一等级所需补充 |
| --- | --- | --- | --- |
| `$base/MODULE_REQUIREMENTS.md` | L2 | 仍需继续从源设计稿抽取稳定边界、角色、场景和验收标准 | 补齐模块边界、异常场景、验收标准模板 |
| `$base/MODULE_DESIGN.md` | L1 | 组件拆分、职责边界与协作路径仍需细化 | 增补模块职责、对象模型、依赖与状态变化模板 |
| `$base/MODULE_API_DESIGN.md` | L1 | 输入输出契约、错误语义与鉴权边界仍需补齐 | 增补统一接口契约、错误码与鉴权章节 |
| `$base/MODULE_SCHEMA_DESIGN.md` | L1 | 核心实体、字段约束和生命周期仍需补齐 | 增补实体定义、约束、索引、迁移模板 |
| `$base/MODULE_LOGIC_DESIGN.md` | L1 | 状态机、例外路径和规则分支仍需补齐 | 增补主流程、分支流程、异常路径和状态机模板 |
| `$base/MODULE_TASK_INDEX.md` | L2 | 子任务优先级与成熟度需要持续回写 | 增补成熟度字段、阻塞字段、下游 readiness 字段 |
| `$base/MODULE_OPEN_QUESTIONS.md` | L2 | 仍需逐轮关闭或降级问题 | 增补问题优先级、影响范围和关闭状态 |
| `$base/MODULE_EXECUTION_LOG.md` | L1 | 需要在模块进入真实实施后持续补齐 | 增补轮次摘要、成熟度变化、阻塞与建议动作模板 |

### 4.3 子任务文档模板成熟度

> 说明：本节描述“子任务文档模板”的当前成熟度，不等同于某个具体子任务已经达到该等级。

| 文档模板 | 当前等级 | 当前缺失项 | 下一等级所需补充 |
| --- | --- | --- | --- |
| `$subBase/SUBTASK_DESIGN.md` | L2 | 输入输出、目标区域、验证目标和边界仍需细化 | 增补接口契约、数据结构、状态变化、测试设计模板 |
| `$subBase/SUBTASK_IMPLEMENTATION.md` | L2 | 修改范围、步骤、验证、DoD 和回滚方案仍需细化 | 增补允许修改范围、逐步验证、浏览器验证、代码检视与提交模板 |

## 5. 当前低成熟度重点模块

> 由总控 Codex 每轮评估后更新。本节必须反映“当前真实模块状态”，而不是模板状态。

### 5.1 本轮模块成熟度变化

| 模块 | 本轮整体成熟度 | 当前最低成熟度文档 | 变化说明 | 是否可进入子任务设计 |
| --- | --- | --- | --- | --- |
| M01 | L2 | `MODULE_DESIGN.md` / `MODULE_API_DESIGN.md` / `MODULE_SCHEMA_DESIGN.md` / `MODULE_LOGIC_DESIGN.md`（L1） | 从“待评估”回写为“需求初稿已成型，但设计包仍是骨架” | 否 |
| M02 | L2 | `MODULE_DESIGN.md` / `MODULE_API_DESIGN.md` / `MODULE_SCHEMA_DESIGN.md` / `MODULE_LOGIC_DESIGN.md`（L1） | 从“待评估”回写为“需求初稿已成型，但设计包仍是骨架” | 否 |
| M03 | L2 | `MODULE_DESIGN.md` / `MODULE_API_DESIGN.md` / `MODULE_SCHEMA_DESIGN.md` / `MODULE_LOGIC_DESIGN.md`（L1） | 从“待评估”回写为“需求初稿已成型，但设计包仍是骨架” | 否 |
| M04 | L1 | `MODULE_DESIGN.md` / `MODULE_API_DESIGN.md` / `MODULE_SCHEMA_DESIGN.md` / `MODULE_LOGIC_DESIGN.md`（L1） | 本轮确认仍停留在“需求初稿 + 模块骨架”阶段 | 否 |
| M05 | L1 | `MODULE_DESIGN.md` / `MODULE_API_DESIGN.md` / `MODULE_SCHEMA_DESIGN.md` / `MODULE_LOGIC_DESIGN.md`（L1） | 本轮确认仍停留在“需求初稿 + 模块骨架”阶段 | 否 |
| M06 | L1 | `MODULE_DESIGN.md` / `MODULE_API_DESIGN.md` / `MODULE_SCHEMA_DESIGN.md` / `MODULE_LOGIC_DESIGN.md`（L1） | 本轮确认仍停留在“需求初稿 + 模块骨架”阶段 | 否 |
| M07 | L1 | `MODULE_DESIGN.md` / `MODULE_API_DESIGN.md` / `MODULE_SCHEMA_DESIGN.md` / `MODULE_LOGIC_DESIGN.md`（L1） | 本轮确认仍停留在“需求初稿 + 模块骨架”阶段 | 否 |
| M08 | L1 | `MODULE_DESIGN.md` / `MODULE_API_DESIGN.md` / `MODULE_SCHEMA_DESIGN.md` / `MODULE_LOGIC_DESIGN.md`（L1） | 本轮确认仍停留在“需求初稿 + 模块骨架”阶段 | 否 |
| M09 | L1 | `MODULE_DESIGN.md` / `MODULE_API_DESIGN.md` / `MODULE_SCHEMA_DESIGN.md` / `MODULE_LOGIC_DESIGN.md`（L1） | 本轮确认仍停留在“需求初稿 + 模块骨架”阶段 | 否 |
| M10 | L1 | `MODULE_DESIGN.md` / `MODULE_API_DESIGN.md` / `MODULE_SCHEMA_DESIGN.md` / `MODULE_LOGIC_DESIGN.md`（L1） | 本轮确认仍停留在“需求初稿 + 模块骨架”阶段 | 否 |

### 5.2 当前低成熟度重点模块

| 优先级 | 模块 | 当前整体判断 | 主要缺口 | 当前最低成熟度文档 | 是否可进入子任务设计 |
| --- | --- | --- | --- | --- | --- |
| P0 | M04、M05、M06 | 下游链路核心模块整体停留在 L1，仍缺稳定模块设计输入 | 字段级 API 契约、schema 关系、状态变化、异常回退与跨模块边界均未固化 | `MODULE_DESIGN.md` / `MODULE_API_DESIGN.md` / `MODULE_SCHEMA_DESIGN.md` / `MODULE_LOGIC_DESIGN.md` | 否 |
| P0 | M07、M08、M09、M10 | 业务后段模块整体停留在 L1，且被共享评估口径和治理边界问题共同阻塞 | 评估规则、review 输入、弱项生命周期、管理台治理边界都未从“方向”收敛为契约 | `MODULE_DESIGN.md` / `MODULE_API_DESIGN.md` / `MODULE_SCHEMA_DESIGN.md` / `MODULE_LOGIC_DESIGN.md` | 否 |
| P1 | M01、M02、M03 | 基础链路虽达到 L2，但设计包仍为骨架，尚不能向下游稳定供给 | monorepo、鉴权、渲染链与异步边界仍未冻结，导致设计包无法进入可评审 | `MODULE_DESIGN.md` / `MODULE_API_DESIGN.md` / `MODULE_SCHEMA_DESIGN.md` / `MODULE_LOGIC_DESIGN.md` | 否 |

## 6. 当前可作为下游输入的文档

> 由总控 Codex 统一登记，供模块 Codex 与子模块 Codex 判断是否可继续推进。

- `AGENTS.md`
- `docs/DOC_GOVERNANCE.md`

> 说明：本轮未发现任何模块级或子任务级文档达到稳定下游输入门槛；当前可稳定依赖的仍仅限全局治理入口。

## 7. 当前可直接用于实施的子任务

> 只有当 `SUBTASK_DESIGN.md >= L5` 且 `SUBTASK_IMPLEMENTATION.md >= L6` 时，子任务才能出现在这里。

- 暂无。
- 本轮 readiness 判断：所有模块均未达到 `MODULE_REQUIREMENTS / MODULE_DESIGN / MODULE_API_DESIGN / MODULE_SCHEMA_DESIGN / MODULE_LOGIC_DESIGN >= L5` 的上游门槛；所有 `SUBTASK_DESIGN.md` 与 `SUBTASK_IMPLEMENTATION.md` 也都仍停留在骨架级或接近骨架级，因此没有可进入实施准备或代码实施的子任务。

## 8. 判断规则

- 模块文档达到 L5 前，不应将子任务实施文档视为可直接执行输入。
- 子任务设计文档达到 L5 后，才允许继续细化对应实施文档。
- 子任务实施文档达到 L6 前，不进入代码实施。
- 模块 Codex 与子模块 Codex 可以提出成熟度建议，但最终回写以总控 Codex 为准。
- 每轮工作结束后，必须同步回写本文件与 `DOCUMENT_PROGRESS.md`。

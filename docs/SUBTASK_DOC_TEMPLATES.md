# 子任务双文档模板

## 1. 文档定位与边界

- 本文档用于统一定义子任务双文档模板：
  - `SUBTASK_DESIGN.md`
  - `SUBTASK_IMPLEMENTATION.md`
- 本文档是模板事实来源，用于指导写作，不负责定义 `doc-governor` 的正式状态真值。
- 子任务是否允许推进、何时可开窗、何时可视为 `downstream_ready` / `implementation_ready`，应以以下真值来源为准：
  - `docs/governance/DOC_AUTOMATION.md`
  - `tools/doc_governor/cli.py`
  - `tools/doc_governor/schema.py`
  - `tools/doc_governor/validate.py`
  - `tools/doc_governor/evaluate.py`
  - `tools/doc_governor/confirm.py`
- Markdown 正文中的自我声明不会自动写回 `DOC_STATE.yaml`；模板只负责帮助作者把信息写清楚，不负责“自封状态”。
- 当前主链下，子任务的两个官方文档槽位就是：
  - `SUBTASK_DESIGN.md`
  - `SUBTASK_IMPLEMENTATION.md`
- `DOC_GOVERNOR_REPORT.md`、讨论轮次文件、history、evaluate JSON 等运行工件都不能替代这两个官方文档槽位。

## 2. 使用原则

- 设计文档和实施文档必须分离。
- `SUBTASK_DESIGN.md` 解释“做什么、为什么这样做、边界在哪里”。
- `SUBTASK_IMPLEMENTATION.md` 解释“本轮怎么实施、允许改哪里、如何验证、何时算完成”。
- 不要在 `SUBTASK_IMPLEMENTATION.md` 中重复复制大量设计内容。
- 不要在 `SUBTASK_DESIGN.md` 中退化成简单操作步骤。
- 如果上游 requirement / module 文档不稳定，优先记录阻塞与待确认问题，不要发明契约。
- 如果 `SUBTASK_IMPLEMENTATION.md` 仍然只是空模板或占位骨架，不要把它写成已经进入 `implementation_ready`。

## 3. 中文文档规则

本模板生成的正式文档默认必须满足以下要求：

- 文档主标题必须使用中文。
- 章节标题必须使用中文。
- 正文必须以中文为主。
- 英文仅允许用于必要技术标识，例如：
  - 代码
  - 命令
  - 文件路径
  - 配置键
  - 接口名
  - 类名
  - 函数名
  - 字段名
  - 协议名、标准名、库名、框架名
  - 难以自然翻译且翻译会降低准确性的术语

不建议出现以下写法：

- 英文主标题
- 英文章节标题
- 大段英文正文
- 用英文直接描述本应中文表达的需求、技术方案、实施方案、结论

若需保留英文术语，优先采用“中文说明 + 英文原词”的写法。

## 4. 状态口径说明

### 4.1 作者写作态

如需在正文中记录当前写作进度，建议只使用“作者写作态”这种说明性口径，例如：

- `骨架中`
- `编写中`
- `待评审`
- `阻塞中`

这些标签只表示作者当前的写作进度或人工判断，不是 `doc-governor` 的正式状态值。

### 4.2 官方状态字段

当前与子任务最相关的官方状态字段主要包括：

- `maturity`
- `candidate_status`
- `review_status`
- `readiness`
- `implementation_doc_state`
- `blocker_refs`

这些字段的正式真值保存在 `docs/governance/DOC_STATE.yaml`，只能通过当前治理流程和工具链维护，不应在模板正文中自我确认。

### 4.3 gate 关注点

当前代码与治理流程对以下信息最敏感：

- 上游 requirement / module 是否已经足够稳定
- `SUBTASK_DESIGN.md` 是否存在且不只是空骨架
- `SUBTASK_IMPLEMENTATION.md` 是否存在且不只是空骨架
- `implementation_doc_state` 是否已经进入 `active_working_doc`
- 当前是否仍存在 `blocker_refs`
- 全局 `formal_window_open` 是否允许进入正式实施开窗

因此，模板的目标不是“把状态写成对的枚举”，而是把这些判断所依赖的信息写完整、写清楚。

### 4.4 旧状态用语的处理方式

以下旧写法不再建议直接作为模板中的“当前状态”字段使用：

| 旧写法 | 当前处理方式 |
| --- | --- |
| `draft` | 改为作者写作态，例如 `骨架中` / `编写中` |
| `reviewable` | 改为作者写作态，例如 `待评审` |
| `downstream-ready` | 不再作为正文自封状态；若要表达，应写“当前判断已接近下游输入可用”，正式真值仍看 `readiness=downstream_ready` |
| `blocked` | 不再把它当唯一状态字段；正文中可写“当前阻塞原因”，正式真值仍看 `readiness=blocked` 与 `blocker_refs` |
| `implementation-ready` | 不再作为正文自封状态；正式真值仍看 `readiness=implementation_ready`、`implementation_doc_state`、`formal_window_open` 与实际 blocker |

## 5. requirement / module / task 链路说明

当前模板服务的对象，位于如下链路中：

- requirement：当前仓库主链通常按 requirement 索引簇工作，必要时可引用 `RQxx`
- module：`Mxx`
- task / subtask：当前主链仍以 `STxx_yy` 作为子任务 ID，并在 `subtasks` 容器下治理

写作时至少应明确以下关系：

- 当前子任务属于哪个 requirement 或 requirement 索引簇
- 当前子任务属于哪个 module
- 当前子任务在 `TASK_INDEX.md` 中对应哪一项
- 当前子任务在所属模块的 `MODULE_TASK_INDEX.md` 中对应哪一项
- 当前子任务依赖哪些父文档
- 当前子任务是否受某些 `OPEN_QUESTIONS.md` / `MODULE_OPEN_QUESTIONS.md` 约束

当前推荐同步引用的父级文档通常包括：

- 全局索引：
  - `PLAN_LATEST.md`
  - `MODULE_INDEX.md`
  - `TASK_INDEX.md`
- 模块文档：
  - `MODULE_REQUIREMENTS.md`
  - `MODULE_DESIGN.md`
  - `MODULE_API_DESIGN.md`
  - `MODULE_SCHEMA_DESIGN.md`
  - `MODULE_LOGIC_DESIGN.md`
  - `MODULE_TASK_INDEX.md`
  - `MODULE_DEPENDENCIES.md`
  - `MODULE_OPEN_QUESTIONS.md`

artifact governance 相关提醒：

- `SUBTASK_DESIGN.md` 和 `SUBTASK_IMPLEMENTATION.md` 是当前子任务的官方文档槽位。
- 讨论轮次、报告、history、临时 JSON 只能作为参考或证据，不能冒充官方设计文档或官方实施文档。
- 若实施文档仍为空模板、占位骨架或明显未开始，不应把它写成“已可实施”。

## 6. `SUBTASK_DESIGN.md` 模板

### 6.1 作用

这份文档用于回答：

- 这个子任务到底要解决什么问题
- 它在 requirement / module 链路里承担什么职责
- 它依赖哪些上游约束
- 它的输入输出、接口、数据和边界是什么
- 后续实施时应遵守哪些技术方案和验证要求

它不是执行步骤清单。  
它的目标是让实施前，先把“设计依据”说清楚。

### 6.2 放置位置

放在子任务目录下：

- `docs/modules/<module>/sub_modules/<subtask>/SUBTASK_DESIGN.md`

例如：

- `docs/modules/M02-identity-and-team/sub_modules/ST02_03-authorization-matrix/SUBTASK_DESIGN.md`

### 6.3 模板正文

```markdown
# 子任务设计文档

## 1. 文档定位

- 本文档用于定义当前子任务的设计依据、边界、输入输出、接口契约、数据约束、实现方向与验证目标。
- 本文档是子任务级设计文档，不代替实施文档。
- 本文档用于支撑后续 `SUBTASK_IMPLEMENTATION.md` 的编写与细化。
- 正文中的状态描述只代表作者说明，不直接等于 official state。

## 2. 基本信息与关联

- 子任务 ID：
- 子任务名称：
- 所属 requirement / requirement 索引簇：
- 所属模块：
- 对应全局任务索引项：`TASK_INDEX.md`
- 对应模块任务索引项：`MODULE_TASK_INDEX.md`
- 对应官方状态条目：`docs/governance/DOC_STATE.yaml -> subtasks.<子任务 ID>`
- 官方文档槽位：
  - `SUBTASK_DESIGN.md`
  - `SUBTASK_IMPLEMENTATION.md`
- 关联上游文档：
  - `MODULE_REQUIREMENTS.md`
  - `MODULE_DESIGN.md`
  - `MODULE_API_DESIGN.md`
  - `MODULE_SCHEMA_DESIGN.md`
  - `MODULE_LOGIC_DESIGN.md`
  - `MODULE_DEPENDENCIES.md`
  - `MODULE_OPEN_QUESTIONS.md`
- 作者写作态（可选，非 official state）：`骨架中 / 编写中 / 待评审 / 阻塞中`
- 当前治理状态摘录（可选，仅引用，不在本文自定真值）：
  - `maturity`：
  - `candidate_status`：
  - `review_status`：
  - `readiness`：
  - `blocker_refs`：

## 3. 子任务目标

- 本子任务要解决的问题：
- 本子任务在 requirement / module 链路中的作用：
- 本子任务完成后应带来的直接结果：
- 当前不应误解成已解决的问题：

## 4. 范围与边界

### 4.1 范围内
- 本子任务明确负责：
  -
  -
  -

### 4.2 范围外
- 本子任务不负责：
  -
  -
  -

## 5. 上游依赖与前置条件

### 5.1 文档依赖
- 依赖的 requirement / 全局索引：
- 依赖的模块需求：
- 依赖的模块设计：
- 依赖的 API 契约：
- 依赖的 schema：
- 依赖的 logic 设计：

### 5.2 任务依赖
- 前置子任务：
- 平行子任务：
- 后续子任务：

### 5.3 待确认问题 / 共享契约
- 关联的 `OPEN_QUESTIONS.md` / `MODULE_OPEN_QUESTIONS.md`：
- 当前仍未冻结的共享契约：
- 哪些问题会阻塞后续实施：

## 6. 需求细化

- 用户视角的目标：
- 模块视角的目标：
- 关键业务规则：
- 错误语义 / 失败语义：
- 合规、权限或安全要求：

## 7. 技术方案

### 7.1 核心方案
- 核心实现思路：
- 关键接口 / 关键对象：
- 关键状态或流程：

### 7.2 输入输出与约束
- 输入来源：
- 输出对象：
- 输入校验要求：
- 输出一致性要求：

### 7.3 接口 / 数据 / 状态约束
- 涉及接口：
- 涉及数据结构：
- 状态变化规则：
- 并发 / 一致性 / 幂等性要求：

## 8. 风险、边界与待确认问题

### 8.1 风险点
| 风险 ID | 风险描述 | 影响范围 | 当前缓解方案 |
| --- | --- | --- | --- |
| R-001 |  |  |  |

### 8.2 待确认问题
| 问题 ID | 问题描述 | 优先级 | 影响范围 | 当前建议 | 是否阻塞后续实施 |
| --- | --- | --- | --- | --- | --- |
| SQ-001 |  | P1 | 当前子任务 |  | 是 / 否 |

## 9. 对实施文档的派生输入

> 本节用于给 `SUBTASK_IMPLEMENTATION.md` 提供输入，不直接写成完整实施步骤。

- 允许修改的大致区域：
- 不允许突破的边界：
- 预计实施顺序：
- 必须先满足的前置条件：
- 实施后应重点验证的目标：
- 需要哪些测试与联调：

## 10. 当前判断与下一步

- 当前成熟度判断（人工说明）：
- 当前最主要缺口：
- 是否已可作为 `SUBTASK_IMPLEMENTATION.md` 的稳定下游输入：是 / 否
- 若否，当前最缺失的是：
```

## 7. `SUBTASK_IMPLEMENTATION.md` 模板

### 7.1 作用

这份文档用于回答：

- 本轮到底准备实施什么
- 允许改哪些范围，不允许碰哪些范围
- 具体实施顺序和验证方案是什么
- 当前还缺哪些前置条件
- 什么标准下才算本轮实施完成

它不是 requirement / module / task 的正式状态写回工具。  
它的目标是把“怎么改、怎么验、什么时候算完成”写清楚。

### 7.2 放置位置

放在子任务目录下：

- `docs/modules/<module>/sub_modules/<subtask>/SUBTASK_IMPLEMENTATION.md`

例如：

- `docs/modules/M02-identity-and-team/sub_modules/ST02_03-authorization-matrix/SUBTASK_IMPLEMENTATION.md`

### 7.3 模板正文

```markdown
# 子任务实施文档

## 1. 文档定位

- 本文档用于定义当前子任务的实施目标、允许修改范围、实施步骤、验证方式、完成判定与回写要求。
- 本文档是子任务级实施文档，不代替设计文档。
- 本文档必须以 `SUBTASK_DESIGN.md` 为上游输入，不在此处重写整套设计推导。
- 正文中的状态描述只代表作者说明，不直接等于 official state。

## 2. 基本信息与关联

- 子任务 ID：
- 子任务名称：
- 所属 requirement / requirement 索引簇：
- 所属模块：
- 对应全局任务索引项：`TASK_INDEX.md`
- 对应模块任务索引项：`MODULE_TASK_INDEX.md`
- 对应设计文档：`SUBTASK_DESIGN.md`
- 对应官方状态条目：`docs/governance/DOC_STATE.yaml -> subtasks.<子任务 ID>`
- 作者写作态（可选，非 official state）：`骨架中 / 编写中 / 待评审 / 阻塞中`
- 当前治理状态摘录（可选，仅引用，不在本文自定真值）：
  - `maturity`：
  - `candidate_status`：
  - `review_status`：
  - `readiness`：
  - `implementation_doc_state`：
  - `blocker_refs`：

## 3. 本轮实施目标

- 本轮准备完成什么：
- 本轮不准备完成什么：
- 本轮完成后应交付的直接结果：

## 4. 实施前提与阻塞

- 上游设计输入是否已稳定：
- 上游 requirement / module 阻塞：
- 当前关联的开放问题：
- 若当前仍不能正式进入实施，原因是什么：

## 5. 允许修改范围

### 5.1 允许修改
- 允许修改的目录：
- 允许修改的文件：
- 允许新增的内容：

### 5.2 禁止修改
- 本轮不应修改的目录 / 文件：
- 不应顺手扩展的相邻问题：
- 不应在本轮重新定义的共享契约：

## 6. 实施方案

### 6.1 计划改动
- 改动点 1：
- 改动点 2：
- 改动点 3：

### 6.2 实施步骤
1. 
2. 
3. 

### 6.3 关键技术约束
- 接口 / 字段约束：
- 数据 / 状态约束：
- 兼容性要求：
- 幂等性 / 一致性要求：

## 7. 测试与验证

### 7.1 自动化验证
- 计划运行的测试：
- 需要补的测试：
- 不准备在本轮覆盖的测试：

### 7.2 手动验证
- 入口：
- 操作路径：
- 预期结果：
- 重点观察项：

### 7.3 回归风险检查
- 对上游模块的影响：
- 对兄弟子任务的影响：
- 对共享契约的影响：

## 8. 完成判定

- 满足哪些条件可视为本轮完成：
- 满足哪些条件才可进入下一轮评审：
- 哪些内容完成后仍不等于 official state 的 `implementation_ready`：

## 9. 风险与回滚

| 风险 ID | 风险描述 | 影响范围 | 回滚或缓解方案 |
| --- | --- | --- | --- |
| IR-001 |  |  |  |

## 10. 待确认问题

| 问题 ID | 问题描述 | 优先级 | 影响范围 | 当前建议 | 是否阻塞本轮实施 |
| --- | --- | --- | --- | --- | --- |
| IQ-001 |  | P1 | 当前子任务 |  | 是 / 否 |

## 11. 实施后回写项

- 需要回写的设计结论：
- 需要回写的模块文档：
- 需要回写的索引文档：
- 需要补充的测试结果：
- 若本轮未完成，下一轮最小继续条件：
```

## 8. 模板使用提醒

- 模板的作用是帮助写作者把信息写全，不是让正文模拟 `DOC_STATE.yaml`。
- 若需要引用当前正式状态，可在正文中写“当前治理状态摘录（仅引用）”，但不要在正文中自我确认 `candidate_status`、`readiness`、`implementation_doc_state` 已变更。
- 若 `SUBTASK_IMPLEMENTATION.md` 仍为空模板、占位骨架或未形成明确实施方案，不应把它描述成已经进入 `active_working_doc`。
- 若需要判断是否真的可推进、可确认、可开窗，应回到批次 1 和批次 2 已对齐的治理文档与代码真值。

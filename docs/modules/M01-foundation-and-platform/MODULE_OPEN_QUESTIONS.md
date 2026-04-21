# 模块待确认问题

## 1. 文档定位

- 本文档用于记录当前模块内部仍未收敛、会影响模块设计或子任务推进的问题。
- 本文档是模块级问题清单，不代替根目录 `OPEN_QUESTIONS.md` 的全局问题总表。
- 当前模块主责 Codex 在推进模块文档时，若发现新的模块级问题，应优先记录在这里。
- 若问题已明显影响多个模块、多个子任务或共享契约，应进一步上升到根目录 `OPEN_QUESTIONS.md`。

## 2. 状态定义

- `open`：问题已识别，但尚无明确默认方案
- `proposed-default`：已有默认建议，可在未正式确认前先按该口径继续推进
- `confirmed`：问题已确认，后续文档应按确认结果回写
- `superseded`：问题已失效或已被其他新口径替代

## 3. 已继承的全局冻结口径

| 问题 ID | 状态 | 当前在 M01 中采用的口径 | 影响文档 | 是否阻塞本轮 L4 | 对子任务设计的影响 |
| --- | --- | --- | --- | --- | --- |
| OQ-001 | proposed-default | 按 monorepo：`apps/web` + `apps/api` + `infra` 推进 | `MODULE_REQUIREMENTS.md`、`MODULE_DESIGN.md`、`MODULE_DEPENDENCIES.md`、`MODULE_TASK_INDEX.md` | 否 | 当前不是主阻塞项 |
| OQ-002 | proposed-default | 首轮只建立最小运行时、测试和 CI 基线 | `MODULE_REQUIREMENTS.md`、`MODULE_DESIGN.md`、`MODULE_LOGIC_DESIGN.md`、`MODULE_DEPENDENCIES.md`、`MODULE_TASK_INDEX.md` | 否 | 会影响子任务设计粒度，但不是唯一阻塞项 |
| OQ-003 | proposed-default | 首轮只沉淀壳层、头部、列表原语与基础页面样式 | `MODULE_REQUIREMENTS.md`、`MODULE_DESIGN.md`、`MODULE_API_DESIGN.md`、`MODULE_SCHEMA_DESIGN.md` | 否 | 会限制 ST01_02 的设计范围 |

## 4. 模块问题表

| MQ ID | 问题 | 状态 | 影响范围 | 当前建议 | 是否需上升到全局 | 需回写文档 |
| --- | --- | --- | --- | --- | --- | --- |
| MQ-001 | 根目录统一脚本与最小 CI 校验矩阵应细化到什么粒度，才算满足 M01 的下游输入要求 | open | `MODULE_REQUIREMENTS.md`、`MODULE_DEPENDENCIES.md`、ST01_01、ST01_03 | 本轮先只冻结“需要最小运行时 / 测试 / CI 基线”，不擅自补命令级契约 | 否 | `MODULE_REQUIREMENTS.md`、`MODULE_DEPENDENCIES.md`、`MODULE_TASK_INDEX.md` |
| MQ-002 | `PageHeader` 与 Dashboard 摘要区的最小 props / slot 边界如何冻结 | proposed-default | `MODULE_DESIGN.md`、`MODULE_API_DESIGN.md`、`MODULE_SCHEMA_DESIGN.md`、ST01_02 | 采用方案 B：`PageHeader` 只冻结标题/说明/主次动作，摘要区独立承载 `status_badge` / `updated_at` / `summary_items` 与最小状态表达，不冻结代码级 props 形态 | 否 | `MODULE_DESIGN.md`、`MODULE_API_DESIGN.md`、`MODULE_SCHEMA_DESIGN.md`、`MODULE_TASK_INDEX.md` |
| MQ-003 | 列表查询状态、分页交互与 URL / callback 的映射规则应如何统一 | proposed-default | `MODULE_API_DESIGN.md`、`MODULE_SCHEMA_DESIGN.md`、`MODULE_LOGIC_DESIGN.md`、ST01_02 | 已与全局 `OQ-021` 对齐：冻结共享 `ListQueryState`、最小 query 映射、分页响应骨架与页面容器 adapter 职责；不冻结完整 props / callback catalog 与高级筛选序列化细节 | 否 | `MODULE_API_DESIGN.md`、`MODULE_SCHEMA_DESIGN.md`、`MODULE_LOGIC_DESIGN.md`、`MODULE_TASK_INDEX.md` |
| MQ-004 | locale fallback、切换策略与消息命名空间需要冻结到什么程度，才能支撑下游子任务设计 | proposed-default | `MODULE_REQUIREMENTS.md`、`MODULE_API_DESIGN.md`、`MODULE_LOGIC_DESIGN.md`、ST01_02 | 已按全局 `OQ-022` 形成最小共享默认口径：冻结集中取词入口、locale seed、统一 fallback 与最小 namespace 边界，但不冻结完整 locale 策略 | 否 | `MODULE_REQUIREMENTS.md`、`MODULE_API_DESIGN.md`、`MODULE_LOGIC_DESIGN.md`、`MODULE_TASK_INDEX.md` |

## 5. 当前高优问题

| 优先级 | MQ ID | 当前阻塞文档 | 原因 | 本轮处理要求 |
| --- | --- | --- | --- | --- |
| P0 | MQ-001 | `MODULE_DEPENDENCIES.md`、`MODULE_TASK_INDEX.md` | 若没有最小脚本 / CI 矩阵，ST01_01 与 ST01_03 仍无法形成下游输入 | 明确这是进入 `L5` 前的剩余阻塞，而不是本轮 L4 的阻塞 |
| P0 | MQ-002 | `MODULE_DESIGN.md`、`MODULE_API_DESIGN.md`、`MODULE_SCHEMA_DESIGN.md` | 若没有最小共享页面原语口径，ST01_02 与后续业务页面会继续各写一套头部/摘要区模型 | 本轮按方案 B 冻结最小对象模型与职责边界，不补代码级 props |
| P0 | MQ-003 | `MODULE_API_DESIGN.md`、`MODULE_LOGIC_DESIGN.md` | 列表查询状态若不形成默认口径，会导致后续页面各写一套列表交互 | 本轮已形成 `proposed-default`，下一轮重点转为模块吸收与实现级接口细化 |
| P1 | MQ-004 | `MODULE_API_DESIGN.md` | locale 规则不清会影响 i18n 下游拆解 | 本轮已形成最小共享默认口径，按该口径回写，不扩张到完整 locale 策略 |

## 6. 需要升级到全局的问题

> 只有当问题影响多个模块、共享契约或全局技术口径时，才列在这里，等待总控 Codex 同步到根目录 `OPEN_QUESTIONS.md`。

- `MQ-003` 已映射到全局 `OQ-021`，并按 `proposed-default` 口径继续回写。

## 7. 对子任务设计的影响

- `OQ-001~003` 已足够支撑 M01 在本轮达到可评审，但不足以自动让模块进入子任务设计。
- 当前真正阻塞子任务设计的，主要是 `MQ-001~003` 仍停留在方向级；`MQ-004` 虽已形成 `proposed-default` 最小共享口径，但模块整体尚未达到 `L5` 可下游引用标准。

## 8. 使用说明

- 模块 Codex 每轮推进模块文档时，都应检查是否新增了模块级问题。
- 若问题只影响当前模块，优先记录在本文件。
- 若问题已影响多个模块、共享契约或全局技术口径，应在本文件记录后，同时上报总控 Codex，并推动更新根目录 `OPEN_QUESTIONS.md`。
- 当问题状态从 `open` 变为 `proposed-default` 或 `confirmed` 时，应同步回写受影响模块文档。

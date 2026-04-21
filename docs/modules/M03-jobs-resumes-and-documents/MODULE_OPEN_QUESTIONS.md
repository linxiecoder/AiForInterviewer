# 模块待确认问题

## 1. 文档定位

- 本文档用于记录当前模块内部仍未收敛、会影响模块设计或子任务推进的问题。
- 本文档是模块级问题清单，不代替根目录 `OPEN_QUESTIONS.md` 的全局问题总表。
- 当前模块主责 Codex 在推进模块文档时，若发现新的模块级问题，应优先记录在这里。
- 若问题已明显影响多个模块、多个子任务或共享契约，应进一步上升到根目录 `OPEN_QUESTIONS.md`。
- 已冻结的全局输入：
  - `OQ-006`：Markdown 预览与导出共用同一渲染链。
  - `OQ-007`：上传同步入库，转换与导出异步。

## 2. 状态定义

- `open`：问题已识别，但尚无明确默认方案。
- `proposed-default`：已有默认建议，可在未正式确认前先按该口径继续推进。
- `confirmed`：问题已确认，后续文档应按确认结果回写。
- `superseded`：问题已失效或已被其他新口径替代。

## 3. 问题表

| MQ ID | 问题 | 状态 | 影响范围 | 当前建议 | 是否需上升到全局 | 需回写文档 |
| --- | --- | --- | --- | --- | --- | --- |
| MQ-301 | 简历保存新版本时是否必须提交 `base_version_no` 以做乐观锁校验 | confirmed | `MODULE_API_DESIGN.md`、`MODULE_SCHEMA_DESIGN.md`、`MODULE_LOGIC_DESIGN.md`、`ST03_02` | 已确认：本轮只冻结“保存会新增不可变版本快照”，`base_version_no` 不设为模块级必填；若后续需要冲突校验，由 `ST03_02` 细化 | 否 | `MODULE_API_DESIGN.md`、`MODULE_SCHEMA_DESIGN.md`、`MODULE_LOGIC_DESIGN.md` |
| MQ-302 | `jobs.status` 与 `resumes.status` 是否要在本轮冻结到精确枚举级 | confirmed | `MODULE_REQUIREMENTS.md`、`MODULE_SCHEMA_DESIGN.md`、`MODULE_TASK_INDEX.md`、`ST03_01`、`ST03_02` | 已确认：本轮只冻结“必须存在可筛选状态字段与生命周期语义”，不在模块级冻结最终枚举表；精确枚举留待子任务评审 | 否 | `MODULE_REQUIREMENTS.md`、`MODULE_SCHEMA_DESIGN.md`、`MODULE_TASK_INDEX.md` |
| MQ-303 | 原始 PDF / 导出 PDF 的业务下载入口与共享 `storage_objects` 下载入口如何映射 | confirmed | `MODULE_API_DESIGN.md`、`MODULE_DEPENDENCIES.md`、`ST03_03` | 已确认：保留业务入口定位资源，真实文件下载统一复用共享文件下载能力 | 否 | `MODULE_API_DESIGN.md`、`MODULE_DEPENDENCIES.md` |
| MQ-304 | 在 `OQ-021` 默认冻结后，M03 如何与全局列表共享契约对齐 | proposed-default | `MODULE_API_DESIGN.md`、`MODULE_DEPENDENCIES.md`、`ST03_01`、`ST03_02` | 已与全局 `OQ-021` 对齐：冻结服务端查询键 `page` / `page_size` / `q` / `status` / `sort` / `order` / `updated_after` / `updated_before`、统一分页骨架与最小 URL / request 映射；实现级 callback 与复杂筛选双向映射继续留待子任务细化 | 否 | `MODULE_API_DESIGN.md`、`MODULE_DEPENDENCIES.md`、`MODULE_TASK_INDEX.md` |
| MQ-305 | 在 `OQ-020` 已形成默认冻结候选后，M03 页面如何承接共享页面头部 / 摘要区的最小接口边界 | proposed-default | `MODULE_DESIGN.md`、`MODULE_TASK_INDEX.md`、`ST03_01`、`ST03_02` | 跟随全局方案 B：`PageHeader` 承载 `title` / `subtitle` / `primary_actions` / `secondary_actions`，摘要区独立承载 `status_badge` / `updated_at` / `summary_items` 与最小状态表达；完整 shared props catalog 继续后置 | 否 | `MODULE_DESIGN.md`、`MODULE_TASK_INDEX.md` |
| MQ-306 | 现有 `ST03_01`、`ST03_02`、`ST03_03` 是否还能继续作为直接子任务设计入口 | proposed-default | `MODULE_TASK_INDEX.md`、`MODULE_DESIGN.md`、`MODULE_DEPENDENCIES.md`、现有 `ST03_*` 子任务双文档 | 本轮默认不再作为直接入口，而是先回退为旧切分容器；待总控决定是否在全局任务索引与目录层面正式重编号或重映射 | 是 | `MODULE_TASK_INDEX.md`、`MODULE_DESIGN.md`、`MODULE_DEPENDENCIES.md`、`MODULE_EXECUTION_LOG.md` |
| MQ-307 | `jobs.requirement_items_json` 既作为 M04 / M06 输入，又未冻结最小 item 结构，是否必须先上提到模块层收口 | open | `MODULE_REQUIREMENTS.md`、`MODULE_DESIGN.md`、`MODULE_SCHEMA_DESIGN.md`、`MODULE_DEPENDENCIES.md`、`ST03_01`、M04、M06 | 建议先在模块层冻结“最小可消费结构、空值语义、排序规则、写入责任”，再允许岗位相关微任务与下游模块继续下钻 | 是 | `MODULE_REQUIREMENTS.md`、`MODULE_DESIGN.md`、`MODULE_SCHEMA_DESIGN.md`、`MODULE_DEPENDENCIES.md` |

## 4. 当前高优问题

| 优先级 | MQ ID | 当前阻塞文档 | 原因 | 本轮处理要求 |
| --- | --- | --- | --- | --- |
| P0 | MQ-306 | `MODULE_TASK_INDEX.md`、`MODULE_DESIGN.md`、`MODULE_DEPENDENCIES.md`、现有 `ST03_*` 子任务双文档 | 若不先把旧入口回退为容器，M03 仍会被误判为“已可进入子任务设计” | 本轮先在模块层清理入口、重切微任务，并上报总控处理全局索引同步 |
| P0 | MQ-307 | `MODULE_REQUIREMENTS.md`、`MODULE_SCHEMA_DESIGN.md`、`MODULE_DEPENDENCIES.md`、M04 / M06 下游输入判断 | 若继续把 `jobs.requirement_items_json` 宣称为稳定输入，下游会各自发明 item schema，模块边界会继续漂移 | 本轮先把它降级为“字段级候选输入”，并要求后续优先上提到模块层收口 |
| P0 | MQ-301 | `ST03_02` 下游设计 | 若子任务阶段重新发明冲突策略，编辑器保存接口仍可能漂移 | 已确认当前轮口径；下一步只在 `ST03_02` 细化冲突契约 |
| P1 | MQ-302 | `MODULE_SCHEMA_DESIGN.md`、`ST03_01`、`ST03_02` | 若子任务阶段各自定义状态枚举，列表筛选和日志仍会对不齐 | 已确认当前轮口径；下一步由 `ST03_01` / `ST03_02` 细化枚举 |
| P1 | MQ-303 | `MODULE_API_DESIGN.md`、`ST03_03` | 若实施时绕开共享下载能力，仍会产生重复权限逻辑 | 已确认当前轮口径；下一步由 `ST03_03` 按共享下载能力落实现 |
| P1 | MQ-304 | `ST03_01`、`ST03_02` | 若不按全局默认口径吸收列表查询键与分页骨架，子任务设计仍会继续漂移 | 已按模块级最小查询键集合推进，并要求子任务文档显式引用 `OQ-021` |
| P1 | MQ-305 | `ST03_01`、`ST03_02` | 若不按全局默认冻结口径承接页面头部/摘要区，岗位页与简历页仍会各自发明共享 UI 口径 | 建议直接按最小字段集合推进，并在子任务文档中显式引用 `OQ-020` |

## 5. 需要升级到全局的问题

> 只有当问题影响多个模块、共享契约或全局技术口径时，才列在这里，等待总控 Codex 同步到根目录 `OPEN_QUESTIONS.md`。

- `MQ-304`、`MQ-305` 分别依赖已存在的 `OQ-021`、`OQ-020`；其中 `MQ-304` 已按全局 `proposed-default` 吸收，本轮不重复升级。
- `MQ-306` 建议升级到全局：
  - 原因：它会影响根目录 `TASK_INDEX.md`、`MODULE_INDEX.md` 对 M03 阶段判断的口径。
  - 建议动作：由总控决定是否把现有 `ST03_*` 保留为容器，并在全局索引中同步“暂不直开”。
- `MQ-307` 建议升级到全局：
  - 原因：它影响 M04 / M06 对 `jobs.requirement_items_json` 的可依赖性判断，已经超出 M03 内部单模块边界。
  - 建议动作：由总控评估是否升级为新的全局 `OQ`，或在总控轮中直接冻结最小 item schema。

## 6. 使用说明

- 模块 Codex 每轮推进模块文档时，都应检查是否新增了模块级问题。
- 若问题只影响当前模块，优先记录在本文件。
- 若问题已影响多个模块、共享契约或全局技术口径，应在本文件记录后，同时上报总控 Codex，并推动更新根目录 `OPEN_QUESTIONS.md`。
- 当问题状态从 `open` 变为 `proposed-default` 或 `confirmed` 时，应同步回写受影响模块文档。

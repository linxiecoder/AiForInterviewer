---
title: MODULE_OPEN_QUESTIONS
type: note
permalink: ai-for-interviewer/docs/modules/m01-foundation-and-platform/module-open-questions
---

# 模块待确认问题

> 当前输入对齐：本文只保留 M01 模块内 MQ/OQ 治理记录。凡涉及一期 MVP 范围、IA / 用户旅程、对象模型 / RAG / 多轮 / 后端边界、评分 / 复盘 / 导出 / DoD 的当前事实，统一引用 `docs/design/workbench-mvp/scope.md`、`docs/design/workbench-mvp/information-architecture.md`、`docs/design/workbench-mvp/object-model-rag-multiround-backend.md`、`docs/design/workbench-mvp/scoring-review-export-dod.md`。旧 MQ/OQ 中若出现 W10 `apps/web` 原型、首切片 MVP、RAG / 知识库后续、多轮固定三轮或直接发起模拟面试等产品范围判断，一律按 historical / superseded 理解，不作为当前输入。

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
| OQ-020 | proposed-default | 共享页面原语只冻结 `PageHeader` / 摘要区的最小语义对象模型与职责边界 | `MODULE_DESIGN.md`、`MODULE_API_DESIGN.md`、`MODULE_SCHEMA_DESIGN.md`、`MODULE_TASK_INDEX.md` | 否 | 约束 `ST01_02`、`MT02_06`、`MT03_02`、`MT03_05` 的页面承接方式 |
| OQ-021 | proposed-default | 列表查询默认采用 `ListQueryState` + 页面容器 / request adapter 口径 | `MODULE_API_DESIGN.md`、`MODULE_LOGIC_DESIGN.md`、`MODULE_DEPENDENCIES.md`、`MODULE_TASK_INDEX.md` | 否 | 约束 `ST01_02`、`MT02_06`、`MT03_02` 的列表承接方式 |
| OQ-022 | proposed-default | i18n 只冻结集中取词入口、locale seed、fallback 与最小 namespace 边界 | `MODULE_REQUIREMENTS.md`、`MODULE_DESIGN.md`、`MODULE_LOGIC_DESIGN.md`、`MODULE_TASK_INDEX.md` | 否 | 约束 `ST01_02`、`MT02_05`、`MT02_06` 的文案消费方式 |

## 4. 模块问题表

| MQ ID | 问题 | 状态 | 影响范围 | 当前建议 | 是否需上升到全局 | 需回写文档 |
| --- | --- | --- | --- | --- | --- | --- |
| MQ-001 | 根目录统一脚本与最小 CI 校验矩阵应细化到什么粒度，才算满足 M01 的下游输入要求 | proposed-default | `MODULE_REQUIREMENTS.md`、`MODULE_SCHEMA_DESIGN.md`、`MODULE_LOGIC_DESIGN.md`、`MODULE_DEPENDENCIES.md`、ST01_01、ST01_03 | 已与全局 `OQ-019` 对齐：冻结统一脚本命名（`dev:web` / `dev:api` / `test:web` / `test:api`）、最小存活检查（`GET /api/v1/health` -> `200 {"status":"ok"}`）、最小验证入口类型（API=`pytest`、Web=`vitest`）与 API / Web 双 lane；完整 workflow、lint / format gate、E2E 与多平台矩阵留给 M10 / 后续治理，不再作为 M01 共享前置；该压缩结果只说明共享最小层已写清，不代表 M01 整体已具备接受条件 | 否 | `MODULE_REQUIREMENTS.md`、`MODULE_SCHEMA_DESIGN.md`、`MODULE_LOGIC_DESIGN.md`、`MODULE_DEPENDENCIES.md`、`MODULE_TASK_INDEX.md` |
| MQ-002 | `PageHeader` 与 Dashboard 摘要区的最小 props / slot 边界如何冻结 | proposed-default | `MODULE_DESIGN.md`、`MODULE_API_DESIGN.md`、`MODULE_SCHEMA_DESIGN.md`、ST01_02 | 采用方案 B：`PageHeader` 只冻结标题/说明/主次动作，摘要区独立承载 `status_badge` / `updated_at` / `summary_items` 与最小状态表达，不冻结代码级 props 形态 | 否 | `MODULE_DESIGN.md`、`MODULE_API_DESIGN.md`、`MODULE_SCHEMA_DESIGN.md`、`MODULE_TASK_INDEX.md` |
| MQ-003 | 列表查询状态、分页交互与 URL / callback 的映射规则应如何统一 | proposed-default | `MODULE_API_DESIGN.md`、`MODULE_SCHEMA_DESIGN.md`、`MODULE_LOGIC_DESIGN.md`、ST01_02 | 已与全局 `OQ-021` 对齐，并按三层状态分层：共享最小层固定 `page / page_size / q / status / sort / order` 与统一分页骨架；模块扩展层允许单独登记 `updated_after` / `updated_before` 等扩展键；route / callback / request adapter 细节留在实现细节层，不再回灌为 M01 共享前置；该压缩结果只说明共享最小层已写清，不代表 M01 整体已具备接受条件 | 否 | `MODULE_API_DESIGN.md`、`MODULE_SCHEMA_DESIGN.md`、`MODULE_LOGIC_DESIGN.md`、`MODULE_TASK_INDEX.md` |
| MQ-004 | locale fallback、切换策略与消息命名空间需要冻结到什么程度，才能支撑下游子任务设计 | proposed-default | `MODULE_REQUIREMENTS.md`、`MODULE_API_DESIGN.md`、`MODULE_LOGIC_DESIGN.md`、ST01_02 | 已按全局 `OQ-022` 形成最小共享默认口径：冻结集中取词入口、locale seed、统一 fallback 与最小 namespace 边界，但不冻结完整 locale 策略 | 否 | `MODULE_REQUIREMENTS.md`、`MODULE_API_DESIGN.md`、`MODULE_LOGIC_DESIGN.md`、`MODULE_TASK_INDEX.md` |
| MQ-005 | `shared adapter` 应冻结到什么程度，才能让页面容器、共享页面原语、i18n 消费与服务层按同一默认口径协作 | proposed-default | `MODULE_DESIGN.md`、`MODULE_API_DESIGN.md`、`MODULE_DEPENDENCIES.md`、`MODULE_TASK_INDEX.md`、ST01_02、ST01_03、`MT02_05`、`MT02_06`、`MT03_02`、`MT03_05` | 已吸收 `OQ-020~022`：共享最小层固定页面容器持有 route / locale / page state、request adapter 负责最小 query 映射、shared primitive 只消费稳定输入、服务层只返回领域数据 / 分页骨架 / 错误语义；模块投影层允许业务模块登记摘要字段和扩展 view model；精确 props / callback / resolved copy 载体留在实现细节层，不再作为 M01 共享前置；该压缩结果只说明共享最小层已写清，不代表 M01 整体已具备接受条件 | 否 | `MODULE_DESIGN.md`、`MODULE_API_DESIGN.md`、`MODULE_DEPENDENCIES.md`、`MODULE_TASK_INDEX.md` |
| MQ-006 | 共享下载网关与 `storage_objects` 最小边界应冻结到什么程度，才能让 M03 / M05 继续推进而不把平台契约写进业务模块 | confirmed | `MODULE_API_DESIGN.md`、`MODULE_SCHEMA_DESIGN.md`、`MODULE_LOGIC_DESIGN.md`、`MODULE_DEPENDENCIES.md`、M03、M05 | 已确认：冻结共享 `storage_objects` 最低字段面、bucket / key 规则、`source_type` / `source_id` owner pointer、对象写入顺序，以及 `GET /api/v1/storage-objects/{object_id}/download` 作为唯一实际下载入口；业务入口只做资源定位，不再复制下载逻辑 | 否 | `MODULE_API_DESIGN.md`、`MODULE_SCHEMA_DESIGN.md`、`MODULE_LOGIC_DESIGN.md`、`MODULE_DEPENDENCIES.md`、`MODULE_EXECUTION_LOG.md` |
| MQ-007 | 当 SC-05 已达到下游模块输入门槛后，是否需要由总控统一回写跨模块 / 全局文档，解除旧的“共享下载 / 对象存储成熟度不足”表述 | proposed-default | `MODULE_DEPENDENCIES.md`、`MODULE_EXECUTION_LOG.md`、M03、M05、全局进展 / 问题文档 | 本模块默认判断：M01 状态层已确认为 `maturity=L5`、`readiness=downstream_ready`、`review_status=pending_confirmation`，且 SC-05 共享下载 / `storage_objects` 主题已可作为 M03 / M05 的局部模块设计参考输入；应由总控统一回写跨模块依赖与进展表述，避免继续把该主题记为主阻塞；该判断不外推为实现授权 | 是 | `MODULE_DEPENDENCIES.md`、`MODULE_EXECUTION_LOG.md`、`OPEN_QUESTIONS.md`、`DOCUMENT_PROGRESS.md`、M03 / M05 相关模块文档 |

## 5. 当前高优问题

按 `MR-13` 统一口径，本轮“当前高优问题”只用于锁定 `MQ-001`、`MQ-003`、`MQ-005` 这三项整体接受前主阻塞；`MQ-006`、`MQ-007` 仅保留历史记录，不外推为本轮新增主题。

| 优先级 | MQ ID | 当前阻塞文档 | 原因 | 本轮处理要求 |
| --- | --- | --- | --- | --- |
| P0 | MQ-001 | `MODULE_REQUIREMENTS.md`、`MODULE_SCHEMA_DESIGN.md`、`MODULE_LOGIC_DESIGN.md`、`MODULE_DEPENDENCIES.md`、`MODULE_TASK_INDEX.md` | 若没有最小脚本命名、health check 与 API / Web 双 lane，ST01_01 与 ST01_03 仍无法共享同一验证基线 | 本轮已吸收 `OQ-019` 的默认口径；后续不在 M01 继续扩张完整 workflow、lint / format gate、E2E 与多平台矩阵 |
| P0 | MQ-002 | `MODULE_DESIGN.md`、`MODULE_API_DESIGN.md`、`MODULE_SCHEMA_DESIGN.md` | 若没有最小共享页面原语口径，ST01_02 与后续业务页面会继续各写一套头部/摘要区模型 | 本轮按方案 B 冻结最小对象模型与职责边界，不补代码级 props |
| P0 | MQ-003 | `MODULE_API_DESIGN.md`、`MODULE_SCHEMA_DESIGN.md`、`MODULE_LOGIC_DESIGN.md` | 列表查询状态若不形成共享最小层，会导致后续页面各写一套列表交互 | 本轮已按“共享最小层 / 模块扩展层 / 实现细节层”压缩；后续只在下游模块或子任务补实现级接口细化 |
| P0 | MQ-005 | `MODULE_DESIGN.md`、`MODULE_API_DESIGN.md`、`MODULE_DEPENDENCIES.md`、`MODULE_TASK_INDEX.md` | 若不写清 shared adapter 的共享最小层，M02/M03 页面 adapter 与旧入口会继续把页面容器、共享原语和服务调用混写 | 本轮已按三层边界压缩；后续不在 M01 扩张精确 props / callback / resolved copy 载体 |
| P0 | MQ-006 | `MODULE_API_DESIGN.md`、`MODULE_SCHEMA_DESIGN.md`、`MODULE_LOGIC_DESIGN.md`、`MODULE_DEPENDENCIES.md` | 若共享下载与对象存储边界不冻结，M03 的上传 / 导出与 M05 的对象引用设计会继续把平台契约写进业务模块 | 本轮已按 SC-05 完成确认；后续只保留实现级细节风险，不再把该主题视为模块级主阻塞 |
| P1 | MQ-004 | `MODULE_API_DESIGN.md` | locale 规则不清会影响 i18n 下游拆解 | 本轮已形成最小共享默认口径，按该口径回写，不扩张到完整 locale 策略 |
| P1 | MQ-007 | `MODULE_DEPENDENCIES.md`、`MODULE_EXECUTION_LOG.md`、跨模块依赖文档 | 若总控不统一回写，M03 / M05 与全局进展文档仍会继续把已收口的 SC-05 主题记成旧阻塞 | 由总控统一回写跨模块依赖与进展，不在 M01 窗口直接修改其他模块或全局主文档 |

### 5.1 本轮最低位压缩复核（仅 MQ-001 / MQ-003 / MQ-005）

- `MQ-001` 已压缩：M01 内只保留最小脚本命名、`GET /api/v1/health`、API=`pytest` / Web=`vitest` 与 API / Web 双 lane 作为共享最小层；完整 workflow、lint / format gate、E2E 与多平台矩阵继续后置，但这属于实现级治理后置，不影响 M01 当前 `L5 / downstream_ready` 状态口径。
- `MQ-003` 已压缩：M01 内只冻结 `ListQueryState` 的共享最小映射与统一分页骨架；扩展筛选键和 callback / request adapter 细节继续留在业务模块或子任务设计，但这仍不足以推导出整体已被接受。
- `MQ-005` 已压缩：M01 内只冻结页面容器、request adapter、shared primitive、i18n 消费与服务层的共享最小职责边界；精确 props / callback / hook 组织与 resolved copy 载体继续后置，但这仍不足以形成子任务设计前置条件。
- 复核结论：上述三项已从“方向级缺口”压缩为“共享最小层已明确”；当前正式状态层已确认 M01 为 `maturity=L5`、`readiness=downstream_ready`、`review_status=pending_confirmation`，但 `implementation_ready=false`。
- 当前仍差的最小条件包括：继续维持 M01 不授权实现的保守判断；不得据此创建或修改 `apps/**`、`infra/**`、`.github/**`、`tests/**`、`tools/**` 或运行时代码。若后续扩大到全局索引同步，再单独处理 `DOCUMENT_MATURITY.md`、`DOCUMENT_PROGRESS.md`、`TASK_INDEX.md`、`MODULE_INDEX.md`。

## 6. 需要升级到全局的问题

> 只有当问题影响多个模块、共享契约或全局技术口径时，才列在这里，等待总控 Codex 同步到根目录 `OPEN_QUESTIONS.md`。

- `MQ-003` 已映射到全局 `OQ-021`，并按 `proposed-default` 口径继续回写。
- `MQ-001` 已映射到全局 `OQ-019`，并按最小脚本命名、health check 与 API / Web 双 lane 口径继续回写。
- `MQ-005` 依赖并吸收 `OQ-020~022` 的默认口径，本轮不新增全局问题，只在 M01 记录 shared adapter 的模块层承接方式。
- `MQ-006` 本轮在模块层已完成 `confirmed` 收口，不新增全局升级项；若后续需要改写 bucket 体系、owner/source pointer 或共享下载唯一入口，再考虑升级为全局问题。
- `MQ-007` 影响 M03 / M05 与全局进展判断，应由总控统一回写 `OPEN_QUESTIONS.md`、`DOCUMENT_PROGRESS.md` 及相关模块依赖文档，避免跨窗口继续引用旧阻塞表述。

## 7. 对子任务设计的影响

- `OQ-001~003` 已足够支撑 M01 当前 `L5 / downstream_ready` 状态口径，但不足以自动让模块进入实现窗口。
- 本轮已把 `MQ-001`、`MQ-003` 与 `MQ-005` 压缩到共享最小层口径；当前 M01 可支撑下游设计与 ST01_01 formal window preparation，但仍不授权基础设施实现。
- 对跨模块依赖而言，`MQ-006` 的历史收口可继续被 M03 / M05 引用，但这不改变 M01 `implementation_ready=false` 的判断。
- `MQ-007` 不构成 M01 子任务设计的新增技术阻塞，但会影响总控对 M03 / M05 与全局文档状态的统一判断。

## 8. 使用说明

- 模块 Codex 每轮推进模块文档时，都应检查是否新增了模块级问题。
- 若问题只影响当前模块，优先记录在本文件。
- 若问题已影响多个模块、共享契约或全局技术口径，应在本文件记录后，同时上报总控 Codex，并推动更新根目录 `OPEN_QUESTIONS.md`。
- 当问题状态从 `open` 变为 `proposed-default` 或 `confirmed` 时，应同步回写受影响模块文档。
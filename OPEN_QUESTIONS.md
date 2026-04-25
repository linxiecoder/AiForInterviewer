# AI 模拟面试 P1 待确认问题

## 1. 文档定位

- 本文档汇总当前项目的全局待确认问题。
- 本文档用于帮助总控 Codex、模块 Codex 和评审 Codex 判断：
  - 当前哪些问题会直接阻塞模块成熟度提升
  - 当前哪些问题只需要默认方案即可继续推进
  - 当前哪些问题已应被关闭或降级
- 状态使用：
  - `open`
  - `proposed-default`
  - `confirmed`
  - `superseded`

## 2. 问题表

| OQ ID | 问题 | 状态 | 关联模块 | 当前建议 | 需回写文档 |
| --- | --- | --- | --- | --- | --- |
| OQ-001 | 目标产品代码结构是否固定为 monorepo（`apps/web` + `apps/api` + `infra`），并与当前文档治理仓分层共存 | open | M01-M10 | `W13-A` 已确认一期 MVP 必须重新定义为工作台级，且真实 LLM、登录 / 权限、服务端保存、服务端历史 / 复盘记录和评分系统进入一期范围；但具体代码结构、是否创建 `apps/api/**` / `infra/**`、API 框架、数据库与部署边界仍未确认。本轮暂停代码开发，不得继续扩展 `apps/web/**` 或创建后端目录 | `DESIGN_DECISIONS.md`、`PLAN_LATEST.md`、`docs/superpowers/plans/2026-04-25-workbench-mvp-scope.md` |
| OQ-002 | 首轮是否只建立最小运行时、测试和 CI 基线 | proposed-default | M01、M10 | 最小运行时、测试和 CI 基线只在 `W10-D` 被条件放行时作为最小骨架输入使用，不构成 `W10-A` 直接创建业务代码目录的依据 | `PLAN_LATEST.md`、`TECHNICAL_STANDARDS.md` |
| OQ-003 | 视觉规范首轮需要沉淀到什么粒度 | proposed-default | M01 | 本轮只沉淀壳层、头部、列表原语与基础页面样式 | `TECHNICAL_STANDARDS.md` |
| OQ-004 | P1 鉴权机制采用固定 Bearer token、JWT 还是 session cookie | open | M02、M10 | `W13-A` 已确认一期 MVP 必须包含完整登录 / 权限，但登录方案尚未确认；固定 Bearer token、JWT、session cookie 或托管身份服务仍需在 `W13-C` 中形成确认卡，不能在本轮写成 confirmed 实现方案 | `DESIGN_DECISIONS.md`、`TECHNICAL_STANDARDS.md`、`docs/superpowers/plans/2026-04-25-workbench-mvp-scope.md` |
| OQ-005 | 团队管理员与普通成员的权限矩阵是否先只覆盖 P1 页面 | open | M02、M10 | `W13-A` 已确认一期 MVP 必须有完整权限能力，但角色集合、权限矩阵粒度、管理台职责与多团队预留仍未确认；后续只可在设计文档中补齐，不得直接实施 | `DESIGN_DECISIONS.md`、`MODULE_INDEX.md`、`docs/superpowers/plans/2026-04-25-workbench-mvp-scope.md` |
| OQ-006 | Markdown 预览与导出是否必须共用同一渲染链 | open | M03 | `W13-A` 已确认一期导出采用复制 / Markdown 下载，不做完整 PDF；但 Markdown 预览、Markdown 下载、复制内容与未来 PDF 是否共用同一渲染链仍未确认，需由 `W13-D` 明确 | `DESIGN_DECISIONS.md`、`TECHNICAL_STANDARDS.md`、`docs/superpowers/plans/2026-04-25-workbench-mvp-scope.md` |
| OQ-007 | 上传、转换、导出在 P1 中哪些必须异步 | proposed-default | M03、M10 | 本轮按“上传同步入库，转换与导出异步”推进 | `TECHNICAL_STANDARDS.md` |
| OQ-008 | 匹配分析与评估规则是否需要版本化 | proposed-default | M04、M07、M10 | 本轮先按保留规则版本推进，便于解释与回放 | `TECHNICAL_STANDARDS.md`、`DESIGN_DECISIONS.md` |
| OQ-009 | Embedding 与向量化来源如何确定 | open | M05、M06 | 默认先抽象 provider 接口，并使用本地配置驱动 | `TECHNICAL_STANDARDS.md` |
| OQ-010 | 归档粒度是整份资产、片段还是题目级 | open | M05、M08 | 默认以资产级与片段级为主，题目级作为派生视图 | `MODULE_INDEX.md` |
| OQ-011 | Search snapshot 的来源只做导入还是需要抓取 | proposed-default | M06、M10 | 本轮先按 P1 只做导入，不做在线抓取推进 | `DESIGN_DECISIONS.md`、`TECHNICAL_STANDARDS.md` |
| OQ-012 | 上下文包中的 source priority 与引用摘要规则如何定稿 | open | M06 | 默认优先级为 JD > 简历 > 训练证据 > 资产检索 > search snapshot | `TECHNICAL_STANDARDS.md` |
| OQ-013 | 打磨主题推荐是规则、LLM 还是混合 | open | M07 | 默认首轮采用规则推荐 | `DESIGN_DECISIONS.md`、`TECHNICAL_STANDARDS.md` |
| OQ-014 | 模拟面试、打磨模式和复盘是否共用同一评估口径 | proposed-default | M07、M08、M09 | 本轮先按共享核心评估框架、允许场景级字段扩展推进 | `TECHNICAL_STANDARDS.md` |
| OQ-015 | 真实面试输入是结构化问答、自由 transcript 还是混合 | open | M08 | 默认采用混合输入模型 | `MODULE_INDEX.md` |
| OQ-016 | 薄弱项聚合 key、消减规则和停练规则如何定稿 | open | M09 | 默认按能力节点 + 题型 + 证据来源聚合，规则后续评审定稿 | `TECHNICAL_STANDARDS.md`、`DESIGN_DECISIONS.md` |
| OQ-017 | 管理台的模型推荐来源是本地 catalog 还是在线同步 | proposed-default | M10 | 本轮先按本地 catalog / seed 推进 | `DESIGN_DECISIONS.md`、`TECHNICAL_STANDARDS.md` |
| OQ-018 | 管理台是否负责 search snapshot 导入与运维 | proposed-default | M06、M10 | 本轮先按负责导入与运维入口、不承担抓取本身推进 | `TECHNICAL_STANDARDS.md`、`MODULE_INDEX.md` |
| OQ-019 | 根目录统一脚本与最小 CI 校验矩阵应冻结到什么粒度，才算满足平台基线的下游输入要求 | proposed-default | M01、M10 | 本轮先采用方案 B：冻结统一脚本命名（`dev:web` / `dev:api` / `test:web` / `test:api`）、最小存活检查（`GET /api/v1/health` -> `200 {\"status\":\"ok\"}`）与最小验证入口类型（API=`pytest`、Web=`vitest`），CI 只冻结 API/Web 两类最小校验 lane，不在当前轮冻结完整流水线矩阵 | `TECHNICAL_STANDARDS.md`、`DESIGN_DECISIONS.md`、`DOCUMENT_PROGRESS.md` |
| OQ-020 | 共享页面原语（`PageHeader` / Dashboard 摘要区）应冻结到什么最小接口边界，才能支撑后续页面复用 | proposed-default | M01、M02、M03 | 本轮先采用方案 B：冻结最小共享页面原语边界；`PageHeader` 只承载标题/说明/主次动作，摘要区独立承载 `status_badge` / `updated_at` / `summary_items` 与最小状态表达，不扩张为完整 props catalog | `TECHNICAL_STANDARDS.md`、`DESIGN_DECISIONS.md`、`DOCUMENT_PROGRESS.md` |
| OQ-021 | 列表查询状态、分页交互与 URL / callback 的映射规则应如何统一 | proposed-default | M01、M02、M03、M04-M10 | 当前默认采用方案 B，并按三层状态分层：共享最小层固定为 `page` / `page_size` / `q` / `status` / `sort` / `order` 与统一分页响应骨架；模块扩展层允许单独登记扩展查询键（如 `updated_after` / `updated_before`），但不得回写成共享前提；实现细节层中的 route / callback / request adapter 细节继续留在各模块最低位文档处理。该口径已足够支撑本轮最低位压缩，但仍未达到可直接放行正式候选的程度。本轮模块吸收摘要更新为：`M01` 已压到共享最小层输入且当前目标项已清理完成，但整体仍未被总控接受；`M02` 已在模块内把 `GET /api/v1/members` 闭合到共享最小层且明确“闭合 != 放行”，当前最小剩余缺口已进一步压实为“该共享最小层仍只停留在 `proposed-default` 治理层、尚未升格为正式候选输入 + 正式开窗层为空 + 权限消费边界留在模块层”；`M03` 已在最低位 API 文档稳定吸收且仍未放行 | `TECHNICAL_STANDARDS.md`、`DESIGN_DECISIONS.md`、`DOCUMENT_PROGRESS.md` |
| OQ-022 | locale fallback、切换策略与消息命名空间应冻结到什么程度，才能作为共享 Web 契约下发 | proposed-default | M01、M02、M03、M04-M10 | 本轮先采用方案 B：统一 `apps/web/src/i18n/**` + `getMessages(locale)` 入口，首轮 locale seed 固定为 `zh-CN` / `en-US`、默认 locale=`zh-CN`；切换由 layout / App Shell 统一解析 active locale；fallback 固定为“请求 locale -> `zh-CN` -> 记录缺失 key”，禁止组件硬编码兜底；namespace 只冻结“共享壳层一层、业务页面一层”的最小边界，不扩张为完整 i18n 架构 | `TECHNICAL_STANDARDS.md`、`DESIGN_DECISIONS.md`、`DOCUMENT_PROGRESS.md` |
| OQ-023 | `/(dashboard)/admin/members` 与 `/api/v1/admin/members` 的完整实现应继续由 M02 承接，还是由后续治理模块承接 | proposed-default | M02、M10 | 本轮先采用方案 B：`M02` 只负责身份解析、授权规则、权限矩阵与最小鉴权契约，完整成员管理页面 / API 由后续治理模块承接 | `DESIGN_DECISIONS.md`、`MODULE_INDEX.md` |
| OQ-024 | 计划重构后，旧 `ST02_* / ST03_*` 子任务目录是否应退役为历史容器，并按新的微任务蓝本重建正式入口 | proposed-default | M02、M03 | 当前按总控固定映射处理，并已写死为默认治理口径：历史容器层中，`ST02_01 / ST02_02 / ST02_03 / ST03_01 / ST03_02 / ST03_03` 全部固定为历史容器且禁止直开；观察蓝本层中，`M02` 当前只允许 `MT02_01 / MT02_02`，`M03` 当前只允许 `MT03_01 / MT03_03` 作为白名单观察入口，其余蓝本不得自行上推；正式开窗层中，本轮正式子任务 ID 名单固定为空，只有总控在后续正式候选复评完成后才能在 `TASK_INDEX.md` 中新增正式子任务 ID 与开窗资格。`MQ-209` 已吸收到本条叙事中。当前 `M01 / M02 / M03` 都不是正式子任务设计候选；本轮后续残余已不再是映射未同步或模块侧文案残差，而是正式开窗层持续为空所形成的治理性结构阻塞 | `TASK_INDEX.md`、`DOCUMENT_PROGRESS.md`、`MODULE_INDEX.md` |
| OQ-025 | `jobs.requirement_items_json` 的最小 item 结构、空值语义、排序规则与写入责任应冻结到什么程度，才能作为 M04 / M06 的稳定输入 | proposed-default | M03、M04、M06 | 当前按三层状态分层处理：最小共享输入层固定为 `item_key` / `text`、`null / []` 语义、数组顺序即消费顺序，以及“仅岗位写模型可整体替换”；扩展字段层继续保持未冻结，不进入共享稳定输入；完整链路语义层继续留在 `M03` 的最低位文档压缩，不据此宣布完整岗位链 / 下游链 ready。该口径已被 `M03` 吸收为最小共享输入，但不等于 `MT03_01 / MT03_03` 已升级为正式候选；当前对 `M04 / M06` 只可作为最小设计输入，不足以支撑上传 / 导出微任务或完整岗位链 ready。本轮状态补充为：`M03` 的直接结构性主阻塞已统一写成“正式开窗层为空 + 当前阶段关窗 + 上传 / 导出链依赖未变”，而最低位 API 高 `L4` 只是结果态 | `TECHNICAL_STANDARDS.md`、`DESIGN_DECISIONS.md`、`DOCUMENT_PROGRESS.md` |
| OQ-026 | 一期 MVP 是否继续沿用 W10 首切片“JD + 简历 Markdown -> 3 条问题 -> 第 1 题问答 -> 简版反馈” | confirmed | 全局 | 用户已确认组合 `1B2C3C4C5C6C7B8A9B`：一期 MVP 不再是 W10 首切片，必须重新定义为工作台级 MVP；W10 `apps/web/**` 原型只保留为原型探索证据，不直接扩展为正式一期开发起点 | `DESIGN_DECISIONS.md`、`PLAN_LATEST.md`、`docs/superpowers/plans/2026-04-25-workbench-mvp-scope.md` |
| OQ-027 | 一期 MVP 是否必须包含服务端历史记录 / 复盘记录 | confirmed | M06、M08 | 用户已确认一期 MVP 必须包含服务端历史记录 / 复盘记录；具体对象模型、查询维度、复盘生成边界、保留周期与后端实现仍未确认 | `DESIGN_DECISIONS.md`、`docs/superpowers/plans/2026-04-25-workbench-mvp-scope.md` |
| OQ-028 | 一期 MVP 是否必须接真实 LLM | confirmed | M06、M07、M10 | 用户已确认一期 MVP 必须接真实 LLM；具体 LLM provider、模型选择、调用策略、成本控制、失败重试与配置管理仍未确认 | `DESIGN_DECISIONS.md`、`docs/superpowers/plans/2026-04-25-workbench-mvp-scope.md` |
| OQ-029 | 一期 MVP 是否必须有完整登录 / 权限 | confirmed | M02、M10 | 用户已确认一期 MVP 必须有完整登录 / 权限；具体登录方案、会话机制、权限矩阵、管理员边界与审计策略仍未确认 | `DESIGN_DECISIONS.md`、`docs/superpowers/plans/2026-04-25-workbench-mvp-scope.md` |
| OQ-030 | 简历和面试记录是否必须服务端保存 | confirmed | M03、M06、M08 | 用户已确认简历和面试记录都需要服务端保存；具体数据库类型、文件存储方式、版本模型、数据迁移与备份策略仍未确认 | `DESIGN_DECISIONS.md`、`docs/superpowers/plans/2026-04-25-workbench-mvp-scope.md` |
| OQ-031 | 一期 MVP 是否需要完整 `0-100` 多维评分 | confirmed | M04、M07、M08、M09 | 用户已确认一期 MVP 需要完整 `0-100` 多维评分；具体评分维度、权重、证据绑定、解释模板、通过线与版本化规则仍未确认 | `DESIGN_DECISIONS.md`、`docs/superpowers/plans/2026-04-25-workbench-mvp-scope.md` |
| OQ-032 | 一期导出形态是否做完整 PDF | confirmed | M03、M06、M08 | 用户已确认一期导出采用复制 / Markdown 下载，不做完整 PDF；具体 Markdown 文件结构、命名、复制范围、导出入口与历史记录关系仍未确认 | `DESIGN_DECISIONS.md`、`docs/superpowers/plans/2026-04-25-workbench-mvp-scope.md` |
| OQ-033 | 当前 `apps/web/**` 原型是否作为正式 MVP 开发起点 | confirmed | M01、M03、M06、M07 | 用户已确认当前 `apps/web/**` 原型保留为原型探索参考证据，不直接扩展为正式一期 MVP；后续若复用任何交互或组件，需要先在设计文档中重新裁剪和确认 | `DESIGN_DECISIONS.md`、`PLAN_LATEST.md`、`docs/superpowers/plans/2026-04-25-workbench-mvp-scope.md` |
| OQ-034 | 当前是否继续代码开发 | confirmed | 全局 | 用户已确认暂停代码开发，回到设计文档补齐；在 `W13-B / W13-C / W13-D` 完成并经用户再次确认前，不允许继续扩展 `apps/web/**`、创建 `apps/api/**`、接真实 LLM、做数据库、登录、评分或后端实现 | `PLAN_LATEST.md`、`EXECUTION_LOG.md`、`docs/superpowers/plans/2026-04-25-current-repo-execution-plan.md` |
| OQ-035 | 一期登录是否支持用户自助注册，还是由管理员创建账号 | open | M02、M10 | `W13-B` 推荐一期采用“管理员创建账号”作为默认候选，以保持账号和权限边界受控；自助注册或注册审核作为备选，需 `W13-C` 确认 | `docs/superpowers/plans/2026-04-25-workbench-mvp-ia-user-journey.md`、`DESIGN_DECISIONS.md` |
| OQ-036 | 一期权限是否只有普通用户 / 管理员两级 | open | M02、M10 | `W13-B` 推荐一期采用普通用户 / 管理员两级，避免过早进入复杂组织治理；Owner / Admin / Member 或资源级权限留作备选，需 `W13-C` 确认 | `docs/superpowers/plans/2026-04-25-workbench-mvp-ia-user-journey.md` |
| OQ-037 | 岗位和简历是否都必须列表化管理 | open | M03、M04、M06 | `W13-B` 推荐岗位与简历都列表化管理，以支撑服务端保存、复用、历史记录和工作台总览；是否允许更轻量的简历内嵌管理需用户确认 | `docs/superpowers/plans/2026-04-25-workbench-mvp-ia-user-journey.md` |
| OQ-038 | 复盘记录是否按 `InterviewSession` 展示，还是作为独立复盘对象展示 | open | M06、M08 | `W13-B` 推荐统一历史记录列表展示会话、评分和复盘，并在详情中保留清晰对象关系；具体 `InterviewSession` / `SessionRecord` / 复盘对象边界需 `W13-C` 确认 | `docs/superpowers/plans/2026-04-25-workbench-mvp-ia-user-journey.md` |
| OQ-039 | 评分报告是否独立页面，还是并入复盘详情 | open | M07、M08、M09 | `W13-B` 推荐面试结束后先显示轻量评分，复盘详情显示完整评分报告；具体评分报告结构与验收交 `W13-D` 确认 | `docs/superpowers/plans/2026-04-25-workbench-mvp-ia-user-journey.md` |
| OQ-040 | Markdown 下载入口和导出范围应如何确定 | open | M03、M06、M08 | `W13-B` 推荐一期在评分 / 复盘详情中提供复制 / Markdown 下载，列表提供导出状态或快捷入口但必要时进入详情确认；具体文件结构、命名、复制范围和导出快照需 `W13-D` 确认 | `docs/superpowers/plans/2026-04-25-workbench-mvp-ia-user-journey.md` |
| OQ-041 | 工作台首页是否需要统计卡片，以及一期统计范围是什么 | open | M01、M04、M07、M08 | `W13-B` 推荐只做行动型摘要：待复盘、进行中面试、最近岗位、最近评分；完整趋势分析和 BI 仪表盘后置 | `docs/superpowers/plans/2026-04-25-workbench-mvp-ia-user-journey.md` |
| OQ-042 | 资产库、训练中心、管理台、高级报表、更完整导出、运维 / 配置等后续占位放在哪里 | open | M05、M09、M10 | `W13-B` 推荐统一放入“后续能力”折叠菜单或低干扰占位区；RAG / 知识库和多轮高阶面试已进入一期主链，不再归入本占位问题 | `docs/superpowers/plans/2026-04-25-workbench-mvp-ia-user-journey.md` |
| OQ-043 | 一期 MVP 是否必须包含 RAG / 知识库能力 | confirmed | M05、M06、M08、M10 | 用户已确认一期 MVP 必须包含 RAG / 知识库；知识库入口、发起面试时选择上下文、面试台引用证据和复盘引用来源进入一期 IA。具体上传、切片、检索、权限和引用回溯仍未确认 | `DESIGN_DECISIONS.md`、`PLAN_LATEST.md`、`docs/superpowers/plans/2026-04-25-workbench-mvp-scope.md`、`docs/superpowers/plans/2026-04-25-workbench-mvp-ia-user-journey.md` |
| OQ-044 | 一期 MVP 是否必须包含多轮高阶面试能力 | confirmed | M06、M07、M08、M09 | 用户已确认一期 MVP 必须包含多轮高阶面试；多轮策略选择、面试台轮次 / 追问 / 上下文、每轮评价和复盘回写进入一期 IA。具体策略、轮次数、暂停 / 继续和结束条件仍未确认 | `DESIGN_DECISIONS.md`、`PLAN_LATEST.md`、`docs/superpowers/plans/2026-04-25-workbench-mvp-scope.md`、`docs/superpowers/plans/2026-04-25-workbench-mvp-ia-user-journey.md` |
| OQ-045 | 模拟面试模块默认入口是否必须是历史所有模拟记录列表 | confirmed | M02、M06、M08 | 用户已确认模拟面试模块默认入口必须是当前用户权限范围内可见的历史所有模拟记录 / 复盘记录列表；发起模拟面试是列表主操作，面试完成后必须回写历史记录 / 复盘记录。具体筛选、角色范围、归档 / 删除和团队视图仍未确认 | `DESIGN_DECISIONS.md`、`PLAN_LATEST.md`、`docs/superpowers/plans/2026-04-25-workbench-mvp-scope.md`、`docs/superpowers/plans/2026-04-25-workbench-mvp-ia-user-journey.md` |
| OQ-046 | 模拟记录列表默认筛选范围与普通用户 / 管理员可见范围如何确定 | open | M02、M06、M08 | `W13-B` 推荐普通用户和管理员默认都进入“我的记录”，管理员额外有团队 / 组织筛选；具体角色、资源范围、审计和列表查询交 `W13-C` 确认 | `docs/superpowers/plans/2026-04-25-workbench-mvp-ia-user-journey.md` |
| OQ-047 | 发起模拟面试是否必须先选择岗位和简历 | open | M03、M04、M06、M07 | `W13-B` 推荐岗位和简历都必选，并提供就地创建入口，以保证评分、RAG 和复盘证据可解释；是否允许缺失输入仍需用户确认 | `docs/superpowers/plans/2026-04-25-workbench-mvp-ia-user-journey.md` |
| OQ-048 | RAG / 知识库是否支持用户上传，以及知识库是个人私有、团队共享还是管理员公共 | open | M05、M06、M10 | `W13-B` 推荐一期支持用户私有上传 + 管理员公共知识库，团队共享后置；上传、解析、切片、删除、权限和引用回溯需 `W13-C` 确认 | `docs/superpowers/plans/2026-04-25-workbench-mvp-ia-user-journey.md` |
| OQ-049 | RAG 无命中或检索失败时是否允许继续面试 | open | M05、M06、M07、M08 | `W13-B` 推荐降级为岗位 + 简历上下文继续，但在面试台和复盘中明确证据缺口；具体错误码、重试和降级条件需 `W13-C / W13-D` 确认 | `docs/superpowers/plans/2026-04-25-workbench-mvp-ia-user-journey.md` |
| OQ-050 | 多轮高阶面试采用固定轮次、岗位驱动、弱项驱动还是混合策略 | open | M06、M07、M08、M09 | `W13-B` 推荐一期采用固定模板 + 岗位驱动，弱项驱动作为后续增强入口；具体轮次、追问和结束条件需用户确认 | `docs/superpowers/plans/2026-04-25-workbench-mvp-ia-user-journey.md` |
| OQ-051 | 多轮高阶面试是否允许中途暂停 / 继续 | open | M06、M08 | `W13-B` 推荐一期支持轮次边界暂停 / 继续，题目中途暂停后置；具体状态机、恢复上下文和记录列表操作需 `W13-C` 确认 | `docs/superpowers/plans/2026-04-25-workbench-mvp-ia-user-journey.md` |
| OQ-052 | 一期服务端保存采用什么数据库类型 | open | M01、M02、M03、M05、M06、M07、M08、M10 | `W13-C` 推荐 PostgreSQL 作为 `recommended / proposed-default`，因为登录 / 权限、历史记录、评分、RAG、审计和列表查询都是强关系场景；SQLite、本地轻量数据库或文档数据库仍作为备选，需用户确认 | `docs/superpowers/plans/2026-04-25-workbench-mvp-object-model-rag-multiround-backend.md` |
| OQ-053 | LLM prompt / response 是否保存以及保存到什么程度 | open | M06、M07、M08、M10 | `W13-C` 推荐保存脱敏后的 prompt / response 作为 `recommended / proposed-default`，既保留真实 LLM 审计能力，也降低简历、回答和知识库材料暴露风险；不保存完整内容或完整保存仍需用户确认 | `docs/superpowers/plans/2026-04-25-workbench-mvp-object-model-rag-multiround-backend.md` |
| OQ-054 | RAG 检索证据保存到什么程度 | open | M05、M06、M08、M10 | `W13-C` 推荐保存 query + topK retrieval result 作为 `recommended / proposed-default`，支撑复盘引用和失败分析；仅保存 citation 摘要或完整检索上下文仍需用户确认 | `docs/superpowers/plans/2026-04-25-workbench-mvp-object-model-rag-multiround-backend.md` |
| OQ-055 | 多轮面试上下文如何服务端保存 | open | M06、M07、M08、M09 | `W13-C` 推荐保存完整问答 + 摘要 + 评分证据作为 `recommended / proposed-default`，以支撑暂停 / 继续、评分复盘和 Markdown 导出；保存完整问答或结构化问答 + 摘要仍需用户确认 | `docs/superpowers/plans/2026-04-25-workbench-mvp-object-model-rag-multiround-backend.md` |
| OQ-056 | RAG / 知识库一期采用什么检索技术路线 | open | M05、M06、M08、M10 | `W13-C` 推荐混合检索作为 `recommended / proposed-default`，兼顾关键词精确性和语义召回；仅关键词检索或仅向量检索仍需用户确认 | `docs/superpowers/plans/2026-04-25-workbench-mvp-object-model-rag-multiround-backend.md` |
| OQ-057 | 一期多轮高阶面试中的“高阶”如何定义 | open | M06、M07、M08、M09 | `W13-C` 推荐以技术 / 专业能力深挖作为 `recommended / proposed-default`，行为面试和系统设计 / 案例分析可作为策略模板或后续增强；需用户确认 | `docs/superpowers/plans/2026-04-25-workbench-mvp-object-model-rag-multiround-backend.md` |
| OQ-058 | 一期真实 LLM 接入采用什么 provider 路线 | open | M06、M07、M10 | `W13-C` 推荐可插拔 provider 抽象并默认先接一个 provider 作为 `recommended / proposed-default`；直接 OpenAI API 或兼容 OpenAI-style API provider 路线仍需用户确认 | `docs/superpowers/plans/2026-04-25-workbench-mvp-object-model-rag-multiround-backend.md` |
| OQ-059 | LLM 调用失败时如何处理 | open | M06、M07、M08、M10 | `W13-C` 推荐保存失败状态并允许重新生成作为 `recommended / proposed-default`；失败后仅提示重试或回退 mock 仍需用户确认，其中 mock 回退不得默认作为正式一期行为 | `docs/superpowers/plans/2026-04-25-workbench-mvp-object-model-rag-multiround-backend.md` |
| OQ-060 | prompt / 模型版本记录到什么程度 | open | M06、M07、M08、M10 | `W13-C` 推荐记录脱敏 prompt、模型名和 prompt template version 作为 `recommended / proposed-default`；只记录模型与模板版本或完整记录 prompt / response 仍需用户确认 | `docs/superpowers/plans/2026-04-25-workbench-mvp-object-model-rag-multiround-backend.md` |
| OQ-061 | 一期登录态机制采用 session cookie、JWT 还是托管身份服务 | open | M02、M10 | `W13-C` 推荐 session cookie 作为 Web 工作台的一期 `recommended / proposed-default`；JWT、托管身份服务或其他登录机制仍需用户确认 | `docs/superpowers/plans/2026-04-25-workbench-mvp-object-model-rag-multiround-backend.md` |
| OQ-062 | 一期后端采用什么框架路线 | open | M01、M02、M05、M06、M07、M08、M10 | `W13-C` 推荐 FastAPI 作为 `recommended / proposed-default`，用于承接鉴权、领域服务、RAG、LLM 编排和评分复盘；Node.js / NestJS、Next.js API routes 或其他路线仍需用户确认 | `docs/superpowers/plans/2026-04-25-workbench-mvp-object-model-rag-multiround-backend.md` |
| OQ-063 | 后端设计应先冻结 API contract 还是先实现最小服务 | open | M01、M02、M03、M05、M06、M07、M08、M10 | `W13-C` 推荐先 OpenAPI / contract 作为 `recommended / proposed-default`，避免未确认方案被代码事实化；先最小服务实现或前后端并行定义契约仍需用户确认 | `docs/superpowers/plans/2026-04-25-workbench-mvp-object-model-rag-multiround-backend.md` |
| OQ-064 | 前后端目录结构如何规划 | open | M01-M10 | `W13-C` 推荐 `apps/web + packages/shared + apps/api` 作为 `recommended / proposed-default`，但当前仍禁止创建目录；`apps/web + apps/api`、单体 full-stack 或其他结构仍需用户确认 | `docs/superpowers/plans/2026-04-25-workbench-mvp-object-model-rag-multiround-backend.md` |
| OQ-065 | 一期 MVP 部署目标是什么 | open | M01、M10 | `W13-C` 推荐单机服务器作为 `recommended / proposed-default`，用于验证真实登录、数据库、LLM 和 RAG 的最小服务端闭环；本地 / 演示环境、云平台轻部署或其他部署方式仍需用户确认 | `docs/superpowers/plans/2026-04-25-workbench-mvp-object-model-rag-multiround-backend.md` |
| OQ-066 | 一期日志与观测做到什么程度 | open | M06、M07、M08、M10 | `W13-C` 推荐应用日志 + LLM 调用日志 + RAG 检索日志作为 `recommended / proposed-default`，并要求脱敏与保留周期后续确认；仅应用日志或应用日志 + LLM 调用日志仍需用户确认 | `docs/superpowers/plans/2026-04-25-workbench-mvp-object-model-rag-multiround-backend.md` |

| OQ-067 | 一期账号来源采用用户自助注册、管理员创建账号还是邀请制 | open | M02、M10 | `W13-C` 推荐管理员创建账号作为 `recommended / proposed-default`，以降低一期注册风控和权限初始化复杂度；用户自助注册、邀请制或自定义账号来源仍需用户确认 | `docs/superpowers/plans/2026-04-25-workbench-mvp-object-model-rag-multiround-backend.md` |
| OQ-068 | 一期角色层级采用两级、三级还是细粒度 permission 模型 | open | M02、M10 | `W13-C` 推荐普通用户 / 管理员两级作为 `recommended / proposed-default`，以支撑最小工作台管理；owner/admin/member 三级、细粒度 permission 或自定义模型仍需用户确认 | `docs/superpowers/plans/2026-04-25-workbench-mvp-object-model-rag-multiround-backend.md` |
| OQ-069 | 一期打磨模式和模拟模式做到什么深度 | open | M06、M07、M08、M09 | `W13-C` 推荐打磨模式即时反馈、模拟模式结束后报告作为 `recommended / proposed-default`；仅做入口差异或两种模式完整独立流程仍需用户确认 | `docs/superpowers/plans/2026-04-25-workbench-mvp-object-model-rag-multiround-backend.md` |
| OQ-070 | `WeaknessItem` 是否作为一期核心对象独立服务端保存 | open | M07、M08、M09、M10 | `W13-C` 推荐作为一期核心对象服务端保存，支撑累计、消减、停练和训练闭环；仅报告建议或轻量建议对象仍需用户确认 | `docs/superpowers/plans/2026-04-25-workbench-mvp-object-model-rag-multiround-backend.md` |
| OQ-071 | 能力树是否进入一期以及进入到什么深度 | open | M07、M08、M09 | `W13-C` 推荐轻量能力树作为 `recommended / proposed-default`，仅包含能力节点、等级和训练进展；不做能力树或完整 ontology 仍需用户确认 | `docs/superpowers/plans/2026-04-25-workbench-mvp-object-model-rag-multiround-backend.md` |
| OQ-072 | 一期资产库归档范围是只做归档动作、最小资产列表 / 详情还是完整资产库 | open | M05、M07、M08、M10 | `W13-C` 推荐归档动作 + 最小资产列表 / 详情作为 `recommended / proposed-default`；只做动作或完整资产库仍需用户确认 | `docs/superpowers/plans/2026-04-25-workbench-mvp-object-model-rag-multiround-backend.md` |
| OQ-073 | 训练抽屉是否作为一期通用交互 | open | M04、M06、M07、M08、M09 | `W13-C` 推荐训练抽屉作为岗位详情、模拟面试详情 / 报告、复盘详情的通用入口；只在复盘实现或改成按钮跳转仍需用户确认 | `docs/superpowers/plans/2026-04-25-workbench-mvp-object-model-rag-multiround-backend.md` |
| OQ-074 | 真实面试复盘是否进入一期以及实现深度 | open | M08、M09、M10 | `W13-C` 推荐一期支持手动录入真实面试材料并逐题严格拆解；仅占位或完整上传 / 解析 / 归档链路仍需用户确认 | `docs/superpowers/plans/2026-04-25-workbench-mvp-object-model-rag-multiround-backend.md` |
| OQ-075 | 打磨模式每题反馈是否完整服务端保存 | open | M07、M08、M09、M10 | `W13-C` 推荐保存结构化反馈、失分点、证据、参考回答和原理摘要；只展示不保存或完整保存 prompt / response 中间态仍需用户确认 | `docs/superpowers/plans/2026-04-25-workbench-mvp-object-model-rag-multiround-backend.md` |
| OQ-076 | 薄弱项消减规则一期自动执行还是推荐后用户确认 | open | M07、M08、M09 | `W13-C` 推荐系统给出消减建议、用户确认后生效作为 `recommended / proposed-default`；自动消减或只记录进展仍需用户确认 | `docs/superpowers/plans/2026-04-25-workbench-mvp-object-model-rag-multiround-backend.md` |
| OQ-077 | 资产类型 schema 一期是否支持动态字段以及支持到什么子集 | open | M05、M08、M10 | `W13-C` 推荐支持文本、枚举、标签、日期、引用等 schema 子集动态字段；固定字段或完整 JSON Schema 仍需用户确认 | `docs/superpowers/plans/2026-04-25-workbench-mvp-object-model-rag-multiround-backend.md` |
| OQ-078 | 待打磨清单是否独立页面化 | open | M04、M07、M08、M09 | `W13-C` 推荐工作台首页 / 详情页提供最小待打磨清单，不做完整独立训练中心；不页面化或独立训练中心仍需用户确认 | `docs/superpowers/plans/2026-04-25-workbench-mvp-object-model-rag-multiround-backend.md` |

## 3. 本轮高优问题处理判断

- 本轮（阶段 3 / 总控澄清 + 模块候选白名单准备轮）必须优先处理的问题：
  - `OQ-024` 旧入口退役后的全局映射与直开约束
  - `OQ-025` `jobs.requirement_items_json` 最小输入契约
  - `OQ-021` 共享最小映射与模块级扩展的边界澄清
- 本轮检查结论：
  - `OQ-021 / OQ-024 / OQ-025` 本轮统一继续保持 `proposed-default`，本轮目标是把三者的状态分层、模块吸收结果与真实剩余条件继续锁死，而不是把三者推进到 `confirmed`
  - `OQ-021` 继续保持 `proposed-default`，并正式分为“共享最小层 / 模块扩展层 / 实现细节层”；`updated_after` / `updated_before` 当前不属于共享最小层
  - `OQ-024` 继续保持 `proposed-default`，并正式分为“历史容器层 / 观察蓝本层 / 正式开窗层”；当前该三层映射已被总控写死，白名单观察面与正式子任务开窗条件必须显式分离
  - `OQ-025` 继续保持 `proposed-default`，并正式分为“最小共享输入层 / 扩展字段层 / 完整链路语义层”；当前只足够支撑最低位压缩与最小下游引用，不足以宣告岗位链整体 ready
  - 当前总控补充判断为：`M03` 对 `OQ-021 / OQ-025` 的最低位吸收已经基本稳定，应写成“已吸收但未放行”，且 `OQ-024` 不应再被写成“待同步”；`M02` 已在模块内把 `/members` 闭合到共享最小层，但当前最小剩余缺口已进一步压实为“该共享最小层尚未从 `proposed-default` 治理层升格为正式候选输入”；`M01` 已把 `OQ-021` 吸收为共享最小层输入，且当前目标项已清理完成，但这不等于模块整体候选已成立
  - 本轮不新增全局 OQ；模块局部问题继续只作为吸收记录：`MQ-205 -> OQ-021`、`MQ-207 / MQ-209 -> OQ-024`、`MQ-307 / MQ-308 / MQ-309 -> OQ-025`
  - `OQ-019~OQ-023` 继续维持上一轮已登记的默认冻结口径，不再作为本轮主阻塞重复讨论

| 优先级 | OQ ID | 当前状态 | 当前影响模块 | 本轮处理判断 |
| --- | --- | --- | --- | --- |
| P0 | OQ-001 | open | M01-M10 | W13-A 已确认一期 MVP 是工作台级且包含服务端能力，但目标代码结构、`apps/api/**` / `infra/**` 是否创建、API 框架、数据库与部署边界仍未确认 |
| P0 | OQ-004 / OQ-005 | open | M02、M10 | W13-A 已确认完整登录 / 权限进入一期范围，但登录方案、会话机制、权限矩阵和管理员边界仍未确认 |
| P0 | OQ-006、OQ-007 | open / proposed-default | M03、M10 | W13-A 只确认一期导出采用复制 / Markdown 下载、不做完整 PDF；Markdown 渲染链、上传 / 转换 / 导出异步策略仍需后续确认 |
| P0 | OQ-043 / OQ-044 / OQ-045 | confirmed | M05、M06、M07、M08、M09、M10 | 用户已确认 RAG / 知识库、多轮高阶面试和模拟记录列表默认入口进入一期主链；这些不是 proposed-default，也不再归入后续占位 |
| P0 | OQ-046 / OQ-047 / OQ-048 / OQ-049 / OQ-050 / OQ-051 | open | M02、M03、M04、M05、M06、M07、M08、M09、M10 | 这些是 W13-B 从已确认范围中拆出的实现细节问题：记录范围、岗位简历必选、知识库上传与可见范围、RAG 失败降级、多轮策略、多轮暂停 / 继续；不得在 W13-B 中自行写成 confirmed |
| P0 | OQ-052 / OQ-053 / OQ-054 / OQ-055 / OQ-056 / OQ-057 / OQ-058 / OQ-059 / OQ-060 / OQ-061 / OQ-062 / OQ-063 / OQ-064 / OQ-065 / OQ-066 | open | M01-M10 | 这些是 W13-C 从已确认范围中拆出的对象模型、服务端保存、RAG、多轮、LLM、API / 后端和运维边界确认问题；推荐方案只可作为 `recommended / proposed-default`，不得写成 confirmed，也不得据此进入实现窗口 |
| P0 | OQ-067 / OQ-068 / OQ-069 / OQ-070 / OQ-071 / OQ-072 / OQ-073 / OQ-074 / OQ-075 / OQ-076 / OQ-077 / OQ-078 | open | M02-M10 | 这些是 W13-C 补齐的账号来源、角色层级、面试模式、薄弱项、能力树、资产归档、训练抽屉、真实面试复盘、打磨反馈保存、薄弱项消减、资产 schema 和待打磨清单页面化确认问题；推荐方案只可作为 `recommended / proposed-default`，不得写成 confirmed，也不得据此进入实现窗口 |
| P0 | OQ-019 | proposed-default | M01、M10 | 已形成入口语义级默认冻结方案；可作为 `M01` 平台基线与 `M10` 治理边界切分输入，但暂不扩张为完整流水线定稿 |
| P0 | OQ-021 | proposed-default | M01、M02、M03、M04-M10 | 已形成三层状态：共享最小映射维持 `page/page_size/q/status/sort/order`、分页骨架与页面容器 adapter 职责；模块扩展键单独登记；route / callback / request adapter 细节继续留在最低位文档处理。模块吸收摘要：`M01` 已压到共享最小层输入且当前目标项已清理完成，`M02` 已在模块内闭合到共享最小层但 `GET /api/v1/members` 当前仍只停留在默认治理层、尚未升格为正式候选输入，`M03` 已吸收但未放行 |
| P0 | OQ-024 | proposed-default | M02、M03 | 已形成并写死三层状态：旧 `ST02_* / ST03_*` 为历史容器、`M02` 当前只允许 `MT02_01 / MT02_02`、`M03` 当前只允许 `MT03_01 / MT03_03` 作为观察蓝本、正式子任务 ID 与开窗资格继续后置到正式候选复评之后；当前正式开窗名单固定为空。`MR-18 / MR-23 / RV-09` 已把 `M03` 的现行口径压稳为“已吸收但未放行”，当前剩余只保留正式开窗层为空所形成的治理性结构阻塞，不再重开全局映射讨论 |
| P0 | OQ-025 | proposed-default | M03、M04、M06 | 已形成三层状态：`item_key` / `text`、`null` / `[]`、数组顺序与写入责任属于最小共享输入层；扩展字段继续未冻结；完整岗位链语义继续留在模块最低位文档处理。`M03` 已吸收最小共享输入，但该问题目前只足够支撑 `M04 / M06` 的最小设计输入，仍不足以支撑上传 / 导出微任务或完整岗位链 ready；当前直接结构性主阻塞已固定为“正式开窗层为空 + 当前阶段关窗 + 上传 / 导出链依赖未变”，最低位 API 高 `L4` 是结果态 |
| P1 | OQ-020 | proposed-default | M01、M02、M03 | 已形成方案 B 默认冻结候选；最小共享页面原语已足够支撑 `M01/M03` 继续推进，并为 `M02` 提供页面承接口径，但暂不升级为 `confirmed` |
| P1 | OQ-022 | proposed-default | M01、M02、M03、M04-M10 | 已形成最小 i18n 共享默认口径；可作为模块设计输入，但完整 locale 切换持久化、URL 策略与 formatter 规则仍未冻结 |
| P1 | OQ-023 | proposed-default | M02、M10 | 继续保持 `proposed-default`；本轮直接作为模块职责重切输入，不再回退为 `open` |
| P1 | OQ-008 | proposed-default | M04、M07、M10 | 已按“规则需要版本化”冻结，作为评审窗口基线 |
| P1 | OQ-011、OQ-018 | proposed-default | M06、M10 | 已按“snapshot 只导入、不抓取；管理台负责导入与运维入口”冻结，作为评审窗口基线 |
| P1 | OQ-012 | open | M06 | 暂不冻结；当前默认只覆盖 source priority，尚未覆盖引用摘要规则 |
| P1 | OQ-014 | proposed-default | M07、M08、M09 | 已按共享核心评估框架冻结，作为评审窗口基线 |
| P1 | OQ-016 | open | M09 | 暂不冻结；当前默认只覆盖聚合 key，尚未覆盖消减与停练规则 |
| P1 | OQ-017 | proposed-default | M10 | 已按本地 catalog / seed 冻结，作为评审窗口基线 |

## 4. 默认方案冻结建议

> 本节用于帮助总控 Codex 在“信息仍不充分”时决定：哪些问题可以先按默认方案冻结，从而继续推进模块文档。

| OQ ID | 本轮处理 | 默认方案是否足以继续推进 | 若冻结后优先推进模块 |
| --- | --- | --- | --- |
| OQ-001 | 保持 `open` | 否；W13-A 只确认工作台级范围，不确认代码结构、API 框架、数据库或部署边界 | W13-C |
| OQ-002 | 已标记 `proposed-default` | 是，但仅在 `W10-D` 被条件放行后才进入最小骨架输入 | M01、M10 |
| OQ-003 | 已标记 `proposed-default` | 是 | M01 |
| OQ-004 | 保持 `open` | 否；W13-A 确认登录进入范围，但未确认固定 Bearer token、JWT、session cookie 或托管身份服务 | W13-C |
| OQ-005 | 保持 `open` | 否；W13-A 确认权限进入范围，但未确认角色集合、权限矩阵粒度和管理员边界 | W13-C |
| OQ-006 | 保持 `open` | 否；W13-A 确认复制 / Markdown 下载，不确认 Markdown 预览、下载和未来 PDF 是否共用同一渲染链 | W13-D |
| OQ-007 | 已标记 `proposed-default` | 是 | M03 |
| OQ-008 | 已标记 `proposed-default` | 是 | M04、M07 |
| OQ-009 | 保持 `open` | 本轮暂不需要 | M05 |
| OQ-010 | 保持 `open` | 本轮暂不需要 | M05、M08 |
| OQ-011 | 已标记 `proposed-default` | 是 | M06、M10 |
| OQ-012 | 保持 `open` | 否，默认方案尚不足以覆盖引用摘要规则 | M06 |
| OQ-013 | 保持 `open` | 本轮暂不需要 | M07 |
| OQ-014 | 已标记 `proposed-default` | 是，但需跨模块同步 | M07、M08、M09 |
| OQ-015 | 保持 `open` | 本轮暂不需要 | M08 |
| OQ-016 | 保持 `open` | 否，默认方案尚不足以覆盖消减与停练规则 | M09 |
| OQ-017 | 已标记 `proposed-default` | 是 | M10 |
| OQ-018 | 已标记 `proposed-default` | 是 | M06、M10 |
| OQ-019 | 已标记 `proposed-default` | 是，可作为 `M01` 基线收口与 `M10` 职责切分输入 | M01、M10 |
| OQ-020 | 已标记 `proposed-default` | 是，可作为 `M01` 共享页面原语收口、`M03` 页面设计收缩与 `M02` 页面承接口径对齐输入 | M01、M02、M03 |
| OQ-021 | 已标记 `proposed-default` | 是，但共享最小层只覆盖 `page/page_size/q/status/sort/order`、分页骨架与职责边界；`updated_after` / `updated_before` 当前仅可作为模块级扩展，route / callback 细节继续留在最低位文档 | M01、M02、M03 |
| OQ-022 | 已标记 `proposed-default` | 是，可作为 `M01` 共享 i18n 收口、`M02` 模块重切与 `M03` 页面命名基线输入 | M01、M02、M03 |
| OQ-023 | 继续保持 `proposed-default` | 是 | M02、M10 |
| OQ-024 | 已标记 `proposed-default` | 是，可作为 `TASK_INDEX.md` 与模块入口同步的固定治理口径；历史容器、观察蓝本和正式开窗资格已分层且已写死，当前继续通过“正式开窗名单为空”的规则阻止任何观察面被误写成正式候选 | M02、M03 |
| OQ-025 | 已标记 `proposed-default` | 是，可作为 `M03 -> M04/M06` 的最小共享输入；扩展字段继续保持未冻结，完整链路语义继续留在模块最低位压缩，不据此宣告整体 ready | M03、M04、M06 |

## 5. W10-C 首切片问题分类

> 本节 `5.1` 至 `5.5` 只记录 W10 首切片与原型探索历史口径。`W13-A` 之后，当前一期 MVP 范围以 `5.6` 和 `OQ-026` 至 `OQ-034` 为准，W10 首切片不得再被误读为用户认可的一期 MVP。

> 以下分类用于本轮关系补齐，不改变上方问题表的原始状态列。

### 5.1 已确认（关系层事实）

- `RQ01` 当前仍是首切片正式 requirement 入口。
- 首切片直接模块固定为 `M03 / M04 / M06 / M07`，`M01` 只作为条件性支撑模块。
- `MT03_01 / MT03_03` 只允许作为 `M03` 观察蓝本；`ST04_01 / ST04_02 / ST06_01 / ST06_02 / ST07_03` 只允许作为后续承接对象。
- 当前正式开窗层仍为空；本轮不新增正式子任务 ID，不重新激活旧 `ST03_*` 历史容器。

### 5.2 `proposed-default`（可作为本轮关系输入）

- `OQ-001`：当前不创建业务代码目录，未来 monorepo 蓝图不是本轮实施依据。
- `OQ-002`：最小运行时 / 测试 / CI 基线只在 `W10-D` 被条件放行后才可能进入。
- `OQ-006`：Markdown 预览与导出共用同一渲染链，作为 `M03` 的输入侧约束继续保留。
- `OQ-020 / OQ-021`：共享页面原语与列表 shared contract 继续只作为最小共享输入，不外推为正式开窗依据。
- `OQ-024 / OQ-025`：历史容器、观察蓝本、正式开窗层与 `jobs.requirement_items_json` 最小共享输入继续沿用当前默认冻结口径。

### 5.3 需要用户确认（当前不得由 Codex 自行确认）

- `OQ-004 / OQ-005`：在 `W10-D-Gate` 前，用户登录、会话与权限矩阵确需用户确认；本轮用户已确认 `W10-D` 不做登录，只保留轻量 `session / user context` 边界，但未来鉴权机制与权限矩阵仍未在本轮定稿。
- `OQ-008`：匹配分析 / 评分规则是否版本化在 `W10-D-Gate` 前确需用户确认；本轮用户已确认不生成数值评分、只输出文字反馈，但评分维度、评分版本化与正式评分标准仍未在本轮定稿。
- 真实 LLM API、长期记录 / 导出、RAG / search snapshot 是否进入当前切片，在 `W10-D-Gate` 前均需用户或总控明确确认；本轮用户已确认不接真实 LLM、只做会话内临时保存、不做导出，并继续排除 RAG / search snapshot / 资产库 / 管理台，详见 5.5。

### 5.4 本轮明确排除（不进入首切片关系主链）

- `OQ-007`：上传 / 转换 / 导出异步策略对应上传导出链，本轮不进入首切片主链。
- `OQ-009 / OQ-010`：Embedding / 向量化、资产归档粒度属于 `M05` 范围，本轮排除。
- `OQ-011 / OQ-012 / OQ-018`：search snapshot 导入 / 运维、上下文包多源优先级与引用摘要规则不进入当前只依赖 JD + 简历的最小链路。
- `OQ-013 / OQ-014 / OQ-016`：主题推荐、跨场景评估框架、长期进度与停练规则不进入本轮最小反馈摘要范围。
- `OQ-015 / OQ-017`：真实面试复盘输入模型与管理台模型目录继续排除在首切片之外。

### 5.5 W10-D-Gate 已确认（用户确认结果）

> 以下 8 项是用户在 `W10-D-Gate` 中已明确确认的历史原型探索边界；`W13-A` 已重新确认一期 MVP 必须是工作台级，因此这些内容不再代表当前一期 MVP 范围。

- `Q1 / confirmed`：允许在正式开窗层为空时进入原型探索，但仅限首切片最小原型骨架；该探索不代表正式实施完成。
- `Q2 / confirmed`：首切片暂不接入真实 LLM API，必须保留 LLM adapter / provider 边界，并以 mock 输出驱动原型。
- `Q3 / confirmed`：本轮不做登录；只保留 `session / user context` 的轻量边界，避免后续接登录时大改。
- `Q4 / confirmed`：简历和问答记录只在单次会话内临时保存，不做长期持久化；数据结构需可迁移到本地或服务端存储。
- `Q5 / confirmed`：本轮不生成数值评分，只输出文字反馈；反馈模型可预留 optional `score` / `dimensions` 字段，但 UI 不展示评分。
- `Q6 / confirmed`：本轮不做导出，只页面返回 Markdown 兼容文本；复制或导出能力只作为后续阶段候选。
- `Q7 / confirmed`：只允许创建 `apps/web/**` 最小原型骨架；`apps/api/**`、`infra/**` 本轮继续明确禁止。
- `Q8 / confirmed`：首切片完成标准固定为“JD + 简历 Markdown -> 3 条首轮问题 -> 第 1 题问答 -> 简版反馈”。
- 本轮继续明确排除：RAG、资产库、管理台、多轮面试、完整权限体系、完整 CI/CD。

### 5.6 W13-A 与后续用户 confirmed 结果（当前一期工作台 MVP 范围）

> 以下 12 项是用户已确认结论，状态为 `confirmed`，不再是 `proposed-default`。本节只冻结范围层，不冻结具体实现方案。

- `1B / confirmed`：最小项目范围必须是工作台级，一期 MVP 不再是 W10 首切片。
- `2C / confirmed`：一期 MVP 必须包含服务端历史记录 / 复盘记录。
- `3C / confirmed`：一期 MVP 必须接真实 LLM。
- `4C / confirmed`：一期 MVP 必须有完整登录 / 权限。
- `5C / confirmed`：简历和面试记录都需要服务端保存。
- `6C / confirmed`：一期 MVP 需要完整 `0-100` 多维评分。
- `7B / confirmed`：导出采用复制 / Markdown 下载，不做完整 PDF。
- `8A / confirmed`：当前 `apps/web/**` 原型保留为原型探索参考证据，不直接扩展。
- `9B / confirmed`：暂停代码开发，回到设计文档补齐。
- `10B / confirmed`：一期 MVP 必须包含 RAG / 知识库能力。
- `11B / confirmed`：一期 MVP 必须包含多轮高阶面试能力。
- `12B / confirmed`：模拟面试模块默认入口必须是历史所有模拟记录列表；用户从历史记录列表发起模拟面试，再进入面试台，完成后回写历史记录 / 复盘记录。

当前仍未确认的实现方案包括：具体 LLM provider、数据库类型、登录方案、权限模型细节、RAG / 知识库上传与可见范围、检索失败降级策略、多轮高阶面试策略、暂停 / 继续规则、评分维度和权重、API / 后端框架、导出形态细节、运维 / 部署边界。

### 5.7 W13-B 信息架构与用户旅程待确认项

> 以下问题由 `W13-B` 在补齐一期工作台 IA、页面集合、用户旅程和页面到对象映射时识别。它们不改变 `W13-A` 已确认的一期范围，只影响 `W13-C / W13-D` 的对象模型、页面细化和验收标准。

- `OQ-035`：一期登录账号来源。
- `OQ-036`：一期角色层级。
- `OQ-037`：岗位与简历是否都列表化管理。
- `OQ-038`：复盘记录主组织方式。
- `OQ-039`：评分报告页面形态。
- `OQ-040`：Markdown 导出入口与范围。
- `OQ-041`：工作台首页统计卡片范围。
- `OQ-042`：后续占位能力在导航中的位置。
- `OQ-043`：一期包含 RAG / 知识库能力，已 confirmed。
- `OQ-044`：一期包含多轮高阶面试能力，已 confirmed。
- `OQ-045`：模拟面试模块默认入口是历史所有模拟记录列表，已 confirmed。
- `OQ-046`：模拟记录列表默认筛选范围与权限可见范围。
- `OQ-047`：发起模拟面试是否必须先选择岗位和简历。
- `OQ-048`：RAG / 知识库上传能力与个人 / 团队 / 公共可见范围。
- `OQ-049`：RAG 无命中或检索失败时是否允许继续面试。
- `OQ-050`：多轮高阶面试策略类型和结束条件。
- `OQ-051`：多轮高阶面试是否允许中途暂停 / 继续。

## 6. 使用说明

- 问题确认后，应将状态更新为 `confirmed`，并同步回写受影响文档。
- 若某问题暂未正式确认，但已允许本轮按默认口径继续推进，可在总控轮次中临时标记为 `proposed-default`，并同步回写相关文档。
- 若某问题不再适用，应标记为 `superseded`，并补充替代口径。
- 总控 Codex 每轮至少要检查：
  - 高优未解问题是否变化
  - 哪些问题已足以从 `open` 转为 `proposed-default`
  - 哪些问题若被冻结，能够显著提升模块成熟度推进速度

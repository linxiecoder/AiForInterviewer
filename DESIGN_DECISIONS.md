# AI 模拟面试 P1 设计决策

## 1. 文档定位

- 本文档用于记录全局级设计决策、当前口径和后续回写动作。
- 决策状态使用：`proposed`、`confirmed`、`superseded`、`rejected`、`needs-review`。

## 2. 决策表

| 决策 ID | 决策 | 状态 | 当前口径 | 影响范围 | 后续动作 |
| --- | --- | --- | --- | --- | --- |
| DD-001 | 文档体系采用 `global -> module -> subtask` 分层 | confirmed | 全局文档负责约束与导航，模块文档承接设计，子任务文档承接实施准备 | 全局 | 所有新增文档继续遵循该分层 |
| DD-002 | 原始设计稿与原始实现计划保留为上游源文档 | confirmed | `docs/superpowers/specs/...` 与 `docs/superpowers/plans/...` 不承担逐轮回写 | 全局 | 后续回写进入根目录全局文档与 `docs/modules/` |
| DD-003 | 单次实施单位限定为一个子任务 | confirmed | 只有单个 `SUBTASK_IMPLEMENTATION.md` 达到可实施后，才进入代码执行 | 全局实施流程 | 在任务索引与成熟度文档中持续约束 |
| DD-004 | 目标产品代码结构默认采用 monorepo | needs-review | 当前仓库继续以“根目录全局文档 + `docs/` + `tools/doc_governor/` + `tests/doc_governor/`”作为治理与工具布局；`W13-A` 已确认一期 MVP 必须是工作台级并包含服务端能力，但是否创建 `apps/api/**` / `infra/**`、采用何种 API / 后端框架、数据库与部署边界仍未确认；当前暂停代码开发 | M01-M10 | `W13-C` 输出 API / 后端框架、数据库与服务端保存方案确认卡后再决定 |
| DD-005 | 默认技术栈采用 Next.js + FastAPI | proposed | Web 负责工作台与交互，API 负责鉴权、领域服务与 AI 编排 | M01-M10 | 待 M01-M03 细化后收敛 |
| DD-006 | 文档默认使用中文 | confirmed | 文档主体、界面文案和说明均使用中文，技术标识保持英文 | 全局 | 受 [AGENTS.md](AGENTS.md) 与 [docs/project-language-rules.md](docs/project-language-rules.md) 约束 |
| DD-007 | Markdown 预览与导出共用同一渲染链 | needs-review | `W13-A` 只确认一期导出采用复制 / Markdown 下载，不做完整 PDF；Markdown 预览、Markdown 下载、复制内容和未来 PDF 是否共用同一渲染链仍未确认 | M03 | `W13-D` 输出导出形态细节确认卡后再决定 |
| DD-008 | Search snapshot 首轮仅做导入，不做在线抓取 | proposed | P1 聚焦导入与引用，不承担抓取链路 | M06、M10 | 待 OQ-011、OQ-018 确认 |
| DD-009 | 打磨主题推荐首轮优先采用规则推荐 | proposed | 先保证可解释和可验证，再考虑 LLM 混合推荐 | M07 | 待 OQ-013 确认 |
| DD-010 | 模型推荐来源首轮采用本地 catalog / seed | proposed | 管理台不承担在线同步，先沉淀本地配置能力 | M10 | 待 OQ-017 确认 |
| DD-011 | 平台基线首轮只冻结根目录最小脚本、health check 与验证入口 | proposed | 默认冻结 `dev:web` / `dev:api` / `test:web` / `test:api`、`GET /api/v1/health -> 200 {"status":"ok"}`、API=`pytest`、Web=`vitest`，CI 只冻结 API/Web 两类最小校验 lane，不扩张为完整流水线矩阵 | M01、M10（直接），M02、M03（间接） | 待 OQ-019 确认 |
| DD-012 | Web i18n 首轮只冻结最小共享契约，不冻结完整架构 | proposed | 统一 `apps/web/src/i18n/**` + `getMessages(locale)` 入口；locale seed 固定为 `zh-CN` / `en-US`，默认 locale=`zh-CN`；切换由 layout / App Shell 统一解析；fallback 固定为“请求 locale -> `zh-CN` -> 记录缺失 key”；namespace 只冻结“共享壳层一层、业务页面一层”的最小边界 | M01、M02、M03（直接），M04-M10（间接） | 待 OQ-022 确认 |
| DD-013 | 共享页面原语首轮只冻结最小语义对象模型与职责边界 | proposed | 采用方案 B：`PageHeader` 只承载标题、说明、主动作和次动作；Dashboard 摘要区独立承载 `status_badge`、`updated_at`、`summary_items` 与 `loading / ready / empty / error` 最小状态表达，不扩张为完整设计系统 props catalog | M01、M02、M03（直接），后续 Dashboard 页面（间接） | 待 OQ-020 确认 |
| DD-014 | 列表查询状态采用 state-first + adapter 口径 | proposed | 共享 `ListQueryState` 作为 canonical state；页面容器负责 state / URL / request adapter；共享列表原语不直接耦合 router；服务端列表接口遵循统一最小 query 映射与分页响应骨架 | M01、M02、M03（直接），M04-M10（间接） | 待 OQ-021 确认 |
| DD-015 | W10 曾采用“最小功能切片优先”并冻结首切片 | superseded | W10 首切片固定为“岗位 JD 手工输入 + 简历 Markdown 粘贴/编辑 -> 生成首轮模拟面试问题 -> 记录 1 轮问答 -> 输出简版反馈摘要”；该口径已经被 `DD-018` 的工作台级一期 MVP 重新定义取代，不能再作为当前一期 MVP 范围 | W10 历史原型 | 保留为历史记录；后续以 `DD-018` 和 `DD-019` 作为当前范围口径 |
| DD-016 | W10 首切片关系层固定为 `RQ01 -> M03 / M04 / M06 / M07 (+ 条件性 M01)` | superseded | 该关系层只解释 W10 原型探索如何从 `RQ01` 落到最小 mock 原型，不再作为一期工作台 MVP 的模块关系依据；服务端历史、复盘、真实 LLM、登录 / 权限、服务端保存和 `0-100` 多维评分需要在 W13 后续设计中重新建模 | W10 历史原型、W13 后续设计输入 | `W13-B / W13-C / W13-D` 重新补工作台 IA、对象模型、用户旅程和 MVP DoD |
| DD-017 | `W10-D` 采用“首切片最小 Web 原型探索”闸门 | superseded | W10 允许过 `apps/web/**` 最小 mock 原型探索，但 W13-A 已确认该原型只保留为原型探索证据，不直接扩展为正式一期 MVP；其 mock LLM、无登录、会话内临时数据、无数值评分、不导出的边界不得继续前推为当前一期 MVP | `apps/web/**` 原型、W10 历史记录 | 后续若复用任何交互或组件，必须先经 W13 设计文档重新裁剪和用户确认 |
| DD-018 | 一期 MVP 重新定义为“工作台级 MVP” | confirmed | 用户确认组合 `1B2C3C4C5C6C7B8A9B10B11B12B` 已把一期 MVP 范围冻结到工作台级：必须包含服务端历史记录 / 复盘记录、真实 LLM、完整登录 / 权限、简历与面试记录服务端保存、完整 `0-100` 多维评分、复制 / Markdown 下载导出、RAG / 知识库、多轮高阶面试，以及模拟记录列表优先入口；完整 PDF 不进入一期导出范围 | 全局产品范围、M02、M03、M04、M05、M06、M07、M08、M09、M10 | 先补 `W13-B` 工作台 IA 与用户旅程、`W13-C` 对象模型 / 权限 / 保存 / RAG / 多轮 / LLM / API 决策、`W13-D` 评分 / 复盘 / 导出与 MVP DoD；具体实现方案仍需后续确认 |
| DD-019 | W10 `apps/web/**` 原型降级为参考证据并暂停代码开发 | confirmed | 当前 `apps/web/**` 原型仅作为原型探索参考证据，不作为正式一期 MVP 开发起点；当前暂停代码开发，直到 `W13-B / W13-C / W13-D` 完成并经用户再次确认前，不允许继续扩 `apps/web/**`、创建 `apps/api/**`、接真实 LLM、做数据库、登录、评分或后端实现 | 当前推进路径、`apps/web/**`、后续窗口 | 本轮只写回文档和范围冻结草案；后续先补工作台 IA、对象模型、用户旅程和 MVP DoD |
| DD-020 | W13-B 一期工作台 IA 草案采用“模拟记录列表优先 + 岗位 / 简历 / 知识库 / 多轮策略 -> 面试台 -> 评分复盘 -> 回到记录列表”主闭环 | proposed | `W13-B` 已更新 `docs/superpowers/plans/2026-04-25-workbench-mvp-ia-user-journey.md`，将一期必须页面收敛为登录页、工作台首页、岗位列表 / 新建岗位、简历列表 / 新建简历、模拟记录列表、发起模拟面试页、面试台、RAG / 知识库页面、多轮高阶面试策略入口、评分 / 反馈详情、历史记录 / 复盘详情、复制 / Markdown 下载入口和账号 / 权限入口；资产库、训练中心、管理台、高级报表、更完整导出、运维 / 配置仍作为后续占位 | W13-B、W13-C、W13-D、全局产品 IA | 用户确认 `OQ-046` 至 `OQ-051` 等细节后，再由 `W13-C / W13-D` 吸收为对象模型、评分复盘导出和 MVP DoD 输入 |
| DD-021 | 一期 MVP 包含 RAG / 知识库能力 | confirmed | 用户已确认 RAG / 知识库进入一期 MVP；一期 IA 中必须包含知识库入口、发起模拟面试时选择知识库上下文、面试台展示 RAG 引用 / 证据、复盘详情展示引用来源。知识库上传、个人 / 团队 / 公共可见范围、检索失败降级和引用回溯细节仍未确认 | M05、M06、M08、M10、W13-B、W13-C、W13-D | `W13-C` 补对象模型、权限、检索与引用边界确认卡；`W13-D` 补复盘和评分引用展示验收 |
| DD-022 | 一期 MVP 包含多轮高阶面试能力 | confirmed | 用户已确认多轮高阶面试进入一期 MVP；一期 IA 中必须包含发起模拟面试时的多轮策略选择、面试台轮次 / 追问 / 上下文展示、每轮结果进入评分和复盘、模拟记录列表展示轮次与策略。固定轮次、岗位驱动、弱项驱动、暂停 / 继续和结束条件仍未确认 | M06、M07、M08、M09、W13-B、W13-C、W13-D | `W13-C` 补 `InterviewRound`、`InterviewTurn`、`RoundEvaluation` 和状态机；`W13-D` 补每轮评价进入总评分和复盘的验收 |
| DD-023 | 模拟面试模块默认入口为历史模拟记录列表 | confirmed | 用户已确认模拟面试模块默认入口是当前用户权限范围内可见的历史所有模拟记录 / 复盘记录列表；发起模拟面试是列表主操作，面试完成后必须回写历史记录 / 复盘记录。普通用户默认看自己的记录，管理员或有权限角色可看团队 / 组织范围记录，具体权限细节交 `W13-C` | M02、M06、M08、W13-B、W13-C、W13-D | `W13-C` 补记录列表查询、权限过滤、状态机和归档 / 删除边界；`W13-D` 补列表、复盘、评分和导出 DoD |

## 3. 使用说明

- 新增全局级关键口径时，应先补充本表，再更新相关模块文档。
- 决策状态变化后，应同步回写 `TECHNICAL_STANDARDS.md`、`OPEN_QUESTIONS.md` 和 `DOCUMENT_PROGRESS.md`。

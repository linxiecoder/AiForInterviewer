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
| DD-004 | 目标产品代码结构默认采用 monorepo | proposed | 当前仓库继续以“根目录全局文档 + `docs/` + `tools/doc_governor/` + `tests/doc_governor/`”作为治理与工具布局；`W10-A` 当前不创建业务代码目录；若后续进入业务代码实施，默认目录形态为 `apps/web`、`apps/api`、`infra`，且需待 `W10-B / W10-C` 完成边界与关系补齐后再判定 | M01-M10 | 待 OQ-001 确认后更新为 confirmed |
| DD-005 | 默认技术栈采用 Next.js + FastAPI | proposed | Web 负责工作台与交互，API 负责鉴权、领域服务与 AI 编排 | M01-M10 | 待 M01-M03 细化后收敛 |
| DD-006 | 文档默认使用中文 | confirmed | 文档主体、界面文案和说明均使用中文，技术标识保持英文 | 全局 | 受 [AGENTS.md](AGENTS.md) 与 [docs/project-language-rules.md](docs/project-language-rules.md) 约束 |
| DD-007 | Markdown 预览与导出共用同一渲染链 | proposed | 避免预览与导出结果不一致 | M03 | 待 OQ-006 确认 |
| DD-008 | Search snapshot 首轮仅做导入，不做在线抓取 | proposed | P1 聚焦导入与引用，不承担抓取链路 | M06、M10 | 待 OQ-011、OQ-018 确认 |
| DD-009 | 打磨主题推荐首轮优先采用规则推荐 | proposed | 先保证可解释和可验证，再考虑 LLM 混合推荐 | M07 | 待 OQ-013 确认 |
| DD-010 | 模型推荐来源首轮采用本地 catalog / seed | proposed | 管理台不承担在线同步，先沉淀本地配置能力 | M10 | 待 OQ-017 确认 |
| DD-011 | 平台基线首轮只冻结根目录最小脚本、health check 与验证入口 | proposed | 默认冻结 `dev:web` / `dev:api` / `test:web` / `test:api`、`GET /api/v1/health -> 200 {"status":"ok"}`、API=`pytest`、Web=`vitest`，CI 只冻结 API/Web 两类最小校验 lane，不扩张为完整流水线矩阵 | M01、M10（直接），M02、M03（间接） | 待 OQ-019 确认 |
| DD-012 | Web i18n 首轮只冻结最小共享契约，不冻结完整架构 | proposed | 统一 `apps/web/src/i18n/**` + `getMessages(locale)` 入口；locale seed 固定为 `zh-CN` / `en-US`，默认 locale=`zh-CN`；切换由 layout / App Shell 统一解析；fallback 固定为“请求 locale -> `zh-CN` -> 记录缺失 key”；namespace 只冻结“共享壳层一层、业务页面一层”的最小边界 | M01、M02、M03（直接），M04-M10（间接） | 待 OQ-022 确认 |
| DD-013 | 共享页面原语首轮只冻结最小语义对象模型与职责边界 | proposed | 采用方案 B：`PageHeader` 只承载标题、说明、主动作和次动作；Dashboard 摘要区独立承载 `status_badge`、`updated_at`、`summary_items` 与 `loading / ready / empty / error` 最小状态表达，不扩张为完整设计系统 props catalog | M01、M02、M03（直接），后续 Dashboard 页面（间接） | 待 OQ-020 确认 |
| DD-014 | 列表查询状态采用 state-first + adapter 口径 | proposed | 共享 `ListQueryState` 作为 canonical state；页面容器负责 state / URL / request adapter；共享列表原语不直接耦合 router；服务端列表接口遵循统一最小 query 映射与分页响应骨架 | M01、M02、M03（直接），M04-M10（间接） | 待 OQ-021 确认 |
| DD-015 | 下一轮先采用“最小功能切片优先”并冻结首个 MVP 切片 | confirmed | 首切片固定为“岗位 JD 手工输入 + 简历 Markdown 粘贴/编辑 -> 生成首轮模拟面试问题 -> 记录 1 轮问答 -> 输出简版反馈摘要”；直接设计范围限定为 `M03 / M04 / M06 / M07`，`M01` 仅作为条件性最小壳层支撑，`M02 / M05 / M08 / M09 / M10` 暂不进入首切片 | 当前推进路径 | `W10-B` 细化文档边界与验收口径，`W10-C` 补齐关系映射，`W10-D` 仅在条件满足后再判断是否需要最小代码骨架 |

## 3. 使用说明

- 新增全局级关键口径时，应先补充本表，再更新相关模块文档。
- 决策状态变化后，应同步回写 `TECHNICAL_STANDARDS.md`、`OPEN_QUESTIONS.md` 和 `DOCUMENT_PROGRESS.md`。

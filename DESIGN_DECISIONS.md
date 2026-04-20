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
| DD-004 | 仓库结构默认采用 monorepo | proposed | 默认目录形态为 `apps/web`、`apps/api`、`infra` | M01-M10 | 待 OQ-001 确认后更新为 confirmed |
| DD-005 | 默认技术栈采用 Next.js + FastAPI | proposed | Web 负责工作台与交互，API 负责鉴权、领域服务与 AI 编排 | M01-M10 | 待 M01-M03 细化后收敛 |
| DD-006 | 文档默认使用中文 | confirmed | 文档主体、界面文案和说明均使用中文，技术标识保持英文 | 全局 | 受 [AGENTS.md](AGENTS.md) 与 [docs/project-language-rules.md](docs/project-language-rules.md) 约束 |
| DD-007 | Markdown 预览与导出共用同一渲染链 | proposed | 避免预览与导出结果不一致 | M03 | 待 OQ-006 确认 |
| DD-008 | Search snapshot 首轮仅做导入，不做在线抓取 | proposed | P1 聚焦导入与引用，不承担抓取链路 | M06、M10 | 待 OQ-011、OQ-018 确认 |
| DD-009 | 打磨主题推荐首轮优先采用规则推荐 | proposed | 先保证可解释和可验证，再考虑 LLM 混合推荐 | M07 | 待 OQ-013 确认 |
| DD-010 | 模型推荐来源首轮采用本地 catalog / seed | proposed | 管理台不承担在线同步，先沉淀本地配置能力 | M10 | 待 OQ-017 确认 |

## 3. 使用说明

- 新增全局级关键口径时，应先补充本表，再更新相关模块文档。
- 决策状态变化后，应同步回写 `TECHNICAL_STANDARDS.md`、`OPEN_QUESTIONS.md` 和 `DOCUMENT_PROGRESS.md`。

# AI 模拟面试系统当前推进计划

## 1. 文档定位

- 本文档是当前仓库推进入口，只保留当前阶段、事实源、阻断项和下一步。
- 历史治理轮次、W10 原型探索和完整确认卡正文保留在 `EXECUTION_LOG.md` 或 Git 历史中，不在本文档重复展开。
- 当前仓库仍以设计文档、治理状态、`doc_governor` 工具链和测试验证为主；不是可直接进入业务代码实施的 monorepo 实现仓库。

## 2. 当前阶段

- 当前阶段：`W13-E2 / State Remap dry-run`，吸收用户已确认的 W13-E 推荐组合，检查 `WT13-xx` 状态层兼容性，细化旧 `STxx_*` superseded 映射，并建立长期 backlog-roadmap。
- 当前窗口：`W13-E2`，只做状态层 dry-run、任务 ID 约束检查、旧 `STxx_*` 映射方案和项目待办路线图；不修改 `DOC_STATE.yaml`，不进入实现。
- 代码开发状态：暂停。不得扩展 `apps/web/**`，不得创建 `apps/api/**`、`infra/**`，不得接真实 LLM、数据库、登录、评分、RAG、多轮、复盘、导出、薄弱项、训练抽屉、资产库或后端实现。
- W10 `apps/web/**` 原型只作为参考证据，不是正式一期 MVP 起点。

## 3. 当前唯一事实源

| 内容类别 | 唯一事实源 |
| --- | --- |
| 一期 MVP 范围 | `docs/superpowers/plans/2026-04-25-workbench-mvp-scope.md` |
| IA / 用户旅程 | `docs/superpowers/plans/2026-04-25-workbench-mvp-ia-user-journey.md` |
| 对象模型 / RAG / 多轮 / 后端边界 | `docs/superpowers/plans/2026-04-25-workbench-mvp-object-model-rag-multiround-backend.md` |
| 评分 / 复盘 / 导出 / DoD | `docs/superpowers/plans/2026-04-25-workbench-mvp-scoring-review-export-dod.md` |
| 任务重映射草案 | `docs/superpowers/plans/2026-04-25-workbench-mvp-task-remap.md` |
| 待办与路线图清单 | `docs/superpowers/plans/2026-04-25-workbench-mvp-backlog-roadmap.md` |
| 决策索引 | `DESIGN_DECISIONS.md` |
| OQ / MQ 归并入口 | `OPEN_QUESTIONS.md` |
| 历史执行记录 | `EXECUTION_LOG.md` |

## 4. 当前 confirmed 主口径

- 一期 MVP 是工作台级，包含服务端历史 / 复盘记录、真实 LLM、完整登录 / 权限、简历与面试记录服务端保存、完整 `0-100` 多维评分、复制 / Markdown 下载、RAG / 知识库和多轮高阶面试。
- 模拟面试默认入口是历史模拟记录列表；可从岗位详情或模拟面试模块发起；发起时选择岗位、简历、模式；系统整理参考材料包并生成策略与首题。
- 打磨模式由 `ProgressTree` 驱动，用户决定继续或结束；压力面模式由 `InterviewQuestionSet` 驱动，题目完成后结束；固定 3 轮不再是多轮总规则。
- 真实面试复盘与模拟面试复盘都进入一期复盘设计；复盘、评分、RAG 证据、训练建议和 Markdown 导出以评分 / 复盘 / 导出 / DoD 文档为准。
- `WeaknessItem`、训练抽屉、资产库归档动作和最小资产列表 / 详情进入一期设计闭环。

## 5. 当前主线窗口

| 窗口 | 状态 | 作用 |
| --- | --- | --- |
| W13-B | 已产出，作为当前 IA / 用户旅程事实源 | 维护工作台 IA、模拟记录入口、RAG / 知识库入口、多轮入口和页面流转。 |
| W13-C | 已产出，作为当前对象模型 / RAG / 多轮 / 后端边界事实源 | 维护对象模型、服务端保存、权限、RAG、LLM、多轮状态机和后端边界。 |
| W13-D | 已产出，作为当前评分 / 复盘 / 导出 / DoD 事实源 | 维护评分、复盘、导出、错误态、空状态和 DoD。 |
| W13-Cleanup / W13-FC-RefAudit | 已完成项目级清理 | 清理旧 OQ/MQ、旧 DD、重复确认卡、孤立文档候选和唯一事实源引用。 |
| W13-GOV-MergeArchive | 已完成 | 合并旧实现计划归档、M01-M10 旧 MQ/OQ 标记和模块子文档补链结果；确认剩余归档问题不阻断 W13 后续设计。 |
| W13-StateArchive | 已完成 | 将旧 P1 设计稿从当前 `documents` 受管集合移出并迁入 archive；旧 STxx_* 骨架因仍在状态层和索引层引用，本轮不迁移。 |
| W13-F | 已完成阶段收口核验 | 已验证 W13-D 存在且内容完整，完成 Basic Memory 写回与回读验证；Superpowers / 当前执行计划正文未在本轮扩写。 |
| W13-E | 当前草案已形成 | 已新增任务重映射草案，建立 `WT13-xx` 候选任务树、旧 `STxx_*` 处理策略、模块映射、开窗顺序和 `DOC_STATE.yaml` 后续改造确认卡；仍不放行实现。 |
| W13-E2 | 当前 dry-run 收口 | 已检查 `WT13-xx` 与当前 schema 不直接兼容，旧 `STxx_*` 到 `WT13` 映射草案形成，并新增 backlog-roadmap 作为后续事项追踪清单；仍不写 `DOC_STATE.yaml`。 |

## 6. 当前阻断与风险

- 当前没有 active 产品范围 `open / proposed-default` OQ；`OQ-090~OQ-092` 已按用户确认吸收，`OQ-093` 记录 W13-E3 是否创建 preview YAML / 写入 `DOC_STATE.yaml` 的待确认项。
- `DD-005` 与 `DD-007` 仍为 `needs-review`：后端 FastAPI 与导出形态已 confirmed，但完整 Web framework / 渲染链实现细节不得直接进入代码。
- 正式开窗层仍为空；`TASK_INDEX.md` 仅新增 W13-E 候选任务树摘要，任何实现仍必须等待用户确认、状态层改造和正式开窗。
- 旧实现计划正文已迁移到 `archive/docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md`；原路径只保留跳转说明，不作为当前事实源。
- 旧 P1 设计稿已从 `DOC_STATE.yaml` 当前 `documents` 受管集合移出，并迁移到 `archive/docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md`；原路径只保留跳转说明，不作为当前事实源。
- M01-M10 的旧 MQ/OQ 标记和模块子文档补链已完成第一轮；旧 STxx_* 骨架仍在 `DOC_STATE.yaml`、`TASK_INDEX.md` 和模块索引中保留，当前不得迁移 archive。
- Basic Memory 已完成 W13-F 阶段收口摘要写回并回读验证；W13-E2 本轮不写 Basic Memory，W13-E2 增量如需沉淀由后续专门收口窗口统一写回。
- `DOC_STATE.yaml` 尚未写入 W13 新任务；旧 `STxx_*` 仍留在正式 `subtasks` 容器，后续必须另开 W13-E3 / Preview YAML 或 State Write。
- `WT13-xx` 可作为文档层候选任务域 ID，但当前 `doc_governor` 状态层 `subtasks` key 仍只接受 `STxx_yy` 格式，不能直接写入正式状态层。
- `docs/superpowers/plans/2026-04-25-workbench-mvp-backlog-roadmap.md` 已成为项目待办、状态层后续、二期 / 三期和归档后续事项的持续追踪入口。

## 7. 下一步

1. 用户确认 W13-E3 路径：推荐先创建 preview YAML，不修改正式 `DOC_STATE.yaml`。
2. 若用户确认方案 B，进入 W13-E3 / Preview YAML，验证 `WT13-xx`、状态层兼容 ID / 业务别名和旧 `STxx_*` superseded 表达。
3. 旧 `STxx_*` 骨架迁移需在 `DOC_STATE.yaml`、`TASK_INDEX.md` 与模块索引引用重构后另开窗口。
4. 持续维护 backlog-roadmap，不再把状态层后续、二期 / 三期或归档事项散落在聊天记录中。
5. 在状态层写入 W13 新任务并明确正式开窗前，不进入业务代码实施。

## 8. 验证命令

验证命令以执行窗口的实际输出为准；本文档不再内嵌关键字复扫表达式，避免验证命令本身成为误命中来源。

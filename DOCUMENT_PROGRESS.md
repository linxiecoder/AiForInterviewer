# AI 模拟面试 P1 文档进展

## 1. 文档定位

- 本文档用于记录当前文档治理进展摘要和历史归档入口。
- 本文档不再承载完整产品事实、完整 OQ/MQ 明细、完整确认卡正文或模块放行判断正文。
- 当前产品事实以 `PLAN_LATEST.md` 和四份 W13 唯一事实源为准。
- 当前 OQ / MQ 归并状态以 `OPEN_QUESTIONS.md` 为准。
- 当前 DD 状态以 `DESIGN_DECISIONS.md` 为准。
- 当前模块成熟度以 `DOCUMENT_MATURITY.md` 的当前摘要为准。

## 2. 当前阶段摘要

- 当前阶段：`W13-E2 / State Remap dry-run`，吸收用户已确认的 W13-E 推荐组合，检查 `WT13-xx` 状态层兼容性，细化旧 `STxx_*` superseded 映射，并建立长期 backlog-roadmap。
- 当前窗口：`W13-E2`。
- 代码开发状态：暂停。
- 当前不允许扩展 `apps/web/**`，不允许创建 `apps/api/**` / `infra/**`，不允许接真实 LLM、数据库、登录、评分、RAG、多轮、复盘、导出、薄弱项、训练抽屉、资产库或后端实现。
- 正式开窗层：为空；本轮仅形成 dry-run 结论、映射草案和待办路线图，不写入 `DOC_STATE.yaml`。
- 当前没有可直接进入代码实施的子任务。

## 3. 当前 confirmed 摘要

- `FC-01~FC-19` 已完成用户确认。
- `OPEN_QUESTIONS.md` 已回压 W13 产品事实为 confirmed / historical 归并索引；当前 active 产品范围 `open=0`，`OQ-090~OQ-092` 已按用户确认吸收，`OQ-093` 作为 W13-E3 preview / state write 待确认项。
- 一期 MVP 是工作台级，不再是 W10 首切片。
- W10 `apps/web/**` 原型只作为参考证据，不作为正式一期 MVP 起点。
- 一期包含服务端历史 / 复盘记录、真实 LLM、完整登录 / 权限、服务端保存、完整 `0-100` 多维评分、复制 / Markdown 下载、RAG / 知识库和多轮高阶面试。
- 模拟面试模块默认入口是历史模拟记录列表；发起模拟面试从记录列表进入，面试完成后回写历史记录 / 复盘。
- `FC-06D`：压力面模式支持按岗位自动生成默认题型组合，并允许用户手动调整；打磨模式支持用户自定义主题 / 题型，并可结合岗位与薄弱项自动推荐，但不强制固定题组。
- `FC-11D`：真实面试输入支持用户上传逐字稿原文，不要求用户先按题目拆分；系统由大模型自动识别问题与回答边界，再输出逐题拆解复盘；若切分置信度不足，提示用户校对。

## 4. 当前唯一事实源

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
| 技术标准摘要 | `TECHNICAL_STANDARDS.md` |
| 历史执行记录 | `EXECUTION_LOG.md` |

## 5. 当前阻断与风险

- `TASK_INDEX.md` 已写入 W13 候选任务树摘要；`WT13-xx` 已确认作为文档层候选任务域命名，但尚未成为 `DOC_STATE.yaml` 正式任务，也不具备实施条件。
- `MODULE_INDEX.md` 已写入 W13 候选任务域到 M01-M10 的映射摘要；M01-M10 已完成第一轮旧 MQ/OQ 标记和子文档补链，但这不等于模块成熟度升级。
- `DD-005` 与 `DD-007` 仍为 `needs-review`：后端 FastAPI 和导出形态已 confirmed，但完整 Web framework / 渲染链实现细节不能直接进入代码。
- `M01-M03` 仍不因 FC confirmed 自动升级为 L5 或正式候选。
- `M04-M10` 仍多为 L1 / 骨架级，需要后续模块窗口按 W13 唯一事实源继续补齐模块级设计。
- `docs/modules/**` 中仍存在旧设计稿、旧实现计划路径引用和历史 OQ/MQ/ST/MT 引用；其中历史引用可保留，但不能作为当前事实源。
- 旧 P1 设计稿已从当前 `documents` 受管集合移出并迁入 archive；旧 `STxx_*` 骨架仍被 `DOC_STATE.yaml` 和索引层引用，本轮不迁移 archive。
- W13-E 的任务 ID 命名、旧 `STxx_*` 后续处理和先做 W13-E2 dry-run 已由用户确认；下一步是否创建 preview YAML 或写入正式 `DOC_STATE.yaml` 仍需用户确认。

## 6. 当前完成事项

- 已完成 `validate-state` / `evaluate-state` 开始前验证，状态层仍为 `ok=true` 且 `documents_blocked_count=0`。
- 已扫描根目录与 `docs/**` 下全部 Markdown 文档。
- 已确认 `FC-01~FC-19` 在项目级文档中有 confirmed 或 historical 写回位置。
- 已将 `DOCUMENT_PROGRESS.md` 从旧进展正文降级为当前摘要 + 历史归档入口。
- 已将 W10 首切片、旧 OQ/MQ、旧 proposed-default、固定 3 轮等内容从当前事实源判断中剥离。
- 已确认旧实现计划正文迁移到 `archive/docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md`，原路径保留跳转说明。
- 已确认旧 P1 设计稿迁移到 `archive/docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md`，原路径保留跳转说明，`DOC_STATE.yaml` 当前 `documents` 受管集合不再登记 `DOC-SPEC-P1`。
- 已汇总 A/C1/C2/C3：M01-M10 的旧 MQ/OQ 状态标记和子文档父模块补链已完成第一轮，未迁移模块文档到 archive。
- 已完成 W13-F 阶段收口核验：W13-D 文件存在且覆盖评分、复盘、导出、错误态 / 空状态和一期 MVP DoD；Basic Memory 已写入阶段收口摘要并回读验证。
- 已完成 W13-E 任务重映射草案：新增 `docs/superpowers/plans/2026-04-25-workbench-mvp-task-remap.md`，形成 `WT13-01~WT13-25` 候选任务树、旧 `STxx_*` 处理策略、模块映射、开窗顺序、窗口边界模板和状态层后续改造方案。
- 已完成 W13-E2 状态层 dry-run 文档收口：确认 `WT13-xx` 不能直接作为当前 `DOC_STATE.yaml.subtasks` key，形成旧 `STxx_*` 到 `WT13` 映射草案，并新增 `docs/superpowers/plans/2026-04-25-workbench-mvp-backlog-roadmap.md` 作为长期待办与路线图入口。

## 7. 历史归档说明

- W10 首切片、阶段 3 白名单治理、模块最低位压缩、`MR-*` / `RV-*` / `GC-*` 细节均属于历史治理过程。
- 上述历史过程不再作为当前一期 MVP 范围、模块优先级、正式开窗或 implementation readiness 的依据。
- 需要追溯历史过程时，优先查看：
  - `EXECUTION_LOG.md`
  - Git 历史
  - 对应模块目录下的 `MODULE_EXECUTION_LOG.md`

## 8. 下一步建议

1. 先由用户确认 W13-E3 是否采用 preview YAML 路径；推荐方案是创建 preview YAML，不修改正式 `DOC_STATE.yaml`。
2. 若后续要迁移旧 `STxx_*` 骨架，必须先重构 `DOC_STATE.yaml`、`TASK_INDEX.md` 和模块索引中的正式引用关系。
3. 开模块同步窗口，优先同步 `M06 / M08 / M09 / M05 / M10` 中与多轮、复盘、评分、训练、RAG、资产库和管理台入口相关的 W13 confirmed 范围。
4. 持续维护 backlog-roadmap 中的状态层、实现前置、二期 / 三期和归档待办。
5. 在状态层写入 W13 新任务并明确正式开窗前，继续暂停代码实施。

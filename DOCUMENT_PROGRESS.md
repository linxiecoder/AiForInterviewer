# AI 模拟面试 P1 文档进展

## 1. 文档定位

- 本文档用于记录当前文档治理进展摘要和历史归档入口。
- 本文档不再承载完整产品事实、完整 OQ/MQ 明细、完整确认卡正文或模块放行判断正文。
- 当前产品事实以 `PLAN_LATEST.md` 和四份 W13 唯一事实源为准。
- 当前 OQ / MQ 归并状态以 `OPEN_QUESTIONS.md` 为准。
- 当前 DD 状态以 `DESIGN_DECISIONS.md` 为准。
- 当前模块成熟度以 `DOCUMENT_MATURITY.md` 的当前摘要为准。

## 2. 当前阶段摘要

- 当前阶段：`W13-E4-E / Stage3 Preview` 已完成；已新增并验证 Stage3 Preview YAML，正式 `DOC_STATE.yaml` 未修改。
- 当前边界：本轮只做 Preview YAML 创建、验证、对比和分析；不正式移出旧 `STxx_*`，不正式改写 `RQ01.facts.task_ids`，不进入实现。
- 代码开发状态：暂停。
- 当前不允许扩展 `apps/web/**`，不允许创建 `apps/api/**` / `infra/**`，不允许接真实 LLM、数据库、登录、评分、RAG、多轮、复盘、导出、薄弱项、训练抽屉、资产库或后端实现。
- 正式开窗层：为空；本轮只完成 Stage3 Preview 创建与验证，不修改正式 `DOC_STATE.yaml`，不生成 implementation packet，不进入实现。
- 当前没有可直接进入代码实施的子任务。

## 3. 当前 confirmed 摘要

- `FC-01~FC-19` 已完成用户确认。
- `OPEN_QUESTIONS.md` 已回压 W13 产品事实为 confirmed / historical 归并索引；当前 active 产品范围 `open=0`，`OQ-097~OQ-099` 的 preview 路径已完成验证，但正式 Stage 3 是否执行仍需用户确认。
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
| 状态层 Preview YAML | `docs/superpowers/plans/2026-04-25-workbench-mvp-doc-state-preview.yaml` |
| State Write 分阶段计划 | `docs/superpowers/plans/2026-04-25-workbench-mvp-state-write-plan.md` |
| State Write 阶段 1 变更与回退说明 | `docs/superpowers/plans/2026-04-25-workbench-mvp-state-write-stage1.md` |
| State Write 阶段 2 变更与回退说明 | `docs/superpowers/plans/2026-04-25-workbench-mvp-state-write-stage2.md` |
| State Write 阶段 3 dry-run 与影响分析 | `docs/superpowers/plans/2026-04-25-workbench-mvp-state-write-stage3-dry-run.md` |
| Stage3 Preview YAML | `docs/superpowers/plans/2026-04-25-workbench-mvp-doc-state-stage3-preview.yaml` |
| 待办与路线图清单 | `docs/superpowers/plans/2026-04-25-workbench-mvp-backlog-roadmap.md` |
| 决策索引 | `DESIGN_DECISIONS.md` |
| OQ / MQ 归并入口 | `OPEN_QUESTIONS.md` |
| 技术标准摘要 | `TECHNICAL_STANDARDS.md` |
| 历史执行记录 | `EXECUTION_LOG.md` |

## 5. 当前阻断与风险

- `TASK_INDEX.md` 已同步 `ST13_01~ST13_25` 正式状态层入口与 `WT13-xx` alias，并同步旧 `STxx_*` 已通过 facts 表达 historical / superseded；这些入口仍不具备实施条件。
- `MODULE_INDEX.md` 已写入 W13 候选任务域到 M01-M10 的映射摘要；M01-M10 已完成第一轮旧 MQ/OQ 标记和子文档补链，但这不等于模块成熟度升级。
- `DD-005` 与 `DD-007` 仍为 `needs-review`：后端 FastAPI 和导出形态已 confirmed，但完整 Web framework / 渲染链实现细节不能直接进入代码。
- `M01-M03` 仍不因 FC confirmed 自动升级为 L5 或正式候选。
- `M04-M10` 仍多为 L1 / 骨架级，需要后续模块窗口按 W13 唯一事实源继续补齐模块级设计。
- `docs/modules/**` 中仍存在旧设计稿、旧实现计划路径引用和历史 OQ/MQ/ST/MT 引用；其中历史引用可保留，但不能作为当前事实源。
- 旧 P1 设计稿已从当前 `documents` 受管集合移出并迁入 archive；旧 `STxx_*` 骨架仍被 `DOC_STATE.yaml` 和索引层引用，本轮不迁移 archive。
- W13-E 的任务 ID 命名、旧 `STxx_*` 后续处理、先做 W13-E2 dry-run、`OQ-093=B` Preview YAML 和 `OQ-094~OQ-096` State Write 口径均已确认；旧 `STxx_*` 的正式 superseded / historical-reference 表达已在阶段 2 完成，但旧任务仍未移出正式容器。
- `W13-E4-E` 已完成 Stage3 Preview YAML 创建与验证：preview 中旧 `STxx_*` 已从正式 `subtasks` 容器移出，`RQ01.facts.task_ids` 只保留 `ST13_01~ST13_25`；正式状态仍未改写。

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
- 已完成 W13-E4-A State Write 计划窗口：新增 `docs/superpowers/plans/2026-04-25-workbench-mvp-state-write-plan.md`，定义阶段 1 写入 `ST13_01~ST13_25` 且不移除旧 `STxx_*`、阶段 2 标记旧任务 superseded、阶段 3 移出旧任务正式容器、阶段 4 archive 迁移准备，并补充验证矩阵、回退方案、写入草案和用户确认卡。
- 已完成 W13-E4-B State Write 阶段 1：正式 `DOC_STATE.yaml` 已新增 `ST13_01~ST13_25`，`RQ01.facts.task_ids` 已追加新任务，旧 `STxx_*` 保持并存，新增 `docs/superpowers/plans/2026-04-25-workbench-mvp-state-write-stage1.md` 记录变更与回退说明。
- 已完成 W13-E4-C State Write 阶段 2：30 个旧 `STxx_*` 仍保留在正式 `DOC_STATE.yaml.subtasks`，并已在各自 `facts` 中写入 `w13_status=superseded`、`w13_role=historical-reference`、`w13_superseded_by`、`w13_alias_target` 和 `w13_archive_candidate=true`；新增 `docs/superpowers/plans/2026-04-25-workbench-mvp-state-write-stage2.md` 记录变更与回退说明。
- 已完成 W13-E4-D State Write 阶段 3 dry-run：新增 `docs/superpowers/plans/2026-04-25-workbench-mvp-state-write-stage3-dry-run.md`，确认旧 `STxx_*` 仍被索引层全量历史引用，closed round 未直接引用旧 ST；用户已确认在 Stage3 Preview 中验证移除 `RQ01.facts.task_ids` 中旧 `ST01_01`、`ST09_03` 的方案。正式 `DOC_STATE.yaml` 未修改，旧任务未移出。
- 已完成 W13-E4-E Stage3 Preview：新增 `docs/superpowers/plans/2026-04-25-workbench-mvp-doc-state-stage3-preview.yaml`；preview `validate-state / evaluate-state` 均为 `ok=true,error=0,warning=0`，preview `subtasks_blocked_count=25`，未出现 missing reference、stale target、schema error、implementation-ready 误判或 formal window 误开。

## 7. 历史归档说明

- W10 首切片、阶段 3 白名单治理、模块最低位压缩、`MR-*` / `RV-*` / `GC-*` 细节均属于历史治理过程。
- 上述历史过程不再作为当前一期 MVP 范围、模块优先级、正式开窗或 implementation readiness 的依据。
- 需要追溯历史过程时，优先查看：
  - `EXECUTION_LOG.md`
  - Git 历史
  - 对应模块目录下的 `MODULE_EXECUTION_LOG.md`

## 8. 下一步建议

1. 下一步建议由用户确认是否基于 Stage3 Preview 执行正式 Stage 3；确认前不得直接修改正式 `DOC_STATE.yaml`。
2. 若后续要迁移旧 `STxx_*` 骨架，必须先完成阶段 3 正式移出，重构 `DOC_STATE.yaml`、`TASK_INDEX.md` 和模块索引中的正式引用关系。
3. 开模块同步窗口，优先同步 `M06 / M08 / M09 / M05 / M10` 中与多轮、复盘、评分、训练、RAG、资产库和管理台入口相关的 W13 confirmed 范围。
4. 持续维护 backlog-roadmap 中的状态层、实现前置、二期 / 三期和归档待办。
5. 在正式开窗层和 implementation-ready 形成前，继续暂停代码实施。

# AI 模拟面试 P1 文档成熟度

## 1. 文档定位

- 本文档用于登记当前文档体系的成熟度摘要。
- 本文档不再承载完整产品事实、完整 OQ/MQ 正文或历史模块推进长记录。
- 当前产品事实以 `PLAN_LATEST.md` 和四份 W13 唯一事实源为准。
- 当前 OQ / MQ 状态以 `OPEN_QUESTIONS.md` 为准。
- 当前进展摘要以 `DOCUMENT_PROGRESS.md` 为准。

## 2. 成熟度等级定义

| 等级 | 名称 | 说明 | 可作为下游输入 | 可直接用于实施 |
| --- | --- | --- | --- | --- |
| L0 | 未创建 | 文档不存在或仅在索引中占位 | 否 | 否 |
| L1 | 仅有骨架 | 只有标题、章节或极少量提示信息 | 否 | 否 |
| L2 | 初稿 | 已有初步内容，但边界、输入输出、依赖和问题仍不稳定 | 否 | 否 |
| L3 | 待澄清 | 结构基本完整，但仍有会阻塞下游的关键问题 | 否 | 否 |
| L4 | 可评审 | 已具备稳定结构，可用于组织评审，但尚未细化到实施粒度 | 部分 | 否 |
| L5 | 可作为下游输入 | 已能稳定支撑下游设计或拆分 | 是 | 否 |
| L6 | 可直接用于实施 | 已明确目标、范围、文件边界、实施步骤、验证方式和 DoD | 是 | 是 |
| L7 | 稳定维护 | 已经过多轮使用和回写，只做增量维护 | 是 | 是 |

## 3. 当前全局文档成熟度摘要

| 文档路径 | 当前等级 | 当前角色 | 是否可作为下游输入 | 是否可直接用于实施 |
| --- | --- | --- | --- | --- |
| `AGENTS.md` | L5 | 项目协作入口和索引 | 是 | 否 |
| `docs/DOC_GOVERNANCE.md` | L5 | 人工协作与文档治理总则 | 是 | 否 |
| `PLAN_LATEST.md` | L5 | 当前推进入口和唯一事实源索引 | 是 | 否 |
| `OPEN_QUESTIONS.md` | L5 | OQ / MQ confirmed / historical 归并入口 | 是 | 否 |
| `DESIGN_DECISIONS.md` | L5 | DD confirmed / superseded / needs-review 决策索引 | 是 | 否 |
| `TECHNICAL_STANDARDS.md` | L4 | confirmed 技术标准摘要，仍保留 implementation packet 复核边界 | 部分 | 否 |
| `TASK_INDEX.md` | L4 | 当前任务索引；已吸收 `WT13-xx` 候选任务域命名，但未形成正式开窗或 implementation-ready | 部分 | 否 |
| `MODULE_INDEX.md` | L4 | 当前模块索引；已写入 W13 候选任务域映射，但模块同步仍待后续窗口 | 部分 | 否 |
| `DOCUMENT_PROGRESS.md` | L4 | 当前进展摘要 + 历史归档和补链入口 | 部分 | 否 |
| `DOCUMENT_MATURITY.md` | L4 | 当前成熟度摘要 + 历史归档和补链入口 | 部分 | 否 |
| `EXECUTION_LOG.md` | L4 | 历史执行记录 | 部分 | 否 |
| `docs/superpowers/plans/2026-04-25-workbench-mvp-task-remap.md` | L4 | W13-E / W13-E2 任务重映射与状态层 dry-run 草案，包含候选任务树、旧 ST 映射和状态层后续改造方案 | 部分 | 否 |
| `docs/superpowers/plans/2026-04-25-workbench-mvp-backlog-roadmap.md` | L4 | 项目待办、状态层后续、二期 / 三期和历史归档后续事项追踪清单 | 部分 | 否 |
| `archive/docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md` | L4 | 历史设计稿归档快照 | 部分 | 否 |

## 4. W13 唯一事实源成熟度

| 文档路径 | 当前等级 | 当前角色 | 是否可作为下游输入 |
| --- | --- | --- | --- |
| `docs/superpowers/plans/2026-04-25-workbench-mvp-scope.md` | L5 | 一期 MVP 范围唯一事实源 | 是 |
| `docs/superpowers/plans/2026-04-25-workbench-mvp-ia-user-journey.md` | L5 | IA / 用户旅程唯一事实源 | 是 |
| `docs/superpowers/plans/2026-04-25-workbench-mvp-object-model-rag-multiround-backend.md` | L5 | 对象模型 / RAG / 多轮 / 后端边界唯一事实源 | 是 |
| `docs/superpowers/plans/2026-04-25-workbench-mvp-scoring-review-export-dod.md` | L5 | 评分 / 复盘 / 导出 / DoD 唯一事实源 | 是 |

## 5. 当前模块成熟度摘要

| 模块 | 当前整体成熟度 | 当前判断 | 是否可进入子任务设计 |
| --- | --- | --- | --- |
| M01 | L4 | 接近候选但未接受；不因 FC confirmed 自动升级 | 否 |
| M02 | L4 | `/members` 共享最小层已确认，但正式开窗层仍为空，权限消费边界仍需模块层复核 | 否 |
| M03 | L4 | 已吸收但未放行；正式开窗层为空、当前阶段关窗、上传 / 导出链依赖未变 | 否 |
| M04 | L1 | 骨架级；旧 OQ/MQ 已标记并补链，仍需按 W13 同步匹配分析、评分证据和训练入口 | 否 |
| M05 | L1 | 骨架级；旧 OQ/MQ 已标记并补链，仍需按 W13 同步 RAG / 知识库、资产归档与 schema 边界 | 否 |
| M06 | L1 | 骨架级；旧 OQ/MQ 已标记并补链，仍需按 W13 同步模拟记录列表、多轮、上下文包与面试台边界 | 否 |
| M07 | L1 | 骨架级；旧 OQ/MQ 已标记并补链，仍需按 W13 同步打磨模式、进展树、题级反馈与训练进展 | 否 |
| M08 | L1 | 骨架级；旧 OQ/MQ 已标记并补链，仍需按 W13 同步真实面试复盘、模拟复盘、逐题拆解与导出 | 否 |
| M09 | L1 | 骨架级；旧 OQ/MQ 已标记并补链，仍需按 W13 同步薄弱项、训练抽屉、消减和停练规则 | 否 |
| M10 | L1 | 骨架级；旧 OQ/MQ 已标记并补链，仍需按 W13 同步管理台入口、模型 catalog、snapshot 与运维边界 | 否 |

## 6. 当前可作为下游输入的文档

- `AGENTS.md`
- `docs/DOC_GOVERNANCE.md`
- `PLAN_LATEST.md`
- `OPEN_QUESTIONS.md`
- `DESIGN_DECISIONS.md`
- 四份 W13 唯一事实源文档
- `docs/superpowers/plans/2026-04-25-workbench-mvp-task-remap.md`
- `docs/superpowers/plans/2026-04-25-workbench-mvp-backlog-roadmap.md`

说明：
- 上述“可作为下游输入”仅表示可用于继续做文档设计、任务重映射和模块同步。
- 这不等于可以直接进入代码实施。
- 当前没有任何模块或子任务被登记为可直接实施。
- `W13-E` 任务重映射草案和 W13-E2 backlog-roadmap 可作为 W13-E3 / Preview YAML 的输入，但不能替代 `DOC_STATE.yaml` 正式状态。

## 7. 当前可直接用于实施的子任务

- 暂无。

## 8. 历史归档说明

- W10 首切片、阶段 3 白名单治理、模块最低位压缩、`MR-*` / `RV-*` / `GC-*` 细节均属于历史治理过程。
- 上述历史内容不再作为当前一期 MVP 范围、模块优先级、正式开窗或 implementation readiness 的依据。
- 旧实现计划正文已迁移到 `archive/docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md`；原路径只保留跳转说明。
- 旧 P1 设计稿已迁移到 `archive/docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md`；原路径只保留跳转说明，`DOC_STATE.yaml` 当前 `documents` 受管集合不再登记 `DOC-SPEC-P1`。
- 旧 STxx_* 骨架当前通过 `DOC_STATE.yaml`、`TASK_INDEX.md` 和模块索引保留为状态层 / 结构参考；用户已确认后续映射为 `superseded`，但未写入正式状态层，不在本轮迁移 archive。
- 需要追溯历史判断时，优先查看 `EXECUTION_LOG.md`、Git 历史和对应模块目录下的 `MODULE_EXECUTION_LOG.md`。

## 9. 下一等级所需动作

1. 用户需要确认 W13-E3 是否先创建 preview YAML；推荐不直接写正式 `DOC_STATE.yaml`。
2. `TASK_INDEX.md` 需要在状态层方案确认后把候选任务树升级为正式任务 ID、允许修改范围、前置条件和验证方式。
3. `MODULE_INDEX.md` 需要在模块同步窗口后回写 W13 模块优先级，而不是继续沿用 W10 首切片顺序。
4. `M05 / M06 / M08 / M09 / M10` 需要优先按 confirmed 范围补齐模块级设计，尤其是 RAG、多轮、复盘、训练、资产归档和管理台入口。
5. 旧 `STxx_*` 骨架如需归档，必须先完成状态层 / 任务索引 / 模块索引的统一重映射；确认前不直接移动这些文档。
6. 正式开窗层写入前，所有子任务仍不得进入实施准备或代码实施。

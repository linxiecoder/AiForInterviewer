---
title: 2026-04-25-workbench-mvp-design-canon-plan
type: note
permalink: ai-for-interviewer/archive/docs/superpowers/plans/2026-04-25/2026-04-25-workbench-mvp-design-canon-plan
---

# AI 模拟面试一期工作台 MVP 正式设计文档归位与模块承接计划

## 1. 背景

当前一期工作台 MVP 的核心设计事实源仍位于 `docs/superpowers/plans/**`：

- `docs/superpowers/plans/2026-04-25-workbench-mvp-scope.md`
- `docs/superpowers/plans/2026-04-25-workbench-mvp-ia-user-journey.md`
- `docs/superpowers/plans/2026-04-25-workbench-mvp-object-model-rag-multiround-backend.md`
- `docs/superpowers/plans/2026-04-25-workbench-mvp-scoring-review-export-dod.md`

这些文件已经承载一期工作台 MVP 的正式产品范围、信息架构、对象模型、RAG、多轮、后端边界、评分、复盘、导出和 DoD 事实，不应长期留在计划目录中作为 current fact source。

本计划用于冻结后续一次性实现方案。本文只做依赖分析、迁移方案、文件清单、模块承接方案、引用修正规则、验证命令、回退方案和步骤 2 输入包，不执行正式迁移。

## 2. 用户确认

用户已确认方案 A：完整归位。

整体事项只分两个步骤：

| 步骤 | 目标 | 本轮是否执行 |
| --- | --- | --- |
| 步骤 1 | 计划窗口，只做分析和计划冻结 | 是 |
| 步骤 2 | 实现窗口，一次性完成正式设计归位、模块承接、引用修正、验证和提交 | 否 |

本窗口不创建 `docs/design/workbench-mvp/`，不降级原 W13 plans 文档，不修改模块正文，不修改 `DOC_STATE.yaml`，不打开 formal window，不生成 implementation packet，不进入实现，不写 Basic Memory，不执行 Git 提交或推送。

## 3. 当前 confirmed 事实

步骤 2 不得回退以下事实：

1. 一期 MVP 是 AI 模拟面试工作台级 MVP。
2. 一期包含真实 LLM。
3. 一期包含完整登录 / 权限。
4. 一期包含服务端保存。
5. 一期包含历史模拟记录 / 复盘。
6. 一期包含 RAG / 知识库。
7. 一期包含多轮高阶面试。
8. 多轮面试分为打磨模式和压力面模式。
9. 打磨模式由 `ProgressTree / 进展树` 驱动，用户决定是否结束。
10. 压力面模式由 `InterviewQuestionSet` 驱动，题目完成后结束。
11. 固定 3 轮不是多轮面试总规则，只能作为压力面题组策略候选。
12. 一期包含 `0-100` 多维评分。
13. 一期包含 Markdown 下载 / 复制。
14. 一期包含薄弱项体系、训练抽屉、资产归档。
15. 模拟面试入口是历史模拟记录列表。
16. 从列表或岗位详情发起模拟面试。
17. 面试台是执行页。
18. 完成后回写历史记录与复盘。
19. W10 `apps/web` 仅为参考证据，不作为正式一期 MVP 起点。
20. 旧 P1 / W10 文档已归档或历史化。
21. `ST13_01~ST13_25` 是当前正式任务入口。
22. 当前仍不能进入实现。
23. 当前仍不能生成 implementation packet。
24. 当前仍不能打开 formal window。

## 4. 依赖分析摘要

### 4.1 引用扫描结果

步骤 1 扫描表达式：

```powershell
rg -n "2026-04-25-workbench-mvp-scope|2026-04-25-workbench-mvp-ia-user-journey|2026-04-25-workbench-mvp-object-model-rag-multiround-backend|2026-04-25-workbench-mvp-scoring-review-export-dod|docs/design/workbench-mvp" README.md AGENTS.md PLAN_LATEST.md DOCUMENT_PROGRESS.md DOCUMENT_MATURITY.md TASK_INDEX.md MODULE_INDEX.md OPEN_QUESTIONS.md DESIGN_DECISIONS.md docs
```

命中的主要文件分组如下。

| 分组 | 文件 | 当前含义 | 步骤 2 处理 |
| --- | --- | --- | --- |
| current fact source | `PLAN_LATEST.md`、`DOCUMENT_PROGRESS.md`、`DOCUMENT_MATURITY.md`、`OPEN_QUESTIONS.md`、`DESIGN_DECISIONS.md` | 明确把四份 W13 plans 标为唯一事实源 | 改为 `docs/design/workbench-mvp/`；旧路径只保留为迁移来源 / 历史推进记录 |
| 项目索引 | `AGENTS.md` | 当前索引仍把四份 W13 plans 放在计划区 | 增加正式设计区入口；旧 plans 保留在计划 / 历史推进记录区并标明桥接 |
| 历史跳转 / 旧蓝图 | `docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md`、`docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md` | 旧 P1 文件跳转到 W13 唯一事实源 | 改为跳转到正式设计目录；可保留旧 W13 plans 作为迁移来源说明 |
| 当前仓库执行计划 | `docs/superpowers/plans/2026-04-25-current-repo-execution-plan.md` | 说明旧设计只作历史，当前 W13 事实在四份 plans | 改为正式设计目录；旧 W13 plans 作为历史迁移来源 |
| 原事实源内部互链 | 四份 W13 plans，尤其 `scope.md` 内部链接 | plans 之间互相作为设计正文 | 降级为桥接文档后改为新正式设计链接 |
| task governance context | `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-first-contract-task-packages.md`、`docs/superpowers/plans/st13-task-packages/ST13_20/ST13_20_DESIGN.md`、`ST13_21_DESIGN.md`、`ST13_24_DESIGN.md` | ST13 任务包把四份 W13 plans 当输入事实源 | 使用双引用：正式设计入口 + 原任务治理 / 历史计划来源 |
| module design context | `docs/modules/M01-foundation-and-platform/MODULE_OPEN_QUESTIONS.md`、`M02-identity-and-team/MODULE_OPEN_QUESTIONS.md`、`M03-jobs-resumes-and-documents/MODULE_OPEN_QUESTIONS.md` | 模块内 MQ/OQ 说明当前事实应指向四份 W13 plans | 指向正式设计目录，只保留模块视角摘要；不得复制完整设计正文 |

### 4.2 引用分类

| 引用类型 | 判定规则 | 示例 | 步骤 2 处理 |
| --- | --- | --- | --- |
| current fact source | 文案含“唯一事实源”“当前事实以...为准”“当前产品事实” | `PLAN_LATEST.md`、`OPEN_QUESTIONS.md`、`DOCUMENT_MATURITY.md` | 必须改为 `docs/design/workbench-mvp/` |
| historical / execution trace | 文案说明 W13-A/B/C/D 产出、旧 P1 归档、执行记录 | `EXECUTION_LOG.md`、旧 P1 跳转文件、W13 stage 文档 | 保留旧 plans 路径，但上下文必须明确历史 / 迁移来源 |
| task governance context | 文案描述 ST13 任务包输入、readiness、formal window candidate | ST13 first contract task packages、ST13 双文档 | 双引用：正式设计 + 任务治理文档 |
| module design context | 模块文档用来承接产品事实 | 模块 `MODULE_*` 文档 | 指向正式设计；模块只写摘要和模块影响 |
| backlog / roadmap context | 追踪后续事项、归档、二期三期 | backlog-roadmap | 保留旧 plans 为已迁移来源，新增正式设计待维护规则 |
| 不确定引用 | 无法判断是当前事实还是历史说明 | 后续扫描新增命中 | 放入待复核清单，不强行替换 |

### 4.3 必须替换、保留与双引用

| 处理方式 | 文件或范围 |
| --- | --- |
| 必须改为正式设计路径 | `PLAN_LATEST.md` 当前事实源表、`DOCUMENT_PROGRESS.md` 当前事实源表、`DOCUMENT_MATURITY.md` W13 唯一事实源成熟度表、`OPEN_QUESTIONS.md` 唯一事实源清单、`DESIGN_DECISIONS.md` DD 当前事实引用、`README.md` 当前事实说明、`AGENTS.md` 正式设计入口 |
| 保留旧 plans 路径作为历史记录 | `EXECUTION_LOG.md` 历史轮次、W13 stage 变更说明、旧 P1 跳转页中的迁移来源、Git 历史追溯说明 |
| 双引用 | ST13 任务包、ST13 双文档、backlog-roadmap 中同时需要“正式设计事实源”和“任务治理来源”的段落 |
| 待复核 | 新增扫描命中、相对链接、只写文件名不写完整路径的旧 W13 文档引用 |

### 4.4 双事实源风险

当前双事实源风险集中在四类：

1. 根文档继续把 `docs/superpowers/plans/**` 写成“唯一事实源”。
2. 原 W13 plans 保留完整 current 设计正文，同时新建 `docs/design/workbench-mvp/**`。
3. 模块文档继续引用旧 W13 plans 作为模块设计输入。
4. ST13 任务包只引用旧 plans，不引用正式设计目录，导致 future formal window / packet 输入层级混乱。

步骤 2 必须以“正式设计目录唯一承载 current 设计事实，旧 W13 plans 只承载桥接 / 历史 / 迁移来源”为通过标准。

## 5. 正式设计目录结构

步骤 2 冻结创建目录：

```text
docs/design/workbench-mvp/
```

冻结文件清单：

| 文件 | 来源文档 | 内容边界 | 非目标 | 关联模块 | 关联 ST13 | 后续维护规则 |
| --- | --- | --- | --- | --- | --- | --- |
| `README.md` | 四份 W13 facts source + 本计划 | 正式设计目录定位、文档索引、事实源优先级、与旧 plans / ST13 / 模块文档的关系 | 不承载完整设计正文，不替代 `PLAN_LATEST.md` 或 `DOC_STATE.yaml` | M01-M10 | `ST13_01~ST13_25` | 新增正式设计文档必须先入此索引；旧 plans 不得重新成为 current 设计事实 |
| `scope.md` | `2026-04-25-workbench-mvp-scope.md` | 一期 MVP 范围、当前 / 后续边界、W10 原型定位、登录、权限、服务端保存、真实 LLM、RAG、多轮、评分、导出、薄弱项、训练、资产归档 | 不放入任务包执行计划，不写 formal window 状态，不写 implementation-ready | M01-M10 | 重点 `ST13_01~ST13_04`、`ST13_10~ST13_13`、`ST13_16~ST13_25` | 范围变更必须同步 `OPEN_QUESTIONS.md` / `DESIGN_DECISIONS.md`，不得只改正文 |
| `information-architecture.md` | `2026-04-25-workbench-mvp-ia-user-journey.md` | 工作台 IA、页面集合、历史模拟记录列表入口、发起模拟面试、面试台、RAG / 知识库入口、多轮入口、评分复盘、导出、账号权限旅程 | 不定义后端 schema，不定义接口 contract，不替代模块设计 | M01、M02、M03、M05、M06、M07、M08、M09、M10 | 重点 `ST13_01~ST13_09`、`ST13_14~ST13_19`、`ST13_23` | 页面或旅程变更先更新本文件，再由模块文档承接摘要 |
| `object-model-rag-multiround-backend.md` | `2026-04-25-workbench-mvp-object-model-rag-multiround-backend.md` | 对象模型、权限、服务端保存、RAG / 知识库、多轮、打磨、压力面、复盘、薄弱项、训练、资产归档、LLM、API / 后端边界 | 不写 OpenAPI 文件，不创建 schema / DTO / migration，不替代 `DOC_STATE.yaml` | M01-M10 | 重点 `ST13_01`、`ST13_03~ST13_12`、`ST13_16~ST13_22` | 对象新增 / 字段变更需要同步 ST13 contract 和相关模块文档 |
| `scoring-review-export-dod.md` | `2026-04-25-workbench-mvp-scoring-review-export-dod.md` | `0-100` 多维评分、打磨反馈、压力面报告、真实 / 模拟复盘、RAG 证据、Markdown 导出、错误态 / 空状态、MVP DoD | 不写测试代码，不生成 packet，不把 DoD 直接改成 implementation-ready | M04、M06、M07、M08、M09、M10 | 重点 `ST13_08`、`ST13_09`、`ST13_13~ST13_19`、`ST13_24`、`ST13_25` | DoD 变更必须同步测试 / 验收任务包和 `DOCUMENT_MATURITY.md` 摘要 |

本计划不新增额外设计文件。若后续要拆出 API、schema、视觉系统或部署设计，应另开确认窗口，不能在步骤 2 中顺手扩目录。

## 6. 原 W13 plans 降级策略

四份原 W13 plans 在步骤 2 中统一改为短桥接文档：

| 原文件 | 新角色 | 正文处理 | 目标链接 |
| --- | --- | --- | --- |
| `2026-04-25-workbench-mvp-scope.md` | W13-A 设计推进历史 / `scope.md` 迁移来源 | 压缩为桥接文档，不保留完整 current 正文 | `docs/design/workbench-mvp/scope.md` |
| `2026-04-25-workbench-mvp-ia-user-journey.md` | W13-B 设计推进历史 / `information-architecture.md` 迁移来源 | 压缩为桥接文档，不保留完整 current 正文 | `docs/design/workbench-mvp/information-architecture.md` |
| `2026-04-25-workbench-mvp-object-model-rag-multiround-backend.md` | W13-C 设计推进历史 / `object-model-rag-multiround-backend.md` 迁移来源 | 压缩为桥接文档，不保留完整 current 正文 | `docs/design/workbench-mvp/object-model-rag-multiround-backend.md` |
| `2026-04-25-workbench-mvp-scoring-review-export-dod.md` | W13-D 设计推进历史 / `scoring-review-export-dod.md` 迁移来源 | 压缩为桥接文档，不保留完整 current 正文 | `docs/design/workbench-mvp/scoring-review-export-dod.md` |

桥接文档顶部固定说明：

```markdown
> 当前正式设计事实源已迁入 `docs/design/workbench-mvp/...`。
> 本文仅保留为 W13 设计推进历史、迁移来源和执行过程证据。
> 当前事实以 `docs/design/workbench-mvp/` 下对应正式设计文档为准。
```

保留内容：

- 原 W13 阶段名称和日期。
- 迁移目标链接。
- 迁移来源说明。
- 3-8 条历史摘要。
- 关键确认来源和 Git 历史追溯说明。

不迁入正式设计正文的内容：

- W13-A/B/C/D 执行过程叙述。
- “本轮不进入实现”的过程性说明，除非作为正式边界摘要。
- 旧确认卡正文、推荐草案、proposed-default 过程材料。
- 与当前 confirmed 事实冲突或已被后续确认吸收的旧口径。
- 任务治理、state write、formal window、packet 准备细节。

必须迁入正式设计的内容：

- 已 confirmed 的范围、IA、对象模型、RAG、多轮、评分、复盘、导出、DoD 事实。
- W10 原型仅作参考证据的边界。
- 固定 3 轮不是总规则的纠偏。
- 当前仍不能实现、不能生成 packet、不能打开 formal window 的正式边界。

## 7. 模块承接方案

步骤 1 检查发现，用户给出的部分模块路径与当前仓库实际路径不同：

| 用户给定路径 | 当前仓库实际路径 | 处理 |
| --- | --- | --- |
| `docs/modules/M04-question-generation-and-evaluation/` | `docs/modules/M04-match-analysis-and-evidence/` | 按实际路径承接，不创建新目录 |
| `docs/modules/M07-reporting-and-export/` | `docs/modules/M07-polish-assessment-and-progress/` | 按实际路径承接，不创建新目录 |
| `docs/modules/M09-weakness-and-training/` | `docs/modules/M09-training-and-weakness-lifecycle/` | 按实际路径承接，不创建新目录 |
| `docs/modules/M10-admin-ops-and-settings/` | `docs/modules/M10-admin-governance-and-observability/` | 按实际路径承接，不创建新目录 |

步骤 2 不重命名模块目录，不新增模块目录。

| 模块 | 模块路径 | 应承接正式设计来源 | 最少更新入口 | 是否新增模块文档 | 承接摘要范围 | 不应复制内容 | 关联 ST13 | 后续深度补齐 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M01 | `docs/modules/M01-foundation-and-platform/` | `README.md`、`scope.md`、`object-model-rag-multiround-backend.md`、`scoring-review-export-dod.md` | `MODULE_REQUIREMENTS.md`、`MODULE_DESIGN.md`、`MODULE_TASK_INDEX.md` | 否 | 工程边界、前后端工程化、workspace、状态层、正式设计入口、测试和临时产物规则 | 不复制完整产品范围，不承诺实现目录 | `ST13_02`、`ST13_20~ST13_25` | 后续补前后端工程化、测试执行、doc-governor 链路与包结构 |
| M02 | `docs/modules/M02-identity-and-team/` | `scope.md`、`information-architecture.md`、`object-model-rag-multiround-backend.md` | `MODULE_REQUIREMENTS.md`、`MODULE_DESIGN.md`、`MODULE_TASK_INDEX.md` | 否 | 登录、账号、角色、权限、团队范围、记录可见性、M02 blocker 对 `ST13_20 / ST13_21` 的影响 | 不自创完整组织权限体系，不写实现字段 | `ST13_01`、`ST13_20`、`ST13_21`、`ST13_22` | 补 API / open_questions blocker、权限矩阵、session cookie 和管理员创建账号边界 |
| M03 | `docs/modules/M03-jobs-resumes-and-documents/` | `scope.md`、`information-architecture.md`、`object-model-rag-multiround-backend.md`、`scoring-review-export-dod.md` | `MODULE_REQUIREMENTS.md`、`MODULE_DESIGN.md`、`MODULE_TASK_INDEX.md` | 否 | 岗位、简历、文档输入、岗位详情发起、岗位-简历匹配、服务端保存对象、导出输入 | 不把旧上传 / 导出链直接提升为 ready | `ST13_03`、`ST13_04`、`ST13_06`、`ST13_19`、`ST13_20`、`ST13_23` | 补岗位 / 简历版本、发起必选、材料包、Markdown 导出权限 |
| M04 | `docs/modules/M04-match-analysis-and-evidence/` | `object-model-rag-multiround-backend.md`、`scoring-review-export-dod.md`、`information-architecture.md` | `MODULE_REQUIREMENTS.md`、`MODULE_DESIGN.md`、`MODULE_TASK_INDEX.md` | 否 | LLM 出题、岗位匹配、评分证据、首题、追问、评价边界、训练入口 | 不复制完整 RAG / LLM provider 设计，不替代 M06/M07 | `ST13_06`、`ST13_13`、`ST13_16`、`ST13_17`、`ST13_21`、`ST13_23` | 补评分证据、匹配分析与 question generation 的模块边界 |
| M05 | `docs/modules/M05-assets-and-retrieval/` | `scope.md`、`information-architecture.md`、`object-model-rag-multiround-backend.md`、`scoring-review-export-dod.md` | `MODULE_REQUIREMENTS.md`、`MODULE_DESIGN.md`、`MODULE_TASK_INDEX.md` | 否 | RAG / 知识库 / 文档 / chunk / retrieval / citation / evidence / asset archive | 不把完整资产中心提前做大，不隐藏 RAG 失败态 | `ST13_10`、`ST13_18`、`ST13_20` | 补知识库权限、混合检索、引用、证据缺口、资产归档 schema |
| M06 | `docs/modules/M06-simulated-interview-and-context/` | `information-architecture.md`、`object-model-rag-multiround-backend.md`、`scoring-review-export-dod.md` | `MODULE_REQUIREMENTS.md`、`MODULE_DESIGN.md`、`MODULE_TASK_INDEX.md` | 否 | 模拟记录列表、发起面试、面试台、`InterviewSession`、打磨 / 压力面、多轮上下文 | 不恢复直接开始面试为默认入口，不固定 3 轮 | `ST13_05~ST13_07`、`ST13_10~ST13_12`、`ST13_15`、`ST13_19`、`ST13_22` | 补状态机、turn / round / context、完成回写、RAG evidence 展示 |
| M07 | `docs/modules/M07-polish-assessment-and-progress/` | `object-model-rag-multiround-backend.md`、`scoring-review-export-dod.md`、`information-architecture.md` | `MODULE_REQUIREMENTS.md`、`MODULE_DESIGN.md`、`MODULE_TASK_INDEX.md` | 否 | 打磨模式、`ProgressTree`、题级反馈、能力树、训练进展、Markdown 阶段总结 | 不把 M07 写成 reporting/export 总模块，不替代 M08/M09 | `ST13_08`、`ST13_13`、`ST13_16`、`ST13_17` | 补打磨结束条件、题级评分、能力树最小范围 |
| M08 | `docs/modules/M08-review-and-replay/` | `information-architecture.md`、`object-model-rag-multiround-backend.md`、`scoring-review-export-dod.md` | `MODULE_REQUIREMENTS.md`、`MODULE_DESIGN.md`、`MODULE_TASK_INDEX.md` | 否 | 真实面试复盘、模拟面试复盘、逐题拆解、追问风险、复盘来源、导出入口 | 不把真实复盘要求用户手工拆题，不只写简版报告 | `ST13_14~ST13_16`、`ST13_18`、`ST13_19` | 补 ReviewReport、MockReview、RealReview、逐题反馈与 RAG evidence |
| M09 | `docs/modules/M09-training-and-weakness-lifecycle/` | `object-model-rag-multiround-backend.md`、`scoring-review-export-dod.md` | `MODULE_REQUIREMENTS.md`、`MODULE_DESIGN.md`、`MODULE_TASK_INDEX.md` | 否 | `WeaknessItem`、`ProgressTree`、`TrainingDrawer`、待打磨、能力树、薄弱项消减与停练 | 不扩成完整训练中心，不替代评分与复盘来源 | `ST13_16`、`ST13_17` | 补弱项证据、训练抽屉动作、消减规则、停练条件 |
| M10 | `docs/modules/M10-admin-governance-and-observability/` | `scope.md`、`object-model-rag-multiround-backend.md`、`scoring-review-export-dod.md` | `MODULE_REQUIREMENTS.md`、`MODULE_DESIGN.md`、`MODULE_TASK_INDEX.md` | 否 | 配置、provider、部署、观测、日志、成本、运维、管理员边界 | 不创建 infra，不写 provider 密钥，不把运维设计变实现 | `ST13_01`、`ST13_11`、`ST13_13`、`ST13_22`、`ST13_24`、`ST13_25` | 补 provider 配置、日志脱敏、审计、单机部署、snapshot |

模块承接只允许写模块视角摘要、正式设计链接、模块影响、后续补齐事项和不放行实现的边界。不得把正式设计全文复制进模块文档。

## 8. 索引同步方案

| 文件 | 是否修改 | 修改目的 | 修改范围 | 不允许写入 | 是否可能产生确认卡 | 验证方式 |
| --- | --- | --- | --- | --- | --- | --- |
| `README.md` | 是 | 把当前事实入口从“四份 W13 plans”改为正式设计目录 | 当前事实源说明、相关入口 | 不写详细设计正文，不写实现指令 | 否 | 引用扫描 |
| `AGENTS.md` | 是 | 增加 `docs/design/workbench-mvp/` 正式设计入口；保留本计划和旧 plans 桥接 | 文档索引 | 不把旧 plans 继续标为 current fact source | 否 | 引用扫描 |
| `PLAN_LATEST.md` | 是 | 当前阶段记录 DesignCanon-Plan / Step 2 待确认；当前事实源改为正式设计目录 | 当前阶段、事实源表、下一步 | 不写 formal window open，不写 implementation-ready | 否 | 引用扫描、validate/evaluate |
| `DOCUMENT_PROGRESS.md` | 是 | 记录设计归位计划冻结，说明待步骤 2 实现 | 阶段摘要、完成事项、事实源表 | 不宣称迁移已完成，除非步骤 2 已执行 | 否 | 引用扫描 |
| `DOCUMENT_MATURITY.md` | 是 | 记录正式设计归位处于计划冻结阶段 | 全局成熟度表、W13 事实源成熟度说明 | 不自动提升模块或子任务成熟度 | 否 | 引用扫描 |
| `TASK_INDEX.md` | 是 | 让 ST13 输入事实源指向正式设计；任务治理文档保留双引用 | ST13 事实源 / 输入说明 | 不新增 implementation-ready，不生成 packet | 可能，仅当发现任务依赖需用户确认 | 引用扫描、risk scan |
| `MODULE_INDEX.md` | 是 | 记录 M01-M10 正式设计承接状态和实际模块路径 | 模块映射、承接摘要 | 不修改模块成熟度为 ready | 可能，仅当实际路径或承接口径需确认 | 引用扫描 |
| `OPEN_QUESTIONS.md` | 是 | 唯一事实源清单改为正式设计目录；旧 W13 plans 保留历史 / 迁移来源 | 唯一事实源表、必要 OQ 注释 | 不把 `OQ-125~OQ-127` 写成 confirmed | 可能，若发现新 unresolved source routing | 引用扫描 |
| `DESIGN_DECISIONS.md` | 是 | DD 当前事实引用改为正式设计目录 | DD 引用列、事实源清单 | 不把 `proposed-default` 写成 confirmed | 否 | 引用扫描 |
| `docs/superpowers/plans/2026-04-25-workbench-mvp-backlog-roadmap.md` | 是 | 路线图记录正式设计归位完成与旧 plans 历史化后续事项 | 设计事实源、backlog 条目 | 不把 future backlog 写成 current fact | 可能，若后续归档策略需确认 | 引用扫描 |

## 9. 引用替换规则

1. current fact source 引用：改为 `docs/design/workbench-mvp/` 或其具体文件。
2. historical / execution log 引用：保留旧 `docs/superpowers/plans/**` 路径，但必须明确是历史推进、迁移来源或执行证据。
3. task governance 引用：使用双引用，正式设计入口指向 `docs/design/workbench-mvp/`，任务治理来源保留 ST13 计划 / 双文档路径。
4. module design 引用：必须指向 `docs/design/workbench-mvp/`，模块文档只保留模块视角摘要。
5. archive 引用：保持 archive 语义，不提升为当前事实源。
6. 不确定引用：列入待复核清单，不强行替换。
7. 相对链接处理：原 W13 plans 降级为桥接文档后，内部互链不得继续形成 current design chain。
8. 文案规则：禁止把旧 W13 plans 写成“唯一事实源”“当前事实源”“正式设计正文”；只能写“迁移来源”“历史推进记录”“桥接文档”。

## 10. 验证方案

步骤 2 完成后必须运行：

```powershell
git status --short
git status -sb
git rev-list --left-right --count origin/main...HEAD

python -m tools.doc_governor.cli validate-state --input docs/governance/DOC_STATE.yaml
python -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml
```

引用扫描：

```powershell
rg -n "2026-04-25-workbench-mvp-scope|2026-04-25-workbench-mvp-ia-user-journey|2026-04-25-workbench-mvp-object-model-rag-multiround-backend|2026-04-25-workbench-mvp-scoring-review-export-dod|docs/design/workbench-mvp" README.md AGENTS.md PLAN_LATEST.md DOCUMENT_PROGRESS.md DOCUMENT_MATURITY.md TASK_INDEX.md MODULE_INDEX.md OPEN_QUESTIONS.md DESIGN_DECISIONS.md docs
```

事实源路径扫描：

```powershell
rg -n "唯一事实源|当前事实源|当前事实以|正式设计事实源" README.md AGENTS.md PLAN_LATEST.md DOCUMENT_PROGRESS.md DOCUMENT_MATURITY.md TASK_INDEX.md MODULE_INDEX.md OPEN_QUESTIONS.md DESIGN_DECISIONS.md docs
```

风险关键词扫描：

```powershell
rg -n "candidate_status: candidate|formal_window_open: true|implementation_ready: true|implementation-ready|implementation packet|formal window open|可直接进入实现|已打开 formal window|已生成 implementation packet" README.md AGENTS.md PLAN_LATEST.md DOCUMENT_PROGRESS.md DOCUMENT_MATURITY.md TASK_INDEX.md MODULE_INDEX.md OPEN_QUESTIONS.md DESIGN_DECISIONS.md docs
```

禁止范围检查：

```powershell
git diff --name-only -- docs/governance/DOC_STATE.yaml docs/governance/DOC_STATE.bootstrap.yaml tools tests apps infra archive package.json package-lock.json pnpm-lock.yaml
```

步骤 2 允许修改 `docs/design/**` 与 `docs/modules/**`，但必须另行检查它们只包含设计归位和模块承接变更：

```powershell
git diff --name-only -- docs/design docs/modules
git diff -- docs/design docs/modules
```

孤立文档风险检查：

```powershell
rg -n "docs/design/workbench-mvp" README.md AGENTS.md PLAN_LATEST.md DOCUMENT_PROGRESS.md DOCUMENT_MATURITY.md TASK_INDEX.md MODULE_INDEX.md OPEN_QUESTIONS.md DESIGN_DECISIONS.md docs
rg -L "docs/design/workbench-mvp" README.md AGENTS.md PLAN_LATEST.md DOCUMENT_PROGRESS.md DOCUMENT_MATURITY.md TASK_INDEX.md MODULE_INDEX.md OPEN_QUESTIONS.md DESIGN_DECISIONS.md
```

双事实源风险检查：

```powershell
rg -n "docs/superpowers/plans/2026-04-25-workbench-mvp-(scope|ia-user-journey|object-model-rag-multiround-backend|scoring-review-export-dod)\\.md.*(唯一事实源|当前事实源|正式设计事实源)|唯一事实源.*docs/superpowers/plans/2026-04-25-workbench-mvp" README.md AGENTS.md PLAN_LATEST.md DOCUMENT_PROGRESS.md DOCUMENT_MATURITY.md TASK_INDEX.md MODULE_INDEX.md OPEN_QUESTIONS.md DESIGN_DECISIONS.md docs
```

验证判定：

- `validate-state` 必须 `ok=true,error=0,warning=0`。
- `evaluate-state` 必须 `ok=true,error=0,warning=0,documents_blocked_count=0`。
- 旧 W13 plans 不得再以 current / unique fact source 身份出现。
- `docs/design/workbench-mvp/` 必须被根入口、OQ/DD、任务索引、模块索引和模块承接文档引用。
- 不得出现 `formal_window_open=true`、`implementation_ready=true`、`candidate_status=candidate` 等未授权状态写入。

## 11. 回退方案

### 11.1 未提交前回退

若步骤 2 完成后验证失败且尚未提交：

```powershell
git diff --name-only
git restore -- README.md AGENTS.md PLAN_LATEST.md EXECUTION_LOG.md DOCUMENT_PROGRESS.md DOCUMENT_MATURITY.md TASK_INDEX.md MODULE_INDEX.md OPEN_QUESTIONS.md DESIGN_DECISIONS.md docs/superpowers/plans/2026-04-25-workbench-mvp-backlog-roadmap.md
git restore -- docs/superpowers/plans/2026-04-25-workbench-mvp-scope.md docs/superpowers/plans/2026-04-25-workbench-mvp-ia-user-journey.md docs/superpowers/plans/2026-04-25-workbench-mvp-object-model-rag-multiround-backend.md docs/superpowers/plans/2026-04-25-workbench-mvp-scoring-review-export-dod.md
git restore -- docs/modules
```

删除新建正式设计文档时必须先确认路径：

```powershell
Resolve-Path docs/design/workbench-mvp
Remove-Item -Recurse -Force docs/design/workbench-mvp
```

### 11.2 已提交后回退

若步骤 2 已提交但未推送，优先使用反向提交：

```powershell
git revert <design-canon-commit>
```

若已推送，仍使用 `git revert`，不得使用强推覆盖远端历史。

### 11.3 分项回退

| 范围 | 回退方式 | 回退后验证 |
| --- | --- | --- |
| `docs/design/workbench-mvp/` 新文档 | 删除新目录或 revert 对应 commit | `Test-Path docs/design/workbench-mvp` 按预期为 false 或回到上版 |
| 原 W13 plans 降级 | 恢复四份旧 plans | 引用扫描确认旧 plans 若恢复为 current，也必须同步根索引，否则停止 |
| 模块承接修改 | 恢复 `docs/modules/**` 变更 | `git diff -- docs/modules` 为空 |
| 索引同步 | 恢复根文档和 backlog-roadmap | 引用扫描、validate/evaluate |
| 状态层误改 | 立即停止；恢复 `docs/governance/DOC_STATE.yaml` 并重跑 validate/evaluate | `git diff -- docs/governance/DOC_STATE.yaml` 为空 |

## 12. 步骤 2 实现窗口输入包

### 12.1 目标

按本计划一次性完成正式设计归位、原 W13 plans 桥接降级、M01-M10 模块承接、引用修正、验证、回退说明和提交。

### 12.2 已冻结文件清单

新增：

- `docs/design/workbench-mvp/README.md`
- `docs/design/workbench-mvp/scope.md`
- `docs/design/workbench-mvp/information-architecture.md`
- `docs/design/workbench-mvp/object-model-rag-multiround-backend.md`
- `docs/design/workbench-mvp/scoring-review-export-dod.md`

修改：

- 四份原 W13 facts source plans 文档。
- `README.md`
- `AGENTS.md`
- `PLAN_LATEST.md`
- `EXECUTION_LOG.md`
- `DOCUMENT_PROGRESS.md`
- `DOCUMENT_MATURITY.md`
- `TASK_INDEX.md`
- `MODULE_INDEX.md`
- `OPEN_QUESTIONS.md`
- `DESIGN_DECISIONS.md`
- `docs/superpowers/plans/2026-04-25-workbench-mvp-backlog-roadmap.md`
- M01-M10 的最少承接入口文档：`MODULE_REQUIREMENTS.md`、`MODULE_DESIGN.md`、`MODULE_TASK_INDEX.md`

### 12.3 允许修改范围

- `docs/design/workbench-mvp/**`
- 四份原 W13 facts source plans 文档
- 根入口 / 总控文档：`README.md`、`AGENTS.md`、`PLAN_LATEST.md`、`EXECUTION_LOG.md`、`DOCUMENT_PROGRESS.md`、`DOCUMENT_MATURITY.md`、`TASK_INDEX.md`、`MODULE_INDEX.md`、`OPEN_QUESTIONS.md`、`DESIGN_DECISIONS.md`
- `docs/superpowers/plans/2026-04-25-workbench-mvp-backlog-roadmap.md`
- `docs/modules/M01-foundation-and-platform/**`
- `docs/modules/M02-identity-and-team/**`
- `docs/modules/M03-jobs-resumes-and-documents/**`
- `docs/modules/M04-match-analysis-and-evidence/**`
- `docs/modules/M05-assets-and-retrieval/**`
- `docs/modules/M06-simulated-interview-and-context/**`
- `docs/modules/M07-polish-assessment-and-progress/**`
- `docs/modules/M08-review-and-replay/**`
- `docs/modules/M09-training-and-weakness-lifecycle/**`
- `docs/modules/M10-admin-governance-and-observability/**`

### 12.4 禁止修改范围

- `docs/governance/DOC_STATE.yaml`
- `docs/governance/DOC_STATE*.yaml`
- `tools/**`
- `tests/**`
- `apps/**`
- `infra/**`
- `archive/**`
- `package.json`
- `package-lock.json`
- `pnpm-lock.yaml`
- Basic Memory

### 12.5 执行顺序

1. 运行基线 Git 和 state 验证。
2. 确认本计划文件存在且内容为步骤 2 输入。
3. 创建 `docs/design/workbench-mvp/` 五个正式设计文件。
4. 从四份 W13 plans 迁移 current 设计正文到对应正式设计文件。
5. 将四份 W13 plans 压缩为桥接文档。
6. 同步 `README.md`、`AGENTS.md`、`PLAN_LATEST.md`、`DOCUMENT_PROGRESS.md`、`DOCUMENT_MATURITY.md`。
7. 同步 `TASK_INDEX.md`、`MODULE_INDEX.md`、`OPEN_QUESTIONS.md`、`DESIGN_DECISIONS.md`、backlog-roadmap。
8. 按 M01-M10 最少入口文档做模块承接。
9. 执行引用替换扫描和不确定引用复核。
10. 运行 validate/evaluate、禁止范围检查、风险关键词扫描。
11. 输出修改清单、验证结果、是否可提交。
12. 用户若要求提交，再执行 `git add` / `git commit` / `git push`；否则停止在可审查 diff。

### 12.6 迁移内容规则

- 正式设计文件承接 current confirmed 设计事实。
- 旧 W13 plans 只保留历史摘要、迁移来源和目标链接。
- 不迁移旧确认卡正文、过程日志、proposed-default 讨论材料。
- 不新增未确认产品能力。
- 不把 current fact source 写成 archive、plans 或 execution log。

### 12.7 模块承接规则

- 每个模块只写模块视角摘要、引用新正式设计、关联 ST13、后续补齐事项。
- 不复制正式设计全文。
- 不提升模块成熟度，不宣称可进入子任务实现。
- 不创建新模块目录，不重命名模块目录。
- 若目标模块最少入口文件缺失，步骤 2 必须停止并输出缺失清单。

### 12.8 引用替换规则

按第 9 节执行。所有 current fact source 指向 `docs/design/workbench-mvp/`；历史和任务治理引用可保留旧 plans，但必须显式标注历史 / 迁移来源 / 任务治理。

### 12.9 验证命令

使用第 10 节命令，并补充：

```powershell
git diff --check
git status --short
```

### 12.10 回退方案

使用第 11 节。任何涉及 `DOC_STATE.yaml` 的误改都必须立即停止，先恢复状态层，再重跑 validate/evaluate。

### 12.11 输出格式

步骤 2 输出至少包含：

1. 基线 git status。
2. 初始 validate/evaluate。
3. 修改文件清单。
4. 新增正式设计文档清单。
5. 原 W13 plans 降级结果。
6. M01-M10 模块承接结果。
7. 引用替换结果。
8. 禁止范围检查。
9. 风险关键词扫描。
10. 最终 validate/evaluate。
11. 是否可提交。
12. 是否已提交 / 推送。

### 12.12 完成标准

- `docs/design/workbench-mvp/` 五个正式设计文件已创建。
- 四份原 W13 plans 已降级为桥接文档。
- M01-M10 已完成最少入口承接。
- 根文档、OQ/DD、任务索引、模块索引和 backlog-roadmap 已同步。
- 旧 W13 plans 不再作为 current / unique fact source。
- `DOC_STATE.yaml` 未修改。
- 未打开 formal window。
- 未生成 implementation packet。
- 未进入实现。
- validate/evaluate 全绿。

## 13. 当前不执行迁移说明

本计划文档只冻结步骤 2 输入，不创建 `docs/design/workbench-mvp/`，不改四份原 W13 facts source 正文，不修改模块正文，不写状态层，不打开 formal window，不生成 implementation packet，不进入实现，不写 Basic Memory，不提交。
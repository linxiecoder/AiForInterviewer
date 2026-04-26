# AI 模拟面试一期工作台 MVP 任务重映射草案

> 本文档是 `W13-E / Task Remap` 与 `W13-E2 / State Remap dry-run` 草案，用于把四份 W13 唯一事实源转换为可治理、可验证、可开窗前审查的候选任务结构，并记录状态层 dry-run 结论。`W13-E4-B` 已按阶段 1 将 `ST13_01~ST13_25` 写入正式 `DOC_STATE.yaml`，`W13-E4-C` 已按阶段 2 用旧 `STxx_*` facts 表达 `historical-reference / superseded`；本文档仍不是 implementation packet，不放行任何实现窗口。

## 1. 背景

`W13-F` 已完成阶段收口核验：W13 工作台级 MVP 范围、IA / 用户旅程、对象模型 / RAG / 多轮 / 后端边界、评分 / 复盘 / 导出 / DoD 均已有当前事实源，旧 P1 设计稿和旧实现计划已迁入 `archive/`，`DOC_STATE.yaml` 当前 `documents` 受管集合只登记 `DOC-PLAN-CURRENT-REPO-2026-04-25`。

当前剩余阻断不是产品事实源缺失，而是任务治理层尚未重映射：

- `TASK_INDEX.md` 已同步 `ST13_01~ST13_25` 正式状态层入口与 `WT13-xx` alias，但仍未形成 implementation-ready 或开窗资格。
- `MODULE_INDEX.md` 已同步 `ST13_*` 到 M01-M10 的模块映射摘要，但模块成熟度和下游设计入口仍未放行。
- `DOC_STATE.yaml` 的正式 `subtasks` 容器仍登记旧 `STxx_*`，并已在阶段 1 新增 `ST13_01~ST13_25`，阶段 2 为旧任务写入 `w13_status=superseded` 与 `w13_role=historical-reference`。
- `W13-E4-B` 已将 `ST13_01~ST13_25` 作为 `WT13-01~WT13-25` 的正式状态层兼容入口写入 `DOC_STATE.yaml`。
- 旧 `STxx_*` 仍被状态层和索引层引用，当前不能迁入 archive。
- 当前不等于 `implementation-ready`，不能直接进入业务代码实现。

## 2. 当前 W13 收口状态

### 2.1 已确认事实

以下事实继承自 W13 confirmed 结果，不得回退为 `proposed-default`：

1. 一期 MVP 是工作台级。
2. 一期包含服务端历史 / 复盘记录。
3. 一期接真实 LLM。
4. 一期有完整登录 / 权限。
5. 简历与面试记录服务端保存。
6. 一期有完整 `0-100` 多维评分。
7. 导出采用复制 / Markdown 下载。
8. 一期包含 RAG / 知识库。
9. 一期包含多轮高阶面试。
10. 模拟面试模块默认入口是历史模拟记录列表。
11. 发起模拟面试从记录列表进入。
12. 面试台是执行页。
13. 面试完成后回写历史记录 / 复盘。
14. 多轮面试拆分为打磨模式和压力面模式。
15. 打磨模式由 `ProgressTree / 进展树` 驱动，用户决定是否结束，不固定轮次。
16. 压力面模式由 `InterviewQuestionSet` 驱动，题目完成后结束。
17. 固定 3 轮不再是多轮面试总规则，只能作为压力面题组策略候选。
18. 当前 `apps/web/**` 原型仅作为参考证据，不作为正式一期 MVP 起点。
19. 代码开发暂停，先补设计和任务治理。
20. 旧 P1 设计稿和旧实现计划均为历史归档 / 历史追溯，不作为当前事实源。

### 2.2 基线验证

本窗口开始前状态命令均通过：

```powershell
python -m tools.doc_governor.cli validate-state --input docs/governance/DOC_STATE.yaml
python -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml
```

基线结果：

- `validate-state`: `ok=true, error=0, warning=0`
- `evaluate-state`: `ok=true, error=0, warning=0`
- `documents_blocked_count=0`
- `subtasks_blocked_count=30`
- `formal_window_open=false`

## 3. 旧任务结构审计

### 3.1 当前全局任务结构

`TASK_INDEX.md` 当前包含：

- 10 个模块级入口：`M01` 至 `M10`。
- 1 个历史 requirement：`RQ01`，仅解释 W10 首切片关系层。
- 30 个旧 `STxx_*` 子任务骨架。
- `ST02_*`、`ST03_*` 已明确为历史容器，禁止直开。
- `ST04_01 / ST04_02 / ST06_01 / ST06_02 / ST07_03` 只作为 W10 后续承接对象，不等于 W13 正式任务。
- 当前正式开窗层固定为空。

### 3.2 当前模块索引结构

`MODULE_INDEX.md` 当前包含：

- M01: 基础平台与工作台壳层，L4，不可支撑下游。
- M02: 鉴权、团队与成员，L4，不可支撑下游。
- M03: 岗位、简历与文档处理，L4，不可支撑下游。
- M04-M10: 仍多为 L1 骨架，不可支撑下游。
- W10-C 首切片模块映射已标记为历史参考。
- 当前 P0 建议已指向全局 W13 任务重映射。

### 3.3 `DOC_STATE.yaml` 当前旧 `STxx_*`

`DOC_STATE.yaml` 当前正式 `subtasks` 容器仍包含 30 个旧 `STxx_*`：

| 模块 | 旧 STxx_* |
| --- | --- |
| M01 | `ST01_01`、`ST01_02`、`ST01_03` |
| M02 | `ST02_01`、`ST02_02`、`ST02_03` |
| M03 | `ST03_01`、`ST03_02`、`ST03_03` |
| M04 | `ST04_01`、`ST04_02`、`ST04_03` |
| M05 | `ST05_01`、`ST05_02`、`ST05_03` |
| M06 | `ST06_01`、`ST06_02`、`ST06_03` |
| M07 | `ST07_01`、`ST07_02`、`ST07_03` |
| M08 | `ST08_01`、`ST08_02`、`ST08_03` |
| M09 | `ST09_01`、`ST09_02`、`ST09_03` |
| M10 | `ST10_01`、`ST10_02`、`ST10_03` |

状态层共性：

- `candidate_status=none`
- `readiness=blocked`
- `implementation_doc_state=missing`
- `formal_window_open=false`
- `implementation_ready=false`

### 3.4 旧 `STxx_*` 可复用性分类

| 旧任务范围 | 分类 | 说明 |
| --- | --- | --- |
| `ST01_*` | `reusable-evidence` + `state-bound` | 工程基线、壳层、测试治理可作为 W13 基础工程和验收参考，但不能直接作为工作台 MVP 开窗任务。 |
| `ST02_*` | `historical-reference` + `superseded` + `state-bound` | 旧鉴权 / 成员 / 授权入口已不适合作为 W13 直接入口；权限事实应由 W13 登录 / 权限任务重建。 |
| `ST03_*` | `historical-reference` + `reusable-evidence` + `state-bound` | 岗位、简历、上传导出链可复用结构信息；但 W13 需要服务端保存、列表化管理、发起必选和导出边界重裁剪。 |
| `ST04_*` | `reusable-evidence` + `superseded` + `state-bound` | 匹配分析、评分证据和训练入口可复用概念，但 W13 评分体系、RAG 证据和训练闭环已显著扩展。 |
| `ST05_*` | `reusable-evidence` + `state-bound` | 资产、归档、检索入库对 W13 RAG / 知识库和资产归档有参考价值；需重建为知识库 / 资产任务域。 |
| `ST06_*` | `reusable-evidence` + `superseded` + `state-bound` | 会话创建、上下文包、消息 trace 可复用；但 W13 主入口改为模拟记录列表，并新增打磨 / 压力面、RAG、真实 LLM。 |
| `ST07_*` | `reusable-evidence` + `state-bound` | 打磨主题、能力树、逐题评估可复用；需按 `ProgressTree` 与 W13 题级反馈重映射。 |
| `ST08_*` | `reusable-evidence` + `state-bound` | 复盘对象、真实面试复盘、模拟复盘有参考价值；需按 W13 复盘 / 评分 / 导出 DoD 重切。 |
| `ST09_*` | `reusable-evidence` + `state-bound` | 薄弱项、训练抽屉、生命周期规则可复用；需按 `WeaknessItem` 中粒度主题和消减规则重建。 |
| `ST10_*` | `reusable-evidence` + `state-bound` | 管理、模型规则、可观测性可复用；需按 W13 单机部署、日志、provider、snapshot 入口重切。 |

### 3.5 审计结论

- 旧 `RQ01` 与旧 `STxx_*` 只解释 W10 首切片或早期模块骨架，不能作为 W13 工作台级 MVP 的正式任务树。
- W10 首切片任务仍被索引保留，但已有明确历史 / 反向约束，不应再被误认为当前任务。
- `RQ01 / STxx / MTxx` 与 W13 事实源的主要冲突是范围粒度：W13 已包含登录、权限、服务端保存、RAG、真实 LLM、多轮、评分、复盘、导出和训练闭环，远大于 W10 首切片。
- 模块索引与任务索引在“旧关系已历史化、正式开窗层为空”上基本一致；W13-E4-B 已将 `ST13_01~ST13_25` 写入正式状态层，W13-E4-C 已将旧 `STxx_*` 通过 facts 表达为 `historical-reference / superseded`，但仍保留在正式容器中。
- 旧 `STxx_*` 暂不能迁移 archive，因为仍被 `DOC_STATE.yaml`、`TASK_INDEX.md` 和模块索引引用。

## 4. 新 W13 工作台级任务树草案

> 用户已确认 `WT13-xx` 作为 W13 工作台级候选任务域命名。该确认不等于 `doc_governor` 当前状态层已经接受 `WT13-xx` 作为 `subtasks` key，也不等于任何任务进入 `implementation-ready`。

| 候选任务 ID | 任务名称 | 关联模块 | 输入事实源 | 产出文档或实现对象 | 是否必须进入一期 | 依赖任务 | 是否可并行 | 允许修改范围 | 禁止修改范围 | 验证命令 | 验收标准 | 需用户确认 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `WT13-01` | 账号 / 登录 / 权限 | M02、M10、M01 | W13 scope、IA、对象模型、`FC-02` | 登录页、session cookie、用户 / 角色 / 权限对象、权限不足状态 | 是 | `WT13-20`、`WT13-21` | 可与 UI 草案并行，不能与数据 schema 冲突 | `apps/api/**`、`apps/web/**`、`packages/shared/**`、M02 文档 | `DOC_STATE.yaml`、无确认时的账号体系扩展 | `validate-state`、`evaluate-state`、后续 auth/API 测试 | 普通用户 / 管理员权限、记录可见范围和未登录状态可验收 | 否，产品事实已 confirmed；实现细节需任务包确认 |
| `WT13-02` | 工作台首页 / 导航 / 权限入口 | M01、M02、M10 | W13 IA、`FC-09`、`FC-15` | 工作台壳层、左侧导航、顶部账号区、行动型摘要 | 是 | `WT13-01` | 可与 `WT13-03/04/05` 页面设计并行 | `apps/web/**`、`packages/shared/**`、M01 文档 | 不得扩展完整设计系统或实现未开窗后端 | `validate-state`、`evaluate-state`、后续 web 测试 | 导航包含一期主链，后续能力低干扰，不绕过权限入口 | 否 |
| `WT13-03` | 岗位管理 | M03、M04 | W13 scope、IA、对象模型、`FC-10` | `Job` 列表 / 详情 / 创建编辑 / 归档 | 是 | `WT13-01`、`WT13-20` | 可与简历管理并行 | `apps/web/**`、`apps/api/**`、M03 文档 | 不得恢复 W10 手工 JD 单页作为正式主链 | `validate-state`、`evaluate-state`、后续 job API / UI 测试 | 岗位可服务端保存，可作为发起面试必选输入和评分证据 | 否 |
| `WT13-04` | 简历管理 | M03、M10 | W13 scope、IA、对象模型、`FC-03`、`FC-10` | `Resume` 列表 / 编辑 / 上传 / 粘贴 / 版本 | 是 | `WT13-01`、`WT13-20` | 可与岗位管理并行 | `apps/web/**`、`apps/api/**`、M03 文档 | 不得把上传 / 导出链直接视为旧 `ST03_03` 开窗 | `validate-state`、`evaluate-state`、后续 resume API / UI 测试 | 简历服务端保存并作为面试、复盘、评分证据 | 否 |
| `WT13-05` | 模拟记录列表 | M06、M08、M02 | W13 IA、对象模型、评分 / 复盘 DoD、`FC-06` | `SessionRecord` 列表、筛选、权限可见范围、继续 / 复盘 / 导出入口 | 是 | `WT13-01`、`WT13-20`、`WT13-21` | 可与发起流程设计并行 | `apps/web/**`、`apps/api/**`、M06 / M08 文档 | 不得把模拟面试默认页写成直接开始新面试 | `validate-state`、`evaluate-state`、后续列表 API / UI 测试 | 模拟面试模块默认进入记录列表，完成后回写列表状态 | 否 |
| `WT13-06` | 发起模拟面试 | M03、M04、M05、M06、M07 | W13 IA、对象模型 | `InterviewLaunchContext`、`InterviewReferencePack`、模式选择、知识库选择 | 是 | `WT13-03`、`WT13-04`、`WT13-10`、`WT13-11` | 可与面试台 UI 并行，但不能早于输入对象 contract | `apps/web/**`、`apps/api/**`、M06 文档 | 不得跳过岗位 / 简历必选 confirmed 事实 | `validate-state`、`evaluate-state`、后续 launch API / UI 测试 | 从记录列表或岗位详情发起，选择岗位、简历、模式并生成参考材料包 | 否 |
| `WT13-07` | 面试台 | M06、M05、M07、M08 | W13 IA、对象模型、DoD | `InterviewSession` 执行页、turn、RAG 引用、暂停 / 继续 / 完成 | 是 | `WT13-06`、`WT13-10`、`WT13-11`、`WT13-12` | 可与评分 / 复盘 contract 并行 | `apps/web/**`、`apps/api/**`、M06 文档 | 不得使用 mock LLM 作为正式 MVP 行为 | `validate-state`、`evaluate-state`、后续 interview flow 测试 | 面试台可承载真实 LLM、多轮、RAG 证据、完成后触发复盘 / 评分 | 否 |
| `WT13-08` | 打磨模式 | M07、M06、M09 | W13 对象模型、评分 / 复盘 DoD、`FC-13` | `PolishModeSession`、`ProgressTree`、题级反馈、`UserEndDecision` | 是 | `WT13-07`、`WT13-13`、`WT13-16` | 可与压力面模式并行 | `apps/web/**`、`apps/api/**`、M07 / M09 文档 | 不得写成固定轮次 | `validate-state`、`evaluate-state`、后续 polish flow 测试 | 进展树驱动出题，用户决定继续 / 结束，每题反馈结构完整 | 否 |
| `WT13-09` | 压力面模式 | M06、M08、M07 | W13 对象模型、评分 / 复盘 DoD、`FC-06` | `PressureInterviewSession`、`InterviewQuestionSet`、`InterviewCompletion` | 是 | `WT13-07`、`WT13-13`、`WT13-15` | 可与打磨模式并行 | `apps/web/**`、`apps/api/**`、M06 / M08 文档 | 不得把固定 3 轮写成总规则 | `validate-state`、`evaluate-state`、后续 pressure flow 测试 | 题组驱动，题目完成后结束，结束后生成最终评估、评分和复盘 | 否 |
| `WT13-10` | RAG / 知识库 | M05、M06、M08、M10 | W13 scope、IA、对象模型、`FC-05` | `KnowledgeBase`、`KnowledgeDocument`、`KnowledgeChunk`、`RetrievalQuery`、`Citation / Evidence` | 是 | `WT13-01`、`WT13-20`、`WT13-21` | 可与 LLM adapter 并行，需统一证据模型 | `apps/api/**`、`apps/web/**`、M05 文档 | 不得伪造 RAG evidence 或隐藏无命中 | `validate-state`、`evaluate-state`、后续 RAG 检索 / 引用测试 | 支持私有上传和管理员公共知识库，混合检索，失败降级并标注证据缺口 | 否 |
| `WT13-11` | 真实 LLM provider / adapter | M10、M06、M04、M08 | W13 scope、对象模型、`FC-04` | `LLMProviderConfig`、`LLMGenerationRequest / Result`、`PromptTemplateVersion` | 是 | `WT13-20`、`WT13-21` | 可与 RAG contract 并行 | `apps/api/**`、`packages/shared/**`、M10 文档 | 不得把密钥写入文档或日志，不得继续用 mock 作为正式行为 | `validate-state`、`evaluate-state`、后续 provider adapter 测试 | 接一个默认真实 provider，可插拔，失败可重试，记录脱敏请求与版本 | 否 |
| `WT13-12` | 多轮上下文 / 状态机 | M06、M07、M08 | W13 对象模型、DoD | `InterviewContext`、`InterviewRound`、`InterviewTurn`、状态流转 | 是 | `WT13-07`、`WT13-08`、`WT13-09` | 可与 UI 展示并行，需先统一状态枚举 | `apps/api/**`、`apps/web/**`、M06 文档 | 不得以固定 3 轮替代模式状态机 | `validate-state`、`evaluate-state`、后续 state machine 测试 | 暂停 / 继续、题组完成、用户结束和复盘可恢复 | 否 |
| `WT13-13` | 评分体系 | M04、M07、M08、M10 | W13 scoring / DoD、`FC-07` | `ScoreReport`、`ScoreDimension`、规则版本、证据绑定 | 是 | `WT13-10`、`WT13-11`、`WT13-12` | 可与复盘设计并行 | `apps/api/**`、`apps/web/**`、M04 / M08 文档 | 不得输出黑盒分数或无证据评分 | `validate-state`、`evaluate-state`、后续 scoring 测试 | `0-100` 多维评分可解释、可版本化、可重算 / 修订 | 否 |
| `WT13-14` | 真实面试复盘 | M08、M09、M10 | W13 scoring / DoD、`FC-11` | `RealInterviewReview`、`QuestionReviewItem`、逐题拆解 | 是 | `WT13-11`、`WT13-13`、`WT13-16` | 可与模拟复盘并行 | `apps/web/**`、`apps/api/**`、M08 文档 | 不得要求用户先手工拆题作为唯一入口 | `validate-state`、`evaluate-state`、后续 real review 测试 | 支持逐字稿输入，LLM 自动识别问答边界，低置信度提示校对 | 否 |
| `WT13-15` | 模拟面试复盘 | M08、M06、M07、M09 | W13 scoring / DoD | `MockInterviewReview`、整场判断、逐题点评、改进建议 | 是 | `WT13-09`、`WT13-13`、`WT13-16` | 可与真实复盘并行 | `apps/web/**`、`apps/api/**`、M08 文档 | 不得只生成简版反馈摘要 | `validate-state`、`evaluate-state`、后续 mock review 测试 | 压力面结束后展示整场判断、多维评分、岗位匹配、通过概率和训练建议 | 否 |
| `WT13-16` | 薄弱项 `WeaknessItem` | M09、M04、M07、M08 | W13 对象模型、DoD、`FC-13` | `WeaknessItem`、`WeaknessEvidence`、聚合 / 消减 / 停练规则 | 是 | `WT13-13`、`WT13-14`、`WT13-15` | 可与训练抽屉并行 | `apps/api/**`、`apps/web/**`、M09 文档 | 不得把待打磨清单替代薄弱项中心 | `validate-state`、`evaluate-state`、后续 weakness 测试 | 中粒度主题可累计、可消减、可停练，证据可回溯 | 否 |
| `WT13-17` | 训练抽屉 / 待打磨清单 | M09、M07、M08、M03 | W13 对象模型、DoD | `TrainingDrawerContext`、`TrainingTask`、训练动作 | 是 | `WT13-16`、`WT13-08`、`WT13-14`、`WT13-15` | 可与 UI 细化并行 | `apps/web/**`、`apps/api/**`、M09 文档 | 不得扩成完整训练中心而吞掉一期主链 | `validate-state`、`evaluate-state`、后续 training drawer 测试 | 支持归并、加入待打磨、立即打磨、暂不处理，并显示影响预览 | 否 |
| `WT13-18` | 资产归档 | M05、M08、M10 | W13 对象模型、DoD、`FC-14` | `Asset`、`AssetType`、`AssetSchema`、整份 / 单题归档 | 是 | `WT13-14`、`WT13-15`、`WT13-20` | 可与导出任务并行 | `apps/web/**`、`apps/api/**`、M05 文档 | 不得做复杂资产中心替代主链 | `validate-state`、`evaluate-state`、后续 asset archive 测试 | 支持整份和单题归档，选择资产类型，动态字段子集可验收 | 否 |
| `WT13-19` | Markdown 导出 / 复制 | M07、M08、M03、M10 | W13 scoring / DoD、`FC-12` | `ExportSnapshot / ExportRecord`、复制内容、Markdown 下载内容 | 是 | `WT13-13`、`WT13-14`、`WT13-15`、`WT13-18` | 可与资产归档并行 | `apps/web/**`、`apps/api/**`、M08 / M03 文档 | 不得做完整 PDF，不得导出无权限原文 | `validate-state`、`evaluate-state`、后续 export 测试 | 详情页可复制 / 下载 Markdown，包含评分、复盘、RAG 引用和训练建议 | 否 |
| `WT13-20` | 服务端保存 / 数据库 | M01、M02-M10 | W13 scope、对象模型、`FC-03` | PostgreSQL schema / migration、核心对象持久化 | 是 | `WT13-21` contract | 可与 API contract 设计并行，实施需串行控 schema | `apps/api/**`、`packages/shared/**`、M01 / M10 文档 | 不得在未确认 state 写回前直接创建目录 | `validate-state`、`evaluate-state`、后续 migration / repository 测试 | 会话、简历、复盘、脱敏 LLM 记录、RAG query/topK、完整问答、摘要与评分证据可保存 | 否，数据库已 confirmed，schema 细节需任务包确认 |
| `WT13-21` | API / 后端服务边界 | M01、M10、M02-M09 | W13 对象模型、`FC-01` | Auth、Job、Resume、Knowledge、Interview、Review、Score、Export 等 API contract | 是 | `WT13-01`、`WT13-20` | 可先做 contract 窗口，实施需按服务域拆分 | `apps/api/**`、`packages/shared/**`、M01 / M10 文档 | 不得无 contract 直接实现业务服务 | `validate-state`、`evaluate-state`、后续 API contract 测试 | 后端 FastAPI 边界、接口输入输出、错误态和权限态可验收 | 否 |
| `WT13-22` | 日志 / 观测 / 运维 | M10、M01 | W13 对象模型、`FC-01`、`FC-18` | 应用日志、LLM 日志、RAG 日志、审计、部署 / 配置边界 | 是，最小能力 | `WT13-11`、`WT13-20`、`WT13-21` | 可与后端骨架并行设计 | `apps/api/**`、`infra/**` 仅在开窗后、M10 文档 | 当前窗口禁止创建 `infra/**` | `validate-state`、`evaluate-state`、后续 ops smoke 测试 | 关键操作、权限、LLM、RAG、导出、归档可追踪，密钥不明文 | 否 |
| `WT13-23` | 前端工作台 UI / 页面集合 | M01-M10 | W13 IA、scoring / DoD | 登录、工作台、岗位、简历、知识库、记录列表、发起、面试台、复盘、导出 | 是 | `WT13-01`、`WT13-03` 至 `WT13-19` contract | 可按页面域并行，需共享壳层先行 | `apps/web/**`、`packages/shared/**`、模块文档 | 不得继续从 W10 原型直接扩展为正式事实 | `validate-state`、`evaluate-state`、后续 web:test / web:build | 页面集合符合 IA，错误态 / 空状态完整，响应式与无障碍达标 | 否 |
| `WT13-24` | 测试 / 验收 / DoD | M01、M10、全模块 | W13 scoring / DoD、AGENTS、TEST_POLICY | 产品 / 数据 / UI / 工程 / 收口五层 DoD 测试矩阵 | 是 | 所有实现任务 | 可作为横向验证窗口并行 | `tests/**`、`apps/**` 测试文件、docs 测试说明 | 当前窗口禁止修改 `tests/**` | `validate-state`、`evaluate-state`、`python -m tools.test_runner.run_tests` | 关键流程、权限、RAG、LLM、评分、复盘、导出均有验收证据 | 否 |
| `WT13-25` | 文档治理 / 收口 / Basic Memory | global、M01、M10 | AGENTS、DOC_GOVERNANCE、DOC_AUTOMATION、W13 facts | 任务索引、模块映射、状态层迁移方案、收口记录、Basic Memory 写回 | 是，治理必需 | 所有任务 | 可与只读审计并行，写回需总控 | 根文档、必要的 `docs/superpowers/plans/**` | 未确认前禁止改 `DOC_STATE.yaml` 和 Basic Memory | `validate-state`、`evaluate-state`、关键词回归 | 任务树、确认卡、状态层方案和下一窗口边界清晰，无新增 blocker | 是，需确认 ID / 旧 ST / DOC_STATE 策略 |

## 5. 任务 ID 命名方案确认卡

**问题：W13 工作台级任务 ID 如何命名？**

| 方案 | 内容 | 解决 | 限制 | 风险 | 后续影响 |
| --- | --- | --- | --- | --- | --- |
| A | 使用 `WT13-xx`，例如 `WT13-01`、`WT13-02` | 和旧 `STxx_*` 区分明显 | 需要更新索引规则 | 新旧任务体系并存一段时间 | 适合 W13 工作台级任务树 |
| B | 使用 `WB-MVP-xx`，例如 `WB-MVP-01` | 语义更清晰 | 编号较长 | 可能不符合旧工具对 ID 的假设 | 需要检查 `doc_governor` 是否接受该格式 |
| C | 继续使用 `ST13_xx` | 延续旧 `ST` 风格 | 容易与旧 `STxx_*` 混淆 | 可能误激活旧任务 | 不推荐，除非工具强依赖 `ST` 格式 |
| D | 自定义方案 | 由用户补充 | 待定义 | 待评估 | 待评估 |

推荐方案：A。

推荐理由：`WT13-xx` 能清楚表达“Workbench Task / W13 工作台任务”，不与旧 `STxx_*` 状态容器混淆。

必须检查项：`docs/governance/DOC_AUTOMATION.md` 当前说明主链 task 对象容器仍为 `subtasks`，命名规则仍以 `STxx_yy` 为准。因此在用户确认前，`WT13-xx` 只能作为草案 ID；写入 `DOC_STATE.yaml` 前必须在 W13-E2 检查 `schema.py`、`validate.py`、`evaluate.py` 和相关测试对 ID 格式的实际约束。

当前状态：用户已确认采用 `WT13-xx` 作为候选任务域命名；状态层兼容性结论见第 10.2 节。

## 6. 旧 `STxx_*` 处理策略确认卡

**问题：旧 `STxx_*` 在 W13 Task Remap 中如何处理？**

| 方案 | 内容 | 解决 | 限制 | 风险 | 后续影响 |
| --- | --- | --- | --- | --- | --- |
| A | 全部暂保留原路径，通过 `TASK_INDEX.md` / `MODULE_INDEX.md` 标记为 `historical-reference` | 最稳，不断链 | 历史文件仍留在模块目录 | 需要明确索引说明避免误用 | 不阻断 W13 任务树设计 |
| B | 建立新 W13 任务后，将旧 `STxx_*` 映射为 `superseded`，并计划后续状态层窗口迁入 archive | 最终状态更干净 | 需要后续 `DOC_STATE.yaml` 同步 | 迁移窗口风险较高 | 适合 W13-E2 / State Remap |
| C | 逐个审计，部分保留、部分 `superseded`、部分 `archive-candidate` | 最精细 | 耗时最长 | 容易陷入大量旧文档细节 | 适合后续模块窗口，不适合本窗口一次完成 |
| D | 自定义方案 | 由用户补充 | 待定义 | 待评估 | 待评估 |

推荐方案：B。

推荐理由：本窗口先建立新任务树和 `superseded` 关系，后续再用状态层窗口迁移旧 `STxx_*`，既不阻断当前推进，也满足长期归档目标。

当前状态：用户已确认旧 `STxx_*` 后续映射为 `superseded`；本轮仅做 dry-run 和映射草案，不写 `DOC_STATE.yaml`，不移动文件。

## 7. W13 任务到模块映射

| 模块 | W13 候选任务域 | 当前判断 | 是否存在职责冲突 |
| --- | --- | --- | --- |
| M01 基础架构 / 平台规则 / 工程边界 | `WT13-02`、`WT13-20`、`WT13-21`、`WT13-22`、`WT13-23`、`WT13-24`、`WT13-25` | 承接壳层、工程边界、测试基线、数据 / API 基础和治理收口 | 无硬冲突，但不得把当前仓库直接写成已具备业务 monorepo |
| M02 身份 / 权限 / 团队 | `WT13-01`、`WT13-05`、`WT13-21` | 承接登录、session、角色、权限、记录可见范围 | 无硬冲突；旧 `/members` 闭合不等于正式候选 |
| M03 岗位 / 简历 / 文档 | `WT13-03`、`WT13-04`、`WT13-06`、`WT13-19` | 承接岗位、简历、发起必选输入、部分导出边界 | 无硬冲突；旧上传 / 导出链不得直开 |
| M04 问题生成 / 评分 | `WT13-06`、`WT13-13`、`WT13-16` | 承接岗位-简历绑定、评分证据、规则版本和主题推荐输入 | 无硬冲突；旧匹配分析不足以覆盖 W13 评分 |
| M05 RAG / 知识库 / 资产 | `WT13-10`、`WT13-18`、`WT13-20` | 承接知识库、检索、引用、资产归档和动态 schema 子集 | 无硬冲突；需从“资产库”扩展到一期 RAG 主链 |
| M06 模拟面试 / 上下文 / 面试台 | `WT13-05`、`WT13-06`、`WT13-07`、`WT13-09`、`WT13-12`、`WT13-15` | 承接记录列表、发起、面试台、压力面、多轮状态和模拟复盘 | 无硬冲突；旧单轮会话口径已不足 |
| M07 打磨 / 评估 / 进度 | `WT13-08`、`WT13-12`、`WT13-13`、`WT13-17`、`WT13-19` | 承接打磨模式、进展树、题级反馈和训练入口 | 无硬冲突；不得沿用固定轮次 |
| M08 复盘 | `WT13-05`、`WT13-09`、`WT13-14`、`WT13-15`、`WT13-18`、`WT13-19` | 承接真实 / 模拟复盘、逐题拆解、导出、归档入口 | 无硬冲突；需从骨架补到 W13 复盘事实源 |
| M09 薄弱项 / 训练机制 | `WT13-08`、`WT13-14`、`WT13-15`、`WT13-16`、`WT13-17` | 承接 `WeaknessItem`、证据、消减、训练抽屉和待打磨 | 无硬冲突；待打磨不能替代薄弱项中心 |
| M10 管理 / 运维 / 配置 | `WT13-01`、`WT13-10`、`WT13-11`、`WT13-18`、`WT13-20`、`WT13-21`、`WT13-22`、`WT13-24`、`WT13-25` | 承接 provider、日志、模型 catalog、snapshot、审计、配置和部署边界 | 无硬冲突；完整管理台仍需低干扰，不吞主链 |

结论：当前未发现必须立即重定义模块职责的硬冲突。需要做的是把 W13 任务域覆盖到 M01-M10，并在后续模块窗口按候选任务域同步模块文档。

## 8. 正式开窗顺序草案

| 阶段 | 目标 | 前置条件 | 可并行窗口 | 禁止并行窗口 | 验证命令 | 完成标准 | 需用户确认 | 是否可进入实现 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 阶段 1：设计 / contract 任务 | 冻结 ID 规则、旧 ST 策略、任务边界、API / 数据 / UI contract | 用户确认本文件确认卡；W13-E2 预检 ID 格式 | 任务 ID 复核、模块映射复核、API contract 草案、UI IA 复核 | 任何业务实现、目录创建、状态层写入 | `validate-state`、`evaluate-state`、关键词回归 | `TASK_INDEX.md` / `MODULE_INDEX.md` 有确认后的候选任务边界 | 是 | 否 |
| 阶段 2：基础工程骨架任务 | 建立最小 monorepo / API / web / shared / test 骨架 | `DOC_STATE.yaml` 写入新任务或明确临时开窗策略；用户确认允许目录创建 | 前端壳层、后端骨架、shared contract、测试矩阵 | 真实业务逻辑、真实 LLM、数据库 schema 大改 | `validate-state`、`evaluate-state`、后续构建 / 测试命令 | 骨架可运行，未越过业务边界 | 是 | 仅在 W13-E2 后可能 |
| 阶段 3：数据与权限任务 | 落地用户、角色、权限、岗位、简历、记录保存 | API / 数据 contract 已确认，schema 迁移策略已确认 | Auth、Job、Resume、SessionRecord 可并行但需统一 schema | RAG / LLM / 评分提前接入 | `validate-state`、`evaluate-state`、后续 API / DB 测试 | 权限隔离、服务端保存和基础列表可验收 | 是 | 仅正式开窗后 |
| 阶段 4：核心面试 / LLM / RAG 任务 | 落地发起、面试台、真实 LLM、RAG、上下文状态机 | 数据与权限最低链路通过 | LLM adapter、RAG、面试台 UI、状态机可拆窗 | 评分 / 复盘在证据模型未稳前抢跑 | `validate-state`、`evaluate-state`、后续 interview / RAG / LLM 测试 | 可发起并完成打磨 / 压力面核心流程，引用和失败态可见 | 是 | 仅正式开窗后 |
| 阶段 5：评分 / 复盘 / 训练闭环任务 | 落地评分、真实复盘、模拟复盘、WeaknessItem、训练抽屉、资产归档 | 核心面试、RAG、证据模型可用 | 评分、复盘、训练、资产可并行但需共享 evidence | 导出在复盘内容未稳定前最终验收 | `validate-state`、`evaluate-state`、后续 scoring / review / training 测试 | 多维评分可解释，复盘可训练，资产归档可追溯 | 是 | 仅正式开窗后 |
| 阶段 6：导出 / 观测 / 验收任务 | 完成 Markdown 导出、日志观测、DoD、收口写回 | 评分 / 复盘 / 训练闭环稳定 | 导出、观测、E2E、文档收口可并行 | 新增大范围产品功能 | `validate-state`、`evaluate-state`、`python -m tools.test_runner.run_tests`、后续 web / API 测试 | 产品、数据、UI、工程、收口五层 DoD 通过 | 是 | 仅正式开窗后 |

## 9. 各类任务窗口边界模板

### 9.1 前端窗口模板

- 允许修改范围：`apps/web/**`、必要的 `packages/shared/**`、对应页面文档。
- 禁止修改范围：`docs/governance/DOC_STATE.yaml`、`tools/**`、`tests/**`，除非该窗口被明确授权写测试。
- 输入文档：W13 IA、对象模型、评分 / 复盘 DoD、任务包边界。
- 验证命令：`validate-state`、`evaluate-state`、后续 `npm.cmd run web:test`、`npm.cmd run web:build`。
- 完成标准：页面符合 IA，错误态 / 空状态完整，不越过 API / 数据 contract。
- Basic Memory / Superpowers 写回：通常不在模块实现窗写回；由收口窗口统一写。

### 9.2 后端窗口模板

- 允许修改范围：`apps/api/**`、必要的 `packages/shared/**`、对应 API 文档。
- 禁止修改范围：未授权的前端页面、`infra/**`、`DOC_STATE.yaml`。
- 输入文档：对象模型、API / 后端服务边界、权限和数据 contract。
- 验证命令：`validate-state`、`evaluate-state`、后续 API 单测 / 集成测试。
- 完成标准：接口输入输出、错误态、权限态、审计和测试覆盖闭合。
- Basic Memory / Superpowers 写回：重大后端 contract 变更由总控或收口窗口写回。

### 9.3 RAG / 知识库窗口模板

- 允许修改范围：`apps/api/**`、`apps/web/**` 中知识库和引用展示相关路径、M05 文档。
- 禁止修改范围：无关评分公式、完整资产中心、未授权 provider 密钥配置。
- 输入文档：W13 对象模型第 12 节、IA 知识库入口、评分证据边界。
- 验证命令：`validate-state`、`evaluate-state`、后续检索、引用、失败降级测试。
- 完成标准：知识库可见范围、检索、引用、无命中 / 失败提示可验收。
- Basic Memory / Superpowers 写回：若确认检索路线或权限策略，需后续写回。

### 9.4 LLM provider 窗口模板

- 允许修改范围：`apps/api/**` provider adapter、`packages/shared/**` provider contract、M10 文档。
- 禁止修改范围：明文密钥、未授权 provider 扩展、无证据评分逻辑。
- 输入文档：W13 对象模型第 14 节、`FC-04`、日志 / 审计边界。
- 验证命令：`validate-state`、`evaluate-state`、后续 provider adapter 测试。
- 完成标准：默认真实 provider 可用，失败可重试，脱敏记录和模板版本可追踪。
- Basic Memory / Superpowers 写回：provider 选型若由用户 confirmed，需要写入决策层。

### 9.5 评分 / 复盘窗口模板

- 允许修改范围：评分、复盘、证据、训练建议相关 API / UI / 文档。
- 禁止修改范围：绕过证据模型、将推荐公式写成不可变 confirmed、完整 PDF。
- 输入文档：评分 / 复盘 / 导出 / DoD 文档、对象模型第 8 至 13 节。
- 验证命令：`validate-state`、`evaluate-state`、后续 scoring / review 测试。
- 完成标准：评分可解释、证据可追溯、复盘可读、训练动作可进入抽屉。
- Basic Memory / Superpowers 写回：若形成新的评分公式决策，需要后续写回。

### 9.6 权限 / 登录窗口模板

- 允许修改范围：auth API、session、角色、权限 guard、登录 UI。
- 禁止修改范围：复杂成员管理中心、无确认的组织模型扩展。
- 输入文档：W13 scope、IA、对象模型、`FC-02`。
- 验证命令：`validate-state`、`evaluate-state`、后续 auth 测试。
- 完成标准：未登录、普通用户、管理员、无权限状态均可验收。
- Basic Memory / Superpowers 写回：权限模型若发生 confirmed 变更，需写回。

### 9.7 数据存储窗口模板

- 允许修改范围：schema、migration、repository、数据 contract、对应测试。
- 禁止修改范围：业务 UI 大改、无确认的数据保留策略、`DOC_STATE.yaml`。
- 输入文档：对象模型第 3 至 4 节、`FC-03`、API contract。
- 验证命令：`validate-state`、`evaluate-state`、后续 migration / repository 测试。
- 完成标准：核心对象可保存、版本可追踪、权限隔离生效。
- Basic Memory / Superpowers 写回：schema 边界若上升为长期决策，需写回。

### 9.8 导出窗口模板

- 允许修改范围：导出 API、复盘详情导出 UI、`ExportSnapshot` 相关路径。
- 禁止修改范围：完整 PDF、批量导出中心、无权限原文导出。
- 输入文档：评分 / 复盘 / 导出 / DoD 第 9 节、`FC-12`。
- 验证命令：`validate-state`、`evaluate-state`、后续 export 测试。
- 完成标准：复制和 Markdown 下载可用，权限限制和内容范围可解释。
- Basic Memory / Superpowers 写回：导出范围如被用户调整，需写回。

### 9.9 运维 / 部署窗口模板

- 允许修改范围：后续正式授权的 `infra/**`、配置样例、日志 / 观测代码、M10 文档。
- 禁止修改范围：当前 W13-E 禁止创建 `infra/**`；密钥不得明文。
- 输入文档：对象模型第 16 节、`FC-01`、`FC-18`。
- 验证命令：`validate-state`、`evaluate-state`、后续 ops smoke / 配置测试。
- 完成标准：部署目标、日志、审计、成本和配置边界可验收。
- Basic Memory / Superpowers 写回：部署目标 confirmed 后需写回。

### 9.10 文档收口窗口模板

- 允许修改范围：根索引、W13 计划文档、必要的模块摘要、Basic Memory 写回。
- 禁止修改范围：业务代码、`tools/**`、`tests/**`、未确认的 `DOC_STATE.yaml`。
- 输入文档：AGENTS、DOC_GOVERNANCE、DOC_AUTOMATION、当前任务产物。
- 验证命令：`validate-state`、`evaluate-state`、关键词回归、必要时 Basic Memory 回读。
- 完成标准：状态、进展、成熟度、确认卡和下一窗口边界一致。
- Basic Memory / Superpowers 写回：需要；但本 W13-E 窗口明确禁止写 Basic Memory。

## 10. `DOC_STATE.yaml` 后续改造方案

本窗口不修改 `DOC_STATE.yaml`。后续状态层改造建议如下：

1. 用户已确认任务 ID 命名采用 `WT13-xx`，旧 `STxx_*` 后续映射为 `superseded`，且暂不直接写 `DOC_STATE.yaml`，先做 W13-E2 dry-run。
2. W13-E2 已读取并核对 `schema.py`、`validate.py`、`evaluate.py`、`confirm.py` 当前实现，确认当前状态层不直接接受非 `STxx_yy` 的 subtask ID。
3. 先做 preview / dry-run：构造候选 state patch 或临时样例，运行 `validate-state` / `evaluate-state`，不直接覆盖正式 `DOC_STATE.yaml`。
4. 若工具只接受 `STxx_yy`，需要在用户确认后选择：
   - 修改工具 schema 支持 `WT13-xx`；
   - 或在状态层采用兼容 ID，并在索引层保留 `WT13-xx` 业务别名。
5. 新任务写入需覆盖 requirement / module / subtask 的关系一致性，避免 `RQ01` 历史 requirement 被误用为 W13 新主需求。
6. 旧 `STxx_*` 不应直接删除。应先标记为 `superseded` / `historical-reference`，再逐步解除 `DOC_STATE.yaml`、`TASK_INDEX.md`、`MODULE_INDEX.md` 引用。
7. 已关闭 round 中的 `DOC-SPEC-P1 / DOC-PLAN-P1` 历史引用不应修改。
8. 旧 `STxx_*` 迁移 archive 的时间点应在状态层、任务索引和模块索引均不再引用之后。

受 schema 限制的字段包括：

- `global_policy.formal_window_open`
- `candidate_status`
- `readiness`
- `implementation_doc_state`
- `blocker_refs`
- `facts.upstream_module_ids`
- `facts.requirement_ids` / requirement 容器关系
- document entity 的 `status`、`kind`、`active_round_id`、`last_round_id`

### 10.1 `DOC_STATE.yaml` 写入确认卡

**问题：W13 任务树是否应在下一窗口写入 `DOC_STATE.yaml`？**

| 方案 | 内容 | 解决 | 限制 | 风险 | 后续影响 |
| --- | --- | --- | --- | --- | --- |
| A | 暂不写 `DOC_STATE.yaml`，只更新 `TASK_INDEX.md` / `MODULE_INDEX.md` 和 task-remap 草案 | 风险最低 | 状态层仍旧 | 不能进入正式开窗 | 需要 W13-E2 |
| B | 下一窗口写入 `DOC_STATE.yaml` 的 W13 新任务，但暂不移除旧 `STxx_*` | 开始建立新状态层 | 新旧并存 | 评估规则可能出现新 blocker | 需要精细 validate/evaluate |
| C | 下一窗口同时写入 W13 新任务并移出旧 `STxx_*` | 最彻底 | 风险最高 | 可能破坏现有状态层和索引 | 需要强回退方案 |
| D | 自定义方案 | 由用户补充 | 待定义 | 待评估 | 待评估 |

推荐方案：A。

推荐理由：先完成 task-remap 草案和用户确认，再写 `DOC_STATE.yaml`，更符合当前高风险状态层修改节奏。

当前状态：用户已确认采用方案 A 作为 W13-E2 前置动作；W13-E2 不写 `DOC_STATE.yaml`。用户后续又确认第 10.4 节方案 B，W13-E3 已创建独立 Preview YAML；W13-E4-B 已在正式 `DOC_STATE.yaml` 中写入 `ST13_01~ST13_25`，旧 `STxx_*` 保留。

### 10.2 `WT13-xx` 兼容性检查结论

本轮只读检查结果如下：

- `tools/doc_governor/naming_rules.py` 当前定义 `SUBTASK_ID_RE = ^ST\d{2}_\d{2}$`。
- `tools/doc_governor/schema.py` 的 `TYPED_BLOCKER_REF_RE` 当前只接受 `subtask:ST\d{2}_\d{2}`，不接受 `subtask:WT13-xx`。
- `tools/doc_governor/validate.py` 会校验 `subtasks` 容器 key 必须匹配 `SUBTASK_ID_RE`；因此把 `WT13-xx` 直接写入 `DOC_STATE.yaml.subtasks` 会被 `validate-state` 拒绝。
- `tools/doc_governor/requirement_scan.py` 只把 `TASK_INDEX.md` 中匹配 `RQ\d{2}`、`M\d{2}`、`ST\d{2}_\d{2}` 的行纳入 requirement / module / subtask 关系扫描；`WT13-xx` 行在当前状态扫描链路中会被忽略。
- `tools/doc_governor/artifact_policy.py` 当前子任务目录模式仍是 `ST\d{2}_\d{2}-...`；因此 `WT13-xx` 不能直接作为现有子任务目录发现规则。

结论：

1. `WT13-xx` 与当前文档层的 W13 候选任务域命名兼容。
2. `WT13-xx` 直接写入 `DOC_STATE.yaml.subtasks` 看起来不兼容，预计会被 `validate-state` 拒绝。
3. `WT13-xx` 只写入 `TASK_INDEX.md` / `MODULE_INDEX.md` 时，`validate-state` 不会因其存在而失败，但当前 `evaluate-state` 不会把它识别为正式 subtask。
4. 不建议本窗口自行改用 `ST13_xx` 或其他命名；应保持用户已确认的 `WT13-xx` 为业务候选 ID，同时在 W13-E3 用 preview YAML 验证“状态层兼容 ID / 业务别名”或“工具 schema 扩展”方案。
5. 状态写入前应先创建单独 preview YAML，不直接覆盖正式 `DOC_STATE.yaml`。

### 10.3 旧 `STxx_*` 到 `WT13` 映射 dry-run

| 旧任务 ID | 旧任务名称或路径 | 所属模块 | 当前状态层角色 | 建议分类 | 映射到 WT13 | 可复用信息 | 是否可后续归档 | 风险 | 后续动作 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `ST01_01` | 运行环境与仓库基线 | M01 | state-bound / blocked subtask | historical-reference + reusable-evidence + state-bound + superseded-candidate + archive-candidate | `WT13-20`、`WT13-21`、`WT13-24`、`WT13-25` | 工程基线、运行环境、仓库约束 | 是，解除状态与索引引用后 | 直接归档会断开状态层引用 | W13-E3 先建新任务 preview，再决定 superseded 写法 |
| `ST01_02` | 工作台壳层与 i18n 基线 | M01 | state-bound / blocked subtask | historical-reference + reusable-evidence + state-bound + superseded-candidate + archive-candidate | `WT13-02`、`WT13-23` | 壳层、导航、i18n 最小层 | 是，解除状态与索引引用后 | 可能被误读为可直接扩展 W10 原型 | 保留为参考，后续映射到工作台 UI 任务 |
| `ST01_03` | 测试、日志与文档治理基线 | M01 | state-bound / blocked subtask | historical-reference + reusable-evidence + state-bound + superseded-candidate + archive-candidate | `WT13-22`、`WT13-24`、`WT13-25` | 测试治理、日志、文档收口 | 是，解除状态与索引引用后 | 不能替代 W13 DoD 测试矩阵 | 后续由测试 / 治理任务吸收 |
| `ST02_01` | 鉴权机制与会话边界（旧入口） | M02 | state-bound / blocked subtask | historical-reference + reusable-evidence + state-bound + superseded-candidate + archive-candidate | `WT13-01`、`WT13-21` | session、鉴权边界 | 是，解除状态与索引引用后 | 旧入口不足以覆盖 W13 登录 / 权限 | 后续按账号 / 权限任务重建 |
| `ST02_02` | 团队、用户与成员目录（旧入口） | M02 | state-bound / blocked subtask | historical-reference + reusable-evidence + state-bound + superseded-candidate + archive-candidate | `WT13-01`、`WT13-21` | 用户、成员目录、可见范围参考 | 是，解除状态与索引引用后 | 可能把完整团队协作提前做大 | 后续只吸收一期最小角色与记录可见范围 |
| `ST02_03` | 授权矩阵与管理员/成员边界（旧入口） | M02 | state-bound / blocked subtask | historical-reference + reusable-evidence + state-bound + superseded-candidate + archive-candidate | `WT13-01`、`WT13-22` | 权限矩阵、审计边界 | 是，解除状态与索引引用后 | 权限消费边界仍需模块层复核 | 后续写入权限 / 审计任务边界 |
| `ST03_01` | 岗位域与页面（旧入口） | M03 | state-bound / blocked subtask | historical-reference + reusable-evidence + state-bound + superseded-candidate + archive-candidate | `WT13-03`、`WT13-06`、`WT13-23` | 岗位对象、页面、发起输入 | 是，解除状态与索引引用后 | 不能恢复 W10 手工 JD 单页主链 | 后续按岗位管理与发起流程重切 |
| `ST03_02` | 简历域、版本与编辑器（旧入口） | M03 | state-bound / blocked subtask | historical-reference + reusable-evidence + state-bound + superseded-candidate + archive-candidate | `WT13-04`、`WT13-06`、`WT13-23` | 简历对象、版本、编辑器 | 是，解除状态与索引引用后 | 上传 / 编辑边界可能被旧口径误导 | 后续按服务端保存和版本管理重建 |
| `ST03_03` | 上传、转换与导出链路（旧入口） | M03 | state-bound / blocked subtask | historical-reference + reusable-evidence + state-bound + superseded-candidate + archive-candidate | `WT13-04`、`WT13-19`、`WT13-20` | 上传、转换、导出链参考 | 是，解除状态与索引引用后 | 不得直接放行旧上传 / 导出实现 | 后续拆到简历管理、导出和数据持久化 |
| `ST04_01` | 岗位-简历绑定与输入契约 | M04 | state-bound / blocked subtask | historical-reference + reusable-evidence + state-bound + superseded-candidate + archive-candidate | `WT13-06`、`WT13-13`、`WT13-21` | 绑定关系、输入契约 | 是，解除状态与索引引用后 | 旧契约不足以覆盖 RAG / 多轮 | 后续纳入发起流程、评分和 API contract |
| `ST04_02` | 匹配分析、评分与证据 | M04 | state-bound / blocked subtask | historical-reference + reusable-evidence + state-bound + superseded-candidate + archive-candidate | `WT13-13`、`WT13-16` | 评分证据、分析口径 | 是，解除状态与索引引用后 | 旧评分不足以覆盖 W13 `0-100` 多维评分 | 后续纳入评分体系与薄弱项任务 |
| `ST04_03` | 分析展示与训练入口 | M04 | state-bound / blocked subtask | historical-reference + reusable-evidence + state-bound + superseded-candidate + archive-candidate | `WT13-17`、`WT13-23` | 展示入口、训练入口参考 | 是，解除状态与索引引用后 | 不能替代训练抽屉和复盘闭环 | 后续纳入训练抽屉与页面集合 |
| `ST05_01` | 资产类型与资产域 | M05 | state-bound / blocked subtask | historical-reference + reusable-evidence + state-bound + superseded-candidate + archive-candidate | `WT13-18` | 资产类型、动态字段 | 是，解除状态与索引引用后 | 完整资产中心可能提前做大 | 后续纳入一期最小资产归档 |
| `ST05_02` | 归档记录与来源追踪 | M05 | state-bound / blocked subtask | historical-reference + reusable-evidence + state-bound + superseded-candidate + archive-candidate | `WT13-18`、`WT13-20` | 来源追踪、归档记录 | 是，解除状态与索引引用后 | 归档与持久化边界需统一 | 后续纳入资产归档和数据库任务 |
| `ST05_03` | 检索分块与索引入库 | M05 | state-bound / blocked subtask | historical-reference + reusable-evidence + state-bound + superseded-candidate + archive-candidate | `WT13-10`、`WT13-20` | chunk、索引、入库参考 | 是，解除状态与索引引用后 | 不能代表 W13 混合检索完整策略 | 后续纳入 RAG / 知识库和数据任务 |
| `ST06_01` | 面试会话创建与列表 | M06 | state-bound / blocked subtask | historical-reference + reusable-evidence + state-bound + superseded-candidate + archive-candidate | `WT13-05`、`WT13-06`、`WT13-07` | 会话创建、列表、入口 | 是，解除状态与索引引用后 | 旧单轮会话口径不足 | 后续纳入记录列表、发起和面试台 |
| `ST06_02` | 上下文包与问题来源规则 | M06 | state-bound / blocked subtask | historical-reference + reusable-evidence + state-bound + superseded-candidate + archive-candidate | `WT13-06`、`WT13-07`、`WT13-10`、`WT13-11`、`WT13-12` | 上下文包、问题来源、参考材料 | 是，解除状态与索引引用后 | 不得绕过真实 LLM / RAG / 状态机 | 后续拆入发起、面试台、RAG、LLM 和多轮状态 |
| `ST06_03` | 消息 Trace、报告与导出 | M06 | state-bound / blocked subtask | historical-reference + reusable-evidence + state-bound + superseded-candidate + archive-candidate | `WT13-12`、`WT13-15`、`WT13-19`、`WT13-22` | trace、报告、导出参考 | 是，解除状态与索引引用后 | 旧简版报告不能替代复盘 | 后续纳入状态机、模拟复盘、导出和观测 |
| `ST07_01` | 打磨主题推荐与启动 | M07 | state-bound / blocked subtask | historical-reference + reusable-evidence + state-bound + superseded-candidate + archive-candidate | `WT13-08`、`WT13-16`、`WT13-17` | 主题推荐、启动入口 | 是，解除状态与索引引用后 | 不得固定轮次或替代 ProgressTree | 后续纳入打磨模式、薄弱项和训练抽屉 |
| `ST07_02` | 能力树蓝图与节点状态 | M07 | state-bound / blocked subtask | historical-reference + reusable-evidence + state-bound + superseded-candidate + archive-candidate | `WT13-08`、`WT13-16` | 能力树、节点状态 | 是，解除状态与索引引用后 | 能力树不能覆盖薄弱项中心 | 后续纳入打磨模式和 WeaknessItem |
| `ST07_03` | 逐题评估与进度快照 | M07 | state-bound / blocked subtask | historical-reference + reusable-evidence + state-bound + superseded-candidate + archive-candidate | `WT13-08`、`WT13-13`、`WT13-16`、`WT13-17` | 题级评估、进度快照 | 是，解除状态与索引引用后 | 旧简版反馈不足以覆盖 W13 评分 | 后续纳入打磨、评分、薄弱项和训练入口 |
| `ST08_01` | 复盘总对象与列表/详情 | M08 | state-bound / blocked subtask | historical-reference + reusable-evidence + state-bound + superseded-candidate + archive-candidate | `WT13-14`、`WT13-15`、`WT13-18`、`WT13-19` | 复盘对象、列表、详情 | 是，解除状态与索引引用后 | 需区分真实复盘和模拟复盘 | 后续拆入复盘、资产和导出任务 |
| `ST08_02` | 真实面试导入与逐题分析 | M08 | state-bound / blocked subtask | historical-reference + reusable-evidence + state-bound + superseded-candidate + archive-candidate | `WT13-14`、`WT13-16` | 逐字稿导入、逐题分析 | 是，解除状态与索引引用后 | 不能要求用户先手工拆题 | 后续纳入真实面试复盘和薄弱项 |
| `ST08_03` | 模拟面试复盘回放与导出 | M08 | state-bound / blocked subtask | historical-reference + reusable-evidence + state-bound + superseded-candidate + archive-candidate | `WT13-15`、`WT13-18`、`WT13-19` | 模拟复盘、回放、导出 | 是，解除状态与索引引用后 | 旧回放不能替代完整评分复盘 | 后续纳入模拟复盘、资产归档和导出 |
| `ST09_01` | 薄弱项聚合与训练中心 | M09 | state-bound / blocked subtask | historical-reference + reusable-evidence + state-bound + superseded-candidate + archive-candidate | `WT13-16` | 薄弱项聚合 | 是，解除状态与索引引用后 | 不得把完整训练中心提前做大 | 后续纳入 WeaknessItem 任务 |
| `ST09_02` | 训练抽屉与待打磨入列 | M09 | state-bound / blocked subtask | historical-reference + reusable-evidence + state-bound + superseded-candidate + archive-candidate | `WT13-17` | 训练抽屉、待打磨入列 | 是，解除状态与索引引用后 | 训练执行层不能替代薄弱项中心 | 后续纳入训练抽屉任务 |
| `ST09_03` | 生命周期、消减与停练规则 | M09 | state-bound / blocked subtask | historical-reference + reusable-evidence + state-bound + superseded-candidate + archive-candidate | `WT13-16`、`WT13-17` | 消减、停练、生命周期 | 是，解除状态与索引引用后 | 状态规则需与评分证据绑定 | 后续纳入 WeaknessItem 和训练抽屉 |
| `ST10_01` | 成员治理与角色操作 | M10 | state-bound / blocked subtask | historical-reference + reusable-evidence + state-bound + superseded-candidate + archive-candidate | `WT13-01`、`WT13-22` | 管理员角色、审计参考 | 是，解除状态与索引引用后 | 完整成员管理后置 | 后续纳入权限和观测任务 |
| `ST10_02` | 模型目录、评分规则与系统设置 | M10 | state-bound / blocked subtask | historical-reference + reusable-evidence + state-bound + superseded-candidate + archive-candidate | `WT13-11`、`WT13-13`、`WT13-22` | 模型 catalog、评分规则、配置 | 是，解除状态与索引引用后 | 不得把在线模型同步写入一期主链 | 后续纳入 LLM provider、评分和运维 |
| `ST10_03` | 可观测性、CI/E2E 与 snapshot 运维 | M10 | state-bound / blocked subtask | historical-reference + reusable-evidence + state-bound + superseded-candidate + archive-candidate | `WT13-22`、`WT13-24`、`WT13-25` | 观测、CI/E2E、snapshot 运维 | 是，解除状态与索引引用后 | 不能替代完整 DoD 和状态层治理 | 后续纳入日志 / 观测、测试和文档治理 |

### 10.4 W13-E3 写入路径确认卡

问题：W13-E3 是否允许写入 `DOC_STATE.yaml`？

背景：W13-E2 已确认 `WT13-xx` 不能直接作为当前 `DOC_STATE.yaml.subtasks` key；旧 `STxx_*` 后续映射为 `superseded` 已确认。W13-E4-B 阶段 1 只并存写入新 `ST13_*`，暂不表达旧任务 superseded。

| 方案 | 解决什么 | 限制 | 风险 | 后续影响 |
| --- | --- | --- | --- | --- |
| A：仍不写 `DOC_STATE.yaml`，只维护 `TASK_INDEX` / `MODULE_INDEX` / task-remap / backlog-roadmap | 风险最低 | 仍不能进入正式开窗 | 状态层仍旧 | 适合继续设计和任务治理 |
| B：下一窗口创建 preview YAML，不修改正式 `DOC_STATE.yaml` | 可以验证结构而不污染正式状态 | 仍需后续 apply | preview 与正式状态可能有差异 | 推荐作为下一步 |
| C：下一窗口直接向 `DOC_STATE.yaml` 写入 W13 新任务，但不移除旧 `STxx_*` | 开始建立正式 W13 状态层 | 新旧并存 | 可能产生新的 blocker | 需要强验证和回退方案 |
| D：自定义方案 / 其他 | 由用户补充 | 待定义 | 待评估 | 待评估 |

推荐方案：B。

推荐理由：符合 dry-run 目标，风险低，可验证 `WT13-xx`、状态层兼容 ID / 业务别名和旧 `STxx_*` superseded 表达是否兼容。

当前确认结果：用户已确认方案 B；W13-E3 已创建 `docs/superpowers/plans/2026-04-25-workbench-mvp-doc-state-preview.yaml`。该轮未修改正式 `DOC_STATE.yaml`，后续 W13-E4-B 已执行阶段 1 正式写入。

### 10.5 W13-E4-A C-Phased State Write 计划

用户已确认采用方案 C 的分阶段版本：最终把 `ST13_01~ST13_25` 写入正式 `DOC_STATE.yaml`，并将旧 `STxx_*` 标记为 `superseded / historical-reference` 或移出正式任务容器，但不得一次性粗暴切换。

W13-E4-A 已新增 [`2026-04-25-workbench-mvp-state-write-plan.md`](2026-04-25-workbench-mvp-state-write-plan.md)，作为后续 State Write 的阶段计划、验证矩阵、回退方案和确认卡入口。该计划本身不修改正式 `DOC_STATE.yaml`，不放行实现；W13-E4-B 已按阶段 1 执行正式状态层写入，W13-E4-C 已按阶段 2 执行旧任务 facts historical / superseded 表达，W13-E4-D 已完成阶段 3 dry-run / 影响分析并新增 [`2026-04-25-workbench-mvp-state-write-stage3-dry-run.md`](2026-04-25-workbench-mvp-state-write-stage3-dry-run.md)，W13-E4-E 已创建并验证 [`2026-04-25-workbench-mvp-doc-state-stage3-preview.yaml`](2026-04-25-workbench-mvp-doc-state-stage3-preview.yaml)，W13-E4-F 已新增 [`2026-04-25-workbench-mvp-state-write-stage3.md`](2026-04-25-workbench-mvp-state-write-stage3.md) 并正式完成 Stage 3 写入。

当前推荐执行顺序：

1. 阶段 1：`W13-E4-B` 已写入 `ST13_01~ST13_25`，但不移除旧 `STxx_*`。
2. 阶段 2：`W13-E4-C` 已完成，旧 `STxx_*` 标记为 `superseded / historical-reference`，仍不迁移 archive。
3. 阶段 3：`W13-E4-D` 已完成 dry-run，`W13-E4-E` 已完成 Stage3 Preview，`W13-E4-F` 已完成正式写入；正式状态层已验证旧 `STxx_*` 移出、`RQ01.facts.task_ids` 移除旧 `ST01_01` / `ST09_03` 后仍为 `ok=true,error=0,warning=0`。
4. 阶段 4：只做旧 `STxx_*` archive 迁移准备，不直接迁移。

当前确认结果：

- `OQ-094=B`：允许 `W13-E4-B` 执行阶段 1，只写入新任务并保留旧任务。
- `OQ-095`：阶段 1 按 C 只并存新旧任务；阶段 2 按 B 再表达旧 `STxx_*` superseded / historical-reference。
- `OQ-096=B`：创建 State Write 变更说明和回退说明，不复制正式 `DOC_STATE.yaml`。
- `OQ-097~OQ-099`：由 `W13-E4-D` 新增，用户已确认进入 Stage3 Preview 路径；`W13-E4-E` 已创建 Stage3 Preview YAML，并验证旧 `ST01_01`、`ST09_03` 从 preview `RQ01.facts.task_ids` 移除后的状态层结果。
- `OQ-100`：用户已确认方案 B；`W13-E4-F` 已正式移出旧 `STxx_*` 并从正式 `RQ01.facts.task_ids` 移除旧 `ST01_01`、`ST09_03`。

## 11. 需要用户确认的问题

| 确认卡 ID | 问题 | 推荐方案 | 当前状态 | 写回位置建议 |
| --- | --- | --- | --- | --- |
| `W13-E-Q1` | W13 工作台级任务 ID 如何命名？ | A: `WT13-xx` | `confirmed` | 已吸收为候选任务域命名；状态层写入仍需 W13-E3 preview / write 决策 |
| `W13-E-Q2` | 旧 `STxx_*` 在 W13 Task Remap 中如何处理？ | B: 新任务树建立后映射为 `superseded`，后续状态层迁移 | `confirmed` | 已形成本文件第 10.3 节映射草案；阶段 1 已写入新 `ST13_*`，阶段 2 已写入旧任务 facts historical / superseded |
| `W13-E-Q3` | W13 任务树是否应在下一窗口写入 `DOC_STATE.yaml`？ | A: 暂不写，先完成 W13-E2 dry-run | `confirmed` | 本轮执行 W13-E2，不修改 `DOC_STATE.yaml` |
| `W13-E2-Q1` | W13-E3 是否允许写入 `DOC_STATE.yaml`？ | B: 先创建 preview YAML，不修改正式状态 | `confirmed` | 用户已确认方案 B；W13-E3 已创建 Preview YAML，后续 State Write 仍需另开确认 |
| `W13-E4-Q1` | 是否允许 W13-E4-B 写入 `ST13_01~ST13_25`，但不移除旧 `STxx_*`？ | B: 写入新任务，不移除旧任务 | `confirmed` | 对应 `OQ-094=B`；阶段 1 已执行 |
| `W13-E4-Q2` | 旧 `STxx_*` superseded 表达方式 | 第一阶段 C，第二阶段 B | `confirmed` | 对应 `OQ-095`；阶段 1 不处理旧任务 superseded，阶段 2 已由 `W13-E4-C` 完成 |
| `W13-E4-Q3` | 是否创建正式 State Write 备份文件 | B: 创建变更说明和回退说明，不复制 `DOC_STATE` | `confirmed` | 对应 `OQ-096=B`；已新增阶段 1 变更说明和回退说明 |
| `W13-E4-D-Q1` | 是否创建 Stage3 Preview YAML？ | B: 下一窗口创建 Preview YAML，不修改正式 `DOC_STATE.yaml` | `confirmed` | 对应 `OQ-097`；用户已确认，W13-E4-E 已创建并验证 preview |
| `W13-E4-D-Q2` | 旧 `STxx_*` 移出策略 | 先做 B 的 preview，再决定是否正式移出 | `confirmed` | 对应 `OQ-098`；用户已确认先做 Preview，不正式移出旧任务 |
| `W13-E4-D-Q3` | `RQ01.facts.task_ids` 中旧任务处理 | B: preview 中移除 `ST01_01`、`ST09_03`，只保留 `ST13_01~ST13_25` | `confirmed` | 对应 `OQ-099`；用户已确认在 Preview 中验证，本轮未修改正式 `RQ01.facts.task_ids` |
| `W13-E4-E-Q1` | 是否基于 Stage3 Preview 执行正式 Stage 3？ | B: 正式移出旧 `STxx_*` 并同步改写 `RQ01.facts.task_ids` | `confirmed` | 对应 `OQ-100`；用户已确认，W13-E4-F 已执行正式 Stage 3 |

### 11.1 W13-E5 readiness audit 后续确认卡

`W13-E5` 已新增 [`2026-04-25-workbench-mvp-st13-readiness-audit.md`](2026-04-25-workbench-mvp-st13-readiness-audit.md)。该审计确认 `ST13_01~ST13_25` 均仍不是 implementation-ready；`ST13_20`、`ST13_21`、`ST13_24`、`ST13_25` 仅作为下一窗口任务包草案候选。

新增 `OQ-101~OQ-110` 用于确认：

- 是否允许生成 ST13 任务包。
- ST13 任务包生成顺序。
- 哪些 ST13 可先做 contract。
- 是否允许创建 ST13 专属子任务文档。
- 是否允许创建 `apps/api/**`、`apps/web/**` 或 `infra/**`。
- 是否允许生成 implementation packet。
- formal window 何时打开。
- 任务包准备与实现是否拆窗。
- API contract 与 UI skeleton 的先后。
- 后端与前端准备顺序。

当前状态：已由 W13-E6 全部确认；确认结果见下节。

### 11.2 W13-E6 用户确认吸收

用户已确认：

- `OQ-101=A`：先只生成 `ST13_21 / ST13_20 / ST13_24 / ST13_25` 四个横向 contract / 测试 / 治理任务包草案。
- `OQ-102=A`：横向 contract 先行。
- `OQ-103=A`：第一批只做 `ST13_21 / ST13_20 / ST13_24 / ST13_25`。
- `OQ-104=B`：先在 `docs/superpowers/plans/**` 生成任务包草案，不创建模块子任务目录。
- `OQ-105=A`：formal window 和 implementation packet 前禁止创建 `apps/api/**`、`apps/web/**` 或 `infra/**`。
- `OQ-106=A`：所有 P0 gate 补齐前禁止生成 implementation packet。
- `OQ-107=A`：逐个 ST13 在任务包、双文档、验收、测试和用户确认齐备后再打开 formal window。
- `OQ-108=A`：任务包准备与实现严格拆窗。
- `OQ-109=A`：API contract 先行。
- `OQ-110=C`：后端 contract 与前端页面规格可并行准备，等 contract 合并后再实现。

W13-E6 已新增 [`2026-04-25-workbench-mvp-st13-first-contract-task-packages.md`](2026-04-25-workbench-mvp-st13-first-contract-task-packages.md)。该文档只是任务包草案，不是 implementation packet，不表示 formal window open 或 implementation-ready。

## 12. 当前不进入实现说明

当前不能进入实现，原因是：

- `WT13-xx` 任务域命名虽已 confirmed，但当前 `doc_governor` 状态层不直接接受 `WT13-xx` 作为 `subtasks` key。
- 旧 `STxx_*` 后续映射为 `superseded` 已在阶段 2 通过 facts 写入；阶段 3 已由 `W13-E4-F` 正式执行，旧任务不再留在 formal current `subtasks` 容器中。
- `DOC_STATE.yaml` 已登记 `ST13_01~ST13_25`，但这些入口仍为 blocked / review-required 状态。
- `formal_window_open=false`。
- 30 个旧 `STxx_*` 已从 formal current `subtasks` 容器移出，且不应被误认为 W13 新任务或 current implementation entry。
- 未来实现窗口还需要明确允许修改范围、禁止修改范围、验证命令和 DoD。

因此，本文档完成后可进入 archive 迁移评估或任务包 / 子任务文档准备；不能直接进入业务代码实现窗口。

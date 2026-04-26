# AI 模拟面试一期工作台 MVP ST13 readiness audit

## 1. 背景

本文档记录 `W13-E5 / ST13 任务包准备前置审计` 结果。审计目标是检查 `ST13_01~ST13_25` 从“正式状态层任务入口”进入“任务包准备候选”之前还缺什么。

本窗口只做前置审计、缺口识别、依赖排序、任务包准备建议和用户确认卡输出。

本窗口明确不做：

- 不写代码。
- 不进入实现。
- 不创建 `apps/**`、`infra/**`。
- 不修改 `tools/**`、`tests/**`。
- 不修改 `docs/governance/DOC_STATE.yaml`。
- 不生成 implementation packet。
- 不标记 implementation-ready。
- 不打开 formal window。
- 不执行 Git 提交或推送。
- 不写 Basic Memory。

## 2. 当前状态层摘要

基线验证结果：

| 命令 | 结果 |
| --- | --- |
| `python -m tools.doc_governor.cli validate-state --input docs/governance/DOC_STATE.yaml` | `ok=true,error=0,warning=0` |
| `python -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml` | `ok=true,error=0,warning=0` |

`evaluate-state` 摘要：

| 指标 | 当前值 |
| --- | ---: |
| `documents_blocked_count` | 0 |
| `modules_blocked_count` | 1 |
| `subtasks_blocked_count` | 25 |
| `formal_window_closed` | 25 |
| `implementation_doc_not_active` | 25 |
| `implementation_scope_unclear` | 25 |
| `acceptance_criteria_missing` | 25 |
| `required_tests_missing` | 25 |
| `missing_required_doc_slot` | 50 |
| `template_like_required_doc_slot` | 14 |
| `upstream_module_not_ready` | 6 |

当前正式状态层事实：

- `docs/governance/DOC_STATE.yaml.subtasks` 只保留 `ST13_01~ST13_25`。
- `RQ01.facts.task_ids` 只保留 `ST13_01~ST13_25`。
- 旧 `ST01_01~ST10_03` 已从 formal current `subtasks` 容器移出。
- `WT13-xx` 是文档层业务 alias；正式状态层入口仍使用 `ST13_01~ST13_25`。
- 所有 `ST13_*` 均为 `readiness=blocked`、`candidate_status=none`、`review_status=unreviewed`、`implementation_doc_state=missing`。
- 当前没有任何 `ST13_*` 可进入 implementation-ready。

W13-E8.5 更新：`ST13_21 / ST13_20 / ST13_24 / ST13_25` 的 DESIGN / IMPLEMENTATION 路径已登记到 `DOC_STATE.yaml` required doc slot；其他 ST13 不受本窗口影响，formal window、implementation doc activation、acceptance criteria、required tests 和 implementation scope 仍未闭合。

## 3. 审计字段说明

下表每行覆盖以下字段：`ST13 ID`、`WT13 alias`、任务名称、所属模块、对应事实源、当前 `DOC_STATE` 状态、当前 blocker、任务设计文档、实施说明文档、验收标准、测试要求、允许修改范围、禁止修改范围、前置依赖、后置依赖、是否可并行、是否需要用户确认、是否可进入任务包准备、是否可进入 implementation-ready、缺口清单。

缺口代码：

| 代码 | 含义 |
| --- | --- |
| A | 缺任务设计文档 |
| B | 缺实施边界 |
| C | 缺验收标准 |
| D | 缺测试要求 |
| E | 缺 API contract |
| F | 缺 UI / 页面规格 |
| G | 缺数据模型细化 |
| H | 缺权限规则 |
| I | 缺 LLM / RAG / provider 细节 |
| J | 缺错误态 / 空状态 |
| K | 缺运维 / 配置 / 观测边界 |
| L | 上游任务未完成 |
| M | 用户确认未完成 |
| N | 模块依赖不清 |
| O | 不适合一期实现 |
| P | 仍只是历史参考或 future candidate |

## 4. ST13_01~ST13_25 审计表

| ST13 | WT13 | 任务名称 | 所属模块 | 事实源 | DOC_STATE / blocker | 文档与验收测试 | 范围 | 依赖 / 并行 / 确认 | 任务包准备判断 | implementation-ready | 缺口 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `ST13_01` | `WT13-01` | 账号 / 登录 / 权限 | M01、M02、M10 | scope、IA、object、`FC-02` | `blocked`；缺 design/implementation doc；M02 `api/open_questions` template-like；formal window closed | 无 ST13 专属设计/实施文档；验收和测试仅有 task-remap 高层口径 | 未来允许 `apps/api/**`、`apps/web/**`、`packages/shared/**`、M02 文档；当前窗口禁止代码与 `DOC_STATE.yaml` | 前置 `ST13_20/21`；后置 `ST13_02/05/06/23`；可与 UI 草案并行；需确认任务包顺序 | `blocked_by: ST13_20,ST13_21,module:M02,user_confirmation` | 否 | A,B,C,D,E,F,G,H,J,K,L,M,N |
| `ST13_02` | `WT13-02` | 工作台首页 / 导航 / 权限入口 | M01、M02、M10 | IA、`FC-09`、`FC-15` | `blocked`；缺 design/implementation doc；M02 上游未 ready；formal window closed | 无 ST13 专属双文档；缺页面规格、空状态和测试矩阵 | 未来允许 `apps/web/**`、`packages/shared/**`、M01 文档；当前禁止继续扩 W10 原型 | 前置 `ST13_01`；后置多数页面任务；可与页面规格并行；需确认 UI skeleton 顺序 | `blocked_by: ST13_01,module:M02,user_confirmation` | 否 | A,B,C,D,E,F,H,J,L,M,N |
| `ST13_03` | `WT13-03` | 岗位管理 | M03、M04 | scope、IA、object、`FC-10` | `blocked`；缺 design/implementation doc；formal window closed | 无 ST13 专属双文档；缺岗位 API、schema、验收和测试 | 未来允许 `apps/web/**`、`apps/api/**`、M03 文档；不得恢复 W10 手工 JD 单页主链 | 前置 `ST13_01/20/21`；后置 `ST13_06/13/23`；可与 `ST13_04` 并行；需确认 schema 粒度 | `not_ready` | 否 | A,B,C,D,E,F,G,H,J,L,M,N |
| `ST13_04` | `WT13-04` | 简历管理 | M03、M10 | scope、IA、object、`FC-03`、`FC-10` | `blocked`；缺 design/implementation doc；formal window closed | 无 ST13 专属双文档；缺简历版本、上传、权限和测试要求 | 未来允许 `apps/web/**`、`apps/api/**`、M03 文档；不得直接复活旧 `ST03_03` | 前置 `ST13_01/20/21`；后置 `ST13_06/14/19/23`；可与 `ST13_03` 并行；需确认上传边界 | `not_ready` | 否 | A,B,C,D,E,F,G,H,J,K,L,M,N |
| `ST13_05` | `WT13-05` | 模拟记录列表 | M02、M06、M08 | IA、object、scoring/DoD、`FC-06` | `blocked`；缺 design/implementation doc；M02 上游未 ready；formal window closed | 无 ST13 专属双文档；缺列表 API、权限态、空状态和测试 | 未来允许 `apps/web/**`、`apps/api/**`、M06/M08 文档；不得把默认页改回直接开始新面试 | 前置 `ST13_01/20/21`；后置 `ST13_06/14/15/19/23`；可与发起流程设计并行；需确认列表筛选范围 | `blocked_by: ST13_01,ST13_20,ST13_21,module:M02` | 否 | A,B,C,D,E,F,G,H,J,L,M,N |
| `ST13_06` | `WT13-06` | 发起模拟面试 | M03、M04、M05、M06、M07 | IA、object | `blocked`；缺 design/implementation doc；formal window closed | 无 ST13 专属双文档；缺 launch contract、缺失输入规则和测试 | 未来允许 `apps/web/**`、`apps/api/**`、M06 文档；不得跳过岗位 / 简历必选事实 | 前置 `ST13_03/04/10/11/21`；后置 `ST13_07/08/09`；可与面试台 UI 草案并行；需确认缺失输入处理 | `not_ready` | 否 | A,B,C,D,E,F,G,H,I,J,L,M,N |
| `ST13_07` | `WT13-07` | 面试台 | M05、M06、M07、M08 | IA、object、scoring/DoD | `blocked`；缺 design/implementation doc；formal window closed | 无 ST13 专属双文档；缺执行页状态、RAG 引用、LLM 失败和流测试 | 未来允许 `apps/web/**`、`apps/api/**`、M06 文档；不得用 mock LLM 作为正式行为 | 前置 `ST13_06/10/11/12`；后置 `ST13_08/09/13/15`；可与评分复盘 contract 并行；需确认暂停 / 继续细节 | `not_ready` | 否 | A,B,C,D,E,F,G,H,I,J,K,L,M,N |
| `ST13_08` | `WT13-08` | 打磨模式 | M06、M07、M09 | object、scoring/DoD、`FC-13` | `blocked`；缺 design/implementation doc；formal window closed | 无 ST13 专属双文档；缺 ProgressTree 细化、题级反馈和测试 | 未来允许 `apps/web/**`、`apps/api/**`、M07/M09 文档；不得写成固定轮次 | 前置 `ST13_07/13/16`；后置 `ST13_17/23`；可与 `ST13_09` 并行；需确认反馈保存深度 | `not_ready` | 否 | A,B,C,D,E,F,G,I,J,L,M,N |
| `ST13_09` | `WT13-09` | 压力面模式 | M06、M07、M08 | object、scoring/DoD、`FC-06` | `blocked`；缺 design/implementation doc；formal window closed | 无 ST13 专属双文档；缺 InterviewQuestionSet 题组策略和测试 | 未来允许 `apps/web/**`、`apps/api/**`、M06/M08 文档；不得把固定 3 轮写成总规则 | 前置 `ST13_07/13/15`；后置 `ST13_15/16/23`；可与 `ST13_08` 并行；需确认题组数量 / 难度 | `not_ready` | 否 | A,B,C,D,E,F,G,I,J,L,M,N |
| `ST13_10` | `WT13-10` | RAG / 知识库 | M05、M06、M08、M10 | scope、IA、object、`FC-05` | `blocked`；缺 design/implementation doc；formal window closed | 无 ST13 专属双文档；缺知识库 API、索引、权限、失败降级测试 | 未来允许 `apps/api/**`、`apps/web/**`、M05 文档；不得伪造 RAG evidence | 前置 `ST13_01/20/21`；后置 `ST13_06/07/13/14/15`；可与 LLM adapter contract 并行；需确认向量 / 索引策略 | `not_ready` | 否 | A,B,C,D,E,F,G,H,I,J,K,L,M,N |
| `ST13_11` | `WT13-11` | 真实 LLM provider / adapter | M04、M06、M08、M10 | scope、object、`FC-04` | `blocked`；缺 design/implementation doc；formal window closed | 无 ST13 专属双文档；缺 provider、密钥、重试、脱敏日志和测试 | 未来允许 `apps/api/**`、`packages/shared/**`、M10 文档；不得明文密钥或继续 mock 正式行为 | 前置 `ST13_20/21/22`；后置 `ST13_06/07/13/14/15`；可与 RAG contract 并行；需确认默认 provider | `not_ready` | 否 | A,B,C,D,E,G,I,J,K,L,M,N |
| `ST13_12` | `WT13-12` | 多轮上下文 / 状态机 | M06、M07、M08 | object、DoD | `blocked`；缺 design/implementation doc；formal window closed | 无 ST13 专属双文档；缺状态枚举、恢复策略和状态机测试 | 未来允许 `apps/api/**`、`apps/web/**`、M06 文档；不得用固定 3 轮替代状态机 | 前置 `ST13_07/08/09`；后置 `ST13_13/15`；可与 UI 展示并行；需确认完整 context 保存范围 | `not_ready` | 否 | A,B,C,D,E,F,G,I,J,L,M,N |
| `ST13_13` | `WT13-13` | 评分体系 | M04、M07、M08、M10 | scoring/DoD、`FC-07` | `blocked`；缺 design/implementation doc；formal window closed | 无 ST13 专属双文档；缺计算公式、版本、证据绑定和测试 | 未来允许 `apps/api/**`、`apps/web/**`、M04/M08 文档；不得输出黑盒分数 | 前置 `ST13_10/11/12`；后置 `ST13_14/15/16/19`；可与复盘设计并行；需确认公式 / 权重细节 | `not_ready` | 否 | A,B,C,D,E,F,G,I,J,K,L,M,N |
| `ST13_14` | `WT13-14` | 真实面试复盘 | M08、M09、M10 | scoring/DoD、`FC-11` | `blocked`；缺 design/implementation doc；formal window closed | 无 ST13 专属双文档；缺逐字稿导入、问答切分、低置信度和测试 | 未来允许 `apps/web/**`、`apps/api/**`、M08 文档；不得要求用户先手工拆题 | 前置 `ST13_11/13/16`；后置 `ST13_17/18/19`；可与模拟复盘并行；需确认材料原文保存 / 导出边界 | `not_ready` | 否 | A,B,C,D,E,F,G,H,I,J,K,L,M,N |
| `ST13_15` | `WT13-15` | 模拟面试复盘 | M06、M07、M08、M09 | scoring/DoD | `blocked`；缺 design/implementation doc；formal window closed | 无 ST13 专属双文档；缺整场判断、逐题点评、通过概率和测试 | 未来允许 `apps/web/**`、`apps/api/**`、M08 文档；不得只生成简版反馈摘要 | 前置 `ST13_09/13/16`；后置 `ST13_17/18/19`；可与真实复盘并行；需确认报告结构 | `not_ready` | 否 | A,B,C,D,E,F,G,I,J,L,M,N |
| `ST13_16` | `WT13-16` | 薄弱项 `WeaknessItem` | M04、M07、M08、M09 | object、DoD、`FC-13` | `blocked`；缺 design/implementation doc；formal window closed | 无 ST13 专属双文档；缺聚合 key、消减、停练和测试 | 未来允许 `apps/api/**`、`apps/web/**`、M09 文档；不得用待打磨清单替代薄弱项中心 | 前置 `ST13_13/14/15`；后置 `ST13_17`；可与训练抽屉并行；需确认独立服务端保存 | `not_ready` | 否 | A,B,C,D,E,F,G,I,J,L,M,N |
| `ST13_17` | `WT13-17` | 训练抽屉 / 待打磨清单 | M03、M07、M08、M09 | object、DoD | `blocked`；缺 design/implementation doc；formal window closed | 无 ST13 专属双文档；缺抽屉交互、训练动作和测试 | 未来允许 `apps/web/**`、`apps/api/**`、M09 文档；不得扩成完整训练中心 | 前置 `ST13_16/08/14/15`；后置 `ST13_23`；可与 UI 细化并行；需确认清单是否独立页面化 | `not_ready` | 否 | A,B,C,D,E,F,G,I,J,L,M,N |
| `ST13_18` | `WT13-18` | 资产归档 | M05、M08、M10 | object、DoD、`FC-14` | `blocked`；缺 design/implementation doc；formal window closed | 无 ST13 专属双文档；缺资产类型 schema、权限和测试 | 未来允许 `apps/web/**`、`apps/api/**`、M05 文档；不得做复杂资产中心替代主链 | 前置 `ST13_14/15/20`；后置 `ST13_19`；可与导出并行；需确认动态字段子集 | `not_ready` | 否 | A,B,C,D,E,F,G,H,J,K,L,M,N |
| `ST13_19` | `WT13-19` | Markdown 导出 / 复制 | M03、M07、M08、M10 | scoring/DoD、`FC-12` | `blocked`；缺 design/implementation doc；formal window closed | 无 ST13 专属双文档；缺导出结构、异步、权限和测试 | 未来允许 `apps/web/**`、`apps/api/**`、M08/M03 文档；不得做完整 PDF 或导出无权限原文 | 前置 `ST13_13/14/15/18`；后置验收收口；可与资产归档并行；需确认文件命名和原文范围 | `not_ready` | 否 | A,B,C,D,E,F,G,H,I,J,K,L,M,N |
| `ST13_20` | `WT13-20` | 服务端保存 / 数据库 | M01、M02-M10 | scope、object、`FC-03` | `blocked`；缺 design/implementation doc；M02 上游未 ready；formal window closed | 无 ST13 专属双文档；缺 schema / migration、仓储、回退和测试 | 未来允许 `apps/api/**`、`packages/shared/**`、M01/M10 文档；当前不得创建目录 | 前置 `ST13_21` contract；后置几乎所有业务任务；可与 API contract 设计并行；需确认迁移策略 | `ready_for_task_packet_candidate`，但 `blocked_by: module:M02,user_confirmation` | 否 | A,B,C,D,E,G,H,J,K,L,M,N |
| `ST13_21` | `WT13-21` | API / 后端服务边界 | M01、M02-M10 | object、`FC-01` | `blocked`；缺 design/implementation doc；M02 上游未 ready；formal window closed | 无 ST13 专属双文档；缺 Auth/Job/Resume/Knowledge/Interview/Review/Score/Export API 明细和 contract tests | 未来允许 `apps/api/**`、`packages/shared/**`、M01/M10 文档；不得无 contract 直接实现业务服务 | 前置 `ST13_01/20` 需排序确认；后置所有前后端联调任务；可先做 contract 窗口；需确认 API-first | `ready_for_task_packet_candidate`，但 `blocked_by: module:M02,user_confirmation` | 否 | A,B,C,D,E,G,H,J,K,L,M,N |
| `ST13_22` | `WT13-22` | 日志 / 观测 / 运维 | M01、M10 | object、`FC-01`、`FC-18` | `blocked`；缺 design/implementation doc；formal window closed | 无 ST13 专属双文档；缺日志字段、审计事件、配置和测试 | 未来允许 `apps/api/**`、开窗后 `infra/**`、M10 文档；当前禁止 `infra/**` | 前置 `ST13_11/20/21`；后置验收与运维；可与后端骨架设计并行；需确认日志保留和密钥策略 | `not_ready` | 否 | A,B,C,D,E,G,H,I,J,K,L,M,N |
| `ST13_23` | `WT13-23` | 前端工作台 UI / 页面集合 | M01-M10 | IA、scoring/DoD | `blocked`；缺 design/implementation doc；M02 上游未 ready；formal window closed | 无 ST13 专属双文档；缺页面规格、错误 / 空状态、响应式、无障碍和测试 | 未来允许 `apps/web/**`、`packages/shared/**`、模块文档；不得继续从 W10 原型直接扩展为事实 | 前置 `ST13_01/03~19` contract；后置页面实现；可按页面域并行；需确认 API contract 先还是 UI skeleton 先 | `blocked_by: ST13_01,ST13_21,module:M02,user_confirmation` | 否 | A,B,C,D,E,F,H,J,L,M,N |
| `ST13_24` | `WT13-24` | 测试 / 验收 / DoD | M01、M10、全模块 | scoring/DoD、AGENTS、TEST_POLICY | `blocked`；缺 design/implementation doc；formal window closed | 无 ST13 专属双文档；当前有五层 DoD 事实源，但缺任务级 required tests 矩阵 | 未来允许 `tests/**`、`apps/**` 测试文件、docs 测试说明；当前禁止修改 `tests/**` | 前置所有 contract；后置 formal window 与 implementation packet；可作为横向验证窗口并行；需确认测试入口策略 | `ready_for_task_packet_candidate` | 否 | A,B,C,D,E,F,G,H,I,J,K,L,M,N |
| `ST13_25` | `WT13-25` | 文档治理 / 收口 / Basic Memory | global、M01、M10 | AGENTS、DOC_GOVERNANCE、DOC_AUTOMATION、W13 facts | `blocked`；缺 design/implementation doc；formal window closed | 无 ST13 专属双文档；本审计文档提供前置输入，但不替代任务包 | 未来允许根文档和必要 `docs/superpowers/plans/**`；未确认前禁止 `DOC_STATE.yaml` 和 Basic Memory | 前置所有任务输出；后置收口、BM/Superpowers 写回；可与只读审计并行；需确认写回窗口 | `ready_for_task_packet_candidate` | 否 | A,B,C,D,J,K,L,M,N |

说明：`ready_for_task_packet_candidate` 只表示“可作为下一窗口编制任务包草案的候选”，不表示可生成 implementation packet，更不表示可以进入代码实现。

## 5. 缺口分类统计

| 缺口类别 | 影响范围 | 优先级 | 说明 |
| --- | --- | --- | --- |
| A 缺任务设计文档 | 25/25 | P0 | 所有 `ST13_*` 均缺 ST13 专属 `SUBTASK_DESIGN.md` 或等价任务设计文档。 |
| B 缺实施边界 | 25/25 | P0 | 所有 `ST13_*` 的 `implementation_scope` 均未闭合。 |
| C 缺验收标准 | 25/25 | P0 | task-remap 只有高层验收句，未达到 implementation doc gate。 |
| D 缺测试要求 | 25/25 | P0 | `required_tests` 为空或未形成任务级矩阵。 |
| E 缺 API contract | 25/25 | P1 | 即使纯 UI / 文档任务也需要依赖 API、状态或数据 contract。 |
| F 缺 UI / 页面规格 | 18/25 | P1 | 登录、工作台、岗位、简历、记录、发起、面试台、知识库、评分、复盘、训练、资产、导出和页面集合均受影响。 |
| G 缺数据模型细化 | 21/25 | P1 | 核心领域对象、schema、状态枚举、迁移和版本仍需任务包细化。 |
| H 缺权限规则 | 14/25 | P1 | 登录、记录可见范围、知识库、导出、资产、审计和前端入口均需要权限边界。 |
| I 缺 LLM / RAG / provider 细节 | 13/25 | P1 | RAG、LLM、多轮、评分、复盘、导出证据和训练推荐均受影响。 |
| J 缺错误态 / 空状态 | 25/25 | P1 | 每个任务包都需要显式错误态、空状态和降级策略。 |
| K 缺运维 / 配置 / 观测边界 | 9/25 | P2 | LLM、RAG、数据库、API、导出、任务治理和测试收口需要日志与配置边界。 |
| L 上游任务未完成 | 25/25 | P0/P1 | 当前 contract、数据、权限、API、测试和 formal window 均未闭合。 |
| M 用户确认未完成 | 25/25 | P0 | 是否生成任务包、顺序、是否创建子任务文档、是否拆窗仍待确认。 |
| N 模块依赖不清 | 22/25 | P1 | 多数 ST13 跨 M01-M10，模块侧文档仍未同步到 ST13 粒度。 |
| O 不适合一期实现 | 0/25 | P3 | 当前 ST13 均属于一期主链或一期治理必需项。 |
| P 历史参考 / future candidate | 0/25 | P3 | 该类别适用于旧 `STxx_*`，不适用于当前 `ST13_*`。 |

P0 阻断：

- 25 个 ST13 全部缺 ST13 专属设计文档、实施文档、验收标准、required tests、formal window。
- 6 个 ST13 额外受 `module:M02` 上游未 ready 影响：`ST13_01`、`ST13_02`、`ST13_05`、`ST13_20`、`ST13_21`、`ST13_23`。

P1 开窗前必须补：

- API contract。
- UI / 页面规格。
- 数据模型和状态枚举。
- 权限消费边界。
- LLM / RAG / provider 细节。
- 错误态 / 空状态。
- 模块同步映射。

P2 实现前补：

- 观测 / 日志 / 配置 / 密钥 / 成本边界。
- 回退策略。
- 测试矩阵和验收证据归档。
- Basic Memory / Superpowers 写回策略。

P3 后续完善：

- 旧 `STxx_*` archive 迁移。
- 二期 / 三期能力和完整管理台、完整训练中心、复杂知识库治理。

## 6. 阶段划分

| 阶段 | 阶段目标 | 包含 ST13 | 前置条件 | 可并行任务 | 不可并行任务 | 需用户确认 | 验证命令 | 完成标准 | 是否允许 implementation packet | 是否允许实现 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 阶段 A：实现前置设计 / contract | 先形成 API、数据、权限、LLM/RAG、评分、UI 和测试 contract | `ST13_21`、`ST13_20`、`ST13_01`、`ST13_10`、`ST13_11`、`ST13_12`、`ST13_13`、`ST13_23`、`ST13_24` | 用户确认任务包顺序和是否允许创建 ST13 子任务文档 | `ST13_21/20/24/25` 可并行准备草案 | 业务页面与流程实现不得先行 | API first 还是 UI skeleton first | `validate-state`、`evaluate-state`、关键词扫描 | 每个 contract 有任务包草案、双文档路径、验收和测试清单 | 否 | 否 |
| 阶段 B：工程骨架和基础设施准备 | 明确未来目录、工程脚手架、配置、日志、测试入口 | `ST13_22`、`ST13_24`、`ST13_25`、`ST13_21`、`ST13_23` | 阶段 A 的 contract 草案 | 测试矩阵、日志边界、文档治理可并行 | 目录创建和服务实现不得在本阶段发生 | 是否允许 `apps/api/**`、`apps/web/**`、`infra/**` | `validate-state`、`evaluate-state`、后续 `python -m tools.test_runner.run_tests` | 工程边界和禁止范围清楚 | 否 | 否 |
| 阶段 C：数据与权限 | 定义账号、权限、记录可见范围、PostgreSQL schema、岗位 / 简历 / 资产数据 | `ST13_01`、`ST13_03`、`ST13_04`、`ST13_05`、`ST13_18`、`ST13_20`、`ST13_21` | API contract 和数据 contract 草案 | 岗位 / 简历 / 资产 schema 可并行设计 | 需要统一迁移策略，不能多窗口抢 schema | 是否先补 M02 模块 API/open_questions | `validate-state`、`evaluate-state` | 权限和数据模型可支撑下游任务包 | 否 | 否 |
| 阶段 D：核心面试 / LLM / RAG | 定义发起、面试台、RAG、LLM、打磨 / 压力面、多轮状态机 | `ST13_06`、`ST13_07`、`ST13_08`、`ST13_09`、`ST13_10`、`ST13_11`、`ST13_12` | 数据、权限、API、provider 草案 | RAG 与 LLM adapter contract 可并行 | 面试台实现必须等状态机和 provider contract | provider、RAG 索引、题组策略 | `validate-state`、`evaluate-state` | 核心流程具备任务包草案和失败态 | 否 | 否 |
| 阶段 E：评分 / 复盘 / 训练闭环 | 定义 ScoreReport、复盘、WeaknessItem、训练抽屉、资产归档 | `ST13_13`、`ST13_14`、`ST13_15`、`ST13_16`、`ST13_17`、`ST13_18` | 面试、RAG、LLM、评分证据 contract | 真实复盘与模拟复盘可并行 | WeaknessItem 需等评分证据模型 | 评分公式、保存深度、训练动作 | `validate-state`、`evaluate-state` | 复盘与训练对象可验收 | 否 | 否 |
| 阶段 F：导出 / 观测 / 验收 | 定义 Markdown 导出、复制、日志、观测、五层 DoD | `ST13_19`、`ST13_22`、`ST13_24` | 评分、复盘、资产和权限 contract | 导出与观测可并行 | DoD 需要汇总所有上游任务包 | 导出结构、日志保留、测试策略 | `validate-state`、`evaluate-state`、关键词扫描 | 每条主链均有验收和测试要求 | 否 | 否 |
| 阶段 G：文档收口和开窗准备 | 汇总任务包、确认 formal window 条件、准备后续写回 | `ST13_25` 和全部 ST13 | A-F 的任务包草案齐备 | 只读审计和根文档同步可并行 | formal window open 需总控单独确认 | 是否生成 implementation packet、何时 formal window open | `validate-state`、`evaluate-state` | 形成下一窗口提示词和确认卡结论 | 否 | 否 |

## 7. 任务包准备清单

每个 ST13 进入任务包准备候选至少需要下列内容：

1. 任务目标。
2. 输入文档。
3. 输出物。
4. 允许修改范围。
5. 禁止修改范围。
6. 依赖关系。
7. 验收标准。
8. 测试要求。
9. 数据 / API / UI 边界。
10. 安全 / 隐私边界。
11. 日志 / 观测边界。
12. 回退策略。
13. 用户确认项。
14. Basic Memory / Superpowers 写回要求。
15. 完成后验证命令。

当前判断：

| ST13 | 当前准备状态 | `ready_for_task_packet` 判定 | `not_ready` 主因 | `blocked_by` |
| --- | --- | --- | --- | --- |
| `ST13_01` | 有高层事实源和任务域；缺 ST13 双文档 | 否 | 权限 contract、M02 模块、验收测试缺失 | `ST13_20`、`ST13_21`、`module:M02`、用户确认 |
| `ST13_02` | 有 IA 事实源；缺页面规格 | 否 | 权限入口与 UI skeleton 顺序未确认 | `ST13_01`、`module:M02` |
| `ST13_03` | 有岗位对象事实源；缺 schema/API | 否 | 依赖数据和 API contract | `ST13_01`、`ST13_20`、`ST13_21` |
| `ST13_04` | 有简历对象事实源；缺上传 / 版本 contract | 否 | 依赖数据、权限和导出边界 | `ST13_01`、`ST13_20`、`ST13_21` |
| `ST13_05` | 有记录列表事实源；缺列表 API | 否 | M02 权限和列表筛选未闭合 | `ST13_01`、`ST13_20`、`ST13_21`、`module:M02` |
| `ST13_06` | 有 launch flow；缺输入 contract | 否 | 岗位、简历、知识库、LLM 未闭合 | `ST13_03`、`ST13_04`、`ST13_10`、`ST13_11` |
| `ST13_07` | 有面试台事实源；缺执行状态机 | 否 | LLM、RAG、多轮状态机未闭合 | `ST13_06`、`ST13_10`、`ST13_11`、`ST13_12` |
| `ST13_08` | 有打磨模式事实源；缺 ProgressTree 任务包 | 否 | 依赖面试台、评分、WeaknessItem | `ST13_07`、`ST13_13`、`ST13_16` |
| `ST13_09` | 有压力面事实源；缺题组策略 | 否 | 依赖面试台、评分、复盘 | `ST13_07`、`ST13_13`、`ST13_15` |
| `ST13_10` | 有 RAG confirmed 事实；缺具体索引策略 | 否 | RAG API、权限、向量 / 索引待定 | `ST13_01`、`ST13_20`、`ST13_21` |
| `ST13_11` | 有真实 LLM confirmed 事实；缺 provider 细节 | 否 | 具体 provider、密钥、重试和日志待确认 | `ST13_20`、`ST13_21`、`ST13_22` |
| `ST13_12` | 有双模式状态机事实；缺状态枚举 | 否 | 暂停 / 继续、context 保存深度待确认 | `ST13_07`、`ST13_08`、`ST13_09` |
| `ST13_13` | 有评分事实源；缺公式 / 版本 / 证据 contract | 否 | 依赖 RAG、LLM 和状态机证据 | `ST13_10`、`ST13_11`、`ST13_12` |
| `ST13_14` | 有真实复盘事实源；缺 intake / review contract | 否 | 依赖 LLM、评分、WeaknessItem | `ST13_11`、`ST13_13`、`ST13_16` |
| `ST13_15` | 有模拟复盘事实源；缺报告结构 | 否 | 依赖压力面、评分、WeaknessItem | `ST13_09`、`ST13_13`、`ST13_16` |
| `ST13_16` | 有 WeaknessItem confirmed 事实；缺持久化和消减规则 | 否 | 依赖评分和复盘证据 | `ST13_13`、`ST13_14`、`ST13_15` |
| `ST13_17` | 有训练抽屉事实源；缺交互和动作 contract | 否 | 依赖 WeaknessItem、打磨和复盘 | `ST13_16`、`ST13_08`、`ST13_14`、`ST13_15` |
| `ST13_18` | 有资产归档事实源；缺 schema 子集和权限 | 否 | 依赖复盘、数据和权限 | `ST13_14`、`ST13_15`、`ST13_20` |
| `ST13_19` | 有 Markdown 导出事实源；缺文件结构和异步策略 | 否 | 依赖评分、复盘、资产归档 | `ST13_13`、`ST13_14`、`ST13_15`、`ST13_18` |
| `ST13_20` | 数据库已 confirmed，schema 未闭合 | 是，候选 | 仍需迁移和回退策略 | `ST13_21`、`module:M02`、用户确认 |
| `ST13_21` | API-first 已 confirmed，具体 API 未闭合 | 是，候选 | 需先定义完整 API contract | `module:M02`、用户确认 |
| `ST13_22` | 运维目标已 confirmed，细节未闭合 | 否 | 依赖 LLM、数据库、API | `ST13_11`、`ST13_20`、`ST13_21` |
| `ST13_23` | 页面集合事实源存在，页面规格未闭合 | 否 | API contract 和权限未闭合 | `ST13_01`、`ST13_21`、`module:M02` |
| `ST13_24` | 五层 DoD 事实源存在，任务测试矩阵未闭合 | 是，候选 | 需把 required tests 分配到每个 ST13 | 所有 contract、用户确认 |
| `ST13_25` | 治理事实源存在，本审计提供输入 | 是，候选 | 仍需后续写回规则和 formal window 条件 | 所有任务输出、用户确认 |

## 8. formal window 条件审计

正式开窗至少需要：

| 条件 | 当前状态 | 结论 |
| --- | --- | --- |
| `DOC_STATE.yaml` 是否需要 `formal_window_open` | 当前所有 ST13 均因 `formal_window_closed` blocked | 需要，但本窗口不打开 |
| `implementation_doc_active` | 当前 `implementation_doc_state=missing` | 需要后续双文档和 activation |
| 子任务设计文档 | 当前无 ST13 专属设计文档 | 必须补 |
| 子任务实施文档 | 当前无 ST13 专属实施文档 | 必须补 |
| acceptance criteria | 当前 25 个缺失 | 必须补 |
| required tests | 当前 25 个缺失 | 必须补 |
| required doc slot | 当前 design/implementation slots 均缺失 | 必须补 |
| module readiness | 当前 M02 blocked；M04-M10 文档成熟度低 | 需模块同步窗口 |
| upstream task readiness | contract / 数据 / 权限 / API 未完成 | 需排序和拆窗 |
| 用户确认 | 任务包、顺序、建文档、创建目录、packet、formal window 均待确认 | 必须补 |
| implementation packet | 当前禁止生成 | 后续 formal window 前另行确认 |
| Basic Memory / Superpowers 写回 | 本窗口禁止写 Basic Memory；后续收口需定义 | 需后续窗口 |
| 干净工作区 | 本窗口不做 Git 操作 | 后续实现前需检查 |
| 提交 / 推送策略 | 本窗口禁止 Git 操作 | 后续另定 |

本窗口结论：不打开 formal window，不生成 implementation packet，不进入 implementation-ready。

## 9. 实现前置依赖审计

| 依赖项 | 状态 | 是否阻断 ST13 | 对应 ST13 |
| --- | --- | --- | --- |
| 后端框架 | FastAPI 已 confirmed；完整 Web framework / 工程细节仍 `needs-review` | 是，阻断实现，不阻断 contract 草案 | `ST13_21`、`ST13_22`、`ST13_24` |
| 数据库 | PostgreSQL 已 confirmed；schema / migration / repository 策略 open | 是 | `ST13_20`，并影响所有持久化任务 |
| API contract | API-first 口径 confirmed；具体 Auth/Job/Resume/Knowledge/Interview/Review/Score/Export contract open | 是 | `ST13_01~ST13_24` |
| 登录 / 权限 | session cookie、普通用户 / 管理员、记录可见范围 confirmed；M02 模块文档仍 blocked | 是 | `ST13_01`、`ST13_02`、`ST13_05`、`ST13_10`、`ST13_14`、`ST13_18`、`ST13_19`、`ST13_20`、`ST13_21`、`ST13_23` |
| LLM provider | 真实 LLM、可插拔 provider、默认 provider 方向 confirmed；具体供应商、密钥、模型和成本策略 open | 是 | `ST13_11`、`ST13_06`、`ST13_07`、`ST13_13`、`ST13_14`、`ST13_15` |
| RAG 检索路线 | RAG 入一期、私有上传 + 管理员公共知识库、混合检索和失败降级已 confirmed；具体实现路线 open | 是 | `ST13_10`、`ST13_06`、`ST13_07`、`ST13_13`、`ST13_14`、`ST13_15` |
| 向量 / 索引策略 | 仍 open；chunk、embedding provider、向量库、召回、重建策略未定 | 是 | `ST13_10`、`ST13_20`、`ST13_22`、`ST13_24` |
| 知识库上传 / 权限 | 私有上传 + 管理员公共知识库 confirmed；团队共享后置；权限过滤细节待任务包 | 是 | `ST13_10`、`ST13_01`、`ST13_21` |
| 多轮状态机 | 打磨 / 压力面拆分 confirmed；状态枚举和恢复策略 open | 是 | `ST13_12`、`ST13_07`、`ST13_08`、`ST13_09` |
| ProgressTree | 打磨模式由 `ProgressTree` 驱动 confirmed；节点模型、反馈保存和结束动作 open | 是 | `ST13_08`、`ST13_12`、`ST13_16` |
| InterviewQuestionSet | 压力面由 `InterviewQuestionSet` 驱动 confirmed；题量、难度和组合策略 open | 是 | `ST13_09`、`ST13_12`、`ST13_15` |
| ScoreReport / ScoreDimension | 对象和 `0-100` 多维评分 confirmed；公式、权重、版本和重算策略 open | 是 | `ST13_13`、`ST13_14`、`ST13_15`、`ST13_19` |
| RealInterviewReview | 真实面试复盘入一期 confirmed；逐字稿切分、低置信度校对 confirmed，高低置信阈值和 UI/API open | 是 | `ST13_14`、`ST13_16`、`ST13_19` |
| MockInterviewReview | 模拟复盘入一期 confirmed；报告结构和证据绑定需任务包 | 是 | `ST13_15`、`ST13_16`、`ST13_19` |
| WeaknessItem | 中粒度主题 confirmed；独立持久化、自动消减和恢复规则 open | 是 | `ST13_16`、`ST13_17`、`ST13_08`、`ST13_14`、`ST13_15` |
| TrainingDrawer | 统一训练入口 confirmed；交互范围、任务动作和独立页面化 open | 是 | `ST13_17`、`ST13_23` |
| AssetArchive | 整份 / 单题归档 confirmed；资产类型 schema 子集和权限 open | 是 | `ST13_18`、`ST13_19` |
| Markdown 导出 | 复制 / Markdown 下载 confirmed；文件结构、命名、复制范围和异步任务 open | 是 | `ST13_19` |
| 前端工作台页面集合 | IA confirmed；页面规格、状态、响应式、无障碍和 API 对齐 open | 是 | `ST13_02`、`ST13_03`、`ST13_04`、`ST13_05`、`ST13_06`、`ST13_07`、`ST13_08`、`ST13_09`、`ST13_10`、`ST13_14`、`ST13_15`、`ST13_16`、`ST13_17`、`ST13_18`、`ST13_19`、`ST13_23` |
| 运维 / 配置 / 日志 / 观测 | 单机部署和日志目标 confirmed；字段、保留、成本、密钥、审计策略 open | 是 | `ST13_11`、`ST13_20`、`ST13_21`、`ST13_22`、`ST13_24`、`ST13_25` |

## 10. ST13 到模块文档映射

所有 M01-M10 均存在 `MODULE_REQUIREMENTS.md`、`MODULE_DESIGN.md`、`MODULE_API_DESIGN.md`、`MODULE_SCHEMA_DESIGN.md`、`MODULE_TASK_INDEX.md`，但这些文档目前多数只支撑模块级历史 / 骨架 / L4 摘要，不支撑 ST13 专属任务包。

| ST13 | 模块 | MODULE_REQUIREMENTS | MODULE_DESIGN | MODULE_API_DESIGN | MODULE_SCHEMA_DESIGN | MODULE_TASK_INDEX | 需 ST13 专属子任务文档 | 可复用旧 STxx | 需模块同步窗口 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `ST13_01` | M01/M02/M10 | 有 | 有 | 有，M02 被评估为 template-like | 有 | 有 | 是 | `ST02_*`、`ST10_01` 仅作参考 | 是，优先 M02 |
| `ST13_02` | M01/M02/M10 | 有 | 有 | 有，M02 需复核 | 有 | 有 | 是 | `ST01_02`、`ST02_*` 仅作参考 | 是 |
| `ST13_03` | M03/M04 | 有 | 有 | 有 | 有 | 有 | 是 | `ST03_01`、`ST04_01` 仅作参考 | 是 |
| `ST13_04` | M03/M10 | 有 | 有 | 有 | 有 | 有 | 是 | `ST03_02`、`ST03_03` 仅作参考 | 是 |
| `ST13_05` | M02/M06/M08 | 有 | 有 | 有，M02 需复核 | 有 | 有 | 是 | `ST06_01`、`ST08_01` 仅作参考 | 是，优先 M02/M06/M08 |
| `ST13_06` | M03/M04/M05/M06/M07 | 有 | 有 | 有 | 有 | 有 | 是 | `ST04_01`、`ST06_02` 仅作参考 | 是 |
| `ST13_07` | M05/M06/M07/M08 | 有 | 有 | 有 | 有 | 有 | 是 | `ST06_02`、`ST06_03`、`ST07_03` 仅作参考 | 是 |
| `ST13_08` | M06/M07/M09 | 有 | 有 | 有 | 有 | 有 | 是 | `ST07_*`、`ST09_*` 仅作参考 | 是 |
| `ST13_09` | M06/M07/M08 | 有 | 有 | 有 | 有 | 有 | 是 | `ST06_*`、`ST08_*` 仅作参考 | 是 |
| `ST13_10` | M05/M06/M08/M10 | 有 | 有 | 有 | 有 | 有 | 是 | `ST05_03`、`ST06_02`、`ST10_03` 仅作参考 | 是 |
| `ST13_11` | M04/M06/M08/M10 | 有 | 有 | 有 | 有 | 有 | 是 | `ST10_02`、`ST10_03` 仅作参考 | 是 |
| `ST13_12` | M06/M07/M08 | 有 | 有 | 有 | 有 | 有 | 是 | `ST06_*`、`ST07_*`、`ST08_*` 仅作参考 | 是 |
| `ST13_13` | M04/M07/M08/M10 | 有 | 有 | 有 | 有 | 有 | 是 | `ST04_02`、`ST07_03`、`ST10_02` 仅作参考 | 是 |
| `ST13_14` | M08/M09/M10 | 有 | 有 | 有 | 有 | 有 | 是 | `ST08_02`、`ST09_*` 仅作参考 | 是 |
| `ST13_15` | M06/M07/M08/M09 | 有 | 有 | 有 | 有 | 有 | 是 | `ST06_03`、`ST08_03`、`ST09_*` 仅作参考 | 是 |
| `ST13_16` | M04/M07/M08/M09 | 有 | 有 | 有 | 有 | 有 | 是 | `ST09_01`、`ST09_03` 仅作参考 | 是 |
| `ST13_17` | M03/M07/M08/M09 | 有 | 有 | 有 | 有 | 有 | 是 | `ST07_01`、`ST09_02` 仅作参考 | 是 |
| `ST13_18` | M05/M08/M10 | 有 | 有 | 有 | 有 | 有 | 是 | `ST05_01`、`ST05_02`、`ST08_03` 仅作参考 | 是 |
| `ST13_19` | M03/M07/M08/M10 | 有 | 有 | 有 | 有 | 有 | 是 | `ST03_03`、`ST08_03`、`ST10_03` 仅作参考 | 是 |
| `ST13_20` | M01-M10 | 有 | 有 | 有 | 有 | 有 | 是 | 多个旧 ST 仅作数据对象参考 | 是 |
| `ST13_21` | M01-M10 | 有 | 有 | 有，M02 需复核 | 有 | 有 | 是 | 全部旧 API 片段仅作参考 | 是，优先总控 API contract |
| `ST13_22` | M01/M10 | 有 | 有 | 有 | 有 | 有 | 是 | `ST10_03`、`ST01_03` 仅作参考 | 是 |
| `ST13_23` | M01-M10 | 有 | 有 | 有，M02 需复核 | 有 | 有 | 是 | W10 `apps/web` 和旧 ST 页面骨架仅作参考 | 是 |
| `ST13_24` | M01/M10/全模块 | 有 | 有 | 有 | 有 | 有 | 是 | `ST01_03`、`ST10_03` 仅作参考 | 是 |
| `ST13_25` | global/M01/M10 | 有 | 有 | 有 | 有 | 有 | 是 | 旧治理文档仅作参考 | 是 |

## 11. 用户确认卡

### E5-Q1：是否允许生成 ST13 任务包草案

问题：是否允许下一窗口开始生成 `ST13_01~ST13_25` 的任务包草案？

背景：当前状态层已收敛为 `ST13_01~ST13_25`，但所有 ST13 都缺 ST13 专属双文档、验收标准、required tests、formal window 和 implementation packet。

方案 A：先只生成 `ST13_21 / ST13_20 / ST13_24 / ST13_25` 四个横向 contract / 测试 / 治理任务包草案。

方案 B：生成全部 `ST13_01~ST13_25` 任务包草案，但全部标记 `not_ready_for_implementation`。

方案 C：暂不生成任务包，先补 M02 和 M04-M10 模块同步。

方案 D：自定义方案 / 其他：由用户补充。

每个方案解决什么：

- A 解决最小前置 contract 顺序。
- B 解决全量任务包视图。
- C 解决模块文档承载不足。
- D 保留用户自定义节奏。

限制：A 覆盖窄；B 文档量大；C 会延后任务包；D 需重新审计。

风险：过早生成全部任务包会被误读为 implementation-ready。

后续影响：决定下一窗口是否只开横向 contract，还是全量任务包准备。

推荐方案：A。

推荐理由：先收敛 API / 数据 / 测试 / 治理边界，风险最低。

等待用户确认：是。

### E5-Q2：ST13 任务包生成顺序

问题：`ST13_01~ST13_25` 的任务包应按什么顺序生成？

背景：核心业务任务依赖 API、数据、权限、LLM/RAG、状态机和评分 contract，不能直接平铺开窗。

方案 A：横向 contract 先行：`ST13_21 -> ST13_20 -> ST13_01 -> ST13_10/11/12/13 -> ST13_24/25`。

方案 B：用户旅程先行：`ST13_02/05/06/07/23` 先做页面和流程任务包。

方案 C：模块成熟度先行：先补 M02、M05、M06、M08、M09、M10 模块同步，再生成任务包。

方案 D：自定义方案 / 其他：由用户补充。

每个方案解决什么：A 降低联调风险；B 先形成用户体验闭环；C 降低模块文档承载风险；D 保留自定义。

限制：A UI 反馈慢；B 容易缺 API；C 推进慢。

风险：B 容易从 W10 原型继续扩写为事实。

后续影响：决定是否先开 API/data/permission contract 窗口。

推荐方案：A。

推荐理由：当前最大阻断来自 API、数据、实施边界、验收和 required tests 缺失。

等待用户确认：是。

### E5-Q3：哪些 ST13 可先做 contract

问题：哪些 ST13 应作为第一批 contract 任务包准备？

背景：业务流程任务依赖横向 contract，且 `evaluate-state` 显示所有 ST13 均 blocked。

方案 A：只做 `ST13_21 / ST13_20 / ST13_24 / ST13_25`。

方案 B：A 之外加入 `ST13_01 / ST13_10 / ST13_11 / ST13_12 / ST13_13`。

方案 C：按页面优先加入 `ST13_23 / ST13_02 / ST13_05`。

方案 D：自定义方案 / 其他：由用户补充。

每个方案解决什么：A 收敛横向前置；B 同步核心能力 contract；C 先形成 UI 骨架输入；D 保留自定义。

限制：A 不覆盖业务；B 任务量中等；C API 风险高。

风险：过早做 UI 会绕过 contract。

后续影响：决定下一窗口可并行数量。

推荐方案：A。

推荐理由：四个任务最适合作为任务包准备前置，不会误触业务实现。

等待用户确认：是。

### E5-Q4：是否允许创建 ST13 专属子任务文档

问题：下一窗口是否允许创建 `ST13_*` 专属 `SUBTASK_DESIGN.md` / `SUBTASK_IMPLEMENTATION.md`？

背景：状态层当前官方 doc slot 指向缺失的设计 / 实施文档，所有 ST13 都因此 blocked。

方案 A：允许先为第一批 ST13 创建专属子任务文档目录。

方案 B：先在 `docs/superpowers/plans/**` 生成任务包草案，不创建模块子任务目录。

方案 C：先更新模块 `MODULE_TASK_INDEX.md`，再决定是否创建子任务文档。

方案 D：自定义方案 / 其他：由用户补充。

每个方案解决什么：A 直接补 doc slot；B 风险最低；C 先补模块承载关系；D 保留自定义。

限制：A 可能影响模块目录；B 不能直接满足 doc slot；C 慢。

风险：未确认目录规范时创建子任务文档可能造成路径漂移。

后续影响：决定能否后续激活 `implementation_doc_state`。

推荐方案：B。

推荐理由：先生成任务包草案，待确认路径规范后再创建正式子任务文档。

等待用户确认：是。

### E5-Q5：是否允许创建实现目录

问题：后续何时允许创建 `apps/api/**`、`apps/web/**` 或 `infra/**`？

背景：当前仓库仍是文档治理和状态层工作；本窗口明确禁止创建这些目录。

方案 A：在 formal window 和 implementation packet 之前一律禁止创建。

方案 B：允许仅创建空骨架目录，不写业务逻辑。

方案 C：允许 contract 任务包通过后创建对应最小骨架。

方案 D：自定义方案 / 其他：由用户补充。

每个方案解决什么：A 防止代码事实抢跑；B 提前工程组织；C 兼顾 contract 和工程准备；D 保留自定义。

限制：A 实现启动慢；B/C 都有误读风险。

风险：B 最容易让未确认设计变成目录事实。

后续影响：决定工程骨架窗口是否存在。

推荐方案：A。

推荐理由：当前所有 ST13 均缺实施文档和 formal window。

等待用户确认：是。

### E5-Q6：是否允许生成 implementation packet

问题：何时允许生成 implementation packet？

背景：当前所有 ST13 均缺 design doc、implementation doc、acceptance criteria、required tests 和 formal window。

方案 A：在所有 P0 gate 补齐前禁止生成。

方案 B：允许先生成 dry-run packet，但标记不可实施。

方案 C：只为 contract 任务生成 packet 草案。

方案 D：自定义方案 / 其他：由用户补充。

每个方案解决什么：A 最安全；B 可提前检验格式；C 兼顾前置任务；D 保留自定义。

限制：A 慢；B/C 需要强标记。

风险：任何 packet 都可能被误解为可实施。

后续影响：决定 `doc_governor` packet 链路何时恢复。

推荐方案：A。

推荐理由：当前 gate 明确不满足。

等待用户确认：是。

### E5-Q7：formal window 何时打开

问题：正式 formal window 应在什么条件下打开？

背景：`evaluate-state` 当前对 25 个 ST13 均返回 `formal_window_closed`。

方案 A：每个 ST13 的任务包、双文档、验收、测试和用户确认齐备后逐个打开。

方案 B：按阶段批量打开，例如先开 contract 阶段。

方案 C：等全部 25 个任务包都完成后统一打开。

方案 D：自定义方案 / 其他：由用户补充。

每个方案解决什么：A 精细控制；B 提升并行效率；C 全局一致；D 保留自定义。

限制：A 管理成本高；B 需批次标准；C 推进慢。

风险：B/C 都可能掩盖单个任务缺口。

后续影响：决定后续状态层写回方式。

推荐方案：A。

推荐理由：ST13 跨模块依赖复杂，逐个开窗更可控。

等待用户确认：是。

### E5-Q8：任务包准备与实现是否拆窗

问题：任务包准备和代码实现是否必须拆成不同窗口？

背景：当前任务包准备本身还未完成，直接实现会绕过文档治理。

方案 A：严格拆窗，任务包准备窗口不写代码。

方案 B：允许同一窗口先准备任务包，再在用户确认后继续实现。

方案 C：只允许 contract 任务同窗进入实现。

方案 D：自定义方案 / 其他：由用户补充。

每个方案解决什么：A 降低漂移；B 提升速度；C 对 contract 友好；D 保留自定义。

限制：A 窗口数量多；B/C 容易扩大范围。

风险：同窗实现容易误触 forbidden paths。

后续影响：决定下一轮提示词模板。

推荐方案：A。

推荐理由：当前阻断来自文档链和状态链，拆窗最清楚。

等待用户确认：是。

### E5-Q9：先做 API contract 还是 UI skeleton

问题：下一步应先做 API contract 还是 UI skeleton？

背景：`ST13_23` 依赖 `ST13_01` 和 `ST13_21`，而 `ST13_21` 是 API / 后端服务边界。

方案 A：API contract 先行。

方案 B：UI skeleton 先行。

方案 C：API contract 与 UI skeleton 并行，但只写文档不写代码。

方案 D：自定义方案 / 其他：由用户补充。

每个方案解决什么：A 稳定联调边界；B 快速验证 IA；C 兼顾双方；D 保留自定义。

限制：A UI 反馈慢；B 易无 contract；C 需要强同步。

风险：B 最容易复用 W10 原型作为事实源。

后续影响：决定 `ST13_21` 与 `ST13_23` 的开窗先后。

推荐方案：A。

推荐理由：API、权限、数据和错误态是 formal window 的共同前置。

等待用户确认：是。

### E5-Q10：先做后端还是前端

问题：一期 MVP 实现准备应先做后端还是前端？

背景：当前实现仍禁止，但任务包排序需要提前决定依赖方向。

方案 A：后端 / API / 数据 contract 先行。

方案 B：前端页面规格先行。

方案 C：后端 contract 与前端页面规格并行，等 contract 合并后再实现。

方案 D：自定义方案 / 其他：由用户补充。

每个方案解决什么：A 稳定数据和权限；B 稳定体验；C 缩短周期；D 保留自定义。

限制：A 体验验证慢；B 可能返工；C 需要强接口边界。

风险：无 API contract 的前端会产生假接口事实。

后续影响：决定是否先开 `ST13_21 / ST13_20 / ST13_01`。

推荐方案：C。

推荐理由：并行只限文档 / contract，不进入实现；可兼顾体验和接口，但不绕过 formal gate。

等待用户确认：是。

## 12. 下一窗口建议

推荐下一窗口：`W13-E6 / ST13 任务包准备确认与第一批 contract 草案窗口`。

建议范围：

1. 只处理用户确认后的第一批任务包。
2. 默认第一批为 `ST13_21`、`ST13_20`、`ST13_24`、`ST13_25`。
3. 只生成任务包草案或专属子任务文档路径建议，不生成 implementation packet。
4. 若用户确认创建子任务文档，再按 `docs/SUBTASK_DOC_TEMPLATES.md` 另开文档窗口。
5. 不创建 `apps/**`、`infra/**`、`tools/**`、`tests/**`。

建议提示词：

```text
你是 W13-E6：ST13 第一批任务包准备窗口。
请先读取 AGENTS.md、docs/DOC_GOVERNANCE.md、docs/SUBTASK_DOC_TEMPLATES.md、docs/superpowers/plans/2026-04-25-workbench-mvp-st13-readiness-audit.md。
本窗口只根据用户确认的第一批 ST13 生成任务包草案，不进入实现，不生成 implementation packet，不打开 formal window。
默认第一批候选为 ST13_21、ST13_20、ST13_24、ST13_25；若用户确认其他顺序，以用户最新确认优先。
```

后续状态更新：

- `W13-E6` 已新增 [`2026-04-25-workbench-mvp-st13-first-contract-task-packages.md`](2026-04-25-workbench-mvp-st13-first-contract-task-packages.md)，只生成第一批任务包草案。
- `W13-E7` 已新增 [`2026-04-25-workbench-mvp-st13-first-contract-double-doc-plan.md`](2026-04-25-workbench-mvp-st13-first-contract-double-doc-plan.md)，只形成双文档路径和模板准备方案。
- 上述两个后续文档均不表示 formal window open、implementation packet 生成或 implementation-ready。

## 13. 当前不进入实现说明

本审计结束后仍不能进入实现：

- 25 个 ST13 仍全部 blocked。
- 25 个 ST13 均无 ST13 专属设计 / 实施双文档。
- 25 个 ST13 均缺 acceptance criteria 和 required tests。
- formal window 未打开。
- implementation packet 未生成，且本窗口禁止生成。
- `module:M02` 仍导致 6 个 ST13 带上游 blocker。
- 任务包生成、顺序、子任务文档路径、目录创建、formal window 时机仍需用户确认。

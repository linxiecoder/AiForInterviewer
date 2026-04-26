# AI 模拟面试一期工作台 MVP 待办与路线图清单

> 本文档是 W13-E2 建立的长期待办与路线图清单，用于持续跟踪一期 MVP 阻断项、状态层后续事项、Task Remap 后续事项、实现前置条件、二期 / 三期候选能力和历史归档事项。本文档不是 `DOC_STATE.yaml`，不替代 `TASK_INDEX.md`、`MODULE_INDEX.md`、`OPEN_QUESTIONS.md` 或 implementation packet。

## 1. 文档定位

- 维护范围：项目待办、状态层后续事项、任务重映射后续事项、实现前置条件、二期 / 三期候选能力、历史归档后续事项和用户确认待办。
- 当前状态：W13-E15 / formal window open 前置确认已完成；正式 `DOC_STATE.yaml.subtasks` 仍只保留 `ST13_01~ST13_25`，旧 `STxx_*` 已从 formal current 容器移出，`RQ01.facts.task_ids` 已只保留 `ST13_01~ST13_25`；第一批 `ST13_24 / ST13_25` 已以 facts-only 方式把 candidate 推荐字段写入正式状态层，并已完成前置确认卡输出，但当前仍不能生成 implementation packet、打开 formal window 或进入实现。
- 不做事项：不创建 `apps/**`、`infra/**`，不修改 `tools/**`、`tests/**`，不生成 implementation packet；不迁移 archive，不删除旧 `STxx_*` 文档。
- 更新原则：每轮总控或收口窗口可按同一字段规范增量更新；不得只把后续事项写在聊天记录、`EXECUTION_LOG.md` 或一次性确认卡中。
- 工具治理 backlog 已迁入 `docs/governance/DOC_GOVERNOR_TOOL_DEBT.md`，本文件不复制工具债正文。

## 2. 跟踪字段规范

每个待办项必须至少包含以下字段：

- ID
- 标题
- 类别
- 状态
- 优先级
- 来源
- 负责人或处理窗口
- 阻断关系
- 目标解决窗口
- 最近更新时间
- 备注

状态建议：`open`、`in_review`、`blocked`、`confirmed`、`done`、`superseded`、`backlog`。

优先级建议：`P0`、`P1`、`P2`、`P3`。

## 3. 当前 MVP 阻断项

| ID | 标题 | 类别 | 状态 | 优先级 | 来源 | 负责人或处理窗口 | 阻断关系 | 目标解决窗口 | 最近更新时间 | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BR-BLK-001 | W13-E2 State Remap dry-run 收口 | 当前 MVP 阻断项 | done | P0 | W13-E2 | W13-E2 | 已解除 W13-E3 输入质量阻断 | W13-E2 | 2026-04-25 | dry-run 分析已收口；不放行实现。 |
| BR-BLK-002 | `DOC_STATE.yaml` 尚未写入 W13 新任务 | 当前 MVP 阻断项 | done | P0 | W13-E / W13-E2 / W13-E4-A | W13-E4-B / State Write 阶段 1 | 阶段 1 已解除“新任务未写入”阻断，但不放行 implementation-ready | W13-E4-B | 2026-04-25 | 已写入 `ST13_01~ST13_25`，不移除旧 `STxx_*`。 |
| BR-BLK-003 | 旧 `STxx_*` 尚未在状态层正式 superseded | 当前 MVP 阻断项 | done | P0 | W13-StateArchive / W13-E / W13-E4-A | W13-E4-C / State Write 阶段 2 | 已用旧任务 facts 表达 historical / superseded | W13-E4-C | 2026-04-25 | 阶段 2 已完成；后续 W13-E4-F 已将旧任务从正式 current 容器移出，但不移动文件。 |
| BR-BLK-004 | implementation-ready 尚未形成 | 当前 MVP 阻断项 | blocked | P0 | `evaluate-state` | 后续正式开窗窗口 | 依赖状态层、任务包、实施文档和 formal window | W13-E3+ | 2026-04-25 | 当前不能生成 implementation packet。 |

## 4. 状态层后续事项

| ID | 标题 | 类别 | 状态 | 优先级 | 来源 | 负责人或处理窗口 | 阻断关系 | 目标解决窗口 | 最近更新时间 | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BR-STATE-001 | 检查 `WT13-xx` 是否兼容当前 schema | 状态层后续事项 | done | P0 | W13-E2 | W13-E2 | 无 | W13-E2 | 2026-04-25 | 结论：可作 Markdown 候选任务域 ID；不能直接作为当前 `DOC_STATE.yaml.subtasks` key。 |
| BR-STATE-002 | 创建 preview YAML 验证 W13 新任务结构 | 状态层后续事项 | done | P0 | W13-E2 / OQ-093 | W13-E3 / Preview YAML | 用户已确认方案 B | W13-E3 | 2026-04-25 | 已创建 `docs/superpowers/plans/2026-04-25-workbench-mvp-doc-state-preview.yaml` 并通过预检。 |
| BR-STATE-003 | 设计后续 State Write 窗口 | 状态层后续事项 | done | P0 | W13-E3 Preview YAML | W13-E4-A | 已形成 C-Phased 分阶段计划 | W13-E4-A | 2026-04-25 | 已新增 `docs/superpowers/plans/2026-04-25-workbench-mvp-state-write-plan.md`。 |
| BR-STATE-004 | 决定旧 `STxx_*` 状态层保留、移出或 superseded 表达 | 状态层后续事项 | done | P0 | W13-E2 / W13-E4-A | W13-E4-C / State Write 阶段 2 | 阶段 2 已按用户确认方案 B 执行 | W13-E4-C | 2026-04-25 | 已用现有 `facts` 字段表达旧任务 `historical-reference / superseded`，不移出旧任务。 |
| BR-STATE-005 | 处理 archive-candidate 的状态层解除引用条件 | 状态层后续事项 | open | P1 | W13-StateArchive / W13-E2 / W13-E4-A | 后续 Archive Cleanup | 依赖阶段 3 | W13-E4+ | 2026-04-25 | 解除 `DOC_STATE.yaml`、`TASK_INDEX.md`、`MODULE_INDEX.md` 引用前不得移动旧 ST 文档。 |
| BR-STATE-006 | 执行 State Write 阶段 1 | 状态层后续事项 | done | P0 | W13-E4-A | W13-E4-B | 用户已确认 `OQ-094=B` | W13-E4-B | 2026-04-25 | 已写入 `ST13_01~ST13_25`，不移除旧 `STxx_*`，不处理旧任务 superseded。 |
| BR-STATE-007 | 执行 State Write 阶段 2 | 状态层后续事项 | done | P0 | W13-E4-A / OQ-095 | W13-E4-C | 阶段 1 已通过验证 | W13-E4-C | 2026-04-25 | 已在 30 个旧 `STxx_*` facts 中写入 `w13_status`、`w13_role`、`w13_superseded_by`、`w13_alias_target`；不进入阶段 3。 |
| BR-STATE-008 | 执行 State Write 阶段 3 dry-run / 影响分析 | 状态层后续事项 | done | P0 | W13-E4-C | W13-E4-D | 用户确认只分析不移出 | W13-E4-D | 2026-04-26 | 已新增 stage3 dry-run 文档；该阶段不移出旧任务、不创建 preview。 |
| BR-STATE-009 | 创建 Stage3 Preview YAML | 状态层后续事项 | done | P0 | W13-E4-D / OQ-097 | W13-E4-E / Stage3 Preview | 用户已确认 `OQ-097=B` | W13-E4-E | 2026-04-26 | 已创建 `docs/superpowers/plans/2026-04-25-workbench-mvp-doc-state-stage3-preview.yaml`；preview `validate/evaluate` 全绿，正式 `DOC_STATE.yaml` 未修改。 |
| BR-STATE-010 | 执行正式 Stage 3 | 状态层后续事项 | done | P0 | W13-E4-E / OQ-100 | W13-E4-F / State Write Stage 3 | 用户已确认方案 B | W13-E4-F | 2026-04-26 | 已正式移出旧 `STxx_*`，并将 `RQ01.facts.task_ids` 收敛为 `ST13_01~ST13_25`；不放行实现。 |
| BR-STATE-011 | 评估旧 `STxx_*` archive 迁移 | 状态层后续事项 | open | P1 | W13-E4-F | 后续 Archive Cleanup 确认窗口 | 依赖 Stage 3 已完成 | 后续窗口 | 2026-04-26 | 只可评估，不得在未确认窗口中迁移 archive 或删除旧文档。 |
| BR-STATE-012 | 第一批 ST13 required doc slot State Update | 状态层后续事项 | done | P0 | W13-E8 / `OQ-113=B` | W13-E8.5 | 依赖 W13-E8 双文档已创建 | W13-E8.5 | 2026-04-26 | 已在单独窗口把 `ST13_21 / ST13_20 / ST13_24 / ST13_25` 的 DESIGN / IMPLEMENTATION 路径写入 `DOC_STATE.yaml` required doc slot，并独立 validate/evaluate；仍不放行实现。 |

## 5. Task Remap 后续事项

| ID | 标题 | 类别 | 状态 | 优先级 | 来源 | 负责人或处理窗口 | 阻断关系 | 目标解决窗口 | 最近更新时间 | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BR-REMAP-001 | `WT13-01~WT13-25` 与模块映射复核 | Task Remap 后续事项 | in_review | P0 | task-remap | W13-E2 | 依赖四份 W13 唯一事实源 | W13-E2 | 2026-04-25 | 当前只作为候选任务域映射，不是正式开窗任务。 |
| BR-REMAP-002 | `TASK_INDEX.md` 后续正式化 | Task Remap 后续事项 | open | P0 | W13-E2 | W13-E3+ | 依赖状态层方案确认 | W13-E3+ | 2026-04-25 | 后续需补允许修改范围、验证命令、DoD 和开窗资格。 |
| BR-REMAP-003 | `MODULE_INDEX.md` 后续正式化 | Task Remap 后续事项 | open | P1 | W13-E2 | 模块同步窗口 | 依赖 W13 新任务结构 | W13-E3+ | 2026-04-25 | 不得误激活旧 `STxx_*` 或模块 L5 候选。 |
| BR-REMAP-004 | 任务开窗顺序确认 | Task Remap 后续事项 | open | P1 | task-remap | 总控窗口 | 依赖状态层与 contract 任务确认 | W13-E3+ | 2026-04-25 | 当前仍停留在设计 / contract 前置阶段。 |
| BR-REMAP-005 | 窗口边界模板细化 | Task Remap 后续事项 | backlog | P2 | task-remap | 后续窗口编排 | 依赖正式任务包 | 后续实施准备 | 2026-04-25 | 需要按前端、后端、RAG、LLM、评分、权限、数据、导出、运维分别细化。 |
| BR-REMAP-006 | ST13 readiness audit | Task Remap 后续事项 | done | P0 | W13-E5 | W13-E5 | 已完成 `ST13_01~ST13_25` 前置审计，不放行 implementation-ready | W13-E5 | 2026-04-26 | 新增 `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-readiness-audit.md`；`OQ-101~OQ-110` 已由 W13-E6 确认。 |
| BR-REMAP-007 | 第一批 ST13 任务包准备 | Task Remap 后续事项 | done | P0 | W13-E5 | W13-E6 | 用户已确认 `OQ-101~OQ-110`，已生成第一批任务包草案 | W13-E6 | 2026-04-26 | 新增 `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-first-contract-task-packages.md`；不得生成 implementation packet。 |
| BR-REMAP-008 | 第一批 ST13 正式双文档准备 | Task Remap 后续事项 | done | P0 | W13-E6 | W13-E7 | 已形成双文档路径和模板准备方案 | W13-E7 | 2026-04-26 | 新增 `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-first-contract-double-doc-plan.md`；状态只到 `double_doc_path_planned`，仍不得实现。 |
| BR-REMAP-009 | 第一批 ST13 正式双文档创建 | Task Remap 后续事项 | done | P0 | W13-E7 / `OQ-111~OQ-113` | W13-E8 | 用户已确认 `OQ-111=A`、`OQ-112=A`、`OQ-113=B` | W13-E8 | 2026-04-26 | 已创建 `ST13_21 / ST13_20 / ST13_24 / ST13_25` 双文档；不生成 implementation packet，不修改 `DOC_STATE.yaml`。 |
| BR-REMAP-010 | 第一批 ST13 contract 细化 | Task Remap 后续事项 | done | P0 | W13-E8.5 | W13-E9 | 依赖四个双文档已创建且 required doc slot 已登记 | W13-E9 | 2026-04-26 | 已细化 API、数据、测试和治理 contract；不得实现。 |
| BR-REMAP-011 | 第一批 ST13 readiness 复核 | Task Remap 后续事项 | done | P0 | W13-E9 | W13-E10 | 依赖四个 contract_refined 双文档 | W13-E10 | 2026-04-26 | 已新增 readiness review 文档；`ST13_24 / ST13_25` 建议为 `ready_for_formal_window_candidate`，`ST13_21 / ST13_20` 建议为 `near_ready_for_formal_window_candidate`；不得直接实现。 |
| BR-REMAP-012 | 第一批 ST13 formal window candidate 评估 | Task Remap 后续事项 | done | P0 | W13-E10 / `OQ-114~OQ-117` | W13-E11 | 用户已确认 `OQ-114=A`、`OQ-115=B`、`OQ-116=A`、`OQ-117=A` | W13-E11 | 2026-04-26 | 已形成 `ST13_24 / ST13_25` candidate recommended 与 `ST13_21 / ST13_20` near-ready confirmed；不打开 formal window，不生成 implementation packet，不进入实现。 |
| BR-REMAP-013 | 第一批 ST13 candidate State Update 准备 | Task Remap 后续事项 | done | P0 | W13-E11 | W13-E12 | 依赖 W13-E11 文档层评估和用户另窗授权 | W13-E12 | 2026-04-26 | W13-E12 已完成 State Update 准备、字段影响分析、确认卡和 W13-E13 Preview 方案；未修改正式 `DOC_STATE.yaml`。 |
| BR-REMAP-014 | 第一批 ST13 candidate State Update Preview | Task Remap 后续事项 | done | P0 | W13-E12 | W13-E13 | 用户已确认 `OQ-118=B`、`OQ-119=A`、`OQ-120=B` | W13-E13 | 2026-04-26 | 已创建 `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-candidate-state-preview.yaml`；Preview 验证失败，正式 `DOC_STATE.yaml` 未修改。 |
| BR-REMAP-015 | 修正第一批 ST13 candidate 状态表达策略 | Task Remap 后续事项 | done | P0 | W13-E13 Preview 失败 / `OQ-121=A` | W13-E13.5 | 用户已确认 `OQ-121=A` | W13-E13.5 | 2026-04-26 | 已新增 candidate strategy fix 文档；后续优先 facts-only Preview，备选 `candidate_status=observe`。 |
| BR-REMAP-016 | 创建修正后的 Candidate State Preview | Task Remap 后续事项 | done | P0 | W13-E13.5 / `OQ-122~OQ-123` | W13-E13.6 | 用户已确认 `OQ-122=A`、`OQ-123=A` | W13-E13.6 | 2026-04-26 | 已创建 facts-only Candidate Preview；facts-only 字段验证通过，但完整 Preview `documents_blocked_count=1`，不直接进入 W13-E14。 |
| BR-REMAP-017 | 决定是否执行 facts-only 正式 State Update | Task Remap 后续事项 | done | P0 | W13-E13.6 / `OQ-124` | W13-E13.8 | 用户已确认方案 A：docs/governance/previews 路径 Preview 严格全绿后执行 facts-only 正式 State Update | W13-E13.8 | 2026-04-26 | 已完成；仅写 `ST13_24 / ST13_25` facts-only candidate 推荐字段，未写 `candidate_status=candidate`、`readiness=downstream_ready`、formal window open 或 implementation-ready。 |
| BR-REMAP-018 | facts-only State Update 后续 formal window 前置确认 | Task Remap 后续事项 | done | P0 | W13-E13.8 | W13-E15 | 依赖 formal window 前置条件、implementation scope、required tests 与 acceptance criteria 继续收敛 | formal window 确认前置 | 2026-04-27 | 已新增 W13-E15 formal window open 前置确认文档；只输出确认卡，不修改 `DOC_STATE.yaml`，不直接生成 implementation packet 或进入实现。 |
| BR-REMAP-019 | `ST13_24` formal window open 执行窗口确认 | Task Remap 后续事项 | open | P0 | W13-E15 / `OQ-125~OQ-127` | 后续 State Update 执行窗口 | 依赖用户确认 `OQ-125~OQ-127` | formal window open 执行窗口 | 2026-04-27 | 推荐只打开 `ST13_24` 作为保守试点；同窗不生成 packet，不进入实现。 |

## 6. 实现前置条件

| ID | 标题 | 类别 | 状态 | 优先级 | 来源 | 负责人或处理窗口 | 阻断关系 | 目标解决窗口 | 最近更新时间 | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BR-PRE-001 | API contract | 实现前置条件 | open | P0 | W13-C / W13-E | 后续 API contract 窗口 | 阻断后端和前端联调 | W13-E3+ | 2026-04-25 | 需先定义 Auth、Job、Resume、Knowledge、Interview、Review、Score、Export 等 API 边界。 |
| BR-PRE-002 | 后端框架确认 | 实现前置条件 | confirmed | P0 | FC-01 / DD-005 | 后续实现计划 | 仍需 implementation packet 复核 | W13-E3+ | 2026-04-25 | FastAPI 已确认；Web framework 与工程细节仍不得从旧计划直接推导。 |
| BR-PRE-003 | 数据库确认 | 实现前置条件 | confirmed | P0 | FC-01 / FC-03 | 后续数据 contract 窗口 | 依赖 schema / migration 策略 | W13-E3+ | 2026-04-25 | PostgreSQL 已确认，具体表结构和迁移策略仍待任务包。 |
| BR-PRE-004 | LLM provider 确认 | 实现前置条件 | open | P0 | FC-04 / W13-C | LLM provider 窗口 | 阻断真实 LLM 接入 | W13-E3+ | 2026-04-25 | 已确认可插拔 provider + 默认真实 provider，具体供应商和密钥策略待实现前确认。 |
| BR-PRE-005 | RAG 检索路线确认 | 实现前置条件 | open | P0 | FC-05 / W13-C | RAG 窗口 | 阻断面试证据和评分证据 | W13-E3+ | 2026-04-25 | 混合检索已确认，具体向量库、索引、chunk、召回策略仍需任务包。 |
| BR-PRE-006 | 权限模型确认 | 实现前置条件 | confirmed | P0 | FC-02 | 权限 / 登录窗口 | 依赖 API contract | W13-E3+ | 2026-04-25 | 普通用户 / 管理员两级和记录可见范围已确认；完整成员治理后续细化。 |
| BR-PRE-007 | 评分维度确认 | 实现前置条件 | confirmed | P0 | FC-07 / W13-D | 评分窗口 | 依赖证据模型和版本策略 | W13-E3+ | 2026-04-25 | 五个维度与 `0-100` 总分关系已确认，具体公式和版本策略仍需任务包。 |
| BR-PRE-008 | 部署目标确认 | 实现前置条件 | confirmed | P1 | FC-01 | 运维 / 部署窗口 | 依赖服务结构和配置边界 | W13-E3+ | 2026-04-25 | 单机服务器已确认；部署脚本、日志、成本控制仍待任务包。 |

## 7. 二期 / 三期候选能力

| ID | 标题 | 类别 | 状态 | 优先级 | 来源 | 负责人或处理窗口 | 阻断关系 | 目标解决窗口 | 最近更新时间 | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BR-LATER-001 | 更完整导出 | 二期 / 三期候选能力 | backlog | P2 | FC-12 | 后续产品规划 | 不阻断一期 MVP | 二期候选 | 2026-04-25 | PDF、批量导出、完整渲染链增强后置。 |
| BR-LATER-002 | 管理台增强 | 二期 / 三期候选能力 | backlog | P2 | FC-18 | 后续产品规划 | 不阻断一期 MVP | 二期候选 | 2026-04-25 | 完整成员管理、配置中心、模型在线同步后置。 |
| BR-LATER-003 | 训练中心扩展 | 二期 / 三期候选能力 | backlog | P2 | FC-13 | 后续产品规划 | 不阻断一期 MVP | 二期候选 | 2026-04-25 | 一期只做训练抽屉和待打磨清单，完整训练中心后置。 |
| BR-LATER-004 | 多租户或团队协作增强 | 二期 / 三期候选能力 | backlog | P3 | FC-02 / FC-05 | 后续产品规划 | 不阻断一期 MVP | 三期候选 | 2026-04-25 | 团队共享知识库、跨团队权限、协作复盘后置。 |
| BR-LATER-005 | 更复杂知识库治理 | 二期 / 三期候选能力 | backlog | P2 | FC-05 | 后续产品规划 | 不阻断一期 MVP | 二期候选 | 2026-04-25 | 审批、版本治理、来源可信度、知识过期策略后置。 |
| BR-LATER-006 | 高级观测和成本控制 | 二期 / 三期候选能力 | backlog | P2 | FC-01 / FC-18 | 后续产品规划 | 不阻断一期 MVP | 二期候选 | 2026-04-25 | 细粒度 token 成本、模型质量监控、告警和预算策略后置。 |

## 8. 历史归档后续事项

| ID | 标题 | 类别 | 状态 | 优先级 | 来源 | 负责人或处理窗口 | 阻断关系 | 目标解决窗口 | 最近更新时间 | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BR-ARCH-001 | 旧 `STxx_*` 是否迁入 archive | 历史归档后续事项 | open | P1 | W13-StateArchive / W13-E2 | Archive Cleanup | 依赖状态层解除引用 | W13-E3+ | 2026-04-25 | 用户已确认后续 superseded，但迁入 archive 仍需单独确认和状态层前置。 |
| BR-ARCH-002 | archive 链接复核 | 历史归档后续事项 | backlog | P2 | W13-StateArchive | Archive Cleanup | 依赖 BR-ARCH-001 | 后续归档窗口 | 2026-04-25 | 迁移后必须复核根索引、模块索引和历史跳转说明。 |
| BR-ARCH-003 | 模块历史文档清理 | 历史归档后续事项 | backlog | P2 | W13-GOV-MergeArchive | 模块同步窗口 | 依赖模块窗口 | 后续模块同步 | 2026-04-25 | 只清理当前事实源误导，不删除仍有追溯价值的历史记录。 |
| BR-ARCH-004 | 旧路径引用残留复查 | 历史归档后续事项 | backlog | P2 | W13-StateArchive | Review 窗口 | 依赖归档动作 | 后续归档窗口 | 2026-04-25 | 重点复查旧设计稿、旧实现计划、旧 ST 和 archive 跳转引用。 |

## 9. 用户确认待办

| 编号 | 问题 | 当前推荐 | 状态 | 影响范围 | 预计处理窗口 |
| --- | --- | --- | --- | --- | --- |
| UC-W13-E3-001 | W13-E3 是否允许写入 `DOC_STATE.yaml`？ | 方案 B：创建 preview YAML，不修改正式 `DOC_STATE.yaml`；Preview YAML 已创建。 | confirmed | 状态层、任务索引、正式开窗 | W13-E3 / Preview YAML |
| UC-W13-E3-002 | 是否移出旧 `STxx_*`？ | 已被 `OQ-097~OQ-099` 细化为 Stage3 Preview、移出策略和 `RQ01.facts.task_ids` 三张确认卡。 | superseded | `DOC_STATE.yaml`、`TASK_INDEX.md`、`MODULE_INDEX.md` | W13-E4-D |
| UC-W13-E4-001 | 是否允许 `W13-E4-B` 写入 `ST13_01~ST13_25`，但不移除旧 `STxx_*`？ | 方案 B：写入新任务，不移除旧任务。 | confirmed | `DOC_STATE.yaml`、正式开窗治理 | W13-E4-B |
| UC-W13-E4-002 | 旧 `STxx_*` superseded 如何表达？ | 第一阶段不处理，第二阶段用现有 `facts` 字段表达；W13-E4-C 已完成。 | confirmed | `DOC_STATE.yaml`、索引层、task-remap | W13-E4-C |
| UC-W13-E4-003 | 是否创建正式 State Write 备份文件？ | 方案 B：创建变更说明和回退说明，不复制 `DOC_STATE`。 | confirmed | 回退证据、状态副本治理 | W13-E4-B |
| UC-W13-E4-D-001 | 是否创建 Stage3 Preview YAML？ | 方案 B：下一窗口创建 Preview YAML，不修改正式 `DOC_STATE.yaml`。 | confirmed | 用户已确认 `OQ-097=B`；W13-E4-E 已创建并验证 Preview | W13-E4-E |
| UC-W13-E4-D-002 | 旧 `STxx_*` 移出策略 | 先做方案 B 的 preview；preview 通过后再确认是否正式移出。 | confirmed | 用户已确认 `OQ-098`：先做 Preview，不正式移出旧 `STxx_*` | W13-E4-E |
| UC-W13-E4-D-003 | `RQ01.facts.task_ids` 旧任务处理 | 方案 B：preview 中移除 `ST01_01`、`ST09_03`，只保留 `ST13_01~ST13_25`。 | confirmed | 用户已确认 `OQ-099`：只在 Preview 中验证，正式状态暂不改写 | W13-E4-E |
| UC-W13-E4-E-001 | 是否基于 Stage3 Preview 执行正式 Stage 3？ | 方案 B：正式移出旧 `STxx_*`，并从 `RQ01.facts.task_ids` 移除旧 `ST01_01`、`ST09_03`。 | confirmed | 用户已确认，W13-E4-F 已执行正式 Stage 3 | W13-E4-F |
| UC-W13-E5-001 | 是否允许生成 ST13 任务包草案？ | 方案 A：先只生成 `ST13_21 / ST13_20 / ST13_24 / ST13_25` 四个横向任务包草案。 | confirmed | `OQ-101=A` 已确认；W13-E6 已完成 | W13-E6 |
| UC-W13-E5-002 | ST13 任务包生成顺序如何确定？ | 方案 A：横向 contract 先行。 | confirmed | `OQ-102=A` 已确认；第一批顺序为 `ST13_21 -> ST13_20 -> ST13_24 -> ST13_25` | W13-E6 |
| UC-W13-E5-003 | 哪些 ST13 可先做 contract？ | 方案 A：只做 `ST13_21 / ST13_20 / ST13_24 / ST13_25`。 | confirmed | `OQ-103=A` 已确认；不得扩大到其他 ST13 | W13-E6 |
| UC-W13-E5-004 | 是否允许创建 ST13 专属子任务文档？ | 方案 B：先生成任务包草案，不创建模块子任务目录。 | confirmed | `OQ-104=B` 已确认；本轮不创建正式子任务目录 | W13-E6 |
| UC-W13-E5-005 | 何时允许创建实现目录、生成 packet、打开 formal window 和进入实现？ | 继续禁止，逐项满足 gate 后再确认。 | confirmed | `OQ-105=A`、`OQ-106=A`、`OQ-107=A`、`OQ-108=A`、`OQ-109=A`、`OQ-110=C` 已确认；当前仍不实现 | 后续正式开窗窗口 |
| UC-W13-E7-001 | ST13 双文档路径方案如何选择？ | 方案 A：集中任务包目录。 | confirmed | 用户已确认 `OQ-111=A`；W13-E8 已按该路径创建双文档 | W13-E8 |
| UC-W13-E7-002 | 是否允许下一窗口创建第一批正式双文档？ | 方案 A：允许 W13-E8 创建 `ST13_21 / ST13_20 / ST13_24 / ST13_25` 的正式双文档。 | confirmed | 用户已确认 `OQ-112=A`；W13-E8 已完成 | W13-E8 |
| UC-W13-E7-003 | 是否允许下一窗口更新 `DOC_STATE.yaml` required doc slot？ | 方案 B：创建双文档后，在后续单独 State Update 窗口更新 required doc slot。 | confirmed | 用户已确认 `OQ-113=B`；W13-E8 未修改 `DOC_STATE.yaml`，W13-E8.5 已另窗完成登记 | W13-E8.5 |
| UC-W13-E10-001 | 是否接受 W13-E10 formal window candidate 分级？ | 方案 A：接受 `ST13_24 / ST13_25 = ready_for_formal_window_candidate`，`ST13_21 / ST13_20 = near_ready_for_formal_window_candidate`。 | confirmed | 用户已确认 `OQ-114=A`；W13-E11 只写文档层 candidate 评估，不写 `candidate_status`，不打开 formal window | W13-E11 |
| UC-W13-E10-002 | 是否允许后续 State Update 处理 readiness / candidate_status？ | 方案 B：W13-E11 后再开 State Update。 | confirmed | 用户已确认 `OQ-115=B`；W13-E11 不修改 `DOC_STATE.yaml` | W13-E11 / W13-E12 |
| UC-W13-E10-003 | 是否需要 W13-E10.5 补齐 acceptance criteria / required tests / implementation scope？ | 方案 A：不新增 W13-E10.5，直接进入 W13-E11 candidate 评估。 | confirmed | 用户已确认 `OQ-116=A`；不新增 W13-E10.5 | W13-E11 |
| UC-W13-E10-004 | 是否保持实现类动作继续禁止？ | 方案 A：继续全部禁止，直到用户另窗确认 formal window 和 implementation packet 条件。 | confirmed | 用户已确认 `OQ-117=A`；当前仍不写代码、不创建目录、不生成 packet、不打开 formal window | W13-E11 |
| UC-W13-E12-001 | 是否允许 W13-E13 更新 `ST13_24 / ST13_25` 的 candidate 相关状态？ | 方案 B：下一窗口只在 preview 中测试 `candidate_status` / `readiness` 相关字段，保持 `formal_window_open=false`、`implementation-ready=false`。 | confirmed | 用户已确认 `OQ-118=B`；W13-E13 已创建 Preview，验证失败。 | W13-E13 |
| UC-W13-E12-002 | `ST13_21 / ST13_20` 是否写入状态层 near-ready？ | 方案 A：暂不写入状态层 near-ready，只保留文档层 near-ready。 | confirmed | 用户已确认 `OQ-119=A`；不得写成 formal_window_candidate。 | W13-E13 |
| UC-W13-E12-003 | W13-E13 是否先做 Preview YAML？ | 方案 B：先创建 State Update preview YAML，不修改正式 `DOC_STATE.yaml`。 | confirmed | 用户已确认 `OQ-120=B`；W13-E13 已创建 preview，正式状态未修改。 | W13-E13 |
| UC-W13-E13-001 | 是否基于 W13-E13 Preview 执行 W13-E14 正式 State Update？ | 方案 A：暂不执行正式 State Update，只保留失败 Preview 并修正后续策略；方案 B：正式写入；方案 C：同时准备 formal window open。 | confirmed | 用户已确认 `OQ-121=A`；W13-E13.5 只做策略修正，不进入正式 State Update。 | W13-E13.5 |
| UC-W13-E13.5-001 | W13-E13.5 后是否创建新的 Candidate State Preview？ | 方案 A：创建 facts-only Candidate Preview；备选方案 B：创建 `candidate_status=observe` Preview；方案 C：maturity + downstream_ready Preview 不推荐优先。 | confirmed | 用户已确认 `OQ-122=A`；W13-E13.6 已创建 facts-only Preview。 | W13-E13.6 |
| UC-W13-E13.5-002 | 是否继续禁止 W13-E14 正式 State Update？ | 方案 A：继续禁止，直到新的 Preview 全绿；方案 B：facts-only 方案直接正式写入；方案 C：formal window open 前置确认后再写 candidate。 | confirmed | 用户已确认 `OQ-123=A`；W13-E13.6 未进入 W13-E14，正式 `DOC_STATE.yaml` 未修改。 | W13-E13.6 |
| UC-W13-E13.6-001 | 是否基于 W13-E13.6 facts-only Preview 执行后续 facts-only 正式 State Update？ | 用户确认方案 A：把 Preview 放到 `docs/governance/previews/` 下重新验证；Preview 严格全绿后，再执行 facts-only 正式 State Update。 | confirmed | `OQ-124` 已由 W13-E13.8 吸收；正式状态层仅写入 `ST13_24 / ST13_25` facts-only candidate 推荐字段，未打开 formal window，未形成 implementation-ready。 | W13-E13.8 |
| UC-W13-E15-001 | 是否允许后续单独窗口打开 `ST13_24 / ST13_25` 的 formal window？ | 方案 B：后续单独开 formal window open 窗口，只打开 `ST13_24`。 | proposed-default | `OQ-125` 等待用户确认；确认前不得写 `formal_window_open=true`。 | 后续 State Update 执行窗口 |
| UC-W13-E15-002 | formal window open 后是否允许同窗生成 implementation packet？ | 方案 A：不允许；packet 必须另开窗口并通过 preflight / packet gate。 | proposed-default | `OQ-126` 等待用户确认；确认前不得生成 packet。 | 后续 packet 准备窗口 |
| UC-W13-E15-003 | formal window open 后是否允许立刻进入代码实现？ | 方案 A：不允许；open-window 后仍需 packet 准备和用户确认。 | proposed-default | `OQ-127` 等待用户确认；确认前不得创建实现目录或进入实现。 | 后续实现准备窗口 |
| UC-ARCH-001 | 是否把旧 `STxx_*` 迁入 archive？ | 不在状态层仍引用时迁移；解除引用后另开归档窗口。 | open | `docs/modules/**`、archive、根索引 | Archive Cleanup |
| UC-IMPL-001 | 是否进入实现窗口？ | 否；正式状态层和 implementation-ready 形成前不进入实现。 | confirmed | `apps/**`、`infra/**`、实现包 | 后续正式开窗后 |

## 10. 更新规则

1. 新增待办时必须补齐第 2 节字段。
2. 状态变化后同步更新最近更新时间和备注。
3. 任何 `confirmed` 状态必须能追溯到用户确认、`DESIGN_DECISIONS.md` 或已验证的正式文档事实源。
4. 任何会影响 `DOC_STATE.yaml` 的事项必须先进入 preview / dry-run 或用户确认卡。
5. 本文件不得被用来绕过 `validate-state`、`evaluate-state`、`confirm-transition` 或 formal window gate。

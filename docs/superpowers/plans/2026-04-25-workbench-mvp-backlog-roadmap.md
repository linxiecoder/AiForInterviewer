# AI 模拟面试一期工作台 MVP 待办与路线图清单

> 本文档是 W13-E2 建立的长期待办与路线图清单，用于持续跟踪一期 MVP 阻断项、状态层后续事项、Task Remap 后续事项、实现前置条件、二期 / 三期候选能力和历史归档事项。本文档不是 `DOC_STATE.yaml`，不替代 `TASK_INDEX.md`、`MODULE_INDEX.md`、`OPEN_QUESTIONS.md` 或 implementation packet。

## 1. 文档定位

- 维护范围：项目待办、状态层后续事项、任务重映射后续事项、实现前置条件、二期 / 三期候选能力、历史归档后续事项和用户确认待办。
- 当前状态：W13-E2 / State Remap dry-run 正在把 W13-E 确认组合吸收到文档层；正式状态层仍未写入 W13 新任务。
- 不做事项：不创建 `apps/**`、`infra/**`，不修改 `tools/**`、`tests/**`，不修改 `docs/governance/**` 或 `DOC_STATE.yaml`，不生成 implementation packet。
- 更新原则：每轮总控或收口窗口可按同一字段规范增量更新；不得只把后续事项写在聊天记录、`EXECUTION_LOG.md` 或一次性确认卡中。

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
| BR-BLK-001 | W13-E2 State Remap dry-run 收口 | 当前 MVP 阻断项 | in_review | P0 | W13-E2 | W13-E2 | 阻断 W13-E3 输入质量 | W13-E2 | 2026-04-25 | 完成后仅解除 dry-run 分析阻断，不放行实现。 |
| BR-BLK-002 | `DOC_STATE.yaml` 尚未写入 W13 新任务 | 当前 MVP 阻断项 | blocked | P0 | W13-E / W13-E2 | W13-E3 / State Write | 阻断正式开窗和 implementation-ready | W13-E3 | 2026-04-25 | 当前 `subtasks` 容器仍是旧 `STxx_*`。 |
| BR-BLK-003 | 旧 `STxx_*` 尚未在状态层正式 superseded | 当前 MVP 阻断项 | blocked | P0 | W13-StateArchive / W13-E | W13-E3 或后续 State Cleanup | 依赖 W13 新任务 preview / write | W13-E3+ | 2026-04-25 | 本轮只形成 superseded 映射草案，不移动文件。 |
| BR-BLK-004 | implementation-ready 尚未形成 | 当前 MVP 阻断项 | blocked | P0 | `evaluate-state` | 后续正式开窗窗口 | 依赖状态层、任务包、实施文档和 formal window | W13-E3+ | 2026-04-25 | 当前不能生成 implementation packet。 |

## 4. 状态层后续事项

| ID | 标题 | 类别 | 状态 | 优先级 | 来源 | 负责人或处理窗口 | 阻断关系 | 目标解决窗口 | 最近更新时间 | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BR-STATE-001 | 检查 `WT13-xx` 是否兼容当前 schema | 状态层后续事项 | done | P0 | W13-E2 | W13-E2 | 无 | W13-E2 | 2026-04-25 | 结论：可作 Markdown 候选任务域 ID；不能直接作为当前 `DOC_STATE.yaml.subtasks` key。 |
| BR-STATE-002 | 创建 preview YAML 验证 W13 新任务结构 | 状态层后续事项 | open | P0 | W13-E2 | W13-E3 / Preview YAML | 依赖用户确认 | W13-E3 | 2026-04-25 | 推荐先创建单独 preview YAML，不直接覆盖正式状态。 |
| BR-STATE-003 | 设计 W13-E3 / State Write 窗口 | 状态层后续事项 | open | P0 | W13-E2 | W13-E3 | 依赖 BR-STATE-002 | W13-E3 | 2026-04-25 | 需明确是否使用别名、兼容 ID 或工具 schema 变更。 |
| BR-STATE-004 | 决定旧 `STxx_*` 状态层保留、移出或 superseded 表达 | 状态层后续事项 | open | P0 | W13-E2 | W13-E3 / State Cleanup | 依赖 W13 新任务结构 | W13-E3+ | 2026-04-25 | 用户已确认后续映射为 superseded，但正式写入节奏仍需确认。 |
| BR-STATE-005 | 处理 archive-candidate 的状态层解除引用条件 | 状态层后续事项 | open | P1 | W13-StateArchive / W13-E2 | 后续 Archive Cleanup | 依赖 BR-STATE-004 | W13-E3+ | 2026-04-25 | 解除 `DOC_STATE.yaml`、`TASK_INDEX.md`、`MODULE_INDEX.md` 引用前不得移动旧 ST 文档。 |

## 5. Task Remap 后续事项

| ID | 标题 | 类别 | 状态 | 优先级 | 来源 | 负责人或处理窗口 | 阻断关系 | 目标解决窗口 | 最近更新时间 | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BR-REMAP-001 | `WT13-01~WT13-25` 与模块映射复核 | Task Remap 后续事项 | in_review | P0 | task-remap | W13-E2 | 依赖四份 W13 唯一事实源 | W13-E2 | 2026-04-25 | 当前只作为候选任务域映射，不是正式开窗任务。 |
| BR-REMAP-002 | `TASK_INDEX.md` 后续正式化 | Task Remap 后续事项 | open | P0 | W13-E2 | W13-E3+ | 依赖状态层方案确认 | W13-E3+ | 2026-04-25 | 后续需补允许修改范围、验证命令、DoD 和开窗资格。 |
| BR-REMAP-003 | `MODULE_INDEX.md` 后续正式化 | Task Remap 后续事项 | open | P1 | W13-E2 | 模块同步窗口 | 依赖 W13 新任务结构 | W13-E3+ | 2026-04-25 | 不得误激活旧 `STxx_*` 或模块 L5 候选。 |
| BR-REMAP-004 | 任务开窗顺序确认 | Task Remap 后续事项 | open | P1 | task-remap | 总控窗口 | 依赖状态层与 contract 任务确认 | W13-E3+ | 2026-04-25 | 当前仍停留在设计 / contract 前置阶段。 |
| BR-REMAP-005 | 窗口边界模板细化 | Task Remap 后续事项 | backlog | P2 | task-remap | 后续窗口编排 | 依赖正式任务包 | 后续实施准备 | 2026-04-25 | 需要按前端、后端、RAG、LLM、评分、权限、数据、导出、运维分别细化。 |

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
| UC-W13-E3-001 | W13-E3 是否允许写入 `DOC_STATE.yaml`？ | 方案 B：下一窗口创建 preview YAML，不修改正式 `DOC_STATE.yaml`。 | proposed-default | 状态层、任务索引、正式开窗 | W13-E3 / Preview YAML |
| UC-W13-E3-002 | 是否移出旧 `STxx_*`？ | 先不移出；等 W13 新任务 preview 通过后再决定。 | open | `DOC_STATE.yaml`、`TASK_INDEX.md`、`MODULE_INDEX.md` | W13-E3+ |
| UC-ARCH-001 | 是否把旧 `STxx_*` 迁入 archive？ | 不在状态层仍引用时迁移；解除引用后另开归档窗口。 | open | `docs/modules/**`、archive、根索引 | Archive Cleanup |
| UC-IMPL-001 | 是否进入实现窗口？ | 否；正式状态层和 implementation-ready 形成前不进入实现。 | confirmed | `apps/**`、`infra/**`、实现包 | 后续正式开窗后 |

## 10. 更新规则

1. 新增待办时必须补齐第 2 节字段。
2. 状态变化后同步更新最近更新时间和备注。
3. 任何 `confirmed` 状态必须能追溯到用户确认、`DESIGN_DECISIONS.md` 或已验证的正式文档事实源。
4. 任何会影响 `DOC_STATE.yaml` 的事项必须先进入 preview / dry-run 或用户确认卡。
5. 本文件不得被用来绕过 `validate-state`、`evaluate-state`、`confirm-transition` 或 formal window gate。

# ST13_24 DESIGN：测试 / 验收 / DoD

## 1. 文档状态

- 状态：`draft`
- 实施状态：`not implementation-ready`
- formal window：`formal window closed`
- implementation packet：`implementation packet forbidden`
- 本文件是 W13-E8 创建的正式双文档实体之一，但尚未写入 `DOC_STATE.yaml` required doc slot。

## 2. 关联 ST13 / WT13

- ST13：`ST13_24`
- WT13 alias：`WT13-24`
- 任务名称：测试 / 验收 / DoD
- 当前来源状态：`task_packet_draft_created` -> `double_doc_created`

## 3. 关联模块

- 主模块：M01
- 相关模块：M10、全模块
- 本任务是横向验收与测试 contract，不创建测试代码。

## 4. 关联 W13 事实源

- `docs/superpowers/plans/2026-04-25-workbench-mvp-scope.md`
- `docs/superpowers/plans/2026-04-25-workbench-mvp-ia-user-journey.md`
- `docs/superpowers/plans/2026-04-25-workbench-mvp-object-model-rag-multiround-backend.md`
- `docs/superpowers/plans/2026-04-25-workbench-mvp-scoring-review-export-dod.md`
- `docs/governance/TEST_POLICY.md`
- `docs/superpowers/plans/st13-task-packages/ST13_21/ST13_21_DESIGN.md`
- `docs/superpowers/plans/st13-task-packages/ST13_20/ST13_20_DESIGN.md`

## 5. 背景

25 个 ST13 当前仍缺 formal window、required tests、acceptance criteria 和 required doc slot。第一批任务中，`ST13_24` 负责把一期工作台 MVP 的产品、数据、UI、工程、收口五层 DoD 转化为后续 formal window 前的测试 / 验收 contract。

## 6. 目标

- 建立测试 / 验收 / DoD 的正式设计文档。
- 定义产品 DoD、数据 DoD、UI DoD、工程 DoD、收口 DoD。
- 为后续每个 ST13 提供 required tests 和失败停止条件的模板。

## 7. 非目标

- 不创建 `tests/**`。
- 不修改 test runner、pytest fixture 或 CI。
- 不创建应用实现、测试实现或测试数据 fixture。
- 不修改 `DOC_STATE.yaml`。
- 不生成 implementation packet，不打开 formal window。

## 8. 输入

- W13 四份事实源。
- `ST13_21` API contract 设计。
- `ST13_20` 数据 contract 设计。
- `docs/governance/TEST_POLICY.md`。
- W13-E5 / E6 / E7 文档和 `OQ-111=A / OQ-112=A / OQ-113=B`。

## 9. 输出

- required tests matrix 草案。
- P0/P1/P2/P3 验收分级。
- 产品 / 数据 / UI / 工程 / 收口五层 DoD。
- formal window 前检查清单。
- 后续实现窗口验证命令模板。

## 10. 依赖

- 前置依赖：`ST13_21` API contract、`ST13_20` 数据 contract。
- 下游依赖：所有 ST13 formal window 和 implementation packet。
- 并行依赖：`ST13_25` 治理收口文档。

## 11. contract 范围

### 11.1 测试 / 验收目标

确保后续实现窗口不只拥有功能描述，还拥有可执行或可检查的验收标准、required tests、失败停止条件和回退说明。

### 11.2 产品 DoD

- 一期主链覆盖登录、工作台、岗位、简历、知识库、记录列表、发起、面试台、复盘、评分、导出。
- 模拟面试默认从历史记录列表进入，完成后回写历史记录 / 复盘。

### 11.3 数据 DoD

- 服务端保存、权限过滤、RAG evidence、LLM 脱敏记录、评分证据、导出快照均可追溯。

### 11.4 UI DoD

- 页面流符合 IA，错误态 / 空状态完整，记录列表、发起、面试台和复盘详情可串联。

### 11.5 工程 DoD

- 默认测试入口为 `python -m tools.test_runner.run_tests`。
- 不在仓库根目录或 `tests/` 下遗留 `tmp/temp`。
- validate-state / evaluate-state 不退化。

### 11.6 收口 DoD

- 修改清单、验证结果、未完成项、风险、下一步窗口边界明确。
- Basic Memory / Superpowers 写回只能在后续授权窗口执行。

### 11.7 API contract 测试要求

- schema validation、权限矩阵、错误 taxonomy、幂等、异步任务状态。

### 11.8 数据库测试要求

- schema relation、migration dry-run、权限过滤、数据一致性、evidence 引用完整性。

### 11.9 RAG 测试要求

- 私有 / 公共知识库权限、混合检索、无命中降级、引用回溯、证据进入评分但不直接决定分数。

### 11.10 LLM provider 测试要求

- provider 失败、重试、脱敏日志、模型名 / 模板版本记录、成本字段候选。

### 11.11 多轮面试测试要求

- 暂停 / 继续、上下文保存、轮次 / turn 状态、模式切换边界。

### 11.12 打磨模式测试要求

- `ProgressTree` 驱动，用户决定继续或结束，不固定轮次。

### 11.13 压力面模式测试要求

- `InterviewQuestionSet` 驱动，题目完成后结束；固定 3 轮只能作为题组策略候选。

### 11.14 评分 / 复盘测试要求

- 0-100 多维评分、证据绑定、真实复盘、模拟复盘、弱项 / 训练建议。

### 11.15 Markdown 导出测试要求

- 复制 / Markdown 下载、导出完整复盘 + RAG 引用 + 训练建议，不做完整 PDF。

### 11.16 错误态 / 空状态测试要求

- 未登录、权限不足、空记录、空知识库、RAG 无命中、LLM 失败、导出失败、复盘未生成。

### 11.17 治理验证

- `validate-state` / `evaluate-state` 是治理验证，不替代业务测试。

## 12. 数据 / API / UI / 状态边界

- 数据边界：引用 `ST13_20` schema contract，不创建数据库测试。
- API 边界：引用 `ST13_21` API contract，不创建 API 测试代码。
- UI 边界：定义验收维度，不创建页面。
- 状态边界：不修改 `DOC_STATE.yaml`。

## 13. 权限 / 安全 / 隐私边界

- 测试矩阵必须覆盖用户数据隔离、管理员公共知识库、私有上传、导出权限、LLM 日志脱敏。
- 测试 fixture 不得包含真实简历、真实 provider key 或私有知识库内容。

## 14. 错误态 / 空状态

- 每个后续 ST13 必须列出空态、失败态、权限态和恢复路径。
- 错误态验收不得只依赖 happy path。

## 15. 验收标准

- 五层 DoD 均有定义。
- API、数据库、RAG、LLM provider、多轮、打磨、压力面、评分 / 复盘、Markdown 导出、错误态 / 空状态均有测试要求。
- 明确当前不创建 `tests/**`。

## 16. 测试要求

本任务未来 required tests 包括：

- doc-governor validate/evaluate 不退化。
- 每个 ST13 的 acceptance criteria 与 required tests 可追溯到 W13 事实源。
- 临时产物治理符合 `TEST_POLICY.md`。

本窗口只运行状态验证和关键词 / 禁止范围检查，不创建测试代码。

## 17. 允许修改范围

本窗口允许：

- `docs/superpowers/plans/st13-task-packages/ST13_24/ST13_24_DESIGN.md`
- `docs/superpowers/plans/st13-task-packages/ST13_24/ST13_24_IMPLEMENTATION.md`
- 用户授权的父索引与 W13 计划文档同步。

## 18. 禁止修改范围

- `tests/**`
- `tools/**`
- `apps/**`
- `infra/**`
- `docs/governance/**`
- `docs/governance/DOC_STATE.yaml`
- test runner、pytest fixture、CI 配置

## 19. 用户确认项

- `OQ-111=A`：采用集中任务包目录。
- `OQ-112=A`：允许创建第一批正式双文档。
- `OQ-113=B`：后续单独 State Update 更新 required doc slot。

## 20. 下游任务

- 所有 ST13 formal window。
- W13-E9 contract 细化。
- W13-E10 readiness 复核。
- W13-E11 formal window 候选评估。

## 21. 当前不进入实现说明

本文件创建后，`ST13_24` 仍是 `not implementation-ready`。当前不创建测试代码，不生成 implementation packet，不打开 formal window。

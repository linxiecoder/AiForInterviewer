---
title: SUBTASK_DESIGN
type: note
permalink: ai-for-interviewer/docs/modules/m01-foundation-and-platform/sub-modules/st01-01-runtime-and-repo-baseline/subtask-design
---

# ST01_01 运行环境与仓库基线子任务设计文档

## 1. 文档状态

- 文档状态：正式状态条目已存在，当前 scoped formal window 已打开，`implementation_approval_status=approved`，`implementation_ready=true`，`can_generate_implementation_packet=true`。
- 文档层级：M01 基础设施根模块下的正式子任务设计入口。
- 当前用途：记录 ST01_01 runtime baseline implementation 本窗实际落地结果。
- 当前限制：本窗口不修改 `docs/governance/DOC_STATE.yaml`，不修改 tools/tests/CI 配置，不发起业务实现，仅完成 runtime baseline 最小实现所需范围。
- 状态口径：`docs/governance/DOC_STATE.yaml` 是正式真值；本文档只同步当前事实，不通过 Markdown 自行扩大 `candidate_status`、`readiness`、`implementation_ready` 或 runtime 实施授权。

## 2. 子任务定位

ST01_01 只负责运行环境与仓库基线，目标是把 M01 中已经收敛的最小工程边界明确并记录 ST01_01 runtime baseline implementation 的边界与本窗结果。

本子任务覆盖：

- workspace baseline：根目录脚本、包管理入口、环境样例和 monorepo 目录边界。
- API runtime baseline：已落地最小 `apps/api/**` 入口、`/api/v1/health` 与 API lane 验证口径。
- Web runtime baseline：现有 Web 原型资产的现状判断、未来 Web lane 验证口径和与正式 Workbench MVP 的边界。
- environment baseline：`.env.example` 与本地依赖说明的最小约束。
- verification baseline：状态验证、API health smoke、Web smoke 和 API / Web 双 lane 验证口径。

本文档不承担业务模块设计、身份鉴权、数据库、RAG、评分复盘、导出或真实 LLM 接入。

## 3. 上游输入

- `AGENTS.md`
- `docs/DOC_GOVERNANCE.md`
- `docs/governance/DOC_AUTOMATION.md`
- `docs/governance/TEST_POLICY.md`
- `README.md`
- `PLAN_LATEST.md`
- `TASK_INDEX.md`
- `MODULE_INDEX.md`
- `docs/governance/DOC_STATE.yaml`
- `docs/requirements/workbench-mvp/README.md`
- `docs/requirements/workbench-mvp/scope-and-acceptance.md`
- `docs/design/workbench-mvp/README.md`
- `docs/design/workbench-mvp/scope.md`
- `docs/design/workbench-mvp/information-architecture.md`
- `docs/design/workbench-mvp/object-model-rag-multiround-backend.md`
- `docs/design/workbench-mvp/scoring-review-export-dod.md`
- `docs/modules/M01-foundation-and-platform/MODULE_REQUIREMENTS.md`
- `docs/modules/M01-foundation-and-platform/MODULE_DESIGN.md`
- `docs/modules/M01-foundation-and-platform/MODULE_API_DESIGN.md`
- `docs/modules/M01-foundation-and-platform/MODULE_SCHEMA_DESIGN.md`
- `docs/modules/M01-foundation-and-platform/MODULE_LOGIC_DESIGN.md`
- `docs/modules/M01-foundation-and-platform/MODULE_DEPENDENCIES.md`
- `docs/modules/M01-foundation-and-platform/MODULE_TASK_INDEX.md`
- `docs/modules/M01-foundation-and-platform/MODULE_OPEN_QUESTIONS.md`
- `docs/modules/M01-foundation-and-platform/MODULE_EXECUTION_LOG.md`

## 4. 目标

1. 将 ST01_01 作为正式子任务设计入口，记录 runtime baseline 实施范围。
2. 已明确最小运行环境与仓库基线 allowed / forbidden / DoD / validation。
3. 明确当前 `apps/web` 只能作为 W10 mock / 前端原型资产和历史参考，不是 Workbench MVP 的正式实现基础。
4. 明确 ST01_01 继续承接 runtime baseline，不另开新 task；本窗口已完成最小实现落地。
5. 明确 `/api/v1/health` 的最小契约：只返回 `{ "status": "ok" }`，不访问数据库、Redis、对象存储或 LLM。
6. 已完成 ST01_01 runtime baseline 实施：建立 `apps/api/**` 最小入口并落地 `GET /api/v1/health`。

## 5. 非目标

- 不创建数据库 schema、migration、ORM、repository 或持久化层。
- 不创建或修改 `.github/**`。
- 不创建或修改 `tests/**`。
- 不接入真实 LLM、RAG、Redis、PostgreSQL、MinIO 或对象存储。
- 不做 M02 auth、登录、会话、权限或团队成员能力。
- 不做业务 API 路由。
- 不做评分、复盘、导出、RAG、知识库、面试会话或多轮业务能力。
- 不修改正式 `docs/governance/DOC_STATE.yaml`。
- 不修改已生成 packet 文件，不以本窗口文档作为 runtime 授权口径扩展依据。

## 6. 当前仓库基线判断

当前窗口已完成 ST01_01 runtime baseline 的最小实现。

- M01 模块文档已经将根目录脚本、health check、API / Web 双 lane、`apps/web` / `apps/api` / `infra` 目标拓扑收敛到共享最小层。
- `MQ-001`、`MQ-003`、`MQ-005` 已从方向级缺口压缩为共享最小层与后续实现级细化项。
- `docs/governance/DOC_STATE.yaml` 仍是正式状态真值；当前 M01 已是 `maturity=L5`、`readiness=downstream_ready`，但该状态只表示可支撑 ST01 子任务入口与后续审查。
- `docs/governance/DOC_STATE.yaml` 已存在正式 `subtasks.ST01_01` entry，且 `implementation_doc_state=active_working_doc`。
- ST01_01 当前是 `maturity=L4`、`readiness=downstream_ready`、`candidate_status=none`、scoped `formal_window_status=open`。
- `global_policy.formal_window_open=false` 仍保持不变；当前 scoped formal window 已局部打开。
- ST01_01 当前 `implementation_approval_status=approved`，`implementation_ready=true`，`can_generate_implementation_packet=true`。
- 当前 ST01_01 gate 已通过，未保留 `gate:implementation_approval_missing` blocker。
- 当前窗口已在最小范围落地 `apps/api/**` 与 `GET /api/v1/health`，并补充基础 `infra/**`/`.env.example`；`M02/M03` 不在本窗口范围。
- 当前窗口已落地 `apps/api/**` 与最小 runtime code；M02/M03 不在本窗口范围。
- 当前 `apps/web` 仅可视为 W10 mock / 前端原型资产；可作为历史观察材料，但不能作为 Workbench MVP 正式实现基线。

本轮结论：ST01_01 已完成 runtime baseline implementation 最小范围，执行结果同步本窗口实施事实。

## 7. 设计范围

### 7.1 工作区基线

以下边界可沿用，不改变本窗口已落地范围：

- 根目录脚本命名保持 API / Web 双 lane 可区分。
- 根目录脚本不得隐式启动真实数据库、缓存、对象存储或 LLM provider。
- `.env.example` 只允许声明最小本地开发变量和占位说明，不得写入真实密钥。
- 目标目录拓扑为 `apps/web`、`apps/api`、`infra`；本窗口 runtime baseline allowed paths 包含 `apps/api/**` 与 `infra/**` 的 minimal 占位，`apps/web/**` 不在 implementation scope。
- 任何脚本、环境变量或依赖入口都必须能被后续测试命令验证，而不是只停留在 README 说明。

### 7.2 API 运行时基线

最小 API runtime 的本窗约束如下：

- API 入口仅覆盖健康检查。
- 健康检查路径固定为 `GET /api/v1/health`。
- 响应体固定为：

```json
{ "status": "ok" }
```

- 健康检查不得访问数据库、Redis、对象存储、LLM、RAG、队列或外部网络服务。
- 健康检查不得包含业务会话、用户身份、权限、岗位、简历、评分、复盘或导出逻辑。
- API runtime 的第一目标是证明后端进程可启动、路由可达、API lane 可被测试，而不是承载业务能力。

### 7.3 Web 运行时基线

Web lane 维持最小不破坏验证，但必须先处理当前事实边界：

- 当前 `apps/web` 是 W10 mock / 前端原型资产，不是 Workbench MVP 正式实现基础。
- 现有 Web 资产可作为视觉、交互或测试命令观察材料，但不能直接证明 Workbench MVP 业务链路已经可实施。
- Web lane 的最小目标是保持已有前端 smoke 能运行，并与 API lane 形成可并行验证的工程基线。
- 本子任务不重写 App Shell、i18n、页面容器、列表原语或业务工作台；这些属于 ST01_02 或后续业务模块。

### 7.4 环境基线

环境说明与占位要求：

- `.env.example` 只声明示例变量，不包含真实凭据。
- 与数据库、Redis、对象存储、LLM、RAG 或队列相关的变量只能作为后续能力预留，不得在 ST01_01 中要求可用。
- 本地启动说明必须区分 API lane 与 Web lane。
- 环境缺失时的失败信息应指向缺失的最小运行条件，而不是引导用户配置完整生产依赖。

### 7.5 验证基线

runtime baseline 的最小验证分为治理验证和工程验证：

- 治理验证：
  - `python3 -m tools.doc_governor.cli validate-state --input docs/governance/DOC_STATE.yaml`
  - `python3 -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml --entity-type subtask --entity-id ST01_01`
- API lane：
  - future `test:api` health smoke。
  - 验证 `/api/v1/health` 返回 `200` 与 `{ "status": "ok" }`。
- Web lane：
  - future `test:web` existing web smoke。
  - 验证 Web 原型或正式 Web lane 的最小 smoke 不被 API baseline 破坏。
- 双 lane：
  - future API / Web 双 lane 验证，证明两个入口可独立运行、独立失败、独立定位。

本轮运行治理验证与 API smoke，不新增 tests/CI 文件。

## 8. 对下游输出

ST01_01 对下游只输出以下内容：

- 一个已落地 runtime / repo baseline 设计入口。
- 对 `apps/web` 原型资产与正式 Workbench MVP 实现基线的明确区分。
- 对本窗口落地范围中 `apps/api/**`、根脚本、`.env.example`、`infra/**` 和健康检查的最小边界；该边界不构成本窗口 runtime code 授权。
- 对 `/api/v1/health` 的无外部依赖契约。
- 对 ST01_02 和 ST01_03 的前置关系说明：它们可以依赖 ST01_01 的目录、运行时和验证基线，但不得在本轮被打开或扩展。

ST01_01 不输出：

- M02 / M03 或其他业务模块的实现条件。
- 数据库、RAG、LLM、评分、复盘、导出的实施方案。
- 本窗口 runtime code implementation 授权。
- 本窗口不重新生成新的 implementation packet；后续只同步状态与索引入口。

## 9. 风险与约束

- 状态误读风险：当前 `implementation_ready=true` 容易被误读为 runtime code 已授权；必须以正式状态与允许路径共同控制实施边界。
- 原型误读风险：当前 `apps/web` 可能被误读为正式 Workbench MVP 实现基础；本文档明确将其降为 W10 mock / 前端原型资产。
- 范围膨胀风险：`/api/v1/health` 可能被顺手扩展为数据库、Redis、对象存储或 LLM 探活；ST01_01 明确禁止。
- 下游抢跑风险：ST01_01 的 scoped formal window 已打开且 approval 已写入，不代表 M02 / M03 可以开始业务实现。
- 状态写回风险：正文中的 L5 / downstream / active working doc 建议不能自动导入 `DOC_STATE.yaml`。

## 10. 设计验收标准

- ST01_01 设计文档已脱离空模板和历史骨架。
- 设计范围明确覆盖 workspace baseline、API runtime baseline、Web runtime baseline、environment baseline、verification baseline。
- 已明确当前 `apps/web` 是 W10 mock / 前端原型资产，不是 Workbench MVP 正式实现基础。
- 已明确本轮落地范围包含最小 `apps/api/**`、`.env.example`、`infra/**` 与 `GET /api/v1/health`。
- 已明确 `/api/v1/health` 只返回 `{ "status": "ok" }`，不访问数据库、Redis、对象存储或 LLM。
- 已明确不做 M02 auth、不做业务路由、不做数据库、不做 RAG、不做评分复盘导出。
- 已同步本窗口实施结果；当前 official state 已 approved 且 `implementation_ready=true`，本窗口 runtime baseline 已在已授权范围内落地。

## 11. 当前状态摘录

### 11.1 M01 当前状态

- `maturity=L5`。
- `candidate_status=observe`。
- `review_status=pending_confirmation`。
- `readiness=downstream_ready`。
- `blocker_refs=[]`。
- 该状态只表示 M01 可支撑 ST01 子任务入口与后续审查，不表示可以直接进入基础设施或业务实现。

### 11.2 ST01_01 当前状态

- 已存在正式 `DOC_STATE.yaml -> subtasks.ST01_01` entry。
- `meta.module_id=M01`。
- `implementation_doc_state=active_working_doc`。
- `maturity=L4`。
- `readiness=downstream_ready`。
- scoped `formal_window_status=open`。
- `global_policy.formal_window_open=false`。
- `candidate_status=none`。
- `implementation_approval_status=approved`。
- `implementation_ready=true`。
- `can_generate_implementation_packet=true`。
- 本窗实施结果已落地；后续同步以本窗口状态与索引为准。

本文档不作为 runtime code 实施授权口径；以 `DOC_STATE.yaml` 与正式验证结果为准。

## 12. 当前不进入实现说明

本窗口已完成 ST01_01 runtime baseline implementation（`apps/api/**` 与 `GET /api/v1/health`）。仍不代表：

- 可将 `apps/web/**` 作为 runtime business 实现。
- 可接入数据库、Redis、对象存储、LLM 或 RAG。
- 可修改 `docs/governance/DOC_STATE.yaml`。
- 已落地结果同步了 allowed / forbidden 实施边界。
- M02 / M03 已可启动业务实现。

下一步推进建议聚焦 ST01_02 前置同步；本窗口不修改 packet 文件、也不改正式状态入口。
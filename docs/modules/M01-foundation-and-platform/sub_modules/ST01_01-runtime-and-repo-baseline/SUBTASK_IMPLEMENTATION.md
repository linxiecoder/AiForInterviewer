# ST01_01 运行环境与仓库基线子任务实施文档

## 1. 文档状态

- 文档状态：正式状态条目已存在，当前 scoped formal window 已打开，`implementation_approval_status=approved`，`implementation_ready=true`，`can_generate_implementation_packet=true`。
- 文档用途：记录 ST01_01 runtime baseline implementation 的实施边界和本轮已落地结果。
- 当前限制：本窗口不修改 `docs/governance/DOC_STATE.yaml`，不改 tools/tests/CI 配置，不启动业务功能实现，仅完成 runtime baseline 最小实现。
- 上游设计：[`SUBTASK_DESIGN.md`](SUBTASK_DESIGN.md)。

## 2. 本轮实施目标

本轮实际目标是完成 ST01_01 的 runtime baseline implementation，实现最小 FastAPI 运行时与 `GET /api/v1/health`。

1. 明确 ST01_01 继续承接最小 runtime baseline，不另开新 task。
2. 明确本窗口已落地的 `apps/api/**`、`.env.example`、`infra/**`、`package.json`、`requirements.txt` 与 `pytest.ini`。
3. 明确 forbidden paths 为排除业务实现和重型基础设施，保持 runtime baseline 的最小边界。
4. 明确 ST01_01 runtime baseline DoD：GET /api/v1/health 可达、无外部依赖、环境模板安全、API / Web lane 可区分。
5. 明确 required validation：状态 gate、diff check、API health smoke 和现有 Web lane smoke。
6. 已完成 runtime code 落地：最小 FastAPI 入口与健康检查。

## 3. 前置条件

当前状态前提：

- M01 当前已是 `maturity=L5`、`readiness=downstream_ready`，但该状态只支撑 ST01 子任务入口和后续审查，不直接放行实现。
- ST01_01 的 `design_doc.exists=true`、`design_doc.template_like=false`、`implementation_doc.exists=true`、`implementation_doc.template_like=false` 已被状态层确认。
- ST01_01 当前已有正式 entry，且 `implementation_doc_state=active_working_doc`。
- ST01_01 当前是 `maturity=L4`、`readiness=downstream_ready`、scoped `formal_window_status=open`、`candidate_status=none`。
- `global_policy.formal_window_open=false` 仍保持不变；当前 scoped formal window 已局部打开。
- ST01_01 当前 `implementation_approval_status=approved`。
- ST01_01 当前 `implementation_ready=true`、`can_generate_implementation_packet=true`。
- 当前 gate 已通过，已无 `gate:implementation_approval_missing` blocker。
- 本窗口已按 packet 授权完成最小 runtime baseline，范围覆盖 `apps/api/**`、`.env.example`、`infra/**`、`package.json`、`requirements.txt`、`pytest.ini` 与索引文档。
- 当前窗口已创建 `apps/api/**` 与最小入口实现；M02/M03 不在本窗口范围。

runtime implementation 落地已完成。

- 允许范围已落地：`apps/api/**`、`.env.example`、`infra/**`、`package.json`、`requirements.txt`、`pytest.ini`。
- 本轮不变更：`docs/governance/DOC_STATE.yaml` 与 `docs/governance/packets/**`。

## 4. 允许修改范围

以下路径为本窗口已落地 runtime baseline 的 allowed paths：

- `apps/api/**`
- `.env.example`
- `infra/**`
- `package.json`
- `requirements.txt`
- `pytest.ini`
- `docs/modules/M01-foundation-and-platform/sub_modules/ST01_01-runtime-and-repo-baseline/SUBTASK_DESIGN.md`
- `docs/modules/M01-foundation-and-platform/sub_modules/ST01_01-runtime-and-repo-baseline/SUBTASK_IMPLEMENTATION.md`
- `TASK_INDEX.md`
- `docs/modules/M01-foundation-and-platform/MODULE_TASK_INDEX.md`
- `docs/modules/M01-foundation-and-platform/MODULE_DEPENDENCIES.md`

## 5. 禁止修改

以下路径与能力为当前窗口禁止修改范围；禁止范围用于排除业务实现和重型基础设施，不应 blanket 禁止 API runtime 或本地 infra 占位路径：

- `docs/governance/DOC_STATE.yaml`
- `docs/governance/transition_history.jsonl`
- `.github/**`
- `tools/**`
- `tests/**`
- `apps/web/**`
- 任何 M02/M03 业务实现文件
- 登录、会话、权限、团队成员业务
- 岗位 / 简历 / 面试 / 评分 / 复盘 / 导出业务 API
- 数据库 migration / ORM / schema / repository 实现
- LLM provider 接入
- RAG / embedding 接入
- Redis / PostgreSQL / MinIO 真实接入
- 对象存储真实 bucket / client / provider 初始化
- Dashboard 壳层、App Shell、PageHeader、DataTable 实现
- 完整测试 / CI workflow / lint gate / E2E / 多平台矩阵
- 大规模重构

### 5.1 当前授权范围说明

本窗口已对 ST01_01 双文档、TASK_INDEX.md 与必要 M01 模块索引完成落地；allowed / forbidden 范围用于本窗口 runtime baseline 约束。

## 6. 当前 runtime baseline 授权边界

以下内容为本窗口已实施范围：

- `apps/api/**` 只用于最小 FastAPI runtime 与 `GET /api/v1/health`。
- `.env.example` 只用于安全占位变量模板，不包含真实 secret / DSN。
- `infra/**` 只用于本地占位说明或最小占位，不接真实服务。
- `package.json`、`requirements.txt`、`pytest.ini` 只用于区分 API lane、Web lane 和最小 health smoke 所需入口。
- `apps/web/**` 不进入本次 runtime implementation allowed paths；Web lane 仅保留现有 `npm run web:test` smoke 作为不破坏验证。
- `tests/**` 不进入本次 runtime implementation allowed paths；API health smoke 后续根据实际入口用最小方式确定，不扩张为完整测试 / CI 基线。
- M02/M03 不属于 ST01_01 runtime baseline 候选范围。
- 后续即使 runtime baseline 获得授权，也只能围绕最小 API runtime、`GET /api/v1/health`、本地占位说明和 API / Web 双 lane 验证口径讨论，不得扩张到业务实现。

## 7. 实施范围与验证要求

本窗口已完成范围如下：

- 建立最小 API runtime 入口。
- 提供 `GET /api/v1/health`。
- 健康检查只返回：

```json
{ "status": "ok" }
```

- 健康检查不访问数据库、Redis、对象存储、LLM、RAG、队列或外部网络服务。
- 建立或校准 API lane 的最小 health smoke 入口。
- 保持 Web lane 现有 `npm run web:test` smoke 可验证，但不把 W10 mock / 前端原型资产提升为 Workbench MVP 正式实现基础。
- 建立 API / Web 双 lane 的最小本地验证口径。
- 更新必要文档，记录实际创建的路径、命令和验证结果。

运行时实施后续不再包含的范围：

- M02 身份、团队、登录、权限、会话。
- 业务路由、业务 DTO、业务数据库表。
- RAG、知识库、embedding、LLM provider。
- 评分、复盘、导出。
- 完整 CI workflow、lint / format gate、E2E、多平台矩阵或完整测试基线。

## 8. 测试与验证

### 8.1 自动化验证

本窗口必须复核：

- 必须运行：`python3 -m tools.doc_governor.cli validate-state --input docs/governance/DOC_STATE.yaml`
- 必须运行：`python3 -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml --entity-type subtask --entity-id ST01_01`
- 必须运行：`python3 -m tools.doc_governor.cli preflight-open-window --subtask ST01_01`
- 必须运行：`git diff --check`
- 必须运行：`git status --short`

runtime baseline 实施要求以下验证：

- API health smoke 根据后续实际入口确定，例如用最小 pytest 或等价 HTTP smoke 覆盖 /api/v1/health。
- Web lane smoke 保持现有命令：`npm run web:test`
- Web lane smoke 只作为不破坏现有 Web lane 的验证，不作为 Web runtime 实现授权。
- API health smoke 必须验证 GET /api/v1/health 返回 200，且响应 JSON 的 status 字段等于 ok。
- 双 lane 验证必须能区分 API lane 与 Web lane 的失败来源。

### 8.2 手动验证

- 手动复核 git status --short，确认本轮未触碰 apps/**、infra/**、.github/**、tools/**、tests/**、docs/governance/DOC_STATE.yaml 或 docs/governance/packets/**。
- 手动复核 ST01_01 双文档标题和章节标题，确认不再出现未白名单英文标题。
- 手动复核 evaluate-state、preview 和 preflight 的 ST01_01 gate blockers，确认不再出现 scope、tests、acceptance、language、formal-window-closed 或 path scope blocker。

## 9. 完成判定

runtime baseline implementation acceptance criteria：

- ST01_01 official state 摘录已同步为 `implementation_approval_status=approved`、`implementation_ready=true`、`can_generate_implementation_packet=true`。
- ST01_01 双文档已脱离历史骨架和空模板。
- allowed_modify_paths 已包含最小 runtime baseline 路径，包括 apps/api/**、.env.example、infra/**、package.json、requirements.txt、pytest.ini 和 ST01_01 文档 / 索引路径。
- forbidden_paths 不再 blanket 禁止 apps/api/** 或 infra/**，但继续禁止业务实现、重型基础设施、测试 / CI 基线、Web shell 和 M02/M03。
- required tests 已覆盖状态验证、diff check、API health smoke、现有 Web lane smoke 和 API / Web 双 lane 失败来源区分。
- GET /api/v1/health 可达并返回 200，且响应 JSON 的 status 字段等于 ok。
- health check 不访问 DB、Redis、MinIO、LLM、RAG 或外部网络。
- API runtime 可本地启动，失败信息指向最小缺失条件。
- .env.example 只包含安全占位，不含真实 secret / DSN。
- 根目录脚本或等价入口能区分 API lane 与 Web lane。
- 不触碰业务模块实现。
- ST01_01 文档和索引同步记录实际 runtime baseline 边界。
- path_conflicts=[]。

必须明确的负向验收：

- 不代表可以创建或修改 apps/web/**。
- 不代表可以修改 .github/**、tests/** 或 tools/**。
- 不代表 M02 / M03 可以开始业务实现。
- 不代表可以接入数据库、Redis、PostgreSQL、MinIO、对象存储、LLM 或 RAG。
- 不代表可以实现登录、权限、岗位、简历、面试、评分、复盘或导出业务 API。

## 10. 停止条件与回滚条件

未来 implementation window 如出现以下任一情况必须停止：

- `validate-state` 或 `evaluate-state` 失败。
- `DOC_STATE.yaml` 未确认 ST01_01 正式 entry，却开始执行代码改动。
- 不在 packet 范围之外新增新业务实现路径。
- 不以本窗口改动的说明性文本替代已授权 packet 的实现边界。
- `allowed_modify_paths` 与 `forbidden_paths` 出现 `path_scope_conflict`。
- 健康检查需要数据库、Redis、MinIO、对象存储、LLM、RAG 或外部网络才能通过。
- 改动越过 ST01_01 边界，进入 M02 auth、业务路由、数据库 schema、评分、复盘或导出。
- `apps/web` 原型资产被当作正式 Workbench MVP 实现基础继续堆叠。
- 测试或脚本在仓库根目录或 `tests/` 下遗留被禁止的 `tmp` / `temp` 目录。

未来 implementation window 的 rollback 原则：

- 回退本窗口新增的 runtime / script / env / docs 改动。
- 保留独立状态确认窗口已经正式写入且仍有效的 confirmed state；不得用代码回滚顺手改写状态真值。
- 若状态写入本身有误，必须由独立 State Update / rollback 窗口处理。

## 11. 当前状态摘录

### 11.1 M01 当前状态

- `maturity=L5`。
- `candidate_status=observe`。
- `review_status=pending_confirmation`。
- `readiness=downstream_ready`。
- `blocker_refs=[]`。
- 明确：该状态只表示 M01 可支撑 ST01 子任务入口与后续审查，不表示 M01 可直接实现基础设施代码。

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
- 当前已完成 runtime baseline implementation，`ST01_01` 实施结果已同步到索引与双文档。

本文档不复述实现授权口径；runtime 实施授权依据仍以 `DOC_STATE.yaml` 与正式状态为准。

## 12. 当前窗口不执行说明

本窗口执行 ST01_01 runtime baseline implementation 和必要索引同步。

本窗口不执行：

- 不创建或修改 `apps/web/**`、`tests/**`、`tools/**`、`.github/**`。
- 不创建数据库 schema / migration / ORM / repository。
- 不启动 M02/M03。
- 不接入真实 LLM / RAG / Redis / PostgreSQL / MinIO。
- 不修改 `docs/governance/DOC_STATE.yaml`。
- 不修改 `docs/governance/packets/**`。
- 不启动业务实现，不扩展到 `apps/web/**`、`tests/**`、`tools/**`、`.github/**`。
- 不提交、不推送。

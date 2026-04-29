# ST01_01 运行环境与仓库基线子任务实施文档

## 1. 文档状态

- 文档状态：正式状态条目已存在，当前 scoped formal window 已打开，本文档作为 implementation approval readiness 审查输入。
- 文档用途：分层记录当前 docs-only 修复范围、当前 scoped formal window 审查范围，以及后续 runtime implementation approval 候选范围。
- 当前限制：本文档不是 State Update、implementation approval 或 implementation 窗口；不修改 `docs/governance/DOC_STATE.yaml`，不写 implementation approval，不生成 implementation packet，不声明 `implementation_ready`，不创建 `apps/api/**`。
- 上游设计：[`SUBTASK_DESIGN.md`](SUBTASK_DESIGN.md)。

## 2. 本轮实施目标

本轮的实际目标不是执行基础设施实现，而是修复 ST01_01 的滞后状态摘录并把后续审查输入写清楚：

1. 修正旧的阻塞态、未开窗语义和 formal-window-closed blocker 摘录。
2. 明确当前 docs-only 修复窗口的允许修改范围只限 ST01_01 双文档和必要索引。
3. 明确当前 docs-only 修复窗口的禁止修改范围。
4. 将后续 runtime implementation approval 候选范围放在非当前授权层，不写成当前允许路径。
5. 形成后续只读 approval preview 输入，但不写正式状态，不写 implementation approval。

## 3. 前置条件

当前状态前提：

- M01 当前已是 `maturity=L5`、`readiness=downstream_ready`，但该状态只支撑 ST01 子任务入口和后续审查，不直接放行实现。
- ST01_01 的 `design_doc.exists=true`、`design_doc.template_like=false`、`implementation_doc.exists=true`、`implementation_doc.template_like=false` 已被状态层确认。
- ST01_01 当前已有正式 entry，且 `implementation_doc_state=active_working_doc`。
- ST01_01 当前是 `maturity=L4`、`readiness=downstream_ready`、scoped `formal_window_status=open`、`candidate_status=none`。
- `global_policy.formal_window_open=false` 仍保持不变；当前 scoped formal window 已局部打开，但不等于 implementation approval。
- ST01_01 当前 `implementation_approval_status` 未登记 / 未批准，`implementation_ready=false`。
- 当前剩余 blocker 为 `gate:implementation_approval_missing`。
- 当前仍不得创建 `apps/api/**`，不得修改 runtime code，不得启动 M02/M03。

后续写入 implementation approval 前，至少需要满足：

- 另开 state-only approval confirmation 或 approval preview 窗口，且用户明确授权该窗口处理 approval。
- gate 明确确认 `allowed_modify_paths`、`forbidden_paths`、required tests、acceptance criteria、path conflict、M02/M03 边界全部通过。
- approval preview 不再因旧状态摘录、formal-window-closed 语义或 path scope 语义阻断。
- 只有 implementation approval 被独立写入后，才可进入 implementation packet 生成判断。

若上述任一条件不满足，只能继续停留在 docs-only 修复 / approval readiness review / 后续审查输入阶段。

## 4. 允许修改范围

以下路径是当前 docs-only 修复窗口的唯一允许修改范围：

- `docs/modules/M01-foundation-and-platform/sub_modules/ST01_01-runtime-and-repo-baseline/SUBTASK_DESIGN.md`
- `docs/modules/M01-foundation-and-platform/sub_modules/ST01_01-runtime-and-repo-baseline/SUBTASK_IMPLEMENTATION.md`
- `TASK_INDEX.md`
- `docs/modules/M01-foundation-and-platform/MODULE_TASK_INDEX.md`
- `docs/modules/M01-foundation-and-platform/MODULE_DEPENDENCIES.md`

## 5. 禁止修改

以下是当前 docs-only 修复窗口的禁止范围；这不代表后续 implementation approval 后的最终禁止范围：

- `docs/governance/DOC_STATE.yaml`
- `apps/**`
- `apps/api/**`
- `infra/**`
- `.github/**`
- `tools/doc_governor/**`
- `tests/doc_governor/**`
- `tests/**`
- 任何运行时代码
- 任何数据库 migration / ORM / schema 实现
- 任何真实 LLM / RAG / Redis / PostgreSQL / MinIO / 对象存储接入
- 任何 M02/M03 业务实现文件

### 5.1 当前授权范围说明

本轮只允许修改 ST01_01 双文档、`TASK_INDEX.md` 与必要的 M01 模块索引表述。

## 6. 后续审批事项（非当前授权）

以下内容仅作为下一轮 approval preview 的候选审查输入，不构成本窗口授权；候选路径必须在独立 implementation approval 写入后才可使用，且不得被当前 docs-only 窗口或当前 preflight 解释为 current `allowed_modify_paths`：

- `apps/api/**` 可能作为后续 runtime baseline implementation 的候选路径。
- 相关测试路径如 `tests/**` 只有在后续 implementation approval 明确批准后才可进入实施范围。
- 根目录脚本、`.env.example` 或 API 相关依赖入口只有在后续 approval 明确批准后才可进入实施范围。
- `infra/**`、`.github/**`、`tools/**` 默认不进入 ST01_01 runtime baseline implementation 候选范围，除非后续独立审批另行说明。
- M02/M03 不属于 ST01_01 implementation approval 候选范围。
- 后续即使 approval 获批，也只能围绕最小 API runtime、`GET /api/v1/health`、本地占位说明和 API / Web 双 lane 验证口径讨论，不得扩张到业务实现。

## 7. 后续实施范围

后续若单独获得 implementation approval，implementation scope 应限制为：

- 建立最小 API runtime 入口。
- 提供 `GET /api/v1/health`。
- 健康检查只返回：

```json
{ "status": "ok" }
```

- 健康检查不访问数据库、Redis、对象存储、LLM、RAG、队列或外部网络服务。
- 建立或校准 API lane 的最小测试入口。
- 保持 Web lane 现有 smoke 可验证，但不把 W10 mock / 前端原型资产提升为 Workbench MVP 正式实现基础。
- 建立 API / Web 双 lane 的最小本地验证口径。
- 更新必要文档，记录实际创建的路径、命令和验证结果。

后续 approval 候选范围不应包含：

- M02 身份、团队、登录、权限、会话。
- 业务路由、业务 DTO、业务数据库表。
- RAG、知识库、embedding、LLM provider。
- 评分、复盘、导出。
- 完整 CI workflow、lint / format gate、E2E 或多平台矩阵。

## 8. 测试与验证

### 8.1 自动化验证

本轮实际运行的只读验证必须包括：

- 本轮必须运行：`python3 -m tools.doc_governor.cli validate-state --input docs/governance/DOC_STATE.yaml`
- 本轮必须运行：`python3 -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml`
- 本轮必须运行：`python3 -m tools.doc_governor.cli preview-task-readiness-state-sync --entity-id ST01_01`
- 本轮必须运行：`python3 -m tools.doc_governor.cli preview-task-formal-window-sync --entity-id ST01_01`
- 本轮必须运行：`python3 -m tools.doc_governor.cli preview-task-state-dependency-map --entity-id ST01_01`
- 本轮必须运行：`python3 -m tools.doc_governor.cli preflight-open-window --subtask ST01_01`
- 本轮必须运行：`git diff --check`
- 本轮必须运行：`git diff -- docs/governance/DOC_STATE.yaml`
- 本轮必须运行：`git status --short`
- 本轮必须运行：`test -e apps/api && echo "apps/api exists" || echo "apps/api missing"`

后续 implementation approval 若批准 runtime 实施，至少应补充：

- 未来需补充：`future test:api health smoke`
- 未来需补充：`future test:web existing web smoke`
- 未来需补充：`future API / Web 双 lane 验证`
- API health smoke 必须验证 `GET /api/v1/health` 返回 `200` 与 `{ "status": "ok" }`。
- Web smoke 必须证明现有 Web lane 未因 ST01_01 基线改动被破坏。
- 双 lane 验证必须能区分 API lane 与 Web lane 的失败来源。

### 8.2 手动验证

- 手动复核 `git status --short`，确认本轮未触碰 `apps/**`、`infra/**`、`.github/**`、`tools/doc_governor/**`、`tests/doc_governor/**` 或 `docs/governance/DOC_STATE.yaml`。
- 手动复核 ST01_01 双文档标题和章节标题，确认不再出现未白名单英文标题。
- 手动复核 `evaluate-state`、preview 和 preflight 的 ST01_01 gate blockers，确认不再出现 scope、tests、acceptance、language、formal-window-closed 或 path scope blocker。

## 9. 完成判定

本轮 acceptance criteria：

- ST01_01 可作为下一轮只读 approval preview 输入。
- ST01_01 双文档已脱离历史骨架和空模板。
- 当前允许文档范围与禁止范围已分层说明。
- 后续 implementation approval 候选范围已明确放在非当前授权层，不会被解释为 current `allowed_modify_paths`。
- required tests 已覆盖状态验证、future API health smoke、future Web smoke 和 future 双 lane 验证。
- 后续状态审查输入已形成，但未写入正式 `DOC_STATE.yaml`。
- `apps/api/**` 只出现在当前禁止范围或后续非授权说明中，不出现在当前 `allowed_modify_paths` 中。
- `path_conflicts=[]`。

必须明确的负向验收：

- 不代表 `implementation_ready`。
- 不代表 implementation approval 已写入。
- 不代表可以创建 `apps/api/**`。
- 不代表可以创建或修改 `apps/**`。
- 不代表可以创建或修改 `infra/**`。
- 不代表可以修改 `.github/**`、`tests/**` 或 `tools/**`。
- 不代表 M02 / M03 可以开始业务实现。
- 不代表可以接入数据库、Redis、对象存储、LLM 或 RAG。

## 10. 停止条件与回滚条件

未来 implementation window 如出现以下任一情况必须停止：

- `validate-state` 或 `evaluate-state` 失败。
- `DOC_STATE.yaml` 未确认 ST01_01 正式 entry，却开始执行代码改动。
- `implementation_approval_status` 未登记 / 未批准，却开始创建实现路径。
- `allowed_modify_paths` 与 `forbidden_paths` 出现 `path_scope_conflict`。
- 健康检查需要数据库、Redis、对象存储、LLM 或 RAG 才能通过。
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
- `implementation_approval_status` 未登记 / 未批准。
- `implementation_ready=false`。
- 当前剩余 blocker 为 `gate:implementation_approval_missing`。

本文档不得把 scoped formal window 已打开改写为已写 implementation approval、已 candidate 或已 implementation-ready。

## 12. 当前窗口不执行说明

本窗口只执行 ST01_01 docs-only implementation approval readiness 口径修复和必要索引同步。

本窗口不执行：

- 不创建 `apps/api/**`。
- 不创建或修改 `apps/**`。
- 不创建或修改 `infra/**`。
- 不创建或修改 `.github/**`。
- 不创建或修改 `tests/**`。
- 不创建或修改 `tools/**`。
- 不创建数据库 schema / migration / ORM / repository。
- 不写运行时代码。
- 不启动 M02/M03。
- 不接入真实 LLM / RAG / Redis / PostgreSQL / MinIO。
- 不修改 `docs/governance/DOC_STATE.yaml`。
- 不写 implementation approval。
- 不生成可执行 implementation packet。
- 不标记 implementation-ready。
- 不提交、不推送。

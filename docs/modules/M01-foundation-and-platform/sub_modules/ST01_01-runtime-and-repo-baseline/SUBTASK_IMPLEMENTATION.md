# ST01_01 运行环境与仓库基线子任务实施文档

## 1. 文档状态

- 文档状态：正式状态条目已存在，当前仅作为 formal window preparation 输入。
- 文档用途：为后续独立 ST01_01 formal window 提供实施边界、允许范围建议、禁止范围、验证要求和停止条件。
- 当前限制：本文档不是本轮执行授权，不修改 `docs/governance/DOC_STATE.yaml`，不打开 formal window，不生成 implementation packet，不声明 `implementation_ready`。
- 上游设计：[`SUBTASK_DESIGN.md`](SUBTASK_DESIGN.md)。

## 2. 本轮实施目标

本轮的实际目标不是执行基础设施实现，而是把 ST01_01 的未来 formal window 输入写清楚：

1. 明确未来 formal window 可建议的最小允许修改范围。
2. 明确本轮强制禁止触碰的路径和能力。
3. 明确未来 implementation scope 只覆盖 runtime / repo baseline。
4. 明确 required tests、acceptance criteria、stop conditions 与 rollback conditions。
5. 形成后续审查输入，但不写正式状态。

## 3. 前置条件

后续 formal window 真正开始前，至少需要满足：

- 用户单独明确授权打开 ST01_01 formal window。
- `docs/governance/DOC_STATE.yaml` 中的 `global_policy.formal_window_open=false` 已被后续独立开窗窗口改变，或已有经批准的 scoped formal window 机制。
- M01 当前已是 `maturity=L5`、`readiness=downstream_ready`，但该状态只支撑 ST01 子任务入口和后续审查，不直接放行实现。
- ST01_01 的 `design_doc.exists=true`、`design_doc.template_like=false`、`implementation_doc.exists=true`、`implementation_doc.template_like=false` 已被状态层确认。
- ST01_01 当前已有正式 entry，且 `implementation_doc_state=active_working_doc`；但 `candidate_status=none`、`readiness=blocked`、`implementation_ready=false` 仍保持不变。
- 全局 `formal_window_open` 或后续 scoped formal window 机制允许该任务进入实施后，才能执行运行时代码改动。
- 禁止范围检查、状态验证和 worktree 差异检查均为绿。

若上述任一条件不满足，只能继续停留在 preparation / review / 后续审查输入阶段。

## 4. 允许修改范围

以下路径仅作为未来 ST01_01 formal window 的建议允许范围，不构成本轮授权；在当前最小文档修复窗口中仍不得修改：

- `apps/api/**`
- `infra/**`
- `package.json`
- API 相关依赖入口。
- `.env.example`
- 根目录脚本相关文件。
- 必要的文档收口文件。

### 4.1 未来开窗限制

未来 formal window 即使获批，也应继续保持最小化：

- `apps/api/**` 只允许最小 API runtime 和 `/api/v1/health`。
- `infra/**` 只允许最小本地开发占位或说明，不允许真实生产化基础设施。
- 根脚本只允许支持 API / Web 双 lane 的最小启动与测试入口。
- `.env.example` 只允许示例变量和占位说明，不允许真实密钥。

## 5. 禁止修改

本轮强制禁止修改：

- `apps/api/**`
- `apps/**`
- `infra/**`
- `.github/**`
- `tests/**`
- `docs/governance/DOC_STATE.yaml`
- `tools/**`
- 任何数据库 migration / ORM / schema 实现
- 任何业务模块代码
- 任何真实 LLM / RAG / Redis / PostgreSQL / MinIO / 对象存储接入
- 任何 M02 auth、业务 API、评分、复盘、导出、知识库或面试会话实现

### 5.1 当前授权范围说明

本轮只允许修改 ST01_01 双文档和必要索引表述。

## 6. 实施范围

未来 formal window 的 implementation scope 应限制为：

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

未来 formal window 不应包含：

- M02 身份、团队、登录、权限、会话。
- 业务路由、业务 DTO、业务数据库表。
- RAG、知识库、embedding、LLM provider。
- 评分、复盘、导出。
- 完整 CI workflow、lint / format gate、E2E 或多平台矩阵。

## 7. 测试与验证

### 7.1 自动化验证

本轮实际运行的只读验证必须包括：

- 本轮必须运行：`python -X utf8 -m tools.doc_governor.cli validate-state --input docs/governance/DOC_STATE.yaml`
- 本轮必须运行：`python -X utf8 -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml`
- 本轮必须运行：`git diff --check`
- 本轮必须运行：`git status --short`

未来 formal window 至少应补充：

- 未来需补充：`future test:api health smoke`
- 未来需补充：`future test:web existing web smoke`
- 未来需补充：`future API / Web 双 lane 验证`
- API health smoke 必须验证 `GET /api/v1/health` 返回 `200` 与 `{ "status": "ok" }`。
- Web smoke 必须证明现有 Web lane 未因 ST01_01 基线改动被破坏。
- 双 lane 验证必须能区分 API lane 与 Web lane 的失败来源。

### 7.2 手动验证

- 手动复核 `git status --short`，确认本轮未触碰 `apps/**`、`infra/**`、`.github/**`、`tests/**`、`tools/**` 或 `docs/governance/DOC_STATE.yaml`。
- 手动复核 ST01_01 双文档标题和章节标题，确认不再出现未白名单英文标题。
- 手动复核 `evaluate-state` 的 ST01_01 gate blockers，确认不再出现 scope、tests、acceptance 或 language blocker。

## 8. 完成判定

本轮 acceptance criteria：

- ST01_01 可作为 future formal window 输入。
- ST01_01 双文档已脱离历史骨架和空模板。
- allowed paths 与 forbidden paths 已分层说明。
- required tests 已覆盖状态验证、future API health smoke、future Web smoke 和 future 双 lane 验证。
- 后续状态审查输入已形成，但未写入正式 `DOC_STATE.yaml`。

必须明确的负向验收：

- 不代表 `implementation_ready`。
- 不代表 formal window 已打开。
- 不代表可以创建 `apps/api/**`。
- 不代表可以创建或修改 `infra/**`。
- 不代表可以修改 `.github/**` 或 `tests/**`。
- 不代表 M02 / M03 可以开始业务实现。
- 不代表可以接入数据库、Redis、对象存储、LLM 或 RAG。

## 9. 停止条件与回滚条件

未来 formal window 如出现以下任一情况必须停止：

- `validate-state` 或 `evaluate-state` 失败。
- `DOC_STATE.yaml` 未确认 ST01_01 正式 entry，却开始执行代码改动。
- `formal_window_open=false` 或 scoped formal window 机制未批准，却开始创建实现路径。
- 健康检查需要数据库、Redis、对象存储、LLM 或 RAG 才能通过。
- 改动越过 ST01_01 边界，进入 M02 auth、业务路由、数据库 schema、评分、复盘或导出。
- `apps/web` 原型资产被当作正式 Workbench MVP 实现基础继续堆叠。
- 测试或脚本在仓库根目录或 `tests/` 下遗留被禁止的 `tmp` / `temp` 目录。

未来 formal window 的 rollback 原则：

- 回退本窗口新增的 runtime / script / env / docs 改动。
- 保留独立状态确认窗口已经正式写入且仍有效的 confirmed state；不得用代码回滚顺手改写状态真值。
- 若状态写入本身有误，必须由独立 State Update / rollback 窗口处理。

## 10. 当前状态摘录

### 10.1 M01 当前状态

- `maturity=L5`。
- `candidate_status=observe`。
- `review_status=pending_confirmation`。
- `readiness=downstream_ready`。
- `blocker_refs=[]`。
- 明确：该状态只表示 M01 可支撑 ST01 子任务入口与后续审查，不表示 M01 可直接实现基础设施代码。

### 10.2 ST01_01 当前状态

- 已存在正式 `DOC_STATE.yaml -> subtasks.ST01_01` entry。
- `meta.module_id=M01`。
- `implementation_doc_state=active_working_doc`。
- `candidate_status=none`。
- `readiness=blocked`。
- `global_policy.formal_window_open=false`。
- `implementation_ready=false`。

本文档不得把上述事实改写为 ST01_01 已开窗、已 candidate、已 downstream_ready 或已 implementation-ready。

## 11. 当前窗口不执行说明

本窗口只执行 ST01_01 formal window preparation 文档重建和必要索引同步。

本窗口不执行：

- 不创建 `apps/api/**`。
- 不创建或修改 `infra/**`。
- 不创建或修改 `.github/**`。
- 不创建或修改 `tests/**`。
- 不创建数据库 schema / migration / ORM / repository。
- 不写运行时代码。
- 不接入真实 LLM / RAG / Redis / PostgreSQL / MinIO。
- 不修改 `docs/governance/DOC_STATE.yaml`。
- 不打开 formal window。
- 不生成可执行 implementation packet。
- 不标记 implementation-ready。
- 不提交、不推送。

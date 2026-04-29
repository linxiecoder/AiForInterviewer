# ST13_21 IMPLEMENTATION：R0 最小 API / 后端服务边界

## 1. 文档状态

- 状态：`draft`
- 文档性质：ST13 任务实施说明；只定义后续 packet 输入，不是 implementation packet。
- 实施状态：`not implementation-ready`
- formal window：`formal window closed`
- implementation packet：`implementation packet forbidden`
- 当前定位：为后续 `ST13_21` state sync / preview / formal window readiness 准备最小实施输入。
- 本窗口不修改 `DOC_STATE.yaml`，不打开 formal window，不生成 packet，不进入 implementation。

## 2. 本轮实施目标

- 在 ST01_01 最小 FastAPI runtime 上建立 API / 后端服务边界骨架，统一 /api/v1 路由注册、最小错误响应、配置读取和未来业务路由占位；不实现任何业务 API、不接 DB、不接 LLM/RAG、不接 Redis/PostgreSQL/MinIO。

## 3. 前置条件

后续真正进入 implementation 前，必须同时满足：

- `ST13_21_DESIGN.md` 已保持 R0 minimal API service boundary，不再以完整 API 合同作为本任务实施范围。
- M02 只作为 downstream identity boundary input；完整身份系统不由本任务实现。
- ST01_01 runtime baseline 已存在，且 health endpoint 不被本任务破坏。
- `DOC_STATE.yaml` 仍由专门状态窗口维护；本文档正文不替代 official state。
- formal window open、implementation_doc_state activation、implementation approval 和 packet generation 均需后续另窗确认。

## 4. 范围内

后续 packet 如获授权，只能覆盖：

- 基于现有 FastAPI runtime 的 API service skeleton。
- `/api/v1` prefix 和 router registration 最小模式。
- health endpoint regression，确保 `GET /api/v1/health` 继续可达。
- 最小 error response / error envelope。
- 最小配置读取边界。
- future routes placeholder / contract boundary。
- M02 identity context 的消费边界说明。

本任务不实现任何业务 API。

## 5. 允许修改范围

候选 allowed paths 仅限以下路径；后续 packet 不得自行扩大：

- `apps/api/**`
- `package.json`
- `requirements.txt`
- `.env.example`
- `docs/tasks/workbench-mvp/st13-task-packages/ST13_21/ST13_21_DESIGN.md`
- `docs/tasks/workbench-mvp/st13-task-packages/ST13_21/ST13_21_IMPLEMENTATION.md`

如果后续确实需要其它路径，只能作为另窗建议或确认卡，不得在本任务内直接扩大。

## 6. 禁止修改

后续 packet 的 candidate forbidden paths 必须至少包含：

- `apps/web/**`
- `.github/**`
- `tools/**`
- `tests/**`
- `docs/governance/DOC_STATE.yaml`
- `docs/governance/transition_history.jsonl`
- `docs/governance/previews/**`
- `docs/governance/packets/**`
- `infra/**`
- DB / ORM / migration / repository
- LLM provider
- RAG / embedding
- Redis / PostgreSQL / MinIO
- 真实对象存储
- M02 / M03 业务实现
- 登录 / 权限完整实现
- Job / Resume / Knowledge / Interview / Score / Review / Export 业务实现
- Dashboard / App Shell / PageHeader / DataTable
- 完整 CI / E2E / 多平台矩阵

禁止范围优先级高于 allowed paths。若后续 packet 发现 path conflict，必须停止。

## 7. 后续实施步骤

以下步骤只供 formal window 和 packet 通过后的实现窗口使用；当前均不执行：

1. 复核 official `DOC_STATE.yaml`、`evaluate-state` 和 `preflight-open-window`。
2. 复核 ST01_01 runtime baseline 中 health endpoint 的当前入口。
3. 建立或整理 `/api/v1` router registration 的最小骨架。
4. 保持 health endpoint 可达，避免迁移回归。
5. 添加最小 error response / error envelope。
6. 添加最小配置读取边界，且不读取外部服务 secret。
7. 只保留 future routes placeholder，不实现业务逻辑。
8. 运行 required validation，并在依赖不可用时记录 environment-blocked。

## 8. 测试与验证

后续 packet 的 required validation 至少包含：

- `python3 -m tools.doc_governor.cli validate-state --input docs/governance/DOC_STATE.yaml`
- `python3 -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml --entity-type subtask --entity-id ST13_21`
- `python3 -m tools.doc_governor.cli preflight-open-window --subtask ST13_21`
- `git diff --check`
- API import / route smoke，前提是依赖可用。
- health endpoint regression smoke，前提是依赖可用。
- 如果依赖不可用，记录 environment-blocked，不允许绕过边界新增 vendor code。
- Web lane smoke 只作为不破坏验证，不作为本任务实现授权。

当前文档修正窗口只运行 governance validation、preflight 和 diff 检查，不执行 API runtime smoke，不启动 dev server。

## 9. 完成判定

`ST13_21` R0 minimal scope 的 acceptance criteria：

- API routes 可以按 /api/v1 prefix 组织。
- health endpoint 继续可达，不被破坏。
- 后端服务边界有清晰 router registration 方式。
- 存在最小 error response / error envelope 约定。
- 配置读取边界只覆盖最小运行参数，不引入外部服务。
- Auth / Identity 仅作为 placeholder / boundary，不实现完整身份系统。
- Job / Resume / Knowledge / Interview / Score / Review / Export 仅作为 future contract boundary，不实现业务逻辑。
- 不引入 DB / ORM / migration。
- 不引入 LLM / RAG。
- 不引入 Redis / PostgreSQL / MinIO。
- 不修改 apps/web/**。
- 不修改 tests/**，除非后续 packet 明确授权。
- 与 M02 downstream input 关系明确。
- 与 ST13_20 / ST13_24 的依赖关系明确：数据保存与测试体系分别由对应任务承接。

完成判定只表示文档输入具备 state sync / preview 的基础，不表示 formal window 已打开，也不表示 implementation-ready。

## 10. 停止条件

出现以下任一情况必须停止：

- 需要修改 `DOC_STATE.yaml` 或 `transition_history.jsonl`。
- 需要打开 formal window。
- 需要生成 implementation packet。
- 需要修改 `apps/web/**`、`tests/**`、`tools/**`、`.github/**`。
- 需要实现 Job / Resume / Knowledge / Interview / Score / Review / Export 业务 API。
- 需要接入 DB、ORM、migration、LLM、RAG、Redis、PostgreSQL、MinIO 或对象存储。
- 需要扩大 M02 / M03 业务实现范围。
- 依赖不可用但有人要求通过 vendor code 或临时大改绕过。

## 11. 回退策略

- 文档回退：只回退本双文档中本次 scope correction 内容。
- 状态回退：必须另开 State Update 或治理窗口；本文档不得直接修改 `DOC_STATE.yaml`。
- 代码回退：仅适用于未来已授权 implementation window；当前没有代码改动。
- 验证失败：停止后续 state sync / formal window 讨论，先输出失败命令、失败原因和受影响范围。

## 12. 当前未放行实现说明

`ST13_21_IMPLEMENTATION.md` 的存在不等于 active working doc。本文档不声明：

- `implementation_doc_state=active_working_doc`
- `maturity=L5`
- `readiness=downstream_ready`
- `implementation_approval_status=approved`
- `candidate_status=candidate`
- `implementation_ready=true`
- formal window open
- packet ready

上述状态只能由后续正式状态流程处理。

## 13. 下一步

下一步建议是 `ST13_21 state sync preview`，只验证本文档补齐后的 packet input / readiness 影响，不直接 apply，不打开 formal window，不生成 packet。

# ST13_21 IMPLEMENTATION：R0 最小 API / 后端服务边界

## 1. 文档状态

- 状态：`draft`
- 文档性质：ST13 任务实施说明；记录 ST13_21 R0 minimal API service boundary 的实际实施结果与后续验证口径，不是 implementation packet。
- official gate：formal window 已打开；implementation approval 已批准；当前 `implementation_ready=true`，`can_generate_implementation_packet=true`。
- packet 状态：implementation packet 已重新生成并提交，提交为 `89d82cf gov: generate ST13_21 implementation packet`。
- implementation 状态：R0 minimal API service boundary 已完成并通过 acceptance refresh；实现提交为 `b9d7fd3`，TestClient 依赖提交为 `1f65274`。
- 当前定位：为 post-implementation docs / module sync 记录实际实施边界。
- 本窗口不修改 `DOC_STATE.yaml`，不修改 packet，不继续 implementation，不扩大业务 API 范围。

## 2. 本轮实施目标

- 已在 ST01_01 最小 FastAPI runtime 上建立 API / 后端服务边界骨架，统一 `/api/v1` 路由注册、最小错误响应、配置读取和未来业务路由占位；未实现任何业务 API，未接 DB，未接 LLM/RAG，未接 Redis/PostgreSQL/MinIO。

## 3. 前置条件

进入 implementation 前已满足以下条件：

- `ST13_21_DESIGN.md` 已保持 R0 minimal API service boundary，不再以完整 API 合同作为本任务实施范围。
- M02 只作为 downstream identity boundary input；完整身份系统不由本任务实现。
- ST01_01 runtime baseline 已存在，且 health endpoint 不被本任务破坏。
- `DOC_STATE.yaml` 仍由专门状态窗口维护；本文档正文不替代 official state。
- 当前 official state 已满足 formal window open、`implementation_doc_state=active_working_doc`、implementation approval approved、`implementation_ready=true`。
- 已基于修正后的文档提交 packet，并已通过 packet acceptance review / commit-prep。
- implementation 已按提交后的 packet 执行并通过 acceptance refresh。

## 4. 范围内

已完成的 implementation 只覆盖：

- 基于现有 FastAPI runtime 的 API service skeleton。
- `/api/v1` prefix 和 router registration 最小模式。
- health endpoint regression，确保 `GET /api/v1/health` 继续可达。
- 最小 error response / error envelope。
- 最小配置读取边界。
- future routes placeholder / contract boundary；当前仅为未注册常量。
- M02 identity context 的消费边界说明。

本任务不实现任何业务 API。

## 5. 允许修改范围

packet allowed paths 限定如下，且不得自行扩大：

- `apps/api/**`
- `package.json`
- `requirements.txt`
- `.env.example`
- `docs/tasks/workbench-mvp/st13-task-packages/ST13_21/ST13_21_DESIGN.md`
- `docs/tasks/workbench-mvp/st13-task-packages/ST13_21/ST13_21_IMPLEMENTATION.md`

如果后续确实需要其它路径，只能作为另窗建议或确认卡，不得在本任务内直接扩大。

## 6. 禁止修改

packet forbidden paths 已包含且本次未触碰：

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

## 7. 已执行实施步骤

本次 implementation 已按以下顺序完成：

1. 复核 official `DOC_STATE.yaml`、`evaluate-state` 和 `preflight-open-window`。
2. 复核 ST01_01 runtime baseline 中 health endpoint 的当前入口。
3. 建立或整理 `/api/v1` router registration 的最小骨架。
4. 保持 health endpoint 可达，避免迁移回归。
5. 添加最小 error response / error envelope。
6. 添加最小配置读取边界，且不读取外部服务 secret。
7. 只保留 future route placeholders 为未注册常量，不实现业务逻辑。
8. 补充 `httpx` 依赖以支持 FastAPI `TestClient` smoke。
9. 运行 required validation；非 sandbox 环境 API smoke / TestClient smoke 已通过，sandbox 内 TestClient 超时记录为 runtime limitation。

## 8. 测试与验证

本任务 required validation 至少包含，且已在 implementation / acceptance refresh 中执行或记录：

- `python3 -m tools.doc_governor.cli validate-state --input docs/governance/DOC_STATE.yaml`
- `python3 -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml --entity-type subtask --entity-id ST13_21`
- `python3 -m tools.doc_governor.cli preflight-open-window --subtask ST13_21`
- `git diff --check`
- API import / route smoke，前提是依赖可用。
- health endpoint regression smoke，前提是依赖可用。
- 如果依赖不可用，记录 environment-blocked，不允许绕过边界新增 vendor code。
- Web lane smoke 只作为不破坏验证，不作为本任务实现授权。

当前已确认：

- `validate-state`、`evaluate-state ST13_21`、`preflight-open-window ST13_21` 通过。
- `git diff --check` 通过。
- 非 sandbox 环境 uvicorn + curl smoke 通过，`GET /api/v1/health` 返回 HTTP 200 + `{ "status": "ok" }`。
- missing route 返回 minimal error envelope。
- `httpx>=0.27,<1.0` 已加入 `requirements.txt`，用于 FastAPI `TestClient` smoke。
- 非 sandbox 环境 `TestClient` smoke 通过；sandbox 内 TestClient 可能超时，记录为 runtime limitation。
- 未新增或修改 `tests/**`。

## 9. 完成判定

`ST13_21` R0 minimal scope 的 acceptance criteria 与当前结果：

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

完成判定不扩大实现范围；后续 implementation 仍必须受 packet allowed / forbidden paths 限制。

## 10. 停止条件

出现以下任一情况必须停止：

- 需要修改 `DOC_STATE.yaml` 或 `transition_history.jsonl`。
- 需要修改 formal window 或 implementation approval 状态。
- 需要手工修改、覆盖或重新生成 implementation packet，除非处于专门 packet generation 窗口。
- 需要修改 `apps/web/**`、`tests/**`、`tools/**`、`.github/**`。
- 需要实现 Job / Resume / Knowledge / Interview / Score / Review / Export 业务 API。
- 需要接入 DB、ORM、migration、LLM、RAG、Redis、PostgreSQL、MinIO 或对象存储。
- 需要扩大 M02 / M03 业务实现范围。
- 依赖不可用但有人要求通过 vendor code 或临时大改绕过。

## 11. 回退策略

- 文档回退：只回退本双文档中本次 scope correction 内容。
- 状态回退：必须另开 State Update 或治理窗口；本文档不得直接修改 `DOC_STATE.yaml`。
- 代码回退：仅适用于已提交的 implementation commit；需另窗按允许路径处理。
- 验证失败：停止后续 state sync / formal window 讨论，先输出失败命令、失败原因和受影响范围。

## 12. 当前 gate 与实施验收说明

`ST13_21_IMPLEMENTATION.md` 已在 official state 中登记为 active working doc；当前 confirmed / derived gate 事实为：

- `implementation_doc_state=active_working_doc`
- `maturity=L5`
- `readiness=downstream_ready`
- `implementation_approval_status=approved`
- `implementation_ready=true`
- formal window open
- `can_generate_implementation_packet=true`

上述状态仍是 official state / gate 事实，不等于 accepted / done state 已写回。implementation 层事实为：

- packet 已生成并提交：`89d82cf gov: generate ST13_21 implementation packet`。
- implementation 已提交：`b9d7fd3 feat(ST13_21): add minimal API service boundary`。
- TestClient 依赖已提交：`1f65274 test(ST13_21): add httpx for FastAPI TestClient smoke`。
- acceptance refresh 结论：accepted。
- 本窗口不写 official state，不修改 packet，不继续 implementation。

## 13. R1 API 契约冻结执行说明

`R1-W02-ST13_21-API-CONTRACT-FREEZE` 只执行 docs-only contract freeze。本文档记录后续执行边界，不代表本窗口进入 implementation，不生成 packet，不打开 formal window，不修改 official state。

### 13.1 本窗口新增的实施输入

后续 `ST13_20` R1 data / schema / migration readiness 可以从 `ST13_21_DESIGN.md` 第 13 节消费以下输入：

- R1 API domain boundary：Identity / Auth context、Job / Resume、Knowledge / RAG、Interview、Score、Review、Export、History。
- action list：以 create / read / update / archive / restore / generate / retry / list / detail 等 action 语义为边界，不在本窗口创建 endpoint。
- request contract：actor context、resource identity、snapshot / version、operation intent、RAG query context、LLM / generation context。
- response contract：resource response、permission-aware response、async response、evidence response、review / score response、export response。
- error envelope：`error.code`、`error.message`、`error.reason`、`error.request_id`、`error.resource_ref`、`error.retryable`、`error.degraded`、`error.details`。
- permission context：user / role / workspace / tenant 候选、resource visibility、permission denied 与 resource not visible 的区分。
- async / degradation semantics：RAG indexing、RAG no result、LLM failed、parsing low confidence、score / review pending、export failed、restore failed。
- traceability fields：request / operation、actor / workspace scope、resource refs、source snapshot refs、status fields、evidence refs、error refs、export refs。
- RAG evidence / citation、score / review / export / history 的共享 API 语义。

### 13.2 ST13_20 下游消费边界

`ST13_20` 可以把本窗口冻结内容作为 data / schema / migration readiness 的上游输入，但必须遵守：

- 只有已在 `ST13_21_DESIGN.md` 第 13 节稳定表达的 API 语义，才能进入 `ST13_20` 的字段、状态、错误、traceability 讨论。
- `ST13_21` 中标注为 contract 占位的字段，不得被 `ST13_20` 直接写成数据库字段或 migration。
- 完整 prompt 原文、完整 LLM response 原文、embedding 向量、provider secret、对象存储真实路径、完整权限矩阵、企业级 tenant 配置、PDF 模板配置和训练任务调度参数不得在 `ST13_20` 中直接落库。
- 如果 `ST13_20` 发现 API contract 与 data contract 字段漂移，应回到文档评审窗口，不得通过实现补丁临时修正。

### 13.3 本窗口仍禁止的内容

本窗口明确未执行且仍禁止：

- 不写业务 API。
- 不创建 endpoint、OpenAPI 文件、schema、migration、ORM、repository、worker、queue、provider adapter 或测试文件。
- 不修改 `apps/**`、`tests/**`、`docs/governance/**`、`DOC_STATE.yaml`。
- 不生成 implementation packet。
- 不打开 formal window。
- 不新增依赖、环境变量或长期状态入口。
- 不把 R1 contract freeze 写成 accepted / done / implementation-ready 状态。

### 13.4 后续验证口径

本窗口的完成判定只面向文档与治理：

- `ST13_21_DESIGN.md` 已明确 R1 API contract freeze 范围。
- R1 API contract 已从 R0 minimal service boundary 扩展为可供 `ST13_20` 消费的 domain、request、response、error、permission、async、degradation、traceability 和 evidence contract。
- R0 / R1 / R2 scope split 已明确。
- 禁止实现范围已明确。
- 代码、测试、governance state、packet 和 formal window 未修改。

### 13.5 前端消费边界补丁

`R1-W02a-ST13_21-FRONTEND-UI-CONSUMER-CONTRACT-PATCH` 在 `ST13_21_DESIGN.md` 第 14 节补齐前端消费边界。该补丁只说明前端如何消费 R1 API contract，不实现页面、组件、测试或 endpoint。

后续前端或测试窗口可以消费以下 contract 信息：

- R1 用户可见 surface：工作台概览、模拟记录列表、发起模拟入口、面试台、评分 / 复盘详情、知识库入口、Markdown 导出入口、账号 / 权限提示。
- 前端直接消费 action：current user / permission context、job / resume list and detail、knowledge / RAG status and search context、interview start / restore / submit / finish / detail / history、score / review read or generate status、export create / status / retry。
- 前端展示字段：资源摘要、评分与复盘、RAG citation / evidence / evidence gap、异步状态、权限和可见性安全摘要。
- 后端追踪字段：`request_id`、`operation_id`、audit event id、source snapshot refs、provider alias、model alias 等默认不直接展示。
- 错误和状态：permission denied、resource not visible、archived resource、validation failed、RAG unavailable、LLM failed、pending / running、retryable、empty history / empty knowledge。
- R1 / R2 UI 边界：R1 只要求主链路、证据、评分复盘、导出、历史回看、权限 / 降级 / 空状态可感知；训练抽屉完整闭环、资产归档、复杂组织后台和团队共享知识库治理延后。

本补丁仍禁止修改 `apps/**`、`tests/**`、`docs/governance/**`、`DOC_STATE.yaml`，禁止新增依赖、schema、migration、packet 或 formal window。

## 14. 下一步

下一步建议开启 `R1-W03-ST13_20-DATA-SCHEMA-MIGRATION-READINESS`。该窗口应只消费本次 `ST13_21` R1 API contract freeze 结果，先做 data / schema / migration readiness，不直接创建 schema、migration、ORM、业务代码或测试。

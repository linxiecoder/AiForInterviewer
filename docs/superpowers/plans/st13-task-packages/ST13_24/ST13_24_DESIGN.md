# ST13_24 DESIGN：测试 / 验收 / DoD

## 1. 文档状态

- 状态：`draft`
- 实施状态：`not implementation-ready`
- formal window：`formal window closed`
- implementation packet：`implementation packet forbidden`
- contract 状态：`contract_refined`
- 本文件是 W13-E8 创建的正式双文档实体之一；W13-E8.5 已将本文件登记到 `DOC_STATE.yaml` 既有 `facts.design_doc` slot，`exists=true`，`template_like=false`。
- 当前仍未形成 implementation-ready；formal window 仍关闭；implementation packet 仍禁止生成。

## 2. 关联 ST13 / WT13

- ST13：`ST13_24`
- WT13 alias：`WT13-24`
- 任务名称：测试 / 验收 / DoD
- 当前来源状态：`task_packet_draft_created` -> `double_doc_registered` -> `contract_refined`

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

25 个 ST13 当前仍缺 formal window、required tests、acceptance criteria、implementation doc activation 和 implementation scope。W13-E8.5 已登记第一批四个 ST13 的 required doc slot，但这只解除文档路径登记缺口，不放行 implementation-ready。第一批任务中，`ST13_24` 负责把一期工作台 MVP 的产品、数据、UI、工程、收口五层 DoD 转化为后续 formal window 前的测试 / 验收 contract。

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

确保后续实现窗口不只拥有功能描述，还拥有可执行或可检查的验收标准、required tests、失败停止条件、回退说明和真实浏览器验证要求。本任务只定义 contract，不创建 `tests/**`。

### 11.2 产品 DoD contract

- 一期主链覆盖登录、工作台、岗位、简历、知识库、记录列表、发起、面试台、复盘、评分、导出。
- 模拟面试默认从历史记录列表进入，完成后回写历史记录 / 复盘。
- 真实 LLM、服务端保存、RAG / 知识库、多轮高阶面试、0-100 多维评分、历史 / 复盘和复制 / Markdown 下载都必须可验收。
- W10 `apps/web/**` 原型只能作为参考证据，不能作为产品 DoD 的正式完成标准。
- 产品 DoD 必须区分“可手工验收的端到端路径”和“必须自动化的回归路径”。

### 11.3 数据 DoD contract

- 服务端保存、权限过滤、RAG evidence、LLM 脱敏记录、评分证据、导出快照均可追溯。
- `ST13_20` 中定义的核心对象必须能被保存、读取、归档、恢复候选或明确不保存。
- 数据 DoD 必须覆盖版本 / schema version、删除 / 归档、审计日志和导出快照一致性。
- 数据测试不得创建数据库或 migration；具体自动化只能在 formal window 后执行。

### 11.4 UI DoD contract

- 页面流符合 IA，错误态 / 空状态完整，记录列表、发起、面试台和复盘详情可串联。
- 浏览器真实验证必须覆盖桌面和移动视口，检查无横向溢出、关键控件可见、文本不重叠。
- UI DoD 不允许把“页面存在”当作“主链完成”。

### 11.5 工程 DoD contract

- 默认测试入口为 `python -m tools.test_runner.run_tests`。
- 不在仓库根目录或 `tests/` 下遗留 `tmp/temp`。
- validate-state / evaluate-state 不退化。
- 后续若引入前后端测试命令，必须在实施窗口补充窄范围命令和失败停止条件。

### 11.6 收口 DoD contract

- 修改清单、验证结果、未完成项、风险、下一步窗口边界明确。
- Basic Memory / Superpowers 写回只能在后续授权窗口执行。
- 收口不得把 contract_refined 写成 implementation-ready，不得把 formal window 写成已打开。

### 11.7 API contract 测试要求

- 覆盖 `ST13_21` 中的 Auth、Account / Role / Permission、Job、Resume、Knowledge、Retrieval、Interview、Generation、Feedback / Score、SessionRecord、Markdown Export、Admin / Ops。
- 必测类型：request / response 字段最小一致性、schema validation、权限矩阵、错误 taxonomy、幂等、状态冲突、异步任务状态。
- API 测试必须区分未登录、权限不足、资源不可见、已归档、LLM 失败、RAG 无命中和导出失败。

### 11.8 数据库测试要求

- 覆盖 `ST13_20` 数据对象：账号权限、岗位、简历、知识库、检索、面试、回答、反馈评分、弱项训练、资产、导出、LLM 生成和审计。
- 必测类型：schema relation、migration up/down dry-run、权限过滤、数据一致性、导出快照一致性、evidence 引用完整性。
- 本窗口不创建数据库测试；后续 formal window 才能选择工具和执行方式。

### 11.9 RAG 测试要求

- 私有 / 公共知识库权限、混合检索、无命中降级、引用回溯、证据进入评分但不直接决定分数。
- 检索失败、索引未完成、权限过滤后为空必须有独立错误态和可继续 / 可重试策略。

### 11.10 LLM provider 测试要求

- provider 失败、重试、脱敏日志、模型名 / 模板版本记录、成本字段候选。
- LLM 日志必须脱敏，测试 fixture 不得含真实 provider key、真实简历或私有知识库内容。
- 失败时不得把 fallback 内容误标为真实 LLM 成功。

### 11.11 多轮面试测试要求

- 暂停 / 继续、上下文保存、轮次 / turn 状态、模式切换边界。
- 打磨模式与压力面模式必须分开验收，不得用单一固定轮次覆盖全部多轮场景。
- 多轮上下文中的 RAG evidence、回答、追问、评分和复盘必须可追溯。

### 11.12 打磨模式测试要求

- `ProgressTree` 驱动，用户决定继续或结束，不固定轮次。
- 必须验收每题反馈、能力树 / 当前进展 / 薄弱点更新、下一题建议和用户结束决策。
- 若评分或复盘尚未生成，必须出现明确状态，不得显示为完成。

### 11.13 压力面模式测试要求

- `InterviewQuestionSet` 驱动，题目完成后结束；固定 3 轮只能作为题组策略候选。
- 必须验收题组生成、作答进度、最终评估、岗位匹配判断、通过概率、多维评分和建议打磨主题。
- 题组生成失败、部分回答缺失和复盘失败必须有错误态。

### 11.14 评分 / 复盘测试要求

- 0-100 多维评分、证据绑定、真实复盘、模拟复盘、弱项 / 训练建议。
- 评分失败不得丢失回答和历史记录；复盘失败不得伪装成已完成。
- RAG 证据不足时，复盘必须标注证据缺口。

### 11.15 Markdown 导出测试要求

- 复制 / Markdown 下载、导出完整复盘 + RAG 引用 + 训练建议，不做完整 PDF。
- 若后续要增加 PDF，必须另走确认卡。
- 导出必须验证权限过滤、脱敏、文件名候选、空内容、导出失败和重复导出。

### 11.16 错误态 / 空状态测试要求

- 未登录、权限不足、空记录、空知识库、RAG 无命中、LLM 失败、导出失败、复盘未生成。
- 错误态必须包含用户可恢复动作或明确阻断原因。
- 空状态不得用 mock 成功数据替代。

### 11.17 权限 / 登录 contract 测试要求

- 覆盖 session 过期、未登录访问、普通用户访问管理员资源、管理员筛选公共知识库、用户访问他人记录。
- 权限测试必须验证 API、数据、UI 和导出四层一致。
- 资源不可见错误不得泄露敏感摘要或原文。

### 11.18 安全 / 隐私 contract 测试要求

- 覆盖简历原文、真实面试材料、私有知识库、LLM prompt / response、RAG evidence、Markdown export 的脱敏与可见范围。
- 测试 fixture 必须使用脱敏样例，不得包含真实 provider key。
- Basic Memory / 收口报告不得写入敏感样例。

### 11.19 validate-state / evaluate-state 治理验证

- `validate-state` / `evaluate-state` 是治理验证，不替代业务测试。
- 若状态验证失败，后续写入和细化必须停止并输出失败原因。

### 11.20 临时产物规则

- 默认遵守 `docs/governance/TEST_POLICY.md`。
- 禁止在仓库根目录或 `tests/` 下遗留 `tmp-*`、`tmp_*`、`temp-*`、`temp_*` 等目录。
- 后续测试实现若需要临时产物，必须使用测试策略允许的位置并在收口检查清理。

### 11.21 浏览器真实验证要求

- 后续 UI 实现窗口必须使用真实浏览器验证主链，而不仅依赖静态检查。
- 至少覆盖桌面和移动视口、关键路径、错误态 / 空状态、导出入口、面试台交互和复盘详情。
- 本窗口不启动 dev server，不创建页面，不执行 Playwright 或浏览器测试。

### 11.22 失败回退要求

- 验证失败时停止扩展，不继续实施下一类能力。
- 回退报告必须说明失败命令、失败原因、受影响文件、是否需要状态回退、是否需要用户确认。
- 状态回退必须另开 State Update 或治理窗口，本文档不直接修改 `DOC_STATE.yaml`。

### 11.23 必须自动化的测试

- API request / response contract、权限矩阵、数据一致性、RAG evidence 引用、LLM 失败语义、评分 / 复盘关键路径、Markdown 导出权限过滤、临时产物治理。
- `validate-state` / `evaluate-state` 和禁止范围检查必须在相关治理窗口自动执行或命令化执行。

### 11.24 可先手工验收的测试

- 产品主链体验、复杂 UI 响应式细节、文案可读性、复盘报告可解释性、训练建议质量、管理员公共知识库运营边界。
- 手工验收必须记录检查项、结果和截图 / 证据要求；不能只写“已看过”。

### 11.25 测试分层建议

| 层级 | 目标 | 后续执行方式 |
| --- | --- | --- |
| P0 contract | API、数据、权限、状态、治理不退化 | 必须自动化或命令化 |
| P1 主链 | 登录到复盘导出的端到端路径 | 自动化优先，必要时手工补证据 |
| P2 错误态 | LLM / RAG / 导出 / 权限失败 | 自动化与手工结合 |
| P3 体验 | 响应式、文案、可解释性 | 手工验收为主，后续沉淀自动化 |

### 11.26 与 ST13_25 的关系

- `ST13_24` 定义测试 / 验收 / DoD contract，`ST13_25` 定义文档治理、收口、写回和过时检查 contract。
- 后续 readiness 复核必须同时检查测试矩阵和治理收口矩阵。

## 12. 数据 / API / UI / 状态边界

- 数据边界：引用 `ST13_20` schema contract，不创建数据库测试。
- API 边界：引用 `ST13_21` API contract，不创建 API 测试代码。
- UI 边界：定义验收维度，不创建页面。
- 状态边界：本窗口不修改 `DOC_STATE.yaml`；W13-E8.5 已登记 required doc slot，但 formal window、implementation doc activation、acceptance criteria、required tests 和 implementation scope 仍未闭合。

## 13. 权限 / 安全 / 隐私边界

- 测试矩阵必须覆盖用户数据隔离、管理员公共知识库、私有上传、导出权限、LLM 日志脱敏。
- 测试 fixture 不得包含真实简历、真实 provider key 或私有知识库内容。

## 14. 错误态 / 空状态

- 每个后续 ST13 必须列出空态、失败态、权限态和恢复路径。
- 错误态验收不得只依赖 happy path。

## 15. 验收标准

- 五层 DoD 均有定义。
- API、数据库、RAG、LLM provider、多轮、打磨、压力面、评分 / 复盘、Markdown 导出、错误态 / 空状态均有测试要求。
- 权限 / 登录、安全 / 隐私、临时产物、浏览器真实验证、失败回退、自动化 / 手工分层均有 contract。
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
- `OQ-113=B`：required doc slot 由 W13-E8.5 单独 State Update 完成；本窗口不修改 `DOC_STATE.yaml`。

## 20. 下游任务

- 所有 ST13 formal window。
- W13-E9 contract 细化。
- W13-E10 readiness 复核。
- W13-E11 formal window 候选评估。

## 21. 当前不进入实现说明

本文件经 W13-E9 contract 细化后，`ST13_24` 仍是 `not implementation-ready`。当前不创建 `tests/**`，不写测试代码，不生成 implementation packet，不打开 formal window。

## 22. W13-E13.5 candidate 表达策略同步

W13-E13.5 后，`ST13_24` 继续保留文档层 `formal_window_candidate_recommended`，但正式 `DOC_STATE.yaml` 暂不写 `candidate_status=candidate`，也不直接写 `readiness=downstream_ready`。

下一轮 Candidate Preview 优先验证 facts-only 表达，例如 `facts.formal_window_candidate_recommended=true` 或等价现有 facts 字段；备选验证 `candidate_status=observe`。`formal_window_open` 必须保持 `false`，implementation-ready 必须保持 `false`，implementation packet 仍 forbidden。

## 23. W13-E13.8 facts-only 正式 State Update 同步

W13-E13.8 已在 docs/governance 直下创建 `DOC_STATE_W13_E13_8_CANDIDATE_FACTS_PREVIEW.yaml` 并通过严格验证；随后正式 `DOC_STATE.yaml` 已为 `ST13_24.facts` 写入 facts-only candidate 推荐字段：

- `formal_window_candidate_recommended=true`
- `formal_window_candidate_source=W13-E11 candidate evaluation`
- `formal_window_candidate_review_status=pending_confirmation`
- `formal_window_candidate_state=document_layer_recommended`
- `formal_window_candidate_notes=formal window closed; implementation-ready false; implementation packet forbidden`

该写入只表示测试 / 验收 / DoD contract 的 candidate 推荐事实进入正式状态层；不等于 `candidate_status=candidate`，不等于 `readiness=downstream_ready`，不打开 formal window，不生成 implementation packet，不创建 `tests/**`，不进入实现。

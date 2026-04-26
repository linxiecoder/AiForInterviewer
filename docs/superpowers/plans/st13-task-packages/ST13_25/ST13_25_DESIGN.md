# ST13_25 DESIGN：文档治理 / 收口 / Basic Memory

## 1. 文档状态

- 状态：`draft`
- 实施状态：`not implementation-ready`
- formal window：`formal window closed`
- implementation packet：`implementation packet forbidden`
- contract 状态：`contract_refined`
- 本文件是 W13-E8 创建的正式双文档实体之一；W13-E8.5 已将本文件登记到 `DOC_STATE.yaml` 既有 `facts.design_doc` slot，`exists=true`，`template_like=false`。
- 当前仍未形成 implementation-ready；formal window 仍关闭；implementation packet 仍禁止生成。

## 2. 关联 ST13 / WT13

- ST13：`ST13_25`
- WT13 alias：`WT13-25`
- 任务名称：文档治理 / 收口 / Basic Memory
- 当前来源状态：`task_packet_draft_created` -> `double_doc_registered` -> `contract_refined`

## 3. 关联模块

- 主体范围：global、M01、M10
- 横向关联：全部 W13 文档治理入口
- 本任务只定义治理和收口 contract，不写 Basic Memory。

## 4. 关联 W13 事实源

- `AGENTS.md`
- `docs/DOC_GOVERNANCE.md`
- `docs/governance/DOC_AUTOMATION.md`
- `docs/governance/TEST_POLICY.md`
- W13 四份事实源
- W13-E5 readiness audit
- W13-E6 task packages
- W13-E7 double doc plan
- 本轮 `ST13_21 / ST13_20 / ST13_24` 双文档

## 5. 背景

W13 已把当前一期 MVP 重定义为工作台级范围，并把正式状态层入口收敛为 `ST13_01~ST13_25`。第一批 ST13 文档创建和 W13-E8.5 required doc slot State Update 后，必须清楚区分任务包草案、正式双文档、required doc slot 已登记、contract refined、formal window、implementation packet、实现窗口和 Basic Memory 写回，避免把文档创建或 contract 细化误读为实现放行。

## 6. 目标

- 建立文档治理 / 收口 / Basic Memory 的正式设计文档。
- 明确唯一事实源维护、OQ / DD / backlog-roadmap、State Write 历史、archive 历史治理和收口报告结构。
- 明确本窗口不执行 Basic Memory 写回。

## 7. 非目标

- 不写 Basic Memory。
- 不修改 `DOC_STATE.yaml`。
- 不打开 formal window。
- 不生成 implementation packet。
- 不创建代码、测试、应用或基础设施目录。

## 8. 输入

- 当前用户确认 `OQ-111=A`、`OQ-112=A`、`OQ-113=B`。
- W13 四份事实源和 W13-E5 / E6 / E7 文档。
- `ST13_21`、`ST13_20`、`ST13_24` 双文档。
- W13-E8.5 required doc slot State Update 结果：四个目标 ST13 的 `facts.design_doc` / `facts.implementation_doc` 已登记，`exists=true`，`template_like=false`。
- 父索引同步要求和完成标准。

## 9. 输出

- formal window 前置条件清单。
- implementation packet 禁止与放行条件清单。
- 任务包草案到正式双文档的迁移策略。
- 父索引、OQ、DD、backlog-roadmap、执行日志、成熟度和进展同步规则。
- 后续 State Update、Basic Memory / Superpowers 写回和收口报告要求。

## 10. 依赖

- 前置依赖：`OQ-111=A / OQ-112=A / OQ-113=B`。
- 并行依赖：`ST13_21`、`ST13_20`、`ST13_24` 双文档。
- 下游依赖：W13-E9 contract 细化、State Update、W13-E10 readiness 复核、W13-E11 formal window 候选评估。

## 11. contract 范围

### 11.1 文档治理目标

确保本轮 contract 细化不越权进入 state 写回、implementation packet、formal window、Basic Memory 写回或代码实现。

### 11.2 唯一事实源维护

- W13 四份事实源继续作为产品和对象边界真值。
- `DOC_STATE.yaml` 仍是正式结构化状态真值。
- W13-E8.5 已将本轮四个双文档登记到 `DOC_STATE.yaml` 既有 required doc slot；本窗口不再把 required doc slot 视为待写入事项。
- 双文档与 contract_refined 只能作为 readiness 复核输入，不能反推 implementation-ready。

### 11.3 OQ / DD / backlog-roadmap 维护

- `OQ-111~OQ-113` 已写回 confirmed，且 `OQ-113=B` 已由 W13-E8.5 执行。
- `DESIGN_DECISIONS.md` 只记录 confirmed 高层事实；contract_refined 不等于实现完成，不应新增为“实现已完成”决策。
- backlog-roadmap 应把 W13-E9 contract 细化从 `open` 更新为 `done`，并保留 implementation-ready 阻断。

### 11.4 State Write 历史记录

- 保留 W13-E4-B / E4-C / E4-F / E8.5 状态层历史。
- 本轮不修改 `DOC_STATE.yaml`；不减少 formal window、implementation doc activation、acceptance criteria、required tests 或 implementation scope blocker。

### 11.5 Archive 历史文档治理

- archive 只能作为历史追溯。
- 本轮不迁移 archive，不删除旧文档。

### 11.6 Basic Memory 写回策略

- 本窗口禁止写 Basic Memory，禁止调用 Basic Memory 工具。
- 后续写回窗口必须先检索、后写入、再回读验证，且必须使用白名单目录。
- Basic Memory 不能反推 `DOC_STATE.yaml` 结构化真值，不能替代 `validate-state` / `evaluate-state`。

### 11.7 Superpowers 计划更新策略

- 后续 Superpowers 计划更新必须引用当前事实源、本轮双文档路径和 W13-E9 contract_refined 结论。
- 不得用旧 W10 原型替代 W13 工作台 MVP。
- 若后续写回 Superpowers 计划，应明确“仍不能实现、不能生成 packet、不能打开 formal window”。

### 11.8 fallback 包要求

若后续 Basic Memory 或写回失败，必须输出可复制 fallback 包，包含主题、confirmed 事实、未确认事项、风险、下一步、验证结果和禁止误读说明。

### 11.9 用户确认项闭环

本轮不新增 OQ 确认卡。扩大 ST13 范围、修改路径、创建 OpenAPI / schema / 测试文件、创建应用目录、写 state、写 Basic Memory、生成 packet、打开 formal window 或实现，均需确认卡。

### 11.10 收口报告结构

收口必须包含基线验证、阶段 0 过时表述清理、修改文件、双文档清单、contract 摘要、索引同步、禁止范围、validate/evaluate、是否新增 blocker、是否可进入 W13-E10 readiness 复核。

### 11.11 文档过时检查

父索引必须从 W13-E8.5 的 `double_doc_registered` 更新为 W13-E9 的 `contract_refined`，同时保持 `not implementation-ready`、`formal window closed` 和 `implementation packet forbidden`。

### 11.12 引用和孤立文档检查

四个双文档路径必须继续出现在 `AGENTS.md`、`TASK_INDEX.md`、`MODULE_INDEX.md`、W13-E6 / W13-E7 / W13-E8.5 文档和 backlog-roadmap。
- 过时表述检查必须确认不再出现 required doc slot 待登记、双文档待登记或 OQ-113 未执行等当前事实冲突表述。

### 11.13 与 ST13_24 DoD 的关系

`ST13_25` 定义治理收口规则，`ST13_24` 定义测试 / 验收 / DoD。两者必须互相引用，但都不创建测试代码、实现目录或外部写回。

### 11.14 当前不执行写回

本窗口不写 Basic Memory，不写 `DOC_STATE.yaml`，不执行 Superpowers 远端或外部写回。

### 11.15 阶段收口 DoD

- 8 个双文档 required doc slot 过时表述已清理。
- `ST13_21` API contract、`ST13_20` 数据 contract、`ST13_24` 测试 contract、`ST13_25` 治理 contract 已细化。
- `TASK_INDEX.md` 与 `MODULE_INDEX.md` 同步 `contract_refined`，但仍标记不可实施。
- `validate-state` / `evaluate-state` 保持 `ok=true,error=0,warning=0`。
- 禁止范围检查确认未修改 `DOC_STATE.yaml`、`apps/**`、`infra/**`、`tools/**`、`tests/**`、`archive/**`、`docs/modules/**`。

### 11.16 与 ST13_24 测试 / DoD 的关系

- `ST13_24` 给出测试和验收 contract，`ST13_25` 负责确保这些 contract 在收口、索引、执行日志和后续写回中不丢失。
- 后续 W13-E10 readiness 复核必须同时检查 ST13_24 的测试矩阵和 ST13_25 的治理收口矩阵。

### 11.17 未来写回窗口要求

- Basic Memory / Superpowers 写回必须另窗授权。
- 写回前必须检索；写回后必须回读验证；失败时输出 fallback 包。
- 写回内容不得包含真实简历、provider key、私有知识库内容或未确认实现事实。

## 12. 数据 / API / UI / 状态边界

- 数据边界：无数据实现。
- API 边界：只引用 `ST13_21`。
- UI 边界：只记录 `ST13_23` 后续并行准备口径。
- 状态边界：本窗口不修改 `DOC_STATE.yaml`；W13-E8.5 已登记 required doc slot，但 formal window、implementation doc activation、acceptance criteria、required tests 和 implementation scope 仍未闭合。

## 13. 权限 / 安全 / 隐私边界

- 治理写回不得泄露真实简历、真实 provider key、私有知识库内容。
- 归档和导出引用必须遵守权限可见范围。
- Basic Memory 写回如后续发生，只写项目级结论，不写敏感样例。

## 14. 错误态 / 空状态

- Basic Memory 写入失败：输出 fallback 包。
- validate/evaluate 失败：停止后续写入并报告原因。
- 父索引缺引用：视为收口缺口。
- contract_refined 被误写成 implementation-ready：必须回退措辞并重新扫描。

## 15. 验收标准

- 明确唯一事实源维护。
- 明确 OQ / DD / backlog-roadmap / State Write / archive / Basic Memory / Superpowers 的边界。
- 明确当前不执行 Basic Memory 写回。
- 明确与 `ST13_24` DoD 的关系。
- 明确 fallback 包、写回前检索、写回后回读验证、过时检查、孤立文档检查和阶段收口 DoD。
- 明确不修改 `DOC_STATE.yaml`、不生成 packet、不打开 formal window、不实现。

## 16. 测试要求

本任务治理验证包括：

- `validate-state`。
- `evaluate-state`。
- 关键词扫描。
- UTF-8 回读和 mojibake 检查。
- 禁止范围检查。

本窗口不执行 open-window，不生成 implementation packet。

## 17. 允许修改范围

本窗口允许：

- `docs/superpowers/plans/st13-task-packages/ST13_25/ST13_25_DESIGN.md`
- `docs/superpowers/plans/st13-task-packages/ST13_25/ST13_25_IMPLEMENTATION.md`
- 用户授权的父索引与 W13 计划文档同步。

## 18. 禁止修改范围

- `docs/governance/**`
- `docs/governance/DOC_STATE.yaml`
- `apps/**`
- `infra/**`
- `tools/**`
- `tests/**`
- `archive/**`
- `docs/modules/**`
- Basic Memory 写入
- implementation packet、formal window、实现代码

## 19. 用户确认项

- `OQ-111=A`：采用集中任务包目录。
- `OQ-112=A`：允许创建第一批正式双文档。
- `OQ-113=B`：required doc slot 由 W13-E8.5 单独 State Update 完成；本窗口不修改 `DOC_STATE.yaml`。

## 20. 下游任务

- W13-E9：第一批 ST13 contract 细化。
- W13-E10：readiness 复核。
- W13-E11：formal window 候选评估。
- 后续 Basic Memory / Superpowers 写回窗口。

## 21. 当前不进入实现说明

本文件经 W13-E9 contract 细化后，`ST13_25` 仍是 `not implementation-ready`。当前不写 Basic Memory，不调用 Basic Memory，不生成 implementation packet，不打开 formal window，不修改 `DOC_STATE.yaml`。

## 22. W13-E13.5 candidate 表达策略同步

W13-E13.5 后，`ST13_25` 继续保留文档层 `formal_window_candidate_recommended`，但正式 `DOC_STATE.yaml` 暂不写 `candidate_status=candidate`，也不直接写 `readiness=downstream_ready`。

下一轮 Candidate Preview 优先验证 facts-only 表达，例如 `facts.formal_window_candidate_recommended=true` 或等价现有 facts 字段；备选验证 `candidate_status=observe`。`formal_window_open` 必须保持 `false`，implementation-ready 必须保持 `false`，implementation packet 仍 forbidden；当前仍不写 Basic Memory。

## 23. W13-E13.8 facts-only 正式 State Update 同步

W13-E13.8 已在 docs/governance 直下创建 `DOC_STATE_W13_E13_8_CANDIDATE_FACTS_PREVIEW.yaml` 并通过严格验证；随后正式 `DOC_STATE.yaml` 已为 `ST13_25.facts` 写入 facts-only candidate 推荐字段：

- `formal_window_candidate_recommended=true`
- `formal_window_candidate_source=W13-E11 candidate evaluation`
- `formal_window_candidate_review_status=pending_confirmation`
- `formal_window_candidate_state=document_layer_recommended`
- `formal_window_candidate_notes=formal window closed; implementation-ready false; implementation packet forbidden`

该写入只表示文档治理 / 收口 / Basic Memory contract 的 candidate 推荐事实进入正式状态层；不等于 `candidate_status=candidate`，不等于 `readiness=downstream_ready`，不打开 formal window，不生成 implementation packet，不写 Basic Memory，不进入实现。

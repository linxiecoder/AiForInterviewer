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

## 4. 关联正式设计事实源

- `AGENTS.md`
- `docs/DOC_GOVERNANCE.md`
- `docs/governance/DOC_AUTOMATION.md`
- `docs/governance/TEST_POLICY.md`
- `docs/design/workbench-mvp/` 正式设计事实源
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
- `docs/design/workbench-mvp/` 正式设计事实源和 W13-E5 / E6 / E7 文档。
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

- `docs/design/workbench-mvp/` 正式设计事实源继续作为产品和对象边界真值。
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
- 禁止范围检查确认未修改 `DOC_STATE.yaml`、`apps/**`、`infra/**`、`tools/**`、`tests/**`、历史材料目录、`docs/modules/**`。

### 11.16 与 ST13_24 测试 / DoD 的关系

- `ST13_24` 给出测试和验收 contract，`ST13_25` 负责确保这些 contract 在收口、索引、执行日志和后续写回中不丢失。
- 后续 W13-E10 readiness 复核必须同时检查 ST13_24 的测试矩阵和 ST13_25 的治理收口矩阵。

### 11.17 未来写回窗口要求

- Basic Memory / Superpowers 写回必须另窗授权。
- 写回前必须检索；写回后必须回读验证；失败时输出 fallback 包。
- 写回内容不得包含真实简历、provider key、私有知识库内容或未确认实现事实。

### 11.18 W13-E14-B 收口标准补齐

后续任何 ST13_25 治理收口窗口的输出必须至少包含：

- 结论：说明本轮是完整收口、部分收口、失败收口还是回退收口。
- 修改范围：列出实际修改文件，并说明是否触及禁止范围。
- 验证结果：列出 `validate-state`、`evaluate-state`、关键词扫描、UTF-8 回读和禁止范围检查结果。
- 剩余风险：说明仍未关闭的 formal window、implementation packet、Basic Memory 授权、状态层字段或父索引同步风险。
- 下一步建议：明确交给总控窗口、State Update 窗口、Basic Memory 写回窗口或后续 formal window 的事项。

收口类型定义如下：

- 完整收口：授权文件已补齐，验证全绿，禁止范围未触碰，且没有新增需要本窗口处理的阻塞项。
- 部分收口：授权文件已部分补齐，但存在需 W13-E14-Merge 或后续窗口处理的父索引、状态层、Basic Memory 或 formal window 事项。
- 失败收口：基线验证、写后验证或禁止范围检查失败；必须停止后续写入并报告失败原因。
- 回退收口：已发生需撤销或替换的误写；必须列出回退对象、回退原因、验证结果和仍需人工确认的影响面。

### 11.19 Basic Memory 授权边界补齐

- 默认不写 Basic Memory，不把聊天内容、终端摘要或文档草稿直接当作已写记忆。
- 只有用户明确授权的收口窗口才允许写 Basic Memory；授权必须说明写入主题、目录建议和是否允许更新已有笔记。
- 写回前必须先检索，至少判断是否已有同主题笔记或近似会话总结，避免重复写入。
- 写回后必须回读验证，并在收口报告中说明验证方式；没有回读验证的内容不得称为已沉淀记忆。
- Basic Memory 不可用、检索失败、写入失败、命中歧义或回读失败时，必须输出 fallback 包。
- Basic Memory 只是长期上下文层，不是 `DOC_STATE.yaml`、`TASK_INDEX.md`、`MODULE_INDEX.md` 或 formal window 的结构化真值。

### 11.20 fallback 包标准补齐

fallback 包必须可复制到后续授权窗口继续执行，至少包含：

- 主题：例如 `ST13_25 文档治理 / 收口 / Basic Memory 前置补齐`。
- 目录建议：只能使用项目白名单目录，例如 `90-session-summaries`、`20-decisions` 或 `60-risks-constraints`，并说明选择理由。
- 摘要：用短段落说明本轮做了什么、未做什么。
- confirmed 结论：只记录已确认事实，不把 proposed-default、candidate 推荐或预览结果写成 confirmed。
- 遗留风险：列出 formal window、implementation packet、Basic Memory 授权、状态层同步和父索引同步风险。
- 验证结果：列出本轮执行的 validate/evaluate、关键词扫描、范围检查和回读结果。
- 下一步建议：说明后续由哪个窗口处理。
- 后续补写正文：提供可直接写入 Basic Memory 的中文正文草案，并标明需用户授权后才能写入。

### 11.21 Superpowers 更新规则补齐

- 只更新当前事实源或对应计划，不把 archive 历史文档改写为当前事实源。
- 只记录已确认的用户选择、已完成的文档治理动作和验证结果；不得把 proposed-default、near-ready、facts-only candidate 推荐写成 confirmed。
- 若 Superpowers 计划与 `DOC_STATE.yaml`、`TASK_INDEX.md`、`MODULE_INDEX.md` 或 backlog-roadmap 不一致，必须交由 W13-E14-Merge 或总控窗口统一判断，不在 ST13_25 局部窗口自行扩大范围。
- Superpowers 更新不得替代 `validate-state` / `evaluate-state`，也不得作为 formal window open、implementation-ready 或 implementation packet ready 的依据。

### 11.22 文档治理 DoD 补齐

ST13_25 的文档治理 DoD 至少包括：

- 唯一事实源维护：确认当前事实源、状态层真值和历史 archive 边界没有混淆。
- OQ / DD / backlog-roadmap 更新检查：识别是否需要总控窗口回写，不在本窗口越权修改。
- `DOC_STATE.yaml` / `TASK_INDEX.md` / `MODULE_INDEX.md` 同步检查：只做检查和交接，不在本窗口写入禁止文件。
- archive 与 current 引用检查：archive 只作为历史追溯，不作为当前事实源。
- 过时表述检查：重点检查 `implementation-ready`、`formal window open`、`candidate_status=candidate`、required doc slot 待登记等误导表述。
- 孤立文档检查：确认 ST13_25 双文档仍能被父索引和 W13 计划链路引用；缺口交给 W13-E14-Merge。
- 中文文档规则检查：新增说明默认中文，技术字段、命令、路径和 schema key 保持原样。

### 11.23 allowed paths / forbidden paths 补齐

当前 W13-E14-B 窗口只允许修改：

- `docs/superpowers/plans/st13-task-packages/ST13_25/ST13_25_DESIGN.md`
- `docs/superpowers/plans/st13-task-packages/ST13_25/ST13_25_IMPLEMENTATION.md`

未来若用户另窗授权 formal window 或治理收口窗口，才可按授权范围考虑以下文档治理文件：

- `PLAN_LATEST.md`
- `EXECUTION_LOG.md`
- `DOCUMENT_PROGRESS.md`
- `DOCUMENT_MATURITY.md`
- `TASK_INDEX.md`
- `MODULE_INDEX.md`
- `OPEN_QUESTIONS.md`
- `DESIGN_DECISIONS.md`
- `docs/superpowers/plans/2026-04-25-workbench-mvp-backlog-roadmap.md`
- 经用户明确授权的 Basic Memory 白名单目录写回。

当前窗口仍禁止：

- 写 Basic Memory 或调用 Basic Memory 写入流程。
- 修改 `docs/governance/**`，尤其是 `docs/governance/DOC_STATE.yaml`。
- 创建或修改 `apps/**`、`infra/**`、`tools/**`、`tests/**`、`docs/modules/**`、历史材料目录。
- 生成 implementation packet、打开 formal window、标记 implementation-ready、执行 Git 提交或推送。

### 11.24 formal window 前置条件补齐

`ST13_25` 只有在满足以下条件后，才可由后续窗口讨论是否打开 formal window：

- 用户另窗明确授权讨论或打开 `ST13_25` formal window。
- `validate-state` 与 `evaluate-state` 对正式 `DOC_STATE.yaml` 均为 `ok=true,error=0,warning=0`，且 `documents_blocked_count=0`。
- facts-only candidate 推荐已被正确理解为文档层推荐事实，不等于 `candidate_status=candidate`、formal window open 或 implementation-ready。
- 收口标准、Basic Memory 授权边界、fallback 包、allowed / forbidden paths、required tests、acceptance criteria 和 implementation scope 已在文档层明确。
- 若需要写 `DOC_STATE.yaml`，必须由独立 State Update / confirm-transition 授权窗口处理；本文件不得自行声明状态层已打开。

### 11.25 implementation packet 前置条件补齐

- 文档治理任务通常不应生成业务 implementation packet；ST13_25 的主要产物是治理收口规则、写回边界和交接材料。
- 当前窗口不生成 implementation packet，后续 formal window 未打开前也不得生成。
- 即使未来需要治理 packet，也必须由用户单独确认 packet 类型、目标、允许路径、禁止路径、required tests、acceptance criteria、回退策略和是否涉及 Basic Memory 写回。
- 任何 packet 生成都必须满足 `formal_window_open=true`、`implementation_doc_state=active_working_doc`、状态层 gate 全部通过，并由工具链拒绝 blocked task。

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

当前 W13-E14-B 窗口允许：

- `docs/superpowers/plans/st13-task-packages/ST13_25/ST13_25_DESIGN.md`
- `docs/superpowers/plans/st13-task-packages/ST13_25/ST13_25_IMPLEMENTATION.md`

父索引、W13 计划文档、状态层文件和 Basic Memory 均不在当前窗口写入范围内；如发现需要修改，只记录给 W13-E14-Merge。

## 18. 禁止修改范围

- `docs/governance/**`
- `docs/governance/DOC_STATE.yaml`
- `apps/**`
- `infra/**`
- `tools/**`
- `tests/**`
- 历史材料目录
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

W13-E13.8 已在 docs/governance/previews 路径创建 `DOC_STATE_W13_E13_8_CANDIDATE_FACTS_PREVIEW.yaml` 并通过严格验证；随后正式 `DOC_STATE.yaml` 已为 `ST13_25.facts` 写入 facts-only candidate 推荐字段：

- `formal_window_candidate_recommended=true`
- `formal_window_candidate_source=W13-E11 candidate evaluation`
- `formal_window_candidate_review_status=pending_confirmation`
- `formal_window_candidate_state=document_layer_recommended`
- `formal_window_candidate_notes=formal window closed; implementation-ready false; implementation packet forbidden`

该写入只表示文档治理 / 收口 / Basic Memory contract 的 candidate 推荐事实进入正式状态层；不等于 `candidate_status=candidate`，不等于 `readiness=downstream_ready`，不打开 formal window，不生成 implementation packet，不写 Basic Memory，不进入实现。

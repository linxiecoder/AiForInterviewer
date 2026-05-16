---
title: F4 Full Design Adversarial Review
type: review
status: active-f4
source_task: AIFI-ARCH-004
permalink: ai-for-interviewer/design/reviews/f4-full-design-adversarial-review
---

# F4 全量技术设计对抗性审计

## 1. 本轮重新审计说明

本文件是 `AIFI-ARCH-004` 的全量 F4 设计审计主报告。本轮重新基于当前 active design docs 取证，不复制旧 `AIFI-ARCH-003` finding。旧 `F4_PROMPT_SECURITY_TECH_*` 产物只作为前序审计证据，用于判断旧问题是否仍存在；本轮 finding 均使用 `AR-F4-FULL-*` 编号。

本轮只审计，不修复 `TECH_DESIGN.md`、`DATA_MODEL.md`、`SECURITY_PRIVACY.md`、`API_SPEC.md`、`PROMPT_SPEC.md` 或 `prompt-contracts/*.md`。

## 2. Executive Verdict

Status: Pending

结论：F4 不允许退出，F5 不允许启动。当前 F4 active docs 已覆盖主要业务域和 Prompt contract registry，但仍存在 4 个 High finding、2 个 Medium finding 和 1 个 Low finding。阻断集中在 `F4_TECH_DESIGN` UNKNOWN 未关闭、API 契约仍为骨架、评分 / 风险提示仍未冻结，以及 Report contract 重新引入 Markdown 下载 / 导出语义。

F7 具备部分测试输入，但不足以形成全链路可执行断言。当前可测试的是 owner / evidence / low confidence / no exact pass probability / candidate not formal 等局部负例；不可测试的是完整 API endpoint、request / response、错误码、异步任务、幂等、rate limit、评分公式、阈值、校准和 F4 UNKNOWN 关闭状态。

## 3. 审计范围

### 3.1 已读取的治理入口

- `AGENTS.md`
- `docs/00-governance/DOCS_INDEX.md`
- `docs/00-governance/AI_WORKFLOW.md`
- `docs/03-delivery/DELIVERY_PLAN.md`
- `docs/03-delivery/BACKLOG.md`

### 3.2 已读取的 F4 active design docs

- `docs/02-design/TECH_DESIGN.md`
- `docs/02-design/DATA_MODEL.md`
- `docs/02-design/SECURITY_PRIVACY.md`
- `docs/02-design/API_SPEC.md`
- `docs/02-design/PROMPT_SPEC.md`
- `docs/02-design/prompt-contracts/ASSET_CONTRACTS.md`
- `docs/02-design/prompt-contracts/JOB_MATCH_CONTRACTS.md`
- `docs/02-design/prompt-contracts/POLISH_CONTRACTS.md`
- `docs/02-design/prompt-contracts/PRESSURE_CONTRACTS.md`
- `docs/02-design/prompt-contracts/REPORT_CONTRACTS.md`
- `docs/02-design/prompt-contracts/REVIEW_CONTRACTS.md`
- `docs/02-design/prompt-contracts/SHARED_CONTRACTS.md`
- `docs/02-design/prompt-contracts/TRAINING_CONTRACTS.md`
- `docs/02-design/prompt-contracts/WEAKNESS_CONTRACTS.md`

`docs/02-design/prompt-contracts/` 下未发现额外 `.md` 文件。

### 3.3 只读辅助文档

- `docs/01-product/PRD.md`
- `docs/01-product/REQUIREMENT_TRACEABILITY.md`
- `docs/02-design/UX_SPEC.md`
- `docs/02-design/UI_DESIGN_SYSTEM.md`
- `docs/04-decisions/ADR-0001-document-governance.md`
- `docs/04-decisions/ADR-0002-unified-delivery-system.md`
- `docs/04-decisions/ADR-0004-ai-collaboration-governance.md`

### 3.4 前序审计证据

- `docs/02-design/reviews/F4_PROMPT_SECURITY_TECH_ADVERSARIAL_REVIEW.md`
- `docs/02-design/reviews/F4_PROMPT_SECURITY_TECH_RISK_REGISTER.md`
- `docs/02-design/reviews/F4_PROMPT_SECURITY_TECH_REMEDIATION_MATRIX.md`
- `docs/02-design/reviews/F4_PROMPT_SECURITY_TECH_ACCEPTANCE.md`

## 4. Prompt Registry 快速结论

主 `PROMPT_SPEC.md` 的 Contract Catalog 仍是 canonical registry；子文档只承载细则。本轮只读比对结果：

| Check | Result |
|---|---|
| Main catalog `P-*` ID 数量 | 48 |
| Child docs `P-*` ID 数量 | 48 |
| child-only `P-*` ID | 未发现 |
| main-only `P-*` ID | 未发现 |

Registry 本身不是本轮阻断项。

## 5. Role Matrix

| 角色 | 结论 | Finding |
|---|---|---|
| F4 Scope Gatekeeper | F4 退出标准未满足；`F4_TECH_DESIGN` UNKNOWN 仍显式保留；Report contract 重新引入 Markdown 下载 / 导出语义 | `AR-F4-FULL-001`、`AR-F4-FULL-004` |
| Architecture Boundary Reviewer | 顶层分层清晰，前端 / 后端 / LLM 边界明确；阻断来自子文档未闭合，不是模块边界自相矛盾 | 无新增阻断项 |
| API Contract Reviewer | `API_SPEC.md` 自称不定义完整 endpoint / schema / error / retry / rate limit，不能支撑 F5 | `AR-F4-FULL-002` |
| Data Model Reviewer | 数据对象覆盖面较全，项目经历未被错误升级为一级对象；但多项版本、状态、评分和 trace 决策仍 UNKNOWN | `AR-F4-FULL-001`、`AR-F4-FULL-003` |
| Security / Privacy Reviewer | ownership、LLM 隔离、日志脱敏和真实复盘隐私边界较完整；Report 下载语义与安全复制边界冲突 | `AR-F4-FULL-004` |
| Prompt / AI Contract Reviewer | registry ID 与子文档一致；多数业务 contract 已 Draft；部分子文档的下游 Stub 说明已过期；阻断来自评分 / 风险 / API handoff 未闭合 | `AR-F4-FULL-003`、`AR-F4-FULL-007` |
| Prompt Injection Red Team | Shared / Security / contract validation 已有注入防线；未发现当前 active docs 允许模型直接越权写正式对象 | 未发现新增阻断项 |
| RAG / Evidence Reviewer | owner/source/version/snapshot/trace 规则存在；F7 仍需 API 字段与 fixture 落地 | `AR-F4-FULL-002` |
| Scoring / Report Risk Reviewer | 评分公式、权重、阈值、校准、通过倾向展示和免责声明仍未冻结 | `AR-F4-FULL-003` |
| Candidate-to-Formal State Reviewer | candidate / suggestion / confirmation / formal object 边界总体一致 | 未发现新增阻断项 |
| Reliability / SRE Reviewer | async / retry / idempotency / rate limit / timeout 仍停留在占位，不能直接验收 | `AR-F4-FULL-002`、`AR-F4-FULL-005` |
| Testability / F7 Reviewer | 局部 fixture 思路充足，但 F7 无法验证完整 endpoint、状态机、UNKNOWN 关闭和 API failure path | `AR-F4-FULL-001`、`AR-F4-FULL-002`、`AR-F4-FULL-005` |

## 6. Dimension Matrix

| 维度 | 结论 |
|---|---|
| F4 范围覆盖 | Blocked: M4 退出标准要求关闭 `F4_TECH_DESIGN` UNKNOWN，当前未关闭 |
| PRD → UX/F3 → F4 输入一致性 | Partial: PRD/UX 非目标边界清晰，但 F3 交接状态与 DELIVERY 存在冲突 |
| TECH / API / DATA / SECURITY / PROMPT 横向一致性 | Partial: 顶层语义一致，API 完整性和 Report 导出语义冲突 |
| F5 后端实现可交接性 | Blocked: API endpoint/schema/error/retry/idempotency/rate limit 未冻结 |
| F6 前端实现可交接性 | Partial: UX 场景可用，但 F3 高保真交付状态冲突需复核 |
| F7 测试可验证性 | Blocked: 只能形成局部测试，无法覆盖完整 API / UNKNOWN closure |
| 权限与数据隔离 | 未发现阻断项；Security 文档已冻结 owner enforcement |
| LLM 输入最小化 | 未发现阻断项；TECH / PROMPT / SECURITY 均约束最小上下文 |
| Prompt injection | 未发现新增阻断项；需在 F7 fixture 落地 |
| RAG evidence 与 trace | Partial: 规则存在，API 字段和实现 fixture 未冻结 |
| 评分、通过倾向、风险提示 | Blocked: 公式、权重、阈值、校准、展示边界仍未冻结 |
| 报告复制边界 | Blocked: Report contract 使用 download / Markdown export 语义 |
| 真实面试复盘隐私 | 未发现新增阻断项；Review / Security 已有第三方信息与可信度边界 |
| 资产 / 薄弱项 / 训练建议写入边界 | 未发现新增阻断项；candidate-to-formal 边界总体一致 |
| 进展树、暂停恢复、状态机 | Partial: UX 可见，DATA / PROMPT 仍有保存字段和状态机 UNKNOWN |
| 异步任务、幂等、重试、失败状态 | Blocked: API 只占位，不可交接 |
| 版本策略、审计字段、追踪字段 | Partial: 引用模型完整，但多个版本策略仍 UNKNOWN |
| 非目标违背项 | Blocked: Report contract reintroduces Markdown download/export |
| UNKNOWN 关闭状态 | Blocked: 多文档明确不关闭 `F4_TECH_DESIGN` UNKNOWN |
| 文档治理一致性 | Partial: 新审计产物需登记；F3/F6 交接状态冲突需复核；部分 prompt-contract 子文档仍保留过期 Stub 说明 |

## 7. Findings

## AR-F4-FULL-001: F4_TECH_DESIGN UNKNOWN 仍显式保留，M4 退出标准未满足

Severity: High  
Category: Scope / Governance / Testability  
Source Documents:
- `docs/03-delivery/DELIVERY_PLAN.md` §1 F4 / M4 退出标准
- `docs/03-delivery/BACKLOG.md` §1 `AIFI-ARCH-002`
- `docs/02-design/TECH_DESIGN.md` §16 / §18
- `docs/02-design/DATA_MODEL.md` §12
- `docs/02-design/PROMPT_SPEC.md` §13
- `docs/02-design/API_SPEC.md` §12
Affected Downstream:
- F5 Backend / F6 Frontend / F7 QA / API_SPEC / DATA_MODEL / PROMPT_SPEC / SECURITY_PRIVACY / TECH_DESIGN
Affected IDs:
- `AIFI-ARCH-002` / `F4_TECH_DESIGN` / `OQ-F1-002`..`OQ-F1-040`
Status: Open

### Claim Under Review

F4 active design docs 已经足以让 M4 退出，并可进入 F5/F7。

### Contradiction / Gap

`DELIVERY_PLAN.md` 明确要求 F4 不得遗留评分、算法、数据结构、Prompt、模型选择、模型调用参数、接口、安全、版本策略、输入优先级、资产合并、复盘切分、薄弱项生命周期等 `F4_TECH_DESIGN` UNKNOWN。当前 `BACKLOG.md` 中 `AIFI-ARCH-002` 仍为 `NOT_STARTED`，多个 active design docs 也明确不关闭 UNKNOWN。

### Adversarial Scenario

F5 开发者按现有草案实现，遇到版本触发、评分校准、资产合并、进展树更新、暂停恢复、LLM 原始输出保存、rate limit 或幂等时自行补规则。不同实现窗口会产生不一致的接口、数据状态和测试断言。

### Failure Mode

F4 被误判为已完成，导致 F5/F7 把设计 UNKNOWN 转移到实现阶段；后续会出现不可测状态、临时实现规则、无法追溯的评分版本或无法验证的 failure path。

### Evidence

- `docs/03-delivery/DELIVERY_PLAN.md` §1 F4 / M4 退出标准要求不得遗留 `F4_TECH_DESIGN` UNKNOWN。
- `docs/03-delivery/BACKLOG.md` §1 `AIFI-ARCH-002` 仍为 `NOT_STARTED`。
- `docs/02-design/TECH_DESIGN.md` §18 写明“未关闭任何 `F4_TECH_DESIGN` UNKNOWN”。
- `docs/02-design/DATA_MODEL.md` §12 列出 `DM-UNK-001` 至 `DM-UNK-015`。
- `docs/02-design/PROMPT_SPEC.md` §13 列出评分公式、权重、阈值、模型选择、retry / fallback、RAG 实现等 UNKNOWN。
- `docs/02-design/API_SPEC.md` §12 列出完整 endpoint、error code、retry、idempotency、rate limit、timeout 和异步任务协议等 UNKNOWN。

### Required Fix

需要回写 `TECH_DESIGN.md`、`DATA_MODEL.md`、`API_SPEC.md`、`PROMPT_SPEC.md`、`SECURITY_PRIVACY.md`，并在 `BACKLOG.md` / `DELIVERY_PLAN.md` 中保持 `AIFI-ARCH-002` 与 M4 退出状态一致。

### Required Decision

需要人工确认哪些 `F4_TECH_DESIGN` 项必须在 F4 关闭，哪些可以按产品原因 Deferred，哪些必须转入 F7 测试断言。

### Acceptance Condition

`AIFI-ARCH-002` 完成前置复核；所有 F4 UNKNOWN 均已在 active design docs 中 Fixed、Deferred 或 Accepted_Risk；F7 能通过 grep / fixture / review gate 验证 UNKNOWN 关闭状态。

## AR-F4-FULL-002: API_SPEC 仍为骨架，不能支撑 F5/F6/F7 的接口交接

Severity: High  
Category: API / Reliability / Testability  
Source Documents:
- `docs/02-design/API_SPEC.md` §1 / §2 / §10 / §11 / §12
- `docs/02-design/TECH_DESIGN.md` §15 / §16 / §18
- `docs/03-delivery/DELIVERY_PLAN.md` §1 F4 / F5 / F7
Affected Downstream:
- F5 Backend / F6 Frontend / F7 QA / API_SPEC / PROMPT_SPEC / SECURITY_PRIVACY
Affected IDs:
- `AIFI-API-001` / `AIFI-ARCH-002` / UNKNOWN
Status: Open

### Claim Under Review

当前 API 契约足以让后端、前端和测试围绕候选态、正式态、AI task result、错误语义、鉴权、异步任务、幂等和 rate limit 开始实现。

### Contradiction / Gap

`API_SPEC.md` 当前明确“当前版本是骨架草案”，并声明不定义完整 endpoint、path、method、query 参数、pagination、完整 request / response、完整错误码、鉴权 API、队列、重试、rate limit 或 idempotency。它只给出语义边界，尚不能作为 F5/F6/F7 的接口合同。

### Adversarial Scenario

前端把 `api_state_mapping` 当作真实 response enum，后端按临时 JSON 直接返回 LLM 状态。重复点击生成报告或训练建议时缺少 idempotency key，provider timeout 后重复写入候选对象；跨用户 target id 只在前端过滤，API 未冻结 owner enforcement 的接口层字段。

### Failure Mode

F5 需要自行发明 endpoint、请求体、错误码和异步任务协议；F6 无法稳定接入；F7 无法覆盖未登录、越权、重复提交、timeout、rate limit、validation failed、source unavailable 和 rollback-safe 断言。

### Evidence

- `docs/02-design/API_SPEC.md` §1 声明不定义完整 endpoint，不冻结完整 request / response schema。
- `docs/02-design/API_SPEC.md` §2.2 明确不展开所有业务 endpoint、path、method、query 参数、pagination、完整错误码、权限矩阵、retry、rate limit 或 idempotency。
- `docs/02-design/API_SPEC.md` §10 只把 async / status / retry / idempotency 标为待收敛项。
- `docs/02-design/API_SPEC.md` §11 把完整接口族列为后续占位。
- `docs/02-design/API_SPEC.md` §12 明确完整 endpoint、error code、retry、idempotency、rate limit、timeout 和异步任务协议仍未关闭。

### Required Fix

需要回写 `API_SPEC.md`，补齐每个核心资源族的 endpoint、method、path、request、response、error code、auth / owner、pagination / sorting / filtering、status query、async / sync、retry、idempotency、timeout、rate limit 和 rollback-safe 语义；必要时同步 `TECH_DESIGN.md`、`PROMPT_SPEC.md` 与 `SECURITY_PRIVACY.md` 的交接边界。

### Required Decision

需要人工确认 AI 任务的同步 / 异步分界、报告 / 复盘 / 训练类任务是否必须异步、idempotency key 范围、rate limit 维度和前端可见错误语义。

### Acceptance Condition

F7 能根据 `API_SPEC.md` 直接生成 API contract tests，覆盖正例、权限失败、owner mismatch、validation failed、source unavailable、provider timeout、重复提交、rate limit、retry、partial success 和 rollback-safe。

## AR-F4-FULL-003: 评分、通过倾向、风险提示和校准口径仍未冻结

Severity: High  
Category: Scoring / Prompt / Testability  
Source Documents:
- `docs/03-delivery/DELIVERY_PLAN.md` §1 F4 / M4 退出标准
- `docs/01-product/PRD.md` §5.7 / §10
- `docs/02-design/DATA_MODEL.md` §10 / §12
- `docs/02-design/PROMPT_SPEC.md` §13
- `docs/02-design/prompt-contracts/JOB_MATCH_CONTRACTS.md` §11.2
- `docs/02-design/prompt-contracts/PRESSURE_CONTRACTS.md` §14.4
- `docs/02-design/prompt-contracts/REPORT_CONTRACTS.md` §3.2 / §3.3
Affected Downstream:
- F5 Backend / F6 Frontend / F7 QA / PROMPT_SPEC / DATA_MODEL / API_SPEC
Affected IDs:
- `OQ-F1-009` / `OQ-F1-010` / `OQ-F1-011` / `OQ-F1-032` / `OQ-F1-040` / `P-JOBMATCH-002` / `P-PRESSURE-008` / `P-REPORT-002` / `P-REPORT-003`
Status: Open

### Claim Under Review

F4 已经把 0-100 分、通过倾向、风险提示、可信度说明和免责声明转为可实现、可测试的设计。

### Contradiction / Gap

PRD 把具体评分公式、权重、阈值、校准方法、可信度说明、免责声明和通过倾向展示边界交给 F4/F7。当前 F4 active docs 只冻结“不得精确通过概率”和“0-100 是展示刻度”，但多个 contract 仍要求在评分规则未冻结时保留 UNKNOWN 或 `score_rule_unknown`。

### Adversarial Scenario

用户要求“给我一个 87% 通过概率”或 RAG 证据诱导模型输出“必过”。系统虽然禁止精确概率，但没有冻结评分阈值、校准、风险等级映射和免责声明，最终可能把低置信度风险文案包装成确定性结论，或不同报告使用不同评分口径。

### Failure Mode

F5 无法实现稳定评分规则版本；F6 无法展示一致的风险等级；F7 只能测试“不能输出精确概率”，无法测试“什么情况下低置信度”“何时提示风险”“评分与风险提示如何校准”。

### Evidence

- `docs/01-product/PRD.md` §5.7 明确具体评分公式、权重、阈值、校准方法、可信度说明、免责声明和最终展示方式由 F4 / F7 决定。
- `docs/01-product/PRD.md` §10 将匹配度评分公式、权重、阈值、校准、报告评分和通过倾向展示边界标为 `F4_TECH_DESIGN`。
- `docs/02-design/DATA_MODEL.md` §10 写明 `ScoreRuleVersion` 只表达规则版本边界，评分公式、权重、阈值、校准算法和规则发布流程不冻结。
- `docs/02-design/prompt-contracts/JOB_MATCH_CONTRACTS.md` §11.2、`PRESSURE_CONTRACTS.md` §14.4 和 `REPORT_CONTRACTS.md` §3.2 / §3.3 均保留评分规则 UNKNOWN、通过倾向展示边界或风险提示阈值 open question。

### Required Fix

需要回写 `TECH_DESIGN.md`、`PROMPT_SPEC.md`、`DATA_MODEL.md`、`API_SPEC.md` 和 `REPORT_CONTRACTS.md` / `JOB_MATCH_CONTRACTS.md` / `PRESSURE_CONTRACTS.md`，冻结最小评分规则版本、风险等级映射、低置信度触发、免责声明、禁止表达和 F7 fixture。

### Required Decision

需要人工确认 MVP 是否采用固定评分维度 / 权重 / 阈值，还是采用“无固定公式但有评分规则版本 + rubric + 校准声明”的替代口径；同时确认通过倾向只允许趋势性 / 等级性表达还是完全不展示。

### Acceptance Condition

F7 能验证 0、100、中间分、分数越界、证据不足、评分规则缺失、低置信度、风险提示、免责声明、禁止精确通过概率、禁止“必过 / 必挂”以及评分规则版本追踪。

## AR-F4-FULL-004: Report contract 重新引入 Markdown 下载 / 导出语义，违背 MVP 非目标

Severity: High  
Category: Scope / Prompt / Security / Privacy  
Source Documents:
- `docs/01-product/PRD.md` §5.7 / §9 / §10
- `docs/02-design/TECH_DESIGN.md` §4 / §12
- `docs/02-design/SECURITY_PRIVACY.md` §14 / §22
- `docs/02-design/prompt-contracts/REPORT_CONTRACTS.md` §3.0 / §3.4
Affected Downstream:
- F5 Backend / F6 Frontend / F7 QA / PROMPT_SPEC / SECURITY_PRIVACY
Affected IDs:
- `P-REPORT-004` / `OQ-F1-003` / `SP-DEF-002`
Status: Open

### Claim Under Review

F4 不承接文件导出，报告复制只是页面交互。

### Contradiction / Gap

PRD、TECH 和 SECURITY 均明确 MVP 不支持 PDF / Markdown / Word / docx / 批量导出，复制不是文件导出。但 `REPORT_CONTRACTS.md` 的公共 action 与 `P-REPORT-004` 明确出现 `download_markdown`、`markdown export preference`、`download_filename_hint`、`MarkdownExportSnapshot` 和“用户可以复制、下载”。

### Adversarial Scenario

F5/F6 依据 Report contract 实现 Markdown 下载能力，生成包含报告、复盘、第三方公司信息、面试回答或低置信度内容的导出文件。由于 Security 文档只设计页面复制审计，没有设计下载物鉴权、水印、保留、删除或外流控制，F7 无法按 MVP non-goal 验收。

### Failure Mode

MVP 范围被扩大到文件导出；复制审计边界被绕过；报告 / 复盘敏感内容可能以文件形式落到用户设备或日志 / trace 之外，导致隐私和交付范围双重偏移。

### Evidence

- `docs/01-product/PRD.md` §5.7 和 §9 明确 MVP 不支持 PDF、Markdown 文件、Word / docx 或批量导出，只支持报告内容复制。
- `docs/02-design/TECH_DESIGN.md` §4 / §12 明确报告复制是页面交互，后端不生成 PDF、Markdown、Word 或批量文件。
- `docs/02-design/SECURITY_PRIVACY.md` §14 / §22 明确 `CopyableContent` 不是导出物，Markdown / PDF / docx / 批量导出为 Deferred。
- `docs/02-design/prompt-contracts/REPORT_CONTRACTS.md` §3.0 将 `download_markdown` 列为 `next_recommended_actions` 允许值。
- `docs/02-design/prompt-contracts/REPORT_CONTRACTS.md` §3.4 在 trigger、optional inputs、output schema、persistence targets、user confirmation 和 test strategy 中多次使用 Markdown 下载 / export 语义。

### Required Fix

需要回写 `REPORT_CONTRACTS.md`，删除或改写 `download_markdown`、`markdown export preference`、`download_filename_hint`、`MarkdownExportSnapshot` 和“下载”相关语义；如需要可复制 Markdown 文本，应明确为剪贴板复制内容结构，不生成文件、不提供下载、不创建 export snapshot。同步检查 `PROMPT_SPEC.md`、`API_SPEC.md`、`SECURITY_PRIVACY.md` 是否有导出残留。

### Required Decision

需要人工确认 `P-REPORT-004` 是否只允许 `copy_report_section` / `copy_report_content`，以及是否禁止任何“download / export / filename / snapshot”实现语义进入 MVP。

### Acceptance Condition

`rg -n "download|export|导出|下载|filename|MarkdownExport" docs/02-design docs/03-delivery` 的 active 命中只能出现在 non-goal、deferred、禁止说明或本审计 finding 中；F7 能验证无文件生成、无文件下载、无批量导出入口。

## AR-F4-FULL-005: 进展树、暂停恢复与异步失败状态仍缺少可执行状态机

Severity: Medium  
Category: State / Reliability / Testability  
Source Documents:
- `docs/02-design/DATA_MODEL.md` §12
- `docs/02-design/PROMPT_SPEC.md` §13
- `docs/02-design/API_SPEC.md` §10 / §12
- `docs/02-design/prompt-contracts/SHARED_CONTRACTS.md` §10.6
- `docs/02-design/prompt-contracts/PRESSURE_CONTRACTS.md` §14.2 / §14.3
Affected Downstream:
- F5 Backend / F6 Frontend / F7 QA / DATA_MODEL / API_SPEC / PROMPT_SPEC
Affected IDs:
- `DM-UNK-005` / `DM-UNK-006` / `P-SHARED-006` / `P-PRESSURE-006` / `P-PRESSURE-007`
Status: Open

### Claim Under Review

打磨 / 压力面进展树、暂停恢复、状态查询、重试和失败恢复已具备可实现状态机。

### Contradiction / Gap

UX 已给出暂停、恢复失败和进展树可见状态；Prompt contracts 也定义 summary / pace / end condition 语义。但 `DATA_MODEL.md` 仍把暂停恢复最小快照、进展树节点全集、状态机和更新触发列为 UNKNOWN，`API_SPEC.md` 只占位 status query、retry、idempotency、cancellation、timeout 和 partial result。

### Adversarial Scenario

用户在打磨模式连续回答后暂停，再恢复时部分 LLM 任务失败或 source unavailable。前端显示恢复成功，但后端没有冻结最小恢复快照、进展树位置、covered_turn_refs、失败状态和重试 idempotency，导致重复题目、丢失进展或错把旧 summary 当新上下文。

### Failure Mode

恢复、重试和状态查询实现不一致；F7 无法验证 pause snapshot unavailable、resume failed、partial result、generation failed 和 low confidence inherited 等状态。

### Evidence

- `docs/02-design/DATA_MODEL.md` §12 `DM-UNK-005` / `DM-UNK-006` 明确暂停恢复字段、进展树数据结构、节点状态和更新触发未冻结。
- `docs/02-design/API_SPEC.md` §10 / §12 明确 status query、retry、idempotency、cancellation、timeout、partial result 和异步任务协议未定义。
- `docs/02-design/prompt-contracts/SHARED_CONTRACTS.md` §10.6 的 API state mapping 只定义状态语义，不定义 endpoint 或 schema。

### Required Fix

需要在 `DATA_MODEL.md` 冻结暂停恢复最小快照和进展树状态机；在 `API_SPEC.md` 定义 status query、resume、retry、cancel、timeout 和 idempotency；在 `PROMPT_SPEC.md` / `SHARED_CONTRACTS.md` 对齐 summary failure 与 source unavailable。

### Required Decision

需要确认打磨模式和压力面是否都允许暂停恢复、最小恢复快照字段、恢复失败时用户可见路径，以及重复提交 / 取消 / 重试是否由统一 async task 协议承接。

### Acceptance Condition

F7 能覆盖暂停、恢复、恢复失败、summary missing、covered_turn_refs missing、source unavailable、重复恢复请求、取消生成、timeout 和 partial result。

## AR-F4-FULL-006: F3 / F6 交接状态存在辅助文档冲突

Severity: Medium  
Category: Governance / Frontend Handoff  
Source Documents:
- `docs/03-delivery/DELIVERY_PLAN.md` §3 当前完成状态
- `docs/02-design/UI_DESIGN_SYSTEM.md` §22 / §25
Affected Downstream:
- F6 Frontend / F7 QA / N/A
Affected IDs:
- `AIFI-UI-001` / UNKNOWN
Status: Open

### Claim Under Review

F3 已完成且可作为 F6 前端实现输入。

### Contradiction / Gap

`DELIVERY_PLAN.md` 当前完成状态将 F3 标为 `DONE`，但 `UI_DESIGN_SYSTEM.md` 的高保真交付物索引仍列出多个页面 `UNKNOWN` / `NOT_STARTED`，且声明高保真页面总览、工作台、简历、岗位、模拟面试、报告、复盘、资产库、薄弱项、内容沉淀和低置信校对等均未完成或待复核。

### Adversarial Scenario

F6 实现窗口以 DELIVERY 的 F3 DONE 为依据，忽略 UI_DESIGN_SYSTEM 中的 UNKNOWN / NOT_STARTED 状态，导致前端实现按未批准或未完成的高保真草案推进。

### Failure Mode

F6 UI 实现与设计状态不一致；F7 视觉 / 交互验收无法判断哪些页面已批准，哪些只是候选或待复核。

### Evidence

- `docs/03-delivery/DELIVERY_PLAN.md` §3 将 F3 标为 `DONE`。
- `docs/02-design/UI_DESIGN_SYSTEM.md` §22 高保真交付物索引中多个页面状态为 `UNKNOWN` / `NOT_STARTED`。
- `docs/02-design/UI_DESIGN_SYSTEM.md` §25 仍要求覆盖 WARN / UNKNOWN / CONFLICT 台账，且不得把 UNKNOWN 写成已验证事实。

### Required Fix

需要回到 F3 / F6 交接治理窗口，统一 `DELIVERY_PLAN.md` 与 `UI_DESIGN_SYSTEM.md` 的状态口径；本轮不修改 F3 文档。

### Required Decision

需要人工确认 F3 DONE 是否只表示文档草案完成，还是高保真页面交付也已完成；若后者成立，需要把关闭证据回写到 `UI_DESIGN_SYSTEM.md`。

### Acceptance Condition

`DELIVERY_PLAN.md`、`UI_DESIGN_SYSTEM.md` 和后续 F6 任务入口对 F3 交付状态一致；F6 可以明确区分已批准设计、候选设计和 UNKNOWN。

## AR-F4-FULL-007: Prompt contract 子文档保留过期 Stub 状态说明

Severity: Low  
Category: Governance / Prompt  
Source Documents:
- `docs/02-design/PROMPT_SPEC.md` §10 / §14
- `docs/02-design/prompt-contracts/REPORT_CONTRACTS.md` §3.5
- `docs/02-design/prompt-contracts/REVIEW_CONTRACTS.md` §4.5
- `docs/02-design/prompt-contracts/WEAKNESS_CONTRACTS.md` §4.5
- `docs/02-design/prompt-contracts/ASSET_CONTRACTS.md` §3.5
Affected Downstream:
- PROMPT_SPEC / F7 QA
Affected IDs:
- `P-REPORT-*` / `P-REVIEW-*` / `P-WEAKNESS-*` / `P-ASSET-*` / `P-TRAINING-*`
Status: Open

### Claim Under Review

`PROMPT_SPEC.md` 是 canonical registry，子文档只承载已登记 contract 的正文细则，且当前业务 contract 状态已按 catalog 进入 Draft。

### Contradiction / Gap

当前主 registry 和各子文档状态表已显示相关 `P-*` contract 为 Draft，但多个子文档的“与其他 Contract 的关系”仍声明下游 contract 保持 Stub。这是状态说明过期，不构成 child-only ID 或直接实现阻断，但会误导后续审计、remediation 顺序和 F7 覆盖判断。

### Adversarial Scenario

后续整改窗口按这些过期说明判断 Review / Weakness / Asset / Training 仍未填充，重复创建任务或跳过对已 Draft contract 的一致性复核。

### Failure Mode

Prompt contract 治理状态不清，F7 无法稳定判断哪些 contract 已可形成测试断言，哪些仍只是 Stub 摘要。

### Evidence

- `docs/02-design/PROMPT_SPEC.md` §10 / §14 显示当前 catalog 和变更记录已将 Report、Review、Weakness、Asset、Training contract 更新为 Draft。
- `docs/02-design/prompt-contracts/REPORT_CONTRACTS.md` §3.5 仍写明 Review / Weakness / Asset / Training contracts 保持 Stub。
- `docs/02-design/prompt-contracts/REVIEW_CONTRACTS.md` §4.5 仍写明 Weakness / Asset / Training contracts 保持 Stub。
- `docs/02-design/prompt-contracts/WEAKNESS_CONTRACTS.md` §4.5 仍写明 Asset / Training contracts 保持 Stub。
- `docs/02-design/prompt-contracts/ASSET_CONTRACTS.md` §3.5 仍写明 Training contracts 保持 Stub。

### Required Fix

需要在后续 remediation 轮更新上述 prompt-contract 子文档的关系说明，使其与 `PROMPT_SPEC.md` canonical registry 和当前子文档状态一致。

### Required Decision

无需新增产品决策；需要确认这类过期状态说明是否统一改为“已 Draft，但不关闭相关 UNKNOWN / 不自动写正式对象”。

### Acceptance Condition

`rg -n "仍保持 Stub|仍是 Stub|保持 Stub" docs/02-design/PROMPT_SPEC.md docs/02-design/prompt-contracts` 不再命中过期状态说明；若出现 Stub，只能指向真实未填充 contract 或历史变更记录。

## 8. Previous Findings

| Previous Finding | Carry Forward | 本轮处理 |
|---|---|---|
| `AR-F4-001` 核心业务 Prompt contract Stub | No | 当前 `PROMPT_SPEC.md` 显示 48 个 `P-*` contract 已全部 Draft；previous finding not carried forward |
| `AR-F4-002` API handoff 缺口 | Yes | 以当前 `API_SPEC.md` 骨架证据生成 `AR-F4-FULL-002` |
| `AR-F4-003` 设计文档状态口径过期 | No | 当前 TECH / SECURITY 已承认 API / DATA / PROMPT 存在；previous finding not carried forward |
| `AR-F4-004` Report 风险提示 / 精确概率 | Yes | 以当前评分和风险提示 UNKNOWN 生成 `AR-F4-FULL-003` |
| `AR-F4-005` Real Interview Review 隐私 / 注入 | No | 当前 Review contracts 已 Draft，且包含真实面试确认、低置信、禁止预测和隐私边界；previous finding not carried forward |
| `AR-F4-006` Candidate 到 Formal 写入边界 | No | 当前 DATA / API / Prompt / child contracts 对 candidate / suggestion / confirmation / formal object 边界基本一致；previous finding not carried forward |
| `AR-F4-007` Evidence key claim | No | 当前业务 contracts 多数已补 Evidence Requirements；剩余风险并入 API/F7 可测试性 |
| `AR-F4-008` Reliability / retry / idempotency | Yes | 当前证据并入 `AR-F4-FULL-002` 和 `AR-F4-FULL-005` |

## 9. Final Gate

- Critical: 0
- High: 4
- Medium: 2
- Low: 1

F4 是否允许退出：否。  
F5 是否允许启动：否。  
F7 是否具备测试输入：部分具备，但不足以进入全链路验收。  

## 10. 本轮不修复项

- 不修改 active design docs。
- 不关闭任何 `F4_TECH_DESIGN` UNKNOWN。
- 不修改旧 `AIFI-ARCH-003` 审计产物。
- 不创建 roadmap、plan-v2、latest-plan、codex-plan 或临时计划文件。

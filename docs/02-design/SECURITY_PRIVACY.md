---
title: SECURITY_PRIVACY
type: design
status: draft-f4-security-privacy
owner: 安全隐私
source_task: AIFI-SEC-001
permalink: ai-for-interviewer/docs/02-design/security-privacy
---

# SECURITY_PRIVACY

## 1. 文档状态与治理边界

- 本文件是 F4 / M4 安全隐私规范草案，承接 `AIFI-SEC-001`。
- 本文件定义 MVP 最小可实施安全隐私边界，为后续 `API_SPEC.md`、`PROMPT_SPEC.md`、`DATA_MODEL.md` 协同修订、F5 实现和 F7 验收提供输入。
- 本文件不是企业级安全白皮书，不是法律条款正文，不是 API spec，不是 Prompt spec，不是物理数据库或部署设计。
- 本文件不关闭任何 `F4_TECH_DESIGN` UNKNOWN，不标记 `AIFI-ARCH-002` 完成，也不把 `AIFI-SEC-001` 标记为 DONE。
- 本文件不新增 roadmap、plan-v2、codex-plan、临时任务文档、并行设计文档或 ADR。
- 本文件不得把 `archive/` 内容作为当前执行依据；历史内容只有进入 active docs 后才能影响本文。

## 2. 输入来源与非目标

### 2.1 输入来源

| 来源 | 本文使用方式 |
|---|---|
| `docs/01-product/PRD.md` | MVP 角色、核心业务对象、数据流、状态异常、复制 / 导出口径、低置信度和 UNKNOWN 台账 |
| `docs/02-design/UX_SPEC.md` | 用户可见入口、用户设置、内容沉淀确认、低置信度校对、报告复制和状态表达 |
| `docs/02-design/UI_DESIGN_SYSTEM.md` | F3 页面 / 组件状态边界、复制非导出、低置信度和内容沉淀交接语义 |
| `docs/02-design/TECH_DESIGN.md` | 前后端职责、LLM 后端隔离、模块边界、F4 子文档交接边界 |
| `docs/02-design/DATA_MODEL.md` | `OwnerRef`、`RoleScope`、`PermissionBoundary`、`AuditEvent`、`TraceRef`、`RetentionPolicyRef`、`RedactionRef` 等逻辑对象 |
| `docs/03-delivery/DELIVERY_PLAN.md` | F4 / M4 安全隐私作为技术设计评审输入的阶段边界 |
| `docs/03-delivery/BACKLOG.md` | `AIFI-SEC-001` 范围，以及与 `AIFI-ARCH-002`、`AIFI-DATA-001`、`AIFI-PROMPT-001` 的依赖关系 |

### 2.2 非目标

本文不展开以下内容：

- 企业级多租户、复杂 ACL、组织 / 团队 / 部门空间、资源继承权限模型。
- OAuth / SSO / 企业身份提供商完整方案。
- 完整合规认证方案或法律条款正文。
- API endpoint、request / response API schema、错误码全集。
- Prompt 模板、LLM 模型参数、provider-specific payload、retry / fallback 策略、模型选型细节。
- 物理数据库 DDL、ORM model、数据库索引、外键、migration。
- 向量数据库选型、embedding 模型选型、索引实现。
- Markdown / PDF / docx / 批量导出。
- 精确通过概率承诺或真实面试结果预测承诺。

## 3. MVP 安全隐私设计原则

1. MVP 默认是个人工作台 ownership 边界；用户只能访问自己创建或被明确授权的简历、岗位、会话、报告、复盘、资产、薄弱项、训练建议、知识文档和 trace 摘要。
2. 管理员 / 内容维护者只拥有最小维护能力，不扩展为企业组织管理员。
3. 前端不直接访问模型、密钥、原始 Prompt、provider payload、数据库或后端业务真相。
4. LLM 输入由后端按最小必要原则组装；无关简历、岗位、反馈、资产、隐私字段和第三方敏感信息不得进入模型输入。
5. LLM 原始输出不能直接成为前端展示或业务事实源；必须经过结构化校验和业务语义校验。
6. 低置信度、冲突、不完整、validation failed、generation failed 和 source unavailable 必须显式标记，不得伪装成正常高置信结果。
7. RAG 证据进入业务结果时必须保留来源、版本、快照、证据和 trace 引用。
8. 内容沉淀、资产入库、薄弱项确认、训练建议确认和回流不得静默覆盖用户数据。
9. 历史报告、复盘、评分和资产候选应稳定回看；源对象删除、禁用或归档后，通过来源可用性状态表达，不静默改写历史结论。
10. 复制是页面交互能力，不是文件导出能力。

## 4. 数据分类、ownership 与可见性边界

| 数据域 | 代表对象 | 最小 owner / creator 边界 | MVP 可见性边界 |
|---|---|---|---|
| 简历 | `Resume`、`ResumeVersion`、`ResumeModule` | 求职者 / 面试准备用户为 owner；创建者记录到 `OwnerRef` | 默认仅 owner 可见；管理员 / 内容维护者不得默认查看个人简历正文 |
| 岗位 / JD | `Job`、`JobVersion`、`JobStatus` | 用户手动创建，owner 为个人工作台用户 | 默认仅 owner 可见；公司、岗位职责和投递状态可能包含敏感求职信息 |
| 岗位-简历绑定 | `JobResumeBinding` | 绑定关系归属 owner，引用生成时岗位 / 简历版本 | 默认仅 owner 可见；解绑不得破坏历史报告和复盘回看 |
| 模拟面试会话 | `InterviewSession` | 会话 owner 为发起用户 | 默认仅 owner 可见；会话中的题目、回答、点评、评分均随会话归属 |
| 打磨模式会话 | `PolishSessionDetail` | 会话 owner 为发起用户 | 默认仅 owner 可见；同题多轮历史回答和建议不得跨用户泄露 |
| 压力面模式会话 | `PressureSessionDetail` | 会话 owner 为发起用户 | 默认仅 owner 可见；连续追问和整场评估为个人训练数据 |
| 题目、回答、点评、评分 | `Question`、`Answer`、`Feedback`、`ScoreResult` | 归属关联会话 owner，保留 `TraceRef` | 默认仅 owner 可见；用于后续报告、复盘、薄弱项和训练建议时仍需来源引用 |
| 面试报告 | `InterviewReport`、`ReportSection`、`CopyableContent` | 报告 owner 为会话 owner | 默认仅 owner 可见；页面复制只复制授权范围内内容 |
| 模拟面试复盘 | `MockInterviewReview`、`ReviewItem` | 复盘 owner 为关联会话 owner | 默认仅 owner 可见；来源是系统内会话链路 |
| 真实面试复盘 | `RealInterviewReview`、`RealInterviewInput`、`RealInterviewEvidence` | 用户录入，owner 为个人工作台用户 | 默认仅 owner 可见；可能包含第三方面试官、公司、真实问题和反馈等敏感信息 |
| 薄弱项 | `Weakness`、`WeaknessEvidence` | owner 为个人工作台用户，来源证据保留引用 | 默认仅 owner 可见；不得无确认静默消减或覆盖 |
| 训练建议 | `TrainingRecommendation`、`TrainingTask`、`TrainingResult` | owner 为个人工作台用户 | 默认仅 owner 可见；建议可跳过或确认，不等同于强制训练任务 |
| 资产 / 资产版本 / 资产候选 | `Asset`、`AssetVersion`、`AssetCandidate` | owner 为个人工作台用户；候选需 `UserConfirmationRef` | 默认仅 owner 可见；候选入库前不得成为正式资产 |
| RAG / Knowledge Base | `KnowledgeBase`、`KnowledgeDocument`、`KnowledgeChunk`、`RetrievalEvidence` | 用户私有文档归 owner；公共参考材料归维护者边界 | `KnowledgeBase` 是后端逻辑检索边界，不是用户可见一级模块；证据片段展示需脱敏和来源约束 |
| LLM trace / validation / usage | `LlmRequestTrace`、`LlmResponseTrace`、`LlmUsageRecord`、`LlmValidationResult` | 归属关联业务对象 owner，调用方记录到 trace | 前端只可见可展示结果、状态和必要错误引用；原始输出保存与可见性为 UNKNOWN |
| AuditEvent | `AuditActor`、`AuditTarget`、`AuditEvent` | actor / target / owner 均需记录 | 用户可见审计历史、管理员可见范围、保留周期均为 UNKNOWN |

本文不设计组织、团队、部门空间、企业级租户隔离或资源继承权限模型。

## 5. 用户、账号、角色、RoleScope 与 PermissionBoundary

| 对象 | 安全隐私职责 | 本文边界 |
|---|---|---|
| `UserAccount` | 表达登录身份、账号状态和个人工作台归属 | 不定义完整登录、OAuth、SSO 或企业身份提供商方案 |
| `OwnerRef` | 表达资源 owner、creator 和生成时间 | 所有个人业务对象都应可追溯到 owner 或创建者 |
| `RoleAssignment` | 表达用户被赋予的最小角色 | MVP 至少区分普通用户与管理员 / 内容维护者；不设计组织角色树 |
| `RoleScope` | 表达角色作用范围 | 范围限定为个人工作台资源或维护者负责的公共参考材料 / 基础配置 |
| `PermissionBoundary` | 表达允许动作摘要和限制原因 | 只冻结资源可见性和操作边界；复杂鉴权 API 交给 `API_SPEC.md` / F5 |
| `AuditActor` | 表达动作主体 | 记录用户、系统任务或维护者动作的角色快照 |
| `AuditTarget` | 表达动作目标 | 记录资源类型、资源标识、版本和 owner 引用 |
| `AuditEvent` | 表达关键动作审计 | 只定义最小审计边界，不写日志字段全集或物理存储结构 |

求职者 / 面试准备用户可以访问和维护自己的个人工作台数据，包括简历、岗位、绑定关系、会话、报告、复盘、薄弱项、训练建议、资产和用户私有知识文档。用户不得访问其他用户的个人数据。

复杂鉴权 API、资源继承、组织权限、跨用户授权、用户可查看审计历史和管理员可查看审计历史的细则，交给 `API_SPEC.md` / F5 实现阶段。

## 6. 管理员 / 内容维护者最小管理边界

管理员 / 内容维护者的 MVP 边界为：

- 维护公共参考材料、基础评分口径和账号可见性配置的最小管理入口。
- 维护动作必须记录 `AuditActor`、`AuditTarget`、`AuditEvent` 和风险标记。
- 不默认拥有查看、导出、复制或修改用户个人简历、岗位、回答、报告、复盘、资产和 trace 原文的权限。
- 不成为企业组织管理员，不管理组织、团队、部门空间或资源继承。
- 公共参考材料进入 RAG 时必须有来源、版本、维护者和可用性状态。

管理员 / 内容维护者具体能维护哪些公共参考材料、评分口径和账号可见性配置，列为 SECURITY_PRIVACY UNKNOWN。

## 7. 核心对象可见性矩阵

| 对象域 | 普通用户 | 管理员 / 内容维护者 | 系统任务 / 后端编排 |
|---|---|---|---|
| 个人简历、岗位、绑定关系 | 仅访问本人 owner 数据 | 默认不可查看正文；支持最小配置或审计入口待决策 | 可在 owner 授权的业务链路内读取必要版本 |
| 模拟面试会话、题目、回答、点评 | 仅访问本人会话 | 默认不可查看正文 | 可为生成、评分、复盘和恢复读取必要片段 |
| 面试报告、复盘、薄弱项、训练建议 | 仅访问本人结果 | 默认不可查看正文 | 可按业务链路生成、校验、标记低置信度 |
| 资产和资产候选 | 仅访问本人资产；候选需确认 | 默认不可查看正文 | 可生成候选，不得绕过确认写入正式资产 |
| 用户私有知识文档 | 仅 owner 可见 | 默认不可查看正文 | 可按 owner 业务请求参与 RAG |
| 公共参考材料 | 可按产品授权被检索或引用摘要 | 可维护来源、版本和可用性 | 可参与 RAG，但必须保留来源和证据引用 |
| LLM trace / usage / validation | 默认只见业务结果、状态和必要错误提示 | 可查看的 trace 范围为 UNKNOWN | 可保存最小追踪、usage、validation 和 failure |
| AuditEvent | 用户可见范围为 UNKNOWN | 可查看范围、保留周期为 UNKNOWN | 必须记录关键动作最小审计 |

## 8. LLM 输入最小化、后端隔离与输出校验边界

- 前端不得直接访问模型、provider key、模型调用凭据、原始 Prompt、provider-specific request / response payload 或原始模型输出。
- LLM 输入由后端应用编排层和 LLM / Prompt 边界层按最小必要原则组装。
- 不应把无关简历、岗位、回答、反馈、资产、知识文档、第三方信息或隐私字段送入模型。
- Prompt 输入最小化、上下文裁剪、敏感字段排除、低置信度和 validation 要求交给 `PROMPT_SPEC.md`。
- LLM 原始输出不能直接成为前端或业务事实源。
- LLM 输出必须经过结构化校验和业务语义校验后，才能进入报告、复盘、薄弱项、训练建议或资产候选。
- 低置信度、冲突、不完整和失败结果必须进入状态和风险标记。

本文不展开 Prompt 模板、模型调用参数、provider-specific payload、retry / fallback 策略或模型选型细节。

## 9. RAG / Knowledge Base 来源治理与证据边界

- `KnowledgeBase` 是后端逻辑检索边界，不是用户可见一级模块，也不新增一级导航。
- `KnowledgeDocument` 必须记录来源、版本、owner 或维护者、状态和更新时间。
- `KnowledgeChunk` / `RetrievalEvidence` 必须可追踪到知识文档、chunk、来源版本和命中摘要。
- 用户私有知识文档只能服务 owner 的业务链路；公共参考材料必须有维护者边界和可用性状态。
- RAG evidence 进入业务结果时，必须保留 `EvidenceRef` / `SourceRef` / `VersionRef` / `SnapshotRef` / `TraceRef`。
- RAG 证据不足、来源冲突、低可信或 source unavailable 时，必须进入低置信度、风险标记或部分可用状态。
- RAG 证据摘要的前端展示范围应避免泄露无关个人数据、第三方敏感信息和不应展示的原始材料片段。

本文不展开向量数据库选型、embedding 模型选型、索引实现、外部文件导入 / 导出能力。

## 10. LLM trace、usage、validation、retention、redaction 保存边界

| 对象 | 保存边界 | 不保存 / 待决策边界 |
|---|---|---|
| `LlmRequestTrace` | 调用场景、关联业务对象、来源引用、版本 / 快照引用、RAG 组装引用、请求时间、调用方、provider、model family、状态 | 不保存 Prompt 模板、模型参数或 provider-specific payload；原始输入片段保存范围为 UNKNOWN |
| `LlmResponseTrace` | request trace、原始输出引用、结构化输出引用、validation 引用、失败状态 | 原始输出是否保存、保存多久、如何脱敏为 UNKNOWN |
| `LlmUsageRecord` | token、cost、latency、provider、model family 等统计边界 | 不锁定具体供应商实现，不暴露密钥 |
| `LlmValidationResult` | 结构化校验、业务语义校验、低置信度、冲突、不完整、失败 | 不定义具体阈值、评分公式或 Prompt 规则 |
| `LlmRetentionPolicyRef` | 记录适用策略引用和状态 | 具体保留周期、删除触发和历史回看冲突为 UNKNOWN |
| `LlmRedactionRef` | 记录脱敏策略引用、字段范围和状态 | 具体脱敏实现、字段全集和可逆性为 UNKNOWN |
| `LlmFailureRecord` | request trace、失败阶段、错误分类、可重试性、影响对象、时间 | 不定义 retry / fallback 策略 |
| `TraceRef` | 为报告、复盘、评分、薄弱项、训练建议、资产候选和审计提供过程引用 | 不暴露 provider payload、Prompt 模板或密钥 |

## 11. 日志、审计、错误追踪和风控事件最小记录

最小审计事件应覆盖：

- `actor`：用户、管理员 / 内容维护者、系统任务。
- `action`：登录 / 权限、数据查看、创建、编辑、删除、复制、生成、确认、拒绝、修正、跳过、回流、资产入库、管理员维护动作。
- `target`：目标对象、目标版本、owner 引用。
- `timestamp`：动作发生时间。
- `source`：Web UI、API、系统任务、LLM / RAG 链路或维护入口。
- `result`：成功、失败、部分成功、禁用、低置信度、冲突、不完整。
- `risk flag`：低置信度、敏感字段、第三方信息、source unavailable、权限异常、复制动作、删除 / 归档动作。
- `trace reference`：必要时关联 `TraceRef`、`UserConfirmationRef`、`VersionRef` 或 `SnapshotRef`。

本文不写完整日志平台、监控平台、SIEM 方案、日志字段全集或物理存储结构。日志保留周期、可查看主体和用户可见审计历史列为 UNKNOWN。

## 12. 数据脱敏、retention、deletion 与历史快照冲突边界

- 简历、岗位、回答、报告、复盘、资产、知识文档、RAG 证据和 LLM trace 都可能包含敏感信息。
- MVP 采用最小脱敏原则：前端、日志、trace、RAG evidence 和审计记录只展示完成任务所需的最小摘要。
- 历史报告、复盘、评分结果和资产候选需要稳定回看，应通过 `VersionRef` / `SnapshotRef` 引用生成时来源。
- 删除 / 归档 / 禁用源对象后，历史结果不应静默改写结论；应通过 `source_available`、`source_archived`、`source_deleted`、`source_disabled` 或 `source_unavailable` 表达来源当前可用性。
- retention / deletion 与 `VersionRef` / `SnapshotRef` 稳定回看之间的冲突，列为 UNKNOWN，待后续 F5 实现决策。
- 对第三方敏感信息、公司敏感材料和过度个人信息的脱敏规则，应在后续安全实现中细化。

## 13. 报告复制与文件导出 non-goal

- MVP 支持页面复制报告内容。
- 报告复制不是文件导出。
- `CopyableContent` 只表示页面复制所需的结构化内容边界，不是导出物、不是下载文件、不是批量产物。
- MVP 不支持 Markdown / PDF / docx / 批量导出。
- 本文件不得新增任何文件导出能力。
- 复制行为需要最小事件记录，至少应能审计复制主体、目标报告、时间、结果和必要风险标记；具体粒度列为 UNKNOWN。

## 14. 真实面试复盘敏感信息、来源可信度和完整度

- 真实面试复盘来源于用户录入的外部真实面试经历。
- 系统不能假设拥有完整真实面试过程。
- 用户可能输入第三方面试官信息、公司信息、真实问题、回答回忆、结果状态、面试反馈、补充材料和主观判断。
- `RealInterviewInput` / `RealInterviewEvidence` 需要记录输入来源、可信度、完整度和用户确认状态。
- 第三方敏感信息、过度个人信息、公司敏感材料和可能不应上传的外部材料，应作为安全隐私重点风险。
- 材料过短、来源不明、用户回忆不完整、第三方反馈不可验证时，复盘结果应标记低置信度、不完整或需要用户确认。
- 真实面试复盘不得承诺对真实面试结果的准确预测。

## 15. 用户确认、内容沉淀、资产入库和回流审计

以下动作必须保留最小确认和审计边界：

- `UserConfirmationRef`：确认、拒绝、修正、跳过、回流确认和资产入库确认。
- 内容沉淀确认：用户确认是否将报告、复盘、薄弱项中的可复用内容沉淀到资产库、薄弱项、训练建议或后续模拟面试输入。
- 资产入库确认：`AssetCandidate` 不得绕过确认成为正式 `Asset` / `AssetVersion`。
- 资产候选拒绝 / 修正：拒绝或修正都应保留来源和动作结果。
- 薄弱项确认：系统识别的弱项不得静默覆盖用户既有弱项。
- 训练建议确认或跳过：建议可确认、跳过或后续处理，不等同于强制训练任务。
- 回流确认：系统不得静默覆盖资产、薄弱项、训练建议或下一次模拟面试输入。

是否需要详细审计字段、保留周期和用户可见历史，列为 UNKNOWN 或交给后续 `API_SPEC.md` / F5。

## 16. 低置信度、冲突、不完整和失败状态的安全表达

| 状态 | 安全表达边界 |
|---|---|
| `low_confidence` | 告知资料不足、证据不足或模型判断不稳定，不伪装为确定结论 |
| `conflict` | 标记来源冲突、评分解释冲突或证据冲突，提示需要用户校对或后续处理 |
| `incomplete` | 标记材料不完整、模型输出不完整或 RAG 证据不足 |
| `validation_failed` | 结构化校验或业务语义校验失败，不进入正常业务事实 |
| `generation_failed` | 生成失败时保留用户输入和可用部分，不提前展示完成态 |
| `source_unavailable` | 来源被删除、禁用、归档、不可访问或缺少版本快照时，展示来源可用性状态 |

安全表达不得误导用户，不得把低置信度结果伪装成高置信结果，不得承诺精确通过概率或真实面试结果预测。风险提示、可信度说明和免责声明边界需要记录；具体展示文案交给 UX / API / F7 验收细化。

## 17. 密钥、provider、模型调用凭据和后端隔离

- provider key 不进入前端。
- 模型调用凭据只在后端受控边界内使用。
- provider、model family、usage 可以记录统计边界，但不得暴露密钥。
- 前端只接收通过后端校验后的业务结果、状态、风险提示和必要错误引用。
- 密钥管理细则、轮换、部署 secret 管理、最小访问控制和泄露响应作为后续 F5 实现或 SECURITY_PRIVACY UNKNOWN。
- 本文不写具体云服务、密钥平台或部署 secret 选型。

## 18. 与 API_SPEC.md、DATA_MODEL.md、PROMPT_SPEC.md 的交接边界

| 交接对象 | 本文交接内容 | 本文不展开内容 |
|---|---|---|
| `DATA_MODEL.md` | 承接 ownership、`RoleScope`、`PermissionBoundary`、`AuditEvent`、`TraceRef`、`RetentionPolicyRef`、`RedactionRef`，定义安全隐私可见性和保留边界 | 不改写数据对象定义，不写物理 schema |
| `API_SPEC.md` | 交接鉴权语义、错误语义、权限错误、审计触发点、复制事件、删除 / 归档 / 不可用状态 | 不定义 endpoint 或 request / response schema |
| `PROMPT_SPEC.md` | 交接 Prompt 输入最小化、上下文裁剪、敏感字段排除、低置信度和 validation 要求 | 不写 Prompt 模板、模型调用参数或 provider payload |
| F5 实现 | 交接密钥管理、日志保留、脱敏实现、审计事件落库、删除策略、trace 存储和访问控制 | 不写 ORM、DDL、migration 或平台选型 |

`API_SPEC.md` 与 `PROMPT_SPEC.md` 尚未创建前，鉴权语义、错误语义、Prompt 输入裁剪和模型调用细节只能标记待交接，不得在本文提前冻结实现。

## 19. UNKNOWN / 待决策项

本节只登记 SECURITY_PRIVACY 自身待决策项，不关闭 PRD §10、`TECH_DESIGN.md` 或 `DATA_MODEL.md` 中的 `F4_TECH_DESIGN` UNKNOWN。

| 编号 | 待决策项 | 来源 | 本文当前边界 |
|---|---|---|---|
| SP-UNK-001 | 隐私字段分级：简历、岗位、回答、报告、复盘、资产、知识文档、RAG 证据和 LLM trace | `PRD.md`、`DATA_MODEL.md`、`BACKLOG.md` AIFI-SEC-001 | 已列出数据域和最小 owner 边界，未冻结字段级敏感等级 |
| SP-UNK-002 | LLM 原始输出、结构化输出、业务结果之间的保存、脱敏和可见性边界 | `TECH_DESIGN.md`、`DATA_MODEL.md` | 已区分 request trace、response trace、usage、validation、failure，未冻结原始输出保存和可见性 |
| SP-UNK-003 | retention / deletion 与历史 `VersionRef` / `SnapshotRef` 可回看之间的冲突处理 | `DATA_MODEL.md`、`DELIVERY_PLAN.md` F4 | 已确认历史结果不静默改写，未冻结删除、脱敏、保留和恢复策略 |
| SP-UNK-004 | 管理员 / 内容维护者能维护哪些公共参考材料、评分口径和账号可见性配置 | `PRD.md` §3、`BACKLOG.md` AIFI-SEC-001 | 已定义最小维护边界，未冻结维护对象全集和可见范围 |
| SP-UNK-005 | 审计事件 taxonomy、risk flag、日志保留周期和可查看主体 | `DATA_MODEL.md`、`TECH_DESIGN.md` | 已定义最小审计字段，未冻结字段全集、保留周期和查看主体 |
| SP-UNK-006 | 真实面试输入中的第三方敏感信息、可信度等级、完整度等级和用户确认机制 | `PRD.md`、`UX_SPEC.md`、`DATA_MODEL.md` | 已要求来源、可信度、完整度和用户确认，未冻结等级枚举和处理规则 |
| SP-UNK-007 | API_SPEC.md 与 PROMPT_SPEC.md 未创建前的鉴权语义、错误语义、Prompt 输入裁剪和模型调用细节 | `TECH_DESIGN.md`、`BACKLOG.md` AIFI-API-001 / AIFI-PROMPT-001 / AIFI-SEC-001 | 已列为交接边界，不在本文定义 endpoint、schema、Prompt 模板或模型参数 |
| SP-UNK-008 | 报告复制事件审计粒度、用户可见复制历史和复制失败风控表达 | `PRD.md`、`UX_SPEC.md`、`DATA_MODEL.md` | 已确认复制不是导出且需要最小事件记录，未冻结粒度 |
| SP-UNK-009 | 密钥管理、轮换、部署 secret、provider 访问控制和泄露响应 | `TECH_DESIGN.md`、`BACKLOG.md` AIFI-SEC-001 | 已确认密钥只在后端受控边界内使用，未冻结平台和流程 |
| SP-UNK-010 | 公共参考材料与用户私有知识文档混用时的 RAG 证据展示、脱敏和冲突降级 | `DATA_MODEL.md`、`TECH_DESIGN.md` | 已要求来源、版本、维护者和 evidence 引用，未冻结展示规则和降级阈值 |

## 20. 变更记录

| 日期 | 变更 | 影响 |
|---|---|---|
| 2026-05-15 | 初始化 F4 安全隐私规范草案 | 建立 `AIFI-SEC-001` 的 ownership、角色权限、LLM 隔离、RAG 来源、trace、审计、脱敏、保留、复制 non-goal、真实面试敏感信息、用户确认、密钥和 UNKNOWN 边界；不关闭 `F4_TECH_DESIGN` UNKNOWN |

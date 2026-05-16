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
| `.env.example`、`apps/api/app/main.py` | 当前 API 入口只保留最小运行配置；真实密钥、真实 token、真实 DSN 不得进入示例环境文件或启动日志 |

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

### 4.1 核心数据域 ownership

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
| LLM trace / validation / usage | `LlmRequestTrace`、`LlmResponseTrace`、`LlmUsageRecord`、`LlmValidationResult` | 归属关联业务对象 owner，调用方记录到 trace | 前端只可见可展示结果、状态和必要错误引用；MVP 默认不向前端暴露原始 Prompt、completion 或 provider payload |
| AuditEvent | `AuditActor`、`AuditTarget`、`AuditEvent` | actor / target / owner 均需记录 | 用户可见本人关键动作摘要；管理员 / 内容维护者仅可见维护范围和安全事件摘要 |

本文不设计组织、团队、部门空间、企业级租户隔离或资源继承权限模型。

### 4.2 字段级数据分类矩阵

| 数据项 | 数据类型 | PII | 敏感 | 用户生成 | 系统生成 | 派生数据 | 可持久化 | 可发送给 LLM | 允许进入日志 | 支持删除 | 默认 owner | MVP 控制要求 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 用户账号数据 | 邮箱、昵称、账号状态、角色快照 | 是 | 是 | 是 | 是 | 否 | 是 | 否 | 仅脱敏账号标识 | 是 | `UserAccount` 本人 | 密码或凭据不得明文保存；日志只记录脱敏 actor；账号禁用后阻断业务访问 |
| session / token / cookie | 会话标识、刷新状态、过期时间 | 是 | 是 | 否 | 是 | 否 | 条件 | 否 | 否 | 是 | 登录用户 | `HttpOnly`、`Secure`、`SameSite`；不得进入前端可读存储、日志、LLM 或复制内容 |
| 简历原文 | Markdown / text 简历正文 | 是 | 是 | 是 | 否 | 否 | 是 | 条件 | 否 | 是 | 简历 owner | 仅 owner 可读；进入 LLM 前按任务裁剪；删除后 active 读取失效 |
| 简历识别文本 | 模块识别结果、纯文本、结构化段落 | 是 | 是 | 否 | 是 | 是 | 是 | 条件 | 否 | 是 | 简历 owner | 与 `ResumeVersion` 绑定；不得跨用户复用；识别失败不落部分业务事实 |
| 岗位信息 | 公司、岗位、JD、投递状态 | 条件 | 是 | 是 | 否 | 否 | 是 | 条件 | 仅目标标识和状态 | 是 | 岗位 owner | 岗位仅手动录入；公司敏感信息进入 LLM 前最小化；删除后绑定失效 |
| 面试问答 | 题目、回答、追问、点评 | 是 | 是 | 是 | 是 | 条件 | 是 | 条件 | 否 | 是 | 会话 owner | 归属 `InterviewSession`；只允许同 owner 会话链路读取 |
| 真实面试复盘 | 逐字稿、真实反馈、外部面试信息 | 是 | 是 | 是 | 是 | 条件 | 是 | 条件 | 否 | 是 | 复盘 owner | 标记来源、完整度、可信度；第三方敏感信息按最小必要进入 LLM |
| 模拟面试复盘 | 系统内会话复盘、题级表现 | 是 | 是 | 否 | 是 | 是 | 是 | 条件 | 否 | 是 | 会话 owner | 只能引用 owner 的模拟面试快照、评分和 trace |
| 多维评分 | 0-100 展示值、维度、解释、规则版本 | 否 | 是 | 否 | 是 | 是 | 是 | 条件 | 仅状态和 trace | 是 | 关联对象 owner | 必须保留 `ScoreRuleVersion`、证据和低置信度；不承诺精确通过概率 |
| 薄弱项 | 弱项、证据、状态历史 | 条件 | 是 | 否 | 是 | 是 | 是 | 条件 | 仅状态 | 是 | 用户本人 | 系统识别不能静默覆盖；确认、跳过、归档都需记录 |
| 训练记录 | 建议、训练任务、训练结果 | 条件 | 是 | 是 | 是 | 是 | 是 | 条件 | 仅状态 | 是 | 用户本人 | 仅 owner 可见；由用户确认或主动触发，不作为强制任务 |
| RAG 文档 | 私有知识文档、公共参考材料 | 条件 | 条件 | 是 | 是 | 否 | 是 | 条件 | 仅来源标识 | 是 | 私有文档 owner；公共材料维护者 | 私有文档只服务 owner；公共材料需维护者、来源、版本、状态 |
| embedding / vector index | chunk embedding 引用、索引元数据 | 可能 | 是 | 否 | 是 | 是 | 是 | 否 | 否 | 是 | 源文档 owner / 维护者 | 不记录原文到日志；按 owner 或公共范围隔离；源删除后立即失效并重建索引 |
| LLM prompt | 后端组装上下文 | 是 | 是 | 否 | 是 | 是 | 默认不持久化 | 调用内容本身 | 否 | 随 trace 删除 / 脱敏 | 关联对象 owner | 前端不可见；禁止 tokens、secrets、无关用户数据和原始文件二进制进入 |
| LLM completion | 模型原始响应、结构化候选 | 可能 | 是 | 否 | 是 | 是 | 默认不保存原始响应；保存结构化结果 | 否 | 否 | 是 | 关联对象 owner | 先校验再入业务结果；失败只保存错误分类和 trace |
| Markdown 下载 / 复制内容 | `CopyableContent`、剪贴板文本 | 可能 | 是 | 是 | 是 | 是 | 复制结构可持久化；下载文件 Deferred | 否 | 仅复制事件摘要 | 系统内内容支持删除；用户设备副本不可控 | 报告 / 复盘 owner | MVP 只支持页面复制，不生成 Markdown 文件；复制前必须鉴权并审计 |
| 操作日志 | 访问、创建、编辑、删除、复制、生成事件 | 可能 | 条件 | 否 | 是 | 是 | 是 | 否 | 日志自身 | 条件 | 平台安全边界 | 不含正文、Prompt、completion、token、secrets；actor / target 最小化 |
| 错误日志 | 错误分类、trace id、状态码、失败阶段 | 可能 | 条件 | 否 | 是 | 是 | 是 | 否 | 日志自身 | 条件 | 平台安全边界 | 不记录 request / response body；异常堆栈需脱敏；LLM 失败不落原始 payload |
| 环境变量 / API key / secrets | provider key、数据库凭据、cookie secret | 否 | 是 | 否 | 是 | 否 | 仅 secret 管理边界 | 否 | 否 | 轮换 / 废弃 | 项目运维边界 | 不进入仓库、前端、日志、Prompt、trace、示例环境文件；`.env.example` 只允许 fake 值 |

“可发送给 LLM”为“条件”时，含义是后端必须先完成登录态校验、owner 校验、任务必要性判断、字段裁剪、敏感字段排除和 trace 关联；不能由前端直接决定。

## 5. 用户、账号、角色、RoleScope 与 PermissionBoundary

| 对象 | 安全隐私职责 | 本文边界 |
|---|---|---|
| `UserAccount` | 表达登录身份、账号状态和个人工作台归属 | MVP 只冻结本地账号 / 登录态安全边界，不定义 OAuth、SSO 或企业身份提供商方案 |
| `OwnerRef` | 表达资源 owner、creator 和生成时间 | 所有个人业务对象都应可追溯到 owner 或创建者 |
| `RoleAssignment` | 表达用户被赋予的最小角色 | MVP 至少区分普通用户与管理员 / 内容维护者；不设计组织角色树 |
| `RoleScope` | 表达角色作用范围 | 范围限定为个人工作台资源或维护者负责的公共参考材料 / 基础配置 |
| `PermissionBoundary` | 表达允许动作摘要和限制原因 | 冻结资源可见性、操作边界和 enforcement 位置；endpoint schema 交给 `API_SPEC.md` / F5 |
| `AuditActor` | 表达动作主体 | 记录用户、系统任务或维护者动作的角色快照 |
| `AuditTarget` | 表达动作目标 | 记录资源类型、资源标识、版本和 owner 引用 |
| `AuditEvent` | 表达关键动作审计 | 只定义最小审计边界，不写日志字段全集或物理存储结构 |

求职者 / 面试准备用户可以访问和维护自己的个人工作台数据，包括简历、岗位、绑定关系、会话、报告、复盘、薄弱项、训练建议、资产和用户私有知识文档。用户不得访问其他用户的个人数据。

### 5.1 登录态、session / token / cookie 模型

- MVP 默认采用后端签发、后端校验的登录态；业务 API 不接受匿名身份访问个人数据。
- 若使用 cookie 承载 session，cookie 必须设置 `HttpOnly`、`SameSite=Lax` 或更严格策略；非本地开发环境必须设置 `Secure`。
- session / token 不得存入前端可读的 `localStorage`、`sessionStorage` 或页面状态；前端只感知“已登录 / 未登录 / 会话过期”。
- session 生命周期至少包含创建、续期、过期、退出登录失效和账号禁用失效；F5 必须冻结具体 TTL。
- 登录、退出、会话过期、鉴权失败、账号禁用和异常刷新必须产生最小审计事件。
- 如果后续 API 选择 bearer token 而非 cookie，仍必须满足前端不可读长期凭据、短生命周期、服务端可撤销和日志禁止记录 token 的同等要求。

### 5.2 owner enforcement 位置

- API 边界层：每个业务请求先校验登录态，解析 `actor`、`RoleScope` 和请求目标资源标识；未登录直接拒绝。
- 应用编排层：读取简历、岗位、会话、报告、复盘、资产、薄弱项、训练建议、知识文档、trace 前，必须校验目标对象 `OwnerRef` 与当前 actor 一致，或校验维护者是否只访问公共参考材料维护范围。
- 持久化边界层：查询条件必须带 owner / scope 过滤；列表、详情、生成任务、删除、归档、复制、RAG 检索都不能先查全量再在前端过滤。
- LLM / Prompt 边界层：上下文组装前再次校验所有输入片段 owner；任何 owner 不一致、source deleted、source disabled 或 source unavailable 的片段不得进入 prompt。
- RAG 检索层：私有知识文档按 owner 过滤；公共参考材料按维护者发布状态过滤；检索结果返回前校验 source scope。
- 审计边界层：鉴权成功和失败都只记录最小 actor / target / result / risk flag，不记录正文。
- 当前仓库采用 FastAPI API 入口；如果后续引入 server action，也必须执行同等登录态校验、owner 校验和审计，不得绕过 API 边界语义。

### 5.3 ownership 规则

| 资源 | owner 规则 | 关键 enforcement |
|---|---|---|
| 简历、简历版本、识别模块 | 创建用户为 owner；版本和识别结果继承简历 owner | 详情、编辑、删除、识别、绑定岗位前校验 owner |
| 岗位、岗位版本、岗位-简历绑定 | 创建用户为 owner；绑定关系要求岗位和简历 owner 一致 | 绑定、解绑、匹配分析、删除岗位前校验双侧 owner |
| 面试记录、题目、回答、点评、报告 | 发起用户为 owner；报告继承会话 owner | 列表、详情、继续、复盘、复制、删除前校验 owner |
| 模拟面试复盘 | 关联会话 owner 为复盘 owner | 生成时只能选择 owner 本人的会话和报告 |
| 真实面试复盘 | 录入用户为 owner；所选岗位 / 简历必须同 owner | 保存、生成复盘、沉淀内容前校验 owner |
| 知识库文档 | 私有文档归创建用户；公共材料归维护者 scope | RAG 检索时私有与公共 scope 分离，禁止跨用户命中 |
| 薄弱项、训练记录、资产、资产候选 | 用户本人为 owner；候选入库需用户确认 | 读取、确认、跳过、归档、删除、回流前校验 owner |
| LLM / RAG trace、审计事件 | 继承关联业务对象 owner；系统任务记录触发 actor | 前端只返回必要状态和 trace id，不返回原始 payload |

### 5.4 鉴权失败、未登录和归档访问边界

- 未登录用户只能访问登录入口、公开静态资源和不含个人数据的健康检查；业务列表、详情、生成、复制、删除、归档、简历保存、RAG 和 LLM 调用全部拒绝。
- 未认证返回未登录语义；已登录但无 owner / scope 权限返回无权限语义；对容易泄露资源存在性的详情查询，可以统一返回不可访问或不存在语义。
- 水平越权防护以服务端 owner 过滤和二次校验为准；前端隐藏按钮不是安全控制。
- 归档资源默认只读、仅 owner 可读；归档资源不得作为新生成、训练、RAG 检索和内容沉淀的默认输入，除非用户显式恢复或选择历史引用场景。
- 下载 / 复制操作必须先校验当前用户对来源报告、复盘或可复制内容有读取权限；复制失败也要审计，不得把无权限内容放入剪贴板。
- 鉴权失败、水平越权、归档资源误用和 source unavailable 需要产生 `risk flag`，但日志不得记录正文。

## 6. 管理员 / 内容维护者最小管理边界

管理员 / 内容维护者的 MVP 边界为：

- 维护公共参考材料、基础评分口径和账号可见性配置的最小管理入口。
- 维护动作必须记录 `AuditActor`、`AuditTarget`、`AuditEvent` 和风险标记。
- 不默认拥有查看、导出、复制或修改用户个人简历、岗位、回答、报告、复盘、资产和 trace 原文的权限。
- 不成为企业组织管理员，不管理组织、团队、部门空间或资源继承。
- 公共参考材料进入 RAG 时必须有来源、版本、维护者和可用性状态。

MVP 冻结的维护范围仅包含公共参考材料的创建、编辑、归档、禁用、恢复、版本说明和发布状态维护，以及必要的基础评分口径维护。维护者不得用该角色查看用户个人简历、问答、报告、复盘、私有知识文档、Prompt、completion 或 provider payload。更复杂的账号可见性配置、组织级管理和审计检索台列为 Deferred。

## 7. 核心对象可见性矩阵

| 对象域 | 普通用户 | 管理员 / 内容维护者 | 系统任务 / 后端编排 |
|---|---|---|---|
| 个人简历、岗位、绑定关系 | 仅访问本人 owner 数据 | 默认不可查看正文；支持最小配置或审计入口待决策 | 可在 owner 授权的业务链路内读取必要版本 |
| 模拟面试会话、题目、回答、点评 | 仅访问本人会话 | 默认不可查看正文 | 可为生成、评分、复盘和恢复读取必要片段 |
| 面试报告、复盘、薄弱项、训练建议 | 仅访问本人结果 | 默认不可查看正文 | 可按业务链路生成、校验、标记低置信度 |
| 资产和资产候选 | 仅访问本人资产；候选需确认 | 默认不可查看正文 | 可生成候选，不得绕过确认写入正式资产 |
| 用户私有知识文档 | 仅 owner 可见 | 默认不可查看正文 | 可按 owner 业务请求参与 RAG |
| 公共参考材料 | 可按产品授权被检索或引用摘要 | 可维护来源、版本和可用性 | 可参与 RAG，但必须保留来源和证据引用 |
| LLM trace / usage / validation | 默认只见业务结果、状态、低置信度和必要错误引用 | 仅可见公共材料维护相关 trace 摘要，不可见用户正文 | 可保存最小追踪、usage、validation 和 failure |
| AuditEvent | 可见本人关键动作摘要和安全失败提示 | 可见维护范围内公共材料动作和安全事件摘要 | 必须记录关键动作最小审计 |

## 8. 简历 Markdown 输入与文件处理边界

### 8.1 MVP 支持范围

- MVP 简历输入只支持用户在 Markdown 编辑器 / 抽屉中粘贴或手动编辑 Markdown 文本。
- PDF、可解析 PDF、docx、图片 OCR、压缩包、HTML、富文本、远程 URL 抓取、剪贴板批量解析外部材料、多文件批量导入和文件上传解析链路均为 Deferred / Non-goal；MVP 不出现 PDF 上传入口。
- Markdown 文本长度上限、空内容、过短内容和格式不可读的校验规则由 F5 冻结，但不得放宽为文件上传解析链路，且必须有测试覆盖。
- 岗位 / JD 不支持外部文件解析生成；岗位仍按 PRD / UX 冻结为用户手动录入。

### 8.2 文本校验、Markdown 安全和识别失败

- 服务端必须校验 Markdown 文本长度、空内容、过短内容、编码边界和业务必填字段；超出限制或不可读时拒绝并返回可恢复错误。
- Markdown 视为不可信用户输入：前端预览必须禁用脚本、危险 HTML 和不必要的远程资源；展示前清洗 HTML / script 注入风险。
- 服务端只保存用户确认后的 Markdown / text 内容、`ResumeVersion` 和系统识别出的 `ResumeModule` / 识别文本，不保存文件名、MIME、文件大小或原始文件二进制。
- 系统不得跟随 Markdown 中的远程链接抓取外部资源，不得调用 shell 或外部文件转换器处理简历输入。
- 模块识别失败不创建资产候选；可保留失败审计和错误分类，但不得记录简历正文。

### 8.3 原文、识别文本和删除绑定

- MVP 没有上传临时文件、对象存储对象、原始文件下载或文件解析 worker；持久化的是用户确认后的简历 Markdown / text 原文、`ResumeVersion` 和系统识别出的 `ResumeModule` / 识别文本。
- Markdown 保存结果必须绑定当前登录用户和新建或更新的简历资产；不得创建无 owner 简历。
- 删除简历时，当前简历原文、识别文本、模块识别结果、岗位绑定和后续 active 检索全部失效；历史报告和复盘通过 `source_deleted` 标记来源，不再读取当前简历正文。
- Markdown 预览、模块重新识别、复制简历文本和删除简历都必须先校验简历 owner；管理员 / 内容维护者默认不可预览或下载用户简历原文。
- 若未来支持文件导入或原始文件下载，必须先进入 Deferred 项补齐导入 / 导出物鉴权、审计、保留、恶意文件处理和用户设备责任边界。

## 9. LLM 输入最小化、后端隔离与输出校验边界

- 前端不得直接访问模型、provider key、模型调用凭据、原始 Prompt、provider-specific request / response payload 或原始模型输出。
- LLM 输入由后端应用编排层和 LLM / Prompt 边界层按最小必要原则组装。
- 不应把无关简历、岗位、回答、反馈、资产、知识文档、第三方信息、隐私字段、tokens、secrets 或其他用户数据送入模型。
- Prompt 输入最小化、上下文裁剪、敏感字段排除、低置信度和 validation 要求由本文冻结安全边界，具体模板组织交给 `PROMPT_SPEC.md`。
- LLM 原始输出不能直接成为前端或业务事实源。
- LLM 输出必须经过结构化校验和业务语义校验后，才能进入报告、复盘、薄弱项、训练建议或资产候选。
- 低置信度、冲突、不完整和失败结果必须进入状态和风险标记。

本文不展开 Prompt 模板、模型调用参数、provider-specific payload、retry / fallback 策略或模型选型细节。

### 9.1 允许和禁止进入 Prompt 的数据

| 类别 | MVP 规则 |
|---|---|
| 允许 | 当前 owner 的必要简历片段、岗位片段、会话问答、报告 / 复盘摘要、薄弱项、训练上下文、用户确认资产、当前请求相关的私有 RAG 文档片段、已发布公共参考材料片段 |
| 条件允许 | 真实面试逐字稿、第三方反馈、公司材料、历史快照、低置信度来源；必须裁剪、标记来源、只用于当前任务，并在结果中体现可信度 / 完整度 |
| 禁止 | session、token、cookie、API key、环境变量、provider payload、用户账号凭据、无关用户数据、已删除 / 禁用 / 不可访问正文、文件二进制、日志、错误堆栈、原始 embedding 向量 |
| 默认不保存 | 原始 Prompt、原始 completion、provider-specific request / response payload；MVP 只保存结构化业务结果、validation、usage、失败分类、来源引用和 `TraceRef` |

### 9.2 LLM 安全闭环

1. 用户输入：前端收集当前页面允许的文本、选择项或复制动作，不收集 token、密钥或无关页面状态。
2. 服务端校验：API 边界完成登录态、owner、资源状态、大小、格式和业务必填校验。
3. 上下文组装：应用编排层只读取当前 owner、当前任务必要的版本 / 快照 / RAG evidence，过滤 source deleted / disabled / unavailable。
4. LLM 调用：LLM 边界层将系统指令、用户内容和 RAG 内容分区处理；用户内容和 RAG 内容均视为不可信数据，不得覆盖系统安全规则。
5. 响应处理：原始 completion 先做结构化校验、业务语义校验、敏感信息扫描和低置信度标记。
6. 持久化：仅保存结构化结果、`LlmValidationResult`、`LlmUsageRecord`、失败分类和来源引用；默认不保存原始 Prompt / completion。
7. 展示 / 下载 / 删除：前端只展示可展示结果、风险提示和必要错误引用；MVP 不生成下载文件；删除源对象后新生成链路不可再读取被删除正文。

### 9.3 provider 数据使用边界、失败和幻觉风险

- provider 必须通过后端受控配置调用；provider key 不进入前端、日志、Prompt 或 trace。
- MVP 应优先选择 API 数据默认不用于训练的 provider / 配置；正式供应商协议、数据驻留和企业 DPA 为 Deferred。
- 超时、失败、限流和重试不得扩大上下文范围，不得为了重试记录原始 Prompt / completion 到日志。
- 降级时只能返回失败、部分可用、低置信度或重试提示；不得用未校验 completion 填充评分或复盘。
- hallucination 风险通过证据引用、评分规则版本、低置信度、用户校对、不可承诺精确预测和结构化 validation 控制；评分、复盘和训练建议不得伪装成确定事实。

## 10. RAG / Knowledge Base 来源治理与证据边界

- `KnowledgeBase` 是后端逻辑检索边界，不是用户可见一级模块，也不新增一级导航。
- `KnowledgeDocument` 必须记录来源、版本、owner 或维护者、状态和更新时间。
- `KnowledgeChunk` / `RetrievalEvidence` 必须可追踪到知识文档、chunk、来源版本和命中摘要。
- 用户私有知识文档只能服务 owner 的业务链路；公共参考材料必须有维护者边界和可用性状态。
- RAG evidence 进入业务结果时，必须保留 `EvidenceRef` / `SourceRef` / `VersionRef` / `SnapshotRef` / `TraceRef`。
- RAG 证据不足、来源冲突、低可信或 source unavailable 时，必须进入低置信度、风险标记或部分可用状态。
- RAG 证据摘要的前端展示范围应避免泄露无关个人数据、第三方敏感信息和不应展示的原始材料片段。

本文不展开向量数据库选型、embedding 模型选型、索引实现、外部文件导入 / 导出能力。

### 10.1 RAG 安全闭环

1. RAG 文档：创建或更新时记录 owner / 维护者、来源、版本、状态、可见范围和创建 / 编辑 actor。
2. 识别 / 切分：只处理允许的文本来源；失败不创建可检索 chunk，不把原文写入日志。
3. embedding：embedding / vector index 只保存外部引用、chunk id、owner / scope、状态和更新时间；不把向量或原文写入日志。
4. 检索：每次检索必须带 owner / public scope 过滤；私有文档和公共材料混用时保留来源边界和展示规则。
5. prompt 注入：检索片段作为不可信证据放入上下文，不能覆盖系统指令；高风险片段触发低置信度或拒绝进入上下文。
6. 删除 / 重建 / 失效：删除或禁用文档后，chunk、embedding 引用和检索索引立即标记 invalid；后续检索排除；后台重建或清理失败时保持不可检索。

### 10.2 RAG 风险控制

- prompt injection：RAG 文档中的指令、脚本、密钥样式文本和“忽略前文”类内容只作为材料，不作为系统指令。
- RAG context injection：上下文组装层应限制片段长度、来源数量和字段范围，禁止把整份私有文档无裁剪注入。
- 知识库污染：公共参考材料必须由维护者发布；私有文档只影响 owner；低可信、来源不明或冲突材料不得静默进入高置信结果。
- 跨用户检索污染：检索 query、index metadata 和结果返回都必须带 owner / public scope；测试必须覆盖用户 A 无法命中用户 B 文档。
- embedding 敏感信息：embedding 可能泄露语义信息，按敏感派生数据处理；删除源文档时必须同步失效 embedding 引用。

## 11. LLM trace、usage、validation、retention、redaction 保存边界

| 对象 | 保存边界 | 不保存 / 待决策边界 |
|---|---|---|
| `LlmRequestTrace` | 调用场景、关联业务对象、来源引用、版本 / 快照引用、RAG 组装引用、请求时间、调用方、provider、model family、状态 | 不保存 Prompt 模板、模型参数、provider-specific payload、token、secrets 或完整原始输入 |
| `LlmResponseTrace` | request trace、结构化输出引用、validation 引用、失败状态 | MVP 默认不保存原始 completion；如 F5 为排障保留片段，必须先脱敏、限期、禁止前端可见 |
| `LlmUsageRecord` | token、cost、latency、provider、model family 等统计边界 | 不锁定具体供应商实现，不暴露密钥 |
| `LlmValidationResult` | 结构化校验、业务语义校验、低置信度、冲突、不完整、失败 | 不定义具体阈值、评分公式或 Prompt 规则 |
| `LlmRetentionPolicyRef` | 记录适用策略引用和状态 | MVP 采用“业务结果随源对象生命周期、原始 payload 默认不落库”的策略；精确天数在 F5 配置化 |
| `LlmRedactionRef` | 记录脱敏策略引用、字段范围和状态 | 至少覆盖账号、联系方式、token、secrets、第三方个人信息和公司敏感片段 |
| `LlmFailureRecord` | request trace、失败阶段、错误分类、可重试性、影响对象、时间 | 不保存失败 request / response body；retry / fallback 不能扩大数据范围 |
| `TraceRef` | 为报告、复盘、评分、薄弱项、训练建议、资产候选和审计提供过程引用 | 不暴露 provider payload、Prompt 模板或密钥 |

## 12. 日志、审计、错误追踪和风控事件最小记录

最小审计事件应覆盖：

- `actor`：用户、管理员 / 内容维护者、系统任务。
- `action`：登录 / 权限、数据查看、创建、编辑、删除、复制、生成、确认、拒绝、修正、跳过、回流、资产入库、管理员维护动作。
- `target`：目标对象、目标版本、owner 引用。
- `timestamp`：动作发生时间。
- `source`：Web UI、API、系统任务、LLM / RAG 链路或维护入口。
- `result`：成功、失败、部分成功、禁用、低置信度、冲突、不完整。
- `risk flag`：低置信度、敏感字段、第三方信息、source unavailable、权限异常、复制动作、删除 / 归档动作。
- `trace reference`：必要时关联 `TraceRef`、`UserConfirmationRef`、`VersionRef` 或 `SnapshotRef`。

必须审计的操作：

- 登录、退出、session 过期、账号禁用、鉴权失败、水平越权拦截。
- 简历、岗位、绑定关系、会话、报告、复盘、薄弱项、训练记录、资产、知识文档的创建、编辑、删除、归档、禁用、恢复。
- Markdown 保存、模块识别失败、文本长度拒绝、危险 HTML / script 风险拒绝。
- LLM / RAG 生成、validation failed、generation failed、RAG source unavailable、embedding / index invalidation。
- 报告复制、复盘内容复制、复制失败、复制无权限。
- 内容沉淀确认、拒绝、修正、跳过、资产入库、回流失败。
- 管理员 / 内容维护者对公共参考材料和基础评分口径的维护动作。

禁止进入日志的内容：

- 简历正文、识别文本、岗位全文、面试回答、真实面试逐字稿、报告正文、复盘正文、资产正文、私有知识文档正文。
- 原始 Prompt、原始 completion、provider-specific payload、embedding 向量、RAG chunk 原文。
- session、token、cookie、API key、provider key、环境变量、数据库 DSN、密码、验证码。
- 完整 request / response body、未经脱敏的异常堆栈。

必须脱敏或最小化的内容：

- 邮箱、手机号、姓名、IP、User-Agent、公司名、岗位名、第三方面试官或外部反馈来源。
- target id、trace id、source id 可以记录，但不得组合成能还原正文的长文本。
- 错误日志只记录错误分类、失败阶段、状态码、trace id、owner / actor 脱敏引用和是否可重试。

MVP 日志保留原则：

- 审计事件保留以支撑 F7 验收和 MVP 运行排障为目标，建议 30-180 天；具体天数由 F5 配置冻结。
- Debug / error logs 保留应短于审计事件，建议 7-30 天；不得因延长保留而写入正文。
- 用户可见审计历史只展示本人关键动作摘要；管理员 / 内容维护者只看维护范围和安全事件摘要。
- 本文不写完整日志平台、监控平台、SIEM 方案或物理存储结构。

## 13. 数据脱敏、retention、deletion、导出与归档语义

- 简历、岗位、回答、报告、复盘、资产、知识文档、RAG 证据和 LLM trace 都可能包含敏感信息。
- MVP 采用最小脱敏原则：前端、日志、trace、RAG evidence 和审计记录只展示完成任务所需的最小摘要。
- 历史报告、复盘、评分结果和资产候选需要稳定回看，应通过 `VersionRef` / `SnapshotRef` 引用生成时来源。
- 删除 / 归档 / 禁用源对象后，历史结果不应静默改写结论；应通过 `source_available`、`source_archived`、`source_deleted`、`source_disabled` 或 `source_unavailable` 表达来源当前可用性。
- 对第三方敏感信息、公司敏感材料和过度个人信息的脱敏规则，应在后续安全实现中细化。

### 13.1 语义定义

| 语义 | MVP 定义 | 访问 / 生成边界 |
|---|---|---|
| 删除 | 用户主动移除 active 资源；默认先 soft delete，再按策略清理派生索引和临时文件 | 列表和新生成不可见；历史结果展示 `source_deleted` |
| 归档 | 资源不再参与默认列表、生成、训练或 RAG，但 owner 可在历史 / 归档视图只读查看 | 归档资源默认不可作为新生成输入 |
| 禁用 | 系统或维护者因风险阻断资源使用 | owner 可见风险状态；生成、复制、RAG 使用被阻断 |
| 导出 | 生成外部文件或批量文件 | MVP 非目标；Markdown / PDF / docx / 批量导出 Deferred |
| 复制 | 页面内把授权范围内的 `CopyableContent` 写入剪贴板 | 需要 owner 权限和复制审计；用户设备副本超出系统控制 |
| 历史快照保留 | 为历史报告、评分、复盘稳定回看保留生成时版本 / 快照引用 | 不静默重算；源删除后标记来源状态 |
| soft delete | 设置删除状态、隐藏 active 读取、保留必要审计和历史引用 | MVP 默认删除语义 |
| hard delete | 物理清除正文、派生文本和索引 | Deferred；MVP 替代控制是 soft delete + active 读取失效 + 日志脱敏 |
| backup 删除边界 | 已进入备份的数据无法保证实时删除 | MVP 需告知现实边界；备份按周期覆盖 / 过期，不用于 active 恢复除非安全审批 |

### 13.2 关联数据处理

| 触发 | MVP 处理 |
|---|---|
| 删除简历 | 简历原文、识别文本和模块 active 读取失效；岗位绑定失效或标记 source_deleted；新匹配、模拟面试、复盘和 RAG 上下文不得再读取该简历；历史报告 / 复盘保留生成时 `VersionRef` / `SnapshotRef` 并展示 `source_deleted` |
| 删除岗位 | 岗位 active 读取失效；岗位-简历绑定失效；关联面试记录、报告、复盘和薄弱项保留历史引用并展示 `source_deleted`；不能再用该岗位发起新会话或生成训练 |
| 删除知识库文档 | `KnowledgeDocument`、chunk、embedding / vector index 标记 invalid；检索立即排除；后台清理或重建失败时保持不可检索；历史 evidence 展示 `source_deleted` |
| 删除面试记录 | 会话、题目、回答、点评、会话报告和仅由该会话生成的模拟复盘 active 读取失效；关联评分、薄弱项、训练建议、资产候选标记 source_deleted 或要求用户确认是否保留已确认资产 |
| 删除复盘 | 复盘正文、复盘评分、由该复盘直接生成且未确认的薄弱项 / 训练建议 / 资产候选失效；已确认资产保留但来源状态变为 `source_deleted` |
| 删除资产 | 当前资产和版本 active 读取失效；后续生成不得读取；历史结果只显示来源不可用，不恢复资产正文 |
| 归档资产 / 薄弱项 / 训练记录 | owner 可只读查看；默认不参与训练、内容沉淀或新会话输入；恢复前不得进入 LLM / RAG |

### 13.3 复制、下载和用户设备责任边界

- MVP 支持页面复制报告 / 复盘授权内容，不支持 Markdown / PDF / docx / 批量导出。
- 复制前必须校验 owner、来源状态和内容可复制范围；复制空内容、低置信度内容或部分可用内容时需要明确状态。
- 复制动作必须审计 actor、target、范围摘要、result、timestamp 和 risk flag；不得记录复制正文。
- 复制成功后，剪贴板、聊天工具、邮件、用户本地文件和第三方软件中的副本不再受系统删除控制；产品提示和用户责任边界需在 UX / F7 中验证。
- Markdown 下载属于 Deferred：替代控制是页面复制；剩余风险是用户手动保存外部副本不可控；后续若实现必须补齐文件生成、下载鉴权、水印 / 元数据、审计、保留和删除边界。

## 14. 报告复制与文件导出 non-goal

- MVP 支持页面复制报告内容。
- 报告复制不是文件导出。
- `CopyableContent` 只表示页面复制所需的结构化内容边界，不是导出物、不是下载文件、不是批量产物。
- MVP 不支持 Markdown / PDF / docx / 批量导出。
- 本文件不得新增任何文件导出能力。
- 复制行为需要最小事件记录，至少审计复制主体、目标报告 / 复盘、复制范围摘要、时间、结果和必要风险标记；不得记录复制正文。

## 15. 真实面试复盘敏感信息、来源可信度和完整度

- 真实面试复盘来源于用户录入的外部真实面试经历。
- 系统不能假设拥有完整真实面试过程。
- 用户可能输入第三方面试官信息、公司信息、真实问题、回答回忆、结果状态、面试反馈、补充材料和主观判断。
- `RealInterviewInput` / `RealInterviewEvidence` 需要记录输入来源、可信度、完整度和用户确认状态。
- 第三方敏感信息、过度个人信息、公司敏感材料和可能不应输入 / 粘贴的外部材料，应作为安全隐私重点风险。
- 材料过短、来源不明、用户回忆不完整、第三方反馈不可验证时，复盘结果应标记低置信度、不完整或需要用户确认。
- 真实面试复盘不得承诺对真实面试结果的准确预测。

## 16. 用户确认、内容沉淀、资产入库和回流审计

以下动作必须保留最小确认和审计边界：

- `UserConfirmationRef`：确认、拒绝、修正、跳过、回流确认和资产入库确认。
- 内容沉淀确认：用户确认是否将报告、复盘、薄弱项中的可复用内容沉淀到资产库、薄弱项、训练建议或后续模拟面试输入。
- 资产入库确认：`AssetCandidate` 不得绕过确认成为正式 `Asset` / `AssetVersion`。
- 资产候选拒绝 / 修正：拒绝或修正都应保留来源和动作结果。
- 薄弱项确认：系统识别的弱项不得静默覆盖用户既有弱项。
- 训练建议确认或跳过：建议可确认、跳过或后续处理，不等同于强制训练任务。
- 回流确认：系统不得静默覆盖资产、薄弱项、训练建议或下一次模拟面试输入。

确认记录至少保存 actor、目标对象、来源引用、确认动作、编辑后摘要、目标级状态、失败原因、timestamp 和 trace reference。用户可见历史展示摘要，不展示被删除来源正文。

## 17. 低置信度、冲突、不完整和失败状态的安全表达

| 状态 | 安全表达边界 |
|---|---|
| `low_confidence` | 告知资料不足、证据不足或模型判断不稳定，不伪装为确定结论 |
| `conflict` | 标记来源冲突、评分解释冲突或证据冲突，提示需要用户校对或后续处理 |
| `incomplete` | 标记材料不完整、模型输出不完整或 RAG 证据不足 |
| `validation_failed` | 结构化校验或业务语义校验失败，不进入正常业务事实 |
| `generation_failed` | 生成失败时保留用户输入和可用部分，不提前展示完成态 |
| `source_unavailable` | 来源被删除、禁用、归档、不可访问或缺少版本快照时，展示来源可用性状态 |

安全表达不得误导用户，不得把低置信度结果伪装成高置信结果，不得承诺精确通过概率或真实面试结果预测。风险提示、可信度说明和免责声明边界需要记录；具体展示文案交给 UX / API / F7 验收细化。

## 18. 密钥、provider、模型调用凭据和后端隔离

- provider key 不进入前端。
- 模型调用凭据只在后端受控边界内使用。
- provider、model family、usage 可以记录统计边界，但不得暴露密钥。
- 前端只接收通过后端校验后的业务结果、状态、风险提示和必要错误引用。
- `.env.example` 只允许占位符或 fake 值；真实密钥、真实密码、真实 token、真实 DSN 不得进入仓库。
- 启动日志、错误日志、审计日志和 trace 不得输出环境变量值、provider key、cookie secret 或数据库凭据。
- F5 必须提供最小 secret 注入方式、最小访问权限和泄露后废弃 / 轮换流程；企业级 KMS、自动轮换平台和正式泄露演练为 Deferred。
- 本文不写具体云服务、密钥平台或部署 secret 选型。

## 19. MVP 威胁模型

| 威胁 | 影响对象 | 触发路径 | MVP 控制 | 剩余风险 | Deferred |
|---|---|---|---|---|---|
| 未授权访问 | 全部个人工作台数据 | 未登录直接访问业务 API / 页面状态复用 | API 边界登录态校验；未登录业务请求拒绝；前端只展示状态 | 静态资源仍公开 | 否 |
| 水平越权 | 简历、岗位、会话、报告、复盘、资产、知识文档 | 修改 URL id、请求体 id、列表查询参数 | 持久化查询 owner 过滤；应用层二次 owner 校验；失败审计 | 复合资源遗漏 owner 校验 | 否 |
| session 泄漏 | 账号和所有业务资源 | cookie / token 被窃取或日志泄漏 | `HttpOnly`、`Secure`、`SameSite`、短 TTL、退出失效、日志禁止 token | 终端被控无法完全防护 | 否 |
| prompt injection | LLM 结果、评分、复盘、训练建议 | 用户输入或 RAG 片段要求模型忽略规则 | 系统指令与资料分区；用户 / RAG 内容不可信；结构化 validation | 模型仍可能受诱导 | 否 |
| RAG 污染 | 公共参考材料、检索证据、结果可信度 | 维护者误录、低可信文档、恶意私有材料 | 公共材料发布状态；来源 / 版本 / 维护者；低置信度和冲突标记 | 公共材料质量需人工治理 | 否 |
| 跨用户检索污染 | 私有知识文档、embedding、RAG evidence | 检索未带 owner 或 index metadata 错配 | owner / public scope 过滤；删除失效；测试覆盖用户隔离 | 向量库实现错误 | 否 |
| LLM provider 数据外传 | Prompt 上下文、真实面试材料、简历 | 调用外部 provider | 最小必要上下文；禁止 secrets；选择默认不训练的 API 配置 | 供应商协议和数据驻留未企业化 | 是 |
| 敏感日志泄漏 | 简历、Prompt、completion、token、secrets | request body、异常堆栈、debug log | 日志禁止正文和 payload；错误分类化；脱敏 actor / target | 第三方日志平台配置错误 | 否 |
| Markdown 输入攻击 | 简历输入、Markdown 预览 | 超长文本、脚本 Markdown、危险 HTML、远程资源引用 | 长度限制；Markdown 渲染禁危险 HTML / script；不抓取远程资源；日志不存正文 | Markdown 渲染器漏洞 | 否 |
| 简历模块识别风险 | 简历原文、识别文本、模块识别 | 识别失败、错误识别、恶意内容 | 识别失败不落资产候选；用户预览确认；日志不存正文 | 识别质量影响结果 | 否 |
| 数据删除不彻底 | 源正文、快照、embedding、备份 | soft delete、历史回看、备份延迟 | active 读取失效；source_deleted；embedding invalid；备份周期边界说明 | hard delete 和备份即时删除未实现 | 是 |
| 下载 / 复制数据外流 | 报告、复盘、可复制内容 | 用户复制到外部工具或本地文件 | 复制前鉴权；复制审计；MVP 不生成下载文件 | 用户设备外流不可控 | 否 |
| API 滥用 | LLM 调用、简历保存、登录 | 高频请求、暴力尝试、成本消耗 | 按 actor / IP / endpoint / LLM 场景做最小 rate limit 和失败审计 | 高级 WAF / bot 防护未实现 | 是 |
| rate limit 缺失 | provider 成本、可用性、登录安全 | F5 未实现限流 | F5 DoD 必测限流；无 rate limit 不可进入 F7 | 精细配额策略后置 | 是 |
| CSRF | cookie 登录态下的写操作 | 第三方页面诱导浏览器提交请求 | `SameSite` cookie；状态变更请求校验 CSRF token 或同等机制 | 复杂跨域场景后置 | 否 |
| XSS | 前端页面、Markdown 预览、复制内容 | 恶意 Markdown / 模型输出含脚本 | React 默认转义；Markdown 禁危险 HTML / script；输出展示前清洗 | 第三方组件漏洞 | 否 |
| SSRF | 后端网络、metadata service | URL 导入、远程资源抓取 | MVP 不支持 URL 抓取和远程文件导入；禁跟随外部链接抓取 | 未来 URL 导入需重评 | 是 |
| SQL injection | 持久化层 | 拼接查询条件、搜索参数 | ORM / 参数化查询；禁止字符串拼接 SQL | 手写 SQL 需审查 | 否 |
| command injection | 未来文件导入、运维脚本 | 拼接 shell 命令处理用户文件 | MVP 无文件上传解析链路且不调用 shell 处理简历输入 | 未来引入外部转换器需沙箱 | 是 |
| 环境变量泄漏 | `.env`、启动日志、错误日志 | 示例文件、异常输出、前端构建注入 | `.env.example` fake-only；日志禁止 env value；前端不得注入 provider key | 运维误配置 | 否 |
| provider key 泄漏 | LLM 供应商账号、调用成本 | 前端包、日志、trace、Prompt | 后端读取；不进前端、不进日志、不进 Prompt；泄漏后废弃 / 轮换 | 自动轮换平台后置 | 是 |

## 20. 验证 checklist / Definition of Done

F5 / F7 至少需要覆盖以下验收项，未通过时不得宣称安全隐私闭环完成：

- 鉴权测试：未登录访问业务 API、生成、复制、删除、简历保存、RAG / LLM 调用均被拒绝。
- owner 隔离测试：用户 A 不能读取、搜索、生成、复制、删除用户 B 的简历、岗位、会话、报告、复盘、资产、知识文档和 trace。
- 未登录访问测试：业务页面状态和 API 不返回个人数据；会话过期后重新请求失败。
- 水平越权测试：修改 URL id、请求体 id、列表过滤 id、RAG document id、复制 target id 均不能越权。
- Markdown 输入安全测试：空内容、过短内容、超长文本、危险 HTML / script、远程资源引用、恶意 Markdown 和模块识别失败路径均有拒绝或安全降级；MVP 不出现 PDF 上传或文件选择器入口。
- 删除级联测试：删除简历、岗位、面试记录、复盘、资产后，active 列表、详情、生成、训练和复制均不可读取已删除正文，历史结果展示来源状态。
- RAG 删除失效测试：删除 / 禁用知识文档后，chunk、embedding / vector index 立即不可检索，后台重建失败时仍不可检索。
- prompt 不含禁止字段检查：Prompt 组装测试断言不含 session、token、cookie、API key、环境变量、无关用户数据、已删除正文和日志正文。
- 日志不含敏感字段检查：应用日志、错误日志、审计日志、LLM failure、模块识别失败日志不含简历正文、Prompt、completion、provider payload、token、secrets。
- secrets 不进前端、不进日志检查：前端构建产物、API 响应、启动日志、错误日志、trace 均不包含 provider key、cookie secret、数据库凭据或真实 DSN。
- Markdown 复制权限检查：复制按钮仅对有 owner 权限且来源可读的报告 / 复盘可用；复制事件审计不记录正文；MVP 不出现 Markdown 下载入口。
- 归档资源访问边界检查：归档资源 owner 可只读查看，但默认不参与新生成、训练、RAG 检索或内容沉淀；无权限用户不可见。
- LLM / RAG failure 检查：超时、失败、validation failed、source unavailable、低置信度路径不展示完成态，不保存原始 payload 到日志。
- rate limit 检查：登录、简历保存、LLM 生成、RAG 检索至少有 MVP 级限流或调用频次保护。
- CSRF / XSS / SQL injection / command injection 基线检查：cookie 写操作有 CSRF 或同等控制；Markdown / completion 展示清洗；持久化查询参数化；MVP 无文件解析 shell 调用。

## 21. 与 API_SPEC.md、DATA_MODEL.md、PROMPT_SPEC.md 的交接边界

`API_SPEC.md`、`DATA_MODEL.md`、`PROMPT_SPEC.md` 当前均已存在并作为 F4 active draft 承接对应边界。本文继续冻结安全隐私语义和 enforcement 要求；endpoint、schema、Prompt 模板、模型参数、物理 DB schema 和实现方案仍由对应文档及后续阶段承接。本文不关闭 SECURITY_PRIVACY 自身 Deferred / UNKNOWN。

| 交接对象 | 本文交接内容 | 本文不展开内容 |
|---|---|---|
| `API_SPEC.md` | 承接 API resource boundary、candidate / confirmation、status、error、async / retry / idempotency、response envelope、复制和回流失败语义 | 不定义 endpoint、path、method 或完整 request / response schema |
| `DATA_MODEL.md` | 承接 `CandidateRef`、`SuggestionRef`、`UserConfirmationRef`、`AiTaskResultRef`、`EvidenceRef`、`TraceRef`、`LowConfidenceFlag`、`AuditEvent`、`RoleScope`、`PermissionBoundary` 等逻辑对象 | 不改写数据对象定义，不写物理 DB schema、ORM、DDL、migration 或索引 |
| `PROMPT_SPEC.md` 与 `prompt-contracts/*.md` | 承接 AI Task Contract、上下文装配、检索依赖、validation、low confidence、evidence、trace、failure handling、source unavailable 和 LLM payload 交接要求 | 不写 Prompt 模板全集，不选择 provider、模型参数、向量数据库、embedding 模型或搜索服务 |
| F5 实现 | 交接密钥管理、日志保留、脱敏实现、审计事件落库、删除策略、trace 存储和访问控制 | 不写 ORM、DDL、migration 或平台选型 |

### 21.1 Candidate / Confirmation 安全边界

- `CandidateRef`、`SuggestionRef`、`UserConfirmationRef` 不是敏感正文容器，只能保存最小必要引用、状态、摘要和审计关联。
- candidate / suggestion 展示必须先通过 owner / scope 校验；前端可见内容只能是授权范围内的结构化结果、证据摘要和必要 trace id。
- confirmation 记录必须审计 actor、target、action、result、timestamp、trace 和 audit event，但不得记录过量正文。
- `before_summary` / `after_summary` 应为摘要或引用，不应无条件保存简历、回答、复盘、Prompt、completion 或来源原文。
- `edit`、`merge`、`confirm`、`reject`、`manual_review`、`skip` 都应形成 `AuditEvent` 或等价审计记录。
- 回流失败不得导致未授权写入、重复写入或覆盖正式对象；失败状态应保留 trace、audit 和 rollback-safe 语义。

### 21.2 Source unavailable 与 Evidence 展示边界

- `source_unavailable`、`source_deleted`、`source_disabled` 状态下，不得重新读取来源原始正文，也不得把原始正文注入新的 LLM 上下文。
- 可展示 evidence summary 不等于原始敏感正文；需要展示时必须经过 owner / scope 校验、最小化裁剪和敏感字段排除。
- trace / evidence 可追踪不等于原文可见；`TraceRef` / `EvidenceRef` 只证明来源、版本、快照、摘要和生成链路可回溯。
- Report / Review / Asset / Training 的 `CopyableContent` 不得包含无权限来源正文、原始 Prompt、completion 或 provider payload。

### 21.3 LLM payload / trace / audit 交接边界

- API response 不得暴露原始 Prompt、completion 或 provider payload。
- 日志不得保存 provider payload、token、cookie、secrets、数据库 DSN、环境变量、request / response body 或未经脱敏的敏感正文。
- `TraceRef` / `AuditEvent` 只能保存最小必要引用、状态、错误分类、摘要和审计结果。
- Debug、failure、`validation_failed`、`low_confidence` 路径也不得落敏感正文，不得为了排障保存原始 provider payload。
- 这些边界与 `API_SPEC.md` 的 response envelope 和 `DATA_MODEL.md` 的 AI output handoff 保持一致。

## 22. Deferred / 待后续补齐项

本节只登记 SECURITY_PRIVACY 自身 Deferred 项，不关闭 PRD §10、`TECH_DESIGN.md` 或 `DATA_MODEL.md` 中的 `F4_TECH_DESIGN` UNKNOWN。

| 编号 | Deferred 项 | 本轮替代控制 | 剩余风险 | 后续补齐点 |
|---|---|---|---|---|
| SP-DEF-001 | PDF / 可解析 PDF / docx / OCR / 图片 / 压缩包 / 多文件批量简历导入 | MVP 只支持 Markdown 粘贴 / 编辑；不提供文件上传解析链路 | 用户需手动转换为 Markdown 文本，体验受限 | 若进入后续版本，补解析沙箱、恶意文件扫描、格式转换、MIME 校验和更细删除策略 |
| SP-DEF-002 | Markdown / PDF / docx / 批量导出 | MVP 仅支持页面复制并审计复制事件 | 用户手动保存外部副本不可控 | 如实现下载，补导出物鉴权、审计、水印 / 元数据、保留和删除边界 |
| SP-DEF-003 | hard delete 与备份即时删除 | MVP soft delete、active 读取失效、source_deleted、embedding invalid、日志脱敏 | 备份和历史快照中可能短期存在已删数据 | F5 / 运维设计冻结 hard delete、备份周期、恢复审批和删除证明 |
| SP-DEF-004 | 企业级身份、SSO、组织 / 团队 ACL | MVP 个人工作台 owner + 最小维护者 scope | 不支持团队协作和企业权限继承 | 企业版或后续阶段另设 ADR / 安全文档 |
| SP-DEF-005 | 企业级 KMS、自动轮换、泄露演练和 DPA | MVP 后端 secret、fake 示例、日志禁止、泄露后废弃 / 手动轮换 | 运维成熟度有限，供应商协议未冻结 | 发布前按部署环境补 secret 平台、轮换周期和 provider 协议审查 |
| SP-DEF-006 | 高级 WAF、bot 防护和细粒度配额 | MVP 最小 rate limit、失败审计、LLM 场景频次保护 | 高强度滥用下保护有限 | F7 / 发布前按流量和成本补限流参数、告警和封禁策略 |
| SP-DEF-007 | 用户自助完整审计历史和管理员审计检索台 | MVP 仅展示本人关键动作摘要和维护范围摘要 | 用户无法自助检索全部历史安全事件 | 后续 UX / API 冻结审计查询、分页、保留和导出边界 |
| SP-DEF-008 | URL 导入、远程知识抓取、外部站点解析 | MVP 不抓取 URL，不跟随上传内容中的远程链接 | 不能自动导入外部网页材料 | 若实现，补 SSRF 防护、域名 allowlist、内容净化和版权 / 来源治理 |

## 23. 变更记录

| 日期 | 变更 | 影响 |
|---|---|---|
| 2026-05-16 | 同步 API / DATA / Prompt 交接边界当前性 | 同步 `API_SPEC.md` / `DATA_MODEL.md` / `PROMPT_SPEC.md` 已创建后的安全交接口径；补 candidate / confirmation、source unavailable、trace / evidence / audit、LLM payload 边界；不关闭 UNKNOWN，不定义 endpoint、schema、Prompt 模板或实现方案 |
| 2026-05-15 | 补齐 MVP 安全隐私闭环 | 增加字段级数据分类矩阵、session / owner enforcement、简历 Markdown 输入安全、删除 / 归档 / 复制语义、LLM / RAG 安全闭环、日志脱敏、威胁模型、验证 checklist 和 Deferred 台账；仍不引入 API schema、Prompt 模板、DDL 或企业级合规扩展 |
| 2026-05-15 | 初始化 F4 安全隐私规范草案 | 建立 `AIFI-SEC-001` 的 ownership、角色权限、LLM 隔离、RAG 来源、trace、审计、脱敏、保留、复制 non-goal、真实面试敏感信息、用户确认、密钥和 UNKNOWN 边界；不关闭 `F4_TECH_DESIGN` UNKNOWN |

---
title: DOCS_INDEX
type: governance
status: active-f0
owner: 文档治理
source_report: archive/2026-05-doc-consolidation/audit/F0_AUDIT_REPORT.md
permalink: ai-for-interviewer/docs/00-governance/docs-index
---

# DOCS_INDEX

本文件是 F0 文档治理落库后的当前有效文档索引。它只登记当前已经落库并可作为 active 入口的文档；尚未创建或尚未确认的目标文档不得被当作当前执行依据。

当前 AI 模拟面试工作台级 MVP 以 active PRD / UX / TECH / DATA_MODEL / SECURITY_PRIVACY / PROMPT_SPEC / API_SPEC 文档体系为准；archive 下的 workbench-mvp 仅保留历史记录，不作为开发、验收或测试依据。

## 1. 当前有效入口

| 类型 | 路径 | 职责 |
| --- | --- | --- |
| 协作规则 | `AGENTS.md` | AI / 人工协作约束、编号规则、写入边界 |
| 文档索引 | `docs/00-governance/DOCS_INDEX.md` | 当前有效文档清单和 active / archive 边界 |
| 文档治理 | `docs/00-governance/DOCS_GOVERNANCE.md` | 文档生命周期、命名、归档、迁移和防腐规则 |
| AI 工作流 | `docs/00-governance/AI_WORKFLOW.md` | Codex / AI 读取、修改、落库和确认流程 |
| 测试策略 | `docs/00-governance/TEST_POLICY.md` | 测试临时产物治理、受管临时目录工具和测试残留检查规则 |
| 产品需求 | `docs/01-product/PRD.md` | MVP 产品需求唯一事实源 |
| 需求追踪 | `docs/01-product/REQUIREMENT_TRACEABILITY.md` | 历史需求吸收、替代、后置、缺口和待决策项 |
| F2 低保真设计 | `docs/02-design/UX_SPEC.md` | F2 低保真设计唯一 active 文档；输入来源是 `PRD.md`，UNKNOWN 输入来源是 PRD §10；正文以功能场景设计包为主体，Figma 低保真稿链接、Page 名称、Prototype 表达状态和人工接受状态登记以 `UX_SPEC.md` 为准，仓库不存储 Figma 文件本体；不替代 `PRD.md`，不包含高保真 UI、技术设计、API、数据模型或 Prompt 设计 |
| F3 设计系统草案 | `docs/02-design/UI_DESIGN_SYSTEM.md` | AIFI-UI-001 当前产物；阶段 F3；状态 DRAFT；类型 active design draft；不替代 `docs/01-product/PRD.md` 或 `docs/02-design/UX_SPEC.md`；包含 WARN / UNKNOWN / CONFLICT 台账，相关项仍需后续关闭；Figma 仅作为 F2 低保真证据来源 |
| F4 技术设计草案 | `docs/02-design/TECH_DESIGN.md` | AIFI-ARCH-001 当前产物；阶段 F4；状态 DRAFT；类型 active technical design draft；基于 `docs/01-product/PRD.md`、`docs/02-design/UX_SPEC.md` 和 `docs/02-design/UI_DESIGN_SYSTEM.md` 冻结技术架构边界；不替代 `DATA_MODEL.md`、`SECURITY_PRIVACY.md`、`API_SPEC.md` 或 `PROMPT_SPEC.md` |
| F4 数据模型草案 | `docs/02-design/DATA_MODEL.md` | AIFI-DATA-001 当前产物；阶段 F4；状态 DRAFT；类型 active technical design draft；定位为 `TECH_DESIGN.md` 下的数据模型子文档；初始化业务对象、数据对象、状态枚举、版本策略和持久化边界；不替代 `SECURITY_PRIVACY.md`、`API_SPEC.md` 或 `PROMPT_SPEC.md`；不关闭 `F4_TECH_DESIGN` UNKNOWN |
| F4 安全隐私规范草案 | `docs/02-design/SECURITY_PRIVACY.md` | AIFI-SEC-001 当前产物；阶段 F4；状态 DRAFT；类型 active technical design draft；定位为 `TECH_DESIGN.md` 下的安全隐私子文档；初始化 MVP ownership、角色权限、LLM 隔离、RAG 来源治理、trace、审计、脱敏、保留、复制 non-goal 和密钥边界；不替代 `API_SPEC.md` 或 `PROMPT_SPEC.md`；不关闭 `F4_TECH_DESIGN` UNKNOWN |
| F4 API 契约草案 | `docs/02-design/API_SPEC.md` | AIFI-API-001 当前产物；阶段 F4；状态 DRAFT；类型 active technical design draft；定位为 `TECH_DESIGN.md` 下的 API 契约子文档；当前只同步候选态、正式态、建议态、用户确认流、AI task result、response envelope 和 Weakness API handoff 草案；不定义完整 endpoint，不替代 `DATA_MODEL.md`、`PROMPT_SPEC.md` 或 `SECURITY_PRIVACY.md`；不关闭 `F4_TECH_DESIGN` UNKNOWN |
| F4 Prompt / AI 子任务 contract 草案 | `docs/02-design/PROMPT_SPEC.md` | AIFI-PROMPT-001 当前产物；阶段 F4；状态 DRAFT；类型 active technical design draft；定位为 `TECH_DESIGN.md` 下的 AI 编排与 Prompt contract 子文档；定义 AI 子任务 contract、上下文装配、检索依赖、输出 schema、校验、trace / evidence 和失败处理；不替代 `API_SPEC.md`、`DATA_MODEL.md` 或 `SECURITY_PRIVACY.md`；不作为完整提示词文案库；不关闭 `F4_TECH_DESIGN` UNKNOWN |
| F4 Prompt contract 子文档集合 | `docs/02-design/prompt-contracts/*.md` | AIFI-PROMPT-001 active 子文档集合；承载 `PROMPT_SPEC.md` 已登记 contract 的详细正文或 Stub 摘要；主 `PROMPT_SPEC.md` 是 canonical registry；子文档不得自行新增未登记 ID，不替代 `API_SPEC.md`、`DATA_MODEL.md` 或 `SECURITY_PRIVACY.md`，不关闭 `F4_TECH_DESIGN` UNKNOWN |
| F4 Prompt / 安全隐私 / 技术设计对抗性审查主报告 | `docs/02-design/reviews/F4_PROMPT_SECURITY_TECH_ADVERSARIAL_REVIEW.md` | AIFI-ARCH-003 审查证据；阶段 F4；状态 DRAFT；记录 `PROMPT_SPEC.md`、`SECURITY_PRIVACY.md`、`TECH_DESIGN.md` 和 `prompt-contracts/*.md` 的对抗性审查问题、证据和结论；不替代 `TECH_DESIGN.md`、`PROMPT_SPEC.md`、`SECURITY_PRIVACY.md` 或 `DATA_MODEL.md` |
| F4 Prompt / 安全隐私 / 技术设计风险登记表 | `docs/02-design/reviews/F4_PROMPT_SECURITY_TECH_RISK_REGISTER.md` | AIFI-ARCH-003 审查证据；阶段 F4；状态 DRAFT；登记对抗性审查发现的设计风险、严重度、影响面和处置状态；只作为风险台账，不替代 `TECH_DESIGN.md`、`PROMPT_SPEC.md`、`SECURITY_PRIVACY.md` 或 `DATA_MODEL.md` |
| F4 Prompt / 安全隐私 / 技术设计整改矩阵 | `docs/02-design/reviews/F4_PROMPT_SECURITY_TECH_REMEDIATION_MATRIX.md` | AIFI-ARCH-003 审查证据；阶段 F4；状态 DRAFT；追踪风险到整改动作、目标文档、负责人和验证方式的映射；只作为整改追踪证据，不替代 `TECH_DESIGN.md`、`PROMPT_SPEC.md`、`SECURITY_PRIVACY.md` 或 `DATA_MODEL.md` |
| F4 Prompt / 安全隐私 / 技术设计验收记录 | `docs/02-design/reviews/F4_PROMPT_SECURITY_TECH_ACCEPTANCE.md` | AIFI-ARCH-003 审查证据；阶段 F4；状态 DRAFT；记录对抗性审查的退出标准、验收证据、阻断项和最终判定；只作为审查验收证据，不替代 `TECH_DESIGN.md`、`PROMPT_SPEC.md`、`SECURITY_PRIVACY.md` 或 `DATA_MODEL.md` |
| 阶段计划 | `docs/03-delivery/DELIVERY_PLAN.md` | 唯一阶段与里程碑入口 |
| 任务入口 | `docs/03-delivery/BACKLOG.md` | 唯一任务入口 |
| 归档说明 | `archive/README.md` | archive 用途和禁止事项 |
| 归档台账 | `archive/MANIFEST.md` | 归档动作、替代路径、阻断条件和状态 |
| 文档治理决策 | `docs/04-decisions/ADR-0001-document-governance.md` | 唯一文档体系、docs/archive 边界和归档机制 |
| 交付体系决策 | `docs/04-decisions/ADR-0002-unified-delivery-system.md` | 统一阶段、里程碑、任务编号和优先级体系 |
| 高保真设计工具治理决策 | `docs/04-decisions/ADR-0003-high-fidelity-design-tooling.md` | 状态 Proposed；Use OpenDesign as a high-fidelity exploration tool；记录 OpenDesign 作为 F3 高保真探索工具的治理边界；OpenDesign 输出不作为 active docs，不替代 Figma Prototype，不作为 M3 单独通过证据 |
| AI 协作治理决策 | `docs/04-decisions/ADR-0004-ai-collaboration-governance.md` | 状态 Accepted；以 ADR-0001 和 ADR-0002 为上位依据；登记 Claude Code / Codex / ChatGPT 协作治理、Prompt Markdown、安全读取、最小审计、三轮推进和 Scope 外本地改动报告规则；ADR-0003 不作为依据；不定义产品 Prompt，不替代 F4 `PROMPT_SPEC.md` |

## 2. 当前目录边界

| 目录 | 状态 | 规则 |
| --- | --- | --- |
| `docs/00-governance/` | active | 只承载当前治理入口 |
| `docs/01-product/` | active | 当前 `PRD.md` 为产品需求唯一事实源，`REQUIREMENT_TRACEABILITY.md` 只登记历史需求处理 |
| `docs/02-design/` | active | 当前 `UX_SPEC.md`、`UI_DESIGN_SYSTEM.md`、`TECH_DESIGN.md`、`DATA_MODEL.md`、`SECURITY_PRIVACY.md`、`PROMPT_SPEC.md` 和 `API_SPEC.md` 已登记为 active 设计文档；`docs/02-design/reviews/*` 仅作为已登记 F4 设计审查证据，不替代设计事实源；未创建或未登记的后续设计文档不得作为执行依据 |
| `docs/03-delivery/` | active | 当前仅 `DELIVERY_PLAN.md`、`BACKLOG.md` 生效 |
| `docs/04-decisions/` | active | 只承载已确认长期决策 ADR |
| `archive/` | archive-only | 只作历史来源、证据和台账，不作执行依据 |

## 3. 编号规则

| 类型 | 允许值 |
| --- | --- |
| 阶段 | `F0` 至 `F8` |
| 里程碑 | `M0` 至 `M8` |
| 任务 | `AIFI-*` |
| 优先级 | `MUST`、`SHOULD`、`COULD`、`LATER` |

## 4. 历史来源规则

- 历史产品内容只允许通过 `docs/01-product/REQUIREMENT_TRACEABILITY.md` 追踪。
- 历史文档和归档动作只允许通过 `archive/MANIFEST.md` 登记。
- `archive/` 下任何文档不得被列为当前需求、设计、阶段或任务执行依据。
- 若历史内容仍有效，必须迁入 active docs 后才能参与后续交付。

## 5. 目标文档生效条件

新增或更新设计、测试、发布或 ADR 文档时，必须同时满足：

1. 有明确所属阶段、任务或决策来源。
2. 已登记到本索引或对应目录索引。
3. 未绕过 `DELIVERY_PLAN.md`、`BACKLOG.md`、`REQUIREMENT_TRACEABILITY.md` 和 `archive/MANIFEST.md` 的职责边界。
4. 未新建并行阶段体系、任务体系或临时计划入口。

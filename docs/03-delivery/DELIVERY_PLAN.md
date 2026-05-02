---
title: DELIVERY_PLAN
type: delivery-plan
status: active-f1
owner: 项目交付
source_report: archive/2026-05-doc-consolidation/audit/F0_AUDIT_REPORT.md
permalink: ai-for-interviewer/docs/03-delivery/delivery-plan
---

# DELIVERY_PLAN

本文件是唯一阶段与里程碑入口。阶段只使用 `F0` 至 `F8`；里程碑只使用 `M0` 至 `M8`。旧推进体系不得作为 active 阶段或任务编号继续使用。

## 1. 阶段与里程碑

| 阶段 | 里程碑 | 目标 | 主要产物 | 退出标准 |
|---|---|---|---|---|
| F0 文档治理与需求继承审计 | M0 文档体系收敛完成 | 清理文档事实源、归档旧入口、建立唯一治理文档体系 | `DOCS_INDEX.md`、`DOCS_GOVERNANCE.md`、`AI_WORKFLOW.md`、`archive/MANIFEST.md`、ADR | active docs 只保留目标体系；旧入口已归档登记；archive 不作为执行依据；旧阶段体系不再作为 active 体系 |
| F1 产品需求冻结 | M1 MVP 需求冻结 | 建立唯一 PRD，迁入历史有效需求，冻结角色、范围、主流程和非目标 | `docs/01-product/PRD.md`、`docs/01-product/REQUIREMENT_TRACEABILITY.md`、Backlog 更新 | `PRD.md` 已创建；历史有效需求已全部处理；`REQUIREMENT_TRACEABILITY.md` 无未分类高风险项；`BACKLOG.md` 已包含 F2-F8 的任务入口；active docs 中不存在旧阶段体系 |
| F2 低保真设计 | M2 低保真评审通过 | 完成页面流、信息架构、关键状态、错误态 | `docs/02-design/UX_SPEC.md` | 覆盖主链路、异常态、权限态、训练入口；不引入未冻结范围 |
| F3 高保真设计与设计系统 | M3 高保真评审通过 | 固化视觉风格、组件、页面规范 | `docs/02-design/UI_DESIGN_SYSTEM.md`、高保真交付物索引 | 视觉风格与历史有效原则一致；页面可进入前端实现 |
| F4 技术架构、接口、数据、Prompt 设计 | M4 技术设计评审通过 | 冻结技术边界、API、数据模型、Prompt、隐私安全 | `TECH_DESIGN.md`、`API_SPEC.md`、`DATA_MODEL.md`、`PROMPT_SPEC.md`、`SECURITY_PRIVACY.md`、ADR | API contract first；数据状态机闭环；Prompt 证据链和题目生成规则明确 |
| F5 后端开发 | M5 后端主链路完成 | 实现服务端保存、面试编排、RAG/LLM、评分复盘、导出基础能力 | 后端代码、迁移脚本、接口测试 | 后端主链路可被前端/测试调用；错误态和审计记录可追溯 |
| F6 前端开发 | M6 前端主链路完成 | 实现工作台、发起、面试台、复盘、训练入口、基础管理 | 前端代码、页面测试 | 用户可完成端到端主链路；关键空态/错态可用 |
| F7 联调、测试与质量加固 | M7 全链路测试通过 | 完成 E2E、API、数据、权限、降级、回归测试 | `TEST_PLAN.md` 更新、测试报告、缺陷清单 | 全链路通过；MUST 缺陷清零；SHOULD 缺陷有明确豁免 |
| F8 发布、复盘与下一轮迭代 | M8 MVP 可发布 | 完成发布检查、变更记录、运行手册、复盘 | `RELEASE_CHECKLIST.md`、`CHANGELOG.md`、复盘 ADR/Issue | 发布阻塞项清零；后续迭代项进入 Backlog |

## 2. 执行规则

1. 所有任务必须进入 `docs/03-delivery/BACKLOG.md`。
2. 所有阶段必须进入本文件。
3. 所有产品需求必须进入 `docs/01-product/PRD.md`。
4. 所有历史需求处理必须进入 `docs/01-product/REQUIREMENT_TRACEABILITY.md`。
5. 所有归档动作必须进入 `archive/MANIFEST.md`。
6. 所有重大治理或架构决策必须进入 `docs/04-decisions/ADR-*.md`。
7. archive 只作为历史来源；不能作为执行依据。
8. 禁止生成 `plan-v2`、`latest-plan`、`new-roadmap`、`codex-plan` 等临时路线图文件。

## 3. 当前完成状态

| 阶段 | 状态 | 证据 |
|---|---|---|
| F0 | DONE | active docs 已收敛到目标体系；旧入口已迁入 archive 并登记到 `archive/MANIFEST.md` |
| F1 | DONE | `PRD.md` 已创建；历史有效需求已在 `REQUIREMENT_TRACEABILITY.md` 中分类处理；后续任务入口已进入 `BACKLOG.md` |
| F2 | NOT_STARTED | 待基于 PRD 编写 `UX_SPEC.md` |
| F3 | NOT_STARTED | 待 F2 评审后编写 `UI_DESIGN_SYSTEM.md` |
| F4 | NOT_STARTED | 待 F1/F2 输入稳定后编写技术、API、数据、Prompt、安全隐私设计 |
| F5 | NOT_STARTED | 等待 F4 评审 |
| F6 | NOT_STARTED | 等待 F5 主接口 |
| F7 | NOT_STARTED | 等待 F5/F6 联调 |
| F8 | NOT_STARTED | 等待 F7 全链路通过 |

## 4. F2 准入条件

F2 开始前必须满足：

1. F1 产物已 staged。
2. `docs/01-product/PRD.md` 作为唯一产品需求事实源。
3. `docs/01-product/REQUIREMENT_TRACEABILITY.md` 中无未分类高风险历史需求。
4. F2 任务从 `docs/03-delivery/BACKLOG.md` 的 `AIFI-UX-001` 开始。
5. 不创建新的路线图、阶段体系或任务体系。

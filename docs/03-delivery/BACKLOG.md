---
title: BACKLOG
type: delivery-backlog
status: active-f1
owner: 项目交付
source_report: archive/2026-05-doc-consolidation/audit/F0_AUDIT_REPORT.md
permalink: ai-for-interviewer/docs/03-delivery/backlog
---

# BACKLOG

本文件是唯一任务入口。所有任务必须使用 `AIFI-*` 编号；优先级只使用 `MUST`、`SHOULD`、`COULD`、`LATER`；阶段只引用 `F0` 至 `F8`。

## 1. Backlog

| 任务 ID | 阶段 | 里程碑 | 优先级 | 标题 | 范围 | 产物 | 依赖 | 状态 |
|---|---|---|---|---|---|---|---|---|
| AIFI-DOC-001 | F0 | M0 | MUST | 建立目标文档索引 | 新建/改写 `DOCS_INDEX.md`，登记唯一有效文档体系 | `docs/00-governance/DOCS_INDEX.md` | F0 审计 | DONE |
| AIFI-DOC-002 | F0 | M0 | MUST | 合并归档台账 | 新建 `archive/MANIFEST.md`，合并旧归档索引与台账 | `archive/MANIFEST.md` | `DOCS_INDEX.md` | DONE |
| AIFI-DOC-003 | F0 | M0 | MUST | 废弃旧 active 入口 | 将旧 planning/task/module/state 文档迁入 archive 并登记替代路径 | README、AGENTS、`archive/MANIFEST.md` | F0.1 归档 | DONE |
| AIFI-DOC-004 | F0 | M0 | MUST | 清理重复模板文档 | 旧模板和旧治理文档转为历史来源 | `archive/2026-05-doc-consolidation/legacy/` | F0.1 归档 | DONE |
| AIFI-PROD-001 | F1 | M1 | MUST | 编写并冻结 MVP PRD | 建立唯一产品需求事实源，覆盖产品定位、目标、角色、流程和非目标 | `docs/01-product/PRD.md` | AIFI-DOC-001 | DONE |
| AIFI-PROD-002 | F1 | M1 | MUST | 完成历史需求继承处理 | 将历史有效需求标记为 MERGED_TO_PRD / DEFERRED / REJECTED / UNKNOWN | `docs/01-product/REQUIREMENT_TRACEABILITY.md` | AIFI-PROD-001 | DONE |
| AIFI-PROD-003 | F1 | M1 | MUST | 定义 MVP 用户角色与权限边界 | 冻结练习者、管理员/内容维护者、项目维护者和单工作区边界 | `docs/01-product/PRD.md` §3、§12 | AIFI-PROD-001 | DONE |
| AIFI-PROD-004 | F1 | M1 | MUST | 定义核心面试主流程 | 冻结岗位、简历、参考材料、考点规划、问题生成、面试执行和历史回看 | `docs/01-product/PRD.md` §4、§6-§8 | AIFI-PROD-001 | DONE |
| AIFI-PROD-005 | F1 | M1 | MUST | 定义评分、通过概率、弱项训练需求 | 冻结可解释评分、通过概率、复盘报告和弱项训练闭环 | `docs/01-product/PRD.md` §9-§11 | AIFI-PROD-001 | DONE |
| AIFI-PROD-006 | F1 | M1 | MUST | 定义 MVP 非目标范围 | 冻结多团队、多租户、语音、视频、ATS、商业化、高级治理等后置范围 | `docs/01-product/PRD.md` §13-§14 | AIFI-PROD-001 | DONE |
| AIFI-UX-001 | F2 | M2 | MUST | 准备 F2 低保真设计输入 | 基于 PRD 编写低保真 UX 规范，覆盖主流程、页面 IA、状态和错误态 | `docs/02-design/UX_SPEC.md` | F1 完成 | NOT_STARTED |
| AIFI-UI-001 | F3 | M3 | MUST | 编写 UI 设计系统 | 迁移有效视觉原则，补组件、页面规范和设计 token | `docs/02-design/UI_DESIGN_SYSTEM.md` | F2 评审 | NOT_STARTED |
| AIFI-ARCH-001 | F4 | M4 | MUST | 准备 F4 技术设计输入 | 基于 PRD 和当前仓库事实冻结技术架构、服务边界和工程约束 | `docs/02-design/TECH_DESIGN.md`、ADR | F1/F2 | NOT_STARTED |
| AIFI-API-001 | F4 | M4 | MUST | 编写 API 契约 | 汇总岗位、简历、面试、复盘、导出、训练、权限 API | `docs/02-design/API_SPEC.md` | AIFI-ARCH-001 | NOT_STARTED |
| AIFI-DATA-001 | F4 | M4 | MUST | 编写数据模型 | 汇总核心实体、状态机、审计字段、迁移策略 | `docs/02-design/DATA_MODEL.md` | AIFI-PROD-003 | NOT_STARTED |
| AIFI-PROMPT-001 | F4 | M4 | MUST | 编写 Prompt 规范 | 写入参考材料包、考点规划、问题生成、追问、评分解释和低置信度规则 | `docs/02-design/PROMPT_SPEC.md` | AIFI-PROD-004 | NOT_STARTED |
| AIFI-SEC-001 | F4 | M4 | MUST | 编写安全隐私规范 | 权限、数据可见性、审计、脱敏、保留周期、导出边界 | `docs/02-design/SECURITY_PRIVACY.md` | AIFI-PROD-003 | NOT_STARTED |
| AIFI-BE-001 | F5 | M5 | MUST | 完成后端主链路 | 服务端保存、面试编排、RAG/LLM、评分复盘、导出基础能力 | 后端实现、API 测试 | F4 评审通过 | NOT_STARTED |
| AIFI-FE-001 | F6 | M6 | MUST | 完成前端主链路 | 工作台、发起、面试台、复盘、训练入口、基础管理 | 前端实现、页面测试 | F5 主接口可用 | NOT_STARTED |
| AIFI-QA-001 | F7 | M7 | MUST | 完成全链路测试 | API、E2E、权限、降级、数据持久化、导出测试 | `docs/03-delivery/TEST_PLAN.md`、测试报告 | F5/F6 | NOT_STARTED |
| AIFI-REL-001 | F8 | M8 | MUST | 完成发布检查 | 发布清单、变更记录、已知问题、回滚策略 | `docs/03-delivery/RELEASE_CHECKLIST.md`、`CHANGELOG.md` | F7 全链路通过 | NOT_STARTED |

## 2. 优先级定义

| 优先级 | 定义 |
|---|---|
| MUST | 没有它不能发布 |
| SHOULD | 首版强相关，但不阻塞 MVP |
| COULD | 体验增强 |
| LATER | 后续迭代 |

## 3. 旧任务迁移规则

1. 旧任务包只作为历史来源或归档证据，不得直接作为当前任务入口。
2. 每个仍有效的旧任务必须映射到一个 `AIFI-*` 任务。
3. 无法证明仍有效的旧任务标记为 `UNKNOWN`，待核查后再进入 Backlog。
4. 模块级待办不得绕过本文件直接执行。

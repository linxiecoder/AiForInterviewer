---
title: FEEDBACK_LOOP_RELEASE_RUNBOOK
type: release-runbook
status: active-f8
owner: 发布与质量
source_task: AIFI-REL-009
permalink: ai-for-interviewer/docs/03-implementation/feedback-loop-release-runbook
---

# FEEDBACK_LOOP_RELEASE_RUNBOOK

本文档是 feedback-loop（反馈闭环）Step12 / AIFI-REL-009 的 release runbook（发布运行手册）边界稿。它只定义人工审查清单和决策口径，不包含真实部署命令、真实环境变量、脚本、迁移、配置或回滚执行步骤。

## 1. 使用边界

| 项 | 规则 |
|---|---|
| 可使用场景 | 后续 release review（发布审查）或 rollback readiness review（回滚准备审查） |
| 不可使用场景 | 直接生产发布、直接灰度、直接回滚、直接降级、直接变更配置或依赖 |
| 执行前提 | 必须有新的明确授权、环境 owner（负责人）确认、最新测试证据和生产变更窗口 |
| 本文档状态 | draft-ready for review（可供审查的草稿），not executable（不可直接执行） |

## 2. Default-Off（默认关闭）边界

- 当前不命名真实 feature flag（功能开关）或环境变量。
- 后续如需要 default-off，必须在新的授权窗口中补充：
  - owner（负责人）。
  - 生效范围。
  - 观测指标。
  - 验证方式。
  - rollback owner（回滚负责人）。
- 未补齐前，不允许把 feedback-loop 标记为 production release-ready（生产可发布）。

## 3. Gray（灰度）边界

| 检查项 | 要求 |
|---|---|
| 灰度范围 | 本轮不定义真实用户、比例、租户或环境。 |
| 灰度入口 | 必须由后续 release review 显式批准。 |
| 灰度监控 | 至少覆盖 API error rate（接口错误率）、feedback generation failure（反馈生成失败）、session detail visibility（会话详情可见性）、frontend console errors（前端控制台错误）。 |
| 灰度退出 | 任一 blocker（阻断项）触发时停止继续扩大范围；本轮不写执行命令。 |

## 4. Rollback Checklist（回滚清单）

| 步骤 | 检查项 | 当前状态 |
|---|---|---|
| RB-01 | 确认触发原因：生产错误、用户阻断、数据兼容风险或安全风险 | 待后续 release review |
| RB-02 | 确认影响范围：API、web、数据读写、LLM provider（大模型供应商）或前端展示 | 待后续 release review |
| RB-03 | 确认安全投影仍生效，不暴露 `provider_payload`、raw prompt（原始提示词）或敏感字段 | Step11 证据 PASS，但生产前需复核 |
| RB-04 | 确认可以恢复到上一稳定行为或关闭入口 | 当前只登记门槛，不执行 |
| RB-05 | 记录证据：命令、时间、owner、影响面、用户可见结果 | 待后续变更窗口 |
| RB-06 | 回滚后验证：session detail、feedback card、next action、refresh recovery | 待后续 release review |

## 5. Degradation Checklist（降级清单）

| 步骤 | 检查项 | 当前状态 |
|---|---|---|
| DG-01 | feedback 生成失败时是否 fail-closed（失败关闭） | Step3 / Step11 证据支持 |
| DG-02 | pending / partial / generation_failed 是否可安全展示 | Step11 证据支持 |
| DG-03 | signed action（签名动作）是否仍区分 trusted / untrusted（可信 / 不可信） | Step11 enhanced QA 支持 |
| DG-04 | 无法生成下一题时是否不声称算法已完成 | C-054 仍 Deferred |
| DG-05 | 降级后是否保留人工可解释提示 | 待 release review 人工确认 |

## 6. Restore（恢复）边界

- 恢复前必须重新跑最新 QA evidence（质量证据）矩阵。
- 恢复前必须确认 known risks（已知风险）没有扩大。
- 恢复前必须确认 C-049 到 C-054 未被静默关闭。
- 恢复动作必须在新授权窗口中执行；本文档不提供命令。

## 7. Stop Conditions（停止条件）

出现以下任一情况，必须停止 release / rollback / degradation 执行并回到 active docs / BACKLOG 重新授权：

- 需要修改 `apps/**`、`tests/**`、migration、config、dependency 或 deployment script（部署脚本）。
- 需要命名真实环境变量或功能开关。
- 需要关闭 C-049 到 C-054。
- 需要把 `.omo/plans/**`、`archive/**` 或 `_bmad-output/**` 升级为 active docs。
- 需要声明 production release-ready。

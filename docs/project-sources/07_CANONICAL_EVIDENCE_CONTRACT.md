---
title: 07_CANONICAL_EVIDENCE_CONTRACT
type: note
permalink: ai-for-interviewer/docs/project-sources/07-canonical-evidence-contract
---

# 07 Canonical Evidence Contract

## Purpose

CanonicalEvidencePack 是出题 Agent、反馈 Agent、进展树、评分、训练闭环共享的最高优先级事实契约。

Phase 2 / Phase 3 之前，不得继续让 Question / Feedback 各自解释 evidence support 语义。

## 核心决策

### DEC-CTX-001 Evidence First

Status: confirmed

Domain Policy 迁移顺序采用：

CanonicalEvidencePack / SourceSupportSummary first -> Question Policy -> Feedback Policy

原因：

- Question / Feedback 都依赖 source support。
- 若先迁某一侧 policy，会继续形成双轨 evidence 解释。
- CanonicalEvidencePack 必须先成为统一事实入口和 source support 计算入口。

## Shape

CanonicalEvidencePack:

```yaml
schema_version:
owner_ref:
session_ref:
job_snapshot_ref:
resume_snapshot_ref:
progress_node_ref:
canonical_project_assets:
retrieved_rag_chunks:
prior_answer_refs:
prior_feedback_refs:
answer_attempt_refs:
source_support_summary:
warnings:
blocking_issues:
context_digest:
```

## source_support_summary

必须包含：

```yaml
level:
primary_evidence_refs:
adjacent_evidence_refs:
job_gap_refs:
missing_context:
reason_codes:
confidence:
policy_version:
computed_at:
```

## Source Support Levels

允许值：

- direct_project_evidence
- adjacent_project_evidence
- job_gap_only
- insufficient_context

### direct_project_evidence

定义：

有候选人项目 / 简历项目 / 已确认资产 / 历史回答等直接支撑当前能力点或题目主事实。

允许：

- 追问真实项目链路。
- 询问实现细节、职责边界、验证指标、异常处理。

禁止：

- 引入未被 evidence 支撑的技术栈或结果指标。

### adjacent_project_evidence

定义：

有相邻项目或相邻能力证据，但不足以声称候选人已完成目标能力。

允许：

- 假设性扩展。
- “如果要引入 / 如果要改造 / 你会如何设计”。

禁止：

- 声称候选人已经做过、主导过、落地过目标能力。
- 把 job requirement 改写为候选人经历。

### job_gap_only

定义：

只有岗位要求 / match gap 支撑，没有候选人项目证据。

允许：

- 能力补偿题。
- 假设设计题。
- 学习/训练路径建议。

禁止：

- 声称候选人做过相关项目。
- 追问不存在的真实实现。

### insufficient_context

定义：

既无可用项目证据，也无足够岗位/上下文支持。

允许：

- 澄清题。
- 补材料请求。
- low confidence candidate。

禁止：

- 生成事实性项目题。
- 写正式业务事实。

## Canonical Project Assets

canonical_project_assets:

```yaml
available:
selection_policy:
status_policy:
excluded_statuses:
items:
```

item:

```yaml
asset_id:
status:
asset_type:
title:
summary:
content_excerpt:
source_refs:
evidence_refs:
current_version_id:
priority:
relevance_reason:
```

规则：

- 只有 asset_confirmed 可作为 canonical evidence。
- asset_archived 只能作为历史引用，不得默认作为事实源。
- 当前回答中的新事实不能直接进入 canonical evidence。
- asset update 只能作为 candidate，必须 user_confirmation_required=true。
- asset conflict 必须进入 blocking / HITL，不得自动选择一方。

## Provider Boundary

Provider-facing payload 只能包含 compact evidence。

禁止：

- full asset body
- full resume
- full JD
- raw prompt
- system prompt
- developer prompt
- provider payload
- raw completion
- secrets
- token
- cookie

## Context Digest

context_digest 必须稳定计算，至少覆盖：

- schema_version
- owner_ref
- session_ref
- job_snapshot_ref
- resume_snapshot_ref
- progress_node_ref
- canonical_project_assets refs / digest
- source_support_summary
- blocking_issues

context_digest 用于：

- provider request idempotency
- trace comparison
- eval replay
- handoff validation

## Gap Rules

如果 GitHub 当前代码中的 canonical evidence shape 与本 contract 不一致：

- GitHub 描述当前实现。
- 本文件描述目标契约。
- 差异记录到 Refactor Traceability Matrix。
- 不得把目标契约断言为当前代码事实。

当前已知 gap：

- 代码中可能仍存在 `source_support_level` 单字段。
- 目标要求升级为 `source_support_summary`。
- reason_codes / confidence / policy_version 必须补齐。
- Question / Feedback 侧不得各自维护不同 source support 语义。

## Phase Alignment

| Phase | Scope |
|---|---|
| Phase 1 | 不迁 evidence policy，仅锁定 C0 rails |
| Phase 2 | CanonicalEvidencePack / Interview Context 统一 |
| Phase 3 | Domain Policies 使用统一 source_support_summary |
| Phase 5 | Question Agent 使用统一 evidence contract |
| Phase 6 | Feedback Agent 使用统一 evidence contract |
| Phase 9 | Eval 验证 evidence support 行为 |
---
title: Agent IO Shared Abstractions Summary
type: delivery-summary
status: draft
owner: 后端实现
permalink: ai-for-interviewer/docs/03-delivery/agent-io-shared-abstractions-summary
---

# Agent IO Shared Abstractions Summary

## 1. Summary

本轮重构完成了出题 Agent 与 Progress Tree Agent 的公共 IO 抽象收敛。目标是抽出可复用的内部边界，降低 prompt builder、evidence adapter 和 output parser 之间的重复结构；本轮不合并业务 Agent，不改变对外 API，不改变 DB，不改变前端，不改变 LangGraph / orchestration，不改变 LLM transport DTO。

当前公共抽象位于 `apps/api/app/application/llm/agent_io.py`。它只承载通用 Agent IO 数据结构和安全规则，不依赖 polish、domain、infrastructure、fake transport 或 provider DTO。

## 2. Shared abstractions

### AgentEvidenceItem

职责：

- 表示 prompt 可引用的证据摘要。
- 用于 question prompt 的 `evidence_summaries`。
- 用于 Progress Tree evidence chunk 到 agent evidence item 的映射。
- 不承载完整简历、完整 JD、完整 evidence 原文或 provider payload。

### AgentFocusTarget

职责：

- 表示当前 Agent 聚焦的能力点或节点。
- 用于 Progress Tree node 到 Question `EvidenceScope` 的稳定中间层。
- 不承载完整 progress node 原始对象。

### AgentPromptBundle

职责：

- 表示 prompt builder 内部标准包。
- 对外仍允许不同 Agent 通过 adapter 保持既有 top-level shape。
- Question prompt 对外使用 `input_data`。
- Progress prompts 对外使用 `context`。

### AgentOutputEnvelope

职责：

- 表示 LLM 输出解析后的内部 envelope。
- 不替代旧 parser 对外返回 shape。
- 出题 parser、Progress initial parser、Progress state parser 均已内部接入。

### AgentSafetyPolicy

职责：

- 表示公共安全规则来源。
- 三个 prompt builder 已引用。
- 不改变已有 prompt 返回 shape。
- 不依赖 polish、domain 或 infrastructure。

## 3. Adoption matrix

| Area | File | Uses AgentEvidenceItem | Uses AgentFocusTarget | Uses AgentPromptBundle | Uses AgentOutputEnvelope | Uses AgentSafetyPolicy |
| --- | --- | --- | --- | --- | --- | --- |
| Shared definitions | `apps/api/app/application/llm/agent_io.py` | 定义 | 定义 | 定义 | 定义 | 定义 `DEFAULT_AGENT_SAFETY_POLICY` |
| Question prompt builder | `apps/api/app/application/polish/question_generation_prompts.py` | 是，生成 `evidence_summaries` | 否 | 是，内部标准包后转回 `input_data` shape | 否 | 是，生成 prompt safety rules |
| Question parser / scope adapter | `apps/api/app/application/polish/question_generation_service.py` | 否 | 是，Progress node 到 `EvidenceScope` 中间层 | 否 | 是，`_question_payload_envelope(...)` | 否 |
| Progress prompt builder | `apps/api/app/application/polish/progress_prompts.py` | 否 | 否 | 是，内部标准包后转回 `context` shape | 否 | 是，生成 prompt safety rules |
| Progress initial parser | `apps/api/app/application/polish/progress_tree.py` | 否 | 否 | 否 | 是，`_quality_first_menu_payload_envelope(...)` | 否 |
| Progress state parser | `apps/api/app/application/polish/progress_tree.py` | 否 | 否 | 否 | 是，`_progress_tree_state_payload_envelope(...)` | 否 |
| Progress evidence adapter | `apps/api/app/application/polish/progress_evidence.py` | 是，`ProgressEvidenceChunk.to_agent_evidence_item()` | 否 | 否 | 否 | 否 |

## 4. Preserved external contracts

- Question prompt builder 返回顶层仍包含 `input_data`。
- Progress initial prompt builder 返回顶层仍包含 `context`。
- Progress state refresh prompt builder 返回顶层仍包含 `context` 和 state refresh 兼容字段。
- `_parse_llm_question_payload(...)` 对外返回仍是二元 tuple。
- `_normalize_quality_first_menu_payload(...)` 对外返回仍是 5 元 tuple 或 `None`。
- `_normalize_state(...)` 对外仍返回 state dict。
- `PolishProgressTreeLlmService.refresh_state(...)` 主流程未作为本轮重构目标改变。
- API response、DB schema、frontend、LangGraph 均未作为本轮目标改变。

## 5. Guard tests

- `tests/api/test_agent_io.py`：覆盖 `AgentEvidenceItem` prompt dict、`AgentSafetyPolicy` prompt rules / dict、`DEFAULT_AGENT_SAFETY_POLICY`、`ProgressEvidenceChunk` 到 `AgentEvidenceItem` 的映射、question prompt evidence summary 外部 shape，以及 `AgentOutputEnvelope` metadata 过滤。
- `tests/api/test_agent_io_contracts.py`：覆盖 `agent_io.py` 无业务 / transport 反向依赖、公共类型导出、三个 prompt builder 使用 `AgentPromptBundle` 与 `AgentSafetyPolicy`、三类 prompt 外部 top-level shape、三个 output parser 使用 `AgentOutputEnvelope`、旧 parser 返回 shape、`AgentSafetyPolicy` 仅限本阶段 prompt builder 使用，以及未启动未规划 Agent 抽象。
- `tests/api/test_polish_api.py`：覆盖 Progress Tree prompt / parser / API 相关回归，包括 state refresh prompt、quality-first initial prompt、parser envelope 接入和现有 API 行为。
- `tests/api/test_polish_question_refactor_phase1.py`：覆盖出题链路 Phase 1 的 prompt bundle、progress evidence 到 question evidence 的桥接、parser envelope 以及出题行为回归。

## 6. Out of scope

- 不合并出题 Agent 和 Progress Tree Agent。
- 不做 Agent runtime 大一统。
- 不修改 LLM transport DTO。
- 不修改 fake transport。
- 不修改 API schema。
- 不修改 DB。
- 不修改前端。
- 不修改 LangGraph。
- 不做 evidence refs hardening。
- 不做 output parser 彻底大统一。
- 不改 prompt 文案。
- 不新增公共抽象。

## 7. Future optional work

- 更严格的 evidence refs hardening。
- Agent prompt / output telemetry summary。
- 统一 parser result metrics。
- 更正式的 Agent contract registry。
- 更轻量的 projection DTO for frontend。
- 将私有 helper 的测试逐步收敛到更稳定的 public behavior tests。

## 8. Validation commands

```bash
PYTHONPATH=.:apps/api .venv/bin/pytest tests/api/test_agent_io.py tests/api/test_agent_io_contracts.py -q
PYTHONPATH=.:apps/api .venv/bin/pytest tests/api/test_polish_api.py -q
PYTHONPATH=.:apps/api .venv/bin/pytest tests/api/test_polish_question_refactor_phase1.py -q
git diff --check
```

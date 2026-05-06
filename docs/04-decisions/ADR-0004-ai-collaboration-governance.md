---
title: ADR-0004-ai-collaboration-governance
type: decision
status: accepted
owner: 文档治理
date: 2026-05-06
permalink: ai-for-interviewer/docs/04-decisions/adr-0004-ai-collaboration-governance
---

# ADR-0004 AI 协作治理

## 状态

Accepted

## 上位依据

- ADR-0001 文档治理唯一体系。
- ADR-0002 统一交付体系。

ADR-0003 高保真设计工具治理不作为本决策依据。

## 背景

F0/M0 文档治理要求 Claude Code、Codex、ChatGPT 或其他 AI 协作者不能依赖长 Prompt、临时计划、历史审计报告或 archive 内容替代 active docs。AI 协作规则需要进入当前治理入口，并与统一任务、阶段、里程碑和 ADR 机制保持一致。

## 决策

1. AI 协作长期规则以 `docs/00-governance/AI_WORKFLOW.md` 为入口。
2. 面向 AI 的 Prompt 必须使用可复制 Markdown，优先中文表达，并对代码块、表格、反引号、竖线、反斜杠、引号和 JSON 等内容采用安全转义或 fenced code block。
3. Claude Code / Codex / ChatGPT 执行任务前应优先自行完成最小审查，核对 task_id、允许文件、禁止文件、冲突项、完成条件和必要证据。
4. 文档治理、审计、状态判断和续接任务采用最小审计，不得为追求完整而扩大到无关文件、无关 archive 或全仓库扫描。
5. 同一问题按三轮推进：事实核查、定向修正、收口验证。第三轮后如无新 task_id、新文件范围、新 ADR、用户明确要求或允许文件实质变更，不重复全面审计。
6. Scope 外已有本地改动只报告，不阻塞当前任务；除非用户明确授权或这些改动影响允许文件判断，不得读取、修改、暂存、回滚、删除或移动。
7. 重大 AI 协作治理变更进入 ADR，并登记到 `docs/00-governance/DOCS_INDEX.md`。

## 非目标

- 本 ADR 不定义产品 Prompt、模型调用策略、RAG 输入输出或业务 LLM 评分规则。
- 本 ADR 不替代 F4 `PROMPT_SPEC.md`。
- 本 ADR 不替代 `AGENTS.md`、`docs/00-governance/DOCS_GOVERNANCE.md` 或 `docs/00-governance/AI_WORKFLOW.md`。
- 本 ADR 不创建新的 roadmap、plan-v2、latest-plan、codex-plan、`.claude/plans/*` 或并行任务体系。

## 影响

- AI 协作者的可复制 Prompt、安全读取、最小审计、三轮推进和 Scope 外改动处理规则进入 active 治理体系。
- 后续若需要调整 AI 协作治理，必须同步更新 `AI_WORKFLOW.md`；若属于长期重大决策，还必须新增或修订 ADR。
- F4 产品 Prompt 规范仍需在对应任务中独立定义，本 ADR 只约束协作治理，不约束产品生成内容。

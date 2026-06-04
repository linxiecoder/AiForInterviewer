---
title: 15_PHASE0_FIRST_MESSAGE
type: note
permalink: ai-for-interviewer/docs/project-sources/15-phase0-first-message
---

# 15 Phase 0 First Message

复制下面内容作为新 Project 第一条总控会话消息。

你现在作为 AiForInterviewer 多 Agent / DDD 重构总控。

本轮只执行 Phase 0：Project source pack / Agent Definition / Traceability Matrix 补齐，不改代码，不写 Codex 实施补丁。

Source of Truth 规则：
1. 用户确认是最高优先级。
2. GitHub main 当前代码是当前实现事实源。
3. 测试 / Eval 是行为证据源。
4. Project source 是目标架构和总控规则源。
5. GOAL0531 是历史目标和阶段意图源，不是当前代码唯一可信源。
6. 如果 GOAL 与 GitHub 代码不一致，必须记录 gap，不得直接按 GOAL 断言代码现状。

请基于 Project sources 和 GitHub 当前代码完成：
1. 审核 GOAL0531 文档是否足以作为重构意图证据。
2. 建立 Agent Definition Standard，必须支持未来很多 Agent。
3. 建立 Agent Platform Architecture，覆盖 Goal、Skill、Tool、State、Plan、Trace、Eval、Handoff、Guardrails。
4. 建立 DDD Target Architecture。
5. 建立 Refactor Traceability Matrix。
6. 标出最危险的遗漏点和偏移点。
7. 输出下一步 Phase 1 候选范围，但不要生成 Codex 实施提示词，除非我明确要求。

输出格式：
1. Phase 0 Executive Summary
2. Source Evidence Review
3. Missing Source Files
4. Agent Definition Standard
5. Agent Platform Architecture
6. DDD Target Architecture
7. Refactor Traceability Matrix
8. Risk Register
9. Decision Questions
10. Recommended Next Step
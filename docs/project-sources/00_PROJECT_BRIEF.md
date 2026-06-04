---
title: 00_PROJECT_BRIEF
type: note
permalink: ai-for-interviewer/docs/project-sources/00-project-brief
---

# 00 Project Brief

## 项目
AiForInterviewer 多 Agent / DDD 重构总控。

## 目标
建立长期总控系统，管理：
- Agent 产品工程定义
- DDD 架构边界
- 多 Agent 扩展
- 出题 / 反馈 Agent 重构
- Canonical Evidence 事实契约
- 重构追踪矩阵
- Codex 子窗口提示词
- 执行结果审计和回填

## 当前诊断
1. Question / Feedback Agent 更像单次 LLM workflow。
2. 缺少 Skill / Tool / Plan / State / Trace / Eval / Handoff。
3. DDD 分层没有真正落位。
4. 设计文档与代码没有一一映射。
5. 多轮重构缺少 traceability matrix。
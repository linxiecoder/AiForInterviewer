---
title: 01_SOURCE_OF_TRUTH_POLICY
type: note
permalink: ai-for-interviewer/docs/project-sources/01-source-of-truth-policy
---

# 01 Source of Truth Policy

## 核心原则
GOAL0531 不是唯一可信源。GitHub main 当前代码是当前实现事实源。

## 优先级
P0 用户明确确认。
P1 GitHub main 当前代码。
P2 当前测试 / Eval 结果。
P3 Project source 文档。
P4 GOAL0531。
P5 历史聊天。
P6 子窗口输出。

## 冲突处理
如果 GOAL 与 GitHub 冲突：
- GitHub 说明当前实现。
- GOAL 说明目标/历史计划。
- 差异记录为 gap。
- 不得把 GOAL 目标当成代码已完成事实。

## 每次审计必须标注来源
USER_CONFIRMED / GITHUB_CODE / TEST_RESULT / PROJECT_SOURCE / GOAL_SOURCE / INFERENCE / UNKNOWN。

## GitHub Recon 要求
任何实施窗口必须先读取目标文件、调用方、被调用方、相关测试、runtime 配置。
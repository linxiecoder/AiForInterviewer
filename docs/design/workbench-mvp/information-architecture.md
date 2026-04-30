---
title: information-architecture
type: note
permalink: ai-for-interviewer/docs/design/workbench-mvp/information-architecture
---

# Workbench MVP Information Architecture

## 1. IA 总原则

一期 IA 围绕“模拟记录列表 -> 发起模拟面试 -> 面试台 -> 评分 / 复盘详情 -> 回到模拟记录列表”的主链组织。

IA 的目标是让用户能从历史记录、岗位详情或训练上下文进入下一次模拟，并能在完成后回到记录和复盘资产中继续使用结果。

## 2. 一级导航

| 导航 | 一期职责 |
| --- | --- |
| 工作台 | 展示近期模拟、待处理复盘、训练建议和关键状态。 |
| 模拟面试 | 默认显示历史模拟记录列表，并提供发起入口。 |
| 岗位 | 管理岗位、岗位详情和从岗位发起模拟的入口。 |
| 简历 | 管理简历和与岗位 / 模拟关联的简历输入。 |
| 知识库 | 管理用户私有资料和可见的公共知识库材料。 |
| 复盘 / 评分 | 访问模拟面试复盘、真实面试复盘、评分报告和导出入口。 |
| 账号 / 权限 | 管理登录身份、权限边界和基础账号设置。 |
| 后续能力 | 只作为低干扰占位，不抢占一期主链。 |

## 3. 核心页面

| 页面 | 主要对象 | 关键动作 |
| --- | --- | --- |
| 模拟记录列表 | `InterviewSession`、`ScoreReport`、`ExportSnapshot` | 查看历史、筛选状态、发起新模拟、打开复盘。 |
| 发起模拟面试 | `Job`、`Resume`、`KnowledgeBase`、`LaunchContext`、`InterviewMode` | 选择岗位、简历、知识来源、模式和策略。 |
| 面试台 | `InterviewRound`、`InterviewTurn`、`Question`、`Answer`、`ReferencePack` | 回答问题、查看证据、处理追问、暂停或结束。 |
| 评分 / 复盘详情 | `ScoreReport`、`WeaknessItem`、`QuestionReviewItem`、`ExportSnapshot` | 查看总分、维度分、题级反馈、证据、训练建议和导出。 |
| 岗位详情 | `Job`、`Resume`、`MatchSignal`、`InterviewSession` | 查看岗位信息、关联简历、发起模拟。 |
| 知识库列表 / 详情 | `KnowledgeDocument`、`Chunk`、`IndexingJob` | 上传、解析、索引、查看状态和失败原因。 |
| 训练抽屉 | `WeaknessItem`、`TrainingTask`、`TrainingDrawerContext` | 查看薄弱项、入列训练、完成或停练。 |

## 4. 用户路径

| 路径 | 步骤 |
| --- | --- |
| 从模拟记录进入 | 打开模拟记录列表 -> 发起模拟面试 -> 选择岗位 / 简历 / 模式 -> 进入面试台 -> 完成 -> 查看复盘 -> 返回记录列表。 |
| 从岗位详情进入 | 打开岗位详情 -> 选择简历和参考资料 -> 发起模拟 -> 面试台执行 -> 复盘回写到历史记录。 |
| 从复盘继续训练 | 打开复盘详情 -> 查看薄弱项 -> 加入训练抽屉 -> 训练后更新薄弱项状态。 |
| 从真实面试材料复盘 | 上传或输入真实面试材料 -> LLM 识别问答边界 -> 用户校对低置信度项 -> 生成复盘。 |
| 从知识库补充资料 | 上传文档 -> 解析与索引 -> 发起或继续模拟时选择可用资料 -> 在面试和复盘中展示引用证据。 |

## 5. 状态流转

| 对象 | 一期状态 |
| --- | --- |
| `InterviewSession` | `draft` -> `ready` -> `in_progress` -> `paused` / `completed` -> `reviewed` -> `archived` |
| `InterviewRound` | `pending` -> `active` -> `completed` / `skipped` |
| `InterviewTurn` | `asked` -> `answered` -> `evaluated` -> `revised` |
| `KnowledgeDocument` | `uploaded` -> `parsing` -> `indexed` / `failed` -> `archived` |
| `IndexingJob` | `queued` -> `running` -> `succeeded` / `failed` |
| `WeaknessItem` | `active` -> `low_priority` / `dismissed` / `resolved` |
| `TrainingTask` | `queued` -> `active` -> `completed` / `dismissed` |
| `ScoreReport` | `pending` -> `generated` -> `revised` -> `archived` |
| `ExportSnapshot` | `generated` -> `copied` / `downloaded` |

## 6. 模块承接关系

| 模块 | IA 承接摘要 |
| --- | --- |
| M01 | 承接基础平台、配置、审计和运行边界。 |
| M02 | 承接登录、权限、用户身份和可见性边界。 |
| M03 | 承接岗位、简历、文档输入和历史记录入口关系。 |
| M04 | 承接岗位匹配、证据、评分信号和候选训练信号。 |
| M05 | 承接知识库、资产归档、RAG 资料入口和索引状态。 |
| M06 | 承接发起模拟、面试台、上下文包、问题与回答链路。 |
| M07 | 承接打磨模式、能力树、逐题评估和进度状态。 |
| M08 | 承接复盘详情、真实面试复盘、模拟复盘和导出入口。 |
| M09 | 承接薄弱项、训练抽屉和训练生命周期。 |
| M10 | 承接后台、治理、公共知识库和观测入口。 |
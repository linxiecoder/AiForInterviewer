---
title: ST13_19_DESIGN
type: note
permalink: ai-for-interviewer/docs/tasks/workbench-mvp/st13-task-packages/st13-19/st13-19-design-1
---

# ST13_19 Markdown 导出 / 复制设计说明

## 1. 文档定位

本文档定义 `ST13_19` 在 `R0-Final-04` 中的最小 Markdown export / copy 边界。它只用于推进 Markdown export 的 gate、formal window 与 implementation packet，不直接实现业务代码。

`ST13_19` 消费 `ST13_12` session、`ST13_13` score、`ST13_15` review summary 和 `ST13_20` persistence。资产归档、PDF export 和完整导出系统不进入 R0-Final-04。

## 2. 子任务目标

- 为 R0 提供基于 session / turns / score / review 的 Markdown content。
- 返回 `content`、`format`、`content_version`、`metadata`。
- metadata 至少包含 source session、generated_at 或等价字段，并可追溯到 score / review payload。
- 复用 `ST13_20` persistence，把 export payload 写入 session payload。
- 保持 validation、missing session 404 与 stable error envelope 兼容。

## 3. 范围

### 3.1 进入 R0-Final-04

- 基于 existing interview session 生成 Markdown content。
- Markdown content 至少包含 interview/session 信息、question、answer、score、review summary、weakness / improvement。
- 返回 `format=markdown` 或等价字段。
- 返回 `content_version`。
- 返回 metadata，包含 `generated_at` 或等价 trace 字段。
- export payload 可保存到 `ST13_20` session payload，不新增 full DB、ORM、migration。
- validation error、missing session 404 均映射到稳定 error envelope。

### 3.2 不进入 R0-Final-04

- PDF export。
- 完整 asset archive。
- 外部分享权限、复杂模板系统、富文本编辑器。
- full RAG evidence quality platform。
- training center。
- frontend 下载按钮或 UI。
- full DB、ORM、migration 或 repository layer。

## 4. 技术方案

- 新增最小 export service，输入为 session、turns、score payload、review payload 和必要 metadata。
- Markdown 生成必须 deterministic enough for tests，避免依赖真实外部网络。
- API route 只暴露 R0 最小 Markdown export 生成 / 读取能力，并沿用 `ST13_21` error envelope。
- 持久化只复用 `ST13_20` minimal store 的 session payload，不引入正式数据库 schema。
- export 不创建 asset archive；如后续需要归档，必须另走 `ST13_18` 或后续授权窗口。

## 5. 依赖与输入

- `ST13_12`：interview session、turns、answers、history。
- `ST13_13`：`0-100` score payload。
- `ST13_15`：review summary、weakness / improvement minimal output。
- `ST13_20`：minimal persistence 与 session payload。
- `ST13_21`：API boundary 与 stable error envelope。
- `ST13_24`：Markdown export required tests 与 DoD 输入。

## 6. 边界约束

- 本设计只授权 R0 最小 Markdown content / copy payload，不授权 PDF 或完整资产归档。
- Markdown 内容不得泄露未授权用户数据；R0 当前按 owner scoped session 复用既有隔离边界。
- 不要求真实外部网络或真实 API key 才能测试。
- 若实现需要修改 forbidden paths，应停止并回到 governance 窗口。
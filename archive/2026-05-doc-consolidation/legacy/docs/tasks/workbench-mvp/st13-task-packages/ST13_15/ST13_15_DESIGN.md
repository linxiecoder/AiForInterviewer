---
title: ST13_15_DESIGN
type: note
permalink: ai-for-interviewer/docs/tasks/workbench-mvp/st13-task-packages/st13-15/st13-15-design-1
---

# ST13_15 模拟面试复盘设计说明

## 1. 文档定位

本文档定义 `ST13_15` 在 `R0-Final-04` 中的最小模拟面试复盘边界。它只用于推进 review summary、weakness / improvement minimal output 的 gate、formal window 与 implementation packet，不直接实现业务代码。

`ST13_15` 消费 `ST13_12` main flow session、`ST13_13` score 和 `ST13_20` persistence。Markdown 导出由 `ST13_19` 承接，训练中心和完整弱点生命周期不进入 R0-Final-04。

## 2. 子任务目标

- 为 R0 提供面试结束后的最小 review summary。
- 输出主要表现、风险、建议、weakness / improvement minimal output。
- 可调用 `ST13_11` provider boundary 生成 review，也可使用 deterministic review rule。
- 复用 `ST13_20` persistence，把 review payload 写入 session payload。
- 为 `ST13_19` Markdown export 提供可消费的复盘内容。

## 3. 范围

### 3.1 进入 R0-Final-04

- 基于已完成或进行中的 interview session 生成最小复盘摘要。
- 输出 `summary`、`strengths` 或等价表现描述、`risks`、`suggestions`。
- 输出最小 weakness / improvement 列表，用于说明薄弱项和改进建议。
- 允许 provider-assisted review，但必须通过 `ST13_11` provider boundary。
- provider failure、validation error、missing session 404 均映射到稳定 error envelope。
- review payload 可保存到 `ST13_20` session payload，不新增 full DB、ORM、migration。

### 3.2 不进入 R0-Final-04

- 完整复盘中心。
- 真实面试复盘。
- training center、训练抽屉、待打磨清单、弱点累计 / 消减生命周期。
- full RAG evidence quality platform。
- asset archive、PDF export、frontend。
- full DB、ORM、migration 或 repository layer。

## 4. 技术方案

- 新增最小 review service，输入为 session、turns、answers、score payload 和必要 metadata。
- review service 输出结构化 review payload，并保留 `content_version`、`generated_at` 或等价 trace metadata。
- 若使用 provider，必须经由 `ST13_11` provider boundary，不得直接调用外部 SDK 或 HTTP client。
- API route 只暴露 R0 最小 review 触发 / 读取能力，并沿用 `ST13_21` error envelope。
- 持久化只复用 `ST13_20` minimal store 的 session payload，不引入正式数据库 schema。

## 5. 依赖与输入

- `ST13_11`：provider boundary 与 provider failure mapping。
- `ST13_12`：interview session、turns、answers、history。
- `ST13_13`：`0-100` score payload。
- `ST13_20`：minimal persistence 与 session payload。
- `ST13_21`：API boundary 与 stable error envelope。
- `ST13_24`：评分 / 复盘 / Markdown 导出的 required tests 与 DoD 输入。

## 6. 边界约束

- 本设计只授权 R0 最小模拟面试复盘，不授权完整复盘中心或训练闭环。
- weakness / improvement 只作为最小输出字段，不创建 training task、不入列训练抽屉、不实现弱点生命周期。
- 不要求真实外部网络或真实 API key 才能测试。
- 若实现需要修改 forbidden paths，应停止并回到 governance 窗口。
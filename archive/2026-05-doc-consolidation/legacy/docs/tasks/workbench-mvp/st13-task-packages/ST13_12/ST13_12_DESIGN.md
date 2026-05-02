---
title: ST13_12_DESIGN
type: note
permalink: ai-for-interviewer/docs/tasks/workbench-mvp/st13-task-packages/st13-12/st13-12-design-1
---

# ST13_12 多轮上下文 / 状态机设计说明

## 1. 文档定位

本文档定义 ST13_12 在 R0-Final-03 中的最小主链路边界。它只用于推进主链路 implementation gate、formal window 与 implementation packet，不直接实现业务代码。

ST13_12 是 R0 最小模拟面试主链路的主 window entity，承接多轮上下文、状态推进、问题与回答 turn 关系、最小追问和会话恢复边界。ST13_06 作为发起模拟面试入口输入，ST13_07 作为面试台体验输入，ST13_11 / ST13_20 / ST13_21 分别作为 provider、persistence 与 API / error envelope 依赖。

## 2. 子任务目标

- 实现 R0 最小模拟面试主链路的服务端状态推进边界。
- 通过 ST13_11 provider boundary 生成首题与最小 follow-up，不绕过 provider interface。
- 复用 ST13_20 R0 minimal persistence 保存、恢复和查询历史。
- 复用 ST13_21 API boundary 与共享 error envelope。
- 覆盖 start interview、generate first question、submit answer、next turn / minimal follow-up、save / restore / history。
- 不实现 scoring、review、Markdown export、full RAG、frontend 或完整 DB / ORM / migration。

## 3. 范围

### 3.1 进入 R0-Final-03

- `start interview`：接收最小岗位、简历、owner 与 session 元数据，创建会话。
- `generate first question`：通过 ST13_11 provider boundary 生成首题。
- `submit answer`：接收回答并写入当前 turn。
- `next turn / minimal follow-up`：基于 history 和 last_answer 生成最小追问或下一题。
- `save / restore / history`：复用 ST13_20 store，不新增完整 repository / ORM。
- `validation / 404 / error envelope`：沿用 ST13_21 error envelope，保持 request_id / code / message 的稳定表达。

### 3.2 不进入 R0-Final-03

- 评分体系、review summary、weakness / improvement、Markdown export。
- full RAG、知识库治理、引用证据链。
- full database、migration framework、ORM、repository layer。
- 前端页面、面试台 UI polish、训练中心或资产归档。

## 4. 技术方案

- 将 ST13_12 作为主链路状态机与 API 编排边界，业务实现窗口只允许写主链路直接相关的 API route、service 与测试。
- provider 调用必须经由 ST13_11 `LLMProvider.generate()`，禁止直接调用外部 SDK 或 HTTP client。
- 持久化必须复用 ST13_20 当前 R0 minimal persistence store，禁止在本窗口扩展为完整 PostgreSQL / migration / ORM。
- API 响应和错误必须兼容 ST13_21 / ST13_11 / ST13_20 已有 error envelope，不引入并行错误格式。
- deterministic provider 只能作为 test/dev 显式配置，不代表真实 provider 成功。

## 5. 依赖与输入

- ST13_11：LLM provider boundary、config、deterministic test/dev provider、provider error mapping。
- ST13_20：R0 minimal persistence boundary、owner scoped history / restore 基础。
- ST13_21：API service boundary、shared error envelope、FastAPI app wiring 基础。
- ST13_06：发起模拟面试入口语义输入。
- ST13_07：面试台交互对象与 turn 展示语义输入。
- ST13_24：R0 acceptance / DoD 验证输入；本窗口不修改 ST13_24。

## 6. 边界约束

- 本设计只授权 R0-Final-03 主链路实现，不授权 scoring / review / export。
- 主链路实现不得把 provider failure 伪装成 deterministic success。
- 主链路实现不得要求真实外部网络或真实 API key 才能测试通过。
- 主链路实现不得新增 full DB / ORM / migration。
- 若需要修改 forbidden paths，应停止并回到 governance 窗口。
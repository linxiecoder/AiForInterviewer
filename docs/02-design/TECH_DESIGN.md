---
title: TECH_DESIGN
type: design
status: draft-f4-entry
owner: 技术架构
source_task: AIFI-ARCH-001
permalink: ai-for-interviewer/docs/02-design/tech-design
---

# TECH_DESIGN

## 1. 文档状态

- 本文件是 F4 技术设计主架构锚点，用于承接 `AIFI-ARCH-001` 的后续分段设计。
- 本文件不是完整 M4 交付，不替代 `DATA_MODEL.md`、`API_SPEC.md`、`PROMPT_SPEC.md` 或 `SECURITY_PRIVACY.md`。
- 本文件仅冻结 MVP 主架构、模块边界、分层原则、运行链路和子文档输入边界。
- 本文件不关闭 `F4_TECH_DESIGN` UNKNOWN，不标记 F4 / M4 / `AIFI-ARCH-001` 完成。

## 2. F4 目标

- 基于 PRD、UX_SPEC、UI_DESIGN_SYSTEM 和交付计划，拆分 MVP 技术设计产物。
- 先在 `TECH_DESIGN.md` 中建立跨子文档一致的主架构锚点，避免数据、API、Prompt 和安全隐私分段各自发明架构。
- 在后续分段中明确数据模型、API、Prompt、LLM 边界、安全隐私、评分与状态策略。
- 为 F5 实现、F7 验收和发布前风险复核提供可追踪技术依据。

## 3. 输入来源

- `docs/01-product/PRD.md`：MVP 业务对象、核心数据流、非目标、评分/复制/通过倾向口径和 UNKNOWN 台账。
- `docs/02-design/UX_SPEC.md`：F2 低保真信息架构、核心页面场景、状态与异常路径。
- `docs/02-design/UI_DESIGN_SYSTEM.md`：F3 设计系统草案、交互状态约束和前端实现交接边界。
- `docs/03-delivery/DELIVERY_PLAN.md`：F4 / M4 目标、产物和阶段边界。
- `docs/03-delivery/BACKLOG.md`：AIFI-ARCH、AIFI-DATA、AIFI-API、AIFI-PROMPT、AIFI-SEC 后续任务入口。
- 仓库技术配置：根目录 `package.json`、`requirements.txt`、`apps/web/package.json`、`apps/web/vite.config.ts`、`apps/web/tsconfig*.json`、`apps/web/playwright.config.ts`。

## 4. 非目标

- 不在本文件中展开数据表、字段、API endpoint、Prompt 模板、安全策略或测试用例。
- 不创建 `DATA_MODEL.md`、`API_SPEC.md`、`PROMPT_SPEC.md` 或 `SECURITY_PRIVACY.md`。
- 不创建或关闭 ADR。
- 不更新 BACKLOG、DELIVERY_PLAN、DOCS_INDEX 或任何任务状态。
- 不关闭 PRD §10 中归类为 `F4_TECH_DESIGN` 的 UNKNOWN。
- MVP 不支持 PDF、Markdown、Word 或批量文件导出；报告复制是页面交互，不是文件导出。
- MVP 不支持解析外部材料并自动生成岗位 / JD。
- MVP 不承诺精确通过概率或准确预测面试结果。

## 5. 架构目标与设计原则

- 以 MVP 可交付为优先，采用当前仓库已存在的 Web + API 分层，不引入无证据的新框架、服务拆分或部署形态。
- 前端负责交互、状态呈现和用户动作收集；后端负责业务编排、持久化边界、LLM 调用和安全控制。
- 所有 LLM Prompt、模型调用参数、密钥和原始模型响应必须留在后端边界内，前端只接收可展示结果、状态和可追踪错误。
- 业务状态必须可追踪、可恢复、可解释；分数、通过倾向和低信心输出不得伪装成确定预测。
- 数据对象、API 契约、Prompt 规范和安全隐私约束必须从同一组模块边界出发。
- 项目经历属于简历模块，不升级为独立顶层业务对象或顶层数据对象。
- 资产库不是简历的别名，承担跨会话沉淀、复用和反馈回流职责。
- 报告复制是页面交互能力，不是文件导出能力。

## 6. MVP 系统上下文与架构总览

- 用户通过浏览器访问 `apps/web` 前端，完成简历、岗位 / JD、模拟面试、报告、复盘和训练建议相关交互。
- 前端通过 HTTP API 与 `apps/api` 后端交互；API 负责接收请求、校验边界输入、执行业务编排并返回状态或结果。
- 后端内部按应用编排、领域能力、LLM 边界、持久化边界和安全审计边界分层。
- LLM Provider 是外部依赖；后端通过隔离层调用，不允许 UI 直接访问模型或密钥。
- 持久化方案、数据库 schema、数据保留和部署拓扑待 `DATA_MODEL.md` 与 `SECURITY_PRIVACY.md` 明确。
- 队列、对象存储、独立 LLM 服务、服务网格和多租户部署当前没有仓库配置证据，不作为 MVP 默认架构。

## 7. 当前仓库技术栈事实

- 根目录 `package.json` 声明 Node `>=20`，workspace 为 `apps/web`。
- 根目录脚本提供 `web:dev`、`web:build`、`web:test`、`dev:api` 和 `api:dev`。
- `apps/web/package.json` 声明前端使用 React、React DOM、Ant Design、Vite、TypeScript 和 `@vitejs/plugin-react`。
- `apps/web/vite.config.ts` 使用 Vite React plugin。
- `apps/web/tsconfig.json` 启用 TypeScript strict、`react-jsx` 和 Bundler module resolution。
- `apps/web/package.json` 的测试脚本先编译到 `dist-test`，再使用 Node 内置 test runner 执行 `dist-test/interview/*.test.js`。
- `apps/web/playwright.config.ts` 使用 Playwright Chromium，并通过 `npm run build && npm run preview -- --port 4173` 启动 E2E 目标。
- 根目录 `requirements.txt` 声明 FastAPI、httpx、SQLAlchemy、psycopg、uvicorn、pytest 和 PyYAML。
- 根目录 API 脚本使用 `python3 -m uvicorn app.main:app --app-dir apps/api` 启动 FastAPI 应用。
- 当前未读取到根目录 `pyproject.toml`、根目录 `vite.config.ts` 或根目录 `tsconfig.json` 作为架构依据。

## 8. 技术栈选型与方案对比

- 方案 A：沿用当前仓库技术栈，采用 Vite + React + TypeScript + Ant Design 前端，以及 FastAPI + SQLAlchemy + psycopg 后端。
  - 推荐作为 MVP 默认方案。
  - 优点是已有配置、脚本、测试入口和依赖证据，能减少 F4 到 F5 的迁移成本。
  - 风险是部分持久化、部署、鉴权和异步任务策略仍需后续子文档补齐。
- 方案 B：切换到 Next.js、SSR 或其他前端框架。
  - 不推荐作为当前 MVP 默认方案。
  - 当前仓库没有相关配置证据，且会引入路由、构建、部署和数据获取策略重写。
- 方案 C：拆出独立 LLM 服务、队列 worker 或多服务架构。
  - 不推荐作为当前 MVP 默认方案。
  - 除非后续 API、性能或安全设计证明同步 API 编排无法满足 MVP，否则应先保持单 API 后端内的 LLM 隔离层。
- 若后续决定替换主技术栈、引入独立服务或变更 LLM Provider 抽象边界，应先评估是否需要 ADR。

## 9. 系统分层

- Web UI 层：页面、表单、报告展示、复制交互、会话状态展示和错误提示。
- Web 状态适配层：把 API 状态转换为页面 view model，不承载业务真相和 LLM 判断。
- API 边界层：请求校验、鉴权入口、错误语义、任务状态查询和响应 schema。
- 应用编排层：串联简历、岗位、会话、报告、复盘、资产沉淀、训练建议和反馈回流。
- 领域能力层：封装匹配分析、问题生成、回答打磨、压力追问、评分、弱项归因和建议生成。
- LLM / Prompt 边界层：构造模型输入、调用模型、校验结构化输出、记录 trace、处理低信心和失败结果。
- 持久化边界层：封装数据读写、状态版本、会话快照、报告结果、资产版本和审计所需记录。
- 安全与观测边界层：约束密钥、隐私字段、日志脱敏、错误追踪和发布前风险复核。

## 10. 功能模块划分

- 简历模块：保存简历主体、项目经历、能力标签和用户可复用素材。
- 岗位 / JD 模块：保存岗位目标、JD 文本、岗位约束和岗位绑定关系。
- 岗位匹配分析模块：基于简历与岗位生成匹配结果、差距解释和后续训练输入。
- 打磨模式会话模块：围绕用户回答进行追问、优化建议和可复用表达沉淀。
- 压力面模式会话模块：围绕高压追问、追问链路和压力反馈生成训练结果。
- 进展树模块：展示能力、任务、会话和训练建议之间的进展关系。
- 面试报告模块：汇总模拟面试过程、评分、解释、建议和页面复制内容。
- 面试复盘模块：承接模拟面试复盘和真实面试复盘，形成反馈与改进项。
- 薄弱项模块：沉淀、合并、更新和关闭弱项，但具体生命周期由 `DATA_MODEL.md` 明确。
- 资产库模块：沉淀可复用回答、项目表达、岗位材料和反馈结果，不等同于简历模块。
- 训练建议模块：基于匹配分析、会话、报告、复盘和薄弱项生成下一步训练建议。
- 反馈回流模块：把用户确认、复制、复盘和真实面试反馈回写到资产与训练上下文。

## 11. 模块依赖与数据流关系

- 前端只依赖 API 契约，不直接读取数据库、不直接调用 LLM、不保存业务真相。
- API 边界层调用应用编排层；应用编排层协调领域能力、LLM 边界和持久化边界。
- 简历模块和岗位 / JD 模块是匹配分析、会话生成、报告生成和训练建议的主要输入。
- 打磨模式和压力面模式会话产生回答、追问、评分、弱项和资产候选。
- 面试报告和面试复盘消费会话过程、评分结果、弱项和用户反馈。
- 资产库消费简历、会话、报告和复盘输出，并向后续匹配分析、会话和训练建议提供上下文。
- 训练建议消费匹配分析、弱项、进展树、资产库和复盘结果，不直接改写源会话记录。
- 反馈回流通过应用编排层进入资产库、弱项和训练建议，不绕过状态与版本边界。

## 12. 核心运行链路总览

- 简历与岗位链路：用户提交简历和岗位 / JD，后端保存或更新输入，形成后续分析和训练上下文。
- 匹配分析链路：后端读取简历与岗位上下文，调用领域能力和必要的 LLM 边界，返回匹配解释、差距和建议入口。
- 打磨模式链路：用户提交回答或素材，后端生成追问、打磨建议、表达优化和资产候选。
- 压力面模式链路：用户进入压力训练，后端生成追问链、压力反馈、弱项和训练建议。
- 模拟面试复盘链路：会话结束后，后端汇总过程、评分、解释、报告内容和下一步训练建议。
- 真实面试复盘链路：用户录入真实面试反馈，后端形成复盘、弱项更新、资产沉淀和训练建议。
- 报告复制链路：前端根据 API 返回的报告内容执行页面复制；后端不生成 PDF、Markdown、Word 或批量文件。
- 反馈回流链路：用户确认、修正或复盘反馈经 API 写入，影响资产、弱项和后续训练上下文。

## 13. 状态机与状态流总览

- 输入类状态：简历、岗位 / JD 和真实面试反馈应区分草稿、可用、需补充和废弃，具体枚举由 `DATA_MODEL.md` 明确。
- 任务类状态：匹配分析、报告生成、复盘生成和训练建议生成应区分待处理、处理中、成功、失败和低信心完成。
- 会话类状态：打磨模式、压力面模式和模拟面试应区分未开始、进行中、暂停、完成和异常结束。
- 报告类状态：面试报告应区分生成中、可查看、可复制、生成失败和内容需风险提示。
- 弱项类状态：薄弱项应支持新增、合并、验证中、改善中和关闭候选，关闭规则待后续数据模型确认。
- 资产类状态：资产应支持候选、已确认、已归档、被替代和禁用，版本策略待后续数据模型确认。
- LLM 输出状态：结构化输出应区分通过校验、校验失败、低信心、部分可用和不可用。
- 状态流必须能支撑 API 查询、前端展示、重试提示、审计追踪和 F7 验收。

## 14. AI / LLM 总览

- LLM 能力属于后端受控依赖，不是前端能力，也不是独立产品事实源。
- Prompt 组装、上下文裁剪、模型选择、调用参数、输出校验、重试策略和降级策略由 `PROMPT_SPEC.md` 细化。
- LLM 输入应由应用编排层按最小必要原则组装，避免把无关简历、岗位、反馈或隐私字段送入模型。
- LLM 输出必须经过结构化校验和业务语义校验后才能进入报告、复盘、弱项或资产候选。
- 低信心、冲突、不完整和模型失败结果必须以状态和风险提示进入 API 语义，不得伪装为正常高置信结果。
- 评分、通过倾向和训练建议应表达为辅助判断，不承诺精确通过概率或真实面试结果预测。
- 测试中的 LLM 行为应通过可替换 transport 或确定性替身验证，避免依赖真实模型稳定性。

## 15. 子文档输入边界

- `DATA_MODEL.md` 以本文件的模块划分、状态域和数据流为输入，定义业务对象、数据对象、状态枚举、版本策略和持久化边界。
- `API_SPEC.md` 以本文件的系统分层、核心链路和状态流为输入，定义 API 契约、错误语义、任务追踪和前后端协作边界。
- `PROMPT_SPEC.md` 以本文件的 LLM 边界、模块上下文和低信心要求为输入，定义 Prompt 输入输出、模型调用和输出校验约束。
- `SECURITY_PRIVACY.md` 以本文件的数据流、LLM 输入、资产沉淀和日志边界为输入，定义隐私字段、保留策略、密钥、权限和发布风险。
- 子文档可以细化本文件锚点，但不得绕过本文档重新定义顶层模块、前后端职责或 LLM 所属边界。

## 16. 架构风险、UNKNOWN 与补齐路径

- 评分公式、权重、阈值、校准、通过倾向表达和风险提示仍为 `F4_TECH_DESIGN` 待关闭内容。
- 数据对象、状态枚举、版本策略、资产合并、弱项生命周期和持久化 schema 待 `DATA_MODEL.md` 明确。
- API path、request / response schema、错误码、鉴权语义、异步任务语义和重试语义待 `API_SPEC.md` 明确。
- Prompt 模板、模型选择、输入裁剪、输出校验、低信心处理、重试和降级策略待 `PROMPT_SPEC.md` 明确。
- 隐私字段、日志脱敏、密钥管理、数据保留、删除策略和发布风险待 `SECURITY_PRIVACY.md` 明确。
- 部署拓扑、队列、对象存储、后台 worker、监控告警和生产数据库形态当前证据不足，默认不进入 MVP 主架构。
- `AIFI-ARCH-002` 应在子文档证据充分后统一检查 UNKNOWN 关闭状态；本文件不单独关闭 UNKNOWN。

## 17. 后续分段执行顺序

1. 基于本文档创建 `DATA_MODEL.md`，先收敛业务对象、数据对象、状态与版本边界。
2. 创建 `API_SPEC.md`，对齐页面流、任务流、错误语义和前后端契约。
3. 创建 `PROMPT_SPEC.md`，明确 LLM 输入输出、可追踪性和安全约束。
4. 创建 `SECURITY_PRIVACY.md`，补齐隐私、安全、密钥、日志和发布风险。
5. 回到 `TECH_DESIGN.md` 汇总跨文档决策，并在证据充分时关闭对应 `F4_TECH_DESIGN` UNKNOWN。

## 18. 本轮状态

- 已补齐 F4 技术设计主架构锚点。
- 未创建 `DATA_MODEL.md`、`API_SPEC.md`、`PROMPT_SPEC.md` 或 `SECURITY_PRIVACY.md`。
- 未修改 BACKLOG、DELIVERY_PLAN、DOCS_INDEX、PRD、UX_SPEC、UI_DESIGN_SYSTEM、ADR、apps、packages 或 archive。
- 未关闭任何 `F4_TECH_DESIGN` UNKNOWN。

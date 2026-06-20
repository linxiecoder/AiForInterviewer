# apps/api 局部规则

本文件只补充根目录 `AGENTS.md`。冲突时以根规则、`docs/00-governance/DOCS_INDEX.md` 和当前读取过的 active docs / 代码为准。

## 入口与运行

- ASGI 入口是 `apps/api/app/main.py`，导出 `app = create_app(settings)`。
- 本地启动走根脚本：`npm run dev` -> `scripts/dev/start.sh` -> `scripts/dev/start-api.sh` -> `scripts/dev/run_api.py`。
- 默认 API 是 `127.0.0.1:8001`，API prefix 是 `/api/v1`。
- v1 路由必须从 `apps/api/app/api/v1/__init__.py` 聚合，不要绕过聚合入口挂载临时路由。

## 分层边界

- `api/` 只做 FastAPI HTTP 适配、依赖注入、envelope 和错误映射；统一使用 `success_envelope` / `raise_api_error`。
- `application/` 承载 use case、runtime 编排、端口和 contract，不直接依赖 FastAPI、SQLAlchemy session 或 provider SDK。
- `domain/` 放实体、策略和领域错误，不依赖 FastAPI、Pydantic、SQLAlchemy 或 infrastructure。
- `infrastructure/` 放 DB、LLM、embedding、auth、observability、LangGraph runtime 等外部实现。
- `schemas/` 放 API schema；不要把 DB model 当成 response schema 暴露。
- 不新增无边界 `utils.py`；共享逻辑应落在已有分层能解释的位置。

## 持久化

- SQLAlchemy 仓储主边界在 `apps/api/app/infrastructure/db/repositories`。
- `apps/api/app/repositories` 是过渡/门面边界，新增持久化能力前先确认是否已有 infrastructure 仓储。
- 当前已有 Alembic：`alembic.ini`、`apps/api/migrations`、`scripts/db/migrate.sh`、`scripts/db/upgrade.py`。
- `Base.metadata.create_all()` 只用于隔离测试或显式初始化，不作为 dev/prod 主迁移方式。

## AI 与 LLM

- LangGraph / LangChain 具体依赖只留在 `apps/api/app/infrastructure/ai_runtime/langgraph` 或已允许测试中。
- provider 请求必须经 provider boundary 构建；不得跨边界暴露 `raw_prompt`、`raw_completion`、`provider_payload`、完整简历/JD/回答、token、secret、cookie、api_key。
- `LLM_PROVIDER=fake` 只能用于测试显式注入；生产 runtime 不允许从环境启用 fake provider。
- deterministic / replay / fake evidence 只能说明回归稳定性，不证明真实 provider 质量。

## API 契约

- 成功响应保持 envelope 形态，保留 `request_id`、`trace_id` 和明确 `resource_type`。
- candidate / suggestion 不得静默升级为 formal object；正式写入必须有确认、校验、证据和持久化交接。
- MVP 报告只支持内容复制；不要新增 PDF、Markdown、Word/docx、批量下载、OCR、对象存储解析链路。
- 评分和反馈不得承诺精确通过概率、录取概率、offer 概率或准确预测面试结果。

## 验证

- 后端改动优先跑聚焦 pytest，例如 `PYTHONPATH=.:apps/api python -m pytest tests/api/<target>.py -q`。
- API 契约、分层边界或 LLM 边界改动要扩大到相关 architecture / contract / fake boundary 测试。
- 不要声称 GitHub CI 覆盖完整后端回归；当前 workflow 主要是 eval gate。

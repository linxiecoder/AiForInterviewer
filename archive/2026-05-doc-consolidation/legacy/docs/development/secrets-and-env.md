---
title: 密钥与环境变量策略
type: guide
permalink: ai-for-interviewer/development/secrets-and-env
---

# 密钥与环境变量策略

本文档定义当前仓库的 secrets 配置边界。它只约束本地开发、测试、文档和 compose 配置，不引入业务功能、数据库 schema、migration、ORM 或前端页面改动。

## 总规则

- 所有真实密钥、真实密码、真实 token、真实 API key 和真实数据库连接串只能写入本地 `.env`。
- `.env`、`.env.local`、`.env.*.local` 和本地 secret 文件必须被 `.gitignore` 忽略。
- `.env.example` 只能包含变量名、占位符或明显 fake 值，不得包含真实 secret。
- 代码只能通过环境变量或既有 settings/config 入口读取 secret。
- `docker-compose*.yml` 只能通过 `${VAR}` 或 `env_file` 读取 secret。
- 测试只能使用 dummy/fake placeholder；需要真实 PostgreSQL 的测试必须从 `TEST_DATABASE_URL` 读取，没有该变量时 skip。
- 文档只能展示变量名、占位符和格式说明，不写真实账号、真实密码或真实 provider key。

## 本地 `.env`

开发者应在本地 `.env` 中配置真实值。该文件不提交到仓库。

必要变量：

```dotenv
DATABASE_URL=<postgresql_database_url_or_empty_for_sqlite>
TEST_DATABASE_URL=<postgresql_test_database_url_or_empty>
POSTGRES_USER=<postgres_user>
POSTGRES_PASSWORD=<postgres_password>
POSTGRES_DB=<postgres_database>
LLM_PROVIDER=<openai_or_deterministic_for_test_dev>
LLM_API_KEY=<your_llm_provider_api_key>
LLM_MODEL=<your_llm_model>
LLM_BASE_URL=<your_llm_provider_base_url_or_empty>
```

数据库 URL 格式示例只允许使用占位符：

```text
postgresql+psycopg://<user>:<password>@localhost:5432/<database>
```

## `.env.example`

`.env.example` 是模板，不是本地真实配置。它必须满足：

- 不包含真实数据库用户名、密码或连接串。
- 不包含真实 LLM provider key。
- 不包含看起来像真实 secret 的长随机值。
- 需要表达格式时使用 `<...>` 占位符。

## docker-compose

本地 PostgreSQL compose 通过本地 `.env` 读取：

```yaml
POSTGRES_USER: ${POSTGRES_USER:?Set POSTGRES_USER in .env}
POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?Set POSTGRES_PASSWORD in .env}
POSTGRES_DB: ${POSTGRES_DB:?Set POSTGRES_DB in .env}
```

不得在 compose 文件中写死 `POSTGRES_PASSWORD`、真实账号、真实密码或生产连接串。

## 测试

- API 测试默认使用 SQLite 临时文件或 dummy/fake provider。
- PostgreSQL round trip 测试只读取 `TEST_DATABASE_URL`。
- 未设置 `TEST_DATABASE_URL` 时，PG integration tests 必须 skip，不应失败。
- 测试内的 provider key 只能使用 `test-key`、`fake-key` 或 `<...>` 这类明显 fake 值。

## LLM provider

真实 provider 配置只能来自环境变量：

- `LLM_PROVIDER`
- `LLM_API_KEY`
- `LLM_MODEL`
- `LLM_TIMEOUT_SECONDS`
- `LLM_BASE_URL`

代码不得写默认真实 key；文档不得写真实 provider key。`deterministic` provider 只允许在 test/dev 显式配置中使用，不得伪装成真实 provider。

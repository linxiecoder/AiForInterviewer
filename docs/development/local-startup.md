---
title: 本地启动指导
type: guide
permalink: ai-for-interviewer/development/local-startup
---

# 本地启动指导

本文档记录当前仓库可验证的本地启动、测试和 E2E 命令。命令来源于当前 `package.json`、`apps/web/package.json`、`requirements.txt` 和后端应用入口，不替代正式部署手册。

## 环境要求

### Python

- 本地已验证解释器：`Python 3.12.3`。
- Python 依赖入口：`requirements.txt`。
- 后端正式测试必须使用 `.venv/bin/python -m pytest` 或 `.venv/bin/python -m tools.test_runner.run_tests`，不要混用系统 Python。

### Node / npm

- 前端运行基线：Node `20.19+` 或 `22.12+`。
- 仓库根目录已提供 `.nvmrc` 和 `.node-version`，当前固定为 `22.12.0`。
- 本轮已验证 Node：`v22.22.2`；已验证 npm：`10.9.7`。
- 当前前端依赖包含 Vite 7；Vite 7 要求 Node `20.19+` 或 `22.12+`。Node 18 下的 warning 不再视为可长期忽略，前端 build / test / E2E 前必须先切到满足基线的 Node。

WSL / Linux 使用 `nvm` 切换到推荐基线：

```bash
nvm install 22.12.0
nvm use 22.12.0
node -v
npm -v
```

如果本机统一使用 Node 20 LTS，也必须不低于 `20.19.0`：

```bash
nvm install 20.19.0
nvm use 20.19.0
node -v
```

Windows PowerShell 使用 nvm-windows 时执行：

```powershell
nvm install 22.12.0
nvm use 22.12.0
node -v
npm -v
```

如果 Windows / WSL 中 `node -v` 仍显示 `v18.x`，先停止前端 build / test / E2E，完成 Node 切换后再继续。

### WSL2 / Windows / PyCharm

- 当前仓库在 Linux/WSL 路径下运行命令。Windows PyCharm 中如出现 unresolved reference，优先检查项目根目录、解释器和 source root，而不是修改 import。
- 后端代码位于 `apps/api/app`。运行 uvicorn 时需要带 `--app-dir apps/api`，否则 `app.main:app` 可能无法被正确解析。
- PyCharm 解释器建议指向仓库内 `.venv/bin/python`；Windows 原生环境可按等价路径选择 `.venv\Scripts\python.exe`。

## 密钥与本地环境变量

所有真实密钥、数据库密码、provider key、token 和真实数据库连接串只能写入本地 `.env`。仓库中的代码、测试、文档、`docker-compose*.yml`、README 和 `.env.example` 只允许出现变量名、占位符或明显 fake 值。完整规则见 [密钥与环境变量策略](secrets-and-env.md)。

## 后端启动

Linux / WSL 创建并激活虚拟环境：

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows PowerShell 创建并激活虚拟环境：

```powershell
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
```

安装依赖：

```bash
python -m pip install -r requirements.txt
```

从占位模板创建本地 `.env`，再按本机环境替换占位值。真实密钥、真实密码和真实数据库连接串只允许保存在 `.env`，不得写入 `.env.example`、文档、测试或日志。

```bash
cp .env.example .env
```

启动后端 API：

```bash
npm run api:dev
```

等价的直接命令：

```bash
.venv/bin/python -m uvicorn app.main:app --app-dir apps/api --host 127.0.0.1 --port 8001
```

默认 API prefix 为 `/api/v1`。启动后会执行幂等 schema bootstrap，并打印 API base URL、Swagger UI URL 和 OpenAPI JSON URL。`AUTO_MIGRATE_ON_STARTUP=false` 可关闭启动时 schema bootstrap；本地开发默认保持开启，生产环境建议显式控制。

未设置 `DATABASE_URL` 时，后端使用 SQLite fallback。默认 SQLite 路径由 `API_DATABASE_PATH` 控制；未设置时，后端使用系统临时目录下的 `ai-for-interviewer/api.sqlite3`。

指定本地数据库文件可在 shell 环境中设置 `API_DATABASE_PATH` 后启动：

```bash
API_DATABASE_PATH=<local_sqlite_file_path> .venv/bin/python -m uvicorn app.main:app --app-dir apps/api --host 127.0.0.1 --port 8001
```

### PostgreSQL runtime

R1 数据层已支持 `DATABASE_URL`。当 `DATABASE_URL` 非空时，后端优先使用 PostgreSQL 或显式数据库 URL；未设置时继续使用 `API_DATABASE_PATH` 对应的 SQLite fallback。

当前唯一 PostgreSQL driver 是 `psycopg[binary]`，由 `requirements.txt` 安装。`postgresql://...` 会在运行时归一化为 `postgresql+psycopg://...`，也可以直接写 `postgresql+psycopg://...`。

推荐本地开发使用仓库提供的最小 PostgreSQL compose 文件：

```bash
docker compose -f docker-compose.pg.yml up -d
```

上述 compose 只用于本地开发，并强制从本地 `.env` 读取 `POSTGRES_USER`、`POSTGRES_PASSWORD`、`POSTGRES_DB` 和 `POSTGRES_PORT`。如果本机已安装 WSL 原生 PostgreSQL，也可以跳过 Docker Compose，直接在 `.env` 中配置本机 `DATABASE_URL`。

本机如已有 PostgreSQL，可在本地 `.env` 配置 `DATABASE_URL` 后直接启动后端；命令行中不要粘贴真实连接串。连接串格式为：

```bash
postgresql+psycopg://<user>:<password>@localhost:<port>/<database>
```

后端启动日志只会打印数据库类型、host、port、db 名称和 schema bootstrap 开关，不会打印密码或完整 DSN。

后端 targeted API 测试：

```bash
.venv/bin/python -m tools.test_runner.run_tests --pytest-args tests/api/test_traceability_integration.py tests/api/test_traceability_persistence.py tests/api/test_rag_foundation.py tests/api/test_rag_persistence.py tests/api/test_review_export.py -q
```

PostgreSQL integration tests 默认不连接数据库；设置 `TEST_DATABASE_URL` 后手动启用：

```bash
TEST_DATABASE_URL=<postgresql_test_database_url> .venv/bin/python -m tools.test_runner.run_tests --pytest-args tests/api/test_postgresql_runtime.py -q
```

其中 `<postgresql_test_database_url>` 的格式为 `postgresql+psycopg://<user>:<password>@localhost:<port>/<test_database>`，真实值只写入本地 `.env`。

## 前端启动

### 开发步骤

安装 npm workspace 依赖：

```bash
npm install
```

启动 Web dev server，并自动打开本地页面：

```bash
npm --workspace apps/web run dev
```

根目录等价入口：

```bash
npm run web:dev
```

启动后默认打开根路径 `/`，当前根路径是 R1 工作台首页，展示主操作入口、一级导航、可信能力摘要、风险空态，并通过 `/api/v1/interviews?owner_id=<owner>` 读取最近模拟记录。当前 `/interviews` 已接入 history contract，展示 score / review / export 摘要并可进入 `/interviews/:sessionId` 可信详情；`/reviews` 复用 history contract 展示最近复盘入口。`/jobs`、`/resumes`、`/interviews/new` 仍是 R1 工作台真实入口的最小页面。旧 W10 mock 原型不再作为默认首页，可通过 `/legacy-mock` 或 `/mock` 手动访问。

当前 `apps/web/vite.config.ts` 没有配置 API proxy。R1 首页和可信 trace 页面使用相对路径 `/api/v1/interviews`、`/api/v1/interviews/:sessionId` 读取后端；本地真实联调需要同源反向代理、后续 Vite proxy，或通过 E2E mock 验证页面能力。

### 测试步骤

前端 build：

```bash
npm --workspace apps/web run build
```

根目录等价入口：

```bash
npm run web:build
```

前端单测：

```bash
npm --workspace apps/web run test
```

根目录等价入口：

```bash
npm run web:test
```

首次运行或浏览器缺失时安装 Playwright Chromium：

```bash
npm --workspace apps/web exec -- playwright install chromium
```

运行 E2E：

```bash
npm --workspace apps/web run e2e
```

当前 E2E 配置位于 `apps/web/playwright.config.ts`，测试位于 `apps/web/e2e/trusted-trace.spec.ts`。Playwright 会执行 `npm run build && npm run preview -- --port 4173` 并访问 `http://127.0.0.1:4173`。E2E 覆盖根路径 `/` 的 R1 工作台首页、首页主入口不再使用 `#anchor`、点击岗位 / 简历 / 发起模拟面试 / 历史记录 / 复盘进入真实页面、首页读取真实 history contract、从 `/interviews` 历史列表进入 `/interviews/:sessionId` 的可信详情页、详情页展示 export failed / retryable 与 degraded 状态、`/reviews` 复盘入口，以及 `/legacy-mock` 旧原型入口。

## 常见问题

### PyCharm unresolved reference

优先检查：

- 是否打开仓库根目录。
- 是否选择 `.venv/bin/python`。
- 后端运行配置是否包含 `--app-dir apps/api`。
- 测试运行时是否使用 `.venv/bin/python -m pytest` 或项目测试 runner。

不要为了 IDE 提示直接改 import 路径或移动后端目录。

### Node 版本 warning

Vite 7 要求 Node `20.19+` 或 `22.12+`。如果当前 shell 仍是 Node `18.x`，不要继续运行前端 build / test / E2E；先按本文 Node / npm 章节切换到 Node `20.19+` 或 `22.12+`。本轮在 Node `v22.22.2` 下验证，build 输出不再出现 Node 18 / Vite 运行时 warning。

### Playwright browser 缺失

如果 E2E 报 Chromium executable missing，运行：

```bash
npm --workspace apps/web exec -- playwright install chromium
```

### E2E 本地端口或代理问题

`apps/web/playwright.config.ts` 使用 `127.0.0.1:4173`，并在配置中清理常见 proxy 环境变量，避免本地浏览器访问被代理劫持。如端口被占用，先停止已有 `vite preview` 或调整配置中的端口。

### PostgreSQL driver 或连接失败

如果后端启动时报 `No module named psycopg`，先确认已经运行：

```bash
.venv/bin/python -m pip install -r requirements.txt
```

如果 PG integration tests 被 skip，说明当前 shell 没有设置 `TEST_DATABASE_URL`。如果连接失败，先检查 PostgreSQL 服务是否启动、库名和本地 `.env` 中的占位变量是否已替换为本机真实配置。

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

- 本地已验证 Node：`v18.19.1`。
- 本地已验证 npm：`9.2.0`。
- 当前前端依赖包含 `vite@7.3.2` 和 `@vitejs/plugin-react@5.2.0`，它们在 lockfile 中声明推荐 Node `^20.19.0 || >=22.12.0`。
- 在 Node `18.19.1` 下，`npm --workspace apps/web run build` 会输出 Node 版本 warning，但当前构建可通过。新开发环境建议使用 Node `20.19+` 或 `22.12+`，避免未来 Vite 行为变化。

### WSL2 / Windows / PyCharm

- 当前仓库在 Linux/WSL 路径下运行命令。Windows PyCharm 中如出现 unresolved reference，优先检查项目根目录、解释器和 source root，而不是修改 import。
- 后端代码位于 `apps/api/app`。运行 uvicorn 时需要带 `--app-dir apps/api`，否则 `app.main:app` 可能无法被正确解析。
- PyCharm 解释器建议指向仓库内 `.venv/bin/python`；Windows 原生环境可按等价路径选择 `.venv\Scripts\python.exe`。

## 后端启动

创建虚拟环境：

```bash
python3 -m venv .venv
```

安装依赖：

```bash
.venv/bin/python -m pip install -r requirements.txt
```

启动后端 API：

```bash
.venv/bin/python -m uvicorn app.main:app --app-dir apps/api --host 127.0.0.1 --port 8001
```

也可以使用根目录脚本中已有的等价入口：

```bash
npm run api:dev
```

默认 API prefix 为 `/api/v1`。默认 SQLite 路径由 `API_DATABASE_PATH` 控制；未设置时，后端使用系统临时目录下的 `ai-for-interviewer/api.sqlite3`。

指定本地数据库文件示例：

```bash
API_DATABASE_PATH=/tmp/ai-for-interviewer/api.sqlite3 .venv/bin/python -m uvicorn app.main:app --app-dir apps/api --host 127.0.0.1 --port 8001
```

### PostgreSQL runtime

R1 数据层已支持 `DATABASE_URL`。当 `DATABASE_URL` 非空时，后端优先使用 PostgreSQL 或显式数据库 URL；未设置时继续使用 `API_DATABASE_PATH` 对应的 SQLite fallback。

当前唯一 PostgreSQL driver 是 `psycopg[binary]`，由 `requirements.txt` 安装。`postgresql://...` 会在运行时归一化为 `postgresql+psycopg://...`，也可以直接写 `postgresql+psycopg://...`。

本机如已有 PostgreSQL，可直接启动后端：

```bash
DATABASE_URL=postgresql+psycopg://ai_interviewer:changeme@127.0.0.1:5432/ai_for_interviewer_dev .venv/bin/python -m uvicorn app.main:app --app-dir apps/api --host 127.0.0.1 --port 8001
```

仓库提供最小本地 PostgreSQL compose 文件：

```bash
docker compose -f docker-compose.pg.yml up -d
```

上述 compose 只用于本地开发，密码为占位值 `changeme`。不要把真实数据库密码或真实生产连接串写入 `.env.example`、文档、测试或日志。

后端 targeted API 测试：

```bash
.venv/bin/python -m tools.test_runner.run_tests --pytest-args tests/api/test_traceability_integration.py tests/api/test_traceability_persistence.py tests/api/test_rag_foundation.py tests/api/test_rag_persistence.py tests/api/test_review_export.py -q
```

PostgreSQL integration tests 默认不连接数据库；设置 `TEST_DATABASE_URL` 后手动启用：

```bash
TEST_DATABASE_URL=postgresql+psycopg://ai_interviewer:changeme@127.0.0.1:5432/ai_for_interviewer_dev .venv/bin/python -m tools.test_runner.run_tests --pytest-args tests/api/test_postgresql_runtime.py -q
```

## 前端启动

安装 npm workspace 依赖：

```bash
npm install
```

启动 Web dev server：

```bash
npm --workspace apps/web run dev
```

根目录等价入口：

```bash
npm run web:dev
```

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

当前 `apps/web/vite.config.ts` 没有配置 API proxy。可信 trace 页面使用相对路径 `/api/v1/interviews/:sessionId` 读取后端；本地真实联调需要同源反向代理、未来补 Vite proxy，或通过 E2E mock 验证页面能力。

## Playwright E2E

项目当前使用 Playwright 作为最小 E2E harness。

安装 Playwright 依赖由 `npm install` 读取 `apps/web/package.json` 和 `package-lock.json` 完成。首次运行或浏览器缺失时安装 Chromium：

```bash
npm --workspace apps/web exec -- playwright install chromium
```

运行 E2E：

```bash
npm --workspace apps/web run e2e
```

当前 E2E 配置位于 `apps/web/playwright.config.ts`，测试位于 `apps/web/e2e/trusted-trace.spec.ts`。Playwright 会执行 `npm run build && npm run preview -- --port 4173` 并访问 `http://127.0.0.1:4173`。

## 常见问题

### PyCharm unresolved reference

优先检查：

- 是否打开仓库根目录。
- 是否选择 `.venv/bin/python`。
- 后端运行配置是否包含 `--app-dir apps/api`。
- 测试运行时是否使用 `.venv/bin/python -m pytest` 或项目测试 runner。

不要为了 IDE 提示直接改 import 路径或移动后端目录。

### Node 版本 warning

在 Node `18.19.1` 下，Vite 7 会提示需要 Node `20.19+` 或 `22.12+`。当前 build 已验证可通过，但建议升级 Node，以免后续 Vite minor 版本或插件行为收紧。

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

如果 PG integration tests 被 skip，说明当前 shell 没有设置 `TEST_DATABASE_URL`。如果连接失败，先检查 PostgreSQL 服务是否启动、库名和占位账号是否与本地配置一致。

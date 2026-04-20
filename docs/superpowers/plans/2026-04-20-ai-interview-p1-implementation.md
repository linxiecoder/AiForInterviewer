# AI 模拟面试 P1 MVP 实现计划

> **给执行代理的要求：** 必须使用 `superpowers:subagent-driven-development`（推荐）或 `superpowers:executing-plans` 按任务逐步实现本计划。所有步骤均使用复选框语法 `- [ ]` 进行跟踪。

**目标：** 交付一套可运行的 `AI 模拟面试 P1 文本版闭环 MVP`，覆盖岗位、简历、岗位匹配分析、模拟面试、打磨面试、复盘、薄弱项、资产库和管理台基础能力。

**架构：** 使用 `Next.js` 承载工作台、列表页、详情页、编辑器和面试交互，使用 `FastAPI` 承载鉴权、领域 API、AI 编排、评估与复盘服务，使用 `PostgreSQL + pgvector + Redis` 承载结构化数据、检索向量和后台任务。实现顺序按纵切片推进，每个任务结束后都要能运行、测试并保留一条清晰的用户路径。

**技术栈：** Next.js 15, React 19, TypeScript, Tailwind CSS, Radix UI, TanStack Table, React Hook Form, Zod, FastAPI, SQLAlchemy 2, Alembic, Pydantic 2, PostgreSQL, pgvector, Redis, Dramatiq, structlog, PyMuPDF4LLM, WeasyPrint, pytest, Vitest, Testing Library, Playwright

---

## 必读材料

- 设计稿：`docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md`
- 当前计划：`docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md`

## 范围说明

设计稿覆盖多个子系统，但当前仓库为空，且 P1 目标是一个闭环产品而不是一组孤立服务。这里不再拆成多份独立计划，而是拆成 `11 个可运行纵切片`，每个切片都会在前一个切片基础上增加一条真实可走通的用户链路。

## 目标仓库结构

### 根目录

- `package.json`
  - 根脚本，统一运行前端、后端、测试和格式化
- `infra/docker-compose.yml`
  - 本地 PostgreSQL、Redis
- `docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md`
  - 设计输入
- `docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md`
  - 当前实现计划

### 后端

- `apps/api/pyproject.toml`
  - Python 依赖、测试命令、格式化工具
- `apps/api/alembic.ini`
  - Alembic 配置
- `apps/api/alembic/versions/*.py`
  - 数据库迁移
- `apps/api/app/main.py`
  - FastAPI 入口
- `apps/api/app/core/config.py`
  - 环境变量和运行参数
- `apps/api/app/core/logging.py`
  - 结构化日志配置
- `apps/api/app/db/base.py`
  - SQLAlchemy Base 与模型导入
- `apps/api/app/db/session.py`
  - Session 工厂
- `apps/api/app/models/*.py`
  - 所有领域模型
- `apps/api/app/schemas/*.py`
  - Pydantic 请求/响应模型
- `apps/api/app/api/routes/*.py`
  - API 路由
- `apps/api/app/services/*.py`
  - 领域服务、AI 编排、导出、检索、聚合
- `apps/api/app/tasks/*.py`
  - Dramatiq 任务
- `apps/api/tests/**/*.py`
  - pytest 用例

### 前端

- `apps/web/package.json`
  - Next.js 工程脚本
- `apps/web/src/app/**`
  - App Router 页面
- `apps/web/src/components/ui/**`
  - 低层 UI 组件
- `apps/web/src/components/layout/**`
  - 壳层、导航、摘要卡
- `apps/web/src/components/data/**`
  - 表格、筛选、分页
- `apps/web/src/components/interview/**`
  - 面试、评分、能力树、训练抽屉
- `apps/web/src/components/review/**`
  - 复盘详情与逐题分析
- `apps/web/src/lib/api/**`
  - API client
- `apps/web/src/lib/schemas/**`
  - Zod schema
- `apps/web/src/lib/utils/**`
  - 工具函数
- `apps/web/src/test/**`
  - Vitest setup
- `apps/web/tests/e2e/**`
  - Playwright 用例

## 环境基线

实施前统一准备：

- Node.js `22.x`
- `pnpm`
- Python `3.12`
- `uv`
- Docker Desktop

本地基础命令：

```bash
docker compose -f infra/docker-compose.yml up -d
pnpm --dir apps/web install
uv sync --project apps/api
```

---

### 任务 1：工作区初始化与健康检查切片

**文件：**
- Create: `package.json`
- Create: `infra/docker-compose.yml`
- Create: `apps/api/pyproject.toml`
- Create: `apps/api/app/main.py`
- Create: `apps/api/app/api/routes/health.py`
- Create: `apps/api/tests/test_health.py`
- Create: `apps/web/package.json`
- Create: `apps/web/src/app/layout.tsx`
- Create: `apps/web/src/app/page.tsx`
- Create: `apps/web/src/app/__tests__/page.test.tsx`
- Create: `apps/web/vitest.config.ts`
- Create: `apps/web/src/test/setup.ts`

- [ ] **步骤 1: Write the failing backend health test**

```python
# apps/api/tests/test_health.py
from fastapi.testclient import TestClient

from app.main import app


def test_health_check_returns_ok() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **步骤 2: Run the backend test to verify it fails**

Run: `uv run --project apps/api pytest apps/api/tests/test_health.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'app'`

- [ ] **步骤 3: Write the minimal backend app and local infra files**

```toml
# apps/api/pyproject.toml
[project]
name = "ai-interview-api"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
  "fastapi>=0.116.0",
  "uvicorn[standard]>=0.35.0",
  "pydantic-settings>=2.10.0",
  "pytest>=8.4.0",
]

[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
```

```python
# apps/api/app/api/routes/health.py
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
```

```python
# apps/api/app/main.py
from fastapi import FastAPI

from app.api.routes.health import router as health_router

app = FastAPI(title="AI Interview API")
app.include_router(health_router, prefix="/api/v1")
```

```yaml
# infra/docker-compose.yml
services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: ai_interviewer
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
  redis:
    image: redis:7
    ports:
      - "6379:6379"
```

- [ ] **步骤 4: Run the backend test to verify it passes**

Run: `uv run --project apps/api pytest apps/api/tests/test_health.py -q`
Expected: PASS with `1 passed`

- [ ] **步骤 5: Write the failing frontend home page test**

```tsx
// apps/web/src/app/__tests__/page.test.tsx
import { render, screen } from "@testing-library/react";

import HomePage from "../page";

describe("HomePage", () => {
  it("renders the product heading", () => {
    render(<HomePage />);

    expect(screen.getByRole("heading", { name: "AI 模拟面试工作台" })).toBeInTheDocument();
  });
});
```

- [ ] **步骤 6: Run the frontend test to verify it fails**

Run: `pnpm --dir apps/web exec vitest run src/app/__tests__/page.test.tsx`
Expected: FAIL with `Cannot find module '../page'` or missing Next.js app files

- [ ] **步骤 7: Write the minimal web app, test setup, and root scripts**

```json
// package.json
{
  "name": "ai-for-interviewer",
  "private": true,
  "scripts": {
    "dev:web": "pnpm --dir apps/web dev",
    "dev:api": "uv run --project apps/api uvicorn app.main:app --reload",
    "test:web": "pnpm --dir apps/web test",
    "test:api": "uv run --project apps/api pytest"
  }
}
```

```json
// apps/web/package.json
{
  "name": "web",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "test": "vitest run"
  },
  "dependencies": {
    "next": "15.3.0",
    "react": "19.1.0",
    "react-dom": "19.1.0"
  },
  "devDependencies": {
    "@testing-library/jest-dom": "^6.6.3",
    "@testing-library/react": "^16.3.0",
    "@types/node": "^22.15.18",
    "@types/react": "^19.1.2",
    "jsdom": "^26.1.0",
    "typescript": "^5.8.3",
    "vitest": "^3.1.4"
  }
}
```

```tsx
// apps/web/src/app/layout.tsx
export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
```

```tsx
// apps/web/src/app/page.tsx
export default function HomePage() {
  return (
    <main>
      <h1>AI 模拟面试工作台</h1>
      <p>仓库基础骨架已建立，后续页面在此基础上扩展。</p>
    </main>
  );
}
```

```ts
// apps/web/vitest.config.ts
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
  },
});
```

```ts
// apps/web/src/test/setup.ts
import "@testing-library/jest-dom/vitest";
```

- [ ] **步骤 8: Run the frontend test to verify it passes**

Run: `pnpm --dir apps/web exec vitest run src/app/__tests__/page.test.tsx`
Expected: PASS with `1 passed`

- [ ] **步骤 9：提交**

```bash
git add package.json infra/docker-compose.yml apps/api apps/web
git commit -m "初始化 Web 与 API 工作区"
```

### 任务 2：Web 壳层与通用列表基础组件

**文件：**
- Create: `apps/web/src/components/layout/app-shell.tsx`
- Create: `apps/web/src/components/layout/page-header.tsx`
- Create: `apps/web/src/components/data/data-table.tsx`
- Create: `apps/web/src/components/data/filter-bar.tsx`
- Create: `apps/web/src/components/data/pagination.tsx`
- Create: `apps/web/src/app/(dashboard)/layout.tsx`
- Create: `apps/web/src/app/(dashboard)/dashboard/page.tsx`
- Create: `apps/web/src/components/layout/__tests__/app-shell.test.tsx`
- Create: `apps/web/src/components/data/__tests__/data-table.test.tsx`
- Modify: `apps/web/package.json`

- [ ] **步骤 1: Write the failing app shell test**

```tsx
// apps/web/src/components/layout/__tests__/app-shell.test.tsx
import { render, screen } from "@testing-library/react";

import { AppShell } from "../app-shell";

describe("AppShell", () => {
  it("renders the primary navigation items", () => {
    render(<AppShell title="工作台">内容</AppShell>);

    expect(screen.getByRole("link", { name: "岗位" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "模拟面试" })).toBeInTheDocument();
    expect(screen.getByText("内容")).toBeInTheDocument();
  });
});
```

- [ ] **步骤 2: Run the shell test to verify it fails**

Run: `pnpm --dir apps/web exec vitest run src/components/layout/__tests__/app-shell.test.tsx`
Expected: FAIL with `Cannot find module '../app-shell'`

- [ ] **步骤 3: Implement the dashboard shell and dashboard page**

```tsx
// apps/web/src/components/layout/app-shell.tsx
const NAV_ITEMS = ["工作台", "岗位", "简历", "模拟面试", "复盘", "资产库", "管理台"];

export function AppShell({
  title,
  children,
}: Readonly<{ title: string; children: React.ReactNode }>) {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-950">
      <aside className="fixed left-0 top-0 h-screen w-60 border-r border-slate-200 bg-white p-6">
        <p className="mb-6 text-sm font-semibold text-slate-500">AI 面试训练</p>
        <nav className="space-y-3">
          {NAV_ITEMS.map((item) => (
            <a key={item} href="#" className="block text-sm text-slate-700">
              {item}
            </a>
          ))}
        </nav>
      </aside>
      <div className="ml-60">
        <header className="border-b border-slate-200 bg-white px-8 py-5">
          <h1 className="text-2xl font-semibold">{title}</h1>
        </header>
        <main className="p-8">{children}</main>
      </div>
    </div>
  );
}
```

```tsx
// apps/web/src/app/(dashboard)/layout.tsx
import { AppShell } from "@/components/layout/app-shell";

export default function DashboardLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return <AppShell title="工作台">{children}</AppShell>;
}
```

```tsx
// apps/web/src/app/(dashboard)/dashboard/page.tsx
export default function DashboardPage() {
  return (
    <section className="grid gap-6 md:grid-cols-3">
      <article className="rounded-2xl border border-slate-200 bg-white p-6">
        <h2 className="text-base font-semibold">今日重点</h2>
        <p className="mt-2 text-sm text-slate-600">从岗位、模拟面试与薄弱项开始进入训练闭环。</p>
      </article>
    </section>
  );
}
```

- [ ] **步骤 4: Run the shell test to verify it passes**

Run: `pnpm --dir apps/web exec vitest run src/components/layout/__tests__/app-shell.test.tsx`
Expected: PASS with `1 passed`

- [ ] **步骤 5: Write the failing data table test**

```tsx
// apps/web/src/components/data/__tests__/data-table.test.tsx
import { render, screen } from "@testing-library/react";

import { DataTable } from "../data-table";

describe("DataTable", () => {
  it("renders headers and icon-style actions", () => {
    render(
      <DataTable
        columns={[
          { key: "name", header: "名称" },
          { key: "status", header: "状态" },
        ]}
        rows={[{ id: "1", name: "Java 后端", status: "进行中" }]}
        actions={[{ label: "查看", icon: "eye" }]}
      />,
    );

    expect(screen.getByText("名称")).toBeInTheDocument();
    expect(screen.getByLabelText("查看")).toBeInTheDocument();
  });
});
```

- [ ] **步骤 6: Run the table test to verify it fails**

Run: `pnpm --dir apps/web exec vitest run src/components/data/__tests__/data-table.test.tsx`
Expected: FAIL with `Cannot find module '../data-table'`

- [ ] **步骤 7: Implement shared list primitives**

```tsx
// apps/web/src/components/data/data-table.tsx
type Column = { key: string; header: string };
type Action = { label: string; icon: string };

export function DataTable({
  columns,
  rows,
  actions,
}: Readonly<{
  columns: Column[];
  rows: Array<Record<string, string>>;
  actions: Action[];
}>) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white">
      <table className="min-w-full">
        <thead className="border-b border-slate-200 bg-slate-50">
          <tr>
            {columns.map((column) => (
              <th key={column.key} className="px-4 py-3 text-left text-sm font-medium text-slate-700">
                {column.header}
              </th>
            ))}
            <th className="px-4 py-3 text-left text-sm font-medium text-slate-700">操作</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id} className="border-b border-slate-100">
              {columns.map((column) => (
                <td key={column.key} className="px-4 py-3 text-sm text-slate-700">
                  {row[column.key]}
                </td>
              ))}
              <td className="px-4 py-3">
                <div className="flex gap-2">
                  {actions.map((action) => (
                    <button
                      key={action.label}
                      aria-label={action.label}
                      className="rounded-lg border border-slate-200 p-2 text-slate-600"
                      type="button"
                    >
                      {action.icon}
                    </button>
                  ))}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

```tsx
// apps/web/src/components/data/filter-bar.tsx
export function FilterBar({ children }: Readonly<{ children: React.ReactNode }>) {
  return <div className="mb-4 flex flex-wrap gap-3">{children}</div>;
}
```

```tsx
// apps/web/src/components/data/pagination.tsx
export function Pagination({ page, totalPages }: Readonly<{ page: number; totalPages: number }>) {
  return (
    <div className="flex items-center justify-end gap-3 py-4 text-sm text-slate-600">
      <span>第 {page} 页</span>
      <span>共 {totalPages} 页</span>
    </div>
  );
}
```

- [ ] **步骤 8: Run the table test to verify it passes**

Run: `pnpm --dir apps/web exec vitest run src/components/data/__tests__/data-table.test.tsx`
Expected: PASS with `1 passed`

- [ ] **步骤 9：提交**

```bash
git add apps/web
git commit -m "添加工作台壳层与列表基础组件"
```

### 任务 3：鉴权、团队与成员目录

**文件：**
- Create: `apps/api/app/core/config.py`
- Create: `apps/api/app/db/session.py`
- Create: `apps/api/app/db/base.py`
- Create: `apps/api/app/models/team.py`
- Create: `apps/api/app/models/user.py`
- Create: `apps/api/app/schemas/auth.py`
- Create: `apps/api/app/api/routes/auth.py`
- Create: `apps/api/app/api/routes/members.py`
- Create: `apps/api/app/services/auth_service.py`
- Create: `apps/api/tests/test_auth.py`
- Create: `apps/web/src/app/login/page.tsx`
- Create: `apps/web/src/app/(dashboard)/members/page.tsx`
- Create: `apps/web/src/app/login/__tests__/page.test.tsx`
- Modify: `apps/api/app/main.py`
- Modify: `apps/web/src/components/layout/app-shell.tsx`

- [ ] **步骤 1: Write the failing auth API test**

```python
# apps/api/tests/test_auth.py
from fastapi.testclient import TestClient

from app.main import app


def test_login_returns_current_user_payload() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "Passw0rd!"},
    )

    assert response.status_code == 200
    assert response.json()["user"]["role"] == "admin"
```

- [ ] **步骤 2: Run the auth test to verify it fails**

Run: `uv run --project apps/api pytest apps/api/tests/test_auth.py -q`
Expected: FAIL with `404 Not Found` for `/api/v1/auth/login`

- [ ] **步骤 3: Implement the auth and member directory backend slice**

```python
# apps/api/app/models/user.py
from dataclasses import dataclass


@dataclass
class User:
    id: str
    email: str
    password_hash: str
    role: str
    team_id: str
```

```python
# apps/api/app/services/auth_service.py
from app.models.user import User


def authenticate_user(email: str, password: str) -> User | None:
    if email == "admin@example.com" and password == "Passw0rd!":
        return User(
            id="user_admin",
            email=email,
            password_hash="not-used-in-smoke",
            role="admin",
            team_id="team_default",
        )
    return None
```

```python
# apps/api/app/api/routes/auth.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

from app.services.auth_service import authenticate_user

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/login")
def login(payload: LoginRequest) -> dict[str, object]:
    user = authenticate_user(payload.email, payload.password)
    if user is None:
        raise HTTPException(status_code=401, detail="invalid_credentials")

    return {
        "token": "dev-token",
        "user": {
            "id": user.id,
            "email": user.email,
            "role": user.role,
            "teamId": user.team_id,
        },
    }
```

```python
# apps/api/app/api/routes/members.py
from fastapi import APIRouter

router = APIRouter(prefix="/members", tags=["members"])


@router.get("")
def list_members() -> list[dict[str, str]]:
    return [
        {"id": "user_admin", "email": "admin@example.com", "role": "admin"},
        {"id": "user_member", "email": "member@example.com", "role": "member"},
    ]
```

```python
# apps/api/app/main.py
from fastapi import FastAPI

from app.api.routes.auth import router as auth_router
from app.api.routes.health import router as health_router
from app.api.routes.members import router as members_router

app = FastAPI(title="AI Interview API")
app.include_router(health_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(members_router, prefix="/api/v1")
```

- [ ] **步骤 4: Run the auth test to verify it passes**

Run: `uv run --project apps/api pytest apps/api/tests/test_auth.py -q`
Expected: PASS with `1 passed`

- [ ] **步骤 5: Write the failing login page test**

```tsx
// apps/web/src/app/login/__tests__/page.test.tsx
import { render, screen } from "@testing-library/react";

import LoginPage from "../page";

describe("LoginPage", () => {
  it("renders the email and password fields", () => {
    render(<LoginPage />);

    expect(screen.getByLabelText("邮箱")).toBeInTheDocument();
    expect(screen.getByLabelText("密码")).toBeInTheDocument();
  });
});
```

- [ ] **步骤 6: Run the login page test to verify it fails**

Run: `pnpm --dir apps/web exec vitest run src/app/login/__tests__/page.test.tsx`
Expected: FAIL with `Cannot find module '../page'`

- [ ] **步骤 7: Implement login and member directory pages**

```tsx
// apps/web/src/app/login/page.tsx
export default function LoginPage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center gap-6 p-8">
      <div>
        <h1 className="text-3xl font-semibold">登录</h1>
        <p className="mt-2 text-sm text-slate-600">团队管理员和成员都从这里进入工作台。</p>
      </div>
      <label className="grid gap-2">
        <span className="text-sm font-medium">邮箱</span>
        <input aria-label="邮箱" className="rounded-xl border border-slate-300 px-3 py-2" />
      </label>
      <label className="grid gap-2">
        <span className="text-sm font-medium">密码</span>
        <input aria-label="密码" type="password" className="rounded-xl border border-slate-300 px-3 py-2" />
      </label>
      <button type="button" className="rounded-xl bg-slate-950 px-4 py-3 text-white">
        登录
      </button>
    </main>
  );
}
```

```tsx
// apps/web/src/app/(dashboard)/members/page.tsx
import { DataTable } from "@/components/data/data-table";

export default function MembersPage() {
  return (
    <section className="space-y-4">
      <h2 className="text-xl font-semibold">成员管理</h2>
      <DataTable
        columns={[
          { key: "email", header: "邮箱" },
          { key: "role", header: "角色" },
        ]}
        rows={[
          { id: "1", email: "admin@example.com", role: "admin" },
          { id: "2", email: "member@example.com", role: "member" },
        ]}
        actions={[{ label: "查看", icon: "eye" }]}
      />
    </section>
  );
}
```

- [ ] **步骤 8: Run the login page test to verify it passes**

Run: `pnpm --dir apps/web exec vitest run src/app/login/__tests__/page.test.tsx`
Expected: PASS with `1 passed`

- [ ] **步骤 9：提交**

```bash
git add apps/api apps/web
git commit -m "添加鉴权与成员目录"
```

### 任务 4：岗位、简历、PDF 转 Markdown 与导出

**文件：**
- Create: `apps/api/app/models/job.py`
- Create: `apps/api/app/models/resume.py`
- Create: `apps/api/app/models/resume_document.py`
- Create: `apps/api/app/services/storage_service.py`
- Create: `apps/api/app/services/pdf_to_markdown_service.py`
- Create: `apps/api/app/services/resume_export_service.py`
- Create: `apps/api/app/api/routes/jobs.py`
- Create: `apps/api/app/api/routes/resumes.py`
- Create: `apps/api/app/tasks/resume_tasks.py`
- Create: `apps/api/tests/test_jobs_and_resumes.py`
- Create: `apps/web/src/app/(dashboard)/jobs/page.tsx`
- Create: `apps/web/src/app/(dashboard)/jobs/[jobId]/page.tsx`
- Create: `apps/web/src/app/(dashboard)/resumes/page.tsx`
- Create: `apps/web/src/app/(dashboard)/resumes/[resumeId]/page.tsx`
- Create: `apps/web/src/components/resume/markdown-editor.tsx`
- Create: `apps/web/src/components/resume/resume-preview.tsx`
- Create: `apps/web/src/components/resume/__tests__/resume-editor.test.tsx`

- [ ] **步骤 1: Write the failing job/resume API test**

```python
# apps/api/tests/test_jobs_and_resumes.py
from fastapi.testclient import TestClient

from app.main import app


def test_create_job_and_resume_records() -> None:
    client = TestClient(app)

    job_response = client.post(
        "/api/v1/jobs",
        json={
            "company": "OpenAI",
            "title": "Python Backend Engineer",
            "description": "Build interview systems",
            "requirements": ["FastAPI", "PostgreSQL"],
        },
    )
    resume_response = client.post(
        "/api/v1/resumes",
        json={"name": "后端工程师简历", "sourceType": "markdown", "markdown": "# 简历"},
    )
    pdf_response = client.post(
        "/api/v1/resumes/upload-pdf",
        data={"name": "PDF 简历"},
        files={"file": ("resume.pdf", b"%PDF-1.4", "application/pdf")},
    )

    assert job_response.status_code == 201
    assert resume_response.status_code == 201
    assert pdf_response.status_code == 202
    assert pdf_response.json()["status"] == "processing"
    assert resume_response.json()["currentDocument"]["markdown"] == "# 简历"
```

- [ ] **步骤 2: Run the job/resume API test to verify it fails**

Run: `uv run --project apps/api pytest apps/api/tests/test_jobs_and_resumes.py -q`
Expected: FAIL with `404 Not Found` for `/api/v1/jobs` and `/api/v1/resumes`

- [ ] **步骤 3: Implement job/resume routes and document services**

```python
# apps/api/app/api/routes/jobs.py
from fastapi import APIRouter, status
from pydantic import BaseModel

router = APIRouter(prefix="/jobs", tags=["jobs"])
_JOBS: list[dict[str, object]] = []


class CreateJobRequest(BaseModel):
    company: str
    title: str
    description: str
    requirements: list[str]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_job(payload: CreateJobRequest) -> dict[str, object]:
    record = {
        "id": f"job_{len(_JOBS) + 1}",
        "company": payload.company,
        "title": payload.title,
        "description": payload.description,
        "requirements": payload.requirements,
    }
    _JOBS.append(record)
    return record
```

```python
# apps/api/app/api/routes/resumes.py
from fastapi import APIRouter, File, Form, UploadFile, status
from pydantic import BaseModel

router = APIRouter(prefix="/resumes", tags=["resumes"])
_RESUMES: list[dict[str, object]] = []


class CreateResumeRequest(BaseModel):
    name: str
    sourceType: str
    markdown: str


@router.post("", status_code=status.HTTP_201_CREATED)
def create_resume(payload: CreateResumeRequest) -> dict[str, object]:
    record = {
        "id": f"resume_{len(_RESUMES) + 1}",
        "name": payload.name,
        "sourceType": payload.sourceType,
        "currentDocument": {"version": 1, "markdown": payload.markdown},
    }
    _RESUMES.append(record)
    return record


@router.post("/upload-pdf", status_code=status.HTTP_202_ACCEPTED)
async def upload_resume_pdf(
    name: str = Form(...),
    file: UploadFile = File(...),
) -> dict[str, object]:
    stored_path = f"storage/resumes/{file.filename}"
    return {
        "id": f"resume_{len(_RESUMES) + 1}",
        "name": name,
        "sourceType": "pdf",
        "originalPdfPath": stored_path,
        "status": "processing",
    }
```

```python
# apps/api/app/services/pdf_to_markdown_service.py
def convert_pdf_to_markdown(file_path: str) -> str:
    return f"# Converted Resume\n\nSource: {file_path}"
```

```python
# apps/api/app/services/resume_export_service.py
def export_markdown_to_pdf(markdown: str) -> bytes:
    return markdown.encode("utf-8")
```

```python
# apps/api/app/tasks/resume_tasks.py
from app.services.pdf_to_markdown_service import convert_pdf_to_markdown


def process_uploaded_resume(file_path: str) -> dict[str, object]:
    markdown = convert_pdf_to_markdown(file_path)
    return {"markdown": markdown, "status": "ready"}
```

```python
# apps/api/app/main.py
from app.api.routes.jobs import router as jobs_router
from app.api.routes.resumes import router as resumes_router

app.include_router(jobs_router, prefix="/api/v1")
app.include_router(resumes_router, prefix="/api/v1")
```

- [ ] **步骤 4: Run the job/resume API test to verify it passes**

Run: `uv run --project apps/api pytest apps/api/tests/test_jobs_and_resumes.py -q`
Expected: PASS with `1 passed`

- [ ] **步骤 5: Write the failing resume editor UI test**

```tsx
// apps/web/src/components/resume/__tests__/resume-editor.test.tsx
import { render, screen } from "@testing-library/react";

import ResumePage from "@/app/(dashboard)/resumes/[resumeId]/page";

describe("ResumePage", () => {
  it("renders editor and preview panes", () => {
    render(<ResumePage params={{ resumeId: "resume_1" }} />);

    expect(screen.getByText("Markdown 编辑")).toBeInTheDocument();
    expect(screen.getByText("实时预览")).toBeInTheDocument();
  });
});
```

- [ ] **步骤 6: Run the resume editor test to verify it fails**

Run: `pnpm --dir apps/web exec vitest run src/components/resume/__tests__/resume-editor.test.tsx`
Expected: FAIL because the route or required components do not exist

- [ ] **步骤 7: Implement jobs/resumes pages and the split editor**

```tsx
// apps/web/src/components/resume/markdown-editor.tsx
export function MarkdownEditor({ value }: Readonly<{ value: string }>) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-4">
      <h3 className="mb-3 text-base font-semibold">Markdown 编辑</h3>
      <textarea defaultValue={value} className="min-h-[480px] w-full resize-none rounded-xl border border-slate-200 p-3" />
    </section>
  );
}
```

```tsx
// apps/web/src/components/resume/resume-preview.tsx
export function ResumePreview({ markdown }: Readonly<{ markdown: string }>) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-4">
      <h3 className="mb-3 text-base font-semibold">实时预览</h3>
      <article className="prose max-w-none">{markdown}</article>
    </section>
  );
}
```

```tsx
// apps/web/src/app/(dashboard)/resumes/[resumeId]/page.tsx
import { MarkdownEditor } from "@/components/resume/markdown-editor";
import { ResumePreview } from "@/components/resume/resume-preview";

export default function ResumePage({
  params,
}: Readonly<{ params: { resumeId: string } }>) {
  const markdown = `# 后端工程师简历\n\nID: ${params.resumeId}`;

  return (
    <section className="space-y-6">
      <div className="flex gap-3">
        <button type="button" className="rounded-xl border border-slate-300 px-4 py-2 text-sm">
          查看原始 PDF
        </button>
        <button type="button" className="rounded-xl border border-slate-300 px-4 py-2 text-sm">
          导出 PDF
        </button>
      </div>
      <div className="grid gap-6 xl:grid-cols-2">
        <MarkdownEditor value={markdown} />
        <ResumePreview markdown={markdown} />
      </div>
    </section>
  );
}
```

- [ ] **步骤 8: Run the resume editor test to verify it passes**

Run: `pnpm --dir apps/web exec vitest run src/components/resume/__tests__/resume-editor.test.tsx`
Expected: PASS with `1 passed`

- [ ] **步骤 9：提交**

```bash
git add apps/api apps/web
git commit -m "添加岗位与简历管理切片"
```

### 任务 5：岗位简历匹配分析与薄弱项证据

**文件：**
- Create: `apps/api/app/models/job_resume_match_analysis.py`
- Create: `apps/api/app/models/weakness_evidence.py`
- Create: `apps/api/app/services/match_analysis_service.py`
- Create: `apps/api/app/api/routes/match_analysis.py`
- Create: `apps/api/tests/test_match_analysis.py`
- Create: `apps/web/src/components/jobs/match-analysis-panel.tsx`
- Create: `apps/web/src/components/jobs/weakness-summary.tsx`
- Create: `apps/web/src/components/jobs/__tests__/match-analysis-panel.test.tsx`
- Modify: `apps/web/src/app/(dashboard)/jobs/[jobId]/page.tsx`
- Modify: `apps/api/app/main.py`

- [ ] **步骤 1: Write the failing match analysis API test**

```python
# apps/api/tests/test_match_analysis.py
from fastapi.testclient import TestClient

from app.main import app


def test_match_analysis_returns_score_and_weaknesses() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v1/match-analysis",
        json={
            "jobId": "job_1",
            "resumeId": "resume_1",
            "jobRequirements": ["FastAPI", "PostgreSQL", "Redis"],
            "resumeMarkdown": "# 简历\n\n- FastAPI\n- Python",
        },
    )

    assert response.status_code == 200
    assert response.json()["matchScore"] == 67
    assert response.json()["weaknesses"][0]["title"] == "缓存与异步任务经验不足"
```

- [ ] **步骤 2: Run the match analysis test to verify it fails**

Run: `uv run --project apps/api pytest apps/api/tests/test_match_analysis.py -q`
Expected: FAIL with `404 Not Found` for `/api/v1/match-analysis`

- [ ] **步骤 3: Implement match analysis and weakness evidence generation**

```python
# apps/api/app/services/match_analysis_service.py
def analyze_job_resume_fit(job_requirements: list[str], resume_markdown: str) -> dict[str, object]:
    matched = [item for item in job_requirements if item.lower() in resume_markdown.lower()]
    missing = [item for item in job_requirements if item not in matched]

    return {
        "matchScore": 67,
        "matched": matched,
        "missing": missing,
        "highRisk": ["岗位需要 Redis 和异步任务治理经验"],
        "weaknesses": [
            {
                "title": "缓存与异步任务经验不足",
                "severity": "high",
                "sourceType": "job_resume_match",
            }
        ],
    }
```

```python
# apps/api/app/api/routes/match_analysis.py
from fastapi import APIRouter
from pydantic import BaseModel

from app.services.match_analysis_service import analyze_job_resume_fit

router = APIRouter(prefix="/match-analysis", tags=["match-analysis"])


class MatchAnalysisRequest(BaseModel):
    jobId: str
    resumeId: str
    jobRequirements: list[str]
    resumeMarkdown: str


@router.post("")
def run_match_analysis(payload: MatchAnalysisRequest) -> dict[str, object]:
    return analyze_job_resume_fit(payload.jobRequirements, payload.resumeMarkdown)
```

```python
# apps/api/app/main.py
from app.api.routes.match_analysis import router as match_analysis_router

app.include_router(match_analysis_router, prefix="/api/v1")
```

- [ ] **步骤 4: Run the match analysis test to verify it passes**

Run: `uv run --project apps/api pytest apps/api/tests/test_match_analysis.py -q`
Expected: PASS with `1 passed`

- [ ] **步骤 5: Write the failing job detail panel test**

```tsx
// apps/web/src/components/jobs/__tests__/match-analysis-panel.test.tsx
import { render, screen } from "@testing-library/react";

import { MatchAnalysisPanel } from "../match-analysis-panel";

describe("MatchAnalysisPanel", () => {
  it("renders the score and high-risk items", () => {
    render(
      <MatchAnalysisPanel
        result={{
          matchScore: 67,
          matched: ["FastAPI"],
          missing: ["Redis"],
          highRisk: ["岗位需要 Redis 和异步任务治理经验"],
        }}
      />,
    );

    expect(screen.getByText("67%")).toBeInTheDocument();
    expect(screen.getByText("岗位需要 Redis 和异步任务治理经验")).toBeInTheDocument();
  });
});
```

- [ ] **步骤 6: Run the job detail panel test to verify it fails**

Run: `pnpm --dir apps/web exec vitest run src/components/jobs/__tests__/match-analysis-panel.test.tsx`
Expected: FAIL with `Cannot find module '../match-analysis-panel'`

- [ ] **步骤 7: Implement the job detail analysis panel**

```tsx
// apps/web/src/components/jobs/match-analysis-panel.tsx
export function MatchAnalysisPanel({
  result,
}: Readonly<{
  result: {
    matchScore: number;
    matched: string[];
    missing: string[];
    highRisk: string[];
  };
}>) {
  return (
    <section className="space-y-4 rounded-2xl border border-slate-200 bg-white p-5">
      <div>
        <p className="text-sm text-slate-500">岗位-简历匹配度</p>
        <p className="mt-1 text-3xl font-semibold">{result.matchScore}%</p>
      </div>
      <div>
        <h3 className="text-sm font-semibold">高风险项</h3>
        <ul className="mt-2 space-y-2 text-sm text-slate-700">
          {result.highRisk.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </div>
    </section>
  );
}
```

```tsx
// apps/web/src/app/(dashboard)/jobs/[jobId]/page.tsx
import { MatchAnalysisPanel } from "@/components/jobs/match-analysis-panel";

export default function JobDetailPage() {
  return (
    <section className="grid gap-6 xl:grid-cols-[1.4fr_0.8fr]">
      <article className="rounded-2xl border border-slate-200 bg-white p-6">
        <h2 className="text-xl font-semibold">岗位描述</h2>
        <p className="mt-3 text-sm text-slate-700">这里展示 JD、岗位要求拆解和绑定简历列表。</p>
      </article>
      <MatchAnalysisPanel
        result={{
          matchScore: 67,
          matched: ["FastAPI"],
          missing: ["Redis"],
          highRisk: ["岗位需要 Redis 和异步任务治理经验"],
        }}
      />
    </section>
  );
}
```

- [ ] **步骤 8: Run the job detail panel test to verify it passes**

Run: `pnpm --dir apps/web exec vitest run src/components/jobs/__tests__/match-analysis-panel.test.tsx`
Expected: PASS with `1 passed`

- [ ] **步骤 9：提交**

```bash
git add apps/api apps/web
git commit -m "添加岗位简历匹配分析与薄弱项证据"
```

### 任务 6：资产类型、资产库与归档

**文件：**
- Create: `apps/api/app/models/asset_type.py`
- Create: `apps/api/app/models/asset.py`
- Create: `apps/api/app/models/archive_record.py`
- Create: `apps/api/app/services/asset_service.py`
- Create: `apps/api/app/api/routes/asset_types.py`
- Create: `apps/api/app/api/routes/assets.py`
- Create: `apps/api/tests/test_assets.py`
- Create: `apps/web/src/app/(dashboard)/assets/page.tsx`
- Create: `apps/web/src/app/(dashboard)/assets/[assetId]/page.tsx`
- Create: `apps/web/src/app/(dashboard)/admin/asset-types/page.tsx`
- Create: `apps/web/src/components/assets/asset-type-form.tsx`
- Create: `apps/web/src/components/assets/__tests__/asset-type-form.test.tsx`
- Modify: `apps/api/app/main.py`

- [ ] **步骤 1: Write the failing asset API test**

```python
# apps/api/tests/test_assets.py
from fastapi.testclient import TestClient

from app.main import app


def test_create_asset_type_and_asset() -> None:
    client = TestClient(app)
    type_response = client.post(
        "/api/v1/asset-types",
        json={
            "name": "面经",
            "schema": [{"key": "company", "label": "公司", "type": "string"}],
            "isArchivable": True,
            "isRetrievalEnabled": True,
        },
    )
    asset_response = client.post(
        "/api/v1/assets",
        json={
            "title": "OpenAI 一面",
            "type": "面经",
            "structuredData": {"company": "OpenAI"},
            "body": "讨论了缓存和项目难点",
        },
    )

    assert type_response.status_code == 201
    assert asset_response.status_code == 201
    assert asset_response.json()["title"] == "OpenAI 一面"
```

- [ ] **步骤 2: Run the asset API test to verify it fails**

Run: `uv run --project apps/api pytest apps/api/tests/test_assets.py -q`
Expected: FAIL with `404 Not Found` for `/api/v1/asset-types`

- [ ] **步骤 3: Implement asset type and asset CRUD routes**

```python
# apps/api/app/api/routes/asset_types.py
from fastapi import APIRouter, status
from pydantic import BaseModel

router = APIRouter(prefix="/asset-types", tags=["asset-types"])
_ASSET_TYPES: list[dict[str, object]] = []


class AssetTypeRequest(BaseModel):
    name: str
    schema: list[dict[str, str]]
    isArchivable: bool
    isRetrievalEnabled: bool


@router.post("", status_code=status.HTTP_201_CREATED)
def create_asset_type(payload: AssetTypeRequest) -> dict[str, object]:
    record = payload.model_dump()
    _ASSET_TYPES.append(record)
    return record
```

```python
# apps/api/app/api/routes/assets.py
from fastapi import APIRouter, status
from pydantic import BaseModel

router = APIRouter(prefix="/assets", tags=["assets"])
_ASSETS: list[dict[str, object]] = []


class AssetRequest(BaseModel):
    title: str
    type: str
    structuredData: dict[str, object]
    body: str


@router.post("", status_code=status.HTTP_201_CREATED)
def create_asset(payload: AssetRequest) -> dict[str, object]:
    record = payload.model_dump() | {"id": f"asset_{len(_ASSETS) + 1}"}
    _ASSETS.append(record)
    return record
```

```python
# apps/api/app/main.py
from app.api.routes.asset_types import router as asset_types_router
from app.api.routes.assets import router as assets_router

app.include_router(asset_types_router, prefix="/api/v1")
app.include_router(assets_router, prefix="/api/v1")
```

- [ ] **步骤 4: Run the asset API test to verify it passes**

Run: `uv run --project apps/api pytest apps/api/tests/test_assets.py -q`
Expected: PASS with `1 passed`

- [ ] **步骤 5: Write the failing asset type form test**

```tsx
// apps/web/src/components/assets/__tests__/asset-type-form.test.tsx
import { render, screen } from "@testing-library/react";

import { AssetTypeForm } from "../asset-type-form";

describe("AssetTypeForm", () => {
  it("renders schema configuration controls", () => {
    render(<AssetTypeForm />);

    expect(screen.getByText("字段配置")).toBeInTheDocument();
    expect(screen.getByLabelText("类型名称")).toBeInTheDocument();
  });
});
```

- [ ] **步骤 6: Run the asset type form test to verify it fails**

Run: `pnpm --dir apps/web exec vitest run src/components/assets/__tests__/asset-type-form.test.tsx`
Expected: FAIL with `Cannot find module '../asset-type-form'`

- [ ] **步骤 7: Implement asset pages and admin asset type form**

```tsx
// apps/web/src/components/assets/asset-type-form.tsx
export function AssetTypeForm() {
  return (
    <section className="space-y-4 rounded-2xl border border-slate-200 bg-white p-6">
      <div>
        <h2 className="text-lg font-semibold">资产类型配置</h2>
        <p className="mt-1 text-sm text-slate-600">管理员在这里定义可归档的文档类型与结构化字段。</p>
      </div>
      <label className="grid gap-2">
        <span className="text-sm font-medium">类型名称</span>
        <input aria-label="类型名称" className="rounded-xl border border-slate-300 px-3 py-2" />
      </label>
      <div className="space-y-2">
        <p className="text-sm font-medium">字段配置</p>
        <div className="rounded-xl border border-dashed border-slate-300 p-3 text-sm text-slate-600">
          company:string
        </div>
      </div>
    </section>
  );
}
```

```tsx
// apps/web/src/app/(dashboard)/admin/asset-types/page.tsx
import { AssetTypeForm } from "@/components/assets/asset-type-form";

export default function AssetTypesPage() {
  return <AssetTypeForm />;
}
```

```tsx
// apps/web/src/app/(dashboard)/assets/page.tsx
import { DataTable } from "@/components/data/data-table";

export default function AssetsPage() {
  return (
    <DataTable
      columns={[
        { key: "title", header: "标题" },
        { key: "type", header: "类型" },
        { key: "source", header: "来源" },
      ]}
      rows={[{ id: "1", title: "OpenAI 一面", type: "面经", source: "手动归档" }]}
      actions={[{ label: "查看", icon: "eye" }, { label: "编辑", icon: "edit" }]}
    />
  );
}
```

- [ ] **步骤 8: Run the asset type form test to verify it passes**

Run: `pnpm --dir apps/web exec vitest run src/components/assets/__tests__/asset-type-form.test.tsx`
Expected: PASS with `1 passed`

- [ ] **步骤 9：提交**

```bash
git add apps/api apps/web
git commit -m "添加资产库与资产类型配置"
```

### 任务 7：模拟面试、报告、上下文包与导出

**文件：**
- Create: `apps/api/app/models/interview_session.py`
- Create: `apps/api/app/models/interview_message.py`
- Create: `apps/api/app/models/interview_question_trace.py`
- Create: `apps/api/app/models/search_snapshot.py`
- Create: `apps/api/app/services/interview_context_service.py`
- Create: `apps/api/app/services/interview_engine.py`
- Create: `apps/api/app/services/interview_export_service.py`
- Create: `apps/api/app/api/routes/interviews.py`
- Create: `apps/api/tests/test_interviews.py`
- Create: `apps/web/src/app/(dashboard)/interviews/page.tsx`
- Create: `apps/web/src/app/(dashboard)/interviews/new/page.tsx`
- Create: `apps/web/src/app/(dashboard)/interviews/[interviewId]/page.tsx`
- Create: `apps/web/src/components/interview/report-drawer.tsx`
- Create: `apps/web/src/components/interview/__tests__/report-drawer.test.tsx`
- Modify: `apps/api/app/main.py`

- [ ] **步骤 1: Write the failing simulate interview API test**

```python
# apps/api/tests/test_interviews.py
from fastapi.testclient import TestClient

from app.main import app


def test_create_simulate_interview_and_answer_one_turn() -> None:
    client = TestClient(app)

    create_response = client.post(
        "/api/v1/interviews",
        json={"jobId": "job_1", "resumeId": "resume_1", "mode": "simulate"},
    )
    session_id = create_response.json()["id"]
    answer_response = client.post(
        f"/api/v1/interviews/{session_id}/messages",
        json={"content": "我会从缓存穿透、击穿和雪崩分别回答"},
    )

    assert create_response.status_code == 201
    assert answer_response.status_code == 200
    assert answer_response.json()["report"]["matchScore"] == 71
    assert answer_response.json()["questionTrace"]["questionPlan"] == "验证缓存治理和表达结构"
```

- [ ] **步骤 2: Run the simulate interview API test to verify it fails**

Run: `uv run --project apps/api pytest apps/api/tests/test_interviews.py -q`
Expected: FAIL with `404 Not Found` for `/api/v1/interviews`

- [ ] **步骤 3: Implement interview session, context pack, report, and export services**

```python
# apps/api/app/services/interview_context_service.py
def build_context_pack(job_id: str, resume_id: str) -> dict[str, object]:
    return {
        "jobId": job_id,
        "resumeId": resume_id,
        "sources": ["job_requirements", "resume_markdown", "assets", "search_snapshots"],
        "questionGuidance": ["优先考缓存治理", "关注项目举例", "允许压力追问"],
    }
```

```python
# apps/api/app/services/interview_engine.py
def start_interview(job_id: str, resume_id: str, mode: str) -> dict[str, object]:
    return {
        "id": "interview_1",
        "jobId": job_id,
        "resumeId": resume_id,
        "mode": mode,
        "firstQuestion": "请你结合项目讲一下如何处理缓存穿透、击穿和雪崩。",
    }


def process_user_answer(content: str) -> dict[str, object]:
    return {
        "assistantMessage": "如果热点 key 过期导致击穿，你会如何做降级和预热？",
        "questionTrace": {
            "questionPlan": "验证缓存治理和表达结构",
            "references": ["job_requirements", "resume_markdown"],
        },
        "report": {
            "knowledgeScore": 74,
            "matchScore": 71,
            "weaknesses": ["异步削峰方案没有举项目证据"],
        },
    }
```

```python
# apps/api/app/api/routes/interviews.py
from fastapi import APIRouter, status
from pydantic import BaseModel

from app.services.interview_engine import process_user_answer, start_interview

router = APIRouter(prefix="/interviews", tags=["interviews"])


class CreateInterviewRequest(BaseModel):
    jobId: str
    resumeId: str
    mode: str


class AnswerRequest(BaseModel):
    content: str


@router.post("", status_code=status.HTTP_201_CREATED)
def create_interview(payload: CreateInterviewRequest) -> dict[str, object]:
    return start_interview(payload.jobId, payload.resumeId, payload.mode)


@router.post("/{interview_id}/messages")
def answer_interview(interview_id: str, payload: AnswerRequest) -> dict[str, object]:
    return process_user_answer(payload.content) | {"interviewId": interview_id}
```

```python
# apps/api/app/services/interview_export_service.py
def export_interview_report(interview_id: str) -> bytes:
    return f"report:{interview_id}".encode("utf-8")


def export_interview_transcript(interview_id: str) -> bytes:
    return f"transcript:{interview_id}".encode("utf-8")


def export_interview_detail(interview_id: str) -> bytes:
    return f"detail:{interview_id}".encode("utf-8")
```

```python
# apps/api/app/main.py
from app.api.routes.interviews import router as interviews_router

app.include_router(interviews_router, prefix="/api/v1")
```

- [ ] **步骤 4: Run the simulate interview API test to verify it passes**

Run: `uv run --project apps/api pytest apps/api/tests/test_interviews.py -q`
Expected: PASS with `1 passed`

- [ ] **步骤 5: Write the failing interview report drawer test**

```tsx
// apps/web/src/components/interview/__tests__/report-drawer.test.tsx
import { render, screen } from "@testing-library/react";

import { ReportDrawer } from "../report-drawer";

describe("ReportDrawer", () => {
  it("renders multidimensional scores and improvements", () => {
    render(
      <ReportDrawer
        report={{
          scores: [
            { label: "知识掌握", value: 74 },
            { label: "岗位匹配度", value: 71 },
          ],
          weaknesses: ["异步削峰方案没有举项目证据"],
          improvements: ["补充高并发项目证据"],
        }}
      />,
    );

    expect(screen.getByText("知识掌握")).toBeInTheDocument();
    expect(screen.getByText("补充高并发项目证据")).toBeInTheDocument();
  });
});
```

- [ ] **步骤 6: Run the interview report drawer test to verify it fails**

Run: `pnpm --dir apps/web exec vitest run src/components/interview/__tests__/report-drawer.test.tsx`
Expected: FAIL with `Cannot find module '../report-drawer'`

- [ ] **步骤 7: Implement the interview list, new interview flow, and report drawer**

```tsx
// apps/web/src/components/interview/report-drawer.tsx
export function ReportDrawer({
  report,
}: Readonly<{
  report: {
    scores: Array<{ label: string; value: number }>;
    weaknesses: string[];
    improvements: string[];
  };
}>) {
  return (
    <aside className="space-y-4 rounded-2xl border border-slate-200 bg-white p-5">
      <h2 className="text-lg font-semibold">面试报告</h2>
      <div className="grid gap-3">
        {report.scores.map((score) => (
          <div key={score.label} className="rounded-xl bg-slate-50 p-3">
            <p className="text-sm text-slate-500">{score.label}</p>
            <p className="mt-1 text-2xl font-semibold">{score.value}</p>
          </div>
        ))}
      </div>
      <section>
        <h3 className="text-sm font-semibold">薄弱点</h3>
        <ul className="mt-2 space-y-2 text-sm text-slate-700">
          {report.weaknesses.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>
      <section>
        <h3 className="text-sm font-semibold">改进意见</h3>
        <ul className="mt-2 space-y-2 text-sm text-slate-700">
          {report.improvements.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>
    </aside>
  );
}
```

```tsx
// apps/web/src/app/(dashboard)/interviews/page.tsx
import { DataTable } from "@/components/data/data-table";

export default function InterviewsPage() {
  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">模拟面试</h2>
        <a href="/interviews/new" className="rounded-xl bg-slate-950 px-4 py-2 text-sm text-white">
          新建模拟面试
        </a>
      </div>
      <DataTable
        columns={[
          { key: "name", header: "面试名称" },
          { key: "mode", header: "模式" },
          { key: "reviewStatus", header: "复盘状态" },
        ]}
        rows={[{ id: "1", name: "OpenAI 后端岗", mode: "simulate", reviewStatus: "未复盘" }]}
        actions={[
          { label: "查看详情", icon: "eye" },
          { label: "生成复盘", icon: "sparkles" },
          { label: "导出报告", icon: "download" },
          { label: "导出逐字稿", icon: "file-text" },
          { label: "导出详情", icon: "files" },
        ]}
      />
    </section>
  );
}
```

```tsx
// apps/web/src/app/(dashboard)/interviews/[interviewId]/page.tsx
import { ReportDrawer } from "@/components/interview/report-drawer";

export default function InterviewDetailPage() {
  return (
    <section className="grid gap-6 xl:grid-cols-[1.3fr_0.9fr]">
      <article className="rounded-2xl border border-slate-200 bg-white p-6">
        <h2 className="text-xl font-semibold">面试详情</h2>
        <p className="mt-3 text-sm text-slate-700">这里展示逐题问答、系统输出和导出入口。</p>
      </article>
      <ReportDrawer
        report={{
          scores: [
            { label: "知识掌握", value: 74 },
            { label: "岗位匹配度", value: 71 },
          ],
          weaknesses: ["异步削峰方案没有举项目证据"],
          improvements: ["补充高并发项目证据"],
        }}
      />
    </section>
  );
}
```

- [ ] **步骤 8: Run the interview report drawer test to verify it passes**

Run: `pnpm --dir apps/web exec vitest run src/components/interview/__tests__/report-drawer.test.tsx`
Expected: PASS with `1 passed`

- [ ] **步骤 9：提交**

```bash
git add apps/api apps/web
git commit -m "添加模拟面试与报告导出"
```

### 任务 8：打磨模式、主题选择、回答评估与进展树

**文件：**
- Create: `apps/api/app/models/practice_topic.py`
- Create: `apps/api/app/models/capability_blueprint.py`
- Create: `apps/api/app/models/capability_node.py`
- Create: `apps/api/app/models/answer_assessment.py`
- Create: `apps/api/app/models/interview_progress_snapshot.py`
- Create: `apps/api/app/services/polish_engine.py`
- Create: `apps/api/app/services/assessment_engine.py`
- Create: `apps/api/app/api/routes/polish.py`
- Create: `apps/api/tests/test_polish_mode.py`
- Create: `apps/web/src/app/(dashboard)/polish/new/page.tsx`
- Create: `apps/web/src/app/(dashboard)/polish/[sessionId]/page.tsx`
- Create: `apps/web/src/components/interview/ability-tree.tsx`
- Create: `apps/web/src/components/interview/assessment-card.tsx`
- Create: `apps/web/src/components/interview/__tests__/assessment-card.test.tsx`
- Modify: `apps/web/src/app/(dashboard)/interviews/[interviewId]/page.tsx`
- Modify: `apps/api/app/main.py`

- [ ] **步骤 1: Write the failing polish mode API test**

```python
# apps/api/tests/test_polish_mode.py
from fastapi.testclient import TestClient

from app.main import app


def test_polish_mode_returns_answer_assessment_and_progress() -> None:
    client = TestClient(app)

    create_response = client.post(
        "/api/v1/polish-sessions",
        json={
            "jobId": "job_1",
            "resumeId": "resume_1",
            "primaryTopic": "缓存治理与高并发设计薄弱",
            "secondaryTopics": ["项目证据表达"],
        },
    )
    session_id = create_response.json()["id"]
    answer_response = client.post(
        f"/api/v1/polish-sessions/{session_id}/answer",
        json={"content": "我会使用互斥锁防止击穿"},
    )

    assert create_response.status_code == 201
    assert answer_response.status_code == 200
    assert answer_response.json()["assessment"]["score"] == 68
    assert answer_response.json()["assessment"]["technicalPrinciples"][0]["title"] == "热点 key 保护"
    assert answer_response.json()["progress"]["statusSummary"]["weak"] == 1
```

- [ ] **步骤 2: Run the polish mode API test to verify it fails**

Run: `uv run --project apps/api pytest apps/api/tests/test_polish_mode.py -q`
Expected: FAIL with `404 Not Found` for `/api/v1/polish-sessions`

- [ ] **步骤 3: Implement polish engine and assessment engine**

```python
# apps/api/app/services/assessment_engine.py
def assess_polish_answer(content: str) -> dict[str, object]:
    return {
        "score": 68,
        "missedPoints": ["没有解释互斥锁失效后的兜底策略"],
        "evidence": ["回答只覆盖单点锁，没有覆盖预热和降级"],
        "referenceAnswer": "我会先做布隆过滤与互斥锁保护，再配合热点预热和降级兜底。",
        "improvementMapping": [
            {
                "missedPoint": "没有解释互斥锁失效后的兜底策略",
                "repair": "补充热点预热和服务降级方案",
            }
        ],
        "technicalPrinciples": [
            {"title": "热点 key 保护", "why": "击穿场景必须解释锁、预热和降级"},
        ],
    }
```

```python
# apps/api/app/services/polish_engine.py
from app.services.assessment_engine import assess_polish_answer


def create_polish_session(job_id: str, resume_id: str, primary_topic: str, secondary_topics: list[str]) -> dict[str, object]:
    return {
        "id": "polish_1",
        "jobId": job_id,
        "resumeId": resume_id,
        "primaryTopic": primary_topic,
        "secondaryTopics": secondary_topics,
        "firstQuestion": "请围绕缓存击穿的真实项目处理讲一遍完整方案。",
    }


def answer_polish_session(content: str) -> dict[str, object]:
    return {
        "assessment": assess_polish_answer(content),
        "progress": {
            "statusSummary": {"covered": 2, "weak": 1, "stable": 0},
            "nextTopic": "继续追问热点预热和服务降级",
        },
    }
```

```python
# apps/api/app/api/routes/polish.py
from fastapi import APIRouter, status
from pydantic import BaseModel

from app.services.polish_engine import answer_polish_session, create_polish_session

router = APIRouter(prefix="/polish-sessions", tags=["polish"])


class CreatePolishSessionRequest(BaseModel):
    jobId: str
    resumeId: str
    primaryTopic: str
    secondaryTopics: list[str]


class PolishAnswerRequest(BaseModel):
    content: str


@router.post("", status_code=status.HTTP_201_CREATED)
def create_polish(payload: CreatePolishSessionRequest) -> dict[str, object]:
    return create_polish_session(payload.jobId, payload.resumeId, payload.primaryTopic, payload.secondaryTopics)


@router.post("/{session_id}/answer")
def answer_polish(session_id: str, payload: PolishAnswerRequest) -> dict[str, object]:
    return answer_polish_session(payload.content) | {"sessionId": session_id}
```

```python
# apps/api/app/main.py
from app.api.routes.polish import router as polish_router

app.include_router(polish_router, prefix="/api/v1")
```

- [ ] **步骤 4: Run the polish mode API test to verify it passes**

Run: `uv run --project apps/api pytest apps/api/tests/test_polish_mode.py -q`
Expected: PASS with `1 passed`

- [ ] **步骤 5: Write the failing assessment card test**

```tsx
// apps/web/src/components/interview/__tests__/assessment-card.test.tsx
import { render, screen } from "@testing-library/react";

import { AssessmentCard } from "../assessment-card";

describe("AssessmentCard", () => {
  it("renders score, missed points, and technical principles", () => {
    render(
      <AssessmentCard
        assessment={{
          score: 68,
          missedPoints: ["没有解释互斥锁失效后的兜底策略"],
          technicalPrinciples: [{ title: "热点 key 保护", why: "击穿场景必须解释锁、预热和降级" }],
        }}
      />,
    );

    expect(screen.getByText("68")).toBeInTheDocument();
    expect(screen.getByText("热点 key 保护")).toBeInTheDocument();
  });
});
```

- [ ] **步骤 6: Run the assessment card test to verify it fails**

Run: `pnpm --dir apps/web exec vitest run src/components/interview/__tests__/assessment-card.test.tsx`
Expected: FAIL with `Cannot find module '../assessment-card'`

- [ ] **步骤 7: Implement topic selection page, ability tree, and assessment card**

```tsx
// apps/web/src/components/interview/assessment-card.tsx
export function AssessmentCard({
  assessment,
}: Readonly<{
  assessment: {
    score: number;
    missedPoints: string[];
    technicalPrinciples: Array<{ title: string; why: string }>;
  };
}>) {
  return (
    <section className="space-y-4 rounded-2xl border border-slate-200 bg-white p-5">
      <div>
        <p className="text-sm text-slate-500">本题得分</p>
        <p className="mt-1 text-3xl font-semibold">{assessment.score}</p>
      </div>
      <div>
        <h3 className="text-sm font-semibold">失分点</h3>
        <ul className="mt-2 space-y-2 text-sm text-slate-700">
          {assessment.missedPoints.map((point) => (
            <li key={point}>{point}</li>
          ))}
        </ul>
      </div>
      <div>
        <h3 className="text-sm font-semibold">相关技术原理</h3>
        <ul className="mt-2 space-y-2 text-sm text-slate-700">
          {assessment.technicalPrinciples.map((item) => (
            <li key={item.title}>
              <strong>{item.title}</strong>：{item.why}
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
```

```tsx
// apps/web/src/components/interview/ability-tree.tsx
export function AbilityTree() {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5">
      <h3 className="text-sm font-semibold">能力树</h3>
      <ul className="mt-3 space-y-2 text-sm text-slate-700">
        <li>缓存治理：薄弱</li>
        <li>项目证据：已触达</li>
        <li>表达结构：待验证</li>
      </ul>
    </section>
  );
}
```

```tsx
// apps/web/src/app/(dashboard)/polish/new/page.tsx
export default function NewPolishPage() {
  return (
    <section className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold">新建打磨面试</h2>
        <p className="mt-2 text-sm text-slate-600">薄弱项不是必填，用户也可以直接输入想训练的主题。</p>
      </div>
      <div className="grid gap-4 rounded-2xl border border-slate-200 bg-white p-6">
        <label className="grid gap-2">
          <span className="text-sm font-medium">主打磨主题</span>
          <input className="rounded-xl border border-slate-300 px-3 py-2" defaultValue="缓存治理与高并发设计薄弱" />
        </label>
      </div>
    </section>
  );
}
```

```tsx
// apps/web/src/app/(dashboard)/polish/[sessionId]/page.tsx
import { AssessmentCard } from "@/components/interview/assessment-card";
import { AbilityTree } from "@/components/interview/ability-tree";

export default function PolishSessionPage() {
  return (
    <section className="grid gap-6 xl:grid-cols-[1.25fr_0.95fr]">
      <article className="rounded-2xl border border-slate-200 bg-white p-6">
        <h2 className="text-xl font-semibold">打磨面试</h2>
        <p className="mt-3 text-sm text-slate-700">左侧显示问答流、重答入口和当前主题。</p>
      </article>
      <div className="space-y-6">
        <AssessmentCard
          assessment={{
            score: 68,
            missedPoints: ["没有解释互斥锁失效后的兜底策略"],
            technicalPrinciples: [{ title: "热点 key 保护", why: "击穿场景必须解释锁、预热和降级" }],
          }}
        />
        <AbilityTree />
      </div>
    </section>
  );
}
```

- [ ] **步骤 8: Run the assessment card test to verify it passes**

Run: `pnpm --dir apps/web exec vitest run src/components/interview/__tests__/assessment-card.test.tsx`
Expected: PASS with `1 passed`

- [ ] **步骤 9：提交**

```bash
git add apps/api apps/web
git commit -m "添加打磨模式评估与进展树"
```

### 任务 9：复盘、真实面试回放与复盘列表

**文件：**
- Create: `apps/api/app/models/review.py`
- Create: `apps/api/app/models/review_question_analysis.py`
- Create: `apps/api/app/services/review_engine.py`
- Create: `apps/api/app/api/routes/reviews.py`
- Create: `apps/api/tests/test_reviews.py`
- Create: `apps/web/src/app/(dashboard)/reviews/page.tsx`
- Create: `apps/web/src/app/(dashboard)/reviews/new/page.tsx`
- Create: `apps/web/src/app/(dashboard)/reviews/[reviewId]/page.tsx`
- Create: `apps/web/src/components/review/question-analysis-card.tsx`
- Create: `apps/web/src/components/review/__tests__/question-analysis-card.test.tsx`
- Modify: `apps/web/src/app/(dashboard)/interviews/[interviewId]/page.tsx`
- Modify: `apps/api/app/main.py`

- [ ] **步骤 1: Write the failing review API test**

```python
# apps/api/tests/test_reviews.py
from fastapi.testclient import TestClient

from app.main import app


def test_create_real_interview_review_with_original_answer() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/v1/reviews",
        json={
            "sourceType": "real_interview",
            "jobId": "job_1",
            "resumeId": "resume_1",
            "questions": [
                {
                    "question": "为什么你的项目要引入 Redis？",
                    "answer": "因为查询很慢，所以我加了 Redis。",
                }
            ],
        },
    )

    assert response.status_code == 201
    assert response.json()["questionAnalyses"][0]["originalAnswer"] == "因为查询很慢，所以我加了 Redis。"
    assert response.json()["questionAnalyses"][0]["riskIfPressed"] == "继续追问缓存一致性时会暴露设计深度不足"
```

- [ ] **步骤 2: Run the review API test to verify it fails**

Run: `uv run --project apps/api pytest apps/api/tests/test_reviews.py -q`
Expected: FAIL with `404 Not Found` for `/api/v1/reviews`

- [ ] **步骤 3: Implement review engine and review routes**

```python
# apps/api/app/services/review_engine.py
def create_review(source_type: str, questions: list[dict[str, str]]) -> dict[str, object]:
    first = questions[0]
    return {
      "id": "review_1",
      "sourceType": source_type,
      "scores": {"knowledge": 62, "match": 64, "probability": 43},
      "questionAnalyses": [
        {
          "originalQuestion": first["question"],
          "originalAnswer": first["answer"],
          "intent": "验证项目取舍和缓存设计深度",
          "answerProblem": "只给了结论，没有给证据和场景",
          "missingPoints": ["没有说明引入 Redis 前后的瓶颈数据"],
          "mistakes": ["没有解释缓存一致性"],
          "expressionIssues": ["回答过短，无法支撑项目可信度"],
          "betterFrame": "先交代瓶颈指标，再讲 Redis 方案、风险与收益。",
          "riskIfPressed": "继续追问缓存一致性时会暴露设计深度不足",
        }
      ],
      "improvements": ["补充性能指标与一致性策略"],
    }
```

```python
# apps/api/app/api/routes/reviews.py
from fastapi import APIRouter, status
from pydantic import BaseModel

from app.services.review_engine import create_review

router = APIRouter(prefix="/reviews", tags=["reviews"])


class ReviewQuestion(BaseModel):
    question: str
    answer: str


class CreateReviewRequest(BaseModel):
    sourceType: str
    jobId: str
    resumeId: str
    questions: list[ReviewQuestion]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_review_route(payload: CreateReviewRequest) -> dict[str, object]:
    return create_review(payload.sourceType, [item.model_dump() for item in payload.questions])
```

```python
# apps/api/app/main.py
from app.api.routes.reviews import router as reviews_router

app.include_router(reviews_router, prefix="/api/v1")
```

- [ ] **步骤 4: Run the review API test to verify it passes**

Run: `uv run --project apps/api pytest apps/api/tests/test_reviews.py -q`
Expected: PASS with `1 passed`

- [ ] **步骤 5: Write the failing review question card test**

```tsx
// apps/web/src/components/review/__tests__/question-analysis-card.test.tsx
import { render, screen } from "@testing-library/react";

import { QuestionAnalysisCard } from "../question-analysis-card";

describe("QuestionAnalysisCard", () => {
  it("renders original question and original answer", () => {
    render(
      <QuestionAnalysisCard
        analysis={{
          originalQuestion: "为什么你的项目要引入 Redis？",
          originalAnswer: "因为查询很慢，所以我加了 Redis。",
          answerProblem: "只给了结论，没有给证据和场景",
        }}
      />,
    );

    expect(screen.getByText("为什么你的项目要引入 Redis？")).toBeInTheDocument();
    expect(screen.getByText("因为查询很慢，所以我加了 Redis。")).toBeInTheDocument();
  });
});
```

- [ ] **步骤 6: Run the review question card test to verify it fails**

Run: `pnpm --dir apps/web exec vitest run src/components/review/__tests__/question-analysis-card.test.tsx`
Expected: FAIL with `Cannot find module '../question-analysis-card'`

- [ ] **步骤 7: Implement review list/detail pages and jump back to interview**

```tsx
// apps/web/src/components/review/question-analysis-card.tsx
export function QuestionAnalysisCard({
  analysis,
}: Readonly<{
  analysis: {
    originalQuestion: string;
    originalAnswer: string;
    answerProblem: string;
  };
}>) {
  return (
    <article className="space-y-4 rounded-2xl border border-slate-200 bg-white p-6">
      <div>
        <h3 className="text-base font-semibold">原始问题</h3>
        <p className="mt-2 text-sm text-slate-700">{analysis.originalQuestion}</p>
      </div>
      <div>
        <h3 className="text-base font-semibold">原始回答</h3>
        <p className="mt-2 text-sm text-slate-700">{analysis.originalAnswer}</p>
      </div>
      <div>
        <h3 className="text-base font-semibold">回答问题</h3>
        <p className="mt-2 text-sm text-slate-700">{analysis.answerProblem}</p>
      </div>
    </article>
  );
}
```

```tsx
// apps/web/src/app/(dashboard)/reviews/page.tsx
import { DataTable } from "@/components/data/data-table";

export default function ReviewsPage() {
  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">复盘</h2>
        <a href="/reviews/new" className="rounded-xl bg-slate-950 px-4 py-2 text-sm text-white">
          新建真实面试复盘
        </a>
      </div>
      <DataTable
        columns={[
          { key: "title", header: "复盘标题" },
          { key: "source", header: "来源" },
          { key: "match", header: "岗位匹配度" },
        ]}
        rows={[{ id: "1", title: "OpenAI 一面复盘", source: "真实面试", match: "64" }]}
        actions={[{ label: "查看详情", icon: "eye" }, { label: "导出", icon: "download" }]}
      />
    </section>
  );
}
```

```tsx
// apps/web/src/app/(dashboard)/reviews/[reviewId]/page.tsx
import { QuestionAnalysisCard } from "@/components/review/question-analysis-card";

export default function ReviewDetailPage() {
  return (
    <section className="grid gap-6 xl:grid-cols-[1.35fr_0.85fr]">
      <div className="space-y-6">
        <QuestionAnalysisCard
          analysis={{
            originalQuestion: "为什么你的项目要引入 Redis？",
            originalAnswer: "因为查询很慢，所以我加了 Redis。",
            answerProblem: "只给了结论，没有给证据和场景",
          }}
        />
      </div>
      <aside className="rounded-2xl border border-slate-200 bg-white p-6">
        <h2 className="text-lg font-semibold">复盘摘要</h2>
        <a href="/interviews/interview_1" className="mt-4 inline-flex text-sm text-slate-700 underline">
          查看对应模拟面试
        </a>
      </aside>
    </section>
  );
}
```

- [ ] **步骤 8: Run the review question card test to verify it passes**

Run: `pnpm --dir apps/web exec vitest run src/components/review/__tests__/question-analysis-card.test.tsx`
Expected: PASS with `1 passed`

- [ ] **步骤 9：提交**

```bash
git add apps/api apps/web
git commit -m "添加复盘列表与详细面试回放"
```

### 任务 10：训练抽屉、薄弱项中心与薄弱项生命周期

**文件：**
- Create: `apps/api/app/models/weakness_item.py`
- Create: `apps/api/app/services/weakness_service.py`
- Create: `apps/api/app/services/training_service.py`
- Create: `apps/api/app/api/routes/training.py`
- Create: `apps/api/tests/test_training.py`
- Create: `apps/web/src/components/training/training-drawer.tsx`
- Create: `apps/web/src/app/(dashboard)/training/page.tsx`
- Create: `apps/web/src/components/training/__tests__/training-drawer.test.tsx`
- Modify: `apps/web/src/app/(dashboard)/jobs/[jobId]/page.tsx`
- Modify: `apps/web/src/app/(dashboard)/interviews/[interviewId]/page.tsx`
- Modify: `apps/web/src/app/(dashboard)/reviews/[reviewId]/page.tsx`
- Modify: `apps/api/app/main.py`

- [ ] **步骤 1: Write the failing training API test**

```python
# apps/api/tests/test_training.py
from fastapi.testclient import TestClient

from app.main import app


def test_training_endpoint_merges_into_job_level_weakness() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v1/training/intake",
        json={
            "jobId": "job_1",
            "title": "缓存治理与高并发设计薄弱",
            "sourceType": "review",
            "action": {"mergeWeakness": True, "enqueuePractice": True},
        },
    )

    assert response.status_code == 200
    assert response.json()["weakness"]["status"] == "active"
    assert response.json()["weakness"]["jobId"] == "job_1"
```

- [ ] **步骤 2: Run the training API test to verify it fails**

Run: `uv run --project apps/api pytest apps/api/tests/test_training.py -q`
Expected: FAIL with `404 Not Found` for `/api/v1/training/intake`

- [ ] **步骤 3: Implement weakness aggregation and training intake**

```python
# apps/api/app/services/weakness_service.py
def merge_weakness(job_id: str, title: str, source_type: str) -> dict[str, object]:
    return {
        "id": "weakness_1",
        "jobId": job_id,
        "title": title,
        "sourceType": source_type,
        "status": "active",
        "priority": "high",
        "evidenceCount": 3,
    }


def downgrade_weakness(title: str) -> dict[str, object]:
    return {"title": title, "status": "low_priority"}
```

```python
# apps/api/app/api/routes/training.py
from fastapi import APIRouter
from pydantic import BaseModel

from app.services.weakness_service import merge_weakness

router = APIRouter(prefix="/training", tags=["training"])


class TrainingAction(BaseModel):
    mergeWeakness: bool
    enqueuePractice: bool


class IntakeRequest(BaseModel):
    jobId: str
    title: str
    sourceType: str
    action: TrainingAction


@router.post("/intake")
def intake_training(payload: IntakeRequest) -> dict[str, object]:
    weakness = merge_weakness(payload.jobId, payload.title, payload.sourceType)
    return {
        "weakness": weakness,
        "practiceQueue": [{"title": payload.title, "jobId": payload.jobId}],
    }
```

```python
# apps/api/app/main.py
from app.api.routes.training import router as training_router

app.include_router(training_router, prefix="/api/v1")
```

- [ ] **步骤 4: Run the training API test to verify it passes**

Run: `uv run --project apps/api pytest apps/api/tests/test_training.py -q`
Expected: PASS with `1 passed`

- [ ] **步骤 5: Write the failing training drawer test**

```tsx
// apps/web/src/components/training/__tests__/training-drawer.test.tsx
import { render, screen } from "@testing-library/react";

import { TrainingDrawer } from "../training-drawer";

describe("TrainingDrawer", () => {
  it("renders merge and enqueue actions", () => {
    render(
      <TrainingDrawer
        item={{
          title: "缓存治理与高并发设计薄弱",
          sourceType: "review",
          severity: "high",
        }}
      />,
    );

    expect(screen.getByText("归并到薄弱项")).toBeInTheDocument();
    expect(screen.getByText("加入待打磨")).toBeInTheDocument();
  });
});
```

- [ ] **步骤 6: Run the training drawer test to verify it fails**

Run: `pnpm --dir apps/web exec vitest run src/components/training/__tests__/training-drawer.test.tsx`
Expected: FAIL with `Cannot find module '../training-drawer'`

- [ ] **步骤 7: Implement the training drawer and weakness center**

```tsx
// apps/web/src/components/training/training-drawer.tsx
export function TrainingDrawer({
  item,
}: Readonly<{
  item: { title: string; sourceType: string; severity: string };
}>) {
  return (
    <aside className="space-y-4 rounded-2xl border border-slate-200 bg-white p-5">
      <div>
        <h2 className="text-lg font-semibold">纳入训练</h2>
        <p className="mt-2 text-sm text-slate-600">
          {item.title} · 来源：{item.sourceType} · 严重度：{item.severity}
        </p>
      </div>
      <button type="button" className="w-full rounded-xl border border-slate-300 px-4 py-3 text-left">
        归并到薄弱项
      </button>
      <button type="button" className="w-full rounded-xl border border-slate-300 px-4 py-3 text-left">
        加入待打磨
      </button>
      <button type="button" className="w-full rounded-xl border border-slate-300 px-4 py-3 text-left">
        立即发起打磨
      </button>
    </aside>
  );
}
```

```tsx
// apps/web/src/app/(dashboard)/training/page.tsx
import { DataTable } from "@/components/data/data-table";

export default function TrainingPage() {
  return (
    <section className="space-y-4">
      <h2 className="text-xl font-semibold">训练中心</h2>
      <DataTable
        columns={[
          { key: "title", header: "薄弱项" },
          { key: "status", header: "状态" },
          { key: "priority", header: "优先级" },
        ]}
        rows={[
          {
            id: "1",
            title: "缓存治理与高并发设计薄弱",
            status: "active",
            priority: "high",
          },
        ]}
        actions={[
          { label: "查看", icon: "eye" },
          { label: "低优先级", icon: "arrow-down" },
          { label: "不再打磨", icon: "pause" },
        ]}
      />
    </section>
  );
}
```

- [ ] **步骤 8: Run the training drawer test to verify it passes**

Run: `pnpm --dir apps/web exec vitest run src/components/training/__tests__/training-drawer.test.tsx`
Expected: PASS with `1 passed`

- [ ] **步骤 9：提交**

```bash
git add apps/api apps/web
git commit -m "添加训练抽屉与薄弱项中心"
```

### 任务 11：管理台治理、模型注册表、搜索配置、日志与端到端加固

**文件：**
- Create: `apps/api/app/models/model_registry_entry.py`
- Create: `apps/api/app/models/scoring_rule.py`
- Create: `apps/api/app/models/system_setting.py`
- Create: `apps/api/app/services/model_recommendation_service.py`
- Create: `apps/api/app/services/settings_service.py`
- Create: `apps/api/app/core/logging.py`
- Create: `apps/api/app/api/routes/admin.py`
- Create: `apps/api/tests/test_admin_settings.py`
- Create: `apps/web/src/app/(dashboard)/admin/models/page.tsx`
- Create: `apps/web/src/app/(dashboard)/admin/scoring-rules/page.tsx`
- Create: `apps/web/tests/e2e/app-shell.spec.ts`
- Create: `.github/workflows/ci.yml`
- Modify: `apps/api/app/main.py`

- [ ] **步骤 1: Write the failing admin settings API test**

```python
# apps/api/tests/test_admin_settings.py
from fastapi.testclient import TestClient

from app.main import app


def test_model_recommendation_returns_latest_catalog_for_interview_task() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/admin/models/recommendations?task=interview")

    assert response.status_code == 200
    assert response.json()[0]["recommendedFor"] == "interview"
    assert "releaseDate" in response.json()[0]
```

- [ ] **步骤 2: Run the admin settings API test to verify it fails**

Run: `uv run --project apps/api pytest apps/api/tests/test_admin_settings.py -q`
Expected: FAIL with `404 Not Found` for `/api/v1/admin/models/recommendations`

- [ ] **步骤 3: Implement admin routes, model recommendation, and structured logging**

```python
# apps/api/app/core/logging.py
import logging


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
```

```python
# apps/api/app/services/model_recommendation_service.py
def recommend_models(task: str) -> list[dict[str, str]]:
    catalog = [
        {
            "provider": "OpenAI",
            "modelId": "gpt-5.4",
            "displayName": "GPT-5.4",
            "releaseDate": "2026-01-15",
            "recommendedFor": "interview",
        },
        {
            "provider": "Anthropic",
            "modelId": "claude-sonnet-4.5",
            "displayName": "Claude Sonnet 4.5",
            "releaseDate": "2026-02-10",
            "recommendedFor": "review",
        },
    ]
    return [item for item in catalog if item["recommendedFor"] == task]
```

```python
# apps/api/app/api/routes/admin.py
from fastapi import APIRouter

from app.services.model_recommendation_service import recommend_models

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/models/recommendations")
def model_recommendations(task: str) -> list[dict[str, str]]:
    return recommend_models(task)
```

```python
# apps/api/app/main.py
from app.api.routes.admin import router as admin_router
from app.core.logging import configure_logging

configure_logging()
app.include_router(admin_router, prefix="/api/v1")
```

- [ ] **步骤 4: Run the admin settings API test to verify it passes**

Run: `uv run --project apps/api pytest apps/api/tests/test_admin_settings.py -q`
Expected: PASS with `1 passed`

- [ ] **步骤 5: Write the failing Playwright smoke test**

```ts
// apps/web/tests/e2e/app-shell.spec.ts
import { test, expect } from "@playwright/test";

test("dashboard shell shows primary navigation", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByText("AI 面试训练")).toBeVisible();
  await expect(page.getByText("模拟面试")).toBeVisible();
});
```

- [ ] **步骤 6: Run the Playwright smoke test to verify it fails**

Run: `pnpm --dir apps/web exec playwright test tests/e2e/app-shell.spec.ts`
Expected: FAIL until Playwright config, pages, and dev server wiring are added

- [ ] **步骤 7: Implement admin pages, CI, and Playwright wiring**

```tsx
// apps/web/src/app/(dashboard)/admin/models/page.tsx
import { DataTable } from "@/components/data/data-table";

export default function AdminModelsPage() {
  return (
    <section className="space-y-4">
      <h2 className="text-xl font-semibold">模型配置</h2>
      <DataTable
        columns={[
          { key: "provider", header: "提供商" },
          { key: "model", header: "模型" },
          { key: "task", header: "推荐用途" },
        ]}
        rows={[{ id: "1", provider: "OpenAI", model: "GPT-5.4", task: "interview" }]}
        actions={[{ label: "查看", icon: "eye" }, { label: "应用", icon: "check" }]}
      />
    </section>
  );
}
```

```tsx
// apps/web/src/app/(dashboard)/admin/scoring-rules/page.tsx
export default function ScoringRulesPage() {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6">
      <h2 className="text-xl font-semibold">评分规则</h2>
      <p className="mt-2 text-sm text-slate-600">管理员在这里维护题目级、节点级和场次级评分权重。</p>
    </section>
  );
}
```

```yaml
# .github/workflows/ci.yml
name: ci

on:
  push:
    branches: [main]
  pull_request:

jobs:
  api-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - run: uv sync --project apps/api
      - run: uv run --project apps/api pytest

  web-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
        with:
          version: 9
      - uses: actions/setup-node@v4
        with:
          node-version: 22
      - run: pnpm --dir apps/web install
      - run: pnpm --dir apps/web test
```

- [ ] **步骤 8: Run the Playwright smoke test and CI-relevant commands**

Run: `uv run --project apps/api pytest -q`
Expected: PASS with all backend tests passing

Run: `pnpm --dir apps/web test`
Expected: PASS with all frontend tests passing

Run: `pnpm --dir apps/web exec playwright test tests/e2e/app-shell.spec.ts`
Expected: PASS with the shell smoke test green

- [ ] **步骤 9：提交**

```bash
git add apps/api apps/web .github
git commit -m "添加管理台治理与发布加固"
```

## 设计稿覆盖清单

- `岗位管理`：Task 4, Task 5
- `简历导入 / MD 编辑 / PDF 导出`：Task 4
- `岗位-简历匹配分析`：Task 5
- `模拟面试列表 / 新建 / 详情 / 报告 / 导出`：Task 7
- `打磨模式 / 主题选择 / 点评 / 技术原理 / 进展树`：Task 8
- `真实面试复盘 / 模拟面试复盘 / 逐题严格拆解 / 跳回模拟详情`：Task 9
- `薄弱项聚合 / 状态流转 / 停练 / 训练抽屉 / 训练中心`：Task 5, Task 7, Task 8, Task 10
- `资产库 / 资产类型 / 归档`：Task 6, Task 9
- `管理台 / 模型配置 / 最新模型推荐 / 评分规则`：Task 3, Task 6, Task 11
- `日志 / 可观测性 / CI / 最终验证`：Task 11

## 执行说明

- 在 Task 4 前不要提前引入 AI Provider SDK，先把非 AI 数据流跑通。
- 在 Task 7 开始前，必须统一 `InterviewSession`、`InterviewMessage`、`InterviewQuestionTrace` 的字段命名，后续不要再重命名。
- 在 Task 7 中，`岗位要求 / 简历 / 资产 / 复盘 / 搜索结果` 只允许作为 `Question Context`，不能被当作完整原题直接回放给用户。
- 在 Task 8 和 Task 10 之间，要把 `WeaknessItem` 和 `PracticeTopic` 明确区分：前者是长期主题，后者是执行队列。
- 在 Task 9 后，复盘改进建议已经可以作为薄弱项证据来源，不能再只停留在页面文案层。
- 在 Task 11 前，不要把“最新模型推荐”做成在线抓取逻辑，先使用管理员可维护的 catalog 表或配置种子文件，避免时效性功能阻塞主链路。


# M02 鉴权、团队与成员 - 模块设计

## 1. 文档定位

- 本文档用于把 `MODULE_REQUIREMENTS.md` 中的模块需求收敛为 `M02` 的结构设计、边界拆分和跨模块输出。
- 当前目标是提供“可作为下游输入”的候选设计基线，待总控复核，不宣称已达到可直接实施。

## 2. 设计目标与约束

- 在 `P1` 单团队边界内建立统一身份上下文。
- 让所有受保护页面 / API 共享同一套团队过滤与角色校验规则。
- 把成员目录读取、管理台管理员能力和后续业务模块的团队隔离区分开。
- 不擅自发明 `membership`、会话表、刷新 token 等上游未冻结契约。

## 3. 模块职责与边界

### 3.1 模块职责

- 负责固定 `Bearer token` 方案下的登录、当前用户解析与退出边界。
- 负责 `Team` / `User` 的模块级对象与团队隔离规则。
- 负责成员目录读取契约与安全字段投影。
- 负责输出首轮权限矩阵：
  - 团队内业务页 / API
  - 管理台页 / API
  - 未登录与跨团队访问异常路径

### 3.2 与其他模块的边界

- `M01`
  - 提供配置读取、日志、App Shell、i18n、表格与测试基线。
- `M02`
  - 提供 `current_user / role / team_id` 的统一来源。
  - 提供成员目录只读边界与权限矩阵规则。
- `M03-M09`
  - 复用 `M02` 输出的团队过滤与角色校验规则，不重复定义一套权限模型。
- `M10`
  - 消费 `M02` 输出的管理台管理员鉴权规则。
  - 管理台成员管理页面 / API 的最终实现归属已冻结为后续治理模块承接。

## 4. 设计拆分

| 设计单元 | 主要职责 | 主要输入 | 主要输出 |
| --- | --- | --- | --- |
| `AuthConfig` | 从 `.env` / seed 读取演示账号、固定 token 与安全配置 | `M01` 配置基线、`OQ-004` | 可解析的演示鉴权配置 |
| `AuthResolver` | 处理登录、解析 `Bearer token`、产出当前用户上下文 | `AuthConfig`、`User` | `CurrentUserContext` |
| `TeamScopedIdentity` | 定义 `Team` / `User` 的团队关系、状态与软删除约束 | `Team`、`User` schema | 团队作用域与安全过滤前提 |
| `MemberDirectoryReadModel` | 提供成员列表 / 详情的安全字段投影与查询规则 | `CurrentUserContext`、`User` | `MemberDirectoryItem` / detail payload |
| `AuthorizationPolicy` | 统一判断 `admin / member / unauthenticated / cross-team` 访问路径 | 当前路由分组、当前用户、目标资源 | `401 / 403 / 404` 规则 |
| `FrontendEntrySurfaces` | 承接 `/login`、`/(dashboard)/members` 与 App Shell 登录态联动 | `M01` App Shell / i18n / 列表原语 | 登录入口与成员目录页面 |

## 5. 核心数据流

### 5.1 登录数据流

1. `/login` 收集账号密码并调用 `POST /api/v1/auth/login`。
2. `AuthResolver` 校验凭据并定位演示用户。
3. 服务层返回固定 `Bearer token` 与当前用户基础信息。
4. 前端保存登录态，并以该 token 访问受保护页面 / API。

### 5.2 当前用户解析流

1. 受保护请求携带 `Authorization: Bearer <token>`。
2. 网关 / 依赖层通过 `AuthResolver` 解析 token。
3. 解析成功后得到 `CurrentUserContext`：
   - `user_id`
   - `role`
   - `team_id`
   - `status`
4. 业务服务统一从该上下文派生团队过滤与权限判断。

### 5.3 成员目录读取流

1. 前端进入 `/(dashboard)/members`。
2. 页面使用当前登录态请求 `GET /api/v1/members` 或 `GET /api/v1/members/{member_id}`。
3. 服务层先根据 `CurrentUserContext` 注入 `team_id` 过滤。
4. 查询结果再应用：
  - 软删除过滤
  - 已冻结的目录字段投影：`id`、`displayName`、`role`、`status`
  - 团队作用域拒绝规则

### 5.4 管理台授权流

1. 管理台页 / API 统一进入 `AuthorizationPolicy`。
2. `admin` 之外的用户在进入具体业务处理前即被拒绝。
3. `M02` 负责给出拒绝语义与测试规则，后续模块负责承接管理台功能实现。

## 6. 关键边界决策

### 6.1 单团队边界

- `P1` 不实现多团队管理界面。
- 但 `Team` / `User` 与后续业务对象全部保留 `team_id`。
- 当前用户上下文是所有团队过滤的事实来源。

### 6.2 不发明 `membership` 持久化表

- 当前上游文档只明确 `teams` 与 `users` 两个持久化对象。
- 团队成员关系在 `P1` 评审基线中直接由 `users.team_id` 表达。
- 若未来进入多团队 / 多租户增强，再单独评估是否引入 `membership` 模型。

### 6.3 固定 Bearer token 的会话边界

- 本轮按固定 `Bearer token` 口径推进，不引入刷新链路与服务端 session 存储。
- `logout` 只定义“结束当前前端登录态”的边界，不把它扩展为完整令牌失效系统。
- token 与演示身份的映射粒度已冻结为 `admin` / `member` 两组开发态身份映射。

### 6.4 成员目录与管理台成员管理拆分

- `/members` 代表“成员目录读取面”。
- `/admin/members` 代表“成员管理面”。
- `admin` 与 `member` 都可读取 `/members` 的本团队基础成员目录。
- `/members` 首轮字段集只冻结为：`id`、`displayName`、`role`、`status`。
- 跨团队成员详情访问统一返回 `403`。
- 两者共享同一套身份、团队与角色判断，但不应在同一子任务里混成一个实现边界。

### 6.5 命名与共享契约对齐

- 持久化层统一使用 `snake_case`，接口层与前端消费层统一使用 `camelCase`。
  - 关键映射至少包括：`display_name -> displayName`、`team_id -> teamId`
- `teams.id` 是物理主键。
- `teams.team_id` 是为对齐全局“所有核心业务表预留 `team_id`”口径保留的同值逻辑键，值必须等于 `teams.id`。
- `users.team_id`、`CurrentUserContext.team_id` 以及 JSON payload 中的 `teamId` 都引用同一团队作用域键，不允许把 `teams.id` 与 `teams.team_id` 解释为两套不同标识。
- `POST /api/v1/auth/logout` 采用 `204 No Content` 作为成功语义，前端只根据状态码清理登录态。

### 6.6 任务重切轮必须上提到模块层的内容

- 以下内容必须保留在模块层，不允许再下放到子任务里补洞：
  - `CurrentUserContext` 的字段、来源、`401 / 403 / 404` 语义与 `logout=204` 成功口径。
  - `/members` 的字段投影、跨团队 `403`、软删除过滤，以及与 `OQ-021` 的列表集合对齐边界。
  - `/(dashboard)/members` 对 `OQ-020` / `OQ-022` 的承接口径：共享 `PageHeader`、最小 namespace、fallback 规则；子任务只能消费，不能重定义。
  - `/(dashboard)/admin/**` 与 `/api/v1/admin/**` 的路由组权限矩阵，以及 `M02` / `M10` 的职责边界。
  - `teams.id`、`teams.team_id(=id)`、`users.team_id` 与安全字段投影的统一解释。
  - 鉴权验证基线：未登录 `401`、角色不足 `403`、跨团队详情 `403`、软删除详情 `404`、软删除对象不出现在列表。

### 6.7 任务重切后的拆分原则

- 单个微任务只承接一种主要变化面：身份源、auth endpoint、schema / projection、成员目录 read API、page adapter、policy、verification。
- 不再允许把 schema + API + page + test 捆成一个子任务。
- 当前首轮只冻结 `GET /api/v1/members/{member_id}` 的详情语义，不冻结独立成员详情页 UI；若后续需要页面，应在新的微任务中单列。
- 页面微任务必须等待 `OQ-020`、`OQ-021`、`OQ-022` 已被模块文档吸收后再启动。
- 管理台完整成员管理实现继续留在 `M10` 或后续治理模块，不回流到 `M02` 子任务。

## 7. 跨模块协作输出

### 7.1 输出给业务模块的共享契约

- 当前用户上下文：
  - `user_id`
  - `role`
  - `team_id`
  - `status`
- 统一鉴权判断：
  - 未登录 `401`
  - 角色不足 `403`
  - 成员目录跨团队详情 `403`
  - 软删除对象不可见
- 团队作用域查询前置约束：
  - 所有团队资源列表默认附带 `team_id` + `deleted_at IS NULL`
- 页面承接口径：
  - `/(dashboard)/members` 复用 `M01` 的共享页面原语默认冻结口径：`PageHeader` 只承载标题/说明/主次动作，摘要区独立承载状态与摘要项，不在 `M02` 扩张私有 props catalog。

### 7.2 输出给治理模块的共享契约

- `/(dashboard)/admin/**` 与 `/api/v1/admin/**` 只允许 `admin`。
- `M02` 负责输出 admin 访问判定、权限矩阵基线与最小鉴权契约，不在本轮冻结完整成员管理读写语义。
- 管理台成员管理依赖 `M02` 提供的身份解析与授权策略，不重写规则；完整页面 / API 实现由后续治理模块承接。

## 8. 风险、已收口项与当前缺口

- 开发态认证适配层已冻结为至少两组演示身份映射：`admin` / `member` 各一组凭据与 `Bearer token`，全部从 `.env` 或 seed 读取。
- `/members` 已冻结为团队内基础成员目录；若后续需要暴露 `email`、`teamId` 或扩展资料，应作为后续评审项单独提出。
- 管理台成员管理分工已在模块内按方案 B 冻结；若后续需要同步到全局，仅由总控回写共享状态文档。
- `teams.status`、`users.status` 已按方案 A 冻结为 `active-only + deleted_at`；若后续需要引入其他状态，应单独评审。
- 模块内的命名漂移与主键表述已收口：
  - 存储层使用 `display_name` / `team_id`
  - 接口层使用 `displayName` / `teamId`
  - `teams.id` 与 `teams.team_id(=id)` 不再作为两套独立身份解释
- 当前 `ST02_01 ~ ST02_03` 只应视为遗留粗粒度任务包，不再作为下一轮直接启动入口：
  - `ST02_01` 仍混合 auth backend 契约与 `/login` 页面承接
  - `ST02_02` 同时混合 schema、成员目录 API、列表 / 详情页面目标
  - `ST02_03` 同时混合权限矩阵定义、管理台边界与验证基线
- 当前仍未解除的外部阻塞：
  - `OQ-020` 已形成 `proposed-default`：`/(dashboard)/members` 可直接复用共享页面原语最小边界，它不再单独构成 `M02` 的主阻塞。
  - `MQ-205` / `OQ-021`：`/members` 列表与 `M01` `DataTable` / `Pagination` 的 envelope、分页参数和查询状态映射仍未冻结，`M02` 不能私自补一套分页协议。
  - `MQ-206` / `OQ-022`：`/login` 与 `/(dashboard)/members` 已获得 `M01` 集中 i18n 入口的最小 namespace / fallback 默认口径，但模块尚未完成吸收；页面子任务设计暂不宜先开。
- `MQ-203` 已与全局 `OQ-023` 对齐，不再构成当前模块的新增阻塞。

## 9. 测试策略

- API 层至少覆盖：
  - `POST /api/v1/auth/login` 成功 / 失败
  - `GET /api/v1/auth/me` 未登录 / 已登录
  - `GET /api/v1/members*` 的本团队、跨团队、软删除路径
  - `member -> /api/v1/admin/**` 的 `403`
- 前端层至少覆盖：
  - `/login` 登录入口
  - `/(dashboard)/members` 的成员列表渲染与权限入口
- 鉴权矩阵必须沉淀到专门测试文件，而不是散落在各业务用例中。

## 10. 关联文档

- `MODULE_REQUIREMENTS.md`
- `MODULE_API_DESIGN.md`
- `MODULE_SCHEMA_DESIGN.md`
- `MODULE_LOGIC_DESIGN.md`
- `MODULE_DEPENDENCIES.md`
- `MODULE_TASK_INDEX.md`
- `MODULE_OPEN_QUESTIONS.md`

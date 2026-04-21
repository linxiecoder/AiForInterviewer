# M02 鉴权、团队与成员 - API 设计

## 1. 文档定位

- 本文档用于沉淀 `M02` 直接负责的接口契约，以及本模块输出给其他模块复用的权限矩阵基线。
- 当前目标是提供可评审、可供最低位复核的接口边界，明确哪些接口面已可审计、哪些仍未达到正式候选输入，而不是把所有字段细节伪装成已经完全定稿。

## 2. 接口范围

### 2.1 本模块直接承接的接口

- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `POST /api/v1/auth/logout`
- `GET /api/v1/members`
- `GET /api/v1/members/{member_id}`

### 2.2 本模块输出给其他模块复用的授权约束

- `/(dashboard)/admin/**`
- `/api/v1/admin/**`
- 所有团队作用域业务页 / API 的：
  - 登录态要求
  - 团队过滤要求
  - `401 / 403 / 404` 语义基线

## 3. 通用契约

### 3.1 鉴权方式

- 除 `POST /api/v1/auth/login` 外，其他本模块接口均为受保护接口。
- 受保护接口统一使用：
  - `Authorization: Bearer <token>`
- 当前口径定义为“JWT 前的开发态认证适配层”。
- 当前 `Bearer token` 只承担开发态认证适配职责，不应被业务层或前端当成最终认证形态。
- 当前已冻结的开发态身份映射至少包含：
  - `admin` 一组凭据 + 一组 token
  - `member` 一组凭据 + 一组 token
- token 来源必须是 `.env` 或种子配置，不允许在业务代码中写死真实凭据。

### 3.2 当前用户与当前团队

- 当前用户上下文必须由 `Bearer token` 解析得到。
- 团队作用域不得由客户端直接指定 `team_id` 覆盖。
- 所有团队作用域详情查询默认同时满足：
  - `team_id = current_user.team_id`
  - `deleted_at IS NULL`

### 3.3 通用错误语义

- `400`：请求结构不合法或字段缺失。
- `401`：未登录、token 无效、凭据校验失败。
- `403`：已登录但角色不足，或本模块已冻结的成员目录跨团队详情访问被拒绝。
- `404`：资源不存在或资源已软删除。

### 3.4 字段命名与 ID 映射

- 持久化层统一使用 `snake_case`，接口 JSON 统一使用 `camelCase`。
- 当前模块至少固定以下映射：
  - `display_name -> displayName`
  - `team_id -> teamId`
- `teamId` 在接口层表达“团队作用域键”。
  - 当来源于 `users` 或 `CurrentUserContext` 时，取自 `users.team_id`
  - 当来源于 `teams` 对象时，其值必须与 `teams.id` 以及 `teams.team_id(=id)` 相同
- `email`、`role`、`status` 等字段保持当前命名，不额外引入别名。

## 4. 直接接口契约

### 4.1 `POST /api/v1/auth/login`

#### 作用

- 校验账号密码并返回开发态 `Bearer token` 与当前用户上下文。

#### 请求体

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `email` | `string` | 登录邮箱 |
| `password` | `string` | 登录密码 |

#### 成功响应

```json
{
  "token": "dev-admin-token",
  "user": {
    "id": "user_admin",
    "email": "admin@example.com",
    "displayName": "管理员",
    "role": "admin",
    "status": "active",
    "teamId": "team_default"
  }
}
```

#### 评审基线

- `token` 为开发态认证适配层发放的 `Bearer token`，当前已冻结为至少两组演示身份映射：`admin` 与 `member`。
- `user` 必须至少返回：
  - `id`
  - `email`
  - `role`
  - `status`
  - `teamId`
- `status` 在 `P1` 当前只冻结 `active`，不引入额外状态机语义。
- 若前端需要统一封装 `tokenType`，默认使用 `Bearer`，无需额外引入新鉴权类型。
- 后续若切换为 JWT，应只替换 token 签发与解析实现，不改变本接口的外部鉴权头格式和 `CurrentUserContext` 语义。

#### 失败响应

- `401 invalid_credentials`

### 4.2 `GET /api/v1/auth/me`

#### 作用

- 根据当前 `Bearer token` 返回当前登录用户上下文。

#### 鉴权要求

- 必须携带有效 `Authorization` 头。

#### 成功响应

```json
{
  "user": {
    "id": "user_admin",
    "email": "admin@example.com",
    "displayName": "管理员",
    "role": "admin",
    "status": "active",
    "teamId": "team_default"
  }
}
```

#### 评审基线

- 本轮冻结 `user` 负载，不额外发明完整 `team` 摘要或权限快照对象。
- 其他模块如需团队显示名或权限摘要，应在后续子任务设计阶段显式扩展，而不是隐式依赖。

#### 失败响应

- `401 unauthorized`

### 4.3 `POST /api/v1/auth/logout`

#### 作用

- 结束当前前端登录态，并为后续审计留出统一退出入口。

#### 鉴权要求

- 需要当前有效登录态。

#### 成功语义

- 成功响应冻结为 `204 No Content`。
- 本轮只冻结“成功结束当前登录态”的语义，不把该接口扩展为复杂令牌失效系统。
- 前端收到 `204` 后清空当前登录态即可，不依赖返回 payload。

#### 失败响应

- `401 unauthorized`

### 4.4 `GET /api/v1/members`

#### 作用

- 返回当前团队基础成员目录列表。

#### 鉴权要求

- 需要当前有效登录态。

#### 查询语义

- 必须只查询 `current_user.team_id` 下的成员。
- 默认过滤软删除成员。
- 列表 envelope 与分页参数在模块层只闭合到共享最小层；页面 callback、URL 序列化与 request adapter 细节不在本轮 API 契约内展开。

#### 与 `M01` 列表原语的对齐边界

- 本模块当前只冻结：
  - 集合资源语义
  - 成员条目字段投影
  - 服务端分页方向
  - 团队过滤与软删除过滤规则
- 当前按 `OQ-021` 的 `proposed-default` 口径继承共享契约：
  - 请求查询默认沿用 `page`、`page_size`、`q`、`status`、`sort`、`order`
  - 响应骨架默认沿用 `items`、`page`、`page_size`、`total`、`total_pages`
- `/members` 的共享列表契约在模块文档内到此闭合：
  - `M02` 只吸收上述共享 query key 与分页骨架
  - 不额外定义 `M02` 专属分页参数、列表包装格式或私有 URL 序列化协议
  - callback 签名、复杂筛选编码与 request adapter 细节继续留在页面 / 实现层，不回流为模块级 API 契约
- “模块内已闭合”在本轮只表示：
  - `M02` 已停止私自补充共享 query / envelope / URL 协议
  - `GET /api/v1/members` 的模块级契约只保留共享最小层，不再把实现层细节误抬到 API 文档
  - 该结论仍停留在 `OQ-021` 的 `proposed-default` 治理层，不等于正式候选输入已经放行
- 因此不能从这条闭合结论外推：
  - `MT02_04` ready
  - `MT02_06` ready
- 若实现样例暂时返回裸数组，也只能视为临时 stub，不代表最终 API 契约已经冻结；但它也不得反向否定上述共享最小层口径。

#### 成员条目冻结字段集

| 字段 | 说明 |
| --- | --- |
| `id` | 成员 ID |
| `displayName` | 展示名 |
| `role` | `admin` / `member` |
| `status` | 当前状态 |

#### 评审基线

- `/members` 已冻结为团队内基础成员目录，`admin` 与 `member` 都可读取本团队成员列表。
- 无论最终可见范围如何，列表都不得返回：
  - `email`
  - `password_hash`
  - 跨团队成员
  - 已软删除成员

#### 失败响应

- `401 unauthorized`

### 4.5 `GET /api/v1/members/{member_id}`

#### 作用

- 返回当前团队某成员的基础详情投影。

#### 鉴权要求

- 需要当前有效登录态。

#### 详情字段冻结基线

| 字段 | 说明 |
| --- | --- |
| `id` | 成员 ID |
| `displayName` | 展示名 |
| `role` | 角色 |
| `status` | 状态 |

#### 错误语义

- 目标成员不属于当前团队：`403`
- 目标成员已软删除：`404`
- 当前角色不具备读取权限：`403`

## 5. P1 页面 / API 权限矩阵基线

| 路由分组 | 归属说明 | admin | member | 未登录 | 跨团队 |
| --- | --- | --- | --- | --- | --- |
| `/login`、`POST /api/v1/auth/login` | 登录入口 | 允许 | 允许 | 允许 | 不适用 |
| `GET /api/v1/auth/me`、`POST /api/v1/auth/logout` | 当前登录态接口 | 允许 | 允许 | `401` | 不适用 |
| `/(dashboard)/members`、`GET /api/v1/members*` | 成员目录读取面 | 允许 | 允许读取本团队基础成员目录 | `401` / 跳转登录 | `403` |
| 普通团队业务页 / API | 如岗位、简历、面试、复盘、资产、训练 | 允许 | 允许访问本团队资源 | `401` / 跳转登录 | `404` 或 `403` |
| `/(dashboard)/admin/**`、`/api/v1/admin/**` | 管理台专属能力 | 允许 | `403` | `401` / 跳转登录 | `403` |

## 6. 接口与旧新入口映射

| 旧入口 | 当前由 API 文档冻结的内容 | 对应新蓝本 | 当前 readiness 判断 |
| --- | --- | --- | --- |
| `ST02_01` | `POST /api/v1/auth/login`、`GET /api/v1/auth/me`、`POST /api/v1/auth/logout` 的 payload、`CurrentUserContext` 语义、`logout=204` | `MT02_01`、`MT02_02` | auth backend 边界已比页面面更稳定；但全局 `OQ-024` 已写死为“历史容器 / 观察蓝本 / 正式开窗层当前为空”，模块内只吸收该引用，因此 `MT02_01/MT02_02` 仍仅是白名单观察面，旧入口不得直开 |
| `ST02_01` | `/login` 只允许消费上面的 auth 契约，不允许反向扩张 API 负载 | `MT02_05` | 页面 adapter 继续后置；不能因为 `/auth/*` 边界已较清楚，就误判 `/login` 已可进入子任务设计 |
| `ST02_02` | `GET /api/v1/members`、`GET /api/v1/members/{member_id}` 的安全字段投影、过滤与错误语义 | `MT02_03`、`MT02_04` | `member detail` 边界已接近稳定；`/members` 列表契约虽已在模块内闭合到共享最小层，但这只表示 `M02` 不再私补共享协议，且该口径当前仍只处于全局 `OQ-021` 的默认治理层，因此 `MT02_03` 仅保留后续观察顺序，`MT02_04` 继续阻塞 |
| `ST02_02` | `/(dashboard)/members` 只能消费共享列表 / i18n / 页面原语口径，不能私自倒推 API 细节 | `MT02_06` | 页面 adapter 继续后置；`/members` 的模块内闭合不等于页面 ready，必须等待 `MT02_04` 与页面共享口径同时稳定 |
| `ST02_03` | `/(dashboard)/admin/**`、`/api/v1/admin/**` 的访问矩阵基线 | `MT02_07`、`MT02_08` | policy 面本轮仅保留后续观察顺序；验证矩阵必须等待 `MT02_04`、`MT02_07` 稳定，旧入口不得直开 |

## 7. 鉴权测试硬约束映射

- 所有新增受保护接口必须覆盖：
  - 未登录 `401`
  - `member` 访问 `admin` 接口 `403`
  - 本团队访问本团队资源 `200 / 201`
  - 跨团队成员目录详情访问 `403`
  - 软删除资源详情 `404`
  - 软删除资源不出现在列表
- 权限矩阵专门测试文件基线：
  - `apps/api/tests/test_authorization_matrix.py`

## 8. 当前缺口与 readiness 收紧点

- `/members` 列表的共享列表契约已在模块内闭合到共享最小层：只承认 `page/page_size/q/status/sort/order` 与统一分页骨架；callback、URL 序列化与 request adapter 细节继续留在页面 / 实现层。
- 这意味着当前 API 文档仍维持高 `L4`，且最低位原因已经收缩到可判定范围：
  - `POST /api/v1/auth/login`、`GET /api/v1/auth/me`、`POST /api/v1/auth/logout`、`GET /api/v1/members/{member_id}` 与权限矩阵基线本身已可审计，它们不再是把文档压在高 `L4` 的主因
  - 当前唯一仍把 `MODULE_API_DESIGN.md` 压在高 `L4` 的结构性主阻塞，是 `GET /api/v1/members` 的共享最小层虽已在模块内闭合，但仍只停留在全局 `OQ-021` 的 `proposed-default` 治理层，尚未被总控认可为可直接下发的正式候选输入
  - 只要这一点未变，`MODULE_API_DESIGN.md` 就仍是模块最低位，整体也不能跨过 `L5`
- “正式开窗层当前为空”与“仍只是观察面”的关系应分两段理解：
  - `MODULE_API_DESIGN.md` 仍是高 `L4`，说明模块层还有最低位文档未跨过下游输入门槛
  - `OQ-024` 正式开窗层当前为空，说明即使某些接口面已可审计，总控也尚未把任何 `MT02_*` 蓝本登记为正式入口
  - 因此 `MT02_01 / MT02_02` 现在只能停留在白名单观察面：前者解决“哪些 auth 接口面已稳定可观察”，后者解决“这些观察面仍未被总控放进正式开窗层”
- `MT02_02` 的权限消费边界仍必须继续留在模块层：
  - `CurrentUserContext`、`logout=204`、`401/403` 与 admin route group 同时被 `/login`、`MT02_07`、`MT02_08` 等后续变化面消费，属于跨微任务共享契约，而不是 `MT02_02` 的私有实现细节
  - 若把这些边界下放到 `MT02_02`，会重新把 auth backend、页面 adapter、policy / validation 混回旧 `ST02_01` 式混合入口，子任务层也会被迫再次定义共享契约
- 因此离正式候选还差的最小条件已收敛为：
  1. 总控认可 `GET /api/v1/members` 当前共享最小层已足以作为正式候选输入，或等价地使 `MODULE_API_DESIGN.md` 不再因这条引用维持高 `L4`
  2. 总控在 `OQ-024` 已写死的三层映射基础上，把 `MT02_01 / MT02_02` 从观察蓝本推进到正式开窗层
  3. 上述推进仍以前述权限消费边界继续留在模块层为前提，不得借旧 `ST02_01` 或新的子任务层重复定义
- 针对本轮候选前复核，`/members` 必须被读成“已闭合但未放行”：
  - 对 `MT02_04` 而言，当前只证明模块内共享最小层吸收已闭合，不证明 `OQ-021` 已升格为可直接下发的正式候选输入，也不证明 `MODULE_API_DESIGN.md` 已跨过 `L5`
  - 对 `MT02_06` 而言，除继承 `MT02_04` 的全部阻塞外，还额外受 `OQ-020`、`OQ-022` 与页面 request adapter 仍故意留在实现层的约束
  - 只要上述任一条件未变，“`/members` 已闭合”就不能被摘句式回写成“`MT02_04 / MT02_06` 接近 ready”
- 因此当前 API 文档达到的是“`/members` 共享列表契约已在模块内闭合到共享最小层、auth 接口 / detail 接口 / 权限矩阵基线已可审计，但 API 文档整体仍因这一共享契约引用而维持高 `L4`；页面类微任务继续后置”的状态，而不是“所有接口都已足以支撑子任务设计”。

### 8.1 `MT02_01 / MT02_02` 白名单复核结论

| 蓝本 | 当前已可稳定观察的接口面 | 仍不能转为正式子任务候选的直接原因 | 仍缺的推进条件 |
| --- | --- | --- | --- |
| `MT02_01` | 开发态 `Bearer token` 口径、`admin/member` 演示身份映射、token 解析只来自 `.env` / seed | `MODULE_API_DESIGN.md` 仍是模块最低位且整体仍为高 `L4`；全局 `OQ-024` 虽已写死三层映射，但正式开窗层当前仍为空；复读遗留 `ST02_01` 后已确认其 `SUBTASK_DESIGN.md` 仍写着“当前成熟度：仅有骨架”，父模块行仍残留 `$(System.Collections.Specialized.OrderedDictionary.Id)` 占位符，`SUBTASK_IMPLEMENTATION.md` 也仍是空白实施模板，因此不能充当 `MT02_01` 的正式入口证明 | 总控在既有 `OQ-024` 映射基础上，把 `MT02_01` 从观察蓝本推进到正式候选 / 开窗层；`MODULE_API_DESIGN.md` 整体跨过 `L5`；按新蓝本而不是旧容器判断正式入口 |
| `MT02_02` | `POST /api/v1/auth/login`、`GET /api/v1/auth/me`、`POST /api/v1/auth/logout` 的 payload，`CurrentUserContext` 语义，`logout=204` | 除了仍受模块最低位高 `L4` 与“正式开窗层当前为空”约束外，`CurrentUserContext`、`logout=204`、`401/403`、admin route group 不是 `MT02_02` 的私有输出，而是被 `/login`、`MT02_07`、`MT02_08` 等共同消费的模块级共享边界；复读遗留 `ST02_01` 后也已确认旧设计仍把 `/auth/*` 与 `/login` 页面承接混在同一骨架文档里，实施文档仍为空模板，不能视为 `MT02_02` 已具备正式子任务入口 | 总控在既有 `OQ-024` 映射基础上完成“观察蓝本 -> 正式开窗层”状态回写；继续保持上述共享消费边界留在模块层，并在不借旧 `ST02_01` 直开的前提下，按新蓝本判断是否创建正式入口 |

- 结论：`MT02_01 / MT02_02` 本轮仍只属于“可持续复核的最小非页面观察面”，不属于正式子任务候选，也不允许据此补写子任务双文档或开启子任务窗口。

### 8.2 从观察面转为正式候选的最小放行条件

- 条件 A：总控认可 `GET /api/v1/members` 当前共享最小层已足以作为正式候选输入，或等价地使 `MODULE_API_DESIGN.md` 不再因这一条引用维持高 `L4`。
- 条件 B：总控虽已把 `OQ-024` 的三层映射写死为“历史容器 / 观察蓝本 / 正式开窗层当前为空”，但后续仍需把 `MT02_01/MT02_02` 从观察蓝本推进到正式开窗层，而不是让模块或旧 `ST02_*` 自行证明入口。
- 条件 C：正式入口必须基于 `MT02_01 / MT02_02` 新蓝本重新定义，并继续只消费模块层已冻结的 `CurrentUserContext`、`logout=204`、`401/403` 与 admin route group 边界；这些共享契约不得回流到子任务层重定义。

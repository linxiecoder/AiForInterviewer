# M02 鉴权、团队与成员 - 模块待确认问题

## 1. 当前模块问题
- OQ-004 P1 鉴权机制采用固定 Bearer token、JWT 还是 session cookie
- OQ-005 团队管理员与普通成员的权限矩阵是否先只覆盖 P1 页面

## 2. 问题详情
### OQ-004 P1 鉴权机制采用固定 Bearer token、JWT 还是 session cookie

- 为什么影响本模块：会影响鉴权 API、前端登录流、测试夹具和权限校验方式。
- 当前建议：默认用固定 Bearer token 作为 P1 开发口径，但在决策表中标记为 proposed。
- 需要回写的文档：`MODULE_REQUIREMENTS.md`、`MODULE_DESIGN.md`、`MODULE_API_DESIGN.md`、`MODULE_SCHEMA_DESIGN.md`、`MODULE_LOGIC_DESIGN.md`

### OQ-005 团队管理员与普通成员的权限矩阵是否先只覆盖 P1 页面

- 为什么影响本模块：会影响权限测试矩阵、管理台范围和跨团队访问边界。
- 当前建议：默认先覆盖 P1 页面和 API，不扩展到未来多租户治理能力。
- 需要回写的文档：`MODULE_REQUIREMENTS.md`、`MODULE_DESIGN.md`、`MODULE_API_DESIGN.md`、`MODULE_SCHEMA_DESIGN.md`、`MODULE_LOGIC_DESIGN.md`

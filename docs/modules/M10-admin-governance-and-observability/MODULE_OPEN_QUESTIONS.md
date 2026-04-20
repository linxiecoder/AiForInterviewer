# M10 管理台、治理与可观测性 - 模块待确认问题

## 1. 当前模块问题
- OQ-002 首轮是否只建立最小运行时、测试和 CI 基线
- OQ-004 P1 鉴权机制采用固定 Bearer token、JWT 还是 session cookie
- OQ-005 团队管理员与普通成员的权限矩阵是否先只覆盖 P1 页面
- OQ-007 上传、转换、导出在 P1 中哪些必须异步
- OQ-017 管理台的模型推荐来源是本地 catalog 还是在线同步
- OQ-018 管理台是否负责 search snapshot 导入与运维

## 2. 问题详情
### OQ-002 首轮是否只建立最小运行时、测试和 CI 基线

- 为什么影响本模块：会影响基础模块的范围，决定是否先搭骨架还是一次补齐完整工程化。
- 当前建议：默认只做最小可运行基线，把完整 CI/E2E 提升到后续轮次。
- 需要回写的文档：`MODULE_REQUIREMENTS.md`、`MODULE_DESIGN.md`、`MODULE_API_DESIGN.md`、`MODULE_SCHEMA_DESIGN.md`、`MODULE_LOGIC_DESIGN.md`

### OQ-004 P1 鉴权机制采用固定 Bearer token、JWT 还是 session cookie

- 为什么影响本模块：会影响鉴权 API、前端登录流、测试夹具和权限校验方式。
- 当前建议：默认用固定 Bearer token 作为 P1 开发口径，但在决策表中标记为 proposed。
- 需要回写的文档：`MODULE_REQUIREMENTS.md`、`MODULE_DESIGN.md`、`MODULE_API_DESIGN.md`、`MODULE_SCHEMA_DESIGN.md`、`MODULE_LOGIC_DESIGN.md`

### OQ-005 团队管理员与普通成员的权限矩阵是否先只覆盖 P1 页面

- 为什么影响本模块：会影响权限测试矩阵、管理台范围和跨团队访问边界。
- 当前建议：默认先覆盖 P1 页面和 API，不扩展到未来多租户治理能力。
- 需要回写的文档：`MODULE_REQUIREMENTS.md`、`MODULE_DESIGN.md`、`MODULE_API_DESIGN.md`、`MODULE_SCHEMA_DESIGN.md`、`MODULE_LOGIC_DESIGN.md`

### OQ-007 上传、转换、导出在 P1 中哪些必须异步

- 为什么影响本模块：会影响对象存储、任务队列、导出日志和实施顺序。
- 当前建议：默认转换和正式导出异步，上传元数据登记同步。
- 需要回写的文档：`MODULE_REQUIREMENTS.md`、`MODULE_DESIGN.md`、`MODULE_API_DESIGN.md`、`MODULE_SCHEMA_DESIGN.md`、`MODULE_LOGIC_DESIGN.md`

### OQ-017 管理台的模型推荐来源是本地 catalog 还是在线同步

- 为什么影响本模块：会影响治理边界、实现复杂度和维护成本。
- 当前建议：默认采用本地 catalog / seed。
- 需要回写的文档：`MODULE_REQUIREMENTS.md`、`MODULE_DESIGN.md`、`MODULE_API_DESIGN.md`、`MODULE_SCHEMA_DESIGN.md`、`MODULE_LOGIC_DESIGN.md`

### OQ-018 管理台是否负责 search snapshot 导入与运维

- 为什么影响本模块：会影响模块边界，以及上下文包对运营后台的依赖。
- 当前建议：默认由管理台承担导入配置和审计，不承担在线抓取。
- 需要回写的文档：`MODULE_REQUIREMENTS.md`、`MODULE_DESIGN.md`、`MODULE_API_DESIGN.md`、`MODULE_SCHEMA_DESIGN.md`、`MODULE_LOGIC_DESIGN.md`

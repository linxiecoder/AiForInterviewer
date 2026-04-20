# M01 基础平台与工作台壳层 - 模块待确认问题

## 1. 当前模块问题
- OQ-001 仓库结构是否固定为 monorepo (`apps/web` + `apps/api` + `infra`)
- OQ-002 首轮是否只建立最小运行时、测试和 CI 基线
- OQ-003 视觉规范首轮需要沉淀到什么粒度

## 2. 问题详情
### OQ-001 仓库结构是否固定为 monorepo (`apps/web` + `apps/api` + `infra`)

- 为什么影响本模块：会影响所有模块的目录规划、引用方式和实施文档中的目标路径。
- 当前建议：默认采用原始实施计划中的 monorepo 结构，并在 `DESIGN_DECISIONS.md` 先登记为 proposed。
- 需要回写的文档：`MODULE_REQUIREMENTS.md`、`MODULE_DESIGN.md`、`MODULE_API_DESIGN.md`、`MODULE_SCHEMA_DESIGN.md`、`MODULE_LOGIC_DESIGN.md`

### OQ-002 首轮是否只建立最小运行时、测试和 CI 基线

- 为什么影响本模块：会影响基础模块的范围，决定是否先搭骨架还是一次补齐完整工程化。
- 当前建议：默认只做最小可运行基线，把完整 CI/E2E 提升到后续轮次。
- 需要回写的文档：`MODULE_REQUIREMENTS.md`、`MODULE_DESIGN.md`、`MODULE_API_DESIGN.md`、`MODULE_SCHEMA_DESIGN.md`、`MODULE_LOGIC_DESIGN.md`

### OQ-003 视觉规范首轮需要沉淀到什么粒度

- 为什么影响本模块：会影响工作台壳层、设计 token、页面模板和后续页面设计的一致性。
- 当前建议：默认先沉淀全局视觉原则、token 方向和页面家族，不直接展开到高保真页面实现。
- 需要回写的文档：`MODULE_REQUIREMENTS.md`、`MODULE_DESIGN.md`、`MODULE_API_DESIGN.md`、`MODULE_SCHEMA_DESIGN.md`、`MODULE_LOGIC_DESIGN.md`

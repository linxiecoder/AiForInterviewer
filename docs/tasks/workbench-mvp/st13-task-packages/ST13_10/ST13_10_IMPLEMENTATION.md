# ST13_10 IMPLEMENTATION：R1 RAG 最小可用任务包实施说明

## 1. 文档状态

- 状态：`draft`
- 文档性质：ST13 任务实施说明；只定义后续实现窗口的输入、禁止范围、required tests 和停止条件。
- 当前 readiness：docs-only readiness。
- 当前 official state：`DOC_STATE.yaml` 中 `ST13_10` 仍为 missing / blocked；本窗口不修改 official state。
- 当前不允许：RAG implementation、schema / migration / ORM implementation、测试实现、packet generation、formal window open。

## 2. 当前 readiness state

`ST13_10` 已被确认为 R1 RAG anchor，但当前仍不是 implementation-ready：

- 已有状态层 task：`ST13_10 / WT13-10 / RAG / 知识库`。
- 本窗口创建 task package 双文档。
- 不新增 task ID。
- 不修改 `DOC_STATE.yaml`。
- 不生成 implementation packet。
- 不打开 formal window。
- 不写代码、测试、schema、migration 或 ORM。

## 3. 后续实现允许路径候选

以下路径仅是未来 implementation packet 的候选输入，不是当前授权：

| 路径 | 未来可能用途 | 当前状态 |
| --- | --- | --- |
| `apps/api/**` | RAG ingestion / indexing / retrieval API、service、adapter、persistence integration | 当前禁止 |
| `tests/**` | RAG contract、integration、failure、visibility 测试 | 当前禁止 |
| `requirements.txt` | 仅当正式实现引入新依赖时同步 | 当前禁止 |
| `.env.example` | 仅当正式实现引入新环境变量时同步占位 | 当前禁止 |
| schema / migration 文件 | 仅当 formal window 和 packet 明确授权后处理 | 当前禁止 |
| `docs/tasks/workbench-mvp/st13-task-packages/ST13_10/**` | ST13_10 文档同步 | 当前仅本双文档允许 |

任何未来 allowed paths 都必须由 formal window、implementation packet 和用户明确授权最终决定。

## 4. 当前禁止路径

当前窗口和后续未授权状态下禁止：

- `apps/**`
- `tests/**`
- `docs/governance/**`
- `DOC_STATE.yaml`
- `docs/tasks/workbench-mvp/st13-task-packages/ST13_20/**`
- `docs/tasks/workbench-mvp/st13-task-packages/ST13_21/**`
- schema 文件
- migration 文件
- ORM / database implementation
- packet
- formal window
- 任何新长期状态入口

## 5. Implementation stop conditions

出现以下任一情况必须停止：

1. 需要修改 `DOC_STATE.yaml` 或 `docs/governance/**`。
2. 需要修改 `ST13_20`、`ST13_21` 或 `ST13_24` 文档。
3. 需要修改 task remap 才能继续。
4. 需要新增 task ID。
5. 需要生成 packet 或打开 formal window。
6. 需要实现业务代码、测试代码、schema、migration、ORM、repository、worker、queue、provider 或前端页面。
7. 需要引入新依赖或环境变量。
8. `validate-state` 或 `evaluate-state` 失败。
9. `git status --short` 出现本窗口允许范围外改动。

## 6. Required tests / acceptance boundary

未来 `ST13_10` implementation packet 至少需要覆盖以下 required tests 输入：

| 测试面 | required tests 输入 |
| --- | --- |
| governance | `validate-state`、`evaluate-state`、`git diff --check`、allowed / forbidden path audit |
| knowledge source | 用户私有资料、管理员公共资料、岗位 / 简历 / 历史回答 scope 的读取边界 |
| document lifecycle | uploaded、parsing、indexed、failed、archived 等状态语义 |
| retrieval query | query summary、scope、selected materials、topK、actor / visibility filter |
| retrieval result | hit count、hit summary、empty result、permission filtered empty、degraded |
| citation | source ref、chunk ref、snippet summary、visibility snapshot 不泄露不可见资源 |
| evidence gap | no result、index pending、index failed、RAG unavailable、low confidence |
| frontend contract | 面试台、评分、复盘、导出和历史回看能消费 citation / evidence gap |
| persistence | 与 `ST13_20` 对齐 retrieval query/result/citation/evidence/source snapshot 边界 |
| security | owner、visibility、resource_not_visible、permission_denied、安全 404、脱敏输出 |
| failure | RAG unavailable 时主链路继续，评分 / 复盘 / 导出明确降级 |

当前窗口不创建 `tests/**`。

## 7. RAG ingestion / indexing / retrieval 最小实现输入

未来最小实现输入应按以下顺序收敛：

1. knowledge source：确认用户私有资料、管理员公共资料、岗位、简历、历史回答的 scope。
2. document ingestion：确认文档上传 / 粘贴、解析状态、失败原因和 source snapshot。
3. chunk / indexing：确认 chunk 引用、index status、index pending / failed / retryable。
4. retrieval query：确认 query summary、topK、scope、selected materials、visibility filter。
5. retrieval result：确认 hit summary、empty reason、permission filtered summary、degraded。
6. citation / evidence：确认 source ref、chunk ref、snippet summary、evidence gap、confidence label。
7. integration：确认面试台、评分、复盘、导出、历史回看如何消费。

该顺序是后续实现输入，不代表当前创建 API、schema、worker、queue、provider 或 tests。

## 8. RAG 与 score / review / export / history 的集成边界

| 下游 | RAG integration boundary |
| --- | --- |
| score | 评分可引用 evidence refs、evidence gap、low confidence；RAG evidence 不直接决定分数 |
| review | 复盘展示整场证据、关键缺口、建议来源和降级说明 |
| export | Markdown 导出包含 RAG 引用、证据缺口、低置信度和 content version |
| history | 历史回看恢复 source snapshot、citation、evidence gap 和当时的可见性摘要 |

训练闭环自动消费 RAG evidence 属于 R2，不进入 R1 must-have。

## 9. RAG 与 frontend UI consumption 的集成边界

未来前端消费需要遵守：

- 面试台展示 citation、reference summary、evidence gap、RAG degraded。
- 知识库显示 upload / parse / index status、failure reason、retryable。
- 评分 / 复盘显示 evidence、low confidence、missing evidence。
- 导出显示引用和证据缺口，但不得泄露不可见资源。
- empty result 与 RAG unavailable 必须区分展示。
- pending / running 不能误显示为无资料。

当前不实现页面、组件、hook、store、route 或样式。

## 10. RAG 与 schema / migration / ORM 的前置依赖

RAG implementation 进入持久化前必须等待：

- `ST13_20` 将 RAG must-persist 字段转换为明确 schema 设计。
- schema 文件路径、migration 工具、up/down、rollback、dry-run 策略确认。
- Citation / Evidence / SourceSnapshot 与权限字段的关系确认。
- embedding 向量是否落库、落哪里、如何脱敏和如何保留仍需另窗确认；R1 默认不把 embedding 向量作为必落库字段。
- ORM / repository / persistence layer 只有在 packet 授权后才可实现。

当前不允许进入 schema / migration / ORM implementation。

## 11. 后续窗口顺序建议

推荐顺序：

1. `R1-W05b-ST13_10-DOCS-CLOSEOUT-COMMIT`：验证并提交本双文档。
2. `R1-W06-ST13_10-RAG-CONTRACT-REVIEW`：只读或 docs-only 复核 `ST13_10` 与 `ST13_20` / `ST13_21` 的字段一致性。
3. `R1-W07-ST13_24-R1-TESTS-ACCEPTANCE-READINESS`：补 R1 RAG / scoring / review / export / history 的 acceptance 和 required tests。
4. 后续 schema / migration readiness 或 formal window 只能在用户明确授权、packet 和状态 gate 通过后开启。

不建议下一窗口直接进入 RAG implementation。

## 12. 完成判定

本 docs-only readiness 窗口完成判定：

- `ST13_10_DESIGN.md` 已覆盖 R1 RAG minimum scope、source、snapshot、query、result、citation、evidence、gap、fallback、security、frontend、persistence、`ST13_21` / `ST13_20` dependency。
- `ST13_10_IMPLEMENTATION.md` 已覆盖 readiness state、future allowed paths、forbidden paths、stop conditions、required tests、acceptance boundary、后续窗口顺序。
- 明确 `ST13_10` 是 R1 RAG anchor。
- 明确不新增 task ID。
- 明确当前不能进入 RAG implementation。
- 明确当前不能进入 schema / migration / ORM implementation。
- 未修改代码、测试、governance state、packet 或 formal window。

# ST13_10 实施说明：R1 RAG 最小可用任务包实施说明

## 当前非实现状态

- 状态：`draft`
- 文档性质：ST13 任务实施说明；只定义后续实现窗口的输入、禁止范围、required tests 和停止条件。
- 当前 readiness：docs-only readiness；仍不是 implementation-ready。
- 当前 official state：`DOC_STATE.yaml` 中 `ST13_10` 已为 `implementation_doc_state=active_working_doc`、`maturity=L5`、`readiness=blocked`；仍未打开 formal window，仍不是 implementation-ready。
- 当前不允许：RAG implementation、schema / migration / ORM implementation、测试实现、packet generation、formal window open。
- 已有状态层 task：`ST13_10 / WT13-10 / RAG / 知识库`。
- 不新增 task ID，不创建新长期状态入口。

## 本轮实施目标

- 建立 ST13_10 R1 RAG 最小可用 readiness 和 future implementation input 的可识别边界。
- 让后续 formal readiness 评审能从本文档抽取目标、允许修改范围、禁止修改范围和 required tests。
- 继续消费 ST13_21 API contract、ST13_20 data readiness 和 ST13_24 acceptance / tests boundary。
- 保持 R1 RAG must-have / optional / R2-deferred 边界不变。
- 明确当前仍不能进入 RAG implementation、schema / migration / ORM implementation 或 tests implementation。

## 允许修改范围

- `docs/tasks/workbench-mvp/st13-task-packages/ST13_10/ST13_10_IMPLEMENTATION.md`
- `docs/tasks/workbench-mvp/st13-task-packages/ST13_10/ST13_10_DESIGN.md`

## 禁止修改范围

本节为当前窗口和 formal window 打开前的禁止修改范围。下方 `禁止修改` 子句柄用于让 evaluator 抽取 forbidden paths。

### 禁止修改

- `apps/**`
- `tests/**`
- `docs/governance/**`
- `DOC_STATE.yaml`
- `docs/tasks/workbench-mvp/2026-04-25-workbench-mvp-task-remap.md`
- `docs/tasks/workbench-mvp/st13-task-packages/ST13_20/**`
- `docs/tasks/workbench-mvp/st13-task-packages/ST13_21/**`
- `docs/tasks/workbench-mvp/st13-task-packages/ST13_24/**`
- schema 文件
- migration 文件
- ORM / database implementation
- packet
- formal window
- 任何新 task ID
- 任何新长期状态入口

## 测试与验证

未来 ST13_10 implementation packet 至少需要覆盖以下 required tests 输入；当前窗口不创建测试文件：

- governance / state validation：validate-state、evaluate-state、focused ST13_10 evaluate、preflight-open-window、git diff --check、allowed / forbidden path audit。
- knowledge source boundary：用户私有资料、管理员公共资料、岗位、简历和历史回答 scope 的读取边界。
- document lifecycle：uploaded、parsing、parsed、indexed、failed、archived 等状态语义。
- indexing status：pending、running、indexed、failed、retryable 和 failure reason 的展示与追踪。
- retrieval query summary：query summary、scope、selected materials、topK、actor context 和 visibility filter。
- retrieval result summary：hit count、hit summary、empty result、permission filtered empty、degraded 和 retryable。
- citation contract：source ref、chunk ref、snippet summary、source label、visibility snapshot 不泄露不可见资源。
- evidence item / evidence gap：evidence summary、citation refs、confidence label、no result、index pending、index failed、RAG unavailable、low confidence。
- RAG unavailable / empty result / degraded behavior：主链路继续，评分、复盘、导出和历史回看明确降级或证据缺口。
- permission / resource visibility filtering：owner、visibility、resource_not_visible、permission_denied、安全 404 和脱敏输出。
- frontend display contract：面试台、评分、复盘、导出和历史回看能消费 citation、evidence item、evidence gap、pending、failed、degraded 和 empty state。
- persistence boundary：与 ST13_20 对齐 retrieval query、retrieval result、citation、evidence、source snapshot 和 permission snapshot。
- score / review / export / history evidence integration：评分理由、复盘证据、Markdown 导出和历史回看都能追溯 evidence refs、source snapshot、low confidence 和降级说明。

## 停止条件

出现以下任一情况必须停止：

1. 需要修改 `DOC_STATE.yaml` 或 `docs/governance/**`。
2. 需要修改 task remap。
3. 需要修改 `ST13_20`、`ST13_21` 或 `ST13_24` 文档正文。
4. 需要新增 task ID 或任何新长期状态入口。
5. 需要生成 packet 或打开 formal window。
6. 需要实现业务代码、测试代码、schema、migration、ORM、repository、worker、queue、provider 或前端页面。
7. 需要引入新依赖或环境变量。
8. `validate-state`、全量 `evaluate-state`、focused ST13_10 evaluate 或 ST13_10 preflight 失败且无法解释。
9. `git status --short` 出现本窗口允许范围外改动。

## 7. RAG 摄取 / 索引 / 检索最小实现输入

未来最小实现输入应按以下顺序收敛：

1. knowledge source：确认用户私有资料、管理员公共资料、岗位、简历、历史回答的 scope。
2. document ingestion：确认文档上传 / 粘贴、解析状态、失败原因和 source snapshot。
3. chunk / indexing：确认 chunk 引用、index status、index pending / failed / retryable。
4. retrieval query：确认 query summary、topK、scope、selected materials、visibility filter。
5. retrieval result：确认 hit summary、empty reason、permission filtered summary、degraded。
6. citation / evidence：确认 source ref、chunk ref、snippet summary、evidence gap、confidence label。
7. integration：确认面试台、评分、复盘、导出、历史回看如何消费。

该顺序是后续实现输入，不代表当前创建 API、schema、worker、queue、provider 或 tests。

## 8. RAG 与评分 / 复盘 / 导出 / 历史回看的集成边界

| 下游 | RAG integration boundary |
| --- | --- |
| score | 评分可引用 evidence refs、evidence gap、low confidence；RAG evidence 不直接决定分数 |
| review | 复盘展示整场证据、关键缺口、建议来源和降级说明 |
| export | Markdown 导出包含 RAG 引用、证据缺口、低置信度和 content version |
| history | 历史回看恢复 source snapshot、citation、evidence gap 和当时的可见性摘要 |

训练闭环自动消费 RAG evidence 属于 R2，不进入 R1 must-have。

## 9. RAG 与前端 UI 消费的集成边界

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

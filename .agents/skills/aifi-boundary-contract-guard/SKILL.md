---
name: aifi-boundary-contract-guard
description: Use when AiForInterviewer work has strict allowlists, contract fields, non-goals, forbidden domains, or candidate/default-off semantics.
---

# aifi-boundary-contract-guard

## Purpose

在受控小切片中保护 contract、allowlist、non-goals 和状态词，防止把局部补丁扩成 scoring、taxonomy、coaching、provider、runtime、Training、DB 或 frontend 大改。

适用于 G-001/G-003/G-004、Composition Layer、M2 conservative split、M3 scoring/report partial substrate 这类“输入字段和边界已经很明确”的任务。

## When to use

- 用户给出精确 allowlist 或单文件范围。
- 用户给出固定 schema key、status vocabulary、response fields、mode routing 或 contract tests。
- 用户明确禁止某些相邻系统：例如 no scoring、no taxonomy、no coaching、no provider-facing schema、no DB migration、no frontend state dependency。
- 任务目标是 partial、skeleton、candidate-only、default-off、design-only、draft-input 的边界保留。
- 需要用 focused tests、forbidden-term scan、schema/types sync 或 non-mutability checks 锁住范围。

不要用于大范围重构；那时用 `large-refactor-goal-pack`。不要用于只读 control authority 审计；那时用 `aifi-control-plane-audit`。

## Required Inputs

1. `allowed files` 和 `forbidden files`。
2. 必须保持的 contract fields / enum / status / mode / schema id。
3. 显式 non-goals 和 forbidden domains。
4. 验证命令或验收格式。
5. 是否允许代码实现。默认按用户请求；docs-only / recon-only 时不得写代码。

## Guard Set

开局运行或读取：

```bash
git branch --show-current
git rev-parse HEAD
git status --short --untracked-files=all
git diff --stat
```

如果用户禁止改 `AGENTS.md` 或临时工作区外文件，再加：

```bash
git status --short -- AGENTS.md
git diff -- AGENTS.md
```

## Procedure

1. 写下本轮 boundary statement：目标、allowlist、non-goals、done condition。
2. 找真实 runtime landing point，不从历史 docs 或邻近模块推断。
3. 若要改代码，先写或确认 RED/focused characterization test；缺模块、缺字段、旧状态断言失败都可以是有效 RED。
4. 只在 allowlist 内做最小 patch。
5. 如果 contract 触及 API/frontend，同步 schema、frontend types、view model 或 render layer；不要只改 backend。
6. 如是 composition/orchestration，优先用 fake service 注入，断言 routing、object identity、nested payload unchanged、no mutation。
7. 如是 partial/skeleton/default-off/candidate-only，更新或检查 capability matrix、skeleton guard、route inventory、snapshot 文案，禁止升级为 implemented。
8. 跑 focused verification；pytest 若只因 repo-root `tmp/` leak guard 失败，用 `AI_FOR_INTERVIEWER_ALLOW_TEST_DIR_LEAKS=1` 复跑。
9. 做 forbidden-term / no-touch scan，确认没有引入被禁止域。
10. 最终报告 changed files、tests、scope compliance、implementation risks only。

## Contract Checks

常用检查项：

- Contract fields 原样保留，不新增隐式语义。
- Status taxonomy 在 generation service、application service、API schema、frontend types、render layer 一致。
- `trace_refs` 只做 metadata-only 安全展示，不泄露 raw provider payload、prompt、completion、secret。
- formal persistence 与 response-level embedded result 分开；没有授权不得新增正式 `ScoreResult`、Training asset 或 DB write。
- `candidate-only`、`default-off`、`partial`、`skeleton`、`design-only`、`draft-input` 不得改写成 `implemented`。
- frontend 不得因为后端字段变化回退到旧三态或宽泛 fallback。

## Output Format

```markdown
## 结论

PASS / NOT READY / BLOCKED / UNKNOWN: <scope and contract result>

## Boundary Statement

- objective:
- allowed files:
- forbidden files:
- non-goals:
- contract fields:

## Scope Compliance

| Check | Evidence | Result |
|---|---|---|

## Verification

- commands:
- result:
- known gaps:

## Changed Files

- ...

## Risks

- implementation risks only:
- deferred / not claimed:
```

## Common Mistakes

- 因为 route 存在就把 capability 写成 implemented。
- 把 `partial` / `skeleton` / `default-off` / `candidate-only` 升级成完成态。
- 只改 backend 状态词，漏掉 schema/types/frontend display。
- 用 broad grep 把历史 docs/goals 噪音当当前事实。
- 单文件 orchestration 任务顺手改底层 G-003/G-004 逻辑。
- 在 validation 窗口修新功能，而不是先区分 test drift、snapshot drift 和真实生产缺陷。

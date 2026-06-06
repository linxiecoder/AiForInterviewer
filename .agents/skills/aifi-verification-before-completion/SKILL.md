---
name: aifi-verification-before-completion
description: Before completing AiForInterviewer tasks, verify scope, diff, tests, and unresolved risks without loading the full superpowers workflow.
---

# aifi-verification-before-completion

## Purpose

在完成 AiForInterviewer 任务前做轻量验证，确认本轮改动仍在授权范围内，并留下必要的测试和风险证据。

## Checks

1. 运行或读取 `git status --short --untracked-files=all`。
2. 运行或读取 `git diff --stat`。
3. 核对 changed files 是否全部在当前 scope 内。
4. 列出本轮实际执行的 tests / commands；未运行则说明原因。
5. 列出 unresolved risks、未验证路径和待用户确认项。
6. 确认没有意外纳入 `.understand-anything/` 内容。
7. 确认没有意外纳入 `.codegraph/` 内容。

## Output

- `scope check`
- `changed files`
- `commands run`
- `tests result`
- `unresolved risks`
- `index artifacts check`

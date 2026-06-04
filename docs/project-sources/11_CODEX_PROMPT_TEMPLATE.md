---
title: 11_CODEX_PROMPT_TEMPLATE
type: note
permalink: ai-for-interviewer/docs/project-sources/11-codex-prompt-template
---

# 11 Codex Prompt Template

你现在在 AiForInterviewer 仓库中执行一个受控重构窗口。

Window ID:
<WINDOW_ID>

Phase:
<PHASE_NAME>

Capability IDs:
<CAPABILITY_IDS>

Source of Truth:
1. GitHub main 当前代码是当前实现事实源。
2. Project source 是目标架构和执行规则源。
3. GOAL0531 是阶段意图源，不是当前代码事实源。
4. 如三者冲突，以 GitHub 描述当前实现，以 Project source 描述目标，以 GOAL 描述历史意图，并把差异记录为 gap。

Must Recon First:
<FILE_LIST>

Allowed Files:
<ALLOWED_FILES>

Forbidden Files:
<FORBIDDEN_FILES>

Implementation Requirements:
<REQUIREMENTS>

Validation Commands:
<COMMANDS>

Done Criteria:
<DONE_CRITERIA>

Final Output:
1. Root Cause
2. What Changed
3. Files Changed
4. Behavior Before / After
5. Validation Commands and Results
6. Remaining Risks
7. Follow-up Goal

Stop Conditions:
需要修改 forbidden files；需要改变未授权 prompt/schema/provider/DB；无法读取关键文件；发现严重 gap 需总控确认。
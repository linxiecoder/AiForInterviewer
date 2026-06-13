---
title: INTERVIEW_COACH_REFACTOR_SPEC
type: design-spec
status: active-f0
updated: 2026-06-13
permalink: ai-for-interviewer/docs/02-design/interview-coach-refactor-spec
canonical: true
source_migrated_from: docs/active/interview-coach-refactor.md
---

# Interview Coach Refactor Spec

本文是 AiForInterviewer interview-coach-refactor 的当前 active system spec。它覆盖 G-003、G-004 与 Composition Layer 的最终职责边界，并取代此前 `docs/active/interview-coach-refactor.md`、`.codex-temp/interview-coach-refactor/**` 以及其他临时说明中的系统定义地位。

此前文档只保留为 historical evidence。任何旧文档、旧计划、历史审计或 archive 内容不得作为当前系统架构、职责边界、运行模式或语义 contract 的 authoritative source。

## Final System Architecture

最终系统由三个独立模块组成：

- G-003: Evaluation Layer
- G-004: Understanding Layer
- Composition Layer: Orchestration Layer

三者不是顺序 pipeline。G-003 不依赖 G-004 的内部语义，G-004 不依赖 G-003 的输出，Composition Layer 也不把其中任一层转换成另一层的输入语义。

系统通过 Composition Layer 进行组合。Composition Layer 只负责按运行模式决定是否调用 G-003 / G-004，并把各层输出以可返回的响应形态组合在一起。组合只表示 routing 与 packaging，不表示跨层解释、重写、推理、评分或语义升级。

| Layer | Final responsibility | Output boundary |
| --- | --- | --- |
| G-003 | Evaluation Layer | 只产出 evaluation / feedback / UI-safe status labeling |
| G-004 | Understanding Layer | 只产出 transcript structure / behavioral signals |
| Composition Layer | Orchestration Layer | 只产出按 mode 组合后的 response envelope |

## Implemented Capability Map

### G-003 Evaluation Layer

What it does:

- 生成 feedback / evaluation 输出。
- 给 UI 提供安全状态标签。
- 在 feedback evaluation 前把 raw `answer_text` 解析为 bounded `structured_answer`，包含 `claims`、`topics`、`sentiment`、`confidence_indicators` 和 `experience_signals`。
- parser 失败时使用 fallback wrapper，不把解析失败升级为 cross-layer understanding。

Where implemented:

- `apps/api/app/application/polish/transcript_signal_parser.py`
- `apps/api/app/application/polish/feedback_generation_service.py`
- `apps/api/app/application/polish/feedback_prompt_assets.py`
- `apps/api/app/application/polish/feedback_agent.py`
- `apps/api/app/application/polish/feedback_application_service.py`

Validation evidence:

- 已迁入的 GREEN evidence：`AI_FOR_INTERVIEWER_ALLOW_TEST_DIR_LEAKS=1 .venv/bin/python -m pytest tests/api/test_polish_transcript_signal_parser.py tests/api/test_polish_feedback_generation_service.py tests/api/test_polish_feedback_pipeline_contract.py tests/api/test_polish_feedback_agent_io_alignment.py tests/api/test_transcript_analysis.py tests/api/test_transcript_analysis_contract_lock.py` -> `67 passed in 0.96s`。
- Regression test paths: `tests/api/test_polish_transcript_signal_parser.py`、`tests/api/test_polish_feedback_generation_service.py`、`tests/api/test_polish_feedback_pipeline_contract.py`、`tests/api/test_polish_feedback_agent_io_alignment.py`。

Current system behavior impact:

- G-003 feedback prompt consumes structured current-answer signals instead of only raw free text.
- Historical same-question answers remain compact; full/raw answer fields remain forbidden provider payload unless explicitly bounded as current-answer input.
- G-003 不输出 transcript structure、behavioral signal extraction、candidate reasoning trace 或 understanding model。

### G-004 Understanding Layer

What it does:

- 解析 transcript。
- 输出 transcript structure 与 behavioral signals。
- 保持 understanding-only，不生成 feedback、score、rubric verdict 或 coaching plan。

Where implemented:

- `apps/api/app/application/transcript_analysis/models.py`
- `apps/api/app/application/transcript_analysis/parser.py`
- `apps/api/app/application/transcript_analysis/analyzer.py`
- `apps/api/app/application/transcript_analysis/service.py`

Validation evidence:

- 已迁入的 GREEN evidence 覆盖 `tests/api/test_transcript_analysis.py` 与 `tests/api/test_transcript_analysis_contract_lock.py`。
- Regression test paths: `tests/api/test_transcript_analysis.py`、`tests/api/test_transcript_analysis_contract_lock.py`。

Current system behavior impact:

- G-004 只定义 transcript understanding contract `transcript_analysis_v1`。
- G-004 模块不得 import G-003 或 Polish feedback services。
- G-004 输出不得被解释为 scoring、taxonomy 或 coaching。

### Composition Layer

What it does:

- 根据 `interview`、`training`、`analysis` mode 路由 G-003 / G-004。
- 只把 layer-owned 输出并列打包到 response envelope。
- 不解释、不重写、不覆盖任一 layer 输出语义。

Where implemented:

- `apps/api/app/application/composition/service.py`

Validation evidence:

- Regression test path: `tests/api/test_composition_layer.py`。
- Tests cover mode routing, analysis mode not invoking G-003, G-003 / G-004 replacement independence, and response field isolation.

Current system behavior impact:

- `interview` mode: G-004 always runs; G-003 conditionally runs.
- `training` mode: G-004 runs; G-003 runs; balanced output returned.
- `analysis` mode: G-004 only; no feedback returned.
- Composition merge 只能是 envelope-level packaging，不得变成 semantic transformation。

## Hard System Invariants

- No scoring system exists.
- No taxonomy system exists.
- No coaching system exists.
- No cross-layer semantic mutation is allowed.
- No layer may override another layer's output semantics.
- Each layer is independent and immutable in responsibility.
- G-003, G-004 与 Composition Layer 不构成 sequential pipeline.
- Composition Layer 的 merge 只能是 envelope-level packaging，不得变成 semantic transformation.
- Layer 输出只能由产出该输出的 layer 负责定义，其他 layer 只能透传或并列返回。
- 历史设计中出现的 scoring、taxonomy、coaching 或 pipeline 表述不得被恢复为当前系统事实。

## Runtime Behavior Specification

### interview mode

- G-004 always runs.
- G-003 runs conditionally.
- Composition Layer merges outputs.
- 这里的 merge 只表示把 G-004 输出与可选 G-003 输出放入同一 response envelope；不得修改、解释或覆盖任一 layer 的语义。

### training mode

- G-004 runs.
- G-003 runs.
- balanced output returned.
- balanced output 表示同时返回 understanding 与 evaluation / feedback 两类结果；不得引入 scoring system、taxonomy system 或 coaching system。

### analysis mode

- G-004 only.
- no feedback returned.
- Composition Layer 不得在 analysis mode 中隐式触发 G-003，也不得从 G-004 输出推导 feedback。

## Forbidden Behaviors

- G-004 must NOT evolve into scoring engine.
- G-003 must NOT include reasoning or understanding model output.
- Composition Layer must NOT transform semantic meaning.
- No implicit shared taxonomy between layers.
- G-004 must NOT emit evaluation, feedback, verdict, score, grade, coaching plan, or rubric decision.
- G-003 must NOT emit transcript structure, behavioral-signal extraction, candidate reasoning trace, or understanding model.
- Composition Layer must NOT synthesize new semantic fields from cross-layer data.
- Composition Layer must NOT downgrade, upgrade, normalize, reinterpret, or override layer-owned status semantics.
- UI copy, API schemas, prompt wording, tests and future docs must preserve this boundary.

## Deprecation Rule

本文件是 interview-coach-refactor 的 active system spec。`docs/active/interview-coach-refactor.md` 已迁入本文件，不再作为 active 文档入口。

No other documentation is authoritative for the system definition of G-003, G-004, Composition Layer, runtime modes, layer responsibilities, or cross-layer semantic boundaries.

All previous design docs, audit notes, temporary workspace documents, planning records, goal packages, and merge records are historical. They may be used only as evidence of how the system reached this state. They must not override this final spec, reopen deprecated responsibilities, or introduce a competing source of truth.

Any future change to this architecture requires an explicitly authorized update to this file or a superseding ADR / active design update registered in `docs/00-governance/DOCS_INDEX.md`.

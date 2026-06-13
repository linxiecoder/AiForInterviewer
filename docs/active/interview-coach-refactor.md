---
title: Interview Coach Refactor Final System Spec
type: final-system-spec
status: final
updated: 2026-06-13
permalink: ai-for-interviewer/interview-coach-refactor
canonical: true
---

# Interview Coach Refactor Final System Spec

Status: FINAL SYSTEM SPEC

本文是 AiForInterviewer interview-coach-refactor 的唯一权威系统规格。它覆盖 G-003、G-004 与 Composition Layer 合入后的最终系统定义，并取代此前所有 G-003 / G-004 / Composition Layer 设计说明、审计记录、临时计划、历史摘要和阶段性记录的系统定义地位。

此前文档只保留为 historical evidence。任何旧文档、旧计划、历史审计或 archive 内容不得作为当前系统架构、职责边界、运行模式或语义 contract 的 authoritative source。

## Final System Architecture

### System Overview

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

## System Contract (Final State)

### G-003 responsibilities

G-003 是 Evaluation Layer，职责固定为：

- evaluation only
- feedback generation
- UI-safe status labeling

G-003 MUST NOT perform reasoning or understanding. 它不得解析 transcript 结构，不得抽取 behavioral signal，不得推断候选人的长期能力模型，也不得把 feedback 扩展成 coaching system。

### G-004 responsibilities

G-004 是 Understanding Layer，职责固定为：

- transcript understanding only
- structure extraction
- behavioral signal extraction

G-004 MUST NOT perform evaluation or scoring. 它不得生成 feedback，不得输出分数，不得解释为 rubric verdict，不得把 behavioral signal 升级为评价结论，也不得维护 taxonomy system。

### Composition Layer responsibilities

Composition Layer 是 Orchestration Layer，职责固定为：

- routing only
- decides invocation of G-003 / G-004
- MUST NOT modify or interpret outputs

Composition Layer 可以决定某个 mode 下调用哪些 layer，也可以把多个 layer 的输出放入同一个 response envelope。它不得修改任一 layer 的字段语义，不得替换 status 含义，不得把 G-004 的结构化理解解释成 G-003 的评价，也不得把 G-003 的 feedback 解释成 G-004 的 transcript understanding。

## Hard System Invariants

以下 invariant 是最终系统边界，不得被后续实现、文档、prompt、UI copy 或 orchestration 改写：

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

## System Boundary Rules

### Forbidden Behaviors

- G-004 must NOT evolve into scoring engine.
- G-003 must NOT include reasoning logic.
- Composition Layer must NOT transform semantic meaning.
- No implicit shared taxonomy between layers.
- G-004 must NOT emit evaluation, feedback, verdict, score, grade, coaching plan, or rubric decision.
- G-003 must NOT emit transcript structure, behavioral-signal extraction, candidate reasoning trace, or understanding model.
- Composition Layer must NOT synthesize new semantic fields from cross-layer data.
- Composition Layer must NOT downgrade, upgrade, normalize, reinterpret, or override layer-owned status semantics.
- UI copy, API schemas, prompt wording, tests and future docs must preserve this boundary.

## Deprecation Rule

`docs/active/interview-coach-refactor.md` is the FINAL SYSTEM SPEC for interview-coach-refactor.

No other documentation is authoritative for the system definition of G-003, G-004, Composition Layer, runtime modes, layer responsibilities, or cross-layer semantic boundaries.

All previous design docs, audit notes, temporary workspace documents, planning records, goal packages, and merge records are historical. They may be used only as evidence of how the system reached this state. They must not override this final spec, reopen deprecated responsibilities, or introduce a competing source of truth.

Any future change to this architecture requires an explicitly authorized update to this file. Until such update is made, this file remains the single source of truth.

## Proof: Non-existent Systems

The final architecture defines only these system modules:

- G-003: Evaluation Layer
- G-004: Understanding Layer
- Composition Layer: Orchestration Layer

It does not define a Scoring System. Any appearance of `scoring`, `score`, `rubric`, `grade`, or similar vocabulary in older artifacts is historical or forbidden in this architecture unless this file is explicitly updated.

It does not define a Taxonomy System. Any labels used inside one layer are layer-local contract fields only; they do not create shared ontology, cross-layer taxonomy, candidate classification model, or global semantic hierarchy.

It does not define a Coaching System. Feedback generation in G-003 is not coaching, not a training planner, not a long-term mentor model, and not a behavioral intervention system.

Therefore, the authoritative final system contains no scoring system, no taxonomy system, and no coaching system.

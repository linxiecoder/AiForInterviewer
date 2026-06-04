---
title: 02_CURRENT_BASELINE_AND_AUDIT
type: note
permalink: ai-for-interviewer/docs/project-sources/02-current-baseline-and-audit
---

# 02 Current Baseline and Audit

## 当前阶段性能力
- PolishUseCases 做过初步拆分。
- 反馈主链路已接入 FeedbackGenerationService。
- canonical evidence 已进入部分上下文。
- 出题侧已有 source_support_level / grounding gate / follow-up coverage 雏形。
- 反馈侧已有 asset_consistency_check / answer_coverage / answer_change_analysis / feedback_cards。
- runtime 已拒绝 LLM_PROVIDER=fake。
- eval seed 已存在。

## 核心审计结论
这些改造是必要的，但仍是过渡架构：
1. Application Service 可能只是 wrapper。
2. Question / Feedback 仍不是成熟 Agent。
3. Domain Policy、prompt、validation、post-processing、persistence 边界混乱。
4. CanonicalEvidencePack 不是所有链路唯一事实入口。
5. Eval 仍不足以证明 AI 质量。
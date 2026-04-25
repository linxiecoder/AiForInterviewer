import assert from "node:assert/strict";
import test from "node:test";

import { getFeedbackGenerationHint, getQuestionGenerationHint } from "./uiState.js";

test("question generation hint names both missing required inputs", () => {
  const hint = getQuestionGenerationHint({
    isJobDescriptionMissing: true,
    isResumeMarkdownMissing: true,
  });

  assert.equal(hint, "请先填写岗位 JD 和简历 Markdown。");
});

test("question generation hint confirms ready mock flow when required inputs exist", () => {
  const hint = getQuestionGenerationHint({
    isJobDescriptionMissing: false,
    isResumeMarkdownMissing: false,
  });

  assert.equal(hint, "已填写岗位 JD 和简历 Markdown，可以生成 3 条 mock 首轮问题。");
});

test("feedback generation hint blocks feedback before the first question is ready", () => {
  const hint = getFeedbackGenerationHint({
    hasFirstQuestion: false,
    hasAnswer: false,
  });

  assert.equal(hint, "请先生成首轮问题。");
});

test("feedback generation hint asks for the first answer before feedback", () => {
  const hint = getFeedbackGenerationHint({
    hasFirstQuestion: true,
    hasAnswer: false,
  });

  assert.equal(hint, "请填写第 1 题回答后再生成简版反馈。");
});

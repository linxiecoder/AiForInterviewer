import assert from "node:assert/strict";
import test from "node:test";

import { createMockInterviewGenerator } from "./mockInterviewGenerator.js";
import type { InterviewAnswer, JobDescription, ResumeMarkdown } from "./types.js";

const jobDescription: JobDescription = {
  id: "jd-demo",
  title: "前端工程师",
  content:
    "负责 React 应用交互体验、状态管理和复杂表单开发，需要关注可维护性与工程质量。",
};

const resumeMarkdown: ResumeMarkdown = {
  id: "resume-demo",
  content:
    "## 项目经历\n- 使用 React 和 TypeScript 搭建候选人工作台。\n- 负责组件抽象、接口联调和性能优化。",
};

test("mock generator returns exactly three first-round questions", () => {
  const generator = createMockInterviewGenerator();
  const questions = generator.generateFirstRoundQuestions(jobDescription, resumeMarkdown);

  assert.equal(questions.length, 3);
  assert.deepEqual(
    questions.map((question) => question.order),
    [1, 2, 3],
  );
  assert.ok(questions.every((question) => question.prompt.includes("React")));
});

test("mock generator returns markdown-compatible feedback without displayed score", () => {
  const generator = createMockInterviewGenerator();
  const [question] = generator.generateFirstRoundQuestions(jobDescription, resumeMarkdown);
  const answer: InterviewAnswer = {
    id: "answer-1",
    questionId: question.id,
    content: "我会先拆分表单状态，再用 TypeScript 类型约束和组件边界控制复杂度。",
    answeredAt: "2026-04-25T00:00:00.000Z",
  };

  const feedback = generator.generateFeedbackSummary({
    jobDescription,
    resumeMarkdown,
    question,
    answer,
  });

  assert.equal(feedback.score, undefined);
  assert.ok(feedback.overallJudgement.length > 0);
  assert.ok(feedback.strengths.length >= 1);
  assert.ok(feedback.gaps.length >= 1);
  assert.ok(feedback.nextFocus.length > 0);
  assert.ok(feedback.actionableSuggestions.length >= 1);
  assert.ok(feedback.markdown.includes("## 简版反馈摘要"));
  assert.ok(!feedback.markdown.includes("分数"));
});

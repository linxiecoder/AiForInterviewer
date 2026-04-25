import type {
  FeedbackSummary,
  FeedbackSummaryInput,
  InterviewGenerator,
  InterviewQuestion,
  JobDescription,
  LLMProvider,
  ResumeMarkdown,
} from "./types.js";

const keywordCandidates = [
  "React",
  "TypeScript",
  "状态管理",
  "复杂表单",
  "组件抽象",
  "性能优化",
  "工程质量",
  "接口联调",
];

const buildStableId = (prefix: string, seed: string) => {
  let hash = 0;
  for (const char of seed) {
    hash = (hash * 31 + char.charCodeAt(0)) >>> 0;
  }

  return `${prefix}-${hash.toString(16)}`;
};

const findPrimaryKeyword = (jobDescription: JobDescription, resumeMarkdown: ResumeMarkdown) => {
  const mergedText = `${jobDescription.content}\n${resumeMarkdown.content}`;

  return keywordCandidates.find((keyword) => mergedText.includes(keyword)) ?? "岗位核心能力";
};

const buildMarkdown = (feedback: Omit<FeedbackSummary, "markdown">) => {
  const strengthItems = feedback.strengths.map((item) => `- ${item}`).join("\n");
  const gapItems = feedback.gaps.map((item) => `- ${item}`).join("\n");
  const suggestionItems = feedback.actionableSuggestions.map((item) => `- ${item}`).join("\n");

  return [
    "## 简版反馈摘要",
    "",
    "### 总体判断",
    feedback.overallJudgement,
    "",
    "### 回答亮点",
    strengthItems,
    "",
    "### 主要缺口",
    gapItems,
    "",
    "### 下一步打磨方向",
    feedback.nextFocus,
    "",
    "### 可执行建议",
    suggestionItems,
  ].join("\n");
};

export class MockInterviewGenerator implements InterviewGenerator {
  generateFirstRoundQuestions(
    jobDescription: JobDescription,
    resumeMarkdown: ResumeMarkdown,
  ): InterviewQuestion[] {
    const now = new Date().toISOString();
    const keyword = findPrimaryKeyword(jobDescription, resumeMarkdown);
    const seed = `${jobDescription.content}|${resumeMarkdown.content}`;

    return [
      {
        id: buildStableId("question", `${seed}|1`),
        order: 1,
        prompt: `请结合你在简历中与 ${keyword} 相关的经历，说明你如何拆解一个复杂业务问题。`,
        focusArea: "经历拆解",
        source: "mock",
        createdAt: now,
      },
      {
        id: buildStableId("question", `${seed}|2`),
        order: 2,
        prompt: `如果岗位要求持续提升 ${keyword} 相关工程质量，你会优先建立哪些判断标准？`,
        focusArea: "工程判断",
        source: "mock",
        createdAt: now,
      },
      {
        id: buildStableId("question", `${seed}|3`),
        order: 3,
        prompt: `围绕 ${keyword} 的协作交付，请举例说明你如何处理需求变化和边界沟通。`,
        focusArea: "协作边界",
        source: "mock",
        createdAt: now,
      },
    ];
  }

  generateFeedbackSummary(input: FeedbackSummaryInput): FeedbackSummary {
    const now = new Date().toISOString();
    const primaryKeyword = findPrimaryKeyword(input.jobDescription, input.resumeMarkdown);
    const answerText = input.answer.content.trim();
    const hasConcreteMethod = /先|步骤|拆分|指标|验证|复盘|边界/.test(answerText);

    const feedbackBase: Omit<FeedbackSummary, "markdown"> = {
      id: buildStableId("feedback", `${input.question.id}|${answerText}`),
      overallJudgement: hasConcreteMethod
        ? `回答已经围绕 ${primaryKeyword} 给出处理思路，适合作为首轮追问基础。`
        : `回答覆盖了 ${primaryKeyword} 方向，但还需要补充更明确的行动过程。`,
      strengths: [
        "能回应题目中的核心能力要求，没有偏离岗位场景。",
        hasConcreteMethod
          ? "表达里出现了拆解或验证动作，便于继续追问细节。"
          : "已经给出个人经验方向，可以继续补充具体项目证据。",
      ],
      gaps: [
        "缺少可复述的项目背景、约束条件和最终结果。",
        "还没有说明如何判断方案有效，也缺少失败或权衡处理。",
      ],
      nextFocus: `下一轮应把 ${primaryKeyword} 相关经历压缩成“背景-动作-结果-复盘”的 60 秒回答。`,
      actionableSuggestions: [
        "补充一个具体项目名称和当时的业务约束。",
        "说明你亲自负责的动作，避免只描述团队整体产出。",
        "用一句话交代结果或影响，例如效率、质量或协作改善。",
      ],
      createdAt: now,
      dimensions: {
        relevance: "岗位相关性",
        evidence: "证据具体度",
        structure: "回答结构",
      },
    };

    return {
      ...feedbackBase,
      markdown: buildMarkdown(feedbackBase),
    };
  }
}

export const createMockInterviewGenerator = () => new MockInterviewGenerator();

export const createMockLLMProvider = (): LLMProvider => {
  const generator = createMockInterviewGenerator();

  return {
    id: "mock-local-provider",
    name: "本地 Mock Provider",
    mode: "mock",
    generator,
  };
};

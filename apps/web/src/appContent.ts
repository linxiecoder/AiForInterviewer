export const sampleInputs = {
  jobDescription:
    "我们正在招聘前端工程师，负责 React + TypeScript 业务系统建设，关注复杂表单、状态管理、组件抽象和工程质量。",
  resumeMarkdown:
    "## 项目经历\n- 使用 React 和 TypeScript 搭建候选人工作台。\n- 负责组件抽象、接口联调和性能优化。\n- 推动前端质量检查和代码评审规范。",
} as const;

export const appText = {
  header: {
    eyebrow: "W10 首切片 / apps/web mock 原型",
    title: "AI 模拟面试首切片原型",
    copy: "JD + 简历 Markdown 生成 3 条首轮问题，只进入第 1 题问答并输出简版反馈。",
  },
  statusBadges: ["Mock LLM", "单次会话临时数据"],
  boundary: {
    title: "原型边界",
    description:
      "当前数据只保存在浏览器页面状态中，刷新后回到示例输入；不连接真实 LLM，不做登录或长期保存。",
  },
  workflowStages: [
    {
      id: "input",
      label: "输入",
      description: "岗位 JD + 简历 Markdown",
    },
    {
      id: "questions",
      label: "首轮问题",
      description: "生成 3 条 mock 问题",
    },
    {
      id: "answer",
      label: "第 1 题问答",
      description: "只记录 1 次回答",
    },
    {
      id: "feedback",
      label: "简版反馈",
      description: "Markdown 兼容文本",
    },
  ],
  fields: {
    jobDescription: {
      label: "岗位 JD",
      helper: "粘贴目标岗位说明，至少保留岗位名称、核心职责和必需技能。",
      placeholder: "示例：前端工程师，负责 React 业务系统、复杂表单和工程质量建设。",
    },
    resumeMarkdown: {
      label: "简历 Markdown",
      helper: "粘贴当前简历片段，优先保留项目经历、工作经历和可映射到岗位要求的证据。",
      placeholder: "示例：## 项目经历\n- 使用 React 和 TypeScript 搭建候选人工作台。",
    },
    firstAnswer: {
      fallbackLabel: "先生成首轮问题",
      helper: "当前切片只处理第 1 题，不开启多轮追问或长期记忆。",
      placeholder: "写下你对第 1 题的回答，系统会基于当前 JD、简历和回答生成简版反馈。",
    },
  },
  actions: {
    generateQuestions: "生成 3 条首轮问题",
    generateFeedback: "生成简版反馈",
  },
  panels: {
    questionsTitle: "首轮问题",
    answerTitle: "第 1 题回答",
    feedbackTitle: "简版反馈摘要（Markdown 兼容）",
  },
  emptyStates: {
    questions: "等待生成。填写 JD 与简历后生成 3 条首轮问题。",
    feedback: "等待第 1 题回答与反馈生成。",
  },
} as const;

export type WorkflowStageId = (typeof appText.workflowStages)[number]["id"];

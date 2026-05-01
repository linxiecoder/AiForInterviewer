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

export const workbenchHomeText = {
  header: {
    eyebrow: "R1 可信工作台闭环",
    title: "AI 模拟面试工作台",
    copy:
      "围绕岗位、简历、知识库、模拟记录、评分复盘和导出证据链组织 R1 工作台入口。",
  },
  statusTags: ["PostgreSQL", "RAG citation", "traceability", "0-100 scoring", "E2E protected"],
  primaryActions: [
    {
      title: "发起模拟面试",
      description: "选择岗位、简历和知识来源后进入文本面试台。",
      href: "/interviews/new",
      status: "真实入口",
    },
    {
      title: "历史记录",
      description: "查看最近模拟、待处理复盘和导出快照。",
      href: "/interviews",
      status: "R1 重点",
    },
    {
      title: "岗位管理",
      description: "维护岗位目标、职责、能力要求和匹配线索。",
      href: "/jobs",
      status: "材料入口",
    },
    {
      title: "简历管理",
      description: "维护简历要点、项目经历和可引用证据。",
      href: "/resumes",
      status: "材料入口",
    },
    {
      title: "复盘",
      description: "查看评分复盘、弱项建议、导出状态和证据缺口。",
      href: "/reviews",
      status: "验收入口",
    },
  ],
  recentInterviews: [
    {
      title: "React 前端工程师模拟复盘",
      sessionId: "session-r1-trace",
      ownerId: "owner-e2e",
      status: "feedback_ready",
      score: 82,
      updatedAt: "2026-05-01 10:20",
      description: "已生成评分、RAG citation、evidence gap 和 Markdown export 状态。",
      href: "/interviews/session-r1-trace?owner_id=owner-e2e",
    },
  ],
  capabilitySummary: [
    {
      title: "Trace summary",
      description: "展示 session、turn、answer、score、review、export 等可追踪引用。",
      tags: ["traceability"],
    },
    {
      title: "RAG citation 证据",
      description: "展示引用来源、chunk 摘要、chunk index 和 position。",
      tags: ["RAG citation"],
    },
    {
      title: "Evidence gap",
      description: "展示 no_result、permission_filtered、index_pending 等证据缺口。",
      tags: ["evidence gap"],
    },
    {
      title: "0-100 score report",
      description: "展示总分、维度分、理由、低置信度和建议。",
      tags: ["0-100 scoring"],
    },
    {
      title: "Review evidence chain",
      description: "关联评分、复盘、弱项、建议和导出引用。",
      tags: ["review evidence chain"],
    },
    {
      title: "Markdown export",
      description: "展示导出状态、失败原因和 retryable 提示。",
      tags: ["Markdown export", "degraded", "failed", "retryable"],
    },
  ],
  entitySummary: [
    {
      label: "岗位",
      value: "当前岗位目标 1 个",
    },
    {
      label: "简历",
      value: "候选简历材料 1 份",
    },
    {
      label: "知识库",
      value: "RAG 索引状态可见",
    },
    {
      label: "复盘",
      value: "可信详情页已接入",
    },
  ],
} as const;

export const workbenchNavigation = [
  {
    label: "工作台",
    href: "/",
  },
  {
    label: "岗位",
    href: "/jobs",
  },
  {
    label: "简历",
    href: "/resumes",
  },
  {
    label: "历史记录",
    href: "/interviews",
  },
  {
    label: "发起面试",
    href: "/interviews/new",
  },
  {
    label: "复盘",
    href: "/reviews",
  },
] as const;

export const workbenchRoutePages = {
  jobs: {
    eyebrow: "R1B-01 工作台入口 / 岗位",
    title: "岗位管理",
    copy: "当前阶段提供真实可访问的岗位管理入口，后续再接入岗位创建、编辑和服务端保存。",
    stage: "R1B-01 只修复入口验收，不新增岗位后端 API 或数据库 schema。",
    emptyTitle: "暂无岗位列表",
    emptyDescription: "可以先从发起模拟面试入口进入最小主链路，岗位持久化将在后续 R1 切片接入。",
    facts: [
      "入口 route: /jobs",
      "当前数据来源: 静态空态",
      "禁止范围: 不新增岗位 API、不新增 DB migration",
    ],
  },
  resumes: {
    eyebrow: "R1B-01 工作台入口 / 简历",
    title: "简历管理",
    copy: "当前阶段提供真实可访问的简历管理入口，后续再接入简历录入、解析和服务端保存。",
    stage: "R1B-01 只修复入口验收，不新增简历后端 API 或对象存储能力。",
    emptyTitle: "暂无简历材料",
    emptyDescription: "简历材料持久化将在后续 R1 切片接入；本页先保证入口可访问且不伪装完成能力。",
    facts: [
      "入口 route: /resumes",
      "当前数据来源: 静态空态",
      "禁止范围: 不接入对象存储、不新增解析服务",
    ],
  },
  interviewsNew: {
    eyebrow: "R1B-01 工作台入口 / 发起",
    title: "发起模拟面试",
    copy: "当前阶段提供真实可访问的发起入口，后续再接入岗位、简历和问题生成主链路。",
    stage: "R1B-01 不接入真实 LLM，也不新增面试创建 API。",
    emptyTitle: "面试发起表单尚未接入",
    emptyDescription: "本页是 R1B-01 验收入口，避免首页继续停留在锚点跳转。",
    facts: [
      "入口 route: /interviews/new",
      "当前能力: 可访问页面与阶段说明",
      "禁止范围: 不接入 LLM、不新增后端创建接口",
    ],
  },
  reviews: {
    eyebrow: "R1B-01 工作台入口 / 复盘",
    title: "复盘",
    copy: "当前阶段提供真实可访问的复盘列表入口；可信详情仍由 /interviews/:sessionId 承接。",
    stage: "R1B-01 保留现有可信详情页，不扩展复盘后端 contract。",
    emptyTitle: "暂无独立复盘列表",
    emptyDescription: "已有复盘详情可从历史记录进入；独立复盘列表将在后续 R1 切片接入。",
    facts: [
      "入口 route: /reviews",
      "当前详情能力: /interviews/:sessionId",
      "禁止范围: 不新增复盘 API、不扩展导出链路",
    ],
  },
} as const;

import { useMemo, useState } from "react";

import { createMockInterviewGenerator } from "./interview/mockInterviewGenerator.js";
import type {
  FeedbackSummary,
  InterviewAnswer,
  InterviewSession,
  JobDescription,
  ResumeMarkdown,
} from "./interview/types.js";

const initialJobDescription =
  "我们正在招聘前端工程师，负责 React + TypeScript 业务系统建设，关注复杂表单、状态管理、组件抽象和工程质量。";

const initialResumeMarkdown =
  "## 项目经历\n- 使用 React 和 TypeScript 搭建候选人工作台。\n- 负责组件抽象、接口联调和性能优化。\n- 推动前端质量检查和代码评审规范。";

const createBrowserId = (prefix: string) => {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return `${prefix}-${crypto.randomUUID()}`;
  }

  return `${prefix}-${Date.now()}`;
};

const createMarkdownPreview = (feedback: FeedbackSummary | undefined) => {
  if (!feedback) {
    return "";
  }

  return feedback.markdown;
};

export function App() {
  const generator = useMemo(() => createMockInterviewGenerator(), []);
  const [jobDescriptionText, setJobDescriptionText] = useState(initialJobDescription);
  const [resumeMarkdownText, setResumeMarkdownText] = useState(initialResumeMarkdown);
  const [session, setSession] = useState<InterviewSession | undefined>();
  const [firstAnswer, setFirstAnswer] = useState("");

  const canGenerateQuestions =
    jobDescriptionText.trim().length > 0 && resumeMarkdownText.trim().length > 0;
  const firstQuestion = session?.questions[0];
  const canGenerateFeedback = Boolean(firstQuestion && firstAnswer.trim().length > 0);
  const missingInputLabels = [
    jobDescriptionText.trim().length === 0 ? "岗位 JD" : undefined,
    resumeMarkdownText.trim().length === 0 ? "简历 Markdown" : undefined,
  ].filter((label): label is string => Boolean(label));
  const missingInputText =
    missingInputLabels.length === 2
      ? `${missingInputLabels[0]} 和${missingInputLabels[1]}`
      : missingInputLabels[0];
  const questionGenerationHint =
    missingInputLabels.length > 0
      ? `请先填写${missingInputText}。`
      : "已填写岗位 JD 和简历 Markdown，可以生成 3 条 mock 首轮问题。";
  const feedbackGenerationHint = !firstQuestion
    ? "请先生成首轮问题。"
    : firstAnswer.trim().length === 0
      ? "请填写第 1 题回答后再生成简版反馈。"
      : "第 1 题回答已就绪，可以生成简版反馈。";

  const handleGenerateQuestions = () => {
    const now = new Date().toISOString();
    const jobDescription: JobDescription = {
      id: createBrowserId("jd"),
      title: "当前岗位",
      content: jobDescriptionText.trim(),
      createdAt: now,
    };
    const resumeMarkdown: ResumeMarkdown = {
      id: createBrowserId("resume"),
      content: resumeMarkdownText.trim(),
      createdAt: now,
    };
    const questions = generator.generateFirstRoundQuestions(jobDescription, resumeMarkdown);

    setSession({
      id: createBrowserId("session"),
      jobDescription,
      resumeMarkdown,
      questions,
      answers: [],
      status: "questions_ready",
      createdAt: now,
      updatedAt: now,
    });
    setFirstAnswer("");
  };

  const handleGenerateFeedback = () => {
    if (!session || !firstQuestion) {
      return;
    }

    const now = new Date().toISOString();
    const answer: InterviewAnswer = {
      id: createBrowserId("answer"),
      questionId: firstQuestion.id,
      content: firstAnswer.trim(),
      answeredAt: now,
    };
    const feedbackSummary = generator.generateFeedbackSummary({
      jobDescription: session.jobDescription,
      resumeMarkdown: session.resumeMarkdown,
      question: firstQuestion,
      answer,
    });

    setSession({
      ...session,
      answers: [answer],
      feedbackSummary,
      status: "feedback_ready",
      updatedAt: now,
    });
  };

  return (
    <main className="app-shell">
      <section className="workspace-header" aria-labelledby="page-title">
        <div>
          <p className="eyebrow">W10-D / apps/web</p>
          <h1 id="page-title">AI 模拟面试首切片原型</h1>
          <p className="header-copy">
            仅用于首切片 mock 原型验证，不连接真实 LLM，不做登录或长期保存。
          </p>
        </div>
        <div className="status-pill">Mock Provider</div>
      </section>

      <section className="boundary-note" aria-label="原型边界">
        <strong>原型边界</strong>
        <span>当前数据只保存在浏览器页面状态中，刷新后会回到示例输入。</span>
      </section>

      <section className="workbench" aria-label="首切片输入与输出">
        <div className="input-column">
          <label className="field-block">
            <span>岗位 JD</span>
            <textarea
              value={jobDescriptionText}
              onChange={(event) => setJobDescriptionText(event.target.value)}
              rows={9}
            />
          </label>

          <label className="field-block">
            <span>简历 Markdown</span>
            <textarea
              value={resumeMarkdownText}
              onChange={(event) => setResumeMarkdownText(event.target.value)}
              rows={11}
            />
          </label>

          <p className="helper-text" id="question-generation-hint" aria-live="polite">
            {questionGenerationHint}
          </p>
          <button
            className="primary-action"
            type="button"
            onClick={handleGenerateQuestions}
            disabled={!canGenerateQuestions}
            aria-describedby="question-generation-hint"
          >
            生成首轮问题
          </button>
        </div>

        <div className="output-column">
          <section className="panel" aria-labelledby="questions-title">
            <div className="panel-heading">
              <h2 id="questions-title">首轮问题</h2>
              <span>{session?.questions.length ?? 0}/3</span>
            </div>

            <ol className="question-list">
              {session?.questions.map((question) => (
                <li key={question.id}>
                  <div className="question-order">Q{question.order}</div>
                  <p>{question.prompt}</p>
                  <span>{question.focusArea}</span>
                </li>
              )) ?? <li className="empty-state">等待生成</li>}
            </ol>
          </section>

          <section className="panel" aria-labelledby="answer-title">
            <div className="panel-heading">
              <h2 id="answer-title">第 1 题回答</h2>
              <span>{firstQuestion ? "已选中" : "未生成"}</span>
            </div>

            <label className="field-block compact">
              <span>{firstQuestion?.prompt ?? "先生成首轮问题"}</span>
              <textarea
                value={firstAnswer}
                onChange={(event) => setFirstAnswer(event.target.value)}
                rows={6}
                disabled={!firstQuestion}
              />
            </label>

            <p className="helper-text" id="feedback-generation-hint" aria-live="polite">
              {feedbackGenerationHint}
            </p>
            <button
              className="secondary-action"
              type="button"
              onClick={handleGenerateFeedback}
              disabled={!canGenerateFeedback}
              aria-describedby="feedback-generation-hint"
            >
              生成简版反馈
            </button>
          </section>

          <section className="panel feedback-panel" aria-labelledby="feedback-title">
            <div className="panel-heading">
              <h2 id="feedback-title">Markdown 兼容结果</h2>
              <span>{session?.feedbackSummary ? "已生成" : "未生成"}</span>
            </div>
            <pre>{createMarkdownPreview(session?.feedbackSummary) || "等待第 1 题回答与反馈生成"}</pre>
          </section>
        </div>
      </section>
    </main>
  );
}

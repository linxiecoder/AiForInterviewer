import { useMemo, useState } from "react";

import { appText, sampleInputs, type WorkflowStageId } from "./appContent.js";
import { StageStrip, type WorkflowStageStatus } from "./components/StageStrip.js";
import { TrustedTracePage } from "./components/TrustedTracePage.js";
import { createMockInterviewGenerator } from "./interview/mockInterviewGenerator.js";
import {
  getFeedbackGenerationHint,
  getMissingInputLabels,
  getQuestionGenerationHint,
} from "./interview/uiState.js";
import type {
  FeedbackSummary,
  InterviewAnswer,
  InterviewSession,
  JobDescription,
  ResumeMarkdown,
} from "./interview/types.js";

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
  const currentPath = typeof window === "undefined" ? "/" : window.location.pathname;
  if (currentPath.startsWith("/interviews/")) {
    const sessionId = decodeURIComponent(currentPath.replace(/^\/interviews\//, ""));
    const ownerId =
      typeof window === "undefined"
        ? "owner-local"
        : new URLSearchParams(window.location.search).get("owner_id") ?? "owner-local";

    return <TrustedTracePage sessionId={sessionId} ownerId={ownerId} />;
  }

  const generator = useMemo(() => createMockInterviewGenerator(), []);
  const [jobDescriptionText, setJobDescriptionText] = useState<string>(
    sampleInputs.jobDescription,
  );
  const [resumeMarkdownText, setResumeMarkdownText] = useState<string>(
    sampleInputs.resumeMarkdown,
  );
  const [session, setSession] = useState<InterviewSession | undefined>();
  const [firstAnswer, setFirstAnswer] = useState("");

  const isJobDescriptionMissing = jobDescriptionText.trim().length === 0;
  const isResumeMarkdownMissing = resumeMarkdownText.trim().length === 0;
  const hasFirstQuestion = Boolean(session?.questions[0]);
  const hasFirstAnswer = firstAnswer.trim().length > 0;
  const hasFeedback = Boolean(session?.feedbackSummary);
  const canGenerateQuestions =
    !isJobDescriptionMissing && !isResumeMarkdownMissing;
  const firstQuestion = session?.questions[0];
  const canGenerateFeedback = Boolean(firstQuestion && hasFirstAnswer);
  const missingInputLabels = getMissingInputLabels({
    isJobDescriptionMissing,
    isResumeMarkdownMissing,
  });
  const questionGenerationHint = getQuestionGenerationHint({
    isJobDescriptionMissing,
    isResumeMarkdownMissing,
  });
  const feedbackGenerationHint = getFeedbackGenerationHint({
    hasFirstQuestion,
    hasAnswer: hasFirstAnswer,
  });
  const workflowStageStatus: Record<WorkflowStageId, WorkflowStageStatus> = {
    input: session ? "done" : "current",
    questions: session ? "done" : "waiting",
    answer: !firstQuestion ? "waiting" : hasFirstAnswer ? "done" : "current",
    feedback: hasFeedback ? "done" : canGenerateFeedback ? "current" : "waiting",
  };
  const workflowStages = appText.workflowStages.map((stage) => ({
    ...stage,
    status: workflowStageStatus[stage.id],
  }));

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
          <p className="eyebrow">{appText.header.eyebrow}</p>
          <h1 id="page-title">{appText.header.title}</h1>
          <p className="header-copy">{appText.header.copy}</p>
        </div>
        <div className="status-group" aria-label="原型状态">
          {appText.statusBadges.map((badge) => (
            <div className="status-pill" key={badge}>
              {badge}
            </div>
          ))}
        </div>
      </section>

      <section className="boundary-note" aria-label="原型边界">
        <strong>{appText.boundary.title}</strong>
        <span>{appText.boundary.description}</span>
      </section>

      <StageStrip stages={workflowStages} />

      <section className="workbench" aria-label="首切片输入与输出">
        <div className="input-column">
          <label className="field-block">
            <span>{appText.fields.jobDescription.label}</span>
            <p className="field-hint" id="job-description-hint">
              {appText.fields.jobDescription.helper}
            </p>
            <textarea
              value={jobDescriptionText}
              onChange={(event) => setJobDescriptionText(event.target.value)}
              placeholder={appText.fields.jobDescription.placeholder}
              aria-describedby="job-description-hint question-generation-hint"
              aria-invalid={isJobDescriptionMissing}
              rows={9}
            />
          </label>

          <label className="field-block">
            <span>{appText.fields.resumeMarkdown.label}</span>
            <p className="field-hint" id="resume-markdown-hint">
              {appText.fields.resumeMarkdown.helper}
            </p>
            <textarea
              value={resumeMarkdownText}
              onChange={(event) => setResumeMarkdownText(event.target.value)}
              placeholder={appText.fields.resumeMarkdown.placeholder}
              aria-describedby="resume-markdown-hint question-generation-hint"
              aria-invalid={isResumeMarkdownMissing}
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
            {appText.actions.generateQuestions}
          </button>
        </div>

        <div className="output-column">
          <section className="panel" aria-labelledby="questions-title">
            <div className="panel-heading">
              <h2 id="questions-title">{appText.panels.questionsTitle}</h2>
              <span>{session?.questions.length ?? 0}/3</span>
            </div>

            <ol className="question-list" aria-live="polite">
              {session?.questions.map((question) => (
                <li key={question.id}>
                  <div className="question-order">Q{question.order}</div>
                  <p>{question.prompt}</p>
                  <span>{question.focusArea}</span>
                </li>
              )) ?? <li className="empty-state">{appText.emptyStates.questions}</li>}
            </ol>
          </section>

          <section className="panel" aria-labelledby="answer-title">
            <div className="panel-heading">
              <h2 id="answer-title">{appText.panels.answerTitle}</h2>
              <span>{firstQuestion ? "已选中" : "未生成"}</span>
            </div>

            <label className="field-block compact">
              <span>{firstQuestion?.prompt ?? appText.fields.firstAnswer.fallbackLabel}</span>
              <p className="field-hint" id="first-answer-hint">
                {appText.fields.firstAnswer.helper}
              </p>
              <textarea
                value={firstAnswer}
                onChange={(event) => setFirstAnswer(event.target.value)}
                placeholder={appText.fields.firstAnswer.placeholder}
                aria-describedby="first-answer-hint feedback-generation-hint"
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
              {appText.actions.generateFeedback}
            </button>
          </section>

          <section className="panel feedback-panel" aria-labelledby="feedback-title">
            <div className="panel-heading">
              <h2 id="feedback-title">{appText.panels.feedbackTitle}</h2>
              <span>{session?.feedbackSummary ? "已生成" : "未生成"}</span>
            </div>
            <pre aria-live="polite" tabIndex={0}>
              {createMarkdownPreview(session?.feedbackSummary) || appText.emptyStates.feedback}
            </pre>
          </section>
        </div>
      </section>
    </main>
  );
}

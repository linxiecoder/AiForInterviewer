export interface JobDescription {
  id: string;
  title?: string;
  content: string;
  createdAt?: string;
}

export interface ResumeMarkdown {
  id: string;
  content: string;
  createdAt?: string;
}

export interface InterviewQuestion {
  id: string;
  order: number;
  prompt: string;
  focusArea: string;
  source: "mock";
  createdAt: string;
}

export interface InterviewAnswer {
  id: string;
  questionId: string;
  content: string;
  answeredAt: string;
}

export interface FeedbackSummary {
  id: string;
  overallJudgement: string;
  strengths: string[];
  gaps: string[];
  nextFocus: string;
  actionableSuggestions: string[];
  markdown: string;
  score?: number;
  dimensions?: Record<string, string>;
  createdAt: string;
}

export interface InterviewSession {
  id: string;
  jobDescription: JobDescription;
  resumeMarkdown: ResumeMarkdown;
  questions: InterviewQuestion[];
  answers: InterviewAnswer[];
  feedbackSummary?: FeedbackSummary;
  status: "draft" | "questions_ready" | "feedback_ready";
  createdAt: string;
  updatedAt: string;
}

export interface FeedbackSummaryInput {
  jobDescription: JobDescription;
  resumeMarkdown: ResumeMarkdown;
  question: InterviewQuestion;
  answer: InterviewAnswer;
}

export interface QuestionGenerator {
  generateFirstRoundQuestions(
    jobDescription: JobDescription,
    resumeMarkdown: ResumeMarkdown,
  ): InterviewQuestion[];
}

export interface FeedbackGenerator {
  generateFeedbackSummary(input: FeedbackSummaryInput): FeedbackSummary;
}

export interface InterviewGenerator extends QuestionGenerator, FeedbackGenerator {}

export interface LLMProvider {
  id: string;
  name: string;
  mode: "mock";
  generator: InterviewGenerator;
}

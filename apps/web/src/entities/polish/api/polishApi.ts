import { request, buildSuccessData } from "../../../shared/api/client";
import type {
  CreatePolishAnswerRequest,
  CreatePolishFeedbackTaskRequest,
  CreatePolishQuestionTaskRequest,
  CreatePolishSessionRequest,
  PolishAnswer,
  PolishSessionDetail,
  PolishSessionSummary,
  PolishTaskStatus,
  PolishTopic,
} from "../model/types";

export const POLISH_API_PATHS = {
  sessions: "/polish-sessions",
  sessionDetail: (sessionId: string) => `/polish-sessions/${encodeURIComponent(sessionId)}` as `/polish-sessions/${string}`,
  questionTask: (sessionId: string) => `/polish-sessions/${encodeURIComponent(sessionId)}/questions` as `/polish-sessions/${string}/questions`,
  progressTreeState: (sessionId: string) => `/polish-sessions/${encodeURIComponent(sessionId)}/progress-tree/state` as `/polish-sessions/${string}/progress-tree/state`,
  answers: (sessionId: string) => `/polish-sessions/${encodeURIComponent(sessionId)}/answers` as `/polish-sessions/${string}/answers`,
  feedbackTask: (sessionId: string) => `/polish-sessions/${encodeURIComponent(sessionId)}/feedback` as `/polish-sessions/${string}/feedback`,
  topics: "/polish-topics",
} as const;

export async function fetchPolishSessions(): Promise<PolishSessionSummary[]> {
  const response = await request<PolishSessionSummary[]>(POLISH_API_PATHS.sessions);
  const data = buildSuccessData(response);
  return data ?? [];
}

export async function fetchPolishTopics(resumeJobBindingId?: string): Promise<PolishTopic[]> {
  const query = resumeJobBindingId
    ? `?resume_job_binding_id=${encodeURIComponent(resumeJobBindingId)}`
    : "";
  const response = await request<PolishTopic[]>(`${POLISH_API_PATHS.topics}${query}`);
  const data = buildSuccessData(response);
  return data ?? [];
}

export async function createPolishSession(payload: CreatePolishSessionRequest): Promise<PolishSessionDetail> {
  const response = await request<PolishSessionDetail>(POLISH_API_PATHS.sessions, {
    method: "POST",
    body: payload,
  });
  const data = buildSuccessData(response);
  if (data === null) {
    throw new Error("模拟面试创建返回为空");
  }
  return data;
}

export async function fetchPolishSession(sessionId: string): Promise<PolishSessionDetail> {
  const response = await request<PolishSessionDetail>(POLISH_API_PATHS.sessionDetail(sessionId));
  const data = buildSuccessData(response);
  if (data === null) {
    throw new Error("模拟面试详情返回为空");
  }
  return data;
}

export async function createPolishQuestionTask(
  sessionId: string,
  payload: CreatePolishQuestionTaskRequest,
): Promise<PolishTaskStatus> {
  const response = await request<PolishTaskStatus>(POLISH_API_PATHS.questionTask(sessionId), {
    method: "POST",
    body: payload,
  });
  const data = buildSuccessData(response);
  if (data === null) {
    throw new Error("题目生成任务返回为空");
  }
  return data;
}

export async function refreshPolishProgressTreeState(sessionId: string): Promise<PolishSessionDetail> {
  const response = await request<PolishSessionDetail>(POLISH_API_PATHS.progressTreeState(sessionId), {
    method: "POST",
  });
  const data = buildSuccessData(response);
  if (data === null) {
    throw new Error("进展树刷新返回为空");
  }
  return data;
}

export async function createPolishAnswer(
  sessionId: string,
  payload: CreatePolishAnswerRequest,
): Promise<PolishAnswer> {
  const response = await request<PolishAnswer>(POLISH_API_PATHS.answers(sessionId), {
    method: "POST",
    body: payload,
  });
  const data = buildSuccessData(response);
  if (data === null) {
    throw new Error("回答保存返回为空");
  }
  return data;
}

export async function createPolishFeedbackTask(
  sessionId: string,
  payload: CreatePolishFeedbackTaskRequest,
): Promise<PolishTaskStatus> {
  const response = await request<PolishTaskStatus>(POLISH_API_PATHS.feedbackTask(sessionId), {
    method: "POST",
    body: payload,
  });
  const data = buildSuccessData(response);
  if (data === null) {
    throw new Error("反馈生成任务返回为空");
  }
  return data;
}

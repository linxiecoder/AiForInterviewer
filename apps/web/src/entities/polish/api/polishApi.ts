import { request, buildSuccessData } from "../../../shared/api/client";
import type {
  CreatePolishAnswerRequest,
  CreatePolishFeedbackTaskRequest,
  CreatePolishFeedbackNextQuestionIntentRequest,
  CreatePolishSessionRequest,
  PolishAnswer,
  PolishCandidate,
  PolishCandidateActionResult,
  PolishSessionDetail,
  PolishSessionSummary,
  PolishTaskStatus,
  PolishTopic,
} from "../model/types";

export const POLISH_API_PATHS = {
  sessions: "/polish-sessions",
  sessionDetail: (sessionId: string) => `/polish-sessions/${encodeURIComponent(sessionId)}` as `/polish-sessions/${string}`,
  feedbackNextQuestionTask: (sessionId: string, feedbackId: string) =>
    `/polish-sessions/${encodeURIComponent(sessionId)}/feedback/${encodeURIComponent(feedbackId)}/next-question` as `/polish-sessions/${string}/feedback/${string}/next-question`,
  completeQuestion: (sessionId: string, questionId: string) => `/polish-sessions/${encodeURIComponent(sessionId)}/questions/${encodeURIComponent(questionId)}/complete` as `/polish-sessions/${string}/questions/${string}/complete`,
  endSession: (sessionId: string) => `/polish-sessions/${encodeURIComponent(sessionId)}/end` as `/polish-sessions/${string}/end`,
  sessionReport: (sessionId: string) => `/polish-sessions/${encodeURIComponent(sessionId)}/report` as `/polish-sessions/${string}/report`,
  softDeleteSession: (sessionId: string) => `/polish-sessions/${encodeURIComponent(sessionId)}/delete` as `/polish-sessions/${string}/delete`,
  progressTreeGenerate: (sessionId: string) => `/polish-sessions/${encodeURIComponent(sessionId)}/progress-tree/generate` as `/polish-sessions/${string}/progress-tree/generate`,
  progressTreeState: (sessionId: string) => `/polish-sessions/${encodeURIComponent(sessionId)}/progress-tree/state` as `/polish-sessions/${string}/progress-tree/state`,
  answers: (sessionId: string) => `/polish-sessions/${encodeURIComponent(sessionId)}/answers` as `/polish-sessions/${string}/answers`,
  feedbackTask: (sessionId: string) => `/polish-sessions/${encodeURIComponent(sessionId)}/feedback` as `/polish-sessions/${string}/feedback`,
  topics: "/polish-topics",
  candidates: "/polish-candidates",
  candidateDetail: (candidateId: string) => `/polish-candidates/${encodeURIComponent(candidateId)}` as `/polish-candidates/${string}`,
  confirmCandidate: (candidateId: string) => `/polish-candidates/${encodeURIComponent(candidateId)}/confirm` as `/polish-candidates/${string}/confirm`,
  dismissCandidate: (candidateId: string) => `/polish-candidates/${encodeURIComponent(candidateId)}/dismiss` as `/polish-candidates/${string}/dismiss`,
} as const;

export interface FetchPolishCandidateFilters {
  status?: string | null;
  candidate_type?: string | null;
  session_id?: string | null;
  source_type?: string | null;
  confidence_level?: string | null;
  limit?: number | null;
  offset?: number | null;
}

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

export async function fetchPolishCandidates(filters: FetchPolishCandidateFilters = {}): Promise<PolishCandidate[]> {
  const query = buildPolishCandidateQuery(filters);
  const response = await request<PolishCandidate[]>(`${POLISH_API_PATHS.candidates}${query}`);
  const data = buildSuccessData(response);
  return data ?? [];
}

export async function confirmPolishCandidate(candidateId: string): Promise<PolishCandidateActionResult> {
  const response = await request<PolishCandidateActionResult>(POLISH_API_PATHS.confirmCandidate(candidateId), {
    method: "POST",
  });
  const data = buildSuccessData(response);
  if (data === null) {
    throw new Error("候选确认返回为空");
  }
  return data;
}

export async function dismissPolishCandidate(candidateId: string): Promise<PolishCandidateActionResult> {
  const response = await request<PolishCandidateActionResult>(POLISH_API_PATHS.dismissCandidate(candidateId), {
    method: "POST",
  });
  const data = buildSuccessData(response);
  if (data === null) {
    throw new Error("候选忽略返回为空");
  }
  return data;
}

export async function createPolishFeedbackNextQuestionTask(
  sessionId: string,
  feedbackId: string,
  payload: CreatePolishFeedbackNextQuestionIntentRequest = {},
): Promise<PolishTaskStatus> {
  const response = await request<PolishTaskStatus>(POLISH_API_PATHS.feedbackNextQuestionTask(sessionId, feedbackId), {
    method: "POST",
    body: payload,
  });
  const data = buildSuccessData(response);
  if (data === null) {
    throw new Error("下一题生成任务返回为空");
  }
  return data;
}

export async function completePolishQuestion(sessionId: string, questionId: string): Promise<PolishSessionDetail> {
  const response = await request<PolishSessionDetail>(POLISH_API_PATHS.completeQuestion(sessionId, questionId), {
    method: "POST",
  });
  const data = buildSuccessData(response);
  if (data === null) {
    throw new Error("问题完成状态返回为空");
  }
  return data;
}

export async function endPolishSession(sessionId: string): Promise<PolishSessionDetail> {
  const response = await request<PolishSessionDetail>(POLISH_API_PATHS.endSession(sessionId), {
    method: "POST",
  });
  const data = buildSuccessData(response);
  if (data === null) {
    throw new Error("模拟面试结束状态返回为空");
  }
  return data;
}

export async function generatePolishSessionReport(sessionId: string): Promise<PolishSessionDetail> {
  const response = await request<PolishSessionDetail>(POLISH_API_PATHS.sessionReport(sessionId), {
    method: "POST",
  });
  const data = buildSuccessData(response);
  if (data === null) {
    throw new Error("面试报告生成状态返回为空");
  }
  return data;
}

export async function softDeletePolishSession(sessionId: string): Promise<PolishSessionDetail> {
  const response = await request<PolishSessionDetail>(POLISH_API_PATHS.softDeleteSession(sessionId), {
    method: "POST",
  });
  const data = buildSuccessData(response);
  if (data === null) {
    throw new Error("模拟面试删除状态返回为空");
  }
  return data;
}

function buildPolishCandidateQuery(filters: FetchPolishCandidateFilters): string {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(filters)) {
    if (value === null || value === undefined || value === "") {
      continue;
    }
    params.set(key, String(value));
  }
  const query = params.toString();
  return query ? `?${query}` : "";
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

export async function generateInitialPolishProgressTree(sessionId: string): Promise<PolishSessionDetail> {
  const response = await request<PolishSessionDetail>(POLISH_API_PATHS.progressTreeGenerate(sessionId), {
    method: "POST",
  });
  const data = buildSuccessData(response);
  if (data === null) {
    throw new Error("进展树生成返回为空");
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

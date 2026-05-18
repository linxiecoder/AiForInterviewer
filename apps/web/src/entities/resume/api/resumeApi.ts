import { isApiHttpError, type ApiHttpError } from "../../../shared/api/errors";
import { request, buildSuccessData } from "../../../shared/api/client";
import type { ResumeSummary } from "../model/types";

export type CreateResumeRequest = {
  title: string;
  markdown_text: string;
};

export type ResumeApiState =
  | {
      kind: "ready";
      resumes: ResumeSummary[];
    }
  | {
      kind: "error";
      message: string;
      resumes: [];
      status: number;
    };

export async function createResume(payload: CreateResumeRequest): Promise<ResumeSummary> {
  const response = await request<ResumeSummary>("/resumes", {
    method: "POST",
    body: payload,
  });
  const data = buildSuccessData(response);
  if (data === null) {
    throw new Error("简历创建返回为空");
  }
  return data;
}

export async function fetchResumeSummaries(): Promise<ResumeApiState> {
  try {
    const response = await request<ResumeSummary[] | ResumeSummary>("/resumes");
    const data = buildSuccessData(response);

    if (Array.isArray(data)) {
      return { kind: "ready", resumes: data };
    }

    if (data === null) {
      return { kind: "ready", resumes: [] };
    }

    const resumeItems = (data as { items?: unknown }).items;
    if (Array.isArray(resumeItems)) {
      return {
        kind: "ready",
        resumes: resumeItems as ResumeSummary[],
      };
    }

    return { kind: "ready", resumes: [] };
  } catch (error) {
    if (isApiHttpError(error)) {
      const apiError = error as ApiHttpError;
      return {
        kind: "error",
        status: apiError.status,
        message: apiError.safeMessage,
        resumes: [],
      };
    }

    if (error instanceof Error) {
      return {
        kind: "error",
        status: 0,
        message: error.message || "获取简历失败",
        resumes: [],
      };
    }

    return {
      kind: "error",
      status: 0,
      message: "获取简历失败",
      resumes: [],
    };
  }
}

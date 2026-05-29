import { isApiHttpError, type ApiHttpError } from "../../../shared/api/errors";
import { request, buildSuccessData } from "../../../shared/api/client";
import type { ResumeDetail, ResumeSummary } from "../model/types";
import type { VersionRef } from "../../job/model/types";

export type CreateResumeRequest = {
  title: string;
  markdown_text: string;
};

export type UpdateResumeRequest = {
  title: string;
  markdown_text: string;
  base_version_ref: VersionRef;
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

export const RESUME_API_PATHS = {
  list: "/resumes",
  detail: "/resumes/:resume_id",
  delete: "/resumes/:resume_id",
} as const;

function replaceResumeId(path: string, resumeId: string): string {
  return path.replace(":resume_id", encodeURIComponent(resumeId));
}

export async function createResume(payload: CreateResumeRequest): Promise<ResumeSummary> {
  const response = await request<ResumeSummary>(RESUME_API_PATHS.list, {
    method: "POST",
    body: payload,
  });
  const data = buildSuccessData(response);
  if (data === null) {
    throw new Error("简历创建返回为空");
  }
  return data;
}

export async function fetchResumeDetail(resumeId: string): Promise<ResumeDetail> {
  const response = await request<ResumeDetail>(replaceResumeId(RESUME_API_PATHS.detail, resumeId));
  const data = buildSuccessData(response);
  if (data === null) {
    throw new Error("简历详情返回为空");
  }
  return data;
}

export async function updateResume(resumeId: string, payload: UpdateResumeRequest): Promise<ResumeDetail> {
  const response = await request<ResumeDetail>(replaceResumeId(RESUME_API_PATHS.detail, resumeId), {
    method: "PATCH",
    body: payload,
  });
  const data = buildSuccessData(response);
  if (data === null) {
    throw new Error("简历更新返回为空");
  }
  return data;
}

export async function deleteResume(resumeId: string): Promise<ResumeDetail> {
  const response = await request<ResumeDetail>(replaceResumeId(RESUME_API_PATHS.delete, resumeId), {
    method: "DELETE",
  });
  const data = buildSuccessData(response);
  if (data === null) {
    throw new Error("简历删除返回为空");
  }
  return data;
}

export async function fetchResumeSummaries(): Promise<ResumeApiState> {
  try {
    const response = await request<ResumeSummary[] | ResumeSummary>(RESUME_API_PATHS.list);
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

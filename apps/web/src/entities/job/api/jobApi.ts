import { request, buildSuccessData } from "../../../shared/api/client";
import { isApiHttpError } from "../../../shared/api/errors";
import type {
  CreateBindingRequest,
  CreateJobMatchAnalysisRequest,
  DeleteBindingRequest,
  JobCreateRequest,
  JobDetail,
  JobMatchAnalysis,
  JobResumeBinding,
  JobSummary,
  JobUpdateRequest,
} from "../model/types";

export const JOB_MATCH_ANALYSIS_API_PATHS = {
  create: "/job-match-analyses",
  latest: "/job-match-analyses/latest",
  byId: "/job-match-analyses/:analysis_id",
} as const;

export const JOB_API_PATHS = {
  list: "/jobs",
  detail: "/jobs/:job_id",
  delete: "/jobs/:job_id",
} as const;

function replaceJobId(path: string, jobId: string): string {
  return path.replace(":job_id", encodeURIComponent(jobId));
}

export async function fetchJobs(): Promise<JobSummary[]> {
  const response = await request<JobSummary[]>(JOB_API_PATHS.list);
  const data = buildSuccessData(response);
  return data ?? [];
}

export async function fetchJob(jobId: string): Promise<JobDetail> {
  const response = await request<JobDetail>(replaceJobId(JOB_API_PATHS.detail, jobId));
  const data = buildSuccessData(response);
  if (data === null) {
    throw new Error("岗位详情返回为空");
  }
  return data;
}

export async function createJob(payload: JobCreateRequest): Promise<JobDetail> {
  const response = await request<JobDetail>(JOB_API_PATHS.list, {
    method: "POST",
    body: payload,
  });
  const data = buildSuccessData(response);
  if (data === null) {
    throw new Error("岗位创建返回为空");
  }
  return data;
}

export async function updateJob(jobId: string, payload: JobUpdateRequest): Promise<JobDetail> {
  const response = await request<JobDetail>(replaceJobId(JOB_API_PATHS.detail, jobId), {
    method: "PATCH",
    body: payload,
  });
  const data = buildSuccessData(response);
  if (data === null) {
    throw new Error("岗位更新返回为空");
  }
  return data;
}

export async function deleteJob(jobId: string): Promise<JobDetail> {
  const response = await request<JobDetail>(replaceJobId(JOB_API_PATHS.delete, jobId), {
    method: "DELETE",
  });
  const data = buildSuccessData(response);
  if (data === null) {
    throw new Error("岗位删除返回为空");
  }
  return data;
}

export async function createBinding(payload: CreateBindingRequest): Promise<JobResumeBinding> {
  const response = await request<JobResumeBinding>("/resume-job-bindings", {
    method: "POST",
    body: payload,
  });
  const data = buildSuccessData(response);
  if (data === null) {
    throw new Error("绑定返回为空");
  }
  return data;
}

export async function removeBinding(
  bindingId: string,
  payload: DeleteBindingRequest = {},
): Promise<JobResumeBinding> {
  const response = await request<JobResumeBinding>(`/resume-job-bindings/${bindingId}`, {
    method: "DELETE",
    body: payload,
  });
  const data = buildSuccessData(response);
  if (data === null) {
    throw new Error("解绑返回为空");
  }
  return data;
}

export async function createJobMatchAnalysis(
  payload: CreateJobMatchAnalysisRequest,
): Promise<JobMatchAnalysis> {
  const response = await request<JobMatchAnalysis>(JOB_MATCH_ANALYSIS_API_PATHS.create, {
    method: "POST",
    body: payload,
  });
  const data = buildSuccessData(response);
  if (data === null) {
    throw new Error("岗位匹配分析返回为空");
  }
  return data;
}

export async function fetchLatestJobMatchAnalysis(
  resumeJobBindingId: string,
): Promise<JobMatchAnalysis | null> {
  try {
    const response = await request<JobMatchAnalysis>(
      `${JOB_MATCH_ANALYSIS_API_PATHS.latest}?resume_job_binding_id=${encodeURIComponent(resumeJobBindingId)}`,
    );
    return buildSuccessData(response);
  } catch (error) {
    if (isApiHttpError(error) && error.status === 404) {
      return null;
    }
    throw error;
  }
}

export async function fetchJobMatchAnalysis(analysisId: string): Promise<JobMatchAnalysis> {
  const response = await request<JobMatchAnalysis>(
    JOB_MATCH_ANALYSIS_API_PATHS.byId.replace(":analysis_id", encodeURIComponent(analysisId)),
  );
  const data = buildSuccessData(response);
  if (data === null) {
    throw new Error("岗位匹配分析返回为空");
  }
  return data;
}

import { request, buildSuccessData } from "../../../shared/api/client";
import type {
  CreateBindingRequest,
  DeleteBindingRequest,
  JobCreateRequest,
  JobDetail,
  JobResumeBinding,
  JobSummary,
  JobUpdateRequest,
} from "../model/types";

export async function fetchJobs(): Promise<JobSummary[]> {
  const response = await request<JobSummary[]>("/jobs");
  const data = buildSuccessData(response);
  return data ?? [];
}

export async function fetchJob(jobId: string): Promise<JobDetail> {
  const response = await request<JobDetail>(`/jobs/${jobId}`);
  const data = buildSuccessData(response);
  if (data === null) {
    throw new Error("岗位详情返回为空");
  }
  return data;
}

export async function createJob(payload: JobCreateRequest): Promise<JobDetail> {
  const response = await request<JobDetail>("/jobs", {
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
  const response = await request<JobDetail>(`/jobs/${jobId}`, {
    method: "PATCH",
    body: payload,
  });
  const data = buildSuccessData(response);
  if (data === null) {
    throw new Error("岗位更新返回为空");
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

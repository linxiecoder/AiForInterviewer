import { request, buildSuccessData } from "../../../shared/api/client";
import type { WeaknessDetail, WeaknessSummary } from "../model/types";

export const WEAKNESS_API_PATHS = {
  list: "/weaknesses",
  detail: "/weaknesses/:weakness_id",
  updateStatus: "/weaknesses/:weakness_id/status",
  delete: "/weaknesses/:weakness_id",
} as const;

export type FetchWeaknessesParams = {
  status?: string;
  severity?: string;
  q?: string;
};

function replaceWeaknessId(path: string, weaknessId: string): string {
  return path.replace(":weakness_id", encodeURIComponent(weaknessId));
}

function toQuery(params: FetchWeaknessesParams): string {
  const query = new URLSearchParams();
  if (params.status) {
    query.set("status", params.status);
  }
  if (params.severity) {
    query.set("severity", params.severity);
  }
  if (params.q?.trim()) {
    query.set("q", params.q.trim());
  }
  const serialized = query.toString();
  return serialized ? `?${serialized}` : "";
}

export async function fetchWeaknesses(params: FetchWeaknessesParams = {}): Promise<WeaknessSummary[]> {
  const response = await request<WeaknessSummary[]>(`${WEAKNESS_API_PATHS.list}${toQuery(params)}`);
  return buildSuccessData(response) ?? [];
}

export async function fetchWeakness(weaknessId: string): Promise<WeaknessDetail> {
  const response = await request<WeaknessDetail>(replaceWeaknessId(WEAKNESS_API_PATHS.detail, weaknessId));
  const data = buildSuccessData(response);
  if (data === null) {
    throw new Error("薄弱项详情返回为空");
  }
  return data;
}

export async function updateWeaknessStatus(
  weaknessId: string,
  status: string,
): Promise<WeaknessDetail> {
  const response = await request<WeaknessDetail>(replaceWeaknessId(WEAKNESS_API_PATHS.updateStatus, weaknessId), {
    method: "POST",
    body: { status },
  });
  const data = buildSuccessData(response);
  if (data === null) {
    throw new Error("薄弱项状态更新返回为空");
  }
  return data;
}

export async function deleteWeakness(weaknessId: string): Promise<WeaknessDetail> {
  const response = await request<WeaknessDetail>(replaceWeaknessId(WEAKNESS_API_PATHS.delete, weaknessId), {
    method: "DELETE",
  });
  const data = buildSuccessData(response);
  if (data === null) {
    throw new Error("薄弱项删除返回为空");
  }
  return data;
}

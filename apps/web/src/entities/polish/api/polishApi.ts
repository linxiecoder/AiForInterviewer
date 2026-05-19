import { request, buildSuccessData } from "../../../shared/api/client";
import type { PolishSessionSummary } from "../model/types";

export async function fetchPolishSessions(): Promise<PolishSessionSummary[]> {
  const response = await request<PolishSessionSummary[]>("/polish-sessions");
  const data = buildSuccessData(response);
  return data ?? [];
}

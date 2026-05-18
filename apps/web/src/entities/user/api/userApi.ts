import type { User } from "../model/types";
import { request, buildSuccessData } from "../../../shared/api/client";

export async function fetchCurrentUser(): Promise<User> {
  const response = await request<User>("/auth/me");
  const data = buildSuccessData(response);
  if (data === null) {
    throw new Error("当前用户返回为空");
  }
  return data;
}

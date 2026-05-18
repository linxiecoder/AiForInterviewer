import type { LogoutResponse } from "./model";
import { request } from "../../shared/api/client";

export async function logout(): Promise<LogoutResponse> {
  const response = await request<LogoutResponse>("/auth/logout", {
    method: "POST",
  });
  if (response.data === null) {
    return { logged_out: true };
  }
  return response.data;
}

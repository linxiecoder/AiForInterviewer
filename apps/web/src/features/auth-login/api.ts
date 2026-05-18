import type { LoginRequest } from "./model";
import type { User } from "../../entities/user/model/types";
import { request, buildSuccessData } from "../../shared/api/client";

export async function login(payload: LoginRequest): Promise<User> {
  const response = await request<User>("/auth/login", {
    method: "POST",
    body: payload,
  });
  const data = buildSuccessData(response);
  if (data === null) {
    throw new Error("登录返回未包含用户数据。");
  }
  return data;
}

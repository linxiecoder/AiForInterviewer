import type { ApiErrorPayload, ApiSuccessEnvelope } from "./envelope";
import {
  ApiHttpError,
  DEFAULT_INTERNAL_ERROR_CODE,
  DEFAULT_UNAUTHENTICATED_ERROR_CODE,
} from "./errors";
import { API_BASE_URL } from "../config/env";

type HttpMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";

export interface ApiRequestOptions extends Omit<RequestInit, "body" | "method"> {
  method?: HttpMethod | (string & {});
  body?: unknown;
}

function buildApiUrl(path: string): string {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  if (/^https?:\/\//i.test(API_BASE_URL)) {
    return `${API_BASE_URL}${normalizedPath}`;
  }
  return `${API_BASE_URL}${normalizedPath}`;
}

function ensureString(value: unknown): string | null {
  return typeof value === "string" ? value : null;
}

function toApiError(payload: unknown, response: Response): ApiHttpError {
  if (typeof payload === "object" && payload !== null) {
    const errorPayload = (payload as { error?: unknown }).error;
    if (typeof errorPayload === "object" && errorPayload !== null) {
      const error = errorPayload as Partial<ApiErrorPayload>;
      const code = ensureString(error.code) ?? (response.status === 401 ? DEFAULT_UNAUTHENTICATED_ERROR_CODE : DEFAULT_INTERNAL_ERROR_CODE);
      const message = ensureString(error.message) ?? `请求失败（${response.status}）`;
      const retryable = typeof error.retryable === "boolean" ? error.retryable : false;
      const userAction = typeof error.user_action === "string" ? error.user_action : undefined;
      const details = typeof error.details === "object" && error.details !== null ? (error.details as Record<string, unknown>) : undefined;
      return new ApiHttpError({
        status: response.status,
        code,
        message,
        retryable,
        userAction,
        details,
      });
    }
  }

  return new ApiHttpError({
    status: response.status,
    code: response.status === 401 ? DEFAULT_UNAUTHENTICATED_ERROR_CODE : DEFAULT_INTERNAL_ERROR_CODE,
    message: `请求失败（${response.status}）`,
  });
}

async function parseJsonBody(response: Response): Promise<unknown | null> {
  const raw = await response.text();
  if (!raw.trim()) {
    return null;
  }
  try {
    return JSON.parse(raw);
  } catch {
    throw new ApiHttpError({
      status: response.status,
      code: DEFAULT_INTERNAL_ERROR_CODE,
      message: "响应 JSON 无法解析。",
    });
  }
}

export async function request<TData = unknown>(
  path: string,
  options: ApiRequestOptions = {},
): Promise<ApiSuccessEnvelope<TData>> {
  const { body: rawBody, headers: rawHeaders, ...restOptions } = options;
  const headers = {
    "Content-Type": "application/json",
    ...(rawHeaders ?? {}),
  };
  const body = rawBody === undefined ? undefined : JSON.stringify(rawBody);
  const mergedOptions: RequestInit = {
    method: options.method ?? "GET",
    credentials: "include",
    headers,
    body,
  };

  const response = await fetch(buildApiUrl(path), {
    ...restOptions,
    ...mergedOptions,
  });

  const payload = await parseJsonBody(response);

  if (!response.ok) {
    const error = toApiError(payload, response);
    throw error;
  }

  if (typeof payload !== "object" || payload === null) {
    throw new ApiHttpError({
      status: response.status,
      code: DEFAULT_INTERNAL_ERROR_CODE,
      message: "后端返回格式不符合 API 预期。",
    });
  }

  const envelope = payload as ApiSuccessEnvelope<TData>;
  if (typeof envelope.request_id !== "string" || typeof envelope.trace_id !== "string") {
    throw new ApiHttpError({
      status: response.status,
      code: DEFAULT_INTERNAL_ERROR_CODE,
      message: "成功响应缺少 request_id/trace_id 字段。",
    });
  }

  return envelope;
}

export function buildSuccessData<TData>(response: ApiSuccessEnvelope<TData>): TData | null {
  return response.data ?? null;
}

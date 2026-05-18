import type { ApiErrorEnvelope } from "./envelope";

export const DEFAULT_UNAUTHENTICATED_ERROR_CODE = "unauthenticated";
export const DEFAULT_INTERNAL_ERROR_CODE = "internal_error";

export interface ApiHttpErrorOptions {
  status: number;
  code: string;
  message: string;
  retryable?: boolean;
  userAction?: string | null;
  details?: Record<string, unknown> | null;
  requestId?: string;
  traceId?: string;
}

export class ApiHttpError extends Error {
  public readonly status: number;
  public readonly code: string;
  public readonly retryable: boolean;
  public readonly userAction?: string | null;
  public readonly details?: Record<string, unknown> | null;
  public readonly requestId: string;
  public readonly traceId: string;

  constructor(options: ApiHttpErrorOptions) {
    super(options.message);
    this.name = "ApiHttpError";
    this.status = options.status;
    this.code = options.code;
    this.retryable = options.retryable ?? false;
    this.userAction = options.userAction;
    this.details = options.details;
    this.requestId = options.requestId ?? "";
    this.traceId = options.traceId ?? "";
  }

  get safeMessage(): string {
    return this.message || "请求处理失败，请稍后重试。";
  }

  static fromEnvelope(payload: ApiErrorEnvelope, status: number): ApiHttpError {
    const errorPayload = payload?.error;
    return new ApiHttpError({
      status,
      code: errorPayload.code,
      message: errorPayload.message,
      retryable: errorPayload.retryable,
      userAction: errorPayload.user_action,
      details: errorPayload.details,
      requestId: payload.request_id,
      traceId: payload.trace_id,
    });
  }
}

export function isApiHttpError(error: unknown): error is ApiHttpError {
  return error instanceof ApiHttpError;
}

export function isUnauthenticatedError(error: unknown): boolean {
  return isApiHttpError(error) && error.code === "unauthenticated";
}

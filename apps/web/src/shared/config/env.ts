type ViteEnvWithApiBase = {
  readonly VITE_API_BASE_URL?: string;
};

type ViteEnvModeHints = {
  readonly DEV?: boolean;
};

type ApiImportMeta = Omit<ImportMeta, "env"> & {
  readonly env?: ViteEnvWithApiBase & ViteEnvModeHints;
};

const apiMeta = import.meta as ApiImportMeta;

const DEFAULT_API_BASE_URL = "/api/v1";
const DEV_FALLBACK_API_BASE_URL = "http://127.0.0.1:8000/api/v1";

function normalizeApiBaseUrl(raw: string | undefined): string {
  const trimmed = raw?.trim();

  if (!trimmed) {
    if (isLocalViteDevServer()) {
      return DEV_FALLBACK_API_BASE_URL;
    }

    return DEFAULT_API_BASE_URL;
  }

  return trimmed.endsWith("/") ? trimmed.slice(0, -1) : trimmed;
}

function isLocalViteDevServer(): boolean {
  if (typeof window === "undefined") {
    return false;
  }

  const isLoopback =
    window.location.hostname === "127.0.0.1" ||
    window.location.hostname === "localhost";
  return (
    isLoopback &&
    (window.location.port === "5173" || window.location.port === "5174")
  );
}

export const API_BASE_URL = normalizeApiBaseUrl(apiMeta.env?.VITE_API_BASE_URL);

if (apiMeta.env?.DEV) {
  console.info("[AIFI] API_BASE_URL", API_BASE_URL);
}

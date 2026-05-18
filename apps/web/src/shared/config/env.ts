type ViteEnvWithApiBase = {
  readonly VITE_API_BASE_URL?: string;
};

type ViteEnvModeHints = {
  readonly DEV?: boolean;
};

type ViteImportMeta = ImportMeta & {
  readonly env: ViteEnvWithApiBase & ViteEnvModeHints;
};

const DEFAULT_API_BASE_URL = "/api/v1";
const DEV_FALLBACK_API_BASE_URL = "http://127.0.0.1:8001/api/v1";

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

const viteEnv = (import.meta as ViteImportMeta).env;

export const API_BASE_URL = normalizeApiBaseUrl(viteEnv.VITE_API_BASE_URL);

if (viteEnv.DEV) {
  console.info("[AIFI] API_BASE_URL", API_BASE_URL);
}

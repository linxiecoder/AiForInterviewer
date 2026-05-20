type ViteEnvWithApiBase = {
  readonly VITE_API_BASE_URL?: string;
};

type ViteEnvModeHints = {
  readonly DEV?: boolean;
};

type ViteImportMeta = ImportMeta & {
  readonly env: ViteEnvWithApiBase & ViteEnvModeHints;
};

type BrowserLocationLike = {
  readonly hostname: string;
  readonly port: string;
};

type LoopbackHostname = "127.0.0.1" | "localhost";
type LocalVitePort = "5173" | "5174";
type LocalLoopbackApiBase<
  TApiBaseUrl extends string,
  THostname extends string,
  TPort extends string,
> = TPort extends LocalVitePort
  ? THostname extends LoopbackHostname
    ? TApiBaseUrl extends `http://${LoopbackHostname}:${infer TApiPort}/${infer TPath}`
      ? typeof DEFAULT_API_BASE_URL
      : TApiBaseUrl
    : TApiBaseUrl
  : TApiBaseUrl;

const DEFAULT_API_BASE_URL = "/api/v1";

export function alignLocalLoopbackApiBaseUrl<
  const TApiBaseUrl extends string,
  const THostname extends string,
  const TPort extends string,
>(
  apiBaseUrl: TApiBaseUrl,
  location: BrowserLocationLike & { readonly hostname: THostname; readonly port: TPort },
): LocalLoopbackApiBase<TApiBaseUrl, THostname, TPort> {
  if (!isLocalViteDevServer(location)) {
    return apiBaseUrl as LocalLoopbackApiBase<TApiBaseUrl, THostname, TPort>;
  }

  let parsed: URL;
  try {
    parsed = new URL(apiBaseUrl);
  } catch {
    return apiBaseUrl as LocalLoopbackApiBase<TApiBaseUrl, THostname, TPort>;
  }

  if (parsed.protocol !== "http:" || !isLoopbackHostname(parsed.hostname)) {
    return apiBaseUrl as LocalLoopbackApiBase<TApiBaseUrl, THostname, TPort>;
  }

  return DEFAULT_API_BASE_URL as LocalLoopbackApiBase<TApiBaseUrl, THostname, TPort>;
}

function normalizeApiBaseUrl(raw: string | undefined): string {
  const trimmed = raw?.trim();

  if (!trimmed) {
    return DEFAULT_API_BASE_URL;
  }

  const normalized = trimmed.endsWith("/") ? trimmed.slice(0, -1) : trimmed;
  if (typeof window === "undefined") {
    return normalized;
  }
  return alignLocalLoopbackApiBaseUrl(normalized, window.location);
}

function isLoopbackHostname(hostname: string): hostname is LoopbackHostname {
  return hostname === "127.0.0.1" || hostname === "localhost";
}

function getBrowserLocation(): BrowserLocationLike | undefined {
  return typeof window === "undefined" ? undefined : window.location;
}

function isLocalViteDevServer(
  location: BrowserLocationLike | undefined = getBrowserLocation(),
): boolean {
  if (location === undefined) {
    return false;
  }

  const isLoopback = isLoopbackHostname(location.hostname);
  return (
    isLoopback &&
    (location.port === "5173" || location.port === "5174")
  );
}

const viteEnv = (import.meta as ViteImportMeta).env;

export const API_BASE_URL = normalizeApiBaseUrl(viteEnv.VITE_API_BASE_URL);

if (viteEnv.DEV) {
  console.info("[AIFI] API_BASE_URL", API_BASE_URL);
}

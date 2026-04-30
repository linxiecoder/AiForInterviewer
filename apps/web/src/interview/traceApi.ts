import type { TrustedInterviewDetail } from "./traceTypes.js";

export async function fetchTrustedInterviewDetail({
  sessionId,
  ownerId,
  signal,
}: {
  sessionId: string;
  ownerId: string;
  signal?: AbortSignal;
}): Promise<TrustedInterviewDetail> {
  const params = new URLSearchParams({ owner_id: ownerId });
  const response = await fetch(`/api/v1/interviews/${encodeURIComponent(sessionId)}?${params}`, {
    headers: { accept: "application/json" },
    signal,
  });

  if (!response.ok) {
    throw new Error(`trace detail request failed: ${response.status}`);
  }

  return (await response.json()) as TrustedInterviewDetail;
}

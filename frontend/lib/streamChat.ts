const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export interface ToolStep {
  id: string;
  type: "kb" | "data" | "web" | "chart";
  label: string;
}

export interface ChartStep {
  chart_id: string;
  title: string;
  chart_type: string;
}

export interface StreamChatOptions {
  threadId: string;
  message: string;
  token: string;
  forceTools?: string[];
  onToken: (token: string) => void;
  onToolStart?: (step: ToolStep) => void;
  onToolEnd?: (id: string) => void;
  onChart?: (chart: ChartStep) => void;
  onRateLimit?: (info: RateLimitInfo) => void;
  signal?: AbortSignal;
}

/** Thrown when the backend rejects the token (missing/expired/invalid) —
 * callers should treat this as "log in again", not a generic chat failure. */
export class UnauthorizedError extends Error {}

/** Chat rate limit status (ADR-0027), parsed from X-RateLimit-* response headers. */
export interface RateLimitInfo {
  limit: number;
  remaining: number;
  resetSeconds: number;
}

/** Thrown when the backend's per-user chat rate limit (ADR-0027) is
 * exceeded — callers should show the blocked-chat UX, not a generic chat
 * failure. */
export class RateLimitedError extends Error {
  rateLimit: RateLimitInfo;
  constructor(message: string, rateLimit: RateLimitInfo) {
    super(message);
    this.rateLimit = rateLimit;
  }
}

function parseRateLimitHeaders(response: Response): RateLimitInfo | null {
  const limit = response.headers.get("X-RateLimit-Limit");
  const remaining = response.headers.get("X-RateLimit-Remaining");
  const reset = response.headers.get("X-RateLimit-Reset");
  if (limit === null || remaining === null || reset === null) return null;
  return { limit: Number(limit), remaining: Number(remaining), resetSeconds: Number(reset) };
}

/** POST + manual SSE parsing (ADR-0017) — native EventSource doesn't support POST bodies. */
export async function streamChat({
  threadId,
  message,
  token,
  forceTools,
  onToken,
  onToolStart,
  onToolEnd,
  onChart,
  onRateLimit,
  signal,
}: StreamChatOptions): Promise<void> {
  const response = await fetch(`${BACKEND_URL}/api/v1/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ thread_id: threadId, message, force_tools: forceTools ?? [] }),
    signal,
  });

  if (response.status === 401) {
    throw new UnauthorizedError("Session expired or invalid.");
  }
  if (response.status === 429) {
    const rateLimit = parseRateLimitHeaders(response) ?? { limit: 30, remaining: 0, resetSeconds: 0 };
    const body = await response.json().catch(() => null);
    const detailMessage = typeof body?.detail === "string" ? body.detail : "You've reached the chat rate limit.";
    throw new RateLimitedError(detailMessage, rateLimit);
  }
  if (!response.ok || !response.body) {
    throw new Error(`Chat request failed: ${response.status}`);
  }

  const rateLimit = parseRateLimitHeaders(response);
  if (rateLimit) onRateLimit?.(rateLimit);

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const frames = buffer.split("\n\n");
    buffer = frames.pop() ?? "";

    for (const frame of frames) {
      const lines = frame.split("\n");
      const dataLine = lines.find((line) => line.startsWith("data:"));
      if (!dataLine) continue;
      const eventLine = lines.find((line) => line.startsWith("event:"));
      const eventType = eventLine ? eventLine.slice("event:".length).trim() : "message";
      const payload = JSON.parse(dataLine.slice("data:".length).trim());

      if (eventType === "message" && payload.token) {
        onToken(payload.token);
      } else if (eventType === "tool_start") {
        onToolStart?.(payload as ToolStep);
      } else if (eventType === "tool_end") {
        onToolEnd?.(payload.id);
      } else if (eventType === "chart") {
        onChart?.(payload as ChartStep);
      }
    }
  }
}

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export interface ToolStep {
  id: string;
  type: "kb" | "data" | "web";
  label: string;
}

export interface StreamChatOptions {
  threadId: string;
  message: string;
  token: string;
  onToken: (token: string) => void;
  onToolStart?: (step: ToolStep) => void;
  onToolEnd?: (id: string) => void;
  signal?: AbortSignal;
}

/** Thrown when the backend rejects the token (missing/expired/invalid) —
 * callers should treat this as "log in again", not a generic chat failure. */
export class UnauthorizedError extends Error {}

/** POST + manual SSE parsing (ADR-0017) — native EventSource doesn't support POST bodies. */
export async function streamChat({
  threadId,
  message,
  token,
  onToken,
  onToolStart,
  onToolEnd,
  signal,
}: StreamChatOptions): Promise<void> {
  const response = await fetch(`${BACKEND_URL}/api/v1/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ thread_id: threadId, message }),
    signal,
  });

  if (response.status === 401) {
    throw new UnauthorizedError("Session expired or invalid.");
  }
  if (!response.ok || !response.body) {
    throw new Error(`Chat request failed: ${response.status}`);
  }

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
      }
    }
  }
}

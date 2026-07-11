const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

export interface StreamChatOptions {
  threadId: string;
  message: string;
  businessUnit: string;
  onToken: (token: string) => void;
  signal?: AbortSignal;
}

/** POST + manual SSE parsing (ADR-0017) — native EventSource doesn't support POST bodies. */
export async function streamChat({ threadId, message, businessUnit, onToken, signal }: StreamChatOptions): Promise<void> {
  const response = await fetch(`${BACKEND_URL}/api/v1/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Nova-Business-Units": businessUnit,
    },
    body: JSON.stringify({ thread_id: threadId, message }),
    signal,
  });

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
      const dataLine = frame.split("\n").find((line) => line.startsWith("data:"));
      if (!dataLine) continue;
      const payload = JSON.parse(dataLine.slice("data:".length).trim());
      if (payload.token) onToken(payload.token);
    }
  }
}

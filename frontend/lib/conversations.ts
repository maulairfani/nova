const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export interface Conversation {
  id: string;
  title: string;
  updated_at: string;
}

async function request<T>(path: string, token: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BACKEND_URL}/api/v1${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}`, ...init?.headers },
  });
  if (!response.ok) throw new Error(`Request to ${path} failed: ${response.status}`);
  if (response.status === 204) return undefined as T;
  return response.json();
}

export function listConversations(token: string): Promise<Conversation[]> {
  return request<Conversation[]>("/conversations", token);
}

export function renameConversation(token: string, id: string, title: string): Promise<Conversation> {
  return request<Conversation>(`/conversations/${id}`, token, {
    method: "PATCH",
    body: JSON.stringify({ title }),
  });
}

export function deleteConversation(token: string, id: string): Promise<void> {
  return request<void>(`/conversations/${id}`, token, { method: "DELETE" });
}

export interface StoredMessage {
  role: "user" | "assistant";
  content: string;
  steps?: { type: "kb" | "data" | "web" | "chart"; label: string }[];
  charts?: { chart_id: string; title: string; chart_type: string }[];
  citations?: {
    type: "kb" | "web";
    title: string;
    snippet: string;
    unit?: string;
    source_document?: string;
    url?: string;
  }[];
}

export function getConversationMessages(token: string, id: string): Promise<StoredMessage[]> {
  return request<StoredMessage[]>(`/conversations/${id}/messages`, token);
}

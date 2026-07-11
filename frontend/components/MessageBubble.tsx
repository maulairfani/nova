import { renderInlineMarkdown } from "../lib/renderInlineMarkdown";

export interface Message {
  role: "user" | "assistant";
  content: string;
}

export function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";
  return (
    <div style={{ display: "flex", justifyContent: isUser ? "flex-end" : "flex-start", marginBottom: 12 }}>
      <div
        style={{
          maxWidth: "72%",
          padding: "10px 14px",
          borderRadius: 14,
          borderBottomRightRadius: isUser ? 4 : 14,
          borderBottomLeftRadius: isUser ? 14 : 4,
          background: isUser ? "var(--nova-user-bubble)" : "var(--nova-assistant-bubble)",
          color: isUser ? "var(--nova-user-ink)" : "var(--nova-ink)",
          border: isUser ? "none" : "1px solid var(--nova-border)",
          whiteSpace: "pre-wrap",
          lineHeight: 1.5,
          fontSize: 14.5,
        }}
      >
        {message.content ? renderInlineMarkdown(message.content) : isUser ? "" : "…"}
      </div>
    </div>
  );
}

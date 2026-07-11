"use client";

import { useRef, useState } from "react";
import { streamChat } from "../lib/streamChat";
import { ChatInput } from "./ChatInput";
import { Message, MessageBubble } from "./MessageBubble";

/** Phase-1 simplification: no real auth yet — identity is a fixed dummy
 * value forwarded as a header. See backend/CLAUDE.md and mcp_servers/tv/CLAUDE.md. */
const BUSINESS_UNIT = "tv";

function newThreadId(): string {
  return crypto.randomUUID();
}

export function ChatWindow() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [busy, setBusy] = useState(false);
  const threadIdRef = useRef<string>(newThreadId());

  const handleSend = async (text: string) => {
    setMessages((prev) => [...prev, { role: "user", content: text }, { role: "assistant", content: "" }]);
    setBusy(true);

    try {
      await streamChat({
        threadId: threadIdRef.current,
        message: text,
        businessUnit: BUSINESS_UNIT,
        onToken: (token) => {
          setMessages((prev) => {
            const next = [...prev];
            next[next.length - 1] = { role: "assistant", content: next[next.length - 1].content + token };
            return next;
          });
        },
      });
    } catch (err) {
      setMessages((prev) => {
        const next = [...prev];
        next[next.length - 1] = { role: "assistant", content: "Sorry, something went wrong reaching Nova." };
        return next;
      });
    } finally {
      setBusy(false);
    }
  };

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100vh",
        maxWidth: 760,
        margin: "0 auto",
      }}
    >
      <header
        style={{
          padding: "16px 20px",
          borderBottom: "1px solid var(--nova-border)",
          display: "flex",
          alignItems: "baseline",
          justifyContent: "space-between",
        }}
      >
        <div>
          <div style={{ fontSize: 17, fontWeight: 700, letterSpacing: -0.2 }}>Nova</div>
          <div style={{ fontSize: 12.5, color: "var(--nova-ink-muted)" }}>MCN Group internal assistant</div>
        </div>
        <div
          style={{
            fontSize: 11.5,
            color: "var(--nova-ink-muted)",
            border: "1px solid var(--nova-border)",
            borderRadius: 999,
            padding: "4px 10px",
          }}
        >
          MCN TV employee
        </div>
      </header>

      <div style={{ flex: 1, overflowY: "auto", padding: "20px 20px 0" }}>
        {messages.length === 0 && (
          <div style={{ color: "var(--nova-ink-muted)", fontSize: 14, marginTop: 40, textAlign: "center" }}>
            Ask about MCN TV's SOPs (ad booking, content compliance, incident escalation) or its viewership/ad
            revenue data.
          </div>
        )}
        {messages.map((message, i) => (
          <MessageBubble key={i} message={message} />
        ))}
      </div>

      <ChatInput onSend={handleSend} disabled={busy} />
    </div>
  );
}

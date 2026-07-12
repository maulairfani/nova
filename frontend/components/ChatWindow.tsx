"use client";

import { useRef, useState } from "react";
import { streamChat } from "../lib/streamChat";
import { ChatInput } from "./ChatInput";
import { Message, MessageBubble } from "./MessageBubble";

/** Phase-1 simplification: no real auth yet — identity is a single selected
 * business unit forwarded as a header, not a verified login. See
 * backend/CLAUDE.md and mcp_servers/<unit>/CLAUDE.md. */
interface BusinessUnitConfig {
  id: string;
  label: string;
  badge: string;
  placeholder: string;
}

const BUSINESS_UNITS: BusinessUnitConfig[] = [
  {
    id: "tv",
    label: "MCN TV",
    badge: "MCN TV employee",
    placeholder: "Ask about MCN TV's SOPs (ad booking, content compliance, incident escalation) or its viewership/ad revenue data.",
  },
  {
    id: "plus",
    label: "MCN+",
    badge: "MCN+ employee",
    placeholder: "Ask about MCN+'s SOPs (content licensing, subscription billing, Shorts coin purchases) or its titles/engagement/revenue data.",
  },
  {
    id: "news",
    label: "MCN News",
    badge: "MCN News employee",
    placeholder: "Ask about MCN News's SOPs (fact-checking, breaking news, corrections) or its article engagement/ad revenue data.",
  },
];

function newThreadId(): string {
  return crypto.randomUUID();
}

export function ChatWindow() {
  const [businessUnit, setBusinessUnit] = useState<string>(BUSINESS_UNITS[0].id);
  const [messages, setMessages] = useState<Message[]>([]);
  const [busy, setBusy] = useState(false);
  const threadIdRef = useRef<string>(newThreadId());
  const activeUnit = BUSINESS_UNITS.find((u) => u.id === businessUnit) ?? BUSINESS_UNITS[0];

  const handleUnitChange = (unitId: string) => {
    // Switching business units starts a fresh conversation — a unit switch
    // is effectively a new context, not a continuation of the old thread.
    setBusinessUnit(unitId);
    setMessages([]);
    threadIdRef.current = newThreadId();
  };

  const handleSend = async (text: string) => {
    setMessages((prev) => [...prev, { role: "user", content: text }, { role: "assistant", content: "" }]);
    setBusy(true);

    try {
      await streamChat({
        threadId: threadIdRef.current,
        message: text,
        businessUnit,
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
        <select
          value={businessUnit}
          onChange={(e) => handleUnitChange(e.target.value)}
          disabled={busy}
          style={{
            fontSize: 11.5,
            color: "var(--nova-ink-muted)",
            border: "1px solid var(--nova-border)",
            borderRadius: 999,
            padding: "4px 10px",
            background: "var(--nova-surface)",
            cursor: busy ? "not-allowed" : "pointer",
          }}
        >
          {BUSINESS_UNITS.map((unit) => (
            <option key={unit.id} value={unit.id}>
              {unit.badge}
            </option>
          ))}
        </select>
      </header>

      <div style={{ flex: 1, overflowY: "auto", padding: "20px 20px 0" }}>
        {messages.length === 0 && (
          <div style={{ color: "var(--nova-ink-muted)", fontSize: 14, marginTop: 40, textAlign: "center" }}>
            {activeUnit.placeholder}
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

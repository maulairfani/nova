"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { getClaims, getToken, logout, TokenClaims } from "../lib/auth";
import { streamChat, UnauthorizedError } from "../lib/streamChat";
import { ChatInput } from "./ChatInput";
import { Message, MessageBubble } from "./MessageBubble";

function newThreadId(): string {
  return crypto.randomUUID();
}

const BUSINESS_UNIT_LABELS: Record<string, string> = {
  tv: "MCN TV",
  plus: "MCN+",
  news: "MCN News",
  group: "MCN Group",
};

export function ChatWindow() {
  const router = useRouter();
  const [claims, setClaims] = useState<TokenClaims | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [busy, setBusy] = useState(false);
  const threadIdRef = useRef<string>(newThreadId());

  // Which business units this identity can access is entirely a function of
  // the JWT's claims (ADR-0021) — there is no manual "pick a unit" control
  // anymore; the agent scopes itself to whatever the token actually grants.
  useEffect(() => {
    const c = getClaims();
    if (!c) {
      router.replace("/login");
      return;
    }
    setClaims(c);
  }, [router]);

  const handleLogout = () => {
    logout();
    router.replace("/login");
  };

  const handleSend = async (text: string) => {
    const token = getToken();
    if (!token) {
      router.replace("/login");
      return;
    }

    setMessages((prev) => [...prev, { role: "user", content: text }, { role: "assistant", content: "" }]);
    setBusy(true);

    try {
      await streamChat({
        threadId: threadIdRef.current,
        message: text,
        token,
        onToken: (token) => {
          setMessages((prev) => {
            const next = [...prev];
            next[next.length - 1] = { role: "assistant", content: next[next.length - 1].content + token };
            return next;
          });
        },
      });
    } catch (err) {
      if (err instanceof UnauthorizedError) {
        logout();
        router.replace("/login");
        return;
      }
      setMessages((prev) => {
        const next = [...prev];
        next[next.length - 1] = { role: "assistant", content: "Sorry, something went wrong reaching Nova." };
        return next;
      });
    } finally {
      setBusy(false);
    }
  };

  if (!claims) return null;

  const unitLabels = claims.business_units.map((u) => BUSINESS_UNIT_LABELS[u.code] ?? u.code);

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
          <div style={{ fontSize: 12.5, color: "var(--nova-ink-muted)" }}>
            {claims.display_name} · {unitLabels.length > 0 ? unitLabels.join(", ") : "No business unit access"}
          </div>
        </div>
        <button
          onClick={handleLogout}
          style={{
            fontSize: 11.5,
            color: "var(--nova-ink-muted)",
            border: "1px solid var(--nova-border)",
            borderRadius: 999,
            padding: "4px 10px",
            background: "var(--nova-surface)",
            cursor: "pointer",
          }}
        >
          Log out
        </button>
      </header>

      <div style={{ flex: 1, overflowY: "auto", padding: "20px 20px 0" }}>
        {messages.length === 0 && (
          <div style={{ color: "var(--nova-ink-muted)", fontSize: 14, marginTop: 40, textAlign: "center" }}>
            Ask Nova about MCN Group's SOPs, your business unit's data, or anything else.
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

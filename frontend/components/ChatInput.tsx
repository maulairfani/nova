import { useState, KeyboardEvent } from "react";

export function ChatInput({ onSend, disabled }: { onSend: (text: string) => void; disabled: boolean }) {
  const [value, setValue] = useState("");

  const submit = () => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue("");
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  const sendDisabled = disabled || !value.trim();

  return (
    <div style={{ flex: "none", borderTop: "1px solid var(--nova-border)", background: "var(--nova-bg)" }}>
      <div style={{ maxWidth: 760, margin: "0 auto", padding: "14px 24px 20px" }}>
        <div
          style={{
            display: "flex",
            alignItems: "flex-end",
            gap: 10,
            padding: "10px 12px",
            borderRadius: 16,
            border: "1px solid var(--nova-border)",
            background: "var(--nova-surface)",
          }}
        >
          <textarea
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Message Nova…"
            disabled={disabled}
            rows={1}
            style={{
              flex: 1,
              resize: "none",
              border: "none",
              outline: "none",
              background: "transparent",
              color: "var(--nova-ink)",
              font: "400 15px/1.5 var(--font-figtree),sans-serif",
              maxHeight: 160,
              minHeight: 24,
              padding: "4px 4px",
            }}
          />
          <button
            onClick={submit}
            disabled={sendDisabled}
            aria-label="Send message"
            style={{
              flex: "none",
              width: 34,
              height: 34,
              borderRadius: 10,
              border: "none",
              background: sendDisabled ? "var(--nova-border)" : "var(--nova-accent)",
              color: sendDisabled ? "var(--nova-ink-faint)" : "#fff",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              cursor: sendDisabled ? "default" : "pointer",
            }}
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M2 8h11M8 3l5 5-5 5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>
        </div>
        <div style={{ font: "400 11.5px/1.4 var(--font-figtree),sans-serif", color: "var(--nova-ink-faint)", marginTop: 8 }}>
          Nova can make mistakes. Verify important information.
        </div>
      </div>
    </div>
  );
}

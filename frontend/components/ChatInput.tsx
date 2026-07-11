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

  return (
    <div
      style={{
        display: "flex",
        gap: 8,
        padding: 12,
        borderTop: "1px solid var(--nova-border)",
        background: "var(--nova-surface)",
      }}
    >
      <textarea
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask Nova about MCN TV's SOPs or data…"
        rows={1}
        style={{
          flex: 1,
          resize: "none",
          border: "1px solid var(--nova-border)",
          borderRadius: 10,
          padding: "10px 12px",
          fontSize: 14.5,
          fontFamily: "inherit",
          outline: "none",
        }}
      />
      <button
        onClick={submit}
        disabled={disabled || !value.trim()}
        style={{
          border: "none",
          borderRadius: 10,
          padding: "0 18px",
          background: "var(--nova-accent)",
          color: "var(--nova-accent-ink)",
          fontWeight: 600,
          fontSize: 14,
          cursor: disabled ? "default" : "pointer",
          opacity: disabled || !value.trim() ? 0.5 : 1,
        }}
      >
        Send
      </button>
    </div>
  );
}

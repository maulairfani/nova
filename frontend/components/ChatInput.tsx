import { ReactElement, useEffect, useRef, useState, KeyboardEvent } from "react";

const MAX_INPUT_HEIGHT = 160;

export type FeatureKey = "chart" | "web_search";

const FEATURES: { key: FeatureKey; label: string; icon: ReactElement }[] = [
  {
    key: "chart",
    label: "Data visualization",
    icon: (
      <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
        <path d="M3 13.5V9M8 13.5V5M13 13.5V7" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
        <path d="M2 13.5h12" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
      </svg>
    ),
  },
  {
    key: "web_search",
    label: "Web search",
    icon: (
      <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
        <circle cx="8" cy="8" r="6" stroke="currentColor" strokeWidth="1.3" />
        <path
          d="M2 8h12M8 2c1.8 1.8 2.8 4 2.8 6s-1 4.2-2.8 6c-1.8-1.8-2.8-4-2.8-6s1-4.2 2.8-6z"
          stroke="currentColor"
          strokeWidth="1.2"
        />
      </svg>
    ),
  },
];

export function ChatInput({
  onSend,
  disabled,
  blockedReason,
}: {
  onSend: (text: string, forceTools: FeatureKey[]) => void;
  disabled: boolean;
  blockedReason?: string | null;
}) {
  const [value, setValue] = useState("");
  const [menuOpen, setMenuOpen] = useState(false);
  const [activeFeatures, setActiveFeatures] = useState<Set<FeatureKey>>(new Set());
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const composerDisabled = disabled || !!blockedReason;

  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.overflowY = el.scrollHeight > MAX_INPUT_HEIGHT ? "auto" : "hidden";
    el.style.height = `${Math.min(el.scrollHeight, MAX_INPUT_HEIGHT)}px`;
  }, [value]);

  const toggleFeature = (key: FeatureKey) => {
    setActiveFeatures((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  const submit = () => {
    const trimmed = value.trim();
    if (!trimmed || composerDisabled) return;
    onSend(trimmed, Array.from(activeFeatures));
    setValue("");
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  const sendDisabled = composerDisabled || !value.trim();

  return (
    <div style={{ flex: "none", background: "var(--nova-bg)" }}>
      <div style={{ maxWidth: 760, margin: "0 auto", padding: "14px 24px 20px" }}>
        {activeFeatures.size > 0 && (
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 8 }}>
            {FEATURES.filter((f) => activeFeatures.has(f.key)).map((f) => (
              <button key={f.key} onClick={() => toggleFeature(f.key)} style={pillStyle} aria-label={`Turn off ${f.label}`}>
                {f.icon}
                {f.label}
                <svg width="9" height="9" viewBox="0 0 16 16" fill="none">
                  <path d="M3 3l10 10M13 3L3 13" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
                </svg>
              </button>
            ))}
          </div>
        )}

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
          <div style={{ position: "relative", flex: "none" }}>
            <button
              onClick={() => setMenuOpen((v) => !v)}
              disabled={composerDisabled}
              aria-label="Add features"
              aria-expanded={menuOpen}
              className="nova-icon-btn"
              style={{ ...iconBtnStyle, color: menuOpen ? "var(--nova-accent)" : "var(--nova-ink-muted)" }}
            >
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path d="M8 2.5v11M2.5 8h11" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
              </svg>
            </button>

            {menuOpen && (
              <>
                <div onClick={() => setMenuOpen(false)} style={{ position: "fixed", inset: 0, zIndex: 15 }} />
                <div style={popoverStyle}>
                  {FEATURES.map((f) => {
                    const active = activeFeatures.has(f.key);
                    return (
                      <div key={f.key} onClick={() => toggleFeature(f.key)} style={popoverItemStyle}>
                        <span style={{ display: "flex", color: active ? "var(--nova-accent)" : "var(--nova-ink-muted)" }}>{f.icon}</span>
                        <span style={{ flex: 1 }}>{f.label}</span>
                        {active && (
                          <svg width="13" height="13" viewBox="0 0 16 16" fill="none">
                            <path
                              d="M3 8.5l3.5 3.5L13 5"
                              stroke="var(--nova-accent)"
                              strokeWidth="1.7"
                              strokeLinecap="round"
                              strokeLinejoin="round"
                            />
                          </svg>
                        )}
                      </div>
                    );
                  })}
                </div>
              </>
            )}
          </div>

          <textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Message Nova…"
            disabled={composerDisabled}
            rows={1}
            style={{
              flex: 1,
              resize: "none",
              border: "none",
              outline: "none",
              background: "transparent",
              color: "var(--nova-ink)",
              font: "400 15px/1.5 var(--font-figtree),sans-serif",
              maxHeight: MAX_INPUT_HEIGHT,
              minHeight: 24,
              padding: "4px 4px",
              overflowY: "hidden",
            }}
          />
          <button
            onClick={submit}
            disabled={sendDisabled}
            aria-label="Send message"
            className="nova-send-btn"
            style={{
              flex: "none",
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
        <div style={{ font: "400 11.5px/1.4 var(--font-figtree),sans-serif", color: "var(--nova-ink-faint)", marginTop: 8, textAlign: "center" }}>
          {blockedReason ?? "Nova can make mistakes. Verify important information."}
        </div>
      </div>
    </div>
  );
}

const iconBtnStyle: React.CSSProperties = {
  border: "none",
  background: "transparent",
  cursor: "pointer",
  padding: 7,
  borderRadius: 7,
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
};

const popoverStyle: React.CSSProperties = {
  position: "absolute",
  bottom: "calc(100% + 8px)",
  left: 0,
  background: "var(--nova-surface)",
  border: "1px solid var(--nova-border)",
  borderRadius: 12,
  boxShadow: "var(--nova-dropdown-shadow)",
  minWidth: 210,
  padding: 6,
  zIndex: 20,
};

const popoverItemStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 10,
  padding: "9px 10px",
  borderRadius: 8,
  cursor: "pointer",
  font: "500 13.5px/1.3 var(--font-figtree),sans-serif",
  color: "var(--nova-ink)",
};

const pillStyle: React.CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  gap: 6,
  padding: "5px 10px",
  borderRadius: 999,
  border: "1px solid var(--nova-accent)",
  background: "var(--nova-accent-soft)",
  color: "var(--nova-accent)",
  font: "500 12.5px/1.3 var(--font-figtree),sans-serif",
  cursor: "pointer",
};

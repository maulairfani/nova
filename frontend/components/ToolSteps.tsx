import { useState } from "react";

export interface StepData {
  type: "kb" | "data" | "web" | "chart";
  label: string;
}

export interface LiveStepData extends StepData {
  id: string;
  status: "active" | "done";
}

export function StepIcon({ type }: { type: StepData["type"] }) {
  if (type === "kb") {
    return (
      <svg width="10" height="10" viewBox="0 0 16 16" fill="none">
        <circle cx="7" cy="7" r="5" stroke="currentColor" strokeWidth="1.4" />
        <line x1="11" y1="11" x2="14.5" y2="14.5" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
      </svg>
    );
  }
  if (type === "data") {
    return (
      <svg width="10" height="10" viewBox="0 0 16 16" fill="none">
        <ellipse cx="8" cy="3.5" rx="6" ry="2" stroke="currentColor" strokeWidth="1.3" />
        <path d="M2 3.5v9c0 1.1 2.7 2 6 2s6-.9 6-2v-9" stroke="currentColor" strokeWidth="1.3" />
        <path d="M2 8c0 1.1 2.7 2 6 2s6-.9 6-2" stroke="currentColor" strokeWidth="1.3" />
      </svg>
    );
  }
  if (type === "web") {
    return (
      <svg width="10" height="10" viewBox="0 0 16 16" fill="none">
        <circle cx="8" cy="8" r="6" stroke="currentColor" strokeWidth="1.3" />
        <path d="M2 8h12M8 2c1.8 1.8 2.8 4 2.8 6s-1 4.2-2.8 6c-1.8-1.8-2.8-4-2.8-6s1-4.2 2.8-6z" stroke="currentColor" strokeWidth="1.2" />
      </svg>
    );
  }
  return (
    <svg width="10" height="10" viewBox="0 0 16 16" fill="none">
      <path d="M3 13.5V9M8 13.5V5M13 13.5V7" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
      <path d="M2 13.5h12" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
    </svg>
  );
}

const stepRowStyle: React.CSSProperties = { display: "flex", alignItems: "center", gap: 8, padding: "4px 0" };
const iconWrapStyle: React.CSSProperties = {
  flex: "none",
  width: 18,
  height: 18,
  borderRadius: 5,
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  color: "var(--nova-ink-muted)",
  background: "var(--nova-surface-2)",
};
const activeIconWrapStyle: React.CSSProperties = { ...iconWrapStyle, color: "var(--nova-accent)", background: "var(--nova-accent-soft)" };
const labelStyle: React.CSSProperties = { font: "500 12.5px/1.4 var(--font-figtree),sans-serif", color: "var(--nova-ink-muted)" };

/** Shown while the agent is actively working on the current turn — full
 * open list, each step showing pulsing dots while active and a checkmark
 * once done. No collapse toggle; nothing to hide yet. */
export function LiveSteps({ steps }: { steps: LiveStepData[] }) {
  if (steps.length === 0) return null;
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 2, marginBottom: 12, paddingBottom: 10, borderBottom: "1px solid var(--nova-border)" }}>
      {steps.map((step) => (
        <div key={step.id} style={stepRowStyle}>
          {step.status === "active" ? (
            <div style={activeIconWrapStyle}>
              <span style={dotStyle(0)} />
              <span style={dotStyle(0.13)} />
              <span style={dotStyle(0.26)} />
            </div>
          ) : (
            <div style={iconWrapStyle}>
              <svg width="10" height="10" viewBox="0 0 16 16" fill="none">
                <path d="M3 8.5l3.5 3.5L13 5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </div>
          )}
          <div style={labelStyle}>{step.label}</div>
        </div>
      ))}
    </div>
  );
}

function dotStyle(delay: number): React.CSSProperties {
  return {
    width: 4,
    height: 4,
    borderRadius: "50%",
    background: "var(--nova-accent)",
    display: "inline-block",
    animation: `nova-bounce 1.1s infinite ${delay}s`,
  };
}

/** Shown on a finished assistant message — collapsed to a one-line count
 * by default (supporting evidence, not the main content), expandable to
 * show each step with a settled checkmark. */
export function StepsTrace({ steps }: { steps: StepData[] }) {
  const [expanded, setExpanded] = useState(false);
  if (steps.length === 0) return null;

  const summaryBtnStyle: React.CSSProperties = {
    display: "inline-flex",
    alignItems: "center",
    gap: 5,
    border: "none",
    background: "transparent",
    color: "var(--nova-ink-faint)",
    font: "500 12px/1.3 var(--font-figtree),sans-serif",
    cursor: "pointer",
    padding: "0 0 12px",
    marginBottom: 2,
  };

  const countText = `${steps.length} ${steps.length === 1 ? "step" : "steps"}`;

  if (!expanded) {
    return (
      <button onClick={() => setExpanded(true)} style={summaryBtnStyle}>
        <svg width="12" height="12" viewBox="0 0 16 16" fill="none">
          <path d="M4 6l4 4 4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        {countText}
      </button>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 2, marginBottom: 12, paddingBottom: 10, borderBottom: "1px solid var(--nova-border)" }}>
      <button onClick={() => setExpanded(false)} style={summaryBtnStyle}>
        <svg width="12" height="12" viewBox="0 0 16 16" fill="none" style={{ transform: "rotate(180deg)" }}>
          <path d="M4 6l4 4 4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        {countText}
      </button>
      {steps.map((step, i) => (
        <div key={i} style={stepRowStyle}>
          <div style={iconWrapStyle}>
            <StepIcon type={step.type} />
          </div>
          <div style={labelStyle}>{step.label}</div>
        </div>
      ))}
    </div>
  );
}

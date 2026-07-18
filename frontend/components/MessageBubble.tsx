import { ChartImage } from "./ChartImage";
import { NovaMarkdown } from "../lib/NovaMarkdown";
import { ChartStep, Citation } from "../lib/streamChat";
import { LiveStepData, LiveSteps, StepData, StepsTrace } from "./ToolSteps";

export interface Message {
  role: "user" | "assistant";
  content: string;
  steps?: StepData[];
  charts?: ChartStep[];
  citations?: Citation[];
}

export function MessageBubble({
  message,
  isStreaming,
  liveSteps,
  liveCharts,
  liveCitations,
  onOpenSources,
}: {
  message: Message;
  isStreaming?: boolean;
  liveSteps?: LiveStepData[];
  liveCharts?: ChartStep[];
  liveCitations?: Citation[];
  onOpenSources?: (citations: Citation[], highlightIndex?: number) => void;
}) {
  const isUser = message.role === "user";

  if (isUser) {
    return (
      <div style={{ display: "flex", justifyContent: "flex-end" }}>
        <div
          style={{
            maxWidth: "70%",
            background: "var(--nova-user-bubble)",
            color: "var(--nova-user-ink)",
            padding: "12px 16px",
            borderRadius: "16px 16px 4px 16px",
            font: "400 15px/1.55 var(--font-figtree),sans-serif",
            whiteSpace: "pre-wrap",
          }}
        >
          {message.content}
        </div>
      </div>
    );
  }

  const citations = (isStreaming ? liveCitations : message.citations) ?? [];

  return (
    <div style={{ width: "100%" }}>
      {isStreaming && liveSteps && liveSteps.length > 0 ? (
        <LiveSteps steps={liveSteps} />
      ) : (
        message.steps && message.steps.length > 0 && <StepsTrace steps={message.steps} />
      )}

      {(isStreaming ? liveCharts : message.charts)?.map((chart) => (
        <ChartImage key={chart.chart_id} chartId={chart.chart_id} title={chart.title} />
      ))}

      {message.content ? (
        <div className="nova-markdown" style={{ font: "400 15px/1.65 var(--font-figtree),sans-serif", color: "var(--nova-ink)" }}>
          <NovaMarkdown
            text={message.content}
            citations={citations}
            onCiteClick={(citation) => onOpenSources?.(citations, citations.indexOf(citation))}
          />
        </div>
      ) : (
        isStreaming &&
        !(liveSteps && liveSteps.length > 0) &&
        !(liveCharts && liveCharts.length > 0) && (
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <TypingDot delay={0} />
            <TypingDot delay={0.15} />
            <TypingDot delay={0.3} />
            <span style={{ font: "500 11.5px/1.4 var(--font-figtree),sans-serif", color: "var(--nova-ink-muted)", marginLeft: 4 }}>
              Nova is responding…
            </span>
          </div>
        )
      )}

      {!isStreaming && citations.length > 0 && (
        <button onClick={() => onOpenSources?.(citations)} style={sourcesPillStyle}>
          <svg width="11" height="11" viewBox="0 0 16 16" fill="none">
            <path d="M4 1.5h6l3 3v10a1 1 0 01-1 1H4a1 1 0 01-1-1v-12a1 1 0 011-1z" stroke="currentColor" strokeWidth="1.3" strokeLinejoin="round" />
            <path d="M6 8.5h5M6 11h5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
          </svg>
          {citations.length} {citations.length === 1 ? "source" : "sources"}
        </button>
      )}
    </div>
  );
}

function TypingDot({ delay }: { delay: number }) {
  return (
    <span
      style={{
        width: 5,
        height: 5,
        borderRadius: "50%",
        background: "var(--nova-accent)",
        display: "inline-block",
        animation: `nova-bounce 1.2s infinite ${delay}s`,
      }}
    />
  );
}

const sourcesPillStyle: React.CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  gap: 6,
  marginTop: 10,
  padding: "5px 11px",
  borderRadius: 999,
  border: "1px solid var(--nova-border)",
  background: "var(--nova-surface-2)",
  color: "var(--nova-ink-muted)",
  font: "600 12px/1.3 var(--font-figtree),sans-serif",
  cursor: "pointer",
};

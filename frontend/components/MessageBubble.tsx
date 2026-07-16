import { renderInlineMarkdown } from "../lib/renderInlineMarkdown";
import { LiveStepData, LiveSteps, StepData, StepsTrace } from "./ToolSteps";

export interface Message {
  role: "user" | "assistant";
  content: string;
  steps?: StepData[];
}

export function MessageBubble({
  message,
  isStreaming,
  liveSteps,
}: {
  message: Message;
  isStreaming?: boolean;
  liveSteps?: LiveStepData[];
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

  return (
    <div style={{ display: "flex", justifyContent: "flex-start" }}>
      <div
        style={{
          maxWidth: "82%",
          background: "var(--nova-assistant-bubble)",
          border: "1px solid var(--nova-border)",
          padding: "14px 18px",
          borderRadius: "16px 16px 16px 4px",
        }}
      >
        {isStreaming && liveSteps && liveSteps.length > 0 ? (
          <LiveSteps steps={liveSteps} />
        ) : (
          message.steps && message.steps.length > 0 && <StepsTrace steps={message.steps} />
        )}

        {message.content ? (
          <div style={{ font: "400 15px/1.65 var(--font-figtree),sans-serif", color: "var(--nova-ink)", whiteSpace: "pre-wrap" }}>
            {renderInlineMarkdown(message.content)}
          </div>
        ) : (
          isStreaming &&
          !(liveSteps && liveSteps.length > 0) && (
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
      </div>
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

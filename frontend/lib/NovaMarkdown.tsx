import { CSSProperties, ReactNode, useMemo, useState } from "react";
import ReactMarkdown, { Components } from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkBreaks from "remark-breaks";
import { Citation } from "./streamChat";

const CODE_BLOCK_PRE_STYLE: CSSProperties = {
  margin: "6px 0 10px",
  borderRadius: 8,
  border: "1px solid var(--nova-border)",
  overflow: "hidden",
  background: "var(--nova-bg)",
};

const CODE_BLOCK_LANG_STYLE: CSSProperties = {
  font: "500 11px/1.4 var(--font-figtree),sans-serif",
  color: "var(--nova-ink-muted)",
  textTransform: "uppercase",
  letterSpacing: "0.04em",
  padding: "6px 12px",
  borderBottom: "1px solid var(--nova-border)",
  background: "var(--nova-surface-2)",
};

const CODE_BLOCK_CODE_STYLE: CSSProperties = {
  display: "block",
  margin: 0,
  padding: "10px 12px",
  overflowX: "auto",
  whiteSpace: "pre",
  font: "400 13px/1.55 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace",
  color: "var(--nova-ink)",
};

const INLINE_CODE_STYLE: CSSProperties = {
  background: "var(--nova-bg)",
  padding: "1px 5px",
  borderRadius: 4,
  fontSize: "0.9em",
  font: "400 0.9em ui-monospace,SFMono-Regular,Menlo,Consolas,monospace",
};

// Matches the SYSTEM_PROMPT's instructed block languages
// (backend/app/agent/prompts.py) - a fenced code block, one clickable
// option per line, exact text as it should be sent. Detected in the `pre`
// override below rather than via a text regex (like the citation marker)
// because a fenced block is unambiguous and react-markdown/remark-gfm
// already parses it into a `code` node with a `language-*` className -
// no custom preprocessing needed.
const QUICK_REPLY_LANG = "nova-quick-replies";
const MULTI_CHOICE_LANG = "nova-multi-choice";

function parseOptionLines(code: string): string[] {
  return code
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
}

const OPTION_BLOCK_WRAP_STYLE: CSSProperties = {
  display: "flex",
  flexWrap: "wrap",
  gap: 8,
  margin: "6px 0 10px",
};

const OPTION_BTN_STYLE: CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  gap: 6,
  padding: "7px 14px",
  borderRadius: 999,
  border: "1px solid var(--nova-accent)",
  background: "var(--nova-accent-soft)",
  color: "var(--nova-accent)",
  font: "600 13px/1.3 var(--font-figtree),sans-serif",
  cursor: "pointer",
};

const OPTION_BTN_INACTIVE_STYLE: CSSProperties = {
  ...OPTION_BTN_STYLE,
  border: "1px solid var(--nova-border)",
  background: "var(--nova-surface)",
  color: "var(--nova-ink)",
};

const OPTION_BTN_DISABLED_STYLE: CSSProperties = { opacity: 0.55, cursor: "default" };

/** Single-click-to-send options (`nova-quick-replies` fence) - each click
 * sends its exact label as the next user message immediately. */
function QuickReplyBlock({
  code,
  onSend,
  disabled,
}: {
  code: string;
  onSend?: (text: string) => void;
  disabled?: boolean;
}) {
  const options = useMemo(() => parseOptionLines(code), [code]);
  if (options.length === 0) return null;
  return (
    <div style={OPTION_BLOCK_WRAP_STYLE}>
      {options.map((opt, i) => (
        <button
          key={i}
          type="button"
          onClick={() => onSend?.(opt)}
          disabled={disabled}
          style={disabled ? { ...OPTION_BTN_STYLE, ...OPTION_BTN_DISABLED_STYLE } : OPTION_BTN_STYLE}
        >
          {opt}
        </button>
      ))}
    </div>
  );
}

/** Multi-select options (`nova-multi-choice` fence) - clicking toggles an
 * option; the currently-selected set is written into the existing message
 * composer (joined by ", ") on every toggle, so sending still goes through
 * the composer's normal Send button rather than a separate one. */
function MultiChoiceBlock({
  code,
  onComposeText,
  disabled,
}: {
  code: string;
  onComposeText?: (text: string) => void;
  disabled?: boolean;
}) {
  const options = useMemo(() => parseOptionLines(code), [code]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  if (options.length === 0) return null;

  // Computed here (not inside setSelected's updater) so onComposeText -
  // which calls back up into a parent's setState - isn't invoked during
  // this component's render phase, which React (correctly) warns about.
  const toggle = (opt: string) => {
    const next = new Set(selected);
    if (next.has(opt)) next.delete(opt);
    else next.add(opt);
    setSelected(next);
    onComposeText?.(options.filter((o) => next.has(o)).join(", "));
  };

  return (
    <div style={OPTION_BLOCK_WRAP_STYLE}>
      {options.map((opt, i) => {
        const active = selected.has(opt);
        const base = active ? OPTION_BTN_STYLE : OPTION_BTN_INACTIVE_STYLE;
        return (
          <button
            key={i}
            type="button"
            onClick={() => toggle(opt)}
            disabled={disabled}
            style={disabled ? { ...base, ...OPTION_BTN_DISABLED_STYLE } : base}
          >
            {active && (
              <svg width="11" height="11" viewBox="0 0 16 16" fill="none">
                <path d="M3 8.5l3.5 3.5L13 5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            )}
            {opt}
          </button>
        );
      })}
    </div>
  );
}

function firstText(children: ReactNode): string {
  if (typeof children === "string") return children;
  if (Array.isArray(children)) return children.map(firstText).join("");
  return "";
}

function fenceLangAndCode(children: ReactNode): { lang: string | undefined; code: string } {
  const codeChild = Array.isArray(children) ? children[0] : children;
  const props = (codeChild as { props?: { className?: string; children?: ReactNode } })?.props;
  const lang = /language-(\S+)/.exec(props?.className || "")?.[1];
  const code = firstText(props?.children).replace(/\n$/, "");
  return { lang, code };
}

function renderCodeFence(children: ReactNode) {
  const { lang, code } = fenceLangAndCode(children);
  return (
    <pre style={CODE_BLOCK_PRE_STYLE}>
      {lang && <div style={CODE_BLOCK_LANG_STYLE}>{lang}</div>}
      <code style={CODE_BLOCK_CODE_STYLE}>{code}</code>
    </pre>
  );
}

function headingStyle(level: number): CSSProperties {
  const fontSize = level <= 2 ? 17 : 15;
  return { font: `600 ${fontSize}px/1.4 var(--font-figtree),sans-serif`, margin: "10px 0 4px" };
}

const components: Components = {
  h1: ({ children }) => <div style={headingStyle(1)}>{children}</div>,
  h2: ({ children }) => <div style={headingStyle(2)}>{children}</div>,
  h3: ({ children }) => <div style={headingStyle(3)}>{children}</div>,
  h4: ({ children }) => <div style={headingStyle(4)}>{children}</div>,
  h5: ({ children }) => <div style={headingStyle(5)}>{children}</div>,
  h6: ({ children }) => <div style={headingStyle(6)}>{children}</div>,
  p: ({ children }) => <p style={{ margin: "0 0 8px" }}>{children}</p>,
  ul: ({ children }) => <ul style={{ margin: "4px 0 8px", paddingLeft: 22 }}>{children}</ul>,
  ol: ({ children, start }) => (
    <ol start={start} style={{ margin: "4px 0 8px", paddingLeft: 22 }}>
      {children}
    </ol>
  ),
  li: ({ children, className }) => (
    <li style={{ marginBottom: 2, listStyleType: className?.includes("task-list-item") ? "none" : undefined, marginLeft: className?.includes("task-list-item") ? -18 : undefined }}>
      {children}
    </li>
  ),
  input: ({ checked }) => (
    <input type="checkbox" checked={!!checked} disabled style={{ marginRight: 6, accentColor: "var(--nova-accent)" }} readOnly />
  ),
  blockquote: ({ children }) => (
    <blockquote
      style={{
        margin: "6px 0 10px",
        padding: "2px 14px",
        borderLeft: "3px solid var(--nova-accent)",
        color: "var(--nova-ink-muted)",
      }}
    >
      {children}
    </blockquote>
  ),
  hr: () => <hr style={{ margin: "12px 0", border: "none", borderTop: "1px solid var(--nova-border)" }} />,
  del: ({ children }) => <del style={{ opacity: 0.65 }}>{children}</del>,
  table: ({ children }) => (
    <div style={{ overflowX: "auto", margin: "6px 0 10px" }}>
      <table style={{ borderCollapse: "collapse", width: "100%", font: "400 14px/1.5 var(--font-figtree),sans-serif" }}>{children}</table>
    </div>
  ),
  thead: ({ children }) => <thead>{children}</thead>,
  th: ({ children }) => (
    <th
      style={{
        textAlign: "left",
        padding: "6px 10px",
        borderBottom: "2px solid var(--nova-border)",
        background: "var(--nova-surface-2)",
        fontWeight: 600,
      }}
    >
      {children}
    </th>
  ),
  td: ({ children }) => <td style={{ padding: "6px 10px", borderBottom: "1px solid var(--nova-border)" }}>{children}</td>,
  pre: ({ children }) => renderCodeFence(children),
  code: ({ children }) => <code style={INLINE_CODE_STYLE}>{children}</code>,
};

const CITATION_BADGE_STYLE: CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  justifyContent: "center",
  minWidth: 15,
  height: 15,
  padding: "0 4px",
  marginLeft: 1,
  borderRadius: 999,
  border: "none",
  background: "var(--nova-accent-soft)",
  color: "var(--nova-accent)",
  font: "600 10px/1 var(--font-figtree),sans-serif",
  cursor: "pointer",
  verticalAlign: "super",
};

const PLAIN_LINK_STYLE: CSSProperties = { color: "var(--nova-accent)", textDecoration: "underline" };

// A same-page anchor fragment, not a custom URL scheme: react-markdown's
// default urlTransform strips any href scheme outside http/https/mailto/tel
// (XSS hardening) - a fragment link passes through untouched, so this
// sidesteps that entirely rather than fighting it with a custom
// urlTransform prop.
const CITATION_HREF_PREFIX = "#nova-citation-";
// Matches the SYSTEM_PROMPT's instructed marker (backend/app/agent/prompts.py)
// - a source's exact title wrapped in full-width brackets, e.g.
// 【Ad Slot Booking SOP — MCN TV】. Chosen over plain [1]/[[1]] because the
// model copies a title it already sees verbatim in tool results, rather
// than tracking an abstract number it's never shown - far more reliable
// for a small model, and full-width brackets essentially never appear in
// ordinary prose, so there's no realistic collision with real content.
const CITATION_MARKER_RE = /【([^】]+)】/g;

/** Rewrites 【Title】 markers into markdown links (`[n](#nova-citation-i)`)
 * the `a` override below renders as clickable numbered badges - numbers
 * assigned by first appearance in the text, not by retrieval order, so
 * they always match what the reader actually sees top-to-bottom. A marker
 * whose title doesn't match any known citation is dropped silently
 * (better than a broken-looking badge) - can happen if the model
 * paraphrases a title instead of copying it exactly. */
function preprocessCitationMarkers(text: string, citations: Citation[]): string {
  if (citations.length === 0) return text;
  const numberByIndex = new Map<number, number>();
  let nextNumber = 1;
  return text.replace(CITATION_MARKER_RE, (_match, rawTitle: string) => {
    const needle = rawTitle.trim().toLowerCase();
    const idx = citations.findIndex((c) => c.title.trim().toLowerCase() === needle);
    if (idx === -1) return "";
    if (!numberByIndex.has(idx)) numberByIndex.set(idx, nextNumber++);
    return `[${numberByIndex.get(idx)}](${CITATION_HREF_PREFIX}${idx})`;
  });
}

/** Chat-bubble markdown: CommonMark + GFM (tables, strikethrough, task
 * lists, autolinks) via react-markdown/remark-gfm, plus remark-breaks so a
 * single newline (how the LLM's replies are formatted) still renders as a
 * visual line break instead of CommonMark's default soft-break-as-space.
 *
 * `citations`/`onCiteClick` are optional - only assistant messages that
 * actually retrieved sources pass them, wiring 【Title】 markers to
 * clickable badges that open the Sources panel (SourcesPanel.tsx). */
export function NovaMarkdown({
  text,
  citations = [],
  onCiteClick,
  onQuickReply,
  onComposeText,
  interactionsDisabled,
}: {
  text: string;
  citations?: Citation[];
  onCiteClick?: (citation: Citation) => void;
  onQuickReply?: (text: string) => void;
  onComposeText?: (text: string) => void;
  interactionsDisabled?: boolean;
}) {
  const processedText = useMemo(() => preprocessCitationMarkers(text, citations), [text, citations]);

  const linkAwareComponents = useMemo<Components>(
    () => ({
      ...components,
      pre: ({ children }) => {
        const { lang, code } = fenceLangAndCode(children);
        if (lang === QUICK_REPLY_LANG) {
          return <QuickReplyBlock code={code} onSend={onQuickReply} disabled={interactionsDisabled} />;
        }
        if (lang === MULTI_CHOICE_LANG) {
          return <MultiChoiceBlock code={code} onComposeText={onComposeText} disabled={interactionsDisabled} />;
        }
        return renderCodeFence(children);
      },
      a: ({ children, href }) => {
        if (href?.startsWith(CITATION_HREF_PREFIX)) {
          const citation = citations[Number(href.slice(CITATION_HREF_PREFIX.length))];
          if (!citation) return null;
          return (
            <button type="button" onClick={() => onCiteClick?.(citation)} style={CITATION_BADGE_STYLE} title={citation.title}>
              {children}
            </button>
          );
        }
        return (
          <a href={href} target="_blank" rel="noopener noreferrer" style={PLAIN_LINK_STYLE}>
            {children}
          </a>
        );
      },
    }),
    [citations, onCiteClick, onQuickReply, onComposeText, interactionsDisabled]
  );

  return (
    <ReactMarkdown remarkPlugins={[remarkGfm, remarkBreaks]} components={linkAwareComponents}>
      {processedText}
    </ReactMarkdown>
  );
}

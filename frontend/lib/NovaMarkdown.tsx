import { CSSProperties, ReactNode, useMemo } from "react";
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

function firstText(children: ReactNode): string {
  if (typeof children === "string") return children;
  if (Array.isArray(children)) return children.map(firstText).join("");
  return "";
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
  pre: ({ children }) => {
    const codeChild = Array.isArray(children) ? children[0] : children;
    const props = (codeChild as { props?: { className?: string; children?: ReactNode } })?.props;
    const match = /language-(\w+)/.exec(props?.className || "");
    const code = firstText(props?.children).replace(/\n$/, "");
    return (
      <pre style={CODE_BLOCK_PRE_STYLE}>
        {match && <div style={CODE_BLOCK_LANG_STYLE}>{match[1]}</div>}
        <code style={CODE_BLOCK_CODE_STYLE}>{code}</code>
      </pre>
    );
  },
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
}: {
  text: string;
  citations?: Citation[];
  onCiteClick?: (citation: Citation) => void;
}) {
  const processedText = useMemo(() => preprocessCitationMarkers(text, citations), [text, citations]);

  const linkAwareComponents = useMemo<Components>(
    () => ({
      ...components,
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
    [citations, onCiteClick]
  );

  return (
    <ReactMarkdown remarkPlugins={[remarkGfm, remarkBreaks]} components={linkAwareComponents}>
      {processedText}
    </ReactMarkdown>
  );
}

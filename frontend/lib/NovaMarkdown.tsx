import { CSSProperties, ReactNode } from "react";
import ReactMarkdown, { Components } from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkBreaks from "remark-breaks";

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
  a: ({ children, href }) => (
    <a href={href} target="_blank" rel="noopener noreferrer" style={{ color: "var(--nova-accent)", textDecoration: "underline" }}>
      {children}
    </a>
  ),
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

/** Chat-bubble markdown: CommonMark + GFM (tables, strikethrough, task
 * lists, autolinks) via react-markdown/remark-gfm, plus remark-breaks so a
 * single newline (how the LLM's replies are formatted) still renders as a
 * visual line break instead of CommonMark's default soft-break-as-space. */
export function NovaMarkdown({ text }: { text: string }) {
  return (
    <ReactMarkdown remarkPlugins={[remarkGfm, remarkBreaks]} components={components}>
      {text}
    </ReactMarkdown>
  );
}

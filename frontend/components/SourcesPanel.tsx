import { useEffect, useState } from "react";
import { getToken } from "../lib/auth";
import { BUSINESS_UNIT_LABELS } from "../lib/businessUnits";
import { DocumentItem, findDocumentByObjectKey } from "../lib/documents";
import { Citation } from "../lib/streamChat";
import { DocumentPreviewModal } from "./DocumentPreviewModal";
import { StepIcon } from "./ToolSteps";

/** Slide-in panel (same fixed-overlay convention as the mobile sidebar
 * drawer) listing every source a message's answer drew on - opened via
 * either the "N sources" pill under a message or an inline 【Title】
 * citation badge (NovaMarkdown), the latter passing `highlightIndex` so
 * the matching card is scrolled to and briefly highlighted. */
export function SourcesPanel({
  citations,
  highlightIndex,
  onClose,
}: {
  citations: Citation[];
  highlightIndex?: number | null;
  onClose: () => void;
}) {
  const [resolvingIndex, setResolvingIndex] = useState<number | null>(null);
  const [unavailable, setUnavailable] = useState<Set<number>>(new Set());
  const [previewDoc, setPreviewDoc] = useState<DocumentItem | null>(null);

  useEffect(() => {
    if (highlightIndex == null) return;
    document.getElementById(`nova-source-${highlightIndex}`)?.scrollIntoView({ block: "center", behavior: "smooth" });
  }, [highlightIndex]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const handleViewDocument = async (citation: Citation, index: number) => {
    const token = getToken();
    if (!token || !citation.unit || !citation.source_document) return;
    setResolvingIndex(index);
    try {
      const doc = await findDocumentByObjectKey(token, citation.unit, citation.source_document);
      if (doc) setPreviewDoc(doc);
      else setUnavailable((prev) => new Set(prev).add(index));
    } catch {
      setUnavailable((prev) => new Set(prev).add(index));
    } finally {
      setResolvingIndex(null);
    }
  };

  return (
    <>
      <div className="nova-sidebar-backdrop" onClick={onClose} />
      <div style={panelStyle}>
        <div style={headerStyle}>
          <div style={headerTitleStyle}>{citations.length} {citations.length === 1 ? "source" : "sources"}</div>
          <button onClick={onClose} aria-label="Close sources" className="nova-icon-btn" style={closeBtnStyle}>
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <line x1="3" y1="3" x2="13" y2="13" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
              <line x1="13" y1="3" x2="3" y2="13" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
            </svg>
          </button>
        </div>
        <div style={listStyle}>
          {citations.map((c, i) => (
            <div key={i} id={`nova-source-${i}`} style={i === highlightIndex ? { ...cardStyle, ...highlightedCardStyle } : cardStyle}>
              <div style={cardHeaderStyle}>
                <div style={iconWrapStyle}>
                  <StepIcon type={c.type} />
                </div>
                <div style={cardTitleStyle}>{c.title}</div>
              </div>
              {c.type === "kb" && c.unit && <div style={tagStyle}>{BUSINESS_UNIT_LABELS[c.unit] ?? c.unit}</div>}
              <div style={snippetStyle}>{c.snippet}</div>
              {c.type === "web" && c.url && (
                <a href={c.url} target="_blank" rel="noopener noreferrer" style={linkStyle}>
                  Open source
                  <svg width="10" height="10" viewBox="0 0 16 16" fill="none">
                    <path d="M6 3h7v7M13 3L4 12" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </a>
              )}
              {c.type === "kb" &&
                (unavailable.has(i) ? (
                  <div style={{ ...linkStyle, color: "var(--nova-ink-faint)", cursor: "default" }}>Document no longer available</div>
                ) : (
                  <button onClick={() => handleViewDocument(c, i)} disabled={resolvingIndex === i} style={{ ...linkStyle, background: "none", border: "none", padding: 0, cursor: resolvingIndex === i ? "default" : "pointer" }}>
                    {resolvingIndex === i ? "Opening…" : "View document"}
                    {resolvingIndex !== i && (
                      <svg width="10" height="10" viewBox="0 0 16 16" fill="none">
                        <path d="M6 3h7v7M13 3L4 12" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
                      </svg>
                    )}
                  </button>
                ))}
            </div>
          ))}
        </div>
      </div>

      {previewDoc && (
        <DocumentPreviewModal
          documentId={previewDoc.id}
          title={previewDoc.title}
          format={previewDoc.format}
          onClose={() => setPreviewDoc(null)}
        />
      )}
    </>
  );
}

const panelStyle: React.CSSProperties = {
  position: "fixed",
  top: 0,
  bottom: 0,
  right: 0,
  zIndex: 45,
  width: "min(360px, 90vw)",
  background: "var(--nova-surface)",
  borderLeft: "1px solid var(--nova-border)",
  display: "flex",
  flexDirection: "column",
  boxShadow: "-8px 0 24px rgba(0,0,0,0.08)",
};

const headerStyle: React.CSSProperties = {
  flex: "none",
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  padding: "16px 16px 12px",
  borderBottom: "1px solid var(--nova-border)",
};

const headerTitleStyle: React.CSSProperties = {
  font: "600 14.5px/1.3 var(--font-figtree),sans-serif",
  color: "var(--nova-ink)",
};

const closeBtnStyle: React.CSSProperties = {
  border: "none",
  background: "transparent",
  color: "var(--nova-ink-muted)",
  cursor: "pointer",
  padding: 6,
  borderRadius: 7,
  display: "flex",
};

const listStyle: React.CSSProperties = { flex: 1, overflowY: "auto", padding: "12px 16px 16px", display: "flex", flexDirection: "column", gap: 10 };

const cardStyle: React.CSSProperties = {
  padding: 12,
  borderRadius: 10,
  border: "1px solid var(--nova-border)",
  background: "var(--nova-bg)",
  transition: "background .4s ease, border-color .4s ease",
};

const highlightedCardStyle: React.CSSProperties = {
  borderColor: "var(--nova-accent)",
  background: "var(--nova-accent-soft)",
};

const cardHeaderStyle: React.CSSProperties = { display: "flex", alignItems: "flex-start", gap: 8 };

const iconWrapStyle: React.CSSProperties = {
  flex: "none",
  width: 20,
  height: 20,
  marginTop: 1,
  borderRadius: 5,
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  color: "var(--nova-accent)",
  background: "var(--nova-accent-soft)",
};

const cardTitleStyle: React.CSSProperties = {
  font: "600 13px/1.4 var(--font-figtree),sans-serif",
  color: "var(--nova-ink)",
};

const tagStyle: React.CSSProperties = {
  display: "inline-block",
  marginTop: 6,
  marginLeft: 28,
  padding: "1px 8px",
  borderRadius: 999,
  font: "600 10.5px/1.4 var(--font-figtree),sans-serif",
  color: "var(--nova-ink-muted)",
  background: "var(--nova-surface-2)",
  width: "fit-content",
};

const snippetStyle: React.CSSProperties = {
  marginTop: 6,
  marginLeft: 28,
  font: "400 12.5px/1.5 var(--font-figtree),sans-serif",
  color: "var(--nova-ink-muted)",
  display: "-webkit-box",
  WebkitLineClamp: 3,
  WebkitBoxOrient: "vertical",
  overflow: "hidden",
};

const linkStyle: React.CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  gap: 4,
  marginTop: 8,
  marginLeft: 28,
  font: "600 12px/1.3 var(--font-figtree),sans-serif",
  color: "var(--nova-accent)",
  textDecoration: "none",
};

import { useEffect, useState } from "react";
import { NovaMarkdown } from "../lib/NovaMarkdown";
import { authenticatedFetch } from "../lib/authenticatedFetch";
import { getToken } from "../lib/auth";
import { useBlobUrl } from "../lib/useBlobUrl";
import { overlayStyle, previewModalStyle } from "../lib/modalStyles";

export function DocumentPreviewModal({
  documentId,
  title,
  format,
  onClose,
}: {
  documentId: string;
  title: string;
  format: string;
  onClose: () => void;
}) {
  const isMarkdown = format === "markdown";
  const contentPath = `/api/v1/documents/${documentId}/content`;

  const [text, setText] = useState<string | null>(null);
  const [textError, setTextError] = useState(false);
  const { url: pdfUrl, loading: pdfLoading, error: pdfError } = useBlobUrl(isMarkdown ? null : contentPath);

  useEffect(() => {
    if (!isMarkdown) return;
    const token = getToken();
    if (!token) {
      setTextError(true);
      return;
    }
    let cancelled = false;
    authenticatedFetch(contentPath, token)
      .then((r) => r.text())
      .then((body) => {
        if (!cancelled) setText(body);
      })
      .catch(() => {
        if (!cancelled) setTextError(true);
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [documentId, isMarkdown]);

  return (
    <div style={overlayStyle} onClick={onClose}>
      <div style={previewModalStyle} onClick={(e) => e.stopPropagation()}>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: 12,
            padding: "16px 20px",
            borderBottom: "1px solid var(--nova-border)",
            flex: "none",
          }}
        >
          <div className="nova-serif" style={{ fontSize: 16, fontWeight: 600, color: "var(--nova-ink)" }}>
            {title}
          </div>
          <button onClick={onClose} aria-label="Close preview" style={closeBtnStyle}>
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M3 3l10 10M13 3L3 13" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
            </svg>
          </button>
        </div>

        <div style={{ flex: 1, overflow: "auto", padding: isMarkdown ? "20px 24px" : 0 }}>
          {isMarkdown ? (
            textError ? (
              <div style={emptyStateStyle}>Couldn't load this document's content.</div>
            ) : text === null ? (
              <div style={emptyStateStyle}>Loading…</div>
            ) : (
              <NovaMarkdown text={text} />
            )
          ) : pdfError ? (
            <div style={emptyStateStyle}>Couldn't load this document's content.</div>
          ) : pdfLoading || !pdfUrl ? (
            <div style={emptyStateStyle}>Loading…</div>
          ) : (
            <iframe src={pdfUrl} title={title} style={{ width: "100%", height: "100%", border: "none" }} />
          )}
        </div>
      </div>
    </div>
  );
}

const closeBtnStyle: React.CSSProperties = {
  border: "none",
  background: "transparent",
  color: "var(--nova-ink-muted)",
  cursor: "pointer",
  padding: 6,
  borderRadius: 6,
  display: "flex",
  flex: "none",
};

const emptyStateStyle: React.CSSProperties = {
  padding: "40px 20px",
  textAlign: "center",
  color: "var(--nova-ink-muted)",
  font: "400 14px/1.6 var(--font-figtree),sans-serif",
};

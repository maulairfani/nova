import { useBlobUrl } from "../lib/useBlobUrl";

export function ChartImage({ chartId, title }: { chartId: string; title: string }) {
  const { url, loading, error } = useBlobUrl(`/api/v1/charts/${chartId}`);

  if (error) return null;

  return (
    <div style={wrapStyle}>
      {loading || !url ? (
        <div style={loadingStyle}>Loading chart…</div>
      ) : (
        <>
          <img src={url} alt={title} style={imgStyle} />
          <div style={footerStyle}>
            <span style={titleStyle}>{title}</span>
            <a href={url} download={`${title || "chart"}.png`} style={downloadLinkStyle}>
              Download
            </a>
          </div>
        </>
      )}
    </div>
  );
}

const wrapStyle: React.CSSProperties = {
  margin: "6px 0 10px",
  borderRadius: 12,
  border: "1px solid var(--nova-border)",
  overflow: "hidden",
  background: "#fcfcfb",
};

const imgStyle: React.CSSProperties = { display: "block", width: "100%", height: "auto" };

const loadingStyle: React.CSSProperties = {
  padding: "40px 20px",
  textAlign: "center",
  color: "var(--nova-ink-muted)",
  font: "400 13px/1.5 var(--font-figtree),sans-serif",
};

const footerStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  gap: 10,
  padding: "8px 12px",
  borderTop: "1px solid var(--nova-border)",
  background: "var(--nova-surface)",
};

const titleStyle: React.CSSProperties = {
  font: "500 12px/1.4 var(--font-figtree),sans-serif",
  color: "var(--nova-ink-muted)",
  overflow: "hidden",
  textOverflow: "ellipsis",
  whiteSpace: "nowrap",
};

const downloadLinkStyle: React.CSSProperties = {
  flex: "none",
  font: "600 12px/1.2 var(--font-figtree),sans-serif",
  color: "var(--nova-accent)",
  textDecoration: "none",
};

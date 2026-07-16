import { useEffect, useState } from "react";
import { BUSINESS_UNIT_LABELS } from "../lib/businessUnits";
import { DocumentItem, deleteDocument, listDocuments, uploadDocument } from "../lib/documents";
import { getToken } from "../lib/auth";

const STATUS_STYLE: Record<DocumentItem["status"], { label: string; bg: string; fg: string }> = {
  pending: { label: "Pending", bg: "var(--nova-accent-soft)", fg: "var(--nova-accent)" },
  ingested: { label: "Ingested", bg: "#e9f0e6", fg: "#5a8a52" },
  failed: { label: "Failed", bg: "var(--nova-danger-soft)", fg: "var(--nova-danger)" },
};

export function DocumentsView({
  units,
  canManageUnit,
}: {
  units: readonly string[];
  canManageUnit: (unit: string) => boolean;
}) {
  const [activeUnit, setActiveUnit] = useState(units[0] ?? "");
  const [docs, setDocs] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);
  const [uploadOpen, setUploadOpen] = useState(false);
  const [uploadTitle, setUploadTitle] = useState("");
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadUnit, setUploadUnit] = useState(activeUnit);
  const [uploadBusy, setUploadBusy] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const refresh = () => {
    const token = getToken();
    if (!token || !activeUnit) return;
    setLoading(true);
    listDocuments(token, activeUnit)
      .then(setDocs)
      .catch(() => setDocs([]))
      .finally(() => setLoading(false));
  };

  useEffect(refresh, [activeUnit]);

  if (!activeUnit) {
    return (
      <div style={{ flex: 1, overflowY: "auto", display: "flex", justifyContent: "center", padding: "36px 24px" }}>
        <div style={{ maxWidth: 860, width: "100%" }}>
          <div className="nova-serif" style={{ fontSize: 26, fontWeight: 600, color: "var(--nova-ink)", marginBottom: 6 }}>
            Manage documents
          </div>
          <div style={{ font: "400 14.5px/1.6 var(--font-figtree),sans-serif", color: "var(--nova-ink-muted)" }}>
            You don't have access to any business unit's documents yet.
          </div>
        </div>
      </div>
    );
  }

  const filtered = docs.filter((d) => !search.trim() || d.title.toLowerCase().includes(search.trim().toLowerCase()));
  const canUpload = canManageUnit(activeUnit);

  const openUpload = () => {
    setUploadTitle("");
    setUploadFile(null);
    setUploadUnit(activeUnit);
    setUploadError(null);
    setUploadOpen(true);
  };

  const submitUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    const token = getToken();
    if (!token || !uploadFile) {
      setUploadError("Choose a file to upload.");
      return;
    }
    setUploadBusy(true);
    setUploadError(null);
    try {
      await uploadDocument(token, uploadUnit, uploadFile, uploadTitle);
      setUploadOpen(false);
      if (uploadUnit === activeUnit) refresh();
    } catch {
      setUploadError("Upload failed. Only Markdown (.md) and PDF (.pdf) files are supported.");
    } finally {
      setUploadBusy(false);
    }
  };

  const handleDelete = async (id: string) => {
    const token = getToken();
    if (!token) return;
    setDocs((prev) => prev.filter((d) => d.id !== id));
    setConfirmDeleteId(null);
    try {
      await deleteDocument(token, id);
    } catch {
      refresh();
    }
  };

  return (
    <div style={{ flex: 1, overflowY: "auto", display: "flex", justifyContent: "center", padding: "36px 24px" }}>
      <div style={{ maxWidth: 860, width: "100%" }}>
        <div className="nova-serif" style={{ fontSize: 26, fontWeight: 600, color: "var(--nova-ink)", marginBottom: 6 }}>
          Manage documents
        </div>
        <div style={{ font: "400 14.5px/1.6 var(--font-figtree),sans-serif", color: "var(--nova-ink-muted)", marginBottom: 24 }}>
          Browse the knowledge base documents Nova can draw on for your business unit.
        </div>

        {units.length > 1 && (
          <div style={{ display: "flex", gap: 4, padding: 4, background: "var(--nova-surface-2)", borderRadius: 999, width: "fit-content", marginBottom: 20 }}>
            {units.map((u) => (
              <button
                key={u}
                onClick={() => setActiveUnit(u)}
                style={{
                  padding: "7px 16px",
                  borderRadius: 999,
                  border: "none",
                  cursor: "pointer",
                  font: `${u === activeUnit ? 600 : 500} 13px/1.2 var(--font-figtree),sans-serif`,
                  background: u === activeUnit ? "var(--nova-ink)" : "transparent",
                  color: u === activeUnit ? "var(--nova-bg)" : "var(--nova-ink-muted)",
                }}
              >
                {BUSINESS_UNIT_LABELS[u] ?? u}
              </button>
            ))}
          </div>
        )}

        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12, marginBottom: 16 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "8px 12px", borderRadius: 9, background: "var(--nova-surface)", border: "1px solid var(--nova-border)", flex: 1, maxWidth: 320 }}>
            <svg width="14" height="14" viewBox="0 0 16 16" fill="none" style={{ flex: "none", color: "var(--nova-ink-muted)" }}>
              <circle cx="7" cy="7" r="5" stroke="currentColor" strokeWidth="1.4" />
              <line x1="11" y1="11" x2="14.5" y2="14.5" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
            </svg>
            <input
              placeholder="Search by title"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{ border: "none", outline: "none", background: "transparent", flex: 1, font: "400 13.5px/1.3 var(--font-figtree),sans-serif", color: "var(--nova-ink)", minWidth: 0 }}
            />
          </div>
          {canUpload && (
            <button onClick={openUpload} style={uploadBtnStyle}>
              <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                <line x1="8" y1="2" x2="8" y2="14" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
                <line x1="2" y1="8" x2="14" y2="8" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
              </svg>
              Upload document
            </button>
          )}
        </div>

        {!loading && filtered.length === 0 && (
          <div style={{ textAlign: "center", padding: "56px 20px", color: "var(--nova-ink-muted)", font: "400 14.5px/1.6 var(--font-figtree),sans-serif" }}>
            <div style={{ font: "600 16px/1.3 var(--font-figtree),sans-serif", color: "var(--nova-ink)", marginBottom: 6 }}>No documents yet</div>
            {canUpload && <div>Upload a Markdown or PDF file to get started.</div>}
          </div>
        )}

        {!loading && filtered.length > 0 && (
          <div>
            <div style={tableHeadStyle}>
              <div>Title</div>
              <div>Format</div>
              <div>Status</div>
              <div>Chunks</div>
              <div>Date</div>
              <div></div>
            </div>
            {filtered.map((doc) => {
              const sp = STATUS_STYLE[doc.status];
              return (
                <div key={doc.id} style={rowStyle}>
                  <div style={cellTitleStyle}>{doc.title}</div>
                  <div style={formatBadgeStyle}>{doc.format}</div>
                  <div>
                    <span
                      title={doc.error_message ?? undefined}
                      style={{
                        display: "inline-flex",
                        alignItems: "center",
                        padding: "3px 10px",
                        borderRadius: 999,
                        background: sp.bg,
                        color: sp.fg,
                        font: "600 11.5px/1.4 var(--font-figtree),sans-serif",
                        cursor: doc.error_message ? "help" : "default",
                      }}
                    >
                      {sp.label}
                    </span>
                  </div>
                  <div style={cellMutedStyle}>{doc.status === "ingested" ? `${doc.chunk_count ?? 0} chunks` : "—"}</div>
                  <div style={cellMutedStyle}>{new Date(doc.created_at).toLocaleDateString()}</div>
                  <div>
                    {canManageUnit(doc.business_unit_code) &&
                      (confirmDeleteId === doc.id ? (
                        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                          <button onClick={() => handleDelete(doc.id)} style={deleteConfirmBtnStyle}>
                            Delete
                          </button>
                          <button onClick={() => setConfirmDeleteId(null)} style={deleteCancelBtnStyle}>
                            ✕
                          </button>
                        </div>
                      ) : (
                        <button onClick={() => setConfirmDeleteId(doc.id)} aria-label="Delete document" style={deleteBtnStyle}>
                          <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                            <path
                              d="M3 4.5h10M6.5 4.5V3a1 1 0 011-1h1a1 1 0 011 1v1.5M4.5 4.5l.6 8.4a1 1 0 001 .9h3.8a1 1 0 001-.9l.6-8.4"
                              stroke="currentColor"
                              strokeWidth="1.3"
                              strokeLinecap="round"
                              strokeLinejoin="round"
                            />
                          </svg>
                        </button>
                      ))}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {uploadOpen && (
        <div style={overlayStyle} onClick={() => setUploadOpen(false)}>
          <form style={modalStyle} onSubmit={submitUpload} onClick={(e) => e.stopPropagation()}>
            <div className="nova-serif" style={{ fontSize: 18, fontWeight: 600, color: "var(--nova-ink)", marginBottom: 18 }}>
              Upload document
            </div>

            <label style={fieldLabelStyle}>File</label>
            <input
              type="file"
              accept=".md,.markdown,.pdf"
              onChange={(e) => setUploadFile(e.target.files?.[0] ?? null)}
              style={{ font: "400 13px/1.4 var(--font-figtree),sans-serif", color: "var(--nova-ink)" }}
            />

            <label style={fieldLabelStyle}>Title</label>
            <input
              value={uploadTitle}
              onChange={(e) => setUploadTitle(e.target.value)}
              placeholder="e.g. Content Compliance Playbook v3"
              style={inputStyle}
            />

            {units.filter((u) => canManageUnit(u)).length > 1 && (
              <>
                <label style={fieldLabelStyle}>Business unit</label>
                <select value={uploadUnit} onChange={(e) => setUploadUnit(e.target.value)} style={inputStyle}>
                  {units
                    .filter((u) => canManageUnit(u))
                    .map((u) => (
                      <option key={u} value={u}>
                        {BUSINESS_UNIT_LABELS[u] ?? u}
                      </option>
                    ))}
                </select>
              </>
            )}

            {uploadError && (
              <div style={{ font: "500 13px/1.5 var(--font-figtree),sans-serif", color: "var(--nova-danger)", marginTop: 14 }}>{uploadError}</div>
            )}

            <div style={{ display: "flex", justifyContent: "flex-end", gap: 10, marginTop: 26 }}>
              <button type="button" onClick={() => setUploadOpen(false)} style={secondaryBtnStyle}>
                Cancel
              </button>
              <button type="submit" disabled={uploadBusy} style={primaryBtnStyle}>
                {uploadBusy ? "Uploading…" : "Upload"}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}

const uploadBtnStyle: React.CSSProperties = {
  flex: "none",
  display: "flex",
  alignItems: "center",
  gap: 7,
  padding: "9px 16px",
  borderRadius: 9,
  border: "none",
  background: "var(--nova-accent)",
  color: "#fff",
  font: "600 13.5px/1.2 var(--font-figtree),sans-serif",
  cursor: "pointer",
};

const tableHeadStyle: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "minmax(220px,1fr) 76px 96px 76px 92px 32px",
  gap: 12,
  padding: "0 14px 10px",
  borderBottom: "1px solid var(--nova-border)",
  font: "600 11px/1.3 var(--font-figtree),sans-serif",
  letterSpacing: ".04em",
  textTransform: "uppercase",
  color: "var(--nova-ink-faint)",
};

const rowStyle: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "minmax(220px,1fr) 76px 96px 76px 92px 32px",
  gap: 12,
  alignItems: "center",
  padding: "13px 14px",
  borderBottom: "1px solid var(--nova-border)",
};

const cellTitleStyle: React.CSSProperties = {
  font: "500 14px/1.4 var(--font-figtree),sans-serif",
  color: "var(--nova-ink)",
  whiteSpace: "nowrap",
  overflow: "hidden",
  textOverflow: "ellipsis",
};

const cellMutedStyle: React.CSSProperties = { font: "400 13px/1.4 var(--font-figtree),sans-serif", color: "var(--nova-ink-muted)" };

const formatBadgeStyle: React.CSSProperties = {
  font: "600 11px/1.3 var(--font-figtree),sans-serif",
  color: "var(--nova-ink-muted)",
  padding: "2px 8px",
  border: "1px solid var(--nova-border)",
  borderRadius: 6,
  width: "fit-content",
  textTransform: "capitalize",
};

const deleteBtnStyle: React.CSSProperties = { border: "none", background: "transparent", color: "var(--nova-ink-faint)", cursor: "pointer", padding: 5, borderRadius: 6, display: "flex" };
const deleteConfirmBtnStyle: React.CSSProperties = { border: "none", background: "var(--nova-danger)", color: "#fff", font: "600 11px/1.2 var(--font-figtree),sans-serif", padding: "5px 9px", borderRadius: 6, cursor: "pointer" };
const deleteCancelBtnStyle: React.CSSProperties = { border: "1px solid var(--nova-border)", background: "transparent", color: "var(--nova-ink-muted)", font: "600 11px/1.2 var(--font-figtree),sans-serif", padding: "5px 9px", borderRadius: 6, cursor: "pointer" };

const overlayStyle: React.CSSProperties = { position: "fixed", inset: 0, background: "rgba(28,26,23,0.45)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 50 };
const modalStyle: React.CSSProperties = { width: 420, background: "var(--nova-surface)", borderRadius: 16, border: "1px solid var(--nova-border)", padding: 28, boxShadow: "0 20px 48px rgba(0,0,0,0.2)" };
const fieldLabelStyle: React.CSSProperties = { display: "block", font: "600 12px/1.4 var(--font-figtree),sans-serif", color: "var(--nova-ink)", marginBottom: 6, marginTop: 16 };
const inputStyle: React.CSSProperties = { width: "100%", padding: "10px 12px", borderRadius: 8, border: "1px solid var(--nova-border)", background: "var(--nova-input-bg)", color: "var(--nova-ink)", font: "400 13.5px/1.4 var(--font-figtree),sans-serif", outline: "none" };
const secondaryBtnStyle: React.CSSProperties = { padding: "8px 15px", borderRadius: 8, border: "1px solid var(--nova-border)", background: "transparent", color: "var(--nova-ink)", font: "600 13px/1.2 var(--font-figtree),sans-serif", cursor: "pointer" };
const primaryBtnStyle: React.CSSProperties = { padding: "8px 15px", borderRadius: 8, border: "none", background: "var(--nova-accent)", color: "#fff", font: "600 13px/1.2 var(--font-figtree),sans-serif", cursor: "pointer" };

import { CSSProperties } from "react";

/** The one modal convention in the app (originally local to
 * DocumentsView.tsx's upload form) - a dim fixed overlay + a centered
 * card. Shared here so the document-preview modal follows the same
 * pattern instead of inventing a second one. */
export const overlayStyle: CSSProperties = {
  position: "fixed",
  inset: 0,
  background: "rgba(28,26,23,0.45)",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  zIndex: 50,
};

export const uploadModalStyle: CSSProperties = {
  width: "min(420px, calc(100vw - 32px))",
  maxHeight: "calc(100vh - 32px)",
  overflowY: "auto",
  background: "var(--nova-surface)",
  borderRadius: 16,
  border: "1px solid var(--nova-border)",
  padding: 28,
  boxShadow: "0 20px 48px rgba(0,0,0,0.2)",
};

/** Sized for a document body (markdown text or an embedded PDF viewer)
 * rather than a small form. */
export const previewModalStyle: CSSProperties = {
  width: "min(820px, calc(100vw - 48px))",
  height: "min(85vh, 720px)",
  display: "flex",
  flexDirection: "column",
  background: "var(--nova-surface)",
  borderRadius: 16,
  border: "1px solid var(--nova-border)",
  boxShadow: "0 20px 48px rgba(0,0,0,0.2)",
  overflow: "hidden",
};

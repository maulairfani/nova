export function AccountMenu({
  open,
  onOpenSettings,
  onLogout,
  align = "left",
}: {
  open: boolean;
  onOpenSettings: () => void;
  onLogout: () => void;
  align?: "left" | "right";
}) {
  if (!open) return null;
  return (
    <div
      style={{
        position: "absolute",
        [align === "left" ? "left" : "right"]: 0,
        bottom: align === "left" ? 40 : undefined,
        top: align === "right" ? 44 : undefined,
        background: "var(--nova-surface)",
        border: "1px solid var(--nova-border)",
        borderRadius: 10,
        boxShadow: "var(--nova-dropdown-shadow)",
        minWidth: 150,
        padding: 6,
        zIndex: 20,
      }}
    >
      <div
        onClick={onOpenSettings}
        style={{ padding: "9px 10px", borderRadius: 6, font: "500 13px/1.3 var(--font-figtree),sans-serif", color: "var(--nova-ink)", cursor: "pointer" }}
      >
        Settings
      </div>
      <div
        onClick={onLogout}
        style={{ padding: "9px 10px", borderRadius: 6, font: "500 13px/1.3 var(--font-figtree),sans-serif", color: "var(--nova-danger)", cursor: "pointer" }}
      >
        Log out
      </div>
    </div>
  );
}

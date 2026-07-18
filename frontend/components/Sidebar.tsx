import { useMemo, useState } from "react";
import { Conversation } from "../lib/conversations";
import { AccountMenu } from "./AccountMenu";
import { NovaMark } from "./NovaMark";

function groupLabel(updatedAt: string): string {
  const now = new Date();
  const date = new Date(updatedAt);
  const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const days = Math.floor((startOfToday.getTime() - new Date(date.getFullYear(), date.getMonth(), date.getDate()).getTime()) / 86400000);
  if (days <= 0) return "Today";
  if (days === 1) return "Yesterday";
  if (days <= 7) return "Previous 7 days";
  return "Older";
}

const GROUP_ORDER = ["Today", "Yesterday", "Previous 7 days", "Older"];

export function Sidebar({
  collapsed,
  onToggleCollapse,
  mobileOpen,
  onCloseMobile,
  hiddenForA11y,
  conversations,
  loading,
  activeConvId,
  onSelect,
  onNewChat,
  onRename,
  onDelete,
  displayName,
  unitLabel,
  onOpenSettings,
  onOpenDocuments,
  isDocumentsActive,
  onLogout,
}: {
  collapsed: boolean;
  onToggleCollapse: () => void;
  mobileOpen: boolean;
  onCloseMobile: () => void;
  hiddenForA11y: boolean;
  conversations: Conversation[];
  loading: boolean;
  activeConvId: string | null;
  onSelect: (id: string) => void;
  onNewChat: () => void;
  onRename: (id: string, title: string) => void;
  onDelete: (id: string) => void;
  displayName: string;
  unitLabel: string;
  onOpenSettings: () => void;
  onOpenDocuments: () => void;
  isDocumentsActive: boolean;
  onLogout: () => void;
}) {
  const [searchQuery, setSearchQuery] = useState("");
  const [menuOpenId, setMenuOpenId] = useState<string | null>(null);
  const [renamingId, setRenamingId] = useState<string | null>(null);
  const [renameValue, setRenameValue] = useState("");
  const [accountMenuOpen, setAccountMenuOpen] = useState(false);

  const groups = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    const filtered = conversations.filter((c) => !q || c.title.toLowerCase().includes(q));
    return GROUP_ORDER.map((name) => ({
      name,
      items: filtered.filter((c) => groupLabel(c.updated_at) === name),
    })).filter((g) => g.items.length > 0);
  }, [conversations, searchQuery]);

  const commitRename = () => {
    if (!renamingId) return;
    onRename(renamingId, renameValue.trim() || "Untitled conversation");
    setRenamingId(null);
  };

  const initials = displayName
    .split(" ")
    .map((p) => p[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();

  const sidebarClassName = [
    "nova-sidebar",
    collapsed && "nova-sidebar--collapsed",
    mobileOpen && "nova-sidebar--mobile-open",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <aside
      className={sidebarClassName}
      inert={hiddenForA11y}
      aria-hidden={hiddenForA11y}
      style={{
        flex: "none",
        display: "flex",
        flexDirection: "column",
        background: "var(--nova-surface-2)",
        borderRight: "1px solid var(--nova-border)",
        height: "100vh",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "18px 16px 14px" }}>
        <NovaMark size={19} />
        <button onClick={onToggleCollapse} aria-label="Collapse sidebar" title="Collapse sidebar" className="nova-icon-btn nova-desktop-only" style={iconBtnStyle}>
          <CollapseIcon />
        </button>
        <button onClick={onCloseMobile} aria-label="Close sidebar" title="Close sidebar" className="nova-icon-btn nova-mobile-only" style={iconBtnStyle}>
          <CloseIcon />
        </button>
      </div>

      <div style={{ padding: "0 12px 12px", display: "flex", flexDirection: "column", gap: 6 }}>
        <button onClick={onNewChat} style={newChatBtnStyle}>
          <PlusIcon />
          New chat
        </button>
        <button onClick={onOpenDocuments} style={docNavBtnStyle(isDocumentsActive)}>
          <DocumentIcon />
          Manage documents
        </button>
      </div>

      <div style={{ padding: "0 12px 10px" }}>
        <div style={searchWrapStyle}>
          <SearchIcon />
          <input
            placeholder="Search conversations"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={searchInputStyle}
          />
        </div>
      </div>

      <div style={{ flex: 1, overflowY: "auto", padding: "2px 12px 8px" }} onClick={() => setMenuOpenId(null)}>
        {loading && (
          <div>
            {[0, 1, 2, 3, 4, 5].map((i) => (
              <div key={i} style={skeletonRowStyle} />
            ))}
          </div>
        )}

        {!loading &&
          groups.map((group) => (
            <div key={group.name} style={{ marginTop: 14 }}>
              <div style={groupLabelStyle}>{group.name}</div>
              {group.items.map((conv) => {
                const isActive = conv.id === activeConvId;
                const isRenaming = renamingId === conv.id;
                return (
                  <div
                    key={conv.id}
                    onClick={isRenaming ? undefined : () => onSelect(conv.id)}
                    style={{
                      position: "relative",
                      display: "flex",
                      alignItems: "center",
                      gap: 6,
                      padding: "8px 10px",
                      borderRadius: 8,
                      cursor: "pointer",
                      background: isActive ? "var(--nova-accent-soft)" : "transparent",
                      marginBottom: 2,
                    }}
                  >
                    {isRenaming ? (
                      <input
                        value={renameValue}
                        onChange={(e) => setRenameValue(e.target.value)}
                        onBlur={commitRename}
                        onKeyDown={(e) => {
                          if (e.key === "Enter") commitRename();
                          if (e.key === "Escape") setRenamingId(null);
                        }}
                        onClick={(e) => e.stopPropagation()}
                        autoFocus
                        style={renameInputStyle}
                      />
                    ) : (
                      <>
                        <div
                          style={{
                            flex: 1,
                            minWidth: 0,
                            whiteSpace: "nowrap",
                            overflow: "hidden",
                            textOverflow: "ellipsis",
                            font: `${isActive ? 600 : 400} 13.5px/1.4 var(--font-figtree),sans-serif`,
                            color: "var(--nova-ink)",
                          }}
                        >
                          {conv.title}
                        </div>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setMenuOpenId(menuOpenId === conv.id ? null : conv.id);
                          }}
                          aria-label="Conversation options"
                          style={{ flex: "none", border: "none", background: "transparent", color: "var(--nova-ink-muted)", cursor: "pointer", padding: 3, borderRadius: 5, display: "flex" }}
                        >
                          <DotsIcon />
                        </button>
                        {menuOpenId === conv.id && (
                          <div onClick={(e) => e.stopPropagation()} style={dropdownStyle}>
                            <div
                              onClick={() => {
                                setRenamingId(conv.id);
                                setRenameValue(conv.title);
                                setMenuOpenId(null);
                              }}
                              style={dropdownItemStyle}
                            >
                              Rename
                            </div>
                            <div onClick={() => onDelete(conv.id)} style={{ ...dropdownItemStyle, color: "var(--nova-danger)" }}>
                              Delete
                            </div>
                          </div>
                        )}
                      </>
                    )}
                  </div>
                );
              })}
            </div>
          ))}

        {!loading && groups.length === 0 && (
          <div style={{ font: "400 13px/1.5 var(--font-figtree),sans-serif", color: "var(--nova-ink-muted)", padding: "16px 4px" }}>
            {searchQuery ? `No conversations match "${searchQuery}".` : "No conversations yet."}
          </div>
        )}
      </div>

      <div style={{ padding: "14px 12px", borderTop: "1px solid var(--nova-border)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, position: "relative" }}>
          <div style={avatarStyle}>{initials}</div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ font: "600 13.5px/1.3 var(--font-figtree),sans-serif", color: "var(--nova-ink)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
              {displayName}
            </div>
            <div style={{ font: "400 12px/1.3 var(--font-figtree),sans-serif", color: "var(--nova-ink-muted)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
              {unitLabel}
            </div>
          </div>
          <button onClick={() => setAccountMenuOpen((v) => !v)} aria-label="Account menu" className="nova-icon-btn" style={iconBtnStyle}>
            <ChevronUpIcon />
          </button>
          <AccountMenu
            open={accountMenuOpen}
            onOpenSettings={() => {
              setAccountMenuOpen(false);
              onOpenSettings();
            }}
            onLogout={onLogout}
          />
        </div>
      </div>
    </aside>
  );
}

const iconBtnStyle: React.CSSProperties = {
  border: "none",
  background: "transparent",
  color: "var(--nova-ink-muted)",
  cursor: "pointer",
  padding: 7,
  borderRadius: 7,
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
};

function docNavBtnStyle(active: boolean): React.CSSProperties {
  return {
    width: "100%",
    display: "flex",
    alignItems: "center",
    gap: 8,
    padding: "9px 12px",
    borderRadius: 9,
    border: "none",
    background: active ? "var(--nova-accent-soft)" : "transparent",
    color: active ? "var(--nova-accent)" : "var(--nova-ink-muted)",
    font: "600 13.5px/1.3 var(--font-figtree),sans-serif",
    cursor: "pointer",
  };
}

const newChatBtnStyle: React.CSSProperties = {
  width: "100%",
  display: "flex",
  alignItems: "center",
  gap: 8,
  padding: "9px 12px",
  borderRadius: 9,
  border: "1px solid var(--nova-border)",
  background: "var(--nova-surface)",
  color: "var(--nova-ink)",
  font: "600 13.5px/1.3 var(--font-figtree),sans-serif",
  cursor: "pointer",
};

const searchWrapStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 8,
  padding: "8px 10px",
  borderRadius: 9,
  background: "var(--nova-surface)",
  border: "1px solid var(--nova-border)",
};

const searchInputStyle: React.CSSProperties = {
  border: "none",
  outline: "none",
  background: "transparent",
  flex: 1,
  font: "400 13.5px/1.3 var(--font-figtree),sans-serif",
  color: "var(--nova-ink)",
  minWidth: 0,
};

const groupLabelStyle: React.CSSProperties = {
  font: "600 11px/1.4 var(--font-figtree),sans-serif",
  letterSpacing: ".06em",
  textTransform: "uppercase",
  color: "var(--nova-ink-faint)",
  padding: "4px 8px 6px",
};

const skeletonRowStyle: React.CSSProperties = {
  height: 30,
  borderRadius: 8,
  marginBottom: 6,
  background: "linear-gradient(90deg, var(--nova-surface-2) 25%, var(--nova-hover) 37%, var(--nova-surface-2) 63%)",
  backgroundSize: "400px 100%",
  animation: "nova-shimmer 1.4s ease-in-out infinite",
};

const dropdownStyle: React.CSSProperties = {
  position: "absolute",
  top: 36,
  right: 6,
  background: "var(--nova-surface)",
  border: "1px solid var(--nova-border)",
  borderRadius: 10,
  boxShadow: "var(--nova-dropdown-shadow)",
  zIndex: 20,
  minWidth: 140,
  padding: 6,
  overflow: "hidden",
};

const dropdownItemStyle: React.CSSProperties = {
  padding: "9px 10px",
  borderRadius: 6,
  font: "500 13px/1.3 var(--font-figtree),sans-serif",
  color: "var(--nova-ink)",
  cursor: "pointer",
};

const renameInputStyle: React.CSSProperties = {
  flex: 1,
  padding: "4px 6px",
  borderRadius: 6,
  border: "1px solid var(--nova-ring)",
  outline: "none",
  font: "600 13.5px/1.4 var(--font-figtree),sans-serif",
  color: "var(--nova-ink)",
  background: "var(--nova-surface)",
};

const avatarStyle: React.CSSProperties = {
  width: 32,
  height: 32,
  borderRadius: "50%",
  background: "var(--nova-accent-soft)",
  color: "var(--nova-accent)",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  font: "600 12.5px/1 var(--font-figtree),sans-serif",
  flex: "none",
};

function CollapseIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <rect x="1" y="2" width="14" height="12" rx="2" stroke="currentColor" strokeWidth="1.4" />
      <line x1="6" y1="2" x2="6" y2="14" stroke="currentColor" strokeWidth="1.4" />
    </svg>
  );
}

function CloseIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <line x1="3" y1="3" x2="13" y2="13" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
      <line x1="13" y1="3" x2="3" y2="13" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  );
}

function PlusIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 16 16" fill="none">
      <line x1="8" y1="2" x2="8" y2="14" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
      <line x1="2" y1="8" x2="14" y2="8" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  );
}

function SearchIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 16 16" fill="none" style={{ flex: "none", color: "var(--nova-ink-muted)" }}>
      <circle cx="7" cy="7" r="5" stroke="currentColor" strokeWidth="1.4" />
      <line x1="11" y1="11" x2="14.5" y2="14.5" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
    </svg>
  );
}

function DotsIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor">
      <circle cx="3" cy="8" r="1.4" />
      <circle cx="8" cy="8" r="1.4" />
      <circle cx="13" cy="8" r="1.4" />
    </svg>
  );
}

function DocumentIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 16 16" fill="none">
      <path d="M4 1.5h6l3 3v10a1 1 0 01-1 1H4a1 1 0 01-1-1v-12a1 1 0 011-1z" stroke="currentColor" strokeWidth="1.3" strokeLinejoin="round" />
      <path d="M6 8.5h5M6 11h5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
    </svg>
  );
}

function ChevronUpIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
      <path d="M4 6l4 4 4-4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

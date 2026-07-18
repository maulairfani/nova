import { Theme } from "../lib/theme";
import { formatCountdown, UsageStatus } from "../lib/usage";

export function SettingsView({
  displayName,
  email,
  unitLabel,
  theme,
  onToggleTheme,
  onLogout,
  usage,
  usageError,
  remainingSeconds,
}: {
  displayName: string;
  email: string;
  unitLabel: string;
  theme: Theme;
  onToggleTheme: () => void;
  onLogout: () => void;
  usage: UsageStatus | null;
  usageError: boolean;
  remainingSeconds: number;
}) {
  const dark = theme === "dark";
  const atLimit = !!usage && usage.remaining <= 0;
  return (
    <div style={{ flex: 1, overflowY: "auto", display: "flex", justifyContent: "center", padding: "36px 24px" }}>
      <div style={{ maxWidth: 600, width: "100%" }}>
        <div className="nova-serif" style={{ fontSize: 26, fontWeight: 600, color: "var(--nova-ink)", marginBottom: 6 }}>
          Settings
        </div>
        <div style={{ font: "400 14.5px/1.6 var(--font-figtree),sans-serif", color: "var(--nova-ink-muted)", marginBottom: 32 }}>
          Manage your Nova account and preferences.
        </div>

        <div style={sectionStyle}>
          <div style={sectionTitleStyle}>Profile</div>
          <div style={rowStyle}>
            <span style={labelStyle}>Display name</span>
            <span style={valueStyle}>{displayName}</span>
          </div>
          <div style={rowStyle}>
            <span style={labelStyle}>Email</span>
            <span style={valueStyle}>{email}</span>
          </div>
          <div style={rowStyleLast}>
            <span style={labelStyle}>Business unit access</span>
            <span style={valueStyle}>{unitLabel}</span>
          </div>
        </div>

        <div style={sectionStyle}>
          <div style={sectionTitleStyle}>Chat usage</div>
          <div style={{ padding: "4px 0 16px" }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
              <span style={labelStyle}>Messages used</span>
              <span style={valueStyle}>{usage ? `${usage.used} / ${usage.limit}` : "—"}</span>
            </div>
            <div style={{ height: 8, borderRadius: 999, background: "var(--nova-border)", overflow: "hidden" }}>
              <div
                style={{
                  height: "100%",
                  width: `${usage ? Math.min(100, (usage.used / usage.limit) * 100) : 0}%`,
                  background: atLimit ? "var(--nova-danger)" : "var(--nova-accent)",
                  transition: "width .3s ease",
                }}
              />
            </div>
            <div
              style={{
                marginTop: 8,
                font: "400 12.5px/1.4 var(--font-figtree),sans-serif",
                color: atLimit ? "var(--nova-danger)" : "var(--nova-ink-muted)",
              }}
            >
              {!usage
                ? usageError
                  ? "Unable to load usage right now."
                  : "Loading…"
                : atLimit
                  ? `Limit reached — resets in ${formatCountdown(remainingSeconds)}`
                  : usage.used === 0
                    ? `${usage.limit} messages available every 5 hours`
                    : `${usage.remaining} message${usage.remaining === 1 ? "" : "s"} remaining · resets in ${formatCountdown(remainingSeconds)}`}
            </div>
          </div>
        </div>

        <div style={sectionStyle}>
          <div style={sectionTitleStyle}>Appearance</div>
          <div style={rowStyleLast}>
            <span style={labelStyle}>Theme</span>
            <div
              onClick={onToggleTheme}
              role="switch"
              aria-checked={dark}
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") onToggleTheme();
              }}
              style={{
                width: 44,
                height: 25,
                borderRadius: 13,
                background: dark ? "var(--nova-accent)" : "var(--nova-border)",
                position: "relative",
                cursor: "pointer",
                transition: "background .15s",
              }}
            >
              <div
                style={{
                  width: 19,
                  height: 19,
                  borderRadius: "50%",
                  background: "#fff",
                  position: "absolute",
                  top: 3,
                  left: dark ? 22 : 3,
                  transition: "left .15s",
                  boxShadow: "0 1px 3px rgba(0,0,0,0.25)",
                }}
              />
            </div>
          </div>
        </div>

        <div style={sectionStyle}>
          <div style={sectionTitleStyle}>Session</div>
          <div style={rowStyleLast}>
            <span style={labelStyle}>Signed in as {displayName}</span>
            <button onClick={onLogout} style={secondaryBtnStyle}>
              Log out
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

const sectionStyle: React.CSSProperties = {
  border: "1px solid var(--nova-border)",
  borderRadius: 14,
  background: "var(--nova-surface)",
  marginBottom: 18,
  padding: "4px 20px",
};

const sectionTitleStyle: React.CSSProperties = {
  font: "600 13px/1.3 var(--font-figtree),sans-serif",
  letterSpacing: ".03em",
  textTransform: "uppercase",
  color: "var(--nova-ink-faint)",
  padding: "16px 0 10px",
};

const rowStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  padding: "13px 0",
  borderBottom: "1px solid var(--nova-border)",
};

const rowStyleLast: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  padding: "13px 0",
};

const labelStyle: React.CSSProperties = { font: "400 14px/1.4 var(--font-figtree),sans-serif", color: "var(--nova-ink-muted)" };
const valueStyle: React.CSSProperties = { font: "500 14px/1.4 var(--font-figtree),sans-serif", color: "var(--nova-ink)" };

const secondaryBtnStyle: React.CSSProperties = {
  padding: "8px 15px",
  borderRadius: 8,
  border: "1px solid var(--nova-border)",
  background: "transparent",
  color: "var(--nova-ink)",
  font: "600 13px/1.2 var(--font-figtree),sans-serif",
  cursor: "pointer",
};

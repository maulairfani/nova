"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { login } from "../../lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !password.trim()) {
      setError("Enter your email and password to continue.");
      return;
    }
    setError(null);
    setBusy(true);
    try {
      await login(email, password);
      router.push("/");
    } catch {
      setError("Invalid email or password.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="nova-login-root" style={{ minHeight: "100vh" }}>
      <div
        className="nova-login-brand"
        style={{
          background: "var(--nova-login-panel-bg)",
          color: "#f7f5f2",
          display: "flex",
          flexDirection: "column",
        }}
      >
        <div style={{ font: "600 11px/1 var(--font-figtree),sans-serif", letterSpacing: ".16em", color: "rgba(247,245,242,0.7)", textTransform: "uppercase" }}>
          MCN Group
        </div>
        <div
          className="nova-serif nova-login-heading"
          style={{ fontStyle: "italic", fontWeight: 600, lineHeight: 1.05, color: "#f7f5f2", marginTop: 18, display: "flex", alignItems: "center", gap: 12 }}
        >
          <span style={{ width: 14, height: 14, borderRadius: 3, background: "var(--nova-accent)", display: "inline-block", transform: "rotate(8deg)" }} />
          Nova
        </div>
        <div style={{ font: "400 15px/1.6 var(--font-figtree),sans-serif", color: "rgba(247,245,242,0.7)", marginTop: 14, maxWidth: 320 }}>
          Internal AI assistant for MCN Group — grounded in your business unit&apos;s knowledge base, live data, and the web.
        </div>
        <div className="nova-login-tagline" style={{ font: "400 12.5px/1.5 var(--font-figtree),sans-serif", color: "rgba(247,245,242,0.45)" }}>
          Free-to-Air TV · Streaming &amp; Short-Form · Digital News
        </div>
      </div>

      <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", padding: 24 }}>
        <form
          onSubmit={handleSubmit}
          style={{
            width: "100%",
            maxWidth: 380,
            background: "var(--nova-surface)",
            border: "1px solid var(--nova-border)",
            borderRadius: 16,
            padding: 36,
            boxShadow: "var(--nova-shadow)",
          }}
        >
          <div className="nova-serif" style={{ fontWeight: 600, fontSize: 22, lineHeight: 1.2, color: "var(--nova-ink)" }}>
            Sign in to Nova
          </div>
          <div style={{ font: "400 14px/1.5 var(--font-figtree),sans-serif", color: "var(--nova-ink-muted)", marginTop: 6, marginBottom: 28 }}>
            Use your MCN Group employee account.
          </div>

          <label style={labelStyle}>Email</label>
          <input
            type="email"
            placeholder="andi.wijaya@mcngroup.id"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            style={inputStyle}
          />

          <label style={{ ...labelStyle, marginTop: 18 }}>Password</label>
          <input
            type="password"
            placeholder="••••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            style={inputStyle}
          />

          {error && (
            <div style={{ font: "500 13px/1.5 var(--font-figtree),sans-serif", color: "var(--nova-danger)", marginTop: 14 }}>{error}</div>
          )}

          <button type="submit" disabled={busy} style={primaryBtnStyle}>
            {busy ? "Signing in…" : "Sign in"}
          </button>
          <div style={{ font: "400 12.5px/1.5 var(--font-figtree),sans-serif", color: "var(--nova-ink-muted)", marginTop: 18, textAlign: "center" }}>
            Trouble signing in? Contact IT Service Desk.
          </div>
        </form>
      </div>
    </div>
  );
}

const labelStyle: React.CSSProperties = {
  display: "block",
  font: "600 12.5px/1.4 var(--font-figtree),sans-serif",
  color: "var(--nova-ink)",
  marginBottom: 6,
};

const inputStyle: React.CSSProperties = {
  width: "100%",
  padding: "11px 13px",
  borderRadius: 9,
  border: "1px solid var(--nova-border)",
  background: "var(--nova-input-bg)",
  color: "var(--nova-ink)",
  font: "400 14.5px/1.4 var(--font-figtree),sans-serif",
  outline: "none",
};

const primaryBtnStyle: React.CSSProperties = {
  width: "100%",
  marginTop: 22,
  padding: 12,
  borderRadius: 9,
  border: "none",
  background: "var(--nova-accent)",
  color: "#fff",
  font: "600 14.5px/1.2 var(--font-figtree),sans-serif",
  cursor: "pointer",
};

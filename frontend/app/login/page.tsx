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
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        height: "100vh",
        maxWidth: 360,
        margin: "0 auto",
        padding: "0 20px",
      }}
    >
      <div style={{ fontSize: 20, fontWeight: 700, marginBottom: 4 }}>Nova</div>
      <div style={{ fontSize: 13, color: "var(--nova-ink-muted)", marginBottom: 28 }}>
        MCN Group internal assistant
      </div>

      <form onSubmit={handleSubmit} style={{ width: "100%", display: "flex", flexDirection: "column", gap: 12 }}>
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          style={{
            padding: "10px 12px",
            borderRadius: 8,
            border: "1px solid var(--nova-border)",
            fontSize: 14,
          }}
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          style={{
            padding: "10px 12px",
            borderRadius: 8,
            border: "1px solid var(--nova-border)",
            fontSize: 14,
          }}
        />
        {error && <div style={{ color: "#c0392b", fontSize: 13 }}>{error}</div>}
        <button
          type="submit"
          disabled={busy}
          style={{
            padding: "10px 12px",
            borderRadius: 8,
            border: "none",
            background: "#111",
            color: "#fff",
            fontSize: 14,
            fontWeight: 600,
            cursor: busy ? "not-allowed" : "pointer",
          }}
        >
          {busy ? "Signing in…" : "Sign in"}
        </button>
      </form>
    </div>
  );
}

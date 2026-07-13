const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
const TOKEN_KEY = "nova_token";

export interface TokenClaims {
  sub: string;
  email: string;
  display_name: string;
  business_units: { code: string; role: string }[];
  exp: number;
}

export async function login(email: string, password: string): Promise<void> {
  const response = await fetch(`${BACKEND_URL}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!response.ok) {
    throw new Error("Invalid email or password.");
  }
  const { access_token } = await response.json();
  localStorage.setItem(TOKEN_KEY, access_token);
}

export function logout(): void {
  localStorage.removeItem(TOKEN_KEY);
}

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

/** Decodes the JWT payload client-side for display purposes only (which
 * business units/roles to show) — the backend is what actually verifies
 * the signature on every request (ADR-0021, api/v1/deps.py). */
export function getClaims(): TokenClaims | null {
  const token = getToken();
  if (!token) return null;
  try {
    const payload = token.split(".")[1];
    const claims = JSON.parse(atob(payload.replace(/-/g, "+").replace(/_/g, "/"))) as TokenClaims;
    if (claims.exp * 1000 < Date.now()) {
      logout();
      return null;
    }
    return claims;
  } catch {
    logout();
    return null;
  }
}

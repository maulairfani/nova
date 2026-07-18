const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

/** Shared fetch wrapper for endpoints needing the caller's JWT - every
 * lib/*.ts client takes an explicit token argument rather than reading
 * one internally, so this does too. Throws on a non-OK response instead
 * of returning it, matching listDocuments/deleteDocument's convention. */
export async function authenticatedFetch(path: string, token: string): Promise<Response> {
  const response = await fetch(`${BACKEND_URL}${path}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) throw new Error(`Request failed: ${response.status}`);
  return response;
}

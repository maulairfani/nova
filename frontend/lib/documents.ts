const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export interface DocumentItem {
  id: string;
  business_unit_code: string;
  title: string;
  format: string;
  status: "pending" | "ingested" | "failed";
  chunk_count: number | null;
  error_message: string | null;
  created_at: string;
  ingested_at: string | null;
}

export async function listDocuments(token: string, businessUnit: string): Promise<DocumentItem[]> {
  const response = await fetch(`${BACKEND_URL}/api/v1/documents?business_unit=${encodeURIComponent(businessUnit)}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) throw new Error(`Failed to load documents: ${response.status}`);
  return response.json();
}

export async function uploadDocument(
  token: string,
  businessUnit: string,
  file: File,
  title: string
): Promise<DocumentItem> {
  const form = new FormData();
  form.append("business_unit", businessUnit);
  form.append("title", title);
  form.append("file", file);
  const response = await fetch(`${BACKEND_URL}/api/v1/documents`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: form,
  });
  if (!response.ok) {
    const detail = await response.json().then((body) => body.detail, () => null);
    throw new Error(typeof detail === "string" ? detail : `Upload failed (${response.status}). Please try again.`);
  }
  return response.json();
}

export async function deleteDocument(token: string, id: string): Promise<void> {
  const response = await fetch(`${BACKEND_URL}/api/v1/documents/${id}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) throw new Error(`Delete failed: ${response.status}`);
}

/** Resolves a kb citation's (unit, source_document) back to its real
 * Document row (Sources panel's "View document") - null on 404 (e.g. the
 * document was since deleted), so the caller can just hide the action
 * rather than surface an error for something this minor. */
export async function findDocumentByObjectKey(
  token: string,
  businessUnit: string,
  objectKey: string
): Promise<DocumentItem | null> {
  const response = await fetch(
    `${BACKEND_URL}/api/v1/documents/lookup?business_unit=${encodeURIComponent(businessUnit)}&object_key=${encodeURIComponent(objectKey)}`,
    { headers: { Authorization: `Bearer ${token}` } }
  );
  if (response.status === 404) return null;
  if (!response.ok) throw new Error(`Lookup failed: ${response.status}`);
  return response.json();
}

import { useEffect, useState } from "react";
import { authenticatedFetch } from "./authenticatedFetch";
import { getToken } from "./auth";

/** Fetches `path` (an authenticated, binary-ish endpoint - a chart image,
 * a PDF document) as a Blob and exposes it as an object URL a plain
 * <img>/<iframe> can point at - those tags can't carry an Authorization
 * header, so this is the one place that gap gets bridged. Revokes the
 * previous object URL on path change/unmount so blob URLs don't leak. */
export function useBlobUrl(path: string | null): { url: string | null; loading: boolean; error: boolean } {
  const [url, setUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (!path) {
      setUrl(null);
      return;
    }
    const token = getToken();
    if (!token) {
      setError(true);
      return;
    }

    let objectUrl: string | null = null;
    let cancelled = false;

    setLoading(true);
    setError(false);
    authenticatedFetch(path, token)
      .then((response) => response.blob())
      .then((blob) => {
        if (cancelled) return;
        objectUrl = URL.createObjectURL(blob);
        setUrl(objectUrl);
      })
      .catch(() => {
        if (!cancelled) setError(true);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [path]);

  return { url, loading, error };
}

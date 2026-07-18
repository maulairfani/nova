import { useEffect, useState } from "react";

/**
 * SSR-safe media query hook. Returns false on the server and on the very
 * first client render, then syncs via matchMedia + its `change` event (so
 * resizes/orientation changes are reflected live, not just read once).
 *
 * Known trade-off: on an actual narrow device there is one paint where
 * this returns false ("desktop") before the mount effect corrects it —
 * the standard, accepted trade-off for this pattern; avoiding it would
 * require blocking first paint on a client-only value, which reintroduces
 * hydration mismatches instead.
 */
export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(false);

  useEffect(() => {
    const mql = window.matchMedia(query);
    setMatches(mql.matches);
    const handler = (e: MediaQueryListEvent) => setMatches(e.matches);
    mql.addEventListener("change", handler);
    return () => mql.removeEventListener("change", handler);
  }, [query]);

  return matches;
}

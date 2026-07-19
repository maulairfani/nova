"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { getClaims, getToken, logout as clearToken, TokenClaims } from "../lib/auth";
import { BP_SHELL_MAX } from "../lib/breakpoints";
import { useMediaQuery } from "../lib/useMediaQuery";
import {
  Conversation,
  ConversationNotFoundError,
  deleteConversation,
  getConversationMessages,
  listConversations,
  renameConversation,
} from "../lib/conversations";
import { BUSINESS_UNIT_LABELS } from "../lib/businessUnits";
import { ChartStep, Citation, RateLimitedError, streamChat, UnauthorizedError } from "../lib/streamChat";
import { applyTheme, getStoredTheme, Theme } from "../lib/theme";
import { formatCountdown, getUsage, UsageStatus } from "../lib/usage";
import { ChatInput, FeatureKey } from "./ChatInput";
import { DocumentsView } from "./DocumentsView";
import { Message, MessageBubble } from "./MessageBubble";
import { NovaMark } from "./NovaMark";
import { SettingsView } from "./SettingsView";
import { Sidebar } from "./Sidebar";
import { SourcesPanel } from "./SourcesPanel";
import { LiveStepData } from "./ToolSteps";

function newThreadId(): string {
  return crypto.randomUUID();
}

function conversationTitle(text: string): string {
  return text.length > 42 ? text.slice(0, 42) + "…" : text;
}

const STARTER_PROMPTS = [
  "What's our SOP for content takedown requests?",
  "Show me this month's viewership for MCN TV",
  "How do I request press credentials for an event?",
  "Summarize last week's ad sales performance",
];

type View = "empty" | "active" | "settings" | "documents";

export function ChatWindow() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const conversationIdFromUrl = searchParams.get("c");
  const [claims, setClaims] = useState<TokenClaims | null>(null);
  const [theme, setTheme] = useState<Theme>("light");
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const isMobileShell = useMediaQuery(`(max-width: ${BP_SHELL_MAX}px)`);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [conversationsLoading, setConversationsLoading] = useState(true);
  const [activeConvId, setActiveConvId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [view, setView] = useState<View>("empty");
  const [busy, setBusy] = useState(false);
  const [liveSteps, setLiveSteps] = useState<LiveStepData[]>([]);
  const [liveCharts, setLiveCharts] = useState<ChartStep[]>([]);
  const [liveCitations, setLiveCitations] = useState<Citation[]>([]);
  const [sourcesPanel, setSourcesPanel] = useState<{ citations: Citation[]; highlightIndex?: number } | null>(null);
  const [composeRequest, setComposeRequest] = useState<{ text: string; nonce: number } | null>(null);
  const composeNonceRef = useRef(0);
  const [usage, setUsage] = useState<UsageStatus | null>(null);
  const [usageFetchedAt, setUsageFetchedAt] = useState(0);
  const [usageError, setUsageError] = useState(false);
  const [nowTick, setNowTick] = useState(Date.now());
  const threadIdRef = useRef<string>(newThreadId());
  const liveStepsRef = useRef<LiveStepData[]>([]);
  const liveChartsRef = useRef<ChartStep[]>([]);
  const liveCitationsRef = useRef<Citation[]>([]);
  const loadedConvIdRef = useRef<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const c = getClaims();
    if (!c) {
      router.replace("/login");
      return;
    }
    setClaims(c);
    setTheme(getStoredTheme());
  }, [router]);

  useEffect(() => {
    applyTheme(theme);
  }, [theme]);

  useEffect(() => {
    const token = getToken();
    if (!token || !claims) return;
    listConversations(token)
      .then(setConversations)
      .catch(() => {})
      .finally(() => setConversationsLoading(false));
  }, [claims]);

  const refreshUsage = async () => {
    const token = getToken();
    if (!token) return;
    try {
      const status = await getUsage(token);
      setUsage(status);
      setUsageFetchedAt(Date.now());
      setUsageError(false);
    } catch {
      setUsageError(true);
    }
  };

  // ADR-0027 chat rate limit: a fresh snapshot on login and every time
  // Settings is opened, so the progress bar never shows stale data.
  useEffect(() => {
    if (claims) refreshUsage();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [claims]);

  useEffect(() => {
    if (view === "settings") refreshUsage();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [view]);

  const isRateLimited = !!usage && usage.remaining <= 0;
  const remainingSeconds = usage ? Math.max(0, usage.reset_seconds - Math.floor((nowTick - usageFetchedAt) / 1000)) : 0;

  // Ticks the displayed countdown locally instead of repolling every
  // second - only runs while a countdown is actually visible somewhere.
  useEffect(() => {
    if (view !== "settings" && !isRateLimited) return;
    const id = setInterval(() => setNowTick(Date.now()), 1000);
    return () => clearInterval(id);
  }, [view, isRateLimited]);

  // Once the local countdown reaches zero while blocked, confirm with the
  // server rather than trusting the client clock - this is what re-enables
  // the composer once the real window resets.
  useEffect(() => {
    if (isRateLimited && remainingSeconds <= 0) refreshUsage();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [remainingSeconds]);

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages]);

  // Keeps the open conversation in sync with the `c` URL param — the single
  // source of truth for "which conversation is active" is the URL, not
  // component state, so a refresh lands back on the same conversation.
  // loadedConvIdRef guards against re-fetching a conversation whose id we
  // just pushed into the URL ourselves (e.g. handleSend's first message),
  // which would otherwise clobber the in-progress streamed reply.
  useEffect(() => {
    if (!claims) return;
    if (!conversationIdFromUrl) {
      if (loadedConvIdRef.current !== null) {
        loadedConvIdRef.current = null;
        threadIdRef.current = newThreadId();
        setActiveConvId(null);
        setMessages([]);
        setView((v) => (v === "settings" || v === "documents" ? v : "empty"));
      }
      return;
    }
    if (conversationIdFromUrl === loadedConvIdRef.current) return;
    loadedConvIdRef.current = conversationIdFromUrl;
    loadConversation(conversationIdFromUrl);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [claims, conversationIdFromUrl]);

  useEffect(() => {
    if (!isMobileShell) setMobileSidebarOpen(false);
  }, [isMobileShell]);

  useEffect(() => {
    document.body.style.overflow = mobileSidebarOpen ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [mobileSidebarOpen]);

  useEffect(() => {
    if (!mobileSidebarOpen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setMobileSidebarOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [mobileSidebarOpen]);

  const handleLogout = () => {
    clearToken();
    router.replace("/login");
  };

  const newChat = () => {
    loadedConvIdRef.current = null;
    threadIdRef.current = newThreadId();
    setActiveConvId(null);
    setMessages([]);
    setView("empty");
    router.push("/");
  };

  // Redirect away from a conversation id that's gone (just deleted, or a
  // dead/stale ?c=<id> visited directly) — a hard navigation, not
  // router.replace(). router.replace("/") reliably lost the race against
  // Next's own history normalization here (verified: it left the dead id
  // sitting in the address bar in both the "delete the active conversation"
  // and the "direct-navigate to a dead id" cases), which is the exact
  // "doesn't redirect" symptom this was meant to fix.
  // window.location.replace() can't lose that race since it bypasses the
  // App Router's client-side history handling entirely.
  const redirectHome = () => {
    window.location.replace("/");
  };

  const loadConversation = async (id: string) => {
    const token = getToken();
    if (!token) return;
    threadIdRef.current = id;
    setActiveConvId(id);
    setView("active");
    setMessages([]);
    try {
      const stored = await getConversationMessages(token, id);
      setMessages(stored);
    } catch (err) {
      if (err instanceof ConversationNotFoundError) {
        redirectHome();
        return;
      }
      // leave the (empty) message list — the conversation still opens
    }
  };

  const selectConversation = (id: string) => {
    router.push(`/?c=${id}`);
  };

  const handleRename = async (id: string, title: string) => {
    const token = getToken();
    if (!token) return;
    setConversations((prev) => prev.map((c) => (c.id === id ? { ...c, title } : c)));
    try {
      await renameConversation(token, id, title);
    } catch {
      // optimistic update stands; a stale title on the next full list refresh is a minor inconsistency
    }
  };

  const handleDelete = async (id: string) => {
    const token = getToken();
    if (!token) return;
    setConversations((prev) => prev.filter((c) => c.id !== id));
    if (id === activeConvId) redirectHome();
    try {
      await deleteConversation(token, id);
    } catch {
      // row is already gone from the visible list; a failed server-side delete just leaves an orphaned thread
    }
  };

  const handleSend = async (text: string, forceTools: FeatureKey[] = []) => {
    const token = getToken();
    if (!token) {
      router.replace("/login");
      return;
    }
    if (isRateLimited) return;

    const isNewConversation = activeConvId === null;
    const threadId = threadIdRef.current;

    if (isNewConversation) {
      setActiveConvId(threadId);
      loadedConvIdRef.current = threadId;
      router.push(`/?c=${threadId}`);
      setConversations((prev) => [{ id: threadId, title: conversationTitle(text), updated_at: new Date().toISOString() }, ...prev]);
    } else {
      setConversations((prev) =>
        prev
          .map((c) => (c.id === threadId ? { ...c, updated_at: new Date().toISOString() } : c))
          .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())
      );
    }

    setView("active");
    setMessages((prev) => [...prev, { role: "user", content: text }, { role: "assistant", content: "" }]);
    setBusy(true);
    liveStepsRef.current = [];
    setLiveSteps([]);
    liveChartsRef.current = [];
    setLiveCharts([]);
    liveCitationsRef.current = [];
    setLiveCitations([]);

    try {
      await streamChat({
        threadId,
        message: text,
        token,
        forceTools,
        onToken: (token) => {
          setMessages((prev) => {
            const next = [...prev];
            next[next.length - 1] = { ...next[next.length - 1], content: next[next.length - 1].content + token };
            return next;
          });
        },
        onToolStart: (step) => {
          liveStepsRef.current = [...liveStepsRef.current, { ...step, status: "active" }];
          setLiveSteps(liveStepsRef.current);
        },
        onToolEnd: (id) => {
          liveStepsRef.current = liveStepsRef.current.map((s) => (s.id === id ? { ...s, status: "done" } : s));
          setLiveSteps(liveStepsRef.current);
        },
        onChart: (chart) => {
          liveChartsRef.current = [...liveChartsRef.current, chart];
          setLiveCharts(liveChartsRef.current);
        },
        onCitations: (citations) => {
          liveCitationsRef.current = citations;
          setLiveCitations(citations);
        },
        onRateLimit: (info) => {
          setUsage({ used: info.limit - info.remaining, limit: info.limit, remaining: info.remaining, reset_seconds: info.resetSeconds });
          setUsageFetchedAt(Date.now());
        },
      });
      const finishedSteps = liveStepsRef.current.map(({ type, label }) => ({ type, label }));
      const finishedCharts = liveChartsRef.current;
      const finishedCitations = liveCitationsRef.current;
      setMessages((prev) => {
        const next = [...prev];
        next[next.length - 1] = {
          ...next[next.length - 1],
          steps: finishedSteps,
          charts: finishedCharts,
          citations: finishedCitations,
        };
        return next;
      });
    } catch (err) {
      if (err instanceof UnauthorizedError) {
        clearToken();
        router.replace("/login");
        return;
      }
      if (err instanceof RateLimitedError) {
        setUsage({
          used: err.rateLimit.limit - err.rateLimit.remaining,
          limit: err.rateLimit.limit,
          remaining: err.rateLimit.remaining,
          reset_seconds: err.rateLimit.resetSeconds,
        });
        setUsageFetchedAt(Date.now());
        setMessages((prev) => {
          const next = [...prev];
          next[next.length - 1] = { role: "assistant", content: err.message };
          return next;
        });
        return;
      }
      setMessages((prev) => {
        const next = [...prev];
        next[next.length - 1] = { role: "assistant", content: "Sorry, something went wrong reaching Nova." };
        return next;
      });
    } finally {
      setBusy(false);
      liveStepsRef.current = [];
      setLiveSteps([]);
      liveChartsRef.current = [];
      setLiveCharts([]);
      liveCitationsRef.current = [];
      setLiveCitations([]);
    }
  };

  // handleSend is recreated every render (it closes over lots of state),
  // so MessageBubble's onQuickReply must not close over it directly - that
  // would recreate the prop every render, which defeats NovaMarkdown's
  // `pre`-override memoization and silently remounts (resets) any
  // in-progress nova-multi-choice selection on the next unrelated render.
  // Routing the call through a ref keeps the callback identity stable
  // while still invoking the latest handleSend.
  const handleSendRef = useRef(handleSend);
  handleSendRef.current = handleSend;
  const handleQuickReply = useCallback((text: string) => handleSendRef.current(text), []);
  const handleComposeText = useCallback(
    (text: string) => setComposeRequest({ text, nonce: ++composeNonceRef.current }),
    []
  );
  const handleOpenSources = useCallback(
    (sourceCitations: Citation[], highlightIndex?: number) => setSourcesPanel({ citations: sourceCitations, highlightIndex }),
    []
  );

  if (!claims) return null;

  const blockedReason = isRateLimited
    ? `You've reached the limit of ${usage!.limit} messages per 5-hour window. Resets in ${formatCountdown(remainingSeconds)}.`
    : null;

  const unitLabel = claims.business_units.length
    ? claims.business_units.map((u) => BUSINESS_UNIT_LABELS[u.code] ?? u.code).join(", ")
    : "No business unit access";

  const activeConv = conversations.find((c) => c.id === activeConvId);
  const headerTitle =
    view === "active"
      ? activeConv?.title ?? "Conversation"
      : view === "settings"
        ? "Settings"
        : view === "documents"
          ? "Manage documents"
          : null;

  const accessibleUnits = claims.business_units
    .map((u) => u.code)
    .filter((code): code is "tv" | "plus" | "news" => code === "tv" || code === "plus" || code === "news");
  const isGroupAdmin = claims.business_units.some((u) => u.code === "group" && u.role === "admin");
  const documentUnits = isGroupAdmin ? (["tv", "plus", "news"] as const) : accessibleUnits;
  const canManageUnit = (unit: string) => isGroupAdmin || claims.business_units.some((u) => u.code === unit && u.role === "admin");
  const sidebarHidden = isMobileShell ? !mobileSidebarOpen : sidebarCollapsed;

  return (
    <div style={{ display: "flex", height: "100vh", width: "100%", overflow: "hidden" }}>
      <Sidebar
        collapsed={sidebarCollapsed}
        onToggleCollapse={() => setSidebarCollapsed(true)}
        mobileOpen={mobileSidebarOpen}
        onCloseMobile={() => setMobileSidebarOpen(false)}
        hiddenForA11y={sidebarHidden}
        conversations={conversations}
        loading={conversationsLoading}
        activeConvId={activeConvId}
        onSelect={(id) => {
          selectConversation(id);
          setMobileSidebarOpen(false);
        }}
        onNewChat={() => {
          newChat();
          setMobileSidebarOpen(false);
        }}
        onRename={handleRename}
        onDelete={handleDelete}
        displayName={claims.display_name}
        unitLabel={unitLabel}
        onOpenSettings={() => {
          setView("settings");
          setMobileSidebarOpen(false);
        }}
        onOpenDocuments={() => {
          setView("documents");
          setMobileSidebarOpen(false);
        }}
        isDocumentsActive={view === "documents"}
        onLogout={handleLogout}
      />
      {mobileSidebarOpen && <div className="nova-sidebar-backdrop" onClick={() => setMobileSidebarOpen(false)} />}

      <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0, background: "var(--nova-bg)" }} inert={mobileSidebarOpen}>
        <header
          className="nova-header"
          style={{
            height: 58,
            flex: "none",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            background: "var(--nova-bg)",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 12, minWidth: 0 }}>
            <button
              onClick={() => setMobileSidebarOpen((v) => !v)}
              aria-label="Toggle sidebar"
              aria-expanded={mobileSidebarOpen}
              className="nova-icon-btn nova-mobile-only"
              style={iconBtnStyle}
            >
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <line x1="2" y1="4" x2="14" y2="4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                <line x1="2" y1="8" x2="14" y2="8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                <line x1="2" y1="12" x2="14" y2="12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
              </svg>
            </button>
            {sidebarCollapsed && (
              <button onClick={() => setSidebarCollapsed(false)} aria-label="Expand sidebar" className="nova-icon-btn nova-desktop-only" style={iconBtnStyle}>
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <rect x="1" y="2" width="14" height="12" rx="2" stroke="currentColor" strokeWidth="1.4" />
                  <line x1="6" y1="2" x2="6" y2="14" stroke="currentColor" strokeWidth="1.4" />
                </svg>
              </button>
            )}
            {view === "empty" ? (sidebarHidden && <NovaMark size={18} />) : (
              <div
                style={{
                  font: "600 15px/1.3 var(--font-figtree),sans-serif",
                  color: "var(--nova-ink)",
                  whiteSpace: "nowrap",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                }}
              >
                {headerTitle}
              </div>
            )}
          </div>
        </header>

        {view === "empty" && (
          <div style={{ flex: 1, overflowY: "auto", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "32px 24px" }}>
            <div style={{ maxWidth: 640, width: "100%", textAlign: "center" }}>
              <div className="nova-serif" style={{ fontStyle: "italic", fontWeight: 600, fontSize: 34, lineHeight: 1.15, color: "var(--nova-ink)", marginBottom: 10 }}>
                How can I help, {claims.display_name.split(" ")[0]}?
              </div>
              <div style={{ font: "400 15.5px/1.6 var(--font-figtree),sans-serif", color: "var(--nova-ink-muted)", marginBottom: 36 }}>
                Ask about internal policy, business data, or anything on the web.
              </div>
              <div className="nova-starter-grid">
                {STARTER_PROMPTS.map((p) => (
                  <button
                    key={p}
                    onClick={() => handleSend(p)}
                    disabled={isRateLimited}
                    style={{ ...starterCardStyle, opacity: isRateLimited ? 0.5 : 1, cursor: isRateLimited ? "default" : "pointer" }}
                  >
                    {p}
                  </button>
                ))}
              </div>
              {blockedReason && (
                <div style={{ marginTop: 16, font: "400 13px/1.5 var(--font-figtree),sans-serif", color: "var(--nova-danger)" }}>
                  {blockedReason}
                </div>
              )}
            </div>
          </div>
        )}

        {view === "active" && (
          <div ref={scrollRef} style={{ flex: 1, overflowY: "auto" }}>
            <div style={{ maxWidth: 760, margin: "0 auto", padding: "28px 24px 12px", display: "flex", flexDirection: "column", gap: 20 }}>
              {messages.map((m, i) => (
                <MessageBubble
                  key={i}
                  message={m}
                  isStreaming={busy && i === messages.length - 1}
                  liveSteps={busy && i === messages.length - 1 ? liveSteps : undefined}
                  liveCharts={busy && i === messages.length - 1 ? liveCharts : undefined}
                  liveCitations={busy && i === messages.length - 1 ? liveCitations : undefined}
                  onOpenSources={handleOpenSources}
                  onQuickReply={handleQuickReply}
                  onComposeText={handleComposeText}
                  interactionsDisabled={busy || isRateLimited || i !== messages.length - 1}
                />
              ))}
            </div>
          </div>
        )}

        {view === "settings" && (
          <SettingsView
            displayName={claims.display_name}
            email={claims.email}
            unitLabel={unitLabel}
            theme={theme}
            onToggleTheme={() => setTheme((t) => (t === "light" ? "dark" : "light"))}
            onLogout={handleLogout}
            usage={usage}
            usageError={usageError}
            remainingSeconds={remainingSeconds}
          />
        )}

        {view === "documents" && <DocumentsView units={documentUnits} canManageUnit={canManageUnit} />}

        {view !== "settings" && view !== "documents" && (
          <ChatInput onSend={handleSend} disabled={busy} blockedReason={blockedReason} composeRequest={composeRequest} />
        )}
      </div>

      {sourcesPanel && (
        <SourcesPanel
          citations={sourcesPanel.citations}
          highlightIndex={sourcesPanel.highlightIndex}
          onClose={() => setSourcesPanel(null)}
        />
      )}
    </div>
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

const starterCardStyle: React.CSSProperties = {
  textAlign: "left",
  padding: "16px 16px",
  borderRadius: 12,
  border: "1px solid var(--nova-border)",
  background: "var(--nova-surface)",
  color: "var(--nova-ink)",
  font: "400 13.5px/1.5 var(--font-figtree),sans-serif",
  cursor: "pointer",
};

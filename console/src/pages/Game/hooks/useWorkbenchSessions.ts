import { useCallback, useEffect, useMemo, useState } from "react";
import type { SetStateAction } from "react";
import type { DirtyCell } from "./useDirtyCells";
import type { ChatMessage } from "../components/WorkbenchChat";

const STORAGE_KEY_SESSIONS = "ltclaw.workbench.sessions.v2";
const STORAGE_KEY_CURRENT = "ltclaw.workbench.current.v2";
const MAX_MESSAGES_PER_SESSION = 200;
const MAX_SESSIONS = 50;

export interface WorkbenchHighlightState {
  table?: string;
  field?: string;
  row?: string;
  ts: number;
}

export interface WorkbenchSession {
  id: string;
  name: string;
  messages: ChatMessage[];
  dirtyCells: DirtyCell[];
  openTables: string[];
  activeTab: string | null;
  pinnedTab: string | null;
  searchByTable: Record<string, string>;
  highlight: WorkbenchHighlightState;
  createdAt: number;
  updatedAt: number;
  lastManualSavedAt: number | null;
}

interface SessionMap {
  [id: string]: WorkbenchSession;
}

const safeParse = <T,>(raw: string | null, fallback: T): T => {
  if (!raw) return fallback;
  try {
    return JSON.parse(raw) as T;
  } catch {
    return fallback;
  }
};

const newSessionId = () =>
  `wbs_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;

const createBlankSession = (name?: string): WorkbenchSession => {
  const now = Date.now();
  return {
    id: newSessionId(),
    name: name || `会话 ${new Date(now).toLocaleString()}`,
    messages: [],
    dirtyCells: [],
    openTables: [],
    activeTab: null,
    pinnedTab: null,
    searchByTable: {},
    highlight: { ts: 0 },
    createdAt: now,
    updatedAt: now,
    lastManualSavedAt: now,
  };
};

const normalizeSession = (session: WorkbenchSession): WorkbenchSession => ({
  ...session,
  lastManualSavedAt: session.lastManualSavedAt ?? session.createdAt ?? session.updatedAt ?? Date.now(),
});

const applyStateAction = <T,>(prev: T, next: SetStateAction<T>): T =>
  typeof next === "function" ? (next as (value: T) => T)(prev) : next;

const arrayShallowEqual = <T,>(left: T[], right: T[]): boolean => {
  if (left === right) return true;
  if (left.length !== right.length) return false;
  return left.every((item, index) => Object.is(item, right[index]));
};

const objectShallowEqual = (
  left: Record<string, string>,
  right: Record<string, string>,
): boolean => {
  if (left === right) return true;
  const leftKeys = Object.keys(left);
  const rightKeys = Object.keys(right);
  if (leftKeys.length !== rightKeys.length) return false;
  return leftKeys.every((key) => left[key] === right[key]);
};

const highlightEqual = (
  left: WorkbenchHighlightState,
  right: WorkbenchHighlightState,
): boolean =>
  left.table === right.table
  && left.field === right.field
  && left.row === right.row
  && left.ts === right.ts;

export interface UseWorkbenchSessions {
  sessions: WorkbenchSession[];
  currentId: string;
  current: WorkbenchSession | null;
  openTables: string[];
  activeTab: string | null;
  pinnedTab: string | null;
  searchByTable: Record<string, string>;
  highlight: WorkbenchHighlightState;
  messages: ChatMessage[];
  dirtyCells: DirtyCell[];
  setOpenTables: (next: SetStateAction<string[]>) => void;
  setActiveTab: (next: SetStateAction<string | null>) => void;
  setPinnedTab: (next: SetStateAction<string | null>) => void;
  setSearchByTable: (next: SetStateAction<Record<string, string>>) => void;
  setHighlight: (next: SetStateAction<WorkbenchHighlightState>) => void;
  setMessages: (next: SetStateAction<ChatMessage[]>) => void;
  setDirtyCells: (next: SetStateAction<DirtyCell[]>) => void;
  markCurrentSaved: () => number | null;
  isCurrentDirtySinceSave: boolean;
  switchSession: (id: string) => void;
  createSession: (name?: string) => string;
  renameSession: (id: string, name: string) => void;
  removeSession: (id: string) => void;
  clearCurrentMessages: () => void;
}

export function useWorkbenchSessions(): UseWorkbenchSessions {
  const [sessionMap, setSessionMap] = useState<SessionMap>(() => {
    const parsed = safeParse<SessionMap>(
      localStorage.getItem(STORAGE_KEY_SESSIONS),
      {},
    );
    if (Object.keys(parsed).length > 0) {
      return Object.fromEntries(
        Object.entries(parsed).map(([id, session]) => [id, normalizeSession(session)]),
      );
    }
    const first = createBlankSession("默认会话");
    return { [first.id]: first };
  });

  const [currentId, setCurrentId] = useState<string>(() => {
    return localStorage.getItem(STORAGE_KEY_CURRENT) || "";
  });

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY_SESSIONS, JSON.stringify(sessionMap));
    } catch {
      /* ignore */
    }
  }, [sessionMap]);

  useEffect(() => {
    try {
      if (currentId) {
        localStorage.setItem(STORAGE_KEY_CURRENT, currentId);
      }
    } catch {
      /* ignore */
    }
  }, [currentId]);

  useEffect(() => {
    const ids = Object.keys(sessionMap);
    if (ids.length === 0) {
      const first = createBlankSession("默认会话");
      setSessionMap({ [first.id]: first });
      setCurrentId(first.id);
      return;
    }
    if (!currentId || !sessionMap[currentId]) {
      const latest = Object.values(sessionMap).sort((a, b) => b.updatedAt - a.updatedAt)[0];
      setCurrentId(latest.id);
    }
  }, [sessionMap, currentId]);

  const sessions = useMemo(
    () => Object.values(sessionMap).sort((a, b) => b.updatedAt - a.updatedAt),
    [sessionMap],
  );

  const current = currentId ? sessionMap[currentId] || null : null;
  const isCurrentDirtySinceSave = Boolean(
    current && current.updatedAt > (current.lastManualSavedAt ?? 0),
  );

  const updateCurrent = useCallback(
    (updater: (session: WorkbenchSession) => WorkbenchSession) => {
      setSessionMap((prev) => {
        const session = prev[currentId];
        if (!session) return prev;
        const next = updater(session);
        return {
          ...prev,
          [currentId]: {
            ...next,
            updatedAt: Date.now(),
          },
        };
      });
    },
    [currentId],
  );

  const setOpenTables = useCallback(
    (next: SetStateAction<string[]>) => {
      updateCurrent((session) => {
        const resolved = applyStateAction(session.openTables, next);
        if (arrayShallowEqual(session.openTables, resolved)) return session;
        return {
          ...session,
          openTables: resolved,
        };
      });
    },
    [updateCurrent],
  );

  const setActiveTab = useCallback(
    (next: SetStateAction<string | null>) => {
      updateCurrent((session) => {
        const resolved = applyStateAction(session.activeTab, next);
        if (resolved === session.activeTab) return session;
        return {
          ...session,
          activeTab: resolved,
        };
      });
    },
    [updateCurrent],
  );

  const setPinnedTab = useCallback(
    (next: SetStateAction<string | null>) => {
      updateCurrent((session) => {
        const resolved = applyStateAction(session.pinnedTab, next);
        if (resolved === session.pinnedTab) return session;
        return {
          ...session,
          pinnedTab: resolved,
        };
      });
    },
    [updateCurrent],
  );

  const setSearchByTable = useCallback(
    (next: SetStateAction<Record<string, string>>) => {
      updateCurrent((session) => {
        const resolved = applyStateAction(session.searchByTable, next);
        if (objectShallowEqual(session.searchByTable, resolved)) return session;
        return {
          ...session,
          searchByTable: resolved,
        };
      });
    },
    [updateCurrent],
  );

  const setHighlight = useCallback(
    (next: SetStateAction<WorkbenchHighlightState>) => {
      updateCurrent((session) => {
        const resolved = applyStateAction(session.highlight, next);
        if (highlightEqual(session.highlight, resolved)) return session;
        return {
          ...session,
          highlight: resolved,
        };
      });
    },
    [updateCurrent],
  );

  const setMessages = useCallback(
    (next: SetStateAction<ChatMessage[]>) => {
      updateCurrent((session) => {
        const resolved = applyStateAction(session.messages, next);
        const trimmed =
          resolved.length > MAX_MESSAGES_PER_SESSION
            ? resolved.slice(resolved.length - MAX_MESSAGES_PER_SESSION)
            : resolved;
        if (arrayShallowEqual(session.messages, trimmed)) return session;
        return {
          ...session,
          messages: trimmed,
        };
      });
    },
    [updateCurrent],
  );

  const setDirtyCells = useCallback(
    (next: SetStateAction<DirtyCell[]>) => {
      updateCurrent((session) => {
        const resolved = applyStateAction(session.dirtyCells, next);
        if (arrayShallowEqual(session.dirtyCells, resolved)) return session;
        return {
          ...session,
          dirtyCells: resolved,
        };
      });
    },
    [updateCurrent],
  );

  const createSession = useCallback((name?: string): string => {
    const session = createBlankSession(name);
    setSessionMap((prev) => {
      const next = { ...prev, [session.id]: session };
      const ordered = Object.values(next).sort((a, b) => a.updatedAt - b.updatedAt);
      while (ordered.length > MAX_SESSIONS) {
        const oldest = ordered.shift();
        if (oldest && oldest.id !== session.id) {
          delete next[oldest.id];
        }
      }
      return next;
    });
    setCurrentId(session.id);
    return session.id;
  }, []);

  const markCurrentSaved = useCallback((): number | null => {
    const session = currentId ? sessionMap[currentId] : null;
    if (!session) return null;
    const now = Date.now();
    setSessionMap((prev) => ({
      ...prev,
      [currentId]: {
        ...prev[currentId],
        updatedAt: now,
        lastManualSavedAt: now,
      },
    }));
    return now;
  }, [currentId, sessionMap]);

  const switchSession = useCallback(
    (id: string) => {
      if (sessionMap[id]) setCurrentId(id);
    },
    [sessionMap],
  );

  const renameSession = useCallback((id: string, name: string) => {
    setSessionMap((prev) => {
      const session = prev[id];
      if (!session) return prev;
      return {
        ...prev,
        [id]: { ...session, name, updatedAt: Date.now() },
      };
    });
  }, []);

  const removeSession = useCallback(
    (id: string) => {
      setSessionMap((prev) => {
        if (!prev[id]) return prev;
        const next = { ...prev };
        delete next[id];
        if (Object.keys(next).length === 0) {
          const first = createBlankSession("默认会话");
          next[first.id] = first;
        }
        return next;
      });
      if (id === currentId) setCurrentId("");
    },
    [currentId],
  );

  const clearCurrentMessages = useCallback(() => {
    updateCurrent((session) => ({ ...session, messages: [] }));
  }, [updateCurrent]);

  return {
    sessions,
    currentId,
    current,
    openTables: current?.openTables ?? [],
    activeTab: current?.activeTab ?? null,
    pinnedTab: current?.pinnedTab ?? null,
    searchByTable: current?.searchByTable ?? {},
    highlight: current?.highlight ?? { ts: 0 },
    messages: current?.messages ?? [],
    dirtyCells: current?.dirtyCells ?? [],
    setOpenTables,
    setActiveTab,
    setPinnedTab,
    setSearchByTable,
    setHighlight,
    setMessages,
    setDirtyCells,
    markCurrentSaved,
    isCurrentDirtySinceSave,
    switchSession,
    createSession,
    renameSession,
    removeSession,
    clearCurrentMessages,
  };
}
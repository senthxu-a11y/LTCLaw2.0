import { useCallback, useEffect, useMemo, useState } from "react";
import type { ChatMessage } from "../components/WorkbenchChat";

/**
 * 工作台 Chat 的多会话本地持久化。
 * - 会话列表与当前会话 id 都存 localStorage（仅前端，不写后端）
 * - 每个会话存独立 messages 数组
 * - 与全局 /chat 完全隔离
 */

const STORAGE_KEY_SESSIONS = "ltclaw.workbench.chat.sessions.v1";
const STORAGE_KEY_CURRENT = "ltclaw.workbench.chat.current.v1";
const MAX_MESSAGES_PER_SESSION = 200;
const MAX_SESSIONS = 50;

export interface WorkbenchChatSession {
  id: string;
  name: string;
  messages: ChatMessage[];
  createdAt: number;
  updatedAt: number;
}

interface SessionMap {
  [id: string]: WorkbenchChatSession;
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

const createBlankSession = (name?: string): WorkbenchChatSession => {
  const now = Date.now();
  return {
    id: newSessionId(),
    name: name || `会话 ${new Date(now).toLocaleString()}`,
    messages: [],
    createdAt: now,
    updatedAt: now,
  };
};

export interface UseWorkbenchChatSessions {
  /** 当前会话的消息（用于 WorkbenchChat 显示） */
  messages: ChatMessage[];
  /** 替换/更新当前会话的消息（与 setState 同义） */
  setMessages: (
    next: ChatMessage[] | ((prev: ChatMessage[]) => ChatMessage[]),
  ) => void;
  /** 全部会话（按 updatedAt 倒序） */
  sessions: WorkbenchChatSession[];
  /** 当前会话 id */
  currentId: string;
  /** 当前会话对象 */
  current: WorkbenchChatSession | null;
  /** 切换会话 */
  switchSession: (id: string) => void;
  /** 新建一条会话并切换过去 */
  createSession: (name?: string) => string;
  /** 重命名 */
  renameSession: (id: string, name: string) => void;
  /** 删除 */
  removeSession: (id: string) => void;
  /** 清空当前会话消息（会话本身保留） */
  clearCurrentMessages: () => void;
}

export function useWorkbenchChatSessions(): UseWorkbenchChatSessions {
  const [sessionMap, setSessionMap] = useState<SessionMap>(() => {
    const m = safeParse<SessionMap>(
      localStorage.getItem(STORAGE_KEY_SESSIONS),
      {},
    );
    if (Object.keys(m).length === 0) {
      const s = createBlankSession("默认会话");
      return { [s.id]: s };
    }
    return m;
  });

  const [currentId, setCurrentId] = useState<string>(() => {
    const id = localStorage.getItem(STORAGE_KEY_CURRENT) || "";
    return id;
  });

  // 持久化
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY_SESSIONS, JSON.stringify(sessionMap));
    } catch {
      /* quota – ignore */
    }
  }, [sessionMap]);

  useEffect(() => {
    try {
      if (currentId) localStorage.setItem(STORAGE_KEY_CURRENT, currentId);
    } catch {
      /* ignore */
    }
  }, [currentId]);

  // 确保 currentId 一定指向一个存在的会话
  useEffect(() => {
    const ids = Object.keys(sessionMap);
    if (ids.length === 0) {
      const s = createBlankSession("默认会话");
      setSessionMap({ [s.id]: s });
      setCurrentId(s.id);
      return;
    }
    if (!currentId || !sessionMap[currentId]) {
      // 选最新的
      const sorted = ids
        .map((id) => sessionMap[id])
        .sort((a, b) => b.updatedAt - a.updatedAt);
      setCurrentId(sorted[0].id);
    }
  }, [sessionMap, currentId]);

  const sessions = useMemo(
    () =>
      Object.values(sessionMap).sort((a, b) => b.updatedAt - a.updatedAt),
    [sessionMap],
  );

  const current = currentId ? sessionMap[currentId] || null : null;
  const messages = current?.messages ?? [];

  const setMessages = useCallback(
    (
      next: ChatMessage[] | ((prev: ChatMessage[]) => ChatMessage[]),
    ) => {
      setSessionMap((prev) => {
        const sess = prev[currentId];
        if (!sess) return prev;
        const resolved =
          typeof next === "function"
            ? (next as (p: ChatMessage[]) => ChatMessage[])(sess.messages)
            : next;
        const trimmed =
          resolved.length > MAX_MESSAGES_PER_SESSION
            ? resolved.slice(resolved.length - MAX_MESSAGES_PER_SESSION)
            : resolved;
        return {
          ...prev,
          [currentId]: { ...sess, messages: trimmed, updatedAt: Date.now() },
        };
      });
    },
    [currentId],
  );

  const createSession = useCallback((name?: string): string => {
    const sess = createBlankSession(name);
    setSessionMap((prev) => {
      const ids = Object.keys(prev);
      const next = { ...prev, [sess.id]: sess };
      // cap
      if (ids.length + 1 > MAX_SESSIONS) {
        const sortedOldFirst = Object.values(next).sort(
          (a, b) => a.updatedAt - b.updatedAt,
        );
        const drop = sortedOldFirst.slice(
          0,
          ids.length + 1 - MAX_SESSIONS,
        );
        for (const d of drop) {
          if (d.id !== sess.id) delete next[d.id];
        }
      }
      return next;
    });
    setCurrentId(sess.id);
    return sess.id;
  }, []);

  const switchSession = useCallback(
    (id: string) => {
      if (sessionMap[id]) setCurrentId(id);
    },
    [sessionMap],
  );

  const renameSession = useCallback((id: string, name: string) => {
    setSessionMap((prev) => {
      const s = prev[id];
      if (!s) return prev;
      return { ...prev, [id]: { ...s, name, updatedAt: Date.now() } };
    });
  }, []);

  const removeSession = useCallback(
    (id: string) => {
      setSessionMap((prev) => {
        if (!prev[id]) return prev;
        const next = { ...prev };
        delete next[id];
        if (Object.keys(next).length === 0) {
          const s = createBlankSession("默认会话");
          next[s.id] = s;
        }
        return next;
      });
      // currentId 切换由 effect 兜底
      if (id === currentId) setCurrentId("");
    },
    [currentId],
  );

  const clearCurrentMessages = useCallback(() => {
    setSessionMap((prev) => {
      const s = prev[currentId];
      if (!s) return prev;
      return {
        ...prev,
        [currentId]: { ...s, messages: [], updatedAt: Date.now() },
      };
    });
  }, [currentId]);

  return {
    messages,
    setMessages,
    sessions,
    currentId,
    current,
    switchSession,
    createSession,
    renameSession,
    removeSession,
    clearCurrentMessages,
  };
}

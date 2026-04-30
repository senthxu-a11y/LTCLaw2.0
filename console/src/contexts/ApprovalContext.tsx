import React, { createContext, useContext, useEffect, useRef, useState, ReactNode } from "react";
import { consoleApi, type PendingApproval } from "../api/modules/console";

interface ApprovalContextValue {
  approvals: PendingApproval[];
  setApprovals: React.Dispatch<React.SetStateAction<PendingApproval[]>>;
}

const ApprovalContext = createContext<ApprovalContextValue | undefined>(
  undefined,
);

export function ApprovalProvider({ children }: { children: ReactNode }) {
  const [approvals, setApprovals] = useState<PendingApproval[]>([]);
  const stoppedRef = useRef(false);

  // SSE upgrade: on /approval/stream event, immediately refresh approvals
  // (keeps existing /console/push-messages polling as the source of truth
  // for full session/agent fields; SSE just collapses the polling lag).
  useEffect(() => {
    let es: EventSource | null = null;
    let retryTimer: ReturnType<typeof setTimeout> | null = null;
    stoppedRef.current = false;

    const refresh = () => {
      consoleApi
        .getPushMessages()
        .then((res) => {
          if (res?.pending_approvals) setApprovals(res.pending_approvals);
        })
        .catch(() => {});
    };

    const open = () => {
      if (stoppedRef.current) return;
      try {
        es = new EventSource("/api/approval/stream", { withCredentials: true } as EventSourceInit);
        es.addEventListener("approval", () => refresh());
        es.onerror = () => {
          try { es?.close(); } catch { /* ignore */ }
          es = null;
          if (!stoppedRef.current) {
            retryTimer = setTimeout(open, 3000);
          }
        };
      } catch {
        retryTimer = setTimeout(open, 3000);
      }
    };
    open();
    return () => {
      stoppedRef.current = true;
      if (retryTimer) clearTimeout(retryTimer);
      try { es?.close(); } catch { /* ignore */ }
    };
  }, []);

  return (
    <ApprovalContext.Provider value={{ approvals, setApprovals }}>
      {children}
    </ApprovalContext.Provider>
  );
}

export function useApprovalContext() {
  const context = useContext(ApprovalContext);
  if (!context) {
    throw new Error("useApprovalContext must be used within ApprovalProvider");
  }
  return context;
}

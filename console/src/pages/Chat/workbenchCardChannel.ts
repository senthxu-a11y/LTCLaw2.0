/**
 * Chat ↔ NumericWorkbench 联动卡片协议 (v0)
 *
 * 用途：让 NumericWorkbench / DocLibrary 等子页向 Chat 右栏「上下文」面板
 * 推送一张卡片（引用的数值表 / 产出文档草案 / SVN 变更摘要 等），Chat 端
 * 可以订阅渲染。前期实现仅在前端通过 window CustomEvent 广播 + localStorage
 * 持久最近一组卡片，后续可升级为 SSE / WebSocket。
 */

export type WorkbenchCardKind = "numeric_table" | "draft_doc" | "svn_change" | "kb_hit";

export interface WorkbenchCard {
  /** 唯一 ID（同 ID 重复 push 视为更新）。 */
  id: string;
  /** 卡片来源 agent。 */
  agentId: string;
  /** 卡片类型。 */
  kind: WorkbenchCardKind;
  /** 标题。 */
  title: string;
  /** 摘要 / 内容（Markdown 或纯文本）。 */
  summary: string;
  /** 跳转 deep-link（例：/numeric-workbench?table=Equipment&row=1011001）。 */
  href?: string;
  /** 任意结构化负载（数值卡：table / row_id / changes；草案卡：doc_path 等）。 */
  payload?: Record<string, unknown>;
  /** 创建时间（毫秒）。 */
  createdAt: number;
}

const STORAGE_KEY = "ltclaw.chat.workbenchCards";
const EVENT = "ltclaw:workbench-card";
const MAX_KEEP = 20;

function loadCards(): WorkbenchCard[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const arr = JSON.parse(raw);
    return Array.isArray(arr) ? (arr as WorkbenchCard[]) : [];
  } catch {
    return [];
  }
}

function saveCards(cards: WorkbenchCard[]) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(cards.slice(-MAX_KEEP)));
  } catch {
    /* ignore quota */
  }
}

/** 由生产方调用：把一张卡片推送到 Chat 联动栏。 */
export function pushWorkbenchCard(card: Omit<WorkbenchCard, "createdAt">) {
  const full: WorkbenchCard = { ...card, createdAt: Date.now() };
  const cards = loadCards();
  const idx = cards.findIndex((c) => c.id === full.id);
  if (idx >= 0) cards[idx] = full;
  else cards.push(full);
  saveCards(cards);
  try {
    window.dispatchEvent(new CustomEvent(EVENT, { detail: full }));
  } catch {
    /* ignore */
  }
}

/** 由消费方（Chat 右栏）调用：订阅卡片更新。 */
export function subscribeWorkbenchCards(
  cb: (cards: WorkbenchCard[]) => void,
): () => void {
  const handler = () => cb(loadCards());
  cb(loadCards());
  window.addEventListener(EVENT, handler);
  window.addEventListener("storage", handler);
  return () => {
    window.removeEventListener(EVENT, handler);
    window.removeEventListener("storage", handler);
  };
}

/**
 * 订阅后端 SSE 卡片流（v1）。
 * agentId 为空时不订阅，回退到 localStorage 单 tab 模式。
 * 后端事件会自动并入本地缓存，与本 tab 推送共享同一渲染通路。
 */
export function subscribeWorkbenchCardsBackend(
  agentId: string | null | undefined,
): () => void {
  if (!agentId) return () => {};
  let es: EventSource | null = null;
  let stopped = false;
  let retryTimer: ReturnType<typeof setTimeout> | null = null;
  const url = `/api/agents/${encodeURIComponent(agentId)}/workbench-cards/stream`;
  const open = () => {
    if (stopped) return;
    try {
      es = new EventSource(url, { withCredentials: true } as EventSourceInit);
      es.addEventListener("card", (ev) => {
        try {
          const data = JSON.parse((ev as MessageEvent).data);
          if (data && data.id && data.kind && data.title !== undefined) {
            pushWorkbenchCard({
              id: data.id,
              agentId: data.agentId ?? agentId,
              kind: data.kind,
              title: data.title,
              summary: data.summary ?? "",
              href: data.href,
              payload: data.payload,
            });
          }
        } catch {
          /* ignore malformed event */
        }
      });
      es.onerror = () => {
        try { es?.close(); } catch { /* ignore */ }
        es = null;
        if (!stopped) {
          retryTimer = setTimeout(open, 3000);
        }
      };
    } catch {
      retryTimer = setTimeout(open, 3000);
    }
  };
  open();
  return () => {
    stopped = true;
    if (retryTimer) clearTimeout(retryTimer);
    try { es?.close(); } catch { /* ignore */ }
  };
}

/** 清空所有卡片（用户点 Chat 右栏的清除）。 */
export function clearWorkbenchCards() {
  saveCards([]);
  try {
    window.dispatchEvent(new CustomEvent(EVENT, { detail: null }));
  } catch {
    /* ignore */
  }
}

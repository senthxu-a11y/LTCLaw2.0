import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  Alert,
  Button,
  Card,
  Empty,
  Input,
  InputNumber,
  Modal,
  Select,
  Space,
  Spin,
  Table,
  Tabs,
  Tag,
  Tooltip,
  Typography,
} from "antd";
import {
  DeleteOutlined,
  PushpinFilled,
  PushpinOutlined,
  ReloadOutlined,
  RobotOutlined,
  WarningOutlined,
} from "@ant-design/icons";
import { useTranslation } from "react-i18next";
import { useSearchParams } from "react-router-dom";
import { PageHeader } from "@/components/PageHeader";
import { useAppMessage } from "@/hooks/useAppMessage";
import type { FrontendCapabilityToken } from "@/api/types/permissions";
import { canUseGovernanceAction, hasCapabilityContext, isPermissionDeniedError } from "@/utils/permissions";
import { useAgentStore } from "../../stores/agentStore";
import { gameApi } from "../../api/modules/game";
import { gameChangeApi } from "../../api/modules/gameChange";
import { gameWorkbenchApi } from "../../api/modules/gameWorkbench";
import type {
  AiSuggestPanelResponse,
  DamageChainResponse,
  PreviewItem,
  ReverseImpact,
  SuggestChange,
} from "../../api/modules/gameWorkbench";
import type { TableIndex } from "../../api/types/game";
import { pushWorkbenchCard } from "../Chat/workbenchCardChannel";
import { DirtyList } from "./components/DirtyList";
import { ImpactPanel } from "./components/ImpactPanel";
import { WorkbenchChat, type ChatMessage } from "./components/WorkbenchChat";
import { WorkbenchChatSessionToolbar } from "./components/WorkbenchChatSessionToolbar";
import { useWorkbenchSessions } from "./hooks/useWorkbenchSessions";
import ModelSelector from "../Chat/ModelSelector";
import {
  coerceCellValue,
  dirtyKeyOf,
  useDirtyCells,
} from "./hooks/useDirtyCells";
import styles from "./NumericWorkbench.module.less";

const { Text } = Typography;

interface RowsData {
  headers: string[];
  rows: (string | number | boolean)[][];
  total: number;
}

interface CellEditState {
  table: string;
  rowKey: string;
  field: string;
  value: string;      // 用户输入中的字符串
  origin: unknown;    // 原始值（取消时还原）
}

type CitationTargetState =
  | {
      kind: "loading";
      table: string;
      row?: string;
      field?: string;
    }
  | {
      kind: "table-not-found";
      table: string;
      row?: string;
      field?: string;
    }
  | {
      kind: "table-opened-target-found";
      table: string;
      row?: string;
      field?: string;
    }
  | {
      kind: "table-opened-target-not-found";
      table: string;
      row?: string;
      field?: string;
      rowMatched: boolean;
      fieldMatched: boolean;
    };

const formatVal = (v: unknown): string => {
  if (v === null || v === undefined || v === "") return "—";
  if (typeof v === "object") return JSON.stringify(v);
  return String(v);
};

const isNumericType = (t?: string): boolean => {
  const s = (t || "").toLowerCase();
  return s.includes("int") || s.includes("float") || s === "number" || s === "double";
};

export default function NumericWorkbench() {
  const { t } = useTranslation();
  const { message } = useAppMessage();
  const { selectedAgent, agents } = useAgentStore();
  const [searchParams, setSearchParams] = useSearchParams();

  const selectedAgentSummary = agents.find((agent) => agent.id === selectedAgent);
  const capabilities: FrontendCapabilityToken[] | undefined = selectedAgentSummary?.capabilities;
  const hasExplicitCapabilityContext = hasCapabilityContext(capabilities);
  const canReadWorkbench = canUseGovernanceAction(capabilities, "workbench.read");
  const canWriteWorkbench = canUseGovernanceAction(capabilities, "workbench.test.write");
  const canExportWorkbench = canUseGovernanceAction(capabilities, "workbench.test.export");
  const permissionDeniedMessage = t("gameProject.permissionDenied", {
    defaultValue: "You do not have permission to perform this action.",
  });
  const workbenchReadReason =
    hasExplicitCapabilityContext && !canReadWorkbench
      ? t("gameWorkbench.permissionReadRequired", {
          defaultValue: "Requires workbench.read permission.",
        })
      : null;
  const workbenchWriteReason =
    hasExplicitCapabilityContext && !canWriteWorkbench
      ? t("gameWorkbench.permissionWriteRequired", {
          defaultValue: "Requires workbench.test.write permission.",
        })
      : null;
  const workbenchExportReason =
    hasExplicitCapabilityContext && !canExportWorkbench
      ? t("gameWorkbench.permissionExportRequired", {
          defaultValue: "Requires workbench.test.export permission.",
        })
      : null;

  const formatPermissionError = useCallback(
    (error: unknown, fallbackMessage: string) => {
      if (isPermissionDeniedError(error)) {
        return permissionDeniedMessage;
      }
      return error instanceof Error ? error.message : fallbackMessage;
    },
    [permissionDeniedMessage],
  );

  // Deep-link
  const dlTable = searchParams.get("table") || searchParams.get("tableId") || "";
  const dlRow = searchParams.get("row") || searchParams.get("rowId") || "";
  const dlField = searchParams.get("field") || searchParams.get("fieldKey") || "";
  const sessionParam = searchParams.get("session") || "";
  const hasDeepLink = Boolean(dlTable || dlRow || dlField);
  const citationContext = useMemo(() => {
    if (searchParams.get("from") !== "rag-citation" || !hasDeepLink) {
      return null;
    }

    const title = searchParams.get("citationTitle") || "";
    const source = searchParams.get("citationSource") || "";
    const citationId = searchParams.get("citationId") || "";
    if (!title && !source && !citationId && !dlTable && !dlRow && !dlField) {
      return null;
    }

    return {
      citationId,
      title,
      source,
      table: dlTable,
      row: dlRow,
      field: dlField,
    };
  }, [dlField, dlRow, dlTable, hasDeepLink, searchParams]);
  const isWorkbenchView = Boolean(sessionParam || hasDeepLink);

  const sessionStore = useWorkbenchSessions();

  const [tableNames, setTableNames] = useState<string[]>([]);
  const [tablesLoading, setTablesLoading] = useState(false);
  const [tablesLoaded, setTablesLoaded] = useState(false);
  const openTables = sessionStore.openTables;
  const setOpenTables = sessionStore.setOpenTables;
  const activeTab = sessionStore.activeTab;
  const setActiveTab = sessionStore.setActiveTab;
  /** Tab 钉选：当存在 pinnedTab 时，上区横向分屏（左 activeTab / 右 pinnedTab） */
  const pinnedTab = sessionStore.pinnedTab;
  const setPinnedTab = sessionStore.setPinnedTab;
  const [detailsByTable, setDetailsByTable] = useState<Record<string, TableIndex>>({});
  const [rowsByTable, setRowsByTable] = useState<Record<string, RowsData>>({});
  const [rowsLoading, setRowsLoading] = useState(false);
  const searchByTable = sessionStore.searchByTable;
  const setSearchByTable = sessionStore.setSearchByTable;

  // 高亮（来自 deep-link 或「定位」按钮）
  const highlight = sessionStore.highlight;
  const setHighlight = sessionStore.setHighlight;

  // 单元格编辑态（同时只允许一个）
  const [editing, setEditing] = useState<CellEditState | null>(null);

  // 工作台 Chat（属于工作台本地会话，持久化到 localStorage）
  const [chatInput, setChatInput] = useState("");
  const chatMessages = sessionStore.messages;
  const setChatMessages = sessionStore.setMessages;
  const [chatSending, setChatSending] = useState(false);

  // 工作台专属 Agent / 模型覆盖（默认 "" 表示使用全局 selectedAgent）
  const WORKBENCH_AGENT_KEY = "ltclaw.workbench.agentOverride.v1";
  const [workbenchAgentOverride, setWorkbenchAgentOverride] = useState<string>(
    () => {
      try {
        return localStorage.getItem(WORKBENCH_AGENT_KEY) || "";
      } catch {
        return "";
      }
    },
  );
  useEffect(() => {
    try {
      if (workbenchAgentOverride) {
        localStorage.setItem(WORKBENCH_AGENT_KEY, workbenchAgentOverride);
      } else {
        localStorage.removeItem(WORKBENCH_AGENT_KEY);
      }
    } catch {
      /* ignore */
    }
  }, [workbenchAgentOverride]);
  /** 发送 AI 请求使用的 agent id（能定制主模型） */
  const aiAgentId = workbenchAgentOverride || selectedAgent;

  // dirty 状态 hook
  const dirty = useDirtyCells({
    initialCells: sessionStore.dirtyCells,
    onChange: sessionStore.setDirtyCells,
  });

  // 影响 / 反向依赖（基于当前 dirty）
  const [preview, setPreview] = useState<PreviewItem[]>([]);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [damageChain, setDamageChain] = useState<DamageChainResponse | null>(null);
  const [damageChainLoading, setDamageChainLoading] = useState(false);
  const [affectedTables, setAffectedTables] = useState<string[]>([]);
  const [impacts, setImpacts] = useState<ReverseImpact[]>([]);

  // 当前活跃表的字段统计（用于范围/类型校验）
  const [aiPanel, setAiPanel] = useState<AiSuggestPanelResponse | null>(null);

  // 草稿提交
  const [draftOpen, setDraftOpen] = useState(false);
  const [draftTitle, setDraftTitle] = useState("");
  const [draftDesc, setDraftDesc] = useState("");
  const [submitting, setSubmitting] = useState(false);

  // 上下分割（上区高度比例）
  const [topRatio, setTopRatio] = useState(0.55);
  const splitContainerRef = useRef<HTMLDivElement>(null);
  const draggingRef = useRef(false);

  const debounceRef = useRef<number | null>(null);

  const workbenchPendingLabel = sessionStore.isCurrentDirtySinceSave
    ? t("gameWorkbench.currentSessionPendingSave", { defaultValue: "本地变更待保存" })
    : t("gameWorkbench.currentSessionSaved", { defaultValue: "本地会话已保存" });

  const updateQuery = useCallback(
    (patch: Record<string, string | null>, replace = false) => {
      const next = new URLSearchParams(searchParams);
      Object.entries(patch).forEach(([key, value]) => {
        if (!value) {
          next.delete(key);
        } else {
          next.set(key, value);
        }
      });
      setSearchParams(next, { replace });
    },
    [searchParams, setSearchParams],
  );

  const syncWorkbenchRoute = useCallback(
    (
      params: {
        session?: string | null;
        table?: string | null;
        row?: string | null;
        field?: string | null;
      },
      replace = false,
    ) => {
      updateQuery(
        {
          session: params.session ?? null,
          table: params.table ?? null,
          tableId: params.table ?? null,
          row: params.row ?? null,
          rowId: params.row ?? null,
          field: params.field ?? null,
          fieldKey: params.field ?? null,
        },
        replace,
      );
    },
    [updateQuery],
  );

  const notifyAutoPreserved = useCallback(() => {
    if (!sessionStore.isCurrentDirtySinceSave) return;
    message.info(
      t("gameWorkbench.autoPreservedNotice", {
        defaultValue: "当前会话仍有未手动保存的本地变更，但状态已自动保留。",
      }),
    );
  }, [message, sessionStore.isCurrentDirtySinceSave, t]);

  const openSession = useCallback(
    (id: string) => {
      const switchingSession = id !== sessionStore.currentId;
      const routeAlreadyFocused = sessionParam === id && !dlTable && !dlRow && !dlField;
      if (!switchingSession && routeAlreadyFocused) return;
      if (switchingSession) {
        notifyAutoPreserved();
        sessionStore.switchSession(id);
      }
      syncWorkbenchRoute({ session: id }, false);
    },
    [dlField, dlRow, dlTable, notifyAutoPreserved, sessionParam, sessionStore, syncWorkbenchRoute],
  );

  const createAndOpenSession = useCallback(() => {
    notifyAutoPreserved();
    const id = sessionStore.createSession();
    syncWorkbenchRoute({ session: id }, false);
  }, [notifyAutoPreserved, sessionStore, syncWorkbenchRoute]);

  const backToSessionList = useCallback(() => {
    notifyAutoPreserved();
    syncWorkbenchRoute({ session: null }, false);
  }, [notifyAutoPreserved, syncWorkbenchRoute]);

  const removeSessionAndRoute = useCallback(
    (id: string) => {
      const remaining = sessionStore.sessions.filter((session) => session.id !== id);
      const fallback = remaining[0]?.id || null;
      const removingCurrent = id === sessionStore.currentId;
      sessionStore.removeSession(id);
      if (!removingCurrent) return;
      syncWorkbenchRoute({ session: fallback }, true);
      message.success(
        t("gameWorkbench.sessionRemoved", {
          defaultValue: "当前会话已删除。",
        }),
      );
    },
    [message, sessionStore, syncWorkbenchRoute, t],
  );

  const confirmRemoveSession = useCallback(
    (sessionId: string, sessionName: string, dirtySinceSave: boolean) => {
      Modal.confirm({
        title: t("gameWorkbench.removeSessionTitle", {
          defaultValue: "删除会话",
        }),
        content: dirtySinceSave
          ? t("gameWorkbench.removeSessionDirtyConfirm", {
              defaultValue: `删除会话「${sessionName}」？当前会话还有未手动保存的本地变更，删除后将无法恢复。`,
            })
          : t("gameWorkbench.removeSessionConfirm", {
              defaultValue: `删除会话「${sessionName}」？此操作不可撤销。`,
            }),
        okType: "danger",
        okText: t("gameWorkbench.removeSessionOk", { defaultValue: "删除" }),
        cancelText: t("gameWorkbench.removeSessionCancel", { defaultValue: "取消" }),
        onOk: () => removeSessionAndRoute(sessionId),
      });
    },
    [removeSessionAndRoute, t],
  );

  useEffect(() => {
    if (sessionParam && sessionParam !== sessionStore.currentId) {
      sessionStore.switchSession(sessionParam);
    }
  }, [sessionParam, sessionStore.currentId, sessionStore.switchSession]);

  useEffect(() => {
    if (hasDeepLink && !sessionParam && sessionStore.currentId) {
      syncWorkbenchRoute(
        {
          session: sessionStore.currentId,
          table: dlTable || null,
          row: dlRow || null,
          field: dlField || null,
        },
        true,
      );
    }
  }, [dlField, dlRow, dlTable, hasDeepLink, sessionParam, sessionStore.currentId, syncWorkbenchRoute]);

  useEffect(() => {
    if (!sessionParam) return;
    if (sessionStore.sessions.some((session) => session.id === sessionParam)) return;
    if (!sessionStore.currentId) return;
    syncWorkbenchRoute({ session: sessionStore.currentId }, true);
  }, [sessionParam, sessionStore.sessions, sessionStore.currentId, syncWorkbenchRoute]);

  // ── 加载表 ─────────────────────────────────────────────
  const loadTables = useCallback(async () => {
    setTablesLoaded(false);
    if (!selectedAgent) {
      setTableNames([]);
      setTablesLoading(false);
      setTablesLoaded(true);
      return;
    }
    if (hasExplicitCapabilityContext && !canReadWorkbench) {
      setTableNames([]);
      setTablesLoading(false);
      setTablesLoaded(true);
      return;
    }
    setTablesLoading(true);
    try {
      const resp = await gameApi.listTables(selectedAgent, { page: 1, size: 200 });
      setTableNames(resp.items.map((it) => it.table_name));
    } catch {
      message.error(t("gameWorkbench.loadTablesFailed", { defaultValue: "加载表列表失败" }));
    } finally {
      setTablesLoading(false);
      setTablesLoaded(true);
    }
  }, [selectedAgent, message, t, hasExplicitCapabilityContext, canReadWorkbench]);

  const loadTableDetail = useCallback(
    async (name: string) => {
      if (!selectedAgent) return;
      if (hasExplicitCapabilityContext && !canReadWorkbench) return;
      try {
        const detail = await gameApi.getTable(selectedAgent, name);
        setDetailsByTable((prev) => ({ ...prev, [name]: detail }));
      } catch {
        /* ignore */
      }
    },
    [selectedAgent, hasExplicitCapabilityContext, canReadWorkbench],
  );

  const loadRowsForTable = useCallback(
    async (name: string) => {
      if (!selectedAgent) return;
      if (hasExplicitCapabilityContext && !canReadWorkbench) {
        setRowsByTable((prev) => ({ ...prev, [name]: { headers: [], rows: [], total: 0 } }));
        return;
      }
      setRowsLoading(true);
      try {
        const resp = await gameApi.getTableRows(selectedAgent, name, 0, 500);
        setRowsByTable((prev) => ({
          ...prev,
          [name]: { headers: resp.headers, rows: resp.rows, total: resp.total },
        }));
      } catch {
        setRowsByTable((prev) => ({ ...prev, [name]: { headers: [], rows: [], total: 0 } }));
      } finally {
        setRowsLoading(false);
      }
    },
    [selectedAgent, hasExplicitCapabilityContext, canReadWorkbench],
  );

  useEffect(() => { loadTables(); }, [loadTables]);

  useEffect(() => {
    openTables.forEach((name) => {
      if (!detailsByTable[name]) loadTableDetail(name);
      if (!rowsByTable[name]) loadRowsForTable(name);
    });
    if (openTables.length === 0) {
      setActiveTab(null);
      setPinnedTab(null);
    } else if (!activeTab || !openTables.includes(activeTab)) {
      setActiveTab(openTables[0]);
    }
    if (pinnedTab && !openTables.includes(pinnedTab)) {
      setPinnedTab(null);
    }
  }, [openTables, activeTab, pinnedTab, detailsByTable, rowsByTable, loadTableDetail, loadRowsForTable]);

  // Deep-link
  useEffect(() => {
    if (!dlTable) return;
    if (tableNames.length === 0) return;
    if (!tableNames.includes(dlTable)) return;
    setOpenTables((prev) => (prev.includes(dlTable) ? prev : [...prev, dlTable]));
    setActiveTab(dlTable);
    if (dlRow) setSearchByTable((prev) => ({ ...prev, [dlTable]: dlRow }));
    setHighlight({
      table: dlTable,
      field: dlField || undefined,
      row: dlRow || undefined,
      ts: Date.now(),
    });
    const tid = window.setTimeout(() => setHighlight((h) => ({ ...h, ts: 0 })), 1800);
    return () => window.clearTimeout(tid);
  }, [dlTable, dlRow, dlField, tableNames]);

  const citationTargetState = useMemo<CitationTargetState | null>(() => {
    if (!citationContext || !citationContext.table) {
      return null;
    }

    const table = citationContext.table;
    const row = citationContext.row || undefined;
    const field = citationContext.field || undefined;
    const hasTableNameEvidence = tablesLoaded || tableNames.length > 0;

    if (tablesLoading && !hasTableNameEvidence) {
      return { kind: "loading", table, row, field };
    }

    if (!tablesLoading && hasTableNameEvidence && !tableNames.includes(table)) {
      return { kind: "table-not-found", table, row, field };
    }

    const tableOpened = openTables.includes(table);
    const rowData = rowsByTable[table];
    const detail = detailsByTable[table];
    const headers = rowData?.headers ?? detail?.fields.map((item) => item.name) ?? [];
    const rowsResolved = !row || !!rowData;
    const fieldResolved = !field || !!rowData || !!detail;

    if (!tableOpened || !rowsResolved || !fieldResolved) {
      return { kind: "loading", table, row, field };
    }

    const rowMatched =
      !row ||
      !!rowData?.rows.some((record) => String(record[0] ?? "") === row);
    const fieldMatched =
      !field ||
      headers.includes(field) ||
      !!detail?.fields.some((item) => item.name === field);

    if (rowMatched && fieldMatched) {
      return { kind: "table-opened-target-found", table, row, field };
    }

    return {
      kind: "table-opened-target-not-found",
      table,
      row,
      field,
      rowMatched,
      fieldMatched,
    };
  }, [citationContext, detailsByTable, openTables, rowsByTable, tableNames, tablesLoaded, tablesLoading]);

  const citationSourceLabel = useMemo(() => {
    if (!citationContext) {
      return null;
    }
    if (citationContext.title || citationContext.source) {
      return t("gameWorkbench.citationContextSource", {
        title: citationContext.title || citationContext.source,
        source: citationContext.source,
        defaultValue: `Citation: ${citationContext.title || citationContext.source}${citationContext.source ? ` (${citationContext.source})` : ""}`,
      });
    }
    return t("gameWorkbench.citationContextSourceUnknown", {
      defaultValue: "Citation source details were not provided.",
    });
  }, [citationContext, t]);

  const citationTargetSummary = useMemo(() => {
    if (!citationTargetState) {
      return null;
    }

    if (citationTargetState.kind === "loading") {
      return {
        tone: "info",
        title: t("gameWorkbench.citationTargetLoading", {
          defaultValue: "Locating citation target in workbench",
        }),
        detail: t("gameWorkbench.citationTargetLoadingDetail", {
          table: citationTargetState.table,
          defaultValue: `Opening table ${citationTargetState.table} and checking the requested target.`,
        }),
      };
    }

    if (citationTargetState.kind === "table-not-found") {
      return {
        tone: "danger",
        title: t("gameWorkbench.citationTargetTableMissing", {
          defaultValue: "Citation table could not be opened",
        }),
        detail: t("gameWorkbench.citationTargetTableMissingDetail", {
          table: citationTargetState.table,
          defaultValue: `Requested table ${citationTargetState.table} is not available in this workbench.`,
        }),
      };
    }

    if (citationTargetState.kind === "table-opened-target-found") {
      const parts = [
        `Table: ${citationTargetState.table}`,
        citationTargetState.row ? `row: ${citationTargetState.row}` : null,
        citationTargetState.field ? `field: ${citationTargetState.field}` : null,
      ].filter(Boolean);
      return {
        tone: "success",
        title: t("gameWorkbench.citationTargetFound", {
          defaultValue: "Focused citation target in current table",
        }),
        detail: parts.join(", "),
      };
    }

    const missingRow = citationTargetState.row && !citationTargetState.rowMatched;
    const missingField = citationTargetState.field && !citationTargetState.fieldMatched;
    let detail: string;
    if (missingRow && missingField) {
      detail = t("gameWorkbench.citationTargetMissingRowField", {
        table: citationTargetState.table,
        row: citationTargetState.row,
        field: citationTargetState.field,
        defaultValue: `Opened table ${citationTargetState.table}, but row ${citationTargetState.row} or field ${citationTargetState.field} could not be matched.`,
      });
    } else if (missingRow) {
      detail = t("gameWorkbench.citationTargetMissingRow", {
        table: citationTargetState.table,
        row: citationTargetState.row,
        defaultValue: `Opened table ${citationTargetState.table}, but row ${citationTargetState.row} could not be matched.`,
      });
    } else {
      detail = t("gameWorkbench.citationTargetMissingField", {
        table: citationTargetState.table,
        field: citationTargetState.field,
        defaultValue: `Opened table ${citationTargetState.table}, but field ${citationTargetState.field} could not be matched.`,
      });
    }

    return {
      tone: "warning",
      title: t("gameWorkbench.citationTargetNotFound", {
        defaultValue: "Citation target not found in current table",
      }),
      detail,
    };
  }, [citationTargetState, t]);

  // 切换 activeTab → 拉一次结构化面板（用于范围校验）
  useEffect(() => {
    if (!selectedAgent || !activeTab) {
      setAiPanel(null);
      return;
    }
    if (hasExplicitCapabilityContext && !canReadWorkbench) {
      setAiPanel(null);
      return;
    }
    let cancelled = false;
    gameWorkbenchApi
      .aiSuggestPanel(selectedAgent, activeTab, undefined)
      .then((p) => { if (!cancelled) setAiPanel(p); })
      .catch(() => { if (!cancelled) setAiPanel(null); });
    return () => { cancelled = true; };
  }, [selectedAgent, activeTab, hasExplicitCapabilityContext, canReadWorkbench]);

  // dirty → debounced preview + reverse-impact
  const validChanges = dirty.validChanges;
  const runPreview = useCallback(async () => {
    if (!selectedAgent) return;
    if (hasExplicitCapabilityContext && !canReadWorkbench) {
      setPreview([]);
      setDamageChain(null);
      setAffectedTables([]);
      setImpacts([]);
      return;
    }
    if (validChanges.length === 0) {
      setPreview([]);
      setDamageChain(null);
      setAffectedTables([]);
      setImpacts([]);
      return;
    }
    setPreviewLoading(true);
    setDamageChainLoading(true);
    try {
      const [p, d] = await Promise.all([
        gameWorkbenchApi.preview(selectedAgent, validChanges),
        gameWorkbenchApi
          .damageChain(selectedAgent, { changes: validChanges })
          .catch(() => null),
      ]);
      setPreview(p.items);
      setAffectedTables(p.affected_tables ?? []);
      setImpacts(p.impacts ?? []);
      setDamageChain(d);
    } catch {
      message.error(t("gameWorkbench.previewFailed", { defaultValue: "预览失败" }));
    } finally {
      setPreviewLoading(false);
      setDamageChainLoading(false);
    }
  }, [selectedAgent, validChanges, message, t, hasExplicitCapabilityContext, canReadWorkbench]);

  useEffect(() => {
    if (debounceRef.current) window.clearTimeout(debounceRef.current);
    debounceRef.current = window.setTimeout(runPreview, 350);
    return () => {
      if (debounceRef.current) window.clearTimeout(debounceRef.current);
    };
  }, [runPreview]);

  // ── 上下 splitter 拖拽 ─────────────────────────────────
  const onSplitterMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    draggingRef.current = true;
    const onMove = (ev: MouseEvent) => {
      if (!draggingRef.current || !splitContainerRef.current) return;
      const rect = splitContainerRef.current.getBoundingClientRect();
      const ratio = (ev.clientY - rect.top) / rect.height;
      setTopRatio(Math.max(0.25, Math.min(0.85, ratio)));
    };
    const onUp = () => {
      draggingRef.current = false;
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseup", onUp);
    };
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup", onUp);
  };

  // ── 编辑：开始 / 提交 / 取消 ──────────────────────────
  const beginEdit = (
    table: string,
    rowKey: string,
    field: string,
    origin: unknown,
  ) => {
    const existing = dirty.dirty[dirtyKeyOf(table, rowKey, field)];
    setEditing({
      table,
      rowKey,
      field,
      value:
        existing && existing.newValue !== undefined && existing.newValue !== null
          ? String(existing.newValue)
          : origin === null || origin === undefined
            ? ""
            : String(origin),
      origin,
    });
  };

  const cancelEdit = () => setEditing(null);

  const commitEdit = useCallback(() => {
    if (!editing) return;
    const detail = detailsByTable[editing.table];
    const fieldType = detail?.fields.find((f) => f.name === editing.field)?.type;
    const { value, typeOk } = coerceCellValue(editing.value, fieldType);
    if (!typeOk) {
      message.error(
        t("gameWorkbench.typeError", {
          defaultValue: `字段 ${editing.field} 期望数值类型，输入无效`,
        }),
      );
      return;
    }
    // 与原值相同 → 视为撤销
    const sameAsOrigin =
      String(value) === String(editing.origin ?? "") ||
      (value === "" && (editing.origin === null || editing.origin === undefined));
    if (sameAsOrigin) {
      dirty.clearCell(editing.table, editing.rowKey, editing.field);
    } else {
      dirty.setCell({
        table: editing.table,
        rowKey: editing.rowKey,
        field: editing.field,
        oldValue: editing.origin,
        newValue: value,
        source: "manual",
      });
    }
    setEditing(null);
  }, [editing, detailsByTable, dirty, message, t]);

  // ── 单元格渲染（双击进入编辑 / dirty 高亮 / 范围警告） ─
  const renderCell = useCallback(
    (
      tname: string,
      rowKey: string,
      field: string,
      origVal: unknown,
      rowIndex: number,
    ) => {
      void rowIndex;
      const k = dirtyKeyOf(tname, rowKey, field);
      const dItem = dirty.dirty[k];
      const isEditing =
        editing &&
        editing.table === tname &&
        editing.rowKey === rowKey &&
        editing.field === field;

      const detail = detailsByTable[tname];
      const fieldType = detail?.fields.find((f) => f.name === field)?.type;
      const numeric = isNumericType(fieldType);

      // 范围警告（仅当 dirty 且 activeTab=tname 时使用 aiPanel.numeric_stats）
      let rangeWarn: string | null = null;
      if (
        dItem &&
        numeric &&
        tname === activeTab &&
        aiPanel?.numeric_stats &&
        typeof dItem.newValue === "number"
      ) {
        const { min, max } = aiPanel.numeric_stats;
        if (typeof min === "number" && typeof max === "number") {
          if (dItem.newValue < min || dItem.newValue > max) {
            rangeWarn = `参考区间 [${min} ~ ${max}]`;
          }
        }
      }

      if (isEditing) {
        return numeric ? (
          <InputNumber
            autoFocus
            size="small"
            value={editing!.value === "" ? null : Number(editing!.value)}
            onChange={(v) =>
              setEditing((e) => (e ? { ...e, value: v === null || v === undefined ? "" : String(v) } : e))
            }
            onBlur={commitEdit}
            onPressEnter={commitEdit}
            onKeyDown={(e) => { if (e.key === "Escape") cancelEdit(); }}
            style={{ width: "100%" }}
          />
        ) : (
          <Input
            autoFocus
            size="small"
            value={editing!.value}
            onChange={(e) => setEditing((s) => (s ? { ...s, value: e.target.value } : s))}
            onBlur={commitEdit}
            onPressEnter={commitEdit}
            onKeyDown={(e) => { if (e.key === "Escape") cancelEdit(); }}
          />
        );
      }

      const display = dItem ? formatVal(dItem.newValue) : formatVal(origVal);
      const cls = dItem
        ? `${styles.editableCellWrap} ${styles.dirty} ${
            dItem.source === "ai" ? styles.dirtyAi : ""
          }`
        : styles.editableCellWrap;

      return (
        <span
          className={cls}
          title={t("gameWorkbench.dblClickToEdit", {
            defaultValue: "双击编辑（Enter 保存 / Esc 取消）",
          })}
          onDoubleClick={() => beginEdit(tname, rowKey, field, origVal)}
        >
          {dItem && (
            <span
              className={`${styles.dirtyDot} ${dItem.source === "ai" ? styles.ai : ""}`}
            />
          )}
          {display}
          {rangeWarn && (
            <Tooltip title={rangeWarn}>
              <WarningOutlined className={styles.rangeWarn} />
            </Tooltip>
          )}
        </span>
      );
    },
    [dirty.dirty, editing, detailsByTable, aiPanel, activeTab, t, commitEdit],
  );

  // ── 渲染单张表的内容（含搜索 + Table） ────────────────
  const renderTablePane = useCallback(
    (tname: string, isPinnedHalf?: boolean) => {
      const data = rowsByTable[tname];
      if (!data) return <Spin style={{ display: "block", margin: "40px auto" }} />;
      const headers = data.headers;
      const pkCol = headers[0];
      const q = (searchByTable[tname] ?? "").trim().toLowerCase();
      const baseSrc = data.rows.map((r, i) => ({
        __idx: i,
        __rowKey: String(r[0] ?? i),
        ...Object.fromEntries(headers.map((h, ci) => [h, r[ci]])),
      }));
      const dataSource = q
        ? baseSrc.filter((row) =>
            headers.some((h) =>
              String((row as Record<string, unknown>)[h] ?? "").toLowerCase().includes(q),
            ),
          )
        : baseSrc;
      return (
        <div className={styles.tableScroll}>
          <div style={{ padding: "8px 12px", borderBottom: "1px solid #f0f0f0", background: "#fafafa" }}>
            <Space size={6}>
              <Input.Search
                allowClear
                size="small"
                placeholder={t("gameWorkbench.searchPlaceholder", {
                  defaultValue: "全表搜索（按任意单元格内容过滤）",
                })}
                value={searchByTable[tname] ?? ""}
                onChange={(e) =>
                  setSearchByTable((prev) => ({ ...prev, [tname]: e.target.value }))
                }
                style={{ width: 320 }}
              />
              {q && (
                <Tag color={dataSource.length ? "blue" : "default"}>
                  {t("gameWorkbench.searchHit", {
                    defaultValue: `命中 ${dataSource.length} / ${data.rows.length} 行`,
                  })}
                </Tag>
              )}
              {!isPinnedHalf && (
                <Tooltip
                  title={
                    pinnedTab === tname
                      ? t("gameWorkbench.unpinHint", { defaultValue: "取消钉选" })
                      : t("gameWorkbench.pinHint", { defaultValue: "钉到右侧分屏（双击 Tab 头同效）" })
                  }
                >
                  <Button
                    size="small"
                    type={pinnedTab === tname ? "primary" : "default"}
                    icon={pinnedTab === tname ? <PushpinFilled /> : <PushpinOutlined />}
                    onClick={() => {
                      if (pinnedTab === tname) {
                        setPinnedTab(null);
                      } else {
                        // 钉的必须不是 activeTab
                        if (activeTab === tname) {
                          // 找到一个非 tname 的 tab 作为 active
                          const other = openTables.find((n) => n !== tname);
                          if (!other) {
                            message.info(
                              t("gameWorkbench.pinNeedTwoTabs", {
                                defaultValue: "需要至少 2 张表才能分屏",
                              }),
                            );
                            return;
                          }
                          setActiveTab(other);
                        }
                        setPinnedTab(tname);
                      }
                    }}
                  />
                </Tooltip>
              )}
            </Space>
          </div>
          <Table
            size="small"
            rowKey={(_r, idx) => String(idx ?? 0)}
            sticky
            scroll={{ x: "max-content", y: "calc(100% - 60px)" }}
            pagination={{ pageSize: 50, size: "small", showSizeChanger: false }}
            rowClassName={(row) => {
              if (!highlight.ts || highlight.table !== tname || !highlight.row) return "";
              const pkVal = String((row as Record<string, unknown>)[pkCol] ?? "");
              return pkVal === highlight.row ? styles.highlightRow : "";
            }}
            dataSource={dataSource}
            columns={[
              { title: "#", width: 50, fixed: "left" as const, render: (_: unknown, __: unknown, idx: number) => idx + 1 },
              ...headers.map((h, ci) => {
                const isHl =
                  highlight.ts > 0 && highlight.table === tname && highlight.field === h;
                return {
                  title: h,
                  dataIndex: h,
                  key: `${h}__${ci}`,
                  ellipsis: true,
                  width: ci === 0 ? 110 : 140,
                  className: isHl ? styles.highlightCol : undefined,
                  onHeaderCell: () => ({ className: isHl ? styles.highlightCol : "" }),
                  render: (val: unknown, row: unknown, rIdx: number) => {
                    const rowKey = (row as { __rowKey?: string })?.__rowKey ?? String(rIdx);
                    if (ci === 0) return formatVal(val);
                    return renderCell(tname, rowKey, h, val, rIdx);
                  },
                };
              }),
            ]}
          />
        </div>
      );
    },
    [
      rowsByTable,
      searchByTable,
      pinnedTab,
      activeTab,
      openTables,
      highlight,
      message,
      t,
      renderCell,
    ],
  );

  // ── Chat 发送 ─────────────────────────────────────────
  const sendChat = useCallback(async () => {
    const text = chatInput.trim();
    if (!text || !aiAgentId) return;
    if (hasExplicitCapabilityContext && !canReadWorkbench) {
      message.warning(workbenchReadReason || permissionDeniedMessage);
      return;
    }
    const userMsg: ChatMessage = { role: "user", content: text, ts: Date.now() };
    setChatMessages((prev) => [...prev, userMsg]);
    setChatInput("");
    setChatSending(true);
    try {
      const history = chatMessages.slice(-6).map((m) => ({ role: m.role, content: m.content }));
      const resp = await gameWorkbenchApi.suggest(
        aiAgentId,
        text,
        openTables,
        validChanges,
        history,
      );
      const sugs = resp.changes ?? [];
      // AI 提到的表自动打开 + 切到第一张作为 activeTab
      const tablesToOpen = Array.from(new Set(sugs.map((s) => s.table))).filter(
        (n) => n && !openTables.includes(n),
      );
      if (tablesToOpen.length > 0) {
        setOpenTables((prev) => [...prev, ...tablesToOpen]);
      }
      if (sugs.length > 0) {
        const firstSug = sugs[0];
        // 切到首条建议涉及的表 + 高亮 cell
        setActiveTab(firstSug.table);
        setSearchByTable((prev) => ({ ...prev, [firstSug.table]: String(firstSug.row_id) }));
        setHighlight({
          table: firstSug.table,
          row: String(firstSug.row_id),
          field: firstSug.field,
          ts: Date.now(),
        });
        syncWorkbenchRoute({
          session: sessionStore.currentId,
          table: firstSug.table,
          row: String(firstSug.row_id),
          field: firstSug.field,
        });
        window.setTimeout(() => setHighlight((h) => ({ ...h, ts: 0 })), 2000);
      }
      const assistantMsg: ChatMessage = {
        role: "assistant",
        content:
          resp.message ||
          (sugs.length
            ? t("gameWorkbench.aiGotN", {
                count: sugs.length,
                defaultValue: `已生成 ${sugs.length} 条建议，点击「接受写入」即可改进表。`,
              })
            : t("gameWorkbench.aiNoChange", {
                defaultValue: "AI 未返回可采纳的字段改动。",
              })),
        ts: Date.now(),
        suggestions: sugs.length ? sugs : undefined,
        acceptedKeys: [],
      };
      setChatMessages((prev) => [...prev, assistantMsg]);

      // 推 Chat 卡片到全局
      try {
        const tablesUsed = resp.context_summary?.main_tables ?? openTables;
        pushWorkbenchCard({
          id: `numeric-${Date.now()}`,
          agentId: selectedAgent,
          kind: "numeric_table",
          title:
            t("gameWorkbench.cardNumericTitle", {
              defaultValue: `数值查询：${text.slice(0, 30)}`,
            }) + (text.length > 30 ? "…" : ""),
          summary: [
            tablesUsed.length ? `表：${tablesUsed.join(", ")}` : "",
            sugs.length ? `建议：${sugs.length} 条` : "",
            resp.message ? resp.message.slice(0, 120) : "",
          ]
            .filter(Boolean)
            .join("\n"),
          href: tablesUsed[0]
            ? `/numeric-workbench?session=${encodeURIComponent(sessionStore.currentId)}&table=${encodeURIComponent(tablesUsed[0])}`
            : `/numeric-workbench?session=${encodeURIComponent(sessionStore.currentId)}`,
          payload: { tables: tablesUsed, changes: sugs, query_terms: resp.context_summary?.query_terms },
        });
      } catch {
        /* ignore */
      }
    } catch (err: unknown) {
      const msg = formatPermissionError(
        err,
        t("gameWorkbench.aiFailed", { defaultValue: "AI 调用失败" }),
      );
      setChatMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: isPermissionDeniedError(err)
            ? msg
            : t("gameWorkbench.aiFailed", { defaultValue: "AI 调用失败: " }) + msg,
          ts: Date.now(),
        },
      ]);
    } finally {
      setChatSending(false);
    }
  }, [chatInput, chatMessages, aiAgentId, openTables, validChanges, setChatMessages, t, selectedAgent, sessionStore.currentId, syncWorkbenchRoute, hasExplicitCapabilityContext, canReadWorkbench, message, workbenchReadReason, permissionDeniedMessage, formatPermissionError]);

  // ── 接受 AI 建议（写入 dirty） ────────────────────────
  const jumpToCell = useCallback(
    (tableName: string, rowId: string | number, field: string) => {
      if (!openTables.includes(tableName)) {
        setOpenTables((prev) => [...prev, tableName]);
      }
      const rowKey = String(rowId);
      setActiveTab(tableName);
      setSearchByTable((prev) => ({ ...prev, [tableName]: rowKey }));
      setHighlight({
        table: tableName,
        row: rowKey,
        field,
        ts: Date.now(),
      });
      syncWorkbenchRoute({
        session: sessionStore.currentId,
        table: tableName,
        row: rowKey,
        field,
      });
      window.setTimeout(() => setHighlight((h) => ({ ...h, ts: 0 })), 1800);
    },
    [openTables, sessionStore.currentId, syncWorkbenchRoute],
  );

  const findOriginValue = useCallback(
    (tableName: string, rowKey: string, field: string): unknown => {
      const data = rowsByTable[tableName];
      if (!data) return null;
      const fieldIdx = data.headers.indexOf(field);
      if (fieldIdx < 0) return null;
      const row = data.rows.find((r) => String(r[0]) === rowKey);
      if (!row) return null;
      return row[fieldIdx];
    },
    [rowsByTable],
  );

  const acceptSuggestion = useCallback(
    (msgIdx: number, sug: SuggestChange) => {
      const rowKey = String(sug.row_id);
      const detail = detailsByTable[sug.table];
      const fieldType = detail?.fields.find((f) => f.name === sug.field)?.type;
      const numeric = isNumericType(fieldType);
      const newValue: unknown =
        numeric && sug.new_value !== null && sug.new_value !== undefined
          ? Number(sug.new_value as number | string)
          : sug.new_value;
      const origin = findOriginValue(sug.table, rowKey, sug.field);
      dirty.setCell({
        table: sug.table,
        rowKey,
        field: sug.field,
        oldValue: origin,
        newValue: Number.isNaN(newValue as number) ? sug.new_value : newValue,
        source: "ai",
        reason: sug.reason,
      });
      const k = dirtyKeyOf(sug.table, rowKey, sug.field);
      setChatMessages((prev) =>
        prev.map((m, i) =>
          i === msgIdx
            ? { ...m, acceptedKeys: [...(m.acceptedKeys || []), k] }
            : m,
        ),
      );
      jumpToCell(sug.table, sug.row_id, sug.field);
      message.success(
        t("gameWorkbench.acceptedToCell", { defaultValue: "已写入单元格（AI 来源）" }),
      );
    },
    [detailsByTable, dirty, findOriginValue, jumpToCell, message, t],
  );

  const acceptAllSuggestions = useCallback(
    (msgIdx: number, sugs: SuggestChange[]) => {
      const acceptedKeys: string[] = [];
      sugs.forEach((sug) => {
        const rowKey = String(sug.row_id);
        const detail = detailsByTable[sug.table];
        const fieldType = detail?.fields.find((f) => f.name === sug.field)?.type;
        const numeric = isNumericType(fieldType);
        const nv: unknown =
          numeric && sug.new_value !== null && sug.new_value !== undefined
            ? Number(sug.new_value as number | string)
            : sug.new_value;
        const origin = findOriginValue(sug.table, rowKey, sug.field);
        dirty.setCell({
          table: sug.table,
          rowKey,
          field: sug.field,
          oldValue: origin,
          newValue: Number.isNaN(nv as number) ? sug.new_value : nv,
          source: "ai",
          reason: sug.reason,
        });
        acceptedKeys.push(dirtyKeyOf(sug.table, rowKey, sug.field));
      });
      setChatMessages((prev) =>
        prev.map((m, i) => (i === msgIdx ? { ...m, acceptedKeys } : m)),
      );
      message.success(
        t("gameWorkbench.acceptedAllToCell", {
          count: sugs.length,
          defaultValue: `已批量写入 ${sugs.length} 个单元格`,
        }),
      );
    },
    [detailsByTable, dirty, findOriginValue, message, t],
  );

  // ── 提交草稿 ─────────────────────────────────────────
  const openDraft = () => {
    if (!canExportWorkbench) {
      return;
    }
    if (validChanges.length === 0) {
      message.warning(t("gameWorkbench.noChangesToSubmit", { defaultValue: "没有可提交的修改" }));
      return;
    }
    const tables = Array.from(new Set(validChanges.map((c) => c.table))).join(",");
    setDraftTitle(
      t("gameWorkbench.defaultTitle", {
        tables,
        count: validChanges.length,
        defaultValue: `数值改动: ${tables} (${validChanges.length} 项)`,
      }),
    );
    setDraftDesc("");
    setDraftOpen(true);
  };

  const submitDraft = async () => {
    if (!selectedAgent) return;
    if (!canExportWorkbench) {
      message.warning(workbenchExportReason || permissionDeniedMessage);
      return;
    }
    setSubmitting(true);
    try {
      const ops = validChanges.map((c) => ({
        op: "update_cell" as const,
        table: c.table,
        row_id: c.row_id,
        field: c.field,
        new_value: c.new_value,
      }));
      const proposal = await gameChangeApi.create(selectedAgent, {
        title: draftTitle.trim() || "untitled",
        description: draftDesc,
        ops,
      });
      message.success(t("gameWorkbench.draftCreated", { defaultValue: "草案已生成" }));
      try {
        const draftTables = Array.from(new Set(validChanges.map((change) => change.table)));
        pushWorkbenchCard({
          id: `draft-${proposal.id}`,
          agentId: selectedAgent,
          kind: "draft_doc",
          title: proposal.title || t("gameWorkbench.draftCardTitle", { defaultValue: "数值改动草稿" }),
          summary: [
            t("gameWorkbench.draftCardSummaryCount", {
              defaultValue: `变更项：${ops.length}`,
            }),
            draftTables.length
              ? t("gameWorkbench.draftCardSummaryTables", {
                  defaultValue: `涉及表：${draftTables.join(", ")}`,
                })
              : "",
            proposal.status
              ? t("gameWorkbench.draftCardSummaryStatus", {
                  defaultValue: `状态：${proposal.status}`,
                })
              : "",
            draftDesc.trim()
              ? t("gameWorkbench.draftCardSummaryDesc", {
                  defaultValue: `说明：${draftDesc.trim().slice(0, 120)}`,
                })
              : "",
          ].filter(Boolean).join("\n"),
          href: "/chat",
          payload: {
            proposalId: proposal.id,
            status: proposal.status,
            opsCount: ops.length,
            tables: draftTables,
          },
        });
      } catch {
        /* ignore */
      }
      setDraftOpen(false);
    } catch (err) {
      message.error(
        formatPermissionError(
          err,
          t("gameWorkbench.draftCreateFailed", { defaultValue: "草案生成失败" }),
        ),
      );
    } finally {
      setSubmitting(false);
    }
  };

  const saveSession = useCallback(() => {
    const sessionName = sessionStore.current?.name || t("gameWorkbench.defaultSessionName", {
      defaultValue: "当前会话",
    });
    const savedAt = sessionStore.markCurrentSaved();
    if (!savedAt) return;
    message.success(
      t("gameWorkbench.sessionSaved", {
        defaultValue: `已保存到本地会话：${sessionName}`,
      }),
    );
  }, [message, sessionStore, t]);

  const draftPreviewTables = useMemo(
    () => Array.from(new Set(dirty.dirtyList.map((change) => change.table))),
    [dirty.dirtyList],
  );

  const draftPreviewChanges = useMemo(
    () => dirty.dirtyList.slice(0, 6),
    [dirty.dirtyList],
  );

  // ── Tab items（不分屏时） ─────────────────────────────
  const tabItems = useMemo(
    () =>
      openTables.map((tname) => ({
        key: tname,
        label: (
          <span
            onDoubleClick={(e) => {
              e.stopPropagation();
              if (pinnedTab === tname) {
                setPinnedTab(null);
              } else {
                if (activeTab === tname) {
                  const other = openTables.find((n) => n !== tname);
                  if (!other) {
                    message.info(
                      t("gameWorkbench.pinNeedTwoTabs", {
                        defaultValue: "需要至少 2 张表才能分屏",
                      }),
                    );
                    return;
                  }
                  setActiveTab(other);
                }
                setPinnedTab(tname);
              }
            }}
          >
            {tname}
            {pinnedTab === tname && <PushpinFilled style={{ marginLeft: 4, color: "#1677ff" }} />}
          </span>
        ),
        children: renderTablePane(tname),
      })),
    [openTables, pinnedTab, activeTab, message, t, renderTablePane],
  );

  if (!isWorkbenchView) {
    if (workbenchReadReason) {
      return (
        <div className={styles.sessionListPage}>
          <PageHeader
            parent={t("nav.game", { defaultValue: "Game Development" })}
            current={t("nav.gameWorkbench", { defaultValue: "数值工作台" })}
          />
          <Card className={styles.sessionHero}>
            <Alert type="info" showIcon message={workbenchReadReason} />
          </Card>
        </div>
      );
    }
    return (
      <div className={styles.sessionListPage}>
        <PageHeader
          parent={t("nav.game", { defaultValue: "Game Development" })}
          current={t("nav.gameWorkbench", { defaultValue: "数值工作台" })}
          subRow={
            <Text type="secondary" style={{ fontSize: 12 }}>
              {t("gameWorkbench.sessionListSubtitle", {
                defaultValue: "选择一个调值会话继续工作，或新建一个本地会话开始调值。",
              })}
            </Text>
          }
          extra={
            <Button type="primary" onClick={createAndOpenSession}>
              {t("gameWorkbench.createSession", { defaultValue: "新建会话" })}
            </Button>
          }
        />

        <Card className={styles.sessionHero}>
          <Space direction="vertical" size={4}>
            <Text strong style={{ fontSize: 18 }}>
              {t("gameWorkbench.sessionListTitle", { defaultValue: "继续一个调值会话" })}
            </Text>
            <Text type="secondary">
              {t("gameWorkbench.sessionListDesc", {
                defaultValue: "会话会恢复你上次打开的表、修改条目与 AI 对话上下文。",
              })}
            </Text>
            <Text type="secondary">
              {t("gameWorkbench.sessionListBoundary", {
                defaultValue: "仅用于 draft 和 dry-run，不会自动发布，也不会写入 formal knowledge release。",
              })}
            </Text>
          </Space>
        </Card>

        <div className={styles.sessionGrid}>
          {sessionStore.sessions.map((session) => (
            <Card
              key={session.id}
              className={styles.sessionCard}
              hoverable
              onClick={() => openSession(session.id)}
            >
              <div className={styles.sessionCardTop}>
                <Space direction="vertical" size={4}>
                  <Text strong>{session.name}</Text>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    {t("gameWorkbench.sessionBaseline", {
                      defaultValue: "基线 revision：本地会话",
                    })}
                  </Text>
                </Space>
                <Tag color={session.id === sessionStore.currentId ? "blue" : "default"}>
                  {session.id === sessionStore.currentId
                    ? t("gameWorkbench.currentSession", { defaultValue: "当前" })
                    : t("gameWorkbench.savedSession", { defaultValue: "已保存" })}
                </Tag>
              </div>
              <div className={styles.sessionMetaRow}>
                <Tag color={session.updatedAt > (session.lastManualSavedAt ?? 0) ? "volcano" : "green"}>
                  {session.updatedAt > (session.lastManualSavedAt ?? 0)
                    ? t("gameWorkbench.sessionPendingSave", { defaultValue: "待保存" })
                    : t("gameWorkbench.sessionSavedState", { defaultValue: "已手动保存" })}
                </Tag>
                <Tag color="orange">
                  {t("gameWorkbench.sessionDirtyCount", {
                    defaultValue: `${session.dirtyCells.length} 项修改`,
                  })}
                </Tag>
                <Tag>
                  {t("gameWorkbench.sessionTableCount", {
                    defaultValue: `${session.openTables.length} 张表`,
                  })}
                </Tag>
                <Tag color="purple">
                  {t("gameWorkbench.sessionMessageCount", {
                    defaultValue: `${session.messages.length} 条对话`,
                  })}
                </Tag>
              </div>
              <Text type="secondary" style={{ fontSize: 12 }}>
                {t("gameWorkbench.sessionUpdatedAt", {
                  defaultValue: `上次编辑：${new Date(session.updatedAt).toLocaleString()}`,
                })}
              </Text>
              <Text type="secondary" style={{ fontSize: 12 }}>
                {t("gameWorkbench.sessionSavedAt", {
                  defaultValue: `上次保存：${new Date(session.lastManualSavedAt ?? session.updatedAt).toLocaleString()}`,
                })}
              </Text>
              <div className={styles.sessionCardFooter}>
                <Space>
                  <Button
                    danger
                    icon={<DeleteOutlined />}
                    disabled={sessionStore.sessions.length <= 1}
                    onClick={(e) => {
                      e.stopPropagation();
                      confirmRemoveSession(
                        session.id,
                        session.name,
                        session.updatedAt > (session.lastManualSavedAt ?? 0),
                      );
                    }}
                  >
                    {t("gameWorkbench.removeSession", { defaultValue: "删除" })}
                  </Button>
                  <Button type="primary" onClick={(e) => {
                    e.stopPropagation();
                    openSession(session.id);
                  }}>
                    {t("gameWorkbench.resumeSession", { defaultValue: "继续会话" })}
                  </Button>
                </Space>
              </div>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className={styles.workbench}>
      <PageHeader
        parent={t("nav.game", { defaultValue: "Game Development" })}
        current={sessionStore.current?.name || t("nav.gameWorkbench", { defaultValue: "数值工作台" })}
        extra={
          <Space>
            <Button onClick={backToSessionList}>
              {t("gameWorkbench.backToSessions", { defaultValue: "返回会话列表" })}
            </Button>
            <Button
              danger
              disabled={sessionStore.sessions.length <= 1 || !sessionStore.current}
              onClick={() => {
                if (!sessionStore.current) return;
                confirmRemoveSession(
                  sessionStore.current.id,
                  sessionStore.current.name,
                  sessionStore.isCurrentDirtySinceSave,
                );
              }}
            >
              {t("gameWorkbench.removeCurrentSession", { defaultValue: "删除当前会话" })}
            </Button>
            <Button type="primary" onClick={saveSession} disabled={!sessionStore.isCurrentDirtySinceSave}>
              {t("gameWorkbench.saveSession", { defaultValue: "保存当前会话" })}
            </Button>
          </Space>
        }
        subRow={
          <Text type="secondary" style={{ fontSize: 12 }}>
            {t("gameWorkbench.subtitleV2", {
              defaultValue: "下方 Chat 描述意图 → 上方表内直接改 → 右栏看依赖与影响 → 仅生成 draft，不会自动发布",
            })}
          </Text>
        }
      />

      {workbenchReadReason ? (
        <Card>
          <Alert type="info" showIcon message={workbenchReadReason} />
        </Card>
      ) : null}

      <div className={styles.workbenchShell}>
        <div className={styles.editorArea}>
          <div className={styles.toolbar}>
            <Select
              mode="multiple"
              placeholder={t("gameWorkbench.tablePlaceholder", {
                defaultValue: "选择要打开的表（可多选）",
              })}
              loading={tablesLoading}
              value={openTables}
              onChange={(nextOpenTables) => {
                setOpenTables(nextOpenTables);
                if (nextOpenTables.length === 0) {
                  syncWorkbenchRoute({ session: sessionStore.currentId });
                  return;
                }
                const nextActiveTab =
                  activeTab && nextOpenTables.includes(activeTab)
                    ? activeTab
                    : nextOpenTables[0];
                if (nextActiveTab) {
                  syncWorkbenchRoute({
                    session: sessionStore.currentId,
                    table: nextActiveTab,
                  });
                }
              }}
              style={{ minWidth: 360 }}
              showSearch
              allowClear
              disabled={!canReadWorkbench}
              options={tableNames.map((n) => ({ label: n, value: n }))}
            />
            <Button icon={<ReloadOutlined />} onClick={loadTables} loading={tablesLoading} disabled={!canReadWorkbench}>
              {t("gameWorkbench.refresh", { defaultValue: "刷新" })}
            </Button>
            {rowsLoading && <Spin size="small" />}
          </div>

          {!workbenchReadReason ? (
            <div className={styles.statusStack}>
              <div className={`${styles.compactStatusBar} ${styles.workbenchStatusBar}`}>
                <div className={styles.statusPrimaryRow}>
                  <Space size={[6, 6]} wrap>
                    <Tag color="gold">
                      {t("gameWorkbench.boundaryDraftOnlyTag", { defaultValue: "Draft-only" })}
                    </Tag>
                    <Tag>
                      {t("gameWorkbench.boundaryDryRunTag", { defaultValue: "Dry-run" })}
                    </Tag>
                    <Tag color={sessionStore.isCurrentDirtySinceSave ? "volcano" : "green"}>
                      {workbenchPendingLabel}
                    </Tag>
                    <Tag color="blue">
                      {t("gameWorkbench.dirtyTotalTag", {
                        count: dirty.dirtyList.length,
                        defaultValue: `当前 ${dirty.dirtyList.length} 项待保存`,
                      })}
                    </Tag>
                  </Space>
                </div>
                <div className={styles.statusSecondaryRow}>
                  <Text type="secondary">
                    {t("gameWorkbench.boundaryNoticeCompact", {
                      defaultValue: "No auto-publish. No formal knowledge release write. Save and export behavior stays manual.",
                    })}
                  </Text>
                </div>
              </div>

              {citationContext ? (
                <div
                  className={`${styles.compactStatusBar} ${styles.citationStatusBar} ${
                    citationTargetSummary?.tone === "success"
                      ? styles.statusSuccess
                      : citationTargetSummary?.tone === "warning"
                        ? styles.statusWarning
                        : citationTargetSummary?.tone === "danger"
                          ? styles.statusDanger
                          : styles.statusInfo
                  }`}
                >
                  <div className={styles.statusPrimaryRow}>
                    <Space size={[6, 6]} wrap>
                      <Tag color="blue">
                        {t("gameWorkbench.citationContextTitle", {
                          defaultValue: "Opened from a RAG citation",
                        })}
                      </Tag>
                      {citationContext.table ? (
                        <Tag>
                          {t("gameWorkbench.citationContextTable", {
                            table: citationContext.table,
                            defaultValue: `table: ${citationContext.table}`,
                          })}
                        </Tag>
                      ) : null}
                      {citationContext.row ? (
                        <Tag>
                          {t("gameWorkbench.citationContextRow", {
                            row: citationContext.row,
                            defaultValue: `row: ${citationContext.row}`,
                          })}
                        </Tag>
                      ) : null}
                      {citationContext.field ? (
                        <Tag>
                          {t("gameWorkbench.citationContextField", {
                            field: citationContext.field,
                            defaultValue: `field: ${citationContext.field}`,
                          })}
                        </Tag>
                      ) : null}
                      {citationContext.citationId ? <Tag>{citationContext.citationId}</Tag> : null}
                    </Space>
                  </div>
                  <div className={styles.statusSecondaryRow}>
                    {citationSourceLabel ? (
                      <Text type="secondary" className={styles.statusSummary}>
                        {citationSourceLabel}
                      </Text>
                    ) : null}
                    {citationTargetSummary ? (
                      <Text className={styles.statusSummaryStrong}>
                        {citationTargetSummary.title}
                        {citationTargetSummary.detail ? ` ${citationTargetSummary.detail}` : ""}
                      </Text>
                    ) : null}
                  </div>
                </div>
              ) : null}
            </div>
          ) : null}

          <div className={styles.split} ref={splitContainerRef}>
            <Card
              className={styles.upperPane}
              style={{ flex: `${topRatio} 1 0` }}
              styles={{ body: { padding: 0, flex: 1, overflow: "hidden", display: "flex", flexDirection: "column" } }}
              title={
                <Space>
                  <span>
                    {t("gameWorkbench.tablesViewTitle", { defaultValue: "多表编辑视图" })}
                  </span>
                  {pinnedTab && (
                    <Tag color="purple" icon={<PushpinFilled />}>
                      {t("gameWorkbench.pinnedTag", {
                        defaultValue: `分屏中：${activeTab} ↔ ${pinnedTab}`,
                      })}
                    </Tag>
                  )}
                </Space>
              }
            >
          {openTables.length === 0 ? (
            <Empty
              style={{ padding: 24 }}
              description={t("gameWorkbench.emptyTablesView", {
                defaultValue: "请在工具栏选择目标表，或在下方 Chat 描述意图让 AI 自动打开相关表",
              })}
            />
          ) : pinnedTab && activeTab && pinnedTab !== activeTab ? (
            <div className={styles.pinnedSplit}>
              <div className={styles.pinnedHalf}>
                <div className={styles.pinnedTabHeader}>
                  <Space>
                    <Tag>{activeTab}</Tag>
                    <Text type="secondary" style={{ fontSize: 11 }}>
                      {t("gameWorkbench.mainPaneLabel", { defaultValue: "主表" })}
                    </Text>
                  </Space>
                </div>
                {renderTablePane(activeTab, true)}
              </div>
              <div className={styles.pinnedHalf}>
                <div className={styles.pinnedTabHeader}>
                  <Space>
                    <Tag color="purple" icon={<PushpinFilled />}>{pinnedTab}</Tag>
                    <Text type="secondary" style={{ fontSize: 11 }}>
                      {t("gameWorkbench.pinnedPaneLabel", { defaultValue: "钉选副表" })}
                    </Text>
                  </Space>
                  <Button
                    size="small"
                    type="text"
                    icon={<PushpinFilled />}
                    onClick={() => setPinnedTab(null)}
                  >
                    {t("gameWorkbench.unpin", { defaultValue: "取消钉选" })}
                  </Button>
                </div>
                {renderTablePane(pinnedTab, true)}
              </div>
            </div>
          ) : (
            <Tabs
              type="editable-card"
              hideAdd
              activeKey={activeTab ?? undefined}
              onChange={(nextActiveTab) => {
                setActiveTab(nextActiveTab);
                syncWorkbenchRoute({
                  session: sessionStore.currentId,
                  table: nextActiveTab,
                });
              }}
              onEdit={(targetKey, action) => {
                if (action === "remove" && typeof targetKey === "string") {
                  const nextOpenTables = openTables.filter((n) => n !== targetKey);
                  setOpenTables(nextOpenTables);
                  dirty.clearTable(targetKey);
                  if (pinnedTab === targetKey) setPinnedTab(null);
                  if (nextOpenTables.length === 0) {
                    syncWorkbenchRoute({ session: sessionStore.currentId });
                    return;
                  }
                  const nextActiveTab =
                    targetKey === activeTab ? nextOpenTables[0] : activeTab ?? nextOpenTables[0];
                  if (nextActiveTab) {
                    syncWorkbenchRoute({
                      session: sessionStore.currentId,
                      table: nextActiveTab,
                    });
                  }
                }
              }}
              items={tabItems}
              tabBarStyle={{ paddingLeft: 12, marginBottom: 0 }}
              className={styles.tablesTabs}
              style={{ flex: 1, display: "flex", flexDirection: "column", minHeight: 0 }}
            />
          )}
            </Card>

            <div className={styles.splitter} onMouseDown={onSplitterMouseDown} role="separator" />

            <Card
              className={styles.lowerPane}
              style={{ flex: `${1 - topRatio} 1 0` }}
              styles={{ body: { padding: 0, flex: 1, overflow: "hidden", display: "flex", flexDirection: "column" } }}
            >
              <WorkbenchChat
                messages={chatMessages}
                input={chatInput}
                sending={chatSending}
                disabled={!canReadWorkbench}
                placeholder={workbenchReadReason || undefined}
                onInputChange={setChatInput}
                onSend={sendChat}
                onAcceptSuggestion={(sug) => {
                  const idx = chatMessages.findIndex((m) => m.suggestions?.includes(sug));
                  if (idx >= 0) acceptSuggestion(idx, sug);
                }}
                onAcceptAll={(sugs) => {
                  const idx = chatMessages.findIndex((m) => m.suggestions === sugs);
                  if (idx >= 0) acceptAllSuggestions(idx, sugs);
                }}
                onJumpToCell={jumpToCell}
                onClear={sessionStore.clearCurrentMessages}
                headerExtra={
                  <Space size={4}>
                    <Tooltip title={t("gameWorkbench.workbenchAgent", { defaultValue: "工作台专属 Agent（决定 AI 主模型）" })}>
                      <Select
                        size="small"
                        value={workbenchAgentOverride || ""}
                        style={{ minWidth: 140 }}
                        onChange={(v) => setWorkbenchAgentOverride(v)}
                        options={[
                          {
                            value: "",
                            label: t("gameWorkbench.followGlobalAgent", {
                              defaultValue: "跟随全局 Agent",
                            }),
                          },
                          ...agents.map((a) => ({ value: a.id, label: a.name || a.id })),
                        ]}
                      />
                    </Tooltip>
                    <ModelSelector agentId={aiAgentId} disableRouteSync />
                  </Space>
                }
                subHeader={
                  <WorkbenchChatSessionToolbar
                    sessions={sessionStore.sessions}
                    currentId={sessionStore.currentId}
                    currentDirty={sessionStore.isCurrentDirtySinceSave}
                    onSwitch={openSession}
                    onNew={createAndOpenSession}
                    onRename={sessionStore.renameSession}
                    onRemove={(id) => {
                      const target = sessionStore.sessions.find((session) => session.id === id);
                      if (!target) return;
                      confirmRemoveSession(
                        target.id,
                        target.name,
                        id === sessionStore.currentId
                          ? sessionStore.isCurrentDirtySinceSave
                          : target.updatedAt > (target.lastManualSavedAt ?? 0),
                      );
                    }}
                  />
                }
              />
            </Card>
          </div>
        </div>

        <aside className={styles.sidePanel}>
          <div className={styles.sidePanelHeader}>
            <Space>
              <RobotOutlined />
              <Text strong>
                {t("gameWorkbench.rightPanelTitle", { defaultValue: "修改 / 影响 / AI 建议" })}
              </Text>
            </Space>
            {activeTab && <Tag>{activeTab}</Tag>}
          </div>
          <div className={styles.aiDrawerBody}>
          <DirtyList
            items={dirty.dirtyList}
            onJump={(table, rowKey, field) => jumpToCell(table, rowKey, field)}
            onRevert={(table, rowKey, field) => dirty.clearCell(table, rowKey, field)}
            onClearAll={dirty.clearAll}
            onSaveSession={saveSession}
            saveSessionDisabled={!sessionStore.isCurrentDirtySinceSave}
            onExportDraft={openDraft}
            exporting={submitting}
            exportDisabled={validChanges.length === 0 || !canExportWorkbench}
            exportDisabledReason={workbenchExportReason || undefined}
          />
          <ImpactPanel
            preview={preview}
            previewLoading={previewLoading}
            damageChain={damageChain}
            damageChainLoading={damageChainLoading}
            affectedTables={affectedTables}
            impacts={impacts}
            reverseImpact={null}
          />
          </div>
        </aside>
      </div>

      <Modal
        title={t("gameWorkbench.draftModalTitle", { defaultValue: "导出变更草稿" })}
        open={draftOpen}
        onOk={submitDraft}
        onCancel={() => setDraftOpen(false)}
        confirmLoading={submitting}
        okButtonProps={{ disabled: !canWriteWorkbench }}
        okText={t("gameWorkbench.export", { defaultValue: "导出" })}
        cancelText={t("gameWorkbench.cancel", { defaultValue: "取消" })}
      >
        {workbenchWriteReason ? <Alert type="info" showIcon message={workbenchWriteReason} style={{ marginBottom: 16 }} /> : null}
        <Space direction="vertical" style={{ width: "100%" }}>
          <Text type="secondary">
            {t("gameWorkbench.draftModalBoundary", {
              defaultValue: "This exports a draft proposal only. It does not publish automatically or write formal knowledge release.",
            })}
          </Text>
          <Text>{t("gameWorkbench.draftTitleLabel", { defaultValue: "标题" })}</Text>
          <Input value={draftTitle} onChange={(e) => setDraftTitle(e.target.value)} />
          <Text>{t("gameWorkbench.draftDescLabel", { defaultValue: "说明" })}</Text>
          <Input.TextArea
            value={draftDesc}
            onChange={(e) => setDraftDesc(e.target.value)}
            rows={4}
          />
          <Text type="secondary">
            {t("gameWorkbench.draftSummary", {
              count: validChanges.length,
              defaultValue: `共 ${validChanges.length} 项修改`,
            })}
          </Text>
          <Card size="small" title={t("gameWorkbench.draftPreviewTitle", { defaultValue: "导出预览" })}>
            <Space direction="vertical" size={8} style={{ width: "100%" }}>
              <Space size={[6, 6]} wrap>
                {draftPreviewTables.map((tableName) => (
                  <Tag key={tableName} color="gold">
                    {tableName}
                  </Tag>
                ))}
              </Space>
              {draftPreviewChanges.map((change, index) => (
                <div key={`${change.table}-${change.rowKey}-${change.field}-${index}`}>
                  <Text strong>
                    {change.table} / {String(change.rowKey)} / {change.field}
                  </Text>
                  <br />
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    {formatVal(change.oldValue)} -&gt; {formatVal(change.newValue)}
                  </Text>
                </div>
              ))}
              {validChanges.length > draftPreviewChanges.length && (
                <Text type="secondary" style={{ fontSize: 12 }}>
                  {t("gameWorkbench.draftPreviewMore", {
                    defaultValue: `其余 ${validChanges.length - draftPreviewChanges.length} 项将在导出时一并带上。`,
                  })}
                </Text>
              )}
            </Space>
          </Card>
        </Space>
      </Modal>
    </div>
  );
}

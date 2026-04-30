import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  Button,
  Card,
  Drawer,
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
  const { selectedAgent } = useAgentStore();
  const [searchParams] = useSearchParams();

  // Deep-link
  const dlTable = searchParams.get("table") || searchParams.get("tableId") || "";
  const dlRow = searchParams.get("row") || searchParams.get("rowId") || "";
  const dlField = searchParams.get("field") || searchParams.get("fieldKey") || "";

  const [tableNames, setTableNames] = useState<string[]>([]);
  const [tablesLoading, setTablesLoading] = useState(false);
  const [openTables, setOpenTables] = useState<string[]>([]);
  const [activeTab, setActiveTab] = useState<string | null>(null);
  /** Tab 钉选：当存在 pinnedTab 时，上区横向分屏（左 activeTab / 右 pinnedTab） */
  const [pinnedTab, setPinnedTab] = useState<string | null>(null);
  const [detailsByTable, setDetailsByTable] = useState<Record<string, TableIndex>>({});
  const [rowsByTable, setRowsByTable] = useState<Record<string, RowsData>>({});
  const [rowsLoading, setRowsLoading] = useState(false);
  const [searchByTable, setSearchByTable] = useState<Record<string, string>>({});

  // 高亮（来自 deep-link 或「定位」按钮）
  const [highlight, setHighlight] = useState<{
    table?: string;
    field?: string;
    row?: string;
    ts: number;
  }>({ ts: 0 });

  // 单元格编辑态（同时只允许一个）
  const [editing, setEditing] = useState<CellEditState | null>(null);

  // 工作台 Chat（独立会话）
  const [chatInput, setChatInput] = useState("");
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatSending, setChatSending] = useState(false);

  // dirty 状态 hook
  const dirty = useDirtyCells();

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

  // ── 加载表 ─────────────────────────────────────────────
  const loadTables = useCallback(async () => {
    if (!selectedAgent) {
      setTableNames([]);
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
    }
  }, [selectedAgent, message, t]);

  const loadTableDetail = useCallback(
    async (name: string) => {
      if (!selectedAgent) return;
      try {
        const detail = await gameApi.getTable(selectedAgent, name);
        setDetailsByTable((prev) => ({ ...prev, [name]: detail }));
      } catch {
        /* ignore */
      }
    },
    [selectedAgent],
  );

  const loadRowsForTable = useCallback(
    async (name: string) => {
      if (!selectedAgent) return;
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
    [selectedAgent],
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

  // 切换 activeTab → 拉一次结构化面板（用于范围校验）
  useEffect(() => {
    if (!selectedAgent || !activeTab) {
      setAiPanel(null);
      return;
    }
    let cancelled = false;
    gameWorkbenchApi
      .aiSuggestPanel(selectedAgent, activeTab, undefined)
      .then((p) => { if (!cancelled) setAiPanel(p); })
      .catch(() => { if (!cancelled) setAiPanel(null); });
    return () => { cancelled = true; };
  }, [selectedAgent, activeTab]);

  // dirty → debounced preview + reverse-impact
  const validChanges = dirty.validChanges;
  const runPreview = useCallback(async () => {
    if (!selectedAgent) return;
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
  }, [selectedAgent, validChanges, message, t]);

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
      _rIdx: number,
    ) => {
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
    if (!text || !selectedAgent) return;
    const userMsg: ChatMessage = { role: "user", content: text, ts: Date.now() };
    setChatMessages((prev) => [...prev, userMsg]);
    setChatInput("");
    setChatSending(true);
    try {
      const history = chatMessages.slice(-6).map((m) => ({ role: m.role, content: m.content }));
      const resp = await gameWorkbenchApi.suggest(
        selectedAgent,
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
            ? `/numeric-workbench?table=${encodeURIComponent(tablesUsed[0])}`
            : "/numeric-workbench",
          payload: { tables: tablesUsed, changes: sugs, query_terms: resp.context_summary?.query_terms },
        });
      } catch {
        /* ignore */
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setChatMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: t("gameWorkbench.aiFailed", { defaultValue: "AI 调用失败: " }) + msg,
          ts: Date.now(),
        },
      ]);
    } finally {
      setChatSending(false);
    }
  }, [chatInput, chatMessages, selectedAgent, openTables, validChanges, t]);

  // ── 接受 AI 建议（写入 dirty） ────────────────────────
  const jumpToCell = useCallback(
    (tableName: string, rowId: string | number, field: string) => {
      if (!openTables.includes(tableName)) {
        setOpenTables((prev) => [...prev, tableName]);
      }
      setActiveTab(tableName);
      setSearchByTable((prev) => ({ ...prev, [tableName]: String(rowId) }));
      setHighlight({
        table: tableName,
        row: String(rowId),
        field,
        ts: Date.now(),
      });
      window.setTimeout(() => setHighlight((h) => ({ ...h, ts: 0 })), 1800);
    },
    [openTables],
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
    setSubmitting(true);
    try {
      const ops = validChanges.map((c) => ({
        op: "update_cell" as const,
        table: c.table,
        row_id: c.row_id,
        field: c.field,
        new_value: c.new_value,
      }));
      await gameChangeApi.create(selectedAgent, {
        title: draftTitle.trim() || "untitled",
        description: draftDesc,
        ops,
      });
      message.success(t("gameWorkbench.draftCreated", { defaultValue: "草案已生成" }));
      setDraftOpen(false);
      dirty.clearAll();
    } catch {
      message.error(t("gameWorkbench.draftCreateFailed", { defaultValue: "草案生成失败" }));
    } finally {
      setSubmitting(false);
    }
  };

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

  return (
    <div className={styles.workbench}>
      <PageHeader
        parent={t("nav.game", { defaultValue: "Game Development" })}
        current={t("nav.gameWorkbench", { defaultValue: "数值工作台" })}
        subRow={
          <Text type="secondary" style={{ fontSize: 12 }}>
            {t("gameWorkbench.subtitleV2", {
              defaultValue: "下方 Chat 描述意图 → 上方表内直接改 → 右栏看依赖与影响 → 一键提交",
            })}
          </Text>
        }
      />

      <div className={styles.toolbar}>
        <Select
          mode="multiple"
          placeholder={t("gameWorkbench.tablePlaceholder", {
            defaultValue: "选择要打开的表（可多选）",
          })}
          loading={tablesLoading}
          value={openTables}
          onChange={(v) => setOpenTables(v)}
          style={{ minWidth: 360 }}
          showSearch
          allowClear
          options={tableNames.map((n) => ({ label: n, value: n }))}
        />
        <Button icon={<ReloadOutlined />} onClick={loadTables} loading={tablesLoading}>
          {t("gameWorkbench.refresh", { defaultValue: "刷新" })}
        </Button>
        <Tag color="blue">
          {t("gameWorkbench.dirtyTotalTag", {
            count: dirty.dirtyList.length,
            defaultValue: `当前 ${dirty.dirtyList.length} 项待保存`,
          })}
        </Tag>
        {rowsLoading && <Spin size="small" />}
      </div>

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
              onChange={setActiveTab}
              onEdit={(targetKey, action) => {
                if (action === "remove" && typeof targetKey === "string") {
                  setOpenTables((prev) => prev.filter((n) => n !== targetKey));
                  dirty.clearTable(targetKey);
                  if (pinnedTab === targetKey) setPinnedTab(null);
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
            onClear={() => setChatMessages([])}
          />
        </Card>
      </div>

      <Drawer
        title={
          <Space>
            <RobotOutlined />
            <span>
              {t("gameWorkbench.rightPanelTitle", { defaultValue: "依赖 / 影响 / 修改条目" })}
            </span>
            {activeTab && <Tag>{activeTab}</Tag>}
          </Space>
        }
        placement="right"
        width={460}
        open
        closable={false}
        mask={false}
        getContainer={false}
        rootStyle={{ position: "absolute" }}
        styles={{ wrapper: { boxShadow: "-2px 0 8px rgba(0,0,0,0.06)" } }}
      >
        <div className={styles.aiDrawerBody}>
          <DirtyList
            items={dirty.dirtyList}
            onJump={(table, rowKey, field) => jumpToCell(table, rowKey, field)}
            onRevert={(table, rowKey, field) => dirty.clearCell(table, rowKey, field)}
            onClearAll={dirty.clearAll}
            onSave={openDraft}
            saving={submitting}
            saveDisabled={validChanges.length === 0}
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
      </Drawer>

      <Modal
        title={t("gameWorkbench.draftModalTitle", { defaultValue: "生成改动草案" })}
        open={draftOpen}
        onOk={submitDraft}
        onCancel={() => setDraftOpen(false)}
        confirmLoading={submitting}
        okText={t("gameWorkbench.submit", { defaultValue: "提交" })}
        cancelText={t("gameWorkbench.cancel", { defaultValue: "取消" })}
      >
        <Space direction="vertical" style={{ width: "100%" }}>
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
        </Space>
      </Modal>
    </div>
  );
}

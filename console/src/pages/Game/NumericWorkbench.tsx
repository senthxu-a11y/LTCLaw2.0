import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  Avatar,
  Button,
  Card,
  Drawer,
  Empty,
  Input,
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
  CheckCircleTwoTone,
  CloseCircleTwoTone,
  DeleteOutlined,
  PlusOutlined,
  ReloadOutlined,
  RobotOutlined,
  SaveOutlined,
  SendOutlined,
} from "@ant-design/icons";
import { useTranslation } from "react-i18next";
import { PageHeader } from "@/components/PageHeader";
import { useAppMessage } from "@/hooks/useAppMessage";
import { useAgentStore } from "../../stores/agentStore";
import { gameApi } from "../../api/modules/game";
import { gameChangeApi } from "../../api/modules/gameChange";
import { gameWorkbenchApi } from "../../api/modules/gameWorkbench";
import type { FieldChange, PreviewItem, SuggestChange } from "../../api/modules/gameWorkbench";
import type { TableIndex } from "../../api/types/game";
import { pushWorkbenchCard } from "../Chat/workbenchCardChannel";
import styles from "./NumericWorkbench.module.less";

const { Text } = Typography;

interface PendingRow {
  key: string;
  table: string;
  row_id: string;
  field: string;
  new_value: string;
}

const formatValue = (value: unknown): string => {
  if (value === null || value === undefined) return "—";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
};

const newRow = (table: string): PendingRow => ({
  key: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
  table,
  row_id: "",
  field: "",
  new_value: "",
});

export default function NumericWorkbench() {
  const { t } = useTranslation();
  const { message } = useAppMessage();
  const { selectedAgent } = useAgentStore();

  const [tableNames, setTableNames] = useState<string[]>([]);
  const [tablesLoading, setTablesLoading] = useState(false);
  const [openTables, setOpenTables] = useState<string[]>([]);
  const [activeTab, setActiveTab] = useState<string | null>(null);
  const activeTable = activeTab;
  const [detailsByTable, setDetailsByTable] = useState<Record<string, TableIndex>>({});
  const [detailLoading, setDetailLoading] = useState(false);


  const [rowsByTable, setRowsByTable] = useState<
    Record<string, { headers: string[]; rows: (string | number | boolean)[][]; total: number }>
  >({});
  const [rowsLoading, setRowsLoading] = useState(false);
  const [searchByTable, setSearchByTable] = useState<Record<string, string>>({});

  // 右侧抽屉 + 下边聊天
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [chatInput, setChatInput] = useState("");
  const [chatMessages, setChatMessages] = useState<
    { role: "user" | "assistant"; content: string; ts: number }[]
  >([]);
  const [chatSending, setChatSending] = useState(false);
  // AI 建议结果
  const [aiSuggestions, setAiSuggestions] = useState<SuggestChange[]>([]);
  const [aiMessage, setAiMessage] = useState<string>("");

  // 左右分割比例（左侧占比）
  const [topRatio, setTopRatio] = useState(0.6);
  const splitContainerRef = useRef<HTMLDivElement>(null);
  const draggingRef = useRef(false);

  const [pending, setPending] = useState<PendingRow[]>([]);
  const [preview, setPreview] = useState<PreviewItem[]>([]);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const [draftOpen, setDraftOpen] = useState(false);
  const [draftTitle, setDraftTitle] = useState("");
  const [draftDesc, setDraftDesc] = useState("");

  const debounceRef = useRef<number | null>(null);

  const loadTables = useCallback(async () => {
    if (!selectedAgent) {
      setTableNames([]);
      return;
    }
    setTablesLoading(true);
    try {
      const resp = await gameApi.listTables(selectedAgent, { page: 1, size: 200 });
      const names = resp.items.map((it) => it.table_name);
      setTableNames(names);
      // 不再默认选中任何表，避免误把第一张表当成用户选择
    } catch {
      message.error(t("gameWorkbench.loadTablesFailed", { defaultValue: "加载表列表失败" }));
    } finally {
      setTablesLoading(false);
    }
  }, [selectedAgent, message, t]);

  const loadTableDetail = useCallback(async (name: string) => {
    if (!selectedAgent) return;
    setDetailLoading(true);
    try {
      const detail = await gameApi.getTable(selectedAgent, name);
      setDetailsByTable((prev) => ({ ...prev, [name]: detail }));
    } catch {
      message.error(t("gameWorkbench.loadDetailFailed", { defaultValue: "加载表详情失败" }));
    } finally {
      setDetailLoading(false);
    }
  }, [selectedAgent, message, t]);

  useEffect(() => { loadTables(); }, [loadTables]);
  // 为新打开但还没加载详情/行的表自动加载
  useEffect(() => {
    openTables.forEach((name) => {
      if (!detailsByTable[name]) loadTableDetail(name);
    });
  }, [openTables, detailsByTable, loadTableDetail]);

  // \u8868\u5b9e\u9645\u5185\u5bb9\u52a0\u8f7d
  const loadRowsForTable = useCallback(
    async (name: string) => {
      if (!selectedAgent) return;
      setRowsLoading(true);
      try {
        const resp = await gameApi.getTableRows(selectedAgent, name, 0, 200);
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

  // 为打开的表自动加载行数据；activeTab 不在 openTables 时同步
  useEffect(() => {
    openTables.forEach((name) => {
      if (!rowsByTable[name]) loadRowsForTable(name);
    });
    if (openTables.length === 0) {
      setActiveTab(null);
    } else if (!activeTab || !openTables.includes(activeTab)) {
      setActiveTab(openTables[0]);
    }
  }, [openTables, activeTab, rowsByTable, loadRowsForTable]);

  // 分割拖拽（水平）
  const onSplitterMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    draggingRef.current = true;
    const onMove = (ev: MouseEvent) => {
      if (!draggingRef.current || !splitContainerRef.current) return;
      const rect = splitContainerRef.current.getBoundingClientRect();
      const ratio = (ev.clientX - rect.left) / rect.width;
      setTopRatio(Math.max(0.2, Math.min(0.8, ratio)));
    };
    const onUp = () => {
      draggingRef.current = false;
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseup", onUp);
    };
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup", onUp);
  };

  const validChanges: FieldChange[] = useMemo(() => {
    return pending
      .filter((p) => p.row_id !== "" && p.field !== "")
      .map((p) => {
        let value: unknown = p.new_value;
        if (p.new_value !== "" && !Number.isNaN(Number(p.new_value))) {
          value = Number(p.new_value);
        }
        const rowIdNum = Number(p.row_id);
        const rowId = Number.isFinite(rowIdNum) && String(rowIdNum) === p.row_id
          ? rowIdNum
          : p.row_id;
        return {
          table: p.table,
          row_id: rowId,
          field: p.field,
          new_value: value,
        };
      });
  }, [pending]);

  // 聊天发送：调后端 /suggest，将建议填充到 Drawer
  const sendChat = useCallback(async () => {
    const text = chatInput.trim();
    if (!text) return;
    if (!selectedAgent) return;
    setChatMessages((prev) => [...prev, { role: "user", content: text, ts: Date.now() }]);
    setChatInput("");
    setChatSending(true);
    try {
      const history = chatMessages
        .slice(-6)
        .map((m) => ({ role: m.role, content: m.content }));
      const resp = await gameWorkbenchApi.suggest(
        selectedAgent,
        text,
        openTables,
        validChanges,
        history,
      );
      const assistantMsg =
        resp.message ||
        (resp.changes?.length
          ? t("gameWorkbench.aiGotN", {
              count: resp.changes.length,
              defaultValue: `已生成 ${resp.changes.length} 条建议，请在右侧面板查看并采纳。`,
            })
          : t("gameWorkbench.aiNoChange", { defaultValue: "AI 未返回可采纳的字段改动。" }));
      setChatMessages((prev) => [
        ...prev,
        { role: "assistant", content: assistantMsg, ts: Date.now() },
      ]);
      setAiSuggestions(resp.changes || []);
      setAiMessage(resp.message || "");
      if ((resp.changes || []).length > 0) {
        setDrawerOpen(true);
      }
      // 联动 Chat 右栏：推一张数值卡片
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
            (resp.changes ?? []).length
              ? `建议：${(resp.changes ?? []).length} 条`
              : "",
            resp.message ? resp.message.slice(0, 120) : "",
          ]
            .filter(Boolean)
            .join("\n"),
          href: tablesUsed[0]
            ? `/numeric-workbench?table=${encodeURIComponent(tablesUsed[0])}`
            : "/numeric-workbench",
          payload: {
            tables: tablesUsed,
            changes: resp.changes,
            query_terms: resp.context_summary?.query_terms,
          },
        });
      } catch {
        /* ignore card push errors */
      }
    } catch (err: any) {
      const msg = err?.message || String(err);
      setChatMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: t("gameWorkbench.aiFailed", {
            defaultValue: "AI 调用失败: ",
          }) + msg,
          ts: Date.now(),
        },
      ]);
    } finally {
      setChatSending(false);
    }
  }, [chatInput, selectedAgent, openTables, validChanges, t]);

  const adoptSuggestion = useCallback((sug: SuggestChange) => {
    setPending((prev) => [
      ...prev,
      {
        key: `${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
        table: sug.table,
        row_id: String(sug.row_id),
        field: sug.field,
        new_value:
          sug.new_value === null || sug.new_value === undefined
            ? ""
            : String(sug.new_value),
      },
    ]);
    message.success(t("gameWorkbench.adoptedOne", { defaultValue: "已加入待编辑" }));
  }, [message, t]);

  const adoptAllSuggestions = useCallback(() => {
    if (aiSuggestions.length === 0) return;
    setPending((prev) => [
      ...prev,
      ...aiSuggestions.map((sug, i) => ({
        key: `${Date.now()}-${i}-${Math.random().toString(36).slice(2, 6)}`,
        table: sug.table,
        row_id: String(sug.row_id),
        field: sug.field,
        new_value:
          sug.new_value === null || sug.new_value === undefined
            ? ""
            : String(sug.new_value),
      })),
    ]);
    message.success(
      t("gameWorkbench.adoptedAll", {
        count: aiSuggestions.length,
        defaultValue: `已采纳 ${aiSuggestions.length} 条建议加入待编辑`,
      }),
    );
  }, [aiSuggestions, message, t]);

  const runPreview = useCallback(async () => {
    if (!selectedAgent) return;
    if (validChanges.length === 0) {
      setPreview([]);
      return;
    }
    setPreviewLoading(true);
    try {
      const resp = await gameWorkbenchApi.preview(selectedAgent, validChanges);
      setPreview(resp.items);
    } catch {
      message.error(t("gameWorkbench.previewFailed", { defaultValue: "预览失败" }));
    } finally {
      setPreviewLoading(false);
    }
  }, [selectedAgent, validChanges, message, t]);

  useEffect(() => {
    if (debounceRef.current) window.clearTimeout(debounceRef.current);
    debounceRef.current = window.setTimeout(() => {
      runPreview();
    }, 300);
    return () => {
      if (debounceRef.current) window.clearTimeout(debounceRef.current);
    };
  }, [runPreview]);

  const updateRow = (key: string, patch: Partial<PendingRow>) => {
    setPending((prev) => prev.map((r) => (r.key === key ? { ...r, ...patch } : r)));
  };

  const addRow = () => {
    if (!activeTable) return;
    setPending((prev) => [...prev, newRow(activeTable)]);
  };

  const removeRow = (key: string) => {
    setPending((prev) => prev.filter((r) => r.key !== key));
  };

  const resetAll = () => {
    setPending([]);
    setPreview([]);
  };

  const [rebuilding, setRebuilding] = useState(false);
  const rebuildIndex = useCallback(async () => {
    if (!selectedAgent) return;
    setRebuilding(true);
    try {
      const resp = await gameApi.rebuildIndex(selectedAgent);
      message.success(
        t("gameWorkbench.rebuildOk", {
          count: resp.indexed,
          scanned: resp.scanned_files.length,
          defaultValue: `重建完成: 扫描 ${resp.scanned_files.length} 个文件，索引 ${resp.indexed} 张表`,
        }),
      );
      await loadTables();
      // \u5237\u65b0\u5f53\u524d\u8868\u5185\u5bb9
      if (activeTable) {
        setRowsByTable((prev) => {
          const next = { ...prev };
          delete next[activeTable];
          return next;
        });
        await loadRowsForTable(activeTable);
      }
    } catch (err: any) {
      message.error(
        t("gameWorkbench.rebuildFailed", {
          defaultValue: "重建失败",
        }) + (err?.message ? `: ${err.message}` : ""),
      );
    } finally {
      setRebuilding(false);
    }
  }, [selectedAgent, message, t, loadTables, activeTable, loadRowsForTable]);

  const openDraft = () => {
    if (validChanges.length === 0) {
      message.warning(t("gameWorkbench.noChangesToSubmit", { defaultValue: "没有可提交的修改" }));
      return;
    }
    const tables = Array.from(new Set(validChanges.map((c) => c.table))).join(",");
    setDraftTitle(t("gameWorkbench.defaultTitle", {
      tables,
      count: validChanges.length,
      defaultValue: `数值改动: ${tables} (${validChanges.length} 项)`,
    }));
    setDraftDesc("");
    setDraftOpen(true);
    try {
      pushWorkbenchCard({
        id: `draft-${Date.now()}`,
        agentId: selectedAgent || "default",
        kind: "draft_doc",
        title: t("gameWorkbench.cardDraftTitle", {
          defaultValue: `变更草稿：${tables}`,
        }),
        summary: validChanges
          .slice(0, 6)
          .map((c) => `· ${c.table}/${c.row_id}/${c.field} → ${c.new_value}`)
          .join("\n") + (validChanges.length > 6 ? `\n…(共 ${validChanges.length} 条)` : ""),
        href: "/numeric-workbench",
        payload: { tables: tables.split(","), changes: validChanges },
      });
    } catch {
      /* ignore */
    }
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
      resetAll();
    } catch {
      message.error(t("gameWorkbench.draftCreateFailed", { defaultValue: "草案生成失败" }));
    } finally {
      setSubmitting(false);
    }
  };

  const editorColumns = [
    {
      title: t("gameWorkbench.colTable", { defaultValue: "表" }),
      dataIndex: "table",
      width: 140,
      render: (_: unknown, record: PendingRow) => (
        <Tag>{record.table}</Tag>
      ),
    },
    {
      title: t("gameWorkbench.colRowId", { defaultValue: "行 ID" }),
      dataIndex: "row_id",
      width: 130,
      render: (_: unknown, record: PendingRow) => (
        <Input
          value={record.row_id}
          onChange={(e) => updateRow(record.key, { row_id: e.target.value })}
          placeholder="row_id"
        />
      ),
    },
    {
      title: t("gameWorkbench.colField", { defaultValue: "字段" }),
      dataIndex: "field",
      width: 200,
      render: (_: unknown, record: PendingRow) => {
        const tFields = detailsByTable[record.table]?.fields ?? [];
        return (
          <Select
            value={record.field || undefined}
            onChange={(v) => updateRow(record.key, { field: v })}
            options={tFields.map((f) => ({ label: f.name, value: f.name }))}
            placeholder={t("gameWorkbench.fieldPlaceholder", { defaultValue: "选择字段" })}
            style={{ width: "100%" }}
            showSearch
          />
        );
      },
    },
    {
      title: t("gameWorkbench.colNewValue", { defaultValue: "新值" }),
      dataIndex: "new_value",
      render: (_: unknown, record: PendingRow) => (
        <Input
          value={record.new_value}
          onChange={(e) => updateRow(record.key, { new_value: e.target.value })}
          placeholder={t("gameWorkbench.newValuePlaceholder", { defaultValue: "新值（数字会自动识别）" })}
        />
      ),
    },
    {
      title: "",
      width: 60,
      render: (_: unknown, record: PendingRow) => (
        <Button
          type="text"
          danger
          icon={<DeleteOutlined />}
          onClick={() => removeRow(record.key)}
        />
      ),
    },
  ];

  return (
    <div className={styles.workbench}>
      <PageHeader
        parent={t("nav.game", { defaultValue: "Game Development" })}
        current={t("nav.gameWorkbench", { defaultValue: "数值工作台" })}
        subRow={
          <Text type="secondary">
            {t("gameWorkbench.subtitle", {
              defaultValue: "批量编辑数值表 → 实时预览 → 一键生成改动草案",
            })}
          </Text>
        }
      />

      <div className={styles.toolbar}>
        <Text type="secondary">{t("gameWorkbench.tableLabel", { defaultValue: "目标表" })}</Text>
        <Select
          mode="multiple"
          value={openTables}
          onChange={(vals: string[]) => {
            setOpenTables(vals);
            if (vals.length > 0 && (!activeTab || !vals.includes(activeTab))) {
              setActiveTab(vals[0]);
            }
          }}
          options={tableNames.map((n) => ({ label: n, value: n }))}
          loading={tablesLoading}
          style={{ minWidth: 320, maxWidth: 560 }}
          placeholder={t("gameWorkbench.tablePlaceholder", { defaultValue: "选择数据表（可多选）" })}
          showSearch
          maxTagCount="responsive"
          allowClear
        />
        <Button icon={<ReloadOutlined />} onClick={loadTables} disabled={tablesLoading}>
          {t("gameWorkbench.refresh", { defaultValue: "刷新" })}
        </Button>
        <Tooltip title={t("gameWorkbench.rebuildTip", { defaultValue: "扫描 SVN 工作区目录，重新索引所有表（无需先 svn update）" })}>
          <Button onClick={rebuildIndex} loading={rebuilding} disabled={!selectedAgent}>
            {t("gameWorkbench.rebuild", { defaultValue: "重建索引" })}
          </Button>
        </Tooltip>
        <Button
          icon={<RobotOutlined />}
          onClick={() => setDrawerOpen(true)}
          disabled={!selectedAgent}
        >
          {t("gameWorkbench.aiPanel", { defaultValue: "AI 补全面板" })}
        </Button>
        <div style={{ flex: 1 }} />
      </div>

      <div className={styles.split} ref={splitContainerRef}>
        <Card
          className={styles.upperPane}
          style={{ flex: `0 0 calc(${topRatio * 100}% - 4px)` }}
          title={
            <Space>
              <span>{t("gameWorkbench.tablesViewTitle", { defaultValue: "多表并列视图" })}</span>
              {rowsLoading && <Spin size="small" />}
            </Space>
          }
          extra={
            activeTable && (
              <Button
                size="small"
                icon={<ReloadOutlined />}
                onClick={() => {
                  setRowsByTable((prev) => {
                    const next = { ...prev };
                    delete next[activeTable];
                    return next;
                  });
                  loadRowsForTable(activeTable);
                }}
              >
                {t("gameWorkbench.reloadRows", { defaultValue: "重新加载" })}
              </Button>
            )
          }
          styles={{ body: { padding: 0, flex: 1, overflow: "hidden", display: "flex", flexDirection: "column" } }}
        >
          {openTables.length === 0 ? (
            <Empty
              style={{ padding: 24 }}
              description={t("gameWorkbench.emptyTablesView", {
                defaultValue: "请在工具栏选择目标表",
              })}
            />
          ) : (
            <Tabs
              type="editable-card"
              hideAdd
              activeKey={activeTab ?? undefined}
              onChange={setActiveTab}
              onEdit={(targetKey, action) => {
                if (action === "remove" && typeof targetKey === "string") {
                  setOpenTables((prev) => prev.filter((n) => n !== targetKey));
                  setPending((prev) => prev.filter((p) => p.table !== targetKey));
                }
              }}
              items={openTables.map((tname) => {
                const data = rowsByTable[tname];
                return {
                  key: tname,
                  label: tname,
                  children: data ? (
                    <div className={styles.tableScroll}>
                      <div style={{ padding: "8px 12px", borderBottom: "1px solid #f0f0f0", background: "#fafafa" }}>
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
                          style={{ maxWidth: 360 }}
                        />
                        {(() => {
                          const q = (searchByTable[tname] ?? "").trim();
                          if (!q) return null;
                          const matched = data.rows.filter((r) =>
                            r.some((c) => String(c ?? "").toLowerCase().includes(q.toLowerCase())),
                          ).length;
                          return (
                            <Tag style={{ marginLeft: 8 }} color={matched ? "blue" : "default"}>
                              {t("gameWorkbench.searchHit", {
                                defaultValue: `命中 ${matched} / ${data.rows.length} 行`,
                              })}
                            </Tag>
                          );
                        })()}
                      </div>
                      <Table
                        size="small"
                        rowKey={(_, idx) => String(idx ?? 0)}
                        sticky
                        scroll={{ x: "max-content", y: "calc(100vh - 460px)" }}
                        pagination={{ pageSize: 50, size: "small", showSizeChanger: false }}
                        dataSource={(() => {
                          const q = (searchByTable[tname] ?? "").trim().toLowerCase();
                          const base = data.rows.map((r, i) => ({
                            __idx: i,
                            ...Object.fromEntries(data.headers.map((h, ci) => [h, r[ci]])),
                          }));
                          if (!q) return base;
                          return base.filter((row) =>
                            data.headers.some((h) => String((row as Record<string, unknown>)[h] ?? "").toLowerCase().includes(q)),
                          );
                        })()}
                        columns={[
                          { title: "#", width: 50, fixed: "left", render: (_: unknown, __: unknown, idx: number) => idx + 1 },
                          ...data.headers.map((h, ci) => ({
                            title: h,
                            dataIndex: h,
                            key: `${h}__${ci}`,
                            ellipsis: true,
                            width: ci === 0 ? 110 : 140,
                            render: (val: unknown, _row: unknown, rIdx: number) => {
                              const text = val === null || val === undefined || val === "" ? "—" : String(val);
                              const origIdx = (_row as { __idx?: number })?.__idx ?? rIdx;
                              return (
                                <span
                                  title={t("gameWorkbench.dblClickHint", { defaultValue: "双击加入待编辑" })}
                                  style={{ cursor: "pointer" }}
                                  onDoubleClick={() => {
                                    const pkVal = String(data.rows[origIdx][0] ?? "");
                                    if (!pkVal) return;
                                    setPending((prev) => [
                                      ...prev,
                                      {
                                        key: `${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
                                        table: tname,
                                        row_id: pkVal,
                                        field: h,
                                        new_value: "",
                                      },
                                    ]);
                                    message.info(
                                      t("gameWorkbench.addedFromRow", {
                                        defaultValue: `已加入待编辑：${pkVal} / ${h}`,
                                      }),
                                    );
                                  }}
                                >
                                  {text}
                                </span>
                              );
                            },
                          })),
                        ]}
                      />
                    </div>
                  ) : (
                    <Spin style={{ display: "block", margin: "24px auto" }} />
                  ),
                };
              })}
              tabBarStyle={{ paddingLeft: 12, marginBottom: 0 }}
              className={styles.tablesTabs}
              style={{ flex: 1, display: "flex", flexDirection: "column", minHeight: 0 }}
            />
          )}
        </Card>

        <div className={styles.splitter} onMouseDown={onSplitterMouseDown} role="separator" />

        <Card
          className={styles.lowerPane}
          style={{ flex: 1 }}
          title={
            <Space>
              <span>{t("gameWorkbench.lowerTitle", { defaultValue: "实时影响预览" })}</span>
              {activeTable && <Tag>{activeTable}</Tag>}
              <Tag color="blue">
                {t("gameWorkbench.pendingCount", {
                  count: pending.length,
                  defaultValue: `改动 ${pending.length} 项`,
                })}
              </Tag>
              {previewLoading && <Spin size="small" />}
            </Space>
          }
          extra={
            <Space>
              <Button
                icon={<PlusOutlined />}
                onClick={addRow}
                disabled={!activeTable || detailLoading}
                size="small"
              >
                {t("gameWorkbench.addRow", { defaultValue: "添加一行" })}
              </Button>
              <Button onClick={resetAll} disabled={pending.length === 0} size="small">
                {t("gameWorkbench.reset", { defaultValue: "重置" })}
              </Button>
              <Button
                type="primary"
                icon={<SaveOutlined />}
                onClick={openDraft}
                disabled={validChanges.length === 0}
                size="small"
              >
                {t("gameWorkbench.generateDraft", { defaultValue: "生成变更草稿" })}
              </Button>
            </Space>
          }
          styles={{ body: { padding: 12, flex: 1, overflow: "auto" } }}
        >
          <div className={styles.lowerBody}>
            <div className={styles.summarySection}>
              <Text strong>{t("gameWorkbench.changeSummary", { defaultValue: "改动摘要" })}</Text>
              {pending.length === 0 ? (
                <Empty
                  image={Empty.PRESENTED_IMAGE_SIMPLE}
                  description={t("gameWorkbench.emptyEditor", {
                    defaultValue: "在上方表格双击单元格，或点击\"添加一行\"开始",
                  })}
                />
              ) : (
                <Table
                  size="small"
                  rowKey="key"
                  dataSource={pending}
                  columns={editorColumns}
                  pagination={false}
                />
              )}
            </div>

            <div className={styles.previewSection}>
              <Text strong>
                {t("gameWorkbench.previewTitle", { defaultValue: "效果 / 计算链路" })}
                {"  "}
                <Tag color={preview.every((p) => p.ok) && preview.length > 0 ? "green" : "default"}>
                  {t("gameWorkbench.previewCount", {
                    count: preview.length,
                    defaultValue: `${preview.length} 条`,
                  })}
                </Tag>
              </Text>
              {preview.length === 0 ? (
                <Empty
                  image={Empty.PRESENTED_IMAGE_SIMPLE}
                  description={t("gameWorkbench.emptyPreview", { defaultValue: "无可预览内容" })}
                />
              ) : (
                <div className={styles.previewList}>
                  {preview.map((item, idx) => (
                    <div
                      key={idx}
                      className={`${styles.previewItem} ${item.ok ? styles.ok : styles.fail}`}
                    >
                      <Space>
                        {item.ok ? (
                          <CheckCircleTwoTone twoToneColor="#52c41a" />
                        ) : (
                          <Tooltip title={item.error ?? ""}>
                            <CloseCircleTwoTone twoToneColor="#ff4d4f" />
                          </Tooltip>
                        )}
                        <Text strong>
                          {item.table}.{item.field}[{String(item.row_id)}]
                        </Text>
                      </Space>
                      <div className={styles.delta}>
                        <Text type="secondary">{formatValue(item.old_value)}</Text>
                        <span className={styles.deltaArrow}>→</span>
                        <Text>{formatValue(item.new_value)}</Text>
                      </div>
                      {!item.ok && item.error && (
                        <Text type="danger" style={{ fontSize: 12 }}>
                          {item.error}
                        </Text>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </Card>
      </div>

      <div className={styles.chatBar}>
        {chatMessages.length > 0 && (
          <div className={styles.chatHistory}>
            {chatMessages.map((m, i) => (
              <div key={i} className={`${styles.chatMsg} ${styles[m.role]}`}>
                <Avatar
                  size="small"
                  icon={m.role === "user" ? undefined : <RobotOutlined />}
                  style={{ background: m.role === "user" ? "#1677ff" : "#52c41a" }}
                >
                  {m.role === "user" ? "U" : null}
                </Avatar>
                <span className={styles.chatBubble}>{m.content}</span>
              </div>
            ))}
          </div>
        )}
        <div className={styles.chatInputRow}>
          <Input.TextArea
            value={chatInput}
            onChange={(e) => setChatInput(e.target.value)}
            placeholder={t("gameWorkbench.chatPlaceholder", {
              defaultValue: "向 AI 描述你的需求，例如：把所有 Sword 类装备的 SellPrice 提升 20%",
            })}
            autoSize={{ minRows: 1, maxRows: 4 }}
            onPressEnter={(e) => {
              if (!e.shiftKey) {
                e.preventDefault();
                sendChat();
              }
            }}
            disabled={chatSending}
          />
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={sendChat}
            loading={chatSending}
            disabled={!chatInput.trim()}
          >
            {t("gameWorkbench.send", { defaultValue: "确认发送" })}
          </Button>
        </div>
      </div>

      <Drawer
        title={
          <Space>
            <RobotOutlined />
            <span>{t("gameWorkbench.aiPanelTitle", { defaultValue: "AI 补全面板" })}</span>
            {activeTable && <Tag>{activeTable}</Tag>}
          </Space>
        }
        placement="right"
        width={420}
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        mask={false}
      >
        <div className={styles.aiDrawerBody}>
          {aiMessage && (
            <div style={{ padding: "0 4px" }}>
              <Text type="secondary">{aiMessage}</Text>
            </div>
          )}
          {aiSuggestions.length === 0 ? (
            <Empty
              description={t("gameWorkbench.aiPanelPlaceholder", {
                defaultValue: "在下方聊天框描述需求，例如：把所有 Sword 类装备的 SellPrice 提升 20%",
              })}
            />
          ) : (
            <>
              <Space style={{ justifyContent: "space-between", width: "100%" }}>
                <Text strong>
                  {t("gameWorkbench.aiSuggestionsTitle", {
                    count: aiSuggestions.length,
                    defaultValue: `AI 建议 (${aiSuggestions.length} 条)`,
                  })}
                </Text>
                <Space>
                  <Button size="small" onClick={() => setAiSuggestions([])}>
                    {t("gameWorkbench.clear", { defaultValue: "清空" })}
                  </Button>
                  <Button size="small" type="primary" onClick={adoptAllSuggestions}>
                    {t("gameWorkbench.adoptAll", { defaultValue: "全部采纳" })}
                  </Button>
                </Space>
              </Space>
              <div style={{ display: "flex", flexDirection: "column", gap: 8, marginTop: 8 }}>
                {aiSuggestions.map((sug, i) => (
                  <div
                    key={i}
                    className={styles.aiSuggestionCard}
                  >
                    <Space wrap>
                      <Tag color="gold">{sug.table}</Tag>
                      <Text code>{String(sug.row_id)}</Text>
                      <Text strong style={{ color: "var(--ant-color-warning-text)" }}>
                        {sug.field}
                      </Text>
                      <Text>=</Text>
                      <Text code style={{ color: "var(--ant-color-warning-text)", fontWeight: 600 }}>
                        {formatValue(sug.new_value)}
                      </Text>
                    </Space>
                    {sug.reason && (
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        {sug.reason}
                      </Text>
                    )}
                    <Space>
                      <Button size="small" type="link" onClick={() => adoptSuggestion(sug)}>
                        {t("gameWorkbench.adopt", { defaultValue: "采纳" })}
                      </Button>
                    </Space>
                  </div>
                ))}
              </div>
            </>
          )}
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

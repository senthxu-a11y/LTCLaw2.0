import { useEffect, useMemo, useState } from "react";
import {
  Alert,
  Button,
  Card,
  Descriptions,
  Empty,
  Input,
  Select,
  Skeleton,
  Space,
  Table,
  Tag,
  Tree,
  Typography,
} from "antd";
import type { ColumnsType } from "antd/es/table";
import { SearchOutlined, ReloadOutlined } from "@ant-design/icons";
import { useTranslation } from "react-i18next";
import { MarkdownCopy } from "@/components/MarkdownCopy/MarkdownCopy";
import { PageHeader } from "@/components/PageHeader";
import { useAppMessage } from "@/hooks/useAppMessage";
import {
  gameDocLibraryApi,
  type DocLibraryDocument,
  type DocLibraryDocumentDetail,
} from "../../api/modules/gameDocLibrary";
import { useAgentStore } from "../../stores/agentStore";
import styles from "./DocLibrary.module.less";

const { Text, Paragraph } = Typography;
const DOC_STATUSES = ["全部状态", "草稿", "待确认", "已确认", "归档"] as const;

const statusColorMap: Record<string, string> = {
  草稿: "default",
  待确认: "processing",
  已确认: "success",
  归档: "purple",
};

export default function DocLibrary() {
  const { t } = useTranslation();
  const { message } = useAppMessage();
  const { selectedAgent } = useAgentStore();
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>();
  const [documents, setDocuments] = useState<DocLibraryDocument[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [selectedDocumentId, setSelectedDocumentId] = useState<string>();
  const [selectedDocument, setSelectedDocument] = useState<DocLibraryDocumentDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [statusSaving, setStatusSaving] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string>("全部状态");

  const fetchDocuments = async () => {
    if (!selectedAgent) {
      setDocuments([]);
      setCategories([]);
      setSelectedDocumentId(undefined);
      setSelectedDocument(null);
      setLoading(false);
      return;
    }

    setLoading(true);
    try {
      const response = await gameDocLibraryApi.listDocuments(selectedAgent);
      setDocuments(response.items || []);
      setCategories(response.categories || []);
      setSelectedDocument((current) =>
        current && response.items.some((item) => item.id === current.item.id) ? current : null,
      );
    } catch (err) {
      setDocuments([]);
      setCategories([]);
      setSelectedDocumentId(undefined);
      setSelectedDocument(null);
      message.warning(err instanceof Error ? err.message : t("docLibrary.mockFallback"));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, [selectedAgent]);

  const filteredDocuments = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();
    return documents.filter((item) => {
      const matchesCategory = !selectedCategory || item.category === selectedCategory;
      const matchesStatus = statusFilter === "全部状态" || item.status === statusFilter;
      const matchesQuery =
        !query ||
        item.title.toLowerCase().includes(query) ||
        item.author.toLowerCase().includes(query) ||
        item.path?.toLowerCase().includes(query) ||
        item.tags.some((tag) => tag.toLowerCase().includes(query));
      return matchesCategory && matchesStatus && matchesQuery;
    });
  }, [documents, searchQuery, selectedCategory, statusFilter]);

  const treeData = useMemo(
    () => [
      {
        title: t("docLibrary.categoryTitle"),
        key: "__all__",
        children: categories.map((category) => ({ title: category, key: category })),
      },
    ],
    [categories, t],
  );

  useEffect(() => {
    if (filteredDocuments.length === 0) {
      setSelectedDocumentId(undefined);
      setSelectedDocument(null);
      return;
    }
    if (!selectedDocumentId || !filteredDocuments.some((item) => item.id === selectedDocumentId)) {
      setSelectedDocumentId(filteredDocuments[0].id);
    }
  }, [filteredDocuments, selectedDocumentId]);

  useEffect(() => {
    const loadDetail = async () => {
      if (!selectedAgent || !selectedDocumentId) {
        setSelectedDocument(null);
        return;
      }
      setDetailLoading(true);
      try {
        const detail = await gameDocLibraryApi.getDocument(selectedAgent, selectedDocumentId);
        setSelectedDocument(detail);
      } catch (err) {
        setSelectedDocument(null);
        message.warning(err instanceof Error ? err.message : "文档详情加载失败");
      } finally {
        setDetailLoading(false);
      }
    };
    loadDetail();
  }, [message, selectedAgent, selectedDocumentId]);

  const handleUpdateStatus = async (nextStatus: string) => {
    if (!selectedAgent || !selectedDocumentId || !selectedDocument) {
      return;
    }
    if (selectedDocument.item.status === nextStatus) {
      return;
    }
    setStatusSaving(true);
    try {
      const detail = await gameDocLibraryApi.updateDocument(selectedAgent, selectedDocumentId, {
        status: nextStatus,
      });
      setSelectedDocument(detail);
      await fetchDocuments();
      message.success(
        nextStatus === "已确认" && detail.kb_entry_id
          ? `文档已更新为${nextStatus}，并已同步到 legacy KB 镜像`
          : `文档已更新为${nextStatus}`,
      );
    } catch (err) {
      message.warning(err instanceof Error ? err.message : "文档状态更新失败");
    } finally {
      setStatusSaving(false);
    }
  };

  const columns: ColumnsType<DocLibraryDocument> = [
    {
      title: t("docLibrary.columns.title"),
      dataIndex: "title",
      key: "title",
      render: (_, record) => (
        <div>
          <Text strong>{record.title}</Text>
          <div className={styles.tagRow}>
            {record.tags.map((tag) => (
              <Tag key={tag}>{tag}</Tag>
            ))}
          </div>
        </div>
      ),
    },
    {
      title: t("docLibrary.columns.type"),
      dataIndex: "type",
      key: "type",
      width: 120,
      render: (value) => <Tag color="blue">{value}</Tag>,
    },
    {
      title: t("docLibrary.columns.status"),
      dataIndex: "status",
      key: "status",
      width: 120,
      render: (value) => <Tag color={statusColorMap[value] || "default"}>{value}</Tag>,
    },
    {
      title: t("docLibrary.columns.author"),
      dataIndex: "author",
      key: "author",
      width: 120,
    },
    {
      title: t("docLibrary.columns.updatedAt"),
      dataIndex: "updated_at",
      key: "updated_at",
      width: 160,
    },
  ];

  return (
    <div className={styles.page}>
      <PageHeader parent={t("nav.game")} current={t("docLibrary.title")} />

      <div className={styles.body}>
        <Card className={styles.sidebarCard}>
          <Space direction="vertical" size={16} className={styles.fullWidth}>
            <div>
              <Text strong>{t("docLibrary.categoryTitle")}</Text>
              <Paragraph type="secondary" className={styles.helperText}>
                {t("docLibrary.categoryHint")}
              </Paragraph>
            </div>
            <Tree
              treeData={treeData}
              selectedKeys={selectedCategory ? [selectedCategory] : []}
              onSelect={(keys) => {
                const key = keys[0] as string | undefined;
                setSelectedCategory(key && key !== "__all__" ? key : undefined);
              }}
            />
          </Space>
        </Card>

        <Card className={styles.contentCard}>
          <Space direction="vertical" size={16} className={styles.fullWidth}>
            <div className={styles.toolbar}>
              <div>
                <Text strong>{t("docLibrary.listTitle")}</Text>
                <Paragraph type="secondary" className={styles.helperText}>
                  {t("docLibrary.description")}
                </Paragraph>
              </div>
              <Space wrap>
                <Input
                  allowClear
                  prefix={<SearchOutlined />}
                  placeholder={t("docLibrary.searchPlaceholder")}
                  value={searchQuery}
                  onChange={(event) => setSearchQuery(event.target.value)}
                  className={styles.searchInput}
                />
                <Select
                  value={statusFilter}
                  onChange={setStatusFilter}
                  className={styles.statusSelect}
                  options={DOC_STATUSES.map((status) => ({ label: status, value: status }))}
                />
                <Tag
                  className={styles.refreshTag}
                  icon={<ReloadOutlined />}
                  onClick={fetchDocuments}
                >
                  {t("common.refresh")}
                </Tag>
              </Space>
            </div>

            {loading ? (
              <Skeleton active paragraph={{ rows: 8 }} />
            ) : filteredDocuments.length === 0 ? (
              <div className={styles.emptyWrap}>
                <Empty description={t("docLibrary.empty")} />
              </div>
            ) : (
              <div className={styles.workspaceGrid}>
                <div className={styles.listPane}>
                  <Table
                    rowKey="id"
                    columns={columns}
                    dataSource={filteredDocuments}
                    pagination={{ pageSize: 10, hideOnSinglePage: true }}
                    rowClassName={(record) =>
                      record.id === selectedDocumentId ? styles.selectedRow : ""
                    }
                    onRow={(record) => ({
                      onClick: () => setSelectedDocumentId(record.id),
                    })}
                  />
                </div>

                <Card className={styles.previewCard}>
                  {!selectedDocumentId ? (
                    <div className={styles.emptyWrap}>
                      <Empty description="请选择一份文档" />
                    </div>
                  ) : detailLoading || !selectedDocument ? (
                    <Skeleton active paragraph={{ rows: 12 }} />
                  ) : (
                    <Space direction="vertical" size={16} className={styles.fullWidth}>
                      <div className={styles.previewHeader}>
                        <div>
                          <Text strong>{selectedDocument.item.title}</Text>
                          <Paragraph type="secondary" className={styles.helperText}>
                            {selectedDocument.item.path || selectedDocument.item.id}
                          </Paragraph>
                        </div>
                        <Tag color={statusColorMap[selectedDocument.item.status] || "default"}>
                          {selectedDocument.item.status}
                        </Tag>
                      </div>

                      <Descriptions size="small" column={1} className={styles.previewMeta}>
                        <Descriptions.Item label="类型">{selectedDocument.item.type}</Descriptions.Item>
                        <Descriptions.Item label="分类">{selectedDocument.item.category}</Descriptions.Item>
                        <Descriptions.Item label="作者">{selectedDocument.item.author}</Descriptions.Item>
                        <Descriptions.Item label="更新时间">
                          {selectedDocument.item.updated_at}
                        </Descriptions.Item>
                        <Descriptions.Item label="标签">
                          <div className={styles.tagRow}>
                            {selectedDocument.item.tags.length > 0 ? (
                              selectedDocument.item.tags.map((tag) => <Tag key={tag}>{tag}</Tag>)
                            ) : (
                              <Text type="secondary">暂无标签</Text>
                            )}
                          </div>
                        </Descriptions.Item>
                      </Descriptions>

                      <Space wrap>
                        {DOC_STATUSES.filter((status) => status !== "全部状态").map((status) => (
                          <Button
                            key={status}
                            type={selectedDocument.item.status === status ? "primary" : "default"}
                            loading={statusSaving && selectedDocument.item.status !== status}
                            onClick={() => handleUpdateStatus(status)}
                          >
                            {status}
                          </Button>
                        ))}
                      </Space>

                      {selectedDocument.truncated ? (
                        <Alert type="warning" message="预览内容过长，已自动截断。" showIcon />
                      ) : null}

                      <div className={styles.previewBody}>
                        {selectedDocument.preview_kind === "markdown" ? (
                          <MarkdownCopy
                            content={selectedDocument.content}
                            showControls={false}
                            markdownViewerProps={{ className: styles.markdownViewer }}
                          />
                        ) : selectedDocument.preview_kind === "text" ? (
                          <pre className={styles.textPreview}>{selectedDocument.content}</pre>
                        ) : (
                          <Alert
                            type="info"
                            message={selectedDocument.content}
                            showIcon
                          />
                        )}
                      </div>
                    </Space>
                  )}
                </Card>
              </div>
            )}
          </Space>
        </Card>
      </div>
    </div>
  );
}
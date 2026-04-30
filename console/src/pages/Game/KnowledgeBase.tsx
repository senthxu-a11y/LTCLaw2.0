import { useEffect, useMemo, useState } from "react";
import {
  Button,
  Card,
  Empty,
  Form,
  Input,
  List,
  Modal,
  Popconfirm,
  Skeleton,
  Space,
  Tag,
  Tree,
  Typography,
} from "antd";
import { SearchOutlined, ReloadOutlined, PlusOutlined, DeleteOutlined, EditOutlined } from "@ant-design/icons";
import { useTranslation } from "react-i18next";
import { PageHeader } from "@/components/PageHeader";
import { useAppMessage } from "@/hooks/useAppMessage";
import {
  gameKnowledgeBaseApi,
  type KnowledgeBaseEntry,
} from "../../api/modules/gameKnowledgeBase";
import { useAgentStore } from "../../stores/agentStore";
import styles from "./KnowledgeBase.module.less";

const { Text, Paragraph } = Typography;

const defaultCategories = [
  {
    title: "知识分类",
    key: "root",
    children: [
      { title: "机制", key: "机制" },
      { title: "数值规律", key: "数值规律" },
      { title: "历史决策", key: "历史决策" },
      { title: "其它", key: "general" },
    ],
  },
];

const sourceColorMap: Record<string, string> = {
  文档: "blue",
  对话: "gold",
  手动: "green",
  manual: "green",
};

interface EntryFormValues {
  title: string;
  category?: string;
  source?: string;
  summary?: string;
  tags?: string;
}

export default function KnowledgeBase() {
  const { t } = useTranslation();
  const { message } = useAppMessage();
  const { selectedAgent } = useAgentStore();
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>();
  const [entries, setEntries] = useState<KnowledgeBaseEntry[]>([]);
  const [searchHits, setSearchHits] = useState<KnowledgeBaseEntry[] | null>(null);
  const [searching, setSearching] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<KnowledgeBaseEntry | null>(null);
  const [form] = Form.useForm<EntryFormValues>();

  const fetchEntries = async () => {
    if (!selectedAgent) {
      setEntries([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const response = await gameKnowledgeBaseApi.listEntries(selectedAgent);
      setEntries(response.items || []);
    } catch (err) {
      setEntries([]);
      message.warning(`${t("knowledgeBase.mockFallback")} (${(err as Error).message})`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEntries();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedAgent]);

  const runSearch = async (query: string) => {
    if (!selectedAgent || !query.trim()) {
      setSearchHits(null);
      return;
    }
    setSearching(true);
    try {
      const res = await gameKnowledgeBaseApi.search(selectedAgent, {
        query,
        top_k: 20,
        category: selectedCategory && selectedCategory !== "general" ? selectedCategory : undefined,
      });
      setSearchHits(res.items || []);
    } catch (err) {
      message.error(`search failed: ${(err as Error).message}`);
      setSearchHits([]);
    } finally {
      setSearching(false);
    }
  };

  const filteredEntries = useMemo(() => {
    if (searchHits !== null) return searchHits;
    return entries.filter((item) => {
      if (selectedCategory && item.category !== selectedCategory) return false;
      const q = searchQuery.trim().toLowerCase();
      if (!q) return true;
      return (
        item.title.toLowerCase().includes(q) ||
        (item.summary || "").toLowerCase().includes(q) ||
        (item.tags || []).some((tag) => tag.toLowerCase().includes(q))
      );
    });
  }, [entries, searchHits, searchQuery, selectedCategory]);

  const openCreate = () => {
    setEditing(null);
    form.resetFields();
    setModalOpen(true);
  };

  const openEdit = (entry: KnowledgeBaseEntry) => {
    setEditing(entry);
    form.setFieldsValue({
      title: entry.title,
      category: entry.category,
      source: entry.source,
      summary: entry.summary,
      tags: (entry.tags || []).join(", "),
    });
    setModalOpen(true);
  };

  const handleSubmit = async () => {
    if (!selectedAgent) return;
    const values = await form.validateFields();
    const body = {
      title: values.title,
      category: values.category || "general",
      source: values.source || "manual",
      summary: values.summary || "",
      tags: (values.tags || "")
        .split(/[,，;；]/)
        .map((t) => t.trim())
        .filter(Boolean),
    };
    try {
      if (editing) {
        await gameKnowledgeBaseApi.updateEntry(selectedAgent, editing.id, body);
        message.success("updated");
      } else {
        await gameKnowledgeBaseApi.createEntry(selectedAgent, body);
        message.success("created");
      }
      setModalOpen(false);
      setSearchHits(null);
      setSearchQuery("");
      fetchEntries();
    } catch (err) {
      message.error(`save failed: ${(err as Error).message}`);
    }
  };

  const handleDelete = async (entry: KnowledgeBaseEntry) => {
    if (!selectedAgent) return;
    try {
      await gameKnowledgeBaseApi.deleteEntry(selectedAgent, entry.id);
      message.success("deleted");
      setSearchHits(null);
      fetchEntries();
    } catch (err) {
      message.error(`delete failed: ${(err as Error).message}`);
    }
  };

  return (
    <div className={styles.page}>
      <PageHeader parent={t("nav.game")} current={t("knowledgeBase.title")} />

      <div className={styles.body}>
        <Card className={styles.sidebarCard}>
          <Space direction="vertical" size={16} className={styles.fullWidth}>
            <div>
              <Text strong>{t("knowledgeBase.categoryTitle")}</Text>
              <Paragraph type="secondary" className={styles.helperText}>
                {t("knowledgeBase.categoryHint")}
              </Paragraph>
            </div>
            <Tree
              treeData={defaultCategories}
              selectedKeys={selectedCategory ? [selectedCategory] : []}
              onSelect={(keys) => setSelectedCategory(keys[0] as string | undefined)}
            />
          </Space>
        </Card>

        <Card className={styles.contentCard}>
          <Space direction="vertical" size={16} className={styles.fullWidth}>
            <div className={styles.toolbar}>
              <div>
                <Text strong>{t("knowledgeBase.listTitle")}</Text>
                <Paragraph type="secondary" className={styles.helperText}>
                  {t("knowledgeBase.description")}
                </Paragraph>
              </div>
              <Space wrap>
                <Input.Search
                  allowClear
                  prefix={<SearchOutlined />}
                  placeholder={t("knowledgeBase.searchPlaceholder")}
                  value={searchQuery}
                  loading={searching}
                  enterButton="语义搜索"
                  onChange={(event) => {
                    setSearchQuery(event.target.value);
                    if (!event.target.value) setSearchHits(null);
                  }}
                  onSearch={runSearch}
                  className={styles.searchInput}
                />
                <Button icon={<ReloadOutlined />} onClick={() => { setSearchHits(null); fetchEntries(); }}>
                  {t("common.refresh")}
                </Button>
                <Button type="primary" icon={<PlusOutlined />} onClick={openCreate} disabled={!selectedAgent}>
                  新建条目
                </Button>
              </Space>
            </div>

            {loading ? (
              <Skeleton active paragraph={{ rows: 8 }} />
            ) : filteredEntries.length === 0 ? (
              <div className={styles.emptyWrap}>
                <Empty description={t("knowledgeBase.empty")} />
              </div>
            ) : (
              <List
                dataSource={filteredEntries}
                renderItem={(item) => (
                  <List.Item
                    actions={[
                      <Button key="e" size="small" type="text" icon={<EditOutlined />} onClick={() => openEdit(item)}>
                        编辑
                      </Button>,
                      <Popconfirm
                        key="d"
                        title="删除该条目？"
                        onConfirm={() => handleDelete(item)}
                        okText="删除"
                        cancelText="取消"
                      >
                        <Button size="small" type="text" danger icon={<DeleteOutlined />}>
                          删除
                        </Button>
                      </Popconfirm>,
                    ]}
                  >
                    <div className={styles.entryCard}>
                      <div className={styles.entryHeader}>
                        <Text strong>{item.title}</Text>
                        <Space wrap>
                          {typeof item.score === "number" ? (
                            <Tag color="purple">score {(item.score as number).toFixed(3)}</Tag>
                          ) : null}
                          <Tag color="geekblue">{item.category}</Tag>
                          <Tag color={sourceColorMap[item.source] || "default"}>{item.source}</Tag>
                        </Space>
                      </div>
                      <Paragraph className={styles.summary}>{item.summary}</Paragraph>
                      <div className={styles.entryMeta}>
                        <Text type="secondary">
                          {t("knowledgeBase.createdAt")}:{" "}
                          {typeof item.created_at === "number"
                            ? new Date(item.created_at * 1000).toLocaleString()
                            : item.created_at}
                        </Text>
                        <div className={styles.tagRow}>
                          {(item.tags || []).map((tag) => (
                            <Tag key={tag}>{tag}</Tag>
                          ))}
                        </div>
                      </div>
                    </div>
                  </List.Item>
                )}
              />
            )}
          </Space>
        </Card>
      </div>

      <Modal
        open={modalOpen}
        title={editing ? "编辑条目" : "新建条目"}
        onCancel={() => setModalOpen(false)}
        onOk={handleSubmit}
        destroyOnClose
        okText={editing ? "保存" : "创建"}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="title" label="标题" rules={[{ required: true, message: "标题必填" }]}>
            <Input maxLength={200} />
          </Form.Item>
          <Form.Item name="category" label="分类" initialValue="general">
            <Input placeholder="机制 / 数值规律 / 历史决策 / general" />
          </Form.Item>
          <Form.Item name="source" label="来源" initialValue="manual">
            <Input placeholder="manual / 文档 / 对话" />
          </Form.Item>
          <Form.Item name="tags" label="标签 (逗号分隔)">
            <Input placeholder="体力, 节奏" />
          </Form.Item>
          <Form.Item name="summary" label="正文 / 摘要">
            <Input.TextArea rows={6} maxLength={4000} showCount />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
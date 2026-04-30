import { useEffect, useMemo, useState } from "react";
import {
  Card,
  Empty,
  Input,
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
import { PageHeader } from "@/components/PageHeader";
import { useAppMessage } from "@/hooks/useAppMessage";
import {
  gameDocLibraryApi,
  type DocLibraryDocument,
} from "../../api/modules/gameDocLibrary";
import { useAgentStore } from "../../stores/agentStore";
import styles from "./DocLibrary.module.less";

const { Text, Paragraph } = Typography;

const mockCategories = [
  {
    title: "核心策划",
    key: "core",
    children: [
      { title: "玩法设计", key: "玩法设计" },
      { title: "数值表", key: "数值表" },
    ],
  },
  {
    title: "项目协作",
    key: "collab",
    children: [
      { title: "任务拆解", key: "任务拆解" },
      { title: "评审记录", key: "评审记录" },
    ],
  },
];

const mockDocuments: DocLibraryDocument[] = [
  {
    id: "doc-1",
    title: "战斗系统阶段验收说明",
    type: "策划案",
    status: "已确认",
    updated_at: "2026-04-28 16:30",
    author: "Lin",
    category: "玩法设计",
    tags: ["战斗", "阶段验收"],
  },
  {
    id: "doc-2",
    title: "角色成长数值总表",
    type: "数值表",
    status: "待确认",
    updated_at: "2026-04-29 10:15",
    author: "Mia",
    category: "数值表",
    tags: ["成长", "角色"],
  },
  {
    id: "doc-3",
    title: "版本里程碑任务清单",
    type: "任务",
    status: "草稿",
    updated_at: "2026-04-30 09:05",
    author: "Qiao",
    category: "任务拆解",
    tags: ["排期", "里程碑"],
  },
  {
    id: "doc-4",
    title: "数值评审会议纪要",
    type: "文档",
    status: "归档",
    updated_at: "2026-04-25 19:40",
    author: "Ivy",
    category: "评审记录",
    tags: ["会议", "评审"],
  },
];

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

  const fetchDocuments = async () => {
    if (!selectedAgent) {
      setDocuments(mockDocuments);
      setLoading(false);
      return;
    }

    setLoading(true);
    try {
      const response = await gameDocLibraryApi.listDocuments(selectedAgent);
      setDocuments(response.items.length > 0 ? response.items : mockDocuments);
    } catch {
      setDocuments(mockDocuments);
      message.warning(t("docLibrary.mockFallback"));
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
      const matchesQuery =
        !query ||
        item.title.toLowerCase().includes(query) ||
        item.author.toLowerCase().includes(query) ||
        item.tags.some((tag) => tag.toLowerCase().includes(query));
      return matchesCategory && matchesQuery;
    });
  }, [documents, searchQuery, selectedCategory]);

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
      width: 180,
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
              treeData={mockCategories}
              selectedKeys={selectedCategory ? [selectedCategory] : []}
              onSelect={(keys) => setSelectedCategory(keys[0] as string | undefined)}
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
              <Table
                rowKey="id"
                columns={columns}
                dataSource={filteredDocuments}
                pagination={false}
              />
            )}
          </Space>
        </Card>
      </div>
    </div>
  );
}
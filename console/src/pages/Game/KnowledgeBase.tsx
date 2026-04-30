import { useEffect, useMemo, useState } from "react";
import {
  Card,
  Empty,
  Input,
  List,
  Skeleton,
  Space,
  Tag,
  Tree,
  Typography,
} from "antd";
import { SearchOutlined, ReloadOutlined } from "@ant-design/icons";
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

const mockCategories = [
  {
    title: "知识分类",
    key: "root",
    children: [
      { title: "机制", key: "机制" },
      { title: "数值规律", key: "数值规律" },
      { title: "历史决策", key: "历史决策" },
    ],
  },
];

const mockEntries: KnowledgeBaseEntry[] = [
  {
    id: "kb-1",
    title: "体力恢复节奏约束",
    category: "机制",
    source: "文档",
    created_at: "2026-04-27 14:10",
    summary: "挂机与主动玩法的节奏窗口需要保持在 20 分钟内，避免日活时间被拉长。",
    tags: ["体力", "节奏"],
  },
  {
    id: "kb-2",
    title: "装备数值递增原则",
    category: "数值规律",
    source: "手动",
    created_at: "2026-04-28 11:00",
    summary: "紫装到橙装的主属性增幅控制在 12%-15%，避免跨品质断层。",
    tags: ["装备", "成长"],
  },
  {
    id: "kb-3",
    title: "新手引导第三版调整原因",
    category: "历史决策",
    source: "对话",
    created_at: "2026-04-29 18:25",
    summary: "因首日流失集中在战斗前，第三版把教学拆成两段并延后付费提示。",
    tags: ["新手引导", "历史"],
  },
  {
    id: "kb-4",
    title: "Boss 战数值回看结论",
    category: "数值规律",
    source: "文档",
    created_at: "2026-04-30 08:55",
    summary: "Boss 爆发技能前 6 秒为核心预警期，玩家容错窗口不应低于 1.5 秒。",
    tags: ["Boss", "战斗"],
  },
];

const sourceColorMap: Record<string, string> = {
  文档: "blue",
  对话: "gold",
  手动: "green",
};

export default function KnowledgeBase() {
  const { t } = useTranslation();
  const { message } = useAppMessage();
  const { selectedAgent } = useAgentStore();
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>();
  const [entries, setEntries] = useState<KnowledgeBaseEntry[]>([]);

  const fetchEntries = async () => {
    if (!selectedAgent) {
      setEntries(mockEntries);
      setLoading(false);
      return;
    }

    setLoading(true);
    try {
      const response = await gameKnowledgeBaseApi.listEntries(selectedAgent);
      setEntries(response.items.length > 0 ? response.items : mockEntries);
    } catch {
      setEntries(mockEntries);
      message.warning(t("knowledgeBase.mockFallback"));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEntries();
  }, [selectedAgent]);

  const filteredEntries = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();
    return entries.filter((item) => {
      const matchesCategory = !selectedCategory || item.category === selectedCategory;
      const matchesQuery =
        !query ||
        item.title.toLowerCase().includes(query) ||
        item.summary.toLowerCase().includes(query) ||
        item.tags.some((tag) => tag.toLowerCase().includes(query));
      return matchesCategory && matchesQuery;
    });
  }, [entries, searchQuery, selectedCategory]);

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
                <Text strong>{t("knowledgeBase.listTitle")}</Text>
                <Paragraph type="secondary" className={styles.helperText}>
                  {t("knowledgeBase.description")}
                </Paragraph>
              </div>
              <Space wrap>
                <Input
                  allowClear
                  prefix={<SearchOutlined />}
                  placeholder={t("knowledgeBase.searchPlaceholder")}
                  value={searchQuery}
                  onChange={(event) => setSearchQuery(event.target.value)}
                  className={styles.searchInput}
                />
                <Tag
                  className={styles.refreshTag}
                  icon={<ReloadOutlined />}
                  onClick={fetchEntries}
                >
                  {t("common.refresh")}
                </Tag>
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
                  <List.Item>
                    <div className={styles.entryCard}>
                      <div className={styles.entryHeader}>
                        <Text strong>{item.title}</Text>
                        <Space wrap>
                          <Tag color="geekblue">{item.category}</Tag>
                          <Tag color={sourceColorMap[item.source] || "default"}>{item.source}</Tag>
                        </Space>
                      </div>
                      <Paragraph className={styles.summary}>{item.summary}</Paragraph>
                      <div className={styles.entryMeta}>
                        <Text type="secondary">{t("knowledgeBase.createdAt")}: {item.created_at}</Text>
                        <div className={styles.tagRow}>
                          {item.tags.map((tag) => (
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
    </div>
  );
}
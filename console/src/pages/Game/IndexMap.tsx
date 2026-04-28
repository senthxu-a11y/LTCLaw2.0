import { useEffect, useMemo, useState } from "react";
import {
  Badge,
  Button,
  Card,
  Col,
  Descriptions,
  Drawer,
  Empty,
  Input,
  List,
  Row,
  Select,
  Space,
  Table,
  Tag,
  Tooltip,
  Typography,
} from "antd";
import { 
  SearchOutlined, 
  EyeOutlined, 
  ReloadOutlined,
  NodeIndexOutlined,
  TableOutlined,
  LinkOutlined
} from "@ant-design/icons";
import { useTranslation } from "react-i18next";
import { PageHeader } from "@/components/PageHeader";
import { useAppMessage } from "@/hooks/useAppMessage";
import { useAgentStore } from "../../stores/agentStore";
import styles from "./IndexMap.module.less";

const { Text } = Typography;
const { Option } = Select;

interface TableIndex {
  id: string;
  name: string;
  path: string;
  file_type: 'excel' | 'csv' | 'json';
  last_modified: string;
  indexed_at: string;
  field_count: number;
  row_count: number;
  status: 'indexed' | 'pending' | 'error';
  dependencies: string[];
  referenced_by: string[];
  description?: string;
}

interface FieldInfo {
  name: string;
  type: string;
  description?: string;
  is_key: boolean;
  references?: {
    table: string;
    field: string;
  };
}

interface TableDetail {
  index: TableIndex;
  fields: FieldInfo[];
  sample_data: any[];
}

// Mock data for demonstration
const mockTableIndexes: TableIndex[] = [
  {
    id: "items",
    name: "Items",
    path: "Tables/Items.xlsx",
    file_type: "excel",
    last_modified: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    indexed_at: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
    field_count: 12,
    row_count: 1247,
    status: "indexed",
    dependencies: ["ItemTypes", "Rarities"],
    referenced_by: ["Drops", "Shops", "Rewards"],
    description: "游戏物品配置表，包含装备、道具、材料等",
  },
  {
    id: "npcs",
    name: "NPCs",
    path: "Tables/NPCs.csv",
    file_type: "csv",
    last_modified: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(),
    indexed_at: new Date(Date.now() - 10 * 60 * 1000).toISOString(),
    field_count: 8,
    row_count: 356,
    status: "indexed",
    dependencies: ["NPCTypes", "DialogueGroups"],
    referenced_by: ["Quests", "Spawns"],
    description: "NPC 配置表，定义游戏中的非玩家角色",
  },
  {
    id: "skills",
    name: "Skills",
    path: "Tables/Skills.xlsx",
    file_type: "excel", 
    last_modified: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
    indexed_at: new Date(Date.now() - 5 * 60 * 1000).toISOString(),
    field_count: 15,
    row_count: 89,
    status: "indexed",
    dependencies: ["SkillTypes", "Elements"],
    referenced_by: ["Characters", "Effects"],
    description: "技能配置表，包含主动技能和被动技能",
  },
  {
    id: "quests_new",
    name: "QuestsNew",
    path: "Tables/QuestsNew.xlsx",
    file_type: "excel",
    last_modified: new Date(Date.now() - 10 * 60 * 1000).toISOString(),
    indexed_at: new Date().toISOString(),
    field_count: 0,
    row_count: 0,
    status: "pending",
    dependencies: [],
    referenced_by: [],
    description: "新任务配置表 - 正在索引中",
  },
  {
    id: "levels_broken",
    name: "LevelsBroken",
    path: "Tables/Levels.xlsx",
    file_type: "excel",
    last_modified: new Date(Date.now() - 5 * 60 * 1000).toISOString(),
    indexed_at: new Date(Date.now() - 2 * 60 * 1000).toISOString(),
    field_count: 0,
    row_count: 0,
    status: "error",
    dependencies: [],
    referenced_by: [],
    description: "关卡配置表 - 索引失败",
  },
];

export default function IndexMap() {
  const { t } = useTranslation();
  const { message } = useAppMessage();
  const { selectedAgent } = useAgentStore();
  
  const [loading, setLoading] = useState(false);
  const [tableIndexes, setTableIndexes] = useState<TableIndex[]>(mockTableIndexes);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [typeFilter, setTypeFilter] = useState<string>("all");
  const [drawerVisible, setDrawerVisible] = useState(false);
  const [tableDetail, setTableDetail] = useState<TableDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  const fetchTableIndexes = async () => {
    setLoading(true);
    try {
      // Placeholder for actual API call
      // const response = await fetch('/api/game-project/indexes');
      // const data = await response.json();
      // setTableIndexes(data);
      
      // Using mock data for demonstration
      await new Promise(resolve => setTimeout(resolve, 500));
      setTableIndexes(mockTableIndexes);
      
    } catch (err) {
      message.error(t("indexMap.loadFailed"));
    } finally {
      setLoading(false);
    }
  };

  const fetchTableDetail = async (tableId: string) => {
    setDetailLoading(true);
    try {
      // Mock detail data
      const index = tableIndexes.find(t => t.id === tableId);
      if (!index) return;

      // Mock field data
      const mockFields: FieldInfo[] = [
        {
          name: "id",
          type: "integer",
          description: "物品唯一标识符",
          is_key: true,
        },
        {
          name: "name",
          type: "string",
          description: "物品名称",
          is_key: false,
        },
        {
          name: "type_id",
          type: "integer", 
          description: "物品类型ID",
          is_key: false,
          references: { table: "ItemTypes", field: "id" },
        },
        {
          name: "rarity_id",
          type: "integer",
          description: "稀有度ID",
          is_key: false,
          references: { table: "Rarities", field: "id" },
        },
      ];

      const mockSampleData = [
        { id: 1001, name: "铁剑", type_id: 1, rarity_id: 1 },
        { id: 1002, name: "银剑", type_id: 1, rarity_id: 2 },
        { id: 2001, name: "生命药水", type_id: 2, rarity_id: 1 },
      ];

      setTableDetail({
        index,
        fields: mockFields,
        sample_data: mockSampleData,
      });

    } catch (err) {
      message.error(t("indexMap.detailLoadFailed"));
    } finally {
      setDetailLoading(false);
    }
  };

  const filteredTables = useMemo(() => {
    let filtered = tableIndexes;
    
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(table => 
        table.name.toLowerCase().includes(query) ||
        table.path.toLowerCase().includes(query) ||
        table.description?.toLowerCase().includes(query)
      );
    }
    
    if (statusFilter !== "all") {
      filtered = filtered.filter(table => table.status === statusFilter);
    }
    
    if (typeFilter !== "all") {
      filtered = filtered.filter(table => table.file_type === typeFilter);
    }
    
    return filtered;
  }, [tableIndexes, searchQuery, statusFilter, typeFilter]);

  const handleViewTable = (tableId: string) => {
    setDrawerVisible(true);
    fetchTableDetail(tableId);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "indexed": return "success";
      case "pending": return "processing";
      case "error": return "error";
      default: return "default";
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case "indexed": return t("indexMap.statusIndexed");
      case "pending": return t("indexMap.statusPending");
      case "error": return t("indexMap.statusError");
      default: return status;
    }
  };

  const getFileTypeIcon = (fileType: string) => {
    switch (fileType) {
      case "excel": return "📊";
      case "csv": return "📄";
      case "json": return "🔧";
      default: return "📄";
    }
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  const columns = [
    {
      title: t("indexMap.tableName"),
      dataIndex: "name",
      key: "name",
      render: (name: string, record: TableIndex) => (
        <Space>
          <span>{getFileTypeIcon(record.file_type)}</span>
          <Text strong>{name}</Text>
          {record.description && (
            <Tooltip title={record.description}>
              <Text type="secondary" ellipsis style={{ maxWidth: 200 }}>
                {record.description}
              </Text>
            </Tooltip>
          )}
        </Space>
      ),
    },
    {
      title: t("indexMap.path"),
      dataIndex: "path",
      key: "path",
      render: (path: string) => (
        <Text code style={{ fontSize: "12px" }}>{path}</Text>
      ),
    },
    {
      title: t("indexMap.status"),
      dataIndex: "status",
      key: "status",
      width: 120,
      render: (status: string) => (
        <Tag color={getStatusColor(status)}>
          {getStatusText(status)}
        </Tag>
      ),
    },
    {
      title: t("indexMap.fields"),
      key: "fields",
      width: 80,
      align: "center" as const,
      render: (record: TableIndex) => (
        <Badge count={record.field_count} style={{ backgroundColor: '#1677ff' }} />
      ),
    },
    {
      title: t("indexMap.rows"),
      dataIndex: "row_count",
      key: "rows",
      width: 80,
      align: "center" as const,
      render: (count: number) => (
        <Text>{count.toLocaleString()}</Text>
      ),
    },
    {
      title: t("indexMap.dependencies"),
      key: "dependencies",
      width: 150,
      render: (record: TableIndex) => (
        <Space wrap>
          {record.dependencies.slice(0, 2).map(dep => (
            <Tag key={dep}>{dep}</Tag>
          ))}
          {record.dependencies.length > 2 && (
            <Tag>+{record.dependencies.length - 2}</Tag>
          )}
        </Space>
      ),
    },
    {
      title: t("indexMap.lastModified"),
      dataIndex: "last_modified",
      key: "lastModified",
      width: 180,
      render: (timestamp: string) => (
        <Text style={{ fontSize: "12px" }}>
          {formatTimestamp(timestamp)}
        </Text>
      ),
    },
    {
      title: t("indexMap.actions"),
      key: "actions",
      width: 100,
      render: (record: TableIndex) => (
        <Space>
          <Tooltip title={t("indexMap.viewDetails")}>
            <Button
              type="text"
              icon={<EyeOutlined />}
              size="small"
              onClick={() => handleViewTable(record.id)}
            />
          </Tooltip>
        </Space>
      ),
    },
  ];

  useEffect(() => {
    fetchTableIndexes();
  }, [selectedAgent]);

  return (
    <div className={styles.indexMapPage}>
      <PageHeader parent={t("nav.game")} current={t("indexMap.title")} />

      <div className={styles.content}>
        
        {/* Statistics Cards */}
        <Row gutter={16} className={styles.statsRow}>
          <Col span={6}>
            <Card size="small">
              <div className={styles.statCard}>
                <div className={styles.statIcon}>
                  <TableOutlined style={{ color: '#1677ff' }} />
                </div>
                <div className={styles.statContent}>
                  <div className={styles.statValue}>{tableIndexes.length}</div>
                  <div className={styles.statLabel}>{t("indexMap.totalTables")}</div>
                </div>
              </div>
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <div className={styles.statCard}>
                <div className={styles.statIcon}>
                  <NodeIndexOutlined style={{ color: '#52c41a' }} />
                </div>
                <div className={styles.statContent}>
                  <div className={styles.statValue}>
                    {tableIndexes.filter(t => t.status === 'indexed').length}
                  </div>
                  <div className={styles.statLabel}>{t("indexMap.indexedTables")}</div>
                </div>
              </div>
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <div className={styles.statCard}>
                <div className={styles.statIcon}>
                  <LinkOutlined style={{ color: '#fa8c16' }} />
                </div>
                <div className={styles.statContent}>
                  <div className={styles.statValue}>
                    {tableIndexes.reduce((sum, t) => sum + t.dependencies.length, 0)}
                  </div>
                  <div className={styles.statLabel}>{t("indexMap.totalDependencies")}</div>
                </div>
              </div>
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <div className={styles.statCard}>
                <div className={styles.statIcon}>
                  <Text style={{ fontSize: '20px' }}>📊</Text>
                </div>
                <div className={styles.statContent}>
                  <div className={styles.statValue}>
                    {tableIndexes.reduce((sum, t) => sum + t.field_count, 0)}
                  </div>
                  <div className={styles.statLabel}>{t("indexMap.totalFields")}</div>
                </div>
              </div>
            </Card>
          </Col>
        </Row>

        {/* Filters */}
        <Card className={styles.filtersCard}>
          <Space size="large" wrap>
            <Input
              placeholder={t("indexMap.searchPlaceholder")}
              prefix={<SearchOutlined />}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{ width: 300 }}
            />
            <Select
              value={statusFilter}
              onChange={setStatusFilter}
              style={{ width: 150 }}
            >
              <Option value="all">{t("indexMap.allStatus")}</Option>
              <Option value="indexed">{t("indexMap.statusIndexed")}</Option>
              <Option value="pending">{t("indexMap.statusPending")}</Option>
              <Option value="error">{t("indexMap.statusError")}</Option>
            </Select>
            <Select
              value={typeFilter}
              onChange={setTypeFilter}
              style={{ width: 150 }}
            >
              <Option value="all">{t("indexMap.allTypes")}</Option>
              <Option value="excel">Excel</Option>
              <Option value="csv">CSV</Option>
              <Option value="json">JSON</Option>
            </Select>
            <Button
              icon={<ReloadOutlined />}
              onClick={fetchTableIndexes}
              loading={loading}
            >
              {t("common.refresh")}
            </Button>
          </Space>
        </Card>

        {/* Table List */}
        <Card className={styles.tableCard}>
          <Table
            columns={columns}
            dataSource={filteredTables}
            rowKey="id"
            loading={loading}
            pagination={{
              pageSize: 20,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total, range) => 
                t("indexMap.pagination", { 
                  start: range[0], 
                  end: range[1], 
                  total 
                }),
            }}
            locale={{
              emptyText: <Empty description={t("indexMap.noTables")} />
            }}
            scroll={{ x: 1200 }}
          />
        </Card>
      </div>

      {/* Table Detail Drawer */}
      <Drawer
        title={tableDetail ? t("indexMap.tableDetails", { name: tableDetail.index.name }) : ""}
        placement="right"
        width={600}
        open={drawerVisible}
        onClose={() => setDrawerVisible(false)}
        loading={detailLoading}
      >
        {tableDetail && (
          <div className={styles.drawerContent}>
            
            {/* Basic Info */}
            <Card title={t("indexMap.basicInfo")} size="small" className={styles.detailSection}>
              <Descriptions column={1} size="small">
                <Descriptions.Item label={t("indexMap.tableName")}>
                  {tableDetail.index.name}
                </Descriptions.Item>
                <Descriptions.Item label={t("indexMap.path")}>
                  <Text code>{tableDetail.index.path}</Text>
                </Descriptions.Item>
                <Descriptions.Item label={t("indexMap.fileType")}>
                  {getFileTypeIcon(tableDetail.index.file_type)} {tableDetail.index.file_type.toUpperCase()}
                </Descriptions.Item>
                <Descriptions.Item label={t("indexMap.status")}>
                  <Tag color={getStatusColor(tableDetail.index.status)}>
                    {getStatusText(tableDetail.index.status)}
                  </Tag>
                </Descriptions.Item>
                <Descriptions.Item label={t("indexMap.rowCount")}>
                  {tableDetail.index.row_count.toLocaleString()}
                </Descriptions.Item>
                <Descriptions.Item label={t("indexMap.fieldCount")}>
                  {tableDetail.index.field_count}
                </Descriptions.Item>
              </Descriptions>
            </Card>

            {/* Dependencies */}
            <Card title={t("indexMap.dependencies")} size="small" className={styles.detailSection}>
              <Space direction="vertical" style={{ width: '100%' }}>
                <div>
                  <Text strong>{t("indexMap.dependsOn")}:</Text>
                  <div style={{ marginTop: 8 }}>
                    {tableDetail.index.dependencies.length > 0 ? (
                      <Space wrap>
                        {tableDetail.index.dependencies.map(dep => (
                          <Tag key={dep}>{dep}</Tag>
                        ))}
                      </Space>
                    ) : (
                      <Text type="secondary">{t("indexMap.noDependencies")}</Text>
                    )}
                  </div>
                </div>
                <div>
                  <Text strong>{t("indexMap.referencedBy")}:</Text>
                  <div style={{ marginTop: 8 }}>
                    {tableDetail.index.referenced_by.length > 0 ? (
                      <Space wrap>
                        {tableDetail.index.referenced_by.map(ref => (
                          <Tag key={ref} color="blue">{ref}</Tag>
                        ))}
                      </Space>
                    ) : (
                      <Text type="secondary">{t("indexMap.notReferenced")}</Text>
                    )}
                  </div>
                </div>
              </Space>
            </Card>

            {/* Fields */}
            <Card title={t("indexMap.fields")} size="small" className={styles.detailSection}>
              <List
                size="small"
                dataSource={tableDetail.fields}
                renderItem={(field: FieldInfo) => (
                  <List.Item>
                    <div style={{ width: '100%' }}>
                      <Space>
                        <Text strong>{field.name}</Text>
                        <Tag>{field.type}</Tag>
                        {field.is_key && <Tag color="gold">KEY</Tag>}
                        {field.references && (
                          <Tag color="purple">
                            → {field.references.table}.{field.references.field}
                          </Tag>
                        )}
                      </Space>
                      {field.description && (
                        <div style={{ marginTop: 4 }}>
                          <Text type="secondary" style={{ fontSize: '12px' }}>
                            {field.description}
                          </Text>
                        </div>
                      )}
                    </div>
                  </List.Item>
                )}
              />
            </Card>

            {/* Sample Data */}
            <Card title={t("indexMap.sampleData")} size="small" className={styles.detailSection}>
              <div className={styles.sampleData}>
                {tableDetail.sample_data.length > 0 ? (
                  <pre className={styles.jsonPreview}>
                    {JSON.stringify(tableDetail.sample_data, null, 2)}
                  </pre>
                ) : (
                  <Text type="secondary">{t("indexMap.noSampleData")}</Text>
                )}
              </div>
            </Card>

          </div>
        )}
      </Drawer>
    </div>
  );
}

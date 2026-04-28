import { useEffect, useMemo, useState } from "react";
import { ReloadOutlined, EyeOutlined, HistoryOutlined } from "@ant-design/icons";
import {
  Alert,
  Button,
  Card,
  Descriptions,
  Drawer,
  Dropdown,
  Empty,
  Progress,
  Space,
  Table,
  Tabs,
  Tag,
  Typography,
} from "antd";
import { useTranslation } from "react-i18next";
import { PageHeader } from "@/components/PageHeader";
import { useAppMessage } from "@/hooks/useAppMessage";
import { gameChangeApi } from "../../api/modules/gameChange";
import { useAgentStore } from "../../stores/agentStore";
import styles from "./SvnSync.module.less";

const { Text, Title } = Typography;

interface SvnSyncStatus {
  is_syncing: boolean;
  last_sync_time?: string;
  sync_progress?: number;
  current_operation?: string;
  next_scheduled_sync?: string;
}

interface SvnChange {
  id: string;
  revision: number;
  author: string;
  timestamp: string;
  message: string;
  paths: string[];
  action: 'A' | 'M' | 'D';
}

interface WatchStats {
  total_files_watched: number;
  active_watchers: number;
  changes_detected_today: number;
  last_change_time?: string;
}

interface ChangeProposalRecord {
  id: string;
  title: string;
  description?: string;
  status: string;
  author?: string;
  created_at: string;
  updated_at?: string;
  ops: Array<Record<string, any>>;
}

export default function SvnSync() {
  const { t } = useTranslation();
  const { message } = useAppMessage();
  const { selectedAgent } = useAgentStore();
  
  const [loading, setLoading] = useState(true);
  const [syncStatus, setSyncStatus] = useState<SvnSyncStatus | null>(null);
  const [recentChanges, setRecentChanges] = useState<SvnChange[]>([]);
  const [watchStats, setWatchStats] = useState<WatchStats | null>(null);
  const [proposalsLoading, setProposalsLoading] = useState(false);
  const [proposals, setProposals] = useState<ChangeProposalRecord[]>([]);
  const [selectedProposal, setSelectedProposal] = useState<ChangeProposalRecord | null>(null);
  const [drawerVisible, setDrawerVisible] = useState(false);
  const [dryRunResult, setDryRunResult] = useState<any[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const canUseGameChange = !!selectedAgent;

  const fetchSyncStatus = async () => {
    setLoading(true);
    setError(null);
    try {
      // Note: These endpoints would need to be implemented in the backend
      const [statusResponse, changesResponse, statsResponse] = await Promise.allSettled([
        // These are placeholder calls - actual API endpoints need to be implemented
        fetch('/api/game-project/sync/status'),
        fetch('/api/game-project/sync/changes?limit=10'),
        fetch('/api/game-project/watch/stats'),
      ]);
      
      if (statusResponse.status === 'fulfilled' && statusResponse.value.ok) {
        const status = await statusResponse.value.json();
        setSyncStatus(status);
      } else {
        // Mock data for demonstration
        setSyncStatus({
          is_syncing: false,
          last_sync_time: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
          sync_progress: 100,
          current_operation: '',
          next_scheduled_sync: new Date(Date.now() + 5 * 60 * 1000).toISOString(),
        });
      }

      if (changesResponse.status === 'fulfilled' && changesResponse.value.ok) {
        const changes = await changesResponse.value.json();
        setRecentChanges(changes);
      } else {
        // Mock data for demonstration
        setRecentChanges([
          {
            id: '1',
            revision: 1234,
            author: 'developer1',
            timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
            message: '更新配置表数据',
            paths: ['Tables/Items.xlsx', 'Tables/NPCs.csv'],
            action: 'M',
          },
          {
            id: '2',
            revision: 1233,
            author: 'developer2',
            timestamp: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
            message: '新增技能配置',
            paths: ['Tables/Skills.xlsx'],
            action: 'A',
          },
        ]);
      }

      if (statsResponse.status === 'fulfilled' && statsResponse.value.ok) {
        const stats = await statsResponse.value.json();
        setWatchStats(stats);
      } else {
        // Mock data for demonstration
        setWatchStats({
          total_files_watched: 128,
          active_watchers: 3,
          changes_detected_today: 7,
          last_change_time: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
        });
      }
      
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : t("svnSync.loadFailed");
      setError(errMsg);
    } finally {
      setLoading(false);
    }
  };

  const fetchProposals = async () => {
    if (!selectedAgent) {
      setProposals([]);
      return;
    }
    setProposalsLoading(true);
    try {
      const data = await gameChangeApi.list(selectedAgent);
      setProposals(Array.isArray(data) ? data : []);
    } catch (err) {
      const detail = err instanceof Error ? err.message : t("gameProposal.loadFailed");
      message.error(detail);
    } finally {
      setProposalsLoading(false);
    }
  };

  const handleManualSync = async () => {
    try {
      message.info(t("svnSync.syncStarted"));
      // Placeholder - actual API call would be:
      // await fetch('/api/game-project/sync/trigger', { method: 'POST' });
      await new Promise(resolve => setTimeout(resolve, 1000)); // Simulate API call
      message.success(t("svnSync.syncSuccess"));
      fetchSyncStatus(); // Refresh status
    } catch (err) {
      message.error(t("svnSync.syncFailed"));
    }
  };

  const handleOpenProposal = async (proposalId: string) => {
    if (!selectedAgent) return;
    try {
      const proposal = await gameChangeApi.get(selectedAgent, proposalId);
      setSelectedProposal(proposal);
      setDryRunResult(null);
      setDrawerVisible(true);
    } catch (err) {
      message.error(err instanceof Error ? err.message : t("gameProposal.detailLoadFailed"));
    }
  };

  const handleProposalAction = async (proposal: ChangeProposalRecord, action: string) => {
    if (!selectedAgent) return;
    try {
      if (action === "dry_run") {
        const result = await gameChangeApi.dryRun(selectedAgent, proposal.id);
        setSelectedProposal(proposal);
        setDryRunResult(Array.isArray(result) ? result : []);
        setDrawerVisible(true);
        return;
      }
      if (action === "approve") await gameChangeApi.approve(selectedAgent, proposal.id);
      if (action === "apply") await gameChangeApi.apply(selectedAgent, proposal.id);
      if (action === "commit") await gameChangeApi.commit(selectedAgent, proposal.id);
      if (action === "reject") await gameChangeApi.reject(selectedAgent, proposal.id);
      if (action === "revert") await gameChangeApi.revert(selectedAgent, proposal.id);
      message.success(t(`gameProposal.actionSuccess.${action}`));
      fetchProposals();
    } catch (err) {
      message.error(err instanceof Error ? err.message : t("gameProposal.actionFailed"));
    }
  };

  useEffect(() => {
    fetchSyncStatus();
    fetchProposals();
    // Set up periodic refresh every 30 seconds
    const interval = setInterval(() => {
      fetchSyncStatus();
      fetchProposals();
    }, 30000);
    return () => clearInterval(interval);
  }, [selectedAgent]);

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  const getActionColor = (action: string) => {
    switch (action) {
      case 'A': return 'green';
      case 'M': return 'blue';
      case 'D': return 'red';
      default: return 'default';
    }
  };

  const getActionText = (action: string) => {
    switch (action) {
      case 'A': return t("svnSync.actionAdded");
      case 'M': return t("svnSync.actionModified");
      case 'D': return t("svnSync.actionDeleted");
      default: return action;
    }
  };

  const changesColumns = [
    {
      title: t("svnSync.revision"),
      dataIndex: 'revision',
      key: 'revision',
      width: 100,
    },
    {
      title: t("svnSync.action"),
      dataIndex: 'action',
      key: 'action',
      width: 80,
      render: (action: string) => (
        <Tag color={getActionColor(action)}>{getActionText(action)}</Tag>
      ),
    },
    {
      title: t("svnSync.author"),
      dataIndex: 'author',
      key: 'author',
      width: 120,
    },
    {
      title: t("svnSync.message"),
      dataIndex: 'message',
      key: 'message',
      render: (message: string) => (
        <Text ellipsis={{ tooltip: message }}>{message}</Text>
      ),
    },
    {
      title: t("svnSync.paths"),
      dataIndex: 'paths',
      key: 'paths',
      render: (paths: string[]) => (
        <Space wrap>
          {paths.slice(0, 2).map((path, index) => (
            <Tag key={index}>{path}</Tag>
          ))}
          {paths.length > 2 && (
            <Tag>+{paths.length - 2} {t("svnSync.morePaths")}</Tag>
          )}
        </Space>
      ),
    },
    {
      title: t("svnSync.timestamp"),
      dataIndex: 'timestamp',
      key: 'timestamp',
      width: 180,
      render: (timestamp: string) => formatTimestamp(timestamp),
    },
  ];

  const proposalStatusColor = (status: string) => {
    switch (status) {
      case "approved":
        return "processing";
      case "applied":
        return "gold";
      case "committed":
        return "success";
      case "rejected":
      case "reverted":
        return "default";
      default:
        return "blue";
    }
  };

  const proposalActionItems = (proposal: ChangeProposalRecord) => [
    { key: "dry_run", label: t("gameProposal.actions.dryRun") },
    { key: "approve", label: t("gameProposal.actions.approve"), disabled: proposal.status !== "draft" },
    { key: "apply", label: t("gameProposal.actions.apply"), disabled: proposal.status !== "approved" },
    { key: "commit", label: t("gameProposal.actions.commit"), disabled: proposal.status !== "applied" },
    { key: "reject", label: t("gameProposal.actions.reject"), disabled: !["draft", "approved"].includes(proposal.status) },
    { key: "revert", label: t("gameProposal.actions.revert"), disabled: proposal.status !== "applied" },
  ];

  const proposalColumns = useMemo(() => ([
    {
      title: t("gameProposal.title"),
      dataIndex: "title",
      key: "title",
      render: (value: string, record: ChangeProposalRecord) => (
        <Button type="link" onClick={() => handleOpenProposal(record.id)} className={styles.inlineLink}>
          {value}
        </Button>
      ),
    },
    {
      title: t("gameProposal.status"),
      dataIndex: "status",
      key: "status",
      width: 120,
      render: (status: string) => <Tag color={proposalStatusColor(status)}>{t(`gameProposal.statuses.${status}`)}</Tag>,
    },
    {
      title: t("gameProposal.author"),
      dataIndex: "author",
      key: "author",
      width: 120,
      render: (value?: string) => value || "-",
    },
    {
      title: t("gameProposal.createdAt"),
      dataIndex: "created_at",
      key: "created_at",
      width: 180,
      render: (value: string) => formatTimestamp(value),
    },
    {
      title: t("gameProposal.actions.label"),
      key: "actions",
      width: 180,
      render: (_: unknown, record: ChangeProposalRecord) => (
        <Space>
          <Button size="small" icon={<EyeOutlined />} onClick={() => handleOpenProposal(record.id)}>
            {t("gameProposal.actions.view")}
          </Button>
          <Dropdown
            menu={{
              items: proposalActionItems(record),
              onClick: ({ key }) => handleProposalAction(record, key),
            }}
          >
            <Button size="small">{t("gameProposal.actions.more")}</Button>
          </Dropdown>
        </Space>
      ),
    },
  ]), [t, proposals]);

  const syncTabContent = (
    <>
      <Card 
        title={t("svnSync.syncStatus")} 
        className={styles.section}
        extra={
          <Space>
            <Button 
              icon={<ReloadOutlined />}
              onClick={fetchSyncStatus}
              size="small"
            >
              {t("common.refresh")}
            </Button>
            <Button 
              type="primary"
              onClick={handleManualSync}
              disabled={syncStatus?.is_syncing}
              size="small"
            >
              {t("svnSync.manualSync")}
            </Button>
          </Space>
        }
      >
        {syncStatus && (
          <>
            {syncStatus.is_syncing && (
              <Alert
                message={t("svnSync.syncInProgress")}
                description={syncStatus.current_operation || t("svnSync.syncingDescription")}
                type="info"
                showIcon
                style={{ marginBottom: 16 }}
              />
            )}
            
            {syncStatus.is_syncing && syncStatus.sync_progress && (
              <Progress 
                percent={syncStatus.sync_progress} 
                status={syncStatus.sync_progress === 100 ? "success" : "active"}
                style={{ marginBottom: 16 }}
              />
            )}
            
            <Descriptions column={2}>
              <Descriptions.Item label={t("svnSync.lastSyncTime")}>
                {syncStatus.last_sync_time ? formatTimestamp(syncStatus.last_sync_time) : t("svnSync.never")}
              </Descriptions.Item>
              <Descriptions.Item label={t("svnSync.nextScheduledSync")}>
                {syncStatus.next_scheduled_sync ? formatTimestamp(syncStatus.next_scheduled_sync) : t("svnSync.notScheduled")}
              </Descriptions.Item>
              <Descriptions.Item label={t("svnSync.syncStatus")}>
                <Tag color={syncStatus.is_syncing ? "processing" : "success"}>
                  {syncStatus.is_syncing ? t("svnSync.syncing") : t("svnSync.idle")}
                </Tag>
              </Descriptions.Item>
            </Descriptions>
          </>
        )}
      </Card>

      <Card title={t("svnSync.watchStats")} className={styles.section}>
        {watchStats && (
          <Descriptions column={2}>
            <Descriptions.Item label={t("svnSync.totalFilesWatched")}>
              <Text strong>{watchStats.total_files_watched}</Text>
            </Descriptions.Item>
            <Descriptions.Item label={t("svnSync.activeWatchers")}>
              <Text strong>{watchStats.active_watchers}</Text>
            </Descriptions.Item>
            <Descriptions.Item label={t("svnSync.changesDetectedToday")}>
              <Text strong>{watchStats.changes_detected_today}</Text>
            </Descriptions.Item>
            <Descriptions.Item label={t("svnSync.lastChangeTime")}>
              {watchStats.last_change_time ? formatTimestamp(watchStats.last_change_time) : t("svnSync.noChanges")}
            </Descriptions.Item>
          </Descriptions>
        )}
      </Card>

      <Card 
        title={t("svnSync.recentChanges")} 
        className={styles.section}
        extra={
          <Button 
            icon={<HistoryOutlined />}
            size="small"
            onClick={() => message.info(t("svnSync.viewAllChanges"))}
          >
            {t("svnSync.viewAll")}
          </Button>
        }
      >
        <Table
          columns={changesColumns}
          dataSource={recentChanges}
          rowKey="id"
          size="middle"
          pagination={false}
          scroll={{ x: 800 }}
          locale={{
            emptyText: t("svnSync.noRecentChanges")
          }}
        />
      </Card>
    </>
  );

  const proposalTabContent = (
    <Card
      title={t("gameProposal.tab")}
      className={styles.section}
      extra={
        <Button icon={<ReloadOutlined />} onClick={fetchProposals} size="small" disabled={!canUseGameChange}>
          {t("common.refresh")}
        </Button>
      }
    >
      {!canUseGameChange ? (
        <Empty description={t("gameProposal.noAgent")} />
      ) : (
        <Table
          columns={proposalColumns}
          dataSource={proposals}
          rowKey="id"
          loading={proposalsLoading}
          pagination={false}
          locale={{ emptyText: t("gameProposal.empty") }}
        />
      )}
    </Card>
  );

  if (loading) {
    return (
      <div className={styles.svnSyncPage}>
        <div className={styles.centerState}>
          <span className={styles.stateText}>{t("common.loading")}</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.svnSyncPage}>
        <div className={styles.centerState}>
          <span className={styles.stateTextError}>{error}</span>
          <Button size="small" onClick={fetchSyncStatus} style={{ marginTop: 12 }}>
            {t("common.retry")}
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.svnSyncPage}>
      <PageHeader parent={t("nav.game")} current={t("svnSync.title")} />

      <div className={styles.content}>
        <Tabs
          defaultActiveKey="sync"
          items={[
            { key: "sync", label: t("nav.svnSync"), children: syncTabContent },
            { key: "proposal", label: t("gameProposal.tab"), children: proposalTabContent },
          ]}
        />
      </div>

      <Drawer
        title={selectedProposal?.title || t("gameProposal.detail")}
        open={drawerVisible}
        onClose={() => setDrawerVisible(false)}
        width={720}
      >
        {selectedProposal && (
          <div className={styles.proposalDrawer}>
            <Descriptions column={1} size="small" className={styles.drawerMeta}>
              <Descriptions.Item label={t("gameProposal.status")}>
                <Tag color={proposalStatusColor(selectedProposal.status)}>
                  {t(`gameProposal.statuses.${selectedProposal.status}`)}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label={t("gameProposal.description")}>
                {selectedProposal.description || "-"}
              </Descriptions.Item>
            </Descriptions>

            <Title level={5}>{t("gameProposal.ops")}</Title>
            <Table
              rowKey={(_, index) => `${selectedProposal.id}-${index}`}
              pagination={false}
              size="small"
              dataSource={selectedProposal.ops}
              columns={[
                { title: t("gameProposal.op"), dataIndex: "op", key: "op" },
                { title: t("gameProposal.table"), dataIndex: "table", key: "table" },
                { title: t("gameProposal.rowId"), dataIndex: "row_id", key: "row_id" },
                { title: t("gameProposal.field"), dataIndex: "field", key: "field", render: (value?: string) => value || "-" },
                { title: t("gameProposal.oldValue"), dataIndex: "old_value", key: "old_value", render: (value: any) => value ?? "-" },
                { title: t("gameProposal.newValue"), dataIndex: "new_value", key: "new_value", render: (value: any) => typeof value === "object" ? JSON.stringify(value) : value ?? "-" },
              ]}
            />

            {dryRunResult && (
              <>
                <Title level={5} className={styles.drawerSectionTitle}>{t("gameProposal.dryRunResult")}</Title>
                <Table
                  rowKey={(_, index) => `${selectedProposal.id}-dry-${index}`}
                  pagination={false}
                  size="small"
                  dataSource={dryRunResult}
                  columns={[
                    { title: t("gameProposal.op"), dataIndex: ["op", "op"], key: "op" },
                    { title: t("gameProposal.before"), dataIndex: "before", key: "before", render: (value: any) => typeof value === "object" ? JSON.stringify(value) : value ?? "-" },
                    { title: t("gameProposal.after"), dataIndex: "after", key: "after", render: (value: any) => typeof value === "object" ? JSON.stringify(value) : value ?? "-" },
                    { title: t("gameProposal.reason"), dataIndex: "reason", key: "reason", render: (value?: string) => value || "-" },
                  ]}
                />
              </>
            )}
          </div>
        )}
      </Drawer>
    </div>
  );
}

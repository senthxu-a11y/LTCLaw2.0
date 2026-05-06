import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { IconButton } from "@agentscope-ai/design";
import { useTranslation } from "react-i18next";
import {
  Badge,
  Button,
  Descriptions,
  Drawer,
  Dropdown,
  Empty,
  Space,
  Table,
  Tag,
  Tooltip,
  Typography,
} from "antd";
import { EyeOutlined, ReloadOutlined } from "@ant-design/icons";
import { useAppMessage } from "../../../../hooks/useAppMessage";
import { useAgentStore } from "../../../../stores/agentStore";
import {
  gameChangeApi,
  type ChangeProposalRecord,
} from "../../../../api/modules/gameChange";
import { subscribeOpenGameProposal } from "../../workbenchCardChannel";

const POLL_INTERVAL_MS = 15_000;
const ACTIVE_STATUSES = new Set(["draft", "approved", "applied"]);

type ActionKey =
  | "dry_run"
  | "approve"
  | "apply"
  | "commit"
  | "reject"
  | "revert";

const StatusColor: Record<string, string> = {
  draft: "blue",
  approved: "processing",
  applied: "gold",
  committed: "success",
  rejected: "default",
  reverted: "default",
};

const ProposalIcon = () => (
  <svg
    width="1em"
    height="1em"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
    <polyline points="14 2 14 8 20 8" />
    <path d="M9 13h6M9 17h4" />
  </svg>
);

const GameProposalsButton: React.FC = () => {
  const { t } = useTranslation();
  const { message } = useAppMessage();
  const { selectedAgent } = useAgentStore();
  const [available, setAvailable] = useState(false);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [proposals, setProposals] = useState<ChangeProposalRecord[]>([]);
  const [selected, setSelected] = useState<ChangeProposalRecord | null>(null);
  const [dryRunResult, setDryRunResult] = useState<unknown[] | null>(null);
  const stopRef = useRef(false);

  const fetchProposals = useCallback(
    async (silent: boolean = true) => {
      if (!selectedAgent) {
        setProposals([]);
        setAvailable(false);
        return;
      }
      if (!silent) setLoading(true);
      try {
        const list = await gameChangeApi.list(selectedAgent);
        setProposals(Array.isArray(list) ? list : []);
        setAvailable(true);
      } catch {
        // Game service not registered for this workspace: hide silently.
        setProposals([]);
        setAvailable(false);
      } finally {
        if (!silent) setLoading(false);
      }
    },
    [selectedAgent],
  );

  useEffect(() => {
    stopRef.current = false;
    fetchProposals(false);
    const timer = setInterval(() => {
      if (!stopRef.current) fetchProposals(true);
    }, POLL_INTERVAL_MS);
    return () => {
      stopRef.current = true;
      clearInterval(timer);
    };
  }, [fetchProposals]);

  const activeCount = useMemo(
    () => proposals.filter((p) => ACTIVE_STATUSES.has(p.status)).length,
    [proposals],
  );

  const openProposalDetail = useCallback(
    async (proposalId: string) => {
      if (!selectedAgent) return;
      setOpen(true);
      const existing = proposals.find((proposal) => proposal.id === proposalId) || null;
      if (existing) {
        setSelected(existing);
        setDryRunResult(null);
      }
      try {
        const detail = await gameChangeApi.get(selectedAgent, proposalId);
        setSelected(detail);
        setDryRunResult(null);
      } catch (err) {
        message.error(
          err instanceof Error
            ? err.message
            : t("gameProposal.detailLoadFailed", { defaultValue: "Failed to load proposal detail" }),
        );
      }
    },
    [message, proposals, selectedAgent, t],
  );

  useEffect(
    () => subscribeOpenGameProposal(({ proposalId }) => {
      void openProposalDetail(proposalId);
    }),
    [openProposalDetail],
  );

  const handleAction = useCallback(
    async (proposal: ChangeProposalRecord, action: ActionKey) => {
      if (!selectedAgent) return;
      try {
        if (action === "dry_run") {
          const result = await gameChangeApi.dryRun(selectedAgent, proposal.id);
          setSelected(proposal);
          setDryRunResult(Array.isArray(result) ? (result as unknown[]) : []);
          return;
        }
        if (action === "approve") await gameChangeApi.approve(selectedAgent, proposal.id);
        if (action === "apply") await gameChangeApi.apply(selectedAgent, proposal.id);
        if (action === "commit") await gameChangeApi.commit(selectedAgent, proposal.id);
        if (action === "reject") await gameChangeApi.reject(selectedAgent, proposal.id);
        if (action === "revert") await gameChangeApi.revert(selectedAgent, proposal.id);
        message.success(
          t(`gameProposal.actionSuccess.${action}`, {
            defaultValue: "Done",
          }),
        );
        fetchProposals(true);
      } catch (err) {
        message.error(
          err instanceof Error
            ? err.message
            : t("gameProposal.actionFailed", { defaultValue: "Action failed" }),
        );
      }
    },
    [selectedAgent, message, t, fetchProposals],
  );

  const menuItems = useCallback(
    (p: ChangeProposalRecord) => [
      { key: "dry_run", label: t("gameProposal.actions.dryRun", { defaultValue: "Dry run" }) },
      {
        key: "approve",
        label: t("gameProposal.actions.approve", { defaultValue: "Approve" }),
        disabled: p.status !== "draft",
      },
      {
        key: "apply",
        label: t("gameProposal.actions.apply", { defaultValue: "Apply" }),
        disabled: p.status !== "approved",
      },
      {
        key: "commit",
        label: t("gameProposal.actions.commit", { defaultValue: "Commit" }),
        disabled: p.status !== "applied",
      },
      {
        key: "reject",
        label: t("gameProposal.actions.reject", { defaultValue: "Reject" }),
        disabled: !["draft", "approved"].includes(p.status),
      },
      {
        key: "revert",
        label: t("gameProposal.actions.revert", { defaultValue: "Revert" }),
        disabled: p.status !== "applied",
      },
    ],
    [t],
  );

  const columns = [
    {
      title: t("gameProposal.title", { defaultValue: "Title" }),
      dataIndex: "title",
      key: "title",
      render: (title: string, record: ChangeProposalRecord) => (
        <Button
          type="link"
          size="small"
          style={{ padding: 0, height: "auto" }}
          onClick={() => {
            void openProposalDetail(record.id);
          }}
        >
          {title}
        </Button>
      ),
    },
    {
      title: t("gameProposal.status", { defaultValue: "Status" }),
      dataIndex: "status",
      key: "status",
      width: 110,
      render: (status: string) => (
        <Tag color={StatusColor[status] || "default"}>
          {t(`gameProposal.statuses.${status}`, { defaultValue: status })}
        </Tag>
      ),
    },
    {
      title: t("gameProposal.actions.label", { defaultValue: "Actions" }),
      key: "actions",
      width: 160,
      render: (_: unknown, record: ChangeProposalRecord) => (
        <Space size="small">
          <Tooltip title={t("gameProposal.actions.view", { defaultValue: "View" })}>
            <Button
              type="text"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => {
                void openProposalDetail(record.id);
              }}
            />
          </Tooltip>
          <Dropdown
            menu={{
              items: menuItems(record),
              onClick: ({ key }) => handleAction(record, key as ActionKey),
            }}
          >
            <Button size="small">
              {t("gameProposal.actions.more", { defaultValue: "More" })}
            </Button>
          </Dropdown>
        </Space>
      ),
    },
  ];

  if (!available) return null;

  return (
    <>
      <Tooltip
        title={t("chat.gameProposalsTooltip", {
          defaultValue: "Game change proposals",
        })}
        mouseEnterDelay={0.5}
      >
        <Badge count={activeCount} size="small" offset={[-2, 2]}>
          <IconButton
            bordered={false}
            icon={<ProposalIcon />}
            onClick={() => setOpen(true)}
          />
        </Badge>
      </Tooltip>
      <Drawer
        title={t("chat.gameProposalsTitle", {
          defaultValue: "Game proposals",
        })}
        open={open}
        onClose={() => setOpen(false)}
        width={720}
        extra={
          <Button
            size="small"
            icon={<ReloadOutlined />}
            onClick={() => fetchProposals(false)}
            loading={loading}
          >
            {t("common.refresh", { defaultValue: "Refresh" })}
          </Button>
        }
      >
        {proposals.length === 0 ? (
          <Empty
            description={t("gameProposal.empty", {
              defaultValue: "No proposals yet",
            })}
          />
        ) : (
          <Table
            rowKey="id"
            size="small"
            pagination={false}
            loading={loading}
            dataSource={proposals}
            columns={columns}
          />
        )}
        {selected && (
          <div style={{ marginTop: 16 }}>
            <Typography.Title level={5}>{selected.title}</Typography.Title>
            <Descriptions column={1} size="small">
              <Descriptions.Item
                label={t("gameProposal.status", { defaultValue: "Status" })}
              >
                <Tag color={StatusColor[selected.status] || "default"}>
                  {t(`gameProposal.statuses.${selected.status}`, {
                    defaultValue: selected.status,
                  })}
                </Tag>
              </Descriptions.Item>
              {selected.description && (
                <Descriptions.Item
                  label={t("gameProposal.description", {
                    defaultValue: "Description",
                  })}
                >
                  {selected.description}
                </Descriptions.Item>
              )}
            </Descriptions>
            <Typography.Title level={5} style={{ marginTop: 12 }}>
              {t("gameProposal.ops", { defaultValue: "Operations" })}
            </Typography.Title>
            <Table
              rowKey={(_, i) => `${selected.id}-${i}`}
              size="small"
              pagination={false}
              dataSource={selected.ops}
              columns={[
                { title: "op", dataIndex: "op", key: "op", width: 110 },
                { title: "table", dataIndex: "table", key: "table" },
                { title: "row_id", dataIndex: "row_id", key: "row_id", width: 90 },
                { title: "field", dataIndex: "field", key: "field" },
                {
                  title: "new_value",
                  dataIndex: "new_value",
                  key: "new_value",
                  render: (v: unknown) =>
                    typeof v === "object" ? JSON.stringify(v) : String(v ?? "-"),
                },
              ]}
            />
            {dryRunResult && (
              <>
                <Typography.Title level={5} style={{ marginTop: 12 }}>
                  {t("gameProposal.dryRunResult", {
                    defaultValue: "Dry-run preview",
                  })}
                </Typography.Title>
                <pre
                  style={{
                    background: "var(--ant-color-fill-quaternary)",
                    padding: 8,
                    borderRadius: 4,
                    maxHeight: 240,
                    overflow: "auto",
                    fontSize: 12,
                  }}
                >
                  {JSON.stringify(dryRunResult, null, 2)}
                </pre>
              </>
            )}
          </div>
        )}
      </Drawer>
    </>
  );
};

export default GameProposalsButton;

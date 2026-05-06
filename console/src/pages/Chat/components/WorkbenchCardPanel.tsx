import { useEffect, useState } from "react";
import { Button, Empty, List, Tag, Typography } from "antd";
import { DeleteOutlined } from "@ant-design/icons";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import {
  subscribeWorkbenchCards,
  subscribeWorkbenchCardsBackend,
  clearWorkbenchCards,
  openGameProposal,
  type WorkbenchCard,
} from "../workbenchCardChannel";
import { useAgentStore } from "../../../stores/agentStore";

const { Text } = Typography;

const KIND_COLOR: Record<string, string> = {
  numeric_table: "geekblue",
  draft_doc: "purple",
  svn_change: "orange",
  kb_hit: "green",
};
const KIND_LABEL: Record<string, string> = {
  numeric_table: "数值表",
  draft_doc: "草案",
  svn_change: "SVN",
  kb_hit: "知识",
};

/** Chat 右栏的「联动卡片」面板：消费 workbenchCardChannel。 */
export default function WorkbenchCardPanel() {
  const { t } = useTranslation();
  const [cards, setCards] = useState<WorkbenchCard[]>([]);
  const selectedAgent = useAgentStore((s) => s.selectedAgent);

  useEffect(() => subscribeWorkbenchCards(setCards), []);
  useEffect(() => subscribeWorkbenchCardsBackend(selectedAgent), [selectedAgent]);

  const sorted = [...cards].sort((a, b) => b.createdAt - a.createdAt);

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      <div
        style={{
          padding: "10px 12px",
          borderBottom: "1px solid var(--ant-color-border-secondary, #f0f0f0)",
          display: "flex",
          alignItems: "center",
        }}
      >
        <Text strong>{t("chat.workbenchCards", { defaultValue: "联动卡片" })}</Text>
        <span style={{ flex: 1 }} />
        {sorted.length > 0 && (
          <Button
            size="small"
            type="text"
            icon={<DeleteOutlined />}
            onClick={() => clearWorkbenchCards()}
          >
            {t("common.clear", { defaultValue: "清空" })}
          </Button>
        )}
      </div>
      <div style={{ flex: 1, overflow: "auto", padding: 8 }}>
        {sorted.length === 0 ? (
          <Empty
            style={{ marginTop: 32 }}
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description={t("chat.workbenchCardsEmpty", {
              defaultValue: "数值工作台 / 文档库会在这里推送卡片",
            })}
          />
        ) : (
          <List
            size="small"
            dataSource={sorted}
            renderItem={(c) => (
              <List.Item style={{ display: "block", padding: "6px 4px" }}>
                <div style={{ marginBottom: 4 }}>
                  <Tag color={KIND_COLOR[c.kind] ?? "default"}>
                    {KIND_LABEL[c.kind] ?? c.kind}
                  </Tag>
                  <Text strong style={{ fontSize: 13 }}>{c.title}</Text>
                </div>
                <div style={{ fontSize: 12, color: "var(--ant-color-text-secondary)", whiteSpace: "pre-wrap" }}>
                  {c.summary}
                </div>
                <div style={{ marginTop: 4, display: "flex", gap: 8, flexWrap: "wrap" }}>
                  {c.kind === "draft_doc" && typeof c.payload?.proposalId === "string" && (
                    <Button
                      size="small"
                      type="link"
                      style={{ padding: 0, height: "auto" }}
                      onClick={() => openGameProposal({ proposalId: c.payload?.proposalId as string })}
                    >
                      {t("chat.workbenchCardOpenProposal", { defaultValue: "查看草案 →" })}
                    </Button>
                  )}
                  {c.href && (
                    <Link to={c.href} style={{ fontSize: 12 }}>
                      {t("chat.workbenchCardOpen", { defaultValue: "打开 →" })}
                    </Link>
                  )}
                </div>
              </List.Item>
            )}
          />
        )}
      </div>
    </div>
  );
}

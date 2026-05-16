import { DownOutlined } from "@ant-design/icons";
import { Typography } from "antd";
import { useTranslation } from "react-i18next";
import { PageHeader } from "@/components/PageHeader";
import { useAgentStore } from "@/stores/agentStore";
import FormalMapWorkspace from "../components/FormalMapWorkspace";
import styles from "../GameProject.module.less";

const { Text } = Typography;

export default function MapEditorPage() {
  const { t } = useTranslation();
  const { selectedAgent, agents } = useAgentStore();
  const selectedAgentSummary = agents.find((agent) => agent.id === selectedAgent);
  const currentProjectName = selectedAgentSummary?.name || selectedAgent || "-";

  return (
    <div className={styles.mapEditorPage}>
      <PageHeader
        items={[{ title: t("gameWorkspaceUi.map.title", { defaultValue: "Map 编辑器" }) }]}
        className={styles.mapEditorHeader}
        extra={
          <div className={styles.mapHeaderSelector}>
            <Text strong>{currentProjectName}</Text>
            <DownOutlined />
          </div>
        }
      />
      <FormalMapWorkspace mode="full" />
    </div>
  );
}
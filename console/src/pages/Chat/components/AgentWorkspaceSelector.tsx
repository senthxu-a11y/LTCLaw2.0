import { useEffect, useMemo } from "react";
import { Select, Tooltip } from "antd";
import { TeamOutlined } from "@ant-design/icons";
import { useTranslation } from "react-i18next";
import { useAgentStore } from "../../../stores/agentStore";
import { agentsApi } from "../../../api/modules/agents";

/**
 * 顶部 Agent / Workspace 切换器。
 * 让 Chat 页可以在 default / QA / 项目级 agent 之间快速切换。
 */
export default function AgentWorkspaceSelector() {
  const { t } = useTranslation();
  const { selectedAgent, agents, setAgents, setSelectedAgent } = useAgentStore();

  useEffect(() => {
    let cancelled = false;
    if (agents.length === 0) {
      agentsApi
        .listAgents()
        .then((res) => {
          if (!cancelled && Array.isArray(res?.agents)) setAgents(res.agents);
        })
        .catch((e) => console.warn("listAgents failed:", e));
    }
    return () => {
      cancelled = true;
    };
  }, [agents.length, setAgents]);

  const options = useMemo(
    () =>
      agents
        .filter((a) => a.enabled !== false)
        .map((a) => ({
          value: a.id,
          label: a.name || a.id,
        })),
    [agents],
  );

  return (
    <Tooltip title={t("chat.workspaceTooltip", { defaultValue: "切换工作区/Agent" })}>
      <Select
        size="small"
        prefix={<TeamOutlined style={{ color: "#999" }} />}
        value={selectedAgent}
        onChange={(v) => setSelectedAgent(v)}
        options={
          options.length > 0
            ? options
            : [{ value: selectedAgent, label: selectedAgent }]
        }
        style={{ minWidth: 140 }}
        showSearch
        optionFilterProp="label"
      />
    </Tooltip>
  );
}

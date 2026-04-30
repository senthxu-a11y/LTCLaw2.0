import { Segmented, Tooltip, App } from "antd";
import {
  CommentOutlined,
  FileTextOutlined,
  TableOutlined,
  FileAddOutlined,
  BookOutlined,
} from "@ant-design/icons";
import { useTranslation } from "react-i18next";
import { create } from "zustand";
import { persist } from "zustand/middleware";
import { useAgentStore } from "../../../stores/agentStore";
import { pushWorkbenchCard } from "../workbenchCardChannel";

export type ChatMode = "free" | "design" | "numeric" | "doc" | "kb";

interface ChatModeStore {
  mode: ChatMode;
  setMode: (m: ChatMode) => void;
}

/** 持久化当前对话模式（影响后续消息的系统提示前缀）。 */
export const useChatModeStore = create<ChatModeStore>()(
  persist(
    (set) => ({
      mode: "free",
      setMode: (m) => set({ mode: m }),
    }),
    { name: "ltclaw.chat.mode" },
  ),
);

/** 给系统/用户消息附加的模式前缀，由发送方调用以注入意图。 */
export const MODE_PROMPT_PREFIX: Record<ChatMode, string> = {
  free: "",
  design:
    "[模式：策划案]请按规范的策划文档结构作答（背景/目标/方案/风险/附录），引用数据来源。",
  numeric:
    "[模式：数值查询]请优先调用数值/表格相关 Skill，回答需带表名 + row_id + 字段。如需修改请输出 changes。",
  doc:
    "[模式：文档生成]请生成可直接落库的 Markdown 文档（含 frontmatter / 标题层级 / 引用清单）。",
  kb:
    "[模式：知识查询]请基于知识库 / 文档库 / 索引图回答，标注来源文件与命中片段。",
};

/** Chat 顶部模式工具栏（自由对话 / 策划案 / 数值查询 / 文档生成 / 知识查询）。 */
export default function ChatModeToolbar() {
  const { t } = useTranslation();
  const { mode, setMode } = useChatModeStore();
  const { message } = App.useApp();
  const selectedAgent = useAgentStore((s) => s.selectedAgent);

  const MODE_LABEL: Record<ChatMode, string> = {
    free: t("chat.modes.free", { defaultValue: "自由对话" }),
    design: t("chat.modes.design", { defaultValue: "策划案" }),
    numeric: t("chat.modes.numeric", { defaultValue: "数值查询" }),
    doc: t("chat.modes.doc", { defaultValue: "文档生成" }),
    kb: t("chat.modes.kb", { defaultValue: "知识查询" }),
  };

  const handleChange = (next: ChatMode) => {
    if (next === mode) return;
    setMode(next);
    const label = MODE_LABEL[next];
    if (next === "free") {
      message.info(
        t("chat.modeBackToFree", {
          defaultValue: "已切换到自由对话（不再注入模式前缀）",
        }),
      );
      return;
    }
    message.success(
      t("chat.modeSwitched", {
        defaultValue: "已切换到「{{label}}」模式，本次起新消息会带上该模式提示",
        label,
      }),
    );
    // Drop a hint card on the workbench-card panel so it's visually obvious
    // the mode is in effect for the active agent.
    pushWorkbenchCard({
      id: `mode-hint-${next}`,
      agentId: selectedAgent || "default",
      kind: next === "kb" ? "kb_hit" : next === "numeric" ? "numeric_table" : "draft_doc",
      title: t("chat.modeCardTitle", {
        defaultValue: "模式：{{label}}",
        label,
      }),
      summary: MODE_PROMPT_PREFIX[next],
      payload: { mode: next },
    });
  };

  return (
    <Tooltip
      title={t("chat.modeTooltip", {
        defaultValue: "对话模式（影响系统提示）",
      })}
    >
      <Segmented
        size="small"
        value={mode}
        onChange={(v) => handleChange(v as ChatMode)}
        options={[
          {
            label: t("chat.modes.free", { defaultValue: "自由对话" }),
            value: "free",
            icon: <CommentOutlined />,
          },
          {
            label: t("chat.modes.design", { defaultValue: "策划案" }),
            value: "design",
            icon: <FileTextOutlined />,
          },
          {
            label: t("chat.modes.numeric", { defaultValue: "数值查询" }),
            value: "numeric",
            icon: <TableOutlined />,
          },
          {
            label: t("chat.modes.doc", { defaultValue: "文档生成" }),
            value: "doc",
            icon: <FileAddOutlined />,
          },
          {
            label: t("chat.modes.kb", { defaultValue: "知识查询" }),
            value: "kb",
            icon: <BookOutlined />,
          },
        ]}
      />
    </Tooltip>
  );
}
